#ifndef MATHLIB_VECTOR3_H
#define MATHLIB_VECTOR3_H

namespace mathlib {

/// Templated 3D vector demonstrating explicit instantiation pattern
///
/// Architecture:
/// - Declarations in header (this file)
/// - Definitions in .cpp file (hidden from users)
/// - Explicit instantiations for float, double in .cpp
/// - Extern template declarations prevent implicit instantiation
template <typename T>
class Vector3 {
public:
    T x, y, z;

    // Constructors - declared only
    Vector3();
    Vector3(T x_, T y_, T z_);

    // Arithmetic operations - declared only
    Vector3<T> operator+(const Vector3<T>& other) const;
    Vector3<T> operator-(const Vector3<T>& other) const;
    Vector3<T> operator*(T scalar) const;
    Vector3<T> operator/(T scalar) const;

    // Vector operations - declared only
    T dot(const Vector3<T>& other) const;
    Vector3<T> cross(const Vector3<T>& other) const;
    T magnitude() const;
    T magnitude_squared() const;
    Vector3<T> normalized() const;

    // Component-wise operations
    Vector3<T> component_mul(const Vector3<T>& other) const;
    T sum_components() const;
    T max_component() const;
    T min_component() const;

    // Comparison
    bool operator==(const Vector3<T>& other) const;
    bool operator!=(const Vector3<T>& other) const;
};

// ============================================================================
// Explicit Instantiation Declarations (extern template)
// ============================================================================
// These tell the compiler: "Don't instantiate these templates here.
// The instantiations exist in vector3.cpp and will be linked later."
//
// Benefits:
// - Faster compilation (templates only instantiated once in .cpp)
// - Smaller object files (no duplicate template code)
// - Implementation hidden from users
//
// Trade-off:
// - Only works for these specific types
// - Cannot use Vector3<int> or other types without modifying .cpp

extern template class Vector3<float>;
extern template class Vector3<double>;

// Type aliases for convenience
using Vector3f = Vector3<float>;
using Vector3d = Vector3<double>;

} // namespace mathlib

#endif // MATHLIB_VECTOR3_H
