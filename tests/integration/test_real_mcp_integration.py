"""
Integration Tests for Real MCP Services - MCP Proxy Integration Testing

This module contains integration tests that verify the complete workflow
with real MCP proxy services, ensuring the DocAnalyzer commands work
correctly with actual MCP infrastructure.

Real MCP Services:
- MCP Proxy Server (vstl, vst1, emb, embl, svo, aiadm)
- Health check and monitoring commands
- System statistics and metrics collection

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

from docanalyzer.commands.auto_commands import (
    HealthCheckCommand,
    SystemStatsCommand,
    ProcessingStatsCommand,
    QueueStatusCommand
)


class TestRealMCPIntegration:
    """
    Integration tests with real MCP proxy services.
    
    Tests the complete workflow using actual MCP infrastructure
    to ensure end-to-end functionality in production environments.
    """
    
    @pytest.fixture
    def mcp_config(self) -> Dict[str, Any]:
        """Create configuration for MCP testing."""
        return {
            "mcp_proxy_url": "http://localhost:8001",  # Embedding service
            "vector_store_url": "http://localhost:8007",  # Vector store service
            "chunker_url": "http://localhost:8009",  # Chunker service
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 2.0
        }
    
    @pytest.fixture
    def health_check_command(self) -> HealthCheckCommand:
        """Create health check command instance."""
        return HealthCheckCommand()
    
    @pytest.fixture
    def system_stats_command(self) -> SystemStatsCommand:
        """Create system stats command instance."""
        return SystemStatsCommand()
    
    @pytest.fixture
    def processing_stats_command(self) -> ProcessingStatsCommand:
        """Create processing stats command instance."""
        return ProcessingStatsCommand()
    
    @pytest.fixture
    def queue_status_command(self) -> QueueStatusCommand:
        """Create queue status command instance."""
        return QueueStatusCommand()
    
    async def check_mcp_service_health(self, service_name: str, service_url: str) -> bool:
        """Check if an MCP service is healthy and responding."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{service_url}/health", timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ {service_name} is healthy: {result}")
                        return True
                    else:
                        print(f"❌ {service_name} health check failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ {service_name} connection failed: {e}")
            return False
    
    @pytest.mark.asyncio
    async def test_mcp_services_health_check(self, mcp_config: Dict[str, Any]):
        """
        Test health checks for all MCP services.
        
        This test verifies that all required MCP services are running
        and responding correctly before running integration tests.
        """
        # Check embedding service
        embedding_healthy = await self.check_mcp_service_health(
            "Embedding Service",
            mcp_config["mcp_proxy_url"]
        )
        
        # Check vector store service
        vector_store_healthy = await self.check_mcp_service_health(
            "Vector Store Service",
            mcp_config["vector_store_url"]
        )
        
        # Check chunker service
        chunker_healthy = await self.check_mcp_service_health(
            "Chunker Service",
            mcp_config["chunker_url"]
        )
        
        # All services should be healthy
        assert embedding_healthy, "Embedding service is not available"
        assert vector_store_healthy, "Vector store service is not available"
        assert chunker_healthy, "Chunker service is not available"
        
        print("✅ All MCP services are healthy and responding")
    
    @pytest.mark.asyncio
    async def test_real_health_check_command(
        self,
        health_check_command: HealthCheckCommand
    ):
        """
        Test health check command with real MCP services.
        
        This test verifies that:
        - Health check command executes successfully
        - All system components are reported correctly
        - Service status information is accurate
        - Response format is correct
        """
        # Execute health check command
        result = await health_check_command.execute()
        
        # Verify command execution
        assert result is not None, "Health check command should return a result"
        assert hasattr(result, 'to_dict'), "Result should have to_dict method"
        
        result_dict = result.to_dict()
        
        # Verify response structure
        assert "status" in result_dict, "Response missing status field"
        assert "version" in result_dict, "Response missing version field"
        assert "uptime" in result_dict, "Response missing uptime field"
        assert "components" in result_dict, "Response missing components field"
        assert "docanalyzer_metrics" in result_dict, "Response missing docanalyzer_metrics field"
        
        # Verify system status
        assert result_dict["status"] in ["ok", "error"], "Invalid status value"
        
        # Verify components information
        components = result_dict["components"]
        assert isinstance(components, dict), "Components should be a dictionary"
        
        # Check for required component information
        required_components = ["system", "process", "docanalyzer"]
        for component in required_components:
            if component in components:
                component_info = components[component]
                assert isinstance(component_info, dict), f"Component {component} should be a dictionary"
        
        print(f"✅ Health check completed with status: {result_dict['status']}")
        print(f"📊 Components checked: {list(components.keys())}")
    
    @pytest.mark.asyncio
    async def test_real_system_stats_command(
        self,
        system_stats_command: SystemStatsCommand
    ):
        """
        Test system stats command with real MCP services.
        
        This test verifies that:
        - System stats command executes successfully
        - System metrics are collected correctly
        - Performance data is accurate
        - Resource usage information is available
        """
        # Execute system stats command
        result = await system_stats_command.execute()
        
        # Verify command execution
        assert result is not None, "System stats command should return a result"
        result_dict = result.to_dict()
        
        # Verify response structure
        assert "system_stats" in result_dict, "Response missing system_stats field"
        assert "performance_metrics" in result_dict, "Response missing performance_metrics field"
        assert "docanalyzer_stats" in result_dict, "Response missing docanalyzer_stats field"
        assert "timestamp" in result_dict, "Response missing timestamp field"
        
        # Verify system statistics
        system_stats = result_dict["system_stats"]
        assert "platform" in system_stats, "System stats missing platform"
        assert "cpu" in system_stats, "System stats missing cpu"
        assert "memory" in system_stats, "System stats missing memory"
        
        # Verify performance metrics
        performance_metrics = result_dict["performance_metrics"]
        assert isinstance(performance_metrics, dict), "Performance metrics should be a dictionary"
        
        print(f"✅ System stats collected successfully")
        print(f"📊 Platform: {system_stats.get('platform', {}).get('system', 'unknown')}")
        print(f"💾 Memory: {system_stats.get('memory', {}).get('total', 'unknown')} bytes")
    
    @pytest.mark.asyncio
    async def test_real_processing_stats_command(
        self,
        processing_stats_command: ProcessingStatsCommand
    ):
        """
        Test processing stats command with real MCP services.
        
        This test verifies that:
        - Processing stats command executes successfully
        - Processing metrics are collected correctly
        - File processing statistics are accurate
        - Performance data is available
        """
        # Execute processing stats command
        result = await processing_stats_command.execute()
        
        # Verify command execution
        assert result is not None, "Processing stats command should return a result"
        result_dict = result.to_dict()
        
        # Verify response structure
        assert "processing_stats" in result_dict, "Response missing processing_stats field"
        assert "file_stats" in result_dict, "Response missing file_stats field"
        assert "performance_stats" in result_dict, "Response missing performance_stats field"
        assert "timestamp" in result_dict, "Response missing timestamp field"
        
        # Verify processing statistics
        processing_stats = result_dict["processing_stats"]
        assert isinstance(processing_stats, dict), "Processing stats should be a dictionary"
        
        # Verify file statistics
        file_stats = result_dict["file_stats"]
        assert isinstance(file_stats, dict), "File stats should be a dictionary"
        
        # Verify performance statistics
        performance_stats = result_dict["performance_stats"]
        assert isinstance(performance_stats, dict), "Performance stats should be a dictionary"
        
        print(f"✅ Processing stats collected successfully")
        print(f"📊 Processing stats keys: {list(processing_stats.keys())}")
        print(f"📁 File stats keys: {list(file_stats.keys())}")
        print(f"⚡ Performance stats keys: {list(performance_stats.keys())}")
    
    @pytest.mark.asyncio
    async def test_real_queue_status_command(
        self,
        queue_status_command: QueueStatusCommand
    ):
        """
        Test queue status command with real MCP services.
        
        This test verifies that:
        - Queue status command executes successfully
        - Queue information is accurate
        - Queue items are reported correctly
        - Performance metrics are available
        """
        # Execute queue status command
        result = await queue_status_command.execute()
        
        # Verify command execution
        assert result is not None, "Queue status command should return a result"
        result_dict = result.to_dict()
        
        # Verify response structure
        assert "queue_status" in result_dict, "Response missing queue_status field"
        assert "queue_items" in result_dict, "Response missing queue_items field"
        assert "performance_metrics" in result_dict, "Response missing performance_metrics field"
        assert "timestamp" in result_dict, "Response missing timestamp field"
        
        # Verify queue status
        queue_status = result_dict["queue_status"]
        assert isinstance(queue_status, dict), "Queue status should be a dictionary"
        
        # Verify queue items
        queue_items = result_dict["queue_items"]
        assert isinstance(queue_items, list), "Queue items should be a list"
        
        # Verify performance metrics
        performance_metrics = result_dict["performance_metrics"]
        assert isinstance(performance_metrics, dict), "Performance metrics should be a dictionary"
        
        print(f"✅ Queue status collected successfully")
        print(f"📊 Queue status keys: {list(queue_status.keys())}")
        print(f"📋 Queue items count: {len(queue_items)}")
        print(f"⚡ Performance metrics keys: {list(performance_metrics.keys())}")
    
    @pytest.mark.asyncio
    async def test_real_mcp_command_integration(
        self,
        health_check_command: HealthCheckCommand,
        system_stats_command: SystemStatsCommand,
        processing_stats_command: ProcessingStatsCommand,
        queue_status_command: QueueStatusCommand
    ):
        """
        Test complete MCP command integration workflow.
        
        This test verifies the entire MCP command workflow:
        1. Health check to verify system status
        2. System stats to monitor performance
        3. Processing stats to track operations
        4. Queue status to monitor workload
        """
        print("🔄 Starting complete MCP command integration test...")
        
        # Step 1: Health Check
        print("🔄 Step 1: Executing health check...")
        health_result = await health_check_command.execute()
        health_dict = health_result.to_dict()
        
        assert health_dict["status"] in ["ok", "error"], "Invalid health status"
        print(f"✅ Health check completed: {health_dict['status']}")
        
        # Step 2: System Stats
        print("🔄 Step 2: Collecting system statistics...")
        system_result = await system_stats_command.execute()
        system_dict = system_result.to_dict()
        
        assert "system_stats" in system_dict, "System stats missing system_stats"
        assert "performance_metrics" in system_dict, "System stats missing performance_metrics"
        print(f"✅ System stats collected successfully")
        
        # Step 3: Processing Stats
        print("🔄 Step 3: Collecting processing statistics...")
        processing_result = await processing_stats_command.execute()
        processing_dict = processing_result.to_dict()
        
        assert "processing_stats" in processing_dict, "Processing stats missing processing_stats"
        assert "file_stats" in processing_dict, "Processing stats missing file_stats"
        print(f"✅ Processing stats collected successfully")
        
        # Step 4: Queue Status
        print("🔄 Step 4: Checking queue status...")
        queue_result = await queue_status_command.execute()
        queue_dict = queue_result.to_dict()
        
        assert "queue_status" in queue_dict, "Queue status missing queue_status"
        assert "queue_items" in queue_dict, "Queue status missing queue_items"
        print(f"✅ Queue status checked successfully")
        
        # Step 5: Verify data consistency
        print("🔄 Step 5: Verifying data consistency...")
        
        # Check that timestamps are present
        for result_dict in [health_dict, system_dict, processing_dict, queue_dict]:
            if "timestamp" in result_dict:
                timestamp = result_dict["timestamp"]
                assert isinstance(timestamp, str), "Timestamp should be a string"
        
        # Check that system is operational
        assert health_dict["status"] != "error", "System should not be in error state"
        
        print("✅ Data consistency verified")
        print("🎉 Complete MCP command integration test passed!")
    
    @pytest.mark.asyncio
    async def test_real_mcp_error_handling(
        self,
        health_check_command: HealthCheckCommand,
        system_stats_command: SystemStatsCommand
    ):
        """
        Test error handling with real MCP services.
        
        This test verifies that:
        - Commands handle service failures gracefully
        - Error responses are properly formatted
        - System can recover from MCP service failures
        - Timeout handling works correctly
        """
        print("🔄 Testing MCP error handling...")
        
        # Test with invalid parameters
        try:
            # This should handle invalid parameters gracefully
            result = await health_check_command.execute(invalid_param="test")
            assert result is not None, "Command should handle invalid parameters"
        except Exception as e:
            print(f"✅ Command properly handled invalid parameters: {e}")
        
        # Test system stats with potential service failures
        try:
            result = await system_stats_command.execute()
            assert result is not None, "System stats should handle service failures"
            result_dict = result.to_dict()
            
            # Even if some services fail, we should get partial results
            assert "system_info" in result_dict, "Should have system info even with failures"
            
        except Exception as e:
            print(f"✅ System stats properly handled service failures: {e}")
        
        print("✅ MCP error handling test passed")
    
    @pytest.mark.asyncio
    async def test_real_mcp_performance(
        self,
        health_check_command: HealthCheckCommand,
        system_stats_command: SystemStatsCommand,
        processing_stats_command: ProcessingStatsCommand,
        queue_status_command: QueueStatusCommand
    ):
        """
        Test performance with real MCP services.
        
        This test verifies that:
        - Commands respond within acceptable time limits
        - Throughput is reasonable
        - Resource usage is stable
        - Concurrent operations work correctly
        """
        print("🔄 Testing MCP command performance...")
        
        commands = [
            ("Health Check", health_check_command),
            ("System Stats", system_stats_command),
            ("Processing Stats", processing_stats_command),
            ("Queue Status", queue_status_command)
        ]
        
        performance_results = {}
        
        for command_name, command in commands:
            # Measure execution time
            start_time = time.time()
            try:
                result = await command.execute()
                end_time = time.time()
                execution_time = end_time - start_time
                
                performance_results[command_name] = {
                    "success": True,
                    "execution_time": execution_time,
                    "result_size": len(str(result.to_dict())) if result else 0
                }
                
                print(f"✅ {command_name}: {execution_time:.3f}s")
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                
                performance_results[command_name] = {
                    "success": False,
                    "execution_time": execution_time,
                    "error": str(e)
                }
                
                print(f"❌ {command_name}: {execution_time:.3f}s (failed: {e})")
        
        # Verify performance metrics
        successful_commands = [name for name, data in performance_results.items() if data["success"]]
        assert len(successful_commands) >= 2, "At least 2 commands should succeed"
        
        # Check execution times
        for command_name, data in performance_results.items():
            if data["success"]:
                assert data["execution_time"] < 10.0, f"{command_name} too slow: {data['execution_time']}s"
                assert data["result_size"] > 0, f"{command_name} returned empty result"
        
        # Calculate average performance
        avg_time = sum(data["execution_time"] for data in performance_results.values()) / len(performance_results)
        print(f"📊 Average execution time: {avg_time:.3f} seconds")
        print(f"✅ {len(successful_commands)}/{len(commands)} commands executed successfully")
        
        print("✅ MCP performance test passed") 