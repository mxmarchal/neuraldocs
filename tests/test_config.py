import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

class TestSettings:
    
    def test_default_settings(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            from config import Settings
            settings = Settings()
            
            assert settings.mongo_host == "mongodb"
            assert settings.mongo_port == 27017
            assert settings.redis_host == "redis"
            assert settings.redis_port == 6379
            assert settings.chroma_host == "chromadb"
            assert settings.chroma_port == 8000
            assert settings.embedding_model_name == "all-MiniLM-L6-v2"
            assert settings.nano_model_name == "gpt-4.1-nano"
            assert settings.rag_model_name == "gpt-4.1-nano"
            assert settings.top_k == 5
            assert settings.openai_api_key == "test-key"
    
    def test_custom_settings(self):
        """Test configuration with custom values."""
        from config import Settings
        
        settings = Settings(
            mongo_host="custom-mongo",
            mongo_port=27018,
            redis_host="custom-redis",
            redis_port=6380,
            chroma_host="custom-chroma",
            chroma_port=8001,
            openai_api_key="custom-key",
            embedding_model_name="custom-model",
            nano_model_name="gpt-4",
            rag_model_name="gpt-3.5-turbo",
            top_k=10
        )
        
        assert settings.mongo_host == "custom-mongo"
        assert settings.mongo_port == 27018
        assert settings.redis_host == "custom-redis"
        assert settings.redis_port == 6380
        assert settings.chroma_host == "custom-chroma"
        assert settings.chroma_port == 8001
        assert settings.openai_api_key == "custom-key"
        assert settings.embedding_model_name == "custom-model"
        assert settings.nano_model_name == "gpt-4"
        assert settings.rag_model_name == "gpt-3.5-turbo"
        assert settings.top_k == 10
    
    def test_environment_variables(self):
        """Test that environment variables are loaded correctly."""
        env_vars = {
            'MONGO_HOST': 'env-mongo',
            'REDIS_PORT': '6381',
            'OPENAI_API_KEY': 'env-api-key',
            'TOP_K': '3'
        }
        
        with patch.dict(os.environ, env_vars):
            from config import Settings
            settings = Settings()
            
            assert settings.mongo_host == "env-mongo"
            assert settings.redis_port == 6381
            assert settings.openai_api_key == "env-api-key"
            assert settings.top_k == 3
    
    def test_required_openai_key(self):
        """Test that OpenAI API key is required."""
        # Clear any existing OPENAI_API_KEY
        with patch.dict(os.environ, {}, clear=False):
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            
            from config import Settings
            
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            # Check that the error is about the missing openai_api_key
            errors = exc_info.value.errors()
            assert any(error['loc'] == ('openai_api_key',) for error in errors)
    
    def test_type_validation(self):
        """Test that type validation works correctly."""
        from config import Settings
        
        # Test invalid port (should be int)
        with pytest.raises(ValidationError):
            Settings(mongo_port="invalid", openai_api_key="test-key")
        
        # Test invalid top_k (should be int)  
        with pytest.raises(ValidationError):
            Settings(top_k="invalid", openai_api_key="test-key")
    
    def test_config_class(self):
        """Test that Config class specifies .env file."""
        from config import Settings
        
        # Check that Config class exists and has env_file attribute
        assert hasattr(Settings, 'Config')
        assert hasattr(Settings.Config, 'env_file')
        assert Settings.Config.env_file == ".env"