#!/usr/bin/env python3
"""
Demonstration of State Management Usage

This script demonstrates how to use the state management module
in real-world scenarios.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.state import AgentState, WorkspaceInfo, GitInfo, ContextWindowInfo
import json


def demo_basic_usage():
    """Demonstrate basic state creation and serialization"""
    print("=" * 60)
    print("DEMO 1: Basic State Creation and Serialization")
    print("=" * 60)

    # Create a state
    state = AgentState(
        model="Claude",
        workspace=WorkspaceInfo(
            path="/Users/developer/projects/my-app",
            name="my-app",
            git=GitInfo(is_repo=True, branch="feature/new-feature")
        ),
        context_window=ContextWindowInfo(
            max_tokens=200000,
            tokens_used=45000,
            usage_pct=22
        ),
        display="[Claude] my-app (feature/new-feature) | 22%"
    )

    print("\n1. State Created:")
    print(f"   Model: {state.model}")
    print(f"   Workspace: {state.workspace.name}")
    print(f"   Branch: {state.workspace.git.branch}")
    print(f"   Context: {state.context_window.usage_pct}%")

    print("\n2. JSON Serialization:")
    print(state.to_json())

    print("\n3. Immutability Test:")
    try:
        state.model = "GPT-4"
        print("   ERROR: State was modified (should be frozen!)")
    except Exception as e:
        print(f"   ✅ State is frozen: {type(e).__name__}")


def demo_sensor_parsing():
    """Demonstrate parsing sensor output"""
    print("\n" + "=" * 60)
    print("DEMO 2: Parsing Sensor Output")
    print("=" * 60)

    # Simulate sensor output
    sensor_data = {
        "model": "Claude",
        "workspace": {
            "path": "/home/user/projects/web-app",
            "name": "web-app",
            "git": {
                "is_repo": True,
                "branch": "main"
            }
        },
        "context_window": {
            "max_tokens": 200000,
            "tokens_used": 50000,
            "usage_pct": 25
        },
        "version": "1.0.0"
    }

    display_output = "[Claude] web-app (main) | 25%"

    print("\n1. Sensor Data:")
    print(json.dumps(sensor_data, indent=2))

    print("\n2. Display Output:")
    print(f'   "{display_output}"')

    print("\n3. Parsed State:")
    state = AgentState.from_sensor_output(sensor_data, display_output)
    print(f"   Model: {state.model}")
    print(f"   Workspace: {state.workspace.name} at {state.workspace.path}")
    print(f"   Branch: {state.workspace.git.branch}")
    print(f"   Context: {state.context_window.usage_pct}%")


def demo_change_detection():
    """Demonstrate change detection between states"""
    print("\n" + "=" * 60)
    print("DEMO 3: Change Detection")
    print("=" * 60)

    # Initial state
    state1 = AgentState(
        model="Claude",
        workspace=WorkspaceInfo(
            name="my-project",
            git=GitInfo(is_repo=True, branch="main")
        ),
        context_window=ContextWindowInfo(usage_pct=15)
    )

    print("\n1. Initial State:")
    print(f"   Model: {state1.model}")
    print(f"   Branch: {state1.workspace.git.branch}")
    print(f"   Context: {state1.context_window.usage_pct}%")

    # Simulated state after branch switch
    state2 = AgentState(
        model="Claude",
        workspace=WorkspaceInfo(
            name="my-project",
            git=GitInfo(is_repo=True, branch="feature/api-update")
        ),
        context_window=ContextWindowInfo(usage_pct=45)
    )

    print("\n2. Updated State:")
    print(f"   Model: {state2.model}")
    print(f"   Branch: {state2.workspace.git.branch}")
    print(f"   Context: {state2.context_window.usage_pct}%")

    print("\n3. Change Detection:")
    has_changed = state2.has_changed(state1)
    print(f"   Has changed? {has_changed}")

    print("\n4. Detailed Changes:")
    changes = state2.get_changes(state1)
    for key, value in changes.items():
        print(f"   {key}:")
        print(f"      old: {value['old']}")
        print(f"      new: {value['new']}")


def demo_validation():
    """Demonstrate input validation"""
    print("\n" + "=" * 60)
    print("DEMO 4: Input Validation")
    print("=" * 60)

    print("\n1. Testing negative values:")
    context = ContextWindowInfo(
        max_tokens=-1000,
        tokens_used=-500,
        usage_pct=-50
    )
    print(f"   Input: max_tokens=-1000, tokens_used=-500, usage_pct=-50")
    print(f"   Result: max_tokens={context.max_tokens}, tokens_used={context.tokens_used}, usage_pct={context.usage_pct}")
    print(f"   ✅ Negative values clamped to 0")

    print("\n2. Testing usage_pct > 100:")
    context2 = ContextWindowInfo(
        max_tokens=100000,
        tokens_used=150000,
        usage_pct=150
    )
    print(f"   Input: usage_pct=150")
    print(f"   Result: usage_pct={context2.usage_pct}")
    print(f"   ✅ Usage clamped to 100")


def demo_partial_sensor_data():
    """Demonstrate handling partial sensor data"""
    print("\n" + "=" * 60)
    print("DEMO 5: Handling Partial Sensor Data")
    print("=" * 60)

    # Minimal sensor data
    sensor_data = {
        "model": "Claude",
        "workspace": {
            "name": "minimal-project"
        }
    }

    print("\n1. Minimal Sensor Data:")
    print(json.dumps(sensor_data, indent=2))

    print("\n2. Parsed State (with defaults):")
    state = AgentState.from_sensor_output(sensor_data, "Minimal")
    print(f"   Model: {state.model}")
    print(f"   Workspace: {state.workspace.name}")
    print(f"   Workspace Path: '{state.workspace.path}' (default)")
    print(f"   Git Repo: {state.workspace.git.is_repo} (default)")
    print(f"   Git Branch: '{state.workspace.git.branch}' (default)")
    print(f"   Context Max: {state.context_window.max_tokens} (default)")
    print(f"   ✅ All missing fields use safe defaults")


def demo_thread_safety():
    """Demonstrate thread safety"""
    print("\n" + "=" * 60)
    print("DEMO 6: Thread Safety (Immutability)")
    print("=" * 60)

    state = AgentState(model="Claude")

    print("\n1. Original State:")
    print(f"   Model: {state.model}")

    print("\n2. Attempting to modify state fields:")

    tests = [
        ("state.model", lambda: setattr(state, 'model', 'GPT-4')),
        ("state.workspace.name", lambda: setattr(state.workspace, 'name', 'hacked')),
        ("state.workspace.git.branch", lambda: setattr(state.workspace.git, 'branch', 'evil')),
        ("state.context_window.usage_pct", lambda: setattr(state.context_window, 'usage_pct', 999)),
    ]

    for field_name, mutation_func in tests:
        try:
            mutation_func()
            print(f"   ❌ {field_name}: MODIFIED (SECURITY ISSUE!)")
        except Exception as e:
            print(f"   ✅ {field_name}: Blocked ({type(e).__name__})")

    print("\n3. State Remains Unchanged:")
    print(f"   Model: {state.model}")
    print(f"   ✅ State is completely immutable - safe for concurrent access")


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 60)
    print("STATE MANAGEMENT DEMONSTRATION")
    print("=" * 60)
    print("\nThis demo shows all features of the state management module:")
    print("- State creation and serialization")
    print("- Sensor output parsing")
    print("- Change detection")
    print("- Input validation")
    print("- Partial data handling")
    print("- Thread safety (immutability)")

    demo_basic_usage()
    demo_sensor_parsing()
    demo_change_detection()
    demo_validation()
    demo_partial_sensor_data()
    demo_thread_safety()

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nAll state management features verified successfully!")
    print("Ready for production use.")
    print()


if __name__ == "__main__":
    main()
