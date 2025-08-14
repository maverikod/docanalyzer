"""
File Processing Logger - Utility for logging file processing operations

This module provides a dedicated logger for tracking file processing operations
including start and end of processing, results, and performance metrics.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

from docanalyzer.config import get_unified_config


class FileProcessingLogger:
    """
    File Processing Logger - Dedicated logger for file processing operations
    
    Provides structured logging for file processing operations including:
    - Start of file processing
    - End of file processing with results
    - Performance metrics
    - Error tracking
    """
    
    def __init__(self):
        """Initialize the file processing logger."""
        self.config = get_unified_config()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup the file processing logger."""
        logger = logging.getLogger("file_processing")
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create log directory if it doesn't exist
        log_dir = Path(self.config.logging.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file handler for file processing log
        log_file = log_dir / self.config.logging.file_processing_log
        
        try:
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                fmt=self.config.logging.format,
                datefmt=self.config.logging.date_format
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(file_handler)
            
            # Prevent propagation to root logger
            logger.propagate = False
            
            # Test that logger works
            logger.info("File processing logger initialized successfully")
            
        except Exception as e:
            print(f"Error setting up file processing logger: {e}")
            # Fallback to console logging
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                fmt=self.config.logging.format,
                datefmt=self.config.logging.date_format
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            logger.propagate = False
        
        return logger
    
    def log_processing_start(self, file_path: str, file_size: int, file_type: str = "unknown") -> str:
        """
        Log the start of file processing.
        
        Args:
            file_path: Path to the file being processed
            file_size: Size of the file in bytes
            file_type: Type of the file (e.g., "text", "markdown", "python")
        
        Returns:
            str: Processing ID for tracking
        """
        processing_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        log_data = {
            "event": "processing_start",
            "processing_id": processing_id,
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "file_size": file_size,
            "file_type": file_type,
            "status": "started"
        }
        
        self.logger.info(f"FILE_PROCESSING_START: {json.dumps(log_data, ensure_ascii=False)}")
        
        return processing_id
    
    def log_processing_end(self, processing_id: str, file_path: str, 
                          success: bool, processing_time: float,
                          chunks_created: int = 0, error_message: Optional[str] = None,
                          additional_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log the end of file processing.
        
        Args:
            processing_id: ID returned from log_processing_start
            file_path: Path to the processed file
            success: Whether processing was successful
            processing_time: Time taken for processing in seconds
            chunks_created: Number of chunks created from the file
            error_message: Error message if processing failed
            additional_data: Additional data to log
        """
        log_data = {
            "event": "processing_end",
            "processing_id": processing_id,
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "success": success,
            "processing_time_seconds": round(processing_time, 3),
            "chunks_created": chunks_created,
            "status": "completed" if success else "failed"
        }
        
        if error_message:
            log_data["error_message"] = error_message
        
        if additional_data:
            log_data["additional_data"] = additional_data
        
        self.logger.info(f"FILE_PROCESSING_END: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_processing_error(self, processing_id: str, file_path: str, 
                           error_type: str, error_message: str,
                           additional_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log processing errors.
        
        Args:
            processing_id: ID returned from log_processing_start
            file_path: Path to the file being processed
            error_type: Type of error (e.g., "validation", "processing", "system")
            error_message: Detailed error message
            additional_data: Additional error data
        """
        log_data = {
            "event": "processing_error",
            "processing_id": processing_id,
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "error_type": error_type,
            "error_message": error_message,
            "status": "error"
        }
        
        if additional_data:
            log_data["additional_data"] = additional_data
        
        self.logger.error(f"FILE_PROCESSING_ERROR: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_processing_metrics(self, processing_id: str, file_path: str,
                             metrics: Dict[str, Any]) -> None:
        """
        Log processing metrics.
        
        Args:
            processing_id: ID returned from log_processing_start
            file_path: Path to the processed file
            metrics: Dictionary of metrics to log
        """
        log_data = {
            "event": "processing_metrics",
            "processing_id": processing_id,
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "metrics": metrics
        }
        
        self.logger.info(f"FILE_PROCESSING_METRICS: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_batch_processing_start(self, batch_id: str, file_count: int, 
                                 total_size: int) -> None:
        """
        Log the start of batch processing.
        
        Args:
            batch_id: Unique batch identifier
            file_count: Number of files in the batch
            total_size: Total size of all files in bytes
        """
        log_data = {
            "event": "batch_processing_start",
            "batch_id": batch_id,
            "timestamp": datetime.now().isoformat(),
            "file_count": file_count,
            "total_size_bytes": total_size,
            "status": "started"
        }
        
        self.logger.info(f"BATCH_PROCESSING_START: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_batch_processing_end(self, batch_id: str, processed_count: int,
                               success_count: int, failed_count: int,
                               total_processing_time: float) -> None:
        """
        Log the end of batch processing.
        
        Args:
            batch_id: Unique batch identifier
            processed_count: Total number of files processed
            success_count: Number of successfully processed files
            failed_count: Number of failed files
            total_processing_time: Total processing time in seconds
        """
        log_data = {
            "event": "batch_processing_end",
            "batch_id": batch_id,
            "timestamp": datetime.now().isoformat(),
            "processed_count": processed_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_processing_time_seconds": round(total_processing_time, 3),
            "success_rate": round(success_count / processed_count * 100, 2) if processed_count > 0 else 0,
            "status": "completed"
        }
        
        self.logger.info(f"BATCH_PROCESSING_END: {json.dumps(log_data, ensure_ascii=False)}")


# Global instance for easy access
file_processing_logger = FileProcessingLogger() 