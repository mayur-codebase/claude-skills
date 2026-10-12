#!/bin/sh
# Installs skills from this repo into ~/.claude/skills/ (personal, all projects).
# All skills:     curl -fsSL https://raw.githubusercontent.com/mayur-codebase/claude-skills/main/install.sh | sh
# Specific ones:  curl -fsSL https://raw.githubusercontent.com/mayur-codebase/claude-skills/main/install.sh | sh -s -- codebase-docs [ctx ...]
set -e

REPO="https://github.com/mayur-codebase/claude-skills.git"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Fetching claude-skills..."
git clone --quiet --depth 1 "$REPO" "$TMP"

mkdir -p "$HOME/.claude/skills"
count=0
for skill in "$TMP"/plugins/*/skills/*/; do
  [ -f "${skill}SKILL.md" ] || continue
  name="$(basename "$skill")"
  if [ "$#" -gt 0 ]; then
    case " $* " in *" $name "*) ;; *) continue ;; esac
  fi
  rm -rf "$HOME/.claude/skills/$name"
  cp -R "$skill" "$HOME/.claude/skills/$name"
  echo "  installed /$name"
  count=$((count + 1))
done

if [ "$count" -eq 0 ]; then
  echo "No matching skills found. Available: $(ls "$TMP"/plugins | tr '\n' ' ')" >&2
  exit 1
fi

echo "Done. $count skill(s) installed to ~/.claude/skills/ — available in your next Claude Code session."
