#!/usr/bin/env bash
#
# Context Sensor - Authoritative Runtime Context Detection
#
# This script is the canonical source of truth for context information.
# It reads JSON from STDIN and emits a single-line status string.
#
# Dependencies: jq, git
# Exit codes: 0 = success, non-zero = error (gracefully handled)

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

readonly SCRIPT_VERSION="1.0.0"
readonly DEFAULT_MAX_TOKENS=200000

# ============================================================================
# Utility Functions
# ============================================================================

# Safely extract JSON field with default value
json_get() {
    local field="$1"
    local default="${2:-}"
    echo "${INPUT_JSON}" | jq -r ".${field} // \"${default}\"" 2>/dev/null || echo "${default}"
}

# Check if we're in a git repository
is_git_repo() {
    git rev-parse --is-inside-work-tree &>/dev/null
}

# Get current git branch safely
get_git_branch() {
    if is_git_repo; then
        git branch --show-current 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# Get workspace name from path
get_workspace_name() {
    local path="$1"
    if [[ -n "$path" && -d "$path" ]]; then
        basename "$path"
    else
        echo ""
    fi
}

# Calculate percentage safely (avoid division by zero)
calculate_percentage() {
    local used=$1
    local max=$2

    if [[ $max -eq 0 ]]; then
        echo 0
        return
    fi

    echo $(( (used * 100) / max ))
}

# ============================================================================
# Main Sensor Logic
# ============================================================================

main() {
    # Read JSON from STDIN
    if [[ -t 0 ]]; then
        # STDIN is a terminal (not piped), use empty JSON
        readonly INPUT_JSON='{}'
    else
        readonly INPUT_JSON=$(cat)
    fi

    # Extract context information
    local model
    local workspace_path
    local workspace_name
    local git_branch
    local is_repo
    local max_tokens
    local tokens_used
    local usage_pct

    # Model identification
    model=$(json_get "model" "Claude")

    # Workspace detection
    workspace_path=$(json_get "workspace_path" "$PWD")
    workspace_name=$(get_workspace_name "$workspace_path")

    # Git repository detection
    if is_git_repo; then
        is_repo="true"
        git_branch=$(get_git_branch)
    else
        is_repo="false"
        git_branch=""
    fi

    # Context window calculation
    max_tokens=$(json_get "context_window.max_tokens" "$DEFAULT_MAX_TOKENS")
    tokens_used=$(json_get "context_window.tokens_used" "0")
    usage_pct=$(calculate_percentage "$tokens_used" "$max_tokens")

    # ========================================================================
    # Emit Status String (Single Line, Deterministic)
    # ========================================================================

    local status=""

    # Model
    status="[${model}]"

    # Workspace
    if [[ -n "$workspace_name" ]]; then
        status="${status} 📁 ${workspace_name}"
    fi

    # Git branch
    if [[ "$is_repo" == "true" && -n "$git_branch" ]]; then
        status="${status} 🌿 ${git_branch}"
    fi

    # Context usage
    if [[ $tokens_used -gt 0 ]]; then
        status="${status} | 📊 ${usage_pct}%"
    fi

    # Emit final status
    echo "$status"

    # ========================================================================
    # Emit Structured Data (JSON) to STDERR for agent consumption
    # ========================================================================

    cat >&2 <<EOF
{
  "version": "${SCRIPT_VERSION}",
  "model": "${model}",
  "workspace": {
    "path": "${workspace_path}",
    "name": "${workspace_name}",
    "git": {
      "is_repo": ${is_repo},
      "branch": "${git_branch}"
    }
  },
  "context_window": {
    "max_tokens": ${max_tokens},
    "tokens_used": ${tokens_used},
    "usage_pct": ${usage_pct}
  }
}
EOF
}

# ============================================================================
# Entry Point
# ============================================================================

main "$@"
