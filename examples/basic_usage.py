#!/usr/bin/env python3
"""
Basic Usage Example for ContextAgent

Demonstrates how to use the ContextAgent to execute sensors
and retrieve context information.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import ContextAgent
from src.events import EventType


def main():
    print("=== ContextAgent Basic Usage Example ===\n")

    # Create agent
    agent = ContextAgent(
        sensor_timeout=5.0,
        context_threshold=80,
        enable_events=True
    )

    # Register event handler
    def on_state_changed(event):
        print(f"[EVENT] {event.event_type.value}")
        if event.old_value and event.new_value:
            print(f"  Changed from: {event.old_value}")
            print(f"  Changed to: {event.new_value}")

    agent.on(EventType.STATE_UPDATED, on_state_changed)

    # Get initial state
    print("1. Getting initial state...")
    state = agent.get_state(input_data={
        "model": "Claude",
        "workspace_path": str(Path.cwd()),
        "context_window": {
            "max_tokens": 200000,
            "tokens_used": 50000
        }
    })

    print(f"\nDisplay String: {state.display}")
    print(f"Model: {state.model}")
    print(f"Workspace: {state.workspace.name}")
    print(f"Context Usage: {state.context_window.usage_pct}%")
    print(f"Git Branch: {state.workspace.git.branch if state.workspace.git.branch else 'N/A'}")

    # Get cached state
    print("\n2. Getting cached state (no refresh)...")
    cached_state = agent.get_state(force_refresh=False)
    print(f"Display String: {cached_state.display}")
    print(f"Same as previous: {cached_state == state}")

    # Get display string
    print("\n3. Getting just the display string...")
    display = agent.get_display_string(input_data={
        "model": "Claude",
        "context_window": {
            "max_tokens": 200000,
            "tokens_used": 100000
        }
    })
    print(f"Display: {display}")

    # Access state properties
    print("\n4. Accessing state properties...")
    print(f"Current State: {agent.current_state.workspace.name if agent.current_state else 'None'}")
    print(f"Previous State: {agent.previous_state.workspace.name if agent.previous_state else 'None'}")

    # Demonstrate state to JSON
    print("\n5. Converting state to JSON...")
    print(state.to_json())

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
