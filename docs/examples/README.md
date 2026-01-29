# Context Agent - ZeroDB Examples

This directory contains examples demonstrating ZeroDB integration with Context Agent.

## Prerequisites

1. **AINative Account** - Sign up at [ainative.studio](https://ainative.studio)
2. **ZeroDB Project** - Create a project in your dashboard
3. **API Credentials** - Get your API key and project ID
4. **AINative SDK** - Install the Python SDK

## Setup

### Install Dependencies

```bash
# Install AINative SDK
pip install ainative

# Or from the core repository
pip install -e /path/to/core/developer-tools/sdks/python
```

### Configure Credentials

```bash
# Set environment variables
export CONTEXT_AGENT_ENABLE_ZERODB=true
export CONTEXT_AGENT_ZERODB_API_KEY="your_api_key_here"
export CONTEXT_AGENT_ZERODB_PROJECT_ID="your_project_id"
export CONTEXT_AGENT_ZERODB_ENABLE_LOGGING=true
```

## Running Examples

### Run All Examples

```bash
cd /Users/aideveloper/Desktop/context-agent
python docs/examples/zerodb_example.py
```

### Run from Project Root

```bash
# From context-agent directory
python -m docs.examples.zerodb_example
```

## Examples Included

### Example 1: Basic Usage
- Create agent with automatic config loading
- Check ZeroDB status
- Get and persist state

### Example 2: Explicit Configuration
- Create AgentConfig programmatically
- Use context manager for cleanup
- Check initialization status

### Example 3: Event Handlers
- Register event handlers
- Monitor state changes
- Automatic event logging to ZeroDB

### Example 4: Query Historical Data
- Store state snapshots
- Query historical states
- Filter by workspace and branch

### Example 5: Query Event Logs
- Query all events
- Filter by event type
- Analyze state transitions

### Example 6: Statistics
- Get ZeroDB storage statistics
- Monitor record counts
- Check table information

### Example 7: Error Handling
- Graceful degradation with invalid credentials
- Agent continues without persistence
- Error status reporting

## Expected Output

When running with valid credentials:

```
2026-01-28 16:00:00 - __main__ - INFO - Example 1: Basic Usage
2026-01-28 16:00:00 - __main__ - INFO - ZeroDB Status: {'enabled': True, 'initialized': True, ...}
2026-01-28 16:00:00 - __main__ - INFO - Current State: [Claude] 📁 context-agent 🌿 main | 📊 13%
2026-01-28 16:00:00 - __main__ - INFO - Workspace: context-agent
2026-01-28 16:00:00 - __main__ - INFO - Branch: main
2026-01-28 16:00:00 - __main__ - INFO - Context Usage: 13%
...
```

When running without credentials:

```
2026-01-28 16:00:00 - __main__ - WARNING - ZeroDB credentials not configured!
2026-01-28 16:00:00 - __main__ - WARNING - Examples will run but ZeroDB features will be disabled.
...
```

## Troubleshooting

### Import Errors

If you get import errors:

```bash
# Make sure you're in the project root
cd /Users/aideveloper/Desktop/context-agent

# Run with Python module syntax
python -m docs.examples.zerodb_example
```

### ZeroDB Connection Errors

Check your credentials:

```bash
echo $CONTEXT_AGENT_ZERODB_API_KEY
echo $CONTEXT_AGENT_ZERODB_PROJECT_ID
```

Verify they're set correctly:

```python
import os
print("API Key:", os.getenv("CONTEXT_AGENT_ZERODB_API_KEY"))
print("Project ID:", os.getenv("CONTEXT_AGENT_ZERODB_PROJECT_ID"))
```

### Table Creation Errors

Tables are created automatically. If you see errors:

1. Check your project has database enabled
2. Verify your API key has write permissions
3. Check the logs for detailed error messages

## Next Steps

After running the examples:

1. **Review the Documentation** - See [docs/zerodb_integration.md](../zerodb_integration.md)
2. **Build Your Integration** - Use the patterns from these examples
3. **Monitor Your Data** - Use the ZeroDB dashboard to view stored data
4. **Analyze Patterns** - Query historical data for insights

## Additional Resources

- [ZeroDB Integration Guide](../zerodb_integration.md)
- [Context Agent API](../api.md)
- [ZeroDB Documentation](https://zerodb.ainative.studio)
- [AINative SDK](https://github.com/AINative-Studio/core/tree/main/developer-tools/sdks/python)
