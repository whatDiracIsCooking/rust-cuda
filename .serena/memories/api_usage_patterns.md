# Rust CUDA API Usage Patterns

A comprehensive guide to common API patterns in the Rust CUDA project, covering host-side (cust) and device-side (cuda_std) patterns with real examples from the codebase.

## 1. Context Initialization & Setup

### Canonical Host-Side Initialization Pattern

All examples follow the same initialization sequence:

```rust
// Initialize CUDA context on the first available device
let _ctx = cust::quick_init()?;

// Load GPU code from compiled PTX
let module = Module::from_ptx(PTX, &[])?;

// Create a stream for asynchronous kernel execution
let stream = Stream::new(StreamFlags::NON_BLOCKING, None)?;
```

**Key Points:**
- `quick_init()` returns a `Context` that must stay in scope (typically held as `_ctx`)
- The context is dropped at the end of `main()`, cleaning up all GPU resources
- `Module::from_ptx()` accepts `&str` PTX code (typically included at compile time via `include_str!`)
- Non-blocking streams allow the CPU to continue without waiting for GPU completion

**File References:**
- `examples/cuda/vecadd/src/main.rs:21` - basic pattern
- `examples/cuda/gemm/src/main.rs:43-51` - cuBLAS integration pattern
- `samples/introduction/async_api/src/main.rs:26-34` - with device enumeration

## 2. Memory Management Patterns

### Host-to-Device Transfer: as_dbuf()

The ergonomic way to allocate and copy host data to GPU:

```rust
// Simple slice conversion (allocates + copies in one call)
let lhs_gpu = lhs.as_slice().as_dbuf()?;
let rhs_gpu = rhs.as_slice().as_dbuf()?;

// For output buffers, use either:
let mut out = vec![0.0f32; NUMBERS_LEN];
let out_buf = out.as_slice().as_dbuf()?;  // Pre-allocated output

// OR use uninitialized for output-only buffers (no copy overhead)
let mut mat_c_gpu = unsafe { DeviceBuffer::uninitialized(sz * sz)? };
```

**Pattern Details:**
- `as_dbuf()` requires the slice be in standard layout (contiguous memory)
- Returns `Result<DeviceBuffer<T>, CudaError>`
- Automatically deallocates on drop (RAII pattern)
- Use `uninitialized()` when you don't need initial values (faster)

### Device-to-Host Transfer: copy_to()

```rust
// Copy back from device to host after kernel completion
out_buf.copy_to(&mut out)?;
```

**Safety:**
- Should only be called after stream synchronization
- The host buffer must be valid and not accessed by other GPU operations

### Single-Value Allocations: DeviceBox

For single scalar values or small structures:

```rust
let alpha = 1.0f32;
let beta = 0.0f32;
let alpha_gpu = DeviceBox::new(&alpha)?;
let beta_gpu = DeviceBox::new(&beta)?;

// Use in kernel launch
cublas_ctx.gemm::<f32>(
    stream,
    sz, sz, sz,
    &alpha_gpu,  // DeviceBox acts like &T
    // ...
)?;

// Copy back if modified
let mut result = 0i32;
result_box.copy_to(&mut result)?;
```

**Use Cases:**
- Alpha/beta parameters for linear algebra
- Output scalars that kernels write to
- Configuration parameters

### Pinned Host Memory: LockedBuffer

For efficient asynchronous transfers:

```rust
use cust::memory::LockedBuffer;

let mut host_a = LockedBuffer::new(&0u32, N)?;
let mut device_a = DeviceBuffer::from_slice(&[u32::MAX; N])?;

// Asynchronous copy (requires proper stream synchronization)
unsafe {
    device_a.async_copy_from(&host_a, &stream)?;
    device_a.async_copy_to(&mut host_a, &stream)?;
}
```

**Benefits:**
- Page-locked memory improves transfer bandwidth
- Essential for asynchronous copy operations
- Must maintain safety invariants until operations complete

### Unified Memory: UnifiedBuffer

For simplified memory management:

```rust
let unified = UnifiedBuffer::new(&data, size)?;
// Accessible from both host and device
```

**Tradeoff:** Simplified API vs. explicit control over memory location.

## 3. Kernel Launching Patterns

### Launch Configuration with Occupancy API

The recommended pattern for optimal performance:

```rust
// Retrieve kernel from module
let vecadd = module.get_function("vecadd")?;

// Query optimal launch configuration
let (_, block_size) = vecadd.suggested_launch_configuration(0, 0.into())?;

// Calculate grid size (blocks needed)
let grid_size = (NUMBERS_LEN as u32).div_ceil(block_size);

println!("using {grid_size} blocks and {block_size} threads per block");

// Launch kernel
unsafe {
    launch!(
        vecadd<<<grid_size, block_size, 0, stream>>>(
            lhs_gpu.as_device_ptr(),
            lhs_gpu.len(),
            rhs_gpu.as_device_ptr(),
            rhs_gpu.len(),
            out_buf.as_device_ptr(),
        )
    )?;
}
```

**Pattern Details:**
- `suggested_launch_configuration(shared_mem_per_block, max_block_size)` auto-tunes block size
- Grid and block sizes are unsigned integers (total threads = grid * block)
- `launch!` macro requires `unsafe` block due to kernel parameter type checking limitations
- Third parameter (0) is shared memory per block
- Fourth parameter is the stream

### Manual Launch Configuration

For explicit control or when occupancy hints aren't sufficient:

```rust
use cust::function::{BlockSize, GridSize};

let blocks = BlockSize::xy(512, 1);
let grids = GridSize::xy((N / 512).try_into().unwrap(), 1);

unsafe {
    launch!(increment<<<grids, blocks, 0, stream>>>(
        device_a.as_device_ptr(),
        value
    ))?;
}
```

**Common Configurations:**
- 1D: `<<<grid_1d, block_1d>>>`
- 2D: `<<<grid.xy(gx, gy), block.xy(bx, by)>>>`
- 3D: `<<<grid.xyz(gx, gy, gz), block.xyz(bx, by, bz)>>>`

### Passing Slices to Kernels

Slices are passed as pointer + length pairs:

```rust
unsafe {
    launch!(
        vecadd<<<grid_size, block_size, 0, stream>>>(
            lhs_gpu.as_device_ptr(),   // *const f32
            lhs_gpu.len(),              // usize
            rhs_gpu.as_device_ptr(),   // *const f32
            rhs_gpu.len(),              // usize
            out_buf.as_device_ptr(),   // *mut f32
        )
    )?;
}
```

**Device-Side Reception:**

```rust
#[kernel]
pub unsafe fn vecadd(a: &[f32], b: &[f32], c: *mut f32) {
    // Slices received as references
    let idx = thread::index_1d() as usize;
    if idx < a.len() {
        let elem = unsafe { &mut *c.add(idx) };
        *elem = a[idx] + b[idx];
    }
}
```

## 4. Error Handling Conventions

### Result-Based Pattern

All CUDA operations return `Result<T, CudaError>`:

```rust
fn main() -> Result<(), Box<dyn Error>> {
    let _ctx = cust::quick_init()?;
    let module = Module::from_ptx(PTX, &[])?;
    let stream = Stream::new(StreamFlags::NON_BLOCKING, None)?;

    // All operations propagate errors with ?
    let gpu_buf = host_slice.as_dbuf()?;
    let kernel = module.get_function("kernel_name")?;

    unsafe {
        launch!(kernel<<<grid, block, 0, stream>>>(...))?;
    }

    stream.synchronize()?;

    Ok(())
}
```

### CudaError Enum

Comprehensive error representation:

```rust
pub enum CudaError {
    InvalidValue,
    OutOfMemory,
    NotInitialized,
    InvalidDevice,
    LaunchOutOfResources,
    LaunchTimeout,
    // ... ~40 other variants
}
```

**Common Errors:**
- `OutOfMemory` - insufficient GPU memory
- `LaunchOutOfResources` - too many blocks or shared memory
- `InvalidHandle` - module/stream already deallocated
- `NotReady` - stream operation incomplete

### Error Propagation Pattern

```rust
// Pattern 1: Propagate with ?
let kernel = module.get_function("my_kernel")?;

// Pattern 2: Handle explicitly
match stream.synchronize() {
    Ok(()) => println!("Success"),
    Err(CudaError::LaunchTimeout) => eprintln!("GPU computation timed out"),
    Err(e) => return Err(Box::new(e)),
}

// Pattern 3: Convert to other error types
let _ctx = cust::quick_init()
    .map_err(|e| format!("CUDA init failed: {}", e))?;
```

## 5. Stream & Event Synchronization Patterns

### Stream Synchronization

Block until all work in stream completes:

```rust
// Issue kernels asynchronously
unsafe {
    launch!(kernel1<<<grid, block, 0, stream>>>())?;
    launch!(kernel2<<<grid, block, 0, stream>>>())?;
}

// Wait for all previous operations to complete
stream.synchronize()?;

// Now safe to read results
gpu_buffer.copy_to(&mut host_buffer)?;
```

### Event-Based Synchronization (Non-Blocking)

For performance-sensitive code:

```rust
use cust::event::{Event, EventFlags, EventStatus};

let start_event = Event::new(EventFlags::DEFAULT)?;
let stop_event = Event::new(EventFlags::DEFAULT)?;

start_event.record(&stream)?;

// Issue work
unsafe {
    device_a.async_copy_from(&host_a, &stream)?;
    launch!(increment<<<grids, blocks, 0, stream>>>(...))?;
    device_a.async_copy_to(&mut host_a, &stream)?;
}

stop_event.record(&stream)?;

// CPU can do other work while waiting
let mut counter = 0;
while stop_event.query() != Ok(EventStatus::Ready) {
    counter += 1;  // Spin-wait or do CPU work here
}

// Calculate GPU execution time
let gpu_time = stop_event.elapsed(&start_event)?;
println!("GPU execution: {:?} microseconds", gpu_time.as_micros());
```

**File Reference:** `samples/introduction/async_api/src/main.rs:42-111`

### Multiple Stream Parallelism

Run multiple kernels concurrently:

```rust
let stream1 = Stream::new(StreamFlags::NON_BLOCKING, None)?;
let stream2 = Stream::new(StreamFlags::NON_BLOCKING, None)?;

// Issue work on different streams (may execute in parallel)
unsafe {
    launch!(kernel1<<<grid, block, 0, stream1>>>(...))?;
    launch!(kernel2<<<grid, block, 0, stream2>>>(...))?;
}

// Wait for both
stream1.synchronize()?;
stream2.synchronize()?;
```

## 6. Device-Side (GPU Kernel) Patterns

### Kernel Declaration & Safety

```rust
use cuda_std::prelude::*;

#[kernel]
#[allow(improper_ctypes_definitions)]
pub unsafe fn vecadd(a: &[f32], b: &[f32], c: *mut f32) {
    // Must be:
    // 1. Marked with #[kernel] attribute
    // 2. Declared as unsafe
    // 3. Parameters must be Copy types (primitives, references, pointers)
    // 4. Should not return a value

    let idx = thread::index_1d() as usize;
    if idx < a.len() {
        let elem = unsafe { &mut *c.add(idx) };
        *elem = a[idx] + b[idx];
    }
}
```

**Kernel Attribute Requirements:**
- `#[kernel]` is mandatory for entry points
- Kernel functions must be `unsafe` (GPU memory access is unsafe)
- All parameters must be `Copy`
- Return type must be `()`
- Parameters can be slice references or raw pointers

**File Reference:** `examples/cuda/vecadd/kernels/src/lib.rs` - canonical example

### Thread Indexing Patterns

#### 1D Indexing (Most Common)

```rust
#[kernel]
pub unsafe fn kernel_1d(data: *mut f32) {
    let idx = cuda_std::thread::index_1d() as usize;
    // or equivalently:
    // let idx = (cuda_std::thread::block_dim().x * cuda_std::thread::block_idx().x
    //     + cuda_std::thread::thread_idx().x) as usize;

    let elem = unsafe { &mut *data.add(idx) };
    *elem = (*elem) * 2.0;
}
```

#### 2D Indexing

```rust
#[kernel]
pub unsafe fn kernel_2d(matrix: *mut f32, width: u32) {
    let x = cuda_std::thread::thread_idx().x as usize;
    let y = cuda_std::thread::block_idx().x as usize;
    let idx = y * width as usize + x;

    let elem = unsafe { &mut *matrix.add(idx) };
    *elem = (*elem).sqrt();
}
```

### Bounds Checking

Always validate array access:

```rust
#[kernel]
pub unsafe fn safe_kernel(data: &[f32], output: *mut f32) {
    let idx = thread::index_1d() as usize;

    // Essential: check bounds before access
    if idx < data.len() {
        let elem = unsafe { &mut *output.add(idx) };
        *elem = data[idx] * 2.0;
    }
    // Threads beyond valid range simply return (no work)
}
```

**Pattern:** Grid and block dimensions often exceed actual data size for efficiency. Excess threads must gracefully exit.

### Thread Synchronization

```rust
#[kernel]
pub unsafe fn shared_memory_kernel(data: &[f32], output: *mut f32) {
    let idx = thread::index_1d() as usize;

    // Allocate shared memory (example: 256 elements)
    let shared = cuda_std::shared::SharedMemory::<f32>::new(256);

    // Load data into shared memory
    if idx < data.len() {
        shared[idx] = data[idx];
    }

    // Synchronize all threads in block
    cuda_std::thread::sync_threads();

    // Now all threads can safely read shared memory
    if idx < data.len() {
        let elem = unsafe { &mut *output.add(idx) };
        *elem = shared[idx] * 2.0;
    }
}
```

### Warp Operations

For optimized within-warp reductions:

```rust
use cuda_std::warp::*;

#[kernel]
pub unsafe fn warp_reduction(data: &[f32], output: *mut f32) {
    let idx = thread::index_1d() as usize;
    let tid = thread::thread_idx().x as u32;

    if idx < data.len() {
        let mut val = data[idx];

        // Warp-level reduction
        for offset in 16u32..=1 {
            val = shfl_down_sync(0xffffffff, val, offset);
        }

        // Write result from lane 0 of each warp
        if tid % 32 == 0 {
            let elem = unsafe { &mut *output.add(idx) };
            *elem = val;
        }
    }
}
```

## 7. Safety Invariants & Preconditions

### Host-Side Async Copy Safety

When using `async_copy_from` or `async_copy_to`:

```rust
unsafe {
    // Safety: Documented preconditions for async_copy_from
    // 1. host_buffer is not modified until event.query() == Ready
    // 2. Both buffers not deallocated until operation completes
    // 3. No other GPU operations on device_buffer until event fires
    device_a.async_copy_from(&host_a, &stream)?;
}

// Wait for completion before any access
stop_event.record(&stream)?;
while stop_event.query() != Ok(EventStatus::Ready) { }

// Now safe to use host_a again
```

**File Reference:** `samples/introduction/async_api/src/main.rs:56-92`

### Device-Side Pointer Safety

```rust
#[kernel]
pub unsafe fn pointer_safety_kernel(input: &[f32], output: *mut f32) {
    let idx = thread::index_1d() as usize;

    // Kernel safety preconditions:
    // 1. Output pointer is valid and allocated for at least input.len() elements
    // 2. Excess threads (beyond data size) must not access memory
    // 3. No thread synchronization issues with bounds

    if idx < input.len() {
        unsafe { *output.add(idx) = input[idx]; }
    }
}
```

### Kernel Parameter Copy Requirement

```rust
#[kernel]
pub unsafe fn kernel(
    // Correct: Copy types
    data: *const f32,
    len: usize,
    value: f32,

    // WRONG: NonCopy types cause compile errors
    // data: String,  // String is not Copy - COMPILE ERROR
    // data: Vec<f32>, // Vec is not Copy - COMPILE ERROR
) {
    // All parameters must be Copy because they're passed by value to GPU memory
}
```

## 8. Common Patterns & Anti-Patterns

### Good Pattern: Validate Before Launch

```rust
// Check inputs before expensive GPU launch
let kernel = module.get_function("kernel_name")
    .expect("kernel not found - PTX compilation may have failed");

if data.is_empty() {
    return Err("Cannot launch with empty data".into());
}

unsafe {
    launch!(kernel<<<grid, block, 0, stream>>>(...))
        .map_err(|e| format!("Launch failed: {}", e))?;
}
```

### Anti-Pattern: Forgetting Stream Synchronization

```rust
// WRONG - race condition
unsafe {
    launch!(kernel<<<grid, block, 0, stream>>>(...))?;
}
// DON'T read results immediately - kernel may still be running!
gpu_buffer.copy_to(&mut host_buffer)?;  // May read stale data

// CORRECT
unsafe {
    launch!(kernel<<<grid, block, 0, stream>>>(...))?;
}
stream.synchronize()?;  // Wait for kernel
gpu_buffer.copy_to(&mut host_buffer)?;  // Safe to read
```

### Anti-Pattern: Ignoring Memory Limits

```rust
// WRONG - may allocate more memory than GPU has
let huge_buffer = DeviceBuffer::zeros::<f32>(1_000_000_000)?;

// CORRECT - check capacity
match DeviceBuffer::zeros::<f32>(1_000_000_000) {
    Ok(buf) => { /* use buffer */ }
    Err(CudaError::OutOfMemory) => {
        eprintln!("Insufficient GPU memory");
        // Reduce problem size or cleanup
    }
    Err(e) => return Err(e.into()),
}
```

### Anti-Pattern: Not Using Occupancy API

```rust
// Suboptimal
unsafe {
    launch!(kernel<<<256, 128, 0, stream>>>(...))?;  // Arbitrary numbers
}

// Optimal
let (_, block_size) = kernel.suggested_launch_configuration(0, 0.into())?;
let grid_size = (count as u32).div_ceil(block_size);
unsafe {
    launch!(kernel<<<grid_size, block_size, 0, stream>>>(...))?;
}
```

## 9. Common API Elements Reference

### cust Prelude Exports

```rust
use cust::prelude::*;

// Includes:
pub use crate::context::Context;
pub use crate::device::Device;
pub use crate::event::{Event, EventFlags, EventStatus};
pub use crate::function::Function;
pub use crate::launch;
pub use crate::memory::{
    CopyDestination, DeviceBuffer, DevicePointer,
    DeviceSlice, DeviceVariable, UnifiedBuffer
};
pub use crate::module::Module;
pub use crate::stream::{Stream, StreamFlags};
pub use crate::util::*;
```

### cuda_std Prelude Exports

```rust
use cuda_std::prelude::*;

// Includes:
pub use crate::thread;        // Thread indexing & sync
pub use crate::kernel;        // #[kernel] attribute
pub use cuda_std_macros::*;   // Device-side macros
pub use alloc::*;             // Allocator traits
```

## Key Files for Reference

**Host-Side Patterns:**
- `examples/cuda/vecadd/src/main.rs` - Basic workflow
- `examples/cuda/gemm/src/main.rs` - Advanced memory & events
- `samples/introduction/async_api/src/main.rs` - Async patterns

**Device-Side Patterns:**
- `examples/cuda/vecadd/kernels/src/lib.rs` - Simple kernel
- `examples/cuda/gemm/kernels/src/gemm_naive.rs` - 2D kernels
- `samples/introduction/async_api/kernels/src/lib.rs` - Shared memory

**API Documentation:**
- `crates/cust/src/error.rs` - Error types
- `crates/cust/src/prelude.rs` - Main API exports
- `crates/cuda_std/src/lib.rs` - Device-side library
