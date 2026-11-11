#!/usr/bin/env bash
# Builds the tkinterFit Linux executable and a .tar.gz package of it.
#
#   bash build-linux.sh
#
# Steps:
#   1. creates .venv (Python 3.14) if it does not exist
#   2. installs requirements.txt and PyInstaller
#   3. builds dist/tkinterFit/tkinterFit with PyInstaller (tkinterFit.spec)
#   4. builds installer/Output/tkinterFit-<ver>-linux-<arch>.tar.gz, which
#      contains the program, LICENSE.md, README.md and install.sh
#
# The executable runs on Linux systems with the same or a newer glibc than
# the one it was built on, so build on the oldest distribution you want to
# support.  It is built for this machine's architecture (x86_64 or aarch64).
#
# Environment variables (optional):
#   PYTHON   Python 3.14 interpreter to use (default: python3.14)

set -euo pipefail
cd "$(dirname "$0")"

if [[ "$(uname -s)" != Linux ]]; then
    echo "build-linux.sh must be run on Linux" >&2
    exit 1
fi

PYTHON=${PYTHON:-python3.14}
VERSION=$(sed -n 's/^#define MyAppVersion "\(.*\)"/\1/p' installer/tkinterFit.iss)
ARCH=$(uname -m)

if [[ ! -x .venv/bin/python ]]; then
    if ! command -v "$PYTHON" >/dev/null; then
        echo "$PYTHON not found - install Python 3.14 (with venv and tkinter)," >&2
        echo "or set PYTHON to the interpreter to use" >&2
        exit 1
    fi
    "$PYTHON" -m venv .venv
fi
python=.venv/bin/python

if ! "$python" -c 'import tkinter; tkinter.Tcl()' 2>/dev/null; then
    echo "This Python has no working tkinter. Install your distribution's" >&2
    echo "tkinter package, e.g. python3.14-tk (Debian/Ubuntu) or" >&2
    echo "python3.14-tkinter (Fedora)" >&2
    exit 1
fi

"$python" -m pip install --upgrade pip
"$python" -m pip install -r requirements.txt pyinstaller

"$python" -m PyInstaller --noconfirm --clean tkinterFit.spec
echo "Built dist/tkinterFit/tkinterFit"

PACKAGE="tkinterFit-$VERSION-linux-$ARCH"
STAGING=$(mktemp -d)
trap 'rm -rf "$STAGING"' EXIT
mkdir "$STAGING/$PACKAGE"
cp -R dist/tkinterFit "$STAGING/$PACKAGE/"
cp LICENSE.md README.md "$STAGING/$PACKAGE/"

# install.sh installs for the current user, or system wide when run as root
cat > "$STAGING/$PACKAGE/install.sh" <<'EOF'
#!/usr/bin/env bash
# Installs tkinterFit for the current user (~/.local), or for all users
# (/opt and /usr/local) when run as root.  Run again to upgrade.
set -euo pipefail
cd "$(dirname "$0")"
if [[ $EUID -eq 0 ]]; then
    APPDIR=/opt/tkinterFit
    BINDIR=/usr/local/bin
    DESKTOPDIR=/usr/local/share/applications
else
    APPDIR="$HOME/.local/share/tkinterFit"
    BINDIR="$HOME/.local/bin"
    DESKTOPDIR="$HOME/.local/share/applications"
fi
rm -rf "$APPDIR"
mkdir -p "$APPDIR" "$BINDIR" "$DESKTOPDIR"
cp -R tkinterFit/. "$APPDIR/"
cp LICENSE.md README.md "$APPDIR/"
ln -sf "$APPDIR/tkinterFit" "$BINDIR/tkinterFit"
cat > "$DESKTOPDIR/tkinterFit.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=tkinterFit
Comment=Curve and surface fitting
Exec="$APPDIR/tkinterFit"
Terminal=false
Categories=Science;Math;Education;
DESKTOP
echo "Installed tkinterFit in $APPDIR"
echo "Run it from your applications menu, or with: $BINDIR/tkinterFit"
EOF
chmod +x "$STAGING/$PACKAGE/install.sh"

mkdir -p installer/Output
tar -C "$STAGING" -czf "installer/Output/$PACKAGE.tar.gz" "$PACKAGE"
echo "Built installer/Output/$PACKAGE.tar.gz"
