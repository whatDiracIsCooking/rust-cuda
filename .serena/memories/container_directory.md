# Container Directory Overview

## Purpose
The `container/` directory provides Docker configurations for reproducible builds and CI/CD pipelines. These containerized environments ensure consistent compilation and testing across different Linux distributions and CUDA versions.

## Directory Structure
Contains Dockerfiles for multiple Linux distributions, each supporting multiple CUDA versions:

### Supported Distributions
- **Ubuntu 24.04** - Latest Ubuntu LTS
- **Ubuntu 22.04** - Stable Ubuntu LTS
- **Rocky Linux 9** - Enterprise Linux alternative

### CUDA Versions
- **CUDA 11.8.0** - Legacy support
- **CUDA 12.8.1** - Current version
- **LLVM Debug variant** - Development debugging support

## Configuration Details

### Architecture Support
- **amd64** - x86-64 processors
- **ARM** - ARM64/AArch64 processors

### Standard Installation Stack
Each Dockerfile installs a consistent development environment:
- CUDA base runtime and toolkit
- Build tools (GCC, CMake, Ninja)
- Graphics libraries (OpenGL, graphics development)
- LLVM 7.1.0 toolchain
- Rust toolchain (latest stable)
- Standard development utilities

## Key Features

### Reproducibility
- Fixed base images and package versions ensure identical build environments
- Eliminates "works on my machine" issues
- Enables reliable CI/CD testing

### CI/CD Integration
- Used in GitHub Actions and automated testing workflows
- Provides baseline environments for regression testing
- Supports parallel builds across multiple configurations

### Development Flexibility
- Debug LLVM variant for detailed build troubleshooting
- Multi-distro support for broader platform coverage
- Version flexibility for CUDA compatibility testing

## Usage in Development Workflow

### Building Container Images
Containers are typically built during CI/CD setup or for local testing:
```bash
docker build -f container/ubuntu-24.04.dockerfile -t rust-cuda:ubuntu-24.04 .
docker build -f container/rocky-9-cuda-12.8.1-llvm-debug.dockerfile -t rust-cuda:rocky-debug .
```

### Role in CI/CD
- GitHub Actions uses containers for matrix testing across distros/CUDA versions
- Ensures compatibility before merge
- Enables rapid feedback on platform-specific issues

### Local Development
Developers can use containers to:
- Test builds in specific environments
- Debug platform-specific compilation errors
- Validate cross-architecture changes before CI

## Naming Convention
Files follow pattern: `{distro}-{version}-{optional-variant}.dockerfile`

Example: `ubuntu-24.04.dockerfile`, `rocky-9-cuda-12.8.1-llvm-debug.dockerfile`

## Quick Reference
- **When to update**: New CUDA versions, distro updates, toolchain changes
- **Key contact**: CI/CD configuration maintainers
- **Impact scope**: Affects all reproducible builds and CI pipeline behavior
