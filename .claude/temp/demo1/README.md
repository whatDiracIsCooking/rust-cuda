# Dual-Mode Library: Headers + C++20 Modules

## Architecture Overview

This demo shows how to design a library that supports **both** traditional header-based inclusion (for CUDA/nvcc) **and** C++20 module imports (for modern C++ compilers).

### The Problem

- **CUDA (nvcc)** doesn't support C++20 modules yet
- **Modern C++20** users want module benefits (faster compilation, better encapsulation)
- Library maintainers don't want to maintain two separate codebases

### The Solution

A **dual-mode library** with:
1. Traditional `.h` + `.cpp` for CUDA/legacy users
2. C++20 `.cppm` module interface wrapping the same implementation
3. CMake build system supporting both consumption models

## Directory Structure

```
demo/
├── CMakeLists.txt              # Build system with dual-mode targets
├── include/
│   └── mathlib/
│       └── vector3.h           # Traditional header (CUDA-compatible)
├── src/
│   ├── vector3.cpp             # Implementation (shared by both modes)
│   └── mathlib.cppm            # C++20 module interface
└── examples/
    ├── cuda_user.cu            # CUDA consumer using #include
    └── cpp20_user.cpp          # C++20 consumer using import
```

## Key Design Decisions

### 1. Single Source of Truth

The implementation lives in `vector3.cpp` and is compiled once. Both the traditional library and the module target link against this implementation.

**Rationale**: Avoids code duplication and maintenance burden.

### 2. Module as Wrapper

The `.cppm` file uses the **global module fragment** to include traditional headers, then re-exports them:

```cpp
module;
#include "mathlib/vector3.h"  // Global fragment
export module mathlib;
export namespace mathlib {
    using mathlib::Vector3;
}
```

**Rationale**: Reuses existing header-based interface while providing module interface.

### 3. Separate CMake Targets

- `mathlib_traditional`: Traditional static library (for CUDA)
- `mathlib_module`: C++20 module library (for modern C++)

**Rationale**: Clear separation of concerns, explicit dependencies, supports both build modes.

## Build System Architecture

### Traditional Target (CUDA-compatible)

```cmake
add_library(mathlib_traditional STATIC src/vector3.cpp)
target_include_directories(mathlib_traditional PUBLIC include)
target_compile_features(mathlib_traditional PUBLIC cxx_std_17)
```

- Uses C++17 (CUDA-compatible)
- Exports header directory
- Standard static library

### Module Target (C++20)

```cmake
add_library(mathlib_module)
target_sources(mathlib_module
    PUBLIC FILE_SET CXX_MODULES FILES src/mathlib.cppm
)
target_link_libraries(mathlib_module PRIVATE mathlib_traditional)
target_compile_features(mathlib_module PUBLIC cxx_std_20)
```

- Uses CMake 3.28+ module support
- Links against traditional implementation
- Requires C++20

## Usage Examples

### CUDA Code (Traditional Headers)

```cpp
#include "mathlib/vector3.h"  // Header include

int main() {
    mathlib::Vector3 v1(1, 2, 3);
    mathlib::Vector3 v2(4, 5, 6);
    auto sum = v1 + v2;  // Works in CUDA!
}
```

**Why**: nvcc doesn't support modules, needs traditional headers.

### C++20 Code (Module Import)

```cpp
import mathlib;  // Module import - no #include!

int main() {
    mathlib::Vector3 v1(1, 2, 3);
    mathlib::Vector3 v2(4, 5, 6);
    auto sum = v1 + v2;  // Same API, cleaner imports!
}
```

**Why**: Faster compilation, better encapsulation, cleaner dependencies.

## Build Instructions

### Requirements

- CMake 3.28+ (for C++20 module support)
- C++20-capable compiler (GCC 11+, Clang 16+, MSVC 19.28+)
- CUDA Toolkit (for CUDA examples)

### Building

```bash
cd .claude/temp/demo
mkdir build && cd build

# Configure with both CUDA and C++20 support
cmake .. -G Ninja

# Build all targets
ninja

# Run examples
./cuda_user      # Uses traditional headers
./cpp20_user     # Uses C++20 modules
```

## Trade-offs Analysis

### Advantages

| Aspect | Benefit |
|--------|---------|
| **Compatibility** | CUDA code works without changes |
| **Modern C++** | C++20 users get module benefits |
| **Single Implementation** | One codebase to maintain |
| **Migration Path** | Users can switch from headers to modules incrementally |
| **Build Flexibility** | CMake provides both options |

### Costs

| Aspect | Cost |
|--------|------|
| **Build Complexity** | Requires CMake 3.28+, more complex configuration |
| **Toolchain Requirements** | Module support still maturing in some compilers |
| **Learning Curve** | Developers need to understand both paradigms |
| **Build Time** | Module compilation adds overhead (though saves time later) |

## When to Use This Pattern

### Ideal For

- Libraries supporting both CUDA and modern C++ consumers
- Projects with mixed CUDA/.cu and pure C++/.cpp code
- Teams migrating from headers to modules incrementally
- Public libraries needing broad compatibility

### Not Ideal For

- CUDA-only projects (just use headers)
- Pure C++20 projects with no CUDA (just use modules)
- Projects with CMake < 3.28
- Environments where module support is unreliable

## Architectural Principles Applied

### Type Safety (Stroustrup)

- Same strong types available in both modes
- No runtime overhead from abstraction
- Compile-time interface validation

### Pragmatic Trade-offs (Brooks)

- Balances modern features with practical constraints
- Provides migration path without breaking existing code
- Documents decision rationale clearly
- Validates assumptions with working examples

### Build System Excellence (Both)

- Clean target separation with clear dependencies
- Proper use of modern CMake features
- Interface/implementation separation maintained
- Supports incremental builds efficiently

## Future Evolution

### When nvcc Supports Modules

Once CUDA supports C++20 modules:

1. Deprecate traditional header target
2. Migrate CUDA code to use `import mathlib`
3. Remove `.h` files (keep `.cppm` only)
4. Simplify CMake to single module target

**Migration is seamless** because the API is identical in both modes.

## Validation

Both consumers compile and run successfully, demonstrating:

- ✅ CUDA code works with traditional headers
- ✅ C++20 code works with module imports
- ✅ Same implementation serves both modes
- ✅ API is identical regardless of inclusion method
- ✅ Build system manages both targets correctly

## References

- [CMake C++20 Modules](https://www.kitware.com/import-cmake-c20-modules/)
- [C++20 Modules Tutorial](https://vector-of-bool.github.io/2019/03/10/modules-1.html)
- [CUDA C++ Best Practices](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/)

---

**Author**: Stroustrup + Brooks
**Design Philosophy**: Express intent in types, make decisions you can live with
