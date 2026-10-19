# Quartermaster

Quartermaster is a Claude Code skill that keeps your subscription working at full stretch without giving up any quality. Type `/quartermaster` and a task, and your session becomes a foreman. Before any work starts, cheap reviewer agents make sure it understood what you want and look for a better and leaner way to get there. Then it splits the work into pieces, gives each piece to the cheapest model that does it well, runs independent pieces side by side, and calls the top model in only for the thinking that really needs it. A piece that turns out to be too hard for its model says so and steps up one tier instead of handing you something weak, and every result is checked by a model one tier up. You watch every model at work on a board, and each run ends with a scorecard of the tokens you won back against running it all on the top models. There is no API key and no paid service: it runs on the Claude Code subscription you already have.

## How it works

The foreman runs on your normal session model (Opus). It does not do the work itself. Four tiers are available to it:

| Tier | Model | Gets |
|---|---|---|
| Fable | claude-fable-5-1 | New design, large plans, arbitration, escalations you approved |
| Opus | claude-opus-5-5 | Judgment, reports, text a client or the public reads, live systems, checks |
| Sonnet | claude-sonnet-5-5 | Executing a clear spec: edits, scripts, data pulls, searches, test runs |
| Haiku | claude-haiku-5-5 | Lookups, listings, classification, mechanical checks |

The full table, with one row per task type and its plan, execute, ceiling and check tiers, is in `job/ROUTING.md`.

**1. Classify.** The foreman sizes the task (S: one agent, under ten tool calls; M: two to five pieces; L: more), decides the stakes (high for anything a client or the public sees, live systems, legal, money or brand), whether it is a new design, whether it splits, which routing row fits, and how much review it needs (None, Light or Full; see the next section). A small task goes to one agent with no orchestration. A task an installed skill owns runs inside an agent on that skill's own `model:` line, and Quartermaster only routes the work around it.

**2. Plan.** The planner is the Realist of the review: it takes the Intent Brief and the chosen direction and makes them concrete. For a known pattern of medium size, the routing row is the plan and the foreman writes the pieces itself. For a new design or a large task it first says "Planning on Fable: new design." and calls one Fable agent that returns the pieces. Each piece has an output, a model, its inputs, two to five checkable done-criteria, what it waits for, and a ceiling: the highest tier it may step up to without asking. Deterministic work (a count, a format conversion) becomes a script for a Sonnet or Haiku agent to write and run. The Critics then challenge the plan, and only after that do you see it, in three to six lines: the improved request, what changed from your request and why (or "the request as asked was the best option"), the pieces with model and ceiling, open assumptions and the expected board. If the review changed the direction or scope, it waits for your yes. Otherwise low stakes start at once. Anything high stakes, or anything that sends, spends, publishes, changes a live system or deletes, waits for your yes, and that yes covers the stated pieces and ceilings only.

**3. Execute and show the board.** Independent pieces run at the same time as separate agents, each with its model set explicitly, never left to the default. Dependent pieces run in order. Each agent gets only its brief and inputs, not the conversation. The board prints before launch and again after each batch, and the review agents are on it too. Every brief ends with this clause, word for word:

> "If this piece needs more capability than you have (a design decision, a quality bar you cannot reach, or a judgment call with real consequences), do not produce a weaker result. Stop and return exactly: ESCALATE, one line on why, the tier you recommend (sonnet, opus or fable), and the facts and file paths you have already gathered. If the problem is an ambiguity the sources cannot settle, return exactly: AMBIGUOUS, the question, and the options you see. Do not retry. End your result with the line MODEL: <the model you are>."

**4. Escalate.** An ESCALATE, or a verifier's first no on a done-criterion, re-runs that one piece once on the recommended tier with the facts already gathered, if that tier is within the ceiling. Above the ceiling, or any step to Fable, the piece stops and you are asked in one line with the reason; the other pieces keep running. AMBIGUOUS changes no tier: the brief is rewritten with the answer, or the question comes to you. Two pieces failing for a shared cause are re-planned once. A stepped-up piece that fails its check stops and comes to you. Nothing that escalated is ever moved back down.

**5. Check.** Always one tier up, never the agent that did the work. Low stakes: one verifier one tier above the executing tier (a fresh Opus agent checks Opus work) answers each done-criterion yes or no with evidence. High stakes: an independent Opus checker looks at the result the way the end user will, and an Opus editor reads any text a person will read. A Haiku result that feeds a live change gets a Sonnet recount first. If agents disagree or a check fails twice, Fable decides, after your yes.

**6. Report, scorecard, log.** You get the answer first, in one to three sentences, then how it was checked (or "not checked" and why). The foreman runs `quartermaster.py record`, which reads each agent's real token usage and time from its own transcript, prints the final board and the scorecard, appends the run to `~/.claude/quartermaster/runtime/runs.jsonl` and updates the running scoreboard.

## The review before the work

Before a task is planned in full, Quartermaster runs a short review in three modes, and each agent stays in its one mode: Dreamers improve the idea, the Realist makes it concrete, Critics challenge it. The foreman chairs and decides.

- **Intent Brief.** The foreman writes it in six short parts: **Asked** (your request in your words), **Goal** (the outcome behind it), **Recipient** (who gets the result and how they will see it), **Done** (three to five checkable statements), **Constraints** (deadlines, tools, your lessons and rules), **Assumptions** (each one listed). If an assumption would change the plan and nothing can check it, you get one question first.
- **Dreamers.** Three agents on Sonnet, each with the brief and one lens: **amplify** (much more value toward the same goal), **simplify** (most of the value for far less effort, including "use what already exists"), **reframe** (a better goal or a different problem behind the request). They do not judge feasibility or criticise. The foreman picks a direction or merges ideas; your original request stays on the table and wins unless an idea is clearly better against the Done statements.
- **Realist.** The planner (step 2 above) assumes the chosen direction will happen and turns it into pieces. It does not criticise the direction.
- **Critics.** Three agents challenge the plan: **intent** on Sonnet (does it deliver what you actually want, has it drifted or grown), **execution** on Opus (what will fail, what is missing, what cannot be verified), **cost** on Sonnet (is every piece on the right model and ceiling, is anything overbuilt). They return questions only, never verdicts or rewrites, each tagged Blocker, Material or Minor and routed to the Dreamer or the planner.
- **The chair.** The foreman drops minor questions, sends the rest back to the planner or the chosen Dreamer, re-runs only the Critics that raised a Blocker or Material question, and stops when none is left or after three rounds. If serious questions remain after three rounds, it asks you one question with the options.

Review levels:

| Level | When | What runs |
|---|---|---|
| None | Size S, or you wrote "no review" | The goal stated in one line |
| Light | Known pattern, size M, low stakes | Intent Brief and one Critic on Sonnet (intent and execution together) |
| Full | New design, size L, high stakes at size M or above, a prompt or skill to improve, or `/quartermaster review <task>` | Everything above |

`/quartermaster review <task>` forces a full review whatever the size. Add "no review" to your request to skip it. Review agents appear on the board as pieces (`dream: amplify`, `plan`, `critic: cost` and so on) and count in the scorecard, so you see what the review cost.

## What you see

Example, with plausible numbers, from the task in the section after this one, in the layout `quartermaster.py` prints. The board is a Markdown table that Claude Code renders.

The board while the work runs. All four models are always listed:

```text
Quartermaster board

| Model | Piece | Status | Tokens | Time |
|---|---|---|---|---|
| Fable | not needed for this task | - | - | - |
| Opus | Check against the done-criteria | planned | - | - |
| Sonnet | critic: intent and execution | done | 52,900 | 1:11 |
| Sonnet | list --json | running | - | - |
| Sonnet | show --json | running | - | - |
| Sonnet | stats --json | running | - | - |
| Sonnet | Assemble: docs and changelog | planned | - | - |
| Haiku | Find the three report commands, their output code and tests | done | 55,200 | 52s |
```

The final board and the scorecard:

```text
Quartermaster board

| Model | Piece | Status | Tokens | Time |
|---|---|---|---|---|
| Fable | not needed for this task | - | - | - |
| Opus | stats --json (stepped up from Sonnet) - date format decision | done | 174,700 | 3:46 |
| Opus | Check against the done-criteria | done | 100,500 | 2:08 |
| Sonnet | critic: intent and execution | done | 52,900 | 1:11 |
| Sonnet | list --json | done | 180,400 | 3:14 |
| Sonnet | show --json | done | 161,200 | 2:51 |
| Sonnet | stats --json | escalated | 71,600 | 1:23 |
| Sonnet | Assemble: docs and changelog | done | 76,700 | 1:37 |
| Haiku | Find the three report commands, their output code and tests | done | 55,200 | 52s |

Scorecard

- Tokens won against all on Fable: 633,978 Fable-equivalent tokens (873,200 tokens processed by 8 agents)
- Tokens won against all on Opus: 301,294 Opus-equivalent tokens
- Time won: 13.3 minutes (the longest piece took 3:46, the pieces together would have taken 17:02 one after another)
- Share of the work on cheaper models: 68% of tokens on Sonnet and Haiku
- This week: 1,670,478 Fable-equivalent tokens won in 5 runs. Personal best: 1,182,400 (Move the test suite to the new runner). Level: Bookkeeper, 7,886,022 tokens to Treasurer.

For reference, at Anthropic API list prices (an estimate, not a bill): this run $1.03, all on Fable $3.76, all on Opus $1.57.
```

How the scorecard counts:

- **Tokens won** compares the run with two baselines: the same tokens all on Fable and all on Opus, at list prices. Each saving is expressed in that model's tokens: the dollar saving divided by what one token cost on that model in this run. Opus is your normal session model, so the Opus figure is the plainer comparison; the Fable figure feeds the weekly total and the level.
- **Pricing.** A Haiku message whose prompt is over 100K tokens is priced at the higher list rate for long prompts. The other models have one rate.
- **Time won** is the sum of every piece's time minus the longest piece.
- **Share on cheaper models** is the part of all tokens processed by Sonnet and Haiku agents.
- **Level** follows your cumulative Fable-equivalent tokens won: Apprentice (0), Clerk (1 million), Bookkeeper (5 million), Treasurer (15 million), Quartermaster (40 million), Grand Miser (100 million), Counting House (250 million), Fort Knox (600 million).
- **The reference line** prices the run three ways at the list prices in `prices.json`. It is an estimate for comparison. On a subscription nobody bills you per token.

## A typical task

You type: `/quartermaster Add a --json flag to the three report commands of our CLI, with tests, and document it.`

**Classify.** Medium, low stakes (internal code, easy to undo), a known pattern, splittable. Routing row: scripts and automation (execute on Sonnet, ceiling Opus). Review level Light. No Fable needed.

**Review.** The foreman writes the Intent Brief. Goal: other tools can read the reports without parsing text. Done: each command takes `--json`, prints valid JSON, has tests, and the flag is documented. One Critic on Sonnet reads the brief and the draft plan and asks one Material question for the planner: "Should the JSON carry the same fields as the text output, or the full record?" The foreman settles it from the brief (same fields, plus each record's id) and puts it in every brief. No question is left, so the review stops after one round.

**Plan, as you see it:**

```text
Improved request: the same, with one decision made: JSON carries the text fields plus each record's id.
1. Find the three report commands, their output code and tests. Haiku, ceiling Sonnet.
2-4. Add --json to list, show and stats, one agent each, in parallel. Sonnet, ceiling Opus.
5. Assemble: docs and changelog from pieces 2 to 4. Sonnet, ceiling Opus.
6. Check every done-criterion: a fresh Opus verifier runs each command and the tests.
Board: Fable not needed, Opus checks, Sonnet reviews and builds, Haiku looks up. Starting now (low stakes).
```

**Execute.** The Haiku agent returns the file list in under a minute. Three Sonnet agents start at once, one per command, each the only writer of its own file. The `list` and `show` agents finish.

**One escalation.** The `stats` agent stops and returns: "ESCALATE: the text output mixes two date formats and other tools parse it; choosing the JSON format is a design call with consequences. Recommend opus." Opus is within the piece's ceiling, so the foreman re-runs that piece once on Opus with the same brief plus the facts the Sonnet agent gathered, and the board shows "stepped up from Sonnet". Opus picks ISO 8601 in UTC and notes why. Had the agent asked for Fable, the piece would have stopped and you would have been asked first.

**Check.** A fresh Opus verifier, not one of the agents that did the work, gets the original request, the result and the done-criteria. It runs each command with `--json`, runs the test suite, and answers every criterion yes or no with one line of evidence. All yes.

**Report.** "All three report commands now take --json; dates are ISO 8601 in UTC, as written in the docs and changelog. Checked by a fresh Opus verifier that ran each command and the tests." Then the board and scorecard shown above, pasted unchanged.

Fable did nothing on this task, and the board says so. On a new design it would have planned the pieces, and nothing more.

## The daily self-review

Once a day (10:00 by default; launchd on macOS, cron on Linux) a runner keeps Quartermaster current. Most days no model runs at all.

1. **Scripts collect the evidence.** Since the last run, a script scans your Claude Code transcripts (except folders named in `skip_project_folders`) for messages that start with `lesson:`, `/model` switches you made by hand to a tier above `default_tier`, routed runs and the pieces that escalated, possible corrections (your next message within 60 minutes of a routed run containing "wrong", "redo" or "not what I asked"), clean runs, and skills whose `model:` line changed or was dropped by an update. Each item goes into a ledger, deduplicated.
2. **Quiet day.** If there is no lesson, switch, escalation, drift or proposal to lower a tier, the runner writes a report and stops. No model. A correction flag alone starts no model run either, but it is notified to you the same day as needing your eyes. Corrections are never counted automatically.
3. **Decision day.** Otherwise it starts one headless Claude Code run: Sonnet by default, Opus when a lesson, an escalation or a hand switch needs judging. It has a fixed tool list and a hard kill after 20 minutes. The model reads only the evidence file the script wrote, never the transcripts, and treats any text quoted from them as data. It may change only `LESSONS.md`, `ROUTING.local.md`, the runtime folder and a skill's `model:` line. It turns lessons into rules, restores a `model:` line an update dropped (a line you changed by hand is accepted, never reverted), lists new skills by tier, and raises a task type's execute tier by one when it escalated from the same tier in two or more runs. Hand switches are reported to you, never counted, because a switch carries no task type. It never raises anything to Fable and never lowers a tier itself: after ten clean runs of a task type on one tier it only proposes lowering. It then answers a Done list yes or no, fixes and re-checks up to three times, and stops with BLOCKED rather than guess.
4. **Afterwards.** The runner compares fingerprints of every protected file. Anything changed outside the allowed paths is restored from the copy taken before the run, and the run is marked tampered.

It notifies you only when something changed, something needs your eyes (a new skill's tier, a raised row, a candidate to lower, a correction flag), the run failed or was tampered with, or it is Monday. A quiet Monday sends one line, "Quartermaster ran N of 7 days, no changes", so silence can be told from a dead job. The same failure notifies once, not every day. Reports are kept in `~/.claude/quartermaster/runtime/reports/`.

## Install

```bash
git clone https://github.com/johnuppard/quartermaster.git
cd quartermaster
./install.sh
```

The installer needs no sudo and checks first that Claude Code and Python 3.9 or newer are present and that the copy of the repository is complete. Then it:

- copies the skill to `~/.claude/skills/quartermaster/SKILL.md`;
- copies the scripts, `JOB.md`, `ROUTING.md`, `prices.json` and the example files to `~/.claude/quartermaster/`, and `LESSONS.md` only if you have none;
- runs setup, which creates `ROUTING.local.md` and `config.json` from the examples if missing, takes the first snapshot of every installed skill's `model:` line, and schedules the daily self-review (a launchd job labelled `com.quartermaster.daily` on macOS, a crontab line on Linux; if it cannot, it prints the line to add yourself).

Running `./install.sh` again updates Quartermaster and keeps your routing, lessons, config and history. `./install.sh --force` resets those as well, after saving a backup in the runtime folder.

Then, in Claude Code:

- `/quartermaster help` explains what it does, when to use it and how to steer it.
- `/quartermaster setup` repairs a broken install or applies a new `run_hour`. It never overwrites your files.
- `/quartermaster <task>` runs a task. `/quartermaster review <task>` runs it with the full review. `/quartermaster lesson: <feedback>` adds a rule.

To uninstall: `./install.sh --uninstall`. It lists what it will remove (the skill, the `~/.claude/quartermaster/` folder with your routing, lessons, config and run history, and the daily job) and asks you to type yes; `--yes` skips the question.

## Configure

Everything lives in `~/.claude/quartermaster/`.

**config.json** (created from `config.example.json`):

| Key | Default | Meaning |
|---|---|---|
| `notify_command` | empty | Shell command run when the self-review has something to tell you |
| `run_hour` | 10 | Hour of the daily run, 0 to 23. Run `/quartermaster setup` after changing it |
| `max_minutes` | 20 | Hard time limit for the headless model run |
| `model_review` | claude-sonnet-5-5 | Model for a review with no decision to make |
| `model_decide` | claude-opus-5-5 | Model when lessons, escalations or hand switches need judging |
| `correction_words` | wrong, redo, not what I asked | Words that flag a possible correction; add your own language's |
| `claude_path` | the standard install location | Where the `claude` command is; PATH is searched if it is not there |
| `skip_project_folders` | `["quartermaster"]` | Transcript folders the self-review never scans |
| `forbid_dashes` | false | When true, the Done check also fails on an em or en dash in your own files |
| `default_tier` | opus | Your normal session model; only a hand switch above it counts as evidence |

`notify_command` runs with `/bin/sh -c` and receives two environment variables: `SUBJECT` (one line) and `BODY_FILE` (the path of a text file with the report). Leave it empty and the report file is the only record; `python3 ~/.claude/quartermaster/quartermaster.py status` shows the last report's headline. Two examples, as they go in `config.json`:

```json
"notify_command": "osascript -e 'display notification \"Quartermaster wrote a new report\" with title \"'\"$SUBJECT\"'\"'"
```

```json
"notify_command": "mail -s \"$SUBJECT\" you@example.com < \"$BODY_FILE\""
```

The first shows a macOS notification with the subject as its title; the body stays in the report file. In a terminal it reads `osascript -e 'display notification "Quartermaster wrote a new report" with title "'"$SUBJECT"'"'`. The second sends the whole report by email through any `mail` command you already have set up.

**ROUTING.local.md** is yours. A row there overrides the shipped row of the same task type in `ROUTING.md`, with the same columns. Its "Skills by tier" section lists your skills, one line per tier, and the self-review adds new skills there and writes its tier changes under "Notes" with the date. Updates never overwrite it. Do not edit the shipped `ROUTING.md`; an update replaces it.

**LESSONS.md** holds the rules Quartermaster has learned, 30 lines at most. Write `/quartermaster lesson: <feedback>` in a session, or start any message with `lesson:` and the daily self-review picks it up. Each lesson becomes one rule; a similar rule is merged and the newer one wins. A lesson that names another skill or project is reported to you instead of written here.

**prices.json** holds list prices per tier in US dollars per million tokens (input, output, cache read, cache write, and Haiku's long-prompt rates above 100K tokens), with the date they were taken. It drives only the scorecard's conversions and the reference line. Edit it if your rates differ. An update replaces it, so re-apply your edits after updating.

## Files

```text
README.md                         this file
LICENSE                           MIT
install.sh                        install, update (--force) and uninstall (--uninstall)
skill/SKILL.md                    the skill: classify, review, plan, execute, escalate, check, report
job/JOB.md                        the daily self-review, its rules and its Done list
job/ROUTING.md                    tiers, task type to plan, execute, ceiling and check, skills by tier
job/ROUTING.local.example.md      template for your own rows and skill tiers
job/LESSONS.md                    learned rules; starts empty
job/config.example.json           template for config.json
job/prices.json                   list prices used by the scorecard
job/quartermaster.py                    status, setup, board, record, help
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
- **Time won is an upper bound.** It is the sum of all piece times minus the longest, so pieces that waited for each other count as if they had run side by side.
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

## License

MIT. The full text is in `LICENSE`.
