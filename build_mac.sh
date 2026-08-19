#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv-mac-build"
DIST_DIR="$PROJECT_DIR/dist-mac"
BUILD_DIR="$PROJECT_DIR/build-mac"
RELEASE_DIR="$PROJECT_DIR/release"
ZIP_PATH="$RELEASE_DIR/TextConverter-macOS.zip"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$PROJECT_DIR/requirements-build.txt"

rm -rf "$DIST_DIR" "$BUILD_DIR"
mkdir -p "$RELEASE_DIR"
rm -f "$ZIP_PATH"

# 从项目父目录启动，避免根目录的 copy.py 遮蔽 Python 标准库 copy。
cd "$(dirname "$PROJECT_DIR")"
"$VENV_DIR/bin/python" -m PyInstaller \
  --noconfirm \
  --clean \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  "$PROJECT_DIR/mac.spec"

ditto -c -k --sequesterRsrc --keepParent \
  "$DIST_DIR/TextConverter.app" \
  "$ZIP_PATH"

echo "Build complete: $ZIP_PATH"
