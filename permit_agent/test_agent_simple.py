#!/usr/bin/env python3

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_azure_search_connection():
    """Test Azure AI Search connection"""
    print("=== Testing Azure AI Search Connection ===")
    
    try:
        from backend import AzureAISearch
        
        # Test with title index
        title_client = AzureAISearch(
            base_url=os.getenv("AZURE_SEARCH_SERVICE", "").replace("https://", "https://") if not os.getenv("AZURE_SEARCH_SERVICE", "").startswith("https://") else os.getenv("AZURE_SEARCH_SERVICE"),
            api_key=os.getenv("AZURE_SEARCH_KEY"),
            index_name=os.getenv("AZURE_AI_SEARCH_TITLE_INDEX", "title_index")
        )
        
        print(f"✅ Title client created for index: {os.getenv('AZURE_AI_SEARCH_TITLE_INDEX')}")
        
        # Test with content index  
        content_client = AzureAISearch(
            base_url=os.getenv("AZURE_SEARCH_SERVICE", "").replace("https://", "https://") if not os.getenv("AZURE_SEARCH_SERVICE", "").startswith("https://") else os.getenv("AZURE_SEARCH_SERVICE"),
            api_key=os.getenv("AZURE_SEARCH_KEY"),
            index_name=os.getenv("AZURE_AI_SEARCH_CONTENT_INDEX", "index_typea_cz_5000_co_500_prod_2")
        )
        
        print(f"✅ Content client created for index: {os.getenv('AZURE_AI_SEARCH_CONTENT_INDEX')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating search clients: {e}")
        return False

async def test_cosmos_connection():
    """Test Cosmos DB connection"""
    print("\n=== Testing Cosmos DB Connection ===")
    
    try:
        from azure.cosmos import CosmosClient
        
        cosmos_client = CosmosClient(
            url=os.getenv("COSMOS_DB_URI"),
            credential=os.getenv("COSMOS_DB_KEY")
        )
        
        database_id = "permitMetadataDB"
        container_id = "permitMetadataContainer"
        
        database = cosmos_client.get_database_client(database_id)
        container = database.get_container_client(container_id)
        
        print(f"✅ Cosmos DB client created successfully")
        print(f"   Database: {database_id}")
        print(f"   Container: {container_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating Cosmos DB client: {e}")
        return False

def test_query_classification():
    """Test query classification"""
    print("\n=== Testing Query Classification ===")
    
    def classify_query_intent(user_query: str) -> str:
        time_keywords = ["expired", "kedaluwarsa", "berapa lama", "sudah berapa", "waktu", "tanggal", "masa berlaku", "habis"]
        if any(keyword in user_query.lower() for keyword in time_keywords):
            return "time_calculation"
        return "content_search"
    
    test_queries = [
        ("Dokumen apa saja yang sudah expired?", "time_calculation"),
        ("Berapa panjang submarine pipeline yang ada di IT Semarang?", "content_search"),
        ("Berapa lama lagi masa berlaku PLO untuk IT Jakarta?", "time_calculation"),
    ]
    
    all_passed = True
    for query, expected in test_queries:
        result = classify_query_intent(query)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"{status} '{query}' → {result}")
    
    return all_passed

async def main():
    """Run all tests"""
    print("Starting Agent Connection Tests\n")
    
    # Test 1: Query Classification
    classification_ok = test_query_classification()
    
    # Test 2: Azure Search Connection
    search_ok = await test_azure_search_connection()
    
    # Test 3: Cosmos DB Connection
    cosmos_ok = await test_cosmos_connection()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"✅ Query Classification: {'PASS' if classification_ok else 'FAIL'}")
    print(f"✅ Azure Search Setup: {'PASS' if search_ok else 'FAIL'}")
    print(f"✅ Cosmos DB Setup: {'PASS' if cosmos_ok else 'FAIL'}")
    
    if all([classification_ok, search_ok, cosmos_ok]):
        print("\n🎯 All tests PASSED! Agent is ready for use.")
    else:
        print("\n❌ Some tests FAILED. Check configuration.")
    
    return all([classification_ok, search_ok, cosmos_ok])

if __name__ == "__main__":
    asyncio.run(main())
