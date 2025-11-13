#!/bin/bash
# Hook: Block raw cmake/ninja/make commands and redirect to build script
# Triggers on: Tool execution (Bash, serena execute_shell_command)
# Purpose: Ensure Claude always uses scripts/build.sh instead of raw build commands

# Debug logging (optional)
LOG_FILE="/tmp/claude_command_block_hook.log"
echo "=== Hook invoked at $(date) ===" >> "$LOG_FILE"

# Read the hook input (JSON with command info)
input=$(cat)

# Parse the command being executed
# The input JSON structure varies, but typically has a "command" field
command=$(echo "$input" | grep -oP '"command"\s*:\s*"\K[^"]+' || echo "")

echo "Command attempted: $command" >> "$LOG_FILE"

# Quick exit for known-safe commands (avoids false positives in git commits, echo, etc.)
# Allow all git commands to avoid false positives with paths like cmake/Dependencies.cmake
if echo "$command" | grep -qE '^(git|cat|grep|find|ls|du|pwd|which|type|man|info|apropos|command)'; then
    echo "Command allowed (known-safe command pattern)" >> "$LOG_FILE"
    exit 0
fi

# Allow commands with cmake/ paths or .cmake files (not actual cmake commands)
if echo "$command" | grep -qE '(cmake/|\.cmake)'; then
    echo "Command allowed (cmake path or .cmake file)" >> "$LOG_FILE"
    exit 0
fi

# Check if build tools appear as actual commands (not just in string arguments)
# Matches when tool appears at command position: start of line or after shell operators
if echo "$command" | grep -qE '(^|[[:space:];|&(])\s*(cmake|ninja|make)\b'; then
    # Extract which tool was used
    tool=$(echo "$command" | grep -oE '\b(cmake|ninja|make)\b' | head -1)

    echo "Blocked: $tool command" >> "$LOG_FILE"

    # Provide helpful error message
    cat >&2 <<EOF
❌ Direct ${tool} command blocked!

Please use the build script instead:
  scripts/build.sh              # Incremental build
  scripts/build.sh --clean      # Clean build
  scripts/build.sh --test       # Build + run tests
  scripts/build.sh --clean --test  # Full rebuild + tests

The build script ensures:
  ✓ Proper output capture to .logs/
  ✓ Consistent build configuration
  ✓ ccache acceleration
  ✓ Test execution and coverage support

Log files are available in: .logs/
Latest build log: .logs/latest.log
EOF

    # Exit 2 to block the command
    exit 2
fi

echo "Command allowed (no build tools detected)" >> "$LOG_FILE"

# Not a build command - allow it to proceed
exit 0
