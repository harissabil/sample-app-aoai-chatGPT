import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.permit_agent.agent_langchain import agent, classify_query_intent
from dotenv import load_dotenv

load_dotenv()

async def test_time_calculation_query():
    """Test query that should use Cosmos DB for time calculation"""
    print("=== Testing Time Calculation Query ===")
    
    query = "Dokumen apa saja yang sudah expired?"
    print(f"Query: {query}")
    
    # Test classification
    intent = classify_query_intent.func(query)
    print(f"Classified as: {intent}")
    
    try:
        response = await agent.ainvoke({
            "messages": [{"role": "user", "content": query}]
        })
        print(f"Response: {response['messages'][-1]['content']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")

async def test_content_search_query():
    """Test query that should use AI Search with improved flow"""
    print("=== Testing Content Search Query ===")
    
    query = "Berapa panjang submarine pipeline yang ada di IT Semarang?"
    print(f"Query: {query}")
    
    # Test classification
    intent = classify_query_intent.func(query)
    print(f"Classified as: {intent}")
    
    try:
        response = await agent.ainvoke({
            "messages": [{"role": "user", "content": query}]
        })
        print(f"Response: {response['messages'][-1]['content']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")

async def test_mixed_query():
    """Test query that might need both sources"""
    print("=== Testing Mixed Query ===")
    
    query = "Berapa lama lagi masa berlaku PLO untuk IT Jakarta?"
    print(f"Query: {query}")
    
    # Test classification
    intent = classify_query_intent.func(query)
    print(f"Classified as: {intent}")
    
    try:
        response = await agent.ainvoke({
            "messages": [{"role": "user", "content": query}]
        })
        print(f"Response: {response['messages'][-1]['content']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")

async def main():
    """Run all tests"""
    print("Starting Agent Tests with Improved Retrieval Flow\n")
    
    await test_time_calculation_query()
    await test_content_search_query()
    await test_mixed_query()
    
    print("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
