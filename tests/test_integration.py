"""
Integration Tests for Context Agent

End-to-end tests covering complete workflows and system integration.
"""

import pytest
import json
import time
import subprocess
from pathlib import Path
from unittest.mock import patch, Mock

from src.agent import ContextAgent
from src.state import AgentState
from src.events import EventType


# ============================================================================
# Full Lifecycle Integration Tests
# ============================================================================

@pytest.mark.integration
class TestFullAgentLifecycle:
    """Test complete agent lifecycle from initialization to shutdown"""

    @patch.object(ContextAgent, '_execute_sensor')
    def test_complete_lifecycle_workflow(self, mock_execute):
        """Test complete agent lifecycle"""
        mock_execute.return_value = (
            "[Claude] 📁 test 🌿 main",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {
                    "path": "/test",
                    "name": "test",
                    "git": {"is_repo": True, "branch": "main"}
                },
                "context_window": {
                    "max_tokens": 200000,
                    "tokens_used": 10000,
                    "usage_pct": 5
                }
            })
        )

        # 1. Initialize agent
        agent = ContextAgent()
        assert agent.current_state is None

        # 2. Get initial state
        state = agent.get_state()
        assert state is not None
        assert state.model == "Claude"
        assert agent.current_state == state

        # 3. Get display
        display = agent.get_display_string()
        assert display == "[Claude] 📁 test 🌿 main"

        # 4. Register event handlers
        handler = Mock()
        agent.on(EventType.BRANCH_CHANGED, handler)

        # 5. Trigger state change
        mock_execute.return_value = (
            "[Claude] 📁 test 🌿 feature",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {
                    "path": "/test",
                    "name": "test",
                    "git": {"is_repo": True, "branch": "feature"}
                },
                "context_window": {
                    "max_tokens": 200000,
                    "tokens_used": 10000,
                    "usage_pct": 5
                }
            })
        )

        new_state = agent.get_state(force_refresh=True)
        assert new_state.workspace.git.branch == "feature"

        # 6. Verify event was emitted
        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert event.old_value == "main"
        assert event.new_value == "feature"

        # 7. Verify state history
        assert agent.previous_state.workspace.git.branch == "main"
        assert agent.current_state.workspace.git.branch == "feature"


@pytest.mark.integration
class TestStateChangePropagation:
    """Test state change detection and event propagation"""

    @patch.object(ContextAgent, '_execute_sensor')
    def test_multiple_sequential_changes(self, mock_execute):
        """Test multiple sequential state changes are properly detected"""
        states = [
            {
                "stdout": "[Claude] 📁 test 🌿 main",
                "state": {
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {
                        "path": "/test",
                        "name": "test",
                        "git": {"is_repo": True, "branch": "main"}
                    },
                    "context_window": {
                        "max_tokens": 200000,
                        "tokens_used": 10000,
                        "usage_pct": 5
                    }
                }
            },
            {
                "stdout": "[Claude] 📁 test 🌿 develop",
                "state": {
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {
                        "path": "/test",
                        "name": "test",
                        "git": {"is_repo": True, "branch": "develop"}
                    },
                    "context_window": {
                        "max_tokens": 200000,
                        "tokens_used": 10000,
                        "usage_pct": 5
                    }
                }
            },
            {
                "stdout": "[Claude] 📁 test 🌿 feature",
                "state": {
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {
                        "path": "/test",
                        "name": "test",
                        "git": {"is_repo": True, "branch": "feature"}
                    },
                    "context_window": {
                        "max_tokens": 200000,
                        "tokens_used": 10000,
                        "usage_pct": 5
                    }
                }
            }
        ]

        def sensor_side_effect(*args, **kwargs):
            idx = mock_execute.call_count - 1
            s = states[min(idx, len(states) - 1)]
            return (s["stdout"], json.dumps(s["state"]))

        mock_execute.side_effect = sensor_side_effect

        agent = ContextAgent()
        branch_events = []

        def track_events(event):
            branch_events.append({
                "old": event.old_value,
                "new": event.new_value
            })

        agent.on(EventType.BRANCH_CHANGED, track_events)

        # Get states
        agent.get_state()
        agent.get_state(force_refresh=True)
        agent.get_state(force_refresh=True)

        # Verify all changes were tracked
        assert len(branch_events) == 2
        assert branch_events[0]["old"] == "main"
        assert branch_events[0]["new"] == "develop"
        assert branch_events[1]["old"] == "develop"
        assert branch_events[1]["new"] == "feature"

    @patch.object(ContextAgent, '_execute_sensor')
    def test_context_threshold_crossing(self, mock_execute):
        """Test context threshold event emission"""
        states = [
            (70, "[Claude] 📁 test | 📊 70%"),
            (75, "[Claude] 📁 test | 📊 75%"),
            (85, "[Claude] 📁 test | 📊 85%"),
            (90, "[Claude] 📁 test | 📊 90%"),
        ]

        def sensor_side_effect(*args, **kwargs):
            idx = min(mock_execute.call_count - 1, len(states) - 1)
            pct, display = states[idx]
            return (
                display,
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {
                        "path": "/test",
                        "name": "test",
                        "git": {"is_repo": False, "branch": ""}
                    },
                    "context_window": {
                        "max_tokens": 200000,
                        "tokens_used": pct * 2000,
                        "usage_pct": pct
                    }
                })
            )

        mock_execute.side_effect = sensor_side_effect

        agent = ContextAgent(context_threshold=80)
        threshold_events = []

        def track_threshold(event):
            threshold_events.append({
                "old": event.old_value,
                "new": event.new_value,
                "exceeded": event.metadata.get("exceeded")
            })

        agent.on(EventType.CONTEXT_THRESHOLD, track_threshold)

        # Poll through states
        for _ in range(4):
            agent.get_state(force_refresh=True)

        # Should emit once when crossing from 75% to 85%
        assert len(threshold_events) == 1
        assert threshold_events[0]["old"] == 75
        assert threshold_events[0]["new"] == 85
        assert threshold_events[0]["exceeded"] is True


# ============================================================================
# Polling Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestPollingIntegration:
    """Test polling mode integration"""

    @patch.object(ContextAgent, '_execute_sensor')
    def test_polling_detects_changes(self, mock_execute):
        """Test polling mode detects and emits changes"""
        call_count = [0]

        def sensor_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                branch = "main"
            else:
                branch = "feature"

            return (
                f"[Claude] 📁 test 🌿 {branch}",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {
                        "path": "/test",
                        "name": "test",
                        "git": {"is_repo": True, "branch": branch}
                    },
                    "context_window": {
                        "max_tokens": 200000,
                        "tokens_used": 0,
                        "usage_pct": 0
                    }
                })
            )

        mock_execute.side_effect = sensor_side_effect

        agent = ContextAgent()
        events_received = []

        def handler(event):
            events_received.append(event)

        agent.on(EventType.BRANCH_CHANGED, handler)

        # Start polling
        agent.start(polling_interval=0.1)
        time.sleep(0.35)
        agent.stop()

        # Should have detected branch change
        assert len(events_received) > 0
        assert events_received[0].old_value == "main"
        assert events_received[0].new_value == "feature"

    @patch.object(ContextAgent, '_execute_sensor')
    def test_polling_with_multiple_event_types(self, mock_execute):
        """Test polling detects multiple types of changes"""
        call_count = [0]

        def sensor_side_effect(*args, **kwargs):
            call_count[0] += 1

            if call_count[0] == 1:
                model, branch, pct = "Claude", "main", 50
            elif call_count[0] == 2:
                model, branch, pct = "GPT-4", "main", 50
            elif call_count[0] == 3:
                model, branch, pct = "GPT-4", "feature", 50
            else:
                model, branch, pct = "GPT-4", "feature", 85

            return (
                f"[{model}] 📁 test 🌿 {branch} | 📊 {pct}%",
                json.dumps({
                    "version": "1.0.0",
                    "model": model,
                    "workspace": {
                        "path": "/test",
                        "name": "test",
                        "git": {"is_repo": True, "branch": branch}
                    },
                    "context_window": {
                        "max_tokens": 200000,
                        "tokens_used": pct * 2000,
                        "usage_pct": pct
                    }
                })
            )

        mock_execute.side_effect = sensor_side_effect

        agent = ContextAgent(context_threshold=80)

        model_events = []
        branch_events = []
        threshold_events = []

        agent.on(EventType.MODEL_CHANGED, lambda e: model_events.append(e))
        agent.on(EventType.BRANCH_CHANGED, lambda e: branch_events.append(e))
        agent.on(EventType.CONTEXT_THRESHOLD, lambda e: threshold_events.append(e))

        agent.start(polling_interval=0.1)
        time.sleep(0.45)
        agent.stop()

        # Should have detected all change types
        assert len(model_events) > 0
        assert len(branch_events) > 0
        assert len(threshold_events) > 0


# ============================================================================
# Error Recovery Integration Tests
# ============================================================================

@pytest.mark.integration
class TestErrorRecoveryIntegration:
    """Test error recovery and resilience"""

    @patch.object(ContextAgent, '_execute_sensor')
    def test_recovery_from_transient_errors(self, mock_execute):
        """Test agent recovers from transient sensor errors"""
        from src.agent import SensorError

        call_count = [0]

        def sensor_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise SensorError("Transient error")

            return (
                "[Claude] 📁 test",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {
                        "path": "/test",
                        "name": "test",
                        "git": {"is_repo": False, "branch": ""}
                    },
                    "context_window": {
                        "max_tokens": 200000,
                        "tokens_used": 0,
                        "usage_pct": 0
                    }
                })
            )

        mock_execute.side_effect = sensor_side_effect

        agent = ContextAgent()

        # First call succeeds
        state1 = agent.get_state()
        assert state1 is not None

        # Second call fails but returns cached state
        state2 = agent.get_state()
        assert state2 == state1

        # Third call succeeds again
        state3 = agent.get_state()
        assert state3 is not None

    @patch.object(ContextAgent, '_execute_sensor')
    def test_polling_continues_after_errors(self, mock_execute):
        """Test polling continues after encountering errors"""
        from src.agent import SensorError

        call_count = [0]

        def sensor_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise SensorError("Transient error")

            return (
                "[Claude] 📁 test",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {
                        "path": "/test",
                        "name": "test",
                        "git": {"is_repo": False, "branch": ""}
                    },
                    "context_window": {
                        "max_tokens": 200000,
                        "tokens_used": 0,
                        "usage_pct": 0
                    }
                })
            )

        mock_execute.side_effect = sensor_side_effect

        agent = ContextAgent()
        agent.start(polling_interval=0.1)

        time.sleep(0.35)

        agent.stop()

        # Should have continued polling after error
        assert call_count[0] >= 3


# ============================================================================
# Real Sensor Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestRealSensorIntegration:
    """Test with actual sensor script (if available)"""

    def test_real_sensor_execution(self, sensor_script_path, temp_git_repo):
        """Test executing real sensor script"""
        if not sensor_script_path.exists():
            pytest.skip("Sensor script not found")

        # Execute sensor from git repo directory
        result = subprocess.run(
            [str(sensor_script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            input='{}',
            cwd=str(temp_git_repo),
            timeout=5
        )

        assert result.returncode == 0
        assert result.stdout  # Should have display string
        assert result.stderr  # Should have JSON data

        # Verify JSON is parseable
        data = json.loads(result.stderr)
        assert "version" in data
        assert "model" in data
        assert "workspace" in data

    def test_sensor_with_git_detection(self, sensor_script_path, temp_git_repo):
        """Test sensor detects git repository"""
        if not sensor_script_path.exists():
            pytest.skip("Sensor script not found")

        result = subprocess.run(
            [str(sensor_script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            input=json.dumps({"workspace_path": str(temp_git_repo)}),
            cwd=str(temp_git_repo),
            timeout=5
        )

        assert result.returncode == 0

        data = json.loads(result.stderr)
        assert data["workspace"]["git"]["is_repo"] is True
        assert data["workspace"]["git"]["branch"]  # Should have branch name

    def test_sensor_with_non_repo(self, sensor_script_path, temp_non_repo):
        """Test sensor detects non-git directory"""
        if not sensor_script_path.exists():
            pytest.skip("Sensor script not found")

        result = subprocess.run(
            [str(sensor_script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            input=json.dumps({"workspace_path": str(temp_non_repo)}),
            cwd=str(temp_non_repo),
            timeout=5
        )

        assert result.returncode == 0

        data = json.loads(result.stderr)
        assert data["workspace"]["git"]["is_repo"] is False
        assert data["workspace"]["git"]["branch"] == ""


# ============================================================================
# State Consistency Integration Tests
# ============================================================================

@pytest.mark.integration
class TestStateConsistency:
    """Test state consistency across operations"""

    @patch.object(ContextAgent, '_execute_sensor')
    def test_state_consistency_across_methods(self, mock_execute):
        """Test state remains consistent across different access methods"""
        mock_execute.return_value = (
            "[Claude] 📁 test 🌿 main",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {
                    "path": "/test",
                    "name": "test",
                    "git": {"is_repo": True, "branch": "main"}
                },
                "context_window": {
                    "max_tokens": 200000,
                    "tokens_used": 10000,
                    "usage_pct": 5
                }
            })
        )

        agent = ContextAgent()

        # Get state via different methods
        state1 = agent.get_state()
        state2 = agent.current_state
        display = agent.get_display_string()

        # Verify consistency
        assert state1 == state2
        assert state1.display == display

    @patch.object(ContextAgent, '_execute_sensor')
    def test_state_serialization_roundtrip(self, mock_execute):
        """Test state can be serialized and deserialized without data loss"""
        mock_execute.return_value = (
            "[Claude] 📁 test 🌿 main | 📊 13%",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {
                    "path": "/test/path",
                    "name": "test",
                    "git": {"is_repo": True, "branch": "main"}
                },
                "context_window": {
                    "max_tokens": 200000,
                    "tokens_used": 25000,
                    "usage_pct": 13
                }
            })
        )

        agent = ContextAgent()
        original_state = agent.get_state()

        # Serialize
        json_str = original_state.to_json()
        state_dict = json.loads(json_str)

        # Recreate
        recreated_state = AgentState.from_sensor_output(
            state_dict,
            state_dict["display"]
        )

        # Verify key fields match
        assert recreated_state.model == original_state.model
        assert recreated_state.workspace.name == original_state.workspace.name
        assert recreated_state.workspace.git.branch == original_state.workspace.git.branch
        assert recreated_state.context_window.usage_pct == original_state.context_window.usage_pct


# ============================================================================
# Concurrency Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestConcurrencyIntegration:
    """Test concurrent operations"""

    @patch.object(ContextAgent, '_execute_sensor')
    def test_concurrent_state_access(self, mock_execute):
        """Test concurrent state access doesn't cause issues"""
        import threading

        mock_execute.return_value = (
            "[Claude] 📁 test",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {
                    "path": "/test",
                    "name": "test",
                    "git": {"is_repo": False, "branch": ""}
                },
                "context_window": {
                    "max_tokens": 200000,
                    "tokens_used": 0,
                    "usage_pct": 0
                }
            })
        )

        agent = ContextAgent()
        agent.get_state()  # Initialize

        errors = []

        def access_state():
            try:
                for _ in range(10):
                    state = agent.current_state
                    _ = state.to_dict()
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=access_state) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
