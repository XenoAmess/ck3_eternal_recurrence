# Save checkpoints by game date

The current ordinary queue uses `root_checkpoint_calendar_cadence.py` rather
than a modulo of planning cycles. A normal cycle can be a readonly query, so
five cycles are neither five game days nor five mutations.

At the user's explicit 2026-10-15 request, the normal policy is 90 game days
(approximately three months), in both peace and war.
Already verified material outcomes and an observed ended war request an extra
checkpoint. The first existing advancement after a due date can overshoot that
date; this helper does not interrupt or shorten advancement. An active player
decision keeps the queue's existing save deferral. A legacy dirty state without
a last-saved date requests one reconciliation SAVE, then uses the same 90-day
clock; query counts never install another recurring schedule. A terminal
actor/episode handoff remains owned by Root.

No new game query is issued. `checkpoint_context_from_auto` projects the
already verified advancement and its before/after war observations, then binds
the small result to the paired METRICS frame. Readonly queries do not move the
save clock. An actual SAVE failure, ACK or pending SAVE does not clear it.
The checkpoint origin character remains separate from the current naturally
succeeded actor; existing Driver/SAVE validation still owns origin binding.

## Queue integration

Freeze this helper as the queue's checkpoint helper and retain the sibling
`root_checkpoint_cadence.py` containing its readonly classification functions.
Import `checkpoint_saved` along with the two existing public functions. In
`finish_cumulative_checkpoint`, after the existing actual SAVE validation, call
`checkpoint_saved(state, saved['checkpoint'])` before clearing the pending
checkpoint and persisting the loop state. Keep the actual semantic revision,
SAVE result/file/Driver binding, pending-response and player-decision guards.

Use calendar deferral receipts and counters for this policy, carrying
`regime`, `interval_game_days` and `elapsed_since_actual_save_days`. Do not label
ordinary calendar deferrals as stable siege deferrals. Freeze a new queue
generation; never edit an executing queue or its imported helper.

## Validation

```text
python -B -X utf8 tools/g2_saved_campaign/test_checkpoint_calendar_cadence.py
```

The focused cases cover query-count inflation, war/end-of-war recovery points,
same-date verified outcomes, unknown legacy state, unconfirmed SAVE, natural
successor identity and the existing terminal handoff.

An offline replay of 120 settled N39 AUTO/METRICS pairs spans 160 game days.
The quarterly candidate requests one periodic SAVE without changing an AUTO or the
ending date. This is a counterfactual schedule, not a measured live speedup.
Evidence: external `calendar-checkpoint-opt01/QUARTERLY-ANALYSIS.json` and its compact
projected trace under the current Robert demonstration work package. The old
cycle-based fixture and evidence remain in `README-checkpoint-cadence.md`.
