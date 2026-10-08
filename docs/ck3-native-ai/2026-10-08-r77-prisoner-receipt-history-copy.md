# R77 retained release receipt: unnecessary history copies

Status: `SOURCE_NOTRUN`. This Python change has no new native ABI, query,
action, or live capability credit. Its unique connected FIRST0 is authored
for Root execution; no test, import, build, EXE query, SDK or Game action was
performed by the source worker.

The actual ordinary R77 release receipt reads a retained target on a paused
frame. The source path is `ck3_auto_turn` → `GameplayBridgeService.auto_turn`
→ `_execute_planned_turn` → `read_release_receipt_private` →
`NativeHeadlessGameplayDriver.query_player_prisoner_collection_private_v1`
→ `query_player_prisoner_collection_private_v1`.

That path exported the entire command history three times: the receipt's
initial frame, the collection transport's initial frame, and its final
same-frame check. Each `take_snapshot()` called `_history_snapshot()`, which
deep-copied every retained command result. These readers use actor, native
and public revisions, date, paused state, native provenance and the existing
frame binding; none consumes `native_command_history`.

The existing `take_internal_semantic_snapshot()` provides all those inputs
without exporting the transcript. A local transport helper selects that
reader when present and retains the previous public-reader fallback for
offline or legacy drivers. The receipt and both transport frame reads use
the helper. The final `_binding` comparison, native normalization, original
release ACK, freedom/transfer/death/pending distinction and independent
readback remain unchanged. The Driver still records the complete query
result and retains the complete public history and durable state.

This is separate from the already qualified `70e01ad` planning optimization:
that change keeps private policy history views outside the intermediate plan
copy; it cannot remove these three explicit public Snapshot exports.

The new single connected fixture reuses the qualified complete
`retained-held-player.json` command result as input. It compares the previous
three-export route with the new route through the registered ordinary MCP
turn, real Service dispatch, real NativeDriver and strict transport. A
counted synthetic transcript makes the avoidable copies observable without
loading the large actual Driver state. It also checks the whole independent
result, original pending ACK, full public export, full durable history,
post-query frame drift rejection and legacy reader fallback. No native
producer or previous acceptance is rerun.

The intended deterministic improvement is removal of three complete history
deep copies per ordinary release receipt. No percentage, CPU attribution or
live turn latency improvement is claimed until a new actual turn provides
that evidence.
