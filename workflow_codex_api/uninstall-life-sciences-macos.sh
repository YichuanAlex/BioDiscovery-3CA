#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS="$ROOT/skills/anthropic-life-sciences"
RUNTIME="$ROOT/.runtime/macos/life-sciences"

usage() {
  echo "Usage: $0 --skills | --runtimes | --all" >&2
  exit 2
}

[[ $# -eq 1 ]] || usage
case "$1" in
  --skills)
    rm -rf "$SKILLS"
    echo "Removed installed Anthropic life-sciences skills: $SKILLS"
    ;;
  --runtimes)
    rm -rf "$RUNTIME"
    echo "Removed isolated life-sciences runtimes: $RUNTIME"
    ;;
  --all)
    rm -rf "$SKILLS" "$RUNTIME"
    echo "Removed installed life-sciences skills and isolated runtimes."
    ;;
  *)
    usage
    ;;
esac
