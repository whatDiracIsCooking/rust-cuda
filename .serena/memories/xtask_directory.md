# xtask Directory - Development Task Automation

## Overview

The `xtask/` directory implements a Rust-based task automation tool following the standard Rust pattern for workspace utilities. It provides a command-line interface accessible via `cargo xtask`, enabling developers to perform build and debugging tasks.

**Location:** `/xtask/`

## Structure

- **Cargo.toml** - Package definition with minimal dependencies
- **src/main.rs** - Command dispatcher using pico-args for argument parsing
- **src/extract_llfns.rs** - Primary task implementation

## Dependencies

- **pico-args** (0.4.2) - Lightweight argument parsing
- **rayon** (1.10) - Data parallelism for batch operations
- **regex** (1.11.1) - Pattern matching for LLVM IR parsing

## Available Commands

### extract_llfns
Extracts individual LLVM IR functions from a compiled LLVM IR file.

**Usage:**
```
cargo xtask extract_llfns <input_file.ll> <output_directory>
```

**Behavior:**
- Reads LLVM IR file and parses function definitions using regex pattern: `define .*(_Z.*?)(\(|")`
- Uses llvm-extract to isolate each function with recursive dependency inclusion (`--recursive`)
- Processes all functions in parallel using rayon
- Outputs each function as a separate `.ll` file in the specified directory
- Sorts functions by size (shortest first) for processing optimization

**Use Cases:**
- Debugging GPU compilation pipeline issues
- Analyzing individual kernel functions
- Testing NVVM compiler on specific functions
- Identifying which functions cause segfaults or compilation errors

## Integration with Build System

The xtask tool is registered as a workspace member in the root `Cargo.toml` and integrates with the Rust cargo ecosystem via the standard `xtask` pattern. It's a development-time tool that doesn't affect the main library build process.

## Development Workflow

### For Debugging Compilation Issues

When the GPU compilation pipeline fails:
1. Use `cargo xtask extract_llfns <compiled_file.ll> <output_dir>` to decompose the IR
2. Modify `run_command_for_each_fn()` in extract_llfns.rs to run custom debugging commands
3. The tool will apply your debug command to each function and report failures
4. Use the failure list to identify problematic functions

### Adding Custom Debug Logic

The `run_command_for_each_fn()` function in extract_llfns.rs provides a hook for custom debugging:
- Return `true` to continue processing
- Return `false` to stop after current function
- **Important:** Remove any modifications before committing (as noted in the code comment)

## Key Design Features

- **Minimal Dependencies** - Only essential tools for focused debugging
- **Parallel Processing** - rayon enables efficient batch function extraction
- **Incremental Output** - Each function extracted to its own file for independent analysis
- **Error Reporting** - Collects and displays first 30 failing functions
