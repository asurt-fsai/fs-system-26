#include "config.h"

///////////////////////////////////////////////////////////////////////////////
// Initialization Helper for StaticConstants
///////////////////////////////////////////////////////////////////////////////
// This module provides utility initialization functions for MPC configuration

namespace mpc_controller {
// Note: Application configuration is now handled entirely by the Params class
// in src/Params/params.h and src/Params/params.cpp
//
// All MPC parameters (costs, bounds, vehicle dynamics) are loaded from JSON files
// and consolidated into a single Params object that is passed to all components
// (BicycleModel, ConstraintSet, Cost).
//
// This design pattern ensures:
// - Single source of truth for all parameters
// - No duplicate file reads (read once in main.cpp)
// - Easy parameter updates without code changes
// - Type-safe parameter access

} // namespace mpc_controller
