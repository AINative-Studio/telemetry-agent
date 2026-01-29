"""
Integration Tests for ContextAgent

Tests the full integration with the actual sensor script.
"""

import pytest
import json
from pathlib import Path

from src.agent import ContextAgent, SensorError
from src.state import AgentState
from src.events import EventType


class TestAgentIntegration:
    """Integration tests with real sensor script"""

    def test_agent_executes_real_sensor(self):
        """Test agent can execute the real sensor script"""
        agent = ContextAgent()

        # Execute sensor with basic input
        state = agent.get_state(input_data={
            "model": "Claude",
            "workspace_path": str(Path.cwd()),
            "context_window": {
                "max_tokens": 200000,
                "tokens_used": 50000
            }
        })

        # Verify state was created
        assert isinstance(state, AgentState)
        assert state.model == "Claude"
        assert state.display != ""
        assert state.workspace.path != ""

    def test_agent_caches_state(self):
        """Test agent caches state correctly"""
        agent = ContextAgent()

        # First call
        state1 = agent.get_state()

        # Second call without refresh
        state2 = agent.get_state(force_refresh=False)

        # Should be same instance
        assert state1 == state2
        assert agent.current_state == state1

    def test_agent_display_string(self):
        """Test agent returns display string"""
        agent = ContextAgent()

        display = agent.get_display_string(input_data={
            "model": "Claude",
            "context_window": {
                "max_tokens": 200000,
                "tokens_used": 100000
            }
        })

        # Display should contain model name
        assert "Claude" in display
        assert isinstance(display, str)

    def test_agent_tracks_state_changes(self):
        """Test agent tracks previous and current state"""
        agent = ContextAgent()

        # First state
        state1 = agent.get_state(input_data={"model": "Claude"})

        assert agent.current_state == state1
        assert agent.previous_state is None

        # Second state
        state2 = agent.get_state(input_data={"model": "GPT-4"})

        assert agent.current_state == state2
        assert agent.previous_state == state1

    def test_agent_event_emission_integration(self):
        """Test event emission with real sensor"""
        agent = ContextAgent(enable_events=True)

        events_received = []

        def handler(event):
            events_received.append(event)

        agent.on(EventType.STATE_UPDATED, handler)

        # Execute sensor twice with different inputs
        agent.get_state(input_data={"model": "Claude"})
        agent.get_state(input_data={
            "model": "Claude",
            "context_window": {
                "max_tokens": 200000,
                "tokens_used": 100000
            }
        })

        # Should have received events
        assert len(events_received) >= 1
        assert all(e.event_type == EventType.STATE_UPDATED for e in events_received)

    def test_agent_sensor_failure_fallback(self):
        """Test agent falls back to cached state on sensor failure"""
        # Use invalid sensor path after getting initial state
        agent = ContextAgent()

        # Get initial state with valid sensor
        state1 = agent.get_state()

        # Now simulate sensor failure by using invalid path
        agent._sensor_path = Path("/nonexistent/sensor.sh")

        # Should return cached state
        state2 = agent.get_state()

        # Should be the same as previous state
        assert state2 == state1
