# Contributing to Context Agent

Thank you for your interest in contributing to the Context Agent project! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Development Workflow](#development-workflow)
- [Release Process](#release-process)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information
- Other conduct considered inappropriate

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- bash 4.0+
- jq (JSON processor)
- git

### Initial Setup

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/telemetry-agent.git
cd telemetry-agent

# 3. Add upstream remote
git remote add upstream https://github.com/AINative-Studio/telemetry-agent.git

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 6. Install pre-commit hooks
pre-commit install

# 7. Verify installation
python -m pytest tests/ -v
```

### Project Structure

```
context-agent/
├── src/                    # Source code
│   ├── __init__.py
│   ├── agent.py           # Main agent implementation
│   ├── state.py           # State management
│   ├── events.py          # Event system
│   └── config.py          # Configuration management
├── scripts/
│   └── context_sensor.sh  # Bash sensor script
├── tests/                 # Test suite
│   ├── test_sensor.py
│   ├── test_agent.py
│   ├── test_state.py
│   └── test_events.py
├── docs/                  # Documentation
├── examples/              # Usage examples
└── config/                # Configuration files
```

---

## Code Style

### Python Style Guide

We follow **PEP 8** with some modifications:

- Line length: 100 characters (not 79)
- Use type hints for all functions and methods
- Use docstrings for all public APIs

### Formatting

We use **Black** for code formatting:

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Linting

We use **flake8** for linting:

```bash
# Run linter
flake8 src/ tests/

# Configuration in setup.cfg
```

### Type Checking

We use **mypy** for static type checking:

```bash
# Run type checker
mypy src/

# Configuration in setup.cfg
```

### Import Sorting

We use **isort** for import organization:

```bash
# Sort imports
isort src/ tests/

# Check import order
isort --check src/ tests/
```

### Pre-commit Hooks

All checks run automatically on commit:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Example Code Style

```python
"""
Module docstring explaining the module's purpose.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ExampleClass:
    """
    Class docstring explaining the class.

    Attributes:
        name: Description of name
        value: Description of value
    """

    name: str
    value: int

    def example_method(self, param: str) -> Optional[str]:
        """
        Method docstring explaining what the method does.

        Args:
            param: Description of parameter

        Returns:
            Description of return value

        Raises:
            ValueError: When param is invalid
        """
        if not param:
            raise ValueError("param cannot be empty")

        return f"{self.name}: {param}"
```

---

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 80%
- **Target coverage**: 90%+

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=context_agent --cov-report=html

# Run specific test file
pytest tests/test_agent.py -v

# Run specific test
pytest tests/test_agent.py::test_agent_start -v

# Run in watch mode
pytest-watch
```

### Writing Tests

We use **pytest** and follow these guidelines:

1. **Test file naming**: `test_*.py`
2. **Test function naming**: `test_<what>_<expected_behavior>`
3. **Use fixtures** for setup/teardown
4. **Use parametrize** for multiple test cases
5. **Mock external dependencies**

**Example Test**:

```python
import pytest
from context_agent import ContextAgent, AgentState


class TestContextAgent:
    """Tests for ContextAgent class"""

    @pytest.fixture
    def agent(self):
        """Create test agent instance"""
        return ContextAgent(config={"polling_interval": 1})

    def test_agent_start_success(self, agent):
        """Test that agent starts successfully"""
        agent.start()
        assert agent.is_running() is True
        agent.stop()

    def test_get_state_returns_agent_state(self, agent):
        """Test get_state returns AgentState instance"""
        agent.start()
        state = agent.get_state()
        assert isinstance(state, AgentState)
        agent.stop()

    @pytest.mark.parametrize("interval", [1, 5, 10])
    def test_polling_interval_configuration(self, interval):
        """Test various polling intervals"""
        agent = ContextAgent(config={"polling_interval": interval})
        assert agent.config["polling_interval"] == interval
```

### Test Categories

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

### Mocking

```python
from unittest.mock import Mock, patch

def test_sensor_execution_with_mock():
    """Test sensor execution with mocked subprocess"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            stdout='[Claude] 📁 test',
            stderr='{"model": "Claude"}',
            returncode=0
        )

        agent = ContextAgent()
        agent.start()
        state = agent.get_state()

        assert state.model == "Claude"
```

---

## Pull Request Process

### Before Submitting

- [ ] All tests pass
- [ ] Code coverage is >= 80%
- [ ] Code is formatted (black, isort)
- [ ] No linting errors (flake8)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

### PR Title Format

```
[TYPE] Brief description

Examples:
[FEATURE] Add async support for agent methods
[BUG] Fix sensor timeout handling
[DOCS] Update API documentation
[REFACTOR] Improve event emitter performance
[TEST] Add tests for state comparison
```

### PR Description Template

```markdown
## Summary
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

## Related Issues
Fixes #123
Relates to #456
```

### Review Process

1. **Automated checks**: CI must pass
2. **Code review**: At least one maintainer approval
3. **Testing**: All tests must pass
4. **Documentation**: Docs must be updated
5. **Merge**: Squash and merge to main

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
- Linting (flake8)
- Type checking (mypy)
- Formatting check (black)
- Tests (pytest)
- Coverage report
- Documentation build
```

---

## Issue Reporting

### Bug Reports

Use this template:

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., macOS 12.0]
- Python: [e.g., 3.10.0]
- Agent version: [e.g., 1.0.0]
- bash version: [output of bash --version]
- jq version: [output of jq --version]

## Logs
```
Paste relevant logs here
```

## Additional Context
Any other information
```

### Feature Requests

```markdown
## Feature Description
Clear description of the feature

## Motivation
Why is this feature needed?

## Proposed Solution
How should this be implemented?

## Alternatives Considered
Other approaches considered

## Additional Context
Any other information
```

### Issue Labels

- `bug`: Something isn't working
- `feature`: New feature request
- `documentation`: Documentation improvements
- `performance`: Performance optimization
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed

---

## Development Workflow

### Branching Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Create bugfix branch
git checkout -b bugfix/issue-number-description

# Create docs branch
git checkout -b docs/what-you-are-documenting
```

### Commit Messages

Follow **Conventional Commits**:

```bash
# Format
<type>(<scope>): <subject>

# Examples
feat(agent): Add async support for get_state
fix(sensor): Handle git detached HEAD state
docs(api): Update ContextAgent docstrings
test(state): Add tests for state comparison
refactor(events): Simplify event emission logic
chore(deps): Update pytest to 7.2.0
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `chore`: Maintenance
- `perf`: Performance improvement

### Sync with Upstream

```bash
# Fetch upstream changes
git fetch upstream

# Merge upstream main into your branch
git checkout main
git merge upstream/main

# Rebase your feature branch
git checkout feature/your-feature
git rebase main
```

### Local Testing Workflow

```bash
# 1. Make changes to code

# 2. Format code
black src/ tests/
isort src/ tests/

# 3. Run linter
flake8 src/ tests/

# 4. Run type checker
mypy src/

# 5. Run tests
pytest tests/ -v --cov=context_agent

# 6. Commit changes
git add .
git commit -m "feat(agent): add new feature"

# 7. Push to your fork
git push origin feature/your-feature

# 8. Create pull request on GitHub
```

---

## Release Process

### Version Numbering

We follow **Semantic Versioning** (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Example: `1.2.3` = Major.Minor.Patch

### Release Checklist

- [ ] Update version in `src/__init__.py`
- [ ] Update CHANGELOG.md
- [ ] Create git tag
- [ ] Build package
- [ ] Test package installation
- [ ] Publish to PyPI
- [ ] Create GitHub release
- [ ] Update documentation

### Creating a Release

```bash
# 1. Update version
# Edit src/__init__.py

# 2. Update CHANGELOG.md
# Add release notes

# 3. Commit changes
git add .
git commit -m "chore: bump version to 1.2.3"

# 4. Create tag
git tag -a v1.2.3 -m "Release version 1.2.3"

# 5. Push changes and tags
git push origin main
git push origin v1.2.3

# 6. Build package
python -m build

# 7. Publish to PyPI
python -m twine upload dist/*
```

---

## Questions?

- Check the [FAQ](docs/troubleshooting.md#faq)
- Search existing [issues](https://github.com/AINative-Studio/telemetry-agent/issues)
- Create a new [discussion](https://github.com/AINative-Studio/telemetry-agent/discussions)
- Email: support@ainative.studio

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

## Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort!
