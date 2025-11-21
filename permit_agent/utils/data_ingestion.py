import os
import io
import base64
import logging
import asyncio
import instructor
import pytesseract

from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Any, Literal, Dict
from pdf2image import convert_from_path
from PIL import Image

from openai import AzureOpenAI

from dotenv import load_dotenv

from tenacity import retry, wait_exponential, stop_after_attempt, before_sleep_log

load_dotenv()

instructor_client = instructor.from_provider("azure_openai/gpt-4o")

api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

client = AzureOpenAI(
    base_url=f"{api_base}/openai/deployments/{deployment_name}",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

def setup_logger(name: str = "data_ingestion", level: int = logging.INFO) -> logging.Logger:
    """
    Set up and return a logger for OCR extraction steps.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger

metadata_extraction_prompt = """
You are an expert in extracting metadata from permit images. Given an image of a permit, extract the following metadata fields:
- Issue Date
  - The date when the permit was issued, formatted as dd MMMM yyyy (e.g., 25 December 2023)
  - Use english month names only
- Expiration Date
  - The date when the permit expires, formatted as dd MMMM yyyy (e.g., 25 December 2024)
  - Use english month names only
- Permit Type: Permit type is categorized as PLO, KKPR/KKPRL, or Ijin Lingkungan
- Permit Number. 
  - Permit number is usually a combination of letters and numbers, often found at the top of the permit.
  - Permit number may contain multiple identifiers separated by commas.
  - One permit number may contain alphanumeric characters, slashes (/).
  - Return as string without any additional text and spaces.
- Summary: A brief summary of the permit content in no more than 100 words.
  - Summarize the main points of the permit, including its purpose, scope, and any important conditions or requirements mentioned.

Return the extracted metadata in the JSON format. Do not include any additional text or explanations.
"""

permit_number_extraction_prompt = """
You are an expert in extracting metadata from permit images. Given an image of a permit, extract the following metadata fields:
- Permit Type. Permit type is categorized as PLO, KKPR/KKPRL, or Ijin Lingkungan. Only return one of these three types.
- Permit Number. 
  - Permit number is usually a combination of letters and numbers, often found at the top of the permit.
  - Permit number may contain multiple identifiers separated by commas.
  - One permit number may contain alphanumeric characters, slashes (/).
  - Return as string without any additional text and spaces.

Return the extracted metadata in the JSON format. Do not include any additional text or explanations.
"""

metadata_extraction_prompt_plo = """
You are an expert in extracting metadata from permit images. Given an image of a permit, extract the following metadata fields:
- Issue Date
  - The date when the permit was issued, formatted as dd MMMM yyyy (e.g., 25 December 2023)
  - Use english month names only
- Expiration Date
  - The date when the permit expires, formatted as dd MMMM yyyy (e.g., 25 December 2024)
  - Use english month names only
- Permit Type: Permit type is categorized as PLO, KKPR/KKPRL, or Ijin Lingkungan
- Installation: The installation associated with the PLO permit. This tipically refers to the facility or site where the permit is applicable.
- Summary: A brief summary of the permit content in no more than 100 words.
  - Summarize the main points of the permit, including its purpose, scope, and any important conditions or requirements mentioned.

Return the extracted metadata in the JSON format. Do not include any additional text or explanations.
"""

logger = setup_logger()

class PermitMetadata(BaseModel):
    issue_date: str = Field(..., description="The date when the permit was issued.")
    expiration_date: str = Field(..., description="The date when the permit expires if any.")
    permit_type: Literal["PLO", "KKPR/KKPRL", "Ijin Lingkungan"] = Field(..., description="The type/category of the permit.")
    permit_number: str = Field(..., description="The unique identifier for the permit.")
    summary: str = Field(..., description="A brief summary of the permit content.")

class PLOMetadata(BaseModel):
    plo_number: str = Field(..., description="The unique identifier for the PLO permit.")
    installation: str = Field(..., description="The installation location associated with the PLO permit.")
    issue_date: str = Field(..., description="The date when the PLO permit was issued.")
    permit_type: Literal["PLO", "KKPR/KKPRL", "Ijin Lingkungan"] = Field(..., description="The type/category of the permit.")
    expiration_date: str = Field(..., description="The date when the PLO permit expires.")
    summary: str = Field(..., description="A brief summary of the PLO permit content.")

class PermitNumber(BaseModel):
    permit_type: Literal["PLO", "KKPR/KKPRL", "Ijin Lingkungan"] = Field(..., description="The type/category of the permit.")
    permit_number: List[str] = Field(..., description="The unique identifier for the permit.")

def base64_encoded_image(image, format: str = 'JPEG') -> str:
    """
    Generate a base64 encoded string from image object.
    
    Args:
        image: Image object (e.g., PIL.Image).
        
    Returns:
        str: Base64 encoded string of the image.
    """

    buffer = io.BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    encoded_str = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    image_data = f"data:image/{format.lower()};base64,{encoded_str}"

    return image_data

def create_message(system_prompt: str, image_content: List[Any], document_title:str = None) -> dict:
    """
    Create a message payload for the chat API.

    Args:
        system_prompt (str): The system prompt to include in the message.
        document_title (str): The title of the document being processed.
        image_content (List[Any]): The content to include in the message.

    Returns:
        dict: The message payload.
    """

    if document_title:
        text = f"Extract the metadata from the permit image with this title: {document_title}."
    else:
        text = "Extract the metadata from the permit image."

    message = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [
            {
                "type" : "text",
                "text": text
            }
            ]
        }
    ]

    for content in image_content:
        message[1]['content'].append({"type": "image_url", "image_url": {"url" : base64_encoded_image(content)}})

    return message

logging.basicConfig(level=logging.INFO)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    before_sleep=before_sleep_log(logging.getLogger(), logging.WARNING)
)
async def process_permit_metadata_async(file_path: str, max_pages: int = 12) -> PermitMetadata:
    loop = asyncio.get_event_loop()
    images = await loop.run_in_executor(
        None, 
        lambda: convert_from_path(file_path, first_page=1, last_page=max_pages)
    )
    message_payload = create_message(metadata_extraction_prompt, images)
    logging.info(f"Processing file: {file_path} with {len(images)} pages.")

    user, completion = await loop.run_in_executor(
        None,
        instructor_client.chat.completions.create_with_completion,
        message_payload,
        PermitMetadata
    )

    try:
        issue_date = datetime.strptime(user.issue_date, "%d %B %Y").strftime("%Y-%m-%d")
    except ValueError as e:
        logger.warning(f"Warning parsing issue date: {user.issue_date} in file {file_path}: {e}")
        issue_date = ""

    try:
        expiration_date = datetime.strptime(user.expiration_date, "%d %B %Y").strftime("%Y-%m-%d")
    except ValueError as e:
        logger.warning(f"Warning parsing expiration date: {user.expiration_date} in file {file_path}: {e}")
        expiration_date = ""

    return {
        "file_path": file_path,
        "issue_date": issue_date,
        "expiration_date": expiration_date,
        "permit_number": user.permit_number.replace(" ", ""),
        "permit_type": user.permit_type,
        "summary": user.summary,
        "usage": completion.usage
    }

async def process_permit_metadata_async_plo(file_path: str, start_page: int = 1, max_pages: int = 12) -> PLOMetadata:
    loop = asyncio.get_event_loop()
    images = await loop.run_in_executor(
        None, 
        lambda: convert_from_path(file_path, first_page=start_page, last_page=max_pages)
    )
    message_payload = create_message(metadata_extraction_prompt_plo, images)
    logging.info(f"Processing file: {file_path} with {len(images)} pages.")

    user, completion = await loop.run_in_executor(
        None,
        instructor_client.chat.completions.create_with_completion,
        message_payload,
        PLOMetadata
    )

    try:
        issue_date = datetime.strptime(user.issue_date, "%d %B %Y").strftime("%Y-%m-%d")
    except ValueError as e:
        logger.warning(f"Warning parsing issue date: {user.issue_date} in file {file_path}: {e}")
        issue_date = ""

    try:
        expiration_date = datetime.strptime(user.expiration_date, "%d %B %Y").strftime("%Y-%m-%d")
    except ValueError as e:
        logger.warning(f"Warning parsing expiration date: {user.expiration_date} in file {file_path}: {e}")
        expiration_date = ""

    return {
        "file_path": file_path,
        "issue_date": issue_date,
        "permit_number": user.plo_number.replace(" ", ""),
        "expiration_date": expiration_date,
        "permit_type": user.permit_type,
        "installation": user.installation,
        "summary": user.summary,
        "usage": completion.usage
    }

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    before_sleep=before_sleep_log(logging.getLogger(), logging.WARNING)
)
async def get_permit_number(doc_path:str) -> PermitNumber:
    loop = asyncio.get_event_loop()
    images = await loop.run_in_executor(None, convert_from_path, doc_path)
    message_payload = create_message(permit_number_extraction_prompt, doc_path, images[:1])

    user, completion = await loop.run_in_executor(
        None,
        instructor_client.chat.completions.create_with_completion,
        message_payload,
        PermitNumber
    )

    return {
        "filepath": doc_path,
        "permit_type": user.permit_type,
        "permit_number": user.permit_number,
        "usage": completion.usage
    }

def serialize_metadata(metadata_list):
    serialized = []
    for item in metadata_list:
        serialized_item = item.copy()
        if 'usage' in serialized_item and serialized_item['usage'] is not None:
            serialized_item['usage'] = serialized_item['usage'].model_dump()
        serialized.append(serialized_item)
    return serialized

def cleansing_plo_number(permit_number: List[str]) -> List[str]:
    """
    Cleansing PLO permit numbers to expand ranges and multiple entries.

    Args:
        permit_number (List[str]): List of permit numbers.
    """
    
    plo_numbers_found = []
    for item in permit_number:
        if "PLO" in item:
            plo_numbers_found.append(item)
        else:
            pass
    if len(plo_numbers_found) == 0:
        return []

    if len(plo_numbers_found) > 1:
        permit_last_number = "/".join(plo_numbers_found[0].split("/")[1:])
        start_number = int(plo_numbers_found[0].split("/")[0])
        end_number = int(plo_numbers_found[-1].split("/")[0])

        number_range = [f"{i:03d}" for i in range(start_number, end_number + 1)]
        result_string = ", ".join(number_range)
        plo_final_list = []
        for result in result_string.split(", "):
            plo_final_list.append("/".join([result, permit_last_number]))

        return plo_final_list

    elif "-" in plo_numbers_found[0].split("/")[0]:
        permit_last_number = "/".join(plo_numbers_found[0].split("/")[1:])
        start_number = int(plo_numbers_found[0].split("/")[0].split("-")[0])
        end_number = int(plo_numbers_found[0].split("/")[0].split("-")[1])

        number_range = [f"{i:03d}" for i in range(start_number, end_number + 1)]
        result_string = ", ".join(number_range)
        plo_final_list = []
        for result in result_string.split(", "):
            plo_final_list.append("/".join([result, permit_last_number]))

        return plo_final_list

    else:
        return plo_numbers_found

def map_keywords_to_pages(
    images: List[Image.Image], 
    anchor_keywords: List[str]
) -> Dict[str, List[int]]:
    """
    Maps each anchor keyword to the page indices where it appears.
    
    Args:
        images (List[Image.Image]): List of PIL Image objects.
        anchor_keywords (List[str]): List of keywords to search for.
    
    Returns:
        Dict[str, List[int]]: Dictionary mapping each keyword to list of page indices where it appears.
    """
    keyword_to_pages: Dict[str, List[int]] = {kw: [] for kw in anchor_keywords}

    max_images_to_inspect = len(anchor_keywords) * 20 # inspect up to 20 pages per keyword
    images_to_process = images[:max_images_to_inspect]
    
    for idx, img in enumerate(images_to_process):
        text: str = pytesseract.image_to_string(img)
        lines = list(map(lambda x: x.replace(" ", ""), text.split('\n')))
        
        for kw in anchor_keywords:
            if any(kw.lower() in line.lower() for line in lines):
                keyword_to_pages[kw].append(idx)
                logger.debug(f"Found '{kw}' on page {idx + 1}")
    
    return keyword_to_pages