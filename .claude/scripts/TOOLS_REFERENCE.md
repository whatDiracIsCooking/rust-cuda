# Claude Code Tools Reference

This document lists all available tools for use in the `multi_claude.py` script's `tools` field.
Use this reference to assign the right tools to each task for optimal orchestration.

## Tool Categories

### File Operations
- **Read** - Read file contents or specific line ranges
- **Write** - Create new files or overwrite existing ones
- **Edit** - Make targeted edits to existing files
- **Glob** - Find files matching patterns (wildcards)
- **Grep** - Search file contents using regex patterns

### Code Analysis & Navigation (Serena MCP)
- **mcp__serena__read_file** - Read files with line ranges, chunking, size limits
- **mcp__serena__create_text_file** - Write/overwrite files
- **mcp__serena__list_dir** - List directory contents (with recursion)
- **mcp__serena__find_file** - Find files by name/pattern
- **mcp__serena__search_for_pattern** - Regex search with file filtering
- **mcp__serena__get_symbols_overview** - Get high-level symbol overview of file
- **mcp__serena__find_symbol** - Find code symbols (classes, functions, methods)
- **mcp__serena__find_referencing_symbols** - Find references to symbols
- **mcp__serena__replace_regex** - Replace content using regex
- **mcp__serena__replace_symbol_body** - Replace entire symbol body
- **mcp__serena__insert_after_symbol** - Insert code after a symbol
- **mcp__serena__insert_before_symbol** - Insert code before a symbol
- **mcp__serena__execute_shell_command** - Run shell commands safely
- **mcp__serena__read_memory** - Read project memory files
- **mcp__serena__write_memory** - Write project memory files
- **mcp__serena__list_memories** - List available memory files
- **mcp__serena__delete_memory** - Delete memory files

### Shell & Process Management
- **Bash** - Execute bash commands and scripts
- **BashBackground** - Run long-running processes in background
- **BashOutput** - Retrieve output from background shells
- **KillShell** - Terminate background shell processes

### Web & Documentation
- **WebSearch** - Search the web for current information
- **WebFetch** - Fetch and analyze web page content
- **mcp__context7__resolve-library-id** - Resolve library names to IDs
- **mcp__context7__get-library-docs** - Fetch up-to-date library documentation

### Task & Workflow Management
- **Task** - Launch specialized sub-agents for complex work
- **TodoWrite** - Create and manage structured task lists
- **SlashCommand** - Execute custom project slash commands

### Jupyter Notebooks
- **NotebookEdit** - Edit Jupyter notebook cells

### Thinking & Analysis
- **mcp__sequential-thinking__sequentialthinking** - Advanced reasoning for complex problems

### MCP Server Resources
- **ListMcpResourcesTool** - List available MCP server resources
- **ReadMcpResourceTool** - Read specific MCP resources

## Tool Selection Guidelines

### For Code Understanding Tasks
**Use these tools:**
- `mcp__serena__read_file` - For reading source files
- `mcp__serena__get_symbols_overview` - For understanding file structure
- `mcp__serena__find_symbol` - For finding specific functions/classes
- `mcp__serena__find_referencing_symbols` - For tracing usage
- `mcp__serena__search_for_pattern` - For finding patterns in code

**Example task:**
```json
{
  "name": "analyze_vector_utils",
  "prompt": "Analyze the pinned_buffer implementation and list all public methods",
  "files": ["src/vector_utils.h"],
  "tools": [
    "mcp__serena__read_file",
    "mcp__serena__get_symbols_overview",
    "mcp__serena__find_symbol"
  ]
}
```

### For Code Modification Tasks
**Use these tools:**
- `mcp__serena__read_file` - Read existing code
- `mcp__serena__find_symbol` - Locate symbols to modify
- `mcp__serena__replace_symbol_body` - Replace entire functions/classes
- `mcp__serena__replace_regex` - Targeted line-level changes
- `mcp__serena__insert_after_symbol` - Add new code after symbols
- `mcp__serena__insert_before_symbol` - Add imports or preceding code

**Example task:**
```json
{
  "name": "add_error_handling",
  "prompt": "Add null pointer checks to all device pointer access methods",
  "files": ["src/thrust_vector.cu"],
  "tools": [
    "mcp__serena__read_file",
    "mcp__serena__find_symbol",
    "mcp__serena__replace_symbol_body"
  ]
}
```

### For Testing & Validation Tasks
**Use these tools:**
- `mcp__serena__execute_shell_command` - Run build/test commands
- `mcp__serena__read_file` - Read test files
- `mcp__serena__search_for_pattern` - Find test cases
- `mcp__serena__read_memory` - Check testing infrastructure docs

**Example task:**
```json
{
  "name": "run_vector_tests",
  "prompt": "Run all vector utility unit tests and report results",
  "files": [],
  "tools": [
    "mcp__serena__execute_shell_command",
    "mcp__serena__read_memory"
  ]
}
```

### For Documentation Tasks
**Use these tools:**
- `mcp__serena__read_file` - Read source files
- `mcp__serena__get_symbols_overview` - Get API overview
- `mcp__context7__get-library-docs` - Fetch external library docs
- `WebSearch` - Search for documentation patterns

**Example task:**
```json
{
  "name": "document_api",
  "prompt": "Generate API documentation for thrust_vector class",
  "files": ["src/thrust_vector.h"],
  "tools": [
    "mcp__serena__read_file",
    "mcp__serena__get_symbols_overview",
    "mcp__serena__find_symbol"
  ]
}
```

### For Research & Investigation Tasks
**Use these tools:**
- `WebSearch` - Search current information
- `WebFetch` - Analyze web pages
- `mcp__context7__resolve-library-id` - Find library docs
- `mcp__context7__get-library-docs` - Get library documentation
- `mcp__serena__search_for_pattern` - Search codebase

**Example task:**
```json
{
  "name": "research_cuda_streams",
  "prompt": "Research CUDA stream best practices and compare with our implementation",
  "files": ["src/cuda_handles.cu"],
  "tools": [
    "WebSearch",
    "mcp__context7__get-library-docs",
    "mcp__serena__read_file"
  ]
}
```

### For Build & Deployment Tasks
**Use these tools:**
- `mcp__serena__execute_shell_command` - Run build scripts
- `mcp__serena__read_memory` - Check build system docs
- `Bash` - Complex build operations
- `mcp__serena__read_file` - Read build configs

**Example task:**
```json
{
  "name": "clean_build",
  "prompt": "Perform a clean build with coverage enabled",
  "files": [],
  "tools": [
    "mcp__serena__execute_shell_command",
    "mcp__serena__read_memory"
  ]
}
```

## Common Tool Combinations

### Code Review
```json
"tools": [
  "mcp__serena__read_file",
  "mcp__serena__find_symbol",
  "mcp__serena__find_referencing_symbols",
  "mcp__serena__search_for_pattern"
]
```

### Refactoring
```json
"tools": [
  "mcp__serena__read_file",
  "mcp__serena__find_symbol",
  "mcp__serena__find_referencing_symbols",
  "mcp__serena__replace_symbol_body",
  "mcp__serena__replace_regex"
]
```

### Bug Investigation
```json
"tools": [
  "mcp__serena__read_file",
  "mcp__serena__search_for_pattern",
  "mcp__serena__find_referencing_symbols",
  "mcp__serena__execute_shell_command",
  "WebSearch"
]
```

### Feature Development
```json
"tools": [
  "mcp__serena__read_file",
  "mcp__serena__get_symbols_overview",
  "mcp__serena__find_symbol",
  "mcp__serena__insert_after_symbol",
  "mcp__serena__replace_symbol_body",
  "mcp__serena__execute_shell_command"
]
```

## Tool Restrictions

### Minimal Tool Sets (Fastest)
For simple summarization or analysis where file modification is not needed:
```json
"tools": [
  "mcp__serena__read_file",
  "mcp__serena__get_symbols_overview"
]
```

### No Tools (Pure Reasoning)
For tasks requiring only analysis of provided file content without any tool calls:
```json
"tools": []
```

### All Tools (Maximum Flexibility)
For complex orchestration tasks requiring full capabilities (note: `"*"` is special syntax for all tools):
```json
"tools": ["*"]
```

## Notes

- **Performance**: Fewer tools = faster execution. Only include necessary tools.
- **Security**: Shell commands (`Bash`, `execute_shell_command`) should be used carefully.
- **Serena Tools**: Always prefer Serena MCP tools over basic tools for code work.
- **Tool Names**: Must match exactly as listed (case-sensitive).
- **Empty List**: `[]` or omitted means default tool access based on Claude Code settings.
