from langchain_groq import ChatGroq
from .base_provider import BaseProvider
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class GroqProvider(BaseProvider):
    """Provider for Groq models."""
    
    def initialize(self):
        """Initialize Groq LLM."""
        logger.info(f"Initializing Groq with model: {self.model_name}")
        
        try:
            # Ensure parameters are clean strings
            model_str = self._ensure_string(self.model_name)
            api_key_str = self._ensure_string(self.api_key).strip()
            
            # Validate API key is not empty
            if not api_key_str:
                raise ValueError("Groq API key is empty or not configured")
            
            # Log API key info (safely)
            logger.info(f"API Key: {api_key_str[:10]}...{api_key_str[-5:]} (length: {len(api_key_str)})")
            
            llm = ChatGroq(
                model=model_str,
                groq_api_key=api_key_str,
                temperature=0.3
            )
            
            logger.info("✓ Groq LLM initialized successfully")
            return llm
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize Groq: {e}")
            raise
    
    def validate_api_key(self) -> bool:
        """Validate Groq API key."""
        try:
            api_key_str = self._ensure_string(self.api_key).strip()
            
            # Validate API key is not empty
            if not api_key_str:
                logger.error("Groq API key is empty or not configured")
                return False
            
            # Try to create an LLM instance - if it works, key is valid
            llm = ChatGroq(
                model=self._ensure_string(self.model_name),
                groq_api_key=api_key_str,
                temperature=0.3
            )
            
            logger.info("✓ Groq API key validated successfully")
            return True
                
        except Exception as e:
            logger.error(f"✗ Groq API key validation failed: {e}")
            return False

    def get_available_models(self) -> Dict[str, Dict]:
        """Fetch available Groq models."""
        try:
            api_key_str = self._ensure_string(self.api_key).strip()
            
            if not api_key_str:
                raise ValueError("Groq API key is required")
            
            from groq import Groq
            
            client = Groq(api_key=api_key_str)
            
            # Get list of available models
            models = client.models.list()
            
            available_models = {}
            
            # Groq offers models for free - list all available models
            for model in models.data:
                model_id = model.id
                
                available_models[model_id] = {
                    "name": model_id,
                    "description": f"Groq model (Free): {model_id}",
                    "context_window": 0,  # Groq doesn't provide this in the list endpoint
                    "max_output": 0
                }
            
            logger.info(f"✓ Fetched {len(available_models)} free Groq models")
            return available_models
            
        except Exception as e:
            logger.error(f"✗ Failed to fetch Groq models: {e}")
            raise
