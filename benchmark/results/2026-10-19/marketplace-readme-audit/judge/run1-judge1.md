# T2-r1 scoring

## Result A

1. All 54 covered: yes. Closing section "Folders checked (54 of 54)" lists every folder by name; a grep of all 54 snapshot folder names finds each one in A.md.
2. Plugin, file and mismatch named: yes. Each finding names plugin, file, often line number and the quoted text (for example plugin-dev README line 201, ralph-loop README line 186).
3. Ordered by harm, rule stated: yes. Five tiers with an explicit "Ordering rule" section and a within-tier tiebreak (silent failure above loud failure, more users first).
4. Conventions as patterns with counts: yes. E1 to E10 give counts and plugin lists (install wording 11/1/3/1/1/1/26/10, version 14 of 40, .mcp.json shapes 5 vs 9, heading counts).
5. No false findings on spot check: yes. Checked five:
   - A7 plugin-dev README line 201 `/plugin install plugin-dev@claude-code-marketplace`; 11 READMEs use `@claude-plugins-official`. Confirmed.
   - A8 `cc --plugin-dir` at plugin-dev lines 207 and 385, hookify line 295. Confirmed.
   - B1 context7 README line 21 claims the key is picked up; `.mcp.json` has no header or env reference; plugin.json says "Authenticate with Context7 when prompted". Confirmed.
   - B3 ralph-loop README line 186 path uses `ralph-wiggum`; manifest name is `ralph-loop`. Confirmed.
   - D2 hookify FILES.txt lists `conversation-analyzer`, `writing-rules`, and examples named `console-log-warning`, `dangerous-rm` etc., while README uses `warn-rm`, `block-dangerous-rm`. Confirmed.
   Also checked: version present in 14 manifests, author missing in exactly the four channel plugins, `## Installation` in 20 and `## Install` in 6, Troubleshooting in the 8 named, kotlin-lsp the only README without an H1, claude-code-setup README never names `claude-automation-recommender`, pr-review-toolkit README never mentions `review-pr`. All correct.

A: y y y y y

## Result B

1. All 54 covered: yes. Coverage table by group (12 LSP, 28 other plugins, 14 external, totals 44/40/14) and every one of the 54 folder names appears in the body; no explicit one-line checklist, but none is missing.
2. Plugin, file and mismatch named: yes. Findings name plugin, file and quote the text (context7 `.mcp.json` URL, ralph-loop cache path, feature-dev confidence ranges), though without line numbers.
3. Ordered by harm, rule stated: yes. P1 to P4 rule stated at the top ("P1 means a user cannot install or start..."), plus a suggested fix order.
4. Conventions as patterns with counts: yes. P4 gives plugin lists and counts for command naming, duplicate agents, .mcp.json shapes (5 vs 9), version 14 of 40, missing LICENSE (10), Python floors.
5. No false findings on spot check: yes. Checked five:
   - playground README lists 4 templates; FILES.txt ships 6 including `code-map` and `diff-review`. Confirmed.
   - feature-dev README line 303 "only reports high-confidence issues >=80" vs line 311 "Important issues (confidence 50-74)". Confirmed.
   - math-olympiad README line 25 links `github.com/anthropics/anthropic/tree/staging/...`. Confirmed (private repo is an inference, reasonable).
   - project-artifact README lines 28-29 "available in beta on Team and Enterprise plans"; manifest only says "claude.ai login". Confirmed.
   - plugin-dev README line 123 cites "multi-agent-swarm" as a real-world example; no such folder in the snapshot. Confirmed.
   Also checked: clangd PATH export appears only as a comment in the code block, security-guidance troubleshooting line 136 text as quoted, context7 and ralph-loop claims as in A. Minor overstatement: "As written, the install fails" for plugin-dev cannot be proven without marketplace.json, but the mismatch itself is real.

B: y y y y y

## Verdict

B better.

Both are accurate on every spot check and meet all five criteria. B finds more distinct real problems a maintainer must fix that A missed: two undocumented playground templates, the feature-dev confidence contradiction, the private math-olympiad link, the project-artifact plan restriction missing from the manifest, plugin-dev utility scripts with no path, ruby-lsp Bundler PATH gap, unpinned `@latest` servers, and the bare versus namespaced command naming pattern. A is more precise (line numbers, hedged claims, an explicit 54-folder checklist, a finer within-tier ordering rule and fuller heading counts), but B's wider coverage and closing fix order make it more useful to act on.
