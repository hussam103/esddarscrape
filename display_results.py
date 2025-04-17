import json
import datetime

def display_formatted_results():
    """Display the API results in a readable format"""
    
    # Load the results
    with open('api_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Print header
    print("=" * 100)
    print(f"VECTOR SEARCH RESULTS FOR QUERY: '{data['query']}'")
    print(f"Total results found: {data['count']}")
    print("=" * 100)
    print()
    
    # Print each tender with formatted information
    for i, item in enumerate(data['results'], 1):
        tender = item['tender']
        similarity = item['similarity']
        
        # Format the similarity score as a percentage
        similarity_pct = f"{similarity * 100:.1f}%"
        
        # Format submission deadline
        deadline = "Not specified"
        if tender.get('submission_deadline'):
            deadline_dt = datetime.datetime.fromisoformat(tender['submission_deadline'].replace('Z', '+00:00'))
            deadline = deadline_dt.strftime("%B %d, %Y")
        
        # Format price
        price = tender.get('price', 'Not specified')
        
        # Get tender details
        title = tender.get('tender_title', 'No title')
        org = tender.get('organization', 'Unknown organization')
        tender_type = tender.get('tender_type', 'Unknown type')
        ref_num = tender.get('reference_number', 'Not specified')
        
        # Print the tender information
        print(f"TENDER #{i} - SIMILARITY SCORE: {similarity_pct}")
        print(f"Title: {title}")
        print(f"Organization: {org}")
        print(f"Type: {tender_type}")
        print(f"Reference Number: {ref_num}")
        print(f"Submission Deadline: {deadline}")
        print(f"Price: {price}")
        print("-" * 100)
    
if __name__ == "__main__":
    display_formatted_results()