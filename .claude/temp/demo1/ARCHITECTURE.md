# Architecture Diagram

## Component Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        Library Consumers                         │
└─────────────────────────────────────────────────────────────────┘
           │                                    │
           │                                    │
           ▼                                    ▼
    ┌─────────────┐                      ┌─────────────┐
    │  CUDA Code  │                      │ C++20 Code  │
    │  (.cu file) │                      │ (.cpp file) │
    │             │                      │             │
    │  #include   │                      │   import    │
    │  <vector3.h>│                      │   mathlib   │
    └─────────────┘                      └─────────────┘
           │                                    │
           │                                    │
           ▼                                    ▼
    ┌─────────────┐                      ┌─────────────┐
    │   Header    │                      │   Module    │
    │  vector3.h  │                      │mathlib.cppm │
    │             │◄─────────────────────│             │
    │ (declares   │  includes in         │ (re-exports │
    │  interface) │  global fragment     │  interface) │
    └─────────────┘                      └─────────────┘
           │                                    │
           │                                    │
           └────────────┬───────────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  Implementation  │
              │   vector3.cpp    │
              │                  │
              │ (single source   │
              │  of truth)       │
              └──────────────────┘
```

## Build System View

```
CMakeLists.txt
    │
    ├─► mathlib_traditional (static library)
    │       │
    │       ├─ Sources: src/vector3.cpp
    │       ├─ Public Headers: include/mathlib/
    │       ├─ C++ Standard: C++17
    │       └─ Consumers: CUDA code, legacy C++
    │
    └─► mathlib_module (module library)
            │
            ├─ Module Interface: src/mathlib.cppm
            ├─ Private Include: include/mathlib/ (for global fragment)
            ├─ Links: mathlib_traditional
            ├─ C++ Standard: C++20
            └─ Consumers: Modern C++ code

Both targets share the SAME implementation (vector3.cpp)
```

## Data Flow

### Traditional Path (CUDA)

```
User Code                 Preprocessor              Compiler
─────────                 ────────────              ────────
cuda_user.cu
    │
    ├─ #include "mathlib/vector3.h"
    │       │
    │       └─► [Textual inclusion]
    │               │
    │               ▼
    ├─ Expanded source with vector3.h content
    │       │
    │       └─► [NVCC compilation]
    │               │
    │               ▼
    └─ cuda_user.o
            │
            └─► [Link with mathlib_traditional.a]
                    │
                    ▼
                cuda_user (executable)
```

### Module Path (C++20)

```
User Code                 Module System             Compiler
─────────                 ─────────────             ────────
cpp20_user.cpp
    │
    ├─ import mathlib;
    │       │
    │       └─► [Load pre-compiled module]
    │               │
    │               └─► mathlib.cppm (compiled to BMI*)
    │                       │
    │                       └─► Uses mathlib_traditional.a
    │
    └─ cpp20_user.o
            │
            └─► [Link with mathlib_module + mathlib_traditional]
                    │
                    ▼
                cpp20_user (executable)

* BMI = Binary Module Interface
```

## Type Safety Guarantee

Both paths expose **identical** API:

```cpp
namespace mathlib {
    class Vector3 {
        // Same interface regardless of #include or import
        Vector3 operator+(const Vector3&) const;
        double dot(const Vector3&) const;
        // ...
    };
}
```

**Compile-time verification**: Any API mismatch causes compilation failure, ensuring consistency.

## Migration Path

```
Phase 1: Current State
┌─────────────────────┐
│ 100% CUDA (.cu)     │──► Uses #include
│ No C++20 modules    │
└─────────────────────┘

Phase 2: Dual Mode (NOW)
┌─────────────────────┐
│ CUDA (.cu)          │──► Uses #include
│ Some C++20 (.cpp)   │──► Uses import
└─────────────────────┘

Phase 3: Future (when nvcc supports modules)
┌─────────────────────┐
│ CUDA (.cu)          │──► Uses import
│ All C++20           │──► Uses import
└─────────────────────┘
    │
    └─► Can remove headers, keep only .cppm
```

## Architectural Decision Record

### Context

NVCC doesn't support C++20 modules, but modern C++ users want module benefits. Library needs to serve both audiences.

### Decision

Implement dual-mode library with traditional headers + C++20 module wrapper, both using single implementation.

### Consequences

**Positive:**
- ✅ CUDA compatibility maintained
- ✅ Modern C++ gets module benefits
- ✅ Single implementation source
- ✅ Clear migration path

**Negative:**
- ❌ More complex build system
- ❌ Requires CMake 3.28+
- ❌ Module toolchain still maturing
- ❌ Two ways to consume same library

**Mitigation:**
- Document build requirements clearly
- Provide working examples for both modes
- Keep API identical in both modes
- Plan for eventual module-only future

### Validation

- Both consumers compile successfully
- Same API accessible from both modes
- Single implementation serves both
- Build system manages complexity appropriately
