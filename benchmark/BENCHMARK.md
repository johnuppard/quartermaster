# Benchmark: does Quartermaster save anything?

Quartermaster claims nothing about saving until this benchmark shows it. The method is fixed here so anyone can repeat it and so the results cannot be tuned after the fact.

## The question

For a large, splittable task, does routing the pieces through Quartermaster use fewer tokens at list price, take less elapsed time, and produce a result at least as good as one Opus agent doing the whole task?

## Fairness rules

1. **Same task sentence** for both arms, saved to a file before either run. It names the output file and format, and nothing else. It must contain judgment, not only mechanical work (for example: read these sources, decide X, write Y).
2. **Baseline arm:** one Opus agent, started fresh, given the task sentence and the escalation clause, free to choose its method. Its start-up cost counts, as it does for every piece.
3. **Routed arm:** the foreman runs the task exactly as the skill says (gate, pieces, checks, record). Every agent counts, and the foreman's own tokens between the first and last agent count as overhead.
4. **Blind judge:** a fresh Opus agent gets the two results renamed A and B by a coin flip recorded in a file it never sees, with headers, footers and model lines stripped, plus the task sentence and the done criteria. It scores each criterion yes or no with evidence and gives one verdict: A better, B better, or equal. Two judges when the verdict is close.
5. **More than one run:** at least two runs per arm per task, and at least two tasks, before any number is published.
6. **Counting:** tokens from the transcripts with the same rules as `record` (one count per message, output at least); elapsed time from first to last timestamp; list prices from `prices.json`. Nothing is estimated that can be counted.

## Procedure, fixed before any run

- **Tasks:** at least two, chosen and written down before the first run, each large and splittable (more than one context of reading, or more than four independent pieces) and each with real judgment in it. The task sentence and three to five done criteria are written by the person running the benchmark, before either arm starts, in `benchmark/results/<date>/<task>/task.md`.
- **Order and conditions:** the arms alternate order between runs; the repository or data is reset to the same state before each run; the same effort setting; no cache warming between arms.
- **Baseline tokens:** recorded with `record` as one work piece plus its check piece, so both arms are counted the same way.
- **Elapsed time:** routed arm, from the foreman's first agent call to the last agent's return; baseline, from the agent's first record to its last.
- **Combining runs:** the median per arm; "no difference" when the medians are within ten percent of each other.
- **Close verdicts:** a second judge when the first splits the criteria evenly or the two results differ on one criterion only; the published verdict is the judges' agreement, or "undecided".
- **Raw data:** transcripts' usage, the judge's scoring and the coin flips, under `benchmark/results/<date>/<task>/`.

## What is published

A table per task and run: tokens by model and arm, list-price estimate, elapsed time, judge verdict, and the net (baseline estimate minus routed cost including overhead). Then one sentence per task: saved, cost more, or no difference, and on quality: better, equal, worse. The README repeats only what this table says.

## Results

None yet.
