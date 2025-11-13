#!/bin/bash
# Build script for dual-mode library demo

set -e  # Exit on error

echo "=== Dual-Mode Library Demo Build ==="
echo ""

# Check CMake version
CMAKE_VERSION=$(cmake --version | head -n1 | cut -d' ' -f3)
echo "CMake version: $CMAKE_VERSION"

# Note: C++20 modules require CMake 3.28+
# If your CMake is older, this will fail with helpful error message

# Clean previous build
if [ -d "build" ]; then
    echo "Cleaning previous build..."
    rm -rf build
fi

# Create build directory
mkdir -p build
cd build

# Configure
echo ""
echo "=== Configuring with Ninja ==="
cmake .. -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

# Build
echo ""
echo "=== Building all targets ==="
ninja -v

# Run examples if built successfully
echo ""
echo "=== Running CUDA Example (traditional headers) ==="
./cuda_user

echo ""
echo "=== Running C++20 Example (module imports) ==="
./cpp20_user

echo ""
echo "=== Build Complete! ==="
echo ""
echo "Architecture summary:"
echo "  - mathlib_traditional: Static library with headers (CUDA-compatible)"
echo "  - mathlib_module: C++20 module library (modern C++)"
echo "  - cuda_user: CUDA consumer using #include"
echo "  - cpp20_user: C++20 consumer using import"
echo ""
echo "Both executables use the SAME underlying implementation!"
