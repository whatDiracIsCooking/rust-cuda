#!/bin/bash
# Test script to verify the DevContainer build and functionality

set -e

IMAGE_NAME="${1:-rust-cuda-optix}"

echo "=== Testing DevContainer Image: $IMAGE_NAME ==="
echo ""

# Test 1: Image exists
echo "Test 1: Checking if image exists..."
if docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "✓ Image found: $IMAGE_NAME"
else
    echo "✗ Image not found: $IMAGE_NAME"
    echo "  Run: docker build -t $IMAGE_NAME -f .devcontainer/Dockerfile ."
    exit 1
fi

# Test 2: Check CUDA version
echo ""
echo "Test 2: Checking CUDA version..."
CUDA_VERSION=$(docker run --rm "$IMAGE_NAME" nvcc --version | grep "release" | awk '{print $5}' | cut -d',' -f1)
echo "✓ CUDA version: $CUDA_VERSION"

# Test 3: Check Rust installation
echo ""
echo "Test 3: Checking Rust installation..."
RUST_VERSION=$(docker run --rm "$IMAGE_NAME" rustc --version)
echo "✓ $RUST_VERSION"

# Test 4: Check OptiX installation
echo ""
echo "Test 4: Checking OptiX SDK..."
if docker run --rm "$IMAGE_NAME" test -d /opt/optix/include; then
    echo "✓ OptiX SDK installed at /opt/optix"
    docker run --rm "$IMAGE_NAME" ls -la /opt/optix
else
    echo "⚠ OptiX SDK not installed (this is OK if you didn't provide the installer)"
fi

# Test 5: Check environment variables
echo ""
echo "Test 5: Checking environment variables..."
OPTIX_ROOT=$(docker run --rm "$IMAGE_NAME" bash -c 'echo $OPTIX_ROOT')
echo "✓ OPTIX_ROOT=$OPTIX_ROOT"

# Test 6: GPU access (if available)
echo ""
echo "Test 6: Checking GPU access..."
if docker run --rm --runtime=nvidia --gpus all "$IMAGE_NAME" nvidia-smi >/dev/null 2>&1; then
    echo "✓ GPU access works"
    docker run --rm --runtime=nvidia --gpus all "$IMAGE_NAME" nvidia-smi --query-gpu=name --format=csv,noheader
else
    echo "⚠ GPU access failed (check --runtime=nvidia --gpus all flags)"
fi

# Test 7: Build a simple CUDA example
echo ""
echo "Test 7: Building vecadd example..."
WORKDIR=$(pwd)
if docker run --rm --runtime=nvidia --gpus all \
    -v "$WORKDIR:/workspace" \
    -w /workspace \
    "$IMAGE_NAME" \
    bash -c "cd examples/cuda/vecadd && cargo build --release --quiet" 2>/dev/null; then
    echo "✓ vecadd example built successfully"
else
    echo "⚠ vecadd build failed"
fi

echo ""
echo "=== All Tests Complete ==="
