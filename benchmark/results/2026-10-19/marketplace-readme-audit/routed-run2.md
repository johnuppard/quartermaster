# Routed, run 2 (order: baseline first, routed second)

Agents: inventory a39f17ff301ce8a2d, ad9ddd2af13812d0e, a5a39c5c16de47b08 (haiku); verify and merge a94ee9dbaa698e969 (sonnet, 40 corrections); write abb82aab6db16806c (opus); check af4482e05dccdd158 (opus). Check answer: ALL YES. No escalations.

```
Quartermaster board

| Model | Piece | Status | Tokens | Time |
|---|---|---|---|---|
| Fable | not needed for this task | - | - | - |
| Opus | write audit (assemble) | done | 3,576,602 | 5:45 |
| Opus | check (check) | done | 620,845 | 33s |
| Sonnet | verify and merge inventory | done | 14,102,605 | 12:08 |
| Haiku | inventory folders 1-18 | done | 487,851 | 1:56 |
| Haiku | inventory folders 19-36 | done | 1,415,918 | 3:52 |
| Haiku | inventory folders 37-54 | done | 1,836,068 | 3:40 |

Used: 22,039,889 tokens by 6 agents (input 220, cache write 1,209,151, cache read 20,685,694, output at least 144,824). By model: Opus 4,197,447, Sonnet 14,102,605, Haiku 3,739,837.
Overhead: plan $0.00, checks $0.49, foreman $0.24, together $0.74 (10% of this run).
Baseline (estimate): the work pieces on one Opus agent, same tokens, $12.59.
Net against the baseline (estimate): saved $5.34 (42%)
Time won: 5.1 minutes (active 27.9, elapsed 22.8)
Running net (estimates): $20.59 over 5 runs. Best run: $5.34 (Benchmark T2 marketplace README audit, routed run 2).
How your subscription weighs these tokens is not published. Dollars are Anthropic API list-price estimates, not a bill.
For reference (estimates): all pieces on Fable $27.53, all on Opus $13.08.
```
