# EVA Pharma Career Assistant

A sophisticated AI-powered career assistant built with LangGraph, Google Gemini, and advanced RAG architecture to help users explore job opportunities at EVA Pharma. The system combines intelligent web scraping, vector-based retrieval, and conversational AI to provide personalized career guidance.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Client Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  Streamlit UI          │         Flask API                      │
│  (streamlit_app.py)    │      (main.py)                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Layer                                  │
├─────────────────────────────────────────────────────────────────┤
│              LangGraph Multi-Agent System                       │
│              (agents/langgraph_agent.py)                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Agent     │  │    Tools    │  │     RAG     │              │
│  │   Node      │  │    Node     │  │  Retrieval  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Tool & Service Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  Job Comparison │ Career Summary │ Location Filter │ RAG Query  │
│ (compare_jobs)  │(summarize_career)│(location_filter)│(retrieve)│
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                   │
├─────────────────────────────────────────────────────────────────┤
│  Vector Store    │    Job Database    │    LLM Services         │
│  (Chroma DB)     │    (jobs.json)     │  (Google Gemini)        │
└─────────────────────────────────────────────────────────────────┘
```

## LLM & Model Architecture

### Primary Language Model
- **Model**: Google Gemini 2.0 Flash (`gemini-2.0-flash`)
- **Provider**: Google Generative AI
- **Temperature**: 0 (deterministic responses)
- **Integration**: LangChain Google GenAI wrapper

### Embedding Model
- **Model**: `models/embedding-001` (Google)
- **Purpose**: Vector embeddings for RAG retrieval
- **Dimensions**: 768-dimensional vectors
- **Use Case**: Semantic similarity search in job database

## Agent System (LangGraph)

### Agent Architecture

The system uses **LangGraph** for building a sophisticated multi-node agent workflow:

#### Core Nodes

1. **Agent Node** (`call_model`):
   - Primary decision-making node
   - Handles LLM invocation with tools
   - Processes user queries and tool responses
   - Generates final responses

2. **Tools Node** (`handle_tools`):
   - Executes function calls
   - Handles tool result processing
   - Manages tool error handling

3. **RAG Retrieval Node** (`rag_retrieval_node`):
   - Contextual information retrieval
   - Vector similarity search
   - Context injection for enhanced responses

#### State Management
- **Messages**: Conversation history with role-based structure
- **RAG Context**: Retrieved job information for context-aware responses
- **Checkpointer**: InMemorySaver for session persistence


## Tool System

### Available Tools

#### 1. `retrieve_jobs`
- **Purpose**: Targeted job search based on specific queries
- **Use Case**: Skills, departments, or role-specific searches
- **Retrieval**: Top 5 relevant documents

#### 2. `list_all_jobs`
- **Purpose**: Comprehensive job listing
- **Strategy**: Multiple broad queries to capture all positions
- **Deduplication**: Job ID-based uniqueness
- **Coverage**: All 42+ available positions

#### 3. `compare_jobs_tool`
- **Purpose**: Side-by-side job comparison
- **Input**: Two job titles (various formats supported)
- **Processing**: 
  - Title parsing and validation
  - Comprehensive information gathering
  - Structured comparison generation
- **Output**: Detailed comparison analysis

#### 4. `summarize_career_tool`
- **Purpose**: Career path and growth analysis
- **Features**:
  - Progression paths
  - Skills development
  - Industry outlook
  - Next-role recommendations

#### 5. `location_filter_tool`
- **Purpose**: Geographic job filtering
- **Capability**: Location-based job matching
- **Flexibility**: Handles various location formats


## RAG (Retrieval-Augmented Generation) System

### Vector Database Architecture

#### Technology Stack
- **Vector Store**: Chroma DB
- **Embeddings**: Google Generative AI Embeddings
- **Persistence**: Local file system (`data/embeddings/chroma_db`)

#### Similarity Calculation

Custom similarity deduplication:
- **Threshold**: 0.8 similarity for deduplication
- **Algorithm**: Jaccard similarity (intersection/union)
- **Purpose**: Prevent duplicate job listings in results

### Retrieval Strategy

#### Query Processing
1. **User Query Analysis**: Intent detection and keyword extraction
2. **Vector Search**: Semantic similarity matching
3. **Result Filtering**: Deduplication and relevance scoring
4. **Context Injection**: Retrieved information added to prompt

#### Optimization Techniques
- **K-value Tuning**: Retrieve 2×k candidates, filter to k results
- **Multi-query Expansion**: Broad queries for comprehensive coverage
- **Content Prioritization**: Job-specific matches ranked higher

## Web Scraping System

- **Framework**: Selenium WebDriver
- **Total Jobs Scraped**: 42 positions
- **Data Format**: JSON output

## Voice Output Feature (TTS)

The application includes a text-to-speech capability using the Web Speech API:

- **Technology**: Browser's built-in Web Speech API


## API Layer

### Flask Application Architecture

#### Endpoint Design

**Primary Endpoint**: `POST /query`


**Request**:
```json
{
  "query": "What jobs are available in Cairo?"
}
```

**Response**:
```json
{
  "response": "Here are the available positions in Cairo..."
}

```

## User Interface

#### Streamlit Application


## File Organization

```
project/
├── agents/
│   └── langgraph_agent.py      # Core agent logic
├── tools/
│   ├── compare_jobs.py         # Job comparison tool
│   ├── location_filter.py      # Location filtering
│   ├── rag_retriever.py        # RAG system
│   └── summarize_career.py     # Career summarization
├── data/
│   ├── jobs.json              # Job database
│   └── embeddings/
│       └── chroma_db/         # Vector store
├── main.py                    # Flask API
├── streamlit_app.py          # UI application
├── scraping.py               # Web scraper
└── requirements.txt          # Dependencies
```


## Environment Setup

#### Development
```bash
pip install -r requirements.txt
export GOOGLE_API_KEY="your-api-key"
python main.py  
streamlit run streamlit_app.py  
```

