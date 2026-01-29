# ZeroDB Integration Guide

## Overview

The Context Agent includes optional integration with AINative ZeroDB for persistent state storage and event logging. This feature allows you to:

- **Store agent state snapshots** - Track state changes over time
- **Log state change events** - Analyze patterns and transitions
- **Query historical data** - Review past states and events
- **Monitor agent behavior** - Build analytics dashboards

## Features

- **Automatic state persistence** - Every state change is stored
- **Event logging** - All state transition events are logged
- **Flexible querying** - Filter by workspace, branch, event type, etc.
- **Graceful degradation** - Agent works normally if ZeroDB is unavailable
- **Async operations** - Non-blocking persistence using background threads
- **Error handling** - Robust error handling with fallbacks

## Table of Contents

1. [Setup](#setup)
2. [Configuration](#configuration)
3. [Usage Examples](#usage-examples)
4. [Querying Data](#querying-data)
5. [Table Schema](#table-schema)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

## Setup

### Prerequisites

1. **AINative Account** - Sign up at [ainative.studio](https://ainative.studio)
2. **ZeroDB Project** - Create a project in your AINative dashboard
3. **API Credentials** - Get your API key and project ID

### Installation

The Context Agent requires the AINative Python SDK:

```bash
# Install AINative SDK
pip install ainative

# Or from the core repository
pip install -e /path/to/core/developer-tools/sdks/python
```

### Environment Variables

Set up your ZeroDB credentials:

```bash
# Required for ZeroDB integration
export CONTEXT_AGENT_ENABLE_ZERODB=true
export CONTEXT_AGENT_ZERODB_API_KEY="your_api_key_here"
export CONTEXT_AGENT_ZERODB_PROJECT_ID="your_project_id"

# Optional
export CONTEXT_AGENT_ZERODB_ENABLE_LOGGING=true
```

## Configuration

### Option 1: Environment Variables

```bash
# Enable ZeroDB persistence
export CONTEXT_AGENT_ENABLE_ZERODB=true
export CONTEXT_AGENT_ZERODB_API_KEY="sk_..."
export CONTEXT_AGENT_ZERODB_PROJECT_ID="proj_..."
export CONTEXT_AGENT_ZERODB_ENABLE_LOGGING=true
```

### Option 2: Configuration File

Create `config/default.json`:

```json
{
  "enable_zerodb": true,
  "zerodb_api_key": "sk_...",
  "zerodb_project_id": "proj_...",
  "zerodb_enable_logging": true,
  "polling_interval": 5.0,
  "context_threshold": 80,
  "sensor_timeout": 5.0
}
```

### Option 3: Programmatic Configuration

```python
from context_agent import AgentConfig, create_context_agent

# Create config
config = AgentConfig(
    enable_zerodb=True,
    zerodb_api_key="sk_...",
    zerodb_project_id="proj_...",
    zerodb_enable_logging=True
)

# Create agent with config
agent = create_context_agent(config=config)
```

## Usage Examples

### Basic Usage with ZeroDB

```python
from context_agent import create_context_agent

# Create agent with automatic config loading
agent = create_context_agent()

# Get state (automatically persisted to ZeroDB)
state = agent.get_state()
print(f"Current state: {state.display}")

# ZeroDB status
status = agent.get_zerodb_status()
print(f"ZeroDB enabled: {status['enabled']}")
print(f"ZeroDB initialized: {status['initialized']}")
```

### Manual Persistence Control

```python
from context_agent import ContextAgentWithZeroDB, AgentConfig

# Create agent
config = AgentConfig(enable_zerodb=True, ...)
agent = ContextAgentWithZeroDB(config=config)

# Get state without persisting
state = agent.get_state(persist=False)

# Get state and persist
state = agent.get_state(persist=True)
```

### Event Handlers with ZeroDB

```python
from context_agent import create_context_agent
from context_agent import EventType

agent = create_context_agent()

# Register event handler
def on_branch_change(event):
    print(f"Branch changed: {event.old_value} -> {event.new_value}")
    print("Event automatically logged to ZeroDB!")

agent.on(EventType.BRANCH_CHANGED, on_branch_change)

# Trigger state refresh
agent.get_state()
```

### Context Manager Pattern

```python
from context_agent import create_context_agent

# Automatic cleanup
with create_context_agent() as agent:
    state = agent.get_state()
    print(state.display)

# Agent shutdown and ZeroDB cleanup happens automatically
```

## Querying Data

### Query Historical State

```python
import asyncio
from context_agent import create_context_agent

async def main():
    agent = create_context_agent()

    # Get last 50 state snapshots
    history = await agent.get_state_history(limit=50)

    for record in history:
        print(f"[{record['timestamp']}] {record['display']}")
        print(f"  Workspace: {record['workspace_name']}")
        print(f"  Branch: {record['git_branch']}")
        print(f"  Context: {record['context_usage_pct']}%")
        print()

    # Filter by workspace
    workspace_history = await agent.get_state_history(
        limit=20,
        workspace_name="my-project"
    )

    # Filter by branch
    branch_history = await agent.get_state_history(
        limit=20,
        git_branch="main"
    )

asyncio.run(main())
```

### Query Event Logs

```python
import asyncio
from context_agent import create_context_agent

async def main():
    agent = create_context_agent()

    # Get all events
    all_events = await agent.get_event_logs(limit=100)

    # Get only branch change events
    branch_events = await agent.get_event_logs(
        event_type="branch_changed",
        limit=50
    )

    for event in branch_events:
        print(f"[{event['timestamp']}] {event['event_type']}")
        print(f"  {event['old_value']} -> {event['new_value']}")

asyncio.run(main())
```

### Get Statistics

```python
import asyncio
from context_agent import create_context_agent

async def main():
    agent = create_context_agent()

    stats = await agent.get_zerodb_statistics()

    print(f"Enabled: {stats['enabled']}")
    print(f"Project ID: {stats['project_id']}")
    print(f"State snapshots: {stats['state_snapshots']}")
    print(f"Event logs: {stats['event_logs']}")

asyncio.run(main())
```

## Table Schema

### context_agent_state

Stores agent state snapshots.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique record ID (UUID) |
| timestamp | string | ISO timestamp of state |
| agent_version | string | Agent version |
| model | string | AI model name (e.g., "Claude") |
| workspace_name | string | Workspace name |
| workspace_path | string | Workspace path |
| git_branch | string | Current git branch |
| git_is_repo | boolean | Whether workspace is git repo |
| context_usage_pct | number | Context window usage % |
| context_tokens_used | number | Tokens used |
| context_max_tokens | number | Max tokens available |
| full_state | object | Complete state object (JSON) |
| display | string | Display string |
| created_at | string | Record creation timestamp |

**Indexes:** timestamp, workspace_name, git_branch

### context_agent_events

Stores state change events.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique event ID (UUID) |
| timestamp | string | ISO timestamp of event |
| event_type | string | Event type (e.g., "branch_changed") |
| old_value | string | Previous value |
| new_value | string | New value |
| metadata | object | Additional event metadata (JSON) |
| created_at | string | Record creation timestamp |

**Indexes:** timestamp, event_type

## Error Handling

### Graceful Degradation

ZeroDB integration is designed to fail gracefully:

```python
from context_agent import create_context_agent

# Agent works even if ZeroDB credentials are invalid
agent = create_context_agent()

# State still works
state = agent.get_state()  # Returns state even if ZeroDB fails

# Check if ZeroDB is available
status = agent.get_zerodb_status()
if not status['enabled']:
    print(f"ZeroDB disabled: {status.get('initialization_error')}")
```

### Missing Credentials

```python
from context_agent import AgentConfig, ContextAgentWithZeroDB

# ZeroDB enabled but no credentials
config = AgentConfig(enable_zerodb=True)

agent = ContextAgentWithZeroDB(config=config)

# Agent logs warning but continues to work
state = agent.get_state()  # Works, but no persistence

# Check status
status = agent.get_zerodb_status()
print(status['initialization_error'])  # "Missing API key" or similar
```

### Network Failures

```python
from context_agent import create_context_agent

agent = create_context_agent()

# Even if network fails, agent continues
state = agent.get_state()  # Always returns state

# Persistence failures are logged but don't raise exceptions
```

## Best Practices

### 1. Use Configuration Files for Production

```python
# Don't hardcode credentials
agent = create_context_agent(config_file="production_config.json")
```

### 2. Check ZeroDB Status on Startup

```python
agent = create_context_agent()

status = agent.get_zerodb_status()
if not status['initialized']:
    logger.warning(f"ZeroDB not available: {status}")
```

### 3. Use Context Manager for Cleanup

```python
# Ensures proper shutdown
with create_context_agent() as agent:
    # Use agent
    pass
```

### 4. Query in Batches for Large Datasets

```python
import asyncio

async def get_all_history(agent, workspace_name):
    batch_size = 100
    offset = 0
    all_records = []

    while True:
        batch = await agent.get_state_history(
            limit=batch_size,
            workspace_name=workspace_name
        )

        if not batch:
            break

        all_records.extend(batch)
        offset += batch_size

        if len(batch) < batch_size:
            break

    return all_records
```

### 5. Monitor Storage Usage

```python
import asyncio

async def check_storage(agent):
    stats = await agent.get_zerodb_statistics()

    total_records = stats['state_snapshots'] + stats['event_logs']

    if total_records > 100000:
        logger.warning(f"High record count: {total_records}")
```

### 6. Handle Async Operations Properly

```python
import asyncio
from context_agent import create_context_agent

# Create event loop
async def main():
    agent = create_context_agent()

    # All query operations are async
    history = await agent.get_state_history(limit=10)
    events = await agent.get_event_logs(limit=10)
    stats = await agent.get_zerodb_statistics()

    return history, events, stats

# Run with asyncio
history, events, stats = asyncio.run(main())
```

## Troubleshooting

### ZeroDB Not Initializing

**Check credentials:**
```python
import os
print(os.getenv("CONTEXT_AGENT_ZERODB_API_KEY"))
print(os.getenv("CONTEXT_AGENT_ZERODB_PROJECT_ID"))
```

**Check status:**
```python
agent = create_context_agent()
status = agent.get_zerodb_status()
print(status)
```

### Tables Not Created

Tables are created automatically on first use. Check logs:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

agent = create_context_agent()
agent.get_state()  # Triggers table creation
```

### Query Returns Empty Results

Check if persistence is working:

```python
import asyncio

async def check():
    agent = create_context_agent()

    # Store some states
    for _ in range(5):
        agent.get_state()
        await asyncio.sleep(1)

    # Query
    history = await agent.get_state_history(limit=10)
    print(f"Found {len(history)} records")

asyncio.run(check())
```

## Advanced Usage

### Custom Persistence Logic

```python
from context_agent import ZeroDBPersistence, AgentState

# Create persistence layer directly
persistence = ZeroDBPersistence(
    api_key="sk_...",
    project_id="proj_...",
    enabled=True
)

# Initialize
await persistence.initialize()

# Store custom state
state = AgentState(...)
await persistence.store_state(state)

# Query
history = await persistence.get_state_history(limit=10)
```

### Integration with Analytics

```python
import asyncio
from context_agent import create_context_agent

async def analyze_branch_changes():
    agent = create_context_agent()

    # Get branch change events
    events = await agent.get_event_logs(
        event_type="branch_changed",
        limit=1000
    )

    # Analyze patterns
    branch_frequency = {}
    for event in events:
        branch = event['new_value']
        branch_frequency[branch] = branch_frequency.get(branch, 0) + 1

    print("Most used branches:")
    for branch, count in sorted(
        branch_frequency.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]:
        print(f"  {branch}: {count} switches")

asyncio.run(analyze_branch_changes())
```

## API Reference

### ContextAgentWithZeroDB

See [API Documentation](api.md) for complete API reference.

Key methods:
- `get_state(persist=True)` - Get state with optional persistence
- `get_state_history(limit, workspace_name, git_branch)` - Query historical states
- `get_event_logs(event_type, limit)` - Query event logs
- `get_zerodb_statistics()` - Get storage statistics
- `get_zerodb_status()` - Get integration status
- `shutdown()` - Cleanup resources

## Support

For issues or questions:
- GitHub Issues: [context-agent/issues](https://github.com/AINative-Studio/context-agent/issues)
- Documentation: [ZeroDB Docs](https://zerodb.ainative.studio)
- Email: support@ainative.studio
