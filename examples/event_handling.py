#!/usr/bin/env python3
"""
Event Handling Example

Demonstrates how to subscribe to state change events.
"""

from context_agent import ContextAgent, EventType
import time


def on_model_changed(event):
    """Handler for model changes"""
    print(f"\n[MODEL CHANGED]")
    print(f"  Old: {event.old_value}")
    print(f"  New: {event.new_value}")
    print(f"  Timestamp: {event.timestamp}")


def on_workspace_changed(event):
    """Handler for workspace changes"""
    print(f"\n[WORKSPACE CHANGED]")
    print(f"  Old: {event.old_value}")
    print(f"  New: {event.new_value}")
    print(f"  Timestamp: {event.timestamp}")


def on_branch_changed(event):
    """Handler for git branch changes"""
    print(f"\n[BRANCH CHANGED]")
    print(f"  Old: {event.old_value}")
    print(f"  New: {event.new_value}")
    print(f"  Timestamp: {event.timestamp}")


def on_context_threshold(event):
    """Handler for context threshold events"""
    usage = event.new_value
    print(f"\n[CONTEXT THRESHOLD]")
    print(f"  Usage: {usage}%")

    if usage >= 90:
        print("  ⚠️ CRITICAL: Context usage very high!")
    elif usage >= 75:
        print("  ⚠️ WARNING: Context usage high")
    else:
        print("  ℹ️ INFO: Context usage normal")


def on_state_updated(event):
    """Handler for any state update"""
    print(".", end="", flush=True)  # Print dot for each update


def main():
    """Event handling example"""
    print("Context Agent - Event Handling Example")
    print("=" * 50)

    # Create agent with faster polling for demonstration
    agent = ContextAgent(config={"polling_interval": 2})

    # Register event handlers
    print("\nRegistering event handlers...")
    agent.on_change(EventType.MODEL_CHANGED, on_model_changed)
    agent.on_change(EventType.WORKSPACE_CHANGED, on_workspace_changed)
    agent.on_change(EventType.BRANCH_CHANGED, on_branch_changed)
    agent.on_change(EventType.CONTEXT_THRESHOLD, on_context_threshold)
    agent.on_change(EventType.STATE_UPDATED, on_state_updated)

    # Start agent
    print("Starting agent...")
    agent.start()
    print("Agent started!")

    # Instructions
    print("\nMonitoring for changes...")
    print("Try the following to trigger events:")
    print("  - Change git branch: git checkout <branch-name>")
    print("  - Change directory: cd /path/to/other/workspace")
    print("  - Continue conversation to increase context usage")
    print("\nPress Ctrl+C to stop\n")

    # Monitor for changes
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping agent...")
        agent.stop()
        print("Agent stopped!")


if __name__ == "__main__":
    main()
