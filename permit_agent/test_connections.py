#!/usr/bin/env python3

import asyncio
import os
import sys
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))

from azure.cosmos import CosmosClient
from backend.azure_service_client.azure_ai_search import AzureAISearch
from backend.azure_service_client.azure_ai_search import MultiSourceSearch

# Load environment variables
load_dotenv()

async def test_cosmos_db_connection():
    """Test Cosmos DB connection and query"""
    print("=== Testing Cosmos DB Connection ===")
    
    try:
        # Initialize client
        cosmos_client = CosmosClient(
            url=os.getenv("COSMOS_DB_URI"),
            credential=os.getenv("COSMOS_DB_KEY")
        )
        
        database_id = "permitMetadataDB"
        container_id = "permitMetadataContainer"
        
        # Get database and container
        database = cosmos_client.get_database_client(database_id)
        container = database.get_container_client(container_id)
        
        print(f"✅ Cosmos DB client initialized")
        print(f"   URI: {os.getenv('COSMOS_DB_URI')}")
        print(f"   Database: {database_id}")
        print(f"   Container: {container_id}")
        
        # Test query
        query = "SELECT TOP 1 c.documentTitle, c.permitType FROM c"
        results = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if results:
            print(f"✅ Query successful - Found {len(results)} sample record(s)")
            print(f"   Sample: {results[0]}")
        else:
            print("⚠️  Query successful but no data found")
        
        return True
        
    except Exception as e:
        print(f"❌ Cosmos DB connection failed: {e}")
        return False

async def test_azure_search_connection():
    """Test Azure AI Search connections"""
    print("\n=== Testing Azure AI Search Connection ===")
    
    try:
        # Test main search client
        search_endpoint = f"https://{os.getenv('AZURE_SEARCH_SERVICE')}.search.windows.net"
        
        main_client = AzureAISearch(
            base_url=search_endpoint,
            api_key=os.getenv("AZURE_SEARCH_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX", "index_typea_cz_5000_co_500_prod_2")
        )
        
        print(f"✅ Main search client initialized")
        print(f"   Endpoint: {search_endpoint}")
        print(f"   Index: {os.getenv('AZURE_SEARCH_INDEX', 'index_typea_cz_5000_co_500_prod_2')}")
        
        # Test search query
        search_results = await main_client.semantic_ranking_search(
            keyword="PLO",
            k=1,
            select_fields=["title"]
        )
        
        if search_results.get('value'):
            print(f"✅ Search query successful - Found {len(search_results['value'])} result(s)")
            print(f"   Sample: {search_results['value'][0]}")
        else:
            print("⚠️  Search query successful but no results")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure AI Search connection failed: {e}")
        return False

async def test_multi_source_search():
    """Test multi-source search (title + content indexes)"""
    print("\n=== Testing Multi-Source Search ===")
    
    try:
        # Initialize multi-source client
        multi_client = MultiSourceSearch()
        
        print(f"✅ Multi-source client initialized")
        print(f"   Title Index: {os.getenv('AZURE_AI_SEARCH_TITLE_INDEX')}")
        print(f"   Content Index: {os.getenv('AZURE_AI_SEARCH_CONTENT_INDEX')}")
        
        # Test title search (distinct documents)
        print("\n--- Testing Title Search ---")
        distinct_docs = await multi_client.get_distinct_documents("PLO", k=3)
        
        if distinct_docs:
            print(f"✅ Title search successful - Found {len(distinct_docs)} distinct documents")
            print(f"   Documents: {distinct_docs[:3]}")
        else:
            print("⚠️  Title search returned no distinct documents")
        
        # Test content search with filtering
        print("\n--- Testing Content Search with Filtering ---")
        content_results = await multi_client.search_content_filtered(
            keyword="PLO",
            document_list=distinct_docs[:2] if distinct_docs else None,
            k=2
        )
        
        if content_results.get('value'):
            print(f"✅ Filtered content search successful - Found {len(content_results['value'])} result(s)")
            for i, result in enumerate(content_results['value'][:2]):
                print(f"   Result {i+1}: {result.get('title', 'No title')}")
        else:
            print("⚠️  Filtered content search returned no results")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-source search failed: {e}")
        return False

async def test_azure_openai_connection():
    """Test Azure OpenAI connection"""
    print("\n=== Testing Azure OpenAI Connection ===")
    
    try:
        from openai import OpenAI
        
        # Initialize OpenAI client
        client = OpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            base_url=f"{os.getenv('AZURE_OPENAI_ENDPOINT')}/openai/v1/",
        )
        
        print(f"✅ Azure OpenAI client initialized")
        print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"   Model: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')}")
        
        # Test simple completion
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            messages=[{"role": "user", "content": "Hello, test connection"}],
            max_tokens=10
        )
        
        if response.choices:
            print(f"✅ OpenAI API call successful")
            print(f"   Response: {response.choices[0].message.content}")
        else:
            print("⚠️  OpenAI API call successful but no response")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI connection failed: {e}")
        return False

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("\n=== Testing Environment Variables ===")
    
    required_vars = {
        "Cosmos DB": ["COSMOS_DB_URI", "COSMOS_DB_KEY"],
        "Azure Search": ["AZURE_SEARCH_SERVICE", "AZURE_SEARCH_KEY", "AZURE_AI_SEARCH_TITLE_INDEX", "AZURE_AI_SEARCH_CONTENT_INDEX"],
        "Azure OpenAI": ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT_NAME"]
    }
    
    all_good = True
    
    for service, vars_list in required_vars.items():
        print(f"\n--- {service} Variables ---")
        for var in vars_list:
            value = os.getenv(var)
            if value:
                masked_value = value[:10] + "..." if len(value) > 10 else value
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"❌ {var}: Not set")
                all_good = False
    
    return all_good

def test_query_classification():
    """Test query classification logic"""
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
        ("Apa isi dokumen KKPRL untuk terminal Lawe-Lawe?", "content_search"),
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
    """Run all connection tests"""
    print("🚀 Starting Comprehensive Connection Tests")
    print("=" * 60)
    
    # Test 1: Environment Variables
    env_ok = test_environment_variables()
    
    # Test 2: Query Classification
    classification_ok = test_query_classification()
    
    # Test 3: Cosmos DB
    cosmos_ok = await test_cosmos_db_connection()
    
    # Test 4: Azure AI Search
    search_ok = await test_azure_search_connection()
    
    # Test 5: Multi-Source Search
    multi_search_ok = await test_multi_source_search()
    
    # Test 6: Azure OpenAI
    openai_ok = await test_azure_openai_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 CONNECTION TEST SUMMARY:")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", env_ok),
        ("Query Classification", classification_ok),
        ("Cosmos DB", cosmos_ok),
        ("Azure AI Search", search_ok),
        ("Multi-Source Search", multi_search_ok),
        ("Azure OpenAI", openai_ok)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL CONNECTIONS SUCCESSFUL! Agent is ready for production.")
    else:
        print("⚠️  Some connections failed. Check configuration and network connectivity.")
    
    return passed == len(tests)

if __name__ == "__main__":
    print("🔧 Permit Agent - Connection Test Suite")
    print("Testing all data source connections...\n")
    
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite failed with error: {e}")
        sys.exit(1)
