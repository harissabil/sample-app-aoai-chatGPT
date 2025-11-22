"""
Utility functions for LangChain message filtering and conversion.
These utilities help filter out tool messages and system plumbing from React agent outputs.
"""

from typing import Iterable
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_core.messages import BaseMessage, ToolMessage


def convert_message(msg: BaseMessage) -> dict:
    """
    Convert a LangChain BaseMessage to a dictionary format for the frontend.

    Args:
        msg: A LangChain message object

    Returns:
        A dictionary with 'role' and 'content' keys

    Raises:
        ValueError: If the message type is not supported
    """
    if isinstance(msg, HumanMessage):
        return {"role": "user", "content": msg.content}
    elif isinstance(msg, AIMessage):
        return {"role": "assistant", "content": msg.content}
    elif isinstance(msg, SystemMessage):
        return {"role": "system", "content": msg.content}
    else:
        raise ValueError(f"Unsupported message type: {type(msg)}")


def is_public(msg: BaseMessage) -> bool:
    """
    Determine if a message should be shown to the frontend.

    Hide tool plumbing:
    - Any ToolMessage
    - Any AIMessage that only carries tool_calls and has empty content
    - Any AIMessage with None or empty content

    Args:
        msg: A LangChain message object

    Returns:
        True if the message should be shown to the user, False otherwise
    """
    if isinstance(msg, ToolMessage):
        return False

    # Filter out AI messages with no meaningful content
    if isinstance(msg, AIMessage):
        # If content is None or empty string, check if there are tool_calls
        if not msg.content:
            # If there are tool_calls, it's just plumbing
            if getattr(msg, "tool_calls", None):
                return False
            # If no content and no tool_calls, also filter it out (incomplete message)
            return False
        # AI message has content, it's public
        return True

    return isinstance(msg, (HumanMessage, SystemMessage))


def to_public_messages(messages: Iterable[BaseMessage]) -> list[dict]:
    """
    Convert LangChain messages to public format, filtering out tool messages.

    Args:
        messages: An iterable of LangChain message objects

    Returns:
        A list of message dictionaries safe to send to the frontend
    """
    return [convert_message(m) for m in messages if is_public(m)]

