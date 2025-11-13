# CI/CD Pipeline - Rust CUDA Project

## Overview

The Rust CUDA project uses GitHub Actions workflows to automate building, testing, and publishing container images. The pipeline ensures code quality across multiple platforms (Linux/Windows) and CUDA versions (11.8.0, 12.8.1) with support for both x86_64 and ARM64 architectures.

## Workflow Files

All workflows are stored in `.github/workflows/`. Here's the complete automation infrastructure:

### 1. CI on Linux (`ci_linux.yml`)
**Purpose**: Build and validate code on Linux with multiple configurations

**Triggers**:
- Pull requests (excluding markdown files)
- Push to main branch (excluding markdown files)
- Manual trigger via GitHub Actions UI

**Build Job (build)**:
- Matrix configuration: 5 variants
  - Ubuntu 22.04 / CUDA 12.8.1 / x86_64
  - Ubuntu 22.04 / CUDA 12.8.1 / ARM64
  - Ubuntu 24.04 / CUDA 12.8.1 / x86_64
  - Ubuntu 24.04 / CUDA 12.8.1 / ARM64
  - RockyLinux 9 / CUDA 12.8.1 / x86_64

- Build steps:
  1. Checkout repository
  2. Verify CUDA and Rust installation
  3. Load Rust cache (key: matrix name + commit SHA)
  4. Format check with `cargo fmt`
  5. Build all CUDA bindings (`cust_raw` with all-features)
  6. Build workspace (excluding optix*, path-tracer, denoiser, examples)
  7. Clippy linting with strict warnings enabled
  8. Documentation generation with strict doctest flags
  9. Upload build artifacts with 1-day retention

**Test Job (test)**:
- Depends on successful build job
- Runs only when:
  - Build succeeded AND
  - (Push to main OR manual dispatch OR PR with write permission)
- Downloads build artifacts and prepares for remote GPU testing
- Currently stubbed out - requires Modal integration

**Compile Tests Job (compiletest)**:
- Standalone job for UI compilation tests
- Uses ubuntu24-cuda12 container
- Runs on three target architectures: compute_61, compute_70, compute_90
- Validates shader compilation without GPU execution

**Artifact Handling**:
- Format: `target_debug-{SANITIZED_NAME}-{RUN_ID}`
- Path: `target/debug`
- Retention: 1 day

### 2. CI on Windows (`ci_windows.yml`)
**Purpose**: Validate Windows build compatibility with CUDA and LLVM

**Triggers**:
- Pull requests (excluding markdown files)
- Push to main branch (excluding markdown files)

**Build Job (rust)**:
- Configuration: Windows latest + CUDA 12.8.1
- Special environment: `LLVM_LINK_STATIC=1` (links LLVM statically on Windows)

- Build steps:
  1. Checkout repository
  2. Install CUDA 12.8.1 via Jimver/cuda-toolkit action
  3. Install Rust toolchain components (rustfmt, clippy)
  4. Update PATH to expose CUDA nvvm bin directory
  5. Verify installations
  6. Load Rust cache
  7. Format check and linting
  8. Build bindings and workspace (more packages excluded than Linux)
  9. Documentation validation

**CUDA Packages Installed**:
- nvcc, nvrtc, nvrtc_dev, cuda_profiler_api, cudart, cublas, cublas_dev, curand, curand_dev

**Notes**:
- Compile tests disabled on Windows (DLL issues requiring Windows-specific expertise)
- More packages excluded from workspace build due to Windows compatibility
- Uses network installation method (not local cache) for CUDA

### 3. Build CI Container Images (`container_images.yml`)
**Purpose**: Build and publish multi-architecture Docker images for CI environments

**Triggers**:
- Manual dispatch (workflow_dispatch)
- Pull requests modifying `.github/workflows/container_images.yml` or `container/**`
- Push to main modifying container files

**Build Images Job (build-images)**:
- Matrix strategy: 2 architectures × 4 variants
  - Architectures: amd64 (ubuntu-latest), arm64 (ubuntu-24.04-arm)
  - Variants:
    - Ubuntu 22.04 / CUDA 11.8.0
    - Ubuntu 22.04 / CUDA 12.8.1
    - Ubuntu 24.04 / CUDA 12.8.1
    - RockyLinux 9 / CUDA 12.8.1

- Build process:
  1. Validate platform matches runner (amd64 = x86_64, arm64 = aarch64)
  2. Login to GitHub Container Registry (ghcr.io)
  3. Extract metadata for Docker tags/labels
  4. Set up Docker Buildx for multi-architecture builds
  5. Build and push with digest output (push only on non-PR)
  6. Leverage GitHub Actions cache for layers
  7. Upload digest artifacts for manifest merging

- Artifact handling:
  - Format: `digests-{IMAGE_NAME}-{ARCH}`
  - Retention: 1 day
  - Conditional upload: Only non-PR events

**Merge Manifests Job (merge-manifests)**:
- Depends on successful build-images job
- Runs only on non-PR events
- Creates multi-architecture manifest lists
- Tags applied (dynamic):
  - Branch refs: `type=ref,event=branch`
  - PR refs: `type=ref,event=pr`
  - Semantic versions: `type=semver`
  - Short SHA: `type=sha`
  - Latest tag: `type=raw,value=latest` (on default branch)

- Manifest creation:
  1. Download digests from artifacts
  2. Create multi-arch manifest using `docker buildx imagetools`
  3. Inspect final image to validate architecture support
  4. Push to registry with all computed tags

**Image Registry**: `ghcr.io/rust-gpu/` (GitHub Container Registry)

## Environment Setup in CI

### Linux Containers
All containers based on NVIDIA CUDA images with consistent setup:

**Base**: `nvcr.io/nvidia/cuda:{VERSION}-cudnn-devel-{DISTRO}`

**Installed Toolchain**:
- CUDA Development Kit (nvcc, nvrtc, cublas, etc.)
- LLVM 7.1.0 (built from source for all architectures)
- Rust toolchain (latest stable)
- Build tools: GCC, CMake, Ninja, pkg-config
- Graphics libraries: X11, Xcursor, Xinerama, Xrandr, fontconfig
- Standard utilities: curl, xz-utils, zlib1g-dev, openssl

**Environment Variables**:
```bash
LD_LIBRARY_PATH="/usr/local/cuda/nvvm/lib64:${LD_LIBRARY_PATH}"
LLVM_LINK_STATIC=1
RUST_LOG=info
RUST_BACKTRACE=1
```

### Windows Setup
- CUDA installed via Jimver/cuda-toolkit GitHub Action
- Network installation method (no local cache)
- nvvm bin added to PATH for codegen backend access
- `LLVM_LINK_STATIC=1` enforces static linking

## Build Artifacts and Caching

### Rust Cache
- Tool: `Swatinem/rust-cache@v2` (GitHub Action)
- Cache key: `{MATRIX_VARIANT}-{COMMIT_SHA}` (Linux)
- Cache key: `{OS}-{TARGET}-{CUDA}` (Windows)
- Caches: Cargo registry, git database, target directory
- Speeds up builds significantly across CI runs

### Build Artifacts
- Stored in `target/debug` directory
- Sanitized names for filesystem compatibility
- Short retention (1 day) to save storage
- Downloaded by test job for validation

## Debugging CI Failures

### Common Issues and Solutions

**Rustfmt Failures**:
- Likely cause: Code formatting inconsistency
- Debug: Run `cargo fmt --all` locally
- Check: Ensure all code is formatted before commit

**Clippy Warnings as Errors**:
- Likely cause: New lint warnings
- Debug: Run `cargo clippy --workspace -- -Dwarnings` locally
- Inspect: Review specific warnings and fix code or suppress with `#[allow(...)]`

**Documentation Build Failures**:
- Likely cause: Broken doc links or missing documentation
- Debug: Run `cargo doc --all-features --document-private-items --no-deps` locally
- Issues: Check for invalid cross-references, missing code examples

**CUDA Verification Failures**:
- Likely cause: Incorrect CUDA_PATH or nvcc not found
- Windows: Check "Update PATH to expose CUDA codegen backend" step added PATH correctly
- Linux: Verify container image has CUDA installed (check Dockerfile)

**Container Image Build Failures**:
- Likely cause: LLVM 7 compilation timeout or network issues
- Debug: Check Docker logs for hung builds
- Solution: LLVM build can timeout on slower hardware (esp. ARM) - increase timeout in GitHub Actions
- Network: Verify curl retry logic in download_ci_optix.bash working correctly

**Test Stub Failures**:
- Current state: Test job is stubbed (runs `echo "Stubbed out"`)
- Future: Requires Modal integration for GPU access
- Workaround: Use local GPU for testing

### Accessing Workflow Logs
1. Navigate to GitHub repository Actions tab
2. Select failed workflow run
3. Expand job logs to see step-by-step execution
4. Check runner logs for infrastructure issues

### Local Reproduction

**Using Docker Containers**:
```bash
# Pull the same container as CI
docker pull ghcr.io/rust-gpu/rust-cuda-ubuntu24-cuda12:latest

# Build locally in container environment
docker run --rm -v "$(pwd)":/data/rust-cuda \
  ghcr.io/rust-gpu/rust-cuda-ubuntu24-cuda12:latest \
  bash -c "cd /data/rust-cuda && cargo build --workspace"
```

**Without Docker**:
- Install CUDA matching CI version
- Install LLVM 7.1.0
- Install Rust stable
- Run individual cargo commands from workflow files

**Windows Local Build**:
```powershell
# Install CUDA 12.8.1 manually
# Add CUDA_PATH\nvvm\bin to PATH
# Then run same cargo commands as CI
cargo build --workspace
```

## Artifact Handling and Deployment

### Build Artifacts
- Uploaded with 1-day retention to save GitHub Actions storage
- Used for test job validation
- Automatically cleaned up after retention period

### Container Images
- Published to GitHub Container Registry (ghcr.io)
- Multi-architecture manifests created automatically
- Pushed with multiple tags:
  - `latest` (on main branch push)
  - Git refs (branches/PRs)
  - Commit SHA (short format)
  - Semantic version tags (if using releases)
- Leverage Docker build cache for faster rebuilds

### Documentation
- Generated by compile tests on compute architectures
- Not currently deployed (future: GitHub Pages integration)
- Guide deployment via `deploy_guide.yml` publishes to GitHub Pages

## Container Image Versioning

### Image Naming Scheme
Repository: `ghcr.io/rust-gpu/rust-cuda-{distro}-{cuda}`

Examples:
- `ghcr.io/rust-gpu/rust-cuda-ubuntu24-cuda12:latest`
- `ghcr.io/rust-gpu/rust-cuda-ubuntu22-cuda11:latest`
- `ghcr.io/rust-gpu/rust-cuda-rockylinux9-cuda12:latest`

### Tag Strategy
Each image has multiple concurrent tags:
- `latest` - Most recent build on main branch
- `main` - Branch ref (current branch)
- `v1.2.3` - Semantic version releases
- `abc1234` - Commit SHA (short)

### Version Updates
- Update Dockerfile when CUDA version changes
- Rebuild container workflow triggers automatically on container/ changes
- Multi-arch builds ensure consistency across platforms

## Documentation Deployment

### Deploy Guide Workflow (`deploy_guide.yml`)

**Purpose**: Deploy Rust CUDA guide to GitHub Pages

**Trigger**: Push to main branch only

**Process**:
1. Checkout with full history (fetch-depth: 0)
2. Download and install latest mdbook release
3. Build guide with `mdbook build guide`
4. Configure GitHub Pages environment
5. Upload artifacts to pages
6. Deploy to GitHub Pages

**Output**: Hosted documentation at `https://rust-gpu.github.io/rust-cuda/`

**Concurrency**: Only one deployment at a time (cancel in progress)

## Environment Variables

### Standard CI Environment
```bash
RUST_LOG=info           # Enable info-level logging
RUST_BACKTRACE=1        # Full backtraces on panic
```

### Secrets Used
- `GITHUB_TOKEN` - Standard GitHub Actions token (write access)
- `MODAL_TOKEN_ID` - For GPU testing (stubbed, not yet implemented)
- `MODAL_TOKEN_SECRET` - For GPU testing (stubbed, not yet implemented)

### Platform-Specific
- `LLVM_LINK_STATIC=1` - Windows only, enforces static LLVM linking
- `RUSTFLAGS=-Dwarnings` - During clippy, treats warnings as errors
- `RUSTDOCFLAGS=-Dwarnings` - During doc build, treats doc warnings as errors

## Workflow Interdependencies

```
Pull Request / Push
  ├─ ci_linux.yml
  │   ├─ build (5 matrix configs)
  │   │   └─ test (conditional: build success + PR permission check)
  │   └─ compiletest (standalone)
  │
  ├─ ci_windows.yml
  │   └─ rust (Windows native)
  │
  └─ container_images.yml (only if container/ changed)
      ├─ build-images (2 arch × 4 variants)
      │   └─ merge-manifests (conditional: non-PR)
      └─ deploy_guide.yml (main push only)
```

## Monitoring and Troubleshooting

### Check Workflow Status
1. GitHub repository > Actions tab
2. View workflow run details
3. Expand job logs for specific failures

### Common Build Times
- Linux build matrix: 5-10 minutes per config
- Windows build: 10-15 minutes
- Container images: 30-45 minutes per architecture (LLVM compilation heavy)
- Documentation build: 2-3 minutes

### Performance Optimization
- Rust cache significantly speeds up builds (cached targets)
- Docker layer cache reuses unchanged Dockerfile steps
- Parallel matrix execution runs variants concurrently

## Key Files and Locations

- Workflows: `.github/workflows/*.yml`
- Containers: `container/{distro}-{cuda}/Dockerfile`
- Scripts: `scripts/download_ci_optix.bash`
- Guide source: `guide/` directory
- Rust workspace: `Cargo.toml` (root), `crates/*/Cargo.toml`

## Future Improvements

- Implement GPU testing job (Modal integration complete)
- Add semantic versioning for releases
- Expand Windows compile test support
- Add performance benchmarking pipeline
- Implement artifact caching for container builds
