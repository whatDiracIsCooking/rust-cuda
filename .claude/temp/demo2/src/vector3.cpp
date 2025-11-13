#include "mathlib/vector3.h"
#include <cmath>
#include <algorithm>

namespace mathlib {

// ============================================================================
// Template Method Definitions
// ============================================================================
// These definitions are HIDDEN from header users.
// They're only compiled once per explicit instantiation below.

// Constructors
template <typename T>
Vector3<T>::Vector3() : x(0), y(0), z(0) {}

template <typename T>
Vector3<T>::Vector3(T x_, T y_, T z_) : x(x_), y(y_), z(z_) {}

// Arithmetic operations
template <typename T>
Vector3<T> Vector3<T>::operator+(const Vector3<T>& other) const {
    return Vector3<T>(x + other.x, y + other.y, z + other.z);
}

template <typename T>
Vector3<T> Vector3<T>::operator-(const Vector3<T>& other) const {
    return Vector3<T>(x - other.x, y - other.y, z - other.z);
}

template <typename T>
Vector3<T> Vector3<T>::operator*(T scalar) const {
    return Vector3<T>(x * scalar, y * scalar, z * scalar);
}

template <typename T>
Vector3<T> Vector3<T>::operator/(T scalar) const {
    return Vector3<T>(x / scalar, y / scalar, z / scalar);
}

// Vector operations
template <typename T>
T Vector3<T>::dot(const Vector3<T>& other) const {
    return x * other.x + y * other.y + z * other.z;
}

template <typename T>
Vector3<T> Vector3<T>::cross(const Vector3<T>& other) const {
    return Vector3<T>(
        y * other.z - z * other.y,
        z * other.x - x * other.z,
        x * other.y - y * other.x
    );
}

template <typename T>
T Vector3<T>::magnitude() const {
    return std::sqrt(magnitude_squared());
}

template <typename T>
T Vector3<T>::magnitude_squared() const {
    return x * x + y * y + z * z;
}

template <typename T>
Vector3<T> Vector3<T>::normalized() const {
    T mag = magnitude();
    if (mag > T(0)) {
        return (*this) / mag;
    }
    return *this;
}

// Component-wise operations
template <typename T>
Vector3<T> Vector3<T>::component_mul(const Vector3<T>& other) const {
    return Vector3<T>(x * other.x, y * other.y, z * other.z);
}

template <typename T>
T Vector3<T>::sum_components() const {
    return x + y + z;
}

template <typename T>
T Vector3<T>::max_component() const {
    return std::max({x, y, z});
}

template <typename T>
T Vector3<T>::min_component() const {
    return std::min({x, y, z});
}

// Comparison
template <typename T>
bool Vector3<T>::operator==(const Vector3<T>& other) const {
    return x == other.x && y == other.y && z == other.z;
}

template <typename T>
bool Vector3<T>::operator!=(const Vector3<T>& other) const {
    return !(*this == other);
}

// ============================================================================
// Explicit Template Instantiations
// ============================================================================
// These are the ONLY instantiations that will exist in the compiled library.
// The compiler generates code for these specific types here.
//
// Key Architectural Point:
// - Users can ONLY use Vector3<float> and Vector3<double>
// - Attempting Vector3<int> will cause linker errors
// - This is intentional: we control which instantiations exist
//
// Benefits:
// 1. Compilation Speed: Template code compiled once, not in every translation unit
// 2. Binary Size: No duplicate template instantiations across object files
// 3. Implementation Hiding: Users see declarations only, not implementation
// 4. ABI Stability: Changing implementation doesn't force user recompilation
//
// Trade-offs:
// 1. Flexibility Loss: Cannot use arbitrary types without modifying library
// 2. Maintenance: Must explicitly add new instantiations as needed

template class Vector3<float>;
template class Vector3<double>;

// Note: These explicit instantiations generate ALL member functions
// for Vector3<float> and Vector3<double>. The linker will find them
// when user code calls these methods.

} // namespace mathlib
