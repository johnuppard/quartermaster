#!/usr/bin/env bash
# Quartermaster installer. Works on macOS and Linux, needs no sudo.
#
#   bash install.sh              install or update
#   bash install.sh --force      also reset your own files (backed up first)
#   bash install.sh --uninstall  remove Quartermaster (asks for a typed yes; --yes skips)
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/quartermaster"
HOME_DIR="$HOME/.claude/quartermaster"
PLIST="$HOME/Library/LaunchAgents/com.quartermaster.daily.plist"
LABEL="com.quartermaster.daily"

FORCE=0
UNINSTALL=0
YES=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --yes) YES=1 ;;
    -h|--help)
      sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

OS="$(uname -s)"
say() { printf '%s\n' "$*"; }
warn() { printf 'Warning: %s\n' "$*" >&2; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

[ -n "$HOME" ] && [ -d "$HOME" ] || die "HOME is not set to an existing folder."

# ---------------------------------------------------------------- uninstall
if [ "$UNINSTALL" -eq 1 ]; then
  say "This will remove Quartermaster:"
  say "  the skill file   $SKILL_DIR"
  say "  the home folder  $HOME_DIR (your routing, lessons, config and run history)"
  say "  the daily job    $LABEL (launchd) or its crontab line"
  if [ "$YES" -ne 1 ]; then
    printf 'Type yes to continue: '
    read -r answer || answer=""
    [ "$answer" = "yes" ] || { say "Cancelled. Nothing was removed."; exit 1; }
  fi

  if [ "$OS" = "Darwin" ]; then
    if command -v launchctl >/dev/null 2>&1; then
      launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
    fi
    rm -f "$PLIST"
  fi
  if command -v crontab >/dev/null 2>&1; then
    current="$(crontab -l 2>/dev/null || true)"
    if printf '%s\n' "$current" | grep -Eq '\.claude/quartermaster/|# quartermaster'; then
      printf '%s\n' "$current" | grep -Ev '\.claude/quartermaster/|# quartermaster' | crontab -
      say "Removed the Quartermaster line from your crontab."
    fi
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
PY_BIN="$(command -v python3)"
say "Python: setup and the daily job will use $PY_BIN ($(python3 --version 2>&1))."
if [ "$OS" = "Darwin" ] && [ "$PY_BIN" = "/usr/bin/python3" ]; then
  if ! xcode-select -p >/dev/null 2>&1; then
    warn "/usr/bin/python3 on macOS needs the Command Line Tools (run: xcode-select --install), and the daily job may fail without them. A python3 earlier on PATH (for example from Homebrew) is used first if you have one."
  fi
fi

if [ "$OS" = "Darwin" ]; then
  command -v launchctl >/dev/null 2>&1 || warn "launchctl not found. The daily job cannot be scheduled automatically."
  command -v plutil >/dev/null 2>&1 || warn "plutil not found. The daily job file cannot be checked."
else
  command -v crontab >/dev/null 2>&1 || warn "crontab not found. Setup will print the cron line for you to add yourself."
fi

# Everything the repository must ship, checked before anything is written.
SHIPPED_FILES="JOB.md ROUTING.md prices.json config.example.json ROUTING.local.example.md LESSONS.md quartermaster.py run_headless.py collect_evidence.py done_check.py snapshot_skill_models.py"
missing=""
[ -f "$HERE/skill/SKILL.md" ] || missing="$missing skill/SKILL.md"
[ -f "$HERE/LICENSE" ] || missing="$missing LICENSE"
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

# ---------------------------------------------------------------- 2. --force: back up, then reset
if [ "$FORCE" -eq 1 ] && [ -d "$HOME_DIR" ]; then
  stamp="$(date +%Y%m%d-%H%M%S)"
  backup="$HOME_DIR/runtime/backup-install-$stamp"
  warn "--force resets your routing, lessons, config and run history."
  warn "A backup is saved to $backup"
  mkdir -p "$backup"
  for f in ROUTING.local.md LESSONS.md config.json; do
    if [ -f "$HOME_DIR/$f" ]; then
      cp -p "$HOME_DIR/$f" "$backup/$f"
      rm -f "$HOME_DIR/$f"
    fi
  done
  if [ -d "$HOME_DIR/runtime" ]; then
    for item in "$HOME_DIR/runtime"/* "$HOME_DIR/runtime"/.[!.]*; do
      [ -e "$item" ] || continue
      case "$(basename "$item")" in backup-install-*) continue ;; esac
      cp -pR "$item" "$backup/"
      rm -rf "$item"
    done
  fi
fi

# ---------------------------------------------------------------- 3. the skill file
mkdir -p "$SKILL_DIR"
cp "$HERE/skill/SKILL.md" "$SKILL_DIR/SKILL.md"

# ---------------------------------------------------------------- 4. the home folder
mkdir -p "$HOME_DIR" "$HOME_DIR/runtime"
for f in "$HERE"/job/*.py; do
  [ -f "$f" ] || continue
  cp "$f" "$HOME_DIR/"
done
chmod +x "$HOME_DIR"/*.py 2>/dev/null || true
for f in JOB.md ROUTING.md prices.json config.example.json ROUTING.local.example.md; do
  cp "$HERE/job/$f" "$HOME_DIR/$f"
done
[ -f "$HOME_DIR/LESSONS.md" ] || cp "$HERE/job/LESSONS.md" "$HOME_DIR/LESSONS.md"

# ---------------------------------------------------------------- 5. setup
say "Files installed. Running setup."
if ! python3 "$HOME_DIR/quartermaster.py" setup; then
  die "Setup did not finish. The files are in place; fix the message above and run: python3 $HOME_DIR/quartermaster.py setup"
fi

# ---------------------------------------------------------------- 6. next step
say ""
say "Quartermaster is installed."
say "Next: open Claude Code and type /quartermaster help"
