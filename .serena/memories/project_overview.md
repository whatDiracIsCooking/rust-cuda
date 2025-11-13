# Rust CUDA Project - Master Overview

## Project Summary

**Rust CUDA** is an ecosystem of Rust libraries and tools for writing and executing high-performance GPU code using NVIDIA's CUDA Toolkit. The project brings Rust's safety guarantees and ergonomic design to GPU computing, providing both low-level compiler infrastructure and high-level abstractions for CUDA programming.

**Status:** Actively developed (2025) - Recently rebooted after dormancy. Early development stage with active community contributions.

**License:** Dual-licensed under Apache 2.0 + MIT

**Toolchain:** Nightly Rust (channel: `nightly-2025-08-04`)

## Compilation Pipeline Architecture

The Rust CUDA project implements a custom GPU compilation chain:

```
Rust Source Code
     ↓
rustc + rustc_codegen_nvvm Backend
     ↓
NVVM IR (LLVM subset via libnvvm)
     ↓
PTX (Parallel Thread Execution)
     ↓
CUDA GPU Execution
```

**Key Architecture Layers:**
- **Frontend:** Standard Rust compiler with custom backend
- **IR Layer:** NVVM IR (subset of LLVM IR) targeting `libnvvm` library
- **Code Gen:** Generates highly optimized PTX bytecode for GPUs
- **Runtime:** CUDA Driver API for kernel launch and memory management

This architecture differs from the problematic LLVM PTX backend by providing a specialized solution with better compatibility and performance.

## Directory Structure

### Core Directories

#### `/crates/` - Main Library Ecosystem (21 crates)

**Compiler & Core Infrastructure:**
- `rustc_codegen_nvvm` - The custom rustc backend that generates NVVM IR
- `rustc_codegen_nvvm_macros` - Procedural macros for the compiler backend
- `cuda_std` - GPU-side standard library with thread utilities, intrinsics, and warp operations
- `cuda_std_macros` - GPU-side procedural macros

**CUDA Runtime & Bindings:**
- `cust` - High-level CPU-side CUDA wrapper (primary user-facing API)
- `cust_core` - Core CUDA functionality
- `cust_raw` - Raw FFI bindings to CUDA Driver API
- `cust_derive` - Derive macros for CUDA types

**Specialized Libraries:**
- `cudnn` - Deep neural network primitives GPU-accelerated wrapper
- `cudnn-sys` - Low-level CUDNN bindings
- `optix` - OptiX raytracing engine wrapper (CPU-side)
- `optix-sys` - Low-level OptiX bindings
- `optix_device` - OptiX device-side utilities
- `optix_device_macros` - OptiX procedural macros
- `gpu_rand` - GPU-friendly random number generation (xoroshiro RNGs)

**Build & Compilation Tools:**
- `cuda_builder` - Build script generation for compiling GPU code
- `ptx_compiler` - PTX code compilation utilities
- `ptx` - PTX bytecode handling
- `nvvm` - NVVM IR abstraction and utilities
- `blastoff` - Project launcher and setup utilities

#### `/examples/cuda/` - Example Applications

Comprehensive examples demonstrating GPU programming:
- `vecadd/` - Vector addition (foundational example)
- `gemm/` - General matrix multiplication
- `path_tracer/` - GPU-accelerated path tracing renderer
- `sha2_crates_io/` - SHA-2 cryptographic hashing on GPU

Each example follows a two-crate pattern:
- Main crate (CPU-side host code)
- Separate `kernels/` crate (GPU device code)

#### `/examples/optix/` - OptiX Ray Tracing Examples

Examples utilizing NVIDIA's OptiX engine for ray tracing and rendering on GPUs.

#### `/samples/` - NVIDIA CUDA Samples Port

Ports of official NVIDIA CUDA samples to Rust, including:
- `/samples/introduction/` - Introductory samples
  - `async_api/` - Asynchronous CUDA API usage with kernel crate

These serve as learning resources and reference implementations.

#### `/guide/` - User Documentation

mdBook-based documentation source (Markdown):
- Building guide for developers
- API reference documentation
- Getting started tutorials
- Feature descriptions
- Published at: https://rust-gpu.github.io/rust-cuda/

Build configuration: `book.toml`

#### `/container/` - Containerized Environments

Docker/Podman configurations for isolated development:
- `ubuntu24-cuda12/` - Ubuntu 24.04 with CUDA Toolkit 12
- `ubuntu22-cuda12/` - Ubuntu 22.04 with CUDA Toolkit 12
- Other distribution variants

Used for consistent CI/CD environments and developer onboarding.

#### `/tests/` - Test Suite

- `compiletests/` - Compile-time behavior tests
  - Tests GPU compilation pipeline correctness
  - Includes dependency helper crate
- Integration tests for runtime behavior

#### `/scripts/` - Build Automation

- `gen_intrinsics.py` - Generate GPU intrinsic function bindings
- `gen_libdevice_json.py` - Parse NVIDIA libdevice into JSON format
- `download_ci_optix.bash` - CI script for OptiX SDK download
- `data/` - Static data files (libdevice, intrinsic definitions)

#### `/xtask/` - Cargo Workspace Task Automation

Development utility following Rust xtask pattern:
- **Primary Task:** `extract_llfns` - Decompose LLVM IR files for debugging
- Command: `cargo xtask extract_llfns <input.ll> <output_dir>`
- Parallel processing of GPU compilation issues
- **See:** `.serena/memories/xtask_directory.md`

### Configuration Files

**Root Directory:**
- `Cargo.toml` - Workspace definition with 21+ member crates
- `Cargo.lock` - Dependency version lock file
- `rust-toolchain.toml` - Specifies nightly Rust + required components
- `rustfmt.toml` - Code formatting configuration (empty, uses defaults)
- `README.md` - Project overview and quick start
- `LICENSE-APACHE`, `LICENSE-MIT` - Dual license files
- `CODEOWNERS` - GitHub code ownership configuration
- `katex-header.html` - Math rendering for documentation

**Development Environment:**
- `.devcontainer.json` - VS Code dev container configuration (Ubuntu 24.04)
- `.mcp.json` - MCP server configuration
- `.cargo/` - Cargo configuration directory
- `.claude/` - Claude Code project instructions
- `.serena/` - Serena analysis tool configuration and memories
- `.github/workflows/` - CI/CD pipeline definitions

## CI/CD Pipeline

GitHub Actions workflows in `.github/workflows/`:

- `ci_linux.yml` - Linux multi-version testing
  - Multiple CUDA versions and Rust channels
  - Compilation, documentation, and lint checks

- `ci_windows.yml` - Windows CI pipeline
  - CUDA Path setup for CodeGen backend exposure
  - Windows-specific build validation

- `container_images.yml` - Docker image building and publishing
  - Automated containerized environment distribution

- `deploy_guide.yml` - Documentation deployment
  - Publishes mdBook guide to GitHub Pages

## Build System

**Primary Build Method:**
```bash
cargo build                    # Standard Rust build
cargo xtask extract_llfns ...  # GPU debugging utility
```

**Requirements:**
- CUDA Toolkit 12+ installed and discoverable
- Nightly Rust (2025-08-04 or compatible)
- LLVM tools and Rust source components (specified in rust-toolchain.toml)
- For OptiX: Optional SDK path via `OPTIX_ROOT` / `OPTIX_ROOT_DIR`

**Workspace Configuration:**
- 21+ member crates organized by functionality
- Shared dependencies via `[workspace.dependencies]`
- `cuda_builder` and `cuda_std` marked for workspace use
- Separate compilation profiles (dev: cuda_std optimized)

## Key Technologies

**Compiler Infrastructure:**
- LLVM/NVVM IR toolchain
- Custom rustc backend (not standard LLVM PTX)
- libnvvm library for IR-to-PTX compilation

**GPU Programming:**
- CUDA Driver API (lower-level control than Runtime API)
- Thread block utilities and warp intrinsics
- Async stream support for concurrent kernels

**High-Level Features:**
- RAII-based resource management
- Result-based error handling
- Safe abstractions over unsafe GPU operations
- Procedural macros for GPU code

## Related Projects & History

Historical context of Rust GPU computing:
- 2016: glassful (Rust → GLSL)
- 2017: inspirv-rust (experimental MIR → SPIR-V)
- 2018: nvptx (LLVM PTX backend - problematic)
- 2020: accel, rlsl (SPIR-V predecessors)
- 2020: rust-gpu (SPIR-V shaders - sister project using same mechanism)
- 2025: Rust CUDA reboot (modern NVVM-based approach)

## Development Status & Contributions

**Active Areas:**
- GPU kernel compilation pipeline
- CUDA standard library enhancements
- OptiX integration
- Documentation and examples
- CI/CD improvements and platform support

**Community Involvement:** Open to contributions; dual-licensed for flexibility.

**Early Development Caveat:** Project expects bugs, safety issues, and incomplete features. Use cautiously in production.
