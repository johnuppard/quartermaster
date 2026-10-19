# Routed, run 2 (order: routed first, baseline second)

Agents: inventory ae3d03a33fd18f195, a8d7ab4870f8cde8b, abcaceb2bf75b7c45 (haiku); verify and merge abd30d06d37511253 (sonnet, 14 corrections); write ab32810552d3fda72 (opus); check aed1fa76cd0f1dc92 (opus). Check answer: ALL YES. No escalations.

```
Quartermaster board

| Model | Piece | Status | Tokens | Time |
|---|---|---|---|---|
| Fable | not needed for this task | - | - | - |
| Opus | write recommendation (assemble) | done | 1,490,351 | 4:54 |
| Opus | check (check) | done | 410,599 | 28s |
| Sonnet | verify and merge inventory | done | 4,932,200 | 4:01 |
| Haiku | inventory skills 1-12 | done | 630,887 | 1:27 |
| Haiku | inventory skills 13-24 | done | 756,411 | 1:17 |
| Haiku | inventory skills 25-36 | done | 797,862 | 1:30 |

Used: 9,018,310 tokens by 6 agents (input 120, cache write 926,136, cache read 8,028,245, output at least 63,809). By model: Opus 1,900,950, Sonnet 4,932,200, Haiku 2,185,160.
Overhead: plan $0.00, checks $0.47, foreman $0.19, together $0.66 (17% of this run).
Baseline (estimate): the work pieces on one Opus agent, same tokens, $7.04.
Net against the baseline (estimate): saved $3.08 (44%)
Time won: 2.4 minutes (active 13.6, elapsed 11.3)
Running net (estimates): $5.84 over 2 runs. Best run: $3.08 (Benchmark T1 sales skill consolidation, routed run 2).
How your subscription weighs these tokens is not published. Dollars are Anthropic API list-price estimates, not a bill.
For reference (estimates): all pieces on Fable $16.78, all on Opus $7.51.
```
