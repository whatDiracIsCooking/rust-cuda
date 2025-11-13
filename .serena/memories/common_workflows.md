# Common Development Workflows in Rust CUDA

This memory documents practical step-by-step workflows for common development tasks in the Rust CUDA project. Use this as a reference guide for recurring development activities.

---

## 1. Adding a New Example

Examples demonstrate Rust CUDA features and follow a consistent two-crate pattern: a host crate and a kernels crate.

### Directory Structure Pattern

```
examples/cuda/myexample/
├── Cargo.toml              # Host crate package definition
├── build.rs                # Build script orchestrating kernel compilation
├── src/
│   └── main.rs             # Host code (CPU-side)
└── kernels/
    ├── Cargo.toml          # Kernel crate package definition
    └── src/
        └── lib.rs          # Kernel code (GPU-side)
```

### Step-by-Step Workflow

1. **Create host crate directory:**
   ```bash
   mkdir -p examples/cuda/myexample/src
   mkdir -p examples/cuda/myexample/kernels/src
   ```

2. **Create host `Cargo.toml`:**
   ```toml
   [package]
   name = "myexample"
   version = "0.1.0"
   edition = "2024"

   [dependencies]
   cust = { path = "../../../crates/cust" }

   [build-dependencies]
   cuda_builder = { workspace = true, default-features = false }
   ```

3. **Create kernel crate `Cargo.toml`:**
   ```toml
   [package]
   name = "myexample-kernels"
   version = "0.1.0"
   edition = "2024"

   [dependencies]
   cuda_std = { path = "../../../../crates/cuda_std" }

   [lib]
   crate-type = ["cdylib", "rlib"]
   ```

4. **Create `build.rs` in host directory:**
   ```rust
   use std::env;
   use std::path;
   use cuda_builder::CudaBuilder;

   fn main() {
       println!("cargo::rerun-if-changed=build.rs");
       println!("cargo::rerun-if-changed=kernels");

       let out_path = path::PathBuf::from(env::var("OUT_DIR").unwrap());
       let manifest_dir = path::PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());

       CudaBuilder::new(manifest_dir.join("kernels"))
           .copy_to(out_path.join("kernels.ptx"))
           .build()
           .unwrap();
   }
   ```

5. **Create kernel code in `kernels/src/lib.rs`:**
   ```rust
   use cuda_std::prelude::*;

   #[kernel]
   #[allow(improper_ctypes_definitions, clippy::missing_safety_doc)]
   pub unsafe fn my_kernel(input: &[f32], output: *mut f32) {
       let idx = thread::index_1d() as usize;
       if idx < input.len() {
           let elem = unsafe { &mut *output.add(idx) };
           *elem = input[idx] * 2.0;
       }
   }
   ```

6. **Create host code in `src/main.rs`:**
   ```rust
   use cust::prelude::*;
   use std::error::Error;

   static PTX: &str = include_str!(concat!(env!("OUT_DIR"), "/kernels.ptx"));

   fn main() -> Result<(), Box<dyn Error>> {
       let _ctx = cust::quick_init()?;
       let module = Module::from_ptx(PTX, &[])?;
       let stream = Stream::new(StreamFlags::NON_BLOCKING, None)?;

       let input = vec![1.0f32; 1024];
       let gpu_input = input.as_slice().as_dbuf()?;
       let mut output = vec![0.0f32; 1024];
       let gpu_output = output.as_slice().as_dbuf()?;

       let kernel = module.get_function("my_kernel")?;
       let (_, block_size) = kernel.suggested_launch_configuration(0, 0.into())?;
       let grid_size = (1024u32).div_ceil(block_size);

       unsafe { launch!(kernel<<<grid_size, block_size, 0, stream>>>(&gpu_input, gpu_output.as_device_ptr() as *mut f32))? }

       gpu_output.copy_to(&mut output)?;
       stream.synchronize()?;

       println!("Result: {:?}", &output[0..10]);
       Ok(())
   }
   ```

7. **Add to root `Cargo.toml` workspace:**
   ```toml
   [workspace]
   members = [
       # ... existing members ...
       "examples/cuda/myexample",
       "examples/cuda/myexample/kernels",
   ]
   ```

8. **Build and run:**
   ```bash
   cargo build --example myexample --release
   cargo run --example myexample --release
   ```

### Important Patterns

- **Kernel macro:** Use `#[kernel]` attribute on GPU functions
- **PTX embedding:** Load compiled kernels via `include_str!` macro
- **Occupancy API:** Always use `suggested_launch_configuration()` for optimal performance
- **Stream usage:** Non-blocking streams enable asynchronous execution
- **Memory transfer:** Use `as_dbuf()` extension trait for host-to-device copies

---

## 2. Adding a New Crate to the Workspace

The workspace contains 21+ crates organized in layers: FFI bindings → core → runtime → domain-specific.

### Determining Crate Type

- **FFI Binding Crate** (`*-sys`): Raw C/C++ bindings via bindgen (feature-gated)
- **Core Crate** (`*_core`): Shared utilities for CPU/GPU (no_std compatible)
- **Host API Crate** (`cust`, `optix`, `cudnn`): High-level safe abstractions
- **Device Crate** (`cuda_std`, `optix_device`): GPU-side utilities
- **Build Crate** (`cuda_builder`): Build system integration

### Step-by-Step Workflow

1. **Create crate directory:**
   ```bash
   mkdir -p crates/mylib
   cd crates/mylib
   cargo init --lib
   ```

2. **Create `Cargo.toml` with proper metadata:**
   ```toml
   [package]
   name = "mylib"
   version = "0.1.0"
   edition = "2021"
   authors = ["Your Name <email@example.com>"]
   license = "MIT OR Apache-2.0"
   description = "Brief description"
   repository = "https://github.com/Rust-GPU/rust-cuda"

   [dependencies]
   # For host API: depend on cust
   cust = { path = "../cust" }
   # For device code: depend on cuda_std
   cuda_std = { path = "../cuda_std" }

   [features]
   default = []
   # Feature-gate optional dependencies
   my_feature = ["dep:some_dep"]
   ```

3. **Use workspace dependencies:**
   Replace path dependencies with workspace references where applicable:
   ```toml
   [dependencies]
   cuda_std = { path = "../cuda_std" }
   cuda_builder = { workspace = true }
   ```

4. **Register in root `Cargo.toml`:**
   ```toml
   [workspace]
   members = [
       # ... existing crates ...
       "crates/mylib",
   ]
   ```

5. **Implement following crate conventions:**
   - Keep FFI code in `*-sys` crates, safe wrappers in main crate
   - Use feature gates for optional functionality (e.g., `feature = "impl_glam"`)
   - Implement `no_std` support for device-side code
   - Provide proc-macro crates for ergonomic APIs (e.g., `cuda_std_macros`)

6. **Build and test:**
   ```bash
   cargo build -p mylib
   cargo test -p mylib
   ```

### Architectural Patterns

**Layered Organization:**
```
FFI Layer (cust_raw, *-sys)
    ↓
Core Layer (cust_core, cuda_std)
    ↓
Host API Layer (cust, optix)
    ↓
Domain-Specific Layer (blastoff, cudnn, gpu_rand)
```

**Dependency Rules:**
- Host-only crates depend on `cust`, `cust_core`, `cust_raw`
- Device crates depend on `cuda_std`, `cust_core` (in no_std mode)
- Feature-gate external dependencies (glam, vek, mint, half)
- Never introduce std dependencies in device crates

---

## 3. Updating CUDA Intrinsics

The intrinsics pipeline converts PDF documentation → JSON → Rust bindings for 300+ CUDA functions.

### Two-Stage Generation Pipeline

```
PDF Documentation → gen_libdevice_json.py → data/libdevice.json
                        ↓
                  gen_intrinsics.py → data/std_intrinsics.rs
```

### Step-by-Step Workflow

1. **Obtain libdevice PDF:**
   Place NVIDIA libdevice documentation at `scripts/data/libdevice.pdf`
   (Download from NVIDIA CUDA Toolkit documentation)

2. **Generate JSON representation:**
   ```bash
   cd scripts
   python3 gen_libdevice_json.py
   ```
   Output: `data/libdevice.json` (machine-readable intrinsics catalog)
   Also generates: `data/libdevice.txt` (debug artifact)

3. **Generate Rust bindings:**
   ```bash
   python3 gen_intrinsics.py
   ```
   Output: `data/std_intrinsics.rs` (Rust code with function bindings)

4. **Integrate into cuda_std:**
   The generated `std_intrinsics.rs` is included in `crates/cuda_std/src/`
   Verify inclusion in `lib.rs`:
   ```rust
   pub mod intrinsics {
       include!(concat!(env!("OUT_DIR"), "/std_intrinsics.rs"));
   }
   ```

5. **Test compilation:**
   ```bash
   cargo build -p cuda_std
   cargo test -p cuda_std
   ```

6. **Commit generated files:**
   ```bash
   git add scripts/data/libdevice.json scripts/data/std_intrinsics.rs
   git commit -m "chore: update CUDA intrinsics"
   ```

### Common Issues

- **PDF parsing fails:** Ensure PDF matches expected format from NVIDIA documentation
- **Invalid regex matches:** Check `gen_libdevice_json.py` regex pattern if NVIDIA format changes
- **Missing dependencies:** Requires `pdfplumber` Python package
  ```bash
  pip install pdfplumber
  ```

### Verification Steps

1. Compare generated `libdevice.json` with previous version
2. Verify all 300+ intrinsics extracted correctly
3. Build `cuda_std` to check for syntax errors in generated Rust
4. Run compiletest suite to validate intrinsic usage

---

## 4. Running Tests Properly

The test suite uses the **compiletest_rs framework** for compile-time validation across 66 UI tests organized by feature.

### Test Categories

- **Language Features** (47 tests): control flow, traits, constants, numeric ops
- **Hardware Primitives** (7 tests): atomics, threads, warps, shared memory
- **Math Libraries** (4 tests): glam integration, float extensions
- **Diagnostics** (4 tests): assembly validation, backend verification

### Test Execution Workflows

**1. Run All Compiletests:**
```bash
cargo compiletest
```
Tests compile GPU code against `nvptx64-nvidia-cuda` target (default: compute_70 architecture).

**2. Run Tests for Specific Architecture:**
```bash
cargo compiletest --target-arch compute_80,compute_90
```
Validates that code compiles for different GPU architectures.

**3. Run Specific Test Category:**
```bash
cargo compiletest lang::control_flow
```
Test filtering by name pattern.

**4. Update Golden Output Files (Blessed Mode):**
```bash
cargo compiletest --bless
```
Use when output changes are intentional. Regenerates expected output files.

**5. Run Full Test Suite:**
```bash
cargo test
cargo test --release
```
Runs compiletests plus any integration tests.

### Test Configuration Details

**Target Setup:**
- Target: `nvptx64-nvidia-cuda` (GPU bytecode format)
- Default Compute Capability: `compute_70` (specified in test harness)
- Build Artifacts: `target/compiletest-deps`, `target/compiletest-results`

**Environment Setup:**
The test harness automatically:
1. Sets up CUDA environment via `setup_cuda_environment()`
2. Configures rustc with NVVM backend integration
3. Provides extern prelude: `core`, `compiler_builtins`, `cuda_std`, `cuda_std_macros`
4. Compiles dependencies (cuda_std, macros, compiler_builtins)

**Test Output Validation:**
- UI tests compare actual compiler output against golden files
- Separate golden files for each compute architecture (e.g., `compute_70.stderr`)
- Disassembly tests validate generated NVPTX assembly

### Important Patterns

- **No runtime execution:** Tests verify compilation only, not GPU execution
- **Error testing:** Use `compile_fail` tests to verify error cases
- **Feature gating:** Tests run with/without optional features
- **Stage IDs:** Architecture-dependent output files allow multi-arch testing

### Common Issues & Solutions

**Issue:** Tests fail with "cannot find cuda_std"
```bash
# Solution: Ensure build dependencies are compiled first
cargo build -p cuda_std -p cuda_std_macros
```

**Issue:** Architecture-specific test failures
```bash
# Solution: Update golden files for specific architecture
cargo compiletest --target-arch compute_90 --bless
```

**Issue:** LLVM/NVVM setup problems
```bash
# Solution: Verify rust-toolchain.toml has correct components
rustup component list --installed | grep llvm-tools
```

---

## 5. Building with Different Compute Capabilities

GPU code must be compiled for specific NVIDIA GPU architectures (compute capabilities).

### Compute Capability Mapping

Common GPU architectures:
- **SM 7.0** (compute_70): Tesla V100, GeForce RTX 20 series
- **SM 7.5** (compute_75): GeForce RTX 20 super, Jetson
- **SM 8.0** (compute_80): Tesla A100, GeForce RTX 30 series
- **SM 8.6** (compute_86): GeForce RTX 30 mobile, Tesla A10
- **SM 9.0** (compute_90): Tesla H100, GeForce RTX 40 series

### Setting Compute Capability in cuda_builder

**In `build.rs`:**
```rust
use cuda_builder::CudaBuilder;

CudaBuilder::new(manifest_dir.join("kernels"))
    .copy_to(out_path.join("kernels.ptx"))
    .arch("compute_75")  // Target RTX 20 series
    .build()
    .unwrap();
```

**Available methods:**
- `.arch("compute_75")` - Single architecture
- `.arch("compute_70,compute_75,compute_80")` - Multiple architectures (creates fat binary)
- `.with_debug_info(DebugInfo::LineTables)` - Enable line-table debugging

### Environment Variable Override

```bash
# Override architecture via environment variable
CUDA_ARCH=compute_80 cargo build --example myexample

# Or set in shell
export CUDA_ARCH=compute_90
cargo build
```

### Testing Multiple Architectures

**For compiletests:**
```bash
# Test against multiple compute capabilities
cargo compiletest --target-arch compute_70,compute_80,compute_90
```

**For examples:**
```bash
# Build example for specific architecture
CUDA_ARCH=compute_75 cargo build --example vecadd --release
```

### Default Architecture

If not specified, `rustc_codegen_nvvm` defaults to:
```rust
CUDA_ARCH=520  // Equivalent to compute_52
```

This is set in `crates/rustc_codegen_nvvm/build.rs` if not overridden by cuda_builder.

### Fat Binaries

Create single PTX file supporting multiple architectures:
```rust
CudaBuilder::new(manifest_dir.join("kernels"))
    .copy_to(out_path.join("kernels.ptx"))
    .arch("compute_70,compute_75,compute_80,compute_90")
    .build()
    .unwrap();
```

The resulting PTX can run on any specified GPU, optimized for each architecture.

---

## 6. Using xtask Commands

The xtask workspace utility provides development-time debugging tools via `cargo xtask`.

### Available Commands

**Primary: extract_llfns**
Decomposes compiled LLVM IR files into individual function files for debugging.

```bash
cargo xtask extract_llfns <input.ll> <output_directory>
```

**Behavior:**
1. Reads LLVM IR file (`.ll` format)
2. Parses function definitions using regex pattern: `define .*(_Z.*?)(\(|\")`
3. Uses `llvm-extract` tool to isolate each function with dependencies
4. Processes all functions in parallel using rayon
5. Outputs each function as separate `.ll` file
6. Sorts functions by size (shortest processed first)

### Use Cases

**Scenario 1: Debugging GPU Compilation Pipeline Failures**
```bash
# When rustc_codegen_nvvm fails on a kernel:
# 1. Get LLVM IR from failed compilation
cargo build 2>&1 | grep "\.ll" > ir_file.ll

# 2. Extract individual functions
cargo xtask extract_llfns ir_file.ll debug_functions/

# 3. Analyze which functions fail
ls -lah debug_functions/ | sort -k5  # Smallest first
```

**Scenario 2: Testing NVVM Compiler on Specific Functions**
```bash
# Isolate problematic function and test in isolation
cargo xtask extract_llfns compiled.ll extracted/
# Then manually test: llvm-as extracted/fn_name.ll && nvvm-ir-to-ptx extracted/fn_name.bc
```

### Extending xtask for Custom Debugging

The `extract_llfns.rs` implementation includes a hook for custom debugging logic:

```rust
fn run_command_for_each_fn() -> Result<(), Box<dyn Error>> {
    // Modify this function to test custom debugging commands
    // Example: run llvm-verify, custom analysis, etc.
}
```

**Important:** Remove any modifications before committing (noted in code comment).

### Dependencies

xtask uses minimal dependencies:
- **pico-args** (0.4.2): Lightweight argument parsing
- **rayon** (1.10): Parallel iteration
- **regex** (1.11.1): LLVM IR pattern matching

No runtime dependencies are introduced by xtask.

---

## 7. Common Build Patterns and Conventions

Standard patterns used throughout the Rust CUDA project.

### Kernel Definition Pattern

```rust
// kernels/src/lib.rs
use cuda_std::prelude::*;

#[kernel]
#[allow(improper_ctypes_definitions, clippy::missing_safety_doc)]
pub unsafe fn my_kernel(input: &[f32], output: *mut f32, scalar: f32) {
    let idx = thread::index_1d() as usize;
    if idx < input.len() {
        let elem = unsafe { &mut *output.add(idx) };
        *elem = input[idx] * scalar;
    }
}
```

**Key elements:**
- `#[kernel]` attribute marks GPU entry point
- `unsafe` keyword acknowledges raw pointer operations
- `#[allow]` suppresses expected warnings for raw FFI
- Parameters: slices for arrays, raw pointers for mutable output
- `thread::index_1d()` gets thread index in 1D grid

### Host-Side Launch Pattern

```rust
use cust::prelude::*;

static PTX: &str = include_str!(concat!(env!("OUT_DIR"), "/kernels.ptx"));

fn main() -> Result<(), Box<dyn Error>> {
    // 1. Initialize CUDA context
    let _ctx = cust::quick_init()?;

    // 2. Load module from PTX
    let module = Module::from_ptx(PTX, &[])?;

    // 3. Create stream for execution
    let stream = Stream::new(StreamFlags::NON_BLOCKING, None)?;

    // 4. Allocate and copy host data to device
    let input = vec![1.0f32; 1024];
    let gpu_input = input.as_slice().as_dbuf()?;
    let mut output = vec![0.0f32; 1024];
    let gpu_output = output.as_slice().as_dbuf()?;

    // 5. Get kernel function
    let kernel = module.get_function("my_kernel")?;

    // 6. Determine optimal launch configuration
    let (_, block_size) = kernel.suggested_launch_configuration(0, 0.into())?;
    let grid_size = (1024u32).div_ceil(block_size);

    // 7. Launch kernel
    unsafe {
        launch!(kernel<<<grid_size, block_size, 0, stream>>>
            (&gpu_input, gpu_output.as_device_ptr() as *mut f32, 2.0))?
    }

    // 8. Copy results back
    gpu_output.copy_to(&mut output)?;

    // 9. Synchronize before cleanup
    stream.synchronize()?;

    Ok(())
}
```

### Build Script Pattern

```rust
// build.rs
use std::env;
use std::path;
use cuda_builder::CudaBuilder;

fn main() {
    println!("cargo::rerun-if-changed=build.rs");
    println!("cargo::rerun-if-changed=kernels");

    let out_path = path::PathBuf::from(env::var("OUT_DIR").unwrap());
    let manifest_dir = path::PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());

    CudaBuilder::new(manifest_dir.join("kernels"))
        .copy_to(out_path.join("kernels.ptx"))
        .arch("compute_75")
        .build()
        .unwrap();
}
```

**Key elements:**
- `cargo::rerun-if-changed` triggers rebuild on file changes
- `OUT_DIR` environment variable for build artifacts
- `CudaBuilder` orchestrates kernel compilation
- `.copy_to()` places PTX in location for `include_str!`

### Feature-Gating Pattern

```toml
[features]
default = []
impl_glam = ["dep:glam"]
impl_half = ["dep:half"]

[dependencies]
glam = { version = "0.25", optional = true }
half = { version = "2.4", optional = true }
```

### Crate Dependency Pattern

**Host-side dependencies:**
```rust
// Cargo.toml
[dependencies]
cust = { path = "../../../crates/cust" }
cust_raw = { path = "../../../crates/cust_raw", features = ["cublas"] }
```

**Device-side dependencies:**
```rust
// kernels/Cargo.toml
[dependencies]
cuda_std = { path = "../../../../crates/cuda_std" }
gpu_rand = { path = "../../../../crates/gpu_rand" }
```

### Testing Correctness Pattern

```rust
// Compare GPU results with CPU reference
fn validate_results(gpu_result: &[f32], cpu_result: &[f32]) {
    for (gpu, cpu) in gpu_result.iter().zip(cpu_result.iter()) {
        assert!((gpu - cpu).abs() < 1e-5, "Result mismatch: {} vs {}", gpu, cpu);
    }
}
```

### Error Handling Pattern

```rust
// Use Result-based error handling
fn run_kernel() -> Result<Vec<f32>, Box<dyn std::error::Error>> {
    let _ctx = cust::quick_init()?;
    let module = Module::from_ptx(PTX, &[])?;
    // ... operations that may fail ...
    Ok(results)
}
```

---

## Quick Reference: Command Cheatsheet

```bash
# Building
cargo build                                    # Standard build
CUDA_ARCH=compute_80 cargo build              # Specific architecture
cargo build --example vecadd --release         # Build specific example

# Testing
cargo test                                    # Full test suite
cargo compiletest                            # GPU compilation tests
cargo compiletest --target-arch compute_90   # Architecture-specific tests
cargo compiletest --bless                    # Update golden files
cargo compiletest lang::control_flow         # Specific test category

# Development utilities
cargo xtask extract_llfns input.ll output/   # Debug LLVM IR

# Intrinsics generation
cd scripts && python3 gen_libdevice_json.py  # PDF → JSON
cd scripts && python3 gen_intrinsics.py      # JSON → Rust

# Adding to workspace
cargo add -p mylib some-crate                # Add dependency to specific crate
cargo build -p mylib --release               # Build specific crate

# Checking
cargo clippy --all-targets
cargo fmt --all
cargo doc --open
```

---

## Common Gotchas & Tips

1. **PTX Embedding:** Always use `include_str!` at compile time, not runtime file reading
2. **Stream Synchronization:** Explicitly call `stream.synchronize()` before using GPU results
3. **Kernel Grid Sizes:** Use occupancy API instead of guessing launch configuration
4. **Compute Capability:** Code compiled for compute_75 won't run on compute_70 GPUs
5. **Build Scripts:** Always set `cargo::rerun-if-changed` for proper incremental builds
6. **Feature Gating:** External math libraries should be feature-gated to keep default small
7. **Device Pointers:** Convert `DeviceBuffer` to raw pointers only in unsafe blocks
8. **Memory Transfers:** Use `as_dbuf()` for automatic allocation and synchronous copy
9. **Kernel Parameters:** Raw slices work; complex types need careful marshalling
10. **Testing:** Compile-time tests catch most GPU code issues before runtime

---

## File Locations Reference

| Task | File | Location |
|------|------|----------|
| Workspace config | `Cargo.toml` | `/` |
| Toolchain version | `rust-toolchain.toml` | `/` |
| Intrinsics generation | `gen_intrinsics.py` | `scripts/` |
| Libdevice parsing | `gen_libdevice_json.py` | `scripts/` |
| Kernel stdlib | `cuda_std` | `crates/cuda_std/` |
| Build integration | `cuda_builder` | `crates/cuda_builder/` |
| Example template | `vecadd` | `examples/cuda/vecadd/` |
| Compilation tests | `compiletests` | `tests/compiletests/` |
| xtask utilities | `xtask` | `xtask/` |
