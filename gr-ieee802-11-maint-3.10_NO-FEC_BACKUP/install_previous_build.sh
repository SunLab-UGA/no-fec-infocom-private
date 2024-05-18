#!/bin/bash

# Exit on error
set -e

# Check if a build directory argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <build-directory>"
    exit 1
fi

ORIGINAL_BUILD_DIR=$1
TEMP_BUILD_DIR="build"

# Check if the specified build directory exists
if [ ! -d "$ORIGINAL_BUILD_DIR" ]; then
    echo "Error: Build directory '$ORIGINAL_BUILD_DIR' does not exist."
    exit 1
fi

# Handle case where a build directory already exists
if [ -d "$TEMP_BUILD_DIR" ]; then
    # Rename existing build directory to a backup name with a timestamp
    BACKUP_DIR="build_backup_$(date +%Y%m%d_%H%M%S)"
    mv "$TEMP_BUILD_DIR" "$BACKUP_DIR"
    echo "Existing 'build' directory renamed to '$BACKUP_DIR' for backup."
fi

# Rename the target build directory to 'build' if it is not already named 'build'
if [ "$ORIGINAL_BUILD_DIR" != "$TEMP_BUILD_DIR" ]; then
    mv "$ORIGINAL_BUILD_DIR" "$TEMP_BUILD_DIR"
    echo "Build directory temporarily renamed for installation purposes."
fi

# Enter the temporary build directory
cd "$TEMP_BUILD_DIR" || exit 1

# Run cmake command to install the build
cmake --install .

# Return to the original directory
cd ..

# Restore the build directory to its original name if it was changed
if [ "$ORIGINAL_BUILD_DIR" != "$TEMP_BUILD_DIR" ]; then
    mv "$TEMP_BUILD_DIR" "$ORIGINAL_BUILD_DIR"
    echo "Build directory renamed back to its original name."
fi

# Restore the original 'build' directory if it was renamed
if [ -d "$BACKUP_DIR" ]; then
    mv "$BACKUP_DIR" "$TEMP_BUILD_DIR"
    echo "Original 'build' directory restored from backup."
fi

echo "Installation of build from '$ORIGINAL_BUILD_DIR' completed successfully"
