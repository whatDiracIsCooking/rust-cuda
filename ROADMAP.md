# Rust CUDA Project Roadmap

This document outlines the development priorities and planned features for the Rust CUDA Project. It serves as a guide for contributors and users to understand what's coming next.

**Last Updated:** November 2025
**Status:** Active Development - Project recently rebooted (Jan 2025)

## Priority Levels

- 🔴 **Critical** - Fundamental features blocking major use cases
- 🟡 **High** - Important features with broad impact
- 🟢 **Medium** - Valuable features for specific use cases
- 🔵 **Low** - Nice-to-have features

---

## Phase 1: Core GPU Features (Q4 2025 - Q1 2026)

### 🔴 Critical Priority

#### 1. Complete Atomic Operations
**Status:** Partial implementation exists
**Location:** `crates/cuda_std/src/atomic.rs`

Current state:
- ✅ Atomic floats (f32, f64) with block/device/system scopes
- ❌ Complete integer atomics (u32, u64, i32, i64)
- ❌ Full memory ordering support (SeqCst, Acquire, Release, AcqRel)
- ❌ 8/16-bit atomics (may need emulation)

**Why it matters:** Atomics are fundamental for parallel GPU algorithms. Many common patterns (reductions, histograms, concurrent data structures) require atomic operations.

**Deliverables:**
- [ ] Complete atomic integer operations (add, sub, min, max, and, or, xor, exchange, CAS)
- [ ] Full memory ordering semantics
- [ ] Comprehensive tests and documentation
- [ ] Performance benchmarks vs CUDA C++

---

#### 2. Tensor Cores (Warp Matrix Functions)
**Status:** Not implemented
**Target:** NVIDIA Tensor Cores (compute capability 7.0+)

**Why it matters:** Critical for ML/AI workloads. Tensor cores provide 10-100x speedup for matrix operations in deep learning.

**Deliverables:**
- [ ] WMMA (Warp Matrix Multiply-Accumulate) API
- [ ] Support for FP16, BF16, TF32, INT8, INT4 operations
- [ ] Integration with existing linear algebra types (glam, vek)
- [ ] Example: matrix multiplication using tensor cores
- [ ] Performance comparison with cuBLAS

---

### 🟡 High Priority

#### 3. Complete cuBLAS Bindings
**Status:** In-progress (`blastoff` crate)
**Location:** `crates/blastoff/`

**Why it matters:** BLAS is fundamental for scientific computing, linear algebra, and ML.

**Deliverables:**
- [ ] Complete BLAS Level 1 operations (vector-vector)
- [ ] Complete BLAS Level 2 operations (matrix-vector)
- [ ] Complete BLAS Level 3 operations (matrix-matrix)
- [ ] High-level safe Rust API
- [ ] Examples and benchmarks

---

#### 4. Complete cuDNN Bindings
**Status:** In-progress
**Location:** `crates/cudnn/`, `crates/cudnn-sys/`

**Why it matters:** Essential for deep learning applications.

**Deliverables:**
- [ ] Convolution operations
- [ ] Pooling operations
- [ ] Activation functions
- [ ] Normalization (batch norm, layer norm)
- [ ] RNN/LSTM operations
- [ ] cuDNN 9 error codes (`crates/cudnn/src/error.rs:160`)
- [ ] High-level safe Rust API
- [ ] Integration examples

---

#### 5. Texture and Surface Functions
**Status:** Not implemented (partial texture support in `cust/src/texture.rs`)

**Why it matters:** Essential for image processing, scientific visualization, and any workload involving 2D/3D data access patterns.

**Deliverables:**
- [ ] Texture memory objects
- [ ] Surface memory objects
- [ ] 1D, 2D, 3D texture support
- [ ] Texture filtering (linear, nearest)
- [ ] Texture addressing modes (clamp, wrap, mirror)
- [ ] Example: image convolution using textures

---

### 🟢 Medium Priority

#### 6. Expand Warp Reduce Functions
**Status:** Partial implementation (i32, u32 only)
**Location:** `crates/cuda_std/src/warp.rs`

Current state:
- ✅ Warp reduce for i32, u32
- ❌ Missing i64, u64, f32, f64

**Why it matters:** Warp-level reductions are highly efficient primitives for parallel algorithms.

**Deliverables:**
- [ ] Warp reduce for i64, u64
- [ ] Warp reduce for f32, f64
- [ ] Tests and examples
- [ ] Performance benchmarks

**Estimated effort:** Low (infrastructure exists, just extend to more types)

---

#### 7. Cooperative Groups
**Status:** Not implemented

**Why it matters:** Modern CUDA programming pattern that provides flexible thread synchronization beyond basic block-level operations.

**Deliverables:**
- [ ] Thread block groups
- [ ] Coalesced groups
- [ ] Tiled partitions
- [ ] Grid groups
- [ ] Synchronization primitives
- [ ] Example: advanced reduction using cooperative groups

---

#### 8. Asynchronous Barriers and Data Copies
**Status:** Not implemented
**Target:** Compute capability 8.0+ (Ampere and above)

**Why it matters:** Better overlap of compute and memory operations for improved performance.

**Deliverables:**
- [ ] Asynchronous barrier primitives
- [ ] Asynchronous shared memory data copies
- [ ] Pipeline primitives
- [ ] Examples demonstrating performance benefits

---

#### 9. Launch Bounds and Optimization Hints
**Status:** Not implemented

**Why it matters:** Performance tuning and optimization for register usage, occupancy control.

**Deliverables:**
- [ ] `#[launch_bounds]` attribute for kernels
- [ ] `#[unroll]` attribute for loops
- [ ] Performance tuning guide
- [ ] Examples showing impact on occupancy

---

## Phase 2: Ecosystem and Libraries (Q2-Q3 2026)

### 🟡 High Priority

#### 10. Additional CUDA Library Bindings

**cuFFT** - Fast Fourier Transform
- [ ] 1D, 2D, 3D FFT
- [ ] Batch operations
- [ ] High-level safe API

**cuSOLVER** - Linear algebra solvers
- [ ] Dense linear systems
- [ ] Sparse linear systems
- [ ] Eigenvalue problems

**cuSPARSE** - Sparse matrix operations
- [ ] Sparse matrix formats (CSR, COO, etc.)
- [ ] Sparse BLAS operations
- [ ] Sparse matrix conversions

**cuTENSOR** - Tensor operations
- [ ] Tensor contractions
- [ ] Element-wise operations
- [ ] Tensor reductions

---

### 🟢 Medium Priority

#### 11. Complete OptiX Support
**Status:** CPU OptiX mostly complete, GPU OptiX in-progress
**Location:** `crates/optix/`

**Deliverables:**
- [ ] Complete device-side OptiX support
- [ ] Ray tracing primitives
- [ ] Any-hit, closest-hit, miss programs
- [ ] Advanced ray tracing examples

---

## Phase 3: Advanced Features (Q4 2026+)

### 🔵 Low Priority

#### 12. Dynamic Parallelism
**Status:** Not implemented

**Why it matters:** Allows kernels to launch other kernels. Complex feature, rarely used.

**Deliverables:**
- [ ] Kernel launch from device code
- [ ] Device-side synchronization
- [ ] Examples and use cases

---

#### 13. Graph Memory Nodes
**Status:** Not implemented

**Deliverables:**
- [ ] Graph memory allocation nodes
- [ ] Graph memory free nodes
- [ ] Integration with existing graph API

---

#### 14. SIMD Video Instructions
**Status:** Not implemented

**Deliverables:**
- [ ] Video codec primitives
- [ ] Color space conversions
- [ ] Examples

---

## Infrastructure and Developer Experience

### 🔴 Critical Priority

#### 15. GPU Test Infrastructure
**Status:** Tests currently stubbed out in CI
**Location:** `.github/workflows/ci_linux.yml:180`

**Why it matters:** Quality and reliability of the project depend on comprehensive testing.

**Deliverables:**
- [ ] GPU runner integration (Modal.com or self-hosted)
- [ ] Automated testing on multiple GPU architectures
- [ ] Compute capability testing (6.1, 7.0, 8.0, 9.0)
- [ ] Performance regression testing

---

### 🟡 High Priority

#### 16. Windows Support Improvements
**Status:** Recent work in progress (commit `7535fb8`)

**Deliverables:**
- [ ] Stable Windows CI
- [ ] Windows-specific documentation
- [ ] CUDA path handling on Windows
- [ ] Windows installer/setup scripts

---

#### 17. Documentation and Examples

**Deliverables:**
- [ ] Port more NVIDIA CUDA samples to Rust
- [ ] Performance optimization guide
- [ ] Debugging guide (cuda-gdb, compute-sanitizer)
- [ ] Profiling guide (Nsight Compute, Nsight Systems)
- [ ] Migration guide from CUDA C++
- [ ] Video tutorials

---

### 🟢 Medium Priority

#### 18. Better Error Messages and Diagnostics

**Deliverables:**
- [ ] Improved compile-time errors for common mistakes
- [ ] Runtime error reporting improvements
- [ ] PTX validation and linting
- [ ] Kernel occupancy analyzer

---

#### 19. Performance Tooling

**Deliverables:**
- [ ] Benchmarking framework for GPU code
- [ ] Performance comparison tools (Rust vs CUDA C++)
- [ ] Automated performance regression detection
- [ ] Profile-guided optimization support

---

## Documentation Fixes

### Immediate Tasks

#### 20. Fix features.md Discrepancies
**Status:** Documentation out of sync with implementation

Current discrepancies found:
- features.md says ❌ for Warp Vote Functions, but they ARE implemented
- features.md says ❌ for Warp Match Functions, but they ARE implemented
- features.md says ❌ for Warp Shuffle Functions, but they ARE implemented
- features.md says ❌ for Warp Reduce Functions, but they ARE partially implemented (i32, u32)
- features.md says ❌ for Atomics, but atomic floats ARE implemented

**Deliverables:**
- [ ] Update features.md to reflect actual implementation status
- [ ] Add 🟨 (Partially Supported) where appropriate
- [ ] Keep documentation in sync going forward

---

## How to Contribute

Interested in working on any of these features? Here's how to get started:

1. **Check the issue tracker** for existing work or discussion
2. **Open an issue** to discuss your proposed implementation
3. **Reference this roadmap** in your PR description
4. **Add tests** for new features
5. **Update documentation** including this roadmap and `features.md`

For more details, see [CONTRIBUTING.md](CONTRIBUTING.md) (if it exists) or reach out to the maintainers.

---

## Version Milestones

### v0.4.0 - "Atomics and Tensor Cores" (Target: Q1 2026)
- Complete atomic operations
- Tensor core support
- Warp reduce expansion
- Updated documentation

### v0.5.0 - "Libraries" (Target: Q2 2026)
- Complete cuBLAS bindings
- Complete cuDNN bindings
- Texture/surface functions
- GPU test infrastructure

### v0.6.0 - "Advanced Features" (Target: Q3 2026)
- Cooperative groups
- Async barriers and copies
- Additional CUDA libraries (cuFFT, cuSOLVER)
- Performance tooling

### v1.0.0 - "Production Ready" (Target: Q4 2026)
- Comprehensive CUDA library coverage
- Stable API
- Complete documentation
- Windows support
- Performance parity with CUDA C++

---

## Community Priorities

This roadmap is a living document. Community feedback is essential! If you have different priorities or need specific features, please:

- Open an issue with the `roadmap` label
- Discuss on community channels
- Vote/comment on existing roadmap issues

We'll update this roadmap quarterly based on:
- Community feedback and priorities
- Emerging CUDA features
- Real-world use cases
- Available contributor bandwidth

---

**Note:** Dates and priorities are subject to change based on community needs and contributor availability. This is an open-source project, and progress depends on volunteer contributions.
