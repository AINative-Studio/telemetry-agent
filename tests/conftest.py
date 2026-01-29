"""
Pytest Configuration and Shared Fixtures
"""

import pytest
import json
import subprocess
from typing import Dict, Any
from datetime import datetime
from pathlib import Path


# ============================================================================
# Sensor Output Fixtures
# ============================================================================

@pytest.fixture
def valid_sensor_json() -> Dict[str, Any]:
    """Valid sensor JSON output"""
    return {
        "version": "1.0.0",
        "model": "Claude",
        "workspace": {
            "path": "/Users/test/project",
            "name": "project",
            "git": {
                "is_repo": True,
                "branch": "main"
            }
        },
        "context_window": {
            "max_tokens": 200000,
            "tokens_used": 25000,
            "usage_pct": 13
        }
    }


@pytest.fixture
def partial_sensor_json() -> Dict[str, Any]:
    """Partial sensor JSON (missing some fields)"""
    return {
        "version": "1.0.0",
        "model": "Claude",
        "workspace": {
            "path": "/Users/test/project",
            "name": "project"
        }
    }


@pytest.fixture
def empty_sensor_json() -> Dict[str, Any]:
    """Empty sensor JSON"""
    return {}


@pytest.fixture
def valid_display_string() -> str:
    """Valid display string from sensor"""
    return "[Claude] 📁 project 🌿 main | 📊 13%"


@pytest.fixture
def minimal_display_string() -> str:
    """Minimal display string (model only)"""
    return "[Claude]"


# ============================================================================
# State Fixtures
# ============================================================================

@pytest.fixture
def sample_agent_state():
    """Sample AgentState for testing"""
    from src.state import AgentState, WorkspaceInfo, GitInfo, ContextWindowInfo

    return AgentState(
        agent_type="context",
        agent_version="1.0.0",
        model="Claude",
        workspace=WorkspaceInfo(
            path="/Users/test/project",
            name="project",
            git=GitInfo(is_repo=True, branch="main")
        ),
        context_window=ContextWindowInfo(
            max_tokens=200000,
            tokens_used=25000,
            usage_pct=13
        ),
        display="[Claude] 📁 project 🌿 main | 📊 13%",
        sensor_version="1.0.0"
    )


@pytest.fixture
def modified_agent_state():
    """Modified AgentState for change detection testing"""
    from src.state import AgentState, WorkspaceInfo, GitInfo, ContextWindowInfo

    return AgentState(
        agent_type="context",
        agent_version="1.0.0",
        model="Claude",
        workspace=WorkspaceInfo(
            path="/Users/test/project",
            name="project",
            git=GitInfo(is_repo=True, branch="feature-branch")  # Different branch
        ),
        context_window=ContextWindowInfo(
            max_tokens=200000,
            tokens_used=50000,  # Different usage
            usage_pct=25
        ),
        display="[Claude] 📁 project 🌿 feature-branch | 📊 25%",
        sensor_version="1.0.0"
    )


# ============================================================================
# Event Fixtures
# ============================================================================

@pytest.fixture
def event_emitter():
    """Fresh EventEmitter instance"""
    from src.events import EventEmitter
    return EventEmitter()


@pytest.fixture
def sample_state_change_event():
    """Sample StateChangeEvent"""
    from src.events import StateChangeEvent, EventType

    return StateChangeEvent(
        event_type=EventType.BRANCH_CHANGED,
        timestamp=datetime.utcnow().isoformat(),
        old_value="main",
        new_value="feature-branch",
        metadata={"workspace": "project"}
    )


# ============================================================================
# Sensor Script Fixtures
# ============================================================================

@pytest.fixture
def sensor_script_path() -> Path:
    """Path to the context sensor script"""
    return Path(__file__).parent.parent / "scripts" / "context_sensor.sh"


@pytest.fixture
def mock_sensor_output(valid_sensor_json, valid_display_string):
    """Mock sensor output (stdout and stderr)"""
    return {
        "stdout": valid_display_string,
        "stderr": json.dumps(valid_sensor_json, indent=2),
        "returncode": 0
    }


# ============================================================================
# Mock Helpers
# ============================================================================

class MockSensorResult:
    """Mock subprocess result for sensor execution"""

    def __init__(self, stdout: str, stderr: str, returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


@pytest.fixture
def mock_successful_sensor(mock_sensor_output):
    """Mock successful sensor execution"""
    def _mock(*args, **kwargs):
        return MockSensorResult(
            stdout=mock_sensor_output["stdout"],
            stderr=mock_sensor_output["stderr"],
            returncode=0
        )
    return _mock


@pytest.fixture
def mock_failed_sensor():
    """Mock failed sensor execution"""
    def _mock(*args, **kwargs):
        return MockSensorResult(
            stdout="",
            stderr="Error: jq not found",
            returncode=1
        )
    return _mock


@pytest.fixture
def mock_timeout_sensor():
    """Mock sensor timeout"""
    def _mock(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="sensor", timeout=5)
    return _mock


# ============================================================================
# Git Repository Fixtures
# ============================================================================

@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository for testing"""
    import subprocess

    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True
    )

    # Create initial commit
    (repo_path / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True
    )

    return repo_path


@pytest.fixture
def temp_non_repo(tmp_path):
    """Create a temporary non-git directory"""
    non_repo_path = tmp_path / "non_repo"
    non_repo_path.mkdir()
    return non_repo_path


# ============================================================================
# Freezetime Fixtures
# ============================================================================

@pytest.fixture
def frozen_time():
    """Freeze time for consistent timestamp testing"""
    from freezegun import freeze_time
    frozen = freeze_time("2024-01-15 10:30:00")
    frozen.start()
    yield
    frozen.stop()


# ============================================================================
# Callback Tracking Fixtures
# ============================================================================

class CallbackTracker:
    """Track callback invocations for testing"""

    def __init__(self):
        self.calls = []

    def callback(self, *args, **kwargs):
        """Record callback invocation"""
        self.calls.append({"args": args, "kwargs": kwargs})

    def assert_called_once(self):
        """Assert callback was called exactly once"""
        assert len(self.calls) == 1, f"Expected 1 call, got {len(self.calls)}"

    def assert_called_n_times(self, n: int):
        """Assert callback was called n times"""
        assert len(self.calls) == n, f"Expected {n} calls, got {len(self.calls)}"

    def assert_not_called(self):
        """Assert callback was never called"""
        assert len(self.calls) == 0, f"Expected 0 calls, got {len(self.calls)}"

    def get_call(self, index: int = 0):
        """Get specific call by index"""
        return self.calls[index]


@pytest.fixture
def callback_tracker():
    """Callback tracker instance"""
    return CallbackTracker()
