#!/usr/bin/env python3
"""
Context Agent API Demo

Demonstrates the public API methods for ContextAgent as specified in Issue #4.
"""

import sys
import time
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import ContextAgent
from src.events import EventType


def main():
    """Demonstrate Context Agent API usage"""

    print("=" * 60)
    print("Context Agent API Demo (Issue #4)")
    print("=" * 60)
    print()

    # Initialize agent
    print("1. Initialize ContextAgent")
    agent = ContextAgent()
    print("   ✓ Agent initialized")
    print()

    # Start agent
    print("2. Start agent")
    agent.start()
    print("   ✓ Agent started and state initialized")
    print()

    # Get state as dictionary
    print("3. Get state using get_state_dict()")
    state = agent.get_state_dict()
    print(f"   Agent Type: {state['agent_type']}")
    print(f"   Model: {state['model']}")
    print(f"   Workspace: {state['workspace']['name']}")
    print(f"   Path: {state['workspace']['path']}")
    if state['workspace']['git']['is_repo']:
        print(f"   Git Branch: {state['workspace']['git']['branch']}")
    print(f"   Context Usage: {state['context_window']['usage_pct']}%")
    print()

    # Get display header
    print("4. Get display header using get_display_header()")
    header = agent.get_display_header()
    print(f"   {header}")
    print()

    # Register event handlers
    print("5. Register event handlers using on_change()")

    def on_branch_change(event):
        print(f"   📌 Branch changed: {event.old_value} → {event.new_value}")

    def on_model_change(event):
        print(f"   🤖 Model changed: {event.old_value} → {event.new_value}")

    def on_workspace_change(event):
        print(f"   📁 Workspace changed: {event.old_value} → {event.new_value}")

    def on_context_threshold(event):
        print(f"   ⚠️  Context threshold exceeded: {event.new_value}%")

    def on_state_update(event):
        if event.metadata and 'changes' in event.metadata:
            changes = event.metadata['changes']
            print(f"   📊 State updated: {len(changes)} change(s)")

    agent.on_change(EventType.BRANCH_CHANGED, on_branch_change)
    agent.on_change(EventType.MODEL_CHANGED, on_model_change)
    agent.on_change(EventType.WORKSPACE_CHANGED, on_workspace_change)
    agent.on_change(EventType.CONTEXT_THRESHOLD, on_context_threshold)
    agent.on_change(EventType.STATE_UPDATED, on_state_update)
    print("   ✓ Event handlers registered")
    print()

    # Monitor for a few seconds
    print("6. Monitor state changes (5 seconds)...")
    print("   (Change git branch, workspace, etc. to see events)")
    print()
    time.sleep(5)

    # Unregister handler
    print("7. Unregister event handler using off()")
    agent.off(EventType.STATE_UPDATED, on_state_update)
    print("   ✓ STATE_UPDATED handler unregistered")
    print()

    # Stop agent
    print("8. Stop agent")
    agent.stop()
    print("   ✓ Agent stopped")
    print()

    print("=" * 60)
    print("API Demo Complete!")
    print("=" * 60)
    print()
    print("Public API Methods Demonstrated:")
    print("  ✓ get_state_dict() -> Dict[str, Any]")
    print("  ✓ get_display_header() -> str")
    print("  ✓ on_change(event_type, callback) -> None")
    print("  ✓ off(event_type, callback) -> None")
    print("  ✓ start() -> None")
    print("  ✓ stop() -> None")
    print()


if __name__ == "__main__":
    main()
