import pytest
import json
from unittest.mock import Mock, patch
from bson import ObjectId

class TestProcessURL:
    
    def test_process_url_success_with_sections(self):
        """Test successful URL processing with structured sections."""
        # Mock all dependencies
        with patch('tasks.httpx.get') as mock_httpx, \
             patch('tasks.trafilatura.extract') as mock_extract, \
             patch('tasks.client') as mock_client, \
             patch('tasks.db') as mock_db, \
             patch('tasks.collection') as mock_collection, \
             patch('tasks.embedding_model') as mock_embedding, \
             patch('tasks.get_current_job') as mock_job:
            
            from tasks import process_url
            
            # Mock HTTP response
            mock_response = Mock()
            mock_response.text = "<html>Test content</html>"
            mock_response.raise_for_status = Mock()
            mock_httpx.return_value = mock_response
            
            # Mock content extraction
            mock_extract.return_value = "Extracted test content"
            
            # Mock OpenAI response with structured data
            structured_data = {
                "title": "Test Article",
                "sections": {
                    "intro": {"text": "Introduction text"},
                    "body": {"text": "Body text"}
                }
            }
            mock_openai_response = Mock()
            mock_openai_response.choices = [Mock()]
            mock_openai_response.choices[0].message.content = json.dumps(structured_data)
            mock_client.chat.completions.create.return_value = mock_openai_response
            
            # Mock MongoDB insertion
            mock_insert_result = Mock()
            mock_insert_result.inserted_id = ObjectId()
            mock_db.documents.insert_one.return_value = mock_insert_result
            
            # Mock embedding model
            mock_embedding.encode.return_value = [0.1] * 384
            
            # Execute
            result = process_url("https://example.com")
            
            # Assertions
            assert result["status"] == "completed"
            assert "doc_id" in result
            
            # Verify HTTP request
            mock_httpx.assert_called_once_with("https://example.com", timeout=30.0)
            
            # Verify content extraction
            mock_extract.assert_called_once_with("<html>Test content</html>", url="https://example.com")
            
            # Verify MongoDB insertion
            mock_db.documents.insert_one.assert_called_once()
            
            # Verify ChromaDB additions (2 sections)
            assert mock_collection.add.call_count == 2
    
    def test_process_url_success_with_raw_text(self):
        """Test successful URL processing with fallback to raw text."""
        with patch('tasks.httpx.get') as mock_httpx, \
             patch('tasks.trafilatura.extract') as mock_extract, \
             patch('tasks.client') as mock_client, \
             patch('tasks.db') as mock_db, \
             patch('tasks.collection') as mock_collection, \
             patch('tasks.embedding_model') as mock_embedding, \
             patch('tasks.get_current_job') as mock_job:
            
            from tasks import process_url
            
            # Mock HTTP response
            mock_response = Mock()
            mock_response.text = "<html>Test content</html>"
            mock_response.raise_for_status = Mock()
            mock_httpx.return_value = mock_response
            
            # Mock content extraction
            mock_extract.return_value = "Extracted test content"
            
            # Mock OpenAI response with invalid JSON (triggers fallback)
            mock_openai_response = Mock()
            mock_openai_response.choices = [Mock()]
            mock_openai_response.choices[0].message.content = "Invalid JSON response"
            mock_client.chat.completions.create.return_value = mock_openai_response
            
            # Mock MongoDB insertion
            mock_insert_result = Mock()
            mock_insert_result.inserted_id = ObjectId()
            mock_db.documents.insert_one.return_value = mock_insert_result
            
            # Mock embedding model
            mock_embedding.encode.return_value = [0.1] * 384
            
            # Execute
            result = process_url("https://example.com")
            
            # Assertions
            assert result["status"] == "completed"
            assert "doc_id" in result
            
            # Verify fallback to raw text was used
            expected_doc = {"url": "https://example.com", "data": {"text": "Extracted test content"}}
            mock_db.documents.insert_one.assert_called_once_with(expected_doc)
            
            # Verify ChromaDB addition (1 content chunk)
            mock_collection.add.assert_called_once()
    
    def test_process_url_http_error(self):
        """Test URL processing with HTTP error."""
        with patch('tasks.httpx.get') as mock_httpx, \
             patch('tasks.get_current_job') as mock_job:
            
            from tasks import process_url
            
            # Mock HTTP error
            mock_httpx.side_effect = Exception("Connection failed")
            
            # Execute
            result = process_url("https://example.com")
            
            # Assertions
            assert "error" in result
            assert "Fetch/Extract error" in result["error"]
    
    def test_process_url_extraction_error(self):
        """Test URL processing with content extraction error."""
        with patch('tasks.httpx.get') as mock_httpx, \
             patch('tasks.trafilatura.extract') as mock_extract, \
             patch('tasks.get_current_job') as mock_job:
            
            from tasks import process_url
            
            # Mock HTTP response
            mock_response = Mock()
            mock_response.text = "<html>Test content</html>"
            mock_response.raise_for_status = Mock()
            mock_httpx.return_value = mock_response
            
            # Mock extraction failure
            mock_extract.return_value = None
            
            # Execute
            result = process_url("https://example.com")
            
            # Assertions
            assert "error" in result
            assert "Failed to extract content" in result["error"]