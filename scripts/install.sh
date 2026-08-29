#!/usr/bin/env bash
# Install the ML4T skills into an agent's skill directory.
#
# Skill discovery is one level deep: an agent looks for
# <skills-dir>/<skill-name>/SKILL.md and does not recurse. This repo groups
# skills into category directories for readability, so the categories have to be
# flattened at install time. That is all this script does.
#
#   ./scripts/install.sh                      # ~/.claude/skills, symlinks
#   ./scripts/install.sh .agents/skills       # a different target
#   ./scripts/install.sh ~/.claude/skills --copy
#
# Symlinks are the default so that `git pull` updates every installed skill.
# Use --copy when the target must not depend on this checkout.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$HOME/.claude/skills}"
MODE="${2:-}"

mkdir -p "$TARGET"

installed=0
skipped=0
for skill in "$REPO"/*/*/SKILL.md; do
    dir="$(dirname "$skill")"
    name="ml4t-$(basename "$dir")"
    dest="$TARGET/$name"

    if [ -e "$dest" ] || [ -L "$dest" ]; then
        if [ -L "$dest" ] && [ "$(readlink -f "$dest")" = "$(readlink -f "$dir")" ]; then
            skipped=$((skipped + 1))
            continue
        fi
        echo "skip: $name already exists at $dest and is not ours" >&2
        skipped=$((skipped + 1))
        continue
    fi

    if [ "$MODE" = "--copy" ]; then
        cp -r "$dir" "$dest"
    else
        ln -s "$dir" "$dest"
    fi
    installed=$((installed + 1))
done

echo "installed $installed skills into $TARGET ($skipped skipped)"
echo "each is available as ml4t-<skill-name>, for example /ml4t-data-leakage"
