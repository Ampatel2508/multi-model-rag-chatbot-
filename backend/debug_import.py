import sys
import traceback

try:
    print("Attempting to import app.main...")
    from app import main
    print("✓ main module imported")
    print(f"Attributes in main: {[x for x in dir(main) if not x.startswith('_')]}")
except Exception as e:
    print(f"✗ ERROR importing main: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
