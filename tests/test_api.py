import pytest
import sys
from unittest.mock import patch, Mock, MagicMock
from bson import ObjectId
from fastapi.testclient import TestClient

@pytest.fixture
def test_client():
    """Create test client with mocked dependencies."""
    # Mock all external dependencies before importing
    with patch('chromadb.HttpClient') as mock_chroma_client, \
         patch('pymongo.MongoClient') as mock_mongo_client, \
         patch('redis.Redis') as mock_redis, \
         patch('sentence_transformers.SentenceTransformer') as mock_st, \
         patch('openai.OpenAI') as mock_openai:
        
        # Setup mocks
        mock_chroma_instance = Mock()
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "metadatas": [[{
                "mongo_id": str(ObjectId()),
                "chunk_key": "content", 
                "source_url": "https://example.com"
            }]]
        }
        mock_collection.count.return_value = 100
        mock_chroma_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_chroma_instance
        
        mock_mongo_instance = Mock()
        mock_db = Mock()
        mock_mongo_collection = Mock()
        mock_db.documents = mock_mongo_collection
        mock_mongo_instance.articles_db = mock_db
        mock_mongo_client.return_value = mock_mongo_instance
        
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        
        mock_st_instance = Mock()
        mock_st_instance.encode.return_value = [0.1] * 384
        mock_st.return_value = mock_st_instance
        
        mock_openai_instance = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test answer"
        mock_openai_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_openai_instance
        
        # Mock RQ Queue
        with patch('rq.Queue') as mock_queue:
            mock_job = Mock()
            mock_job.get_id.return_value = "test-job-id"
            mock_job.get_status.return_value = "finished"
            mock_job.result = "Task completed"
            
            mock_queue_instance = Mock()
            mock_queue_instance.enqueue.return_value = mock_job
            mock_queue_instance.fetch_job.return_value = mock_job
            mock_queue.return_value = mock_queue_instance
            
            # Import and create app after mocking
            from main import app
            yield TestClient(app), mock_db, mock_collection

class TestAPIEndpoints:
    
    def test_get_ui(self, test_client):
        """Test the root endpoint returns HTML."""
        client, _, _ = test_client
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_add_url_valid(self, test_client):
        """Test adding a valid URL."""
        client, _, _ = test_client
        response = client.post("/add-url", json={"url": "https://example.com"})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "task_id" in data
        assert data["task_id"] == "test-job-id"
    
    def test_add_url_invalid_json(self, test_client):
        """Test adding URL with invalid JSON."""
        client, _, _ = test_client
        response = client.post("/add-url", json={"invalid": "data"})
        assert response.status_code == 422
    
    def test_get_task_existing(self, test_client):
        """Test getting an existing task."""
        client, _, _ = test_client
        response = client.get("/tasks/test-job-id")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-job-id"
        assert data["status"] == "finished"
        assert data["result"] == "Task completed"
    
    def test_query_valid(self, test_client, sample_document):
        """Test querying with valid question."""
        client, mock_db, _ = test_client
        mock_db.documents.find_one.return_value = sample_document
        
        response = client.post("/query", json={"question": "What is this about?"})
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert data["answer"] == "Test answer"
    
    def test_get_stats(self, test_client):
        """Test getting system statistics."""
        client, mock_db, mock_collection = test_client
        mock_db.documents.count_documents.return_value = 50
        
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == 50
        assert data["vectors"] == 100


class TestUtilityFunctions:
    
    def test_obj_id_valid(self):
        """Test obj_id with valid ObjectId string."""
        # Mock dependencies before import
        with patch('chromadb.HttpClient'), \
             patch('pymongo.MongoClient'), \
             patch('redis.Redis'), \
             patch('sentence_transformers.SentenceTransformer'), \
             patch('openai.OpenAI'), \
             patch('rq.Queue'):
            
            from main import obj_id
            test_id = str(ObjectId())
            result = obj_id(test_id)
            assert isinstance(result, ObjectId)
            assert str(result) == test_id
    
    def test_obj_id_invalid(self):
        """Test obj_id with invalid ObjectId string."""
        # Mock dependencies before import
        with patch('chromadb.HttpClient'), \
             patch('pymongo.MongoClient'), \
             patch('redis.Redis'), \
             patch('sentence_transformers.SentenceTransformer'), \
             patch('openai.OpenAI'), \
             patch('rq.Queue'):
            
            from main import obj_id
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                obj_id("invalid-id")
            
            assert exc_info.value.status_code == 400
            assert "Invalid document ID" in str(exc_info.value.detail)