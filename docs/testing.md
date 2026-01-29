# Testing Guide - Context Agent

Comprehensive testing guide for the Context Agent project covering unit tests, integration tests, coverage, and testing best practices.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Coverage Reports](#coverage-reports)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Context Agent project maintains a comprehensive test suite with:
- **174 unit and integration tests**
- **90%+ coverage** for core modules (agent.py, state.py, events.py, config.py)
- **BDD-style test organization** with clear Given-When-Then patterns
- **Fixture-based testing** for consistent test data
- **Mock-based isolation** for external dependencies

### Test Philosophy

1. **Test behavior, not implementation** - Tests focus on what the code does, not how
2. **Comprehensive edge case coverage** - Tests include happy paths, error conditions, and edge cases
3. **Fast execution** - Unit tests run in < 5 seconds
4. **Isolated tests** - Each test is independent and can run in any order
5. **Clear test names** - Test names describe what is being tested

---

## Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures and test utilities
├── test_state.py                  # State management tests (72 tests)
├── test_events.py                 # Event system tests (46 tests)
├── test_agent.py                  # Agent core tests (45 tests)
├── test_config.py                 # Configuration tests (29 tests)
├── test_integration.py            # Integration tests (13 tests)
├── test_agent_integration.py      # Agent integration tests (6 tests)
└── test_sensor_execution.sh       # Shell script for sensor testing
```

### Test Files

| File | Purpose | Test Count | Coverage |
|------|---------|------------|----------|
| `test_state.py` | AgentState, WorkspaceInfo, GitInfo, ContextWindowInfo | 72 | 100% |
| `test_events.py` | EventEmitter, EventType, StateChangeEvent | 46 | 98% |
| `test_agent.py` | ContextAgent core functionality | 45 | 93% |
| `test_config.py` | Configuration loading and validation | 29 | 86% |
| `test_integration.py` | End-to-end integration tests | 13 | N/A |
| `test_agent_integration.py` | Agent integration scenarios | 6 | N/A |

---

## Running Tests

### Prerequisites

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements-dev.txt
```

### Basic Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_state.py -v

# Run specific test class
pytest tests/test_state.py::TestAgentState -v

# Run specific test
pytest tests/test_state.py::TestAgentState::test_from_sensor_output_full_data -v

# Run tests matching pattern
pytest tests/ -k "sensor" -v
```

### Running Tests with Coverage

```bash
# Run with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # View in browser

# Generate XML coverage report (for CI)
pytest tests/ --cov=src --cov-report=xml
```

### Test Markers

Tests are organized with markers for selective execution:

```bash
# Run only unit tests
pytest tests/ -m unit -v

# Run only integration tests
pytest tests/ -m integration -v

# Run only state-related tests
pytest tests/ -m state -v

# Run only event-related tests
pytest tests/ -m events -v

# Exclude slow tests
pytest tests/ -m "not slow" -v

# Run multiple markers
pytest tests/ -m "unit and state" -v
```

Available markers:
- `unit` - Unit tests
- `integration` - Integration tests
- `slow` - Slow-running tests (> 1 second)
- `sensor` - Sensor-related tests
- `state` - State management tests
- `events` - Event system tests

---

## Coverage Reports

### Current Coverage

```
Name                        Stmts   Miss   Cover
--------------------------------------------------
src/__init__.py                 9      0 100.00%
src/agent.py                  204     14  93.14%
src/config.py                 137     19  86.13%
src/events.py                  41      1  97.56%
src/state.py                   72      0 100.00%
--------------------------------------------------
Core TOTAL                    463     34  92.66%
```

### Coverage Goals

- **Core modules** (agent.py, state.py, events.py): **≥ 90%** ✓
- **Configuration** (config.py): **≥ 85%** ✓
- **Overall project**: **≥ 80%** (Target)

### Viewing Coverage

```bash
# Terminal report with missing lines
pytest tests/ --cov=src --cov-report=term-missing

# HTML report (most detailed)
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Check coverage threshold
pytest tests/ --cov=src --cov-fail-under=80
```

---

## Test Categories

### 1. State Management Tests (`test_state.py`)

Tests for data classes and state management:

**GitInfo Tests**
- Default and custom initialization
- Serialization (to_dict)
- Equality comparison
- Edge cases (empty values, special characters)

**WorkspaceInfo Tests**
- Nested object handling
- Git repository integration
- Path and name validation

**ContextWindowInfo Tests**
- Token counting
- Usage percentage calculation
- Boundary conditions

**AgentState Tests**
- State creation from sensor output
- Change detection (has_changed, get_changes)
- JSON serialization/deserialization
- Thread safety and immutability

**Test Examples:**
```python
def test_from_sensor_output_full_data():
    """Test creating AgentState from complete sensor output"""
    sensor_data = {
        "model": "GPT-4",
        "workspace": {
            "path": "/home/user/project",
            "name": "my-project",
            "git": {"is_repo": True, "branch": "main"}
        },
        "context_window": {
            "max_tokens": 150000,
            "tokens_used": 30000,
            "usage_pct": 20
        }
    }

    state = AgentState.from_sensor_output(sensor_data, "[GPT-4] my-project")

    assert state.model == "GPT-4"
    assert state.workspace.name == "my-project"
    assert state.context_window.usage_pct == 20
```

### 2. Event System Tests (`test_events.py`)

Tests for event emission and handling:

**EventType Tests**
- Enum values and uniqueness
- Event type comparison

**StateChangeEvent Tests**
- Event creation with metadata
- Serialization (to_dict)
- Complex value handling

**EventEmitter Tests**
- Handler registration and unregistration
- Event emission and propagation
- Multiple handlers per event
- Error handling in callbacks
- Event filtering

**Test Examples:**
```python
def test_emit_calls_all_handlers():
    """Test emit calls all registered handlers"""
    emitter = EventEmitter()
    calls = []

    emitter.on(EventType.BRANCH_CHANGED, lambda e: calls.append(1))
    emitter.on(EventType.BRANCH_CHANGED, lambda e: calls.append(2))
    emitter.on(EventType.BRANCH_CHANGED, lambda e: calls.append(3))

    event = StateChangeEvent(
        event_type=EventType.BRANCH_CHANGED,
        timestamp=datetime.utcnow().isoformat(),
        old_value="main",
        new_value="feature"
    )

    emitter.emit(event)

    assert len(calls) == 3
```

### 3. Agent Core Tests (`test_agent.py`)

Tests for ContextAgent functionality:

**Initialization Tests**
- Default and custom parameters
- Sensor path validation
- Event emitter setup

**Sensor Execution Tests**
- Successful execution
- Timeout handling
- Error recovery
- Exit code handling

**State Management Tests**
- State caching
- Force refresh
- Change detection
- Previous state tracking

**Event Emission Tests**
- Model changed events
- Branch changed events
- Context threshold events
- Event disabling

**Polling Tests**
- Start/stop polling
- Polling intervals
- Error recovery during polling
- Thread safety

**Test Examples:**
```python
@patch.object(ContextAgent, '_execute_sensor')
def test_get_state_cached(mock_execute):
    """Test cached state retrieval"""
    mock_execute.return_value = ("[Claude] test", '{"version": "1.0.0"}')

    agent = ContextAgent()
    state1 = agent.get_state()
    state2 = agent.get_state(force_refresh=False)

    assert state1 == state2
    assert mock_execute.call_count == 1  # Only called once
```

### 4. Configuration Tests (`test_config.py`)

Tests for configuration loading and validation:

**Default Configuration Tests**
- Default values
- Validity checks

**Environment Variable Tests**
- Loading from environment
- Boolean parsing
- Partial configuration

**File Loading Tests**
- JSON file loading
- YAML file loading
- Error handling

**Validation Tests**
- Range validation
- Type validation
- Required field validation

### 5. Integration Tests (`test_integration.py`)

End-to-end tests covering complete workflows:

**Lifecycle Tests**
- Complete agent lifecycle
- State initialization and updates
- Event propagation

**State Change Tests**
- Sequential changes
- Multiple event types
- Threshold crossing

**Error Recovery Tests**
- Transient error handling
- Polling resilience
- State fallback

**Sensor Integration Tests**
- Real sensor execution
- Git detection
- Non-repository handling

---

## Writing Tests

### Test Structure

Follow the AAA (Arrange-Act-Assert) pattern:

```python
def test_example():
    """Test description in docstring"""
    # Arrange - Set up test data and conditions
    agent = ContextAgent()
    expected_value = "test"

    # Act - Execute the code under test
    result = agent.get_some_value()

    # Assert - Verify the results
    assert result == expected_value
```

### Using Fixtures

Fixtures provide reusable test data:

```python
def test_with_fixture(sample_agent_state):
    """Test using fixture from conftest.py"""
    assert sample_agent_state.model == "Claude"
    assert sample_agent_state.workspace.name == "project"
```

### Mocking External Dependencies

Use `unittest.mock` or `pytest-mock` for isolation:

```python
from unittest.mock import patch, Mock

@patch('subprocess.Popen')
def test_sensor_execution(mock_popen):
    """Test with mocked subprocess"""
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = ("output", "error")
    mock_popen.return_value = mock_process

    agent = ContextAgent()
    result = agent._execute_sensor()

    assert result == ("output", "error")
```

### Testing Exceptions

```python
def test_error_handling():
    """Test exception is raised"""
    agent = ContextAgent()

    with pytest.raises(SensorError, match="expected error message"):
        agent.some_failing_method()
```

### Parametrized Tests

Test multiple scenarios with one test:

```python
@pytest.mark.parametrize("input_val,expected", [
    (0, 0),
    (50, 50),
    (100, 100),
    (150, 100),  # Clamped to max
])
def test_percentage_clamping(input_val, expected):
    """Test percentage values are clamped"""
    result = clamp_percentage(input_val)
    assert result == expected
```

### Test Markers

Add markers to categorize tests:

```python
@pytest.mark.unit
@pytest.mark.state
def test_state_creation():
    """Test marked as both unit and state test"""
    state = AgentState()
    assert state is not None
```

---

## Continuous Integration

### GitHub Actions Configuration

Example workflow (`.github/workflows/tests.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt

    - name: Run tests with coverage
      run: |
        pytest tests/ -v --cov=src --cov-report=xml --cov-fail-under=80

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

Add testing to pre-commit (`.pre-commit-config.yaml`):

```yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest
      language: system
      args: [tests/, --cov=src, --cov-fail-under=80, -q]
      pass_filenames: false
```

---

## Troubleshooting

### Common Issues

**1. Import Errors**

```bash
# Ensure you're in the project root
cd /path/to/context-agent

# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall in editable mode
pip install -e .
```

**2. Fixture Not Found**

```python
# Ensure fixture is defined in conftest.py or imported
# Check fixture name matches exactly
def test_example(sample_agent_state):  # Must match fixture name
    pass
```

**3. Tests Hanging**

```bash
# Add timeout to pytest
pytest tests/ -v --timeout=30

# Or run without slow tests
pytest tests/ -m "not slow" -v
```

**4. Coverage Not Updating**

```bash
# Clear coverage cache
rm -rf .coverage htmlcov/

# Run coverage again
pytest tests/ --cov=src --cov-report=html
```

**5. Sensor Tests Failing**

```bash
# Ensure sensor script is executable
chmod +x scripts/context_sensor.sh

# Verify jq is installed
which jq || brew install jq  # macOS
which jq || sudo apt-get install jq  # Linux
```

### Debugging Tests

```bash
# Run with verbose output
pytest tests/test_state.py -vv

# Show print statements
pytest tests/test_state.py -s

# Drop into debugger on failure
pytest tests/test_state.py --pdb

# Run last failed tests only
pytest tests/ --lf
```

### Performance

```bash
# Show slowest tests
pytest tests/ --durations=10

# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto
```

---

## Best Practices

1. **Write tests before fixing bugs** - Ensure regression doesn't happen
2. **Keep tests focused** - One concept per test
3. **Use descriptive test names** - Test name should describe what is being tested
4. **Don't test implementation details** - Test behavior, not internals
5. **Maintain test independence** - Tests should not depend on each other
6. **Use fixtures for setup** - Avoid code duplication
7. **Mock external dependencies** - Keep tests fast and isolated
8. **Verify both success and failure paths** - Test error conditions too
9. **Keep tests readable** - Tests serve as documentation
10. **Run tests frequently** - Don't let test debt accumulate

---

## Test Coverage Goals

| Module | Target | Current | Status |
|--------|--------|---------|--------|
| state.py | 95%+ | 100% | ✓ |
| events.py | 95%+ | 98% | ✓ |
| agent.py | 90%+ | 93% | ✓ |
| config.py | 85%+ | 86% | ✓ |
| **Core Total** | **90%+** | **93%** | **✓** |

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Coverage Plugin](https://pytest-cov.readthedocs.io/)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

---

## Quick Reference

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific marker
pytest tests/ -m unit -v

# Run without slow tests
pytest tests/ -m "not slow" -v

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Run last failed tests
pytest tests/ --lf

# Show slowest tests
pytest tests/ --durations=10
```

---

**Last Updated:** 2026-01-28
**Test Count:** 174 tests
**Coverage:** 93% (core modules)
