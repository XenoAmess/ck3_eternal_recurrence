# Exact war move stop (bounded native run)

`g2_preview_operator.py run` accepts `--exact-war-move-stop-contract PATH`
and `--exact-war-move-stop-sha256 SHA256` together. The contract is an immutable
UTF-8 JSON file with schema `xar.ck3.exact-war-move-stop.v1` and exactly these
fields:

```json
{
  "schema": "xar.ck3.exact-war-move-stop.v1",
  "date_raw": 53157816,
  "war_id": 16777237,
  "army_id": 16777450,
  "origin_province_id": 2634,
  "target_province_id": 2640,
  "source_save_sha256": "<64 hex digits of the prepared checkpoint>",
  "source_driver_sha256": "<64 hex digits of the prepared, rebound driver-state.json>"
}
```

The operator checks the exact contract bytes and prepared save/driver pair
before the formal child starts; the child checks them again before CK3 starts.
The `--turns` value remains a ceiling for read-only discovery. Before submit,
the runner permits only native queries and that ArmyID's move previews. It
accepts exactly one `move-army-<army_id>-to-<target>` selected by the
`native_war_general_battle_distant_route_start` planner phase on the bound
same-date WarID and controllable ArmyID. The planner phase retains its full
hostile contact and first-day risk gates.

After the typed move, the runner requires a separately read paused native
snapshot: same date, campaign, WarID, controllable ArmyID at the origin,
move target equal to the target, and normalized remaining route exactly one
hop. It stops before another planner turn, saves a final checkpoint, and
requires the checkpoint snapshot to preserve that date and route. Only
`exact_war_move_checkpointed` with `ok=true` is the scoped route-start result.
An accepted command ACK, `operator_stop_checkpointed`, turn limit, or an
unverified checkpoint never establishes that result. This stage does not
authorize the next day of travel or a future battle; that needs a new current
frame and full-hostile one-day contact proof.

This is an opt-in static implementation. It has no R0284 matching live result
until a separately frozen attempt uses it and preserves its report and save.
