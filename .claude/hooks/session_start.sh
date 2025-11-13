#!/bin/bash
# Hook: Session startup - prepare environment and wait for Serena
# Triggers on: SessionStart
# Purpose: Ensure build artifacts exist and Serena is ready

set -euo pipefail

# Configuration
TIMEOUT_SECONDS=30
POLL_INTERVAL_MS=500  # Poll every 500ms
LOG_FILE="/tmp/claude_serena_startup.log"

# Initialize log
echo "=== Session startup at $(date) ===" > "$LOG_FILE"

# ============================================================================
# Ensure build directory with compile_commands.json exists
# ============================================================================

ensure_build_exists() {
    local project_root="$CLAUDE_PROJECT_DIR"
    local build_dir="${project_root}/build"
    local compile_commands="${build_dir}/compile_commands.json"
    local build_script="${project_root}/scripts/build.sh"

    # Check if build directory exists with valid compile_commands.json
    if [ -d "${build_dir}" ] && [ -f "${compile_commands}" ]; then
        # Verify the file is not empty and recent
        if [ -s "${compile_commands}" ]; then
            echo "✓ Build directory exists with compile_commands.json" >> "$LOG_FILE"
            return 0
        else
            echo "⚠️  compile_commands.json exists but is empty, rebuilding..." >> "$LOG_FILE"
            rm -rf "${build_dir}"
        fi
    fi

    # Check if build script exists
    if [ ! -f "${build_script}" ]; then
        echo "⚠️  No build directory found and build script missing: ${build_script}" >&2
        return 1
    fi

    echo "→ Running initial build to generate compile_commands.json..." >> "$LOG_FILE"
    echo "  This will take ~2 minutes on first run (builds are cached)..." >> "$LOG_FILE"
    echo "" >&2
    echo "🔨 First-time build required (~2 min)..." >&2
    echo "   Generating compile_commands.json for IDE integration..." >&2
    echo "" >&2

    # Run build script - this may take 2+ minutes
    # If hook gets killed by timeout, user will see the error message
    if NINJA_JOBS=24 "${build_script}" >> "$LOG_FILE" 2>&1; then
        if [ -f "${compile_commands}" ]; then
            echo "✓ Initial build completed successfully" >> "$LOG_FILE"
            return 0
        else
            echo "❌ Build script succeeded but compile_commands.json not found" >> "$LOG_FILE"
            echo "❌ Build script succeeded but compile_commands.json not found" >&2
            return 1
        fi
    else
        local exit_code=$?
        echo "❌ Initial build failed (exit code: $exit_code)" >> "$LOG_FILE"
        echo "❌ Initial build failed" >&2
        echo "   Check log for details: $LOG_FILE" >&2
        echo "   Or run manually: ${build_script}" >&2
        return 1
    fi
}

# ============================================================================
# Wait for Serena MCP server to be ready
# ============================================================================

# Function to check if Serena process is running
check_serena_process() {
    if pgrep -f "serena start-mcp-server" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if Serena is actually connected/responsive
check_serena_connected() {
    # First, check if the process is running
    if ! check_serena_process; then
        echo "  Serena process not running yet" >> "$LOG_FILE"
        return 1
    fi

    # Find the most recent Claude Code MCP log file for Serena
    local log_dir="$HOME/.cache/claude-cli-nodejs"
    local latest_log

    # If log directory doesn't exist, Claude hasn't started MCP connections yet
    if [ ! -d "$log_dir" ]; then
        echo "  Waiting for Claude MCP log directory: $log_dir" >> "$LOG_FILE"
        return 1
    fi

    # Find the most recent serena MCP log
    latest_log=$(find "$log_dir" -path "*/mcp-logs-serena/*.txt" -type f -mmin -1 -printf '%T@ %p
' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

    # If no log file exists yet, Claude hasn't connected to Serena yet
    if [ -z "$latest_log" ] || [ ! -f "$latest_log" ]; then
        echo "  Waiting for Claude MCP log file in $log_dir/*/mcp-logs-serena/" >> "$LOG_FILE"
        return 1
    fi

    # Check if Claude Code has successfully connected to Serena
    if grep -q "Successfully connected" "$latest_log" 2>/dev/null; then
        echo "  ✓ Claude Code connected to Serena" >> "$LOG_FILE"
        return 0
    else
        echo "  Serena process running but Claude not yet connected" >> "$LOG_FILE"
        return 1
    fi
}

wait_for_serena() {
    local elapsed_ms=0
    local timeout_ms=$((TIMEOUT_SECONDS * 1000))
    echo "→ Checking for Serena MCP server..." >> "$LOG_FILE"

    while [ $elapsed_ms -lt $timeout_ms ]; do
        if check_serena_connected; then
            local elapsed_s
            elapsed_s=$(awk "BEGIN {printf \"%.1f\", $elapsed_ms / 1000}")
            echo "✓ Serena MCP server is ready (${elapsed_s}s)" >> "$LOG_FILE"
            return 0
        fi

        sleep "$(awk "BEGIN {print $POLL_INTERVAL_MS / 1000}")"
        elapsed_ms=$((elapsed_ms + POLL_INTERVAL_MS))
    done

    # Timeout reached
    echo "✗ Timeout: Serena MCP server not ready after ${TIMEOUT_SECONDS}s" >> "$LOG_FILE"
    cat >&2 <<EOF
⚠️  Warning: Serena MCP server not detected

The Serena MCP server doesn't appear to be running.

To start it manually:
  serena start-mcp-server

Continuing session anyway...
EOF
    return 1
}

# ============================================================================
# Main execution flow
# ============================================================================

# Step 1: Ensure build exists
if ! ensure_build_exists; then
    echo "❌ Build failed - cannot start session without compile_commands.json" >&2
    exit 1
fi

# Step 2: Wait for Serena and activate project
if wait_for_serena; then
    project_dir="$CLAUDE_PROJECT_DIR"
    if [ -n "$project_dir" ]; then
        echo "→ Auto-activating Serena project at: $project_dir" >> "$LOG_FILE"
        cat <<EOF

🔧 Serena is ready. Activating project automatically...
   Project directory: $project_dir

<session-start-hook>
Call: mcp__serena__activate_project with project="$project_dir"
</session-start-hook>
EOF
    fi
fi

exit 0
