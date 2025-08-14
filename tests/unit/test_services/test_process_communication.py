"""
Tests for Process Communication

Comprehensive test suite for inter-process communication functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import pickle
import queue

from docanalyzer.services.process_communication import (
    ProcessMessage,
    ProcessCommunicationConfig,
    ProcessCommunication
)
from docanalyzer.models.processing import ProcessingResult
from docanalyzer.models.errors import QueueFullError, QueueEmptyError


class TestProcessMessage:
    """Test suite for ProcessMessage class."""
    
    def test_init_valid_message(self):
        """Test valid message initialization."""
        message = ProcessMessage(
            message_id="test_123",
            message_type="command",
            payload={"data": "test"},
            source_pid=12345
        )
        
        assert message.message_id == "test_123"
        assert message.message_type == "command"
        assert message.payload == {"data": "test"}
        assert message.source_pid == 12345
        assert message.target_pid is None
        assert isinstance(message.timestamp, datetime)
    
    def test_init_with_target_pid(self):
        """Test message initialization with target PID."""
        message = ProcessMessage(
            message_id="test_123",
            message_type="command",
            payload={"data": "test"},
            source_pid=12345,
            target_pid=67890
        )
        
        assert message.target_pid == 67890
    
    def test_to_dict(self):
        """Test message to dictionary conversion."""
        message = ProcessMessage(
            message_id="test_123",
            message_type="command",
            payload={"data": "test"},
            source_pid=12345
        )
        
        data = message.to_dict()
        
        assert data["message_id"] == "test_123"
        assert data["message_type"] == "command"
        assert data["payload"] == {"data": "test"}
        assert data["source_pid"] == 12345
        assert data["target_pid"] is None
        assert "timestamp" in data
    
    def test_from_dict_valid(self):
        """Test creating message from valid dictionary."""
        data = {
            "message_id": "test_123",
            "message_type": "command",
            "payload": {"data": "test"},
            "source_pid": 12345,
            "timestamp": datetime.now().isoformat()
        }
        
        message = ProcessMessage.from_dict(data)
        
        assert message.message_id == "test_123"
        assert message.message_type == "command"
        assert message.payload == {"data": "test"}
        assert message.source_pid == 12345
    
    def test_from_dict_missing_field(self):
        """Test creating message from dictionary with missing field."""
        data = {
            "message_id": "test_123",
            "message_type": "command",
            # Missing payload and source_pid
        }
        
        with pytest.raises(ValueError, match="Required field 'payload' missing"):
            ProcessMessage.from_dict(data)
    
    def test_from_dict_invalid_type(self):
        """Test creating message from invalid data type."""
        with pytest.raises(ValueError, match="data must be dictionary"):
            ProcessMessage.from_dict("invalid")
    
    def test_serialize_deserialize(self):
        """Test message serialization and deserialization."""
        original_message = ProcessMessage(
            message_id="test_123",
            message_type="command",
            payload={"data": "test"},
            source_pid=12345
        )
        
        serialized = original_message.serialize()
        deserialized = ProcessMessage.deserialize(serialized)
        
        assert deserialized.message_id == original_message.message_id
        assert deserialized.message_type == original_message.message_type
        assert deserialized.payload == original_message.payload
        assert deserialized.source_pid == original_message.source_pid
    
    def test_deserialize_invalid_data(self):
        """Test deserializing invalid data."""
        with pytest.raises(ValueError, match="Failed to deserialize message"):
            ProcessMessage.deserialize(b"invalid_data")


class TestProcessCommunicationConfig:
    """Test suite for ProcessCommunicationConfig class."""
    
    def test_init_valid_config(self):
        """Test valid configuration initialization."""
        config = ProcessCommunicationConfig(
            queue_size=500,
            timeout=15,
            heartbeat_interval=3,
            enable_encryption=True,
            enable_compression=True,
            max_message_size=2097152
        )
        
        assert config.queue_size == 500
        assert config.timeout == 15
        assert config.heartbeat_interval == 3
        assert config.enable_encryption is True
        assert config.enable_compression is True
        assert config.max_message_size == 2097152
    
    def test_init_defaults(self):
        """Test configuration initialization with defaults."""
        config = ProcessCommunicationConfig()
        
        assert config.queue_size == 1000
        assert config.timeout == 30
        assert config.heartbeat_interval == 5
        assert config.enable_encryption is False
        assert config.enable_compression is False
        assert config.max_message_size == 1048576
    
    def test_init_invalid_queue_size(self):
        """Test configuration with invalid queue size."""
        with pytest.raises(ValueError, match="queue_size must be positive"):
            ProcessCommunicationConfig(queue_size=0)
    
    def test_init_invalid_timeout(self):
        """Test configuration with invalid timeout."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            ProcessCommunicationConfig(timeout=-1)
    
    def test_init_invalid_heartbeat_interval(self):
        """Test configuration with invalid heartbeat interval."""
        with pytest.raises(ValueError, match="heartbeat_interval must be positive"):
            ProcessCommunicationConfig(heartbeat_interval=0)
    
    def test_init_invalid_max_message_size(self):
        """Test configuration with invalid max message size."""
        with pytest.raises(ValueError, match="max_message_size must be positive"):
            ProcessCommunicationConfig(max_message_size=-1)


class TestProcessCommunication:
    """Test suite for ProcessCommunication class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ProcessCommunicationConfig(
            queue_size=10,
            timeout=5,
            heartbeat_interval=1
        )
    
    @pytest.fixture
    def communication(self, config):
        """Create test communication instance."""
        return ProcessCommunication(config)
    
    def test_init_valid_communication(self, config):
        """Test valid communication initialization."""
        comm = ProcessCommunication(config)
        
        assert comm.config == config
        assert comm.process_id > 0
        assert comm.message_handlers == {}
        assert comm._heartbeat_task is None
    
    def test_init_invalid_config(self):
        """Test communication initialization with invalid config."""
        with pytest.raises(ValueError, match="config must be ProcessCommunicationConfig instance"):
            ProcessCommunication("invalid_config")
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, communication):
        """Test successful message sending."""
        message = ProcessMessage(
            message_id="test_123",
            message_type="command",
            payload={"data": "test"},
            source_pid=12345
        )
        
        with patch.object(communication.message_queue, 'put') as mock_put:
            result = await communication.send_message(message)
            
            assert result is True
            mock_put.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_invalid_message(self, communication):
        """Test sending invalid message."""
        with pytest.raises(ValueError, match="message must be ProcessMessage instance"):
            await communication.send_message("invalid_message")
    
    @pytest.mark.asyncio
    async def test_send_message_queue_full(self, communication):
        """Test sending message when queue is full."""
        message = ProcessMessage(
            message_id="test_123",
            message_type="command",
            payload={"data": "test"},
            source_pid=12345
        )
        
        with patch.object(communication.message_queue, 'put', side_effect=queue.Full):
            with pytest.raises(QueueFullError):
                await communication.send_message(message)
    
    @pytest.mark.asyncio
    async def test_receive_message_success(self, communication):
        """Test successful message receiving."""
        test_message = ProcessMessage(
            message_id="test_123",
            message_type="command",
            payload={"data": "test"},
            source_pid=12345
        )
        serialized_message = test_message.serialize()
        
        with patch.object(communication.message_queue, 'get', return_value=serialized_message):
            received_message = await communication.receive_message()
            
            assert received_message.message_id == test_message.message_id
            assert received_message.message_type == test_message.message_type
            assert received_message.payload == test_message.payload
    
    @pytest.mark.asyncio
    async def test_receive_message_queue_empty(self, communication):
        """Test receiving message when queue is empty."""
        with patch.object(communication.message_queue, 'get', side_effect=queue.Empty):
            with pytest.raises(QueueEmptyError):
                await communication.receive_message()
    
    @pytest.mark.asyncio
    async def test_send_result_success(self, communication):
        """Test successful result sending."""
        result = ProcessingResult(
            success=True,
            message="Test result",
            data={"processed": 10}
        )
        
        with patch.object(communication.result_queue, 'put') as mock_put:
            success = await communication.send_result(result)
            
            assert success is True
            mock_put.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_result_invalid_result(self, communication):
        """Test sending invalid result."""
        with pytest.raises(ValueError, match="result must be ProcessingResult instance"):
            await communication.send_result("invalid_result")
    
    @pytest.mark.asyncio
    async def test_receive_result_success(self, communication):
        """Test successful result receiving."""
        test_result = ProcessingResult(
            success=True,
            message="Test result",
            data={"processed": 10}
        )
        serialized_result = pickle.dumps(test_result.to_dict())
        
        with patch.object(communication.result_queue, 'get', return_value=serialized_result):
            received_result = await communication.receive_result()
            
            assert received_result.success == test_result.success
            assert received_result.message == test_result.message
            assert received_result.data == test_result.data
    
    @pytest.mark.asyncio
    async def test_send_status_update_success(self, communication):
        """Test successful status update sending."""
        status = {"progress": 50, "files_processed": 100}
        
        with patch.object(communication.status_queue, 'put') as mock_put:
            success = await communication.send_status_update(status)
            
            assert success is True
            mock_put.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_status_update_invalid_status(self, communication):
        """Test sending invalid status update."""
        with pytest.raises(ValueError, match="status must be dictionary"):
            await communication.send_status_update("invalid_status")
    
    @pytest.mark.asyncio
    async def test_receive_status_update_success(self, communication):
        """Test successful status update receiving."""
        test_status = {"progress": 50, "files_processed": 100}
        serialized_status = pickle.dumps(test_status)
        
        with patch.object(communication.status_queue, 'get', return_value=serialized_status):
            received_status = await communication.receive_status_update()
            
            assert received_status == test_status
    
    def test_register_message_handler(self, communication):
        """Test message handler registration."""
        def test_handler(message):
            pass
        
        communication.register_message_handler("test_type", test_handler)
        
        assert "test_type" in communication.message_handlers
        assert communication.message_handlers["test_type"] == test_handler
    
    def test_register_message_handler_invalid_type(self, communication):
        """Test registering handler with invalid message type."""
        def test_handler(message):
            pass
        
        with pytest.raises(ValueError, match="message_type must be string"):
            communication.register_message_handler(123, test_handler)
    
    def test_register_message_handler_invalid_handler(self, communication):
        """Test registering invalid handler."""
        with pytest.raises(ValueError, match="handler must be callable"):
            communication.register_message_handler("test_type", "not_callable")
    
    @pytest.mark.asyncio
    async def test_start_heartbeat(self, communication):
        """Test starting heartbeat mechanism."""
        with patch.object(communication, '_heartbeat_loop') as mock_loop:
            await communication.start_heartbeat()
            
            assert communication._heartbeat_task is not None
    
    @pytest.mark.asyncio
    async def test_stop_heartbeat(self, communication):
        """Test stopping heartbeat mechanism."""
        # Start heartbeat first
        with patch.object(communication, '_heartbeat_loop'):
            await communication.start_heartbeat()
        
        # Stop heartbeat
        await communication.stop_heartbeat()
        
        assert communication._heartbeat_task is None
    
    @pytest.mark.asyncio
    async def test_cleanup(self, communication):
        """Test communication cleanup."""
        with patch.object(communication, 'stop_heartbeat') as mock_stop, \
             patch.object(communication.message_queue, 'close') as mock_close_msg, \
             patch.object(communication.result_queue, 'close') as mock_close_result, \
             patch.object(communication.status_queue, 'close') as mock_close_status:
            
            await communication.cleanup()
            
            mock_stop.assert_called_once()
            mock_close_msg.assert_called_once()
            mock_close_result.assert_called_once()
            mock_close_status.assert_called_once()
    
    def test_create_message_id(self, communication):
        """Test message ID creation."""
        message_id = communication._create_message_id()
        
        assert isinstance(message_id, str)
        assert str(communication.process_id) in message_id
        assert len(message_id) > len(str(communication.process_id))
    
    def test_validate_message_valid(self, communication):
        """Test validating valid message."""
        message = ProcessMessage(
            message_id="test_123",
            message_type="command",
            payload={"data": "test"},
            source_pid=12345
        )
        
        assert communication._validate_message(message) is True
    
    def test_validate_message_invalid_type(self, communication):
        """Test validating message with invalid type."""
        assert communication._validate_message("not_a_message") is False
    
    def test_validate_message_missing_id(self, communication):
        """Test validating message with missing ID."""
        message = ProcessMessage(
            message_id="",
            message_type="command",
            payload={"data": "test"},
            source_pid=12345
        )
        
        assert communication._validate_message(message) is False
    
    def test_validate_message_invalid_payload(self, communication):
        """Test validating message with invalid payload."""
        message = ProcessMessage(
            message_id="test_123",
            message_type="command",
            payload="not_a_dict",
            source_pid=12345
        )
        
        assert communication._validate_message(message) is False
    
    def test_validate_message_invalid_pid(self, communication):
        """Test validating message with invalid PID."""
        message = ProcessMessage(
            message_id="test_123",
            message_type="command",
            payload={"data": "test"},
            source_pid=-1
        )
        
        assert communication._validate_message(message) is False
    
    @pytest.mark.asyncio
    async def test_heartbeat_loop(self, communication):
        """Test heartbeat loop functionality."""
        with patch.object(communication, 'send_message') as mock_send, \
             patch.object(communication, '_shutdown_event') as mock_event:
            
            mock_event.is_set.return_value = False
            mock_send.side_effect = asyncio.CancelledError()
            
            # Start heartbeat loop
            task = asyncio.create_task(communication._heartbeat_loop())
            
            # Let it run briefly
            await asyncio.sleep(0.1)
            
            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            # Verify heartbeat was attempted
            assert mock_send.called 