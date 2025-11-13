// C++20 Module Interface for mathlib
// This wraps the traditional header-based implementation
// allowing C++20 users to use 'import mathlib' instead of '#include'

module;

// Global module fragment - include traditional headers here
// This brings in the template declarations, extern template declarations,
// and type aliases from vector3.h
#include "mathlib/vector3.h"

export module mathlib;

// Re-export the template class and type aliases from the header
// The extern template declarations ensure we use the instantiations
// from vector3.cpp, not generate new ones here
export namespace mathlib {
    using mathlib::Vector3;
    using mathlib::Vector3f;
    using mathlib::Vector3d;
}
