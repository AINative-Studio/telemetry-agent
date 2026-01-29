# Context Agent

[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-in%20development-yellow.svg)](https://github.com/AINative-Studio/telemetry-agent/issues)

> **Codename:** Cody-Context-Agent
> **Type:** Local Context Monitoring Agent
> **Status:** In Development

A self-contained agent that monitors and exposes runtime context for IDE and workspace environments using AINative Studio APIs, SDK, and ZeroDB.

## Overview

The Context Agent is the authoritative sensing mechanism for detecting and exposing:
- Current AI model in use
- Workspace path and name
- Git repository status and branch
- Context window usage statistics

## Architecture

```
┌─────────────────────────────────────────┐
│         Context Agent (Python)          │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │   Sensor (Bash + jq)            │   │
│  │   - STDIN: JSON input           │   │
│  │   - STDOUT: Display string      │   │
│  │   - STDERR: Structured JSON     │   │
│  └─────────────────────────────────┘   │
│              ⬇                          │
│  ┌─────────────────────────────────┐   │
│  │   Agent Core                    │   │
│  │   - Execute sensor              │   │
│  │   - Parse output                │   │
│  │   - Normalize state             │   │
│  └─────────────────────────────────┘   │
│              ⬇                          │
│  ┌─────────────────────────────────┐   │
│  │   State Management              │   │
│  │   - In-memory cache             │   │
│  │   - Change detection            │   │
│  │   - Event emission              │   │
│  └─────────────────────────────────┘   │
│              ⬇                          │
│  ┌─────────────────────────────────┐   │
│  │   API Surface                   │   │
│  │   - get_state()                 │   │
│  │   - get_display_header()        │   │
│  │   - on_change()                 │   │
│  └─────────────────────────────────┘   │
│              ⬇                          │
│  ┌─────────────────────────────────┐   │
│  │   ZeroDB Integration (Optional) │   │
│  │   - State persistence           │   │
│  │   - Agent logging               │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Quick Start

### Test the Sensor Script

```bash
# Test sensor with sample input
echo '{"model":"claude-sonnet-4","context_window":{"max_tokens":200000,"tokens_used":50000}}' | scripts/context_sensor.sh

# Output: [claude-sonnet-4] 📁 context-agent 🌿 main | 📊 25%

# Run comprehensive test suite
./tests/test_sensor_execution.sh
```

### Use the Context Agent (Coming Soon)

```python
from context_agent import ContextAgent

# Initialize agent
agent = ContextAgent()

# Start monitoring
agent.start()

# Get current state
state = agent.get_state()
print(state)

# Get display header
header = agent.get_display_header()
print(header)  # [Claude] 📁 ainative 🌿 main | 📊 13%

# Register event handlers
agent.on_change("branch_changed", lambda event: print(f"Branch changed to: {event.new_value}"))
agent.on_change("context_threshold", lambda event: print(f"Context usage: {event.new_value}%"))
```

## Installation

```bash
# Clone repository
git clone https://github.com/AINative-Studio/telemetry-agent.git
cd telemetry-agent

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration
```

## Features

- **Real-time Context Monitoring**: Track AI model, workspace, git status, and context window usage
- **Event-Driven Architecture**: Subscribe to state changes with typed events
- **ZeroDB Integration**: Optional persistent state storage and agent logging
- **Minimal Dependencies**: Lightweight bash sensor with jq for JSON processing
- **Type-Safe**: Full type hints throughout the codebase
- **Extensible**: Clean API for integration with IDEs, CLI tools, and monitoring systems

## Development Status

This project is under active development. See [GitHub Issues](https://github.com/AINative-Studio/telemetry-agent/issues) for current progress.

### Milestones

- [x] Project structure created
- [x] Sensor script implemented
- [x] Sensor script verified and tested (Issue #1) ✓
- [x] State management models defined
- [x] Event system defined
- [ ] Agent core implementation (Issue #2)
- [ ] API surface implementation (Issue #4)
- [ ] ZeroDB integration (Issue #6)
- [ ] Testing suite (Issue #7)
- [ ] Documentation (Issue #8)

## Project Structure

```
context-agent/
├── src/
│   ├── __init__.py       # Package exports
│   ├── agent.py          # Main agent implementation
│   ├── state.py          # State management
│   ├── events.py         # Event system
│   └── config.py         # Configuration management
├── scripts/
│   └── context_sensor.sh # Bash sensor script
├── tests/
│   ├── test_sensor.py    # Sensor tests
│   ├── test_agent.py     # Agent core tests
│   ├── test_state.py     # State management tests
│   └── test_events.py    # Event system tests
├── config/
│   └── default.json      # Default configuration
├── docs/
│   ├── api.md            # API documentation
│   ├── examples.md       # Usage examples
│   └── deployment.md     # Deployment guide
└── README.md             # This file
```

## Requirements

- Python 3.8+
- bash
- jq (JSON processor)
- git

## Configuration

See `.env.example` for available configuration options:

```bash
# Agent Settings
POLLING_INTERVAL=5        # Sensor polling interval (seconds)
CONTEXT_THRESHOLD=80      # Context usage alert threshold (%)
SENSOR_TIMEOUT=5          # Sensor execution timeout (seconds)

# ZeroDB Integration (Optional)
ENABLE_ZERODB=false
ZERODB_API_KEY=your_key
ZERODB_PROJECT_ID=your_project
```

## Documentation

- [Sensor Verification Report](docs/SENSOR_VERIFICATION_REPORT.md) - Sensor script testing and validation
- [Sensor Usage Guide](docs/SENSOR_USAGE_GUIDE.md) - How to use the context sensor
- [API Reference](docs/api.md) - Complete API documentation
- [Usage Examples](docs/examples.md) - Common usage patterns
- [Configuration Guide](docs/configuration.md) - Configuration options
- [Architecture](docs/architecture.md) - System design and components
- [Deployment Guide](docs/deployment.md) - Installation and deployment
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## Contributing

This is an AINative Studio internal project. See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

Proprietary - AINative Studio

## Links

- [GitHub Repository](https://github.com/AINative-Studio/telemetry-agent)
- [Issues](https://github.com/AINative-Studio/telemetry-agent/issues)
- [AINative Studio](https://ainative.studio)
- [ZeroDB Documentation](https://zerodb.ainative.studio)
