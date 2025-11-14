#!/bin/bash
# Helper script to build the devcontainer with OptiX support

set -e

OPTIX_INSTALLER="NVIDIA-OptiX-SDK-8.0.0-linux64-x86_64.sh"
OPTIX_DOWNLOAD_URL="https://developer.download.nvidia.com/designworks/optix/secure/8.0.0/NVIDIA-OptiX-SDK-8.0.0-linux64-x86_64.sh"

echo "=== Rust-CUDA DevContainer Builder with OptiX ==="
echo ""

# Check if installer exists locally
if [ -f ".devcontainer/$OPTIX_INSTALLER" ]; then
    echo "✓ Found OptiX installer in .devcontainer/"
    echo "  Building with local installer..."
    docker build -t rust-cuda-optix -f .devcontainer/Dockerfile .
    exit 0
fi

echo "OptiX installer not found in .devcontainer/"
echo ""
echo "You have three options:"
echo ""
echo "1. Download manually from NVIDIA (requires login):"
echo "   https://developer.nvidia.com/designworks/optix/download"
echo "   Then place the installer in .devcontainer/ and run this script again"
echo ""
echo "2. Build with a custom URL (if you host the installer):"
echo "   docker build --build-arg OPTIX_SDK_URL=<your-url> -t rust-cuda-optix -f .devcontainer/Dockerfile ."
echo ""
echo "3. Build without OptiX (OptiX examples won't compile):"
echo "   docker build -t rust-cuda-optix -f .devcontainer/Dockerfile ."
echo ""

read -p "Continue building without OptiX? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Building without OptiX SDK..."
    docker build -t rust-cuda-optix -f .devcontainer/Dockerfile .
else
    echo "Aborted. Please obtain the OptiX installer and try again."
    exit 1
fi
