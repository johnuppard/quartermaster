# Task: sales skill consolidation

Written 2026-10-19, before any run. Material: a read-only snapshot of a public plugin's skills (the "sales" plugin, version 2.0.1: 36 skills, one SKILL.md each, about 298,000 characters), copied to `$SNAP/sales` before the first run and not changed between runs. `$SNAP` and `$OUT` are replaced with real paths in each run; nothing else in the sentence changes.

## Task sentence

Read all 36 SKILL.md files under $SNAP/sales/skills (and the plugin manifest in $SNAP/sales/.claude-plugin/plugin.json) and write one markdown file to $OUT: a consolidation recommendation that says which skills overlap in purpose and how much, which skill descriptions will not trigger reliably and why, and a prioritised merge list with a reason for each merge.

## Done criteria

1. Every one of the 36 skills is accounted for: named in the file at least once with a verdict (keep, merge, or rewrite the description).
2. Each overlap is a named pair or group with the concrete shared purpose, grounded in what the skill files say.
3. Each weak-trigger description is named individually with a specific reason (for example: no trigger phrases, too broad, collides with another skill's phrases).
4. The merge list is in priority order, and each merge gives a reason and what the merged skill keeps.
5. No factual errors about the skills (names, what they do, what their descriptions say) on a spot check of five claims against the source files.
