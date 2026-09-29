# Private feast stage-1 Confirm operator, CK3 1.19.0.6

This is a bounded Python operator route over the native stage-1 option and
Confirm contracts. The native decision tree and R0356 read-only evidence are
recorded in [stage-1 option identity](activity-planning-stage1-option-identity-1.19.0.6.md).
The route was added after R0356; this document records source and focused
test behavior only. It is **not** live action evidence.

`--private-activity-feast-stage1-confirm` is default off and requires the
bounded native-headless contract. On one paused frame it opens the feast
planner, reads the selected `feast_type_generic` option, and submits one typed
`confirm-activity-feast-stage1-v1-private` request only when the native option
reports `generic_feast_confirm_ready=true`. The request binds the native
revision, game date, player character, activity key, and option key. The
operator then independently calls
`query-activity-feast-stage2-option-v1-private` and requires the same paused
frame and selected generic feast in stage 2. A positive command ACK alone is
insufficient. On Confirm or readback RED, the report retains the original
receipt and whether Confirm was submitted; an ambiguous submission remains
pending and is never retried by this run.

This action advances the **planner stage** only. It neither selects a final
cost nor calls Start, advances a game turn, or establishes a recovery/next-turn
loop. Configured cost and final CanStart remain unknown. The native private
Confirm and stage-2 read must both be enabled in the exact candidate build;
the flags are default off in ordinary builds. Focused normal and Python `-O`
tests cover the positive route, negative stage-1 eligibility, submitted RED,
and failed independent stage-2 read. A paired CK3 run is still required before
calling this production-live.
