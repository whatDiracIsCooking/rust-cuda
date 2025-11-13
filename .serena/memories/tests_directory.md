# Tests Directory Overview

## Testing Strategy

The `tests/` directory houses a sophisticated compile-time testing infrastructure focused on validating CUDA kernel compilation correctness. The test suite employs the **compiletest_rs framework**, which mirrors Rust's built-in compiler test infrastructure, enabling validation of compiler output without runtime execution.

**Key Philosophy**: Tests verify that code compiles correctly or fails with expected errors—not whether kernels execute successfully. This focus on compile-time correctness ensures robust language feature support in the CUDA environment.

## Test Framework Configuration

The test harness (`tests/compiletests/src/main.rs`) manages:
- **CUDA Target Architecture**: `nvptx64-nvidia-cuda` (GPU binary format)
- **Configurable Compute Capabilities**: Default `compute_70` with multi-arch support via `--target-arch` flag
- **Build Artifacts**: Separated into `target/compiletest-deps` and `target/compiletest-results`
- **Compilation Flags**: Unified rustc configuration including:
  - NVVM codegen backend integration
  - Edition 2021 with no_std/abi_ptx attributes
  - Extern prelude for core, compiler_builtins, cuda_std, cuda_std_macros

## Test Categories (66 Total UI Tests)

### Language Features (47 tests, ~71%)
- **Control Flow** (8): if/else chains, loops, for ranges, continue/break patterns
- **Core Module Traits** (12): array operations, pointer operations, memory intrinsics, references
- **Constants** (2): constant memory behavior, shallow references
- **Numeric Operations** (2): f32, u32 primitive operations and overloads
- **Compile Failures** (1): error checking (e.g., invalid file I/O in kernels)
- **General** (1): hello_world kernel validation

### Hardware Primitives (7 tests, ~11%)
- **Atomic Operations** (2): atomic memory operations
- **Thread Operations** (2): thread-level utilities
- **Warp Operations** (2): warp-level synchronization and utilities
- **Shared Memory** (1): shared memory access patterns

### Math Libraries (4 tests, ~6%)
- **Glam Support** (3): vec3/mat4 operations, SIMD vector math
- **Float Extensions** (1): extended floating-point operations

### Diagnostic/Experimental (4 tests, ~6%)
- **Disassembly Tests** (4): NVPTX assembly validation and backend verification

## What Is Tested

- Kernel compilation with `#[kernel]` attribute
- Rust language features: control flow, generics, pattern matching
- CUDA std library APIs: synchronization, memory operations
- Third-party math library integration (glam)
- Error cases: invalid operations should fail compilation
- Binary correctness: generated NVPTX code validation

## What Is NOT Tested

- **Runtime Behavior**: No actual kernel execution or GPU memory operations
- **Performance**: No benchmarking or optimization validation
- **Device Synchronization**: Tests run on nvptx64 target, not actual hardware
- **Multi-GPU Scenarios**: Focused on single-device kernel correctness
- **Integration**: Host-device interaction tested separately outside compiletests

## Test Execution Configuration

- **Mode**: UI testing (output-based comparison)
- **Bless Flag**: `--bless` to update golden output files
- **Filters**: CLI support for selective test execution
- **Stage IDs**: Architecture-dependent output validation (e.g., compute_70 vs compute_90)
- **Build Dependencies**: Separate compilation of cuda_std, macros, and compiler_builtins
- **CUDA Environment**: Setup via `setup_cuda_environment()` before test runs

## Usage

Run compiletests via cargo alias:
```bash
cargo compiletest
cargo compiletest --target-arch compute_80,compute_90
cargo compiletest --bless
cargo compiletest lang::control_flow
```
