# Crates Directory Architecture

**Overview**: Contains 21 Rust crates organized in a layered architecture (~66K lines of code) that provides high-level safe abstractions over CUDA functionality, from low-level FFI bindings to specialized GPU utilities.

---

## Architectural Layers

### Layer 1: Low-Level FFI Bindings

These crates provide raw bindings to CUDA C/C++ libraries via `bindgen` and are feature-gated for modularity.

| Crate | Purpose | Key Features |
|-------|---------|--------------|
| **cust_raw** | Low-level CUDA Driver API bindings | `driver`, `runtime`, `cublas`, `cublaslt`, `cudnn`, `nvvm`, `nvptx-compiler` features |
| **optix-sys** | Raw OptiX raytracing bindings | System-level C/C++ wrapper |
| **cudnn-sys** | cuDNN neural network library bindings | Low-level FFI only |

---

### Layer 2: Core Runtime & Device

Fundamental runtime infrastructure for both host and device code.

| Crate | Purpose | Target |
|-------|---------|--------|
| **cust_core** | Shared core utilities (vector types, traits) | CPU + GPU (no_std) |
| **cust_derive** | Procedural macros for `cust` | Derive implementations |
| **cuda_std** | Device-side standard library replacement | GPU (no_std) |
| **cuda_std_macros** | Device-side macro utilities | GPU macros |

**Dependencies**: `cust_core` uses feature-gated dependencies on `glam`, `vek`, `mint`, `half`, `num-complex` for cross-platform vector/math support.

---

### Layer 3: High-Level Host API

Safe, ergonomic host-side abstractions for CUDA operations.

| Crate | Purpose | Dependencies |
|-------|---------|--------------|
| **cust** | High-level CUDA Driver API (primary API) | `cust_core`, `cust_raw`, `cust_derive` + optional vector libs |
| **cust_derive** | Derive macros for custom types | Proc-macro crate |

**Key Features**: Optional support for `glam`, `mint`, `vek` vector types via feature gates (`impl_glam`, `impl_mint`, `impl_vek`, `impl_half`).

---

### Layer 4: GPU Compilation Pipeline

Transforms Rust code into GPU-executable formats (NVVM IR or PTX).

| Crate | Purpose | Role |
|-------|---------|------|
| **rustc_codegen_nvvm** | Custom Rust compiler backend | Converts Rust MIR → NVVM IR (CUDA IR) |
| **rustc_codegen_nvvm_macros** | Compiler backend macros | Codegen support |
| **nvvm** | High-level libnvvm bindings | NVVM IR manipulation & optimization |
| **ptx_compiler** | CUDA PTX compilation wrapper | PTX compilation APIs |
| **ptx** | Low-level PTX IR types | PTX syntax/types |
| **cuda_builder** | Build system integration | Orchestrates `rustc_codegen_nvvm` compilation |

**Workflow**: `cuda_builder` (build-time) → `rustc_codegen_nvvm` (backend) → `nvvm` (IR manipulation) → PTX code

---

### Layer 5: Specialized GPU Utilities & Libraries

High-level APIs for specific GPU domains built on `cust`.

| Crate | Purpose | Dependencies |
|-------|---------|--------------|
| **blastoff** | CUBLAS linear algebra wrapper | `cust`, `cust_raw` (cublas feature) |
| **cudnn** | cuDNN neural network wrapper | `cust`, `cudnn-sys` |
| **gpu_rand** | GPU-friendly RNG implementations | `cust_core` + `cuda_std` (on-device) |
| **optix** | OptiX raytracing framework | `cust`, `optix-sys`, `mint` |
| **optix_device** | Device-side OptiX code | GPU target |
| **optix_device_macros** | OptiX device macros | Proc-macro crate |

---

## Dependency Flow

```
Host Code
    ↓
cust (High-level Host API)
    ↓
cust_core + cust_raw (Core + FFI)
    ↓
cust_raw (bindgen'd C bindings)
↓
blastoff / cudnn / optix (Specialized libraries)
    ↓
cust + cust_raw (Dependencies)

Device Code
    ↓
cuda_std (Device stdlib)
    ↓
cuda_std_macros + cust_core (Device utilities)
    ↓
gpu_rand / optix_device (Device libraries)
```

---

## Key Design Patterns

### Feature Gating for Modularity
- **cust_raw**: Each CUDA library (CUBLAS, cuDNN, NVVM, PTX) is optional via Cargo features
- **cust**: Vector type support (`glam`, `vek`, `mint`) is feature-gated (default enabled)
- **cuda_builder**: `rustc_codegen_nvvm` is optional (requires explicit opt-in)

### Proc-Macros for Ergonomics
- `cust_derive`: Provides `#[derive]` for GPU-compatible types
- `cuda_std_macros`: Device-side macros (threads, synchronization)
- `optix_device_macros`: OptiX-specific device code macros

### Layered Architecture
1. **Raw FFI** (cust_raw, optix-sys, cudnn-sys)
2. **Core Abstractions** (cust_core, cuda_std)
3. **Safe Host API** (cust)
4. **Compilation** (rustc_codegen_nvvm, cuda_builder)
5. **Domain-Specific** (blastoff, cudnn, optix, gpu_rand)

### Cross-Platform Types
- `cust_core` provides shared types that work on both CPU and GPU via feature gates
- Math libraries (`glam`, `vek`, `mint`) support CUDA-compatible variants

---

## Code Statistics

- **Total Lines**: ~66,000 Rust lines across all crates
- **Largest Crates**: rustc_codegen_nvvm (compiler backend), cust (host API), cuda_std (device stdlib)
- **Architecture**: 5 clear layers from FFI to domain-specific utilities

---

## Common Patterns When Working with Crates

### Adding Support for a New Vector Type
1. Add feature to `cust_raw` (if needed)
2. Update `cust_core` with type support
3. Add feature gate to `cust`
4. Example: `impl_half` feature pattern

### Adding a New GPU Library
1. Create FFI bindings in `*-sys` crate
2. Create high-level wrapper (e.g., `blastoff`, `cudnn`)
3. Depend on `cust` and feature-gated `cust_raw`
4. Use `cust_core` for shared types

### Device-Side Code
1. Create code that targets `cuda_std`
2. Use `cuda_std_macros` for device-specific constructs
3. Compile with `cuda_builder` (orchestrates `rustc_codegen_nvvm`)
4. Use `*_device` crates for specialized domains (e.g., `optix_device`)

