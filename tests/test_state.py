"""
Comprehensive unit tests for state management module.

Tests all classes, methods, edge cases, and integration scenarios.
"""

import pytest
import json
from datetime import datetime
from src.state import AgentState, WorkspaceInfo, GitInfo, ContextWindowInfo


class TestGitInfo:
    """Test GitInfo dataclass"""

    def test_default_initialization(self):
        """Test GitInfo with default values"""
        git = GitInfo()
        assert git.is_repo is False
        assert git.branch == ""

    def test_custom_initialization(self):
        """Test GitInfo with custom values"""
        git = GitInfo(is_repo=True, branch="main")
        assert git.is_repo is True
        assert git.branch == "main"

    def test_to_dict(self):
        """Test GitInfo.to_dict() serialization"""
        git = GitInfo(is_repo=True, branch="develop")
        result = git.to_dict()

        assert isinstance(result, dict)
        assert result["is_repo"] is True
        assert result["branch"] == "develop"

    def test_to_dict_defaults(self):
        """Test GitInfo.to_dict() with default values"""
        git = GitInfo()
        result = git.to_dict()

        assert result["is_repo"] is False
        assert result["branch"] == ""

    def test_equality(self):
        """Test GitInfo equality comparison"""
        git1 = GitInfo(is_repo=True, branch="main")
        git2 = GitInfo(is_repo=True, branch="main")
        git3 = GitInfo(is_repo=False, branch="main")

        assert git1 == git2
        assert git1 != git3

    def test_repr(self):
        """Test GitInfo string representation"""
        git = GitInfo(is_repo=True, branch="main")
        repr_str = repr(git)

        assert "GitInfo" in repr_str
        assert "is_repo=True" in repr_str
        assert "branch='main'" in repr_str


class TestWorkspaceInfo:
    """Test WorkspaceInfo dataclass"""

    def test_default_initialization(self):
        """Test WorkspaceInfo with default values"""
        workspace = WorkspaceInfo()

        assert workspace.path == ""
        assert workspace.name == ""
        assert isinstance(workspace.git, GitInfo)
        assert workspace.git.is_repo is False

    def test_custom_initialization(self):
        """Test WorkspaceInfo with custom values"""
        git = GitInfo(is_repo=True, branch="feature")
        workspace = WorkspaceInfo(
            path="/home/user/project",
            name="my-project",
            git=git
        )

        assert workspace.path == "/home/user/project"
        assert workspace.name == "my-project"
        assert workspace.git.branch == "feature"

    def test_to_dict(self):
        """Test WorkspaceInfo.to_dict() serialization"""
        git = GitInfo(is_repo=True, branch="main")
        workspace = WorkspaceInfo(
            path="/test/path",
            name="test-project",
            git=git
        )
        result = workspace.to_dict()

        assert isinstance(result, dict)
        assert result["path"] == "/test/path"
        assert result["name"] == "test-project"
        assert isinstance(result["git"], dict)
        assert result["git"]["is_repo"] is True
        assert result["git"]["branch"] == "main"

    def test_to_dict_nested(self):
        """Test WorkspaceInfo.to_dict() properly nests GitInfo"""
        workspace = WorkspaceInfo()
        result = workspace.to_dict()

        assert "git" in result
        assert isinstance(result["git"], dict)
        assert "is_repo" in result["git"]

    def test_equality(self):
        """Test WorkspaceInfo equality comparison"""
        git1 = GitInfo(is_repo=True, branch="main")
        git2 = GitInfo(is_repo=True, branch="main")
        git3 = GitInfo(is_repo=False, branch="dev")

        workspace1 = WorkspaceInfo(path="/path", name="proj", git=git1)
        workspace2 = WorkspaceInfo(path="/path", name="proj", git=git2)
        workspace3 = WorkspaceInfo(path="/other", name="proj", git=git3)

        assert workspace1 == workspace2
        assert workspace1 != workspace3


class TestContextWindowInfo:
    """Test ContextWindowInfo dataclass"""

    def test_default_initialization(self):
        """Test ContextWindowInfo with default values"""
        context = ContextWindowInfo()

        assert context.max_tokens == 200000
        assert context.tokens_used == 0
        assert context.usage_pct == 0

    def test_custom_initialization(self):
        """Test ContextWindowInfo with custom values"""
        context = ContextWindowInfo(
            max_tokens=100000,
            tokens_used=25000,
            usage_pct=25
        )

        assert context.max_tokens == 100000
        assert context.tokens_used == 25000
        assert context.usage_pct == 25

    def test_to_dict(self):
        """Test ContextWindowInfo.to_dict() serialization"""
        context = ContextWindowInfo(
            max_tokens=150000,
            tokens_used=30000,
            usage_pct=20
        )
        result = context.to_dict()

        assert isinstance(result, dict)
        assert result["max_tokens"] == 150000
        assert result["tokens_used"] == 30000
        assert result["usage_pct"] == 20

    def test_equality(self):
        """Test ContextWindowInfo equality comparison"""
        ctx1 = ContextWindowInfo(max_tokens=100000, tokens_used=50000, usage_pct=50)
        ctx2 = ContextWindowInfo(max_tokens=100000, tokens_used=50000, usage_pct=50)
        ctx3 = ContextWindowInfo(max_tokens=100000, tokens_used=60000, usage_pct=60)

        assert ctx1 == ctx2
        assert ctx1 != ctx3


class TestAgentState:
    """Test AgentState dataclass"""

    def test_default_initialization(self):
        """Test AgentState with default values"""
        state = AgentState()

        assert state.agent_type == "context"
        assert state.agent_version == "1.0.0"
        assert state.model == "Claude"
        assert isinstance(state.workspace, WorkspaceInfo)
        assert isinstance(state.context_window, ContextWindowInfo)
        assert state.display == ""
        assert state.sensor_version == "1.0.0"
        # last_updated should be a valid ISO timestamp
        datetime.fromisoformat(state.last_updated)

    def test_custom_initialization(self):
        """Test AgentState with custom values"""
        workspace = WorkspaceInfo(path="/custom", name="custom-proj")
        context = ContextWindowInfo(max_tokens=100000, tokens_used=10000, usage_pct=10)

        state = AgentState(
            model="GPT-4",
            workspace=workspace,
            context_window=context,
            display="Custom Display",
            sensor_version="2.0.0"
        )

        assert state.model == "GPT-4"
        assert state.workspace.name == "custom-proj"
        assert state.context_window.usage_pct == 10
        assert state.display == "Custom Display"
        assert state.sensor_version == "2.0.0"

    def test_to_dict(self):
        """Test AgentState.to_dict() serialization"""
        state = AgentState()
        result = state.to_dict()

        assert isinstance(result, dict)
        assert result["agent_type"] == "context"
        assert result["agent_version"] == "1.0.0"
        assert result["model"] == "Claude"
        assert isinstance(result["workspace"], dict)
        assert isinstance(result["context_window"], dict)
        assert "last_updated" in result
        assert "sensor_version" in result

    def test_to_json(self):
        """Test AgentState.to_json() serialization"""
        state = AgentState()
        result = state.to_json()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["agent_type"] == "context"
        assert parsed["model"] == "Claude"

    def test_to_json_pretty_formatted(self):
        """Test AgentState.to_json() produces formatted JSON"""
        state = AgentState()
        result = state.to_json()

        # Should be pretty-printed with indentation
        assert "\n" in result
        assert "  " in result

    def test_from_sensor_output_full_data(self):
        """Test from_sensor_output with complete sensor data"""
        sensor_data = {
            "model": "GPT-4",
            "workspace": {
                "path": "/home/user/project",
                "name": "my-project",
                "git": {
                    "is_repo": True,
                    "branch": "main"
                }
            },
            "context_window": {
                "max_tokens": 150000,
                "tokens_used": 30000,
                "usage_pct": 20
            },
            "version": "1.5.0"
        }
        display_string = "  [GPT-4] my-project (main)  \n"

        state = AgentState.from_sensor_output(sensor_data, display_string)

        assert state.model == "GPT-4"
        assert state.workspace.path == "/home/user/project"
        assert state.workspace.name == "my-project"
        assert state.workspace.git.is_repo is True
        assert state.workspace.git.branch == "main"
        assert state.context_window.max_tokens == 150000
        assert state.context_window.tokens_used == 30000
        assert state.context_window.usage_pct == 20
        assert state.display == "[GPT-4] my-project (main)"  # Stripped
        assert state.sensor_version == "1.5.0"

    def test_from_sensor_output_partial_data(self):
        """Test from_sensor_output with partial sensor data"""
        sensor_data = {
            "model": "Claude",
            "workspace": {
                "name": "test-project"
            }
        }
        display_string = "Test Display"

        state = AgentState.from_sensor_output(sensor_data, display_string)

        assert state.model == "Claude"
        assert state.workspace.name == "test-project"
        assert state.workspace.path == ""  # Default
        assert state.workspace.git.is_repo is False  # Default
        assert state.context_window.max_tokens == 200000  # Default
        assert state.display == "Test Display"

    def test_from_sensor_output_empty_data(self):
        """Test from_sensor_output with empty sensor data"""
        sensor_data = {}
        display_string = ""

        state = AgentState.from_sensor_output(sensor_data, display_string)

        assert state.model == "Claude"  # Default
        assert state.workspace.path == ""
        assert state.workspace.name == ""
        assert state.workspace.git.is_repo is False
        assert state.display == ""

    def test_from_sensor_output_missing_nested_keys(self):
        """Test from_sensor_output handles missing nested keys"""
        sensor_data = {
            "workspace": {},
            "context_window": {}
        }
        display_string = "Test"

        state = AgentState.from_sensor_output(sensor_data, display_string)

        assert state.workspace.path == ""
        assert state.workspace.name == ""
        assert state.workspace.git.is_repo is False
        assert state.context_window.max_tokens == 200000

    def test_has_changed_no_previous_state(self):
        """Test has_changed with None previous state"""
        state = AgentState()

        assert state.has_changed(None) is True

    def test_has_changed_identical_states(self):
        """Test has_changed with identical states"""
        state1 = AgentState(model="Claude")
        state2 = AgentState(model="Claude")

        assert state1.has_changed(state2) is False

    def test_has_changed_model_changed(self):
        """Test has_changed detects model change"""
        state1 = AgentState(model="Claude")
        state2 = AgentState(model="GPT-4")

        assert state1.has_changed(state2) is True

    def test_has_changed_workspace_name_changed(self):
        """Test has_changed detects workspace name change"""
        workspace1 = WorkspaceInfo(name="project-a")
        workspace2 = WorkspaceInfo(name="project-b")

        state1 = AgentState(workspace=workspace1)
        state2 = AgentState(workspace=workspace2)

        assert state1.has_changed(state2) is True

    def test_has_changed_branch_changed(self):
        """Test has_changed detects branch change"""
        git1 = GitInfo(is_repo=True, branch="main")
        git2 = GitInfo(is_repo=True, branch="develop")
        workspace1 = WorkspaceInfo(git=git1)
        workspace2 = WorkspaceInfo(git=git2)

        state1 = AgentState(workspace=workspace1)
        state2 = AgentState(workspace=workspace2)

        assert state1.has_changed(state2) is True

    def test_has_changed_context_usage_changed(self):
        """Test has_changed detects context usage change"""
        context1 = ContextWindowInfo(usage_pct=10)
        context2 = ContextWindowInfo(usage_pct=50)

        state1 = AgentState(context_window=context1)
        state2 = AgentState(context_window=context2)

        assert state1.has_changed(state2) is True

    def test_has_changed_workspace_path_changed(self):
        """Test has_changed detects workspace path change"""
        workspace1 = WorkspaceInfo(path="/old/path", name="project")
        workspace2 = WorkspaceInfo(path="/new/path", name="project")

        state1 = AgentState(workspace=workspace1)
        state2 = AgentState(workspace=workspace2)

        assert state1.has_changed(state2) is True

    def test_has_changed_ignores_timestamp(self):
        """Test has_changed ignores timestamp differences"""
        state1 = AgentState(model="Claude")
        # Simulate different timestamps by recreating
        import time
        time.sleep(0.01)
        state2 = AgentState(model="Claude")

        # Timestamps are different but state hasn't changed
        assert state1.last_updated != state2.last_updated
        assert state1.has_changed(state2) is False

    def test_get_changes_no_previous_state(self):
        """Test get_changes with None previous state"""
        state = AgentState()
        changes = state.get_changes(None)

        assert changes == {"initial": True}

    def test_get_changes_no_changes(self):
        """Test get_changes with identical states"""
        state1 = AgentState(model="Claude")
        state2 = AgentState(model="Claude")

        changes = state1.get_changes(state2)

        assert changes == {}

    def test_get_changes_model_changed(self):
        """Test get_changes detects model change"""
        state1 = AgentState(model="GPT-4")
        state2 = AgentState(model="Claude")

        changes = state1.get_changes(state2)

        assert "model" in changes
        assert changes["model"]["old"] == "Claude"
        assert changes["model"]["new"] == "GPT-4"

    def test_get_changes_workspace_changed(self):
        """Test get_changes detects workspace change"""
        workspace1 = WorkspaceInfo(name="project-new")
        workspace2 = WorkspaceInfo(name="project-old")

        state1 = AgentState(workspace=workspace1)
        state2 = AgentState(workspace=workspace2)

        changes = state1.get_changes(state2)

        assert "workspace" in changes
        assert changes["workspace"]["old"] == "project-old"
        assert changes["workspace"]["new"] == "project-new"

    def test_get_changes_branch_changed(self):
        """Test get_changes detects branch change"""
        git1 = GitInfo(is_repo=True, branch="feature")
        git2 = GitInfo(is_repo=True, branch="main")
        workspace1 = WorkspaceInfo(git=git1)
        workspace2 = WorkspaceInfo(git=git2)

        state1 = AgentState(workspace=workspace1)
        state2 = AgentState(workspace=workspace2)

        changes = state1.get_changes(state2)

        assert "branch" in changes
        assert changes["branch"]["old"] == "main"
        assert changes["branch"]["new"] == "feature"

    def test_get_changes_context_usage_changed(self):
        """Test get_changes detects context usage change"""
        context1 = ContextWindowInfo(usage_pct=75)
        context2 = ContextWindowInfo(usage_pct=25)

        state1 = AgentState(context_window=context1)
        state2 = AgentState(context_window=context2)

        changes = state1.get_changes(state2)

        assert "context_usage" in changes
        assert changes["context_usage"]["old"] == 25
        assert changes["context_usage"]["new"] == 75

    def test_get_changes_workspace_path_changed(self):
        """Test get_changes detects workspace path change"""
        workspace1 = WorkspaceInfo(path="/new/path", name="project")
        workspace2 = WorkspaceInfo(path="/old/path", name="project")

        state1 = AgentState(workspace=workspace1)
        state2 = AgentState(workspace=workspace2)

        changes = state1.get_changes(state2)

        assert "workspace_path" in changes
        assert changes["workspace_path"]["old"] == "/old/path"
        assert changes["workspace_path"]["new"] == "/new/path"

    def test_get_changes_multiple_changes(self):
        """Test get_changes detects multiple simultaneous changes"""
        git1 = GitInfo(is_repo=True, branch="dev")
        git2 = GitInfo(is_repo=True, branch="main")
        workspace1 = WorkspaceInfo(name="new-proj", git=git1)
        workspace2 = WorkspaceInfo(name="old-proj", git=git2)
        context1 = ContextWindowInfo(usage_pct=80)
        context2 = ContextWindowInfo(usage_pct=20)

        state1 = AgentState(
            model="GPT-4",
            workspace=workspace1,
            context_window=context1
        )
        state2 = AgentState(
            model="Claude",
            workspace=workspace2,
            context_window=context2
        )

        changes = state1.get_changes(state2)

        assert len(changes) == 4
        assert "model" in changes
        assert "workspace" in changes
        assert "branch" in changes
        assert "context_usage" in changes


class TestStateIntegration:
    """Integration tests for state management"""

    def test_round_trip_serialization(self):
        """Test state can be serialized and deserialized"""
        original = AgentState(
            model="Claude",
            workspace=WorkspaceInfo(
                path="/test",
                name="test-proj",
                git=GitInfo(is_repo=True, branch="main")
            ),
            context_window=ContextWindowInfo(
                max_tokens=100000,
                tokens_used=25000,
                usage_pct=25
            ),
            display="Test Display"
        )

        # Serialize
        json_str = original.to_json()
        data_dict = json.loads(json_str)

        # Recreate from dict (simulating sensor output)
        recreated = AgentState.from_sensor_output(data_dict, data_dict["display"])

        # Verify key fields match (timestamps will differ)
        assert recreated.model == original.model
        assert recreated.workspace.name == original.workspace.name
        assert recreated.workspace.git.branch == original.workspace.git.branch
        assert recreated.context_window.usage_pct == original.context_window.usage_pct

    def test_state_change_workflow(self):
        """Test typical state change detection workflow"""
        # Initial state
        state1 = AgentState(
            model="Claude",
            workspace=WorkspaceInfo(name="project-a")
        )

        # User switches branch
        git = GitInfo(is_repo=True, branch="develop")
        workspace = WorkspaceInfo(name="project-a", git=git)
        state2 = AgentState(model="Claude", workspace=workspace)

        # Detect change
        assert state2.has_changed(state1) is True
        changes = state2.get_changes(state1)
        assert "branch" in changes
        assert changes["branch"]["new"] == "develop"

    def test_empty_to_populated_state(self):
        """Test transition from empty to populated state"""
        empty = AgentState()

        populated = AgentState(
            model="GPT-4",
            workspace=WorkspaceInfo(
                path="/home/user/project",
                name="my-project",
                git=GitInfo(is_repo=True, branch="main")
            ),
            context_window=ContextWindowInfo(
                max_tokens=150000,
                tokens_used=30000,
                usage_pct=20
            )
        )

        assert populated.has_changed(empty) is True
        changes = populated.get_changes(empty)
        assert "model" in changes or "workspace" in changes


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_strings(self):
        """Test handling of empty strings"""
        state = AgentState(
            model="",
            workspace=WorkspaceInfo(path="", name=""),
            display=""
        )

        assert state.model == ""
        assert state.workspace.path == ""
        assert state.workspace.name == ""
        assert state.display == ""

    def test_whitespace_handling(self):
        """Test whitespace is properly handled"""
        sensor_data = {"model": "Claude"}
        display = "   \n\n  Test Display  \n\n  "

        state = AgentState.from_sensor_output(sensor_data, display)
        assert state.display == "Test Display"

    def test_very_large_context_values(self):
        """Test handling of large token counts"""
        context = ContextWindowInfo(
            max_tokens=1000000,
            tokens_used=999999,
            usage_pct=99
        )

        assert context.max_tokens == 1000000
        assert context.tokens_used == 999999
        assert context.usage_pct == 99

    def test_negative_context_values(self):
        """Test handling of negative values (validation should clamp to 0)"""
        context = ContextWindowInfo(
            max_tokens=-1,
            tokens_used=-100,
            usage_pct=-50
        )

        # Validation should clamp negative values to 0
        assert context.max_tokens == 0
        assert context.tokens_used == 0
        assert context.usage_pct == 0

    def test_context_usage_over_100(self):
        """Test handling of usage_pct over 100 (validation should clamp to 100)"""
        context = ContextWindowInfo(
            max_tokens=100000,
            tokens_used=150000,
            usage_pct=150
        )

        # Validation should clamp to 100
        assert context.usage_pct == 100

    def test_unicode_in_strings(self):
        """Test handling of unicode characters"""
        state = AgentState(
            workspace=WorkspaceInfo(
                name="프로젝트-名前-🚀",
                path="/home/user/проект"
            )
        )

        assert "🚀" in state.workspace.name
        assert "проект" in state.workspace.path

    def test_special_characters_in_branch(self):
        """Test handling of special characters in branch names"""
        git = GitInfo(is_repo=True, branch="feature/JIRA-123/add-new-feature")
        assert git.branch == "feature/JIRA-123/add-new-feature"

    def test_json_serialization_special_chars(self):
        """Test JSON serialization with special characters"""
        state = AgentState(
            workspace=WorkspaceInfo(name='test"project\'name')
        )

        json_str = state.to_json()
        parsed = json.loads(json_str)
        assert parsed["workspace"]["name"] == 'test"project\'name'


class TestThreadSafety:
    """Test thread safety and immutability"""

    def test_state_is_frozen(self):
        """Test that state is immutable (frozen)"""
        state = AgentState()

        # Attempt to mutate should raise FrozenInstanceError
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            state.model = "Modified"

    def test_workspace_is_frozen(self):
        """Test that workspace is immutable (frozen)"""
        state = AgentState()

        # Attempt to mutate nested object should raise error
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            state.workspace.name = "Modified"

    def test_git_info_is_frozen(self):
        """Test that git info is immutable (frozen)"""
        git = GitInfo(is_repo=True, branch="main")

        # Attempt to mutate should raise error
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            git.branch = "develop"

    def test_context_window_is_frozen(self):
        """Test that context window is immutable (frozen)"""
        context = ContextWindowInfo()

        # Attempt to mutate should raise error
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            context.usage_pct = 50

    def test_default_factory_creates_new_instances(self):
        """Test that default factories create separate instances"""
        state1 = AgentState()
        state2 = AgentState()

        # Instances should be separate
        assert state1 is not state2
        assert state1.workspace is not state2.workspace
        assert state1.context_window is not state2.context_window


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
