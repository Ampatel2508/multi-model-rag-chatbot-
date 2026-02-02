print("Attempting imports...")
try:
    print("1. Importing ABC and abstractmethod...")
    from abc import ABC, abstractmethod
    print("   ✓ Success")
except Exception as e:
    print(f"   ✗ Failed: {e}")

try:
    print("2. Importing typing...")
    from typing import Any, Dict
    print("   ✓ Success")
except Exception as e:
    print(f"   ✗ Failed: {e}")

try:
    print("3. Importing logging...")
    import logging
    print("   ✓ Success")
except Exception as e:
    print(f"   ✗ Failed: {e}")

print("\nAll imports successful. Now checking the actual file...")
import sys
try:
    with open('C:\\Users\\prans\\OneDrive\\Desktop\\multi model chatbot\\backend\\app\\providers\\base_provider.py', 'r') as f:
        content = f.read()
        print(f"File size: {len(content)} bytes")
        print(f"Contains 'class BaseProvider': {'class BaseProvider' in content}")
        
        # Try to compile it
        compile(content, 'base_provider.py', 'exec')
        print("✓ File compiles successfully")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\nNow trying to execute the file content...")
try:
    with open('C:\\Users\\prans\\OneDrive\\Desktop\\multi model chatbot\\backend\\app\\providers\\base_provider.py', 'r') as f:
        code = f.read()
    
    local_namespace = {}
    exec(code, local_namespace)
    
    print("✓ File executed")
    print(f"Namespace keys: {[k for k in local_namespace.keys() if not k.startswith('_')]}")
    if 'BaseProvider' in local_namespace:
        print("✓ BaseProvider found in namespace!")
    else:
        print("✗ BaseProvider NOT in namespace")
        
except Exception as e:
    print(f"✗ Execution failed: {e}")
    import traceback
    traceback.print_exc()
