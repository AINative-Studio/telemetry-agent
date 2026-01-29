# Deployment Guide

Complete guide for installing and deploying the Context Agent.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Local Development Setup](#local-development-setup)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Dependency Management](#dependency-management)
- [Monitoring and Logging](#monitoring-and-logging)
- [Performance Tuning](#performance-tuning)
- [Upgrade Guide](#upgrade-guide)

---

## System Requirements

### Minimum Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or WSL2 on Windows
- **Shell**: bash 4.0+
- **Tools**: git, jq (JSON processor)
- **Memory**: 50MB minimum
- **Disk**: 10MB minimum

### Recommended Requirements

- **Python**: 3.10+
- **Memory**: 100MB for optimal performance
- **CPU**: Any modern processor (agent is lightweight)

### Dependencies

**Required:**
- `bash` - Shell for sensor script
- `jq` - JSON processing
- `git` - Git repository detection

**Optional:**
- `python-dotenv` - For .env file support
- `requests` - For ZeroDB integration
- `pyyaml` - For YAML configuration files

---

## Installation Methods

### Method 1: pip Install (Recommended)

```bash
# Install from PyPI (when published)
pip install context-agent

# Verify installation
python -c "from context_agent import ContextAgent; print('Success!')"
```

### Method 2: From Source

```bash
# Clone repository
git clone https://github.com/AINative-Studio/telemetry-agent.git
cd telemetry-agent

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Method 3: Poetry

```bash
# Using Poetry package manager
poetry add context-agent

# Or from source
git clone https://github.com/AINative-Studio/telemetry-agent.git
cd telemetry-agent
poetry install
```

### Method 4: Direct Download

```bash
# Download and extract
curl -L https://github.com/AINative-Studio/telemetry-agent/archive/main.zip -o context-agent.zip
unzip context-agent.zip
cd telemetry-agent-main

# Install
pip install .
```

---

## Local Development Setup

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/AINative-Studio/telemetry-agent.git
cd telemetry-agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install development dependencies
pip install -r requirements-dev.txt

# 5. Set up environment
cp .env.example .env
# Edit .env with your settings

# 6. Verify installation
python -c "from context_agent import ContextAgent; agent = ContextAgent(); print('Setup complete!')"
```

### Development Environment Configuration

**.env file:**
```bash
# Development settings
AGENT_POLLING_INTERVAL=2
AGENT_CONTEXT_THRESHOLD=70
AGENT_LOG_LEVEL=DEBUG
AGENT_DEBUG_MODE=true

# ZeroDB (optional for development)
ENABLE_ZERODB=false
ZERODB_API_KEY=your_dev_key
ZERODB_PROJECT_ID=your_dev_project
```

### Running in Development Mode

```python
from context_agent import ContextAgent

# Development configuration
config = {
    "polling_interval": 2,
    "log_level": "DEBUG",
    "debug_mode": True,
    "cache_enabled": False
}

agent = ContextAgent(config=config)
agent.start()

# Test functionality
state = agent.get_state()
print(state.to_json())
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=context_agent --cov-report=html

# Run specific test file
pytest tests/test_agent.py -v

# Run in watch mode
pytest-watch
```

---

## Production Deployment

### Installation

```bash
# 1. Create production directory
sudo mkdir -p /opt/context-agent
cd /opt/context-agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install agent
pip install context-agent

# 4. Create configuration
cat > config/production.json <<EOF
{
  "polling_interval": 10,
  "context_threshold": 85,
  "sensor_timeout": 5,
  "log_level": "WARNING",
  "enable_zerodb": true,
  "zerodb_batch_size": 50,
  "max_retries": 5
}
EOF

# 5. Set environment variables
cat > .env <<EOF
ZERODB_API_KEY=your_production_key
ZERODB_PROJECT_ID=your_production_project
EOF

# 6. Set permissions
chmod 600 .env
```

### Systemd Service

Create `/etc/systemd/system/context-agent.service`:

```ini
[Unit]
Description=Context Agent - Runtime Context Monitoring
After=network.target

[Service]
Type=simple
User=contextuser
Group=contextuser
WorkingDirectory=/opt/context-agent
Environment="PATH=/opt/context-agent/venv/bin"
EnvironmentFile=/opt/context-agent/.env
ExecStart=/opt/context-agent/venv/bin/python -m context_agent.cli --daemon
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=context-agent

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**

```bash
# Create service user
sudo useradd -r -s /bin/false contextuser
sudo chown -R contextuser:contextuser /opt/context-agent

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable context-agent
sudo systemctl start context-agent

# Check status
sudo systemctl status context-agent

# View logs
sudo journalctl -u context-agent -f
```

### Supervisor (Alternative)

Create `/etc/supervisor/conf.d/context-agent.conf`:

```ini
[program:context-agent]
command=/opt/context-agent/venv/bin/python -m context_agent.cli --daemon
directory=/opt/context-agent
user=contextuser
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/context-agent/agent.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=10
environment=AGENT_CONFIG_FILE="/opt/context-agent/config/production.json"
```

**Start with supervisor:**

```bash
# Create log directory
sudo mkdir -p /var/log/context-agent
sudo chown contextuser:contextuser /var/log/context-agent

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start context-agent

# Check status
sudo supervisorctl status context-agent
```

---

## Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install agent
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 contextuser && \
    chown -R contextuser:contextuser /app

USER contextuser

# Set environment
ENV PYTHONUNBUFFERED=1

# Run agent
CMD ["python", "-m", "context_agent.cli", "--daemon"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  context-agent:
    build: .
    container_name: context-agent
    restart: unless-stopped
    environment:
      - AGENT_POLLING_INTERVAL=10
      - AGENT_CONTEXT_THRESHOLD=85
      - AGENT_LOG_LEVEL=INFO
      - ENABLE_ZERODB=true
      - ZERODB_API_KEY=${ZERODB_API_KEY}
      - ZERODB_PROJECT_ID=${ZERODB_PROJECT_ID}
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - ~/.gitconfig:/home/contextuser/.gitconfig:ro
    networks:
      - agent-network

networks:
  agent-network:
    driver: bridge
```

### Building and Running

```bash
# Build image
docker build -t context-agent:latest .

# Run with docker
docker run -d \
  --name context-agent \
  --restart unless-stopped \
  -e AGENT_POLLING_INTERVAL=10 \
  -e ENABLE_ZERODB=true \
  -e ZERODB_API_KEY=your_key \
  -e ZERODB_PROJECT_ID=your_project \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  context-agent:latest

# Run with docker-compose
docker-compose up -d

# View logs
docker logs -f context-agent

# Stop
docker-compose down
```

### Multi-Stage Build (Optimized)

```dockerfile
# Dockerfile.optimized
FROM python:3.10-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    bash jq git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

WORKDIR /app
COPY . .

RUN useradd -m -u 1000 contextuser && \
    chown -R contextuser:contextuser /app

USER contextuser

CMD ["python", "-m", "context_agent.cli", "--daemon"]
```

---

## Dependency Management

### requirements.txt

```txt
# Core dependencies
python-dateutil>=2.8.0

# Optional: Environment variables
python-dotenv>=0.19.0

# Optional: ZeroDB integration
requests>=2.26.0

# Optional: YAML configuration
PyYAML>=5.4.1
```

### requirements-dev.txt

```txt
# Testing
pytest>=7.0.0
pytest-cov>=3.0.0
pytest-watch>=4.2.0

# Code quality
black>=22.0.0
flake8>=4.0.0
mypy>=0.950

# Documentation
sphinx>=4.5.0
sphinx-rtd-theme>=1.0.0
```

### Installing Dependencies

```bash
# Production dependencies only
pip install -r requirements.txt

# Development dependencies
pip install -r requirements.txt -r requirements-dev.txt

# With Poetry
poetry install --no-dev  # Production
poetry install           # Development
```

---

## Monitoring and Logging

### Logging Configuration

```python
import logging
from context_agent import ContextAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/context-agent/agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('context_agent')

# Start agent
agent = ContextAgent()
agent.start()
```

### Log Rotation

```bash
# /etc/logrotate.d/context-agent
/var/log/context-agent/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 contextuser contextuser
    sharedscripts
    postrotate
        systemctl reload context-agent > /dev/null 2>&1 || true
    endscript
}
```

### Health Check Endpoint

```python
from flask import Flask, jsonify
from context_agent import ContextAgent

app = Flask(__name__)
agent = ContextAgent()
agent.start()

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        state = agent.get_state()
        return jsonify({
            "status": "healthy",
            "model": state.model,
            "workspace": state.workspace.name,
            "last_updated": state.last_updated
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Gauge, start_http_server
from context_agent import ContextAgent, EventType

# Define metrics
state_updates = Counter('agent_state_updates_total', 'Total state updates')
context_usage = Gauge('agent_context_usage_pct', 'Context window usage percentage')
branch_changes = Counter('agent_branch_changes_total', 'Total branch changes')

def handle_metrics(event):
    """Update metrics on state change"""
    state_updates.inc()

    if event.event_type == EventType.STATE_UPDATED:
        state = agent.get_state()
        context_usage.set(state.context_window.usage_pct)

    elif event.event_type == EventType.BRANCH_CHANGED:
        branch_changes.inc()

# Start metrics server
start_http_server(9090)

# Start agent with metrics
agent = ContextAgent()
agent.on_change(EventType.STATE_UPDATED, handle_metrics)
agent.start()
```

---

## Performance Tuning

### Optimizing Polling Interval

```python
# High-frequency monitoring (more CPU, faster updates)
config = {"polling_interval": 1}

# Balanced (recommended for most use cases)
config = {"polling_interval": 5}

# Low-frequency (lower CPU, delayed updates)
config = {"polling_interval": 30}

agent = ContextAgent(config=config)
```

### Caching Configuration

```python
# Enable caching for better performance
config = {
    "cache_enabled": True,
    "cache_ttl": 60  # Cache for 60 seconds
}

agent = ContextAgent(config=config)
```

### Resource Limits

```bash
# Systemd resource limits
[Service]
MemoryLimit=100M
CPUQuota=10%
TasksMax=10
```

---

## Upgrade Guide

### Upgrading from Source

```bash
# Pull latest changes
cd /opt/context-agent
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Upgrade dependencies
pip install --upgrade -r requirements.txt

# Restart service
sudo systemctl restart context-agent
```

### Upgrading via pip

```bash
# Upgrade to latest version
pip install --upgrade context-agent

# Upgrade to specific version
pip install context-agent==2.0.0

# Restart service
sudo systemctl restart context-agent
```

### Migration Checklist

- [ ] Backup configuration files
- [ ] Review changelog for breaking changes
- [ ] Update configuration if needed
- [ ] Test in staging environment
- [ ] Stop agent
- [ ] Upgrade package
- [ ] Update configuration
- [ ] Start agent
- [ ] Verify functionality
- [ ] Monitor logs for errors

---

## Next Steps

- [Configuration Guide](configuration.md) - Configure the agent
- [API Reference](api.md) - API documentation
- [Troubleshooting](troubleshooting.md) - Common issues
- [Architecture](architecture.md) - System design
