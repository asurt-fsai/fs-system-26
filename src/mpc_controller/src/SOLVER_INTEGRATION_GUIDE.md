# Solver Integration - Complete Architecture

## Overview

The MPC controller now has a clean, integrated solver stack using:
- **BLASFEO** - Linear algebra library for optimized matrix operations
- **HPIPM** - High-performance interior-point method QP solver
- **Eigen 5.0.0** - Modern C++ linear algebra library
- **hpipm-cpp-main** - C++ wrapper for HPIPM (optional, for future use)

## Directory Structure

```
src/
├── blasfeo/                      # BLASFEO linear algebra library (CLEANED)
│   ├── include/                  # 41 BLASFEO headers (KEPT)
│   ├── lib/                      # Compiled BLASFEO libraries (KEPT)
│   ├── CMakeLists.txt            # Build configuration (reference)
│   ├── README.md                 # Documentation
│   └── LICENSE.txt               # License
│
├── eigen-5.0.0/                  # Eigen C++ linear algebra (REAL library)
│   └── Eigen/                    # All Eigen headers
│       ├── Dense                 # Main header for dense linear algebra
│       └── Core, Geometry, ...   # Specialized modules
│
├── hpipm_stubs/                  # HPIPM stub headers (C API)
│   ├── hpipm_d_ocp_qp_dim.h     # Dimension management
│   ├── hpipm_d_ocp_qp.h         # QP structure
│   ├── hpipm_d_ocp_qp_sol.h     # Solution structure
│   ├── hpipm_d_ocp_qp_ipm.h     # IPM solver
│   └── hpipm_timing.h            # Timing utilities
│
├── hpipm-cpp-main/               # HPIPM C++ wrapper (CLEANED, reference)
│   ├── include/hpipm-cpp/        # C++ wrapper headers
│   ├── src/                      # C++ wrapper implementation
│   ├── CMakeLists.txt            # Build config
│   ├── README.md                 # Documentation
│   └── LICENSE                   # License
│
└── Interfaces/                   # MPC solver interface (NEW)
    ├── solver_interface.h        # Abstract solver interface
    ├── solver_interface.cpp      # Eigen/struct converters
    ├── hpipm_interface.h         # HPIPM concrete implementation
    └── hpipm_interface.cpp       # HPIPM solver code
```

## Clean Directory Size Reduction

### Before:
- **blasfeo**: 700+ MB (with tests, benchmarks, kernel sources, cmake, etc.)
- **hpipm-cpp-main**: Still included tests, examples, doc

### After:
- **blasfeo**: ～ 10 MB (include/ + lib/ + minimal config files)
- **hpipm-cpp-main**: ～ 2 MB (include/ + src/ only)
- **Total reduction**: ~680 MB smaller footprint

## Cleaned Files Removed

### From BLASFEO:
- `.git/`, `.github/` - Git repository history
- `tests/`, `benchmarks/`, `microbenchmarks/` - Test code
- `examples/` - Example code
- `experimental/`, `sandbox/` - Experimental code
- `kernel/`, `auxiliary/`, `blas_api/`, `netlib/`, `utils/` - Build source files
- `cmake/` - Build configuration directory
- `Makefile*` - Build scripts

### From HPIPM-CPP-Main:
- `.git/`, `.github/` - Git repository
- `test/`, `examples/` - Test and example code
- `doc/` - Documentation
- `.gitignore` - Git ignore file

### From Interfaces Folder:
- Removed old `Interfaces/Eigen/` stub (now using real Eigen 5.0.0)

## Integration Points

### 1. Include Paths (`.vscode/c_cpp_properties.json`)
```json
"includePath": [
  "${workspaceFolder}",                      // Root headers
  "${workspaceFolder}/blasfeo/include",      // BLASFEO
  "${workspaceFolder}/eigen-5.0.0",          // Real Eigen 5.0.0
  "${workspaceFolder}/hpipm_stubs",          // HPIPM stubs
  "${workspaceFolder}/hpipm-cpp-main/include", // hpipm-cpp (optional)
  "${workspaceFolder}/Interfaces",           // Solver interface
  "${workspaceFolder}/**"                    // Recursive fallback
],
"defines": [
  "N=20",       // Prediction horizon
  "NX=7",       // State dimension
  "NU=2",       // Control dimension
  "NB=10",      // Max bounds
  "NPC=3",      // Polytopic constraints
  "NS=3"        // Soft constraints
]
```

### 2. Solver Interface Architecture

**Abstract Base Class** (`solver_interface.h`):
```cpp
class SolverInterface {
    virtual std::array<OptVariables, N+1> solveMPC(
        std::array<Stage, N+1> &stages,
        const State &x0,
        int *status) = 0;
};
```

**Concrete Implementation** (`hpipm_interface.h`/`.cpp`):
- Inherits from `SolverInterface`
- Implements MPC problem setup:
  - `setDynamics()` - Sets up plant dynamics
  - `setCost()` - Sets up cost matrices
  - `setBounds()` - Sets up bound constraints
  - `setPolytopicConstraints()` - Sets up trajectory constraints
  - `setSoftConstraints()` - Sets up relaxations
  - `Solve()` - Calls HPIPM solver

### 3. Data Flow

```
MPC Controller
    ↓
[Stage (linearized dynamics + costs)]
    ↓
HpipmInterface::solveMPC()
    ├─ setDynamics() → Extract A, B, g matrices
    ├─ setCost() → Extract Q, R, q, r matrices
    ├─ setBounds() → Extract bound vectors
    ├─ setPolytopicConstraints() → Extract C, D constraints
    └─ Solve()
        ├─ Create HPIPM QP dimension structure
        ├─ Create HPIPM QP problem
        ├─ Create IPM solver
        ├─ d_ocp_qp_ipm_solve()
        └─ Extract solution
    ↓
[OptVariables (state + control solutions)]
    ↓
MPC Controller
```

## Convergence to Libraries

### Current State (Stub-Based):
- ✅ Headers parse correctly
- ✅ Code compiles as stubs
- ⚠️ Solver returns zero vectors (stub behavior)

### To Use Real HPIPM Library:

1. **Build BLASFEO**:
```bash
cd blasfeo
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON
make -j8
# Libraries end up in ../lib/
```

2. **Build HPIPM**:
```bash
cd hpipm
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON -DHPIPM_TESTING=OFF
make -j8
# Libraries end up in ../lib/
```

3. **Update CMakeLists.txt** for your project:
```cmake
include_directories(
    ${CMAKE_SOURCE_DIR}/blasfeo/include
    ${CMAKE_SOURCE_DIR}/eigen-5.0.0
    ${CMAKE_SOURCE_DIR}/hpipm_stubs  # Or use real HPIPM headers
    ${CMAKE_SOURCE_DIR}/Interfaces
)

# Link BLASFEO
target_link_libraries(mpc_controller blasfeo)

# Link real HPIPM library (replace hpipm_stubs with real headers)
target_link_libraries(mpc_controller hpipm)
```

4. **Replace hpipm_stubs with real headers** when HPIPM is built:
   - Download HPIPM source: `https://github.com/giaf/hpipm`
   - Copy `hpipm/include/` to `hpipm/include/` in your project
   - Update include paths in CMakeLists.txt

## Alternative: C++ Wrapper (hpipm-cpp-main)

If you prefer a C++ API instead of the C API:

### Current Implementation (C API via hpipm_interface):
- Direct use of HPIPM C functions
- Manual memory management
- Fast but lower-level

### Alternative (C++ API via hpipm-cpp-main):
- C++ wrapper with RAII
- Automatic memory management
- Better ergonomics
- Requires real HPIPM library

**To switch:**
1. Ensure HPIPM library is built
2. Update `Interfaces/hpipm_interface.cpp` to use `hpipm::OcpQpIpmSolver` class from hpipm-cpp-main
3. Update includes: `#include <hpipm-cpp/hpipm-cpp.hpp>`

## Configuration Parameters

All MPC parameters defined in `config.h`:
- `N = 20` - Prediction horizon length
- `NX = 7` - Number of states: [x, y, vx, vy, theta, delta, v]
- `NU = 2` - Number of controls: [acceleration, steering_rate]
- `NB = 10` - Maximum number of bounds
- `NPC = 3` - Number of polytopic constraints
- `NS = 3` - Number of soft constraints

## Type System

### Solver-Level Types (in `Interfaces/solver_interface.h`):
```cpp
struct LinearModel {           // Dynamics
    Eigen::Matrix<double, NX, NX> A;
    Eigen::Matrix<double, NX, NU> B;
    Eigen::Matrix<double, NX, 1> g;
};

struct CostMatrix {            // Cost matrices
    Eigen::Matrix<double, NX, NX> Q, R;
    Eigen::Matrix<double, NX, NU> S;
    Eigen::Matrix<double, NX, 1> q, r;
    Eigen::Matrix<double, NS, NS> Z;
    Eigen::Matrix<double, NS, 1> z;
};

struct Stage {                 // One MPC stage
    LinearModel lin_model;
    CostMatrix cost_mat;
    int ng, ns;                // Constraint counts
    // Constraint matrices and bounds...
};

struct OptVariables {          // Solution
    Eigen::Matrix<double, NX, 1> x;
    Eigen::Matrix<double, NU, 1> u;
    mpc_controller::state xk;
    mpc_controller::control uk;
};
```

### MPC-Level Types (in `types.h`):
```cpp
namespace mpc_controller {
    struct state {             // 10-state vehicle model
        double x, y, vx, vy, theta, r, delta, v, Throttle, s;
    };
    
    struct control {           // 3-control model
        double D_dot, delta_dot, dV_ghost;
    };
};
```

### Converters:
- `stateToVector(state)` → Eigen 7-vector (subset of 10-state struct)
- `vectorToState(vec)` → State struct
- `vectorToControl(vec)` → Control struct

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `Interfaces/solver_interface.h` | ~90 | Abstract solver interface + type definitions |
| `Interfaces/solver_interface.cpp` | ~22 | Eigen/struct converter functions |
| `Interfaces/hpipm_interface.h` | ~150 | HPIPM solver implementation header |
| `Interfaces/hpipm_interface.cpp` | ~240 | HPIPM solver implementation (C API) |
| `hpipm_stubs/hpipm_*.h` | ~150 | HPIPM function stubs (C API) |
| `blasfeo/include/*.h` | ~350 | BLASFEO header files (KEPT) |
| `eigen-5.0.0/Eigen/` | ~5000 | Real Eigen header library |

## Build Command Example

```bash
g++ -c -I. -I./blasfeo/include -I./eigen-5.0.0 \
    -I./hpipm_stubs -I./Interfaces \
    Interfaces/solver_interface.cpp -o solver_interface.o

g++ -c -I. -I./blasfeo/include -I./eigen-5.0.0 \
    -I./hpipm_stubs -I./Interfaces \
    Interfaces/hpipm_interface.cpp -o hpipm_interface.o

# Link with BLASFEO library (when available)
g++ -L./blasfeo/lib -o mpc_controller main.o ... solver_interface.o hpipm_interface.o -blasfeo
```

## Next Steps

1. ✅ **Files organized and cleaned** - Minimal, focused directory structure
2. ✅ **Interfaces implemented** - Clean solver abstraction
3. ✅ **BLASFEO + Eigen integrated** - Real linear algebra  
4. ⏳ **Build and test** - Compile with your build system
5. ⏳ **Link real HPIPM** - When library is available
6. ⏳ **Benchmark** - Verify solver performance

## Troubleshooting

**IntelliSense errors about Eigen types:**
- May need to restart VS Code to refresh IntelliSense cache
- Ensure `.vscode/c_cpp_properties.json` include paths are correct
- Eigen is a header-only library; no build needed

**Linker errors about HPIPM functions:**
- Replace `hpipm_stubs/` with real HPIPM headers when building
- Link against `libhpipm.so` and `libblasfeo.so`
- Set `LD_LIBRARY_PATH` to library directory

**State/control conversion issues:**
- MPC uses 7-state model: x, y, vx, vy, theta, delta, v
- Full state struct has 10 fields; converters extract needed 7
- Control is 3-DOF in struct but MPC uses NU=2
