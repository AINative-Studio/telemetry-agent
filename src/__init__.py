"""
Context Agent - AINative Studio
Local context monitoring agent for IDE and workspace environments
"""

__version__ = "1.0.0"
__agent_type__ = "context"

from .agent import ContextAgent
from .state import AgentState, WorkspaceInfo, GitInfo, ContextWindowInfo
from .events import EventType, StateChangeEvent

__all__ = [
    "ContextAgent",
    "AgentState",
    "WorkspaceInfo",
    "GitInfo",
    "ContextWindowInfo",
    "EventType",
    "StateChangeEvent",
]
