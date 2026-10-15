# Pure faction and event queries: avoid unused command-history copies

The managed 30-year Robert run accumulated a large `native_command_history` while
continuing to issue paused, read-only queries. A closed P11 Driver state had
79,604,097 bytes of command history in 7,531 rows. P11 completed receipts
recorded 153 player-faction-alert queries (4.469 s median) and six current
event-window queries (6.33 s median). These are before the change described
here and do not prove its eventual live speedup.

The two query paths now ask for the existing history-free snapshot at every
place where the command history was unused:

| Pure query | Service | Native query | Native dispatcher | Primitive | Total removed full-history copies |
| --- | ---: | ---: | ---: | ---: | ---: |
| Player faction alerts | 2 | 2 | 0 | 1 | 5 |
| Current event window | 2 | 2 | 1 (active event ID) | 1 | 6 |

The finite snapshot retains the native/public revisions, episode, paused state,
connection diagnostics, active wars, event identity, and all other semantic
fields. The query's existing frame, build, scope, envelope and handoff checks
still run. The `bookmark.1070` event-material pin still uses the same source
frame and the later option outcome still needs its independent readback.
No strategy preference, action, retry or business-credit rule changes.

The campaign-root query's *own* Native and Service methods already avoid
history copies. Its ordinary auto-turn entry does take one full snapshot:
`_retry_rejected_campaign_root_read` compares the old complete history with a
fresh prefix and requires exactly one failed root-query row before retry. That
snapshot remains full to preserve the existing rejection guard. P13 already
removed unnecessary history copies from pure war-entry/declarable queries;
remaining declarable wall time must be attributed by its own transport and
Native timing, not charged to this patch.

The P13-derived offline candidate is
`D:/codex-ck3-demos/2026-10-14-robert-30year/p13-pure-query-history-free02/`.
Its source patch SHA-256 is
`1e92dc7ef419979fdf7ddc14c4b7ce7fae7a246f7507ab9967449148362f95e8`.
Focused W tests (`test_pure_read_history_free.py`, faction bridge, event service,
and `bookmark1070` driver seam) passed: 25 tests and 23 subtests. They compare
finite and full-history service results, reject native/Service frame drift,
forbid a full snapshot on Native query paths, and exercise event query through
material capture. The existing faction and `bookmark1070` test harnesses were
updated to use the new finite read; the latter now imports this development
tree instead of a frozen historical tree.

The P14 live benefit remains unmeasured until same-Game SDK deployment and
ordinary-stage receipts. Keep pre-change medians labeled as baselines.
