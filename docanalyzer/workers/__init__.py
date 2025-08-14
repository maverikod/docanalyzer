"""
Workers Package - Child Process Workers

This package contains worker processes that perform directory scanning
and file processing operations in isolation from the main process.

The workers communicate with the main process through IPC mechanisms
and handle the actual scanning and processing tasks.

Author: File Watcher Team
Version: 1.0.0
"""

from .directory_scanner_worker import (
    DirectoryScannerWorker,
    WorkerConfig,
    WorkerStatus
)

__all__ = [
    'DirectoryScannerWorker',
    'WorkerConfig', 
    'WorkerStatus'
] 