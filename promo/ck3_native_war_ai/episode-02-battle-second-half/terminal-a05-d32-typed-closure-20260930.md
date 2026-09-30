# E2-09 A05 day 32: native terminal proof and control limit

The preserved A05 day-32 marks `e2t-s02-d32-writer` and
`e2t-s02-d32-war4-after` in
`D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live/recording-e2-09-terminal-a02/marks.jsonl`
both have `control: null` and bind the same terminal response SHA-256
`3CAC1F8F89545C299A957EB49C1B8636BB9A14C2707680A458FA8104EF9B1782`.
The earlier day-31 control is revision 16; it is not day-32 control.

The existing day-32 terminal query is itself a typed native lifecycle read.
Its `accepted=true`, queried wrapper revision 19, native revision 18, and
snapshot ID `native:18` agree with its source and the paused day-32 snapshot.
The observed journal records `normal_result` for CombatID 16777218; the prior
combat is removed, ArmyID 18 has no active combat backlink and is retreating,
and the WarID 4 battle row is recorded. The A05 fact verifier now checks the
exact frame identity and terminal closure in addition to its existing writer,
poststate, recorder, and card-byte checks. This is a read-only check over
preserved small JSON and card assets; it does not decode or hash the raw video.

`GameplayBridgeService.query_battle_control_snapshot_v1` only returns a
successful typed response for an **ongoing** battle. Its production contract
raises `BridgeUnavailableError` when the underlying result is unavailable.
Therefore querying that API after this terminal event cannot supply a
successful day-32 battle-control receipt. The earlier control remains distinct
from the terminal writer; neither is relabeled to fill the missing field.

The A05 a02 raw is still `ENCODED_UNREVIEWED`. Existing FFprobe navigation
locates the writer and after-panel near PTS 397.333 and 487.700, respectively;
these are machine positions, not clean spans. Full 1× human review, actual
visible span selection, and final film signoff remain pending.
