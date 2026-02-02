#!/usr/bin/env python3
"""Test script to verify document processing and RAG chain fixes."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.document_processor import DocumentProcessor
from app.rag_engine import RAGEngine
import tempfile

def test_document_processing():
    """Test document processing with text content."""
    print("=" * 70)
    print("Testing Document Processing Fix")
    print("=" * 70)
    
    processor = DocumentProcessor()
    
    # Create a test text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document.\n\n")
        f.write("It contains important information about testing.\n\n")
        f.write("The document processor should extract this content properly.")
        temp_file = f.name
    
    try:
        # Process the document
        chunks = processor.process_document(temp_file, "test.txt", ".txt")
        
        print(f"\n✓ Document processed successfully!")
        print(f"✓ Created {len(chunks)} chunk(s)")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}:")
            print(f"  Content: {chunk.page_content[:100]}...")
            print(f"  Metadata: {chunk.metadata}")
        
        # Verify content
        if chunks:
            content = chunks[0].page_content
            if "test document" in content.lower():
                print("\n✓ Document content extracted correctly!")
                return True
        
        print("\n✗ Document content not extracted properly")
        return False
        
    finally:
        os.unlink(temp_file)

def test_rag_engine_prompt():
    """Test RAG engine prompt template."""
    print("\n" + "=" * 70)
    print("Testing RAG Engine Prompt Template Fix")
    print("=" * 70)
    
    engine = RAGEngine()
    
    # Get prompt template
    prompt = engine._get_prompt_template("document")
    
    # Check variables
    print(f"\n✓ Prompt template input variables: {prompt.input_variables}")
    
    required_vars = {"context", "document_content", "input"}
    if set(prompt.input_variables) == required_vars:
        print(f"✓ All required variables present: {required_vars}")
        return True
    else:
        print(f"✗ Missing variables. Expected: {required_vars}, Got: {set(prompt.input_variables)}")
        return False

if __name__ == "__main__":
    try:
        test1 = test_document_processing()
        test2 = test_rag_engine_prompt()
        
        print("\n" + "=" * 70)
        if test1 and test2:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed")
        print("=" * 70)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
