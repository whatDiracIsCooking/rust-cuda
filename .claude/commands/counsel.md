---
name: counsel
description: Multi-perspective code review with expert personae
---

You have been asked to provide expert code review using the reviewer agent (`.claude/agents/reviewer.md`).

## Argument Parsing

Parse the command arguments to extract:
1. **File paths** - All arguments that are valid file paths
2. **Personas** - Specified via `--persona=<name>` or `--personae=<name1>,<name2>,...`

If no explicit file paths are provided, ask the user which files they want reviewed.

## Available Personae

- stroustrup - Modern C++ Architect
- volta - CUDA Developer
- guido - Python Engineer
- tali - Test Engineer
- brooks - Software Architect
- computational-physicist - Numerical Computing Expert
- cormac - Documentation & Narrative Designer
- riley - DevOps Engineer

## Review Strategy

Based on the parsed arguments:

### No Persona Specified (Baseline Review)
Spawn one reviewer agent with prompt:
```
Review the following files:
[list files with their full paths]
```

### Single Persona Specified
Spawn one reviewer agent with prompt:
```
Review the following files as [persona]:
[list files with their full paths]
```

### Multiple Personae Specified
Spawn one reviewer agent PER persona, each with prompt:
```
Review the following files as [persona]:
[list files with their full paths]
```

**CRITICAL**: Launch all persona-specific reviewers in PARALLEL using a single message with multiple Task tool calls.

## Implementation Steps

1. Parse arguments to extract files and persona specifications
2. Validate that files exist (use Read or Glob tools as needed)
3. Validate that specified personae are recognized (see Available Personae list above)
4. Construct appropriate prompts for each reviewer agent
5. Use Task tool with subagent_type="general-purpose" to spawn reviewer agents
6. If multiple personae: launch all agents in parallel (single message, multiple Task calls)
7. After all agents complete, present each agent's output clearly, labeled by persona (if applicable)

## Example Usage Patterns

```bash
# Basic review (no persona)
/counsel src/Memory.cpp

# Single persona review
/counsel --persona=volta src/kernels/async_copy.cu

# Multiple files, single persona
/counsel --persona=stroustrup src/Memory.cpp include/Memory.h

# Multi-persona parallel review
/counsel --personae=volta,tali src/kernels/async_copy.cu

# Comprehensive review with all relevant personae
/counsel --personae=stroustrup,volta,brooks src/core_module.cpp
```

## Important Notes

- Always validate file paths before spawning agents
- Convert relative paths to absolute paths before passing to agents
- Use parallel agent spawning for multi-persona reviews (single message, multiple Task calls)
- Each agent reviews ALL specified files from their persona's perspective
- Present results clearly, with persona labels for multi-persona reviews
- If a persona name is misspelled or not recognized, suggest the correct names from the Available Personae list
