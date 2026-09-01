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
#   ./scripts/install.sh --copy               # default target, copies
#   ./scripts/install.sh ~/.claude/skills --copy
#
# Symlinks are the default so that `git pull` updates every installed skill.
# Use --copy when the target must not depend on this checkout.

set -euo pipefail
shopt -s nullglob

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKER=".ml4t-installed"   # written into every copy, so a rerun knows it is ours
TARGET=""
COPY=0

# --copy is a flag, not a positional, so that `install.sh --copy` does not
# quietly create a directory named "--copy".
for arg in "$@"; do
    case "$arg" in
        --copy) COPY=1 ;;
        -h|--help)
            sed -n '2,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        -*) echo "unknown option: $arg" >&2; exit 2 ;;
        *)
            if [ -n "$TARGET" ]; then
                echo "expected at most one target directory, got '$TARGET' and '$arg'" >&2
                exit 2
            fi
            TARGET="$arg"
            ;;
    esac
done
TARGET="${TARGET:-$HOME/.claude/skills}"

skills=("$REPO"/*/*/SKILL.md)
if [ ${#skills[@]} -eq 0 ]; then
    echo "no SKILL.md files found under $REPO" >&2
    exit 1
fi

mkdir -p "$TARGET"

installed=0
current=0
replaced=0
conflicts=0
for skill in "${skills[@]}"; do
    dir="$(dirname "$skill")"
    name="ml4t-$(basename "$dir")"
    dest="$TARGET/$name"

    if [ -e "$dest" ] || [ -L "$dest" ]; then
        # Two ways a destination can be ours: a symlink already pointing at this
        # checkout, or a copy carrying the marker this script wrote. Matching on
        # the SKILL.md contents instead would delete a skill someone copied in by
        # hand and edited, since that file carries the same `name:`.
        if [ -L "$dest" ] && [ "$(readlink -f "$dest")" = "$(readlink -f "$dir")" ]; then
            if [ "$COPY" -eq 0 ]; then
                current=$((current + 1))     # same mode, same target: nothing to do
                continue
            fi
            replaced=$((replaced + 1))       # switching this install to copies
        elif [ ! -L "$dest" ] && [ -f "$dest/$MARKER" ]; then
            replaced=$((replaced + 1))
        else
            # Not ours: leave it alone, but this skill is now missing from the
            # install, so the run must not report success.
            echo "conflict: $name already exists at $dest and is not ours" >&2
            conflicts=$((conflicts + 1))
            continue
        fi
    fi

    if [ "$COPY" -eq 1 ]; then
        # Stage the whole copy first and only then swap, keeping the previous
        # install until the new one is in place: an interrupted or failed run
        # must never leave the target without a working skill.
        staging="$(mktemp -d "$TARGET/.staging-$name.XXXXXX")"
        cp -r "$dir" "$staging/$name"
        printf 'installed by %s\n' "$REPO/scripts/install.sh" > "$staging/$name/$MARKER"
        if [ -e "$dest" ]; then
            mv "$dest" "$staging/previous"
        fi
        # No POSIX call swaps two directories atomically, so put the previous
        # install back if the second move fails rather than leaving nothing.
        mv "$staging/$name" "$dest" || {
            [ -e "$staging/previous" ] && mv "$staging/previous" "$dest"
            echo "failed to install $name; previous install restored" >&2
            exit 1
        }
        rm -rf "$staging"
    else
        # Swapping a symlink over a symlink is atomic, so the old one is never
        # removed first. mv -T refuses a directory target, so a marked copy
        # being converted to a symlink has to go first.
        if [ -d "$dest" ] && [ ! -L "$dest" ]; then
            rm -rf "$dest"
        fi
        ln -sfn "$dir" "$dest.new" && mv -T "$dest.new" "$dest"
    fi
    installed=$((installed + 1))
done

echo "installed $installed skills into $TARGET ($current already current, $replaced replaced)"
echo "each is available as ml4t-<skill-name>, for example /ml4t-data-leakage"

if [ "$conflicts" -gt 0 ]; then
    echo "$conflicts skill(s) not installed: the name was taken. Resolve and re-run." >&2
    exit 1
fi
