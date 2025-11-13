# Rust CUDA Development Setup Guide

This memory documents the complete development environment setup for the Rust CUDA project, including dependencies, configurations, and troubleshooting steps.

## Prerequisites Overview

The Rust CUDA project enables high-performance GPU computing with Rust. Setting up requires careful attention to CUDA SDK versions, LLVM compatibility, and Rust toolchain requirements.

### System Requirements

- **GPU**: NVIDIA GPU with compute capability 6.1+ (for full feature support)
- **Driver**: NVIDIA drivers compatible with your CUDA version (typically >= 470.57.02)
- **OS**: Linux (Ubuntu 22.04, 24.04, or RockyLinux 9) or Windows 10/11
- **Architecture**: x86_64 (tested) or ARM64 (experimental)

## Required Dependencies

### CUDA SDK

**Supported Versions:**
- **Primary**: CUDA 12.x (12.8.1 recommended)
- **Secondary**: CUDA 11.2-11.8 (legacy support)
- **Minimum for execution**: CUDA 9.0+

Install from: https://developer.nvidia.com/cuda-downloads

**Linux Installation Example:**
```bash
# Ubuntu 24.04
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get install cuda-toolkit-12-8
```

### LLVM

**Required Version**: LLVM 7.1.0

The build system searches for LLVM in this order:
1. `LLVM_CONFIG` environment variable (full path to llvm-config)
2. `llvm-config` in PATH
3. Auto-download prebuilt binaries (Windows only)

**Linux Installation:**
```bash
# For Ubuntu 24.04 / 22.04
apt-get install llvm-7 llvm-7-dev clang
# Or install from source (see Dockerfile for detailed build steps)
```

**Manual Build** (if prebuilt unavailable):
```bash
curl -L -O https://github.com/llvm/llvm-project/releases/download/llvmorg-7.1.0/llvm-7.1.0.src.tar.xz
tar -xf llvm-7.1.0.src.tar.xz
cd llvm-7.1.0.src && mkdir build && cd build
cmake -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_TARGETS_TO_BUILD="X86;NVPTX" \
  -DCMAKE_INSTALL_PREFIX=/usr ..
ninja && ninja install
ln -s /usr/bin/llvm-config /usr/bin/llvm-config-7
```

### Optional: OptiX SDK

**For Path Tracer Examples:**
- Download from: https://developer.nvidia.com/designworks/optix/download
- Latest tested version: OptiX SDK 9.0.0

**Linux Setup:**
```bash
export OPTIX_ROOT=/opt/NVIDIA-OptiX-SDK-9.0.0-linux64-x86_64
export OPTIX_ROOT_DIR=/opt/NVIDIA-OptiX-SDK-9.0.0-linux64-x86_64
```

### Additional System Libraries

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install \
  build-essential \
  curl \
  libssl-dev \
  libtinfo-dev \
  pkg-config \
  xz-utils \
  zlib1g-dev \
  ninja-build
```

**For GUI Examples (optional):**
```bash
sudo apt-get install \
  cmake \
  libfontconfig-dev \
  libx11-xcb-dev \
  libxcursor-dev \
  libxi-dev \
  libxinerama-dev \
  libxrandr-dev
```

## Rust Toolchain Setup

### Nightly Version

The GPU codegen only works on a specific nightly version. This is specified in `rust-toolchain.toml`:

```toml
[toolchain]
channel = "nightly-2025-08-04"
components = ["clippy", "llvm-tools-preview", "rust-src", "rustc-dev", "rustfmt", "rust-analyzer"]
```

### Installation

**Install Rust (if not already installed):**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

**Install Nightly Components:**
```bash
rustup toolchain install nightly-2025-08-04
rustup default nightly-2025-08-04
rustup component add rust-src rustc-dev llvm-tools-preview
```

**Verify Installation:**
```bash
rustc --version
cargo --version
rustup show
```

### Important Notes

- Only the GPU codegen (`rustc_codegen_nvvm`) requires nightly
- CPU-side libraries (`cust`, `gpu_rand`) work on stable Rust
- Always copy the `rust-toolchain.toml` file to any project using the GPU codegen

## Environment Variables

### Essential Variables

```bash
# CUDA paths (usually auto-detected, set if needed)
export CUDA_PATH=/usr/local/cuda
export LD_LIBRARY_PATH=/usr/local/cuda/nvvm/lib64:$LD_LIBRARY_PATH

# LLVM configuration
export LLVM_CONFIG=/usr/bin/llvm-config-7
export LLVM_LINK_STATIC=1

# Optional: OptiX paths
export OPTIX_ROOT=/opt/NVIDIA-OptiX-SDK-9.0.0-linux64-x86_64
export OPTIX_ROOT_DIR=/opt/NVIDIA-OptiX-SDK-9.0.0-linux64-x86_64

# Logging and debugging
export RUST_LOG=info
export RUST_BACKTRACE=1
```

### Windows-Specific Variables

The Windows CI automatically adds NVVM binaries to PATH:
```powershell
$env:PATH += ";$env:CUDA_PATH\nvvm\bin"
```

## Docker Development Setup

### Quick Start

**Build and Run:**
```bash
# Build the container
docker build -f container/ubuntu24-cuda12/Dockerfile -t rust-cuda-ubuntu24 .

# Run with GPU support
docker run --rm --runtime=nvidia --gpus all -it rust-cuda-ubuntu24

# Inside container
cd ~/rust-cuda
cargo build --workspace --exclude "optix*" --exclude "path-tracer"
```

### Available Container Images

| Image | CUDA | Base OS | Use Case |
|-------|------|---------|----------|
| `container/ubuntu24-cuda12/` | 12.8.1 | Ubuntu 24.04 | Latest, recommended |
| `container/ubuntu22-cuda12/` | 12.8.1 | Ubuntu 22.04 | Stable |
| `container/rockylinux9-cuda12/` | 12.8.1 | RockyLinux 9 | Enterprise Linux |
| `container/ubuntu22-cuda11/` | 11.8 | Ubuntu 22.04 | Legacy |

### Docker Prerequisites

1. **NVIDIA Docker Runtime**: Install from https://github.com/NVIDIA/nvidia-docker
2. **GPU Support Configuration**:
   ```bash
   # Enable GPU in Docker (add to /etc/docker/daemon.json)
   {
     "runtimes": {
       "nvidia": {
         "path": "nvidia-container-runtime",
         "runtimeArgs": []
       }
     }
   }
   # Restart Docker daemon
   sudo systemctl restart docker
   ```

### Dev Container Setup

VS Code users can use the bundled dev container configuration:

1. Copy `.devcontainer.json` to `.devcontainer/devcontainer.json`
2. Install "Dev Containers" extension in VS Code
3. Click "Reopen in Container"
4. VS Code will automatically:
   - Pull the Ubuntu 24.04/CUDA 12.8.1 container image
   - Mount the project directory
   - Install Rust Analyzer extension

**Configuration File** (`.devcontainer.json`):
```json
{
  "image": "ghcr.io/rust-gpu/rust-cuda-ubuntu24-cuda12:latest",
  "containerEnv": {
    "NVIDIA_DRIVER_CAPABILITIES": "all"
  },
  "runArgs": ["--runtime=nvidia", "--gpus", "all"],
  "customizations": {
    "vscode": {
      "extensions": ["rust-lang.rust-analyzer"]
    }
  }
}
```

## Local Linux Setup

### Complete Ubuntu 24.04 Setup Script

```bash
#!/bin/bash
set -e

# Install CUDA SDK
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get install cuda-toolkit-12-8

# Install LLVM 7
curl -L -O https://github.com/llvm/llvm-project/releases/download/llvmorg-7.1.0/llvm-7.1.0.src.tar.xz
tar -xf llvm-7.1.0.src.tar.xz
cd llvm-7.1.0.src && mkdir build && cd build
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_TARGETS_TO_BUILD="X86;NVPTX" -CMAKE_INSTALL_PREFIX=/usr ..
ninja && sudo ninja install
sudo ln -s /usr/bin/llvm-config /usr/bin/llvm-config-7

# Install system dependencies
sudo apt-get install -y \
  build-essential curl clang \
  libssl-dev libtinfo-dev pkg-config \
  xz-utils zlib1g-dev ninja-build

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Setup Rust toolchain
rustup toolchain install nightly-2025-08-04
rustup default nightly-2025-08-04
rustup component add rust-src rustc-dev llvm-tools-preview

# Configure environment
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/nvvm/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
echo 'export LLVM_LINK_STATIC=1' >> ~/.bashrc
echo 'export RUST_LOG=info' >> ~/.bashrc
source ~/.bashrc

echo "Setup complete!"
```

## Windows Setup

### CUDA Installation

1. Download from: https://developer.nvidia.com/cuda-downloads
2. Run the installer as Administrator
3. Select custom installation with NVCC and NVRTC components
4. Default installation path: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8`

### LLVM Installation

**Option 1: LLVM Auto-Download**
The build system automatically downloads prebuilt LLVM on Windows. No manual installation required.

**Option 2: Manual Installation**
```powershell
# Install via LLVM pre-built binaries
# From: https://releases.llvm.org/download.html
# Download LLVM-7.1.0-win64.exe and run installer
# Add to PATH: C:\Program Files\LLVM\bin
```

### Rust Installation

```powershell
# Download and run Rust installer
# From: https://rustup.rs/

# Install nightly toolchain
rustup toolchain install nightly-2025-08-04
rustup default nightly-2025-08-04
rustup component add rust-src rustc-dev llvm-tools-preview
```

### VS Code Setup

1. Install "Rust Analyzer" extension
2. Optional: Install "CUDA C++" extension for syntax highlighting in PTX
3. Open project and select nightly toolchain when prompted

## Verification Steps

### Verify CUDA Installation

```bash
# Check CUDA compiler
nvcc --version

# Test GPU visibility
nvidia-smi

# Test CUDA samples (optional)
cd /usr/local/cuda/samples/1_Utilities/deviceQuery && make && ./deviceQuery
```

### Verify Rust Setup

```bash
# Check Rust version
rustc --version      # Should show nightly-2025-08-04
cargo --version
rustup show

# Verify components
rustup component list

# Check LLVM
llvm-config --version  # Should be 7.1.0
```

### Build Test

```bash
# Clone or navigate to project
cd rust-cuda

# Verify toolchain is loaded
rustup show
# Should display: nightly-2025-08-04-x86_64-unknown-linux-gnu (override)

# Build simple example
cargo build --workspace --exclude "optix*" --exclude "path-tracer" \
  --exclude "denoiser" --exclude "ex0*" --exclude "cudnn*"

# Run tests (basic CPU-side tests)
cargo test --lib --exclude "optix*" --exclude "path-tracer"
```

## Common Setup Issues and Solutions

### Issue: "LLVM_CONFIG not found"

**Solution:**
```bash
# Find llvm-config location
which llvm-config-7
# Or install LLVM
apt-get install llvm-7
# Set environment variable
export LLVM_CONFIG=/usr/bin/llvm-config-7
```

### Issue: "libnvvm not found"

**Problem:** `libnvvm` library not in PATH or LD_LIBRARY_PATH

**Solution:**
```bash
# Add to environment
export LD_LIBRARY_PATH=/usr/local/cuda/nvvm/lib64:$LD_LIBRARY_PATH
# Or check CUDA installation location
ls $CUDA_PATH/nvvm/lib64/
```

### Issue: "nvcc: command not found"

**Problem:** CUDA not installed or not in PATH

**Solution:**
```bash
# Verify CUDA installation
ls /usr/local/cuda/bin/nvcc
# Add to PATH
export PATH=/usr/local/cuda/bin:$PATH
```

### Issue: "Nightly toolchain mismatch"

**Problem:** Using wrong nightly version

**Solution:**
```bash
# Verify required version
cat rust-toolchain.toml
# Install correct version
rustup toolchain install nightly-2025-08-04
# Set as default
rustup default nightly-2025-08-04
```

### Issue: "GPU not detected in container"

**Problem:** Docker GPU support not configured

**Solution:**
```bash
# Verify nvidia-docker is installed
which nvidia-docker

# Test GPU access
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.8.1-base nvidia-smi

# If not working, reinstall nvidia-docker from:
# https://github.com/NVIDIA/nvidia-docker
```

### Issue: "Windows PATH issues with CUDA DLLs"

**Problem:** CUDA DLLs not found at runtime

**Solution (from CI):**
```powershell
# Add NVVM binaries to PATH
$env:PATH += ";$env:CUDA_PATH\nvvm\bin"
# Make permanent (set in System Environment Variables)
```

## IDE/Editor Setup Recommendations

### VS Code (Recommended)

**Extensions:**
- Rust Analyzer (official)
- Even Better TOML (for Cargo.toml)
- crates (for version checking)

**Settings** (`.vscode/settings.json`):
```json
{
  "[rust]": {
    "editor.defaultFormatter": "rust-lang.rust-analyzer",
    "editor.formatOnSave": true
  },
  "rust-analyzer.check.command": "clippy"
}
```

### CLion / IntelliJ IDEA

- Install Rust plugin
- Configure toolchain: Settings > Languages & Frameworks > Rust > Toolchain
- Select nightly-2025-08-04
- Enable macro expansion for better autocomplete

### Neovim / Vim

Use with rust.vim and nvim-lspconfig:
```lua
-- Configure rust-analyzer to use nightly
require('lspconfig').rust_analyzer.setup {
  settings = {
    ["rust-analyzer"] = {
      cargo = {
        extraEnv = { RUSTUP_TOOLCHAIN = "nightly-2025-08-04" }
      }
    }
  }
}
```

## Quick-Start Commands

### Start Fresh Development Environment

```bash
# 1. Clone repository
git clone https://github.com/Rust-GPU/rust-cuda.git
cd rust-cuda

# 2. Verify Rust toolchain (auto-loads from rust-toolchain.toml)
rustup show

# 3. Build core libraries
cargo build --workspace --exclude "optix*" --exclude "path-tracer"

# 4. Run clippy checks
cargo clippy --workspace --exclude "optix*"

# 5. Build documentation
cargo doc --workspace --no-deps
```

### Build Examples

```bash
# Vector addition example (CPU-side only)
cargo run --example add

# CUDA examples (requires GPU)
cd examples/cuda/cpu/add && cargo run --release
```

### Docker Development Loop

```bash
# Build container once
docker build -f container/ubuntu24-cuda12/Dockerfile -t rust-cuda-dev .

# Development workflow
docker run --rm --runtime=nvidia --gpus all \
  -v $(pwd):/root/rust-cuda \
  -w /root/rust-cuda \
  rust-cuda-dev \
  bash -c "cargo build && cargo clippy && cargo doc --no-deps"
```

## Platform-Specific Differences

### Linux vs Windows

| Aspect | Linux | Windows |
|--------|-------|---------|
| CUDA Install | Package manager or manual | Installer executable |
| LLVM | Install via package manager or build | Auto-downloaded by build system |
| PATH Separators | `:` | `;` |
| Path Style | `/usr/local/cuda` | `C:\Program Files\NVIDIA GPU...` |
| Line Endings | LF | CRLF (Git should auto-convert) |
| GPU Runtime | NVIDIA Driver | NVIDIA Driver + CUDA SDK |

### Ubuntu 22.04 vs 24.04 vs RockyLinux 9

All three are well-supported in CI. Ubuntu 24.04 is recommended for latest packages but Ubuntu 22.04 is stable. RockyLinux 9 requires different package manager (`yum` instead of `apt`).

## Next Steps After Setup

1. **Verify Installation**: Run the verification commands above
2. **Read Getting Started Guide**: `guide/src/guide/getting_started.md`
3. **Build Examples**: Start with `examples/cuda/cpu/add`
4. **Explore Crates**:
   - `cust`: CPU-side CUDA API wrapper
   - `cuda_std`: GPU-side standard library
   - `gpu_rand`: GPU random number generation
5. **Join Community**: Check GitHub issues and discussions

## References

- **Official CUDA Documentation**: https://docs.nvidia.com/cuda/
- **Rust CUDA Repository**: https://github.com/Rust-GPU/rust-cuda
- **LLVM NVVM Specification**: https://docs.nvidia.com/cuda/nvvm-ir-spec/
- **OptiX Documentation**: https://docs.nvidia.com/designworks/optix/
- **Project Guide**: In `guide/src/` directory (built with mdBook)
