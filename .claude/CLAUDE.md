# Calaman_C - Project Instructions

## CRITICAL: Session Startup Protocol

**When you see a `<session-start-hook>` message with tool call instructions:**
1. IMMEDIATELY execute the requested tool calls as your FIRST action
2. DO NOT wait for user input
3. DO NOT explain what you're about to do - just do it

Example: If the hook says "Call: mcp__serena__activate_project with project=...",
call that tool immediately before saying anything else.

**This is non-negotiable - startup hooks must be executed automatically.**

---

## CRITICAL: Tool Preferences and Settings

**ALWAYS verify `compile_commands.json` exists before using symbolic tools.**

Location: `build/compile_commands.json` or symlinked at `compile_commands.json`

### Editing Preferences
- **Strongly prefer** symbolic editing tools over `Edit`:
  - `replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`, `rename_symbol`

**Rule of thumb:**
- Changing a whole symbol → symbolic tools
- Changing a few lines → `Edit` tool

### Reading Preferences
- **Strongly prefer** symbolic reading tools over `search_for_pattern`:
  - `get_symbols_overview` - First step when exploring a new file
  - `find_symbol` - When you know (or can guess) a symbol name
  - `find_referencing_symbols` - To understand symbol relationships
  - Only use `search_for_pattern` when symbolic tools cannot find what you need

### Typical Workflow
1. Don't know what you're looking for → `search_for_pattern`
2. Found candidates → `find_symbol` to get precise locations
3. Need to understand → `get_symbols_overview` + `find_symbol` + `find_referencing_symbols`
4. Ready to edit → `replace_symbol_body` + `insert_after_symbol` + `insert_before_symbol` + `rename_symbol`
5. Symbolic editing tools are inappropriate → `Edit`

### Disabled Tools
- `mcp__serena__replace_regex` + `mcp__serena__read_file` are disabled
- **Hard Rule** When `Edit` is going to be used, you *must* use `Read` first

---

## Using Serena Symbolic Tools

This project uses Serena's AST-aware symbolic tools for all code analysis and modification:
- `get_symbols_overview` Understanding file structure
- `find_symbol` Locating classes/functions by name path
- `find_referencing_symbols` Identifying references
- `replace_symbol_body` Replacing entire symbol definitions
- `insert_after_symbol` Adding code after a symbol
- `insert_before_symbol` Adding code before a symbol
- `rename_symbol` Renaming across entire codebase
- Use symbolic editing tools for whole-symbol changes
- Use regex tools only for small in-function modifications

---

## Project Context
This is a high-performance CUDA library for thrust vector utilities with:
- Pinned memory allocation using modern CUDA 12+ memory resources
- Async copy operations with stream support
- Device pointer access for custom kernels

## Build System

**CRITICAL: Never call cmake, make, or ninja directly. Always use `scripts/build.sh`.**

**For complete build system documentation, see the Serena memory: `build_system`**

Read with: Use Serena's `read_memory` tool with memory name `build_system`
