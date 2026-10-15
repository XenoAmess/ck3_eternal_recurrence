# Routine siege checkpoint cadence

The helper keeps the existing dirty checkpoint policy and uses a ten-settled-cycle
interval for a verified one-day player siege followed by its same-day army
observations. Other phases use the existing five-cycle interval. Explicit
ordinary-planner `save-checkpoint` actions are unchanged.

The ten-cycle case requires an already returned, accepted AUTO result with
`native_war_siege_progress`, `player_siege`, a paused map postcondition, and
matching before/after war, siege, army position, route, occupation and combat
scope. The small projection must match the paired after-METRICS frame.
A new combat, movement, war/siege scope, unknown phase or missing proof falls
back to five. Army strength numbers are not a new military decision rule.

No Game or Native reads are added. Daily planning, army queries, contact safety,
source revision guards, actual SAVE revision checks, and player-decision
deferral remain in the caller. This helper never reuses tactical evidence.
Clean readonly chains still skip redundant SAVE. Dirty clears only after an
actual successful SAVE. Unknown legacy dirty progress keeps the five-cycle
interval.

At each five- or ten-cycle boundary, dirty progress marks a checkpoint due.
A pure readonly query with no date, actor, material or submission change carries
that due flag through the query chain. The next mutation or date advance
requests SAVE immediately, without waiting for another modulo boundary.
Player-decision deferral retains dirty and due; an actual successful SAVE clears
the active due state at the next helper call. Explicit planner SAVE actions
remain on their existing path.

The due interval is ten for routine siege and five otherwise. A readonly chain
can extend the cycle count without adding unsaved game progress. The next
existing date advance can add unsaved progress before SAVE: the retained peace
sample advances seven days, so this is not a guaranteed six-day or universal
game-day bound.

## Integration

Keep `root_checkpoint_cadence.py` next to the queue helper. Call
`checkpoint_context_from_auto(body)` after the existing result classifier
accepts AUTO, retain that small projection in the pending cycle, and call
`checkpoint_after_settled_cycle(state, pending, after)` after paired METRICS.
The original-response reconsume path projects the same retained body without
replaying the action.

At skipped five-cycle boundaries, inspect `checkpoint_last_decision`.
Use a distinct due-readonly-chain or stable-siege deferral receipt/count when dirty progress exists;
do not label that receipt as an unchanged readonly frame. Existing actual
SAVE/terminal guards and `finish_cumulative_checkpoint` remain unchanged.
The bounded session-specific integration diff remains external at
`D:/codex-ck3-demos/2026-10-14-robert-30year/stable-siege-checkpoint-policy01/queue.diff`;
the large runtime queue is not a repository dependency.

## Offline evidence

Run with a standard Python interpreter from any checkout:

```text
python -B -X utf8 tools/g2_saved_campaign/test_checkpoint_cadence_portable.py
```

The five focused groups load exact coroutine excerpts from the existing
`FreshQueue.full_loop`, using fake transport, frame and persistence. A compact
historical 17-cycle/7-day trace produces four SAVE calls with the old helper
and two with the candidate, with identical AUTO count and ending date.
The readonly turn1680 carries due until the following actual siege advance1682.
A separate original prewar trace carries turn2950 through readonly2951 and
saves after the existing seven-day advance2961.
The fixture provenance records original source/response hashes; no current
session, Game, MCP, OBS, desktop or process is accessed.

The measured sample window took 61.739 seconds (8.820 seconds per game day),
including 12.698 seconds across four SAVE calls. Omitting the two routine
saves estimates a 6.320-second reduction, or about 7.917 seconds per game day.
Avoiding a further same-date army requery may save another 2.534 seconds,
but that remains a counterfactual hypothesis. These are offline estimates,
not a measured speedup of the running game.

Timing source: external `p06-army-hotpath-review01/P08-full-cycle-bottleneck.json`,
original response range1473-1514. Raw external artifacts can expire under
the storage retention policy; the compact portable fixture and hashes are
the repository's retained evidence.
