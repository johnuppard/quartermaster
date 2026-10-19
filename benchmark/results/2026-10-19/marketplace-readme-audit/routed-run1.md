# Routed, run 1 (order: routed first, baseline second)

Agents: inventory a761df80708a41f1f, acd42ca3567c01ad3, a50d7b7a44cf02349 (haiku); verify and merge a596c66401dcdb657 (sonnet, 21 corrections); write a4c163974c2ee450a (opus); check a8b05d7deba136f0b (opus). Check answer: ALL YES. No escalations.

Note: inventory agent acd42ca3567c01ad3 started a copy of the foreman session by mistake. The copy ran its own verify, write and check pieces on the same files and recorded one extra entry; that entry is left out, and the files judged are this session's own (see RESULTS.md, deviation 5). The "Running net" line below includes the extra entry and is not used.

```
Quartermaster board

| Model | Piece | Status | Tokens | Time |
|---|---|---|---|---|
| Fable | not needed for this task | - | - | - |
| Opus | write audit (assemble) | done | 4,294,691 | 5:10 |
| Opus | check (check) | done | 500,546 | 28s |
| Sonnet | verify and merge inventory | done | 9,140,554 | 9:32 |
| Haiku | inventory folders 1-18 | done | 872,486 | 2:13 |
| Haiku | inventory folders 19-36 | done | 1,699,476 | 3:48 |
| Haiku | inventory folders 37-54 | done | 1,537,406 | 3:48 |

Used: 18,045,159 tokens by 6 agents (input 198, cache write 1,113,176, cache read 16,814,942, output at least 116,843). By model: Opus 4,795,237, Sonnet 9,140,554, Haiku 4,109,368.
Overhead: plan $0.00, checks $0.45, foreman $0.24, together $0.69 (12% of this run).
Baseline (estimate): the work pieces on one Opus agent, same tokens, $10.81.
Net against the baseline (estimate): saved $4.91 (45%)
Time won: 5.3 minutes (active 25.0, elapsed 19.7)
Running net (estimates): $15.25 over 4 runs. Best run: $4.91 (Benchmark T2 marketplace README audit, routed run 1).
How your subscription weighs these tokens is not published. Dollars are Anthropic API list-price estimates, not a bill.
For reference (estimates): all pieces on Fable $23.96, all on Opus $11.27.
```
