# Usage Examples

Complete usage examples for the Context Agent library.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Event Handling](#event-handling)
- [Custom Configuration](#custom-configuration)
- [ZeroDB Integration](#zerodb-integration)
- [Multiple Agent Instances](#multiple-agent-instances)
- [Error Handling](#error-handling)
- [IDE Integration](#ide-integration)
- [CLI Usage](#cli-usage)
- [Advanced Patterns](#advanced-patterns)

---

## Basic Usage

### Simple Context Monitoring

```python
from context_agent import ContextAgent

# Create and start agent
agent = ContextAgent()
agent.start()

# Get current state
state = agent.get_state()

# Access state properties
print(f"Model: {state.model}")
print(f"Workspace: {state.workspace.name}")
print(f"Path: {state.workspace.path}")
print(f"Git branch: {state.workspace.git.branch}")
print(f"Context usage: {state.context_window.usage_pct}%")

# Get display header
header = agent.get_display_header()
print(header)
# Output: [Claude] 📁 my-project 🌿 main | 📊 25%

# Stop agent when done
agent.stop()
```

### Using Context Manager

```python
from context_agent import ContextAgent

# Automatically stop on exit
with ContextAgent() as agent:
    state = agent.get_state()
    print(state.to_json())
```

### JSON Output

```python
from context_agent import ContextAgent
import json

agent = ContextAgent()
agent.start()

# Get state as JSON string
json_str = agent.get_state().to_json()
print(json_str)

# Get state as dictionary
state_dict = agent.get_state().to_dict()
print(json.dumps(state_dict, indent=2))

agent.stop()
```

**Output:**
```json
{
  "agent_type": "context",
  "agent_version": "1.0.0",
  "model": "Claude",
  "workspace": {
    "path": "/Users/dev/my-project",
    "name": "my-project",
    "git": {
      "is_repo": true,
      "branch": "main"
    }
  },
  "context_window": {
    "max_tokens": 200000,
    "tokens_used": 45000,
    "usage_pct": 22
  },
  "display": "[Claude] 📁 my-project 🌿 main | 📊 22%",
  "last_updated": "2026-01-28T10:30:45.123456",
  "sensor_version": "1.0.0"
}
```

---

## Event Handling

### Basic Event Subscription

```python
from context_agent import ContextAgent, EventType

def on_branch_change(event):
    print(f"Branch changed: {event.old_value} -> {event.new_value}")
    print(f"Timestamp: {event.timestamp}")

agent = ContextAgent()

# Register event handler
agent.on_change(EventType.BRANCH_CHANGED, on_branch_change)

# Start monitoring
agent.start()

# Agent will now call on_branch_change whenever branch changes
```

### Multiple Event Handlers

```python
from context_agent import ContextAgent, EventType

def log_change(event):
    """Log all changes to file"""
    with open("agent.log", "a") as f:
        f.write(f"{event.timestamp}: {event.event_type.value}\n")

def notify_user(event):
    """Show desktop notification"""
    print(f"NOTIFICATION: {event.event_type.value}")

def update_database(event):
    """Store change in database"""
    # db.insert(event.to_dict())
    pass

agent = ContextAgent()

# Register multiple handlers for same event
agent.on_change(EventType.BRANCH_CHANGED, log_change)
agent.on_change(EventType.BRANCH_CHANGED, notify_user)
agent.on_change(EventType.BRANCH_CHANGED, update_database)

agent.start()
```

### Context Threshold Monitoring

```python
from context_agent import ContextAgent, EventType

def handle_context_warning(event):
    """Alert when context usage is high"""
    usage = event.new_value

    if usage >= 90:
        print(f"🚨 CRITICAL: Context usage at {usage}%!")
        print("Consider reducing conversation length.")
    elif usage >= 75:
        print(f"⚠️ WARNING: Context usage at {usage}%")
        print("Approaching context limit.")
    else:
        print(f"ℹ️ INFO: Context usage at {usage}%")

agent = ContextAgent(config={"context_threshold": 75})
agent.on_change(EventType.CONTEXT_THRESHOLD, handle_context_warning)
agent.start()
```

### All Events Monitoring

```python
from context_agent import ContextAgent, EventType

def handle_all_events(event):
    """Handle all state changes"""
    print(f"Event: {event.event_type.value}")
    print(f"Old: {event.old_value}")
    print(f"New: {event.new_value}")
    print(f"Metadata: {event.metadata}")
    print("-" * 40)

agent = ContextAgent()

# Subscribe to all event types
for event_type in EventType:
    agent.on_change(event_type, handle_all_events)

agent.start()
```

### Unsubscribing from Events

```python
from context_agent import ContextAgent, EventType

def temp_handler(event):
    print(f"Temporary handler: {event.new_value}")

agent = ContextAgent()
agent.on_change(EventType.BRANCH_CHANGED, temp_handler)
agent.start()

# Later, remove the handler
agent.off(EventType.BRANCH_CHANGED, temp_handler)
```

---

## Custom Configuration

### Configuration Dictionary

```python
from context_agent import ContextAgent

config = {
    "polling_interval": 10,        # Poll every 10 seconds
    "context_threshold": 85,       # Alert at 85% usage
    "sensor_timeout": 3,           # 3 second sensor timeout
    "enable_zerodb": True,         # Enable ZeroDB integration
    "zerodb_project_id": "proj_123"
}

agent = ContextAgent(config=config)
agent.start()
```

### Environment-Based Configuration

```python
import os
from context_agent import ContextAgent

config = {
    "polling_interval": int(os.getenv("AGENT_POLLING_INTERVAL", "5")),
    "context_threshold": int(os.getenv("AGENT_CONTEXT_THRESHOLD", "80")),
    "enable_zerodb": os.getenv("ENABLE_ZERODB", "false").lower() == "true",
    "zerodb_api_key": os.getenv("ZERODB_API_KEY", ""),
    "zerodb_project_id": os.getenv("ZERODB_PROJECT_ID", "")
}

agent = ContextAgent(config=config)
agent.start()
```

### Configuration from File

```python
import json
from context_agent import ContextAgent

# Load configuration from JSON file
with open("agent_config.json") as f:
    config = json.load(f)

agent = ContextAgent(config=config)
agent.start()
```

**agent_config.json:**
```json
{
  "polling_interval": 15,
  "context_threshold": 90,
  "sensor_timeout": 5,
  "enable_zerodb": false
}
```

---

## ZeroDB Integration

### Basic ZeroDB Logging

```python
from context_agent import ContextAgent, EventType
import requests

ZERODB_API_URL = "https://api.zerodb.ainative.studio"
ZERODB_API_KEY = "your_api_key"
ZERODB_PROJECT_ID = "your_project_id"

def log_to_zerodb(event):
    """Log state changes to ZeroDB"""
    payload = {
        "event_type": event.event_type.value,
        "timestamp": event.timestamp,
        "data": {
            "old_value": event.old_value,
            "new_value": event.new_value,
            "metadata": event.metadata
        }
    }

    headers = {
        "Authorization": f"Bearer {ZERODB_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{ZERODB_API_URL}/projects/{ZERODB_PROJECT_ID}/events",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to log to ZeroDB: {e}")

agent = ContextAgent()
agent.on_change(EventType.STATE_UPDATED, log_to_zerodb)
agent.start()
```

### State Persistence

```python
from context_agent import ContextAgent
import requests
import time

class ZeroDBStateStore:
    def __init__(self, api_key, project_id):
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = "https://api.zerodb.ainative.studio"

    def save_state(self, state):
        """Save agent state to ZeroDB"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "table": "agent_states",
            "data": state.to_dict()
        }

        response = requests.post(
            f"{self.base_url}/projects/{self.project_id}/tables/insert",
            json=payload,
            headers=headers
        )
        return response.json()

# Initialize
store = ZeroDBStateStore("your_api_key", "your_project_id")
agent = ContextAgent()
agent.start()

# Periodically save state
while True:
    state = agent.get_state()
    store.save_state(state)
    time.sleep(60)  # Save every minute
```

---

## Multiple Agent Instances

### Monitoring Multiple Workspaces

```python
from context_agent import ContextAgent
import threading

class WorkspaceMonitor:
    def __init__(self, workspaces):
        self.agents = {}

        for name, path in workspaces.items():
            config = {"workspace_path": path}
            agent = ContextAgent(config=config)
            self.agents[name] = agent

    def start_all(self):
        """Start monitoring all workspaces"""
        for name, agent in self.agents.items():
            agent.start()
            print(f"Started monitoring: {name}")

    def stop_all(self):
        """Stop all agents"""
        for agent in self.agents.values():
            agent.stop()

    def get_status(self):
        """Get status of all workspaces"""
        status = {}
        for name, agent in self.agents.items():
            state = agent.get_state()
            status[name] = {
                "branch": state.workspace.git.branch,
                "context_usage": state.context_window.usage_pct
            }
        return status

# Usage
workspaces = {
    "frontend": "/Users/dev/frontend",
    "backend": "/Users/dev/backend",
    "docs": "/Users/dev/docs"
}

monitor = WorkspaceMonitor(workspaces)
monitor.start_all()

# Check status
status = monitor.get_status()
for name, info in status.items():
    print(f"{name}: {info['branch']} ({info['context_usage']}%)")
```

---

## Error Handling

### Graceful Error Handling

```python
from context_agent import ContextAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_start_agent():
    """Start agent with error handling"""
    agent = ContextAgent()

    try:
        agent.start()
        logger.info("Agent started successfully")
        return agent
    except FileNotFoundError:
        logger.error("Sensor script not found")
        logger.error("Please ensure scripts/context_sensor.sh exists")
        return None
    except RuntimeError as e:
        logger.error(f"Failed to start agent: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

agent = safe_start_agent()
if agent:
    state = agent.get_state()
    print(state.display)
```

### Retry Logic

```python
from context_agent import ContextAgent
import time

def start_agent_with_retry(max_retries=3, delay=2):
    """Start agent with retry logic"""
    for attempt in range(max_retries):
        try:
            agent = ContextAgent()
            agent.start()
            print("Agent started successfully")
            return agent
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("All retry attempts failed")
                raise

agent = start_agent_with_retry()
```

### Event Handler Error Handling

```python
from context_agent import ContextAgent, EventType
import logging

logger = logging.getLogger(__name__)

def safe_event_handler(event):
    """Event handler with error handling"""
    try:
        # Process event
        process_event(event)
    except Exception as e:
        logger.error(f"Error in event handler: {e}")
        logger.exception(e)

def process_event(event):
    """Actual event processing logic"""
    # ... processing logic ...
    pass

agent = ContextAgent()
agent.on_change(EventType.STATE_UPDATED, safe_event_handler)
agent.start()
```

---

## IDE Integration

### VS Code Extension Example

```python
"""
Context Agent integration for VS Code
Displays agent status in status bar
"""
from context_agent import ContextAgent, EventType
import json
import sys

class VSCodeIntegration:
    def __init__(self):
        self.agent = ContextAgent()
        self.agent.on_change(EventType.STATE_UPDATED, self.on_state_change)

    def on_state_change(self, event):
        """Send state to VS Code extension"""
        state = self.agent.get_state()

        # Send to VS Code via stdout
        message = {
            "type": "state_update",
            "data": {
                "display": state.display,
                "workspace": state.workspace.name,
                "branch": state.workspace.git.branch,
                "context_pct": state.context_window.usage_pct
            }
        }

        print(json.dumps(message), flush=True)

    def start(self):
        self.agent.start()

        # Send initial state
        state = self.agent.get_state()
        self.on_state_change(None)

    def stop(self):
        self.agent.stop()

if __name__ == "__main__":
    integration = VSCodeIntegration()
    integration.start()

    # Keep running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        integration.stop()
```

### Terminal Prompt Integration

```bash
# Add to .bashrc or .zshrc

# Function to get context header
get_context_header() {
    python3 -c "
from context_agent import ContextAgent
agent = ContextAgent()
agent.start()
print(agent.get_display_header())
agent.stop()
"
}

# Update PS1 with context
export PS1="\$(get_context_header) \$ "
```

**Python helper script:**
```python
#!/usr/bin/env python3
"""
Context header for terminal prompt
Usage: prompt_context.py
"""
from context_agent import ContextAgent

def main():
    try:
        agent = ContextAgent()
        agent.start()
        print(agent.get_display_header(), end='')
        agent.stop()
    except:
        print("[Context unavailable]", end='')

if __name__ == "__main__":
    main()
```

---

## CLI Usage

### Command-Line Tool

```python
#!/usr/bin/env python3
"""
Context Agent CLI tool
"""
import argparse
import json
from context_agent import ContextAgent

def main():
    parser = argparse.ArgumentParser(description="Context Agent CLI")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--watch", action="store_true", help="Watch for changes")
    parser.add_argument("--threshold", type=int, default=80, help="Context threshold")

    args = parser.parse_args()

    agent = ContextAgent(config={"context_threshold": args.threshold})
    agent.start()

    if args.watch:
        # Watch mode
        def on_change(event):
            if args.json:
                print(json.dumps(event.to_dict()))
            else:
                print(f"{event.event_type.value}: {event.old_value} -> {event.new_value}")

        from context_agent import EventType
        for event_type in EventType:
            agent.on_change(event_type, on_change)

        print("Watching for changes... (Ctrl+C to stop)")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        # Single output
        state = agent.get_state()
        if args.json:
            print(state.to_json())
        else:
            print(state.display)

    agent.stop()

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Get current state
python cli.py

# Get JSON output
python cli.py --json

# Watch for changes
python cli.py --watch

# Custom threshold
python cli.py --threshold 90
```

---

## Advanced Patterns

### State Caching

```python
from context_agent import ContextAgent
import pickle
import os

class CachedContextAgent:
    CACHE_FILE = ".context_cache.pkl"

    def __init__(self):
        self.agent = ContextAgent()
        self.cache = self.load_cache()

    def load_cache(self):
        """Load cached state"""
        if os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, "rb") as f:
                return pickle.load(f)
        return None

    def save_cache(self, state):
        """Save state to cache"""
        with open(self.CACHE_FILE, "wb") as f:
            pickle.dump(state, f)

    def get_state(self):
        """Get state with caching"""
        current = self.agent.get_state()

        # Check if changed
        if self.cache and not current.has_changed(self.cache):
            return self.cache

        # Update cache
        self.cache = current
        self.save_cache(current)
        return current
```

### Async Integration

```python
import asyncio
from context_agent import ContextAgent, EventType

class AsyncContextAgent:
    def __init__(self):
        self.agent = ContextAgent()
        self.event_queue = asyncio.Queue()

        # Register event handler
        for event_type in EventType:
            self.agent.on_change(event_type, self.enqueue_event)

    def enqueue_event(self, event):
        """Add event to async queue"""
        asyncio.create_task(self.event_queue.put(event))

    async def start(self):
        """Start agent and event processor"""
        self.agent.start()

        # Process events asynchronously
        while True:
            event = await self.event_queue.get()
            await self.process_event(event)

    async def process_event(self, event):
        """Process event asynchronously"""
        print(f"Async processing: {event.event_type.value}")
        # Async operations here
        await asyncio.sleep(0.1)

# Usage
async def main():
    agent = AsyncContextAgent()
    await agent.start()

asyncio.run(main())
```

### Metric Collection

```python
from context_agent import ContextAgent, EventType
from collections import defaultdict
import time

class ContextMetrics:
    def __init__(self):
        self.agent = ContextAgent()
        self.metrics = defaultdict(int)
        self.start_time = time.time()

        # Track events
        for event_type in EventType:
            self.agent.on_change(event_type, self.record_metric)

    def record_metric(self, event):
        """Record event metric"""
        self.metrics[event.event_type.value] += 1

    def get_summary(self):
        """Get metrics summary"""
        runtime = time.time() - self.start_time
        state = self.agent.get_state()

        return {
            "runtime_seconds": runtime,
            "current_state": state.to_dict(),
            "event_counts": dict(self.metrics),
            "avg_context_usage": state.context_window.usage_pct
        }

# Usage
metrics = ContextMetrics()
metrics.agent.start()

# ... run for a while ...

summary = metrics.get_summary()
print(summary)
```

---

## Next Steps

- [API Reference](api.md) - Detailed API documentation
- [Configuration Guide](configuration.md) - Configuration options
- [Architecture](architecture.md) - System design
