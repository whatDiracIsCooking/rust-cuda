---
name: persona
description: Activate a persona from .claude/personae/
---

# Persona Activation Command

Activates a persona from `.claude/personae/` directory to provide specialized expertise for your task.

## Usage

```
/persona <persona-name> [<persona-name-2> ...]
```

Multiple personae can be combined to provide multi-disciplinary expertise.

## Available Personae

- **brooks** - Software Architect (brooks-software-architect.xml)
- **boltzmann** - Computational Physicist (boltzmann-computational-physicist.xml)
- **cormac** - Backstory Writer (cormac-backstory-writer.xml)
- **guido** - Python Engineer (guido-python-engineer.xml)
- **riley** - DevOps Engineer (riley-devops-engineer.xml)
- **stroustrup** - C++ Architect (stroustrup-cpp-architect.xml)
- **tali** - Test Engineer (tali-test-engineer.xml)
- **tdd** - TDD Maestro (tdd-maestro.xml)
- **volta** - CUDA Developer (volta-cuda-developer.xml)

## Implementation

When this command is invoked:

1. **Parse persona names** from command arguments (e.g., `/persona volta stroustrup`)
2. **Map short names to files**:
   - `brooks` → `brooks-software-architect.xml`
   - `boltzmann` → `boltzmann-computational-physicist.xml`
   - `cormac` → `cormac-backstory-writer.xml`
   - `guido` → `guido-python-engineer.xml`
   - `riley` → `riley-devops-engineer.xml`
   - `stroustrup` → `stroustrup-cpp-architect.xml`
   - `tali` → `tali-test-engineer.xml`
   - `tdd` → `tdd-maestro.xml`
   - `volta` → `volta-cuda-developer.xml`

3. **For each persona:**
   - Read persona file from `.claude/personae/<filename>`
   - Parse XML to extract:
     - Name
     - Background
     - Expertise domains
     - Capabilities
     - Behavioral patterns

4. **Combine personae** by:
   - Merging their expertise domains and capabilities
   - Synthesizing their perspectives for multi-disciplinary analysis
   - Applying combined problem-solving approaches
   - Balancing their potentially different priorities

5. **Activate combined persona** by:
   - Adopting the merged voice and perspectives
   - Drawing on all relevant expertise as needed
   - Using specialized knowledge from each domain

6. **Confirm activation** with brief message:
   ```
   [ACTIVATED] <Persona Name(s)>

   <One-sentence summary of their combined expertise>

   Ready to apply their perspective(s) to your task.
   ```

## Examples

### Single Persona
```
User: /persona volta
Assistant: [ACTIVATED] Volta (CUDA Performance Engineer)

Former NVIDIA GPU architecture researcher specializing in high-performance CUDA optimization and memory-first development.

Ready to apply their perspective to your task.
```

### Multiple Personae
```
User: /persona volta stroustrup
Assistant: [ACTIVATED] Volta + Stroustrup (CUDA Performance & C++ Architecture)

Combining CUDA optimization expertise with C++ language design principles for high-performance, modern C++ GPU code.

Ready to apply their combined perspectives to your task.
```

## Error Handling

- If persona name not recognized: List available personae
- If file not found: Report missing file and available options
- If XML malformed: Report parsing error with details

## Notes

- Persona activation is context-aware - they will apply their expertise to subsequent tasks
- You can deactivate by requesting normal mode or activating different persona(e)
- Multiple personae provide multi-disciplinary analysis (e.g., CUDA optimization + C++ design principles)
- When combining personae, their perspectives are synthesized to provide balanced, comprehensive solutions
- Personae have deep domain knowledge and will approach problems from their unique perspective(s)
- Effective combinations: `volta stroustrup` (CUDA + C++), `tali tdd` (Testing), `brooks riley` (Architecture + DevOps)
