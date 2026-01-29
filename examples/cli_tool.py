#!/usr/bin/env python3
"""
CLI Tool Example

A command-line interface for the Context Agent.
Demonstrates how to build a CLI tool using the agent.
"""

import argparse
import json
import sys
import time
from context_agent import ContextAgent, EventType


def cmd_get_state(args):
    """Get current agent state"""
    agent = ContextAgent()
    agent.start()
    time.sleep(1)  # Wait for initial state
    state = agent.get_state()

    if args.json:
        print(state.to_json())
    else:
        print(state.display)

    agent.stop()


def cmd_watch(args):
    """Watch for state changes"""
    def on_change(event):
        if args.json:
            print(json.dumps(event.to_dict()))
        else:
            timestamp = event.timestamp.split("T")[1].split(".")[0]
            print(f"[{timestamp}] {event.event_type.value}: {event.old_value} → {event.new_value}")

    agent = ContextAgent(config={
        "polling_interval": args.interval,
        "context_threshold": args.threshold
    })

    # Subscribe to events
    if args.event:
        # Watch specific event
        event_type = EventType(args.event)
        agent.on_change(event_type, on_change)
    else:
        # Watch all events
        for event_type in EventType:
            agent.on_change(event_type, on_change)

    agent.start()

    print(f"Watching for changes (polling every {args.interval}s)...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        agent.stop()


def cmd_monitor(args):
    """Monitor context usage"""
    def on_threshold(event):
        usage = event.new_value
        if usage >= 90:
            print(f"🚨 CRITICAL: Context at {usage}%")
        elif usage >= args.threshold:
            print(f"⚠️ WARNING: Context at {usage}%")

    def on_update(event):
        state = agent.get_state()
        if not args.quiet:
            print(f"\r{state.display}", end="", flush=True)

    agent = ContextAgent(config={
        "polling_interval": args.interval,
        "context_threshold": args.threshold
    })

    agent.on_change(EventType.CONTEXT_THRESHOLD, on_threshold)
    agent.on_change(EventType.STATE_UPDATED, on_update)

    agent.start()

    print(f"Monitoring context usage (threshold: {args.threshold}%)...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        agent.stop()


def cmd_info(args):
    """Display detailed agent information"""
    agent = ContextAgent()
    agent.start()
    time.sleep(1)
    state = agent.get_state()

    print("Context Agent Information")
    print("=" * 50)
    print(f"Agent Type:       {state.agent_type}")
    print(f"Agent Version:    {state.agent_version}")
    print(f"Sensor Version:   {state.sensor_version}")
    print(f"Last Updated:     {state.last_updated}")
    print()
    print("Current State")
    print("-" * 50)
    print(f"Model:            {state.model}")
    print(f"Workspace:        {state.workspace.name}")
    print(f"Path:             {state.workspace.path}")
    print(f"Git Repository:   {state.workspace.git.is_repo}")
    if state.workspace.git.is_repo:
        print(f"Git Branch:       {state.workspace.git.branch}")
    print()
    print("Context Window")
    print("-" * 50)
    print(f"Max Tokens:       {state.context_window.max_tokens:,}")
    print(f"Tokens Used:      {state.context_window.tokens_used:,}")
    print(f"Usage:            {state.context_window.usage_pct}%")
    print()
    print("Display")
    print("-" * 50)
    print(state.display)

    agent.stop()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Context Agent CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get current state
  %(prog)s get

  # Get state as JSON
  %(prog)s get --json

  # Watch all changes
  %(prog)s watch

  # Watch specific event
  %(prog)s watch --event branch_changed

  # Monitor context usage
  %(prog)s monitor --threshold 80

  # Display agent info
  %(prog)s info
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get current agent state")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")
    get_parser.set_defaults(func=cmd_get_state)

    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch for state changes")
    watch_parser.add_argument("--interval", type=int, default=2, help="Polling interval (seconds)")
    watch_parser.add_argument("--threshold", type=int, default=80, help="Context threshold (%)")
    watch_parser.add_argument("--event", choices=[e.value for e in EventType], help="Watch specific event")
    watch_parser.add_argument("--json", action="store_true", help="Output as JSON")
    watch_parser.set_defaults(func=cmd_watch)

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor context usage")
    monitor_parser.add_argument("--interval", type=int, default=5, help="Polling interval (seconds)")
    monitor_parser.add_argument("--threshold", type=int, default=80, help="Alert threshold (%)")
    monitor_parser.add_argument("--quiet", action="store_true", help="Only show alerts")
    monitor_parser.set_defaults(func=cmd_monitor)

    # Info command
    info_parser = subparsers.add_parser("info", help="Display agent information")
    info_parser.set_defaults(func=cmd_info)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
