// C++20 Consumer - Uses module import with explicit template instantiation
// Modern C++ compilers with module support can import instead of include
//
// Key Architectural Point:
// - This file uses 'import mathlib' (C++20 module)
// - Module wraps vector3.h with extern template declarations
// - Template definitions still hidden in vector3.cpp
// - Benefits of BOTH modules AND explicit instantiation

#include <iostream>
#include <iomanip>

import mathlib;  // C++20 module import - clean and fast!

int main() {
    std::cout << "=== C++20 Consumer (Module Import + Explicit Instantiation) ===" << std::endl;
    std::cout << std::fixed << std::setprecision(4);

    // Using Vector3<double> via module import
    std::cout << "\n--- Vector3<double> operations via import mathlib ---" << std::endl;
    mathlib::Vector3d v1(1.5, 2.5, 3.5);
    mathlib::Vector3d v2(4.5, 5.5, 6.5);

    // Arithmetic operations
    mathlib::Vector3d sum = v1 + v2;
    mathlib::Vector3d diff = v2 - v1;
    mathlib::Vector3d scaled = v1 * 2.0;
    mathlib::Vector3d divided = v2 / 2.0;

    std::cout << "v1 = (" << v1.x << ", " << v1.y << ", " << v1.z << ")" << std::endl;
    std::cout << "v2 = (" << v2.x << ", " << v2.y << ", " << v2.z << ")" << std::endl;
    std::cout << "v1 + v2 = (" << sum.x << ", " << sum.y << ", " << sum.z << ")" << std::endl;
    std::cout << "v2 - v1 = (" << diff.x << ", " << diff.y << ", " << diff.z << ")" << std::endl;
    std::cout << "v1 * 2.0 = (" << scaled.x << ", " << scaled.y << ", " << scaled.z << ")" << std::endl;
    std::cout << "v2 / 2.0 = (" << divided.x << ", " << divided.y << ", " << divided.z << ")" << std::endl;

    // Vector operations
    double dot_product = v1.dot(v2);
    mathlib::Vector3d cross_product = v1.cross(v2);
    double mag = v1.magnitude();
    double mag_sq = v1.magnitude_squared();
    mathlib::Vector3d normalized = v1.normalized();

    std::cout << "v1 · v2 = " << dot_product << std::endl;
    std::cout << "v1 × v2 = (" << cross_product.x << ", " << cross_product.y << ", " << cross_product.z << ")" << std::endl;
    std::cout << "|v1| = " << mag << std::endl;
    std::cout << "|v1|² = " << mag_sq << std::endl;
    std::cout << "normalized(v1) = (" << normalized.x << ", " << normalized.y << ", " << normalized.z << ")" << std::endl;

    // Component-wise operations
    mathlib::Vector3d comp_mul = v1.component_mul(v2);
    double sum_comp = v1.sum_components();
    double max_comp = v2.max_component();
    double min_comp = v1.min_component();

    std::cout << "component_mul(v1, v2) = (" << comp_mul.x << ", " << comp_mul.y << ", " << comp_mul.z << ")" << std::endl;
    std::cout << "sum_components(v1) = " << sum_comp << std::endl;
    std::cout << "max_component(v2) = " << max_comp << std::endl;
    std::cout << "min_component(v1) = " << min_comp << std::endl;

    // Comparison operations
    mathlib::Vector3d v3(1.5, 2.5, 3.5);  // Equal to v1
    bool equal = (v1 == v3);
    bool not_equal = (v1 != v2);

    std::cout << "v1 == v3: " << (equal ? "true" : "false") << std::endl;
    std::cout << "v1 != v2: " << (not_equal ? "true" : "false") << std::endl;

    std::cout << "\n--- Vector3<float> also available ---" << std::endl;
    mathlib::Vector3f vf1(1.0f, 0.0f, 0.0f);
    mathlib::Vector3f vf2(0.0f, 1.0f, 0.0f);
    mathlib::Vector3f vf_cross = vf1.cross(vf2);
    std::cout << "Vector3f: (1,0,0) × (0,1,0) = ("
              << vf_cross.x << ", " << vf_cross.y << ", " << vf_cross.z << ")" << std::endl;

    std::cout << "\n--- Architecture Benefits Combined ---" << std::endl;
    std::cout << "✓ C++20 modules: Faster compilation, better encapsulation" << std::endl;
    std::cout << "✓ Explicit instantiation: No duplicate template code" << std::endl;
    std::cout << "✓ extern template: Prevents implicit instantiation" << std::endl;
    std::cout << "✓ Type safety: Only Vector3<float> and Vector3<double>" << std::endl;
    std::cout << "✓ Implementation hiding: Template code not in headers" << std::endl;
    std::cout << "✓ ABI stability: Can change .cpp without recompiling users" << std::endl;

    std::cout << "\n--- Trade-offs ---" << std::endl;
    std::cout << "✗ Limited flexibility: Only pre-instantiated types work" << std::endl;
    std::cout << "✗ Requires CMake 3.28+ for module support" << std::endl;
    std::cout << "✗ Must explicitly add new instantiations to .cpp" << std::endl;

    // Attempting Vector3<int> would fail at link time
    // Uncomment to see the error:
    // mathlib::Vector3<int> vi(1, 2, 3);  // LINKER ERROR!

    std::cout << "\nNote: This combines TWO powerful patterns:" << std::endl;
    std::cout << "  1. Explicit template instantiation (Stroustrup's wisdom)" << std::endl;
    std::cout << "  2. C++20 modules (Brooks' pragmatic evolution)" << std::endl;

    return 0;
}
