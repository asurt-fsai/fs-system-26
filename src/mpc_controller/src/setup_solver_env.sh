#!/bin/bash
# Solver environment setup script
# Source this before building or running MPC solver

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PREFIX="${SCRIPT_DIR}/install"

export LD_LIBRARY_PATH="${INSTALL_PREFIX}/lib:${LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="${INSTALL_PREFIX}/lib/pkgconfig:${PKG_CONFIG_PATH}"
export CMAKE_PREFIX_PATH="${INSTALL_PREFIX}:${CMAKE_PREFIX_PATH}"

echo "Solver environment configured:"
echo "  BLASFEO: $INSTALL_PREFIX"
echo "  LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
