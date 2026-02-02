from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Base class for AI model providers."""
    
    def __init__(self, api_key: str, model_name: str):
        """Initialize provider with API key and model name."""
        self.api_key = self._ensure_string(api_key)
        self.model_name = self._ensure_string(model_name)
        self.llm = None
        logger.info(f"Initialized {self.__class__.__name__} with model: {self.model_name}")

    def _ensure_string(self, value: Any) -> str:
        """Ensure value is a string, not a tuple or other type."""
        if isinstance(value, tuple):
            return value[0] if value else str(value)
        return str(value) if not isinstance(value, str) else value

    @abstractmethod
    def initialize(self) -> Any:
        """Initialize and return the LLM instance."""
        pass

    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate the API key."""
        pass

    @abstractmethod
    def get_available_models(self) -> Dict[str, Dict]:
        """Fetch available models from the provider API."""
        pass

    def get_llm(self) -> Any:
        """Get the LLM instance, initializing if needed."""
        if self.llm is None:
            self.llm = self.initialize()
        return self.llm
    
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self.__class__.__name__.replace("Provider", "").lower()
