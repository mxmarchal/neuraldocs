# Neuraldocs - Web Article RAG API - Built with OpenAI's Codex

Before diving deep into the project, let's discuss Codex, the OpenAI CLI tool for automated code generation using the latest o4-mini and o3 models.
For this project, I exclusively used the `o4-mini` model with `--full-auto` and I planned the project idea in the `codex.md` file using ChatGPT (`o4-mini` again).

While I don't have experience with Claude Code for comparison, using Codex was excellent.

The tool and model handled almost everything in one shot, with only 2 errors due to outdated documentation in their training:

- OpenAI Python package (yes, you read that right)
- ChromaDB

I'm impressed by the model's speed, precision and overall performance. And it's cost-effective too. Building this app, including fixing the 2 errors and adding 2 features (frontend and stats routes), cost less than $1.50 USD. While larger apps will naturally cost more, the tool seems to optimize token usage to maintain reasonable costs. I still need to try o3, but so far, o4-mini has proven excellent and I'm eager to explore it further.

The main challenge remains the knowledge cutoff date. This should be moved to Feb/March 2025, or the OpenAI API/model should have internet access to fetch latest data, as outdated information is problematic in our rapidly evolving tech landscape. To bypass the model's knowledge cutoff, relevant documentation can be included in markdown files. For instance, doc_openai.md was added to provide details on the OpenAI Python Package.

**Web Article Retrieval-Augmented Generation (RAG) API with FastAPI, Docker, and OpenAI**

## Overview

This project provides an API-first system for ingesting web articles, structuring their content via OpenAI, indexing them in a vector database, and answering user queries using a retrieval-augmented generation (RAG) approach.

## Key Features

- **Asynchronous Ingestion**: Background workers fetch URLs, extract article content with `trafilatura`, organize it into structured JSON using OpenAI GPT-4.1-nano, and store documents in MongoDB.
- **Vector Indexing**: Text chunks are embedded with a local `sentence-transformers` model (`all-MiniLM-L6-v2`) and stored in ChromaDB.
- **RAG Querying**: FastAPI endpoints embed user questions, retrieve top-k relevant chunks from ChromaDB, and generate answers via OpenAI GPT-4.1-nano.
- **Dockerized**: All components (API, worker, MongoDB, Redis, ChromaDB) run in Docker containers orchestrated by Docker Compose.

## Tech Stack

- Language & Framework: Python 3.11, FastAPI
- HTTP Client: `httpx`
- Article Extraction: `trafilatura`
- LLM API: OpenAI `gpt-4.1-nano` via `openai` Python SDK
- Embeddings: `sentence-transformers` (`all-MiniLM-L6-v2`)
- Vector Database: ChromaDB
- Metadata Store: MongoDB
- Task Queue: Redis + RQ
- Containerization: Docker, Docker Compose

## Prerequisites

- Docker Engine (v20+)
- Docker Compose (v2+)
- OpenAI API key

## Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/mxmarchal/neuraldocs.git
    cd neuraldocs
    ```
2.  **Configure environment variables**
    Copy the example and set your OpenAI key:
    ```bash
    cp .env.example .env
    # Edit .env and set OPENAI_API_KEY
    ```
3.  **Start services**
    ```bash
    docker-compose up --build
    ```
    This will build the images and start the following services:
    - **api**: The main FastAPI application, accessible at `http://localhost:8000`.
    - **worker**: The RQ worker processing background tasks (no direct access needed).
    - **mongodb**: The MongoDB database, accessible on the host at `mongodb://localhost:27018` (maps to container port 27017).
    - **redis**: The Redis server used for the task queue, accessible on the host at `redis://localhost:6379`.
    - **chromadb**: The ChromaDB vector store, accessible on the host at `http://localhost:8001` (maps to container port 8000).

## API Endpoints

### 1. Add URL for Ingestion

- **Endpoint**: `POST /add-url`
- **Body**:
  ```json
  { "url": "https://example.com/article" }
  ```
- **Response**:
  ```json
  { "message": "URL queued for processing", "task_id": "<rq_job_id>" }
  ```

### 2. Check Task Status

- **Endpoint**: `GET /tasks/{task_id}`
- **Response**:
  ```json
  {
    "task_id": "<rq_job_id>",
    "status": "queued|started|finished|failed",
    "result": {
      /* output of processing or error */
    }
  }
  ```

### 3. Query with RAG

- **Endpoint**: `POST /query`
- **Body**:
  ```json
  {
    "question": "What is the main idea of the article?",
    "top_k": 5 // optional, defaults to 5
  }
  ```
- **Response**:
  ```json
  {
    "answer": "The article explains ...",
    "sources": [
      "https://example.com/article",
      ...
    ]
  }
  ```

### 4. Get System Statistics

- **Endpoint**: `GET /stats`
- **Response**:
  ```json
  {
    "documents": 123, // number of ingested documents in MongoDB
    "vectors": 456 // number of stored vectors in ChromaDB
  }
  ```

## Example Usage

```bash
# 1. Add a URL
curl -X POST http://localhost:8000/add-url \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/article"}'

# 2. Check ingestion status
curl http://localhost:8000/tasks/<task_id>

# 3. Ask a question
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Key points from the article?"}'
```

## Project Structure

```
.
├── docker-compose.yml       # Multi-service orchestration
├── .env.example             # Environment variable template
├── .env                     # Local environment variables (ignored by git)
├── README.md                # Project overview & usage
└── app/
    ├── Dockerfile           # API & worker image definition
    ├── requirements.txt     # Python dependencies
    ├── config.py            # Pydantic settings
    ├── db.py                # DB & vector client setup
    ├── tasks.py             # RQ tasks: ingestion pipeline
    └── main.py              # FastAPI application
```

## Configuration Variables

Environment variables (in `.env`):

| Variable             | Description                           | Default            |
| -------------------- | ------------------------------------- | ------------------ |
| OPENAI_API_KEY       | OpenAI API key                        |                    |
| MONGO_HOST           | MongoDB hostname                      | `mongodb`          |
| MONGO_PORT           | MongoDB port                          | `27017`            |
| REDIS_HOST           | Redis hostname                        | `redis`            |
| REDIS_PORT           | Redis port                            | `6379`             |
| CHROMA_HOST          | ChromaDB hostname                     | `chromadb`         |
| CHROMA_PORT          | ChromaDB port                         | `8000`             |
| EMBEDDING_MODEL_NAME | SentenceTransformer model name        | `all-MiniLM-L6-v2` |
| NANO_MODEL_NAME      | OpenAI model for structuring articles | `gpt-4.1-nano`     |
| RAG_MODEL_NAME       | OpenAI model for RAG answering        | `gpt-4.1-nano`     |
| TOP_K                | Default number of retrieved chunks    | `5`                |

## Testing

The project includes comprehensive unit tests to ensure code quality and reliability.

### Test Suite

**Test Dependencies**:
- `pytest`: Testing framework
- `pytest-asyncio`: Async testing support  
- `pytest-mock`: Enhanced mocking capabilities
- `fakeredis`: Redis mocking for tests

**Running Tests**:
```bash
# Install test dependencies (already in requirements.txt)
cd app && pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_working.py -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

**Test Coverage**:
- ✅ Configuration validation and environment variable loading
- ✅ Pydantic model validation and error handling  
- ✅ Core business logic with mocked external dependencies
- ✅ Error handling scenarios and edge cases
- ✅ Utility function validation and type conversion

**Key Features**:
- **No External Dependencies**: All external services (MongoDB, Redis, ChromaDB, OpenAI) are properly mocked
- **Fast Execution**: Tests run quickly without network calls or service dependencies
- **Comprehensive Mocking**: Complex dependency chains isolated for reliable testing
- **Environment Isolation**: Test environment configured independently

### Test Architecture

The tests use a sophisticated mocking strategy to isolate the application logic from external dependencies:

```python
# Example test structure
def test_process_url_with_mocks(self):
    with patch('httpx.get') as mock_get, \
         patch('trafilatura.extract') as mock_extract, \
         patch('openai.OpenAI') as mock_openai:
        # Test logic with controlled mocks
```

This approach ensures tests are reliable, fast, and don't require external services to be running.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [trafilatura](https://github.com/adbar/trafilatura)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [sentence-transformers](https://www.sbert.net/)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [Redis & RQ](https://python-rq.org/)
- [pytest](https://docs.pytest.org/) - Testing framework
