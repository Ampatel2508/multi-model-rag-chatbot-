#!/usr/bin/env python3
"""
Test script to verify scanned PDF extraction with OCR
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.document_processor import DocumentProcessor
import glob

def test_pdf_extraction():
    """Test PDF extraction on files in uploads directory"""
    processor = DocumentProcessor()
    
    # Find PDF files in uploads directory
    pdf_files = glob.glob("uploads/*_*.pdf")
    
    if not pdf_files:
        print("[INFO] No uploaded PDF files found")
        return
    
    print(f"\n[*] Found {len(pdf_files)} PDF file(s) to test")
    print("=" * 70)
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        doc_id = filename.split('_')[0]
        original_name = '_'.join(filename.split('_')[1:]).replace('.pdf', '')
        
        print(f"\n[*] Testing: {pdf_path}")
        print(f"    Document ID: {doc_id}")
        print(f"    Original filename: {original_name}")
        
        try:
            # Extract content
            content = processor._extract_content(pdf_path, '.pdf')
            
            if content:
                char_count = len(content)
                lines = len(content.split('\n'))
                preview = content[:200].replace('\n', ' ')
                
                print(f"\n    [OK] Extracted {char_count} characters, {lines} lines")
                print(f"    Preview: {preview}...")
                
                # Check if it looks like it used OCR
                if "---" in content and "Page" in content:
                    print(f"    [+] Contains page markers (OCR likely used)")
                
                if "Scanned with" in content:
                    print(f"    [WARNING] Contains 'Scanned with' marker - may need OCR improvement")
                
            else:
                print(f"    [ERROR] No content extracted")
                
        except Exception as e:
            print(f"    [ERROR] {type(e).__name__}: {e}")
    
    print("\n" + "=" * 70)
    print("[*] Test complete")

if __name__ == "__main__":
    test_pdf_extraction()
