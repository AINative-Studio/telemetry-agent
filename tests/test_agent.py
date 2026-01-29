"""
Unit Tests for ContextAgent

Tests the interpretation layer including sensor execution,
output parsing, state management, and event emission.
"""

import pytest
import json
import subprocess
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.agent import ContextAgent, SensorError
from src.state import AgentState
from src.events import EventType, StateChangeEvent


class TestContextAgentInitialization:
    """Test ContextAgent initialization"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        agent = ContextAgent()

        assert agent._sensor_timeout == 5.0
        assert agent._context_threshold == 80
        assert agent._enable_events is True
        assert agent._event_emitter is not None
        assert agent._current_state is None
        assert agent._previous_state is None

    def test_init_with_custom_parameters(self):
        """Test initialization with custom parameters"""
        agent = ContextAgent(
            sensor_timeout=10.0,
            context_threshold=90,
            enable_events=False
        )

        assert agent._sensor_timeout == 10.0
        assert agent._context_threshold == 90
        assert agent._enable_events is False
        assert agent._event_emitter is None

    def test_init_with_custom_sensor_path(self, tmp_path):
        """Test initialization with custom sensor path"""
        sensor_script = tmp_path / "custom_sensor.sh"
        sensor_script.write_text("#!/bin/bash\necho 'test'")
        sensor_script.chmod(0o755)

        agent = ContextAgent(sensor_path=str(sensor_script))
        assert agent._sensor_path == sensor_script

    def test_init_with_nonexistent_sensor(self):
        """Test initialization fails with nonexistent sensor"""
        with pytest.raises(FileNotFoundError):
            ContextAgent(sensor_path="/nonexistent/sensor.sh")

    def test_init_sensor_path_is_directory(self, tmp_path):
        """Test initialization fails when sensor path is a directory"""
        with pytest.raises(ValueError, match="not a file"):
            ContextAgent(sensor_path=str(tmp_path))


class TestSensorExecution:
    """Test sensor execution logic"""

    @patch('subprocess.Popen')
    def test_execute_sensor_success(self, mock_popen):
        """Test successful sensor execution"""
        # Setup mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            "[Claude] 📁 test-workspace",
            '{"version": "1.0.0", "model": "Claude"}'
        )
        mock_popen.return_value = mock_process

        agent = ContextAgent()
        stdout, stderr = agent._execute_sensor({"test": "data"})

        assert stdout == "[Claude] 📁 test-workspace"
        assert stderr == '{"version": "1.0.0", "model": "Claude"}'

        # Verify subprocess was called correctly
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[1]['stdin'] == subprocess.PIPE
        assert call_args[1]['stdout'] == subprocess.PIPE
        assert call_args[1]['stderr'] == subprocess.PIPE
        assert call_args[1]['text'] is True

    @patch('subprocess.Popen')
    def test_execute_sensor_with_empty_input(self, mock_popen):
        """Test sensor execution with no input data"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("output", "error")
        mock_popen.return_value = mock_process

        agent = ContextAgent()
        agent._execute_sensor(None)

        # Should pass empty JSON object
        mock_process.communicate.assert_called_once()
        stdin_input = mock_process.communicate.call_args[1]['input']
        assert stdin_input == "{}"

    @patch('subprocess.Popen')
    def test_execute_sensor_timeout(self, mock_popen):
        """Test sensor execution timeout handling"""
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(
            cmd='sensor', timeout=5.0
        )
        mock_process.kill = MagicMock()
        # After kill, communicate returns empty
        def communicate_after_kill(*args, **kwargs):
            if 'timeout' in kwargs:
                raise subprocess.TimeoutExpired(cmd='sensor', timeout=5.0)
            return ("", "")
        mock_process.communicate.side_effect = communicate_after_kill
        mock_popen.return_value = mock_process

        agent = ContextAgent(sensor_timeout=1.0)

        with pytest.raises(SensorError, match="timed out"):
            agent._execute_sensor()

        mock_process.kill.assert_called_once()

    @patch('subprocess.Popen')
    def test_execute_sensor_nonzero_exit_code(self, mock_popen):
        """Test sensor execution with non-zero exit code"""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "Error message")
        mock_popen.return_value = mock_process

        agent = ContextAgent()

        with pytest.raises(SensorError, match="exit code 1"):
            agent._execute_sensor()

    @patch('subprocess.Popen')
    def test_execute_sensor_permission_error(self, mock_popen):
        """Test sensor execution permission error"""
        mock_popen.side_effect = PermissionError("Permission denied")

        agent = ContextAgent()

        with pytest.raises(SensorError, match="Permission denied"):
            agent._execute_sensor()

    @patch('subprocess.Popen')
    def test_execute_sensor_file_not_found(self, mock_popen):
        """Test sensor execution when script not found"""
        mock_popen.side_effect = FileNotFoundError("Script not found")

        agent = ContextAgent()

        with pytest.raises(SensorError, match="not found"):
            agent._execute_sensor()


class TestOutputParsing:
    """Test sensor output parsing"""

    def test_parse_sensor_output_success(self):
        """Test successful parsing of sensor output"""
        agent = ContextAgent()

        stdout = "[Claude] 📁 test-workspace 🌿 main"
        stderr = json.dumps({
            "version": "1.0.0",
            "model": "Claude",
            "workspace": {
                "path": "/test/path",
                "name": "test-workspace",
                "git": {
                    "is_repo": True,
                    "branch": "main"
                }
            },
            "context_window": {
                "max_tokens": 200000,
                "tokens_used": 10000,
                "usage_pct": 5
            }
        })

        state = agent._parse_sensor_output(stdout, stderr)

        assert isinstance(state, AgentState)
        assert state.display == stdout
        assert state.model == "Claude"
        assert state.workspace.name == "test-workspace"
        assert state.workspace.git.branch == "main"
        assert state.context_window.usage_pct == 5

    def test_parse_sensor_output_empty_stderr(self):
        """Test parsing with empty STDERR (no JSON data)"""
        agent = ContextAgent()

        stdout = "[Claude] 📁 test-workspace"
        stderr = ""

        state = agent._parse_sensor_output(stdout, stderr)

        # Should create partial state with defaults
        assert isinstance(state, AgentState)
        assert state.display == stdout

    def test_parse_sensor_output_invalid_json(self):
        """Test parsing with invalid JSON in STDERR"""
        agent = ContextAgent()

        stdout = "[Claude] 📁 test-workspace"
        stderr = "{ invalid json }"

        # Should not raise error, return partial state
        state = agent._parse_sensor_output(stdout, stderr)

        assert isinstance(state, AgentState)
        assert "error" in state.display.lower() or state.display == stdout

    def test_parse_sensor_output_missing_fields(self):
        """Test parsing with missing fields in JSON"""
        agent = ContextAgent()

        stdout = "[Claude]"
        stderr = json.dumps({
            "version": "1.0.0"
            # Missing all other fields
        })

        # Should create partial state with defaults
        state = agent._parse_sensor_output(stdout, stderr)

        assert isinstance(state, AgentState)
        assert state.model == "Claude"  # Default value
        assert state.workspace.name == ""  # Default value


class TestStateManagement:
    """Test state management and change detection"""

    @patch.object(ContextAgent, '_execute_sensor')
    def test_get_state_success(self, mock_execute):
        """Test successful state retrieval"""
        mock_execute.return_value = (
            "[Claude] 📁 test",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
            })
        )

        agent = ContextAgent()
        state = agent.get_state()

        assert isinstance(state, AgentState)
        assert agent._current_state == state
        mock_execute.assert_called_once()

    @patch.object(ContextAgent, '_execute_sensor')
    def test_get_state_cached(self, mock_execute):
        """Test cached state retrieval without force_refresh"""
        mock_execute.return_value = (
            "[Claude] 📁 test",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
            })
        )

        agent = ContextAgent()
        state1 = agent.get_state()
        state2 = agent.get_state(force_refresh=False)

        assert state1 == state2
        # Should only call sensor once
        assert mock_execute.call_count == 1

    @patch.object(ContextAgent, '_execute_sensor')
    def test_get_state_sensor_failure_with_cache(self, mock_execute):
        """Test sensor failure with cached state returns cache"""
        # First call succeeds
        mock_execute.return_value = (
            "[Claude] 📁 test",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
            })
        )

        agent = ContextAgent()
        state1 = agent.get_state()

        # Second call fails
        mock_execute.side_effect = SensorError("Sensor failed")

        state2 = agent.get_state()

        # Should return cached state
        assert state1 == state2

    @patch.object(ContextAgent, '_execute_sensor')
    def test_get_state_sensor_failure_no_cache(self, mock_execute):
        """Test sensor failure without cached state raises error"""
        mock_execute.side_effect = SensorError("Sensor failed")

        agent = ContextAgent()

        with pytest.raises(SensorError):
            agent.get_state()

    @patch.object(ContextAgent, '_execute_sensor')
    def test_get_display_string(self, mock_execute):
        """Test display string retrieval"""
        mock_execute.return_value = (
            "[Claude] 📁 test 🌿 main",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {"path": "/test", "name": "test", "git": {"is_repo": True, "branch": "main"}},
                "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
            })
        )

        agent = ContextAgent()
        display = agent.get_display_string()

        assert display == "[Claude] 📁 test 🌿 main"


class TestEventEmission:
    """Test event emission on state changes"""

    @patch.object(ContextAgent, '_execute_sensor')
    def test_event_emission_model_changed(self, mock_execute):
        """Test MODEL_CHANGED event emission"""
        # Setup two different states
        mock_execute.side_effect = [
            (
                "[Claude] 📁 test",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                    "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
                })
            ),
            (
                "[GPT-4] 📁 test",
                json.dumps({
                    "version": "1.0.0",
                    "model": "GPT-4",
                    "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                    "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
                })
            )
        ]

        agent = ContextAgent()
        handler = Mock()
        agent.on(EventType.MODEL_CHANGED, handler)

        agent.get_state()  # First state
        agent.get_state()  # Second state

        # Verify event was emitted
        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert event.event_type == EventType.MODEL_CHANGED
        assert event.old_value == "Claude"
        assert event.new_value == "GPT-4"

    @patch.object(ContextAgent, '_execute_sensor')
    def test_event_emission_branch_changed(self, mock_execute):
        """Test BRANCH_CHANGED event emission"""
        mock_execute.side_effect = [
            (
                "[Claude] 📁 test 🌿 main",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {"path": "/test", "name": "test", "git": {"is_repo": True, "branch": "main"}},
                    "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
                })
            ),
            (
                "[Claude] 📁 test 🌿 feature",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {"path": "/test", "name": "test", "git": {"is_repo": True, "branch": "feature"}},
                    "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
                })
            )
        ]

        agent = ContextAgent()
        handler = Mock()
        agent.on(EventType.BRANCH_CHANGED, handler)

        agent.get_state()
        agent.get_state()

        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert event.event_type == EventType.BRANCH_CHANGED
        assert event.old_value == "main"
        assert event.new_value == "feature"

    @patch.object(ContextAgent, '_execute_sensor')
    def test_event_emission_context_threshold(self, mock_execute):
        """Test CONTEXT_THRESHOLD event emission"""
        mock_execute.side_effect = [
            (
                "[Claude] 📁 test | 📊 70%",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                    "context_window": {"max_tokens": 200000, "tokens_used": 140000, "usage_pct": 70}
                })
            ),
            (
                "[Claude] 📁 test | 📊 85%",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                    "context_window": {"max_tokens": 200000, "tokens_used": 170000, "usage_pct": 85}
                })
            )
        ]

        agent = ContextAgent(context_threshold=80)
        handler = Mock()
        agent.on(EventType.CONTEXT_THRESHOLD, handler)

        agent.get_state()  # 70% - below threshold
        agent.get_state()  # 85% - above threshold

        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert event.event_type == EventType.CONTEXT_THRESHOLD
        assert event.old_value == 70
        assert event.new_value == 85
        assert event.metadata["threshold"] == 80

    @patch.object(ContextAgent, '_execute_sensor')
    def test_event_emission_disabled(self, mock_execute):
        """Test no events emitted when events disabled"""
        mock_execute.return_value = (
            "[Claude] 📁 test",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
            })
        )

        agent = ContextAgent(enable_events=False)
        handler = Mock()

        # Should log warning
        agent.on(EventType.STATE_UPDATED, handler)

        agent.get_state()

        # No events should be emitted
        handler.assert_not_called()


class TestPublicAPI:
    """Test public API properties and methods"""

    @patch.object(ContextAgent, '_execute_sensor')
    def test_current_state_property(self, mock_execute):
        """Test current_state property"""
        mock_execute.return_value = (
            "[Claude] 📁 test",
            json.dumps({
                "version": "1.0.0",
                "model": "Claude",
                "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
            })
        )

        agent = ContextAgent()

        assert agent.current_state is None

        state = agent.get_state()
        assert agent.current_state == state

    @patch.object(ContextAgent, '_execute_sensor')
    def test_previous_state_property(self, mock_execute):
        """Test previous_state property"""
        mock_execute.side_effect = [
            (
                "[Claude] 📁 test",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                    "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
                })
            ),
            (
                "[Claude] 📁 test2",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {"path": "/test2", "name": "test2", "git": {"is_repo": False, "branch": ""}},
                    "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}
                })
            )
        ]

        agent = ContextAgent()

        assert agent.previous_state is None

        state1 = agent.get_state()
        assert agent.previous_state is None

        state2 = agent.get_state()
        assert agent.previous_state == state1
        assert agent.current_state == state2

    def test_event_emitter_property(self):
        """Test event_emitter property"""
        agent = ContextAgent(enable_events=True)
        assert agent.event_emitter is not None

        agent_no_events = ContextAgent(enable_events=False)
        assert agent_no_events.event_emitter is None

    def test_on_method(self):
        """Test on() method for event registration"""
        agent = ContextAgent()
        handler = Mock()

        agent.on(EventType.MODEL_CHANGED, handler)

        # Verify handler was registered
        assert handler in agent._event_emitter._handlers[EventType.MODEL_CHANGED]

    def test_off_method(self):
        """Test off() method for event deregistration"""
        agent = ContextAgent()
        handler = Mock()

        agent.on(EventType.MODEL_CHANGED, handler)
        agent.off(EventType.MODEL_CHANGED, handler)

        # Verify handler was removed
        assert handler not in agent._event_emitter._handlers[EventType.MODEL_CHANGED]


class TestExceptionHandling:
    """Test exception handling in parsing and execution"""

    @patch('subprocess.Popen')
    def test_execute_sensor_unexpected_exception(self, mock_popen):
        """Test handling of unexpected exceptions during sensor execution"""
        # Simulate unexpected exception
        mock_popen.side_effect = RuntimeError("Unexpected error")

        agent = ContextAgent()

        with pytest.raises(SensorError, match="Unexpected error"):
            agent._execute_sensor()

    def test_parse_sensor_output_generic_exception(self):
        """Test handling of generic exceptions during parsing"""
        agent = ContextAgent()

        # Simulate exception during parsing by passing invalid type
        # This is a bit contrived but tests the generic exception handler
        stdout = "[Claude] test"
        stderr = '{"version": "1.0.0"}'

        # Mock AgentState.from_sensor_output to raise exception
        with patch('src.agent.AgentState.from_sensor_output', side_effect=ValueError("Parse error")):
            state = agent._parse_sensor_output(stdout, stderr)

            # Should return partial state
            assert isinstance(state, AgentState)
            assert "error" in state.display.lower()


class TestPollingFunctionality:
    """Test polling and background execution"""

    @patch.object(ContextAgent, '_execute_sensor')
    def test_start_polling(self, mock_execute):
        """Test starting polling mode"""
        mock_execute.return_value = (
            "[Claude] test",
            '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": false, "branch": ""}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
        )

        agent = ContextAgent()
        agent.start(polling_interval=0.1)

        # Verify polling started
        assert agent.is_running()
        assert agent._polling

        # Stop agent
        agent.stop()

        # Verify stopped
        assert not agent.is_running()

    @patch.object(ContextAgent, '_execute_sensor')
    def test_start_polling_already_running(self, mock_execute):
        """Test error when starting already-running agent"""
        mock_execute.return_value = (
            "[Claude] test",
            '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": false, "branch": ""}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
        )

        agent = ContextAgent()
        agent.start(polling_interval=0.1)

        try:
            with pytest.raises(RuntimeError, match="already running"):
                agent.start(polling_interval=0.1)
        finally:
            agent.stop()

    @patch.object(ContextAgent, '_execute_sensor')
    def test_stop_when_not_running(self, mock_execute):
        """Test stopping when agent is not running"""
        agent = ContextAgent()

        # Should not raise error
        agent.stop()

    @patch.object(ContextAgent, '_execute_sensor')
    def test_poll_loop_sensor_error(self, mock_execute):
        """Test poll loop continues after sensor error"""
        # Setup: First call succeeds (for initialization), second fails, third succeeds
        mock_execute.side_effect = [
            (
                "[Claude] test",
                '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": false, "branch": ""}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
            ),
            SensorError("Sensor failed"),
            (
                "[Claude] test",
                '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": false, "branch": ""}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
            )
        ]

        agent = ContextAgent()
        agent.start(polling_interval=0.1)

        # Wait for a couple polls
        time.sleep(0.3)

        # Should still be running despite poll error
        assert agent.is_running()

        agent.stop()

    @patch.object(ContextAgent, '_execute_sensor')
    def test_poll_loop_unexpected_error(self, mock_execute):
        """Test poll loop continues after unexpected error"""
        # Setup: First call succeeds (for initialization), second raises error, third succeeds
        mock_execute.side_effect = [
            (
                "[Claude] test",
                '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": false, "branch": ""}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
            ),
            RuntimeError("Unexpected error"),
            (
                "[Claude] test",
                '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": false, "branch": ""}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
            )
        ]

        agent = ContextAgent()
        agent.start(polling_interval=0.1)

        # Wait for a couple polls
        time.sleep(0.3)

        # Should still be running despite poll error
        assert agent.is_running()

        agent.stop()

    @patch.object(ContextAgent, '_execute_sensor')
    def test_is_running_property(self, mock_execute):
        """Test is_running property"""
        mock_execute.return_value = (
            "[Claude] test",
            '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": false, "branch": ""}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
        )

        agent = ContextAgent()

        assert not agent.is_running()

        agent.start(polling_interval=0.1)

        assert agent.is_running()

        agent.stop()

        assert not agent.is_running()

    @patch.object(ContextAgent, '_execute_sensor')
    def test_polling_executes_repeatedly(self, mock_execute):
        """Test that polling executes sensor at regular intervals"""
        mock_execute.return_value = (
            "[Claude] test",
            '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": false, "branch": ""}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
        )

        agent = ContextAgent()
        agent.start(polling_interval=0.1)

        # Wait for multiple polls
        time.sleep(0.35)

        agent.stop()

        # Should have polled at least 3 times
        assert mock_execute.call_count >= 3

    @patch.object(ContextAgent, '_execute_sensor')
    def test_polling_emits_change_events(self, mock_execute):
        """Test that polling detects and emits change events"""
        call_count = [0]

        def sensor_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                return (
                    "[Claude] test 🌿 main",
                    '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": true, "branch": "main"}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
                )
            else:
                return (
                    "[Claude] test 🌿 feature",
                    '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": true, "branch": "feature"}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
                )

        mock_execute.side_effect = sensor_side_effect

        agent = ContextAgent()
        handler = Mock()
        agent.on(EventType.BRANCH_CHANGED, handler)

        agent.start(polling_interval=0.1)

        # Wait for change to be detected
        time.sleep(0.35)

        agent.stop()

        # Verify event was emitted
        handler.assert_called()
        event = handler.call_args[0][0]
        assert event.event_type == EventType.BRANCH_CHANGED
        assert event.old_value == "main"
        assert event.new_value == "feature"

    @patch.object(ContextAgent, '_execute_sensor')
    def test_context_threshold_emits_once_when_crossing(self, mock_execute):
        """Test context threshold event emits only once when crossing threshold"""
        call_count = [0]

        def sensor_side_effect(*args, **kwargs):
            call_count[0] += 1
            # 70, 85, 90, 92, 95 - crosses at second call
            usage_pct = min(70 + (call_count[0] - 1) * 15, 95)

            return (
                f"[Claude] test | 📊 {usage_pct}%",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                    "context_window": {"max_tokens": 200000, "tokens_used": usage_pct * 2000, "usage_pct": usage_pct}
                })
            )

        mock_execute.side_effect = sensor_side_effect

        agent = ContextAgent(context_threshold=80)
        handler = Mock()
        agent.on(EventType.CONTEXT_THRESHOLD, handler)

        agent.start(polling_interval=0.1)

        # Wait for multiple polls to cross threshold
        time.sleep(0.55)

        agent.stop()

        # Should only emit once when crossing from 70 to 85
        assert handler.call_count == 1
        event = handler.call_args[0][0]
        assert event.metadata["threshold"] == 80
        assert event.metadata["exceeded"] is True
        assert event.old_value == 70
        assert event.new_value == 85

    @patch.object(ContextAgent, '_execute_sensor')
    def test_context_threshold_resets_when_dropping_below(self, mock_execute):
        """Test threshold flag resets when usage drops below threshold"""
        call_count = [0]

        def sensor_side_effect(*args, **kwargs):
            call_count[0] += 1
            # 70, 85, 90, 75, 85 - crosses at 2nd and 5th calls
            usage_values = [70, 85, 90, 75, 85]
            usage_pct = usage_values[min(call_count[0] - 1, len(usage_values) - 1)]

            return (
                f"[Claude] test | 📊 {usage_pct}%",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                    "context_window": {"max_tokens": 200000, "tokens_used": usage_pct * 2000, "usage_pct": usage_pct}
                })
            )

        mock_execute.side_effect = sensor_side_effect

        agent = ContextAgent(context_threshold=80)
        handler = Mock()
        agent.on(EventType.CONTEXT_THRESHOLD, handler)

        agent.start(polling_interval=0.1)

        # Wait for all transitions
        time.sleep(0.55)

        agent.stop()

        # Should emit twice: 70->85 and 75->85
        assert handler.call_count == 2

    @patch.object(ContextAgent, '_execute_sensor')
    def test_thread_safety_during_polling(self, mock_execute):
        """Test thread safety with concurrent state access during polling"""
        mock_execute.return_value = (
            "[Claude] test",
            '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": false, "branch": ""}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
        )

        agent = ContextAgent()
        agent.start(polling_interval=0.05)

        errors = []

        def read_state():
            try:
                for _ in range(10):
                    state = agent.current_state
                    if state:
                        _ = state.to_dict()
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        # Create multiple threads accessing state concurrently
        threads = [threading.Thread(target=read_state) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        agent.stop()

        # No errors should occur due to thread safety
        assert len(errors) == 0

    @patch.object(ContextAgent, '_execute_sensor')
    def test_context_manager_ensures_cleanup(self, mock_execute):
        """Test context manager stops polling on exit"""
        mock_execute.return_value = (
            "[Claude] test",
            '{"version": "1.0.0", "model": "Claude", "workspace": {"path": "/test", "name": "test", "git": {"is_repo": false, "branch": ""}}, "context_window": {"max_tokens": 200000, "tokens_used": 0, "usage_pct": 0}}'
        )

        with ContextAgent() as agent:
            agent.start(polling_interval=0.1)
            assert agent.is_running()

        # Should be stopped after context exit
        assert not agent.is_running()

    @patch.object(ContextAgent, '_execute_sensor')
    def test_threshold_with_custom_value(self, mock_execute):
        """Test custom threshold value"""
        call_count = [0]

        def sensor_side_effect(*args, **kwargs):
            call_count[0] += 1
            usage_pct = 85 if call_count[0] == 1 else 92

            return (
                f"[Claude] test | 📊 {usage_pct}%",
                json.dumps({
                    "version": "1.0.0",
                    "model": "Claude",
                    "workspace": {"path": "/test", "name": "test", "git": {"is_repo": False, "branch": ""}},
                    "context_window": {"max_tokens": 200000, "tokens_used": usage_pct * 2000, "usage_pct": usage_pct}
                })
            )

        mock_execute.side_effect = sensor_side_effect

        # Set threshold at 90%
        agent = ContextAgent(context_threshold=90)
        handler = Mock()
        agent.on(EventType.CONTEXT_THRESHOLD, handler)

        agent.start(polling_interval=0.1)
        time.sleep(0.25)
        agent.stop()

        # Should emit when crossing 90%
        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert event.metadata["threshold"] == 90
        assert event.old_value == 85
        assert event.new_value == 92
