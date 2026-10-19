# Baseline, run 2 (order: baseline first, routed second)

Agents: work a46e47b367bf8b294 (opus), check a7a31ca5717fa4ef3 (opus). Check answer: NOT ALL YES (criterion 2: some convention bullets name no plugin or file). The baseline arm is one agent plus a check, so nothing was re-run.

```
Quartermaster board

| Model | Piece | Status | Tokens | Time |
|---|---|---|---|---|
| Fable | not needed for this task | - | - | - |
| Opus | whole task | done | 4,053,066 | 5:18 |
| Opus | check (check) | done | 714,456 | 51s |
| Sonnet | not needed for this task | - | - | - |
| Haiku | not needed for this task | - | - | - |

Used: 4,767,522 tokens by 2 agents (input 64, cache write 253,998, cache read 4,501,348, output at least 12,112). By model: Opus 4,767,522, Sonnet 0, Haiku 0.
Overhead: plan $0.00, checks $0.51, foreman $0.07, together $0.58 (23% of this run).
Baseline (estimate): the work pieces on one Opus agent, same tokens, $1.90.
Net against the baseline (estimate): cost $0.58 more (31%)
No time won (under a minute)
Running net (estimates): -$2.26 over 4 runs. Best run: -$0.52 (Benchmark T2 marketplace README audit, baseline run 1).
How your subscription weighs these tokens is not published. Dollars are Anthropic API list-price estimates, not a bill.
For reference (estimates): all pieces on Fable $4.91, all on Opus $2.41.
```
