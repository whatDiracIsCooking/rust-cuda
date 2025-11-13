cmake_minimum_required(VERSION 3.28)  # C++20 modules require CMake 3.28+
project(MathLibDemo LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ============================================================================
# Traditional Library Target (for CUDA and legacy C++ users)
# ============================================================================
add_library(mathlib_traditional STATIC
    src/vector3.cpp
)

target_include_directories(mathlib_traditional
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_compile_features(mathlib_traditional PUBLIC cxx_std_17)

# ============================================================================
# C++20 Module Target (for modern C++20 users)
# ============================================================================
# Note: CMake 3.28+ has experimental C++20 module support
# This creates a module library that C++20 code can import

add_library(mathlib_module)

target_sources(mathlib_module
    PUBLIC
        FILE_SET CXX_MODULES FILES
            src/mathlib.cppm
)

# The module needs access to headers in the global module fragment
target_include_directories(mathlib_module
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link against the traditional implementation
target_link_libraries(mathlib_module
    PRIVATE
        mathlib_traditional
)

target_compile_features(mathlib_module PUBLIC cxx_std_20)

# ============================================================================
# Example: CUDA Consumer (uses traditional headers)
# ============================================================================
add_executable(cuda_user examples/cuda_user.cu)

target_link_libraries(cuda_user
    PRIVATE
        mathlib_traditional
)

set_target_properties(cuda_user PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
    CUDA_ARCHITECTURES "80;86"
)

# ============================================================================
# Example: C++20 Consumer (uses module imports)
# ============================================================================
add_executable(cpp20_user examples/cpp20_user.cpp)

target_link_libraries(cpp20_user
    PRIVATE
        mathlib_module
)

# ============================================================================
# Architecture Notes
# ============================================================================
# This dual-mode design provides:
# 1. **Backward compatibility**: CUDA and legacy C++ can use #include
# 2. **Forward compatibility**: C++20 code can use import
# 3. **Single source of truth**: Implementation in vector3.cpp serves both
# 4. **Clean migration path**: Users can switch from #include to import without
#    changing library code
#
# Trade-offs:
# - Requires CMake 3.28+ for module support
# - Slightly more complex build configuration
# - Module compilation is still experimental in some toolchains
#
# Benefits:
# - CUDA users unaffected by C++20 module limitations
# - Modern C++ users get faster compilation with modules
# - Library maintainers have single implementation to maintain
