"""
Services Package - Core Services for DocAnalyzer

This package contains all core services for the DocAnalyzer application.
Services include file processing, database management, and system monitoring
components that provide the main functionality of the application.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from .lock_manager import LockManager
from .directory_scanner import DirectoryScanner
from .vector_store_wrapper import VectorStoreWrapper
from .database_manager import DatabaseManager, FileRepository
from .file_processor import FileProcessor
from .chunking_manager import ChunkingManager
from .main_process_manager import MainProcessManager
from .child_process_manager import ChildProcessManager, ChildProcessConfig
from .process_communication import ProcessCommunication, ProcessCommunicationConfig
from .directory_orchestrator import DirectoryOrchestrator, OrchestratorConfig, DirectoryProcessingStatus, OrchestrationResult
from .error_handler import ErrorHandler, ErrorHandlerConfig, ErrorInfo, ErrorRecoveryStrategy

__version__ = "1.0.0"
__version_info__ = (1, 0, 0)
__description__ = "Core services for DocAnalyzer file processing and database management"
__author__ = "DocAnalyzer Team <team@docanalyzer.com>"

__all__ = [
    '__version__',
    '__description__',
    '__author__',
    'LockManager',
    'DirectoryScanner', 
    'VectorStoreWrapper',
    'DatabaseManager',
    'FileRepository',
    'FileProcessor',
    'ChunkingManager',
    'MainProcessManager',
    'ChildProcessManager',
    'ChildProcessConfig',
    'ProcessCommunication',
    'ProcessCommunicationConfig',
    'DirectoryOrchestrator',
    'OrchestratorConfig',
    'DirectoryProcessingStatus',
    'OrchestrationResult',
    'ErrorHandler',
    'ErrorHandlerConfig',
    'ErrorInfo',
    'ErrorRecoveryStrategy'
] 