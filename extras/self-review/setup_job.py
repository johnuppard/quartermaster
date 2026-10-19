#!/usr/bin/env python3
"""Quartermaster self-review: schedule or unschedule the daily job.

    setup_job.py [--home <path>]            schedule run_headless.py once a day
    setup_job.py --remove [--home <path>]   unschedule it (removes only the job, nothing else)

macOS: writes ~/Library/LaunchAgents/com.quartermaster.daily.plist and loads it with launchctl, running
run_headless.py with the Python that ran this script. Elsewhere: adds one crontab line. The hour comes from
run_hour in <home>/config.json (default 10).

Options: --home <path> (default ~/.claude/quartermaster), --launch-agents-dir <path> (macOS, tests),
--no-launchctl (macOS: write or delete the plist but do not call launchctl).

Python 3.9+, standard library only.
"""
import argparse
import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_HOME = Path(os.environ.get('QUARTERMASTER_HOME', str(Path.home() / '.claude' / 'quartermaster'))).expanduser()
LABEL = 'com.quartermaster.daily'
RUN_PY = HERE / 'run_headless.py'
# A crontab line belongs to the job when it runs run_headless.py from a Quartermaster folder.
CRON_MARKERS = ('quartermaster/extras/self-review/run_headless.py', 'quartermaster/run_headless.py')


def run_cmd(cmd, **kw):
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, **kw)
    except (OSError, ValueError) as e:
        class R:
            returncode = 127
            stdout = ''
            stderr = str(e)
        return R()


def read_run_hour(home):
    cfg = Path(home) / 'config.json'
    hour = 10
    if cfg.is_file():
        try:
            data = json.loads(cfg.read_text(encoding='utf-8'))
        except (OSError, ValueError) as e:
            raise SystemExit('config.json cannot be read: %s' % e)
        if isinstance(data, dict) and 'run_hour' in data:
            hour = data['run_hour']
    if isinstance(hour, bool) or not isinstance(hour, int) or not 0 <= hour <= 23:
        raise SystemExit('config.json: run_hour must be a whole number from 0 to 23, got %r' % (hour,))
    return hour


def is_job_line(line):
    if line.lstrip().startswith('#'):
        return False
    return any(m in line for m in CRON_MARKERS) or str(RUN_PY) in line


def cron_rewrite(current, hour, line):
    """Return (new crontab text, action). action: add, changed or same."""
    lines = current.splitlines()
    found = False
    changed = False
    for i, ln in enumerate(lines):
        if not is_job_line(ln):
            continue
        parts = ln.split(None, 5)
        if len(parts) < 6:
            continue
        found = True
        if parts[1] != str(hour):
            parts[1] = str(hour)
            lines[i] = ' '.join(parts)
            changed = True
    if found:
        return ('\n'.join(lines) + '\n', 'changed') if changed else (current, 'same')
    new = '\n'.join(lines) + '\n' if lines else ''
    return new + line + '\n', 'add'


def plist_dir(args):
    return Path(args.launch_agents_dir) if args.launch_agents_dir else Path.home() / 'Library' / 'LaunchAgents'


def install(args, home):
    if not RUN_PY.is_file():
        print('FAILED: %s is missing' % RUN_PY)
        return 1
    hour = read_run_hour(home)
    runtime = home / 'runtime'
    if sys.platform == 'darwin':
        plist_path = plist_dir(args) / (LABEL + '.plist')
        user_home = str(Path.home())
        python_exe = sys.executable or '/usr/bin/python3'
        plist = {
            'Label': LABEL,
            'ProgramArguments': [python_exe, str(RUN_PY), '--home', str(home)],
            'WorkingDirectory': str(home),
            'StartCalendarInterval': {'Hour': hour, 'Minute': 0},
            'EnvironmentVariables': {
                'HOME': user_home,
                'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:%s/.local/bin' % user_home,
            },
            'StandardOutPath': str(runtime / 'launchd.out.log'),
            'StandardErrorPath': str(runtime / 'launchd.err.log'),
        }
        data = plistlib.dumps(plist)
        same = plist_path.is_file() and plist_path.read_bytes() == data
        domain = 'gui/%d' % os.getuid()
        loaded = False
        if not args.no_launchctl:
            loaded = run_cmd(['launchctl', 'print', '%s/%s' % (domain, LABEL)]).returncode == 0
        if same and (loaded or args.no_launchctl):
            print('skipped: %s is already written%s (Python used: %s)' % (
                plist_path, ' and loaded' if loaded else '', python_exe))
            return 0
        runtime.mkdir(parents=True, exist_ok=True)
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_bytes(data)
        print('done: wrote %s (daily at %02d:00, Python used: %s)' % (plist_path, hour, python_exe))
        if args.no_launchctl:
            print('skipped: launchctl bootstrap (--no-launchctl)')
            return 0
        run_cmd(['launchctl', 'bootout', '%s/%s' % (domain, LABEL)])  # failure is fine: not loaded yet
        r = run_cmd(['launchctl', 'bootstrap', domain, str(plist_path)])
        if r.returncode == 0:
            print('done: launchctl bootstrap %s %s' % (domain, LABEL))
            return 0
        print('FAILED: launchctl bootstrap %s: %s' % (LABEL, (r.stderr or r.stdout).strip()))
        return 1
    line = '0 %d * * * %s %s --home %s' % (hour, sys.executable or 'python3', RUN_PY, home)
    r = run_cmd(['crontab', '-l'])
    if r.returncode == 127:
        print('skipped: this system has no launchd or crontab support here. Add this line to your scheduler yourself:')
        print(line)
        return 0
    current = r.stdout if r.returncode == 0 else ''
    new, action = cron_rewrite(current, hour, line)
    if action == 'same':
        print('skipped: crontab already has a line for run_headless.py at hour %d' % hour)
        return 0
    w = run_cmd(['crontab', '-'], input=new)
    if w.returncode == 0:
        print('done: crontab hour changed to %d' % hour if action == 'changed' else 'done: added crontab line: %s' % line)
        return 0
    print('FAILED: crontab said: %s\nAdd this line yourself:\n%s' % (w.stderr.strip(), line))
    return 1


def remove(args, home):
    did = False
    if sys.platform == 'darwin':
        plist_path = plist_dir(args) / (LABEL + '.plist')
        if not args.no_launchctl:
            r = run_cmd(['launchctl', 'bootout', 'gui/%d/%s' % (os.getuid(), LABEL)])
            if r.returncode == 0:
                print('done: unloaded %s from launchd' % LABEL)
                did = True
        if plist_path.is_file():
            plist_path.unlink()
            print('done: removed %s' % plist_path)
            did = True
    r = run_cmd(['crontab', '-l'])
    if r.returncode == 0:
        lines = r.stdout.splitlines()
        kept = [ln for ln in lines if not is_job_line(ln)]
        if len(kept) != len(lines):
            w = run_cmd(['crontab', '-'], input=('\n'.join(kept) + '\n') if kept else '')
            if w.returncode == 0:
                print('done: removed the Quartermaster line from your crontab')
                did = True
            else:
                print('FAILED: crontab said: %s' % w.stderr.strip())
                return 1
    if not did:
        print('skipped: no daily job found, nothing to remove')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--home', default=str(DEFAULT_HOME))
    ap.add_argument('--remove', action='store_true', help='unschedule the daily job')
    ap.add_argument('--launch-agents-dir', default=None, help=argparse.SUPPRESS)
    ap.add_argument('--no-launchctl', action='store_true', help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    home = Path(args.home).expanduser()
    return remove(args, home) if args.remove else install(args, home)


if __name__ == '__main__':
    sys.exit(main())
