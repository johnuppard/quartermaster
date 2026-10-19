# T2-r2 blind judging: A vs B

Snapshot used for checks: scratchpad/snap/marketplace (plugins: 40 folders, external_plugins: 14 folders).

## Result A

1. Coverage of all 54 folders: **yes**. The scope line names all 54 (40 plugins, 14 external), and every folder name appears in the body (the 12 LSP plugins by short name). Weaker than B: there is no per-folder checklist, so a reader has to cross-reference to confirm nothing was skipped.
2. Each finding names plugin, file and mismatch: **yes**. For example: "context7 ... `.mcp.json` is only {type http, url ...}" against the README line quoted. The Tier 2 table names the plugin and the mismatch, with the file clear from context. No line numbers.
3. Ordered by harm, rule stated: **yes**. Tier 1/2/3 rule stated at the top. Tier 1 is overloaded, though. It mixes real blockers (github token, Bun) with softer items (skill-creator one-paragraph README, math-olympiad LaTeX and eval link).
4. Conventions as patterns with counts or lists: **yes**. Tier 3 has tables and lists for install forms, command naming, .mcp.json shape, version pinning, manifest fields (14 of 40 with version), requirements and telemetry.
5. No false findings on five spot checks: **yes**.
   - context7 `.mcp.json` has no key or header, README line 21 says it picks up `CONTEXT7_API_KEY`, and the manifest says "Authenticate with Context7 when prompted". Confirmed.
   - plugin-dev README lines 198 to 201 and 381 use `claude-code-marketplace`. Confirmed.
   - ralph-loop README line 186 uses `ralph-wiggum` in the cache path, and line 197 says `/help`. Confirmed.
   - playground FILES.txt lists 6 templates, and the README lists 4 (code-map and diff-review missing). Confirmed.
   - `version` appears in 14 of 40 manifests. Confirmed.
   - Extra checks: hookify, pr-review-toolkit and plugin-dev README say MIT, while math-proof, cwc-makers and code-modernization say Apache. Confirmed. asana "shuts down on Wed 5 Aug 2026" confirmed. kotlin-lsp has no H1 confirmed. commit-commands `clean_gone.md` confirmed. pr-review-toolkit's `claude-cli-internal` and `build-validator` confirmed.
   - A few items are speculative and flagged "(verify)", such as the `/code-review` collision with the built-in and `ensure_agent_sdk.py`. They are labelled, not stated as fact.

## Result B

1. Coverage of all 54 folders: **yes**. The "Folders checked (54 of 54)" table lists every folder with README, manifest and .mcp.json presence and the findings that apply to each.
2. Each finding names plugin, file and mismatch: **yes**. Every finding gives the file path, usually with line numbers (for example "plugins/plugin-dev/README.md, lines 198 to 201").
3. Ordered by harm, rule stated: **yes**. Tiers A to D are defined, with a tie-break inside each tier (a wrong statement before a missing step, then likelihood of hitting a user). Patterns are sorted by how many plugins they touch.
4. Conventions as patterns with counts or lists: **yes**. P1 to P10 have counts and plugin lists: install forms over 44 READMEs, manifest fields over 40, heading styles with counts, .mcp.json shape 5 vs 9, duplicate component names.
5. No false findings on five spot checks: **yes**.
   - A1: plugin-dev lines 198 to 201 and 381 say `claude-code-marketplace`. Confirmed.
   - D1: the example-plugin manifest says "commands, agents, skills, hooks, and MCP servers", and FILES.txt has no agents/ or hooks/. Confirmed.
   - D4: plugin-dev line 390 says "seven comprehensive skills and three validation agents", and FILES.txt has agent-creator, plugin-validator and skill-reviewer. Confirmed.
   - D6: hookify FILES.txt ships conversation-analyzer, writing-rules and 4 examples/ rules. The README never names them, and only writes dangerous-rm out inline. Confirmed.
   - P2/P6: author.email is in 26 of 36 manifests with an author. "## Installation" heads 20 READMEs, and "## Install" heads 6 (the 6 named). Confirmed.
   - C5: the 13 listed READMEs have no install or setup heading and no `/plugin install` line. Confirmed.

## Comparison

- Accuracy: both passed every spot check. B labels its limits and adds a "checked and not reported" section, which removes false positives up front. A carries a few "(verify)" guesses.
- Completeness: A finds some real issues B misses:
  - code-modernization calls Python "optional" although the proof and the report need it;
  - security-guidance's homepage and issue links point to different repos;
  - the asana notice is stale;
  - receipts needs Node.js but does not say so;
  - math-olympiad needs LaTeX but does not say so;
  - telemetry opt-outs differ;
  - example-plugin has a duplicate `/example-command`.

  B finds some that A misses:
  - example-plugin's manifest promises agents and hooks that do not ship;
  - hookify's shipped components are never mentioned;
  - skill names are missing in claude-code-setup and frontend-design;
  - plugin-dev's "three validation agents" count.
- Prioritisation: B's four tiers, with a stated tie-break, are sharper. A's Tier 1 holds 15 items, several of which do not stop a plugin installing or starting.
- Actionability: B gives line numbers and a per-folder findings index, so a maintainer can check and assign each item quickly. A adds a useful fix order.

## Marks

A: y y y y y / B: y y y y y

VERDICT: B better

Reasons: both are accurate on spot checks and meet every criterion. B is easier to act on. It has line-level citations, an explicit 54-row coverage table, a stated within-tier tie-break and a list of checked non-issues. A finds somewhat more distinct problems, but its Tier 1 mixes true install blockers with documentation gaps, which weakens the harm ordering.
