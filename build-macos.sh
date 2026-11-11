#!/usr/bin/env bash
# Builds the FindCurves Studio macOS application and disk image.
#
#   bash build-macos.sh
#
# Steps:
#   1. creates .venv (Python 3.14) if it does not exist
#   2. installs requirements.txt and PyInstaller
#   3. builds "dist/FindCurves Studio.app" with PyInstaller (FindCurves.spec)
#   4. optionally signs the app with a Developer ID (set CODESIGN_IDENTITY)
#   5. builds installer/Output/FindCurves-Studio-<ver>-macOS-<arch>.dmg
#   6. optionally notarizes the disk image (set NOTARY_PROFILE)
#
# The app is built for the architecture of the Mac running this script
# (arm64 for Apple silicon, x86_64 for Intel) - numpy and scipy do not
# publish universal2 wheels, so build once on each kind of Mac if needed.
#
# Environment variables (all optional):
#   PYTHON             Python 3.14 interpreter to use (default: python3.14)
#   CODESIGN_IDENTITY  e.g. "Developer ID Application: Your Name (TEAMID)".
#                      Without it the app is only ad-hoc signed, and users
#                      must right-click > Open the first time they run it.
#   NOTARY_PROFILE     keychain profile created with
#                      xcrun notarytool store-credentials; requires
#                      CODESIGN_IDENTITY.

set -euo pipefail
cd "$(dirname "$0")"

if [[ "$(uname -s)" != Darwin ]]; then
    echo "build-macos.sh must be run on macOS" >&2
    exit 1
fi

PYTHON=${PYTHON:-python3.14}
VERSION=$(sed -n 's/^#define MyAppVersion "\(.*\)"/\1/p' installer/FindCurves.iss)
ARCH=$(uname -m)

if [[ ! -x .venv/bin/python ]]; then
    if ! command -v "$PYTHON" >/dev/null; then
        echo "$PYTHON not found - install Python 3.14 from https://www.python.org/downloads/" >&2
        echo "(or set PYTHON to the interpreter to use)" >&2
        exit 1
    fi
    "$PYTHON" -m venv .venv
fi
python=.venv/bin/python

if ! "$python" -c 'import tkinter; tkinter.Tcl()' 2>/dev/null; then
    echo "This Python has no working tkinter. Use the python.org installer," >&2
    echo "or with Homebrew: brew install python-tk@3.14" >&2
    exit 1
fi

"$python" -m pip install --upgrade pip
"$python" -m pip install -r requirements.txt pyinstaller

"$python" -m PyInstaller --noconfirm --clean FindCurves.spec
APP="dist/FindCurves Studio.app"
echo "Built $APP"

if [[ -n "${CODESIGN_IDENTITY:-}" ]]; then
    codesign --force --deep --options runtime --timestamp \
        --sign "$CODESIGN_IDENTITY" "$APP"
    codesign --verify --deep --strict "$APP"
    echo "Signed $APP"
fi

mkdir -p installer/Output
DMG="installer/Output/FindCurves-Studio-$VERSION-macOS-$ARCH.dmg"
STAGING=$(mktemp -d)
trap 'rm -rf "$STAGING"' EXIT
cp -R "$APP" "$STAGING/"
cp LICENSE.md README.md "$STAGING/"
ln -s /Applications "$STAGING/Applications"
rm -f "$DMG"
hdiutil create -volname "FindCurves Studio $VERSION" -srcfolder "$STAGING" \
    -fs HFS+ -format UDZO -ov "$DMG"

if [[ -n "${CODESIGN_IDENTITY:-}" ]]; then
    codesign --force --timestamp --sign "$CODESIGN_IDENTITY" "$DMG"
    if [[ -n "${NOTARY_PROFILE:-}" ]]; then
        xcrun notarytool submit "$DMG" --keychain-profile "$NOTARY_PROFILE" --wait
        xcrun stapler staple "$DMG"
        echo "Notarized $DMG"
    fi
fi
echo "Built $DMG"
