#!/bin/bash

# Set the app manifest and build directory
APP_MANIFEST="com.zzimm.GnomeApp.json"
BUILD_DIR="build-dir"
REPO_NAME="my-repo"
BUNDLE_FILE="com.zzimm.GnomeApp.flatpak"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo "Options:"
    echo "  --release    Build and create a release version"
    echo "  --bundle     Build, create release and generate a bundle"
    echo "  --debug      Build a debug version"
}

# Check for argument
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Process the flag
case "$1" in
    --release)
        echo "Building and creating release version..."
        flatpak-builder "$BUILD_DIR" "$APP_MANIFEST" --force-clean --build-only
        ;;

    --bundle)
        echo "Building, creating release, and generating bundle..."
        # Build release version
        flatpak-builder "$BUILD_DIR" "$APP_MANIFEST" --force-clean --build-only 
        # Export to local repository
        flatpak-builder "$BUILD_DIR" "$APP_MANIFEST" --repo="$REPO_NAME" --force-clean 
        # Create Flatpak bundle
        flatpak build-bundle "$REPO_NAME" "$BUNDLE_FILE" com.zzimm.GnomeApp
        echo "Bundle created: $BUNDLE_FILE"
        ;;

    --debug)
        echo "Building debug version..."
        flatpak-builder "$BUILD_DIR" "$APP_MANIFEST" --force-clean 
        ;;

    *)
        echo "Invalid option!"
        show_usage
        exit 1
        ;;
esac

