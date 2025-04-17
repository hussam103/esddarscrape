# Vector Search API Documentation

## Overview

The Vector Search API provides semantic search functionality to find tenders that are conceptually similar to a text query. The API uses OpenAI embeddings to convert text into vector representations and performs cosine similarity searches against tender data in the database.

## Endpoint

```
GET /api/vector-search
```

## Parameters

| Parameter    | Type    | Required | Default | Description                                                                                                        |
|--------------|---------|----------|---------|--------------------------------------------------------------------------------------------------------------------|
| query        | string  | Yes      | -       | The text query to search for. This can be a question, description, or any text to match against tender content.    |
| limit        | integer | No       | 10      | The maximum number of results to return.                                                                           |
| today_only   | boolean | No       | false   | If set to "true", only tenders published within the last 24 hours will be included in the search results.          |

## Response Format

The API returns a JSON object with the following structure:

```json
{
  "query": "original query text",
  "results": [
    {
      "tender": {
        "id": 123,
        "tender_id": "tender-unique-id",
        "reference_number": "REF-12345",
        "publication_date": "2025-04-15T10:00:00+03:00",
        "tender_type": "Type of tender",
        "tender_title": "Title of the tender",
        "organization": "Organization name",
        "tender_url": "https://tenders.etimad.sa/Tender/DetaielsForVisitors?StenderID=unique-id",
        "main_activities": "Description of main activities",
        "duration": "6 months",
        "inquiry_deadline": "2025-04-20T15:00:00+03:00",
        "submission_deadline": "2025-04-30T15:00:00+03:00",
        "opening_date": "2025-05-01T10:00:00+03:00",
        "city": "City name",
        "price": "100,000 SAR",
        "created_at": "2025-04-15T08:30:00+03:00",
        "updated_at": "2025-04-15T08:30:00+03:00"
      },
      "similarity": 0.92
    },
    // More results...
  ],
  "count": 10,
  "today_only": false
}
```

## Response Fields

| Field          | Type          | Description                                                                                                      |
|----------------|---------------|------------------------------------------------------------------------------------------------------------------|
| query          | string        | The original query text submitted.                                                                                |
| results        | array         | Array of tender objects sorted by similarity (most similar first).                                               |
| results[].tender | object      | The tender object containing all tender details.                                                                  |
| results[].similarity | number  | A similarity score between 0 and 1, where 1 is an exact match. Typically ranges from 0.65 to 0.95 for good matches. |
| count          | integer       | The number of results returned.                                                                                  |
| today_only     | boolean       | Indicates whether the results were filtered to show only tenders from the last 24 hours.                         |

## Similarity Score

The similarity score is a value between 0 and 1:
- 0.90-1.00: Excellent match (very high relevance)
- 0.85-0.90: Good match (high relevance)
- 0.80-0.85: Moderate match (relevant)
- 0.75-0.80: Fair match (somewhat relevant)
- <0.75: Poor match (low relevance)

The API returns raw similarity scores without any buffering or normalization, providing authentic confidence values.

## Notes

1. The API only returns tenders with active submission deadlines (future deadlines or no deadline specified).
2. Vector embeddings are created using OpenAI's text-embedding-3-large model with 3072 dimensions.
3. The search takes into account the tender title, organization name, and main activities.
4. All dates are returned in Saudi Arabia time (GMT+3).

## Example Usage

### cURL

```bash
# Replace with your actual domain name
curl "https://etimad-tenders.yourdomain.repl.co/api/vector-search?query=solar%20power%20projects%20in%20Riyadh&limit=5&today_only=true"
```

### Python

```python
import requests

# Replace with your actual domain name
BASE_URL = "https://etimad-tenders.yourdomain.repl.co"

response = requests.get(
    f"{BASE_URL}/api/vector-search",
    params={
        "query": "solar power projects in Riyadh",
        "limit": 5,
        "today_only": "true"
    }
)

results = response.json()
for item in results["results"]:
    print(f"Title: {item['tender']['tender_title']}")
    print(f"Organization: {item['tender']['organization']}")
    print(f"Similarity: {item['similarity']:.2f}")
    print("---")
```

### JavaScript (Browser)

```javascript
// Replace with your actual domain name
const BASE_URL = "https://etimad-tenders.yourdomain.repl.co";

fetch(`${BASE_URL}/api/vector-search?query=solar power projects in Riyadh&limit=5&today_only=true`)
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.count} matches`);
    data.results.forEach(item => {
      console.log(`Title: ${item.tender.tender_title}`);
      console.log(`Organization: ${item.tender.organization}`);
      console.log(`Similarity: ${item.similarity.toFixed(2)}`);
      console.log('---');
    });
  })
  .catch(error => console.error('Error:', error));
```

### Node.js

```javascript
const axios = require('axios');

// Replace with your actual domain name
const BASE_URL = "https://etimad-tenders.yourdomain.repl.co";

axios.get(`${BASE_URL}/api/vector-search`, {
  params: {
    query: 'solar power projects in Riyadh',
    limit: 5,
    today_only: true
  }
})
.then(response => {
  const data = response.data;
  console.log(`Found ${data.count} matches`);
  data.results.forEach(item => {
    console.log(`Title: ${item.tender.tender_title}`);
    console.log(`Organization: ${item.tender.organization}`);
    console.log(`Similarity: ${item.similarity.toFixed(2)}`);
    console.log('---');
  });
})
.catch(error => console.error('Error:', error));
```

## Error Responses

| Status Code | Description                                                           |
|-------------|-----------------------------------------------------------------------|
| 400         | Bad Request - Required parameters are missing or invalid               |
| 500         | Internal Server Error - Something went wrong on the server             |

Error responses will have the following format:

```json
{
  "error": "Error message"
}
```