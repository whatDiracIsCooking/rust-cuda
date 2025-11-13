# Samples Directory

## Purpose and Distinction

The `samples/` directory contains **official NVIDIA CUDA sample ports to Rust**, providing an educational foundation for learning CUDA fundamentals. Unlike `examples/`, which demonstrate library features and usage patterns, samples are:

- **Direct ports** of NVIDIA's canonical cuda-samples repository
- **Simpler and more focused** than examples with clear learning objectives
- **Educational progression** structured by CUDA chapters
- **Foundation for understanding** core CUDA concepts before exploring advanced library features

## Current Sample: async_api

**Location:** `samples/async_api`
**Category:** Chapter 0 - Introduction

The `async_api` sample demonstrates fundamental asynchronous GPU operations:

- **GPU Event Timing**: Uses CUDA events to measure kernel execution time on the device
- **Concurrent CPU-GPU Operations**: Shows how to overlap CPU work with GPU computation
- **Stream Management**: Demonstrates the use of streams for async operations
- **Locked Buffers**: Uses pinned memory for efficient host-device transfers

This sample serves as the entry point for understanding how to efficiently coordinate CPU and GPU work.

## Key Patterns Demonstrated

### Memory Management
- Pinned memory allocation for faster host-device transfers
- Proper buffer cleanup and resource management

### Asynchronous Operations
- Stream-based GPU operations
- Event creation and synchronization
- Non-blocking CPU-GPU coordination

### Performance Measurement
- GPU-side event timing for accurate kernel execution metrics
- Avoiding host-side timing bottlenecks

## Educational Progression

Currently tracking Chapter 0 (Introduction) from NVIDIA's cuda-samples. The structure supports gradual progression through:

- **Chapter 0**: Basic async operations and timing (current: async_api)
- **Future Chapters**: Progressive complexity in memory management, kernels, optimization, etc.

Each new sample will build on foundational concepts, maintaining the educational trajectory while staying true to NVIDIA's original design and intent.

## Integration with rust-cuda

These samples demonstrate:
- Modern CUDA 12+ memory resource APIs
- Safe Rust bindings to CUDA primitives
- Stream and event handling patterns
- Best practices for GPU programming in Rust

The samples complement the main library by showing idiomatic usage patterns for users new to both CUDA and Rust.
