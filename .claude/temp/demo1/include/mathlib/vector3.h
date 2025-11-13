#ifndef MATHLIB_VECTOR3_H
#define MATHLIB_VECTOR3_H

namespace mathlib {

/// A simple 3D vector for demonstration
class Vector3 {
public:
    double x, y, z;

    // Constructors
    Vector3() : x(0), y(0), z(0) {}
    Vector3(double x_, double y_, double z_) : x(x_), y(y_), z(z_) {}

    // Operations
    Vector3 operator+(const Vector3& other) const;
    Vector3 operator-(const Vector3& other) const;
    Vector3 operator*(double scalar) const;

    double dot(const Vector3& other) const;
    double magnitude() const;
    Vector3 normalized() const;
};

} // namespace mathlib

#endif // MATHLIB_VECTOR3_H
