"""
Working unit tests with proper dependency isolation.
"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId

# Mock all problematic modules before any imports
mock_db = Mock()
mock_db.db = Mock()
mock_db.collection = Mock()
mock_db.redis_client = Mock()

sys.modules['db'] = mock_db


class TestBasicFunctionality:
    """Test basic functionality without external dependencies."""
    
    def test_object_id_creation(self):
        """Test ObjectId creation and conversion."""
        # Test valid ObjectId
        oid = ObjectId()
        oid_str = str(oid)
        new_oid = ObjectId(oid_str)
        assert str(new_oid) == oid_str
    
    def test_object_id_validation(self):
        """Test ObjectId validation."""
        from bson import ObjectId
        from bson.errors import InvalidId
        
        # Valid ObjectId string
        valid_id = str(ObjectId())
        assert ObjectId.is_valid(valid_id)
        
        # Invalid ObjectId string
        invalid_id = "invalid-id-123"
        assert not ObjectId.is_valid(invalid_id)
        
        # Test exception on invalid ObjectId
        with pytest.raises(InvalidId):
            ObjectId("invalid")


class TestConfiguration:
    """Test configuration loading."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        from config import Settings
        
        # Create settings with minimal required field
        settings = Settings(openai_api_key="test-key")
        
        # Check defaults (accounting for env vars set in conftest)
        assert settings.openai_api_key == "test-key"
        assert settings.mongo_port == 27017
        assert settings.redis_port == 6379
        assert settings.chroma_port == 8000
        assert settings.top_k == 5
        assert settings.embedding_model_name == "all-MiniLM-L6-v2"
    
    def test_config_validation(self):
        """Test configuration validation."""
        from config import Settings
        from pydantic import ValidationError
        
        # Test invalid types
        with pytest.raises(ValidationError):
            Settings(mongo_port="invalid", openai_api_key="test")
        
        with pytest.raises(ValidationError):
            Settings(top_k="invalid", openai_api_key="test")


class TestMockedTasks:
    """Test task functions with mocked dependencies."""
    
    def test_process_url_with_mocks(self):
        """Test URL processing with all dependencies mocked."""
        # Mock all external libraries
        with patch('httpx.get') as mock_get, \
             patch('trafilatura.extract') as mock_extract, \
             patch('openai.OpenAI') as mock_openai_class, \
             patch('sentence_transformers.SentenceTransformer') as mock_st, \
             patch('rq.get_current_job') as mock_job, \
             patch('uuid.uuid4') as mock_uuid:
            
            # Setup mocks
            mock_response = Mock()
            mock_response.text = "<html>Test</html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            mock_extract.return_value = "Test content"
            
            mock_openai = Mock()
            mock_openai_response = Mock()
            mock_openai_response.choices = [Mock()]
            mock_openai_response.choices[0].message.content = '{"text": "Test"}'
            mock_openai.chat.completions.create.return_value = mock_openai_response
            mock_openai_class.return_value = mock_openai
            
            # Create mock numpy array-like object
            mock_array = Mock()
            mock_array.tolist.return_value = [0.1] * 384
            
            mock_embedding_model = Mock()
            mock_embedding_model.encode.return_value = mock_array
            mock_st.return_value = mock_embedding_model
            
            mock_insert_result = Mock()
            mock_insert_result.inserted_id = ObjectId()
            mock_db.db.documents.insert_one.return_value = mock_insert_result
            
            mock_uuid.return_value = "test-uuid"
            
            # Import and test the function
            from tasks import process_url
            result = process_url("https://example.com")
            
            # Verify the result
            assert result["status"] == "completed"
            assert "doc_id" in result
    
    def test_process_url_error_handling(self):
        """Test error handling in URL processing."""
        with patch('httpx.get') as mock_get, \
             patch('rq.get_current_job'):
            
            # Mock HTTP error
            mock_get.side_effect = Exception("Network error")
            
            from tasks import process_url
            result = process_url("https://example.com")
            
            assert "error" in result
            assert "Network error" in result["error"]


class TestPydanticModels:
    """Test Pydantic model validation."""
    
    def test_url_item_model(self):
        """Test URLItem model."""
        # Need to mock dependencies before import
        with patch('main.redis_conn', Mock()), \
             patch('main.queue', Mock()), \
             patch('main.embedding_model', Mock()), \
             patch('main.client', Mock()):
            
            from main import URLItem
            
            # Valid URL
            item = URLItem(url="https://example.com")
            assert item.url == "https://example.com"
            
            # Test URL validation (if any)
            item2 = URLItem(url="http://test.com/path")
            assert item2.url == "http://test.com/path"
    
    def test_query_item_model(self):
        """Test QueryItem model."""
        with patch('main.redis_conn', Mock()), \
             patch('main.queue', Mock()), \
             patch('main.embedding_model', Mock()), \
             patch('main.client', Mock()):
            
            from main import QueryItem
            
            # Test with default top_k
            item = QueryItem(question="What is this?")
            assert item.question == "What is this?"
            # top_k should default to settings value (5)
            
            # Test with custom top_k
            item2 = QueryItem(question="Test", top_k=10)
            assert item2.top_k == 10


class TestUtilityFunctions:
    """Test utility functions with proper mocking."""
    
    def test_obj_id_function(self):
        """Test obj_id utility function."""
        with patch('main.redis_conn', Mock()), \
             patch('main.queue', Mock()), \
             patch('main.embedding_model', Mock()), \
             patch('main.client', Mock()):
            
            from main import obj_id
            from fastapi import HTTPException
            
            # Test valid ObjectId
            test_id = str(ObjectId())
            result = obj_id(test_id)
            assert isinstance(result, ObjectId)
            assert str(result) == test_id
            
            # Test invalid ObjectId
            with pytest.raises(HTTPException) as exc_info:
                obj_id("invalid-id")
            
            assert exc_info.value.status_code == 400
            assert "Invalid document ID" in str(exc_info.value.detail)