# Quartermaster

A Claude Code skill that runs large, splittable tasks as parallel pieces on cheaper models, checks every deliverable with a separate agent, and prints only what it measured.

## What it does and does not do

**Large work.** When a task is large and splits into pieces that do not need each other's results, Quartermaster runs the pieces in parallel, each on the cheapest model that does that kind of piece well according to its routing table, and a separate agent checks every deliverable. Your session is the foreman: it sizes the task, briefs the agents, has the results checked and records the run. It does not do the work itself.

**Small and medium work.** Everything else goes to one agent plus one check. There is no planning agent and no split, so it adds only a check, a short handover and the foreman's few calls. Splitting small work would not pay: every agent starts with roughly 100,000 tokens of fixed context on a typical setup (it depends on the skills and tools installed).

**Quality.** Quality is protected by the checks, not improved. Every deliverable is checked by an agent that did not produce it, and text others read, legal, money and brand work are never produced or checked below Opus. Nothing in this README claims a saving; that waits for the benchmark below.

## Install

```bash
git clone https://github.com/johnuppard/quartermaster.git
cd quartermaster
./install.sh
```

Then, in Claude Code, type `/quartermaster help`.

What the installer touches:

- It first checks for Claude Code (in `~/.local/bin/claude` or on your PATH), Python 3.9 or newer, and a complete copy of the repository. If anything is missing it stops and writes nothing.
- It copies `skill/SKILL.md` to `~/.claude/skills/quartermaster/SKILL.md`.
- It creates `~/.claude/quartermaster/` and its `runtime/` folder, and copies `quartermaster.py`, `ROUTING.md`, `prices.json`, `config.example.json` and `ROUTING.local.example.md` into it, plus `LESSONS.md` if you have none.
- It copies `extras/review/REVIEW.md` to `~/.claude/quartermaster/extras/review/REVIEW.md`, so the optional review is there when you ask for it.
- It runs `setup`, which creates `ROUTING.local.md` and `config.json` from the examples if they are missing.

It needs no sudo and no API key, and it schedules nothing. Run `./install.sh` again to update the skill and the script (an installed self-review extra is updated by its own installer): your `ROUTING.local.md`, `LESSONS.md`, `config.json` and `runtime/` folder are kept; the shipped files, `prices.json` included, are replaced.

To uninstall, run `./install.sh --uninstall`. It lists what it will remove (the skill folder, and `~/.claude/quartermaster/` with your routing, lessons, config and run history, plus the daily self-review job if you installed it) and asks you to type yes. `--yes` skips the question.

## A run, step by step

Commands: `/quartermaster <task>`, `/quartermaster review <task>` (the optional review first, see Extras), `/quartermaster resume`, `/quartermaster help`, `/quartermaster lesson: <feedback>`. Write "Fable for piece 2" to put one piece on the top model; the foreman never picks Fable by itself.

1. **Start.** The foreman runs `status` (if it says NOT INSTALLED or INCOMPLETE, you are told to run `install.sh` and nothing else happens), then `context` (see "Keeping the thread lean"), then reads `LESSONS.md`, `ROUTING.md` and `ROUTING.local.md`. If the session runs on Sonnet or Haiku it recommends `/model opus` and waits; on Fable it says that costs more than Opus here and continues.
2. **Gate line.** It decides the size (S: one agent, under ten tool calls; M: one agent, one context; L: more than one context, or more than four independent pieces), the stakes (high for anything a client or the public sees, live systems, legal, money or brand), whether the task splits, and which routing row fits. For S or M work, or L work that does not split, it says: "One agent on <tier>; Quartermaster adds only a check and a handover."
3. **Plan line.** For L work that splits, it shows the plan in three to six plain lines. Each piece has an output, a model, its inputs, two to five done criteria, what it waits for, and a ceiling. A new design gets one Opus planner agent, and the foreman says so first. A task an installed skill owns runs in one agent on that skill's own `model:` line. Anything high stakes, or anything that sends, spends, publishes, changes a live system or deletes, waits for your yes, and the yes covers only the stated pieces and ceilings.
4. **Board.** Before any agent starts, `board` prints a table of all four models and the pieces; a model with no piece reads "not needed for this task". It is printed again after each batch, with tokens and time read from the agents' transcripts.
5. **Agents.** Every agent call names its model. Independent pieces start in one message. Each brief ends with a clause that tells the agent to stop and return ESCALATE, with the tier it recommends, instead of a weaker result, or AMBIGUOUS with the open question. An escalated piece is re-run once on the recommended tier if that is within its ceiling; above the ceiling, or to Fable, you are asked. Nothing is moved down a tier.
6. **Check.** One verifier per deliverable, never the agent that did the work: Sonnet checks Haiku work, Opus checks Sonnet work, a fresh Opus agent checks Opus work. It answers each done criterion yes or no with evidence. A no re-runs the piece once, one tier up, within the ceiling. For high stakes the verifier looks at the result as the end user will, and text others read also gets an Opus editor.
7. **Scorecard.** You get the answer first, then how it was checked. The foreman runs `record`, which prints the final board and the scorecard; both are pasted unchanged. The run is appended to `runtime/runs.jsonl` and the totals to `runtime/scoreboard.json`.
8. **Handover.** At the end of every task, `handover` writes `runtime/handover.md` so a fresh chat can continue.

## The scorecard

Example output, from real agent transcripts of an earlier session of the same day: a Haiku piece "count rows" and a Sonnet piece "write summary" (both work), and an Opus "verify report" (check), recorded with `--checked-by` set to the check's agent id.

```text
Quartermaster board

| Model | Piece | Status | Tokens | Time |
|---|---|---|---|---|
| Fable | not needed for this task | - | - | - |
| Opus | verify report (check) | done | 820,260 | 2:26 |
| Sonnet | write summary | done | 320,641 | 20s |
| Haiku | count rows | done | 207,320 | 14s |

Used: 1,348,221 tokens by 3 agents (input 26, cache write 347,597, cache read 986,052, output at least 14,546). By model: Opus 820,260, Sonnet 320,641, Haiku 207,320.
Overhead: plan $0.00, checks $1.01, foreman $3.89, together $4.91 (93% of this run).
Baseline (estimate): the work pieces on one Opus agent, same tokens, $1.21.
Net against the baseline (estimate): cost $4.06 more (335%)
No time won (under a minute)
Running net: -$4.06 over 1 run. Best run: -$4.06 (README example).
How your subscription weighs these tokens is not published. Dollars are Anthropic API list-price estimates, not a bill.
For reference (estimates): all pieces on Fable $5.32, all on Opus $2.23.
```

The agents ran 18 minutes apart in that earlier session, so the foreman line holds everything that long session sent in those 18 minutes, and the honest result is that this run cost more than the baseline.

What each line means:

- **Board.** One row per piece, with tokens and active time from that agent's own transcript. A role other than work is shown in brackets; "(ran on X)" appears when the transcript shows a different model than the one planned.
- **foreman: not found (counted as 0).** Printed only when the session's own transcript could not be found.
- **Used.** The tokens of every agent in the record, split into input, cache write, cache read and output, and by model. The foreman's tokens are not in this line; they appear as dollars under Overhead. Output is "at least" because transcripts often keep an early snapshot of the output count, so `record` takes the larger of that count and the written characters divided by four.
- **Overhead.** List-price dollars for planning pieces, check pieces and the foreman, and their share of the run (all pieces plus the foreman). The foreman line exists because the session that gates, briefs and checks spends tokens too; leaving it out would make every run look cheaper than it was.
- **Baseline (estimate).** The work and assemble pieces that finished, priced as if one Opus agent had used the same tokens. Plans, checks and escalated first attempts are not in it, but they are in the run's cost.
- **Net against the baseline (estimate).** The baseline minus the run, with the foreman included. A positive net prints as "saved", a negative one as "cost ... more"; the percentage is of the baseline.
- **Time won.** The agents' active time added up (a gap of more than two minutes in a transcript counts as two) minus the elapsed time from the first agent's start to the last agent's end. Unless the elapsed time and the gain are both at least a minute, it prints "No time won (under a minute)", which is also what appears when there was no gain at all.
- **Running net.** The sum of the nets of every run recorded in this home folder, and the best run.
- **Subscription line.** Always printed. The subscription's weighting of tokens is not published, so every dollar figure is a list-price estimate from `prices.json`, not a bill.
- **For reference.** All pieces priced on Fable, and all on Opus.

`record` records nothing and says why if an agent id has no transcript, or its transcript has no usage yet. It warns when `--checked-by` names an agent that is not in the pieces, because that agent's tokens are then not counted.

## Keeping the thread lean

- **Context check.** Every run starts with `context`. It reads the prompt size of the last reply in the newest transcript for this folder (two chats open in the same folder can be confused; the figure is then from the other one) and prints one line, "Context: this chat carries about N tokens into every turn. Threshold T.", then ABOVE or BELOW. If it cannot tell, it prints "Context: unknown" and BELOW.
- **Threshold.** `context_threshold_tokens` in `~/.claude/quartermaster/config.json`, default 150000. It is a token count, not a percentage, because models have different windows. `context_window` is optional and only adds a percentage to the line; it changes nothing else.
- **Above the threshold.** The foreman starts nothing new here. It writes the handover with the state "not started" and says why in one line. In the desktop app you start a fresh session that begins with `/quartermaster resume`. In the terminal it prints the two lines to type:

```text
/clear
/quartermaster resume
```

- **Handover.** At the end of every task, `runtime/handover.md` is written with the task, its state, the files and the next step. There is one handover; each one replaces the last.
- **Resume.** `/quartermaster resume` prints the handover and continues from its next step. With no handover it says "No handover found."

## The routing table

`~/.claude/quartermaster/ROUTING.md` (shipped as `job/ROUTING.md`) has a tiers table and one row per task type with five columns: Task type, Plan, Execute, Ceiling, Check. To read it, find the row (if none fits, use "Other"). For small or medium work, or work that does not split, one agent runs on the Execute tier and the Check verifies. For large work that splits, Plan says who writes the pieces, Execute gives the tier per piece, Ceiling is the highest tier a piece may step up to on its own (the plan may lower it, only you may raise it), and Check names the verifier. A send, publish, spend, delete or live write is never done by the agent that wrote the content, and never before your yes.

**Local overrides.** Your rows go in `ROUTING.local.md` next to it. Setup creates it from the example and the installer never overwrites it. A row there overrides the shipped row of the same task type. Do not edit the shipped `ROUTING.md`; an update replaces it.

**Lessons.** `/quartermaster lesson: <feedback>` adds one rule to `LESSONS.md`. A similar rule is merged and the newer one wins; the file stays under 30 lines. A lesson that names another skill or a project belongs there, and the foreman says so. Lessons are read at the start of every run.

**Prices.** `prices.json` holds dated list prices in US dollars per million tokens; Haiku's cache-read price is an assumption, 10 percent of its input price. Edit it if your rates differ, and re-apply your edits after an update, which replaces it.

## Extras

Two optional extras live in the `extras` folder. The review runs only when you type `/quartermaster review <task>`; the self-review is off unless you install it. Nothing in a normal run calls either.

**Review** (`extras/review/REVIEW.md`). A procedure that challenges the approach before any work starts: three Sonnet Dreamers (amplify, simplify, reframe), one Opus Realist that turns the chosen direction into pieces, and three Critics (intent on Sonnet, execution on Opus, cost on Sonnet) that return questions only. Cost: seven or more extra agents before any work (up to thirteen when Critics are run again), each roughly 100,000 tokens on a typical setup (it depends on the skills and tools installed) of start-up context, and several minutes. To use it, type `/quartermaster review <task>`. The foreman reads `~/.claude/quartermaster/extras/review/REVIEW.md`, which the installer copies there, states the number of agents and the cost, and waits for your yes; if the file is missing, it says the review is not installed and continues without it. Every review agent is on the board and in the record with role `plan`, so the scorecard counts it.

**Self-review** (`extras/self-review/`). A daily job that collects the day's evidence from your Claude Code history (`lesson:` messages, model switches you made by hand above your default, escalations in routed runs, and changes to the `model:` lines of your installed skills), writes a short report, and updates your routing rows and lessons when needed. Cost: on a quiet day it starts no model and costs nothing. A day with evidence starts one background Claude run on your subscription, one background run, on Sonnet, or on Opus when the day holds a lesson, an escalation or a hand switch of model, with a hard limit of 20 minutes by default.

- Install, after the main installer: `bash extras/self-review/install.sh`. It copies the scripts to `~/.claude/quartermaster/extras/self-review/`, adds missing keys to `config.json` without overwriting yours, and schedules the job (launchd on macOS, cron elsewhere) at `run_hour`, default 10.
- Remove only the job: `bash extras/self-review/install.sh --remove`. `./install.sh --uninstall` removes it too.
- Reports go to `~/.claude/quartermaster/runtime/reports/`. Details are in `extras/self-review/README.md`.

## Benchmark

The question: for a large, splittable task, does routing it through Quartermaster use fewer tokens at list price, take less elapsed time, and give a result at least as good as one Opus agent doing the whole task?

The rules in brief: the same task sentence for both arms, saved before either run; the baseline is one fresh Opus agent, start-up cost counted; the routed arm runs exactly as the skill says, with every agent and the foreman counted; a blind Opus judge scores both results; at least two runs per arm per task, and at least two tasks, before any number is published; tokens are counted from the transcripts with the same rules as `record`.

Results: none yet. The full method is in [benchmark/BENCHMARK.md](benchmark/BENCHMARK.md).

## Limits, stated plainly

- **It is instructions to a model, not code.** The gate, the routing, the briefs, the checks and the escalations are rules in `SKILL.md` that your session model follows, and it can misjudge a size or a tier. Only the helper script's commands (`status`, `setup`, `context`, `board`, `record`, `handover`, `resume`, `help`) are code.
- **It cannot change the session model.** If the session is below Opus it recommends `/model opus` and waits.
- **It does not fire by itself.** The skill is set so the model cannot start it; you type `/quartermaster`.
- **Output tokens are a minimum.** The transcripts do not always hold the final output count.
- **The baseline is an estimate.** It prices the same tokens at Opus rates; one real Opus agent would use a different number of tokens. The benchmark exists to measure that.
- **The foreman window runs from the first agent to the last.** Everything the session does between the first agent's start and the last agent's end counts as foreman; what it does before the first agent and after the last does not. Run the pieces and their check back to back and record right after they finish; other work in between, or a check started much later, widens the window.
- **The context threshold is a fixed token count.** It does not know your model's window; set `context_threshold_tokens` to suit how you work.
- **macOS and Linux only.** The installers are bash scripts, and the self-review schedules with launchd or cron.

## Requirements

- Claude Code, signed in, in `~/.local/bin/claude` or on your PATH. No API key and no paid service beyond your subscription.
- Python 3.9 or newer. The scripts use the standard library only.
- macOS or Linux, with bash.

## License

MIT. The full text is in `LICENSE`.
