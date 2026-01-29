"""
Context Agent - AINative Studio
Local context monitoring agent for IDE and workspace environments
"""

__version__ = "1.0.0"
__agent_type__ = "context"

from .agent import ContextAgent
from .state import AgentState, WorkspaceInfo, GitInfo, ContextWindowInfo
from .events import EventType, StateChangeEvent
from .config import AgentConfig
from .agent_with_zerodb import ContextAgentWithZeroDB, create_context_agent
from .zerodb_integration import ZeroDBPersistence

__all__ = [
    "ContextAgent",
    "ContextAgentWithZeroDB",
    "create_context_agent",
    "AgentState",
    "WorkspaceInfo",
    "GitInfo",
    "ContextWindowInfo",
    "EventType",
    "StateChangeEvent",
    "AgentConfig",
    "ZeroDBPersistence",
]
