# G2 private truce live capture (2026-09-02)

This is the single bounded paused exact-build follow-up for the `GEN-034`
`evaluated_days` gap. It classifies the production reader failure before the
existing output reset; it does not change the public terms schema, readiness,
offsets, or any termination action.

## Frozen inputs and offline gate

- Parent source baseline: `09f21c8958d9f880d4993c69ce967abc88bdb175`.
- CK3: `1.19.0.6`; `ck3.exe` SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- Checkpoint SHA-256:
  `60108A5DA03DC3A8315A3E79897D9CF2F49763910A8AA15A462E7DD0B6AAF164`.
- Driver-state SHA-256:
  `4FB901C77AF6D95A05EAB2B0E900AE2E07A652B4C14729835DECB69FC8CFF57E`.
- Requested frame: CharacterID `29829`, WarID `50331699`,
  `date_raw=53223936`.
- `open_kaishek` was bound to clean main
  `17caa288eb980aab0b652358e9e94a9901131619`; CLI JAR SHA-256
  `421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
  The `ck3-war-days-trigger-11906` parser/validator preflight was GREEN while
  IR/runtime and root scan were explicitly skipped. Artifact:
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-evaluator-private-capture-20260902T1645\open-kaishek-preflight.json`,
  SHA-256
  `DC3A2FC7216531BD74795788859DD418E11702E2F1B5F4D621D92CE0EBD6F058`.
  This is schema-only offline evidence (`ck3_started=false`), not CK3 live
  evidence.

## Private capture boundary

The production DLL still excludes the capture by default. The one-off
candidate was built with the explicit CMake option
`XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1=ON`; the capture additionally
requires `XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_PATH` at runtime. It appends one
private JSONL row after the observer and context destruction but before the
production failure path clears the observation. No row is serialized through
MCP, and no public header, wire key, readiness bit, action route, or native
offset changes.

The fresh MSVC build passed the focused
`xar_ck3_native_bridge_game_access_fixture` (`1/1`). Candidate identities:

- `xar_ck3_bridge.dll` SHA-256
  `4C8D2C001B8CFADCA8D0ADB4D40353466C4D1EED965F5D11C96DFE573E1FA9CF`;
- `xar_ck3_bridge_injector.exe` SHA-256
  `8789020EC1584E717388CBEAA7CE711F3CE3DAB6D5993976A8A9AD3DB03CB108`.

## Single live result

The retained runner report is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-evaluator-private-capture-20260902T1645\live\report.json`,
SHA-256
`31377779207957E3D18D7260945F5CD933DCCC497F2C1844A95D5CC01F02421E`.
The private sidecar is `g2-truce-private-capture.jsonl` beside that report,
SHA-256
`47514E299D87F6878229115BB60897F5E23FA28DACEE81937619D21A44D268EF`.

The exact-build, paused frame, character, date, concrete
`query-war-termination-terms-v1-50331699` capability, and same-frame query
identity all passed. Both allowed read-only terms queries returned the same
four-domain payload. Both private rows also agreed:

- `failure_code=9`, `failure=root_shape_drift`;
- `pointer_shape_verified=false`;
- `evaluated_days=-1` and `evaluator_double_read_stable=false`;
- `expiry_observable=false`;
- `context_destroyed=true`.

This proves the current reader exits inside the loaded attacker-defeat tree
shape traversal before invoking the duration evaluator. It does not prove a
duration or expiry value. No time advance or surrender, white-peace, enforce,
or other mutation command was sent. Cleanup was GREEN
(`shutdown_ok=true`, `tree_gone=true`, `driver_closed=true`) and the immutable
checkpoint/driver hashes were unchanged.

## Readiness and next entry

`evaluated_days_observable=false`, `truce_ready=false`,
`decision_ready=false`, and `GEN-034=unresolved` remain correct. The four
previously observed terms domains remain production-live read-only primitives;
expiry, generic war-bound loss, campaign/budget/white-peace comparison,
decision, typed action, and postcondition remain unavailable.

Do not replay this checkpoint with the same undifferentiated reader. The next
smallest entry is a private, staged loaded-tree shape capture that identifies
which `ResolveUniqueTruceNode` check returns `root_shape_drift` and records the
corresponding observed vtable/count/capacity value. It must again be
OFF-by-default, run after an `open_kaishek` preflight, preserve the public v1
wire, and issue no war-termination mutation. Only new exact-build evidence may
justify an offset or shape-contract change.
