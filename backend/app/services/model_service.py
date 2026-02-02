from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def _get_provider_class(provider_name: str):
    """Lazy load provider class to avoid slow imports at module load time."""
    if provider_name == "gemini":
        from app.providers.gemini_provider import GeminiProvider
        return GeminiProvider
    elif provider_name == "openrouter":
        from app.providers.openrouter_provider import OpenRouterProvider
        return OpenRouterProvider
    elif provider_name == "groq":
        from app.providers.groq_provider import GroqProvider
        return GroqProvider
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


class ModelService:
    
    PROVIDER_NAMES = ["gemini", "openrouter", "groq"]
    
    @classmethod
    def get_provider(
        cls,
        provider: str,
        model: str,
        api_key: str
    ):

        logger.info(f"Getting provider: {provider} with model: {model}")
        
        # Validate provider
        if provider not in cls.PROVIDER_NAMES:
            raise ValueError(
                f"Invalid provider: {provider}. Must be one of {cls.PROVIDER_NAMES}"
            )
        
        # Validate API key exists and is not empty
        if not api_key or not api_key.strip():
            raise ValueError(f"API key is required for {provider}")
        
        # Log API key info for debugging (safely)
        safe_key = f"{api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else '***'}"
        logger.info(f"API Key for {provider}: {safe_key} (length: {len(api_key)})")
        
        # Create and return provider instance (lazy load provider class)
        provider_class = _get_provider_class(provider)
        provider_instance = provider_class(api_key=api_key, model_name=model)
        
        logger.info(f"✓ Provider {provider} initialized successfully")
        return provider_instance
    
    @classmethod
    def get_llm_instance(
        cls,
        provider: str,
        model: str,
        api_key: str
    ):
        """Get initialized LLM instance for the given provider and model."""
        logger.info(f"Getting LLM instance: {provider}/{model}")
        
        # Get the provider instance
        provider_instance = cls.get_provider(provider, model, api_key)
        
        # Initialize and return the LLM
        llm = provider_instance.initialize()
        logger.info(f"✓ LLM instance initialized for {provider}/{model}")
        return llm
    
    @classmethod
    def validate_configuration(
        cls,
        provider: str,
        model: str,
        api_key: str
    ) -> Dict:
        
        result = {
            "valid": False,
            "provider": provider,
            "model": model,
            "errors": []
        }
        
        # Check provider exists
        if provider not in cls.PROVIDER_NAMES:
            result["errors"].append(
                f"Invalid provider: {provider}. Must be one of {cls.PROVIDER_NAMES}"
            )
            return result
        
        # Check API key
        if not api_key or not api_key.strip():
            result["errors"].append(f"API key is required for {provider}")
            return result
        
        # All validations passed
        result["valid"] = True
        logger.info(f"✓ Configuration valid for {provider}/{model}")
        return result
    
    @classmethod
    def get_available_models(cls, provider: str, api_key: str) -> Dict[str, Dict]:

        logger.info(f"Fetching available models for {provider}")
        
        # Validate provider
        if provider not in cls.PROVIDER_NAMES:
            raise ValueError(
                f"Invalid provider: {provider}. Must be one of {cls.PROVIDER_NAMES}"
            )

        # Validate API key
        if not api_key or not api_key.strip():
            raise ValueError(f"API key is required for {provider}")

        # Lazy-load provider class and create instance with a dummy model
        provider_class = _get_provider_class(provider)
        provider_instance = provider_class(api_key=api_key, model_name="dummy")
        
        # Validate API key first (if provider implements validation)
        try:
            valid_key = provider_instance.validate_api_key()
        except AttributeError:
            # If provider doesn't implement validate_api_key, assume key is valid
            valid_key = True

        if not valid_key:
            raise ValueError(f"Invalid API key for {provider}")
        
        # Fetch available models
        try:
            models = provider_instance.get_available_models()
            logger.info(f"✓ Fetched {len(models)} models for {provider}")
            return models
        except Exception as e:
            logger.error(f"✗ Failed to fetch models for {provider}: {e}")
            raise


# Singleton instance
_model_service_instance = ModelService()

# Export for backward compatibility - use the class methods
model_service = _model_service_instance


# Export validate_configuration as a module-level function for backward compatibility
def validate_configuration(provider: str, model: str, api_key: str) -> dict:
    """Validate provider configuration."""
    return ModelService.validate_configuration(provider, model, api_key)