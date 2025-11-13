# Scripts Directory - Automation & Code Generation

## Overview
The `scripts/` directory contains automation infrastructure for code generation and CI/CD support. It implements a pipeline for generating Rust bindings from CUDA intrinsics documentation and supports external dependency downloads for the build system.

## Available Scripts

### 1. gen_libdevice_json.py
- **Purpose**: Generates JSON representation of CUDA libdevice intrinsics from PDF documentation
- **Input**: PDF documentation files containing intrinsics specifications
- **Output**: `data/libdevice.json` - structured JSON catalog of intrinsics
- **Capabilities**: Parses 300+ CUDA intrinsics with full specifications
- **Features**: Error handling and validation of extracted data

### 2. gen_intrinsics.py
- **Purpose**: Generates Rust language bindings from intrinsics data
- **Input**: JSON data from `gen_libdevice_json.py`
- **Output**: `data/std_intrinsics.rs` - complete Rust module with function bindings
- **Scope**: Covers 300+ CUDA intrinsics
- **Quality**: Includes proper documentation, type safety, and ergonomic Rust patterns

### 3. download_ci_optix.bash
- **Purpose**: CI/CD utility for downloading and setting up OptiX SDK
- **Integration**: Used in GitHub Actions workflows for building with optional OptiX support
- **Reliability**: Implements retry logic and proper error handling
- **Configuration**: Environment-based setup for different CI platforms

## Code Generation Workflow

```
PDF Documentation
    ↓
gen_libdevice_json.py
    ↓
data/libdevice.json
    ↓
gen_intrinsics.py
    ↓
data/std_intrinsics.rs (Rust bindings)
```

The two-stage pipeline enables:
- Separation of parsing and code generation concerns
- Reusability of JSON data for multiple targets
- Independent testing of each stage
- Clear data artifacts for version control and auditing

## CI/CD Integration

- **OptiX Downloads**: `download_ci_optix.bash` handles external SDK setup
- **Retry Logic**: Robust error recovery for network operations
- **GitHub Actions**: Seamless integration with build workflows
- **Platform Support**: Handles CI environment variations

## Data Directory

### Generated Artifacts
- **libdevice.json**: Machine-readable intrinsics catalog
  - Comprehensive metadata for 300+ CUDA functions
  - Used as source of truth for binding generation
  - Suitable for tooling and documentation generation

- **std_intrinsics.rs**: Production Rust module
  - Auto-generated Rust bindings with full type safety
  - Ready for inclusion in compilation
  - Includes documentation for IDE support

### File Management
- Generated files are committed to version control
- Updated when CUDA toolchain or documentation changes
- Build system can regenerate if needed
- Clear separation between manual and generated code

## Usage Notes

- Run scripts from project root or with proper path configuration
- Ensure Python 3.x environment with required dependencies
- Bash scripts assume standard Unix environment
- Generated files should be committed when dependencies update
