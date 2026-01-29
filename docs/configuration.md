# Configuration Guide

Complete guide to configuring the Context Agent.

## Table of Contents

- [Configuration Methods](#configuration-methods)
- [Configuration Options](#configuration-options)
- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)
- [Priority and Overrides](#priority-and-overrides)
- [Configuration Validation](#configuration-validation)
- [Security Best Practices](#security-best-practices)
- [Example Configurations](#example-configurations)

---

## Configuration Methods

The Context Agent supports multiple configuration methods:

1. **Constructor Arguments** - Pass config dictionary directly
2. **Environment Variables** - Set via shell or `.env` file
3. **Configuration Files** - Load from JSON/YAML files
4. **Defaults** - Built-in sensible defaults

### Constructor Configuration

```python
from context_agent import ContextAgent

config = {
    "polling_interval": 5,
    "context_threshold": 80,
    "sensor_timeout": 5,
    "enable_zerodb": False
}

agent = ContextAgent(config=config)
```

### Environment Variable Configuration

```python
import os
from context_agent import ContextAgent

# Configuration is read from environment
agent = ContextAgent()
```

```bash
# Set environment variables
export AGENT_POLLING_INTERVAL=10
export AGENT_CONTEXT_THRESHOLD=90
export ENABLE_ZERODB=true
export ZERODB_API_KEY=your_key
export ZERODB_PROJECT_ID=your_project
```

### File-Based Configuration

```python
import json
from context_agent import ContextAgent

# Load from JSON file
with open("config/agent.json") as f:
    config = json.load(f)

agent = ContextAgent(config=config)
```

---

## Configuration Options

### Core Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `polling_interval` | int | 5 | Sensor polling interval in seconds |
| `context_threshold` | int | 80 | Context usage percentage to trigger threshold events |
| `sensor_timeout` | int | 5 | Maximum time in seconds for sensor execution |
| `sensor_path` | str | `scripts/context_sensor.sh` | Path to sensor script |
| `workspace_path` | str | `$PWD` | Path to workspace directory |
| `log_level` | str | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### ZeroDB Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_zerodb` | bool | false | Enable ZeroDB integration |
| `zerodb_api_key` | str | `""` | ZeroDB API key |
| `zerodb_project_id` | str | `""` | ZeroDB project ID |
| `zerodb_api_url` | str | `https://api.zerodb.ainative.studio` | ZeroDB API endpoint |
| `zerodb_batch_size` | int | 10 | Number of events to batch before sending |
| `zerodb_flush_interval` | int | 30 | Seconds between batch flushes |

### Advanced Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_retries` | int | 3 | Maximum sensor retry attempts |
| `retry_delay` | int | 2 | Delay in seconds between retries |
| `cache_enabled` | bool | true | Enable state caching |
| `cache_ttl` | int | 60 | Cache time-to-live in seconds |
| `debug_mode` | bool | false | Enable debug output |

---

## Environment Variables

### Standard Environment Variables

```bash
# Agent Core Settings
AGENT_POLLING_INTERVAL=5          # Polling interval in seconds
AGENT_CONTEXT_THRESHOLD=80        # Context usage alert threshold
AGENT_SENSOR_TIMEOUT=5            # Sensor execution timeout
AGENT_SENSOR_PATH=/path/to/sensor # Custom sensor script path
AGENT_LOG_LEVEL=INFO              # Logging level

# ZeroDB Integration
ENABLE_ZERODB=false               # Enable/disable ZeroDB
ZERODB_API_KEY=your_api_key       # ZeroDB API key
ZERODB_PROJECT_ID=your_project    # ZeroDB project ID
ZERODB_API_URL=https://api.zerodb.ainative.studio
ZERODB_BATCH_SIZE=10              # Event batch size
ZERODB_FLUSH_INTERVAL=30          # Batch flush interval

# Advanced
AGENT_MAX_RETRIES=3               # Maximum retry attempts
AGENT_RETRY_DELAY=2               # Retry delay in seconds
AGENT_CACHE_ENABLED=true          # Enable caching
AGENT_CACHE_TTL=60                # Cache TTL in seconds
AGENT_DEBUG_MODE=false            # Debug mode
```

### Using .env File

Create a `.env` file in your project root:

```bash
# .env
AGENT_POLLING_INTERVAL=10
AGENT_CONTEXT_THRESHOLD=85
ENABLE_ZERODB=true
ZERODB_API_KEY=sk_your_key_here
ZERODB_PROJECT_ID=proj_123456
```

Load with python-dotenv:

```python
from dotenv import load_dotenv
from context_agent import ContextAgent

# Load .env file
load_dotenv()

# Environment variables are now available
agent = ContextAgent()
agent.start()
```

---

## Configuration Files

### JSON Configuration

**config/agent.json:**
```json
{
  "polling_interval": 10,
  "context_threshold": 85,
  "sensor_timeout": 5,
  "sensor_path": "scripts/context_sensor.sh",
  "log_level": "INFO",
  "enable_zerodb": true,
  "zerodb_api_key": "sk_your_key",
  "zerodb_project_id": "proj_123",
  "zerodb_batch_size": 20,
  "max_retries": 3,
  "cache_enabled": true
}
```

**Loading:**
```python
import json
from context_agent import ContextAgent

with open("config/agent.json") as f:
    config = json.load(f)

agent = ContextAgent(config=config)
```

### YAML Configuration

**config/agent.yaml:**
```yaml
# Agent Configuration
agent:
  polling_interval: 10
  context_threshold: 85
  sensor_timeout: 5
  log_level: INFO

# ZeroDB Integration
zerodb:
  enable: true
  api_key: sk_your_key
  project_id: proj_123
  batch_size: 20
  flush_interval: 30

# Advanced Settings
advanced:
  max_retries: 3
  retry_delay: 2
  cache_enabled: true
  cache_ttl: 60
```

**Loading:**
```python
import yaml
from context_agent import ContextAgent

with open("config/agent.yaml") as f:
    config_data = yaml.safe_load(f)

# Flatten configuration
config = {
    **config_data.get("agent", {}),
    **{f"zerodb_{k}": v for k, v in config_data.get("zerodb", {}).items()},
    **config_data.get("advanced", {})
}

agent = ContextAgent(config=config)
```

### Environment-Specific Configuration

```python
import os
import json
from context_agent import ContextAgent

# Load config based on environment
env = os.getenv("ENVIRONMENT", "development")
config_file = f"config/agent.{env}.json"

with open(config_file) as f:
    config = json.load(f)

agent = ContextAgent(config=config)
```

**Directory structure:**
```
config/
├── agent.development.json
├── agent.staging.json
└── agent.production.json
```

---

## Priority and Overrides

Configuration priority (highest to lowest):

1. **Constructor arguments** - Direct config parameter
2. **Environment variables** - OS environment or .env file
3. **Configuration files** - JSON/YAML files
4. **Defaults** - Built-in default values

### Example: Override Priority

```bash
# .env file
AGENT_POLLING_INTERVAL=10
```

```json
// config/agent.json
{
  "polling_interval": 15
}
```

```python
from context_agent import ContextAgent
import json

# Load file config
with open("config/agent.json") as f:
    file_config = json.load(f)

# Override with constructor
config = {
    **file_config,
    "polling_interval": 20  # This takes precedence
}

agent = ContextAgent(config=config)
# Result: polling_interval = 20
```

### Merging Configurations

```python
import os
import json
from context_agent import ContextAgent

def load_config():
    """Load configuration with priority handling"""
    # Start with defaults
    config = {
        "polling_interval": 5,
        "context_threshold": 80,
        "sensor_timeout": 5
    }

    # Load from file if exists
    config_file = os.getenv("AGENT_CONFIG_FILE", "config/agent.json")
    if os.path.exists(config_file):
        with open(config_file) as f:
            config.update(json.load(f))

    # Override with environment variables
    if os.getenv("AGENT_POLLING_INTERVAL"):
        config["polling_interval"] = int(os.getenv("AGENT_POLLING_INTERVAL"))

    if os.getenv("AGENT_CONTEXT_THRESHOLD"):
        config["context_threshold"] = int(os.getenv("AGENT_CONTEXT_THRESHOLD"))

    return config

agent = ContextAgent(config=load_config())
```

---

## Configuration Validation

### Basic Validation

```python
from context_agent import ContextAgent

def validate_config(config):
    """Validate configuration before use"""
    errors = []

    # Validate polling interval
    if config.get("polling_interval", 0) < 1:
        errors.append("polling_interval must be >= 1")

    # Validate context threshold
    threshold = config.get("context_threshold", 0)
    if threshold < 1 or threshold > 100:
        errors.append("context_threshold must be between 1 and 100")

    # Validate sensor timeout
    if config.get("sensor_timeout", 0) < 1:
        errors.append("sensor_timeout must be >= 1")

    # Validate ZeroDB settings
    if config.get("enable_zerodb"):
        if not config.get("zerodb_api_key"):
            errors.append("zerodb_api_key required when enable_zerodb is true")
        if not config.get("zerodb_project_id"):
            errors.append("zerodb_project_id required when enable_zerodb is true")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    return config

# Usage
config = {
    "polling_interval": 5,
    "context_threshold": 80
}

validated_config = validate_config(config)
agent = ContextAgent(config=validated_config)
```

### Schema Validation

```python
from jsonschema import validate, ValidationError

AGENT_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "polling_interval": {
            "type": "integer",
            "minimum": 1,
            "maximum": 300
        },
        "context_threshold": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100
        },
        "sensor_timeout": {
            "type": "integer",
            "minimum": 1,
            "maximum": 30
        },
        "enable_zerodb": {
            "type": "boolean"
        },
        "zerodb_api_key": {
            "type": "string"
        },
        "log_level": {
            "type": "string",
            "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]
        }
    }
}

def validate_config_schema(config):
    """Validate config against JSON schema"""
    try:
        validate(instance=config, schema=AGENT_CONFIG_SCHEMA)
        return config
    except ValidationError as e:
        raise ValueError(f"Invalid configuration: {e.message}")

# Usage
config = {"polling_interval": 5, "context_threshold": 80}
validated_config = validate_config_schema(config)
agent = ContextAgent(config=validated_config)
```

---

## Security Best Practices

### 1. Never Commit Secrets

```bash
# .gitignore
.env
config/agent.local.json
config/*.secret.json
*.key
```

### 2. Use Environment Variables for Secrets

```python
import os
from context_agent import ContextAgent

config = {
    "polling_interval": 5,
    "enable_zerodb": True,
    # Read secrets from environment
    "zerodb_api_key": os.getenv("ZERODB_API_KEY"),
    "zerodb_project_id": os.getenv("ZERODB_PROJECT_ID")
}

# Validate secrets are present
if config["enable_zerodb"] and not config["zerodb_api_key"]:
    raise ValueError("ZERODB_API_KEY environment variable is required")

agent = ContextAgent(config=config)
```

### 3. Separate Configuration Files

```
config/
├── agent.json              # Public configuration
├── agent.secrets.json      # Secrets (gitignored)
└── agent.local.json        # Local overrides (gitignored)
```

```python
import json
import os

def load_secure_config():
    """Load configuration with separate secrets file"""
    # Load public config
    with open("config/agent.json") as f:
        config = json.load(f)

    # Load secrets if exists
    secrets_file = "config/agent.secrets.json"
    if os.path.exists(secrets_file):
        with open(secrets_file) as f:
            config.update(json.load(f))

    # Load local overrides if exists
    local_file = "config/agent.local.json"
    if os.path.exists(local_file):
        with open(local_file) as f:
            config.update(json.load(f))

    return config

agent = ContextAgent(config=load_secure_config())
```

### 4. Encrypt Sensitive Configuration

```python
from cryptography.fernet import Fernet
import json
import os

class EncryptedConfigLoader:
    def __init__(self, key_env_var="CONFIG_ENCRYPTION_KEY"):
        key = os.getenv(key_env_var)
        if not key:
            raise ValueError(f"{key_env_var} environment variable required")
        self.cipher = Fernet(key.encode())

    def load(self, encrypted_file):
        """Load and decrypt configuration"""
        with open(encrypted_file, "rb") as f:
            encrypted_data = f.read()

        decrypted_data = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted_data)

# Usage
loader = EncryptedConfigLoader()
config = loader.load("config/agent.encrypted.json")
agent = ContextAgent(config=config)
```

---

## Example Configurations

### Development Environment

```json
{
  "polling_interval": 2,
  "context_threshold": 70,
  "sensor_timeout": 10,
  "log_level": "DEBUG",
  "enable_zerodb": false,
  "debug_mode": true,
  "cache_enabled": false
}
```

### Production Environment

```json
{
  "polling_interval": 10,
  "context_threshold": 85,
  "sensor_timeout": 5,
  "log_level": "WARNING",
  "enable_zerodb": true,
  "zerodb_batch_size": 50,
  "zerodb_flush_interval": 60,
  "max_retries": 5,
  "cache_enabled": true,
  "cache_ttl": 300
}
```

### Minimal Configuration

```python
from context_agent import ContextAgent

# Use all defaults
agent = ContextAgent()
agent.start()
```

### High-Frequency Monitoring

```json
{
  "polling_interval": 1,
  "context_threshold": 95,
  "sensor_timeout": 2,
  "cache_enabled": false,
  "enable_zerodb": true,
  "zerodb_batch_size": 100
}
```

### Low-Resource Environment

```json
{
  "polling_interval": 30,
  "context_threshold": 90,
  "sensor_timeout": 3,
  "cache_enabled": true,
  "cache_ttl": 600,
  "enable_zerodb": false
}
```

### Multi-Workspace Configuration

```python
from context_agent import ContextAgent

workspaces = {
    "frontend": {
        "workspace_path": "/Users/dev/frontend",
        "polling_interval": 5,
        "context_threshold": 80
    },
    "backend": {
        "workspace_path": "/Users/dev/backend",
        "polling_interval": 10,
        "context_threshold": 90
    }
}

agents = {}
for name, config in workspaces.items():
    agents[name] = ContextAgent(config=config)
    agents[name].start()
```

---

## Configuration Templates

### Template with Comments

```json
{
  // Core Settings
  "polling_interval": 5,        // How often to poll sensor (seconds)
  "context_threshold": 80,      // Alert when context reaches this %
  "sensor_timeout": 5,          // Max sensor execution time
  "log_level": "INFO",          // DEBUG | INFO | WARNING | ERROR

  // ZeroDB Integration
  "enable_zerodb": false,       // Enable persistent storage
  "zerodb_api_key": "",         // Your ZeroDB API key
  "zerodb_project_id": "",      // Your ZeroDB project ID
  "zerodb_batch_size": 10,      // Events per batch
  "zerodb_flush_interval": 30,  // Seconds between flushes

  // Performance
  "max_retries": 3,             // Sensor retry attempts
  "cache_enabled": true,        // Enable state caching
  "cache_ttl": 60              // Cache lifetime (seconds)
}
```

---

## Next Steps

- [Deployment Guide](deployment.md) - Learn how to deploy the agent
- [API Reference](api.md) - Detailed API documentation
- [Examples](examples.md) - Usage examples
- [Troubleshooting](troubleshooting.md) - Common issues
