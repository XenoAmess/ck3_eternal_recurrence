# H3937 target collector reobservation

## Actual R0119 result

The frozen execution checkout was `C:/h3e30` at
`95eb68a7806b95fd5b8ea900e70f0f6603f4b4c4`. Run
`desktop-3fevhd2-1c74096080--vanilla--R0119`, execution
`77e4d4da-14d9-431b-8742-32d346186f97`, artifact round `R119`, reached
native paused map readiness: PID 34288, generation 1, `native:3`, local
revision 4, native revision 3, date 53219928, actor 29829.

Two queries were accepted and available:

1. `query-province-local-siege-v1-2610`.
2. `query-route-contact-horizon-v1-83886367-to-2610-h-2-50331920-83886484`.

The combined collector's eleven frame, scope, appended history and result
binding checks passed. This is **two observed reads out of six**. The complete
six-read contract remains **0/6 certified, RED**. No gameplay action or date
advance was authorized or performed.

The target collector stopped before its third query at the whole-dictionary
comparison between a fresh `service.snapshot()` and its previous snapshot.
The fresh snapshot was not retained by that old error path, so the exact
changed field and the cause of this particular rejection remain unproven.
`state_changed` strings inside the copied historical command list are not
return codes for these two new queries. The contact result separately reports
`physical_army_inventory_check.valid=false`, reason
`mailbox_source_or_frame_mismatch`; physical inventory completeness is not
proven and is not upgraded by this Python change.

## Source change and bounded verification

The target reobservation gate now uses the existing `_same_frame`,
`_guarded_subject_unchanged` and `_query_history_unchanged` helpers. It keeps
snapshot ID, local/native revision, date, episode and connection generation;
played actor, army/war membership, event/interaction and capability; and
command history. The original published scope comparison still runs before
the third query. Diagnostic heartbeat changes alone no longer reject this
handoff.

The actual target collector was tested once in normal Python and once with
`-O`: each ran two tests, including twelve semantic/revision/membership/history
drift cases. A heartbeat-only refresh reaches the third query; an injected
native `state_changed` rejection remains RED and visible. All drift cases
stop before that query. This does not prove the remaining live reads.

Interpreter: explicit main worktree venv, Python 3.14.7, pywin32 312.
`open_kaishek` is not applicable to this Python snapshot comparison.
No CK3, Steam, desktop or MCP was started by the verification, and no native
source or binary changed. The frozen execution source and original RED
artifacts remain intact; another live attempt requires a new run ID.

## Preserved evidence

- Original directory:
  `C:/Users/1/ck3-handoff-resume-20260930/h3937-live-a01/live-output`.
- `outer-report.json`: 646255865 bytes, SHA-256
  `956F69448072883323F42277C223E634724CC1A81F2346AAD48C978F609E741D`.
- `completion.json`: SHA-256
  `E2DBE0FD207CEB580889388E2076C82F35BDD137DF59FA51D834182481336B3C`;
  08:25:19 UTC, gates restored, processes gone, outer cleanup proven.
- `supervisor-completion.json`: SHA-256
  `B5E2B752DDE863C11FB49797A6E9D38F952C7EB7C23B59283E6D72098583F886`;
  08:25:25 UTC, worker RC1, no timeout or taskkill.
- Small exact envelope extraction:
  `C:/h3937-go-sdk-20260930/attempt-05/receipt.json`. Its original report slice
  is byte range `[24035,258591)`, SHA-256
  `79C5F45F02952661A6E2BE0F75672DA9273434FB2DC60D0328DDCBC4190CC339`.
- Targeted command, stdout/stderr and dependency receipts:
  `C:/h3937-go-sdk-20260930/attempt-06/receipt.json`.

The large original report is retained; use the bounded extractions for this
diagnosis rather than printing all copied history and snapshots.
