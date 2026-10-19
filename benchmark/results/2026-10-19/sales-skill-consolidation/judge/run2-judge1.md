# T1-r2 blind scoring: A vs B

Sources checked: all 36 SKILL.md files and plugin.json under snap/sales.

## Result A

1. All 36 accounted for with a verdict: **yes**. Every skill appears in a merge item, a move item, the section 3 rewrite table, or the "Not recommended for merging" / section 2.3 keep lists (daily-briefing via item 9 "Do not merge the skills"). Less explicit than a per-skill table, but complete.
2. Overlaps as named pairs or groups with concrete shared purpose: **yes**. Sections 2.1 and 2.2 name each pair or group with an estimated share and file-grounded evidence (for example the identical in-deal answer shape in handle-objection and competitive-intelligence Mode A).
3. Weak-trigger descriptions named individually with a specific reason: **yes**. Section 3 table gives skill, problem, colliding phrase or skill, and fix for 15 skills or pairs, plus cross-cutting patterns.
4. Merge list in priority order with reason and what is kept: **yes**. Ten numbered items with a stated priority rule; each gives a reason and what the surviving skill keeps (for example item 2 keeps route-lead's rule chain, accept/override card and override log).
5. No factual errors on five spot checks: **yes**.
   - "Identical 585-word Rules block in all 36 files": confirmed, the paragraph hashes identically in all 36 and is 585 words.
   - deal-advance-gap defines itself against deal-review ("`deal-review` scores where a deal stands today. This skill looks forward"): confirmed, lines 18 to 19.
   - lead-triage "If an account already exists with an owner, that is the routing answer": confirmed, lines 46 to 47.
   - Scheduled-run rule in 8 named files (account-plan, call-summary, customer-health, crm-hygiene-check, expansion-whitespace, forecast, renewal-radar, stakeholder-map): confirmed exactly.
   - daily-briefing pipeline row "opps closing inside 14 days; stale flags": confirmed, line 42.
   - Minor imprecision outside the five: description word counts given as 81 / 75 / 73 measure as 80 / 74 / 72. Not material.

## Result B

1. All 36 accounted for with a verdict: **yes**. Explicit 36-row table with verdict and reason per skill; totals reconcile (6 merged away + 6 survivors + 10 rewrites + 14 keeps = 36), which I verified by listing.
2. Overlaps as named pairs or groups with concrete shared purpose: **yes**. O1 to O10 each name the group, grade it High / Medium / Low, quote the shared flags, thresholds or steps, and state what differs.
3. Weak-trigger descriptions named individually with a specific reason: **yes**. 15 numbered entries ordered by misroute likelihood, each with the colliding phrase, why it fails, and the rewrite; lower-severity patterns listed separately.
4. Merge list in priority order with reason and what is kept: **yes**. Six merges plus one partial move, each with reason, a "merged skill keeps" list, reference updates and a size estimate; rejected merges are also reasoned.
5. No factual errors on five spot checks: **yes**.
   - Rules paragraph 3,423 bytes, repeated in all 36, 123,228 of 298,254 bytes (41%): confirmed exactly.
   - competitive-intelligence description 538 characters with 11 quoted phrases: confirmed.
   - log-activity named by 12 other skills (list given): confirmed, the 12 listed plus log-activity itself.
   - "No other skill names route-lead" and "No other skill names team-pipeline": confirmed.
   - deal-review "Floor 5%, ceiling 95%" and deal-signals "next step unchanged for 21+ days"; setup is 14,090 bytes, the largest: all confirmed.

## Marks

A: y y y y y
B: y y y y y

## Verdict

**B better.**

- Both are accurate on every spot check, but B is easier to act on: an explicit per-skill verdict table, a "keeps" list per merge, the exact reference updates each merge requires in other files, and size estimates that flag when a merge would create the largest skill in the plugin.
- B's "merges considered and rejected" section shows its reasoning on the borderline cases, and its trigger list is ordered by misroute risk, so the reader knows where to start.
- A has real strengths B lacks (a boilerplate extraction plan with the safety lines kept inline, the "call instead of copy" items 8 and 9, and an honest limits section recommending a trigger eval), but its verdicts are scattered across sections and its overlap percentages are unmeasured estimates.
