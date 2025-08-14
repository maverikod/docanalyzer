#!/usr/bin/env python3
"""
Integration Tests Runner - Execute Integration Tests with Real Services

This script runs integration tests with real external services to verify
end-to-end functionality of the DocAnalyzer system.

Real Services Required:
- Port 8001: Embedding Service (Vectorization)
- Port 8009: Chunking Service (Semantic Chunking)  
- Port 8007: Vector Database (Chunk Storage)
- Port 8000: MCP Proxy Server

Author: DocAnalyzer Team
Version: 1.0.0
"""

import asyncio
import sys
import os
import argparse
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import aiohttp
import pytest


class IntegrationTestRunner:
    """
    Runner for integration tests with real services.
    
    Manages test execution, service health checks, and result reporting.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.services = {
            "embedding": "http://localhost:8001",
            "chunking": "http://localhost:8009", 
            "vector_db": "http://localhost:8007",
            "mcp_proxy": "http://localhost:8000"
        }
        self.test_results = {}
    
    async def check_service_health(self, service_name: str, service_url: str) -> bool:
        """Check if a service is healthy and responding."""
        try:
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
    
    async def verify_services(self) -> bool:
        """Verify all required services are running."""
        print("🔍 Verifying required services...")
        
        all_healthy = True
        for service_name, service_url in self.services.items():
            if not await self.check_service_health(service_name, service_url):
                all_healthy = False
        
        if all_healthy:
            print("✅ All required services are healthy and ready for testing")
        else:
            print("❌ Some required services are not available")
            print("Please ensure the following services are running:")
            for service_name, service_url in self.services.items():
                print(f"  - {service_name}: {service_url}")
        
        return all_healthy
    
    def run_pytest_tests(self, test_pattern: str = None, verbose: bool = False) -> int:
        """Run pytest integration tests."""
        print("🧪 Running integration tests...")
        
        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(Path(__file__).parent),
            "--tb=short",
            "--strict-markers",
            "--disable-warnings"
        ]
        
        if test_pattern:
            cmd.extend(["-k", test_pattern])
        
        if verbose:
            cmd.append("-v")
        
        # Add coverage if requested
        if self.config.get("coverage", False):
            cmd.extend([
                "--cov=docanalyzer",
                "--cov-report=html:tests/integration/htmlcov",
                "--cov-report=term-missing"
            ])
        
        # Add performance testing if requested
        if self.config.get("benchmark", False):
            cmd.extend(["--benchmark-only"])
        
        # Add parallel execution if requested
        if self.config.get("parallel", False):
            cmd.extend(["-n", "auto"])
        
        print(f"Running command: {' '.join(cmd)}")
        
        # Execute pytest
        try:
            result = subprocess.run(cmd, capture_output=False, text=True)
            return result.returncode
        except Exception as e:
            print(f"❌ Failed to run tests: {e}")
            return 1
    
    def generate_report(self) -> None:
        """Generate test execution report."""
        print("\n" + "="*60)
        print("📊 INTEGRATION TESTS REPORT")
        print("="*60)
        
        # Check for test results
        test_dirs = [
            Path(__file__).parent / "htmlcov",
            Path(__file__).parent / ".pytest_cache"
        ]
        
        for test_dir in test_dirs:
            if test_dir.exists():
                print(f"📁 Test artifacts available in: {test_dir}")
        
        print("\n🎯 Next Steps:")
        print("1. Review test output above for any failures")
        print("2. Check coverage report in tests/integration/htmlcov/")
        print("3. Verify all services are still healthy")
        print("4. Run specific test categories if needed")
        
        print("\n🔧 Service Status:")
        for service_name, service_url in self.services.items():
            print(f"  - {service_name}: {service_url}")
    
    async def run(self) -> int:
        """Main execution method."""
        print("🚀 Starting DocAnalyzer Integration Tests")
        print("="*60)
        
        # Step 1: Verify services
        if not await self.verify_services():
            print("❌ Service verification failed. Exiting.")
            return 1
        
        # Step 2: Run tests
        test_pattern = self.config.get("test_pattern")
        verbose = self.config.get("verbose", False)
        
        exit_code = self.run_pytest_tests(test_pattern, verbose)
        
        # Step 3: Generate report
        self.generate_report()
        
        if exit_code == 0:
            print("\n🎉 All integration tests passed!")
        else:
            print(f"\n❌ Some tests failed (exit code: {exit_code})")
        
        return exit_code


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run DocAnalyzer integration tests with real services"
    )
    
    parser.add_argument(
        "--test-pattern",
        help="Pattern to filter tests (e.g., 'real_services' or 'mcp')"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmarks"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--skip-service-check",
        action="store_true",
        help="Skip service health check"
    )
    
    args = parser.parse_args()
    
    # Configuration
    config = {
        "test_pattern": args.test_pattern,
        "verbose": args.verbose,
        "coverage": args.coverage,
        "benchmark": args.benchmark,
        "parallel": args.parallel,
        "skip_service_check": args.skip_service_check
    }
    
    # Create runner and execute
    runner = IntegrationTestRunner(config)
    
    try:
        exit_code = asyncio.run(runner.run())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 