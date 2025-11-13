# Rust CUDA Feature Matrix Summary

Quick reference guide for feature support in the Rust CUDA ecosystem. For detailed information, see `/guide/src/features.md` and respective crate READMEs.

## Symbol Legend
- **✔️** Fully Supported
- **🟨** Partially Supported
- **❌** Not Supported
- **➖** Not Applicable

---

## Rust Language Features

| Feature | Support | Notes |
|---------|---------|-------|
| Closures | ✔️ | Full support for GPU kernels |
| Enums | ✔️ | Works with pattern matching |
| Loops & Conditionals | ✔️ | If/Match/Loop all supported |
| Proc Macros | ✔️ | Can be used in kernel code |
| Error Handling (?) | ✔️ | Try operator fully functional |
| Unions | ✔️ | Supported on GPU |
| Iterators | ✔️ | Full iterator support |
| Dynamic Dispatch | ✔️ | Trait objects work |
| Pointer Casts | ✔️ | Supported |
| Unsized Slices | ✔️ | Slice types fully supported |
| Memory Allocation | ✔️ | Alloc crate works on GPU |
| Panicking | ✔️ | Currently traps/aborts |
| Float Operations | ✔️ | Maps to libdevice intrinsics |
| 128-bit Integers | 🟨 | Basic ops work (emulated); advanced intrinsics (ctpop, rotate) unsupported |
| Atomics | ❌ | Not supported on GPU |
| Optimization Levels | ✔️ | -O0 and -O3 (via libnvvm) |
| Codegen Units | ✔️ | Supported |
| LTO | ➖ | N/A - libnvvm handles module linking |

---

## CUDA Library Support

| Library | Support | Version | Notes |
|---------|---------|---------|-------|
| CUDA Driver API | 🟨 | Latest | Most functions wrapped in `cust`; comprehensive coverage but not complete |
| CUDA Runtime API | ➖ | N/A | Not applicable - rust-cuda uses Driver API |
| cuBLAS | ❌ | — | In-progress |
| cuDNN | 🟨 | 8.3.2 | Legacy API usable; backend API WIP; type-safe wrappers via `cudnn` crate |
| cuFFT | ❌ | — | Not implemented |
| cuSOLVER | ❌ | — | Not implemented |
| cuSPARSE | ❌ | — | Not implemented |
| cuRAND | ➖ | N/A | Use `gpu_rand` crate instead (xoroshiro RNGs) |
| cuTENSOR | ❌ | — | Not implemented |
| AmgX | ❌ | — | Not implemented |
| OptiX | 🟨 | Latest | CPU-side mostly complete; GPU-side heavily WIP; requires codegen support |

### GPU-Side Random Number Generation
- **`gpu_rand` Crate**: Replaces cuRAND for Driver API
- **Algorithms**: Xoroshiro (64/128/256/512-bit) and SplitMix64
- **Default**: Xoroshiro128** (subject to change)
- **CPU/GPU Compatible**: Same state can run on both

---

## GPU-Side Features

### Memory Management
| Feature | Support | Notes |
|---------|---------|-------|
| Variable Memory Space Specifiers | ✔️ | Implicit handling; can be explicit with `#[address_space(...)]` |
| Dynamic Global Memory Allocation | ✔️ | malloc/free supported on GPU |
| Unified Memory | ✔️ | Full support |
| Stream Ordered Memory | ✔️ | Supported |
| Address Space Conversion | ✔️ | Implicit handling |
| Address Space Predicates | ✔️ | Implicit, can be explicit for interop |

### Synchronization & Coordination
| Feature | Support | Notes |
|---------|---------|-------|
| Synchronization Functions | ✔️ | __syncthreads(), etc. |
| Memory Fence Instructions | ✔️ | Full memory fence support |
| Execution Configuration | ✔️ | Grid/block configuration in kernels |
| Cooperative Groups | ❌ | Not supported |
| Dynamic Parallelism | ❌ | Not supported |
| Asynchronous Barriers | ❌ | Not supported |
| Asynchronous Data Copies | ❌ | Not supported |
| Graph Memory Nodes | ❌ | Not supported |

### GPU Primitives (Warp/Thread Operations)
| Feature | Support | Notes |
|---------|---------|-------|
| Built-in Variables | ✔️ | threadIdx, blockIdx, blockDim, gridDim |
| Time Function | ✔️ | clock() and clock64() |
| Nanosleep | ✔️ | Supported |
| Warp Vote Functions | ❌ | __all(), __any(), __ballot() |
| Warp Shuffle Functions | ❌ | __shfl_*() functions |
| Warp Reduce Functions | ❌ | Not available |
| Warp Match Functions | ❌ | Not available |
| Warp Matrix (Tensor Cores) | ❌ | Not supported |

### Math & Operations
| Feature | Support | Notes |
|---------|---------|-------|
| Mathematical Functions | 🟨 | Common ops supported; f16 math unsupported |
| Printing & Formatting | ✔️ | printf() works on GPU |
| Assertions | ✔️ | assert!() supported |
| Trap/Breakpoint | ✔️ | Debugging support |
| Profiler Counters | ✔️ | Supported |

### Unsupported Features
| Feature | Status | Notes |
|---------|--------|-------|
| Textures | ❌ | Texture functions not supported |
| Surfaces | ❌ | Surface functions not supported |
| Load Cache Hints | ❌ | No cache hint operations |
| Store Cache Hints | ❌ | No cache hint operations |
| Read-Only Cache Load | ❌ | Unnecessary (immutable refs hint) |
| Built-in Vector Types | ❌ | Use vek/glam linear algebra |
| Function Execution Space | ➖ | Not needed in Rust model |
| Alloca | ➖ | N/A |
| Launch Bounds | ❌ | Not supported |
| Pragma Unroll | ❌ | Not supported |
| SIMD Video Instr. | ❌ | Not available |
| __restrict__ | ➖ | Automatic via Rust noalias |

---

## Compute Capability Support

### Base Architectures (Default)
- **Minimum**: Compute 3.5
- **Common**: Compute 5.0, 6.0, 6.1, 7.0, 8.0, 9.0, 10.0+
- **Suffix**: None (e.g., `NvvmArch::Compute70`)
- **Compatibility**: Enables all lower capability flags

### Architecture-Specific Features

#### Compute 5.0+
- 64-bit integer min/max
- Bitwise atomic operations

#### Compute 6.0+
- Double-precision (f64) atomic operations

#### Compute 7.0+
- Tensor Core operations (partial)

#### Compute 10.0+
- Latest features via CUDA 12.9+
- Family suffix support (`Compute101f`)
- Architecture suffix support (`Compute100a`)

### Suffix Variants (CUDA 12.9+)

| Suffix | Meaning | Use Case |
|--------|---------|----------|
| None | Base architecture | Default; forward compatible within family |
| `f` | Family-specific | Same major, equal or higher minor version |
| `a` | Architecture-specific | Exact GPU model only; all available instructions |

See `/guide/src/guide/compute_capabilities.md` for detailed configuration patterns.

---

## Known Limitations & Workarounds

### Atomics
- **Limitation**: No atomic operations support
- **Workaround**: Use synchronization primitives, shared memory reduction patterns
- **Note**: Consider single-threaded approaches or use warp-level aggregation

### Warp Operations
- **Limitation**: No warp shuffle, vote, or reduce functions
- **Workaround**: Implement using shared memory + synchronization
- **Performance**: Can be slower than native warp ops

### Tensor Cores (Matrix Operations)
- **Limitation**: No direct tensor core access
- **Workaround**: Use cuDNN (supported) for neural network operations
- **Alternative**: Implement matrix kernels with shared memory tiling

### Stack Limitations
- **Limitation**: Threads have very limited stack (~16MB per GPU)
- **Workaround**: Avoid recursion; use static allocation or dynamic memory
- **Debug**: Use `cuda-memcheck` to detect stack overflows (InvalidAddress errors)

### Recursion
- **Limitation**: Recursion causes stack issues
- **Alternative**: Restructure to iterative approach or use dynamic memory
- **Detection**: Use `cuobjdump` to check for functions without statically-known stack usage

### Debug Builds
- **Limitation**: Debug code derives slow compilation and huge PTX files
- **Workaround**: Avoid deriving Debug in GPU crates; use release builds
- **Note**: Global DCE improvements planned for future versions

### 128-bit Integers
- **Limitation**: Only basic arithmetic; no ctpop/rotate intrinsics
- **Workaround**: Use 64-bit where possible; manual implementation for advanced ops

### Tensor Data Types
- **Limitation**: cuDNN doesn't support f16/bf16 natively
- **Workaround**: None currently; workaround via f32 conversion

---

## Architecture Overview

### Compilation Pipeline
1. **Rust Code** → `rustc` with `rustc_codegen_nvvm` backend
2. **NVVM IR** → `libnvvm` optimization
3. **PTX** → CUDA Driver loads & JIT compiles to SASS at runtime
4. **SASS** → Executes on GPU hardware

### Crate Ecosystem
- **`rustc_codegen_nvvm`**: Backend for PTX generation
- **`cuda_std`**: GPU-side std functions and utilities
- **`cust`**: CPU-side Driver API wrapper
- **`cudnn`**: Type-safe cuDNN bindings
- **`gpu_rand`**: Alternative to cuRAND
- **`optix`**: OptiX raytracing support
- **`cuda_builder`**: Build script integration

### Project Status
⚠️ **Early Development**: Expect bugs, safety issues, incomplete features
📈 **Actively Maintained**: Rebooted in 2025 with ongoing development
🔄 **Breaking Changes**: Possible; still stabilizing APIs

---

## Quick Decision Trees

### "Should I use this feature?"

**Atomics needed?**
→ No native support; use shared memory patterns or consider serial implementation

**Need Tensor Cores?**
→ Use cuDNN (supported, well-tested)

**Need Warp Optimization?**
→ Implement with shared memory + __syncthreads()

**Need f16 Support?**
→ Not in cuDNN; convert to f32, process, convert back

**Multiple CUDA Versions?**
→ Use compute capability gating with `#[cfg(target_feature = "compute_XX")]`

---

## References

- **Features Table**: `/guide/src/features.md`
- **Compute Capabilities**: `/guide/src/guide/compute_capabilities.md`
- **Safety & Design**: `/guide/src/faq.md`
- **Tips & Tricks**: `/guide/src/guide/tips.md`
- **cuDNN Docs**: `/crates/cudnn/README.md`
- **gpu_rand Docs**: `/crates/gpu_rand/README.md`
- **NVIDIA CUDA Docs**: https://docs.nvidia.com/cuda/

Last Updated: 2025-11-13
