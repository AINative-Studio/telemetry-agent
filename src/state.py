"""
Normalized Agent State Management

This module defines the canonical state structure for the Context Agent.
All state is derived from sensor output.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class GitInfo:
    """Git repository information"""
    is_repo: bool = False
    branch: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkspaceInfo:
    """Workspace information"""
    path: str = ""
    name: str = ""
    git: GitInfo = field(default_factory=GitInfo)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "git": self.git.to_dict()
        }


@dataclass
class ContextWindowInfo:
    """Context window usage information"""
    max_tokens: int = 200000
    tokens_used: int = 0
    usage_pct: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentState:
    """
    Normalized Agent State

    This is the single source of truth derived exclusively from sensor output.
    No inference beyond emitted values is allowed.
    """
    agent_type: str = "context"
    agent_version: str = "1.0.0"
    model: str = "Claude"
    workspace: WorkspaceInfo = field(default_factory=WorkspaceInfo)
    context_window: ContextWindowInfo = field(default_factory=ContextWindowInfo)
    display: str = ""
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    sensor_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "agent_type": self.agent_type,
            "agent_version": self.agent_version,
            "model": self.model,
            "workspace": self.workspace.to_dict(),
            "context_window": self.context_window.to_dict(),
            "display": self.display,
            "last_updated": self.last_updated,
            "sensor_version": self.sensor_version
        }

    def to_json(self) -> str:
        """Convert state to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_sensor_output(cls, sensor_data: Dict[str, Any], display_string: str) -> "AgentState":
        """
        Create AgentState from sensor output

        Args:
            sensor_data: JSON data from sensor (via STDERR)
            display_string: Display string from sensor (via STDOUT)

        Returns:
            AgentState instance
        """
        workspace_data = sensor_data.get("workspace", {})
        git_data = workspace_data.get("git", {})
        context_data = sensor_data.get("context_window", {})

        return cls(
            model=sensor_data.get("model", "Claude"),
            workspace=WorkspaceInfo(
                path=workspace_data.get("path", ""),
                name=workspace_data.get("name", ""),
                git=GitInfo(
                    is_repo=git_data.get("is_repo", False),
                    branch=git_data.get("branch", "")
                )
            ),
            context_window=ContextWindowInfo(
                max_tokens=context_data.get("max_tokens", 200000),
                tokens_used=context_data.get("tokens_used", 0),
                usage_pct=context_data.get("usage_pct", 0)
            ),
            display=display_string.strip(),
            last_updated=datetime.utcnow().isoformat(),
            sensor_version=sensor_data.get("version", "1.0.0")
        )

    def has_changed(self, other: "AgentState") -> bool:
        """
        Check if state has changed compared to another state

        Args:
            other: Previous AgentState to compare against

        Returns:
            True if state has changed
        """
        if not other:
            return True

        # Compare key fields (excluding timestamps)
        return (
            self.model != other.model or
            self.workspace.name != other.workspace.name or
            self.workspace.git.branch != other.workspace.git.branch or
            self.context_window.usage_pct != other.context_window.usage_pct
        )

    def get_changes(self, other: "AgentState") -> Dict[str, Any]:
        """
        Get specific changes between states

        Args:
            other: Previous AgentState to compare against

        Returns:
            Dictionary of changed fields
        """
        if not other:
            return {"initial": True}

        changes = {}

        if self.model != other.model:
            changes["model"] = {"old": other.model, "new": self.model}

        if self.workspace.name != other.workspace.name:
            changes["workspace"] = {"old": other.workspace.name, "new": self.workspace.name}

        if self.workspace.git.branch != other.workspace.git.branch:
            changes["branch"] = {"old": other.workspace.git.branch, "new": self.workspace.git.branch}

        if self.context_window.usage_pct != other.context_window.usage_pct:
            changes["context_usage"] = {
                "old": other.context_window.usage_pct,
                "new": self.context_window.usage_pct
            }

        return changes
