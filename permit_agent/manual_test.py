#!/usr/bin/env python3

def classify_query_intent(user_query: str) -> str:
    """Classify if query needs time calculation or content search"""
    time_keywords = ["expired", "kedaluwarsa", "berapa lama", "sudah berapa", "waktu", "tanggal", "masa berlaku", "habis"]
    if any(keyword in user_query.lower() for keyword in time_keywords):
        return "time_calculation"
    return "content_search"

def main():
    print("=== Manual Query Classification Test ===")
    print("Ketik query Anda, atau 'quit' untuk keluar\n")
    
    while True:
        query = input("Query: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
            
        if not query:
            continue
            
        result = classify_query_intent(query)
        
        if result == "time_calculation":
            print(f"🕒 ROUTE: Cosmos DB (Time Calculation)")
            print("   Tools: get_current_date, get_time_difference, get_list_documents_already_expired")
        else:
            print(f"📄 ROUTE: AI Search (Content Search)")  
            print("   Flow: Title search → Distinct docs → Filtered content search")
        
        print()

if __name__ == "__main__":
    main()
