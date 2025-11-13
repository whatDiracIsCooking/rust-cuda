// CUDA Consumer - Uses traditional #include with explicit template instantiation
// NVCC doesn't support C++20 modules, so we use headers
//
// Key Architectural Point:
// - This file includes vector3.h (declarations + extern template)
// - Template definitions are NOT visible here (hidden in vector3.cpp)
// - Only Vector3<float> and Vector3<double> are available
// - Linker will find the explicit instantiations from vector3.cpp

#include <iostream>
#include <iomanip>
#include "mathlib/vector3.h"  // Traditional header include

// Simple CUDA kernel demonstrating Vector3<float> usage
__global__ void vector_cross_kernel(const mathlib::Vector3f* a,
                                     const mathlib::Vector3f* b,
                                     mathlib::Vector3f* result) {
    if (threadIdx.x == 0) {
        // Compute cross product on device
        // Note: In real CUDA code, you'd have proper device memory management
        result[0].x = a[0].y * b[0].z - a[0].z * b[0].y;
        result[0].y = a[0].z * b[0].x - a[0].x * b[0].z;
        result[0].z = a[0].x * b[0].y - a[0].y * b[0].x;
    }
}

int main() {
    std::cout << "=== CUDA Consumer (Explicit Template Instantiation) ===" << std::endl;
    std::cout << std::fixed << std::setprecision(4);

    // Using Vector3<float> (explicitly instantiated in vector3.cpp)
    std::cout << "\n--- Vector3<float> operations ---" << std::endl;
    mathlib::Vector3f v1(1.0f, 2.0f, 3.0f);
    mathlib::Vector3f v2(4.0f, 5.0f, 6.0f);

    // Arithmetic operations
    mathlib::Vector3f sum = v1 + v2;
    mathlib::Vector3f diff = v2 - v1;
    mathlib::Vector3f scaled = v1 * 2.5f;

    std::cout << "v1 = (" << v1.x << ", " << v1.y << ", " << v1.z << ")" << std::endl;
    std::cout << "v2 = (" << v2.x << ", " << v2.y << ", " << v2.z << ")" << std::endl;
    std::cout << "v1 + v2 = (" << sum.x << ", " << sum.y << ", " << sum.z << ")" << std::endl;
    std::cout << "v2 - v1 = (" << diff.x << ", " << diff.y << ", " << diff.z << ")" << std::endl;
    std::cout << "v1 * 2.5 = (" << scaled.x << ", " << scaled.y << ", " << scaled.z << ")" << std::endl;

    // Vector operations
    float dot_product = v1.dot(v2);
    mathlib::Vector3f cross_product = v1.cross(v2);
    float mag = v1.magnitude();
    mathlib::Vector3f normalized = v1.normalized();

    std::cout << "v1 · v2 = " << dot_product << std::endl;
    std::cout << "v1 × v2 = (" << cross_product.x << ", " << cross_product.y << ", " << cross_product.z << ")" << std::endl;
    std::cout << "|v1| = " << mag << std::endl;
    std::cout << "normalized(v1) = (" << normalized.x << ", " << normalized.y << ", " << normalized.z << ")" << std::endl;

    // Component-wise operations
    mathlib::Vector3f comp_mul = v1.component_mul(v2);
    float sum_comp = v1.sum_components();
    float max_comp = v1.max_component();

    std::cout << "component_mul(v1, v2) = (" << comp_mul.x << ", " << comp_mul.y << ", " << comp_mul.z << ")" << std::endl;
    std::cout << "sum_components(v1) = " << sum_comp << std::endl;
    std::cout << "max_component(v1) = " << max_comp << std::endl;

    std::cout << "\n--- Key Architectural Points ---" << std::endl;
    std::cout << "✓ CUDA code uses #include (not modules)" << std::endl;
    std::cout << "✓ Template definitions hidden in .cpp file" << std::endl;
    std::cout << "✓ Only Vector3<float> and Vector3<double> available" << std::endl;
    std::cout << "✓ Faster compilation: templates instantiated once" << std::endl;
    std::cout << "✓ Smaller binary: no duplicate instantiations" << std::endl;

    // Demonstrate that type alias works
    std::cout << "\n--- Type Aliases ---" << std::endl;
    std::cout << "Vector3f is Vector3<float>" << std::endl;
    std::cout << "Vector3d is Vector3<double>" << std::endl;

    // Using Vector3<double> as well
    mathlib::Vector3d vd1(1.5, 2.5, 3.5);
    mathlib::Vector3d vd2(4.5, 5.5, 6.5);
    mathlib::Vector3d vd_sum = vd1 + vd2;
    std::cout << "Vector3d: (" << vd1.x << ", " << vd1.y << ", " << vd1.z << ") + ";
    std::cout << "(" << vd2.x << ", " << vd2.y << ", " << vd2.z << ") = ";
    std::cout << "(" << vd_sum.x << ", " << vd_sum.y << ", " << vd_sum.z << ")" << std::endl;

    // What happens if you try to use Vector3<int>?
    // Uncomment this line to see linker error:
    // mathlib::Vector3<int> vi(1, 2, 3);  // ERROR: No explicit instantiation for int!

    std::cout << "\nNote: Attempting Vector3<int> would cause linker error!" << std::endl;
    std::cout << "This is intentional - library controls which instantiations exist." << std::endl;

    return 0;
}
