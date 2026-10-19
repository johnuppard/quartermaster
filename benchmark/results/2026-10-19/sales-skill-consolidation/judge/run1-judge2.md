# T1-r1 scoring (blind judge)

Sources checked: all 36 SKILL.md frontmatter descriptions, plus targeted reads and greps of crm-hygiene-check, pipeline-review, deal-review, deal-advance-gap, handle-objection, competitive-intelligence, lead-triage, route-lead, setup, account-tiering, account-research, draft-outreach, update-opportunity, close-plan, deal-signals, daily-briefing, and file and block sizes.

## Result A

1. Every skill accounted for: **yes**. Section 1 is a 36-row table, one verdict per skill (Keep, Merge, Rewrite description), with totals 14 / 7 / 15.
2. Overlaps named and grounded: **yes**. Overlaps A to L plus a low-overlap list, each a named pair or group with the concrete shared steps (for example the 5 of 7 hygiene checks listed by name).
3. Weak triggers named individually with reasons: **yes**. Section 3 table names each skill or pair, quotes the phrase, and says why it misfires (collision, generic noun, read-only skill promising "clean up").
4. Merge list prioritised with reason and what survives: **yes**. Merges 1 to 7 in stated priority order, each with Reason, "Merged skill keeps", description changes and references to update.
5. No factual errors on five spot checks: **yes**.
   - crm-hygiene-check has 7 checks, 5 match pipeline-review flags (amount and stage criteria unique): correct.
   - pipeline-review and account-tiering both refer to "the crm hygiene flow"; setup names crm-hygiene-check as a routine: correct (pipeline-review line 86, account-tiering line 100, setup line 155).
   - No skill names route-lead or competitive-intelligence outside itself: correct (grep).
   - deal-review probability floor 5%, ceiling 95%; output already lists "what's missing" and who/what/by-when actions: correct.
   - Sizes: deal-review 7,877, deal-advance-gap 7,876, setup 14,090 largest, Rules block 3,423 bytes x 36 = 123,228: correct.

## Result B

1. Every skill accounted for: **yes**. All 36 appear with a verdict across the merge table (section 4) and the "Do not merge" table, though there is no single per-skill list and several verdicts must be assembled from two tables.
2. Overlaps named and grounded: **yes**. Table A to P with shared purpose and what is different, grounded in step contents (for example the "don't pretend otherwise" wording shared by handle-objection and competitive-intelligence, verified).
3. Weak triggers named individually with reasons: **yes**. Sections 3a to 3c name each skill with a reason (hidden deciding fact, phrase claimed twice, too generic or too short). 3d adds collisions with skills outside the plugin.
4. Merge list prioritised with reason and what survives: **yes**. Priorities 1 to 9 each with Result (what the merged skill does) and Reason. "What it keeps" is thinner than A but present.
5. No factual errors on five spot checks: **no**.
   - Rules block 3,424 bytes, identical in all 36, about 41% of 298,254 bytes: correct.
   - Description lengths 224 to 538, competitive-intelligence longest, win-loss-review 286 and 9th shortest: correct.
   - Threading paragraph in exactly call-summary, draft-outreach, inbox-sweep, schedule-meeting: correct.
   - ICP rubrics: tiering 0 to 10 weighted, triage strong/partial/miss, research strong/moderate/poor: correct.
   - "close-plan and deal-review already reference deal-advance-gap": wrong. deal-review never mentions deal-advance-gap; the reference runs the other way (deal-advance-gap line 18 names deal-review). The skills that name deal-advance-gap are close-plan and update-opportunity.

## Marks

A: y y y y y
B: y y y y n

## Verdict

VERDICT: A better

- A is accurate on every claim checked, and its single 36-row verdict table lets someone act without reconstructing decisions.
- A's merge list is the more actionable: each merge states what the survivor keeps, which trigger phrases move, which cross-references must be updated (and those references check out), plus a size ceiling.
- B adds useful extra angles (inconsistent ICP rubrics, cross-environment collisions, honest limits section), but has a factual error in a merge instruction and proposes riskier merges (deal-signals into daily-briefing, renewal mode into customer-health) with less detail on what survives.
