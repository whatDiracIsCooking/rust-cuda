# CUDA Compilation Pipeline in Rust CUDA

## Overview

The Rust CUDA project implements a custom GPU compilation pipeline that transforms Rust code into GPU-executable PTX bytecode. This process differs fundamentally from traditional C/C++ CUDA compilation by using Rust's compiler infrastructure and a specialized NVVM-based backend.

**Pipeline Flow:**
```
Rust Source Code (Device Crate)
    ↓ (rustc with custom backend)
rustc_codegen_nvvm (MIR → NVVM IR)
    ↓
NVVM IR (subset of LLVM IR)
    ↓ (libnvvm optimization & compilation)
PTX Assembly (Parallel Thread Execution)
    ↓ (loaded at runtime)
CUDA Driver API (launches kernels on GPU)
```

---

## Stage 1: Rust Source Code Organization

### Host vs Device Code

Rust CUDA distinguishes between two execution contexts:

**Host Code** (CPU-side):
- Uses `cust` crate for high-level CUDA API
- Allocates GPU memory, manages streams, launches kernels
- Uses standard Rust features (std library, networking, etc.)
- Typical target: `x86_64-unknown-linux-gnu` or `x86_64-pc-windows-msvc`

**Device Code** (GPU-side):
- Uses `cuda_std` crate (GPU-compatible standard library)
- No_std, embedded-like environment
- Limited to GPU-safe constructs (no dynamic allocation, limited intrinsics)
- Compiled with custom target: `nvptx64-nvidia-cuda`

### Multi-Crate Pattern

Projects typically follow a two-crate structure:

```
my_project/
├── src/              # Host code (CPU side)
│   └── main.rs       # Kernel launcher, memory management
├── kernels/          # Device code (GPU side)
│   └── src/lib.rs    # Actual kernel functions
├── build.rs          # Build script orchestrating compilation
└── Cargo.toml        # Main crate dependencies
```

**Example: VecAdd**
- `examples/cuda/vecadd/`: Host binary that manages execution
- `examples/cuda/vecadd/kernels/`: Device code with the actual vector addition kernel

---

## Stage 2: Build Script Integration (cuda_builder)

### Purpose

`cuda_builder` is a build-time crate that orchestrates GPU kernel compilation. It runs in `build.rs` scripts to transform device code into PTX files before the host binary is built.

### Typical build.rs Usage

```rust
use cuda_builder::CudaBuilder;
use std::path;

fn main() {
    let out_path = path::PathBuf::from(env::var("OUT_DIR").unwrap());
    let manifest_dir = path::PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());

    CudaBuilder::new(manifest_dir.join("kernels"))
        .copy_to(out_path.join("kernels.ptx"))
        .build()
        .unwrap();
}
```

### CudaBuilder Configuration

Key builder options:

| Option | Purpose | Default |
|--------|---------|---------|
| `.release(bool)` | Optimize for performance | `true` |
| `.arch(NvvmArch)` | Target GPU compute capability | `Compute61` |
| `.copy_to(path)` | Output PTX file location | None |
| `.nvvm_opts(bool)` | Enable libnvvm optimizations | `true` (with release) |
| `.override_libm()` | Use libdevice math functions | `true` |
| `.use_constant_memory_space()` | Place statics in constant memory | `false` |
| `.emit_llvm_ir()` | Debug: output LLVM IR | `false` |
| `.ftz()`, `.fast_sqrt()`, `.fast_div()` | Floating-point performance tradeoffs | Disabled |

### Architecture Selection (NvvmArch)

The architecture determines GPU compatibility and feature availability:

```rust
CudaBuilder::new(kernels_dir)
    .arch(NvvmArch::Compute70)  // Target Volta (CC 7.0+)
    .build()
```

**Architecture Variants (CUDA 12.9+):**
- **Base** (e.g., `Compute70`): Forward-compatible across all future GPUs
- **Family 'f' suffix** (e.g., `Compute100f`): Compatible within same major version
- **Architecture 'a' suffix** (e.g., `Compute100a`): Only runs on exact compute capability

**Default:** `Compute61` (Pascal era) - good compatibility, supports modern features (f64 atomics, half precision)

---

## Stage 3: rustc_codegen_nvvm Backend

### Architecture

The `rustc_codegen_nvvm` crate is a dynamically loaded rustc backend that implements the actual code generation. It's one of several available rustc backends:

- `rustc_codegen_llvm` (default, general-purpose)
- `rustc_codegen_nvvm` (NVIDIA GPU targets)
- `rustc_codegen_spirv` (shader compilation)
- `rustc_codegen_cranelift`, `rustc_codegen_gcc` (other targets)

### How It Works

1. **Backend Discovery**: `cuda_builder` locates the compiled `rustc_codegen_nvvm` dylib
   - Searches workspace target directory
   - Can auto-build if not found (with feature flag)

2. **Rustc Invocation**:
   ```bash
   cargo build --lib \
     -Zcodegen-backend=/path/to/librustc_codegen_nvvm.so \
     --target=nvptx64-nvidia-cuda \
     -Zbuild-std=core,alloc
   ```

3. **MIR Lowering**: Converts Rust MIR (Mid-Level Intermediate Representation) to LLVM-like IR operations

4. **NVVM-Specific Transformations**:
   - Removes unsupported LLVM features
   - Enforces NVVM IR restrictions
   - Synthesizes compute capability target features for conditional compilation

### Target Features and Conditional Compilation

The backend automatically enables `target_feature` flags based on selected architecture:

```rust
#[cfg(target_feature = "compute_70")]
{
    // Code only compiled when targeting CC 7.0+
    // Automatically enabled when .arch(Compute70) is used
}

#[cfg(target_feature = "compute_75")]
{
    // Only enabled for CC 7.5+
}
```

**Feature Hierarchy:**
- Compute70 enables: compute_35, compute_37, compute_50, compute_52, ..., compute_70
- Allows libraries to gate features on minimum compute capability

---

## Stage 4: NVVM IR (libnvvm Input)

### What is NVVM IR

NVVM IR is a **restricted subset of LLVM IR** optimized for GPU execution. It's the format that libnvvm (NVIDIA's proprietary IR compiler) accepts.

### NVVM IR Restrictions

Not all LLVM IR is valid NVVM IR:

- **Irregular integers** (i4, i111, etc.) unsupported - will segfault
- **Restricted intrinsics** - GPU operations are limited to documented NVVM intrinsics
- **No dots in global names** - naming convention requirement
- **Limited linkage types** - some LLVM linkage not supported
- **PTX calling convention** - all functions use PTX ABI (function ABIs ignored)

### rustc_codegen_nvvm Output

The backend produces LLVM IR text format that respects these constraints. This IR includes:

- Kernel function definitions
- Device memory allocation patterns
- Warp synchronization primitives
- libdevice function calls (overridden libm math)
- Intrinsic function calls

### Debug Artifact: LLVM IR Inspection

For troubleshooting, dump the final LLVM IR before libnvvm:

```rust
CudaBuilder::new(kernels_dir)
    .final_module_path("output.ll")  // Saves LLVM IR
    .emit_llvm_ir()                   // Also saves rustc's intermediate IR
    .build()
```

---

## Stage 5: libnvvm Optimization and PTX Generation

### libnvvm Library

Located in CUDA SDK (`$CUDA_HOME/lib64/libnvvm.so` on Linux):

- Closed-source library from NVIDIA
- Takes NVVM IR and generates optimized PTX
- Applies GPU-specific optimizations
- Handles register allocation, memory coalescing patterns

### Optimization Levels

Controlled by `cuda_builder`:

| Setting | Behavior |
|---------|----------|
| `.release(true)` | Enables `-opt=3` (full optimization) |
| `.release(false)` | Disables optimizations |
| `.nvvm_opts(false)` | Override: disable even in release |

### libnvvm Options Passed from cuda_builder

```rust
let llvm_args = vec![
    "-arch=compute_70",           // Target architecture
    "-opt=3",                     // Optimization level
    "-ftz=1",                     // Flush denormals (if enabled)
    "-prec-sqrt=0",              // Fast sqrt (if enabled)
    "-prec-div=0",               // Fast division (if enabled)
    "-fma=1",                     // Fused multiply-add (default enabled)
    "-generate-line-info",        // Debug line numbers
];
```

### Output: PTX Assembly

PTX (Parallel Thread Execution) is a low-level, human-readable assembly format:

```ptx
.version 8.0
.target sm_70
.address_size 64

.visible .entry kernel_name(
    .param .u64 input_ptr,
    .param .u64 output_ptr
)
{
    .reg .b32   %r<16>;
    .reg .b64   %rd<4>;

    ld.param.u64 %rd1, [input_ptr];
    ld.param.u64 %rd2, [output_ptr];

    // ... actual kernel code

    ret;
}
```

**PTX Features:**
- Virtual registers (compiler allocates actual ones)
- Named parameters
- Well-formatted, mostly ASCII
- Full specification available (though grammar is "iffy")

---

## Stage 6: Kernel Loading and Runtime Execution

### PTX Integration into Host Binary

The generated PTX file is embedded in the host binary using standard Rust patterns:

```rust
// In host code
const KERNEL_PTX: &[u8] = include_bytes!("../target/kernels.ptx");

// Load PTX as a module
let module = CudaModule::load_from_ptx(KERNEL_PTX)?;
let kernel = module.get_function("vector_add")?;

// Launch kernel
let grid = GridSize {
    x: (n + 255) / 256,
    y: 1,
    z: 1,
};
let block = BlockSize {
    x: 256,
    y: 1,
    z: 1,
};

kernel.launch_on_stream(&stream, grid, block, &[
    &input_ptr,
    &output_ptr,
    &n,
])?;
```

### CUDA Driver API

The `cust` crate provides safe bindings to CUDA Driver API:

```rust
use cust::prelude::*;

// Initialize context
let device = Device::get_device(0)?;
let context = Context::new(device)?;

// Memory management
let mut input = vec![1.0; 1024];
let mut input_gpu = input.as_device_copy()?;

// Stream management
let stream = Stream::new(Default::default(), None)?;

// Kernel launch
kernel.launch_on_stream(
    &stream,
    GridSize { x: 1, y: 1, z: 1 },
    BlockSize { x: 256, y: 1, z: 1 },
    &args
)?;

stream.synchronize()?;
```

---

## Device Code (GPU Kernels)

### cuda_std Library

The GPU-side standard library provides:

**Thread and Block Information:**
```rust
use cuda_std::thread;

pub fn kernel(input: *const f32, output: *mut f32) {
    let idx = thread::block_idx_x() * thread::block_dim_x() + thread::thread_idx_x();

    // Access global memory
    output[idx as usize] = input[idx as usize] * 2.0;
}
```

**Synchronization:**
```rust
use cuda_std::thread;

pub fn kernel(data: *mut f32) {
    thread::sync::syncthreads();  // Block-level synchronization
}
```

**Warp Operations:**
```rust
use cuda_std::warp;

pub fn kernel(input: *const f32, output: *mut f32) {
    // Warp reductions
    let sum = warp::reduce_add(value);
}
```

**Attributes:**
```rust
#[kernel]
pub fn add_vectors(input: *const f32, output: *mut f32, n: usize) {
    // Kernel function
}
```

### Address Spaces

Control memory placement with attributes:

```rust
#[cuda_std::address_space(shared)]
static SHARED_BUFFER: [f32; 256] = [0.0; 256];

#[cuda_std::address_space(constant)]
static CONSTANT_COEFF: f32 = 1.5;
```

---

## Compilation Workflow: Developer Perspective

### Typical Development Cycle

1. **Create device crate:**
   ```bash
   cargo new --lib kernels
   # Add cuda_std dependencies
   ```

2. **Write kernels using cuda_std:**
   ```rust
   use cuda_std::prelude::*;

   #[kernel]
   pub fn add(input: *const f32, output: *mut f32, n: usize) {
       let idx = thread::thread_idx_x();
       if idx < n {
           output[idx] = input[idx] + 1.0;
       }
   }
   ```

3. **Create build.rs in host crate:**
   ```rust
   use cuda_builder::CudaBuilder;

   CudaBuilder::new("kernels")
       .arch(NvvmArch::Compute70)
       .copy_to(out_dir.join("kernels.ptx"))
       .build()?;
   ```

4. **Load and launch in host code:**
   ```rust
   const KERNEL_PTX: &[u8] = include_bytes!("kernels.ptx");
   let module = CudaModule::load_from_ptx(KERNEL_PTX)?;
   let kernel = module.get_function("add")?;
   kernel.launch_on_stream(&stream, grid, block, args)?;
   ```

### Performance Considerations

**Debug vs Release:**
- Debug: No optimizations, linenumber info preserved
- Release: Full optimization by libnvvm, smaller code

**Architecture Selection:**
- Older architectures (6.1): Better compatibility
- Newer architectures (8.0+): Better performance, tensor cores

**Memory Placement:**
- Global memory: Slow, unlimited size
- Shared memory: Fast, ~96KB per block
- Constant memory: Very fast, ~64KB total

**Compilation Flags:**
- `override_libm`: Use GPU math libraries (non-deterministic)
- `ftz`: Flush denormals (performance, but less precise)
- `fma_contraction`: Fused multiply-add (default on)

---

## Crate Architecture Summary

| Crate | Stage | Role |
|-------|-------|------|
| `cuda_builder` | Build script | Orchestrates compilation, finds backend |
| `rustc_codegen_nvvm` | Stage 3 | MIR → NVVM IR conversion |
| `nvvm` | Stage 4-5 | Libnvvm API bindings and NVVM IR creation |
| `ptx_compiler` | Stage 5 | PTX compilation utilities |
| `cuda_std` | Device code | GPU standard library (kernels use this) |
| `cust` | Stage 6+ | Host-side CUDA API for kernel launch |

---

## Key Files and References

- **Compilation Guide**: `/guide/src/cuda/pipeline.md`
- **NVVM Technical**: `/guide/src/nvvm/technical/backends.md`
- **cuda_builder Implementation**: `/crates/cuda_builder/src/lib.rs`
- **rustc_codegen_nvvm Backend**: `/crates/rustc_codegen_nvvm/src/lib.rs`
- **NVVM IR Bindings**: `/crates/nvvm/src/lib.rs`
- **Example Build Script**: `/examples/cuda/vecadd/build.rs`

**External References:**
- NVVM IR Specification: https://docs.nvidia.com/cuda/nvvm-ir-spec/index.html
- PTX ISA Reference: https://docs.nvidia.com/cuda/parallel-thread-execution/index.html
- CUDA Compute Capability: https://en.wikipedia.org/wiki/CUDA#Version_features_and_specifications

