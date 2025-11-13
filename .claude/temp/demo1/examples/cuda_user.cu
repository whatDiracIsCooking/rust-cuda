// CUDA Consumer - Uses traditional #include
// NVCC doesn't support C++20 modules, so we use headers

#include <iostream>
#include "mathlib/vector3.h"  // Traditional header include

// Simple CUDA kernel demonstrating Vector3 usage
__global__ void vector_add_kernel(const mathlib::Vector3* a,
                                   const mathlib::Vector3* b,
                                   mathlib::Vector3* result) {
    if (threadIdx.x == 0) {
        // Note: In real CUDA code, you'd copy this to device
        // This is just demonstrating the API compatibility
        result[0].x = a[0].x + b[0].x;
        result[0].y = a[0].y + b[0].y;
        result[0].z = a[0].z + b[0].z;
    }
}

int main() {
    std::cout << "=== CUDA Consumer (using #include) ===" << std::endl;

    // Host-side vector operations using the traditional header
    mathlib::Vector3 v1(1.0, 2.0, 3.0);
    mathlib::Vector3 v2(4.0, 5.0, 6.0);

    mathlib::Vector3 sum = v1 + v2;
    mathlib::Vector3 diff = v2 - v1;
    double dot_product = v1.dot(v2);

    std::cout << "v1 + v2 = (" << sum.x << ", " << sum.y << ", " << sum.z << ")" << std::endl;
    std::cout << "v2 - v1 = (" << diff.x << ", " << diff.y << ", " << diff.z << ")" << std::endl;
    std::cout << "v1 · v2 = " << dot_product << std::endl;

    mathlib::Vector3 normalized = v1.normalized();
    std::cout << "normalized v1 = (" << normalized.x << ", "
              << normalized.y << ", " << normalized.z << ")" << std::endl;
    std::cout << "magnitude = " << normalized.magnitude() << std::endl;

    std::cout << "\nKey point: CUDA code uses traditional headers because nvcc doesn't support C++20 modules" << std::endl;

    return 0;
}
