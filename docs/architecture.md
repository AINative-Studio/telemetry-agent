# Architecture

System architecture and design documentation for the Context Agent.

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Design Decisions](#design-decisions)
- [Performance Considerations](#performance-considerations)
- [Security Model](#security-model)
- [Scalability](#scalability)
- [Future Enhancements](#future-enhancements)

---

## System Overview

The Context Agent is a lightweight, event-driven monitoring system designed to track runtime context for AI-assisted development environments. It follows a clean separation of concerns with distinct layers for sensing, processing, and presentation.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Context Agent (Python)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Sensor Layer (Bash)                     │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  context_sensor.sh                                   │  │  │
│  │  │  - STDIN: JSON input (config)                        │  │  │
│  │  │  - STDOUT: Display string                            │  │  │
│  │  │  - STDERR: Structured JSON (full state)              │  │  │
│  │  │  - Dependencies: bash, jq, git                       │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             ⬇                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Agent Core (Python)                     │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  ContextAgent                                        │  │  │
│  │  │  - Execute sensor subprocess                         │  │  │
│  │  │  - Parse STDOUT/STDERR output                        │  │  │
│  │  │  - Error handling & retries                          │  │  │
│  │  │  - Polling loop management                           │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             ⬇                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 State Management (Python)                  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  AgentState                                          │  │  │
│  │  │  - Normalized state models                           │  │  │
│  │  │  - State comparison (has_changed, get_changes)       │  │  │
│  │  │  - JSON serialization                                │  │  │
│  │  │  - In-memory caching                                 │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             ⬇                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Event System (Python)                    │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  EventEmitter                                        │  │  │
│  │  │  - Event type definitions                            │  │  │
│  │  │  - Change detection                                  │  │  │
│  │  │  - Synchronous event emission                        │  │  │
│  │  │  - Handler registration/removal                      │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             ⬇                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    API Surface (Python)                    │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Public Methods                                      │  │  │
│  │  │  - get_state() -> AgentState                         │  │  │
│  │  │  - get_display_header() -> str                       │  │  │
│  │  │  - on_change(event_type, callback)                   │  │  │
│  │  │  - start() / stop() / refresh()                      │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             ⬇                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              ZeroDB Integration (Optional)                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  ZeroDBClient                                        │  │  │
│  │  │  - State persistence                                 │  │  │
│  │  │  - Event logging                                     │  │  │
│  │  │  - Batch processing                                  │  │  │
│  │  │  - Rate limiting                                     │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Single Responsibility**: Each layer has one clear purpose
2. **Separation of Concerns**: Sensing, processing, and presentation are independent
3. **Event-Driven**: State changes trigger events for reactive integrations
4. **Type Safety**: Full type hints throughout the codebase
5. **Fail-Safe**: Graceful degradation when sensors fail

---

## Component Architecture

### 1. Sensor Layer

**Purpose**: Canonical source of truth for runtime context

**Implementation**: Bash script (`scripts/context_sensor.sh`)

**Responsibilities**:
- Detect current workspace and git repository
- Read AI model and context window information from input
- Execute git commands to determine branch
- Calculate context usage percentage
- Emit formatted display string (STDOUT)
- Emit structured JSON data (STDERR)

**Design Decisions**:
- **Why Bash?**: Universal availability, minimal dependencies, fast execution
- **Why jq?**: Robust JSON processing without Python dependencies
- **Why STDERR for JSON?**: Separates machine-readable data from human-readable display

**Inputs/Outputs**:
```
INPUT (STDIN):  JSON configuration
OUTPUT (STDOUT): Single-line display string
OUTPUT (STDERR): Structured JSON state
EXIT CODE:      0 = success, non-zero = error
```

**Example**:
```bash
# Input
echo '{"model": "Claude", "context_window": {"tokens_used": 45000}}' | ./context_sensor.sh

# STDOUT
[Claude] 📁 my-project 🌿 main | 📊 22%

# STDERR
{
  "version": "1.0.0",
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
  }
}
```

---

### 2. Agent Core

**Purpose**: Orchestrate sensor execution and manage agent lifecycle

**Implementation**: Python class (`src/agent.py`)

**Responsibilities**:
- Execute sensor subprocess with timeout
- Parse sensor output (STDOUT and STDERR)
- Handle sensor failures with retry logic
- Manage polling loop with configurable interval
- Coordinate state updates and event emission

**Key Components**:

```python
class ContextAgent:
    def __init__(self, config, sensor_path):
        self.config = config
        self.sensor_path = sensor_path
        self._running = False
        self._state = None
        self._event_emitter = EventEmitter()

    def start(self):
        """Start monitoring loop"""

    def stop(self):
        """Stop monitoring and cleanup"""

    def _execute_sensor(self):
        """Run sensor subprocess"""

    def _parse_sensor_output(self, stdout, stderr):
        """Parse sensor output into AgentState"""

    def _polling_loop(self):
        """Main polling loop"""
```

**Error Handling**:
- Sensor execution timeout → retry with exponential backoff
- Sensor exit code != 0 → log error, use cached state
- JSON parse failure → log error, use previous state
- Subprocess crash → restart with delay

**Threading Model**:
- Main thread: API calls (get_state, on_change, etc.)
- Worker thread: Polling loop
- Event handlers: Execute synchronously in main thread

---

### 3. State Management

**Purpose**: Normalized, type-safe state representation

**Implementation**: Dataclasses (`src/state.py`)

**State Hierarchy**:
```
AgentState
├── agent_type: str
├── agent_version: str
├── model: str
├── workspace: WorkspaceInfo
│   ├── path: str
│   ├── name: str
│   └── git: GitInfo
│       ├── is_repo: bool
│       └── branch: str
├── context_window: ContextWindowInfo
│   ├── max_tokens: int
│   ├── tokens_used: int
│   └── usage_pct: int
├── display: str
├── last_updated: str
└── sensor_version: str
```

**Design Decisions**:
- **Dataclasses**: Type safety, immutability, JSON serialization
- **No inference**: All fields come directly from sensor
- **Timestamps**: ISO 8601 format for portability
- **Nested structure**: Logical grouping of related data

**State Comparison**:
```python
def has_changed(self, other: AgentState) -> bool:
    """Compare significant fields (excludes timestamps)"""
    return (
        self.model != other.model or
        self.workspace.name != other.workspace.name or
        self.workspace.git.branch != other.workspace.git.branch or
        self.context_window.usage_pct != other.context_window.usage_pct
    )

def get_changes(self, other: AgentState) -> Dict[str, Any]:
    """Return dictionary of changed fields with old/new values"""
```

---

### 4. Event System

**Purpose**: Reactive integration for state changes

**Implementation**: Observer pattern (`src/events.py`)

**Event Types**:
```python
class EventType(Enum):
    MODEL_CHANGED = "model_changed"           # AI model changed
    WORKSPACE_CHANGED = "workspace_changed"   # Directory changed
    BRANCH_CHANGED = "branch_changed"         # Git branch changed
    CONTEXT_THRESHOLD = "context_threshold"   # Context usage crossed threshold
    STATE_UPDATED = "state_updated"           # Any state update
```

**Event Flow**:
```
1. Sensor executes
2. New state parsed
3. State comparison (has_changed)
4. If changed:
   a. Determine specific changes (get_changes)
   b. Create StateChangeEvent for each change
   c. Emit to registered handlers
5. Update cached state
```

**Event Structure**:
```python
@dataclass
class StateChangeEvent:
    event_type: EventType       # What changed
    timestamp: str              # When it changed
    old_value: Any              # Previous value
    new_value: Any              # New value
    metadata: Dict[str, Any]    # Additional context
```

**Handler Execution**:
- Synchronous execution in registration order
- Exceptions in handlers are caught and logged
- Failed handler doesn't prevent other handlers from running

---

### 5. API Surface

**Purpose**: Clean, intuitive public interface

**Implementation**: Public methods on ContextAgent

**API Design Principles**:
- **Simple**: Minimal methods for common use cases
- **Type-safe**: Full type hints for IDE support
- **Non-blocking**: get_state() returns cached state
- **Flexible**: Support both polling and event-driven patterns

**Public Methods**:
```python
# Lifecycle
agent.start() -> None
agent.stop() -> None

# State access
agent.get_state() -> AgentState
agent.get_display_header() -> str
agent.refresh() -> AgentState  # Force immediate update

# Event subscription
agent.on_change(event_type, callback) -> None
agent.off(event_type, callback) -> None
```

---

### 6. ZeroDB Integration

**Purpose**: Optional persistent storage and logging

**Implementation**: Client wrapper (`src/zerodb.py`)

**Responsibilities**:
- Batch event logging
- State persistence
- Rate limiting (respect API limits)
- Retry with exponential backoff
- Graceful degradation if unavailable

**Integration Pattern**:
```python
def log_to_zerodb(event):
    """Handler for ZeroDB logging"""
    zerodb_client.enqueue_event(event)

agent = ContextAgent(config={"enable_zerodb": True})
agent.on_change(EventType.STATE_UPDATED, log_to_zerodb)
agent.start()

# Events are batched and sent asynchronously
```

---

## Data Flow

### Normal Operation Flow

```
1. Timer triggers (polling_interval elapsed)
   ⬇
2. Agent executes sensor subprocess
   ⬇
3. Sensor reads environment (git, workspace)
   ⬇
4. Sensor emits:
   - STDOUT: Display string
   - STDERR: JSON state
   ⬇
5. Agent parses output
   ⬇
6. Create new AgentState from parsed data
   ⬇
7. Compare with previous state (has_changed)
   ⬇
8. If changed:
   a. Determine specific changes
   b. Emit events to handlers
   c. Update cached state
   ⬇
9. Return to step 1
```

### API Call Flow (get_state)

```
1. User calls agent.get_state()
   ⬇
2. Agent returns cached state (no blocking I/O)
   ⬇
3. User accesses state properties
```

### Event Handler Flow

```
1. State change detected
   ⬇
2. Agent calls event_emitter.emit(event)
   ⬇
3. EventEmitter looks up registered handlers
   ⬇
4. For each handler:
   a. Execute handler(event)
   b. Catch exceptions
   c. Log errors
   ⬇
5. All handlers complete
   ⬇
6. Continue normal operation
```

---

## Design Decisions

### Why Bash for Sensor?

**Pros**:
- Universal availability on Unix-like systems
- Minimal dependencies (bash, jq, git already installed)
- Fast execution (< 50ms typical)
- Easy to test independently
- No Python interpreter overhead

**Cons**:
- Windows compatibility requires WSL
- Less robust error handling than Python

**Decision**: Bash is optimal for sensor layer due to speed and minimal dependencies.

---

### Why Separate STDOUT/STDERR?

**Rationale**:
- STDOUT: Human-readable display (terminal prompts, status bars)
- STDERR: Machine-readable JSON (agent parsing)
- Clean separation of concerns
- Easy to test each output independently
- Follows Unix philosophy

**Example Use Cases**:
```bash
# Use display string in terminal
PS1=$(./context_sensor.sh)

# Parse JSON for programmatic use
STATE=$(./context_sensor.sh 2>&1 1>/dev/null | jq '.workspace.name')
```

---

### Why Synchronous Event Handlers?

**Pros**:
- Simpler mental model
- Predictable execution order
- No race conditions
- Easier debugging

**Cons**:
- Blocking handlers delay state updates
- No parallel processing

**Decision**: Synchronous is appropriate because:
- Event handlers should be lightweight
- State updates are not time-critical (5s polling)
- Users can implement async within handlers if needed

---

### Why Polling Instead of File Watching?

**Pros of Polling**:
- Works with all git operations
- No race conditions with fast git commands
- Predictable resource usage
- Simpler implementation

**Cons of Polling**:
- Slight delay in detecting changes
- Regular CPU usage (minimal)

**Decision**: Polling with 5s interval balances responsiveness and resource usage.

---

## Performance Considerations

### CPU Usage

**Typical Load**:
- Sensor execution: 20-50ms every 5 seconds
- Python overhead: 5-10ms
- Total: < 1% CPU on modern systems

**Optimization Strategies**:
- Caching: Avoid redundant sensor calls
- Adaptive polling: Slow down when idle
- Lazy loading: Load ZeroDB client only when enabled

---

### Memory Usage

**Typical Footprint**:
- Python process: 20-30 MB
- State cache: < 1 KB
- Event handlers: Minimal

**Optimization Strategies**:
- Single state instance (no history)
- Bounded event queue
- No persistent logs in memory

---

### Latency

**State Access**: O(1) - Returns cached state
**Event Emission**: O(n) where n = number of handlers (typically < 10)
**Sensor Execution**: O(git_repo_size) - typically < 50ms

---

## Security Model

### Threat Model

**In Scope**:
- Sensor script execution (arbitrary code execution)
- Configuration file parsing (malicious JSON)
- Event handler exceptions (DoS)

**Out of Scope**:
- Network attacks (agent is local-only by default)
- ZeroDB API security (handled by ZeroDB)

---

### Mitigations

1. **Sensor Isolation**:
   - Execute in subprocess with timeout
   - No shell injection (use subprocess.run with list args)
   - Read-only workspace access

2. **Configuration Validation**:
   - Type checking on all config values
   - Range validation (e.g., polling_interval > 0)
   - No code execution in config

3. **Event Handler Safety**:
   - Exception catching around all handlers
   - No handler can crash the agent
   - Timeout for slow handlers (future)

---

## Scalability

### Single Workspace

**Current Design**: Optimized for monitoring single workspace
**Performance**: Excellent (< 1% CPU, < 30MB RAM)

---

### Multiple Workspaces

**Approach**: Run multiple agent instances

```python
agents = {
    "frontend": ContextAgent(config={"workspace_path": "/path/to/frontend"}),
    "backend": ContextAgent(config={"workspace_path": "/path/to/backend"})
}

for agent in agents.values():
    agent.start()
```

**Resource Usage**: Linear scaling (30MB per agent)

---

### High-Frequency Updates

**Challenge**: Default 5s polling may be too slow

**Solution**: Reduce polling interval
```python
config = {"polling_interval": 1}  # 1-second updates
```

**Trade-off**: Higher CPU usage (still < 5% on modern systems)

---

## Future Enhancements

### 1. Async Support

```python
async with ContextAgent() as agent:
    state = await agent.get_state_async()
```

### 2. Plugin System

```python
agent.register_plugin(CustomSensorPlugin())
```

### 3. State History

```python
history = agent.get_state_history(duration="1h")
```

### 4. Adaptive Polling

```python
# Slow down when idle, speed up when active
config = {"adaptive_polling": True}
```

### 5. WebSocket Events

```python
# Real-time events over WebSocket
agent.start_websocket_server(port=8080)
```

---

## Next Steps

- [API Reference](api.md) - Detailed API documentation
- [Configuration Guide](configuration.md) - Configuration options
- [Deployment Guide](deployment.md) - Production deployment
- [Examples](examples.md) - Usage examples
