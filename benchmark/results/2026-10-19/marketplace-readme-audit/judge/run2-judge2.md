# T2-r2 scoring (blind judge)

Snapshot checked: snap/marketplace (40 folders under plugins, 14 under external_plugins, 152 files).

## Result A

1. Coverage of all 54: **yes**. Opening line states all 54 (40 + 14) were read; every one of the 54 folder names appears somewhere in the file (checked by search). No per-folder ledger, so coverage is asserted rather than tabulated.
2. Plugin, file and mismatch named: **yes**. Each item names the plugin and the file (README, .mcp.json, plugin.json, FILES.txt) with the quoted text or command, e.g. context7 README line vs .mcp.json content.
3. Ordered by harm, rule stated: **yes**. Three tiers defined at the top (cannot install/start, README vs files, conventions); Tier 1 is somewhat overloaded (skill-creator one-paragraph README sits in Tier 1).
4. Conventions as patterns with counts or lists: **yes**. Tier 3 gives install-form table with plugin lists, .mcp.json shape split 5 vs 9, version 14 of 40, Python minimums per plugin, telemetry opt-out differences.
5. Spot check of five findings: **yes**, all five true.
   - context7: README says key "picks up automatically"; .mcp.json has only type and url; manifest says "Authenticate with Context7 when prompted". True.
   - plugin-dev: line 201 `@claude-code-marketplace`, line 123 "multi-agent-swarm", line 386 "marketplace-publishing guidelines", skill-reviewer.md in FILES.txt but not named. True.
   - security-guidance: manifest homepage is claude-plugins-official, README line 142 sends issues to anthropics/claude-code. True.
   - pr-review-toolkit: no mention of review-pr; line 286 build-validator; line 301 claude-cli-internal; line 186 `/plugins`. True.
   - Manifest field counts: version in 14 of 40; only cwc-makers has homepage, repository, license and keywords; claude-security license plus keywords; channel plugins keywords only. True. (Also confirmed: only clangd-lsp mentions Windows among LSP READMEs; commit-commands has clean_gone.)

## Result B

1. Coverage of all 54: **yes**. Explicit 54-row table with README, manifest and .mcp.json presence and the findings per folder.
2. Plugin, file and mismatch named: **yes**. Every finding gives the file path, usually with line numbers and a quote.
3. Ordered by harm, rule stated: **yes**. Tiers A to D defined with a tie-break rule (wrong statement before missing step, then likelihood); patterns sorted by number of plugins touched.
4. Conventions as patterns with counts or lists: **yes**. P1 to P10 with counts and plugin lists (install forms, manifest fields, missing README/manifest/LICENSE, heading styles, .mcp.json shape, command prefixing, name collisions, version minimums).
5. Spot check of five findings: **yes**, all five true.
   - A1 plugin-dev: lines 198, 201 and 381 say claude-code-marketplace; 11 other READMEs use @claude-plugins-official. True (12 READMEs carry /plugin install, plugin-dev the only outlier).
   - A3 imessage: line 3 "No external server..."; Bun only on line 12; .mcp.json runs bun. True.
   - D1 example-plugin: manifest promises agents and hooks; FILES.txt has neither. True.
   - C2: code-review line 89, commit-commands line 130, agent-sdk-dev lines 152 and 155 say "included in the Claude Code repository". True.
   - P2 and P6 counts: author.email 26 of 36, keywords 6, homepage 2, license 2, repository 1; Installation 20, Install 6, Setup 2, Quick Setup 2 plus Quick setup 1, Requirements 10, Prerequisites 4, Usage 10, Use 3. All exact.

## Comparison

Both files are accurate on every claim checked and meet all five criteria. A finds more distinct real problems a maintainer would fix: receipts and session-report need Node.js unstated, pr-review-toolkit points at an internal repo and a non-existent build-validator, plugin-dev cites a non-existent multi-agent-swarm plugin, security-guidance homepage vs issue tracker mismatch, asana's past shutdown date framed as upcoming, mcp-tunnels assumes internal environments, math-olympiad needs LaTeX, code-modernization calls Python optional while its core outputs need it, and telemetry opt-out differences. A also ends with a concrete fix order. B is the more traceable document (line numbers, per-folder ledger, a "checked and not reported" section, tighter tier definitions) and has a few findings A lacks (example-plugin manifest promising agents and hooks, unmentioned hookify components, skills never named in READMEs), but it misses more real problems than A does.

VERDICT: A better
Reasons: both are accurate, but A surfaces noticeably more genuine setup and consistency problems and gives a fix order a maintainer can act on directly. B's ordering rule and evidence trail are cleaner, which narrows the gap but does not outweigh A's wider coverage of real issues. A's Tier 1 is a little overloaded, a minor prioritisation weakness.
