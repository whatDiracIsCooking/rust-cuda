---
name: tdd-orchestrate
description: Activate TDD Maestro persona and orchestrate implementation of a TDD plan
---

# TDD Orchestration Command

Activates the TDD Maestro persona and orchestrates the complete implementation of a TDD plan through all phases (RED → GREEN → REFACTOR → VALIDATION) with domain expert validation at each phase transition.

## Usage

```bash
# Orchestrate specific plan file
/tdd-orchestrate path/to/plan.md

# Orchestrate plan from conversation context
/tdd-orchestrate
```

## What This Command Does

1. **Resolves Plan File**: Finds the TDD plan either from arguments or conversation context
2. **Validates Plan**: Ensures plan exists and is in proper TDD format
3. **Activates Maestro**: Invokes the TDD Maestro persona from `.claude/personae/tdd-maestro.xml`
4. **Initiates Orchestration**: Hands off the plan to maestro for complete TDD workflow orchestration

## Architecture Overview

- **Claude orchestrates**: Input parsing, validation, persona activation, handoff
- **Maestro takes over**: Complete TDD workflow management with phase gates and domain expert validation
- **Phase-specific agents**: Invoked by maestro for RED, GREEN, and REFACTOR phases
- **Validator agents**: Same agents invoked in VALIDATOR MODE for quality gates

## Phase 1: Input Resolution and Validation

### Scenario A: Plan File Path Provided

1. **Parse Command Arguments**:
   - Extract file path from arguments after `/tdd-orchestrate`
   - Validate file is markdown (`.md` extension)
   - Convert relative path to absolute if needed

2. **Validate File Exists**:
   - Use Read tool to verify file exists and is readable
   - If file doesn't exist: "Plan file not found: {path}. Please provide a valid TDD plan file."
   - If file exists: Extract feature name from filename and proceed

3. **Extract Feature Name**:
   - From path like `.claude/temp/async_copy_impl/async_copy_plan.md`
   - Extract feature name: `async_copy`
   - This will be provided to maestro for artifact management

### Scenario B: No File Path Provided

1. **Search Conversation Context**:
   - Look for recently discussed plan files
   - Check `.claude/temp/*/` directories for `*_plan_tdd.md` or `*_plan.md` files
   - Prioritize `*_plan_tdd.md` (TDD-formatted plans)

2. **Handle Ambiguity**:
   - If no plan files found: "No TDD plan file specified. Please provide the path to the plan you want to orchestrate, or run /tdd-plan first to create one."
   - If multiple candidates:
     ```
     Found multiple TDD plan files. Which one should I orchestrate?

     1. .claude/temp/async_copy_impl/async_copy_plan_tdd.md
     2. .claude/temp/memory_buffer_impl/memory_buffer_plan.md

     Enter number or provide full path.
     ```
   - Wait for user selection

3. **Extract Feature Name**: Once file is selected, extract feature name for artifact management

### Plan Format Validation

Before activating maestro, verify the plan has TDD structure:

**Required Elements** (check via simple grep/pattern matching):
- [ ] Phase sections (RED, GREEN, REFACTOR, VALIDATION)
- [ ] Checkpoint markers (`✅` or "Checkpoint:")
- [ ] Rollback triggers (`⚠️` or "Rollback:")
- [ ] Test files listed before implementation files

**Validation Results**:
- **Full TDD Format**: Plan has all required elements → Proceed to maestro activation
- **Partial TDD Format**: Plan has some elements but incomplete → Warn user and suggest `/tdd-plan` first
- **No TDD Format**: Plan lacks phase separation → Require `/tdd-plan` conversion first

```
Example warning for partial format:
⚠️  Plan appears incomplete for TDD orchestration.

Missing:
- Checkpoint definitions in GREEN phase
- Rollback triggers in REFACTOR phase

Recommendation: Run /tdd-plan on this file first to ensure maestro-compatible format.

Proceed anyway? [yes/no]
```

## Phase 2: Maestro Persona Activation

Once plan is validated, activate the maestro persona:

1. **Invoke Persona Command**:
   - Use SlashCommand tool with command: `/persona tdd`
   - This reads `.claude/personae/tdd-maestro.xml` and activates the persona

2. **Confirm Activation**:
   - Wait for persona activation confirmation message
   - Maestro will respond with: `[ACTIVATED] The TDD Maestro: Conductor of Quality`

3. **Proceed to Orchestration Handoff**

## Phase 3: Orchestration Handoff

After maestro is activated, provide context and request orchestration:

**Handoff Message Template**:
```
Welcome, Maestro. I'm handing off a TDD implementation plan for orchestration.

📋 Plan Details:
- Plan file: {absolute_plan_path}
- Feature name: {feature_name}
- Artifact directory: .claude/temp/{feature_name}_impl/

📍 Current Status:
{status_summary}

Your mission: Orchestrate this feature through complete TDD workflow with domain expert validation at each phase gate.

Please begin orchestration following your Symphonic TDD Process:
1. Check for existing artifacts at .claude/temp/{feature_name}_impl/
2. If artifacts exist: Resume from current phase per manifest.json
3. If no artifacts: Initialize artifact structure and begin at planning phase (or RED if plan already complete)
4. Invoke phase-specific agents (tdd-red, tdd-green, tdd-refactor) in IMPLEMENTATION mode
5. Invoke same agents in VALIDATOR MODE for quality gates between phases
6. Enforce phase boundaries and quality thresholds per your constraints
7. Synthesize progress and maintain visibility throughout workflow

The plan is ready for your review and orchestration.
```

**Status Summary Generation**:

Check `.claude/temp/{feature_name}_impl/manifest.json` if it exists:
- **No artifacts exist**: "No existing artifacts found - fresh start"
- **Artifacts exist, planning complete**: "Planning phase complete, ready for RED phase"
- **Artifacts exist, RED in progress**: "RED phase in progress at {progress}"
- **Artifacts exist, RED complete**: "RED phase complete and validated, ready for GREEN phase"
- **Artifacts exist, GREEN in progress**: "GREEN phase in progress at {progress}"
- **Artifacts exist, GREEN complete**: "GREEN phase complete and validated, ready for REFACTOR phase"
- **Artifacts exist, REFACTOR in progress**: "REFACTOR phase in progress at {progress}"

## Maestro Orchestration Flow (What Happens Next)

Once maestro receives the handoff, they will follow their Symphonic TDD Process:

### 1. Artifact Detection and Plan Review
- Check `.claude/temp/{feature_name}_impl/` for existing artifacts
- Read `manifest.json` to determine current phase
- Read the plan file to understand requirements
- Optionally: Apply plan_review_protocol if needed (maestro's decision)

### 2. Phase Orchestration
Maestro invokes agents and manages phase transitions:

**If Starting Fresh** (no artifacts):
```
Planning (if needed) → RED → GREEN → REFACTOR → VALIDATION
```

**If Resuming** (artifacts exist):
```
Resume from current phase → Continue to completion
```

**Phase Pattern** (for each phase):
```
1. Invoke phase agent in IMPLEMENTATION mode
2. Agent completes work and saves artifacts
3. Invoke same agent in VALIDATOR MODE
4. Read validation-report.md
5. Make gate decision (PASS/FAIL based on CRITICAL issues)
6. If PASS: Announce transition and invoke next phase
7. If FAIL: Work with agent to fix issues before proceeding
```

### 3. Quality Gate Enforcement
Maestro enforces strict quality thresholds:
- **RED → GREEN**: Tests must compile and fail correctly
- **GREEN → REFACTOR**: All tests must pass, zero regressions
- **REFACTOR → COMPLETE**: Tests still pass, code quality improved

### 4. Completion and Summary
Maestro synthesizes the complete journey:
```
Feature complete! Summary:
✅ Planning: {summary}
✅ Red: {summary} ({validation_outcome})
✅ Green: {summary} ({validation_outcome})
✅ Refactor: {summary} ({validation_outcome})

Result: Production-ready implementation with {coverage}% test coverage.
Artifacts: .claude/temp/{feature_name}_impl/
```

## Error Handling

### Plan File Issues
- **File not found**: Report error, ask for valid path
- **Unreadable file**: Report permissions or format issue
- **Not TDD format**: Suggest `/tdd-plan` conversion first

### Persona Activation Issues
- **Persona file missing**: Report if `.claude/personae/tdd-maestro.xml` not found
- **Activation failed**: Report error and suggest manual persona activation

### Orchestration Issues
- **Artifact corruption**: Maestro will detect and report via manifest.json
- **Phase agent failures**: Maestro handles via quality gate enforcement
- **Validation failures**: Maestro makes rollback decisions per protocol

## Examples

### Example 1: Orchestrate Fresh TDD Plan
```bash
User: /tdd-orchestrate .claude/temp/async_copy_impl/async_copy_plan_tdd.md

Claude: [Validates plan file - TDD format confirmed]
        [Extracts feature name: async_copy]
        [Invokes /persona tdd]

Maestro: [ACTIVATED] The TDD Maestro: Conductor of Quality

         Former technical lead specializing in orchestrated TDD workflows.

         Ready to apply their perspective to your task.

Claude: Welcome, Maestro. I'm handing off a TDD implementation plan for orchestration.

        📋 Plan Details:
        - Plan file: .claude/temp/async_copy_impl/async_copy_plan_tdd.md
        - Feature name: async_copy
        - Artifact directory: .claude/temp/async_copy_impl/

        📍 Current Status:
        No existing artifacts found - fresh start

        [Handoff message continues...]

Maestro: Understood. I'll orchestrate this async_copy feature through complete TDD workflow.

         [Checks for artifacts - none found]
         [Reviews plan - comprehensive and well-structured]
         [Initializes artifact structure]

         Plan reviewed - excellent structure for TDD workflow. Test scenarios are
         comprehensive, phase boundaries are clear. Initializing artifacts and
         proceeding to RED phase.

         [Invokes tdd-red agent in IMPLEMENTATION mode]
         [Orchestration continues through all phases...]
```

### Example 2: Resume Existing Orchestration
```bash
User: /tdd-orchestrate .claude/temp/async_copy_impl/async_copy_plan_tdd.md

Claude: [Validates plan file]
        [Checks artifacts - found existing at .claude/temp/async_copy_impl/]
        [Reads manifest.json - shows GREEN phase in progress]
        [Activates maestro persona]

Claude: Welcome, Maestro. Resuming orchestration of existing implementation.

        📋 Plan Details:
        - Plan file: .claude/temp/async_copy_impl/async_copy_plan_tdd.md
        - Feature name: async_copy

        📍 Current Status:
        GREEN phase in progress (RED phase complete and validated)

        [Handoff message...]

Maestro: Resuming async_copy orchestration from GREEN phase.

         [Reads manifest.json - GREEN phase started but not completed]
         [Invokes tdd-green agent to continue GREEN phase]
         [Continues orchestration from current state...]
```

### Example 3: Plan Needs TDD Conversion First
```bash
User: /tdd-orchestrate .claude/temp/feature_impl/feature_plan.md

Claude: [Validates plan file]
        [Checks TDD format - FAIL: missing phase boundaries and checkpoints]

        ⚠️  Plan is not in TDD-compatible format for maestro orchestration.

        Missing required elements:
        - Phase boundary definitions (RED/GREEN/REFACTOR)
        - Checkpoint markers for quality gates
        - Rollback trigger definitions

        This plan needs to be converted to TDD format first.

        Recommendation: Run /tdd-plan .claude/temp/feature_impl/feature_plan.md

        This will create a maestro-compatible version with strict phase separation
        and quality gates. Then you can orchestrate the TDD version.

        Would you like me to run /tdd-plan on this file now? [yes/no]

User: yes

Claude: [Invokes /tdd-plan command]
        [TDD conversion completes]
        [Asks user if they want to proceed with orchestration of TDD version]
```

### Example 4: Orchestrate from Context
```bash
User: /tdd-orchestrate

Claude: Searching conversation context for TDD plans...

        Found TDD plan from recent discussion:
        .claude/temp/async_copy_impl/async_copy_plan_tdd.md

        Is this the plan you want to orchestrate? [yes/no]

User: yes

Claude: [Validates plan]
        [Activates maestro]
        [Hands off to maestro for orchestration]
```

## Design Rationale

### Why Activate Maestro in Main Thread?

**Context Continuity**: Maestro orchestrates in the main conversation thread, maintaining full context and allowing user interaction throughout the workflow. This enables:
- User questions during orchestration
- Real-time progress visibility
- Interactive decision-making if ambiguities arise
- Seamless transition from planning to implementation

**Persona Immersion**: The maestro persona provides a consistent voice and methodology throughout all phases, creating a cohesive orchestration experience.

### Why Not Use Task Tool to Spawn Maestro Agent?

**Interactive Orchestration**: Maestro needs ongoing user interaction for:
- Plan review feedback
- Gate decision consultations if needed
- Progress reporting and transparency
- Handling unexpected situations

**Long-Running Process**: TDD orchestration can take hours with multiple phase transitions. Main thread orchestration is better suited for this than a single-shot agent invocation.

**Agent Coordination**: Maestro invokes multiple specialized agents (tdd-red, tdd-green, tdd-refactor) in both IMPLEMENTATION and VALIDATOR modes. This multi-agent coordination is more natural in the main thread.

### Maestro's Key Responsibilities

From the persona definition, maestro will:

1. **Detect Existing Work**: Check `.claude/temp/{feature}_impl/manifest.json` to resume if artifacts exist
2. **Plan Review** (optional): Apply plan_review_protocol if user explicitly asks or if plan has concerns
3. **Phase Orchestration**: Invoke phase-specific agents in IMPLEMENTATION mode
4. **Domain Expert Validation**: Invoke same agents in VALIDATOR MODE for quality gates
5. **Gate Decisions**: Read validation reports and decide PASS/FAIL based on CRITICAL issues
6. **Progress Synthesis**: Maintain holistic view and communicate status throughout
7. **Rollback Management**: Make rollback decisions if quality gates fail

### Integration with Existing Workflow

This command completes the TDD workflow trilogy:

1. **`/tdd-plan`**: Creates or converts plans to TDD format with maestro compatibility
2. **`/tdd-orchestrate`**: Activates maestro to orchestrate implementation with validation
3. **Phase agents**: `tdd-red`, `tdd-green`, `tdd-refactor` execute work under maestro's direction

## Important Notes

- **Maestro has autonomy**: Once activated, maestro makes orchestration decisions following their constraints and quality thresholds
- **Phase discipline is strict**: Maestro enforces RED → GREEN → REFACTOR sequence with no shortcuts
- **Validation is mandatory**: Every phase gets domain expert validation before gate transition
- **User maintains control**: User can intervene, ask questions, or request changes at any point
- **Artifacts provide audit trail**: Complete workflow history stored in `.claude/temp/{feature}_impl/`

## Success Criteria

The `/tdd-orchestrate` command succeeds when:
- Plan file is validated and feature name extracted
- Maestro persona is successfully activated
- Orchestration handoff is complete with all necessary context
- Maestro begins orchestration following Symphonic TDD Process
- User has clear visibility into what's happening next

The overall orchestration succeeds when:
- All phases complete with passing validation gates
- Feature is production-ready with comprehensive test coverage
- Zero regressions introduced
- Code quality meets project standards
- Complete audit trail exists in artifact directory
