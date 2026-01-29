#!/usr/bin/env python3
"""
ZeroDB Integration Example for Context Agent

This example demonstrates how to use Context Agent with ZeroDB persistence
for state storage and event logging.
"""

import asyncio
import logging
import time
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from context_agent.config import AgentConfig
from context_agent.agent_with_zerodb import create_context_agent
from context_agent.events import EventType


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_usage():
    """Example 1: Basic usage with automatic config loading"""
    logger.info("=" * 60)
    logger.info("Example 1: Basic Usage")
    logger.info("=" * 60)

    # Create agent (loads from environment or config file)
    agent = create_context_agent()

    # Check ZeroDB status
    status = agent.get_zerodb_status()
    logger.info(f"ZeroDB Status: {status}")

    # Get state (automatically persisted if ZeroDB is enabled)
    state = agent.get_state()
    logger.info(f"Current State: {state.display}")
    logger.info(f"Workspace: {state.workspace.name}")
    logger.info(f"Branch: {state.workspace.git.branch}")
    logger.info(f"Context Usage: {state.context_window.usage_pct}%")

    agent.shutdown()
    logger.info("Example 1 complete\n")


def example_2_with_configuration():
    """Example 2: Using explicit configuration"""
    logger.info("=" * 60)
    logger.info("Example 2: Explicit Configuration")
    logger.info("=" * 60)

    # Create configuration
    config = AgentConfig(
        enable_zerodb=True,
        zerodb_enable_logging=True,
        polling_interval=5.0,
        context_threshold=80
        # Note: API key and project ID should come from environment
    )

    # Create agent with config
    with create_context_agent(config=config) as agent:
        # Get status
        status = agent.get_zerodb_status()
        logger.info(f"ZeroDB Enabled: {status['enabled']}")
        logger.info(f"ZeroDB Initialized: {status['initialized']}")

        # Get state
        state = agent.get_state()
        logger.info(f"State: {state.display}")

    logger.info("Example 2 complete\n")


def example_3_event_handlers():
    """Example 3: Event handlers with ZeroDB logging"""
    logger.info("=" * 60)
    logger.info("Example 3: Event Handlers")
    logger.info("=" * 60)

    agent = create_context_agent()

    # Register event handlers
    def on_state_updated(event):
        logger.info(f"State updated at {event.timestamp}")
        if event.metadata and 'changes' in event.metadata:
            logger.info(f"Changes: {event.metadata['changes']}")

    def on_branch_changed(event):
        logger.info(f"Branch changed: {event.old_value} -> {event.new_value}")

    def on_context_threshold(event):
        logger.warning(
            f"Context threshold exceeded: {event.new_value}% "
            f"(threshold: {event.metadata['threshold']}%)"
        )

    # Register handlers
    agent.on(EventType.STATE_UPDATED, on_state_updated)
    agent.on(EventType.BRANCH_CHANGED, on_branch_changed)
    agent.on(EventType.CONTEXT_THRESHOLD, on_context_threshold)

    # Trigger state updates
    for i in range(3):
        logger.info(f"Update {i + 1}...")
        agent.get_state()
        time.sleep(1)

    agent.shutdown()
    logger.info("Example 3 complete\n")


async def example_4_query_history():
    """Example 4: Query historical state data"""
    logger.info("=" * 60)
    logger.info("Example 4: Query Historical Data")
    logger.info("=" * 60)

    agent = create_context_agent()

    # Store some states first
    logger.info("Storing state snapshots...")
    for i in range(5):
        agent.get_state()
        await asyncio.sleep(0.5)

    # Query historical states
    logger.info("\nQuerying state history...")
    history = await agent.get_state_history(limit=10)

    logger.info(f"Found {len(history)} state records:")
    for record in history[:5]:  # Show first 5
        logger.info(f"  [{record['timestamp']}] {record['display']}")
        logger.info(f"    Workspace: {record['workspace_name']}")
        logger.info(f"    Branch: {record['git_branch']}")
        logger.info(f"    Context: {record['context_usage_pct']}%")

    agent.shutdown()
    logger.info("Example 4 complete\n")


async def example_5_query_events():
    """Example 5: Query event logs"""
    logger.info("=" * 60)
    logger.info("Example 5: Query Event Logs")
    logger.info("=" * 60)

    agent = create_context_agent()

    # Trigger some events
    logger.info("Generating events...")
    for i in range(5):
        agent.get_state()
        await asyncio.sleep(0.5)

    # Query event logs
    logger.info("\nQuerying event logs...")
    events = await agent.get_event_logs(limit=20)

    logger.info(f"Found {len(events)} event records:")
    for event in events[:10]:  # Show first 10
        logger.info(
            f"  [{event['timestamp']}] {event['event_type']}: "
            f"{event['old_value']} -> {event['new_value']}"
        )

    # Query specific event type
    logger.info("\nQuerying branch change events...")
    branch_events = await agent.get_event_logs(
        event_type="branch_changed",
        limit=10
    )
    logger.info(f"Found {len(branch_events)} branch change events")

    agent.shutdown()
    logger.info("Example 5 complete\n")


async def example_6_statistics():
    """Example 6: Get ZeroDB statistics"""
    logger.info("=" * 60)
    logger.info("Example 6: ZeroDB Statistics")
    logger.info("=" * 60)

    agent = create_context_agent()

    # Store some data
    logger.info("Storing data...")
    for i in range(3):
        agent.get_state()
        await asyncio.sleep(0.5)

    # Get statistics
    stats = await agent.get_zerodb_statistics()

    logger.info("\nZeroDB Statistics:")
    logger.info(f"  Enabled: {stats.get('enabled', False)}")
    logger.info(f"  Initialized: {stats.get('initialized', False)}")
    logger.info(f"  Project ID: {stats.get('project_id', 'N/A')}")
    logger.info(f"  State Snapshots: {stats.get('state_snapshots', 0)}")
    logger.info(f"  Event Logs: {stats.get('event_logs', 0)}")

    if 'tables' in stats:
        logger.info(f"  State Table: {stats['tables']['state']}")
        logger.info(f"  Events Table: {stats['tables']['events']}")

    agent.shutdown()
    logger.info("Example 6 complete\n")


async def example_7_error_handling():
    """Example 7: Graceful error handling"""
    logger.info("=" * 60)
    logger.info("Example 7: Error Handling")
    logger.info("=" * 60)

    # Create agent with invalid credentials (simulating error)
    config = AgentConfig(
        enable_zerodb=True,
        zerodb_api_key="invalid_key",
        zerodb_project_id="invalid_project"
    )

    agent = create_context_agent(config=config)

    # Agent should still work even if ZeroDB fails
    logger.info("Getting state (ZeroDB should fail gracefully)...")
    state = agent.get_state()
    logger.info(f"State retrieved: {state.display}")

    # Check status
    status = agent.get_zerodb_status()
    logger.info(f"ZeroDB Status: {status}")

    if not status['initialized']:
        logger.info(f"ZeroDB Error: {status.get('initialization_error', 'Unknown')}")
        logger.info("Agent continues to work without persistence!")

    agent.shutdown()
    logger.info("Example 7 complete\n")


def main():
    """Run all examples"""
    logger.info("ZeroDB Integration Examples for Context Agent")
    logger.info("=" * 60)
    logger.info("")

    # Check if ZeroDB is configured
    import os
    api_key = os.getenv("CONTEXT_AGENT_ZERODB_API_KEY")
    project_id = os.getenv("CONTEXT_AGENT_ZERODB_PROJECT_ID")

    if not api_key or not project_id:
        logger.warning("")
        logger.warning("ZeroDB credentials not configured!")
        logger.warning("Set these environment variables:")
        logger.warning("  export CONTEXT_AGENT_ENABLE_ZERODB=true")
        logger.warning("  export CONTEXT_AGENT_ZERODB_API_KEY='your_key'")
        logger.warning("  export CONTEXT_AGENT_ZERODB_PROJECT_ID='your_project'")
        logger.warning("")
        logger.warning("Examples will run but ZeroDB features will be disabled.")
        logger.warning("")

    try:
        # Run synchronous examples
        example_1_basic_usage()
        example_2_with_configuration()
        example_3_event_handlers()

        # Run async examples
        asyncio.run(example_4_query_history())
        asyncio.run(example_5_query_events())
        asyncio.run(example_6_statistics())
        asyncio.run(example_7_error_handling())

        logger.info("=" * 60)
        logger.info("All examples completed successfully!")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("\nExamples interrupted by user")
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
