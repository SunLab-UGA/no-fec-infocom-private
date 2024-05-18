#!/bin/bash

# used to build and install the project from the source code

# Exit on error
set -e

# Check if a build directory already exists and rename it with a timestamp
if [ -d "build" ]; then
    mv "build" "build_$(date +%Y%m%d_%H%M%S)"
    echo "Previous build directory renamed to build_$(date +%Y%m%d_%H%M%S)"
fi

# Create a new build directory and enter it
mkdir build
cd build || exit 1

# Run cmake commands
cmake -G Ninja -DCMAKE_INSTALL_PREFIX="$CONDA_PREFIX" -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" -DLIB_SUFFIX="" ..
cmake --build .
cmake --build . --target install

# Return to the original directory
cd ..

echo "Build and installation completed successfully"
