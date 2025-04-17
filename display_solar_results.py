import json

def display_solar_results():
    # Load the results
    with open('solar_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Print header
    print("=" * 100)
    print(f"VECTOR SEARCH RESULTS FOR QUERY: '{data['query']}'")
    print(f"Total results found: {data['count']}")
    print("=" * 100)
    print()
    
    # Print each tender with similarity score
    for i, item in enumerate(data['results'], 1):
        tender = item['tender']
        similarity = item['similarity']
        
        # Format the similarity score as a percentage
        similarity_pct = f"{similarity * 100:.1f}%"
        
        # Get tender details
        title = tender.get('tender_title', 'No title')
        org = tender.get('organization', 'Unknown organization')
        
        # Print the tender information
        print(f"{i}. {title}")
        print(f"   Organization: {org}")
        print(f"   Similarity Score: {similarity_pct}")
        print()

if __name__ == "__main__":
    display_solar_results()