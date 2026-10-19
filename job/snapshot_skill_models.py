#!/usr/bin/env python3
"""Quartermaster: snapshot of every installed skill's `model:` frontmatter line.

The snapshot lives in <home>/runtime/skill-models.json:
    {"<skill>": {"model": "<tier>" or null, "frontmatter": true|false, "symlink": true|false}}

Usage:
    snapshot_skill_models.py --write                 write the snapshot from the files now
    snapshot_skill_models.py --diff                  print what differs, as JSON, exit 0
    snapshot_skill_models.py --restore <skill>       put the snapshot tier back into that skill's file

Options:
    --home <path>        Quartermaster home folder (default ~/.claude/quartermaster)
    --skills-dir <path>  installed skills (default ~/.claude/skills), for tests

"Symlink" means the SKILL.md file itself is a symbolic link. A skill folder that is a link to a real
folder elsewhere is edited through the link; a SKILL.md that is itself a link is never edited.

Python 3.9+, standard library only.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

BOM = chr(0xFEFF)
DEFAULT_HOME = Path(os.environ.get('QUARTERMASTER_HOME', str(Path.home() / '.claude' / 'quartermaster'))).expanduser()
DEFAULT_SKILLS = Path.home() / '.claude' / 'skills'

FM_RE = re.compile(r'\A---\s*\n(.*?)\n---\s*$', re.S | re.M)
MODEL_LINE_RE = re.compile(r'^model[ \t]*:[ \t]*(.*)$', re.M)
MODEL_LINE_START = re.compile(r'^model[ \t]*:')


def clean_value(raw):
    """Strip quotes and a trailing comment from a frontmatter value. Empty result -> None."""
    v = raw.strip()
    if not v:
        return None
    if v[0] in ('"', "'"):
        q = v[0]
        end = v.find(q, 1)
        v = v[1:end] if end != -1 else v[1:]
    else:
        v = re.split(r'(?:^|\s)#', v, maxsplit=1)[0]
    v = v.strip().strip('"\'').strip()
    return v or None


def parse_text(text):
    """Return (has_frontmatter, model_or_None) for the text of a SKILL.md."""
    if text.startswith(BOM):
        text = text[1:]
    m = FM_RE.match(text)
    if not m:
        return False, None
    mm = MODEL_LINE_RE.search(m.group(1))
    return True, (clean_value(mm.group(1)) if mm else None)


def read_text(path):
    return Path(path).read_bytes().decode('utf-8', errors='replace')


def scan(skills_dir):
    """Current state of every <skills_dir>/*/SKILL.md."""
    found = {}
    skills_dir = Path(skills_dir)
    if not skills_dir.is_dir():
        return found
    for d in sorted(skills_dir.iterdir(), key=lambda p: p.name):
        f = d / 'SKILL.md'
        if not (f.is_file() or f.is_symlink()):
            continue
        fm, model = False, None
        try:
            fm, model = parse_text(read_text(f))
        except OSError:
            pass
        found[d.name] = {'model': model, 'frontmatter': fm, 'symlink': f.is_symlink()}
    return found


def snapshot_path(home):
    return Path(home) / 'runtime' / 'skill-models.json'


def normalise(entry):
    if isinstance(entry, dict):
        return {'model': entry.get('model'), 'frontmatter': bool(entry.get('frontmatter', False)),
                'symlink': bool(entry.get('symlink', False))}
    return {'model': entry if isinstance(entry, str) else None, 'frontmatter': True, 'symlink': False}


def load_snapshot(home):
    p = snapshot_path(home)
    if not p.exists():
        return None
    try:
        raw = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    return {k: normalise(v) for k, v in raw.items()}


def diff(snap, now):
    out = {'dropped': [], 'changed': [], 'new': [], 'removed': []}
    if snap is None:
        out['snapshot_missing'] = True
        return out
    for name in sorted(set(snap) | set(now)):
        if name not in snap:
            out['new'].append({'skill': name, 'now': now[name]['model'], 'symlink': now[name]['symlink']})
        elif name not in now:
            out['removed'].append({'skill': name, 'snapshot': snap[name]['model']})
        else:
            s, n = snap[name]['model'], now[name]['model']
            if s is not None and n is None:
                out['dropped'].append({'skill': name, 'snapshot': s, 'symlink': now[name]['symlink'],
                                       'frontmatter': now[name]['frontmatter']})
            elif n is not None and s != n:
                out['changed'].append({'skill': name, 'snapshot': s, 'now': n})
    return out


def atomic_write_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o7777 if path.exists() else 0o644
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix='.tmp-', suffix='.part')
    try:
        with os.fdopen(fd, 'wb') as fh:
            fh.write(data)
        os.chmod(tmp, mode)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def restore(home, skills_dir, skill):
    """Put the snapshot tier into the skill file as the first line after the opening ---."""
    snap = load_snapshot(home)
    if snap is None:
        return False, {'skill': skill, 'error': 'no snapshot found'}
    if skill not in snap:
        return False, {'skill': skill, 'error': 'skill is not in the snapshot'}
    tier = snap[skill]['model']
    if not tier:
        return False, {'skill': skill, 'error': 'the snapshot has no tier for this skill'}
    f = Path(skills_dir) / skill / 'SKILL.md'
    if f.is_symlink():
        return False, {'skill': skill, 'error': 'SKILL.md is a symbolic link; not edited, report it'}
    if not f.is_file():
        return False, {'skill': skill, 'error': 'SKILL.md not found'}
    raw = f.read_bytes().decode('utf-8', errors='replace')
    bom = BOM if raw.startswith(BOM) else ''
    text = raw[len(bom):]
    m = FM_RE.match(text)
    if not m:
        return False, {'skill': skill, 'error': 'the file has no frontmatter; not edited'}
    crlf = '\r\n' in text[:m.end(1) + 4]
    lines = m.group(1).split('\n')
    kept = [ln for ln in lines if not MODEL_LINE_START.match(ln)]
    new_line = 'model: ' + tier + ('\r' if crlf else '')
    if lines and lines[0].rstrip('\r') == new_line.rstrip('\r') and len(kept) == len(lines) - 1:
        return True, {'skill': skill, 'restored': tier, 'changed': False, 'note': 'already the first line'}
    new_body = '\n'.join([new_line] + kept)
    new_text = bom + text[:m.start(1)] + new_body + text[m.end(1):]
    atomic_write_bytes(f, new_text.encode('utf-8'))
    check = parse_text(read_text(f))
    if check != (True, tier):
        return False, {'skill': skill, 'error': 'written, but the check read back %r' % (check,)}
    return True, {'skill': skill, 'restored': tier, 'changed': True}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--home', default=str(DEFAULT_HOME))
    ap.add_argument('--skills-dir', default=str(DEFAULT_SKILLS))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--write', action='store_true')
    g.add_argument('--diff', action='store_true')
    g.add_argument('--restore', metavar='SKILL')
    a = ap.parse_args(argv)
    home = Path(a.home).expanduser()
    skills = Path(a.skills_dir).expanduser()

    if a.write:
        now = scan(skills)
        atomic_write_bytes(snapshot_path(home), (json.dumps(now, indent=1, sort_keys=True) + '\n').encode('utf-8'))
        print(json.dumps({'written': str(snapshot_path(home)), 'skills': len(now),
                          'with_model': sum(1 for v in now.values() if v['model']),
                          'symlinks': sum(1 for v in now.values() if v['symlink'])}))
        return 0
    if a.diff:
        print(json.dumps(diff(load_snapshot(home), scan(skills)), indent=1))
        return 0
    ok, info = restore(home, skills, a.restore)
    print(json.dumps(info))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
