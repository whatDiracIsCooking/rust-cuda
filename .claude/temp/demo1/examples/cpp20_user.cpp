// C++20 Consumer - Uses module import
// Modern C++ compilers with module support can import instead of include

#include <iostream>

import mathlib;  // C++20 module import - no need for #include!

int main() {
    std::cout << "=== C++20 Consumer (using import) ===" << std::endl;

    // Same API, but accessed through module import instead of header include
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

    std::cout << "\nKey point: C++20 code uses module import for:" << std::endl;
    std::cout << "  - Faster compilation (modules are pre-compiled)" << std::endl;
    std::cout << "  - Better encapsulation (only exported symbols visible)" << std::endl;
    std::cout << "  - Cleaner dependency management" << std::endl;

    return 0;
}
