# Command Output Capture Hooks

This directory contains hooks for capturing command output from Claude Code tool executions.

## Overview

Two complementary hooks work together to ensure command output is always captured:

1. **PreToolUse Hook** (`wrap_command_output.sh`) - Wraps commands to capture output even when it exceeds token limits
2. **PostToolUse Hook** (`capture_command_output.sh`) - Captures output from successful tool executions

## How It Works

### PreToolUse Hook (Primary - for large outputs)

- **Triggers**: Before `mcp__serena__execute_shell_command` executes
- **Purpose**: Wrap commands to capture full output and return truncated view to Claude
- **Output**:
  - Full output saved to `.log`
  - Truncated output (first 50 + last 50 lines) returned to Claude
  - Prevents hitting 25K token limit

### PostToolUse Hook (Backup - for normal outputs)

- **Triggers**: After `mcp__serena__execute_shell_command` and `Bash` tool complete
- **Purpose**: Capture output from successful executions under token limit
- **Output**: Full output appended to `.log`

## Output Format

All captured output is written to `.log` in the project root with this format:

```
================================================================================
Timestamp: 2025-10-09 19:30:14.960015644
Tool: mcp__serena__execute_shell_command
Exit Code: 0

--- Command ---
bash scripts/build.sh --clean

--- STDOUT ---
[full stdout here]

--- STDERR ---
[full stderr here]

================================================================================
```

## Token Limits

- MCP tools have a 25,000 token limit (~287KB of output)
- Commands exceeding this limit will:
  - Have full output captured in `.log` (via PreToolUse)
  - Return truncated view to Claude (first 50 + last 50 lines)
  - Include message indicating full output location

## Files

- `wrap_command_output.sh` - PreToolUse hook for wrapping commands
- `capture_command_output.sh` - PostToolUse hook for capturing output
- `test_pretool.sh` - Test script for verifying PreToolUse functionality
- `.log` - Output log file (git-ignored)
- `.hook_debug.json` - PostToolUse debug file (git-ignored)
- `.pretool_debug.json` - PreToolUse debug file (git-ignored)

## Configuration

Hooks are configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__serena__execute_shell_command",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/scripts/hooks/wrap_command_output.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__serena__execute_shell_command",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/scripts/hooks/capture_command_output.sh"
          }
        ]
      }
    ]
  }
}
```

## Testing

After restarting Claude Code session, test with:

```bash
# Small output (PostToolUse captures)
echo "test"

# Large output (PreToolUse wraps and truncates)
bash scripts/build.sh --clean
```

Check `.log` for captured output.

## Debugging

To enable debug logging, uncomment the debug lines in the hook scripts:

**In `wrap_command_output.sh`:**
```bash
# Uncomment this line:
# echo "$input" > "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}/.pretool_debug.json"
```

**In `capture_command_output.sh`:**
```bash
# Uncomment this line:
# echo "$input" > "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}/.hook_debug.json"
```

Then check the debug JSON files to see what the hooks received.
