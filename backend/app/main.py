#!/usr/bin/env python3
"""
FastAPI Backend for Multi-Model RAG Chatbot
"""
# Fix OpenMP duplicate library error
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import uuid
from typing import List
import glob

from app.config import settings
from app.models import (
    ChatRequest, ChatResponse, Source, HealthResponse,
    ModelsRequest, ModelsResponse, ModelInfo, UploadResponse
)
from app.document_processor import DocumentProcessor
from app.rag_engine import RAGEngine
from app.content_moderator import ContentModerator
from app.memory_manager import get_memory_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Multi-Model RAG Chatbot API",
    description="Backend API for RAG Chatbot with dynamic model discovery and document upload",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
document_processor = DocumentProcessor()
rag_engine = RAGEngine()
content_moderator = ContentModerator()
memory_manager = get_memory_manager()

logger.info("FastAPI app created successfully")


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("=" * 70)
    logger.info("[*] Starting Multi-Model RAG Chatbot API v2.0.0")
    logger.info("=" * 70)
    
    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"[*] Upload directory: {settings.UPLOAD_DIR}")
    logger.info("[*] Ready for document uploads (no pre-loaded documents)")
    # NOTE: Documents are loaded only when user uploads them via API
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("🛑 Shutting down Multi-Model RAG Chatbot API...")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    logger.info("Root endpoint called")
    return {
        "message": "Multi-Model RAG Chatbot API",
        "version": "2.0.0",
        "status": "running",
        "providers": ["gemini", "openrouter", "groq"],
        "features": ["document_upload", "web_crawl", "multi_model"],
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    logger.info("Health check called")
    stats = rag_engine.get_stats()
    
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        documents_loaded=stats["documents_loaded"],
        chunks_created=stats["chunks_created"]
    )


@app.post("/api/models", response_model=ModelsResponse)
async def get_models(request: ModelsRequest):

    logger.info(f"Fetching models for provider: {request.provider}")
    
    try:
        from app.services.model_service import ModelService
        
        # Get available models
        models_dict = ModelService.get_available_models(request.provider, request.api_key)
        
        # Convert to list of ModelInfo
        models_list = [
            ModelInfo(
                id=model_id,
                name=info["name"],
                description=info["description"],
                context_window=info["context_window"],
                max_output=info["max_output"]
            )
            for model_id, info in models_dict.items()
        ]
        
        logger.info(f"✓ Found {len(models_list)} models for {request.provider}")
        
        return ModelsResponse(
            success=True,
            provider=request.provider,
            models=models_list
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch models: {str(e)}"
        )


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):

    logger.info(f"Uploading document: {file.filename}")
    
    try:
        # Validate file
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File saved: {file_path}")
        
        # Process document
        chunks = document_processor.process_document(file_path, file.filename, file_ext)
        
        # Add to RAG engine
        rag_engine.add_documents(document_id, chunks)
        
        logger.info(f"✓ Document processed: {len(chunks)} chunks created")
        
        return UploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            file_type=file_ext,
            chunks_created=len(chunks),
            message=f"Successfully processed {file.filename}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat request with user-provided API key and selected model.
    """
    logger.info("=" * 60)
    logger.info("💬 Chat endpoint called")
    logger.info(f"Question: {request.question[:100]}...")
    logger.info(f"Provider: {request.provider}, Model: {request.model}")
    logger.info(f"Document IDs: {request.document_ids}")
    
    try:
        # Validate API key is provided first (needed for LLM initialization)
        if not request.api_key or not request.api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key is required"
            )
        
        # Validate configuration
        from app.services.model_service import ModelService
        validation = ModelService.validate_configuration(
            provider=request.provider,
            model=request.model,
            api_key=request.api_key
        )
        
        if not validation["valid"]:
            logger.warning(f"Configuration validation failed: {validation['errors']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid configuration",
                    "errors": validation["errors"]
                }
            )
        
        # Initialize LLM for moderation response generation
        from app.services.model_service import ModelService as MS
        llm = MS.get_llm_instance(
            provider=request.provider,
            model=request.model,
            api_key=request.api_key
        )
        
        # Content Moderation: Check for abusive language and misbehavior
        logger.info("[*] Running content moderation...")
        is_clean, moderation_message = content_moderator.moderate(request.question, llm=llm)
        
        if not is_clean:
            logger.warning(f"⚠️ Content moderation flag triggered: {moderation_message[:50]}...")
            sources = []  # No sources for moderation responses
            response = ChatResponse(
                answer=moderation_message,
                sources=sources,
                session_id=request.session_id,
                model_used="content-moderator",
                provider_used="system"
            )
            logger.info("=" * 60)
            return response
        
        logger.info("[✓] Content passed moderation check")
        
        # Validate document IDs if provided
        if request.document_ids:
            available_docs = rag_engine.list_documents()
            invalid_docs = [doc_id for doc_id in request.document_ids if doc_id not in available_docs]
            if invalid_docs:
                logger.warning(f"Invalid document IDs requested: {invalid_docs}")
                logger.info(f"Available documents: {available_docs}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "One or more document IDs are invalid",
                        "invalid_ids": invalid_docs,
                        "available_ids": available_docs
                    }
                )
        
        # Get answer from RAG engine
        result = rag_engine.ask(
            question=request.question,
            provider=request.provider,
            model=request.model,
            api_key=request.api_key,
            document_ids=request.document_ids,
            url=request.url,
            session_id=request.session_id
        )
        
        # Convert sources to Source models
        sources = [Source(**source) for source in result["sources"]]
        
        response = ChatResponse(
            answer=result["answer"],
            sources=sources,
            session_id=request.session_id,
            model_used=result["model"],
            provider_used=result["provider"]
        )
        
        # Save message to memory for conversation context
        try:
            logger.info(f"[*] Saving to memory for session: {request.session_id}")
            memory_manager.add_message(
                session_id=request.session_id,
                user_message=request.question,
                ai_response=result["answer"]
            )
            logger.info(f"[✓] Message saved to memory")
        except Exception as e:
            logger.warning(f"Failed to save message to memory: {e}")
        
        logger.info(f"✓ Successfully generated answer with {len(sources)} sources")
        logger.info("=" * 60)
        return response
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        
        # Extract meaningful error message
        error_msg = str(e)
        
        if "401" in error_msg or "INVALID_ARGUMENT" in error_msg or "unauthorized" in error_msg.lower():
            detail = "Authentication failed: Invalid API key. Please verify your API key."
        elif "400" in error_msg or "invalid" in error_msg.lower():
            detail = f"Invalid request: {error_msg}"
        else:
            detail = f"Error processing request: {error_msg}"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@app.get("/api/documents")
async def list_documents():
    """List uploaded document IDs currently loaded in the RAG engine."""
    docs = []
    for doc_id, chunks in rag_engine.document_store.items():
        filename = None
        if chunks and hasattr(chunks[0], "metadata"):
            filename = chunks[0].metadata.get("filename")
        docs.append({
            "id": doc_id,
            "filename": filename or f"{doc_id}",
            "chunks_created": len(chunks)
        })

    return {"documents": docs, "count": len(docs)}


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the RAG engine and remove its uploaded file(s)."""
    logger.info(f"Request to delete document: {document_id}")
    removed_files = []
    removed_doc_ids = []

    # Determine filename for this document from RAG engine if available
    filename = None
    if document_id in rag_engine.document_store and rag_engine.document_store[document_id]:
        filename = rag_engine.document_store[document_id][0].metadata.get("filename")

    # If we found a filename, remove all RAG entries and files matching that filename
    if filename:
        logger.info(f"Deleting all documents with filename: {filename}")

        # Remove RAG entries that reference this filename
        to_remove = [did for did, chunks in list(rag_engine.document_store.items()) if chunks and chunks[0].metadata.get("filename") == filename]
        logger.info(f"Document IDs to remove for filename {filename}: {to_remove}")
        for did in to_remove:
            if rag_engine.remove_document(did):
                removed_doc_ids.append(did)

        # Remove files on disk matching *_<filename>
        pattern = os.path.join(settings.UPLOAD_DIR, f"*_{filename}")
        logger.info(f"Attempting to remove files with pattern: {pattern}")
        matches = glob.glob(pattern)
        logger.info(f"Files matched for deletion: {matches}")
        for path in matches:
            try:
                os.remove(path)
                removed_files.append(path)
            except Exception as e:
                logger.warning(f"Failed to remove file {path}: {e}")

    else:
        # Fallback: try removing by document_id prefix only
        pattern = os.path.join(settings.UPLOAD_DIR, f"{document_id}_*")
        logger.info(f"Attempting fallback remove files with pattern: {pattern}")
        matches = glob.glob(pattern)
        logger.info(f"Files matched for deletion: {matches}")
        for path in matches:
            try:
                os.remove(path)
                removed_files.append(path)
            except Exception as e:
                logger.warning(f"Failed to remove file {path}: {e}")

        if rag_engine.remove_document(document_id):
            removed_doc_ids.append(document_id)

    if not removed_doc_ids and not removed_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    return {
        "success": True,
        "requested_id": document_id,
        "removed_doc_ids": removed_doc_ids,
        "files_removed": removed_files,
        "message": "Document(s) removed from RAG engine"
    }


@app.get("/api/memory/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get chat history for a specific session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Chat history with messages
    """
    logger.info(f"Fetching chat history for session: {session_id}")
    
    try:
        chat_history = memory_manager.get_chat_history(session_id)
        summary = memory_manager.get_session_summary(session_id)
        
        return {
            "status": "success",
            "session_id": session_id,
            "summary": summary,
            "history": chat_history,
            "messages": memory_manager.export_session(session_id)
        }
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chat history: {str(e)}"
        )


@app.get("/api/memory/summary/{session_id}")
async def get_session_summary(session_id: str):
    """
    Get summary of a chat session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session summary with message count and preview
    """
    logger.info(f"Fetching summary for session: {session_id}")
    
    try:
        summary = memory_manager.get_session_summary(session_id)
        return {
            "status": "success",
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error fetching session summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session summary: {str(e)}"
        )


@app.post("/api/memory/export/{session_id}")
async def export_session(session_id: str):
    """
    Export chat session history as JSON.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Exported session data
    """
    logger.info(f"Exporting session: {session_id}")
    
    try:
        exported = memory_manager.export_session(session_id)
        return {
            "status": "success",
            "data": exported
        }
    except Exception as e:
        logger.error(f"Error exporting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export session: {str(e)}"
        )


@app.delete("/api/memory/clear/{session_id}")
async def clear_session(session_id: str):
    """
    Clear memory for a specific session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Confirmation message
    """
    logger.info(f"Clearing memory for session: {session_id}")
    
    try:
        memory_manager.clear_session(session_id)
        return {
            "status": "success",
            "message": f"Session {session_id} memory cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session: {str(e)}"
        )


@app.delete("/api/memory/clear-all")
async def clear_all_memory():
    """
    Clear memory for all sessions.
    
    Returns:
        Confirmation message
    """
    logger.warning("Clearing memory for all sessions")
    
    try:
        memory_manager.clear_all_sessions()
        return {
            "status": "success",
            "message": "All sessions cleared from memory"
        }
    except Exception as e:
        logger.error(f"Error clearing all sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear all sessions: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )