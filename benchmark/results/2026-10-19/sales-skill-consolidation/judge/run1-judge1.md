# T1-r1 scoring

Source checked: snap/sales/skills (36 SKILL.md files) and plugin.json.

## Result A

1. All 36 accounted for with a verdict: **yes**. Section 1 is a 36-row table, each row has Keep, Merge or Rewrite description.
2. Overlaps are named pairs or groups with concrete shared purpose: **yes**. Overlaps A to L each name the skills and cite shared steps, data pulls and trigger phrases (for example hygiene's 5 of 7 checks matching pipeline-review flags).
3. Weak-trigger descriptions named individually with a reason: **yes**. Section 3 table names each skill and the exact phrase and why it misfires (for example customer-voice "what's coming up in calls", create-an-asset bare nouns).
4. Merge list in priority order with reason and what the merged skill keeps: **yes**. Merges 1 to 7, each with Reason, Merged skill keeps, description handling and references to update.
5. No factual errors on a spot check of five claims: **yes**.
   - lead-triage description starts "Score and route an inbound lead": correct.
   - route-lead Step 2 runs "lead-triage's scoring ... if not already attached": correct.
   - crm-hygiene-check has 7 checks, 5 of them match pipeline-review flags; amount and stage criteria unique: correct.
   - deal-advance-gap body says "`deal-review` scores where a deal stands today"; sizes 7,877 and 7,876 bytes; setup is largest at 14,090: correct.
   - No other skill names route-lead or competitive-intelligence; close-plan and update-opportunity name deal-advance-gap: correct.
   - (extra) deal-signals 21 days at early stage, inbound waiting 3+ business days; daily-briefing 14 days: correct.

## Result B

1. All 36 accounted for with a verdict: **yes**. 17 skills appear in the merge list and the other 19 in the "Do not merge" table with keep or description-fix verdicts. Less explicit than a per-skill table.
2. Overlaps are named pairs or groups with concrete shared purpose: **yes**. Overlap table A to P names skills, what is shared and what differs.
3. Weak-trigger descriptions named individually with a reason: **yes**. Sections 3a to 3c name each skill with a specific reason (split depends on unknown fact, shared phrase, generic wording).
4. Merge list in priority order with reason and what the merged skill keeps: **yes**. Priorities 1 to 9, each with a Result column (what it keeps) and a Reason column.
5. No factual errors on a spot check of five claims: **no**.
   - Description lengths (competitive-intelligence 538, setup 488, account-research 449; shortest 224 to 258; win-loss-review 286 is 9th shortest) and total 298,254 bytes: correct.
   - Rules block 3,424 bytes, byte-identical in all 36: correct (one hash).
   - "don't pretend otherwise" appears in both competitive-intelligence and handle-objection: correct.
   - crm-hygiene-check "close date unchanged since creation" check: correct.
   - "close-plan and deal-review already reference deal-advance-gap": wrong. deal-review never names deal-advance-gap; the files that do are close-plan and update-opportunity. So the reference-update instruction for priority 2 points at the wrong file and misses update-opportunity.
   - (extra) ICP scales: tiering 0 to 10 weighted, triage strong/partial/miss, research strong/moderate/poor: correct.

## Verdict

A better.

- A is fully accurate on every claim checked, while B's merge-2 instruction names the wrong file to update and misses update-opportunity.
- A's merge list is more actionable: each merge says what the merged skill keeps step by step, how the description changes, which references to update, and the size cost.
- B adds useful extras (description-length data, ICP rubric drift, honest limits), but some judgment is weaker (folding deal-signals into daily-briefing bloats the morning digest) and section 3d goes outside the source files.
