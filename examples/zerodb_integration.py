#!/usr/bin/env python3
"""
ZeroDB Integration Example

Demonstrates how to integrate the Context Agent with ZeroDB for
persistent state storage and event logging.
"""

from context_agent import ContextAgent, EventType
import os
import requests
import json
import time


class ZeroDBClient:
    """Simple ZeroDB client for demonstration"""

    def __init__(self, api_key, project_id):
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = "https://api.zerodb.ainative.studio"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def log_event(self, event):
        """Log a single event to ZeroDB"""
        try:
            payload = {
                "event_type": event.event_type.value,
                "timestamp": event.timestamp,
                "old_value": str(event.old_value),
                "new_value": str(event.new_value),
                "metadata": event.metadata or {}
            }

            response = self.session.post(
                f"{self.base_url}/projects/{self.project_id}/events",
                json=payload
            )

            if response.status_code == 200:
                print(f"✓ Event logged: {event.event_type.value}")
            else:
                print(f"✗ Failed to log event: {response.status_code}")

        except Exception as e:
            print(f"✗ Error logging event: {e}")

    def save_state(self, state):
        """Save agent state to ZeroDB"""
        try:
            payload = {
                "table": "agent_states",
                "data": state.to_dict()
            }

            response = self.session.post(
                f"{self.base_url}/projects/{self.project_id}/tables/insert",
                json=payload
            )

            if response.status_code == 200:
                print(f"✓ State saved to ZeroDB")
            else:
                print(f"✗ Failed to save state: {response.status_code}")

        except Exception as e:
            print(f"✗ Error saving state: {e}")


def example_1_basic_logging():
    """Example 1: Basic event logging to ZeroDB"""
    print("\n" + "=" * 50)
    print("Example 1: Basic Event Logging")
    print("=" * 50)

    # Check for ZeroDB credentials
    api_key = os.getenv("ZERODB_API_KEY")
    project_id = os.getenv("ZERODB_PROJECT_ID")

    if not api_key or not project_id:
        print("⚠️ ZeroDB credentials not found in environment")
        print("Set ZERODB_API_KEY and ZERODB_PROJECT_ID to run this example")
        return

    # Create ZeroDB client
    zerodb = ZeroDBClient(api_key, project_id)

    # Create handler that logs to ZeroDB
    def log_to_zerodb(event):
        zerodb.log_event(event)

    # Create and configure agent
    agent = ContextAgent(config={"polling_interval": 2})
    agent.on_change(EventType.STATE_UPDATED, log_to_zerodb)
    agent.start()

    print("Agent started. Events will be logged to ZeroDB...")
    print("Monitoring for 10 seconds...")

    time.sleep(10)
    agent.stop()
    print("Agent stopped.")


def example_2_state_persistence():
    """Example 2: Periodic state persistence to ZeroDB"""
    print("\n" + "=" * 50)
    print("Example 2: State Persistence")
    print("=" * 50)

    # Check for ZeroDB credentials
    api_key = os.getenv("ZERODB_API_KEY")
    project_id = os.getenv("ZERODB_PROJECT_ID")

    if not api_key or not project_id:
        print("⚠️ ZeroDB credentials not found in environment")
        return

    # Create ZeroDB client
    zerodb = ZeroDBClient(api_key, project_id)

    # Create agent
    agent = ContextAgent(config={"polling_interval": 5})
    agent.start()

    print("Agent started. Saving state to ZeroDB every 10 seconds...")
    print("Running for 30 seconds...")

    # Periodically save state
    for i in range(3):
        time.sleep(10)
        state = agent.get_state()
        print(f"\nIteration {i + 1}:")
        zerodb.save_state(state)

    agent.stop()
    print("Agent stopped.")


def example_3_selective_event_logging():
    """Example 3: Log only specific events"""
    print("\n" + "=" * 50)
    print("Example 3: Selective Event Logging")
    print("=" * 50)

    # Check for ZeroDB credentials
    api_key = os.getenv("ZERODB_API_KEY")
    project_id = os.getenv("ZERODB_PROJECT_ID")

    if not api_key or not project_id:
        print("⚠️ ZeroDB credentials not found in environment")
        return

    # Create ZeroDB client
    zerodb = ZeroDBClient(api_key, project_id)

    # Create handlers for specific events
    def log_branch_change(event):
        print(f"Branch changed: {event.old_value} → {event.new_value}")
        zerodb.log_event(event)

    def log_context_threshold(event):
        print(f"Context threshold reached: {event.new_value}%")
        zerodb.log_event(event)

    # Create and configure agent
    agent = ContextAgent(config={
        "polling_interval": 2,
        "context_threshold": 75
    })

    # Only log specific events
    agent.on_change(EventType.BRANCH_CHANGED, log_branch_change)
    agent.on_change(EventType.CONTEXT_THRESHOLD, log_context_threshold)

    agent.start()

    print("Agent started. Logging only branch changes and context thresholds...")
    print("Running for 15 seconds...")

    time.sleep(15)
    agent.stop()
    print("Agent stopped.")


def example_4_batched_logging():
    """Example 4: Batch events before sending to ZeroDB"""
    print("\n" + "=" * 50)
    print("Example 4: Batched Event Logging")
    print("=" * 50)

    # Check for ZeroDB credentials
    api_key = os.getenv("ZERODB_API_KEY")
    project_id = os.getenv("ZERODB_PROJECT_ID")

    if not api_key or not project_id:
        print("⚠️ ZeroDB credentials not found in environment")
        return

    # Create ZeroDB client
    zerodb = ZeroDBClient(api_key, project_id)

    # Event buffer for batching
    event_buffer = []
    BATCH_SIZE = 5

    def buffer_event(event):
        """Buffer events and send in batches"""
        event_buffer.append(event)
        print(f"Buffered event ({len(event_buffer)}/{BATCH_SIZE}): {event.event_type.value}")

        if len(event_buffer) >= BATCH_SIZE:
            print("Sending batch to ZeroDB...")
            for buffered_event in event_buffer:
                zerodb.log_event(buffered_event)
            event_buffer.clear()
            print("Batch sent!")

    # Create and configure agent
    agent = ContextAgent(config={"polling_interval": 1})
    agent.on_change(EventType.STATE_UPDATED, buffer_event)
    agent.start()

    print("Agent started. Batching events...")
    print("Running for 10 seconds...")

    time.sleep(10)

    # Send remaining buffered events
    if event_buffer:
        print(f"Sending final batch ({len(event_buffer)} events)...")
        for event in event_buffer:
            zerodb.log_event(event)

    agent.stop()
    print("Agent stopped.")


def main():
    """Run all ZeroDB integration examples"""
    print("Context Agent - ZeroDB Integration Examples")
    print("\nNote: These examples require ZERODB_API_KEY and ZERODB_PROJECT_ID")
    print("environment variables to be set.\n")

    example_1_basic_logging()
    example_2_state_persistence()
    example_3_selective_event_logging()
    example_4_batched_logging()

    print("\n" + "=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
