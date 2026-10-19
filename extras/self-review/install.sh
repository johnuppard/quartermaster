#!/usr/bin/env bash
# Quartermaster self-review (optional extra). Installs the daily job on top of Quartermaster.
#
#   bash extras/self-review/install.sh            install or update, and schedule the daily job
#   bash extras/self-review/install.sh --remove   remove only the daily job (files and settings stay)
#
# Run the main install.sh from the repository first.
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
HOME_DIR="$HOME/.claude/quartermaster"
DEST="$HOME_DIR/extras/self-review"

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }

REMOVE=0
for arg in "$@"; do
  case "$arg" in
    --remove) REMOVE=1 ;;
    -h|--help) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

[ -n "$HOME" ] && [ -d "$HOME" ] || die "HOME is not set to an existing folder."

if [ "$REMOVE" -eq 1 ]; then
  [ -f "$DEST/setup_job.py" ] || die "the self-review is not installed ($DEST/setup_job.py not found). Nothing to remove."
  python3 "$DEST/setup_job.py" --remove --home "$HOME_DIR"
  say "Only the daily job was removed. Quartermaster and its files are untouched."
  exit 0
fi

say "Quartermaster self-review: a daily job that keeps Quartermaster current."
say "On a quiet day it starts no model and costs nothing. A day with evidence starts a background Sonnet or Opus run on your Claude subscription."
say "It runs once a day at the hour set by run_hour in $HOME_DIR/config.json (default 10)."
say "To remove only the job: bash $HERE/install.sh --remove   (or: python3 $DEST/setup_job.py --remove)"
say ""

command -v python3 >/dev/null 2>&1 || die "python3 was not found. Install Python 3.9 or newer."
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' \
  || die "python3 is older than 3.9 ($(python3 --version 2>&1)). Install Python 3.9 or newer."
[ -f "$HOME_DIR/quartermaster.py" ] || die "Quartermaster is not installed ($HOME_DIR/quartermaster.py not found). Run install.sh from the repository first."

missing=""
for f in JOB.md run_headless.py collect_evidence.py done_check.py snapshot_skill_models.py setup_job.py config.example.json; do
  [ -f "$HERE/$f" ] || missing="$missing $f"
done
[ -z "$missing" ] || die "this copy of the repository is incomplete. Missing in $HERE:$missing"

mkdir -p "$DEST" "$HOME_DIR/runtime/reports"
for f in JOB.md run_headless.py collect_evidence.py done_check.py snapshot_skill_models.py setup_job.py config.example.json; do
  cp "$HERE/$f" "$DEST/$f"
done
chmod +x "$DEST"/*.py 2>/dev/null || true
say "Copied the self-review scripts and JOB.md to $DEST"

# Merge the example keys into config.json. Existing values are never overwritten.
python3 - "$HERE/config.example.json" "$HOME_DIR/config.json" <<'PY'
import json, os, sys
example_path, config_path = sys.argv[1], sys.argv[2]
with open(example_path, encoding="utf-8") as fh:
    example = json.load(fh)
config = {}
if os.path.isfile(config_path):
    try:
        with open(config_path, encoding="utf-8") as fh:
            config = json.load(fh)
    except ValueError as e:
        sys.exit("Error: %s is not valid JSON (%s). Fix it or move it away, then run this again." % (config_path, e))
    if not isinstance(config, dict):
        sys.exit("Error: %s does not hold a JSON object." % config_path)
added = [k for k in example if not k.startswith("_") and k not in config]
for k in added:
    config[k] = example[k]
if added or not os.path.isfile(config_path):
    tmp = config_path + ".part"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, config_path)
print("config.json: %s" % (("added " + ", ".join(added)) if added else "all keys already present, nothing changed"))
PY

# First snapshot of every installed skill's model line (the daily check compares against it).
if [ ! -f "$HOME_DIR/runtime/skill-models.json" ]; then
  python3 "$DEST/snapshot_skill_models.py" --write --home "$HOME_DIR" >/dev/null \
    && say "Took the first snapshot of the installed skills' model lines." \
    || say "Warning: the skill snapshot failed. The daily job will report it."
fi

python3 "$DEST/setup_job.py" --home "$HOME_DIR"

say ""
say "Self-review installed. Reports appear in $HOME_DIR/runtime/reports/"
