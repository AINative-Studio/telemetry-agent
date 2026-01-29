"""
Context Agent - Interpretation Layer

This module implements the main ContextAgent class that orchestrates
sensor execution, output parsing, and state management.
"""

import subprocess
import json
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from .state import AgentState
from .events import EventEmitter, EventType, StateChangeEvent


# Configure logging
logger = logging.getLogger(__name__)


class SensorError(Exception):
    """Raised when sensor execution fails"""
    pass


class ContextAgent:
    """
    Main Context Agent Class

    Orchestrates sensor execution, output parsing, and state management.
    Provides interpretation layer between raw sensor output and normalized state.
    """

    def __init__(
        self,
        sensor_path: Optional[str] = None,
        sensor_timeout: float = 5.0,
        context_threshold: int = 80,
        enable_events: bool = True
    ):
        """
        Initialize ContextAgent

        Args:
            sensor_path: Path to sensor script (defaults to scripts/context_sensor.sh)
            sensor_timeout: Timeout for sensor execution in seconds (default: 5.0)
            context_threshold: Context window usage percentage threshold for alerts (default: 80)
            enable_events: Whether to enable event emission (default: True)
        """
        # Resolve sensor script path
        if sensor_path is None:
            # Default to scripts/context_sensor.sh relative to project root
            project_root = Path(__file__).parent.parent
            self._sensor_path = project_root / "scripts" / "context_sensor.sh"
        else:
            self._sensor_path = Path(sensor_path)

        # Validate sensor script exists and is executable
        if not self._sensor_path.exists():
            raise FileNotFoundError(f"Sensor script not found: {self._sensor_path}")

        if not self._sensor_path.is_file():
            raise ValueError(f"Sensor path is not a file: {self._sensor_path}")

        # Configuration
        self._sensor_timeout = sensor_timeout
        self._context_threshold = context_threshold
        self._enable_events = enable_events

        # State management
        self._current_state: Optional[AgentState] = None
        self._previous_state: Optional[AgentState] = None
        self._state_lock = threading.Lock()

        # Event system
        self._event_emitter = EventEmitter() if enable_events else None

        # Polling mechanism
        self._polling = False
        self._poll_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Threshold tracking (to emit only once per crossing)
        self._threshold_exceeded = False

        logger.info(
            f"ContextAgent initialized: sensor={self._sensor_path}, "
            f"timeout={sensor_timeout}s, threshold={context_threshold}%"
        )

    def _execute_sensor(self, input_data: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        Execute sensor script via subprocess

        Args:
            input_data: Optional JSON data to pass to sensor via STDIN

        Returns:
            Tuple of (stdout, stderr) as strings

        Raises:
            SensorError: If sensor execution fails or times out
        """
        try:
            # Prepare input JSON
            stdin_input = json.dumps(input_data or {})

            logger.debug(f"Executing sensor: {self._sensor_path}")
            logger.debug(f"Sensor input: {stdin_input}")

            # Execute sensor script
            process = subprocess.Popen(
                [str(self._sensor_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self._sensor_path.parent)
            )

            # Communicate with timeout
            try:
                stdout, stderr = process.communicate(
                    input=stdin_input,
                    timeout=self._sensor_timeout
                )
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise SensorError(
                    f"Sensor execution timed out after {self._sensor_timeout}s"
                )

            # Check return code
            if process.returncode != 0:
                logger.warning(
                    f"Sensor exited with non-zero code: {process.returncode}"
                )
                logger.warning(f"Sensor stderr: {stderr}")
                raise SensorError(
                    f"Sensor failed with exit code {process.returncode}: {stderr}"
                )

            logger.debug(f"Sensor stdout: {stdout}")
            logger.debug(f"Sensor stderr: {stderr}")

            return stdout.strip(), stderr.strip()

        except FileNotFoundError as e:
            raise SensorError(f"Sensor script not found: {e}")
        except PermissionError as e:
            raise SensorError(f"Permission denied executing sensor: {e}")
        except Exception as e:
            if isinstance(e, SensorError):
                raise
            raise SensorError(f"Unexpected error executing sensor: {e}")

    def _parse_sensor_output(
        self,
        stdout: str,
        stderr: str
    ) -> AgentState:
        """
        Parse sensor output and convert to AgentState

        Args:
            stdout: Display string from sensor (STDOUT)
            stderr: JSON data from sensor (STDERR)

        Returns:
            Normalized AgentState

        Raises:
            SensorError: If parsing fails
        """
        try:
            # Parse JSON data from STDERR
            sensor_data = json.loads(stderr) if stderr else {}

            # Display string from STDOUT
            display_string = stdout if stdout else ""

            # Convert to AgentState using the factory method
            state = AgentState.from_sensor_output(sensor_data, display_string)

            logger.debug(f"Parsed sensor output: {state.to_dict()}")

            return state

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse sensor JSON output: {e}")
            logger.error(f"Raw stderr: {stderr}")

            # Return partial state with error indication
            # This satisfies "missing fields result in partial state, not failure"
            return AgentState(
                display=stdout if stdout else "Error parsing sensor output",
                last_updated=datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.error(f"Unexpected error parsing sensor output: {e}")

            # Return minimal valid state
            return AgentState(
                display="Sensor parsing error",
                last_updated=datetime.utcnow().isoformat()
            )

    def _emit_state_change_events(
        self,
        new_state: AgentState,
        old_state: Optional[AgentState]
    ) -> None:
        """
        Emit state change events based on state differences

        Args:
            new_state: New agent state
            old_state: Previous agent state (may be None)
        """
        if not self._enable_events or not self._event_emitter:
            return

        if not old_state:
            # Initial state - emit STATE_UPDATED only
            event = StateChangeEvent(
                event_type=EventType.STATE_UPDATED,
                timestamp=datetime.utcnow().isoformat(),
                old_value=None,
                new_value=new_state.to_dict()
            )
            self._event_emitter.emit(event)
            return

        # Check for specific changes
        changes = new_state.get_changes(old_state)

        # Model changed
        if "model" in changes:
            event = StateChangeEvent(
                event_type=EventType.MODEL_CHANGED,
                timestamp=datetime.utcnow().isoformat(),
                old_value=changes["model"]["old"],
                new_value=changes["model"]["new"]
            )
            self._event_emitter.emit(event)

        # Workspace changed
        if "workspace" in changes:
            event = StateChangeEvent(
                event_type=EventType.WORKSPACE_CHANGED,
                timestamp=datetime.utcnow().isoformat(),
                old_value=changes["workspace"]["old"],
                new_value=changes["workspace"]["new"]
            )
            self._event_emitter.emit(event)

        # Branch changed
        if "branch" in changes:
            event = StateChangeEvent(
                event_type=EventType.BRANCH_CHANGED,
                timestamp=datetime.utcnow().isoformat(),
                old_value=changes["branch"]["old"],
                new_value=changes["branch"]["new"]
            )
            self._event_emitter.emit(event)

        # Context threshold - emit only once when crossing threshold
        if "context_usage" in changes:
            old_pct = changes["context_usage"]["old"]
            new_pct = changes["context_usage"]["new"]

            # Check if threshold crossed from below to above
            threshold_crossed = (
                old_pct < self._context_threshold <= new_pct
            )

            # Emit threshold event only once when crossing threshold
            if threshold_crossed and not self._threshold_exceeded:
                self._threshold_exceeded = True
                event = StateChangeEvent(
                    event_type=EventType.CONTEXT_THRESHOLD,
                    timestamp=datetime.utcnow().isoformat(),
                    old_value=old_pct,
                    new_value=new_pct,
                    metadata={
                        "threshold": self._context_threshold,
                        "exceeded": True
                    }
                )
                self._event_emitter.emit(event)

            # Reset flag if usage drops back below threshold
            elif new_pct < self._context_threshold:
                self._threshold_exceeded = False

        # General state update
        if changes:
            event = StateChangeEvent(
                event_type=EventType.STATE_UPDATED,
                timestamp=datetime.utcnow().isoformat(),
                old_value=old_state.to_dict(),
                new_value=new_state.to_dict(),
                metadata={"changes": changes}
            )
            self._event_emitter.emit(event)

    def get_state(
        self,
        input_data: Optional[Dict[str, Any]] = None,
        force_refresh: bool = True
    ) -> AgentState:
        """
        Get current agent state

        Args:
            input_data: Optional input data to pass to sensor
            force_refresh: Whether to force sensor execution (default: True)

        Returns:
            Current AgentState

        Raises:
            SensorError: If sensor execution fails and no previous state exists
        """
        with self._state_lock:
            if not force_refresh and self._current_state:
                logger.debug("Returning cached state (force_refresh=False)")
                return self._current_state

        try:
            # Execute sensor (outside lock to avoid blocking polling)
            stdout, stderr = self._execute_sensor(input_data)

            # Parse output
            new_state = self._parse_sensor_output(stdout, stderr)

            # Update state tracking with lock
            with self._state_lock:
                self._previous_state = self._current_state
                self._current_state = new_state

                # Emit events if state changed
                if new_state.has_changed(self._previous_state):
                    self._emit_state_change_events(new_state, self._previous_state)

            return new_state

        except SensorError as e:
            logger.error(f"Sensor execution failed: {e}")

            # If we have previous state, return it as fallback
            with self._state_lock:
                if self._current_state:
                    logger.warning("Returning cached state due to sensor failure")
                    return self._current_state

            # No previous state - raise error
            raise

    def get_display_string(
        self,
        input_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get display string from sensor

        Args:
            input_data: Optional input data to pass to sensor

        Returns:
            Display string from sensor STDOUT
        """
        state = self.get_state(input_data)
        return state.display

    @property
    def current_state(self) -> Optional[AgentState]:
        """Get current cached state without executing sensor"""
        return self._current_state

    @property
    def previous_state(self) -> Optional[AgentState]:
        """Get previous cached state"""
        return self._previous_state

    @property
    def event_emitter(self) -> Optional[EventEmitter]:
        """Get event emitter instance"""
        return self._event_emitter

    def on(self, event_type: EventType, callback) -> None:
        """
        Register event handler

        Args:
            event_type: Type of event to listen for
            callback: Callback function that receives StateChangeEvent
        """
        if self._event_emitter:
            self._event_emitter.on(event_type, callback)
        else:
            logger.warning("Event emitter not enabled - cannot register handler")

    def off(self, event_type: EventType, callback) -> None:
        """
        Unregister event handler

        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        if self._event_emitter:
            self._event_emitter.off(event_type, callback)

    def start(self, polling_interval: float = 5.0) -> None:
        """
        Start background polling

        Starts a background thread that polls the sensor at regular intervals
        and emits events when state changes are detected.

        Executes the sensor once immediately to initialize state before
        starting the background polling thread.

        Args:
            polling_interval: Seconds between sensor executions (default: 5.0)

        Raises:
            RuntimeError: If agent is already running
            SensorError: If initial sensor execution fails
        """
        if self._polling:
            raise RuntimeError("Agent is already running")

        logger.info(f"Starting agent with polling interval: {polling_interval}s")

        # Execute sensor once to initialize state
        try:
            self.get_state(force_refresh=True)
            logger.debug("Initial state initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize state: {e}")
            raise

        self._polling = True
        self._stop_event.clear()

        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            args=(polling_interval,),
            daemon=False,
            name="ContextAgent-Poller"
        )
        self._poll_thread.start()

        logger.info("Agent started successfully")

    def stop(self) -> None:
        """
        Stop polling gracefully

        Signals the polling thread to stop and waits for current
        sensor execution to complete.
        """
        if not self._polling:
            logger.debug("Agent is not running, nothing to stop")
            return

        logger.info("Stopping agent...")

        self._polling = False
        self._stop_event.set()

        # Wait for poll thread to finish
        if self._poll_thread and self._poll_thread.is_alive():
            # Wait for sensor timeout + buffer
            timeout = self._sensor_timeout + 2
            self._poll_thread.join(timeout=timeout)

            if self._poll_thread.is_alive():
                logger.warning(
                    f"Poll thread did not stop within {timeout}s timeout"
                )
            else:
                logger.info("Agent stopped successfully")

    def _poll_loop(self, interval: float) -> None:
        """
        Internal polling loop

        Runs in background thread and executes sensor at regular intervals.

        Args:
            interval: Polling interval in seconds
        """
        logger.debug(f"Poll loop started with interval: {interval}s")

        while self._polling and not self._stop_event.is_set():
            try:
                # Execute sensor and update state
                # This will automatically emit events via get_state
                self.get_state(force_refresh=True)

            except SensorError as e:
                logger.error(f"Sensor execution failed in poll loop: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in poll loop: {e}")

            # Wait for next poll (or until stop signal)
            self._stop_event.wait(timeout=interval)

        logger.debug("Poll loop exited")

    def is_running(self) -> bool:
        """
        Check if agent is currently polling

        Returns:
            True if polling thread is active
        """
        return self._polling and (
            self._poll_thread is not None and self._poll_thread.is_alive()
        )

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        self.stop()
        return False

    # ========================================================================
    # Public API Methods (Issue #4)
    # ========================================================================

    def get_state_dict(self) -> Dict[str, Any]:
        """
        Get the current agent state as a normalized dictionary.

        Returns a complete snapshot of the current runtime context including
        model information, workspace details, git status, and context window usage.

        This is the primary API method for accessing agent state. It returns
        cached state without executing the sensor.

        Returns:
            Dictionary containing the full normalized state:
            {
                "agent_type": "context",
                "agent_version": "1.0.0",
                "model": "Claude",
                "workspace": {
                    "path": "/path/to/workspace",
                    "name": "workspace-name",
                    "git": {
                        "is_repo": true,
                        "branch": "main"
                    }
                },
                "context_window": {
                    "max_tokens": 200000,
                    "tokens_used": 26000,
                    "usage_pct": 13
                },
                "display": "[Claude] 📁 workspace-name 🌿 main | 📊 13%",
                "last_updated": "2025-01-28T10:30:45.123456",
                "sensor_version": "1.0.0"
            }

        Raises:
            RuntimeError: If state has not been initialized yet (call start() first)

        Examples:
            >>> from context_agent import ContextAgent
            >>> agent = ContextAgent()
            >>> agent.start()
            >>> state = agent.get_state_dict()
            >>> print(state['workspace']['name'])
            'ainative'
            >>> print(state['context_window']['usage_pct'])
            13
            >>> if state['workspace']['git']['is_repo']:
            ...     print(f"Current branch: {state['workspace']['git']['branch']}")
            'Current branch: main'

            Accessing nested data:
            >>> state = agent.get_state_dict()
            >>> workspace = state['workspace']
            >>> if workspace['git']['is_repo']:
            ...     print(f"Working on branch: {workspace['git']['branch']}")
            ...     print(f"In directory: {workspace['name']}")

        Thread Safety:
            This method is thread-safe and can be called from multiple threads.

        Notes:
            - Returns cached state (no sensor execution)
            - Call start() to initialize and begin monitoring
            - State is updated automatically during polling
        """
        with self._state_lock:
            if self._current_state is None:
                raise RuntimeError(
                    "Agent state not initialized. Call start() first to initialize the agent."
                )
            return self._current_state.to_dict()

    def get_display_header(self) -> str:
        """
        Get the human-readable status string for display in terminals or UIs.

        Returns the exact output from the sensor's display string, formatted
        as a single-line status indicator.

        Returns:
            Formatted status string, e.g.:
            - "[Claude] 📁 ainative 🌿 main | 📊 13%"
            - "[Claude] 📁 workspace 🌿 feature-branch"
            - "[Claude] 📁 project"

        Raises:
            RuntimeError: If state has not been initialized yet (call start() first)

        Examples:
            >>> from context_agent import ContextAgent
            >>> agent = ContextAgent()
            >>> agent.start()
            >>> header = agent.get_display_header()
            >>> print(header)
            '[Claude] 📁 ainative 🌿 main | 📊 13%'

            Terminal integration:
            >>> import sys
            >>> while True:
            ...     sys.stdout.write(f"\\r{agent.get_display_header()}")
            ...     sys.stdout.flush()
            ...     time.sleep(1)

            Status bar integration:
            >>> def update_status_bar():
            ...     status = agent.get_display_header()
            ...     set_window_title(status)
            ...     update_ui_element("status-bar", status)

            Rich terminal output:
            >>> from rich.console import Console
            >>> console = Console()
            >>> console.print(f"[bold]{agent.get_display_header()}[/bold]")

        Thread Safety:
            This method is thread-safe and can be called from multiple threads.

        Notes:
            The display string is cached from the last sensor execution. It
            reflects the state at the time of the last update.
        """
        with self._state_lock:
            if self._current_state is None:
                raise RuntimeError(
                    "Agent state not initialized. Call start() first to initialize the agent."
                )
            return self._current_state.display

    def on_change(self, event_type: EventType, callback: Callable[[StateChangeEvent], None]) -> None:
        """
        Register an event handler for state change notifications.

        Allows consumers to react to specific types of state changes such as
        model changes, branch changes, workspace changes, or context threshold
        violations.

        Args:
            event_type: Type of event to listen for (EventType enum)
            callback: Callback function that receives a StateChangeEvent object

        Event Types:
            - EventType.MODEL_CHANGED: AI model changed
            - EventType.BRANCH_CHANGED: Git branch changed
            - EventType.WORKSPACE_CHANGED: Workspace path/name changed
            - EventType.CONTEXT_THRESHOLD: Context usage exceeded threshold
            - EventType.STATE_UPDATED: Any state change occurred

        StateChangeEvent Structure:
            {
                "event_type": "branch_changed",
                "timestamp": "2025-01-28T10:30:45.123456",
                "old_value": "main",
                "new_value": "feature-branch",
                "metadata": {}
            }

        Examples:
            >>> from context_agent import ContextAgent, EventType
            >>> agent = ContextAgent()
            >>> agent.start()

            Basic event handler:
            >>> def on_branch_change(event):
            ...     print(f"Branch changed: {event.old_value} -> {event.new_value}")
            >>> agent.on_change(EventType.BRANCH_CHANGED, on_branch_change)

            Multiple handlers:
            >>> agent.on_change(EventType.MODEL_CHANGED, lambda e: log_model_change(e))
            >>> agent.on_change(EventType.WORKSPACE_CHANGED, lambda e: update_ui(e))
            >>> agent.on_change(EventType.CONTEXT_THRESHOLD, lambda e: send_alert(e))

            Accessing event details:
            >>> def handle_context_threshold(event):
            ...     usage = event.new_value
            ...     if usage > 90:
            ...         print(f"CRITICAL: Context usage at {usage}%")
            ...     elif usage > 80:
            ...         print(f"WARNING: Context usage at {usage}%")
            >>> agent.on_change(EventType.CONTEXT_THRESHOLD, handle_context_threshold)

            Using event metadata:
            >>> def on_state_update(event):
            ...     if event.metadata and 'changes' in event.metadata:
            ...         for field, change in event.metadata['changes'].items():
            ...             print(f"{field}: {change['old']} -> {change['new']}")
            >>> agent.on_change(EventType.STATE_UPDATED, on_state_update)

            Real-world example - ZeroDB logging:
            >>> from zerodb import ZeroDBClient
            >>> db = ZeroDBClient()
            >>> def log_branch_change(event):
            ...     db.insert("branch_changes", {
            ...         "timestamp": event.timestamp,
            ...         "old_branch": event.old_value,
            ...         "new_branch": event.new_value
            ...     })
            >>> agent.on_change(EventType.BRANCH_CHANGED, log_branch_change)

        Thread Safety:
            This method is thread-safe. Callbacks are executed synchronously
            in the thread that triggers the state change.

        Error Handling:
            Exceptions in callbacks are caught and logged but do not stop
            other handlers from executing or crash the agent.

        Notes:
            - Callbacks must be thread-safe if the agent runs in polling mode
            - Callbacks should execute quickly to avoid blocking state updates
            - Use off() to unregister handlers when no longer needed
        """
        self.on(event_type, callback)
