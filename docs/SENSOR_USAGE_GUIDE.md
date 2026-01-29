# Context Sensor - Usage Guide

Quick reference for using the context sensor script in the Context Agent project.

---

## Basic Usage

### Simple Invocation
```bash
echo '{"model":"claude-sonnet-4"}' | scripts/context_sensor.sh
```

**Output (STDOUT):**
```
[claude-sonnet-4] 📁 context-agent 🌿 main
```

---

## Input Format

The sensor script accepts JSON via STDIN with the following optional fields:

```json
{
  "model": "string",
  "workspace_path": "string",
  "context_window": {
    "max_tokens": number,
    "tokens_used": number
  }
}
```

### Field Descriptions

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | No | `"Claude"` | AI model identifier |
| `workspace_path` | string | No | `$PWD` | Path to workspace directory |
| `context_window.max_tokens` | number | No | `200000` | Maximum context window size |
| `context_window.tokens_used` | number | No | `0` | Current token usage |

---

## Output Format

### STDOUT (Human-Readable)
Single-line status string:
```
[model] 📁 workspace 🌿 branch | 📊 usage%
```

### STDERR (Machine-Readable JSON)
```json
{
  "version": "1.0.0",
  "model": "string",
  "workspace": {
    "path": "string",
    "name": "string",
    "git": {
      "is_repo": boolean,
      "branch": "string"
    }
  },
  "context_window": {
    "max_tokens": number,
    "tokens_used": number,
    "usage_pct": number
  }
}
```

---

## Common Usage Patterns

### 1. Get Full Context Information
```bash
echo '{
  "model": "claude-sonnet-4",
  "workspace_path": "/Users/dev/my-project",
  "context_window": {
    "max_tokens": 200000,
    "tokens_used": 45000
  }
}' | scripts/context_sensor.sh 2>/dev/null
```

**Output:**
```
[claude-sonnet-4] 📁 my-project 🌿 main | 📊 22%
```

### 2. Extract JSON Data Only
```bash
echo '{"model":"test"}' | scripts/context_sensor.sh 2>&1 >/dev/null | jq .
```

**Output:**
```json
{
  "version": "1.0.0",
  "model": "test",
  "workspace": {
    "path": "/Users/dev/context-agent",
    "name": "context-agent",
    "git": {
      "is_repo": true,
      "branch": "main"
    }
  },
  "context_window": {
    "max_tokens": 200000,
    "tokens_used": 0,
    "usage_pct": 0
  }
}
```

### 3. Get Specific Field from JSON
```bash
echo '{"model":"claude-3-opus"}' | \
  scripts/context_sensor.sh 2>&1 >/dev/null | \
  jq -r '.workspace.git.branch'
```

**Output:**
```
main
```

### 4. Check Git Repository Status
```bash
is_git_repo=$(echo '{}' | scripts/context_sensor.sh 2>&1 >/dev/null | jq -r '.workspace.git.is_repo')

if [[ "$is_git_repo" == "true" ]]; then
  echo "Running in git repository"
else
  echo "Not in git repository"
fi
```

### 5. Calculate Token Usage
```bash
echo '{
  "model": "claude-sonnet-4",
  "context_window": {
    "max_tokens": 200000,
    "tokens_used": 150000
  }
}' | scripts/context_sensor.sh 2>&1 >/dev/null | jq '.context_window.usage_pct'
```

**Output:**
```
75
```

---

## Integration Examples

### Shell Script Integration
```bash
#!/bin/bash

# Get context information
context_json=$(cat <<EOF | scripts/context_sensor.sh 2>&1 >/dev/null
{
  "model": "claude-sonnet-4",
  "workspace_path": "$PWD",
  "context_window": {
    "max_tokens": 200000,
    "tokens_used": 50000
  }
}
EOF
)

# Extract specific fields
workspace_name=$(echo "$context_json" | jq -r '.workspace.name')
git_branch=$(echo "$context_json" | jq -r '.workspace.git.branch')
usage_pct=$(echo "$context_json" | jq -r '.context_window.usage_pct')

echo "Workspace: $workspace_name"
echo "Branch: $git_branch"
echo "Context Usage: ${usage_pct}%"
```

### Python Integration
```python
import subprocess
import json

def get_context_info(model, tokens_used=0):
    """Get context information from sensor script."""
    input_data = {
        "model": model,
        "context_window": {
            "max_tokens": 200000,
            "tokens_used": tokens_used
        }
    }

    # Run sensor script
    result = subprocess.run(
        ['scripts/context_sensor.sh'],
        input=json.dumps(input_data),
        capture_output=True,
        text=True
    )

    # Parse JSON output from stderr
    context = json.loads(result.stderr)
    return context

# Usage
context = get_context_info("claude-sonnet-4", tokens_used=75000)
print(f"Workspace: {context['workspace']['name']}")
print(f"Branch: {context['workspace']['git']['branch']}")
print(f"Usage: {context['context_window']['usage_pct']}%")
```

### Node.js Integration
```javascript
const { spawn } = require('child_process');

function getContextInfo(model, tokensUsed = 0) {
  return new Promise((resolve, reject) => {
    const sensor = spawn('scripts/context_sensor.sh');

    let stdout = '';
    let stderr = '';

    sensor.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    sensor.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    sensor.on('close', (code) => {
      if (code === 0) {
        resolve({
          status: stdout.trim(),
          context: JSON.parse(stderr)
        });
      } else {
        reject(new Error(`Sensor exited with code ${code}`));
      }
    });

    // Send JSON input
    sensor.stdin.write(JSON.stringify({
      model,
      context_window: {
        max_tokens: 200000,
        tokens_used: tokensUsed
      }
    }));
    sensor.stdin.end();
  });
}

// Usage
getContextInfo('claude-sonnet-4', 100000).then(result => {
  console.log('Status:', result.status);
  console.log('Workspace:', result.context.workspace.name);
  console.log('Usage:', result.context.context_window.usage_pct + '%');
});
```

---

## Error Handling

### No Input Provided
The script handles missing STDIN gracefully:
```bash
scripts/context_sensor.sh < /dev/null
```
**Output:** `[] 🌿 main` (uses empty JSON)

### Invalid JSON
Invalid JSON will cause jq to fail, but the script uses safe defaults:
```bash
echo 'not json' | scripts/context_sensor.sh
```
The script will use empty JSON `{}` as fallback.

### Missing Fields
All fields are optional. Missing fields use defaults:
```bash
echo '{}' | scripts/context_sensor.sh
```
**Output:** `[Claude] 📁 context-agent 🌿 main`

---

## Performance Tips

### 1. Cache Results
If calling frequently, cache the results:
```bash
# Cache context info for 60 seconds
cache_file="/tmp/context_cache_$$"
if [[ ! -f "$cache_file" ]] || [[ $(find "$cache_file" -mmin +1) ]]; then
  echo '{"model":"claude-sonnet-4"}' | scripts/context_sensor.sh 2>&1 > "$cache_file"
fi

# Use cached results
cat "$cache_file"
```

### 2. Use in Pipelines
The sensor integrates well with Unix pipelines:
```bash
# Get workspace name
workspace=$(echo '{}' | scripts/context_sensor.sh 2>&1 >/dev/null | jq -r '.workspace.name')

# Check if in git repo
if echo '{}' | scripts/context_sensor.sh 2>&1 >/dev/null | jq -e '.workspace.git.is_repo' >/dev/null; then
  echo "In git repository"
fi
```

---

## Debugging

### Enable Verbose Output
To see what the script is doing:
```bash
bash -x scripts/context_sensor.sh <<< '{"model":"test"}'
```

### Validate JSON Output
Ensure the JSON output is valid:
```bash
echo '{"model":"test"}' | \
  scripts/context_sensor.sh 2>&1 >/dev/null | \
  jq empty && echo "Valid JSON" || echo "Invalid JSON"
```

### Check Dependencies
Verify required dependencies are available:
```bash
for cmd in jq git; do
  command -v $cmd >/dev/null && echo "$cmd: OK" || echo "$cmd: MISSING"
done
```

---

## Troubleshooting

### Issue: "command not found: jq"
**Solution:** Install jq
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

### Issue: "command not found: git"
**Solution:** Install git
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git
```

### Issue: No output from script
**Solution:** Check if script is executable
```bash
chmod +x scripts/context_sensor.sh
ls -la scripts/context_sensor.sh
```

### Issue: JSON parsing errors
**Solution:** Ensure input is valid JSON
```bash
# Test JSON validity before piping
echo '{"model":"test"}' | jq empty && echo "Valid"
```

---

## Testing

Run the comprehensive test suite:
```bash
./tests/test_sensor_execution.sh
```

Expected output:
```
========================================
   ALL TESTS PASSED
========================================

Total Tests: 19
Passed:      19
Failed:      0
```

---

## Reference

- **Script Version:** 1.0.0
- **Dependencies:** jq 1.5+, git 2.0+, bash 3.0+
- **Documentation:** `/docs/SENSOR_VERIFICATION_REPORT.md`
- **Tests:** `/tests/test_sensor_execution.sh`

---

**Last Updated:** 2026-01-28
