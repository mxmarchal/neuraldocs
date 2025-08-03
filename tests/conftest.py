import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import fakeredis
from bson import ObjectId

# Set environment variables for testing
os.environ.setdefault('OPENAI_API_KEY', 'test-api-key')
os.environ.setdefault('MONGO_HOST', 'test-mongo')
os.environ.setdefault('REDIS_HOST', 'test-redis')
os.environ.setdefault('CHROMA_HOST', 'test-chroma')

@pytest.fixture
def mock_redis():
    """Mock Redis connection using fakeredis."""
    return fakeredis.FakeRedis()

@pytest.fixture
def mock_mongo_db():
    """Mock MongoDB database."""
    mock_db = Mock()
    mock_collection = Mock()
    mock_db.documents = mock_collection
    return mock_db

@pytest.fixture
def mock_chroma_collection():
    """Mock ChromaDB collection."""
    mock_collection = Mock()
    mock_collection.query.return_value = {
        "metadatas": [[{
            "mongo_id": str(ObjectId()),
            "chunk_key": "content",
            "source_url": "https://example.com"
        }]]
    }
    mock_collection.count.return_value = 100
    return mock_collection

@pytest.fixture
def mock_embedding_model():
    """Mock SentenceTransformer model."""
    mock_model = Mock()
    mock_model.encode.return_value = [0.1] * 384  # Mock embedding vector
    return mock_model

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test answer"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

@pytest.fixture
def mock_settings():
    """Mock settings object."""
    settings = Mock()
    settings.mongo_host = "test-mongo"
    settings.mongo_port = 27017
    settings.redis_host = "test-redis"
    settings.redis_port = 6379
    settings.chroma_host = "test-chroma"
    settings.chroma_port = 8000
    settings.openai_api_key = "test-api-key"
    settings.embedding_model_name = "all-MiniLM-L6-v2"
    settings.nano_model_name = "gpt-4.1-nano"
    settings.rag_model_name = "gpt-4.1-nano"
    settings.top_k = 5
    return settings

@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "_id": ObjectId(),
        "url": "https://example.com",
        "data": {
            "title": "Test Article",
            "text": "This is a test article content.",
            "sections": {
                "content": {
                    "text": "This is a test article content."
                }
            }
        }
    }