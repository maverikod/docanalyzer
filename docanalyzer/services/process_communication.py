"""
Process Communication - Inter-Process Communication (IPC)

Provides communication mechanisms between parent and child processes
for directory scanning operations.

The process communication module handles message passing, result sharing,
and status updates between the main process and worker processes.

Author: File Watcher Team
Version: 1.0.0
"""

import asyncio
import json
import multiprocessing
import pickle
import queue
import signal
import sys
import os
from typing import Dict, List, Optional, Any, Union, Callable
from pathlib import Path
import logging
from datetime import datetime
import threading
import time

from docanalyzer.models.file_system import FileInfo, Directory
from docanalyzer.models.processing import ProcessingResult
from docanalyzer.models.errors import ProcessingError

logger = logging.getLogger(__name__)

DEFAULT_QUEUE_SIZE = 1000
DEFAULT_TIMEOUT = 30
DEFAULT_HEARTBEAT_INTERVAL = 5


class ProcessMessage:
    """
    Message for inter-process communication.
    
    Represents a message sent between parent and child processes
    for coordination and data exchange.
    
    Attributes:
        message_id (str): Unique identifier for the message.
        message_type (str): Type of message (command, result, status, error).
        timestamp (datetime): When the message was created.
        payload (Dict[str, Any]): Message payload data.
        source_pid (int): Process ID of the message sender.
        target_pid (Optional[int]): Process ID of the message target.
    """
    
    def __init__(
        self,
        message_id: str,
        message_type: str,
        payload: Dict[str, Any],
        source_pid: int,
        target_pid: Optional[int] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize ProcessMessage instance.
        
        Args:
            message_id (str): Unique identifier for the message.
            message_type (str): Type of message (command, result, status, error).
            payload (Dict[str, Any]): Message payload data.
            source_pid (int): Process ID of the message sender.
            target_pid (Optional[int]): Process ID of the message target.
                Defaults to None.
            timestamp (Optional[datetime]): When the message was created.
                Defaults to current time.
        """
        self.message_id = message_id
        self.message_type = message_type
        self.payload = payload
        self.source_pid = source_pid
        self.target_pid = target_pid
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of message.
        """
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload.copy(),
            "source_pid": self.source_pid,
            "target_pid": self.target_pid
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessMessage':
        """
        Create instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary data.
        
        Returns:
            ProcessMessage: Created instance.
        
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("data must be dictionary")
        
        required_fields = ["message_id", "message_type", "payload", "source_pid"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' missing in data")
        
        return cls(
            message_id=data["message_id"],
            message_type=data["message_type"],
            payload=data["payload"],
            source_pid=data["source_pid"],
            target_pid=data.get("target_pid"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        )
    
    def serialize(self) -> bytes:
        """
        Serialize message to bytes.
        
        Returns:
            bytes: Serialized message data.
        """
        return pickle.dumps(self.to_dict())
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'ProcessMessage':
        """
        Deserialize message from bytes.
        
        Args:
            data (bytes): Serialized message data.
        
        Returns:
            ProcessMessage: Deserialized message.
        
        Raises:
            ValueError: If data is invalid
        """
        try:
            message_data = pickle.loads(data)
            return cls.from_dict(message_data)
        except (pickle.PickleError, ValueError) as e:
            raise ValueError(f"Failed to deserialize message: {e}")


class ProcessCommunicationConfig:
    """
    Configuration for process communication.
    
    Contains settings for inter-process communication mechanisms.
    
    Attributes:
        queue_size (int): Maximum size of message queues.
            Must be positive integer. Defaults to 1000.
        timeout (int): Timeout for message operations in seconds.
            Must be positive integer. Defaults to 30.
        heartbeat_interval (int): Interval for heartbeat messages in seconds.
            Must be positive integer. Defaults to 5.
        enable_encryption (bool): Whether to enable message encryption.
            Defaults to False.
        enable_compression (bool): Whether to enable message compression.
            Defaults to False.
        max_message_size (int): Maximum size of individual messages in bytes.
            Must be positive integer. Defaults to 1048576 (1MB).
    """
    
    def __init__(
        self,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        timeout: int = DEFAULT_TIMEOUT,
        heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
        enable_encryption: bool = False,
        enable_compression: bool = False,
        max_message_size: int = 1048576
    ):
        """
        Initialize ProcessCommunicationConfig instance.
        
        Args:
            queue_size (int): Maximum size of message queues.
                Must be positive integer. Defaults to 1000.
            timeout (int): Timeout for message operations in seconds.
                Must be positive integer. Defaults to 30.
            heartbeat_interval (int): Interval for heartbeat messages in seconds.
                Must be positive integer. Defaults to 5.
            enable_encryption (bool): Whether to enable message encryption.
                Defaults to False.
            enable_compression (bool): Whether to enable message compression.
                Defaults to False.
            max_message_size (int): Maximum size of individual messages in bytes.
                Must be positive integer. Defaults to 1048576 (1MB).
        
        Raises:
            ValueError: If any parameter has invalid value
        """
        if queue_size <= 0:
            raise ValueError("queue_size must be positive")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if heartbeat_interval <= 0:
            raise ValueError("heartbeat_interval must be positive")
        if max_message_size <= 0:
            raise ValueError("max_message_size must be positive")
        
        self.queue_size = queue_size
        self.timeout = timeout
        self.heartbeat_interval = heartbeat_interval
        self.enable_encryption = enable_encryption
        self.enable_compression = enable_compression
        self.max_message_size = max_message_size


class ProcessCommunication:
    """
    Process Communication - Inter-Process Communication (IPC)
    
    Handles communication between parent and child processes for
    directory scanning operations.
    
    The communication module provides message passing, result sharing,
    and status updates between processes using queues and shared memory.
    
    Attributes:
        config (ProcessCommunicationConfig): Configuration for communication.
        message_queue (multiprocessing.Queue): Queue for message exchange.
        result_queue (multiprocessing.Queue): Queue for result exchange.
        status_queue (multiprocessing.Queue): Queue for status updates.
        process_id (int): ID of the current process.
        message_handlers (Dict[str, Callable]): Registered message handlers.
    
    Example:
        >>> config = ProcessCommunicationConfig()
        >>> comm = ProcessCommunication(config)
        >>> await comm.send_message(message)
        >>> result = await comm.receive_message()
    """
    
    def __init__(self, config: ProcessCommunicationConfig):
        """
        Initialize ProcessCommunication instance.
        
        Args:
            config (ProcessCommunicationConfig): Configuration for communication.
                Must be valid ProcessCommunicationConfig instance.
        
        Raises:
            ValueError: If config is invalid
        """
        if not isinstance(config, ProcessCommunicationConfig):
            raise ValueError("config must be ProcessCommunicationConfig instance")
        
        self.config = config
        self.process_id = os.getpid()
        self.message_handlers: Dict[str, Callable] = {}
        
        # Create queues
        self.message_queue = multiprocessing.Queue(maxsize=config.queue_size)
        self.result_queue = multiprocessing.Queue(maxsize=config.queue_size)
        self.status_queue = multiprocessing.Queue(maxsize=config.queue_size)
        
        # Heartbeat tracking
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    async def send_message(self, message: ProcessMessage) -> bool:
        """
        Send message to another process.
        
        Sends a message to the target process through the message queue.
        The message is serialized and placed in the appropriate queue.
        
        Args:
            message (ProcessMessage): Message to send.
                Must be valid ProcessMessage instance.
        
        Returns:
            bool: True if message was sent successfully, False otherwise.
        
        Raises:
            ValueError: If message is invalid
            QueueFullError: If message queue is full
            TimeoutError: If operation times out
        """
        if not isinstance(message, ProcessMessage):
            raise ValueError("message must be ProcessMessage instance")
        
        if not self._validate_message(message):
            raise ValueError("Invalid message format")
        
        try:
            serialized_message = message.serialize()
            if len(serialized_message) > self.config.max_message_size:
                raise ValueError(f"Message size {len(serialized_message)} exceeds limit {self.config.max_message_size}")
            
            # Use asyncio to run queue operation in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self.message_queue.put(serialized_message, timeout=self.config.timeout)
            )
            
            logger.debug(f"Sent message {message.message_id} to queue")
            return True
            
        except queue.Full:
            from docanalyzer.models.errors import QueueFullError
            raise QueueFullError("Message queue is full", "message_queue")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def receive_message(self, timeout: Optional[int] = None) -> Optional[ProcessMessage]:
        """
        Receive message from another process.
        
        Receives a message from the message queue. Blocks until a message
        is available or timeout is reached.
        
        Args:
            timeout (Optional[int]): Timeout in seconds.
                Defaults to config timeout.
        
        Returns:
            Optional[ProcessMessage]: Received message or None if timeout.
        
        Raises:
            TimeoutError: If operation times out
            QueueEmptyError: If queue is empty
        """
        timeout = timeout or self.config.timeout
        
        try:
            loop = asyncio.get_event_loop()
            serialized_message = await loop.run_in_executor(
                None,
                lambda: self.message_queue.get(timeout=timeout)
            )
            
            message = ProcessMessage.deserialize(serialized_message)
            logger.debug(f"Received message {message.message_id}")
            return message
            
        except queue.Empty:
            from docanalyzer.models.errors import QueueEmptyError
            raise QueueEmptyError("Message queue is empty", "message_queue")
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None
    
    async def send_result(self, result: ProcessingResult) -> bool:
        """
        Send processing result to parent process.
        
        Sends a processing result to the parent process through
        the result queue.
        
        Args:
            result (ProcessingResult): Processing result to send.
                Must be valid ProcessingResult instance.
        
        Returns:
            bool: True if result was sent successfully, False otherwise.
        
        Raises:
            ValueError: If result is invalid
            QueueFullError: If result queue is full
        """
        if not isinstance(result, ProcessingResult):
            raise ValueError("result must be ProcessingResult instance")
        
        try:
            serialized_result = pickle.dumps(result.to_dict())
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.result_queue.put(serialized_result, timeout=self.config.timeout)
            )
            
            logger.debug(f"Sent result to queue")
            return True
            
        except queue.Full:
            from docanalyzer.models.errors import QueueFullError
            raise QueueFullError("Result queue is full", "result_queue")
        except Exception as e:
            logger.error(f"Failed to send result: {e}")
            return False
    
    async def receive_result(self, timeout: Optional[int] = None) -> Optional[ProcessingResult]:
        """
        Receive processing result from child process.
        
        Receives a processing result from a child process through
        the result queue.
        
        Args:
            timeout (Optional[int]): Timeout in seconds.
                Defaults to config timeout.
        
        Returns:
            Optional[ProcessingResult]: Received result or None if timeout.
        
        Raises:
            TimeoutError: If operation times out
            QueueEmptyError: If queue is empty
        """
        timeout = timeout or self.config.timeout
        
        try:
            loop = asyncio.get_event_loop()
            serialized_result = await loop.run_in_executor(
                None,
                lambda: self.result_queue.get(timeout=timeout)
            )
            
            result_data = pickle.loads(serialized_result)
            result = ProcessingResult.from_dict(result_data)
            logger.debug(f"Received result from queue")
            return result
            
        except queue.Empty:
            from docanalyzer.models.errors import QueueEmptyError
            raise QueueEmptyError("Result queue is empty", "result_queue")
        except Exception as e:
            logger.error(f"Failed to receive result: {e}")
            return None
    
    async def send_status_update(self, status: Dict[str, Any]) -> bool:
        """
        Send status update to parent process.
        
        Sends a status update to the parent process through
        the status queue.
        
        Args:
            status (Dict[str, Any]): Status information to send.
                Must be valid status dictionary.
        
        Returns:
            bool: True if status was sent successfully, False otherwise.
        
        Raises:
            ValueError: If status is invalid
            QueueFullError: If status queue is full
        """
        if not isinstance(status, dict):
            raise ValueError("status must be dictionary")
        
        try:
            serialized_status = pickle.dumps(status)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.status_queue.put(serialized_status, timeout=self.config.timeout)
            )
            
            logger.debug(f"Sent status update to queue")
            return True
            
        except queue.Full:
            from docanalyzer.models.errors import QueueFullError
            raise QueueFullError("Status queue is full", "status_queue")
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
            return False
    
    async def receive_status_update(self, timeout: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Receive status update from child process.
        
        Receives a status update from a child process through
        the status queue.
        
        Args:
            timeout (Optional[int]): Timeout in seconds.
                Defaults to config timeout.
        
        Returns:
            Optional[Dict[str, Any]]: Received status or None if timeout.
        
        Raises:
            TimeoutError: If operation times out
            QueueEmptyError: If queue is empty
        """
        timeout = timeout or self.config.timeout
        
        try:
            loop = asyncio.get_event_loop()
            serialized_status = await loop.run_in_executor(
                None,
                lambda: self.status_queue.get(timeout=timeout)
            )
            
            status = pickle.loads(serialized_status)
            logger.debug(f"Received status update from queue")
            return status
            
        except queue.Empty:
            from docanalyzer.models.errors import QueueEmptyError
            raise QueueEmptyError("Status queue is empty", "status_queue")
        except Exception as e:
            logger.error(f"Failed to receive status update: {e}")
            return None
    
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register message handler.
        
        Registers a handler function for a specific message type.
        The handler will be called when messages of that type are received.
        
        Args:
            message_type (str): Type of message to handle.
            handler (Callable): Handler function to call.
                Must accept ProcessMessage as argument.
        """
        if not isinstance(message_type, str):
            raise ValueError("message_type must be string")
        if not callable(handler):
            raise ValueError("handler must be callable")
        
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")
    
    async def start_heartbeat(self) -> None:
        """
        Start heartbeat mechanism.
        
        Starts sending periodic heartbeat messages to indicate
        that the process is still alive and responsive.
        """
        if self._heartbeat_task is not None:
            return
        
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Started heartbeat mechanism")
    
    async def stop_heartbeat(self) -> None:
        """
        Stop heartbeat mechanism.
        
        Stops sending heartbeat messages.
        """
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("Stopped heartbeat mechanism")
    
    async def cleanup(self) -> None:
        """
        Clean up communication resources.
        
        Closes all queues and cleans up any allocated resources.
        Should be called when the process is shutting down.
        """
        self._shutdown_event.set()
        
        # Stop heartbeat
        await self.stop_heartbeat()
        
        # Close queues
        try:
            self.message_queue.close()
            self.result_queue.close()
            self.status_queue.close()
        except Exception as e:
            logger.warning(f"Error closing queues: {e}")
        
        logger.info("Cleaned up communication resources")
    
    def _create_message_id(self) -> str:
        """
        Create unique message ID.
        
        Returns:
            str: Unique message identifier.
        """
        import uuid
        return f"{self.process_id}_{uuid.uuid4().hex[:8]}"
    
    def _validate_message(self, message: ProcessMessage) -> bool:
        """
        Validate message format and content.
        
        Args:
            message (ProcessMessage): Message to validate.
        
        Returns:
            bool: True if message is valid, False otherwise.
        """
        if not isinstance(message, ProcessMessage):
            return False
        
        if not message.message_id or not message.message_type:
            return False
        
        if not isinstance(message.payload, dict):
            return False
        
        if message.source_pid <= 0:
            return False
        
        return True
    
    async def _heartbeat_loop(self) -> None:
        """
        Heartbeat loop for sending periodic heartbeat messages.
        """
        while not self._shutdown_event.is_set():
            try:
                heartbeat_message = ProcessMessage(
                    message_id=self._create_message_id(),
                    message_type="heartbeat",
                    payload={"timestamp": datetime.now().isoformat()},
                    source_pid=self.process_id
                )
                
                await self.send_message(heartbeat_message)
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.config.heartbeat_interval) 