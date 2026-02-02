import sys
import traceback

print("Step 1: Import FastAPI...")
try:
    from fastapi import FastAPI, HTTPException, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from datetime import datetime
    import logging
    print("✓ FastAPI imports OK")
except Exception as e:
    print(f"✗ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 2: Import app.config...")
try:
    from app.config import settings
    print("✓ app.config OK")
except Exception as e:
    print(f"✗ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 3: Import app.models...")
try:
    from app.models import (
        ChatRequest, ChatResponse, HealthResponse, Source,
        ModelsRequest, ModelsResponse, ProviderModels, ModelInfo,
        ErrorResponse
    )
    print("✓ app.models OK")
except Exception as e:
    print(f"✗ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 4: Import app.rag_engine...")
try:
    from app.rag_engine import rag_engine
    print("✓ app.rag_engine OK")
except Exception as e:
    print(f"✗ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 5: Import app.services...")
try:
    from app.services import model_service
    print("✓ app.services OK")
except Exception as e:
    print(f"✗ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 6: Create FastAPI app...")
try:
    app = FastAPI(
        title="Multi-Model RAG Chatbot API",
        description="Backend API for RAG Chatbot with dynamic model discovery",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    print("✓ FastAPI app created")
    print(f"app object: {app}")
except Exception as e:
    print(f"✗ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All imports successful!")
