# Task: marketplace README and manifest audit

Written 2026-10-19, before any run. Material: a read-only snapshot of a public plugin marketplace (54 plugin folders: 40 under `plugins`, 14 under `external_plugins`), holding each plugin's README.md, its `.claude-plugin/plugin.json` and `.mcp.json` where present, and a FILES.txt listing every file the plugin actually ships; about 215,000 characters. Copied to `$SNAP/marketplace` before the first run and not changed between runs. `$SNAP` and `$OUT` are replaced with real paths in each run; nothing else in the sentence changes.

## Task sentence

Read the README, manifest and FILES.txt of every plugin folder under $SNAP/marketplace/plugins and $SNAP/marketplace/external_plugins (54 folders) and write one markdown file to $OUT: a prioritised list of inconsistencies and missing setup steps, covering where a README or manifest disagrees with the files present, where a user could not install or start the plugin from its README alone, and where conventions differ across plugins, most harmful to a user first.

## Done criteria

1. All 54 plugin folders are covered: the file says which were checked, and none is missing.
2. Each finding names the plugin, the file and the specific mismatch or missing step, so it can be verified in the snapshot.
3. The list is ordered by harm to a user, and the ordering rule is stated.
4. Differences in convention across plugins are reported as patterns with counts or plugin lists, not only as single-plugin items.
5. No false findings on a spot check of five findings against the snapshot.
