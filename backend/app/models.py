from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict


class ModelsRequest(BaseModel):
    """Request model for fetching available models."""
    provider: str = Field(..., description="AI provider (gemini, openrouter, groq)")
    api_key: str = Field(..., description="API key for the provider")

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        """Validate provider is one of the supported options."""
        allowed = ["gemini", "openrouter", "groq"]
        if v not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        """Validate API key is not empty."""
        if not v or not v.strip():
            raise ValueError("API key cannot be empty")
        return v.strip()


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., min_length=1, max_length=2000, description="User's question")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation tracking")
    provider: str = Field(..., description="AI provider (gemini, openrouter, groq)")
    model: str = Field(..., description="Model name to use")
    api_key: str = Field(..., description="API key for the provider")
    document_ids: Optional[List[str]] = Field(default=[], description="List of uploaded document IDs to use as context")
    url: Optional[str] = Field(None, description="URL to fetch content from for RAG context")

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        """Validate provider is one of the supported options."""
        allowed = ["gemini", "openrouter", "groq"]
        if v not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v

    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        """Validate question is not empty after stripping."""
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        """Validate API key is not empty."""
        if not v or not v.strip():
            raise ValueError("API key cannot be empty")
        return v.strip()


class Source(BaseModel):
    """Source document metadata."""
    filename: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    sources: List[Source] = []
    session_id: Optional[str] = None
    model_used: str
    provider_used: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    documents_loaded: int
    chunks_created: int


class ModelInfo(BaseModel):
    """Information about a specific model."""
    id: str
    name: str
    description: str
    context_window: int
    max_output: int


class ModelsResponse(BaseModel):
    """Response containing available models for a provider."""
    success: bool
    provider: str
    models: List[ModelInfo]


class UploadResponse(BaseModel):
    """Response for file upload."""
    success: bool
    document_id: str
    filename: str
    file_type: str
    chunks_created: int
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    error_type: Optional[str] = None
    timestamp: Optional[str] = None