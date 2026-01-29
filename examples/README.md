# Context Agent Examples

This directory contains working code examples demonstrating various features of the Context Agent.

## Examples

### 1. basic_usage.py

The simplest way to use the Context Agent.

```bash
python examples/basic_usage.py
```

**Demonstrates:**
- Creating and starting an agent
- Getting current state
- Accessing state properties
- Getting display header
- Converting state to JSON

### 2. event_handling.py

Event-driven programming with the Context Agent.

```bash
python examples/event_handling.py
```

**Demonstrates:**
- Registering event handlers
- Subscribing to different event types
- Handling state changes
- Context threshold alerts

**Try while running:**
- Change git branch: `git checkout <branch-name>`
- Change directory: `cd /path/to/other/workspace`
- Continue conversation to increase context usage

### 3. custom_configuration.py

Different ways to configure the agent.

```bash
python examples/custom_configuration.py
```

**Demonstrates:**
- Inline configuration dictionaries
- Environment variable configuration
- JSON file configuration
- Merged configuration from multiple sources
- Environment-specific configuration (dev vs prod)

### 4. zerodb_integration.py

Integration with ZeroDB for persistent storage.

```bash
# Set ZeroDB credentials first
export ZERODB_API_KEY=your_api_key
export ZERODB_PROJECT_ID=your_project_id

python examples/zerodb_integration.py
```

**Demonstrates:**
- Basic event logging to ZeroDB
- Periodic state persistence
- Selective event logging
- Batched event logging

**Note:** Requires ZeroDB credentials.

### 5. cli_tool.py

Command-line interface for the Context Agent.

```bash
# Get current state
python examples/cli_tool.py get

# Get state as JSON
python examples/cli_tool.py get --json

# Watch all changes
python examples/cli_tool.py watch

# Watch specific event
python examples/cli_tool.py watch --event branch_changed

# Monitor context usage
python examples/cli_tool.py monitor --threshold 80

# Display agent info
python examples/cli_tool.py info
```

**Demonstrates:**
- Building a CLI tool with argparse
- Different output formats
- Event filtering
- Real-time monitoring

---

## Running Examples

### Prerequisites

```bash
# Install Context Agent
pip install context-agent

# Or install from source
cd /path/to/context-agent
pip install -e .
```

### Run All Examples

```bash
# From project root
python examples/basic_usage.py
python examples/event_handling.py
python examples/custom_configuration.py
python examples/zerodb_integration.py  # Requires credentials
python examples/cli_tool.py info
```

---

## Environment Setup

### Development

```bash
# .env
AGENT_POLLING_INTERVAL=2
AGENT_CONTEXT_THRESHOLD=70
AGENT_LOG_LEVEL=DEBUG
```

### Production

```bash
# .env
AGENT_POLLING_INTERVAL=10
AGENT_CONTEXT_THRESHOLD=85
AGENT_LOG_LEVEL=WARNING
ENABLE_ZERODB=true
ZERODB_API_KEY=your_key
ZERODB_PROJECT_ID=your_project
```

---

## Customizing Examples

Feel free to modify these examples to suit your needs:

1. **Change polling intervals** for faster/slower updates
2. **Add custom event handlers** for specific behaviors
3. **Integrate with your tools** (IDEs, terminals, monitoring systems)
4. **Add error handling** for production use
5. **Implement custom logging** or persistence

---

## Troubleshooting

### Example fails with "ModuleNotFoundError"

```bash
# Ensure Context Agent is installed
pip install context-agent

# Or install from source
pip install -e .
```

### Event handlers not firing

Make sure to:
1. Call `agent.start()` before expecting events
2. Keep the script running (events fire over time)
3. Make changes that trigger events (branch switch, etc.)

### ZeroDB examples fail

Ensure environment variables are set:
```bash
export ZERODB_API_KEY=your_key
export ZERODB_PROJECT_ID=your_project
```

---

## More Information

- [API Reference](../docs/api.md)
- [Usage Guide](../docs/examples.md)
- [Configuration Guide](../docs/configuration.md)
- [Troubleshooting](../docs/troubleshooting.md)
