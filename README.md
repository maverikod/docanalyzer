# DocAnalyzer

[![PyPI version](https://badge.fury.io/py/docanalyzer.svg)](https://badge.fury.io/py/docanalyzer)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/docanalyzer/docanalyzer/workflows/Tests/badge.svg)](https://github.com/docanalyzer/docanalyzer/actions)
[![Coverage](https://codecov.io/gh/docanalyzer/docanalyzer/branch/main/graph/badge.svg)](https://codecov.io/gh/docanalyzer/docanalyzer)

Automated file monitoring and chunking for vector databases. DocAnalyzer provides a comprehensive solution for watching directories, processing documents, and storing chunks in vector databases for AI applications.

## Features

- 🔍 **File System Monitoring**: Real-time monitoring of directories for new, modified, and deleted files
- 📄 **Document Processing**: Support for multiple document formats (TXT, MD, PDF, etc.)
- 🧩 **Smart Chunking**: Intelligent document chunking with semantic boundaries
- 🗄️ **Vector Database Integration**: Seamless integration with popular vector databases
- ⚡ **High Performance**: Asynchronous processing with configurable batch sizes
- 🔧 **MCP Commands**: Model Context Protocol commands for easy integration
- 📊 **Comprehensive Monitoring**: Health checks, metrics, and detailed logging
- 🧪 **Test Coverage**: 90%+ test coverage with comprehensive test suite

## Installation

### From PyPI (Recommended)

```bash
pip install docanalyzer
```

### From Source

```bash
git clone https://github.com/docanalyzer/docanalyzer.git
cd docanalyzer
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/docanalyzer/docanalyzer.git
cd docanalyzer
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```python
from docanalyzer import main

# Start the DocAnalyzer service
main()
```

### Configuration

Create a `config.json` file in your project root:

```json
{
  "file_watcher": {
    "directories": ["./documents", "./docs"],
    "scan_interval": 300,
    "lock_timeout": 3600,
    "max_processes": 5
  },
  "vector_store": {
    "base_url": "http://localhost:8007",
    "port": 8007,
    "timeout": 30
  },
  "chunker": {
    "base_url": "http://localhost:8009",
    "port": 8009,
    "timeout": 30
  },
  "embedding": {
    "base_url": "http://localhost:8001",
    "port": 8001,
    "timeout": 30
  }
}
```

### MCP Commands

DocAnalyzer provides MCP commands for easy integration:

```python
# Start watching directories
await mcp_client.call("start_watching", {"directories": ["./docs"]})

# Get watch status
status = await mcp_client.call("get_watch_status")

# Scan directory
await mcp_client.call("scan_directory", {"path": "./documents"})

# Get processing statistics
stats = await mcp_client.call("get_processing_stats")
```

## Documentation

- [User Guide](https://docanalyzer.readthedocs.io/en/latest/user_guide.html)
- [API Reference](https://docanalyzer.readthedocs.io/en/latest/api.html)
- [Configuration](https://docanalyzer.readthedocs.io/en/latest/configuration.html)
- [MCP Commands](https://docanalyzer.readthedocs.io/en/latest/mcp_commands.html)

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/docanalyzer/docanalyzer.git
cd docanalyzer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=docanalyzer --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

### Code Quality

```bash
# Format code
black docanalyzer tests
isort docanalyzer tests

# Lint code
flake8 docanalyzer tests
pylint docanalyzer

# Type checking
mypy docanalyzer
```

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
cd docs
make html
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://docanalyzer.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/docanalyzer/docanalyzer/issues)
- 💬 [Discussions](https://github.com/docanalyzer/docanalyzer/discussions)
- 📧 [Email Support](mailto:team@docanalyzer.com)

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for high-performance web framework
- Uses [Watchdog](https://python-watchdog.readthedocs.io/) for file system monitoring
- Integrates with [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- Powered by [Uvicorn](https://www.uvicorn.org/) for ASGI server

## Roadmap

- [ ] Support for more document formats (DOCX, PPTX, etc.)
- [ ] Advanced chunking algorithms
- [ ] Web UI for monitoring and configuration
- [ ] Docker containerization
- [ ] Kubernetes deployment support
- [ ] Cloud storage integration
- [ ] Real-time collaboration features
- [ ] Advanced analytics and reporting

---

**DocAnalyzer** - Making document processing and vector storage simple and efficient. 