"""
ZeroDB Integration for Context Agent

Provides optional state persistence and event logging to AINative ZeroDB.
This module gracefully handles missing credentials and network failures.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import os

from .state import AgentState
from .events import StateChangeEvent

# Configure logging
logger = logging.getLogger(__name__)


class ZeroDBPersistence:
    """
    ZeroDB persistence layer for Context Agent

    Features:
    - Store agent state snapshots to NoSQL table
    - Log state change events for analytics
    - Query historical state data
    - Graceful degradation when credentials missing or service unavailable
    """

    # Table names for ZeroDB
    STATE_TABLE = "context_agent_state"
    EVENTS_TABLE = "context_agent_events"

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: Optional[str] = None,
        enabled: bool = True,
    ):
        """
        Initialize ZeroDB persistence.

        Args:
            api_key: AINative API key (reads from ZERODB_API_KEY env if not provided)
            project_id: ZeroDB project ID (reads from ZERODB_PROJECT_ID env if not provided)
            base_url: Optional custom API base URL
            enabled: Whether ZeroDB persistence is enabled
        """
        self.enabled = enabled
        self._client = None
        self._initialized = False
        self._initialization_error: Optional[str] = None

        # Get credentials from parameters or environment
        self.api_key = api_key or os.getenv("ZERODB_API_KEY")
        self.project_id = project_id or os.getenv("ZERODB_PROJECT_ID")
        self.base_url = base_url or os.getenv("ZERODB_BASE_URL", "https://api.ainative.studio")

        # Validate credentials
        if self.enabled:
            if not self.api_key:
                logger.warning("ZeroDB enabled but ZERODB_API_KEY not provided - persistence disabled")
                self.enabled = False
                self._initialization_error = "Missing API key"
            elif not self.project_id:
                logger.warning("ZeroDB enabled but ZERODB_PROJECT_ID not provided - persistence disabled")
                self.enabled = False
                self._initialization_error = "Missing project ID"

    async def initialize(self) -> bool:
        """
        Initialize ZeroDB client and ensure tables exist.

        Returns:
            True if initialization successful, False otherwise
        """
        if not self.enabled:
            logger.info("ZeroDB persistence is disabled")
            return False

        if self._initialized:
            return True

        try:
            # Import AINative SDK (only if enabled)
            from ainative import AINativeClient

            # Initialize client
            self._client = AINativeClient(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            # Ensure tables exist
            await self._ensure_tables()

            self._initialized = True
            logger.info(f"ZeroDB persistence initialized for project: {self.project_id}")
            return True

        except ImportError as e:
            logger.error(f"AINative SDK not installed: {e}")
            self._initialization_error = "SDK not installed"
            self.enabled = False
            return False

        except Exception as e:
            logger.error(f"Failed to initialize ZeroDB client: {e}")
            self._initialization_error = str(e)
            self.enabled = False
            return False

    async def _ensure_tables(self) -> None:
        """Ensure required tables exist in ZeroDB."""
        try:
            # Check if state table exists
            state_exists = self._client.zerodb.tables.table_exists(
                self.project_id,
                self.STATE_TABLE
            )

            if not state_exists:
                logger.info(f"Creating {self.STATE_TABLE} table...")
                self._client.zerodb.tables.create_table(
                    project_id=self.project_id,
                    table_name=self.STATE_TABLE,
                    schema={
                        "fields": {
                            "id": "string",
                            "timestamp": "string",
                            "agent_version": "string",
                            "model": "string",
                            "workspace_name": "string",
                            "workspace_path": "string",
                            "git_branch": "string",
                            "git_is_repo": "boolean",
                            "context_usage_pct": "number",
                            "context_tokens_used": "number",
                            "context_max_tokens": "number",
                            "full_state": "object",
                            "display": "string",
                            "created_at": "string"
                        },
                        "indexes": ["timestamp", "workspace_name", "git_branch"]
                    },
                    description="Context Agent state snapshots"
                )
                logger.info(f"Created {self.STATE_TABLE} table")

            # Check if events table exists
            events_exists = self._client.zerodb.tables.table_exists(
                self.project_id,
                self.EVENTS_TABLE
            )

            if not events_exists:
                logger.info(f"Creating {self.EVENTS_TABLE} table...")
                self._client.zerodb.tables.create_table(
                    project_id=self.project_id,
                    table_name=self.EVENTS_TABLE,
                    schema={
                        "fields": {
                            "id": "string",
                            "timestamp": "string",
                            "event_type": "string",
                            "old_value": "string",
                            "new_value": "string",
                            "metadata": "object",
                            "created_at": "string"
                        },
                        "indexes": ["timestamp", "event_type"]
                    },
                    description="Context Agent state change events"
                )
                logger.info(f"Created {self.EVENTS_TABLE} table")

        except Exception as e:
            logger.error(f"Failed to ensure tables exist: {e}")
            raise

    async def store_state(self, state: AgentState) -> Optional[str]:
        """
        Store agent state snapshot to ZeroDB.

        Args:
            state: AgentState to persist

        Returns:
            Record ID if successful, None otherwise
        """
        if not self.enabled or not self._initialized:
            return None

        try:
            record_id = str(uuid.uuid4())

            # Prepare state record
            state_record = {
                "id": record_id,
                "timestamp": state.last_updated,
                "agent_version": state.agent_version,
                "model": state.model,
                "workspace_name": state.workspace.name,
                "workspace_path": state.workspace.path,
                "git_branch": state.workspace.git.branch,
                "git_is_repo": state.workspace.git.is_repo,
                "context_usage_pct": state.context_window.usage_pct,
                "context_tokens_used": state.context_window.tokens_used,
                "context_max_tokens": state.context_window.max_tokens,
                "full_state": state.to_dict(),
                "display": state.display,
                "created_at": datetime.utcnow().isoformat()
            }

            # Insert into ZeroDB
            result = self._client.zerodb.tables.insert_rows(
                project_id=self.project_id,
                table_name=self.STATE_TABLE,
                rows=[state_record]
            )

            logger.debug(f"Stored state snapshot: {record_id}")
            return record_id

        except Exception as e:
            logger.error(f"Failed to store state to ZeroDB: {e}")
            return None

    async def log_event(self, event: StateChangeEvent) -> Optional[str]:
        """
        Log state change event to ZeroDB.

        Args:
            event: StateChangeEvent to log

        Returns:
            Event ID if successful, None otherwise
        """
        if not self.enabled or not self._initialized:
            return None

        try:
            event_id = str(uuid.uuid4())

            # Prepare event record
            event_record = {
                "id": event_id,
                "timestamp": event.timestamp,
                "event_type": event.event_type.value,
                "old_value": str(event.old_value) if event.old_value is not None else "",
                "new_value": str(event.new_value) if event.new_value is not None else "",
                "metadata": event.metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }

            # Insert into ZeroDB
            result = self._client.zerodb.tables.insert_rows(
                project_id=self.project_id,
                table_name=self.EVENTS_TABLE,
                rows=[event_record]
            )

            logger.debug(f"Logged event: {event.event_type.value}")
            return event_id

        except Exception as e:
            logger.error(f"Failed to log event to ZeroDB: {e}")
            return None

    async def get_state_history(
        self,
        limit: int = 100,
        workspace_name: Optional[str] = None,
        git_branch: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query historical state snapshots.

        Args:
            limit: Maximum number of records to return
            workspace_name: Optional filter by workspace name
            git_branch: Optional filter by git branch

        Returns:
            List of state records, newest first
        """
        if not self.enabled or not self._initialized:
            return []

        try:
            # Build filter
            filter_query = {}
            if workspace_name:
                filter_query["workspace_name"] = workspace_name
            if git_branch:
                filter_query["git_branch"] = git_branch

            # Query records
            result = self._client.zerodb.tables.query_rows(
                project_id=self.project_id,
                table_name=self.STATE_TABLE,
                filter=filter_query if filter_query else None,
                sort={"timestamp": -1},  # Newest first
                limit=limit
            )

            return result.get("rows", [])

        except Exception as e:
            logger.error(f"Failed to query state history: {e}")
            return []

    async def get_event_logs(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query event logs with optional filtering.

        Args:
            event_type: Optional filter by event type
            limit: Maximum number of records to return

        Returns:
            List of event records, newest first
        """
        if not self.enabled or not self._initialized:
            return []

        try:
            # Build filter
            filter_query = {}
            if event_type:
                filter_query["event_type"] = event_type

            # Query records
            result = self._client.zerodb.tables.query_rows(
                project_id=self.project_id,
                table_name=self.EVENTS_TABLE,
                filter=filter_query if filter_query else None,
                sort={"timestamp": -1},  # Newest first
                limit=limit
            )

            return result.get("rows", [])

        except Exception as e:
            logger.error(f"Failed to query event logs: {e}")
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored data.

        Returns:
            Dictionary with statistics
        """
        if not self.enabled or not self._initialized:
            return {
                "enabled": False,
                "initialization_error": self._initialization_error
            }

        try:
            state_count = self._client.zerodb.tables.count_rows(
                self.project_id,
                self.STATE_TABLE
            )

            event_count = self._client.zerodb.tables.count_rows(
                self.project_id,
                self.EVENTS_TABLE
            )

            return {
                "enabled": True,
                "initialized": self._initialized,
                "project_id": self.project_id,
                "state_snapshots": state_count,
                "event_logs": event_count,
                "tables": {
                    "state": self.STATE_TABLE,
                    "events": self.EVENTS_TABLE
                }
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "enabled": True,
                "initialized": self._initialized,
                "error": str(e)
            }

    async def close(self) -> None:
        """Close ZeroDB client connection."""
        if self._client:
            try:
                self._client.close()
                logger.debug("ZeroDB client closed")
            except Exception as e:
                logger.error(f"Error closing ZeroDB client: {e}")

    def is_available(self) -> bool:
        """
        Check if ZeroDB persistence is available.

        Returns:
            True if enabled and initialized
        """
        return self.enabled and self._initialized

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of ZeroDB integration.

        Returns:
            Status dictionary
        """
        return {
            "enabled": self.enabled,
            "initialized": self._initialized,
            "initialization_error": self._initialization_error,
            "project_id": self.project_id if self.enabled else None,
            "api_configured": bool(self.api_key),
        }
