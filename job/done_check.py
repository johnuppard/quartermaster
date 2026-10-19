#!/usr/bin/env python3
"""Quartermaster: the mechanical Done check of the daily self-review (JOB.md, step 5, items a to f), and the
manifest used to prove that a headless run changed nothing it may not change.

Usage:
    done_check.py [--home <path>] [--manifest-before <file>] [--report-date YYYY-MM-DD]
        Prints JSON {"items": [{"item": "a".."f", "result": "yes|no|not checked", "evidence": "..."}], ...}
        (a) the skill file's frontmatter parses and has name: quartermaster
        (b) LESSONS.md is 30 lines or fewer
        (c) every skill named under "Skills by tier" in ROUTING.local.md exists
        (d) every snapshot entry matches its skill file (no dropped, changed or removed model line)
        (e) no em dash or en dash in the shipped markdown files (JOB.md, ROUTING.md) and the skill file;
            with config forbid_dashes true also in ROUTING.local.md, LESSONS.md and the report of
            --report-date (default today)
        (f) the manifest taken now equals --manifest-before ("not checked" without it)
        Exit code 0 always; read the JSON.

    done_check.py manifest --out <file> [--home <path>]
        Write sha256 of: every installed SKILL.md with its `model:` line removed, Quartermaster's own skill file,
        and in the home folder run_headless.py, JOB.md, ROUTING.md, prices.json, quartermaster.py,
        collect_evidence.py, done_check.py, snapshot_skill_models.py, config.json (it holds the
        notify command), plus on macOS the plist ~/Library/LaunchAgents/com.quartermaster.daily.plist (env
        QUARTERMASTER_PLIST overrides the path) and elsewhere the lines of `crontab -l` that contain "quartermaster"
        (key "crontab"; env QUARTERMASTER_CRONTAB_TEXT replaces the crontab output, for tests).
        A file that is absent has sha256 null.

    done_check.py manifest --diff <before> <after>
        Print JSON {"changed": [...]} listing every path whose hash differs.

Test options: --skills-dir <path> (default ~/.claude/skills).
Python 3.9+, standard library only.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import snapshot_skill_models as ssm  # noqa: E402  (same folder)

DEFAULT_HOME = Path(os.environ.get('QUARTERMASTER_HOME', str(Path.home() / '.claude' / 'quartermaster'))).expanduser()
DEFAULT_SKILLS = Path.home() / '.claude' / 'skills'
DEFAULT_PLIST = Path.home() / 'Library' / 'LaunchAgents' / 'com.quartermaster.daily.plist'
HOME_FILES = ['run_headless.py', 'JOB.md', 'ROUTING.md', 'prices.json', 'quartermaster.py', 'collect_evidence.py',
              'done_check.py', 'snapshot_skill_models.py', 'config.json']
TIER_WORDS = {'fable', 'opus', 'sonnet', 'haiku', 'tier', 'skill', 'skills', 'name', 'model'}
EM = chr(0x2014)
EN = chr(0x2013)
BOM = chr(0xFEFF)
DASH_RE = re.compile('[' + EM + EN + ']')


# ---------------------------------------------------------------- manifest

def strip_model_line(raw):
    """Bytes of a SKILL.md with the `model:` line of its frontmatter removed."""
    text = raw.decode('utf-8', errors='surrogateescape')
    bom = BOM if text.startswith(BOM) else ''
    body = text[len(bom):]
    m = ssm.FM_RE.match(body)
    if not m:
        return raw
    lines = m.group(1).split('\n')
    kept = [ln for ln in lines if not ssm.MODEL_LINE_START.match(ln)]
    out = bom + body[:m.start(1)] + '\n'.join(kept) + body[m.end(1):]
    return out.encode('utf-8', errors='surrogateescape')


def sha_of(path, strip_model=False):
    try:
        p = Path(path)
        if not p.is_file():
            return None
        raw = p.read_bytes()
    except OSError:
        return None
    if strip_model:
        raw = strip_model_line(raw)
    return hashlib.sha256(raw).hexdigest()


def plist_path():
    return Path(os.environ.get('QUARTERMASTER_PLIST') or DEFAULT_PLIST)


def crontab_sha():
    """sha256 of the crontab lines that contain "quartermaster", or None when there are none."""
    text = os.environ.get('QUARTERMASTER_CRONTAB_TEXT')
    if text is None:
        try:
            r = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=20)
            text = r.stdout if r.returncode == 0 else ''
        except (OSError, subprocess.SubprocessError):
            text = ''
    lines = [ln.strip() for ln in text.splitlines() if 'quartermaster' in ln.lower()]
    if not lines:
        return None
    return hashlib.sha256('\n'.join(lines).encode('utf-8')).hexdigest()


def build_manifest(home, skills_dir):
    home, skills_dir = Path(home), Path(skills_dir)
    files = {}
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir(), key=lambda p: p.name):
            f = d / 'SKILL.md'
            if f.is_file():
                files['skill/' + d.name] = {'path': str(f), 'sha256': sha_of(f, True), 'strip_model': True}
    own = skills_dir / 'quartermaster' / 'SKILL.md'
    files['quartermaster-skill'] = {'path': str(own), 'sha256': sha_of(own, True), 'strip_model': True}
    for name in HOME_FILES:
        f = home / name
        files['home/' + name] = {'path': str(f), 'sha256': sha_of(f), 'strip_model': False}
    if sys.platform == 'darwin':
        pl = plist_path()
        files['plist'] = {'path': str(pl), 'sha256': sha_of(pl), 'strip_model': False}
    else:
        files['crontab'] = {'path': 'crontab (lines containing quartermaster)', 'sha256': crontab_sha(),
                            'strip_model': False}
    return {'version': 1, 'created': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'home': str(home), 'files': files}


def diff_manifests(before, after):
    changed = []
    b, a = before.get('files', {}), after.get('files', {})
    for key in sorted(set(b) | set(a)):
        sb = b.get(key, {}).get('sha256')
        sa = a.get(key, {}).get('sha256')
        if sb != sa:
            changed.append({'key': key, 'path': (a.get(key) or b.get(key) or {}).get('path'),
                            'before': sb[:12] if sb else None, 'after': sa[:12] if sa else None})
    return changed


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.part')
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    os.replace(str(tmp), str(path))


# ---------------------------------------------------------------- items

def result(item, res, evidence):
    return {'item': item, 'result': res, 'evidence': evidence}


def check_a(skills_dir):
    f = Path(skills_dir) / 'quartermaster' / 'SKILL.md'
    if not f.is_file():
        return result('a', 'no', 'skill file not found: %s' % f)
    text = ssm.read_text(f)
    if text.startswith(BOM):
        text = text[1:]
    m = ssm.FM_RE.match(text)
    if not m:
        return result('a', 'no', 'no frontmatter block found at the top of the skill file')
    nm = re.search(r'^name[ \t]*:[ \t]*(.*)$', m.group(1), re.M)
    name = ssm.clean_value(nm.group(1)) if nm else None
    if name != 'quartermaster':
        return result('a', 'no', 'frontmatter name is %r, expected quartermaster' % name)
    return result('a', 'yes', 'frontmatter parses, name: quartermaster, model line %r' % ssm.parse_text(text)[1])


def check_b(home):
    f = Path(home) / 'LESSONS.md'
    if not f.is_file():
        return result('b', 'no', 'LESSONS.md not found')
    n = len(f.read_text(encoding='utf-8', errors='replace').splitlines())
    return result('b', 'yes' if n <= 30 else 'no', 'LESSONS.md has %d lines (limit 30)' % n)


def skills_section(text):
    lines = text.splitlines()
    start = None
    level = 0
    for i, ln in enumerate(lines):
        m = re.match(r'^(#{1,6})\s*(.*)$', ln)
        if m and re.search(r'skills\s+by\s+tier', m.group(2), re.I):
            start, level = i + 1, len(m.group(1))
            break
    if start is None:
        return None
    out = []
    for ln in lines[start:]:
        m = re.match(r'^(#{1,6})\s', ln)
        if m and len(m.group(1)) <= level:
            break
        out.append(ln)
    return out


NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]*$')


def named_skills(section_lines):
    names = []

    def add(tok):
        tok = tok.strip().strip('`*_ ').strip()
        tok = re.sub(r'\(.*?\)', '', tok).strip().strip('`*_ ').strip()
        if tok and NAME_RE.match(tok) and tok.lower() not in TIER_WORDS and tok not in names:
            names.append(tok)

    for ln in section_lines:
        s = ln.strip()
        if not s:
            continue
        for tok in re.findall(r'`([^`]+)`', s):
            if ':' in tok or '/' in tok or '.' in tok or ' ' in tok:
                continue
            add(tok)
        if s.startswith('|'):
            cells = [c.strip() for c in s.strip('|').split('|')]
            if cells and not re.match(r'^[-: ]+$', cells[0]):
                add(cells[0])
            continue
        m = re.match(r'^[-*]\s+(.*)$', s)
        if m:
            body = m.group(1)
            left, sep, right = body.partition(':')
            if sep:
                if left.strip().strip('`*_ ').lower() in TIER_WORDS:
                    for part in re.split(r'[,;]', right):
                        add(part.split(' ')[0] if ' ' in part.strip() and '`' not in part else part)
                else:
                    add(left)
            else:
                add(re.split(r'\s', body.strip().strip('`'), maxsplit=1)[0])
    return names


def check_c(home, skills_dir):
    f = Path(home) / 'ROUTING.local.md'
    if not f.is_file():
        return result('c', 'not checked', 'ROUTING.local.md not found')
    sec = skills_section(f.read_text(encoding='utf-8', errors='replace'))
    if sec is None:
        return result('c', 'yes', 'no "Skills by tier" section in ROUTING.local.md, no skill named')
    names = named_skills(sec)
    missing = [n for n in names if not (Path(skills_dir) / n / 'SKILL.md').exists()]
    if missing:
        return result('c', 'no', 'named but not installed: %s' % ', '.join(missing))
    return result('c', 'yes', '%d skill(s) named, all installed' % len(names))


def check_d(home, skills_dir):
    snap = ssm.load_snapshot(home)
    if snap is None:
        return result('d', 'no', 'no snapshot at runtime/skill-models.json')
    d = ssm.diff(snap, ssm.scan(skills_dir))
    bad = ['dropped %s' % x['skill'] for x in d['dropped']] + \
          ['changed %s (%s -> %s)' % (x['skill'], x['snapshot'], x['now']) for x in d['changed']] + \
          ['removed %s' % x['skill'] for x in d['removed']]
    if bad:
        return result('d', 'no', '; '.join(bad[:8]) + (' ...' if len(bad) > 8 else ''))
    note = ''
    if d['new']:
        note = '; %d new skill(s) not yet in the snapshot: %s' % (
            len(d['new']), ', '.join(x['skill'] for x in d['new'][:8]))
    return result('d', 'yes', '%d snapshot entries match their files%s' % (len(snap), note))


def load_config(home):
    try:
        data = json.loads((Path(home) / 'config.json').read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def check_e(home, skills_dir, report_date):
    home = Path(home)
    files = [home / 'JOB.md', home / 'ROUTING.md', Path(skills_dir) / 'quartermaster' / 'SKILL.md']
    scope = 'shipped files'
    if load_config(home).get('forbid_dashes') is True:
        files += [home / 'ROUTING.local.md', home / 'LESSONS.md', home / 'runtime' / 'reports' / (report_date + '.md')]
        scope = 'shipped and own files (forbid_dashes is on)'
    hits, checked = [], 0
    for f in files:
        if not f.is_file():
            continue
        checked += 1
        try:
            for i, ln in enumerate(f.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
                if DASH_RE.search(ln):
                    hits.append('%s:%d' % (f.name, i))
        except OSError:
            continue
    if hits:
        return result('e', 'no', 'em or en dash at %s%s' % (', '.join(hits[:6]), ' ...' if len(hits) > 6 else ''))
    return result('e', 'yes', 'no em or en dash in %d file(s), scope: %s' % (checked, scope))


def check_f(home, skills_dir, before_path):
    if not before_path:
        return result('f', 'not checked', 'no --manifest-before given')
    try:
        before = json.loads(Path(before_path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        return result('f', 'not checked', 'cannot read the manifest %s: %s' % (before_path, e))
    changed = diff_manifests(before, build_manifest(home, skills_dir))
    if changed:
        return result('f', 'no', 'changed outside the allowed paths: %s' %
                      ', '.join('%s' % c['path'] for c in changed[:6]))
    return result('f', 'yes', 'manifest unchanged: %d files hashed (model lines excluded)' % len(before.get('files', {})))


# ---------------------------------------------------------------- main

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == 'manifest':
        ap = argparse.ArgumentParser(prog='done_check.py manifest')
        ap.add_argument('--home', default=str(DEFAULT_HOME))
        ap.add_argument('--skills-dir', default=str(DEFAULT_SKILLS))
        ap.add_argument('--out')
        ap.add_argument('--diff', nargs=2, metavar=('BEFORE', 'AFTER'))
        a = ap.parse_args(argv[1:])
        if a.diff:
            try:
                b = json.loads(Path(a.diff[0]).read_text(encoding='utf-8'))
                c = json.loads(Path(a.diff[1]).read_text(encoding='utf-8'))
            except (OSError, ValueError) as e:
                print(json.dumps({'error': str(e)}))
                return 1
            print(json.dumps({'changed': diff_manifests(b, c)}, indent=1))
            return 0
        if a.out:
            m = build_manifest(Path(a.home).expanduser(), Path(a.skills_dir).expanduser())
            write_json(a.out, m)
            print(json.dumps({'written': a.out, 'files': len(m['files'])}))
            return 0
        ap.error('give --out <file> or --diff <before> <after>')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--home', default=str(DEFAULT_HOME))
    ap.add_argument('--skills-dir', default=str(DEFAULT_SKILLS))
    ap.add_argument('--manifest-before')
    ap.add_argument('--report-date', default=datetime.now().strftime('%Y-%m-%d'))
    a = ap.parse_args(argv)
    home = Path(a.home).expanduser()
    skills = Path(a.skills_dir).expanduser()
    items = [check_a(skills), check_b(home), check_c(home, skills), check_d(home, skills),
             check_e(home, skills, a.report_date), check_f(home, skills, a.manifest_before)]
    print(json.dumps({'items': items,
                      'failing': [i['item'] for i in items if i['result'] == 'no'],
                      'not_checked': [i['item'] for i in items if i['result'] == 'not checked']}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
