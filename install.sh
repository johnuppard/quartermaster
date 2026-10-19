#!/usr/bin/env bash
# Quartermaster installer. Works on macOS and Linux, needs no sudo, schedules nothing.
#
#   bash install.sh              install or update
#   bash install.sh --uninstall  remove Quartermaster (asks for a typed yes; --yes skips)
#
# A repeat run keeps your ROUTING.local.md, LESSONS.md, config.json and runtime folder.
# Optional extras (the daily self-review, the review procedure) live in the extras folder.
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/quartermaster"
HOME_DIR="$HOME/.claude/quartermaster"
SELF_SETUP="$HOME_DIR/extras/self-review/setup_job.py"

UNINSTALL=0
YES=0
for arg in "$@"; do
  case "$arg" in
    --uninstall) UNINSTALL=1 ;;
    --yes) YES=1 ;;
    -h|--help)
      sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

[ -n "$HOME" ] && [ -d "$HOME" ] || die "HOME is not set to an existing folder."

# ---------------------------------------------------------------- uninstall
if [ "$UNINSTALL" -eq 1 ]; then
  say "This will remove Quartermaster:"
  say "  the skill folder  $SKILL_DIR"
  say "  the home folder   $HOME_DIR (your routing, lessons, config and run history)"
  if [ -f "$SELF_SETUP" ]; then
    say "  the daily self-review job (installed from the extras)"
  fi
  if [ "$YES" -ne 1 ]; then
    printf 'Type yes to continue: '
    read -r answer || answer=""
    [ "$answer" = "yes" ] || { say "Cancelled. Nothing was removed."; exit 1; }
  fi
  if [ -f "$SELF_SETUP" ]; then
    python3 "$SELF_SETUP" --remove --home "$HOME_DIR" || say "Warning: the daily job could not be removed automatically. Check it by hand."
  elif [ -f "$HOME_DIR/run_headless.py" ]; then
    say "Note: an older Quartermaster install scheduled a daily job (launchd label com.quartermaster.daily, or a crontab line). This script did not remove it; remove it yourself if it is still there."
  fi
  rm -rf "$SKILL_DIR" "$HOME_DIR"
  say "Quartermaster removed."
  exit 0
fi

# ---------------------------------------------------------------- 1. preflight
CLAUDE_BIN=""
if [ -x "$HOME/.local/bin/claude" ]; then
  CLAUDE_BIN="$HOME/.local/bin/claude"
elif command -v claude >/dev/null 2>&1; then
  CLAUDE_BIN="$(command -v claude)"
fi
if [ -z "$CLAUDE_BIN" ]; then
  cat >&2 <<'MSG'
Error: Claude Code was not found (looked in ~/.local/bin/claude and on PATH).
Install it first, then run this script again:
  macOS, Linux:  curl -fsSL https://claude.ai/install.sh | bash
  or see https://docs.claude.com/en/docs/claude-code/setup
Then open a new terminal so the claude command is on PATH.
MSG
  exit 1
fi

command -v python3 >/dev/null 2>&1 || die "python3 was not found. Install Python 3.9 or newer."
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' \
  || die "python3 is older than 3.9 ($(python3 --version 2>&1)). Install Python 3.9 or newer."

# Everything the repository must ship, checked before anything is written.
SHIPPED_FILES="quartermaster.py ROUTING.md prices.json config.example.json ROUTING.local.example.md LESSONS.md"
missing=""
[ -f "$HERE/skill/SKILL.md" ] || missing="$missing skill/SKILL.md"
[ -f "$HERE/extras/review/REVIEW.md" ] || missing="$missing extras/review/REVIEW.md"
for f in $SHIPPED_FILES; do
  [ -f "$HERE/job/$f" ] || missing="$missing job/$f"
done
if [ -n "$missing" ]; then
  {
    echo "Error: this copy of the repository is incomplete. Missing:"
    for f in $missing; do echo "  $f"; done
    echo "Nothing was installed or changed. Get a complete copy (git pull, or clone again) and re-run."
  } >&2
  exit 1
fi

# ---------------------------------------------------------------- 2. the skill file
mkdir -p "$SKILL_DIR"
cp "$HERE/skill/SKILL.md" "$SKILL_DIR/SKILL.md"

# ---------------------------------------------------------------- 3. the home folder
mkdir -p "$HOME_DIR" "$HOME_DIR/runtime"
for f in quartermaster.py ROUTING.md prices.json config.example.json ROUTING.local.example.md; do
  cp "$HERE/job/$f" "$HOME_DIR/$f"
done
chmod +x "$HOME_DIR/quartermaster.py" 2>/dev/null || true
[ -f "$HOME_DIR/LESSONS.md" ] || cp "$HERE/job/LESSONS.md" "$HOME_DIR/LESSONS.md"

# ---------------------------------------------------------------- 4. setup
say "Files installed. Running setup."
mkdir -p "$HOME_DIR/extras/review"
cp "$HERE/extras/review/REVIEW.md" "$HOME_DIR/extras/review/REVIEW.md"
if ! python3 "$HOME_DIR/quartermaster.py" setup; then
  die "Setup did not finish. The files are in place; fix the message above and run: python3 $HOME_DIR/quartermaster.py setup"
fi

# ---------------------------------------------------------------- 5. next step
say ""
say "Quartermaster is installed."
say "Next: open Claude Code and type /quartermaster help"
