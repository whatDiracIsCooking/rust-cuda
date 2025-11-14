# Rust-CUDA DevContainer

DevContainer for rust-cuda with optional OptiX SDK support.

## Quick Start (No OptiX)

```bash
# Build the container
docker build -t rust-cuda-optix -f .devcontainer/Dockerfile .

# Run examples
docker run --rm --runtime=nvidia --gpus all -it \
  -v $(pwd):/workspace -w /workspace \
  rust-cuda-optix \
  bash -c "cd examples/cuda/vecadd && cargo run --release"

# Or start interactive shell
docker run --rm --runtime=nvidia --gpus all -it \
  -v $(pwd):/workspace -w /workspace \
  rust-cuda-optix
```

**All CUDA examples work without OptiX.** Only raytracing examples need it.

## Adding OptiX (Optional)

If you need raytracing examples:

1. Download from https://developer.nvidia.com/designworks/optix/download
2. Place `NVIDIA-OptiX-SDK-8.0.0-linux64-x86_64.sh` in `.devcontainer/`
3. Rebuild: `docker build -t rust-cuda-optix -f .devcontainer/Dockerfile .`

Or use build script: `./.devcontainer/build.sh`

## VS Code

Open project → "Reopen in Container" → Everything configured automatically.

## Testing

```bash
./.devcontainer/test.sh rust-cuda-optix
```

## What's Included

- Base: `ghcr.io/rust-gpu/rust-cuda-ubuntu24-cuda12:latest`
- CUDA 12.8.1
- Rust nightly with GPU support
- OptiX 8.0.0 (if installer provided)
- Environment: `OPTIX_ROOT=/opt/optix`

Build works with or without OptiX installer.
