---
name: tdd-plan
description: Convert existing implementation plan to TDD format compatible with maestro persona
---

# TDD Plan Conversion Command

Converts an existing implementation plan (markdown file) to be TDD-compliant with strict phase separation, checkpoints, rollback triggers, and maestro persona compatibility.

## Usage

```bash
# Review plan file passed as argument
/tdd-plan path/to/plan.md

# Review plan from conversation context (ask user if multiple files discussed)
/tdd-plan
```

## Architecture Overview

- Claude orchestrates: argument parsing, file discovery, tdd-planner agent launch, result presentation
- TDD-planner agent executes: reads maestro persona, analyzes existing plan, reformats to TDD standards
- **Single agent execution**: One tdd-planner instance with maestro persona context

## Phase 1: Input Resolution

### Scenario A: File Path Provided as Argument

1. **Parse Command Arguments**:
   - Extract file path from arguments after `/tdd-plan`
   - Validate file path is a markdown file (`.md` extension)
   - Convert relative path to absolute if needed

2. **Validate File Exists**:
   - Check file existence using Read tool
   - If file doesn't exist, report error: "File not found: {path}. Please provide a valid markdown file path."
   - If file exists, proceed to Phase 2

### Scenario B: No File Path Provided

1. **Check Conversation Context**:
   - Review recent conversation for markdown files or plan discussions
   - Look for .md files in `.claude/temp/*/` directories
   - Identify plan files from context

2. **Ask User if Ambiguous**:
   - If no plan files found: "No plan file specified. Please provide the path to the plan markdown file you want to convert to TDD format."
   - If multiple candidates: "Found multiple plan files. Which one should I convert to TDD format?"
     - List candidates with full paths
     - Wait for user selection

3. **Once File Identified**:
   - Proceed to Phase 2 with selected file

## Phase 2: Launch TDD-Planner Agent with Maestro Context

**CRITICAL: The tdd-planner agent MUST read the maestro persona to understand orchestration requirements.**

Construct the Task tool call with:

- `subagent_type`: `"tdd-planner"`
- `description`: `"Convert {filename} to TDD format"`
- `prompt`:
  ```
  CRITICAL TASK: Convert existing implementation plan to TDD-compliant format with maestro persona compatibility.

  ## Context
  You are reviewing an existing implementation plan that needs to be reformatted to meet strict TDD standards and be compatible with the TDD Maestro orchestration persona.

  ## Required Steps

  ### Step 1: Read Maestro Persona
  Read the file: .claude/personae/tdd-maestro.xml

  Understand maestro's requirements for plans:
  - How maestro orchestrates phase transitions
  - What validation gates maestro expects
  - How maestro invokes phase-specific agents
  - What checkpoints and rollback triggers maestro needs
  - How maestro handles quality gates between phases

  ### Step 2: Read Existing Plan
  Read the plan file: {absolute_file_path}

  Analyze current structure:
  - What phases exist (if any)?
  - Are tests mentioned before implementation?
  - Are there checkpoints and rollback triggers?
  - Is phase separation clear and strict?
  - Are there hard boundaries to prevent scope creep?

  ### Step 3: Identify Gaps and Issues
  Compare existing plan against TDD-planner standards (from your agent instructions) and maestro requirements:

  Missing or inadequate:
  - [ ] Strict RED/GREEN/REFACTOR/VALIDATION phase separation
  - [ ] "Scope (ONLY do this)" sections per phase
  - [ ] "Out of Scope (NEVER do this)" sections per phase
  - [ ] Verification checkpoints per phase (measurable success criteria)
  - [ ] Rollback triggers per phase (specific failure conditions)
  - [ ] Hard boundaries (explicit STOP conditions)
  - [ ] Handoff conditions between phases
  - [ ] Tests listed before implementation
  - [ ] Subagent-friendly structure (each phase can be worked independently)
  - [ ] Maestro-compatible orchestration points

  ### Step 4: Reformat Plan to TDD Standards
  Create a new version of the plan that:

  1. **Follows TDD Plan Architecture (TPA) from your instructions**:
     - RED Layer: Write ONLY tests, verify they fail correctly
     - GREEN Layer: Write MINIMAL code to make tests pass
     - REFACTOR Layer: Improve quality WITHOUT changing behavior
     - VALIDATION Layer: Verify integration, update build/memories

  2. **Includes STRICT PHASE SEPARATION**:
     - Each phase has explicit "Scope (ONLY do this)" section
     - Each phase has explicit "Out of Scope (NEVER do this)" section
     - Mutually exclusive scopes prevent overlap

  3. **Defines Quality Gates for Each Phase**:
     ```markdown
     ## Phase X: [Phase Name]

     ### Scope (ONLY do this):
     - [Specific action 1]
     - [Specific action 2]

     ### Out of Scope (NEVER do this):
     - [Prohibited action 1]
     - [Prohibited action 2]

     ### Files to Create/Modify:
     - [List with file paths]

     ### Checkpoint:
     ✅ [Measurable success criteria - be specific]
        Example: "All 5 new test cases compile and fail with expected error messages"

     ### Rollback Trigger:
     ⚠️ [Specific failure condition] → [Recovery action]
        Example: "Tests don't compile → Revert test changes, review test design"

     ### Handoff to [NEXT_PHASE]:
     [Clear exit criteria for this phase]
     ```

  4. **Ensures Maestro Compatibility**:
     - Clear orchestration transition points between phases
     - Explicit validation gates maestro can check
     - Phase-specific agent invocation instructions
     - Quality checkpoint structure maestro expects
     - Rollback decision points for maestro supervision

  5. **Preserves Original Intent**:
     - Keep the feature requirements and acceptance criteria
     - Maintain the file list and technical approach
     - Preserve risk identification and assumptions
     - Retain timeline estimates (adjust if TDD phases clarify scope)

  ### Step 5: Output Reformatted Plan

  Write the reformatted plan to: {output_file_path}

  Use the EXACT template structure from your agent instructions, ensuring:
  - Sequential thinking checkpoint at start (1 thought to analyze original plan)
  - All phases have checkpoints and rollback triggers
  - Tests are listed before implementation in all sections
  - Build system updates in VALIDATION phase
  - Memory updates identified (if new patterns introduced)
  - Sequential thinking checkpoint at end (1 thought to validate completeness)

  ### Step 6: Provide Conversion Summary

  Report back with:
  ```
  ✅ Plan converted to TDD format

  📍 Original: {input_file_path}
  📍 Reformatted: {output_file_path}

  📊 Changes Applied:
  - Added strict phase separation (RED/GREEN/REFACTOR/VALIDATION)
  - Defined checkpoints and rollback triggers for each phase
  - Added "Scope" and "Out of Scope" sections per phase
  - Established hard boundaries to prevent scope creep
  - Made maestro-compatible with orchestration transition points
  - [List other significant changes]

  🎯 Maestro Compatibility:
  - Clear phase transition gates
  - Explicit validation checkpoints
  - Rollback decision points for supervisor
  - Phase-specific agent invocation structure

  ✅ Ready for maestro-orchestrated implementation
  ```

  ## Important Notes

  - DO NOT create a new plan from scratch - CONVERT the existing plan
  - DO preserve the original feature intent, requirements, and technical approach
  - DO enforce strict TDD phase separation even if original lacks it
  - DO add checkpoints/rollback triggers if missing
  - DO structure for maestro orchestration compatibility
  - DO use sequential thinking at start and end (1 thought each)
  - DO NOT skip reading the maestro persona - it's critical for compatibility
  - DO NOT implement the plan yourself - just reformat it
  ```

**Output File Path Convention**:
- If input is `.claude/temp/feature_impl/feature_plan.md`
- Output should be `.claude/temp/feature_impl/feature_plan_tdd.md`
- If input is elsewhere, append `_tdd` before `.md` extension

## Phase 3: Result Presentation

After the tdd-planner agent completes:

1. **Display Agent Results**:
   - Show the conversion summary from the agent
   - Highlight key changes made to the plan

2. **Provide File Locations**:
   ```
   TDD Plan Conversion Complete
   =============================

   Original: {original_file_path}
   TDD Version: {tdd_file_path}

   The plan has been reformatted with:
   - Strict RED/GREEN/REFACTOR/VALIDATION phase separation
   - Quality gates (checkpoints and rollback triggers)
   - Maestro persona compatibility for orchestration
   - Hard boundaries to prevent scope creep

   Ready for implementation via:
   - `/persona tdd` - Activate maestro for orchestrated execution
   - Direct phase execution - Use tdd-red, tdd-green, etc. agents
   ```

3. **Suggest Next Steps**:
   - Recommend reviewing the TDD version
   - Suggest activating maestro persona for orchestrated implementation
   - Offer to clarify any changes made

## Error Handling

- **File not found**: Report clear error with path, ask user to verify
- **Invalid file format**: If not markdown, suggest correct file type
- **Agent failure**: Display agent error output, suggest manual review
- **Maestro persona missing**: Report if `.claude/personae/tdd-maestro.xml` not found
- **Write failure**: Report if TDD version can't be written, suggest alternative location

## Examples

### Example 1: Convert Specific Plan
```bash
User: /tdd-plan .claude/temp/async_copy_impl/async_copy_plan.md

Claude: [Parses argument, validates file exists]
        [Launches tdd-planner agent with maestro context]
        [Agent reads maestro persona, converts plan]
        [Displays conversion summary and file locations]
```

### Example 2: Convert Plan from Context
```bash
User: /tdd-plan

Claude: Found plan file in recent context: .claude/temp/memory_buffer_impl/memory_buffer_plan.md
        Is this the plan you want to convert to TDD format? [yes/no]

User: yes

Claude: [Launches tdd-planner agent with maestro context]
        [Agent completes conversion]
        [Displays results]
```

### Example 3: Ambiguous Context
```bash
User: /tdd-plan

Claude: Found multiple plan files in conversation context:
        1. .claude/temp/async_copy_impl/async_copy_plan.md
        2. .claude/temp/memory_buffer_impl/memory_buffer_plan.md

        Which plan should I convert to TDD format? (Enter 1 or 2, or provide file path)

User: 1

Claude: [Converts async_copy_plan.md]
```

## Design Rationale

**Why delegate to tdd-planner agent?**
- **Specialized expertise**: tdd-planner has deep knowledge of TDD standards
- **Maestro awareness**: Agent can read maestro persona and understand orchestration needs
- **Consistency**: Uses same agent that creates TDD plans from scratch
- **Quality**: Applies full pre-presentation checklist before output
- **Sequential thinking**: Agent uses structured thinking to analyze and validate

**Maestro compatibility requirements:**
- Maestro needs clear phase transition gates to orchestrate workflow
- Checkpoints allow maestro to validate before proceeding
- Rollback triggers enable maestro to make supervision decisions
- Phase separation ensures maestro can invoke correct phase-specific agents
- Hard boundaries prevent maestro from encountering scope creep issues

**Workflow integration:**
- Plan conversion is separate from plan creation (different use cases)
- Converted plans are compatible with both maestro orchestration and direct agent execution
- User maintains control over which orchestration approach to use
