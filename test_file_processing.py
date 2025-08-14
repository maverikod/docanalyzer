#!/usr/bin/env python3
"""
Test script for file processing logging

This script tests the file processing logging functionality
by processing a test file and checking the logs.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from docanalyzer.services.file_processor import FileProcessor
from docanalyzer.services.database_manager import DatabaseManager
from docanalyzer.services.vector_store_wrapper import VectorStoreWrapper
from docanalyzer.utils.file_processing_logger import file_processing_logger


async def test_file_processing_logging():
    """Test file processing with logging."""
    print("🧪 Testing File Processing Logging")
    print("=" * 50)
    
    # Initialize services
    database_manager = DatabaseManager()
    vector_store_wrapper = VectorStoreWrapper()
    file_processor = FileProcessor(
        vector_store=vector_store_wrapper,
        database_manager=database_manager
    )
    
    # Test file path
    test_file = "test_files/test_document.txt"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📁 Processing file: {test_file}")
    print(f"📊 File size: {Path(test_file).stat().st_size} bytes")
    
    try:
        # Process the file
        result = await file_processor.process_file(test_file)
        
        print(f"✅ Processing completed!")
        print(f"   Status: {result.processing_status}")
        print(f"   Processing time: {result.processing_time_seconds:.2f}s")
        print(f"   Blocks processed: {len(result.blocks)}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        # Check log file
        log_file = Path("logs/docanalyzer/file_processing.log")
        if log_file.exists():
            print(f"\n📝 Log file created: {log_file}")
            print("📋 Log content:")
            print("-" * 30)
            with open(log_file, 'r') as f:
                for line in f:
                    if "FILE_PROCESSING" in line:
                        print(line.strip())
        else:
            print(f"❌ Log file not found: {log_file}")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()


async def test_batch_processing_logging():
    """Test batch processing with logging."""
    print("\n🧪 Testing Batch Processing Logging")
    print("=" * 50)
    
    # Initialize services
    database_manager = DatabaseManager()
    vector_store_wrapper = VectorStoreWrapper()
    file_processor = FileProcessor(
        vector_store=vector_store_wrapper,
        database_manager=database_manager
    )
    
    # Create multiple test files
    test_files = []
    for i in range(3):
        test_file = f"test_files/test_document_{i}.txt"
        content = f"This is test document {i}. It contains some content for processing."
        with open(test_file, 'w') as f:
            f.write(content)
        test_files.append(test_file)
    
    print(f"📁 Processing {len(test_files)} files in batch")
    
    try:
        # Process files in batch
        results = await file_processor.process_files_batch(test_files)
        
        print(f"✅ Batch processing completed!")
        success_count = sum(1 for r in results if r.processing_status == "completed")
        print(f"   Success: {success_count}/{len(results)}")
        
        for i, result in enumerate(results):
            print(f"   File {i+1}: {result.processing_status} ({result.processing_time_seconds:.2f}s)")
        
        # Check log file
        log_file = Path("logs/docanalyzer/file_processing.log")
        if log_file.exists():
            print(f"\n📝 Log file updated: {log_file}")
            print("📋 Batch processing log entries:")
            print("-" * 30)
            with open(log_file, 'r') as f:
                for line in f:
                    if "BATCH_PROCESSING" in line:
                        print(line.strip())
        else:
            print(f"❌ Log file not found: {log_file}")
        
    except Exception as e:
        print(f"❌ Error during batch processing: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 Starting File Processing Logging Tests")
    print("=" * 60)
    
    # Test single file processing
    await test_file_processing_logging()
    
    # Test batch processing
    await test_batch_processing_logging()
    
    print("\n🎉 Tests completed!")
    print("📁 Check the log file at: logs/docanalyzer/file_processing.log")


if __name__ == "__main__":
    asyncio.run(main()) 