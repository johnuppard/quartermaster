#!/usr/bin/env python3
"""Quartermaster helper: status, setup, context, handover, resume, board, record, help.

Python 3.9+, standard library only. Installed to ~/.claude/quartermaster/quartermaster.py.
All runtime files live under <home>/runtime/. Use --home <path> to work in another folder
(for tests). Transcripts are read from ~/.claude/projects unless --projects is given.
"""
import argparse
import contextlib
import datetime
import glob
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

try:
    import fcntl
except ImportError:  # not available on Windows: records are then written without a lock
    fcntl = None

TIERS = ["fable", "opus", "sonnet", "haiku"]  # fixed board order
ROLES = ["work", "plan", "check", "assemble"]
OUTCOMES = ["done", "escalated", "failed"]
STATUSES = ["planned", "running", "done", "escalated", "failed"]
NOT_NEEDED = "not needed for this task"
IDLE_CAP = 120.0  # a gap between two records in a transcript counts at most this many seconds
DEFAULT_THRESHOLD_TOKENS = 150000

HELP_TEXT = """Quartermaster help
- What it is for: a separate check on every deliverable, and a lean chat thread. Every task goes to one agent plus a check, so it adds only a check, a short handover and the foreman's few calls. Work is split across cheaper models only when it cannot fit one agent's context, because the benchmark measured splitting at two to three times the cost of one Opus agent on file-reading tasks.
- What it costs: every agent carries roughly 100,000 tokens of start-up context on a typical setup, so small work goes to one agent plus a check. Routing was measured to cost more than one Opus agent on file-reading tasks; see benchmark/BENCHMARK.md in the repository.
- Quality: every deliverable is checked by a separate agent. Quality is protected by that check and is never traded for tokens.
- The lean thread: a handover is written at the end of every task, and a fresh chat is used when this one carries more than 150,000 tokens into every turn (the limit is context_threshold_tokens in config.json). Type /quartermaster resume to continue.
- The scorecard: it prints tokens used by model (output is counted as at least), the overhead of planning, checks and the foreman, the list price of the run, the time won, and the totals recorded so far. It shows what was used and what it cost at list price. Dollar figures are Anthropic API list-price estimates, not a bill. How your subscription weighs tokens is not published.
- Commands: /quartermaster <task>, /quartermaster review <task> (optional review, seven or more extra agents, waits for your yes), /quartermaster resume, /quartermaster help, /quartermaster lesson: <feedback>. Say "Fable for piece 2" to use the top model for one piece.
- Limits: it cannot change the session model, and it does not fire by itself. You start it by typing /quartermaster.
- Extras: the optional review and the daily self-review live in the repository's extras folder, with their cost stated. They are off unless installed.
"""


class QuartermasterError(Exception):
    """Bad input or a broken installation. Printed as one line, exit code 1."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("quartermaster: error: %s\n" % message)
        sys.exit(1)


# ----------------------------------------------------------------------------- paths and files


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


@contextlib.contextmanager
def run_lock(ctx):
    """Exclusive lock so two record calls at the same time cannot overwrite each other."""
    ctx.runtime.mkdir(parents=True, exist_ok=True)
    if fcntl is None:
        yield
        return
    fh = open(str(ctx.runtime / ".lock"), "a")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fh, fcntl.LOCK_UN)
        finally:
            fh.close()


def load_config(ctx):
    """Return (threshold_tokens, window). window is None unless config.json sets context_window (display only).
    A missing or damaged config.json gives the default threshold and no window."""
    threshold, window = DEFAULT_THRESHOLD_TOKENS, None
    path = ctx.home / "config.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            data = None
        if isinstance(data, dict):
            t = data.get("context_threshold_tokens")
            if isinstance(t, (int, float)) and not isinstance(t, bool) and t > 0:
                threshold = int(t)
            w = data.get("context_window")
            if isinstance(w, (int, float)) and not isinstance(w, bool) and w > 0:
                window = int(w)
    return threshold, window


def clean(text):
    """Printed text never carries em or en dashes."""
    return str(text).replace(chr(0x2014), "-").replace(chr(0x2013), "-")


# ----------------------------------------------------------------------------- time and models


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


def active_seconds(stamps):
    """Sum of the gaps between consecutive records, each gap capped at IDLE_CAP seconds."""
    s = sorted(stamps)
    total = 0.0
    for a, b in zip(s, s[1:]):
        total += min((b - a).total_seconds(), IDLE_CAP)
    return total


# ----------------------------------------------------------------------------- transcripts


def find_transcript(ctx, agent_id):
    """The agent transcript under <projects>/<folder>/<session>/subagents/[workflows/<wf>/]agent-<id>.jsonl.
    If the same id exists in more than one session, the largest file wins (then the newest path)."""
    pattern = str(ctx.projects / "*" / "*" / "subagents" / "**" / ("agent-%s.jsonl" % agent_id))
    hits = glob.glob(pattern, recursive=True)
    if not hits:
        return None
    hits.sort(key=lambda p: (os.path.getsize(p), p))
    return hits[-1]


def main_transcript_for(agent_path):
    """<root>/<session>/subagents/.../agent-x.jsonl  ->  <root>/<session>.jsonl (or None)."""
    for parent in Path(agent_path).parents:
        if parent.name == "subagents":
            session_dir = parent.parent
            main = session_dir.parent / (session_dir.name + ".jsonl")
            return main if main.is_file() else None
    return None


def read_usage(path, only_usage=False):
    """Read one transcript. Returns dict(messages, stamps).

    The transcript writes one record per content block, so one API message appears several
    times with the same message.id and the same usage. Records are grouped by message.id and
    the largest value of each field is kept: one count per message. Input and cache fields
    are exact. The recorded output count is only final on the record that has a stop reason,
    and most subagent records are an early snapshot, so output is a floor: for every message
    it is max(recorded, (characters of assistant text + json.dumps of every tool_use input) // 4).
    Records without a message id are counted one by one.
    only_usage=True skips records that do not mention usage (used for the long main transcript).
    """
    by_id = {}
    seen_blocks = {}
    stamps = []
    anon = 0
    with open(str(path), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if only_usage and '"usage"' not in line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            if only_usage and rec.get("isSidechain"):
                continue
            ts = parse_ts(rec.get("timestamp"))
            if ts is not None and not only_usage:
                stamps.append(ts)
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
            cur = by_id.get(mid)
            if cur is None:
                cur = {"id": mid, "model": None, "ts": ts, "input": 0, "cache_write": 0, "cache_read": 0,
                       "output": 0, "chars": 0}
                by_id[mid] = cur
                seen_blocks[mid] = set()
            if ts is not None and (cur["ts"] is None or ts < cur["ts"]):
                cur["ts"] = ts
            for key, field in (("input", "input_tokens"), ("cache_write", "cache_creation_input_tokens"),
                               ("cache_read", "cache_read_input_tokens"), ("output", "output_tokens")):
                v = usage.get(field) or 0
                if isinstance(v, (int, float)) and not isinstance(v, bool) and v > cur[key]:
                    cur[key] = int(v)
            model = msg.get("model")
            if cur["model"] is None and isinstance(model, str) and model and not model.startswith("<"):
                cur["model"] = model
            cur["chars"] += content_chars(msg.get("content"), seen_blocks[mid])
    messages = []
    for cur in by_id.values():
        cur["output"] = max(cur["output"], cur["chars"] // 4)
        messages.append(cur)
    return {"messages": messages, "stamps": stamps}


def content_chars(content, seen):
    """Characters of assistant text plus json.dumps of tool_use inputs; a block seen twice counts once."""
    n = 0
    if isinstance(content, str):
        key = ("s", hash(content))
        if key not in seen:
            seen.add(key)
            n += len(content)
        return n
    if not isinstance(content, list):
        return 0
    for block in content:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind == "text" and isinstance(block.get("text"), str):
            key = ("t", hash(block["text"]))
            if key not in seen:
                seen.add(key)
                n += len(block["text"])
        elif kind == "tool_use":
            try:
                body = json.dumps(block.get("input"), ensure_ascii=False)
            except (TypeError, ValueError):
                body = ""
            key = ("u", block.get("id") or hash(body))
            if key not in seen:
                seen.add(key)
                n += len(body)
    return n


# ----------------------------------------------------------------------------- prices


def load_prices(ctx):
    path = ctx.home / "prices.json"
    data = read_json(path, "prices.json")
    if not isinstance(data, dict):
        raise QuartermasterError("prices.json is not an object: %s" % path)
    for t in TIERS:
        row = data.get(t)
        if not isinstance(row, dict):
            raise QuartermasterError("prices.json has no entry for %s: %s" % (t, path))
        for k in ("in", "out", "cache_read", "cache_write"):
            if not isinstance(row.get(k), (int, float)) or isinstance(row.get(k), bool):
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
    the input price."""
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


def msg_total(m):
    return m["input"] + m["cache_write"] + m["cache_read"] + m["output"]


def price_messages(messages, prices, fallback_tier):
    """Return dict(cost, cost_fable, cost_opus, by_tier, fallback_count). Each message is priced by its own model."""
    out = {"cost": 0.0, "cost_fable": 0.0, "cost_opus": 0.0, "by_tier": {}, "fallback": 0}
    for m in messages:
        tier = tier_of(m["model"])
        if tier is None:
            tier = fallback_tier
            out["fallback"] += 1
        out["cost"] += cost_of(m, prices[tier])
        out["cost_fable"] += cost_of(m, prices["fable"])
        out["cost_opus"] += cost_of(m, prices["opus"])
        out["by_tier"][tier] = out["by_tier"].get(tier, 0) + msg_total(m)
    return out


# ----------------------------------------------------------------------------- pieces


def parse_pieces(text, for_record):
    try:
        pieces = json.loads(text)
    except ValueError as e:
        raise QuartermasterError("--pieces is not valid JSON: %s" % e)
    if not isinstance(pieces, list) or not pieces:
        raise QuartermasterError("--pieces must be a non-empty JSON list of objects")
    out = []
    seen_agents = {}
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
        role = p.get("role", "work")
        if role not in ROLES:
            raise QuartermasterError("%s (%s): \"role\" must be one of %s, got %r" % (label, name, "|".join(ROLES), role))
        outcome = p.get("outcome")
        if outcome is not None and outcome not in OUTCOMES:
            raise QuartermasterError("%s (%s): \"outcome\" must be one of %s, got %r" % (label, name, "|".join(OUTCOMES), outcome))
        status = p.get("status")
        if status is not None and status not in STATUSES:
            raise QuartermasterError("%s (%s): \"status\" must be one of %s, got %r" % (label, name, "|".join(STATUSES), status))
        agent = p.get("agent_id")
        if agent is not None:
            if not isinstance(agent, str) or not re.match(r"^[A-Za-z0-9_-]+$", agent):
                raise QuartermasterError("%s (%s): \"agent_id\" must be a plain id like a67c9a9090265454e, got %r" % (label, name, agent))
            if agent in seen_agents:
                raise QuartermasterError("agent_id %s is used by both \"%s\" and \"%s\". One agent is one piece "
                                         "(a resumed agent is still one piece, and a step-up is a new agent). Nothing was recorded."
                                         % (agent, seen_agents[agent], name))
            seen_agents[agent] = name
        if for_record:
            if not agent:
                raise QuartermasterError("%s (%s) has no \"agent_id\"; record needs it to read the real token usage" % (label, name))
            outcome = outcome or "done"
            status = outcome
        else:
            status = status or outcome or "planned"
            outcome = outcome or (status if status in OUTCOMES else None)
        out.append({"piece": name.strip(), "model": model, "role": role, "outcome": outcome,
                    "status": status, "agent_id": agent or None})
    return out


def measure(ctx, p, prices):
    """Attach usage to a piece: found, path, tokens, total, active, first, last, ran_on, cost... ."""
    p.update({"found": None, "path": None, "tokens": None, "total": 0, "active": None,
              "first": None, "last": None, "messages": None, "ran_on": None, "priced": None})
    if not p["agent_id"]:
        return p
    path = find_transcript(ctx, p["agent_id"])
    p["found"] = bool(path)
    if not path:
        return p
    p["path"] = path
    u = read_usage(path)
    msgs = u["messages"]
    tokens = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    for m in msgs:
        for k in tokens:
            tokens[k] += m[k]
    p["messages"] = msgs
    p["tokens"] = tokens
    p["total"] = sum(tokens.values())
    if u["stamps"]:
        p["first"], p["last"] = min(u["stamps"]), max(u["stamps"])
        p["active"] = active_seconds(u["stamps"])
    by_tier = {}
    for m in msgs:
        t = tier_of(m["model"])
        if t:
            by_tier[t] = by_tier.get(t, 0) + msg_total(m)
    p["ran_on"] = max(by_tier, key=lambda t: by_tier[t]) if by_tier else None
    if prices is not None:
        p["priced"] = price_messages(msgs, prices, p["model"])
    return p


# ----------------------------------------------------------------------------- formatting


def fmt_tokens(p):
    if p["agent_id"] is None:
        return "-"
    if not p["found"] or not p["messages"]:
        return "?"
    return "{:,}".format(p["total"])


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
    if not p["found"] or p["active"] is None:
        return "?"
    return fmt_seconds(p["active"])


def cell(text):
    return clean(str(text).replace("|", "/").replace("\r", " ").replace("\n", " ").strip())


def usd(x):
    x = float(x)
    if round(x, 2) == 0:
        return "$0.00"
    return "%s$%.2f" % ("-" if x < 0 else "", abs(x))


def plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def board_text(pieces):
    lines = ["Quartermaster board", "", "| Model | Piece | Status | Tokens | Time |", "|---|---|---|---|---|"]
    for tier in TIERS:
        group = [p for p in pieces if p["model"] == tier]
        if not group:
            lines.append("| %s | %s | - | - | - |" % (tier.capitalize(), NOT_NEEDED))
            continue
        for p in group:
            model_cell = tier.capitalize()
            if p["ran_on"] and p["ran_on"] != tier:
                model_cell += " (ran on %s)" % p["ran_on"].capitalize()
            piece_cell = p["piece"]
            if p["role"] != "work":
                piece_cell += " (%s)" % p["role"]
            lines.append("| %s | %s | %s | %s | %s |" % (
                cell(model_cell), cell(piece_cell), cell(p["status"]), fmt_tokens(p), fmt_time(p)))
    return "\n".join(lines)


# ----------------------------------------------------------------------------- board and record


def cmd_board(ctx, args):
    pieces = parse_pieces(args.pieces, for_record=False)
    for p in pieces:
        measure(ctx, p, None)
    print(board_text(pieces))
    return 0


def foreman_usage(ctx, prices, pieces):
    """Price the main session's own assistant messages between the earliest and latest agent timestamp.
    Returns (cost, tokens, found)."""
    windows = {}
    for p in pieces:
        if not p["path"] or p["first"] is None:
            continue
        main = main_transcript_for(p["path"])
        if main is None:
            continue
        lo, hi = windows.get(str(main), (p["first"], p["last"]))
        windows[str(main)] = (min(lo, p["first"]), max(hi, p["last"]))
    if not windows:
        return 0.0, 0, False
    cost = 0.0
    tokens = 0
    for main, (lo, hi) in windows.items():
        u = read_usage(main, only_usage=True)
        inside = [m for m in u["messages"] if m["ts"] is not None and lo <= m["ts"] <= hi]
        priced = price_messages(inside, prices, "opus")
        cost += priced["cost"]
        tokens += sum(msg_total(m) for m in inside)
    return cost, tokens, True


def cmd_record(ctx, args):
    pieces = parse_pieces(args.pieces, for_record=True)
    checked_by = args.checked_by.strip()
    if checked_by != "none" and not re.match(r"^[A-Za-z0-9_-]+$", checked_by):
        raise QuartermasterError("--checked-by must be the verifier's agent id or none, got %r" % checked_by)
    prices = load_prices(ctx)
    for p in pieces:
        measure(ctx, p, prices)
        if not p["found"]:
            raise QuartermasterError("no transcript found for agent %s (piece: %s). Searched %s. "
                                     "Check the agent id; nothing was recorded." % (p["agent_id"], p["piece"], ctx.projects))
        if not p["messages"]:
            raise QuartermasterError("the transcript of agent %s (piece: %s) holds no usage yet (still running?); "
                                     "nothing was recorded." % (p["agent_id"], p["piece"]))
    if checked_by != "none" and checked_by not in [p["agent_id"] for p in pieces]:
        sys.stderr.write("quartermaster: warning: checked-by agent %s is not in --pieces, so its tokens are not counted\n"
                         % checked_by)
    fallback = sum(p["priced"]["fallback"] for p in pieces)
    if fallback:
        sys.stderr.write("quartermaster: warning: %d message(s) had no known model name and were priced as their piece's tier\n"
                         % fallback)

    # tokens, by model
    tok = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    by_tier = {}
    for p in pieces:
        for k in tok:
            tok[k] += p["tokens"][k]
        for t, n in p["priced"]["by_tier"].items():
            by_tier[t] = by_tier.get(t, 0) + n
    total_tokens = sum(tok.values())

    # dollars
    cost_pieces = sum(p["priced"]["cost"] for p in pieces)
    cost_plan = sum(p["priced"]["cost"] for p in pieces if p["role"] == "plan")
    cost_check = sum(p["priced"]["cost"] for p in pieces if p["role"] == "check")
    foreman_cost, foreman_tokens, foreman_found = foreman_usage(ctx, prices, pieces)
    overhead = cost_plan + cost_check + foreman_cost
    run_total = cost_pieces + foreman_cost
    overhead_pct = (overhead * 100.0 / run_total) if run_total > 0 else 0.0

    # time
    active = sum(p["active"] for p in pieces if p["active"] is not None)
    firsts = [p["first"] for p in pieces if p["first"] is not None]
    lasts = [p["last"] for p in pieces if p["last"] is not None]
    elapsed = (max(lasts) - min(firsts)).total_seconds() if firsts and lasts else 0.0
    time_won = active - elapsed
    has_win = elapsed >= 60 and time_won >= 60

    ts = now_utc()
    run = {
        "ts": iso(ts), "task": args.task, "type": args.type, "size": args.size, "stakes": args.stakes,
        "checked_by": checked_by, "cwd": os.getcwd(),
        "pieces": [{
            "piece": p["piece"], "model": p["model"], "role": p["role"], "outcome": p["outcome"],
            "agent_id": p["agent_id"], "ran_on": p["ran_on"], "tokens": p["tokens"], "tokens_total": p["total"],
            "active_seconds": None if p["active"] is None else round(p["active"], 1),
            "first": None if p["first"] is None else iso(p["first"]),
            "last": None if p["last"] is None else iso(p["last"]),
            "cost": round(p["priced"]["cost"], 6),
        } for p in pieces],
        "tokens": tok, "tokens_total": total_tokens, "tokens_by_model": by_tier,
        "cost_pieces": round(cost_pieces, 6), "cost_plan": round(cost_plan, 6), "cost_checks": round(cost_check, 6),
        "cost_foreman": round(foreman_cost, 6), "foreman_found": foreman_found, "foreman_tokens": foreman_tokens,
        "overhead": round(overhead, 6), "overhead_pct": round(overhead_pct, 1), "run_total": round(run_total, 6),
        "active_seconds": round(active, 1), "elapsed_seconds": round(elapsed, 1),
        "time_won_seconds": round(time_won, 1) if has_win else 0.0,
    }

    # scoreboard first (validated), then runs.jsonl, both under one lock
    sb_path = ctx.runtime / "scoreboard.json"
    with run_lock(ctx):
        sb = {}
        if sb_path.exists():
            sb = read_json(sb_path, "scoreboard.json")
        try:
            if not isinstance(sb, dict):
                raise TypeError("not an object")
            runs_n = int(sb.get("runs", 0)) + 1
            tokens_n = int(sb.get("total_tokens", 0)) + total_tokens
            price_n = round(float(sb.get("total_list_price", 0.0)) + run_total, 6)
        except (TypeError, ValueError, AttributeError) as e:
            raise QuartermasterError("scoreboard.json is damaged (%s): %s" % (e, sb_path))
        sb.pop("running_net", None)
        sb.pop("best_run", None)
        sb["runs"], sb["total_tokens"], sb["total_list_price"], sb["updated"] = runs_n, tokens_n, price_n, run["ts"]
        write_json_atomic(sb_path, sb)
        with open(str(ctx.runtime / "runs.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(run, ensure_ascii=False) + "\n")

    out = [board_text(pieces), ""]
    if not foreman_found:
        out.append("foreman: not found (counted as 0)")
    out.append("Used: {:,} tokens by {} (input {:,}, cache write {:,}, cache read {:,}, output at least {:,}). By model: {}.".format(
        total_tokens, plural(len(pieces), "agent"), tok["input"], tok["cache_write"], tok["cache_read"], tok["output"],
        ", ".join("%s {:,}".format(by_tier.get(t, 0)) % t.capitalize()
                  for t in ["opus", "sonnet", "haiku"] + (["fable"] if by_tier.get("fable") else []))))
    out.append("Overhead: plan %s, checks %s, foreman %s, together %s (%.0f%% of this run)." % (
        usd(cost_plan), usd(cost_check), usd(foreman_cost), usd(overhead), overhead_pct))
    out.append("List price of this run (estimate, not a bill): %s" % usd(run_total))
    if has_win:
        out.append("Time won: %.1f minutes (active %.1f, elapsed %.1f)" % (time_won / 60.0, active / 60.0, elapsed / 60.0))
    else:
        out.append("No time won (under a minute)")
    out.append("Recorded so far: %s, {:,} tokens, %s at list price.".format(tokens_n) % (plural(runs_n, "run"), usd(price_n)))
    out.append("How your subscription weighs these tokens is not published. Routing was measured to cost more than one Opus agent on file-reading tasks; see benchmark/BENCHMARK.md.")
    print("\n".join(out))
    return 0


# ----------------------------------------------------------------------------- context, handover, resume


def encode_cwd(path):
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def main_transcripts(folder):
    try:
        return [f for f in folder.glob("*.jsonl") if f.is_file()]
    except OSError:
        return []


def newest(files):
    best, best_m = None, -1.0
    for f in files:
        try:
            m = f.stat().st_mtime
        except OSError:
            continue
        if m > best_m:
            best, best_m = f, m
    return best


def find_session_transcript(ctx):
    """Newest main transcript of the project folder for the current directory; else the newest anywhere."""
    names = set()
    for cwd in (os.getcwd(), os.environ.get("PWD")):
        if cwd:
            names.add(encode_cwd(cwd))
            names.add(re.sub(r"[/ @]", "-", cwd))  # the narrower rule, in case a folder name keeps its dots
    for name in sorted(names):
        hit = newest(main_transcripts(ctx.projects / name))
        if hit:
            return hit
    if ctx.projects.is_dir():
        files = []
        for folder in ctx.projects.iterdir():
            if folder.is_dir():
                files.extend(main_transcripts(folder))
        return newest(files)
    return None


def last_prompt_size(path):
    """Prompt size (input + cache write + cache read) of the last assistant message, reading from the end."""
    with open(str(path), "rb") as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        buf = b""
        while pos > 0:
            step = min(1 << 20, pos)
            pos -= step
            f.seek(pos)
            buf = f.read(step) + buf
            lines = buf.split(b"\n")
            start = 0 if pos == 0 else 1
            for raw in reversed(lines[start:]):
                if b'"usage"' not in raw:
                    continue
                try:
                    rec = json.loads(raw.decode("utf-8", errors="replace"))
                except ValueError:
                    continue
                if not isinstance(rec, dict) or rec.get("isSidechain"):
                    continue
                msg = rec.get("message")
                if not isinstance(msg, dict) or msg.get("role") != "assistant":
                    continue
                usage = msg.get("usage")
                if not isinstance(usage, dict):
                    continue
                model = msg.get("model")
                if isinstance(model, str) and model.startswith("<"):
                    continue
                n = 0
                for field in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
                    v = usage.get(field) or 0
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
                        n += int(v)
                if n > 0:
                    return n
            buf = lines[0] if pos > 0 else b""
    return None


def cmd_context(ctx, args):
    threshold, window = load_config(ctx)
    path = find_session_transcript(ctx)
    size = None
    if path is not None:
        try:
            size = last_prompt_size(path)
        except OSError:
            size = None
    if size is None:
        print("Context: unknown")
        print("BELOW")
        return 0
    line = "Context: this chat carries about {:,} tokens into every turn. Threshold {:,}.".format(size, threshold)
    if window:
        line += " (About {:.0f} percent of a {:,} token window.)".format(size * 100.0 / window, window)
    print(line)
    print("ABOVE" if size > threshold else "BELOW")
    return 0


def cmd_handover(ctx, args):
    path = ctx.runtime / "handover.md"
    ctx.runtime.mkdir(parents=True, exist_ok=True)
    text = "\n".join([
        "# Handover", "",
        "Written: %s" % iso(now_utc()), "",
        "## Task", args.task.strip(), "",
        "## State", args.state.strip(), "",
        "## Files", args.files.strip(), "",
        "## Next step", args.next.strip(), ""])
    fd, tmp = tempfile.mkstemp(dir=str(ctx.runtime), prefix="handover.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, str(path))
    print(path)
    return 0


def cmd_resume(ctx, args):
    path = ctx.runtime / "handover.md"
    if not path.is_file():
        print("No handover found.")
        return 0
    sys.stdout.write(path.read_text(encoding="utf-8"))
    return 0


# ----------------------------------------------------------------------------- status and setup


def compute_status(ctx):
    """Return (word, lines, missing). NOT INSTALLED: no home folder, or none of its files."""
    if not ctx.home.is_dir():
        return "NOT INSTALLED", ["home folder: missing (%s)" % ctx.home], 1
    items = [
        ("ROUTING.md", ctx.home / "ROUTING.md", "file"),
        ("ROUTING.local.md", ctx.home / "ROUTING.local.md", "file"),
        ("LESSONS.md", ctx.home / "LESSONS.md", "file"),
        ("config.json", ctx.home / "config.json", "file"),
        ("prices.json", ctx.home / "prices.json", "file"),
        ("runtime folder", ctx.runtime, "dir"),
    ]
    lines = ["home folder: %s" % ctx.home]
    missing = 0
    present_files = 0
    for name, path, kind in items:
        ok = path.is_dir() if kind == "dir" else path.is_file()
        lines.append("%s: %s" % (name, "present" if ok else "MISSING"))
        if not ok:
            missing += 1
        elif kind == "file":
            present_files += 1
    handover = ctx.runtime / "handover.md"
    lines.append("handover: %s" % ("present (%s)" % handover if handover.is_file() else "none"))
    if present_files == 0:
        return "NOT INSTALLED", lines, missing
    return ("INSTALLED" if missing == 0 else "INCOMPLETE"), lines, missing


def cmd_status(ctx, args):
    word, lines, _ = compute_status(ctx)
    print(word)
    for ln in lines:
        print(ln)
    return 0 if word == "INSTALLED" else 1


def make_dir(path, label):
    if path.is_dir():
        print("kept: %s" % label)
    else:
        path.mkdir(parents=True, exist_ok=True)
        print("created: %s" % label)


def copy_if_missing(src, dst, label):
    if dst.exists():
        print("kept: %s" % label)
    elif not src.is_file():
        print("not created: %s (template %s is missing)" % (label, src.name))
    else:
        shutil.copyfile(str(src), str(dst))
        print("created: %s" % label)


def cmd_setup(ctx, args):
    make_dir(ctx.home, "home folder")
    make_dir(ctx.runtime, "runtime folder")
    copy_if_missing(ctx.home / "ROUTING.local.example.md", ctx.home / "ROUTING.local.md", "ROUTING.local.md")
    copy_if_missing(ctx.home / "config.example.json", ctx.home / "config.json", "config.json")
    lessons = ctx.home / "LESSONS.md"
    if lessons.exists():
        print("kept: LESSONS.md")
    else:
        lessons.write_text("# LESSONS\n", encoding="utf-8")
        print("created: LESSONS.md")
    word, lines, _ = compute_status(ctx)
    print("")
    if word != "INSTALLED":
        print("Setup is not complete. Status: %s" % word)
        for ln in lines:
            if "MISSING" in ln:
                print("  " + ln)
        print("Run install.sh from the repository to copy the missing files, then run setup again.")
        return 1
    print("Quartermaster is set up and ready.")
    print("Status: INSTALLED")
    print("Extras (optional review, daily self-review) are installed separately from the repository's extras folder.")
    return 0


def cmd_help(ctx, args):
    sys.stdout.write(HELP_TEXT)
    return 0


# ----------------------------------------------------------------------------- main


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--home", default=argparse.SUPPRESS,
                        help="Quartermaster home folder (default ~/.claude/quartermaster)")
    common.add_argument("--projects", default=argparse.SUPPRESS,
                        help="Claude projects folder holding transcripts (default ~/.claude/projects)")
    p = Parser(prog="quartermaster.py", description="Quartermaster, the model allocator.", parents=[common])
    sub = p.add_subparsers(dest="cmd", parser_class=Parser)
    sub.required = True

    s = sub.add_parser("status", parents=[common], help="show whether Quartermaster is installed")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("setup", parents=[common], help="create folders and files")
    s.set_defaults(func=cmd_setup)

    s = sub.add_parser("context", parents=[common], help="print what this chat carries into every turn (ABOVE or BELOW the token threshold)")
    s.set_defaults(func=cmd_context)

    s = sub.add_parser("handover", parents=[common], help="write runtime/handover.md")
    s.add_argument("--task", required=True)
    s.add_argument("--state", required=True)
    s.add_argument("--files", required=True)
    s.add_argument("--next", required=True)
    s.set_defaults(func=cmd_handover)

    s = sub.add_parser("resume", parents=[common], help="print the handover")
    s.set_defaults(func=cmd_resume)

    s = sub.add_parser("board", parents=[common], help="print the board")
    s.add_argument("--pieces", required=True, help="JSON list of pieces")
    s.set_defaults(func=cmd_board)

    s = sub.add_parser("record", parents=[common], help="print board and scorecard, log the run")
    s.add_argument("--task", required=True)
    s.add_argument("--type", required=True, help="routing row name")
    s.add_argument("--size", required=True, choices=["S", "M", "L"])
    s.add_argument("--stakes", required=True, choices=["low", "high"])
    s.add_argument("--pieces", required=True, help="JSON list: piece, model, agent_id, role, outcome")
    s.add_argument("--checked-by", required=True, help="the verifier's agent id, or none")
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
