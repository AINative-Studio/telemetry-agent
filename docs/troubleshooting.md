# Troubleshooting Guide

Common issues and solutions for the Context Agent.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Sensor Execution Errors](#sensor-execution-errors)
- [Configuration Problems](#configuration-problems)
- [Event Handling Issues](#event-handling-issues)
- [Performance Problems](#performance-problems)
- [ZeroDB Integration Issues](#zerodb-integration-issues)
- [Debug Mode](#debug-mode)
- [Logging](#logging)
- [FAQ](#faq)

---

## Installation Issues

### Error: "ModuleNotFoundError: No module named 'context_agent'"

**Problem**: Python cannot find the context_agent module.

**Solutions**:

1. **Verify installation**:
```bash
pip list | grep context-agent
```

2. **Install the package**:
```bash
pip install context-agent

# Or from source
git clone https://github.com/AINative-Studio/telemetry-agent.git
cd telemetry-agent
pip install -e .
```

3. **Check Python path**:
```python
import sys
print(sys.path)
```

4. **Use correct Python environment**:
```bash
# Activate virtual environment
source venv/bin/activate

# Verify Python
which python
```

---

### Error: "command not found: jq"

**Problem**: The `jq` command-line JSON processor is not installed.

**Solutions**:

**macOS**:
```bash
brew install jq
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install jq
```

**CentOS/RHEL**:
```bash
sudo yum install jq
```

**Verify installation**:
```bash
jq --version
```

---

### Error: "bash: bad interpreter: No such file or directory"

**Problem**: Bash is not installed or sensor script has wrong shebang.

**Solutions**:

1. **Verify bash installation**:
```bash
which bash
```

2. **Update sensor script shebang**:
```bash
# Change first line to match your bash location
#!/usr/bin/env bash
```

3. **Make sensor executable**:
```bash
chmod +x scripts/context_sensor.sh
```

---

## Sensor Execution Errors

### Error: "Sensor execution timeout"

**Problem**: Sensor script takes longer than configured timeout.

**Symptoms**:
- Timeout errors in logs
- Agent starts but never returns state
- High CPU usage

**Solutions**:

1. **Increase timeout**:
```python
config = {"sensor_timeout": 10}  # Increase from 5 to 10 seconds
agent = ContextAgent(config=config)
```

2. **Check for slow git operations**:
```bash
# Test git performance
time git status
time git branch --show-current
```

3. **Optimize git repository**:
```bash
# Clean up repository
git gc --aggressive
git prune
```

4. **Test sensor directly**:
```bash
time ./scripts/context_sensor.sh <<< '{}'
```

---

### Error: "Sensor returned non-zero exit code"

**Problem**: Sensor script failed during execution.

**Diagnosis**:

```bash
# Run sensor with error output
./scripts/context_sensor.sh <<< '{}' 2>&1
echo "Exit code: $?"
```

**Common Causes**:

1. **Git not installed**:
```bash
which git
# If not found, install git
```

2. **Invalid workspace directory**:
```bash
# Check if directory exists
ls -la /path/to/workspace
```

3. **Permission issues**:
```bash
# Check permissions
ls -la scripts/context_sensor.sh
chmod +x scripts/context_sensor.sh
```

---

### Error: "Failed to parse sensor output"

**Problem**: Sensor output is not valid JSON.

**Diagnosis**:

```bash
# Capture sensor output
./scripts/context_sensor.sh <<< '{}' 2>&1 | jq .

# If jq fails, output is not valid JSON
```

**Solutions**:

1. **Check sensor version**:
```bash
grep 'SCRIPT_VERSION=' scripts/context_sensor.sh
```

2. **Update sensor script**:
```bash
git pull origin main
```

3. **Check for stderr interference**:
```bash
# Redirect stderr to file and examine
./scripts/context_sensor.sh <<< '{}' 2>sensor_output.json
cat sensor_output.json | jq .
```

---

## Configuration Problems

### Error: "Invalid configuration: polling_interval must be >= 1"

**Problem**: Configuration validation failed.

**Solution**:

```python
# Ensure all config values are valid
config = {
    "polling_interval": 5,      # Must be >= 1
    "context_threshold": 80,    # Must be 1-100
    "sensor_timeout": 5         # Must be >= 1
}

agent = ContextAgent(config=config)
```

---

### Error: "ZERODB_API_KEY environment variable is required"

**Problem**: ZeroDB is enabled but API key is missing.

**Solutions**:

1. **Set environment variable**:
```bash
export ZERODB_API_KEY=your_key_here
export ZERODB_PROJECT_ID=your_project_id
```

2. **Use .env file**:
```bash
# Create .env file
cat > .env <<EOF
ZERODB_API_KEY=your_key_here
ZERODB_PROJECT_ID=your_project_id
EOF
```

3. **Disable ZeroDB**:
```python
config = {"enable_zerodb": False}
agent = ContextAgent(config=config)
```

---

### Configuration File Not Loading

**Problem**: Configuration file exists but not being used.

**Diagnosis**:

```python
import json
import os

# Check file exists
config_file = "config/agent.json"
print(f"File exists: {os.path.exists(config_file)}")

# Check file contents
with open(config_file) as f:
    config = json.load(f)
    print(config)
```

**Solutions**:

1. **Verify file path**:
```python
import os
full_path = os.path.abspath("config/agent.json")
print(full_path)
```

2. **Check JSON syntax**:
```bash
jq . config/agent.json
# If jq fails, JSON is invalid
```

3. **Verify permissions**:
```bash
ls -la config/agent.json
chmod 644 config/agent.json
```

---

## Event Handling Issues

### Events Not Firing

**Problem**: Event handlers registered but not being called.

**Diagnosis**:

```python
from context_agent import ContextAgent, EventType

def test_handler(event):
    print(f"Event fired: {event.event_type.value}")

agent = ContextAgent(config={"polling_interval": 2})
agent.on_change(EventType.STATE_UPDATED, test_handler)
agent.start()

# Wait and observe
import time
time.sleep(10)
```

**Solutions**:

1. **Verify agent is started**:
```python
# Must call start() before events fire
agent.start()
```

2. **Check event type**:
```python
# Use correct event type
agent.on_change(EventType.BRANCH_CHANGED, handler)  # Correct
agent.on_change("branch_changed", handler)           # Also works
```

3. **Ensure state is changing**:
```python
# Events only fire when state changes
# Try changing git branch or context usage
```

---

### Event Handler Exceptions

**Problem**: Event handler throws exception and crashes.

**Diagnosis**:

```python
import logging
logging.basicConfig(level=logging.ERROR)

def buggy_handler(event):
    raise Exception("Handler error!")

agent = ContextAgent()
agent.on_change(EventType.STATE_UPDATED, buggy_handler)
agent.start()

# Check logs for exceptions
```

**Solutions**:

1. **Add error handling**:
```python
def safe_handler(event):
    try:
        # Handler logic
        process_event(event)
    except Exception as e:
        print(f"Handler error: {e}")
```

2. **Use logging**:
```python
import logging
logger = logging.getLogger(__name__)

def logged_handler(event):
    try:
        process_event(event)
    except Exception as e:
        logger.exception("Handler failed")
```

---

## Performance Problems

### High CPU Usage

**Problem**: Agent consuming excessive CPU.

**Diagnosis**:

```bash
# Check process CPU usage
top -p $(pgrep -f context_agent)

# Monitor with htop
htop -p $(pgrep -f context_agent)
```

**Solutions**:

1. **Increase polling interval**:
```python
config = {"polling_interval": 10}  # Reduce frequency
agent = ContextAgent(config=config)
```

2. **Check for sensor issues**:
```bash
# Test sensor performance
time ./scripts/context_sensor.sh <<< '{}'
# Should complete in < 100ms
```

3. **Reduce event handlers**:
```python
# Remove unnecessary handlers
agent.off(EventType.STATE_UPDATED, handler)
```

---

### High Memory Usage

**Problem**: Agent using too much memory.

**Diagnosis**:

```bash
# Check memory usage
ps aux | grep context_agent

# Detailed memory info
cat /proc/$(pgrep -f context_agent)/status | grep VmRSS
```

**Solutions**:

1. **Disable caching**:
```python
config = {"cache_enabled": False}
agent = ContextAgent(config=config)
```

2. **Check for memory leaks**:
```python
# Monitor over time
import psutil
import time

process = psutil.Process()
while True:
    print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    time.sleep(60)
```

---

### Slow State Updates

**Problem**: State changes take too long to appear.

**Solutions**:

1. **Reduce polling interval**:
```python
config = {"polling_interval": 1}  # Faster updates
agent = ContextAgent(config=config)
```

2. **Force immediate update**:
```python
# Bypass polling interval
fresh_state = agent.refresh()
```

3. **Check sensor performance**:
```bash
time ./scripts/context_sensor.sh <<< '{}'
```

---

## ZeroDB Integration Issues

### Error: "Failed to connect to ZeroDB API"

**Problem**: Cannot reach ZeroDB API endpoint.

**Diagnosis**:

```bash
# Test API connectivity
curl -I https://api.zerodb.ainative.studio

# Check API key
echo $ZERODB_API_KEY
```

**Solutions**:

1. **Verify API credentials**:
```bash
export ZERODB_API_KEY=your_key
export ZERODB_PROJECT_ID=your_project

# Test API call
curl -H "Authorization: Bearer $ZERODB_API_KEY" \
     https://api.zerodb.ainative.studio/projects/$ZERODB_PROJECT_ID/health
```

2. **Check network connectivity**:
```bash
ping api.zerodb.ainative.studio
```

3. **Use custom API URL**:
```python
config = {
    "enable_zerodb": True,
    "zerodb_api_url": "https://custom.api.url"
}
```

---

### Error: "ZeroDB rate limit exceeded"

**Problem**: Too many API requests to ZeroDB.

**Solutions**:

1. **Increase batch size**:
```python
config = {
    "enable_zerodb": True,
    "zerodb_batch_size": 50,      # Larger batches
    "zerodb_flush_interval": 60   # Less frequent flushes
}
```

2. **Reduce event logging**:
```python
# Only log specific events
agent.on_change(EventType.BRANCH_CHANGED, log_to_zerodb)
# Don't log STATE_UPDATED
```

---

## Debug Mode

### Enabling Debug Mode

```python
import logging
from context_agent import ContextAgent

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable debug mode
config = {
    "debug_mode": True,
    "log_level": "DEBUG"
}

agent = ContextAgent(config=config)
agent.start()
```

### Debug Output

```bash
# Enable debug output to file
python your_script.py 2>&1 | tee debug.log

# Increase verbosity
export AGENT_DEBUG=1
python your_script.py
```

### Tracing Sensor Execution

```bash
# Run sensor with bash debug mode
bash -x scripts/context_sensor.sh <<< '{}'

# Trace with set -x in sensor
# Add to context_sensor.sh:
set -x  # Enable tracing
```

---

## Logging

### Configure Logging

```python
import logging

# File logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)

# Get agent logger
logger = logging.getLogger('context_agent')
logger.setLevel(logging.DEBUG)
```

### Log Rotation

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'agent.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

logging.basicConfig(handlers=[handler])
```

### Viewing Logs

```bash
# Tail logs
tail -f agent.log

# Filter errors
grep ERROR agent.log

# View with timestamps
tail -f agent.log | grep -E "$(date +%Y-%m-%d)"
```

---

## FAQ

### Q: Why is my branch not being detected?

**A**: Ensure you're in a git repository and on a branch (not detached HEAD):

```bash
git status
git branch --show-current
```

---

### Q: Can I run multiple agents?

**A**: Yes, create separate instances:

```python
agent1 = ContextAgent(config={"workspace_path": "/path/1"})
agent2 = ContextAgent(config={"workspace_path": "/path/2"})

agent1.start()
agent2.start()
```

---

### Q: How do I stop the agent?

**A**: Call the stop() method:

```python
agent.stop()
```

Or use context manager:

```python
with ContextAgent() as agent:
    # Agent automatically stops when context exits
    state = agent.get_state()
```

---

### Q: Does the agent work on Windows?

**A**: The agent requires bash and jq, which are available on:
- Windows Subsystem for Linux (WSL)
- Git Bash
- Cygwin

Native Windows support (PowerShell sensor) is planned for future releases.

---

### Q: Can I use the agent without ZeroDB?

**A**: Yes, ZeroDB is completely optional:

```python
agent = ContextAgent()  # ZeroDB disabled by default
```

---

### Q: How do I update to the latest version?

**A**:

```bash
pip install --upgrade context-agent
```

---

### Q: The sensor is slow in my large repository

**A**: Try these optimizations:

```bash
# Optimize git
git gc --aggressive

# Increase sensor timeout
config = {"sensor_timeout": 10}

# Reduce polling frequency
config = {"polling_interval": 10}
```

---

### Q: How can I test if the agent is working?

**A**: Use this test script:

```python
from context_agent import ContextAgent
import time

agent = ContextAgent(config={"polling_interval": 2})
agent.start()

print("Agent started. Waiting for state...")
time.sleep(3)

state = agent.get_state()
print(f"Model: {state.model}")
print(f"Workspace: {state.workspace.name}")
print(f"Display: {state.display}")

agent.stop()
print("Test complete!")
```

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check logs**: Enable debug mode and review logs
2. **Search issues**: https://github.com/AINative-Studio/telemetry-agent/issues
3. **Create issue**: Include debug logs and system info
4. **Contact support**: support@ainative.studio

---

## System Information

When reporting issues, include:

```python
import sys
import platform
import subprocess

print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Bash: {subprocess.run(['bash', '--version'], capture_output=True).stdout.decode()}")
print(f"jq: {subprocess.run(['jq', '--version'], capture_output=True).stdout.decode()}")
print(f"git: {subprocess.run(['git', '--version'], capture_output=True).stdout.decode()}")

from context_agent import __version__
print(f"Agent version: {__version__}")
```

---

## Next Steps

- [API Reference](api.md) - Detailed API documentation
- [Configuration Guide](configuration.md) - Configuration options
- [Examples](examples.md) - Usage examples
- [Architecture](architecture.md) - System design
