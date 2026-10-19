# Benchmark results, first run (19 and 20 October 2026)

Two tasks, two runs per arm per task, arms in alternating order, blind Opus judges. Method: [BENCHMARK.md](../../BENCHMARK.md). Quartermaster version: commit a4febc4.

## Answer

On both tasks the routed arm used more tokens, cost more at list price and took longer than one Opus agent doing the whole task. On task 1 the judges preferred the routed result in both runs. On task 2 they preferred the single agent in one run and could not agree in the other.

## The two tasks

Both tasks were written down, with their done criteria, before the first run: [task 1](sales-skill-consolidation/task.md), [task 2](marketplace-readme-audit/task.md). Both read frozen, read-only copies of public plugin material, so the results can be published without private data.

- **Task 1, sales skill consolidation.** Read the 36 skills of a public sales plugin (about 298,000 characters) and write a consolidation recommendation: overlaps, descriptions that will not trigger reliably, and a prioritised merge list.
- **Task 2, marketplace README audit.** Read the README, manifest and file list of 54 plugin folders in a public marketplace (about 215,000 characters) and write a prioritised list of inconsistencies and missing setup steps.

## Arms

- **Baseline:** one fresh Opus agent with the task sentence and the escalation clause from the skill, told to work alone, then one fresh Opus check piece. Recorded with `record` as one work piece plus one check piece.
- **Routed:** the foreman followed `skill/SKILL.md`. Gate: size L, splittable, low stakes, row "Audit or sweep over many files or records" (Haiku finders, Sonnet verifiers, Opus plan). Pieces: three Haiku pieces extracting an inventory (a third of the material each, in parallel), one Sonnet piece verifying and merging the inventory against the sources, one Opus piece writing the deliverable from the inventory, and one fresh Opus check. No piece escalated, and every routed check answered yes on all criteria.

## Table

Tokens are all four kinds together (input, cache write, cache read, output at least), counted by `record` from the agents' transcripts. Foreman is the main session's own messages between the first and last agent of the run, counted the same way for both arms. Dollars are list-price estimates from `prices.json`, not a bill. Elapsed is from the first agent's first record to the last agent's last record, check included, in both arms. Net is the baseline arm's cost minus the routed arm's cost, foreman included in both; a negative net means routing cost more.

### Task 1: sales skill consolidation

| Run | Order | Arm | Opus | Sonnet | Haiku | Foreman | Total tokens | List price | Elapsed | Judge verdict | Net |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | baseline first | Baseline | 3,243,046 | 0 | 0 | 152,566 | 3,243,046 | $2.19 | 4.6 min | | |
| 1 | | Routed | 2,783,261 | 4,972,900 | 2,253,287 | 498,594 | 10,009,448 | $4.10 | 12.5 min | Routed better (2 judges agree) | -$1.91 (routed 87% more) |
| 2 | routed first | Baseline | 3,291,838 | 0 | 0 | 186,038 | 3,291,838 | $1.99 | 4.2 min | | |
| 2 | | Routed | 1,900,950 | 4,932,200 | 2,185,160 | 539,974 | 9,018,310 | $3.96 | 11.3 min | Routed better (2 judges agree) | -$1.97 (routed 99% more) |

Medians: baseline $2.09, 3,267,442 tokens, 4.4 min; routed $4.03, 9,513,879 tokens, 11.9 min.

### Task 2: marketplace README audit

| Run | Order | Arm | Opus | Sonnet | Haiku | Foreman | Total tokens | List price | Elapsed | Judge verdict | Net |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | routed first | Baseline | 3,447,852 | 0 | 0 | 224,057 | 3,447,852 | $2.23 | 4.9 min | | |
| 1 | | Routed | 4,795,237 | 9,140,554 | 4,109,368 | 651,721 | 18,045,159 | $5.91 | 19.7 min | Baseline better (2 judges agree) | -$3.68 (routed 165% more) |
| 2 | baseline first | Baseline | 4,767,522 | 0 | 0 | 228,774 | 4,767,522 | $2.48 | 6.3 min | | |
| 2 | | Routed | 4,197,447 | 14,102,605 | 3,739,837 | 718,435 | 22,039,889 | $7.25 | 22.8 min | Undecided (judges disagree) | -$4.76 (routed 192% more) |

Medians: baseline $2.36, 4,107,687 tokens, 5.6 min; routed $6.58, 20,042,524 tokens, 21.2 min.

## One sentence per task

- **Task 1, cost:** routing cost more, about twice the baseline at list price ($4.03 against $2.09, median) with 2.9 times the tokens, and took 2.7 times as long.
- **Task 1, quality:** better; both judges preferred the routed result in both runs, and in run 1 both found a factual error in the baseline result (criterion 5) that its own check had passed.
- **Task 2, cost:** routing cost more, 2.8 times the baseline at list price ($6.58 against $2.36, median) with 4.9 times the tokens, and took 3.8 times as long.
- **Task 2, quality:** not better; in run 1 both judges preferred the baseline result, and in run 2 one judge preferred each, so that verdict is undecided.

## What the table does not support

- No saving of tokens, money or time on these two tasks. The routed arm cost more in all four pairs, by 87% to 192%.
- The scorecard's own "Net against the baseline (estimate)" printed "saved" (40% to 45%) in all four routed runs. That estimate prices the routed work pieces' own tokens as if Opus had used them. The measured single Opus agent used far fewer tokens than the pieces together, so the estimate pointed the wrong way every time. It is not evidence of a saving.
- Two tasks of one kind (read many files, write one judged report) are not a general result.

## Raw usage

| Task | Run | Arm | Input | Cache write | Cache read | Output at least | Checks $ | Foreman $ |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | Baseline | 50 | 260,417 | 2,971,562 | 11,017 | 0.54 | 0.07 |
| 1 | 1 | Routed | 138 | 940,731 | 9,022,141 | 46,438 | 0.58 | 0.21 |
| 1 | 2 | Baseline | 50 | 221,297 | 3,060,205 | 10,286 | 0.48 | 0.06 |
| 1 | 2 | Routed | 120 | 926,136 | 8,028,245 | 63,809 | 0.47 | 0.19 |
| 2 | 1 | Baseline | 50 | 245,423 | 3,188,106 | 14,273 | 0.44 | 0.08 |
| 2 | 1 | Routed | 198 | 1,113,176 | 16,814,942 | 116,843 | 0.45 | 0.24 |
| 2 | 2 | Baseline | 64 | 253,998 | 4,501,348 | 12,112 | 0.51 | 0.07 |
| 2 | 2 | Routed | 220 | 1,209,151 | 20,685,694 | 144,824 | 0.49 | 0.24 |

Each arm's scorecard, with agent ids and the per-piece board, is in the task folders (`baseline-run1.md` and so on). Judge scoring is in each task's `judge` folder, and the coin flips are in [coin-flips.txt](coin-flips.txt). The routed Sonnet verify piece was the largest single item in every routed run.

Total spent on this benchmark, all counted from transcripts: about 74 million tokens in the measured arms, 10.4 million for the eight judges, 13.0 million for the foreman session itself, and about 22 million wasted by the duplicate session described below. About 119 million in all.

## Deviations and incidents, stated plainly

1. **Material.** The task candidates on the owner's machine held private data, so two public plugin collections of the same shape were used instead, copied once and made read-only before the first run.
2. **Baseline told to work alone.** The baseline brief added "do not start other agents", so that it stayed one agent and every token it caused was in its own transcript.
3. **Foreman above its own threshold.** The skill says to hand over to a fresh chat above 150,000 tokens of context. The foreman session started at about 110,000 tokens of fixed setup and carried 157,000 to 230,000 tokens during the routed runs. It continued, to keep all runs in one measured session. This raises the routed foreman cost (the largest was $0.24 a run), so it works against routing, not for it.
4. **Owner messages during task 1 routed run 1.** The foreman answered one owner message inside that run's window, so that run's foreman figure includes the reply.
5. **Duplicate session in task 2 run 1.** One Haiku inventory piece called a hand-off tool by mistake and started a copy of the foreman session. The copy ran its own verify, write and check pieces and a second baseline agent on the same files at the same time, recorded one extra routed entry, then noticed and stopped. The transcripts show that the files judged for task 2 run 1 are exactly the ones this session's own agents wrote (the baseline file is byte-identical to its agent's write; the routed file was last written by this session's write piece, which read this session's own verified inventory). The extra entry is left out of the table; its tokens are in the total above. The "Running net" lines in the task 2 routed scorecards include that extra entry and are not used anywhere.
6. **Second judges.** BENCHMARK.md asks for a second judge when the first splits the criteria evenly or the results differ on one criterion only. Three first verdicts rested on identical criterion scores (no difference at all), which was treated as close too, so all four runs got a second judge. The published verdict is the two judges' agreement, or "undecided".
7. **Blinding.** Before judging, titles, source lines and MODEL lines were removed, and in the routed task 2 files three mentions of the prepared inventory were removed or reworded. Judges could read the source snapshot to check facts.
8. **Baseline checks.** The baseline arm's own check passed task 1 run 1 although both judges later found a factual error in it, and failed task 2 run 2 on criterion 2 (the judges scored that criterion yes). The baseline arm has no re-run step, so neither result was changed.
