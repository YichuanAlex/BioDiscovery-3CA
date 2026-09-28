#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
COMPONENT="$ROOT/components/tooluniverse"
RUNTIME="$ROOT/.runtime/macos/tooluniverse"
HOME_DIR="$ROOT/.runtime/macos/tooluniverse-home"
LOCK="$ROOT/.runtime/macos/tooluniverse-pip-freeze.txt"

rm -rf "$COMPONENT" "$RUNTIME" "$HOME_DIR"
rm -f "$LOCK"
echo "Removed the workflow-local ToolUniverse component and isolated runtime."
