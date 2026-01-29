# Context Agent API Reference

Complete API documentation for the Context Agent library.

## Table of Contents

- [ContextAgent](#contextagent)
- [AgentState](#agentstate)
- [WorkspaceInfo](#workspaceinfo)
- [GitInfo](#gitinfo)
- [ContextWindowInfo](#contextwindowinfo)
- [EventType](#eventtype)
- [StateChangeEvent](#statechangeevent)
- [EventEmitter](#eventemitter)

---

## ContextAgent

Main agent class for monitoring runtime context.

### Constructor

```python
ContextAgent(
    config: Optional[Dict[str, Any]] = None,
    sensor_path: Optional[str] = None
)
```

**Parameters:**
- `config` (Optional[Dict[str, Any]]): Configuration dictionary. If not provided, defaults are used.
- `sensor_path` (Optional[str]): Path to the sensor script. Defaults to `scripts/context_sensor.sh`.

**Example:**
```python
from context_agent import ContextAgent

# Default configuration
agent = ContextAgent()

# Custom configuration
agent = ContextAgent(config={
    "polling_interval": 10,
    "context_threshold": 90,
    "enable_zerodb": True
})

# Custom sensor path
agent = ContextAgent(sensor_path="/custom/path/sensor.sh")
```

### Methods

#### `start()`

Start the context monitoring agent.

```python
def start() -> None
```

**Description:** Starts periodic sensor polling and event emission. This method initializes the monitoring loop and begins tracking context changes.

**Returns:** None

**Raises:**
- `RuntimeError`: If agent is already running
- `FileNotFoundError`: If sensor script is not found

**Example:**
```python
agent = ContextAgent()
agent.start()

# Agent is now monitoring context
```

**Notes:**
- Must be called before using `get_state()` or event handlers
- Can be stopped with `stop()`

---

#### `stop()`

Stop the context monitoring agent.

```python
def stop() -> None
```

**Description:** Stops the monitoring loop and cleans up resources.

**Returns:** None

**Example:**
```python
agent = ContextAgent()
agent.start()

# ... do work ...

agent.stop()
```

**Notes:**
- Safe to call even if agent is not running
- Clears all event handlers

---

#### `get_state()`

Get current agent state.

```python
def get_state() -> AgentState
```

**Description:** Returns the current normalized agent state with all context information.

**Returns:** `AgentState` - Current state snapshot

**Raises:**
- `RuntimeError`: If agent has not been started

**Example:**
```python
agent = ContextAgent()
agent.start()

state = agent.get_state()
print(f"Model: {state.model}")
print(f"Workspace: {state.workspace.name}")
print(f"Branch: {state.workspace.git.branch}")
print(f"Context usage: {state.context_window.usage_pct}%")
```

**Notes:**
- Returns cached state (no blocking I/O)
- State is updated based on polling interval

---

#### `get_display_header()`

Get formatted display header string.

```python
def get_display_header() -> str
```

**Description:** Returns a formatted, human-readable status string suitable for display in terminal prompts or status bars.

**Returns:** `str` - Formatted display string

**Example:**
```python
agent = ContextAgent()
agent.start()

header = agent.get_display_header()
print(header)
# Output: [Claude] 📁 context-agent 🌿 main | 📊 15%
```

**Notes:**
- Same format as sensor STDOUT output
- Updates automatically based on polling interval

---

#### `on_change()`

Register an event handler for state changes.

```python
def on_change(
    event_type: Union[EventType, str],
    callback: Callable[[StateChangeEvent], None]
) -> None
```

**Parameters:**
- `event_type` (EventType | str): Type of event to listen for
- `callback` (Callable): Function that receives `StateChangeEvent`

**Returns:** None

**Example:**
```python
from context_agent import ContextAgent, EventType

def handle_branch_change(event):
    print(f"Branch changed: {event.old_value} -> {event.new_value}")

def handle_context_threshold(event):
    print(f"Context usage at {event.new_value}%")
    if event.new_value >= 80:
        print("WARNING: High context usage!")

agent = ContextAgent()
agent.on_change(EventType.BRANCH_CHANGED, handle_branch_change)
agent.on_change(EventType.CONTEXT_THRESHOLD, handle_context_threshold)
agent.start()
```

**Event Types:**
- `MODEL_CHANGED`: AI model changed
- `WORKSPACE_CHANGED`: Workspace directory changed
- `BRANCH_CHANGED`: Git branch changed
- `CONTEXT_THRESHOLD`: Context usage crossed threshold
- `STATE_UPDATED`: Any state update

**Notes:**
- Multiple handlers can be registered for the same event
- Handlers are called synchronously in registration order
- Exceptions in handlers are caught and logged

---

#### `off()`

Unregister an event handler.

```python
def off(
    event_type: Union[EventType, str],
    callback: Callable[[StateChangeEvent], None]
) -> None
```

**Parameters:**
- `event_type` (EventType | str): Type of event
- `callback` (Callable): Function to remove

**Returns:** None

**Example:**
```python
def my_handler(event):
    print(event)

agent = ContextAgent()
agent.on_change(EventType.BRANCH_CHANGED, my_handler)

# Later, remove handler
agent.off(EventType.BRANCH_CHANGED, my_handler)
```

---

#### `refresh()`

Force immediate state refresh.

```python
def refresh() -> AgentState
```

**Description:** Bypasses polling interval and immediately executes sensor to get fresh state.

**Returns:** `AgentState` - Newly refreshed state

**Example:**
```python
agent = ContextAgent()
agent.start()

# Force immediate refresh
fresh_state = agent.refresh()
```

**Notes:**
- Blocks until sensor execution completes
- Emits events if state changed
- Useful for on-demand updates

---

## AgentState

Normalized agent state container.

### Properties

```python
@dataclass
class AgentState:
    agent_type: str                          # Agent type identifier
    agent_version: str                       # Agent version
    model: str                               # AI model name
    workspace: WorkspaceInfo                 # Workspace information
    context_window: ContextWindowInfo        # Context usage information
    display: str                             # Display header string
    last_updated: str                        # ISO 8601 timestamp
    sensor_version: str                      # Sensor script version
```

### Methods

#### `to_dict()`

Convert state to dictionary.

```python
def to_dict() -> Dict[str, Any]
```

**Returns:** Dictionary representation of state

**Example:**
```python
state = agent.get_state()
state_dict = state.to_dict()
print(json.dumps(state_dict, indent=2))
```

---

#### `to_json()`

Convert state to JSON string.

```python
def to_json() -> str
```

**Returns:** JSON string representation

**Example:**
```python
state = agent.get_state()
json_output = state.to_json()
```

---

#### `from_sensor_output()`

Create state from sensor output.

```python
@classmethod
def from_sensor_output(
    cls,
    sensor_data: Dict[str, Any],
    display_string: str
) -> AgentState
```

**Parameters:**
- `sensor_data` (Dict): JSON data from sensor STDERR
- `display_string` (str): Display string from sensor STDOUT

**Returns:** `AgentState` instance

**Notes:**
- Used internally by agent core
- Normalizes sensor output into typed structure

---

#### `has_changed()`

Check if state has changed.

```python
def has_changed(self, other: AgentState) -> bool
```

**Parameters:**
- `other` (AgentState): Previous state to compare against

**Returns:** `bool` - True if state changed

**Example:**
```python
old_state = agent.get_state()
# ... time passes ...
new_state = agent.get_state()

if new_state.has_changed(old_state):
    print("State changed!")
```

---

#### `get_changes()`

Get detailed changes between states.

```python
def get_changes(self, other: AgentState) -> Dict[str, Any]
```

**Parameters:**
- `other` (AgentState): Previous state to compare against

**Returns:** Dictionary of changed fields with old/new values

**Example:**
```python
old_state = agent.get_state()
# ... state changes ...
new_state = agent.get_state()

changes = new_state.get_changes(old_state)
for field, values in changes.items():
    print(f"{field}: {values['old']} -> {values['new']}")
```

---

## WorkspaceInfo

Workspace information container.

```python
@dataclass
class WorkspaceInfo:
    path: str              # Absolute workspace path
    name: str              # Workspace directory name
    git: GitInfo           # Git repository information
```

### Methods

#### `to_dict()`

Convert to dictionary.

```python
def to_dict() -> Dict[str, Any]
```

---

## GitInfo

Git repository information.

```python
@dataclass
class GitInfo:
    is_repo: bool          # True if workspace is a git repository
    branch: str            # Current git branch name
```

### Methods

#### `to_dict()`

Convert to dictionary.

```python
def to_dict() -> Dict[str, Any]
```

---

## ContextWindowInfo

Context window usage information.

```python
@dataclass
class ContextWindowInfo:
    max_tokens: int        # Maximum context window size
    tokens_used: int       # Current tokens used
    usage_pct: int         # Usage percentage (0-100)
```

### Methods

#### `to_dict()`

Convert to dictionary.

```python
def to_dict() -> Dict[str, Any]
```

---

## EventType

Enumeration of event types.

```python
class EventType(Enum):
    MODEL_CHANGED = "model_changed"
    WORKSPACE_CHANGED = "workspace_changed"
    BRANCH_CHANGED = "branch_changed"
    CONTEXT_THRESHOLD = "context_threshold"
    STATE_UPDATED = "state_updated"
```

**Usage:**
```python
from context_agent import EventType

agent.on_change(EventType.BRANCH_CHANGED, my_handler)
```

---

## StateChangeEvent

State change event container.

```python
@dataclass
class StateChangeEvent:
    event_type: EventType       # Type of event
    timestamp: str              # ISO 8601 timestamp
    old_value: Any              # Previous value
    new_value: Any              # New value
    metadata: Dict[str, Any]    # Additional event metadata
```

### Methods

#### `to_dict()`

Convert event to dictionary.

```python
def to_dict() -> Dict[str, Any]
```

**Example:**
```python
def log_event(event):
    event_dict = event.to_dict()
    logger.info(json.dumps(event_dict))

agent.on_change(EventType.BRANCH_CHANGED, log_event)
```

---

## EventEmitter

Low-level event emitter (used internally by ContextAgent).

### Methods

#### `on()`

Register event handler.

```python
def on(
    event_type: EventType,
    callback: Callable[[StateChangeEvent], None]
) -> None
```

---

#### `off()`

Unregister event handler.

```python
def off(
    event_type: EventType,
    callback: Callable[[StateChangeEvent], None]
) -> None
```

---

#### `emit()`

Emit event to handlers.

```python
def emit(event: StateChangeEvent) -> None
```

---

#### `clear()`

Clear event handlers.

```python
def clear(event_type: Optional[EventType] = None) -> None
```

**Parameters:**
- `event_type` (Optional[EventType]): Specific event type to clear. If None, clears all.

---

## Type Hints

All classes and methods include complete type hints for IDE support:

```python
from context_agent import ContextAgent, AgentState, EventType
from typing import Optional, Dict, Any

def process_state(agent: ContextAgent) -> AgentState:
    return agent.get_state()

def handle_event(event: StateChangeEvent) -> None:
    print(f"Event: {event.event_type.value}")
```

---

## Error Handling

### Common Exceptions

**RuntimeError**
- Raised when calling methods on a stopped agent
- Raised when starting an already-running agent

**FileNotFoundError**
- Raised when sensor script cannot be found

**TimeoutError**
- Raised when sensor execution exceeds timeout

**Example:**
```python
from context_agent import ContextAgent
import logging

agent = ContextAgent()

try:
    agent.start()
except FileNotFoundError:
    logging.error("Sensor script not found")
except RuntimeError as e:
    logging.error(f"Agent error: {e}")
```

---

## Next Steps

- [Usage Examples](examples.md) - See complete working examples
- [Configuration Guide](configuration.md) - Learn about configuration options
- [Architecture](architecture.md) - Understand the system design
