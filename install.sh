#!/usr/bin/env bash
# Install the `explainer` CLI on PATH (editable: repo edits apply immediately)
# and link every skill into ~/.agents/skills and ~/.claude/skills.
#   ./install.sh              install or update
#   ./install.sh --uninstall  remove the CLI and the skill links
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_SKILLS="$HOME/.agents/skills"
CLAUDE_SKILLS="$HOME/.claude/skills"

link_skill() {  # link_skill <target> <link>
  local target="$1" link="$2"
  if [ -e "$link" ] && [ ! -L "$link" ]; then
    echo "skip: $link exists and is not a symlink"
    return
  fi
  ln -sfn "$target" "$link"
  echo "linked $link -> $target"
}

if [ "${1:-}" = "--uninstall" ]; then
  for dir in "$REPO"/skills/*/; do
    name="$(basename "$dir")"
    for link in "$AGENTS_SKILLS/$name" "$CLAUDE_SKILLS/$name"; do
      if [ -L "$link" ]; then rm "$link" && echo "removed $link"; fi
    done
  done
  uv tool uninstall scaledial-skill || true
  exit 0
fi

command -v uv >/dev/null || { echo "uv is required: brew install uv"; exit 1; }
command -v ffmpeg >/dev/null || echo "warning: ffmpeg not found (brew install ffmpeg)"

uv tool install --python 3.12 --editable "$REPO" --force

mkdir -p "$AGENTS_SKILLS" "$CLAUDE_SKILLS"
for dir in "$REPO"/skills/*/; do
  name="$(basename "$dir")"
  link_skill "${dir%/}" "$AGENTS_SKILLS/$name"
  link_skill "../../.agents/skills/$name" "$CLAUDE_SKILLS/$name"
done

case ":$PATH:" in
  *":$(uv tool dir --bin):"*) ;;
  *) echo "warning: $(uv tool dir --bin) is not on PATH. Run: uv tool update-shell" ;;
esac

explainer doctor --fetch
