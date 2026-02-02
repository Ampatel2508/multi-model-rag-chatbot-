#!/usr/bin/env python3
"""
Startup script for the Multi-Model RAG Chatbot API.
"""

import sys
import logging
import os

# Setup logging to see errors
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    print("Loading config...")
    from app.config import settings
    print(f"[OK] Config loaded: HOST={settings.HOST}, PORT={settings.PORT}")
    
    print("Loading FastAPI app...")
    from app.main import app
    print("[OK] FastAPI app loaded")
    
    print("Importing uvicorn...")
    import uvicorn
    print("[OK] uvicorn imported")
    
    print("\n" + "=" * 70)
    print("[*] Starting Multi-Model RAG Chatbot API")
    print("=" * 70)
    print(f"\n[+] Server Configuration:")
    print(f"   Host: {settings.HOST}")
    print(f"   Port: {settings.PORT}")
    print(f"   CORS Origins: {', '.join(settings.CORS_ORIGINS)}")
    print(f"   Upload Directory: {settings.UPLOAD_DIR}")
    print("\n" + "=" * 70 + "\n")
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"[OK] Upload directory created: {settings.UPLOAD_DIR}")
    
    print("Starting uvicorn.run()...")
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    )
    
except Exception as e:
    import traceback
    print(f"\n[ERROR] {e}")
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)