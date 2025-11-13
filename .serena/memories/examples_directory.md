# Examples Directory Reference

## Overview

The `examples/cuda/` directory contains five production-quality CUDA examples demonstrating progression from basic to advanced GPU programming patterns. Each example showcases key Rust-CUDA library features and best practices.

## Examples Structure

### 1. **vecadd** (Beginner)
Basic vector addition example - the entry point for learning Rust-CUDA.

**Location**: `examples/cuda/vecadd/`

**Demonstrates**:
- CUDA context initialization with `quick_init()`
- Module loading from PTX code
- Stream creation for GPU execution
- Simple memory allocation and transfer (`as_dbuf()`)
- Kernel retrieval and launching with `launch!` macro
- Occupancy-based launch configuration optimization
- Stream synchronization

**Key Learning**: Fundamental CUDA workflow - init, allocate, launch, synchronize.

**Code Pattern**:
```rust
let _ctx = cust::quick_init()?;
let module = Module::from_ptx(PTX, &[])?;
let stream = Stream::new(StreamFlags::NON_BLOCKING, None)?;
let gpu_buf = host_slice.as_dbuf()?;
```

---

### 2. **gemm** (Intermediate)
General Matrix Multiplication comparing naive vs. tiled kernels and cuBLAS.

**Location**: `examples/cuda/gemm/`

**Demonstrates**:
- Two custom kernel implementations (naive and tiled)
- Performance benchmarking with CUDA events
- Warmup runs before timing measurements
- cuBLAS library integration for comparison
- 2D grid/block launch configurations
- Correctness validation across implementations
- Handling multiple kernel variants

**Key Learning**: Performance optimization patterns, benchmarking methodology, library integration.

**Patterns**:
- Event-based timing: `Event::new()`, `record()`, `elapsed_time_f32()`
- Multi-dimensional grids: `<<<(grid_x, grid_y), (block_x, block_y)>>>`
- Correctness assertions with tolerance checking

---

### 3. **sha2_crates_io** (Intermediate)
Cryptographic hashing demonstrating unmodified crate compilation for GPU.

**Location**: `examples/cuda/sha2_crates_io/`

**Demonstrates**:
- Using external Rust crates (`sha2`) in GPU kernels
- CPU/GPU result validation
- DeviceBox for single-value allocations
- Host-device memory synchronization
- Identical behavior between CPU and GPU implementations

**Key Learning**: Codebase portability - same logic runs on CPU and GPU.

**Pattern**: GPU kernel code can use standard Rust crates without modification if they compile to CUDA target.

---

### 4. **path_tracer** (Advanced)
Interactive ray tracing with optional OptiX denoising support.

**Location**: `examples/cuda/path_tracer/`

**Demonstrates**:
- Complex kernel-side code organization (multiple modules: render, material, hittable, sphere, scene)
- Dual CPU/GPU rendering backends with shared data structures
- Interactive viewer with real-time rendering
- Optional OptiX hardware raytracing acceleration
- Image denoising capabilities
- Complex memory patterns for scene management
- Shader compilation (for OptiX)

**Key Learning**: Production-grade example showing modularity, dual-backend architecture, and advanced GPU features.

**Architecture**:
- `kernels/src/`: GPU code (render.rs, material.rs, hittable.rs, etc.)
- `src/cpu/`: CPU reference implementation
- `src/cuda/`: CUDA-specific GPU execution
- `src/optix/`: OptiX denoising integration
- `src/viewer/`: Interactive UI layer

---

## Common Patterns Across Examples

### Initialization Pattern
All examples follow identical context setup:
```rust
let _ctx = cust::quick_init()?;  // Initialize CUDA context
let module = Module::from_ptx(PTX, &[])?;  // Load GPU code
let stream = Stream::new(StreamFlags::NON_BLOCKING, None)?;  // Create execution stream
```

### Memory Transfer Pattern
Host-to-device transfers use the `as_dbuf()` extension trait:
```rust
let gpu_buffer = host_slice.as_dbuf()?;  // Allocate and copy
gpu_buffer.copy_to(&mut host_buf)?;      // Copy back to host
```

### Launch Configuration Pattern
Examples use CUDA occupancy API for optimal performance:
```rust
let (_, block_size) = kernel.suggested_launch_configuration(0, 0.into())?;
let grid_size = (element_count as u32).div_ceil(block_size);
unsafe { launch!(kernel<<<grid_size, block_size, 0, stream>>>(...))? }
```

### Correctness Validation
Examples validate GPU results against CPU implementations or known values.

### Stream Management
Non-blocking streams enable asynchronous execution without explicit synchronization until results needed.

---

## Learning Progression

| Example | Complexity | Focus | Next Skills |
|---------|-----------|-------|------------|
| **vecadd** | Low | Basic workflow, kernel launch | Stream management |
| **gemm** | Medium | Performance optimization, benchmarking | Complex kernels, library integration |
| **sha2_crates_io** | Medium | Crate portability, validation | Multi-module kernels |
| **path_tracer** | High | Architecture, dual backends, OptiX | Production patterns, viewer integration |

---

## Build and Run

All examples use the standard build system:
```bash
scripts/build.sh
./target/release/examples/{example_name}
```

See `examples/cuda/README.md` for detailed instructions.

---

## Key Takeaways

1. **Progressive Complexity**: Start with vecadd, progress through gemm/sha2, master path_tracer
2. **Pattern Consistency**: All examples follow identical initialization and kernel launching patterns
3. **Production Ready**: These are not toy examples - they demonstrate real GPU programming
4. **Validation**: Every example validates GPU results for correctness
5. **Performance**: Benchmarking examples show how to measure and optimize GPU code
