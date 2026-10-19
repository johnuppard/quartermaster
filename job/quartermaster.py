#!/usr/bin/env python3
"""Quartermaster helper: status, setup, board, record, help.

Python 3.9+, standard library only. Installed to ~/.claude/quartermaster/quartermaster.py.
All runtime files live under <home>/runtime/. Use --home <path> to work in another folder
(for tests). Transcripts are read from ~/.claude/projects unless --projects is given.
"""
import argparse
import datetime
import glob
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LABEL = "com.quartermaster.daily"
TIERS = ["fable", "opus", "sonnet", "haiku"]  # fixed board order
STATUSES = ["planned", "running", "done", "escalated", "failed"]
NOT_NEEDED = "not needed for this task"
# Levels count Fable-equivalent tokens won, cumulative.
LEVELS = [
    (0, "Apprentice"),
    (1000000, "Clerk"),
    (5000000, "Bookkeeper"),
    (15000000, "Treasurer"),
    (40000000, "Quartermaster"),
    (100000000, "Grand Miser"),
    (250000000, "Counting House"),
    (600000000, "Fort Knox"),
]

HELP_TEXT = """Quartermaster, the model allocator

What Quartermaster does
  Quartermaster saves tokens and time. The top model (Fable) thinks only where thinking is hard.
  Cheaper models do the rest, several pieces at the same time. A piece steps up one model if
  the cheaper one says it cannot do it well, and the result is checked one model up.
  The board shows what each model did. The scorecard shows the tokens and the minutes you won.

When to use it
  Tasks with more than three steps, several files or systems, new builds, reports and audits.
  Not for one-step questions, small fixes or lookups.

How to call it
  /quartermaster <task>
  /quartermaster review <task>
  /quartermaster help
  /quartermaster setup
  /quartermaster lesson: <feedback>

The review stage
  Before work starts, Dreamers look for a better way, the planner makes it concrete, and
  Critics challenge the plan on intent, execution and cost. Say "no review" to skip it, or
  start with /quartermaster review <task> to ask for it.

What you will see
  The plan line (say no there if you do not want it), the board with all four models, and the
  scorecard at the end: tokens won, time won, the share of work on cheaper models, your week
  and your level. Money appears only as a reference line at the bottom. A daily self-review
  note appears when something changed.

How to steer it
  Raise or lower a ceiling in the plan line, say "no Fable" or "Fable for piece 2", or give
  a lesson. Your lessons live in ~/.claude/quartermaster/LESSONS.md. Your own routing rows live in
  ROUTING.local.md.

What it cannot do
  Change the model of the session you are in (the /model command does that), or start by
  itself. You start it by typing /quartermaster.
"""


class QuartermasterError(Exception):
    """Bad input or a broken installation. Printed as one line, exit code 1."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("quartermaster: error: %s\n" % message)
        sys.exit(1)


# ----------------------------------------------------------------------------- paths


class Ctx:
    def __init__(self, home, projects):
        self.home = Path(home).expanduser().resolve() if home else (Path.home() / ".claude" / "quartermaster")
        self.projects = Path(projects).expanduser() if projects else (Path.home() / ".claude" / "projects")

    @property
    def runtime(self):
        return self.home / "runtime"


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path, what):
    try:
        with open(str(path), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise QuartermasterError("%s not found: %s" % (what, path))
    except ValueError as e:
        raise QuartermasterError("%s is not valid JSON (%s): %s" % (what, e, path))


def write_json_atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, str(path))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ----------------------------------------------------------------------------- pieces and transcripts


def parse_pieces(text, need_agent_for_done):
    try:
        pieces = json.loads(text)
    except ValueError as e:
        raise QuartermasterError("--pieces is not valid JSON: %s" % e)
    if not isinstance(pieces, list) or not pieces:
        raise QuartermasterError("--pieces must be a non-empty JSON list of objects")
    out = []
    for i, p in enumerate(pieces, 1):
        label = "piece %d" % i
        if not isinstance(p, dict):
            raise QuartermasterError("%s is not an object" % label)
        name = p.get("piece")
        if not isinstance(name, str) or not name.strip():
            raise QuartermasterError("%s needs a non-empty \"piece\" text" % label)
        model = p.get("model")
        if model not in TIERS:
            raise QuartermasterError("%s (%s): \"model\" must be one of %s, got %r" % (label, name, "|".join(TIERS), model))
        status = p.get("status")
        if status is not None and status not in STATUSES:
            raise QuartermasterError("%s (%s): \"status\" must be one of %s, got %r" % (label, name, "|".join(STATUSES), status))
        esc = p.get("escalated_to")
        if esc is not None and esc not in TIERS:
            raise QuartermasterError("%s (%s): \"escalated_to\" must be null or one of %s, got %r" % (label, name, "|".join(TIERS), esc))
        agent = p.get("agent_id")
        if agent is not None:
            if not isinstance(agent, str) or not re.match(r"^[A-Za-z0-9_-]+$", agent):
                raise QuartermasterError("%s (%s): \"agent_id\" must be a plain id like a67c9a9090265454e, got %r" % (label, name, agent))
        note = p.get("note")
        outcome = p.get("outcome")
        shown_status = status or (outcome if outcome in STATUSES else None) or "planned"
        done_like = shown_status == "done" or outcome == "done"
        if need_agent_for_done and done_like and not agent:
            raise QuartermasterError("%s (%s) is done but has no \"agent_id\"; record needs it to read the real token usage" % (label, name))
        out.append({
            "piece": name.strip(),
            "model": model,
            "status": shown_status,
            "outcome": outcome if isinstance(outcome, str) and outcome else shown_status,
            "agent_id": agent or None,
            "escalated_to": esc,
            "note": note if isinstance(note, str) and note else None,
        })
    return out


def find_transcript(ctx, agent_id):
    pattern = str(ctx.projects / "*" / "*" / "subagents" / "**" / ("agent-%s.jsonl" % agent_id))
    hits = glob.glob(pattern, recursive=True)
    if not hits:
        return None
    hits.sort(key=lambda p: (len(p), p))
    return hits[0]


_TS = re.compile(r"^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.(\d+))?(Z|[+-]\d\d:?\d\d)?$")


def parse_ts(value):
    if not isinstance(value, str):
        return None
    m = _TS.match(value.strip())
    if not m:
        return None
    y, mo, d, h, mi, s, frac, tz = m.groups()
    micro = int((frac or "0")[:6].ljust(6, "0"))
    dt = datetime.datetime(int(y), int(mo), int(d), int(h), int(mi), int(s), micro, tzinfo=datetime.timezone.utc)
    if tz and tz != "Z":
        sign = 1 if tz[0] == "+" else -1
        digits = tz[1:].replace(":", "")
        dt -= sign * datetime.timedelta(hours=int(digits[:2]), minutes=int(digits[2:]))
    return dt


def tier_of(model_id):
    low = (model_id or "").lower()
    for t in TIERS:
        if t in low:
            return t
    return None


def read_usage(path):
    """Return dict(tokens, actual_model, seconds, messages) from one agent transcript.
    "messages" holds the token counts of every API message, for per-message pricing.

    The transcript writes one record per content block, so a single API message appears
    several times with the same message.id and the same usage. Counting every record would
    multiply the tokens. Records are therefore grouped by message.id and the largest value
    of each field is kept (the last record of a message carries the final output count).
    Records without an id are counted one by one.
    """
    by_id = {}
    models = {}
    first = last = None
    anon = 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            ts = parse_ts(rec.get("timestamp"))
            if ts is not None:
                if first is None or ts < first:
                    first = ts
                if last is None or ts > last:
                    last = ts
            msg = rec.get("message")
            if not isinstance(msg, dict):
                continue
            usage = msg.get("usage")
            if not isinstance(usage, dict):
                continue
            mid = msg.get("id")
            if not mid:
                anon += 1
                mid = "anon-%d" % anon
            cur = by_id.setdefault(mid, {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0})
            for key, field in (("input", "input_tokens"), ("cache_write", "cache_creation_input_tokens"),
                               ("cache_read", "cache_read_input_tokens"), ("output", "output_tokens")):
                v = usage.get(field) or 0
                if isinstance(v, (int, float)) and v > cur[key]:
                    cur[key] = int(v)
            model = msg.get("model")
            if isinstance(model, str) and model and not model.startswith("<"):
                models[model] = models.get(model, 0) + 1
    tokens = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    for cur in by_id.values():
        for k in tokens:
            tokens[k] += cur[k]
    actual = max(models, key=lambda m: models[m]) if models else None
    seconds = None
    if first is not None and last is not None:
        seconds = (last - first).total_seconds()
    return {"tokens": tokens, "actual_model": actual, "seconds": seconds,
            "messages": list(by_id.values())}


def load_prices(ctx):
    path = ctx.home / "prices.json"
    data = read_json(path, "prices.json")
    for t in TIERS:
        row = data.get(t)
        if not isinstance(row, dict):
            raise QuartermasterError("prices.json has no entry for %s: %s" % (t, path))
        for k in ("in", "out", "cache_read", "cache_write"):
            if not isinstance(row.get(k), (int, float)):
                raise QuartermasterError("prices.json: %s.%s must be a number: %s" % (t, k, path))
        tier_keys = ("long_prompt_threshold", "input_over_100k", "output_over_100k")
        if any(k in row for k in tier_keys):
            for k in tier_keys:
                if not isinstance(row.get(k), (int, float)) or isinstance(row.get(k), bool):
                    raise QuartermasterError("prices.json: %s.%s must be a number when a long-prompt price is given: %s"
                                       % (t, k, path))
    return data


def cost_of(tokens, row):
    """Price ONE message's tokens. When the row has long-prompt rates and the message's prompt
    (input + cache write + cache read) is above the threshold, the whole message is priced at the
    long-prompt rates: input and output as given, cache write and cache read keep their ratio to
    the input price (cache read stays at 10% of input in the shipped file)."""
    in_p, out_p, cw_p, cr_p = row["in"], row["out"], row["cache_write"], row["cache_read"]
    thr = row.get("long_prompt_threshold")
    if thr is not None and "input_over_100k" in row and "output_over_100k" in row:
        prompt = tokens["input"] + tokens["cache_write"] + tokens["cache_read"]
        if prompt > thr and row["in"] > 0:
            scale = row["input_over_100k"] / float(row["in"])
            in_p, out_p = row["input_over_100k"], row["output_over_100k"]
            cw_p, cr_p = cw_p * scale, cr_p * scale
    return (tokens["input"] * in_p + tokens["cache_write"] * cw_p
            + tokens["cache_read"] * cr_p + tokens["output"] * out_p) / 1e6


def cost_of_messages(messages, row):
    return sum(cost_of(m, row) for m in messages)


def enrich(ctx, pieces):
    """Attach usage to every piece that has an agent_id. Adds keys: found, tokens, actual_model, seconds."""
    for p in pieces:
        p["found"] = None  # None: no agent id, True/False: transcript looked up
        p["tokens"] = None
        p["messages"] = None
        p["actual_model"] = None
        p["seconds"] = None
        if not p["agent_id"]:
            continue
        path = find_transcript(ctx, p["agent_id"])
        p["found"] = bool(path)
        if not path:
            continue
        u = read_usage(path)
        p["tokens"] = u["tokens"]
        p["messages"] = u["messages"]
        p["actual_model"] = u["actual_model"]
        p["seconds"] = u["seconds"]
    return pieces


# ----------------------------------------------------------------------------- formatting


def group_tier(p):
    return p["escalated_to"] or p["model"]


def fmt_tokens(p):
    if p["agent_id"] is None:
        return "-"
    if not p["found"]:
        return "?"
    return "{:,}".format(sum(p["tokens"].values()))


def fmt_seconds(sec):
    if sec is None:
        return "?"
    sec = int(round(sec))
    if sec < 60:
        return "%ds" % sec
    return "%d:%02d" % (sec // 60, sec % 60)


def fmt_time(p):
    if p["agent_id"] is None:
        return "-"
    if not p["found"] or p["seconds"] is None:
        return "?"
    return fmt_seconds(p["seconds"])


def cell(text):
    return str(text).replace("|", "/").replace("\r", " ").replace("\n", " ").strip()


def money(x):
    x = float(x)
    if abs(x) < 1:
        return "$%.4f" % x
    return "$%.2f" % x


def board_text(pieces):
    lines = ["Quartermaster board", "", "| Model | Piece | Status | Tokens | Time |", "|---|---|---|---|---|"]
    for tier in TIERS:
        group = [p for p in pieces if group_tier(p) == tier]
        if not group:
            lines.append("| %s | %s | - | - | - |" % (tier.capitalize(), NOT_NEEDED))
            continue
        for p in group:
            model_cell = tier.capitalize()
            actual = tier_of(p["actual_model"])
            if actual and actual != tier:
                model_cell += " (ran on %s)" % actual.capitalize()
            piece_cell = p["piece"]
            if p["escalated_to"]:
                piece_cell += " (stepped up from %s)" % p["model"].capitalize()
            if p["note"]:
                piece_cell += " - " + p["note"]
            lines.append("| %s | %s | %s | %s | %s |" % (
                cell(model_cell), cell(piece_cell), cell(p["status"]), fmt_tokens(p), fmt_time(p)))
    return "\n".join(lines)


# ----------------------------------------------------------------------------- board and record


def cmd_board(ctx, args):
    pieces = parse_pieces(args.pieces, need_agent_for_done=False)
    enrich(ctx, pieces)
    print(board_text(pieces))
    return 0


def level_for(total):
    name = LEVELS[0][1]
    for threshold, lname in LEVELS:
        if total >= threshold:
            name = lname
    return name


def next_level(total):
    for threshold, lname in LEVELS:
        if threshold > total:
            return threshold, lname
    return None


def cmd_record(ctx, args):
    pieces = parse_pieces(args.pieces, need_agent_for_done=True)
    prices = load_prices(ctx)
    enrich(ctx, pieces)

    for p in pieces:
        if p["agent_id"] and not p["found"]:
            if p["outcome"] == "done" or p["status"] == "done":
                raise QuartermasterError("no transcript found for agent %s (piece: %s). Searched %s. "
                                   "Check the agent id; nothing was recorded." % (p["agent_id"], p["piece"], ctx.projects))
            sys.stderr.write("quartermaster: warning: no transcript for agent %s (piece: %s); counted as zero tokens\n"
                             % (p["agent_id"], p["piece"]))

    zero = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    total_tokens = 0
    cheap_tokens = 0
    total_cost = cost_fable = cost_opus = 0.0
    seconds_list = []
    run_pieces = []
    agents = set()
    for p in pieces:
        tokens = p["tokens"] or dict(zero)
        priced_tier = tier_of(p["actual_model"]) or group_tier(p)
        if p["actual_model"] and not tier_of(p["actual_model"]):
            sys.stderr.write("quartermaster: warning: unknown model %r for piece %s; priced as %s\n"
                             % (p["actual_model"], p["piece"], priced_tier))
        msgs = p["messages"] or [dict(zero)]
        c = cost_of_messages(msgs, prices[priced_tier])
        total_cost += c
        cost_fable += cost_of_messages(msgs, prices["fable"])
        cost_opus += cost_of_messages(msgs, prices["opus"])
        total_tokens += sum(tokens.values())
        if priced_tier in ("sonnet", "haiku"):
            cheap_tokens += sum(tokens.values())
        if p["seconds"] is not None:
            seconds_list.append(p["seconds"])
        if p["agent_id"]:
            agents.add(p["agent_id"])
        run_pieces.append({
            "piece": p["piece"], "model": p["model"], "actual_model": p["actual_model"],
            "agent_id": p["agent_id"], "escalated_to": p["escalated_to"], "outcome": p["outcome"],
            "tokens": tokens, "seconds": None if p["seconds"] is None else round(p["seconds"], 1),
            "cost": round(c, 6),
        })

    won_fable = cost_fable - total_cost
    won_opus = cost_opus - total_cost
    sec_sum = sum(seconds_list)
    sec_longest = max(seconds_list) if seconds_list else 0.0
    time_won = sec_sum - sec_longest
    # Fable-equivalent tokens won: the saving in dollars divided by Fable's blended price
    # for this run (all-Fable cost per token processed).
    if cost_fable > 0 and total_tokens > 0:
        tokens_won = int(round(won_fable / (cost_fable / total_tokens)))
    else:
        tokens_won = 0
    if cost_opus > 0 and total_tokens > 0:
        tokens_won_opus = int(round(won_opus / (cost_opus / total_tokens)))
    else:
        tokens_won_opus = 0
    cheap_share = (cheap_tokens * 100.0 / total_tokens) if total_tokens > 0 else 0.0

    ts = now_utc()
    run = {
        "ts": iso(ts), "task": args.task, "type": args.type, "size": args.size, "stakes": args.stakes,
        "pieces": run_pieces, "checked_by": args.checked_by,
        "cost_actual": round(total_cost, 6), "cost_all_fable": round(cost_fable, 6),
        "cost_all_opus": round(cost_opus, 6), "won_vs_fable": round(won_fable, 6),
        "won_vs_opus": round(won_opus, 6), "seconds_longest": round(sec_longest, 1),
        "seconds_sum": round(sec_sum, 1), "cwd": os.getcwd(),
        "tokens_total": total_tokens, "tokens_won_fable_eq": tokens_won,
        "tokens_won_opus_eq": tokens_won_opus,
        "cheap_share_pct": round(cheap_share, 1),
    }

    # scoreboard first (validate it before anything is appended), then runs.jsonl
    sb_path = ctx.runtime / "scoreboard.json"
    if sb_path.exists():
        sb = read_json(sb_path, "scoreboard.json")
        if not isinstance(sb, dict):
            raise QuartermasterError("scoreboard.json is not an object: %s" % sb_path)
    else:
        sb = {}
    sb.setdefault("total_won_vs_fable", 0.0)
    sb.setdefault("total_won_vs_opus", 0.0)
    sb.setdefault("total_tokens_won", 0)
    sb.setdefault("total_tokens_won_opus", 0)
    sb.setdefault("runs", 0)
    sb.setdefault("best_run", None)
    sb.setdefault("weeks", {})
    sb["total_won_vs_fable"] = round(float(sb["total_won_vs_fable"]) + won_fable, 6)
    sb["total_won_vs_opus"] = round(float(sb["total_won_vs_opus"]) + won_opus, 6)
    sb["total_tokens_won"] = int(sb["total_tokens_won"]) + tokens_won
    sb["total_tokens_won_opus"] = int(sb["total_tokens_won_opus"]) + tokens_won_opus
    sb["runs"] = int(sb["runs"]) + 1
    iso_year, iso_week, _ = ts.isocalendar()
    week_key = "%d-W%02d" % (iso_year, iso_week)
    wk = sb["weeks"].setdefault(week_key, {"won_vs_fable": 0.0, "tokens_won": 0, "runs": 0})
    wk["tokens_won"] = int(wk.get("tokens_won", 0)) + tokens_won
    wk["tokens_won_opus"] = int(wk.get("tokens_won_opus", 0)) + tokens_won_opus
    wk["won_vs_fable"] = round(float(wk["won_vs_fable"]) + won_fable, 6)
    wk["runs"] = int(wk["runs"]) + 1
    best = sb.get("best_run")
    is_best = (not isinstance(best, dict)) or tokens_won > int(best.get("tokens_won", 0))
    if is_best:
        sb["best_run"] = {"ts": run["ts"], "task": args.task, "tokens_won": tokens_won,
                          "won_vs_fable": round(won_fable, 6)}
    sb["level"] = level_for(sb["total_tokens_won"])

    ctx.runtime.mkdir(parents=True, exist_ok=True)
    with open(str(ctx.runtime / "runs.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(run, ensure_ascii=False) + "\n")
    write_json_atomic(sb_path, sb)

    total = sb["total_tokens_won"]
    nxt = next_level(total)
    if nxt:
        level_part = "Level: %s, %s tokens to %s." % (sb["level"], "{:,}".format(nxt[0] - total), nxt[1])
    else:
        level_part = "Level: %s, top level reached." % sb["level"]
    b = sb["best_run"]
    best_task = re.sub(r"(?i)estimate", "est.", str(b.get("task", "")))
    best_part = "Personal best: %s (%s)." % ("{:,}".format(int(b.get("tokens_won", 0))), best_task)

    def plural(n, word):
        return "%d %s%s" % (n, word, "" if n == 1 else "s")

    out = [board_text(pieces), "", "Scorecard", ""]
    out.append("- Tokens won against all on Fable: %s Fable-equivalent tokens (%s tokens processed by %s)" % (
        "{:,}".format(tokens_won), "{:,}".format(total_tokens), plural(len(agents), "agent")))
    out.append("- Tokens won against all on Opus: %s Opus-equivalent tokens" % "{:,}".format(tokens_won_opus))
    out.append("- Time won: %.1f minutes (the longest piece took %s, the pieces together would have taken %s one after another)" % (
        time_won / 60.0, fmt_seconds(sec_longest), fmt_seconds(sec_sum)))
    out.append("- Share of the work on cheaper models: %.0f%% of tokens on Sonnet and Haiku" % cheap_share)
    out.append("- This week: %s Fable-equivalent tokens won in %s. %s %s" % (
        "{:,}".format(wk["tokens_won"]), plural(wk["runs"], "run"), best_part, level_part))
    out.append("")
    out.append("For reference, at Anthropic API list prices (an estimate, not a bill): this run %s, all on Fable %s, all on Opus %s." % (
        money(total_cost), money(cost_fable), money(cost_opus)))
    print("\n".join(out))
    return 0


# ----------------------------------------------------------------------------- status and setup


def run_cmd(cmd, **kw):
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, **kw)
    except (OSError, ValueError) as e:
        class R:
            returncode = 127
            stdout = ""
            stderr = str(e)
        return R()


def job_state(ctx, agents_dir=None):
    """Return (ok, text) for the daily job."""
    run_py = ctx.home / "run_headless.py"
    if sys.platform == "darwin":
        r = run_cmd(["launchctl", "print", "gui/%d/%s" % (os.getuid(), LABEL)])
        plist = (Path(agents_dir) if agents_dir else Path.home() / "Library" / "LaunchAgents") / (LABEL + ".plist")
        if r.returncode == 0:
            return True, "daily job: launchd %s loaded" % LABEL
        if plist.exists():
            return False, "daily job: plist exists but launchd %s is not loaded (run: quartermaster.py setup)" % LABEL
        return False, "daily job: not installed (run: quartermaster.py setup)"
    if sys.platform.startswith("linux"):
        r = run_cmd(["crontab", "-l"])
        if r.returncode == 0 and "quartermaster/run_headless.py" in r.stdout:
            return True, "daily job: crontab line found"
        return False, "daily job: no crontab line with quartermaster/run_headless.py (run: quartermaster.py setup)"
    return False, "daily job: cannot be checked on this system (add a daily run of %s yourself)" % run_py


def review_line(ctx):
    state_path = ctx.runtime / "state.json"
    parts = []
    if state_path.exists():
        try:
            st = json.loads(state_path.read_text(encoding="utf-8"))
        except ValueError:
            st = None
        if isinstance(st, dict):
            parts.append("last_run %s, last_status %s" % (st.get("last_run", "never"), st.get("last_status", "unknown")))
    reports = ctx.runtime / "reports"
    if reports.is_dir():
        files = [f for f in reports.iterdir() if f.is_file()]
        if files:
            newest = max(files, key=lambda f: f.stat().st_mtime)
            first = ""
            with open(str(newest), "r", encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    if ln.strip():
                        first = ln.strip()
                        break
            parts.append("report %s: %s" % (newest.name, first or "(empty)"))
    if not parts:
        return "last self-review: none yet"
    return "last self-review: " + "; ".join(parts)


def compute_status(ctx, agents_dir=None):
    lines = []
    if not ctx.home.is_dir():
        return "NOT INSTALLED", ["home folder: missing (%s)" % ctx.home]
    missing = 0
    lines.append("home folder: %s" % ctx.home)
    items = [
        ("ROUTING.md", ctx.home / "ROUTING.md"),
        ("ROUTING.local.md", ctx.home / "ROUTING.local.md"),
        ("LESSONS.md", ctx.home / "LESSONS.md"),
        ("prices.json", ctx.home / "prices.json"),
        ("config.json", ctx.home / "config.json"),
        ("runtime/skill-models.json", ctx.runtime / "skill-models.json"),
    ]
    for name, path in items:
        if path.is_file():
            lines.append("%s: present" % name)
        else:
            lines.append("%s: MISSING" % name)
            missing += 1
    ok, text = job_state(ctx, agents_dir)
    lines.append(text)
    if not ok:
        missing += 1
    lines.append(review_line(ctx))
    return ("INSTALLED" if missing == 0 else "INCOMPLETE"), lines


def print_status(ctx, agents_dir=None):
    word, lines = compute_status(ctx, agents_dir)
    print(word)
    for ln in lines:
        print(ln)
    return 0 if word == "INSTALLED" else 1


def cmd_status(ctx, args):
    return print_status(ctx, getattr(args, "launch_agents_dir", None))


def copy_if_missing(src, dst, label):
    if dst.exists():
        print("skipped: %s already exists" % label)
    elif not src.is_file():
        print("skipped: %s not created, template %s is missing" % (label, src.name))
    else:
        shutil.copyfile(str(src), str(dst))
        print("done: created %s from %s" % (label, src.name))


def read_run_hour(ctx):
    cfg = ctx.home / "config.json"
    hour = 10
    if cfg.is_file():
        data = read_json(cfg, "config.json")
        if isinstance(data, dict) and "run_hour" in data:
            hour = data["run_hour"]
    if isinstance(hour, bool) or not isinstance(hour, int) or not 0 <= hour <= 23:
        raise QuartermasterError("config.json: run_hour must be a whole number from 0 to 23, got %r" % (hour,))
    return hour


def cron_rewrite(current, run_py, hour, line):
    """Return (new crontab text, action). action: add, changed or same.
    A Quartermaster line is any non-comment line that runs quartermaster/run_headless.py or this run_py."""
    lines = current.splitlines()
    found = False
    changed = False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("#"):
            continue
        if "quartermaster/run_headless.py" not in ln and str(run_py) not in ln:
            continue
        parts = ln.split(None, 5)
        if len(parts) < 6:
            continue
        found = True
        if parts[1] != str(hour):
            parts[1] = str(hour)
            lines[i] = " ".join(parts)
            changed = True
    if found:
        return ("\n".join(lines) + "\n", "changed") if changed else (current, "same")
    new = "\n".join(lines) + "\n" if lines else ""
    return new + line + "\n", "add"


def install_job(ctx, hour, agents_dir, no_launchctl):
    run_py = ctx.home / "run_headless.py"
    if not run_py.is_file():
        print("skipped: daily job not installed, %s is missing (copy the repo's job folder first)" % run_py)
        return
    if sys.platform == "darwin":
        agents = Path(agents_dir) if agents_dir else Path.home() / "Library" / "LaunchAgents"
        plist_path = agents / (LABEL + ".plist")
        user_home = str(Path.home())
        python_exe = sys.executable or "/usr/bin/python3"
        plist = {
            "Label": LABEL,
            "ProgramArguments": [python_exe, str(run_py)],
            "WorkingDirectory": str(ctx.home),
            "StartCalendarInterval": {"Hour": hour, "Minute": 0},
            "EnvironmentVariables": {
                "HOME": user_home,
                "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:%s/.local/bin" % user_home,
            },
            "StandardOutPath": str(ctx.runtime / "launchd.out.log"),
            "StandardErrorPath": str(ctx.runtime / "launchd.err.log"),
        }
        data = plistlib.dumps(plist)
        same = plist_path.is_file() and plist_path.read_bytes() == data
        loaded = False
        if not no_launchctl:
            loaded = run_cmd(["launchctl", "print", "gui/%d/%s" % (os.getuid(), LABEL)]).returncode == 0
        if same and (loaded or no_launchctl):
            print("skipped: %s is already written%s (Python used: %s)" % (
                plist_path, " and loaded" if loaded else "", python_exe))
            return
        agents.mkdir(parents=True, exist_ok=True)
        plist_path.write_bytes(data)
        print("done: wrote %s (daily at %02d:00, Python used: %s)" % (plist_path, hour, python_exe))
        if no_launchctl:
            print("skipped: launchctl bootstrap (--no-launchctl)")
            return
        domain = "gui/%d" % os.getuid()
        run_cmd(["launchctl", "bootout", "%s/%s" % (domain, LABEL)])  # failure is fine: not loaded yet
        r = run_cmd(["launchctl", "bootstrap", domain, str(plist_path)])
        if r.returncode == 0:
            print("done: launchctl bootstrap %s %s" % (domain, LABEL))
        else:
            print("FAILED: launchctl bootstrap %s: %s" % (LABEL, (r.stderr or r.stdout).strip()))
        return
    line = "0 %d * * * %s %s" % (hour, sys.executable, run_py)
    if sys.platform.startswith("linux"):
        r = run_cmd(["crontab", "-l"])
        current = r.stdout if r.returncode == 0 else ""
        new, action = cron_rewrite(current, run_py, hour, line)
        if action == "same":
            print("skipped: crontab already has a line for run_headless.py at hour %d" % hour)
            return
        try:
            w = subprocess.run(["crontab", "-"], input=new, universal_newlines=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            print("FAILED: could not run crontab (%s). Add this line yourself:\n%s" % (e, line))
            return
        if w.returncode == 0:
            if action == "changed":
                print("done: crontab hour changed to %d" % hour)
            else:
                print("done: added crontab line: %s" % line)
        else:
            print("FAILED: crontab said: %s\nAdd this line yourself:\n%s" % (w.stderr.strip(), line))
        return
    print("skipped: this system has no launchd or crontab support here. Add this line to your scheduler yourself:")
    print(line)


def cmd_setup(ctx, args):
    for d in (ctx.home, ctx.runtime, ctx.runtime / "reports"):
        if d.is_dir():
            print("skipped: folder exists: %s" % d)
        else:
            d.mkdir(parents=True, exist_ok=True)
            print("done: created folder %s" % d)
    copy_if_missing(ctx.home / "ROUTING.local.example.md", ctx.home / "ROUTING.local.md", "ROUTING.local.md")
    copy_if_missing(ctx.home / "config.example.json", ctx.home / "config.json", "config.json")
    lessons = ctx.home / "LESSONS.md"
    if lessons.exists():
        print("skipped: LESSONS.md already exists")
    else:
        lessons.write_text("# LESSONS\n", encoding="utf-8")
        print("done: created LESSONS.md")

    snap_out = ctx.runtime / "skill-models.json"
    snap_script = ctx.home / "snapshot_skill_models.py"
    if snap_out.is_file():
        print("skipped: runtime/skill-models.json already exists")
    elif not snap_script.is_file():
        print("skipped: skill snapshot, %s is missing" % snap_script)
    else:
        env = dict(os.environ)
        env["QUARTERMASTER_HOME"] = str(ctx.home)
        r = run_cmd([sys.executable, str(snap_script), "--write", "--home", str(ctx.home)], env=env, cwd=str(ctx.home))
        if r.returncode != 0:
            print("FAILED: snapshot_skill_models.py: %s" % (r.stderr.strip() or r.stdout.strip()))
        elif snap_out.is_file():
            print("done: skill snapshot written (%s)" % (r.stdout.strip().splitlines() or [""])[-1])
        else:
            print("warning: snapshot_skill_models.py ran but did not write %s" % snap_out)

    hour = read_run_hour(ctx)
    install_job(ctx, hour, args.launch_agents_dir, args.no_launchctl)
    print("")
    return print_status(ctx, args.launch_agents_dir)


def cmd_help(ctx, args):
    sys.stdout.write(HELP_TEXT)
    return 0


# ----------------------------------------------------------------------------- main


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--home", default=argparse.SUPPRESS,
                        help="Quartermaster home folder (default ~/.claude/quartermaster)")
    common.add_argument("--projects", default=argparse.SUPPRESS,
                        help="Claude projects folder holding agent transcripts (default ~/.claude/projects)")
    p = Parser(prog="quartermaster.py", description="Quartermaster, the model allocator.", parents=[common])
    sub = p.add_subparsers(dest="cmd", parser_class=Parser)
    sub.required = True

    s = sub.add_parser("status", parents=[common], help="show whether Quartermaster is installed")
    s.add_argument("--launch-agents-dir", default=None, help=argparse.SUPPRESS)
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("setup", parents=[common], help="create folders and files, install the daily job")
    s.add_argument("--launch-agents-dir", default=None, help="macOS only: where to write the plist (default ~/Library/LaunchAgents)")
    s.add_argument("--no-launchctl", action="store_true", help="macOS only: write the plist but do not call launchctl")
    s.set_defaults(func=cmd_setup)

    s = sub.add_parser("board", parents=[common], help="print the board")
    s.add_argument("--pieces", required=True, help="JSON list of pieces")
    s.set_defaults(func=cmd_board)

    s = sub.add_parser("record", parents=[common], help="print board and scorecard, log the run")
    s.add_argument("--task", required=True)
    s.add_argument("--type", required=True, help="routing row name")
    s.add_argument("--size", required=True, choices=["S", "M", "L"])
    s.add_argument("--stakes", required=True, choices=["low", "high"])
    s.add_argument("--pieces", required=True, help="JSON list of pieces; agent_id required for done pieces")
    s.add_argument("--checked-by", required=True, choices=TIERS + ["none"])
    s.set_defaults(func=cmd_record)

    s = sub.add_parser("help", parents=[common], help="print the help text")
    s.set_defaults(func=cmd_help)
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    ctx = Ctx(getattr(args, "home", None), getattr(args, "projects", None))
    try:
        return args.func(ctx, args)
    except QuartermasterError as e:
        sys.stderr.write("quartermaster: error: %s\n" % e)
        return 1
    except BrokenPipeError:
        return 0
    except OSError as e:
        sys.stderr.write("quartermaster: error: %s\n" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
