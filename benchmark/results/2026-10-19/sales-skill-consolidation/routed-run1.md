# Routed, run 1 (order: baseline first, routed second)

Agents: inventory acc15f6bdb220ba60, a26b6ee74b3d06ab4, aa8174d3e09af985d (haiku); verify and merge a0f0a098ef75af456 (sonnet, 15 corrections); write addbe279c1fdb5bfb (opus); check aae8f3a3cefba3605 (opus). Check answer: ALL YES. No escalations.

Note: the owner sent two messages during this run and the foreman answered one of them inside the run window, so the foreman figure includes that reply.

```
Quartermaster board

| Model | Piece | Status | Tokens | Time |
|---|---|---|---|---|
| Fable | not needed for this task | - | - | - |
| Opus | write recommendation (assemble) | done | 1,917,036 | 5:05 |
| Opus | check (check) | done | 866,225 | 52s |
| Sonnet | verify and merge inventory | done | 4,972,900 | 4:21 |
| Haiku | inventory skills 1-12 | done | 999,090 | 1:37 |
| Haiku | inventory skills 13-24 | done | 773,971 | 1:28 |
| Haiku | inventory skills 25-36 | done | 480,226 | 1:12 |

Used: 10,009,448 tokens by 6 agents (input 138, cache write 940,731, cache read 9,022,141, output at least 46,438). By model: Opus 2,783,261, Sonnet 4,972,900, Haiku 2,253,287.
Overhead: plan $0.00, checks $0.58, foreman $0.21, together $0.78 (19% of this run).
Baseline (estimate): the work pieces on one Opus agent, same tokens, $6.86.
Net against the baseline (estimate): saved $2.76 (40%)
Time won: 2.1 minutes (active 14.6, elapsed 12.5)
Running net (estimates): $2.76 over 1 run. Best run: $2.76 (Benchmark T1 sales skill consolidation, routed run 1).
How your subscription weighs these tokens is not published. Dollars are Anthropic API list-price estimates, not a bill.
For reference (estimates): all pieces on Fable $16.34, all on Opus $7.44.
```
