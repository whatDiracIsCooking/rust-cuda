// C++20 Module Interface for mathlib
// This wraps the traditional header-based implementation
// allowing C++20 users to use 'import mathlib' instead of '#include'

module;

// Global module fragment - include traditional headers here
#include "mathlib/vector3.h"

export module mathlib;

// Re-export the namespace and types from the header
export namespace mathlib {
    using mathlib::Vector3;
}
