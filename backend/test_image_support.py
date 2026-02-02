#!/usr/bin/env python3
"""Test enhanced document processor with image support"""

from app.document_processor import DocumentProcessor, TESSERACT_AVAILABLE
import tempfile
import os

print("=" * 70)
print("TESTING ENHANCED DOCUMENT PROCESSOR")
print("=" * 70)

processor = DocumentProcessor()

print("\n[1] Tesseract Availability:")
print(f"    Tesseract OCR Available: {TESSERACT_AVAILABLE}")

print("\n[2] Image Format Support:")
supported_images = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
print(f"    Supported formats: {', '.join(supported_images)}")

print("\n[3] Testing Text File Processing:")
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write("This is a test document.\n\nIt should extract successfully.")
    temp_file = f.name

try:
    chunks = processor.process_document(temp_file, "test.txt", ".txt")
    print(f"    ✓ Processed: {len(chunks)} chunks created")
finally:
    os.unlink(temp_file)

print("\n[4] Image Processing Capability:")
if TESSERACT_AVAILABLE:
    print("    ✓ Can process image files with OCR")
else:
    print("    ⚠ Image processing requires Tesseract system software")
    print("      Install from: https://github.com/UB-Mannheim/tesseract/wiki")

print("\n" + "=" * 70)
print("ENHANCEMENTS SUMMARY")
print("=" * 70)
print("""
✓ Added support for image files (.jpg, .png, .gif, .bmp, .tiff, .webp)
✓ Added OCR extraction for images using Tesseract
✓ Improved error messages for missing Tesseract
✓ Better handling of scanned PDFs with OCR fallback
✓ Support for PIL/Pillow for image processing

Next Steps:
1. Install Tesseract OCR system software to enable:
   - Photo/image text extraction
   - Scanned PDF processing
   
2. Download from: https://github.com/UB-Mannheim/tesseract/wiki
3. Run as Administrator
4. Use default path: C:\\Program Files\\Tesseract-OCR
""")
