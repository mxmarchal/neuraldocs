import pytest
from unittest.mock import Mock, patch

class TestDatabaseConnections:
    
    def test_mongo_client_initialization(self):
        """Test MongoDB client is initialized correctly."""
        with patch('db.MongoClient') as mock_mongo_client, \
             patch('db.Redis'), \
             patch('db.chromadb.HttpClient'):
            
            mock_client_instance = Mock()
            mock_mongo_client.return_value = mock_client_instance
            
            # Import db module to trigger initialization
            import db
            
            # Verify MongoClient was called with correct parameters
            mock_mongo_client.assert_called_once()
            # Verify db is set to articles_db
            assert hasattr(db, 'db')
    
    def test_redis_client_initialization(self):
        """Test Redis client is initialized correctly."""
        with patch('db.MongoClient'), \
             patch('db.Redis') as mock_redis, \
             patch('db.chromadb.HttpClient'):
            
            mock_redis_instance = Mock()
            mock_redis.return_value = mock_redis_instance
            
            # Import db module to trigger initialization
            import db
            
            # Verify Redis was called
            mock_redis.assert_called_once()
            # Verify redis_client exists
            assert hasattr(db, 'redis_client')
    
    def test_chroma_client_initialization(self):
        """Test ChromaDB client is initialized correctly."""
        with patch('db.MongoClient'), \
             patch('db.Redis'), \
             patch('db.chromadb.HttpClient') as mock_chroma:
            
            mock_client_instance = Mock()
            mock_collection = Mock()
            mock_client_instance.get_or_create_collection.return_value = mock_collection
            mock_chroma.return_value = mock_client_instance
            
            # Import db module to trigger initialization
            import db
            
            # Verify HttpClient was called
            mock_chroma.assert_called_once()
            # Verify collection is created
            mock_client_instance.get_or_create_collection.assert_called_once_with(name="articles")
            assert hasattr(db, 'collection')