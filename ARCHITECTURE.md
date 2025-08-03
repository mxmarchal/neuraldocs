# Neuraldocs Architecture

## Overview

Neuraldocs is a Retrieval-Augmented Generation (RAG) system for web articles, built as a distributed microservices architecture using Docker containers. The system ingests web articles, processes them with OpenAI models, stores structured data and embeddings, and provides intelligent query capabilities.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │────│   FastAPI API   │────│   RQ Worker     │
│                 │    │   (Port 8000)   │    │   (Background)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              │                        │
            ┌─────────────────┼────────────────────────┼─────────────────┐
            │                 │                        │                 │
            ▼                 ▼                        ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │  MongoDB    │   │   Redis     │   │  ChromaDB   │   │  OpenAI     │
    │ (Port 27018)│   │ (Port 6379) │   │ (Port 8001) │   │    API      │
    │ Documents   │   │ Task Queue  │   │ Vectors     │   │ Processing  │
    └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
```

## Core Components

### 1. FastAPI Application (`app/main.py`)

**Purpose**: REST API server handling client requests and serving a simple web interface.

**Key Responsibilities**:
- Accepts URL ingestion requests
- Processes RAG queries with vector similarity search
- Provides task status monitoring
- Serves system statistics and document listing
- Hosts simple HTML frontend

**Key Endpoints**:
- `POST /add-url`: Queue article processing
- `GET /tasks/{task_id}`: Check processing status
- `POST /query`: Perform RAG queries
- `GET /stats`: System statistics
- `GET /documents`: List stored articles

### 2. Background Worker (`tasks.py`)

**Purpose**: Asynchronous processing of web articles using RQ (Redis Queue).

**Processing Pipeline**:
1. **Fetching**: Download article content via `httpx`
2. **Extraction**: Extract text using `trafilatura`
3. **Structuring**: Generate JSON structure via OpenAI GPT-4.1-nano
4. **Storage**: Store structured data in MongoDB
5. **Embedding**: Generate text embeddings using `sentence-transformers`
6. **Indexing**: Store vectors in ChromaDB for similarity search

**Key Function**: `process_url(url: str)` - Complete article processing workflow

### 3. Configuration System (`config.py`)

**Purpose**: Centralized configuration management using Pydantic settings.

**Configuration Sources**:
- Environment variables
- `.env` file
- Default values

**Key Settings**:
- Database connection parameters
- OpenAI API configuration
- Model selection (embedding, structuring, RAG)
- Default query parameters

### 4. Database Layer (`db.py`)

**Purpose**: Database client initialization and connection management.

**Connections**:
- **MongoDB**: Document metadata and structured content (`mongo_client`)
- **ChromaDB**: Vector storage and similarity search (`chroma_client`)
- **Redis**: Task queue backend accessed via RQ (`redis_conn` in main.py)

**Note**: `db.py` contains an unused `redis_client` - Redis is only accessed through RQ's queue connection.

## Data Flow

### Ingestion Flow
```
URL → httpx → trafilatura → OpenAI → MongoDB
                ↓
    sentence-transformers → ChromaDB
```

1. **URL Submission**: Client submits article URL via REST API
2. **Task Queuing**: URL processing task queued in Redis
3. **Content Fetching**: Worker downloads and extracts article text
4. **AI Processing**: OpenAI structures content into JSON format
5. **Document Storage**: Structured data stored in MongoDB with unique ID
6. **Embedding Generation**: Text chunks processed by local transformer model
7. **Vector Storage**: Embeddings stored in ChromaDB with metadata references

### Query Flow
```
Question → sentence-transformers → ChromaDB → MongoDB → OpenAI → Answer
```

1. **Query Embedding**: User question converted to vector representation
2. **Similarity Search**: ChromaDB finds most relevant text chunks
3. **Context Retrieval**: MongoDB fetches full text content using metadata
4. **Answer Generation**: OpenAI generates response using retrieved context
5. **Response Delivery**: Answer returned with source attribution

## Technology Stack

### Backend Services
- **FastAPI**: High-performance async web framework
- **RQ**: Redis-based task queue for background processing
- **Pydantic**: Data validation and settings management
- **Jinja2**: HTML template rendering

### AI/ML Components
- **OpenAI GPT-4.1-nano**: Content structuring and answer generation
- **sentence-transformers**: Local embedding model (`all-MiniLM-L6-v2`)
- **trafilatura**: Web content extraction

### Data Storage
- **MongoDB**: Document-oriented storage for structured articles
- **ChromaDB**: Vector database for semantic search
- **Redis**: Task queue backend for RQ (Redis Queue)

### Infrastructure
- **Docker**: Containerization of all services
- **Docker Compose**: Multi-container orchestration
- **httpx**: Modern HTTP client for web scraping

## Deployment Architecture

### Container Services

1. **API Container**:
   - Runs FastAPI application with Uvicorn
   - Exposed on port 8000
   - Hot-reload enabled for development

2. **Worker Container**:
   - Runs RQ worker processes
   - Shares codebase with API container
   - Processes background tasks asynchronously

3. **MongoDB Container**:
   - Official MongoDB 6.0 image
   - Persistent volume for data storage
   - Exposed on host port 27018

4. **Redis Container**:
   - Alpine-based Redis 7 image
   - Used for task queue management
   - Exposed on host port 6379

5. **ChromaDB Container**:
   - Official ChromaDB image
   - Persistent volume for vector storage
   - Exposed on host port 8001

### Networking
- All containers communicate via Docker internal network
- External access only through exposed ports
- Environment-based service discovery

## Scalability Considerations

### Horizontal Scaling
- **Worker Scaling**: Multiple RQ workers can process tasks concurrently
- **API Scaling**: FastAPI supports async operations for high concurrency
- **Database Sharding**: MongoDB supports horizontal partitioning

### Performance Optimizations
- **Local Embeddings**: sentence-transformers runs locally, reducing API costs
- **Async Processing**: Background task processing prevents API blocking
- **Vector Indexing**: ChromaDB provides fast similarity search
- **Connection Pooling**: Database connections efficiently managed

### Resource Management
- **Memory**: Embedding model loaded once per container
- **CPU**: Async operations minimize thread blocking  
- **Storage**: Persistent volumes for data durability
- **Connections**: Unused `redis_client` in db.py could be removed for cleaner architecture

## Security Architecture

### API Security
- Input validation via Pydantic models
- HTTP timeout configurations
- Error handling prevents information leakage

### Data Security
- Environment-based secret management
- No hardcoded credentials in source code
- Database access restricted to internal network

### Network Security
- Container isolation via Docker networks
- External access limited to API endpoints
- Internal service communication only

## Development Workflow

### Environment Setup
1. Clone repository
2. Configure `.env` with OpenAI API key
3. Run `docker-compose up --build`
4. Access API at `http://localhost:8000`

### Code Organization
```
app/
├── main.py         # FastAPI application and routes
├── tasks.py        # Background processing logic
├── config.py       # Configuration management
├── db.py           # Database client setup
├── Dockerfile      # Container image definition
├── requirements.txt # Python dependencies
└── templates/      # HTML templates
```

### Testing Strategy
- Unit tests for individual components
- Integration tests for API endpoints
- End-to-end tests for complete workflows

## Monitoring and Observability

### Health Checks
- API endpoint availability
- Database connection status
- Queue processing status

### Metrics
- Document ingestion rate
- Query response times
- Error rates and types
- Resource utilization

### Logging
- Structured logging for debugging
- Error tracking and alerting
- Performance monitoring

## Future Enhancements

### Potential Improvements
- Authentication and authorization
- Rate limiting and quotas
- Advanced search filtering
- Document versioning
- Batch processing capabilities
- Real-time updates via WebSockets
- Admin dashboard for system management

### Scalability Roadmap
- Kubernetes deployment
- Load balancer integration
- Database clustering
- CDN for static assets
- Caching layer optimization