# Based on the rust-cuda base image with OptiX SDK added
FROM ghcr.io/rust-gpu/rust-cuda-ubuntu24-cuda12:latest

# OptiX SDK version and download URL
# Note: Direct download requires authentication. This uses a publicly accessible mirror.
# For production, you should host the installer yourself or use build args.
ARG OPTIX_VERSION=8.0.0
ARG OPTIX_INSTALLER_NAME=NVIDIA-OptiX-SDK-8.0.0-linux64-x86_64.sh

# Download and install OptiX SDK
# WARNING: NVIDIA requires accepting their license agreement to download OptiX.
# This downloads from a build argument URL. You must provide a URL to a hosted installer.
#
# Build with custom URL:
#   docker build --build-arg OPTIX_SDK_URL=https://your-host.com/path/to/installer.sh ...
#
# Or place the installer in .devcontainer/ and it will be copied instead of downloaded.

ARG OPTIX_SDK_URL=""

# Install wget for downloading (if not already present)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y wget && \
    rm -rf /var/lib/apt/lists/*

# Copy the entire .devcontainer directory to check for OptiX installer
# This approach allows optional COPY without failing the build
COPY .devcontainer/ /tmp/devcontainer/
RUN if [ -f /tmp/devcontainer/${OPTIX_INSTALLER_NAME} ]; then \
        echo "Found OptiX installer in build context"; \
        mv /tmp/devcontainer/${OPTIX_INSTALLER_NAME} /tmp/optix-installer.sh; \
    fi && \
    rm -rf /tmp/devcontainer

# Download from URL if not copied from local
RUN if [ ! -f /tmp/optix-installer.sh ]; then \
        if [ -n "$OPTIX_SDK_URL" ]; then \
            echo "Downloading OptiX SDK from: $OPTIX_SDK_URL"; \
            wget --progress=bar:force:noscroll -O /tmp/optix-installer.sh "$OPTIX_SDK_URL" || \
            (echo "ERROR: Failed to download OptiX SDK from $OPTIX_SDK_URL" && exit 1); \
        else \
            echo "WARNING: OptiX SDK installer not found and no URL provided."; \
            echo "To install OptiX SDK, either:"; \
            echo "  1. Place ${OPTIX_INSTALLER_NAME} in .devcontainer/ directory, OR"; \
            echo "  2. Build with: docker build --build-arg OPTIX_SDK_URL=<url> ..."; \
            echo ""; \
            echo "Continuing without OptiX SDK. OptiX examples will not build."; \
            mkdir -p /opt/optix && exit 0; \
        fi; \
    fi

# Install OptiX SDK if installer exists
RUN if [ -f /tmp/optix-installer.sh ]; then \
        echo "Installing OptiX SDK to /opt/optix..."; \
        chmod +x /tmp/optix-installer.sh && \
        /tmp/optix-installer.sh --skip-license --prefix=/opt/optix --include-subdir && \
        rm /tmp/optix-installer.sh && \
        echo "OptiX SDK installed successfully"; \
    fi

# Set OptiX environment variables
ENV OPTIX_ROOT=/opt/optix
ENV OPTIX_ROOT_DIR=/opt/optix

# Verify installation
RUN if [ -d /opt/optix/include ]; then \
        echo "OptiX SDK verified at /opt/optix"; \
        ls -la /opt/optix; \
    else \
        echo "OptiX SDK not installed - directory structure not found"; \
    fi

WORKDIR /workspace
