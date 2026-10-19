# T2-r1 scoring (blind judge)

## Result A

1. Coverage of all 54 folders: yes. "Folders checked (54 of 54)" names all 14 external and all 40 plugins folders, and lists those with no own finding.
2. Each finding names plugin, file and mismatch: yes. E.g. A7 "plugin-dev README.md line 201, /plugin install plugin-dev@claude-code-marketplace"; A1 quotes the github .mcp.json header.
3. Ordered by harm, rule stated: yes. "Ordering rule" defines five tiers plus a within-tier rule (silent failure above loud failure, more users first).
4. Conventions as patterns with counts or lists: yes. E1 to E10 give counts and plugin lists (install wording 11/1/3/1/1/1/26/10, .mcp.json shapes 5 vs 9, LICENSE missing in 10).
5. No false findings on five spot checks: yes.
   - A1 github: .mcp.json sends Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}, folder has no README. Confirmed.
   - A3 fakechat: .mcp.json command is bun, README contains no "bun" at all. Confirmed.
   - A7/A8 plugin-dev: line 201 uses @claude-code-marketplace; cc --plugin-dir at plugin-dev 207, 385 and hookify 295. Confirmed. 11 READMEs use /plugin install ...@claude-plugins-official. Confirmed.
   - B1 context7: README line 21 claims the key is picked up; .mcp.json has no header or env reference; plugin.json says "Authenticate with Context7 when prompted". Confirmed.
   - D2 hookify: README rule names warn-rm, block-dangerous-rm, warn-debug-code, require-tests-run differ from the four shipped examples/ files. Confirmed. (C2 kotlin-lsp is the only README without an H1: also confirmed.)
   - Minor softness: D4 says math-olympiad README "never names the skill", but the name appears as heading and install target. Arguable, not false.

## Result B

1. Coverage of all 54 folders: no. It states "all 54" and gives a group count table (12/28/14) naming only the exceptions; there is no list of the checked folders, so "none missing" cannot be verified by name.
2. Each finding names plugin, file and mismatch: yes. E.g. 1.1 table maps each external plugin to its .mcp.json requirement; P3 table names shipped file vs README text.
3. Ordered by harm, rule stated: yes. "Priority order: P1 ... P4" defined at top, plus a "Suggested order of fixes".
4. Conventions as patterns with counts or lists: yes. P4 gives lists and counts (version 14 of 40, .mcp.json shapes 5 vs 9, Python floors, no LICENSE in 10).
5. No false findings on five spot checks: yes.
   - P3 playground: FILES.txt has 6 templates; README lists 4 (code-map and diff-review missing). Confirmed.
   - 2.7 math-olympiad: links github.com/anthropics/anthropic/tree/staging/... Confirmed.
   - 2.9 feature-dev: "only reports high-confidence issues >=80" (line 303) vs "Important issues (confidence 50-74)" (line 311). Confirmed.
   - 2.9 security-guidance: line 136 cheaper model for false positives, then "if precision is the priority, stay on the default". Confirmed.
   - 2.5 ralph-loop: line 186 path uses ralph-wiggum, manifest name ralph-loop. Confirmed. (Also checked: 2.10 project-artifact plan restriction in README only, plugin-dev cites multi-agent-swarm, hookify mixes /hookify and /hookify:list. All confirmed.)
   - Minor overstatement: 1.2 says the plugin-dev install "fails" as written, which the snapshot cannot prove.

## Marks

A: y y y y y
B: n y y y y

## Verdict

B better.
- Both files are accurate on every spot check and share the same core high-harm findings (external plugins without README, context7 key, Bun, cc vs claude, wrong install lines, missing manifests).
- B finds more real, verified problems a maintainer would fix: playground's two undocumented templates, the private math-olympiad link, feature-dev and security-guidance self-contradictions, project-artifact plan limit, unpinned @latest and git sources, telemetry opt-out differences, and it ends with a concrete fix order.
- A is more rigorous on coverage (explicit 54-folder list) and finer in its ranking rule, and catches the hookify example-name mismatch, but misses several of B's real defects. For acting on the list, B's extra correct findings outweigh A's tidier coverage.
