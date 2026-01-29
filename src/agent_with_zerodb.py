"""
Context Agent with ZeroDB Integration

This module extends the base ContextAgent with optional ZeroDB persistence.
"""

import logging
import asyncio
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path

from .agent import ContextAgent, SensorError
from .state import AgentState
from .events import EventType, StateChangeEvent
from .config import AgentConfig
from .zerodb_integration import ZeroDBPersistence


logger = logging.getLogger(__name__)


class ContextAgentWithZeroDB(ContextAgent):
    """
    Context Agent with ZeroDB persistence support.

    Extends ContextAgent to automatically persist state and events to ZeroDB
    when enabled in configuration.
    """

    def __init__(
        self,
        sensor_path: Optional[str] = None,
        sensor_timeout: float = 5.0,
        context_threshold: int = 80,
        enable_events: bool = True,
        config: Optional[AgentConfig] = None
    ):
        """
        Initialize ContextAgent with ZeroDB support.

        Args:
            sensor_path: Path to sensor script
            sensor_timeout: Sensor execution timeout
            context_threshold: Context usage alert threshold
            enable_events: Enable event emission
            config: Optional AgentConfig (enables ZeroDB if configured)
        """
        # Initialize base agent
        super().__init__(
            sensor_path=sensor_path,
            sensor_timeout=sensor_timeout,
            context_threshold=context_threshold,
            enable_events=enable_events
        )

        # Store config
        self._config = config or AgentConfig()

        # ZeroDB integration
        self._zerodb_persistence: Optional[ZeroDBPersistence] = None
        self._zerodb_loop: Optional[asyncio.AbstractEventLoop] = None
        self._zerodb_thread: Optional[threading.Thread] = None
        self._zerodb_ready = threading.Event()

        # Initialize ZeroDB if enabled
        if self._config.enable_zerodb:
            self._init_zerodb()

        # Register event handlers for ZeroDB logging
        if self._zerodb_persistence and self._config.zerodb_enable_logging:
            self._register_zerodb_event_handlers()

    def _init_zerodb(self) -> None:
        """Initialize ZeroDB persistence in background thread."""
        try:
            # Create ZeroDB persistence instance
            self._zerodb_persistence = ZeroDBPersistence(
                api_key=self._config.zerodb_api_key,
                project_id=self._config.zerodb_project_id,
                enabled=self._config.enable_zerodb
            )

            # Start async event loop in background thread
            self._zerodb_thread = threading.Thread(
                target=self._run_zerodb_loop,
                daemon=True,
                name="ZeroDBWorker"
            )
            self._zerodb_thread.start()

            # Wait for initialization
            self._zerodb_ready.wait(timeout=5.0)

            if self._zerodb_persistence.is_available():
                logger.info("ZeroDB persistence initialized successfully")
            else:
                logger.warning(
                    f"ZeroDB persistence not available: "
                    f"{self._zerodb_persistence.get_status()}"
                )

        except Exception as e:
            logger.error(f"Failed to initialize ZeroDB: {e}")
            self._zerodb_persistence = None

    def _run_zerodb_loop(self) -> None:
        """Run async event loop for ZeroDB operations."""
        try:
            # Create new event loop for this thread
            self._zerodb_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._zerodb_loop)

            # Initialize ZeroDB client
            init_future = asyncio.ensure_future(
                self._zerodb_persistence.initialize()
            )
            self._zerodb_loop.run_until_complete(init_future)

            # Signal ready
            self._zerodb_ready.set()

            # Keep loop running for async tasks
            self._zerodb_loop.run_forever()

        except Exception as e:
            logger.error(f"ZeroDB event loop error: {e}")
            self._zerodb_ready.set()  # Signal even on error
        finally:
            if self._zerodb_loop:
                self._zerodb_loop.close()

    def _register_zerodb_event_handlers(self) -> None:
        """Register event handlers to log to ZeroDB."""
        if not self._event_emitter or not self._zerodb_persistence:
            return

        # Log all state change events to ZeroDB
        def log_to_zerodb(event: StateChangeEvent):
            if self._zerodb_loop and self._zerodb_persistence.is_available():
                # Schedule async task in ZeroDB event loop
                asyncio.run_coroutine_threadsafe(
                    self._zerodb_persistence.log_event(event),
                    self._zerodb_loop
                )

        # Register for all event types
        for event_type in EventType:
            self._event_emitter.on(event_type, log_to_zerodb)

    def get_state(
        self,
        input_data: Optional[Dict[str, Any]] = None,
        force_refresh: bool = True,
        persist: bool = True
    ) -> AgentState:
        """
        Get current agent state with optional ZeroDB persistence.

        Args:
            input_data: Optional input data for sensor
            force_refresh: Force sensor execution
            persist: Persist state to ZeroDB (default: True)

        Returns:
            Current AgentState
        """
        # Get state from base implementation
        state = super().get_state(input_data, force_refresh)

        # Persist to ZeroDB if enabled
        if persist and self._zerodb_persistence and self._zerodb_loop:
            if self._zerodb_persistence.is_available():
                # Schedule async persistence task
                asyncio.run_coroutine_threadsafe(
                    self._zerodb_persistence.store_state(state),
                    self._zerodb_loop
                )

        return state

    async def get_state_history(
        self,
        limit: int = 100,
        workspace_name: Optional[str] = None,
        git_branch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query historical state snapshots from ZeroDB.

        Args:
            limit: Maximum records to return
            workspace_name: Filter by workspace name
            git_branch: Filter by git branch

        Returns:
            List of historical state records
        """
        if not self._zerodb_persistence or not self._zerodb_persistence.is_available():
            logger.warning("ZeroDB persistence not available")
            return []

        return await self._zerodb_persistence.get_state_history(
            limit=limit,
            workspace_name=workspace_name,
            git_branch=git_branch
        )

    async def get_event_logs(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query event logs from ZeroDB.

        Args:
            event_type: Optional filter by event type
            limit: Maximum records to return

        Returns:
            List of event log records
        """
        if not self._zerodb_persistence or not self._zerodb_persistence.is_available():
            logger.warning("ZeroDB persistence not available")
            return []

        return await self._zerodb_persistence.get_event_logs(
            event_type=event_type,
            limit=limit
        )

    async def get_zerodb_statistics(self) -> Dict[str, Any]:
        """
        Get ZeroDB storage statistics.

        Returns:
            Statistics dictionary
        """
        if not self._zerodb_persistence:
            return {
                "enabled": False,
                "reason": "ZeroDB not configured"
            }

        return await self._zerodb_persistence.get_statistics()

    def get_zerodb_status(self) -> Dict[str, Any]:
        """
        Get current ZeroDB integration status.

        Returns:
            Status dictionary
        """
        if not self._zerodb_persistence:
            return {
                "enabled": False,
                "initialized": False,
                "reason": "ZeroDB not configured"
            }

        return self._zerodb_persistence.get_status()

    def shutdown(self) -> None:
        """Shutdown agent and cleanup ZeroDB resources."""
        logger.info("Shutting down ContextAgent with ZeroDB...")

        # Stop ZeroDB event loop
        if self._zerodb_loop and self._zerodb_loop.is_running():
            self._zerodb_loop.call_soon_threadsafe(self._zerodb_loop.stop)

        # Wait for ZeroDB thread
        if self._zerodb_thread and self._zerodb_thread.is_alive():
            self._zerodb_thread.join(timeout=5.0)

        # Close ZeroDB client
        if self._zerodb_persistence and self._zerodb_loop:
            asyncio.run_coroutine_threadsafe(
                self._zerodb_persistence.close(),
                self._zerodb_loop
            )

        logger.info("ContextAgent shutdown complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Convenience factory function
def create_context_agent(
    config_file: Optional[str] = None,
    **kwargs
) -> ContextAgentWithZeroDB:
    """
    Factory function to create ContextAgent with automatic config loading.

    Args:
        config_file: Optional path to config file
        **kwargs: Override specific config parameters

    Returns:
        ContextAgentWithZeroDB instance

    Example:
        >>> agent = create_context_agent(
        ...     config_file="config.json",
        ...     enable_zerodb=True,
        ...     zerodb_api_key="...",
        ...     zerodb_project_id="..."
        ... )
    """
    # Load configuration
    config = AgentConfig.load(config_file)

    # Override with kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return ContextAgentWithZeroDB(config=config)
