#!/usr/bin/env python3
"""
Debug run script
"""
import sys
import traceback

try:
    print("Loading config...")
    from app.config import settings
    print(f"✓ Config loaded: HOST={settings.HOST}, PORT={settings.PORT}")
    
    print("\nLoading FastAPI app...")
    from app.main import app
    print("✓ FastAPI app loaded")
    
    print("\nStarting uvicorn server...")
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    )
except Exception as e:
    print(f"\nERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
