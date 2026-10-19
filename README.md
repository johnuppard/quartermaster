# Quartermaster

Plan on the strongest model, do the work on the cheapest one that does each piece well, and see on a scorecard exactly what you won back.

## Why

Running one top model for everything burns your allowance on work a cheaper model does equally well.
Running a cheap model everywhere saves tokens and puts the result at risk.
Quartermaster allocates each piece to the right model, steps a piece up the moment its model says it cannot deliver, checks the result one tier up, and shows the saving, computed from each agent's real token counts.

## Sixty seconds to your first scorecard

You need Claude Code, signed in, and Python 3.9 or newer.

```bash
git clone https://github.com/johnuppard/quartermaster.git
cd quartermaster
./install.sh
```

Then, in Claude Code:

```text
/quartermaster help
/quartermaster <task>
```

The installer needs no sudo. It checks that Claude Code, Python and a complete copy of the repository are present before it writes anything. It copies the skill to `~/.claude/skills/quartermaster/`, puts the scripts and routing table in `~/.claude/quartermaster/`, creates your own `ROUTING.local.md`, `LESSONS.md` and `config.json` if they are missing, takes a snapshot of every installed skill's `model:` line, and schedules the daily self-review. There is no API key and no paid service. It runs on the Claude Code subscription you already have.

Run `./install.sh` again to update; your routing, lessons, config and history are kept. `./install.sh --force` resets them too, after saving a backup in the runtime folder.

## What you see

First the plan, before any work starts. This example is the task in "A worked example" below:

```text
Improved request: add --json to list, show and stats, with tests and docs. The JSON carries the text fields plus each record's id.
Changed: the request as asked, with one detail settled (the id field, so other tools can join records).
1. Find the three report commands, their output code and tests. Haiku, ceiling Sonnet.
2-4. Add --json to list, show and stats, one agent each, in parallel. Sonnet, ceiling Opus.
5. Assemble docs and changelog. Sonnet, ceiling Opus. 6. Check every done-criterion: a fresh Opus verifier.
Board: Fable not needed, Opus checks, Sonnet reviews and builds, Haiku looks up. Starting now (low stakes).
```

Then the board, printed before launch and again after each batch. All four models are always listed. This is example output from `quartermaster.py board`, generated from made-up agent transcripts:

```text
Quartermaster board

| Model | Piece | Status | Tokens | Time |
|---|---|---|---|---|
| Fable | not needed for this task | - | - | - |
| Opus | Check against the done-criteria | planned | - | - |
| Sonnet | critic: intent and execution | done | 127,470 | 1:11 |
| Sonnet | list --json | running | - | - |
| Sonnet | show --json | running | - | - |
| Sonnet | stats --json | running | - | - |
| Sonnet | Assemble: docs and changelog | planned | - | - |
| Haiku | Find the three report commands, their output code and tests | done | 163,526 | 52s |
```

At the end, the final board and the scorecard, from `quartermaster.py record` on the same made-up transcripts:

```text
Quartermaster board

| Model | Piece | Status | Tokens | Time |
|---|---|---|---|---|
| Fable | not needed for this task | - | - | - |
| Opus | stats --json (stepped up from Sonnet) - date format decision | done | 411,265 | 3:46 |
| Opus | Check against the done-criteria | done | 212,276 | 2:08 |
| Sonnet | critic: intent and execution | done | 127,470 | 1:11 |
| Sonnet | list --json | done | 401,053 | 3:14 |
| Sonnet | show --json | done | 340,785 | 2:51 |
| Sonnet | stats --json | escalated | 159,640 | 1:23 |
| Sonnet | Assemble: docs and changelog | done | 157,685 | 1:37 |
| Haiku | Find the three report commands, their output code and tests | done | 163,526 | 52s |

Scorecard

- Tokens won against all on Fable: 1,450,200 Fable-equivalent tokens (1,973,700 tokens processed by 8 agents)
- Tokens won against all on Opus: 738,955 Opus-equivalent tokens
- Time won: 13.3 minutes (the longest piece took 3:46, the pieces together would have taken 17:02 one after another)
- Share of the work on cheaper models: 68% of tokens on Sonnet and Haiku
- This week: 2,490,200 Fable-equivalent tokens won in 5 runs. Personal best: 1,450,200 (Add --json to the three report commands). Level: Bookkeeper, 7,129,800 tokens to Treasurer.

For reference, at Anthropic API list prices (an estimate, not a bill): this run $1.87, all on Fable $7.03, all on Opus $2.98.
```

"Won" is the saving against running the same tokens all on Fable, or all on Opus, expressed in that model's tokens: the dollar difference at list prices divided by what one token cost on that model in this run. The dollar line is only a reference for comparison; on a subscription nobody bills you per token, and Quartermaster costs nothing beyond it. Time won is the sum of all piece times minus the longest. Your level climbs with cumulative Fable-equivalent tokens won: Apprentice, Clerk (1 million), Bookkeeper (5 million), Treasurer (15 million), Quartermaster (40 million), Grand Miser (100 million), Counting House (250 million), Fort Knox (600 million).

## How it works

Your session becomes the foreman. It runs on your normal session model (Opus) and never does the work itself. It has four tiers to hand out:

| Tier | Model | Gets |
|---|---|---|
| Fable | claude-fable-5-1 | New design, large plans, arbitration, escalations you approved |
| Opus | claude-opus-5-5 | Judgment, reports, text a client or the public reads, live systems, checks |
| Sonnet | claude-sonnet-5-5 | Executing a clear spec: edits, scripts, data pulls, searches, test runs |
| Haiku | claude-haiku-5-5 | Lookups, listings, classification, mechanical checks |

`job/ROUTING.md` has one row per task type with its plan, execute, ceiling and check tiers.

**1. Classify.** The foreman sizes the task (S: one agent, under ten tool calls; M: two to five pieces; L: more), sets the stakes (high for anything a client or the public sees, live systems, legal, money or brand), and decides whether it is a new design, whether it splits, which routing row fits and how much review it needs. A small task goes to one agent with no orchestration. A task an installed skill owns runs inside an agent on that skill's own `model:` line.

**2. Plan.** For a known pattern of medium size, the routing row is the plan and the foreman writes the pieces. For a new design or a large task it says "Planning on Fable: new design." and calls one Fable agent that returns the pieces. Each piece has an output, a model, its inputs, two to five checkable done-criteria, what it waits for, and a ceiling: the highest tier it may step up to without asking. Deterministic work, such as a count or a format conversion, becomes a script for a Sonnet or Haiku agent to write and run. Low stakes start at once. Anything high stakes, or anything that sends, spends, publishes, changes a live system or deletes, waits for your yes, and that yes covers the stated pieces and ceilings only.

**3. Execute.** Independent pieces run at the same time as separate agents, each with its model set explicitly, never left to the default. Dependent pieces run in order. Each agent gets only its brief and inputs, not the conversation. Every brief ends with this clause, word for word:

> "If this piece needs more capability than you have (a design decision, a quality bar you cannot reach, or a judgment call with real consequences), do not produce a weaker result. Stop and return exactly: ESCALATE, one line on why, the tier you recommend (sonnet, opus or fable), and the facts and file paths you have already gathered. If the problem is an ambiguity the sources cannot settle, return exactly: AMBIGUOUS, the question, and the options you see. Do not retry. End your result with the line MODEL: <the model you are>."

**4. Escalate.** An ESCALATE, or a verifier's first no on a done-criterion, re-runs that one piece once on the recommended tier with the facts already gathered, if that tier is within the ceiling. Above the ceiling, or any step to Fable, the piece stops and you are asked in one line; the other pieces keep running. AMBIGUOUS changes no tier: the brief is rewritten with the answer, or the question comes to you. Two pieces failing for a shared cause are re-planned once. A stepped-up piece that fails its check stops and comes to you. Nothing that escalated is ever moved back down.

**5. Check.** Always one tier up, never the agent that did the work. Low stakes get one verifier one tier above the executing tier (a fresh Opus agent checks Opus work), answering each done-criterion yes or no with evidence. High stakes get an independent Opus checker that looks at the result the way the end user will, plus an Opus editor for any text a person reads. A Haiku result that feeds a live change gets a Sonnet recount first. If agents disagree or a check fails twice, Fable decides, after your yes.

**6. Report.** You get the answer first, in one to three sentences, then how it was checked, or "not checked" and why. The foreman runs `quartermaster.py record`, which reads each agent's real token usage and time from its own transcript, prints the final board and the scorecard, appends the run to `~/.claude/quartermaster/runtime/runs.jsonl` and updates the scoreboard.

## The review before the work

Before a task is planned in full, a short review checks that Quartermaster understood you and looks for a better and leaner way. Each agent stays in one mode. The foreman chairs and decides.

- **Intent Brief.** The foreman writes six short parts: Asked (your words), Goal (the outcome behind them), Recipient (who gets the result and how they see it), Done (three to five checkable statements), Constraints (deadlines, tools, your lessons and rules) and Assumptions. If an assumption would change the plan and nothing can check it, you get one question first.
- **Dreamers.** Three Sonnet agents, one lens each: **amplify** (much more value toward the same goal), **simplify** (most of the value for far less effort, including "use what already exists") and **reframe** (a better goal or a different problem behind the request). They do not judge or criticise. Your original request stays on the table and wins unless an idea is clearly better against the Done statements.
- **The Realist.** The planner from step 2 assumes the chosen direction will happen and turns it into pieces. It does not criticise the direction.
- **Critics.** Three agents challenge the plan: **intent** on Sonnet (does it deliver what you want, has it drifted or grown), **execution** on Opus (what will fail, what is missing, what cannot be verified) and **cost** on Sonnet (is every piece on the right model and ceiling, is anything overbuilt). They return questions only, never verdicts or rewrites, each tagged Blocker, Material or Minor.
- **The chair.** The foreman drops minor questions, sends the rest to the planner or the chosen Dreamer, re-runs only the Critics that raised a Blocker or Material question, and stops when none is left or after three rounds. If serious questions remain, you get one question with the options.

| Level | When | What runs |
|---|---|---|
| None | Size S, or you wrote "no review" | The goal stated in one line |
| Light | Known pattern, size M, low stakes | Intent Brief and one Sonnet Critic (intent and execution together) |
| Full | New design, size L, high stakes at size M or above, a prompt or skill to improve, or `/quartermaster review <task>` | Everything above |

`/quartermaster review <task>` forces the full review whatever the size. Add "no review" to your request to skip it. The plan shows what the review changed from your request and why, and if it changed the direction or scope, Quartermaster waits for your yes. Review agents appear on the board as pieces (`dream: amplify`, `plan`, `critic: cost` and so on) and count in the scorecard, so you see what the review cost.

## A worked example

You type: `/quartermaster Add a --json flag to the three report commands of our CLI, with tests, and document it.`

**Classify.** Size M, low stakes (internal code, easy to undo), a known pattern, splittable. Routing row: scripts and automation, which executes on Sonnet with a ceiling of Opus. Review level Light. No Fable.

**Review.** The Intent Brief sets the goal (other tools can read the reports without parsing text) and the Done statements (each command takes `--json`, prints valid JSON, has tests, and the flag is documented). One Sonnet Critic asks one Material question: should the JSON carry the same fields as the text output, or the full record? The foreman settles it from the brief: the same fields plus each record's id. Nothing is left, so the review stops after one round.

**Plan and execute.** You see the plan shown under "What you see". A Haiku agent finds the files in under a minute. Three Sonnet agents start at once, one per command, each the only writer of its own file. `list` and `show` finish.

**One escalation.** The `stats` agent stops and returns: "ESCALATE: the text output mixes two date formats and other tools parse it; choosing the JSON format is a design call with consequences. Recommend opus." Opus is within the piece's ceiling, so the foreman re-runs that piece once on Opus with the same brief plus the facts the Sonnet agent gathered. The board shows "stepped up from Sonnet". Opus picks ISO 8601 in UTC and notes why. Had the agent asked for Fable, the piece would have stopped and you would have been asked first.

**Check.** A fresh Opus verifier gets the original request, the result and the done-criteria. It runs each command with `--json`, runs the tests, and answers every criterion yes or no with one line of evidence. All yes.

**Report.** "All three report commands now take --json; dates are ISO 8601 in UTC, as written in the docs and changelog. Checked by a fresh Opus verifier that ran each command and the tests." Then the board and scorecard shown above, pasted unchanged. Fable did nothing on this task, and the board says so.

## The daily self-review

Once a day (10:00 by default; launchd on macOS, cron on Linux) a runner keeps Quartermaster current.

**Scripts collect the evidence.** Since the last run, a script scans your Claude Code transcripts (except folders whose name contains an entry of `skip_project_folders`) for messages that start with `lesson:`, `/model` switches you made by hand to a tier above `default_tier`, routed runs and the pieces that escalated, possible corrections (your next message within 60 minutes of a routed run containing a correction word), clean runs, and skills whose `model:` line changed or was dropped by an update.

**A model wakes only when there is a decision.** If there is no lesson, switch, escalation, skill drift or proposal to lower a tier, the runner writes a report and stops. No model runs. Otherwise it starts one headless Claude Code run: Sonnet by default, Opus when a lesson, an escalation or a hand switch needs judging, with a fixed tool list and a hard kill after 20 minutes. It turns lessons into rules, restores a `model:` line an update dropped (a line you changed by hand is accepted, never reverted), lists new skills by tier, and raises a task type's execute tier by one when it escalated from the same tier in two or more runs. It never raises anything to Fable and never lowers a tier itself; after ten clean runs of a task type on one tier it only proposes lowering. It answers a Done list, fixes and re-checks up to three times, and stops with BLOCKED rather than guess.

**Transcripts are never read by a model.** The model reads only the evidence file the script wrote and treats any quoted text in it as data. It may change only `LESSONS.md`, `ROUTING.local.md`, the runtime folder and a skill's `model:` line.

**Tamper guard.** The runner fingerprints every protected file before the run and compares after. Anything changed outside the allowed paths is restored from the copy taken before the run (a changed crontab line is reported instead), and the run is marked tampered.

**When you hear from it.** Only when something changed, something needs your eyes (a new skill's tier, a raised row, a candidate to lower, a correction flag), the run failed or was tampered with, or it is Monday. A quiet Monday sends one line, "Quartermaster ran N of 7 days, no changes", so silence can be told from a dead job. The same failure notifies once, not every day. Reports are kept in `~/.claude/quartermaster/runtime/reports/`.

## Steering it

**In the plan line.** Raise or lower a piece's ceiling, say "no Fable", or say "Fable for piece 2". The plan may lower a row's ceiling; only you may raise it.

**Lessons.** Write `/quartermaster lesson: <feedback>` in a session, or start any message with `lesson:` and the daily self-review picks it up. Each lesson becomes one rule in `LESSONS.md` (30 lines at most); a similar rule is merged and the newer one wins. A lesson that names another skill or project is reported to you instead.

**ROUTING.local.md** is yours. A row there overrides the shipped row of the same task type in `ROUTING.md`, with the same columns. Its "Skills by tier" section lists your skills, and the self-review adds new skills there and writes its tier changes under "Notes" with the date. Updates never overwrite it. Do not edit the shipped `ROUTING.md`; an update replaces it.

**config.json** in `~/.claude/quartermaster/`, created from `config.example.json`:

| Key | Default | Meaning |
|---|---|---|
| `notify_command` | empty | Shell command run when the self-review has something to tell you |
| `run_hour` | 10 | Hour of the daily run, 0 to 23. Run `/quartermaster setup` after changing it |
| `max_minutes` | 20 | Hard time limit for the headless model run |
| `model_review` | claude-sonnet-5-5 | Model for a review with no decision to make |
| `model_decide` | claude-opus-5-5 | Model when lessons, escalations or hand switches need judging |
| `correction_words` | wrong, redo, not what I asked | Words that flag a possible correction; add your own language's |
| `claude_path` | ~/.local/bin/claude | Where the `claude` command is; if it is not there, the standard folders (/opt/homebrew/bin, /usr/local/bin, /usr/bin, /bin, ~/.local/bin) are searched |
| `skip_project_folders` | `["quartermaster"]` | Transcript folders the self-review never scans (any folder whose name contains an entry) |
| `forbid_dashes` | false | When true, the Done check also fails on an em or en dash in your own files |
| `default_tier` | opus | Your normal session model; only a hand switch above it counts as evidence |

`notify_command` runs with `/bin/sh -c` and receives `SUBJECT` (one line) and `BODY_FILE` (a text file with the message: the full report after a run, one line on a quiet Monday, the flags when only corrections were found). Leave it empty and the report file is the only record; `python3 ~/.claude/quartermaster/quartermaster.py status` shows the last report's headline. Two examples, as they go in `config.json`:

```json
"notify_command": "osascript -e 'display notification \"Quartermaster wrote a new report\" with title \"'\"$SUBJECT\"'\"'"
```

```json
"notify_command": "mail -s \"$SUBJECT\" you@example.com < \"$BODY_FILE\""
```

The first shows a macOS notification with the subject as its title. The second sends that text through any `mail` command you already have set up.

**prices.json** holds list prices per tier in US dollars per million tokens (input, output, cache read, cache write, and Haiku's higher rates for a prompt over 100K tokens), with the date they were taken. It drives only the scorecard's conversions and the reference line. Edit it if your rates differ, and re-apply your edits after an update, which replaces it.

**Repairs.** `/quartermaster setup` repairs a broken install or applies a new `run_hour`. It never overwrites your files.

## Files

```text
README.md                         this file
LICENSE                           MIT
install.sh                        install and update; --force resets your own files; --uninstall removes
skill/SKILL.md                    the skill: classify, review, plan, execute, escalate, check, report
job/JOB.md                        the daily self-review, its rules and its Done list
job/ROUTING.md                    tiers, task type to plan, execute, ceiling and check, skills by tier
job/ROUTING.local.example.md      template for your own rows and skill tiers
job/LESSONS.md                    learned rules; starts with only its title
job/config.example.json           template for config.json
job/prices.json                   list prices used by the scorecard
job/quartermaster.py              status, setup, board, record, help
job/run_headless.py               the daily runner: lock, evidence, headless run, restore, notify
job/collect_evidence.py           scans transcripts and the run log into the evidence file
job/done_check.py                 the mechanical Done check and the file fingerprints
job/snapshot_skill_models.py      records every skill's model: line; shows and restores drift
```

Once installed, your own state sits next to the scripts in `~/.claude/quartermaster/`: `ROUTING.local.md`, `LESSONS.md`, `config.json`, and `runtime/` (run log, scoreboard, ledger, skill snapshot, evidence, reports, logs).

## Limits, stated plainly

- **It cannot change the model of the session you are in.** The foreman is your session model. If that is below Opus, Quartermaster says so, recommends `/model opus` and waits. If it is Fable, it says the foreman is cheaper on Opus and continues.
- **It does not fire by itself.** The skill is set so the model cannot invoke it on its own. You type `/quartermaster`.
- **The baseline figures are estimates.** "All on Fable" and "all on Opus" are the same tokens priced at another model's list price, and the equivalent tokens come from the same prices. A real all-Fable or all-Opus run would not use exactly the same tokens.
- **Time won is an upper bound.** Pieces that waited for each other count as if they had run side by side.
- **Only agents are counted.** The board and scorecard read the agents' transcripts. The foreman's own tokens in your session are not on them.
- **Parallel agents save time, not tokens.** Each agent reads its own inputs, so a piece one agent can finish in ten calls is not split.
- **The Workflow tool is optional.** When it is available, Quartermaster uses it for more than four pieces; without it, several parallel Agent calls do the same job.
- **The daily job uses the Python that ran setup.** If you remove or replace that Python, run `/quartermaster setup` again.
- **Plugin skills are not controlled.** Skills that are not files on your machine have no `model:` line Quartermaster can see; it treats them as Opus and says so in the plan.
- **macOS and Linux only.** The daily job uses launchd or cron. Elsewhere, setup prints the command for you to schedule yourself.
- **Claude Code is required.** Quartermaster uses its agents, its transcripts and its headless mode.

## Requirements

- Claude Code, signed in, with access to the four models. No API key and no paid service beyond your subscription.
- Python 3.9 or newer. The scripts use the standard library only.
- macOS (launchd) or Linux (cron) for the daily self-review.

## Uninstall

```bash
./install.sh --uninstall
```

It lists what it will remove (the skill, the `~/.claude/quartermaster/` folder with your routing, lessons, config and run history, and the daily job) and asks you to type yes. `--yes` skips the question.

## License

MIT. The full text is in `LICENSE`.
