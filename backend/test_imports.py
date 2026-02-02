#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    print("Testing imports...")
    
    print("1. Importing config...")
    from app.config import settings
    print("   ✓ Config imported successfully")
    
    print("2. Importing model_service...")
    from app.services import model_service, ModelService, validate_configuration
    print("   ✓ Model service imported successfully")
    
    print("3. Importing rag_engine...")
    from app.rag_engine import rag_engine
    print("   ✓ RAG engine imported successfully")
    
    print("4. Importing main...")
    from app.main import app
    print("   ✓ Main app imported successfully")
    
    print("\n✓ All imports successful!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n✗ Import error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)