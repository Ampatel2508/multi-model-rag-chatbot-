#!/usr/bin/env python
"""Test imports"""

try:
    print("Importing app.models...")
    from app import models
    print("OK - app.models imported")
    print("Attributes:", dir(models))
except Exception as e:
    import traceback
    print("ERROR importing app.models:")
    traceback.print_exc()
    
try:
    print("\nImporting app.main...")
    from app import main
    print("OK - app.main imported")
except Exception as e:
    import traceback
    print("ERROR importing app.main:")
    traceback.print_exc()
