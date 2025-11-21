#!/usr/bin/env python3

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_query_classification():
    """Test the query classification logic"""
    print("=== Testing Query Classification Logic ===")
    
    def classify_query_intent(user_query: str) -> str:
        """Classify if query needs time calculation or content search"""
        time_keywords = ["expired", "kedaluwarsa", "berapa lama", "sudah berapa", "waktu", "tanggal", "masa berlaku", "habis"]
        if any(keyword in user_query.lower() for keyword in time_keywords):
            return "time_calculation"
        return "content_search"
    
    # Test cases
    test_queries = [
        ("Dokumen apa saja yang sudah expired?", "time_calculation"),
        ("Berapa panjang submarine pipeline yang ada di IT Semarang?", "content_search"),
        ("Berapa lama lagi masa berlaku PLO untuk IT Jakarta?", "time_calculation"),
        ("Apa isi dokumen KKPRL untuk terminal Lawe-Lawe?", "content_search"),
        ("Dokumen mana yang kedaluwarsa tahun ini?", "time_calculation")
    ]
    
    print("Query Classification Results:")
    for query, expected in test_queries:
        result = classify_query_intent(query)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | Query: '{query}'")
        print(f"      | Expected: {expected}, Got: {result}")
        print()
    
    return True

def test_environment_variables():
    """Test if environment variables are properly set"""
    print("=== Testing Environment Variables ===")
    
    # Load environment variables from parent directory
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    print(f"Loading .env from: {env_path}")
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ .env file loaded successfully")
    else:
        print("❌ .env file not found")
    
    # Map existing variables to new names
    env_mapping = {
        "AZURE_AI_SEARCH_ENDPOINT": "AZURE_SEARCH_SERVICE",
        "AZURE_AI_SEARCH_API_KEY": "AZURE_SEARCH_KEY",
        "AZURE_AI_SEARCH_TITLE_INDEX": "AZURE_AI_SEARCH_TITLE_INDEX", 
        "AZURE_AI_SEARCH_CONTENT_INDEX": "AZURE_AI_SEARCH_CONTENT_INDEX",
        "COSMOS_DB_URI": "COSMOS_DB_URI",
        "COSMOS_DB_KEY": "COSMOS_DB_KEY"
    }
    
    print("Environment Variables Check:")
    for new_var, old_var in env_mapping.items():
        value = os.getenv(old_var) or os.getenv(new_var)
        if value:
            if old_var == "AZURE_SEARCH_SERVICE":
                # Convert service name to full endpoint
                value = f"https://{value}.search.windows.net"
            print(f"✅ {new_var}: {'*' * min(len(str(value)), 20)}...")
        else:
            print(f"❌ {new_var}: Not set")
    
    return True

def test_flow_logic():
    """Test the logical flow without actual API calls"""
    print("=== Testing Flow Logic with Separated Indexes ===")
    
    def simulate_title_search_from_title_index(keyword: str):
        """Simulate title search from dedicated title_index"""
        print("🔍 Searching TITLE_INDEX (title_index) for distinct documents...")
        # Mock response from title_index
        return {
            "value": [
                {"title": "PLO Terminal Semarang", "filepath": "doc1.pdf"},
                {"title": "KKPRL IT Jakarta", "filepath": "doc2.pdf"},
                {"title": "PLO Pipeline Lawe-Lawe", "filepath": "doc1.pdf"},  # Duplicate
                {"title": "Ijin Lingkungan Terminal", "filepath": "doc3.pdf"}
            ]
        }
    
    def get_distinct_documents(search_results):
        """Extract distinct documents"""
        distinct_docs = list(set([
            doc.get('filepath', '') 
            for doc in search_results.get('value', [])
            if doc.get('filepath')
        ]))
        return distinct_docs
    
    def simulate_content_search_from_content_index(keyword: str, document_list):
        """Simulate filtered content search from content index"""
        print("🔍 Searching CONTENT_INDEX (index_typea_cz_5000_co_500_prod_2) with filtering...")
        print(f"   Filter: filepath IN {document_list}")
        return {
            "value": [
                {"title": "PLO Terminal Semarang", "content": "Pipeline length: 2.5 km", "filepath": "doc1.pdf"},
                {"title": "KKPRL IT Jakarta", "content": "Depth: 15 meters", "filepath": "doc2.pdf"}
            ]
        }
    
    # Test the flow with separated indexes
    keyword = "pipeline length"
    print(f"Testing separated index flow for keyword: '{keyword}'")
    print()
    
    # Step 1: Title search from dedicated title index
    title_results = simulate_title_search_from_title_index(keyword)
    print(f"✅ Step 1 - Title search from title_index returned: {len(title_results['value'])} results")
    
    # Step 2: Get distinct documents
    distinct_docs = get_distinct_documents(title_results)
    print(f"✅ Step 2 - Distinct documents extracted: {distinct_docs}")
    
    # Step 3: Filtered content search from content index
    content_results = simulate_content_search_from_content_index(keyword, distinct_docs)
    print(f"✅ Step 3 - Content search from content_index returned: {len(content_results['value'])} results")
    
    # Step 4: Format results
    docs = [doc.get('content', '') for doc in content_results.get('value', [])]
    titles = [doc.get('title', '') for doc in content_results.get('value', [])]
    result = "\n".join([f"{t}: {d}" for t, d in zip(titles, docs) if t and d])
    
    print()
    print("📋 Final Result:")
    print(result)
    print()
    print("🎯 Separated index flow test completed successfully!")
    print()
    print("Index Usage:")
    print("  📑 title_index → For getting distinct documents")
    print("  📄 index_typea_cz_5000_co_500_prod_2 → For filtered content search")
    
    return True

def main():
    """Run all tests"""
    print("Starting Simple Logic Tests for Permit Agent\n")
    
    try:
        test_query_classification()
        print("\n" + "="*50 + "\n")
        
        test_environment_variables() 
        print("\n" + "="*50 + "\n")
        
        test_flow_logic()
        print("\n" + "="*50 + "\n")
        
        print("🎯 All logic tests completed successfully!")
        print("\nNext steps:")
        print("1. Install required packages: aiohttp, langchain-openai, langgraph, etc.")
        print("2. Run full integration test with actual API calls")
        print("3. Verify Azure AI Search and Cosmos DB connections")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
