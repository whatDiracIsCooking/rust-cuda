---
name: pr
description: Prepare for pull request - run style compliance checks
---

# Pull Request Preparation Command

## Architecture Overview
- Claude orchestrates: safety checks, file discovery, **parallel agent execution**, result aggregation, **memory updates**, PR creation
- Reviewer agents execute: style compliance reviews with Serena symbolic tools
- **Parallel execution:** Launch one reviewer agent per changed file (all in single message)
- **Memory updates:** Critical for preventing technical debt - keeps Serena memories synchronized with code changes

## Phase 1: Safety Checks

1. Verify current branch is NOT `main`:
   - Get current branch: `git branch --show-current`
   - If branch is `main`, STOP and inform user: "Cannot create PR from main branch. Please create a feature branch first."
   - Otherwise, proceed

2. Check for uncommitted changes and settle pre-commit hooks:
   - Run: `git status --porcelain`
   - If there are unstaged or untracked changes, list them and ask user: "Found uncommitted changes. Please commit them first to run pre-commit hooks (formatting, CUDA checks, test coverage). What would you like to commit? (Respond with file paths or 'all' or 'none')"
   - If user chooses to commit:
     - Stage files: `git add <files>` or `git add -A` for all
     - Commit: `git commit -m "chore: prepare changes for PR"`
     - Pre-commit hooks will run automatically (clang-format, cmake-format, CUDA checks, test coverage)
     - **CRITICAL: Check if hooks modified files**: `git status --porcelain`
     - If hooks modified files (status is dirty):
       - Stage hook changes: `git add -A`
       - Amend commit: `git commit --amend --no-edit`
       - Verify clean state: `git status --porcelain` (must be empty)
     - If clean, proceed
   - **Ensure clean state before proceeding**: No uncommitted changes allowed before review phase

## Phase 2: File Discovery and Style Guide Mapping

1. **Discover Changed Files**:
   - Execute: `git diff $(git merge-base HEAD origin/main)...HEAD --name-only`
   - Filter to source files (.h, .cu, .cpp, .cppm, .cmake, CMakeLists.txt, .py, .md)
   - Exclude deleted files (check existence with `test -f`)
   - Exclude `docs/standards/*.md` from style checking

2. **Map Files to Style Guides**:
   - For each changed file, determine which style guide applies:
     - `*.cu, *.h, *.cpp, *.cppm` → `docs/standards/source-code-style-guide.md`
     - `CMakeLists.txt, *.cmake` → `docs/standards/cmake-style-guide.md`
     - `*.py` → `docs/standards/source-code-style-guide.md`
     - `*.md` → `docs/standards/documentation-style-guide.md`
   - Create list of (file, style_guide) pairs for agent launch

## Phase 3: Launch Parallel Reviewer Agents

**CRITICAL: All Task tool calls MUST be in a single message for parallel execution.**

For each (file, style_guide) pair, create a Task tool call with:
- `subagent_type`: `"reviewer"`
- `description`: `"Review <filename> style compliance"`
- `prompt`:
  ```
  Review {file} against {style_guide} for style compliance.

  IMPORTANT - Formatting Authority:
  - clang-format is AUTHORITATIVE for C++/CUDA formatting
  - cmake-format is AUTHORITATIVE for CMake formatting
  - Pre-commit hooks are AUTHORITATIVE for file hygiene

  Tasks:
  1. Read the style guide: {style_guide}
  2. Read the target file: {file}
  3. Check for violations (SKIP items handled by pre-commit):

     ✅ DO CHECK (semantic/architectural):
     - Naming conventions (variables, functions, classes, namespaces)
     - Include ordering (clang-format has limitations with C++20 modules and .cu files)
     - Code organization and structure
     - Comment content and documentation completeness
     - RAII and resource management patterns
     - Architectural consistency
     - CMake semantic properties (POSITION_INDEPENDENT_CODE, target aliases, coverage flags)

     ⚠️ CRITICAL - README.md Documentation Format:
     - README.md files MUST use standard Markdown (NOT Doxygen)
     - DO NOT require @file, @brief, @param, @return, @throws in README.md
     - Check docs/standards/documentation-style-guide.md lines 36-108
     - Source files (.h/.cpp/.cu/.cppm) use Doxygen
     - README files (.md) use Markdown headings and lists
     - Doxygen tags in Markdown files are VIOLATIONS, not requirements

     ❌ DO NOT CHECK (pre-commit handles):
     - Trailing whitespace (trailing-whitespace hook)
     - End-of-file newlines (end-of-file-fixer hook)
     - Indentation and spacing (clang-format/cmake-format handle)
     - Brace placement (clang-format handles)
     - Line length (clang-format handles)
     - Any other formatting details

  4. If violations found:
     - List each violation with file:line reference
     - DO NOT fix (read-only review)

  5. Output format: 'PASS' if no violations, or 'VIOLATIONS: <count> in {file}' with detailed list

  Be concise - focus on actual semantic violations, not formatting.
  ```

**Example for 3 changed files:**
```python
# Single message with 3 parallel Task calls:
Task(subagent_type="reviewer", description="Review vector_utils.cu", prompt="Review src/vector_utils.cu against docs/standards/source-code-style-guide.md...")
Task(subagent_type="reviewer", description="Review cuda_handles.h", prompt="Review src/cuda_handles.h against docs/standards/source-code-style-guide.md...")
Task(subagent_type="reviewer", description="Review CMakeLists.txt", prompt="Review CMakeLists.txt against docs/standards/cmake-style-guide.md...")
```

All agents execute in parallel, returning results to orchestrator when complete.

## Phase 4: Result Aggregation

1. **Collect Agent Results**:
   - Each reviewer agent returns either "PASS" or "VIOLATIONS: X in {file}"
   - Store results in a structured format: `{file: result_string}`
   - Track which files had violations vs. passed

2. **Parse Results**:
   - Count total files analyzed
   - Count files with violations reported
   - Extract violation counts from "VIOLATIONS" messages
   - Flag any agent failures or errors

3. **Build Unified Report**:
```
PR Readiness Report
===================

Style Compliance Summary:
- Files analyzed: <total_count>
- Files passed: <count>
- Files with violations: <count>
- Total violations: <sum>

Per-File Results:
✓ src/vector_utils.cu: PASS
❌ src/cuda_handles.h: VIOLATIONS - 3 (naming, documentation)
❌ CMakeLists.txt: VIOLATIONS - 1 (macro usage)
```

## Phase 5: Memory Updates & PR Creation

**If ALL tasks succeeded:**

### Step 1: Update Serena Memories (Critical for Technical Debt Prevention)

**Purpose:** Keep project memories synchronized with code changes to prevent documentation drift and accumulating technical debt.

1. **List Available Memories**:
   - Execute: `mcp__serena__list_memories`
   - Get all available memory names

2. **Analyze Impact of Changed Files**:
   - For each changed file, determine which memories might be affected:
     - `src/utils/portable/*.{h,cpp,cu}` → `portable_memory_buffers`
     - `src/utils/cuda/*.{h,cpp,cu}` → Check for CUDA utilities memories
     - `CMakeLists.txt`, `*/CMakeLists.txt`, `*.cmake` → `build_system`
     - `test/**/*_ut.{cpp,cu}` → `test_infrastructure`
     - `scripts/build.sh`, `.github/workflows/*.yml` → `gh_cli_workflows`, `build_system`
     - `docs/standards/*.md` → Related style/doc memories
     - New directories/modules → May need NEW memory creation

3. **Review and Update Each Affected Memory**:
   - For each potentially affected memory:
     - Read current memory: `mcp__serena__read_memory("<memory_name>")`
     - Review changed files to identify updates needed
     - Update memory if needed: `mcp__serena__write_memory("<memory_name>", "<updated_content>")`
     - Document what changed in the memory

4. **Create New Memories if Needed**:
   - If PR introduces new modules/subsystems, create corresponding memories
   - Use descriptive names (e.g., `thrust_wrappers`, `cuda_stream_management`)
   - Include: overview, API reference, usage patterns, testing approach

5. **Verify Memory Updates**:
   - List memories again to confirm updates were written
   - Include memory update summary in PR report

**Example Memory Impact Analysis:**
```
Changed Files → Affected Memories:
- src/utils/portable/memory_buffer.h → portable_memory_buffers
- src/utils/portable/README.md → portable_memory_buffers
- CMakeLists.txt → build_system
- test/unit/memory_buffer_ut.cpp → test_infrastructure

Actions Taken:
✓ Updated portable_memory_buffers: Added new copy() function signatures
✓ Updated build_system: Documented new CMake target
✓ test_infrastructure: Already up-to-date
```

### Step 2: Commit All Changes
1. Stage everything: `git add -A`
2. Commit with descriptive message:
   - If only style fixes: `git commit -m "style: automated compliance fixes for PR"`
   - If memories updated: `git commit -m "chore: style fixes and memory updates for PR"`
   - Include which memories were updated in commit body if significant

### Step 3: Push and Create PR
1. Push branch: `git push -u origin <branch_name>`
2. Create PR: `gh pr create --base main --title "<descriptive title>" --body "<unified report with memory updates>"`
3. Report success with PR URL

**PR Body Template:**
```markdown
## Summary
<Describe changes>

## Style Compliance
✓ All semantic checks passed
- Formatting: Handled by clang-format/cmake-format (automated)
- Violations found: <count> (if any, list them)

## Memory Updates
<List updated memories and why>
- Updated `portable_memory_buffers`: New API signatures
- Updated `build_system`: New CMake targets

## Testing
<Test results if applicable>
```

**If ANY violations found:**
1. Report violation details:
   - Which files have violations
   - List violations by category (naming, documentation, architecture)
   - Distinguish CRITICAL (blocks PR) vs. RECOMMENDED (can defer)
2. Suggest next steps:
   ```
   ⚠️ Style violations found. Next steps:

   CRITICAL violations (must fix):
   - <list critical issues>

   RECOMMENDED violations (should fix):
   - <list recommended issues>

   Fix violations manually, then run /pr again to verify.
   ```
3. Do NOT commit, push, or create PR if CRITICAL violations exist

## Error Handling
- If agent launch fails: report which files couldn't be reviewed, suggest manual review
- If agent returns error: include error message in report, suggest manual fix
- If memory update fails: report which memory failed and why, suggest manual update
- If git commands fail: report git error and suggest manual resolution

## Memory Update Guidelines

**When to Update Memories:**
- API changes (new functions, modified signatures, deprecated features)
- Architectural changes (new modules, refactored components)
- Build system changes (new targets, modified dependencies)
- Testing infrastructure changes (new test patterns, frameworks)
- Documentation structure changes (new standards, conventions)

**What to Include in Memory Updates:**
- Clear description of what changed and why
- Updated API signatures or command examples
- New usage patterns or best practices
- Deprecation notices if applicable
- Links to related memories that may also need updates

**Memory Naming Conventions:**
- Use snake_case: `portable_memory_buffers`, `build_system`
- Be descriptive: `thrust_wrappers` not `tw`
- Group related concepts: `cuda_stream_management`, `cuda_error_handling`

**Memory Organization Best Practices:**
- Keep memories focused on single subsystem/module
- Cross-reference related memories
- Include file locations and key symbols
- Document both "how to use" and "how it works"
- Highlight deprecations and migration paths

## Design Rationale: Parallel Agents vs. Multi-Script

**Why parallel reviewer agents?**
- **Simpler workflow**: No JSON config generation, no script execution, no log parsing
- **Native integration**: Uses Claude Code's built-in agent system
- **Better context awareness**: Agents understand code relationships, not just string patterns
- **Interactive feedback**: Real-time output, easier iteration on failures
- **Smarter reviews**: Can catch architectural issues beyond style compliance
- **Serena-native**: Direct access to symbolic tools without marshaling overhead
- **Scalable parallelism**: Handles 10-20 files efficiently in parallel execution

**Performance characteristics:**
- 1-10 files: ~30-90 seconds (excellent)
- 10-20 files: ~2-4 minutes (good)
- 20+ files: May hit rate limits, but still faster than sequential execution

**Trade-offs accepted:**
- No explicit worker limits (relies on Claude Code's parallelism)
- Less structured output format (but still parseable)
- No separate log files (output in agent results)
