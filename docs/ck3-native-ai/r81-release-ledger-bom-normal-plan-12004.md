# R81 ordinary plan: actual release ledger BOM consumption failure

Status: source-ready, NOTRUN. This is a Python input-decoding repair, not a
native construction, release ACK, save corruption or new game capability.
Root owns its single consumer FIRST and live adoption.

Root's normal `ck3_auto_turn` attempt014 failed at
**2026-10-09 05:03:44.866667–05:04:07.662633 UTC** with FastMCP text:
`Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)`.
The saved response has no structured body and STDERR has no traceback.
The original failed response remains under
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/managed-full-h9715-saved6010-r81-native46restore01/operator/gameplay-responses/014-r81-after-save-normal-turn03.json`.

The finite current-source path is Service's ordinary planning call to
`plan_release_formal`, which reads `read_release_ledger(state_dir)` before
release material arbitration. At source
`088fed39e0ceda7b28c2b0ee2113db4ce61fa58a`, the reader applies
`json.loads(path.read_text(encoding="utf-8"))` to
`player-prisoner-release-formal-v1.json`. The direct normal entry is at
`bridge/service.py:1883`, with the war and initial-plan entries calling the
same function. The decoder fails before the ledger shape or pending identity
can be interpreted.

One three-byte read of the actual **44,935-byte** file proved prefix
**`EF BB BF`** at
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/g2-robert-mainline-12004-full-h9715-saved6010-r81-native46restore01/state/player-prisoner-release-formal-v1.json`.
This is direct byte evidence for the same decoder failure in the current
ordinary path. The worker did not deserialize the opaque actual record,
inspect a large driver file, survey other ledgers or query the live game.
The sole fixture below completes the production-consumer reproduction.

The minimum repair changes only that release reader's encoding to
`utf-8-sig`. It accepts the actual BOM while continuing to accept existing
plain UTF-8 files. It does not change JSON schema, prisoner state, native code,
ACK admission or writer behavior. Historical bytes and the failed attempt are
retained; there is no BOM stripping or state-file rewrite.

Root's only new qualification node is
`test_r81_release_ledger_bom_normal_consumer.py::test_actual_r81_bom_release_ledger_is_consumed_by_normal_plan`.
It reads this actual small capture once, reproduces the old decoder's precise
JSON error, copies the bytes privately, and invokes the real release reader
and normal release planner. Its paused frame is an explicit synthetic seam;
it performs no native query or action. The production-consumed record must
match the decoded saved record, and the private copy must remain byte-for-byte
unchanged. No old GREEN fixture is rerun. Worker test/import/build/hash/Game,
SDK calls and capability credit are zero. Live recovery remains pending Root.
