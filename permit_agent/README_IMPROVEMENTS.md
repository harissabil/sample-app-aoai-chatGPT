# Permit Agent Improvements

## Objective Implementation

Mengubah flow retrieval answer dari Chatbot sesuai dengan requirement:

1. **Time Calculation Queries** → Cosmos DB
2. **Content Search Queries** → AI Search dengan filtering berdasarkan distinct documents

## Changes Made

### 1. Enhanced Backend (`backend.py`)

**New Features:**
- Added `filter_expression` parameter to `semantic_ranking_search()`
- New `MultiSourceSearch` class for handling multiple data sources
- Methods:
  - `get_distinct_documents()` - Get distinct documents from title index
  - `search_content_filtered()` - Search content with document filtering

### 2. Improved Agent (`agent_langchain.py`)

**New Tools:**
- `classify_query_intent()` - Classify queries as time_calculation or content_search

**Enhanced Flow:**
- `get_permit_document_content()` now uses improved retrieval:
  1. Get distinct documents from AI Search Title index
  2. Filter content search based on distinct documents
  3. Fallback to original search if needed

### 3. Environment Variables

**New Variables Added:**
```env
# Multi-source AI Search indexes
AZURE_AI_SEARCH_TITLE_INDEX=ai_search_title_index
AZURE_AI_SEARCH_CONTENT_INDEX=ai_search_content_index

# Agent-specific settings
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_API_VERSION=2024-02-01

# Cosmos DB for metadata
COSMOS_DB_URI=your_cosmos_uri
COSMOS_DB_KEY=your_cosmos_key
```

## Data Sources Architecture

### 1. Cosmos DB
- **Purpose**: Metadata storage for time calculations
- **Used for**: Expired documents, issue dates, expiration dates
- **Tools**: `get_list_documents_already_expired`, `get_current_date`, `get_time_difference`

### 2. AI Search Title Index
- **Purpose**: Store document titles for distinct document filtering
- **Fields**: `title`, `filepath`
- **Used for**: Getting list of relevant documents before content search

### 3. AI Search Content Index  
- **Purpose**: Store full document content
- **Fields**: `title`, `content`, `filepath`
- **Used for**: Detailed content search with document filtering

## Query Flow

### Time Calculation Queries
```
User Query: "Dokumen apa saja yang sudah expired?"
↓
classify_query_intent() → "time_calculation"
↓
get_list_documents_already_expired() → Cosmos DB
↓
Return results with current date calculations
```

### Content Search Queries
```
User Query: "Berapa panjang pipeline di IT Semarang?"
↓
classify_query_intent() → "content_search"
↓
get_distinct_documents() → AI Search Title Index
↓
search_content_filtered() → AI Search Content Index (filtered)
↓
Return filtered content results
```

## Testing

Run the test file to verify functionality:

```bash
cd permit_agent
python test_agent.py
```

**Test Cases:**
1. Time calculation query (should use Cosmos DB)
2. Content search query (should use filtered AI Search)
3. Mixed query (should use appropriate tools)

## Next Steps

1. **Create AI Search Indexes**: Set up separate title and content indexes
2. **Data Migration**: Populate the new indexes with appropriate data
3. **Integration**: Connect with main app.py when ready
4. **Monitoring**: Add logging and metrics for the new flow

## Benefits

- **Better Accuracy**: Distinct document filtering reduces noise
- **Appropriate Data Source**: Time queries use precise Cosmos DB data
- **Scalable**: Modular design allows easy extension
- **Fallback**: Graceful degradation if new indexes not available
