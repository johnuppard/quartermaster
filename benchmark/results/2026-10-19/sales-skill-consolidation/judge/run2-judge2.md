# T1-r2 scoring: A vs B

Task: consolidation recommendation for the 36 skills of the sales plugin (overlaps, weak triggers, prioritised merge list).

## Result A

1. Every skill accounted for with a verdict: **yes**. The 16 skills touched by merge items 1 to 9 plus the 20 named in "Not recommended for merging" make 36. There is no single verdict table, so the reader has to assemble it.
2. Overlaps as named pairs or groups with concrete shared purpose: **yes**. Section 2 tables name each pair with estimated shared scope and file evidence (for example lead-triage's "that is the routing answer" owner check, and deal-advance-gap's self-definition against deal-review).
3. Weak-trigger descriptions named individually with a reason: **yes**. The section 3 table gives 15 rows, each with the problem, the colliding phrase or skill, and a fix (for example win-loss-review "what's working" is too generic).
4. Merge list in priority order with reason and what the merged skill keeps: **yes**. Ten numbered items, each with a reason and what it keeps (for example item 4 keeps hygiene's amount = 0, stage-criteria evidence and suggested values). Items 8 to 10 are refactors, not merges, but each is still reasoned.
5. No factual errors on a spot check of five claims: **yes**.
   - Rules block is 585 words and identical in all 36 files: verified (one checksum across 36 files, 585 words).
   - Thread preview rule appears in 7 files (account-context, call-prep, call-summary, customer-health, deal-signals, draft-outreach, inbox-sweep): verified.
   - Scheduled-run rule appears in 8 named files: verified, exact list matches.
   - The Gong ask_account route appears in call-prep, call-summary and customer-voice: verified.
   - The plugin is about 49,600 words and descriptions average about 58 words (setup 81, competitive-intelligence 75, log-activity 73): verified (49,570 words; about 57 words on average; 80/74/72 without the field label). These are within rounding.
   - One soft point, not counted as an error: "Only account-context and rep-context carry a 'not this, use that' note" overlooks account-research's "when the company is a prospect" qualifier. That qualifier names no other skill, though.

## Result B

1. Every skill accounted for with a verdict: **yes**. An explicit 36-row verdict table gives each skill keep, merge or rewrite with a reason, and the totals add up (6 + 6 + 10 + 14 = 36).
2. Overlaps as named pairs or groups with concrete shared purpose: **yes**. O1 to O10 each name the group, its grade, the shared purpose with quoted file text, what differs, and the trigger collision (for example crm-hygiene-check and pipeline-review on the same 14-day, past-close, 2x-median and single-threaded flags).
3. Weak-trigger descriptions named individually with a reason: **yes**. Fifteen numbered items ranked by misroute likelihood, each with a reason and a rewrite, plus lower-severity patterns (conditions written as phrases).
4. Merge list in priority order with reason and what the merged skill keeps: **yes**. Six merges plus one partial move, each with a reason, a "keeps" list, the reference updates needed in other skills, and a size estimate. It also lists rejected merges with reasons.
5. No factual errors on a spot check of five claims: **yes**.
   - Rules block is 3,423 bytes in all 36 files, 123,228 of 298,254 bytes (41%): verified (298,254 total; the block is 3,424 bytes with its newline).
   - competitive-intelligence's description is 538 characters with 11 quoted phrases: verified (538).
   - log-activity is named by 12 other skills, with an exact list: verified, the list matches.
   - setup is 14,090 bytes: verified.
   - deal-review uses "Floor 5%, ceiling 95%". team-pipeline's purpose is "forecast call or 1:1 prep". No other skill names route-lead or team-pipeline. pipeline-review and account-tiering mention "the crm hygiene flow": all verified.

## Marks

A: y y y y y
B: y y y y y

## Verdict

B better.

- Both are accurate and pass every criterion. B is more actionable for someone who has to carry out the work. It has an explicit per-skill verdict table with reconciled totals, and each merge lists what it keeps, which other skills need reference updates, and a size estimate.
- B ranks weak triggers by misroute likelihood. It explains why near-merges were rejected (customer-health/renewal-radar, call-summary/log-activity, deal-signals/pipeline-review), which shows sound judgment.
- A has useful extras: a boilerplate extraction plan that keeps the safety lines inline, and the cross-plugin lead-triage name clash. But its merge list mixes true merges with refactors, and its verdicts are only implied.
