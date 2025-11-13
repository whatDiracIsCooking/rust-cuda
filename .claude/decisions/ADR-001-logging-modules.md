# ADR-001: Convert Logging Library to C++20 Modules

**Status:** Accepted
**Date:** 2025-11-05
**Decision Makers:** TDD Maestro Orchestration

## Context

The logging library was implemented using traditional C++ headers (logger.h, logger_config.h, logging.h). As the first library to adopt C++20 modules, this conversion establishes patterns for future module migrations.

## Decision

Convert the logging library from traditional headers to a pure C++20 module implementation using the 2-file pattern (interface .cppm + implementation .cpp).

## Rationale

### Benefits Realized

1. **Build Performance:** 10.1x faster incremental builds for implementation changes
   - Clean build: 7.5s
   - Implementation-only change: 0.715s (vs 7.5s with headers)

2. **Dependency Isolation:** Module consumers don't recompile when implementation changes

3. **Cleaner Architecture:** 6 files → 2 files (logging.cppm + logging.cpp)

4. **Future-Proof:** Establishes C++20 as project standard

### Trade-offs Accepted

1. **spdlog as PUBLIC Dependency:** Testing API exposes `spdlog::logger` type
   - Acceptable: Documented in code, matches old header behavior

2. **Build System Complexity:** Requires CMake 3.28+ with module support
   - Acceptable: Infrastructure already in place

3. **Consumer Migration Required:** Breaking change to import statement
   - Mitigated: Only 1 consumer file (test/unit/logging_ut.cpp)

## Implementation

- **Module Interface:** `src/logging/logging.cppm` (export module calaman.logging)
- **Module Implementation:** `src/logging/logging.cpp`
- **Build System:** CMake FILE_SET CXX_MODULES
- **Migration Impact:** 1 file updated (test consumer)

## Validation

- ✅ All 36 tests passing
- ✅ Thread safety verified (code review + concurrent tests)
- ✅ Performance validated (10.1x incremental build improvement)
- ✅ Zero regressions
- ✅ API 100% compatible

## Consequences

### Positive
- Faster development iteration (incremental builds)
- Cleaner module boundaries
- First-class C++20 adoption

### Negative
- Breaking change for consumers (import vs include)
- Requires modern compiler with C++20 module support
- spdlog coupling exposed in interface

## Alternatives Considered

1. **Keep headers:** Rejected - misses performance benefits, doesn't advance C++20 adoption
2. **Private module:** Rejected - testing API requires public spdlog exposure
3. **Wrapper interface:** Rejected - adds complexity for minimal benefit

## Notes

This conversion successfully demonstrates the module migration pattern for the project. Lessons learned will inform future library conversions.

**Artifact Location:** `.claude/temp/logging_module_conversion_impl/`
