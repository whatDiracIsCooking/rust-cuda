# Guide Directory Structure and Content

## Overview
The `guide/` directory contains mdBook-based documentation for GPU Computing with Rust using CUDA. It provides comprehensive coverage from beginner setup through advanced compiler internals, with 500+ pages organized into four main sections.

**Location:** `/home/lostica/projects/rust-cuda-root/rust-cuda/guide/`
**Build tool:** mdBook
**Source directory:** `guide/src/`

## Documentation Structure

### Root Level Files (Entry Points)
- **README.md** - Introduction to the rust-cuda guide
- **features.md** - Support matrix tracking Rust/CUDA features (✔️/🟨/❌ indicators)
- **faq.md** - Frequently asked questions

### Section 1: Guide (Practical Getting Started)
Located at `guide/src/guide/`
- **getting_started.md** - Prerequisites (CUDA SDK 11.2+, LLVM 7.x), toolchain setup, Docker support
- **compute_capabilities.md** - GPU compute capability gating and device-specific optimization
- **kernel_abi.md** - Kernel ABI specifications and calling conventions
- **safety.md** - Undefined behavior documentation, memory safety guarantees, data race semantics
- **tips.md** - Best practices and optimization techniques

### Section 2: CUDA Toolkit (GPU Computing Foundations)
Located at `guide/src/cuda/`
- **gpu_computing.md** - GPU computing fundamentals
- **pipeline.md** - CUDA compilation and execution pipeline

### Section 3: rustc_codegen_nvvm (Advanced - Compiler Backend)
Located at `guide/src/nvvm/`
- **README.md** - Section introduction (currently minimal)
- **technical/README.md** - Technical documentation overview
- **technical/backends.md** - Custom Rustc backends architecture
- **technical/nvvm.md** - rustc_codegen_nvvm internals and details
- **technical/types.md** - Type system and handling in NVVM backend
- **technical/debugging.md** - Debugging techniques for backend issues
- **technical/ptxgen.md** - PTX generation and optimization

## Key Content Areas

### Beginner Track
1. Introduction (README.md)
2. Getting Started (prerequisites, installation)
3. Features support matrix (understanding limitations)
4. Safety fundamentals

### Intermediate Track
- Compute capabilities and optimization
- Kernel ABI and calling conventions
- Tips and best practices
- CUDA toolkit fundamentals

### Advanced Track
- Compiler backend internals (rustc_codegen_nvvm)
- Custom backends
- NVVM type system
- Debugging backend issues
- PTX code generation

## Learning Progression Philosophy

The documentation follows a pyramid approach:
- **Width (Breadth):** Starts with broad "what is CUDA" concepts
- **Depth (Height):** Progresses from "how to use it" to "how it works internally"
- **Safety Focus:** Safety guarantees and UB documented early for user awareness
- **Advanced Topics:** Relegated to technical section for those needing implementation details

## Critical Files for Quick Reference

| File | Purpose | Audience |
|------|---------|----------|
| `getting_started.md` | Setup and requirements | All new users (START HERE) |
| `features.md` | Support matrix tracking | Developers planning features |
| `safety.md` | Undefined behavior spec | Kernel developers, library authors |
| `kernel_abi.md` | ABI guarantees | Custom kernel writers |
| `technical/backends.md` | Backend architecture | Contributors, advanced users |

## File Organization Details

- **book.toml** - mdBook configuration
- **SUMMARY.md** - Table of contents defining document structure and navigation
- **assets/** - Images and other static resources

## Search Tips for Future Sessions

- Hardware/setup questions → `getting_started.md`
- "Is feature X supported?" → `features.md`
- Memory safety concerns → `safety.md`
- Performance optimization → `tips.md` or `compute_capabilities.md`
- Compiler internals → `nvvm/technical/` subdirectory
