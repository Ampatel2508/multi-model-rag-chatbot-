from langchain_openai import ChatOpenAI
from .base_provider import BaseProvider
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseProvider):
    """Provider for OpenRouter models."""
    
    def initialize(self):
        """Initialize OpenRouter LLM."""
        logger.info(f"Initializing OpenRouter with model: {self.model_name}")
        
        try:
            # Ensure parameters are clean strings
            model_str = self._ensure_string(self.model_name)
            api_key_str = self._ensure_string(self.api_key).strip()
            
            # Validate API key is not empty
            if not api_key_str:
                raise ValueError("OpenRouter API key is empty or not configured")
            
            # Log API key info (safely)
            logger.info(f"API Key: {api_key_str[:10]}...{api_key_str[-5:]} (length: {len(api_key_str)})")
            
            llm = ChatOpenAI(
                model=model_str,
                api_key=api_key_str,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.3
            )
            
            logger.info("✓ OpenRouter LLM initialized successfully")
            return llm
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize OpenRouter: {e}")
            raise
    
    def validate_api_key(self) -> bool:
        """Validate OpenRouter API key."""
        try:
            api_key_str = self._ensure_string(self.api_key).strip()
            
            # Validate API key is not empty
            if not api_key_str:
                logger.error("OpenRouter API key is empty or not configured")
                return False
            
            # Try to create an LLM instance - if it works, key is valid
            llm = ChatOpenAI(
                model=self._ensure_string(self.model_name),
                api_key=api_key_str,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.3
            )
            
            logger.info("✓ OpenRouter API key validated successfully")
            return True
                
        except Exception as e:
            logger.error(f"✗ OpenRouter API key validation failed: {e}")
            return False

    def get_available_models(self) -> Dict[str, Dict]:
        """Fetch available OpenRouter models."""
        try:
            api_key_str = self._ensure_string(self.api_key).strip()
            
            if not api_key_str:
                raise ValueError("OpenRouter API key is required")
            
            import requests
            
            headers = {
                "Authorization": f"Bearer {api_key_str}",
                "HTTP-Referer": "http://localhost:3000",
            }
            
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            models_data = response.json()
            available_models = {}
            
            for model in models_data.get("data", []):
                model_id = model.get("id", "")
                if not model_id:
                    continue
                
                # Check if model is free
                pricing = model.get("pricing", {})
                input_cost = float(pricing.get("prompt", 1))
                output_cost = float(pricing.get("completion", 1))
                
                # Only include free models (both input and output must be 0)
                if input_cost == 0 and output_cost == 0:
                    available_models[model_id] = {
                        "name": model.get("name", model_id),
                        "description": model.get("description", f"OpenRouter model (Free): {model_id}"),
                        "context_window": model.get("context_length", 0),
                        "max_output": model.get("max_completion_tokens", 0)
                    }
            
            logger.info(f"✓ Fetched {len(available_models)} free OpenRouter models")
            return available_models
            
        except Exception as e:
            logger.error(f"✗ Failed to fetch OpenRouter models: {e}")
            raise
