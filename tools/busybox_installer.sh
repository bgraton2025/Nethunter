#!/bin/bash

# BusyBox installer for Kali Nethunter

BUSYBOX_URL="https://f-droid.org/repo/stericson.busybox_71.apk"
APK_NAME="busybox.apk"

echo "Checking for existing BusyBox installation..."
if command -v busybox >/dev/null 2>&1; then
    echo "BusyBox is already installed."
    exit 0
fi

echo "Downloading BusyBox.apk from F-Droid..."
if command -v curl >/dev/null 2>&1; then
    curl -L -o "$APK_NAME" "$BUSYBOX_URL"
elif command -v wget >/dev/null 2>&1; then
    wget -O "$APK_NAME" "$BUSYBOX_URL"
else
    echo "Neither curl nor wget is available. Please download the APK manually: $BUSYBOX_URL"
    exit 1
fi

echo "Downloaded $APK_NAME."

cat <<'EOF'
Next steps to install on device:
  - Install via ADB: adb install -r "$APK_NAME"
  - Or transfer the APK to the device and install using a file manager.

Note: Installing APKs requires user approval on the device. This script cannot auto-accept the installation prompt.
EOF

exit 0
