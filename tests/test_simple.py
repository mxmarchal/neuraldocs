"""
Simplified unit tests that focus on core functionality without complex mocking.
"""
import pytest
import os
from unittest.mock import Mock, patch
from bson import ObjectId

class TestConfig:
    """Test configuration module."""
    
    def test_settings_with_env_var(self):
        """Test settings loads from environment variables."""
        from config import Settings
        
        # Test with required env var
        settings = Settings(openai_api_key="test-key")
        assert settings.openai_api_key == "test-key"
        assert settings.mongo_host == "mongodb"
        assert settings.redis_host == "redis"
        assert settings.top_k == 5


class TestUtilities:
    """Test utility functions."""
    
    def test_object_id_conversion_valid(self):
        """Test valid ObjectId string conversion."""
        # Mock external dependencies
        with patch('main.redis_conn'), \
             patch('main.db'), \
             patch('main.collection'), \
             patch('main.embedding_model'), \
             patch('main.client'), \
             patch('main.queue'):
            
            from main import obj_id
            test_id = str(ObjectId())
            result = obj_id(test_id)
            assert isinstance(result, ObjectId)
            assert str(result) == test_id
    
    def test_object_id_conversion_invalid(self):
        """Test invalid ObjectId string conversion."""
        # Mock external dependencies
        with patch('main.redis_conn'), \
             patch('main.db'), \
             patch('main.collection'), \
             patch('main.embedding_model'), \
             patch('main.client'), \
             patch('main.queue'):
            
            from main import obj_id
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                obj_id("invalid-id")
            
            assert exc_info.value.status_code == 400
            assert "Invalid document ID" in str(exc_info.value.detail)


class TestTasksLogic:
    """Test background task logic with mocked dependencies."""
    
    def test_process_url_http_success(self):
        """Test successful HTTP request and content extraction."""
        # Mock all external dependencies
        with patch('tasks.httpx.get') as mock_get, \
             patch('tasks.trafilatura.extract') as mock_extract, \
             patch('tasks.client') as mock_openai, \
             patch('tasks.db') as mock_db, \
             patch('tasks.collection') as mock_collection, \
             patch('tasks.embedding_model') as mock_embedding, \
             patch('tasks.get_current_job'):
            
            # Setup mocks
            mock_response = Mock()
            mock_response.text = "<html>Test content</html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            mock_extract.return_value = "Extracted content"
            
            mock_openai_response = Mock()
            mock_openai_response.choices = [Mock()]
            mock_openai_response.choices[0].message.content = '{"text": "Test content"}'
            mock_openai.chat.completions.create.return_value = mock_openai_response
            
            mock_insert_result = Mock()
            mock_insert_result.inserted_id = ObjectId()
            mock_db.documents.insert_one.return_value = mock_insert_result
            
            # Mock embedding model to return a list (not numpy array)
            mock_embedding.encode.return_value = [0.1] * 384
            
            from tasks import process_url
            result = process_url("https://example.com")
            
            assert result["status"] == "completed"
            assert "doc_id" in result
            mock_get.assert_called_once_with("https://example.com", timeout=30.0)
    
    def test_process_url_http_error(self):
        """Test HTTP error handling."""
        with patch('tasks.httpx.get') as mock_get, \
             patch('tasks.get_current_job'):
            
            mock_get.side_effect = Exception("Connection failed")
            
            from tasks import process_url
            result = process_url("https://example.com")
            
            assert "error" in result
            assert "Connection failed" in result["error"]


class TestDataModels:
    """Test Pydantic models."""
    
    def test_url_item_model(self):
        """Test URLItem model validation."""
        # Mock external dependencies
        with patch('main.redis_conn'), \
             patch('main.db'), \
             patch('main.collection'), \
             patch('main.embedding_model'), \
             patch('main.client'), \
             patch('main.queue'):
            
            from main import URLItem
            
            # Valid URL
            item = URLItem(url="https://example.com")
            assert item.url == "https://example.com"
    
    def test_query_item_model(self):
        """Test QueryItem model validation."""
        # Mock external dependencies  
        with patch('main.redis_conn'), \
             patch('main.db'), \
             patch('main.collection'), \
             patch('main.embedding_model'), \
             patch('main.client'), \
             patch('main.queue'):
            
            from main import QueryItem
            
            # Test with default top_k
            item = QueryItem(question="What is this?")
            assert item.question == "What is this?"
            assert item.top_k == 5  # default from settings
            
            # Test with custom top_k
            item = QueryItem(question="What is this?", top_k=10)
            assert item.top_k == 10