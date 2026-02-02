from langchain_google_genai import ChatGoogleGenerativeAI
from .base_provider import BaseProvider
from typing import Dict
import logging
from google import genai

logger = logging.getLogger(__name__)

# Hardcoded list of free Gemini models
FREE_GEMINI_MODELS = {
    "gemma-3n": {
        "name": "Gemma 3 Nano",
        "description": "Google Gemma 3 Nano - Lightweight open model (Free)",
        "context_window": 16000,
        "max_output": 8192
    },
    "gemma-3": {
        "name": "Gemma 3",
        "description": "Google Gemma 3 - State-of-the-art open model (Free)",
        "context_window": 16000,
        "max_output": 8192
    },
    "gemini-robotics-er-1.5-preview": {
        "name": "Gemini Robotics-ER 1.5 Preview",
        "description": "Gemini Robotics model for embodied reasoning (Free)",
        "context_window": 128000,
        "max_output": 4096
    },
    "gemini-2.0-flash-lite": {
        "name": "Gemini 2.0 Flash Lite",
        "description": "Gemini 2.0 Flash Lite - Small and cost-effective (Free)",
        "context_window": 1000000,
        "max_output": 4096
    },
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "description": "Gemini 2.0 Flash - Balanced multimodal model (Free)",
        "context_window": 1000000,
        "max_output": 4096
    },
    "gemini-2.5-flash-preview-tts": {
        "name": "Gemini 2.5 Flash Preview TTS",
        "description": "Gemini 2.5 Flash Text-to-Speech model (Free)",
        "context_window": 128000,
        "max_output": 4096
    },
    "gemini-2.5-flash-native-audio-preview-12-2025": {
        "name": "Gemini 2.5 Flash Native Audio Preview",
        "description": "Gemini 2.5 Flash with native audio support (Free)",
        "context_window": 1000000,
        "max_output": 4096
    },
    "gemini-2.5-flash-lite-preview-09-2025": {
        "name": "Gemini 2.5 Flash Lite Preview",
        "description": "Gemini 2.5 Flash Lite Preview - Cost-efficient (Free)",
        "context_window": 1000000,
        "max_output": 4096
    },
    "gemini-2.5-flash-lite": {
        "name": "Gemini 2.5 Flash Lite",
        "description": "Gemini 2.5 Flash Lite - Small and efficient (Free)",
        "context_window": 1000000,
        "max_output": 4096
    },
    "gemini-2.5-flash-preview-09-2025": {
        "name": "Gemini 2.5 Flash Preview",
        "description": "Gemini 2.5 Flash Preview - Latest features (Free)",
        "context_window": 1000000,
        "max_output": 4096
    },
    "gemini-2.5-flash": {
        "name": "Gemini 2.5 Flash",
        "description": "Gemini 2.5 Flash - Hybrid reasoning model with 1M context (Free)",
        "context_window": 1000000,
        "max_output": 4096
    },
    "gemini-2.5-pro": {
        "name": "Gemini 2.5 Pro",
        "description": "Gemini 2.5 Pro - State-of-the-art multipurpose model (Free)",
        "context_window": 200000,
        "max_output": 4096
    },
    "gemini-3-flash-preview": {
        "name": "Gemini 3 Flash Preview",
        "description": "Gemini 3 Flash Preview - Latest intelligent model (Free)",
        "context_window": 1000000,
        "max_output": 4096
    },
}


class GeminiProvider(BaseProvider):
    """Provider for Google Gemini models."""
    
    def initialize(self):
        """Initialize Gemini LLM."""
        logger.info(f"Initializing Gemini with model: {self.model_name}")
        
        try:
            # Ensure parameters are clean strings
            model_str = self._ensure_string(self.model_name)
            api_key_str = self._ensure_string(self.api_key).strip()
            
            # Validate API key is not empty
            if not api_key_str:
                raise ValueError("Gemini API key is empty or not configured")
            
            # Log API key info (safely)
            logger.info(f"API Key: {api_key_str[:10]}...{api_key_str[-5:]} (length: {len(api_key_str)})")
            
            llm = ChatGoogleGenerativeAI(
                model=model_str,
                google_api_key=api_key_str,
                temperature=0.3,
                convert_system_message_to_human=True
            )
            
            logger.info("✓ Gemini LLM initialized successfully")
            return llm
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize Gemini: {e}")
            raise
    
    def validate_api_key(self) -> bool:
        """Validate Gemini API key."""
        try:
            api_key_str = self._ensure_string(self.api_key).strip()
            
            # Validate API key is not empty
            if not api_key_str:
                logger.error("Gemini API key is empty or not configured")
                return False
            
            # Configure and test the API key
            client = genai.Client(api_key=api_key_str)
            
            # Try to list models to validate the key
            models = list(client.models.list())
            
            if models:
                logger.info(f"✓ Gemini API key validated successfully ({len(models)} models available)")
                return True
            else:
                logger.warning("Gemini API key validation returned no models")
                return False
                
        except Exception as e:
            logger.error(f"✗ Gemini API key validation failed: {e}")
            return False

    def get_available_models(self) -> Dict[str, Dict]:
        """
        Return hardcoded list of free Gemini models.
        
        Returns:
            Dict mapping model IDs to model details (name, description)
        """
        try:
            logger.info(f"✓ Fetched {len(FREE_GEMINI_MODELS)} free Gemini models")
            return FREE_GEMINI_MODELS
        
        except Exception as e:
            logger.error(f"✗ Failed to fetch Gemini models: {e}")
            raise
