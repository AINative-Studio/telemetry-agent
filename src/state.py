"""
Normalized Agent State Management

This module defines the canonical state structure for the Context Agent.
All state is derived from sensor output.

Example usage:
    >>> from state import AgentState
    >>> sensor_data = {
    ...     "model": "Claude",
    ...     "workspace": {"name": "my-project", "git": {"branch": "main"}}
    ... }
    >>> state = AgentState.from_sensor_output(sensor_data, "Display")
    >>> print(state.workspace.name)
    'my-project'
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime
import json


@dataclass(frozen=True)
class GitInfo:
    """
    Git repository information

    Attributes:
        is_repo: Whether the workspace is a git repository
        branch: Current branch name (empty if not a repo)

    Example:
        >>> git = GitInfo(is_repo=True, branch="main")
        >>> git.to_dict()
        {'is_repo': True, 'branch': 'main'}
    """
    is_repo: bool = False
    branch: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass(frozen=True)
class WorkspaceInfo:
    """
    Workspace information

    Attributes:
        path: Absolute path to workspace directory
        name: Workspace name (usually directory name)
        git: Git repository information

    Example:
        >>> git = GitInfo(is_repo=True, branch="develop")
        >>> workspace = WorkspaceInfo(path="/home/user/project", name="project", git=git)
        >>> workspace.to_dict()
        {'path': '/home/user/project', 'name': 'project', 'git': {'is_repo': True, 'branch': 'develop'}}
    """
    path: str = ""
    name: str = ""
    git: GitInfo = field(default_factory=GitInfo)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "path": self.path,
            "name": self.name,
            "git": self.git.to_dict()
        }


@dataclass(frozen=True)
class ContextWindowInfo:
    """
    Context window usage information

    Attributes:
        max_tokens: Maximum tokens available in context window
        tokens_used: Number of tokens currently used
        usage_pct: Percentage of context window used (0-100)

    Example:
        >>> context = ContextWindowInfo(max_tokens=200000, tokens_used=50000, usage_pct=25)
        >>> context.to_dict()
        {'max_tokens': 200000, 'tokens_used': 50000, 'usage_pct': 25}
    """
    max_tokens: int = 200000
    tokens_used: int = 0
    usage_pct: int = 0

    def __post_init__(self):
        """Validate context window values"""
        # Note: frozen=True requires using object.__setattr__ for validation
        if self.max_tokens < 0:
            object.__setattr__(self, 'max_tokens', 0)
        if self.tokens_used < 0:
            object.__setattr__(self, 'tokens_used', 0)
        if self.usage_pct < 0:
            object.__setattr__(self, 'usage_pct', 0)
        elif self.usage_pct > 100:
            object.__setattr__(self, 'usage_pct', 100)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass(frozen=True)
class AgentState:
    """
    Normalized Agent State

    This is the single source of truth derived exclusively from sensor output.
    No inference beyond emitted values is allowed.

    Attributes:
        agent_type: Type of agent (always "context")
        agent_version: Version of the agent software
        model: AI model being used (e.g., "Claude", "GPT-4")
        workspace: Current workspace information
        context_window: Context window usage statistics
        display: Display string from sensor (STDOUT)
        last_updated: ISO timestamp of last state update
        sensor_version: Version of the sensor script

    Example:
        >>> sensor_data = {"model": "Claude", "workspace": {"name": "project"}}
        >>> state = AgentState.from_sensor_output(sensor_data, "Display")
        >>> state.model
        'Claude'

    Note:
        All dataclasses are frozen (immutable) for thread safety.
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

    def has_changed(self, other: Optional["AgentState"]) -> bool:
        """
        Check if state has changed compared to another state

        Compares key fields while excluding timestamps. Useful for
        detecting meaningful state changes that should trigger events.

        Args:
            other: Previous AgentState to compare against (None = always changed)

        Returns:
            True if state has changed, False if identical

        Example:
            >>> state1 = AgentState(model="Claude")
            >>> state2 = AgentState(model="GPT-4")
            >>> state2.has_changed(state1)
            True
        """
        if not other:
            return True

        # Compare key fields (excluding timestamps)
        return (
            self.model != other.model or
            self.workspace.name != other.workspace.name or
            self.workspace.path != other.workspace.path or
            self.workspace.git.branch != other.workspace.git.branch or
            self.context_window.usage_pct != other.context_window.usage_pct
        )

    def get_changes(self, other: Optional["AgentState"]) -> Dict[str, Any]:
        """
        Get specific changes between states

        Returns a dictionary describing what changed between this state
        and a previous state. Useful for logging and event handling.

        Args:
            other: Previous AgentState to compare against (None = initial state)

        Returns:
            Dictionary of changed fields with old/new values

        Example:
            >>> state1 = AgentState(model="Claude")
            >>> state2 = AgentState(model="GPT-4")
            >>> state2.get_changes(state1)
            {'model': {'old': 'Claude', 'new': 'GPT-4'}}
        """
        if not other:
            return {"initial": True}

        changes = {}

        if self.model != other.model:
            changes["model"] = {"old": other.model, "new": self.model}

        if self.workspace.name != other.workspace.name:
            changes["workspace"] = {"old": other.workspace.name, "new": self.workspace.name}

        if self.workspace.path != other.workspace.path:
            changes["workspace_path"] = {"old": other.workspace.path, "new": self.workspace.path}

        if self.workspace.git.branch != other.workspace.git.branch:
            changes["branch"] = {"old": other.workspace.git.branch, "new": self.workspace.git.branch}

        if self.context_window.usage_pct != other.context_window.usage_pct:
            changes["context_usage"] = {
                "old": other.context_window.usage_pct,
                "new": self.context_window.usage_pct
            }

        return changes
