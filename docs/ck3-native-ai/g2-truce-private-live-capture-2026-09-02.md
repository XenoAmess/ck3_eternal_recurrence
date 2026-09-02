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

## Staged loaded-tree follow-up

The next bounded follow-up used parent baseline
`2c64c420666f0b0adacad783f732bcef7545e884` and the same frozen CK3,
checkpoint, driver state, CharacterID, WarID, and paused date. The
OFF-by-default candidate split every `ResolveUniqueTruceNode` read and
comparison into a named private stage while preserving the production return
codes and public wire. It recorded actual vtables, counts, and capacities only
in the private JSONL sink.

The required `open_kaishek` gate again bound clean main
`17caa288eb980aab0b652358e9e94a9901131619` and CLI JAR SHA-256
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
The `ck3-war-days-trigger-11906` parser/validator preflight was GREEN; artifact:
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-staged-shape-capture-20260902T165942\open-kaishek-preflight.json`,
SHA-256
`5FB98B7BD312F97EB695BDA1DD8735AE9362DC20FB0F0752561211AFF053DB08`.
Candidate identities were:

- `xar_ck3_bridge.dll` SHA-256
  `0FDAF90717B49E573CB39A00BB4B7FA8BF08F5DCF33EF8F8A0182792F762329B`;
- `xar_ck3_bridge_injector.exe` SHA-256
  `B7909865ED03E6DD4E905CB7E4797341312CE16F8DA27ED8888AE3D864FE8779`.

The single live attempt retained:

- report
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-staged-shape-capture-20260902T165942\live\report.json`,
  SHA-256
  `0DE94D78563A2A21256E9F28FFA87D445E4754AE3FE5688834010450CE336E06`;
- private JSONL beside it, SHA-256
  `D93DDF01465EED6F5F8B660276E22658B848ABA981D39DA88EFFA6832E748A28`.

Both captured rows are identical and identify the first failed check as
`root_capacity_mismatch`. The loaded root vtable RVA is `0x44CF030`, exactly
matching the frozen `Jomini::Effect` vtable, and vtable slot 11 is non-null.
The actual root vector is `capacity=13, count=12`; the stale reader contract
expects `capacity=19, count=14`. All three values were read before the
comparison, so the `count=12` evidence remains valid even though capacity is
the first named failure. Traversal correctly stopped before dereferencing the
hard-coded child index; no downstream scripted/template/hidden/context/truce
shape was claimed. The duration evaluator was not invoked and both rows remain
`evaluated_days=-1`, `pointer_shape_verified=false`, and
`expiry_observable=false` with `context_destroyed=true`.

The runner is RED only because the public paused double-sample semantic proof
still cannot pass without duration. Cleanup is GREEN (`shutdown_ok=true`,
`tree_gone=true`, `driver_closed=true`), no war-termination mutation or time
advance was sent, and the source checkpoint/driver hashes remain unchanged.
Focused validation passed the private source contract (`3/3`) and the native
game-access fixture.

This narrows the next reverse entry: enumerate the 12 actual root children in
a private capture, record their vtables, and locate a unique
`scripted_effect_vtable` child before changing the stale `19/14/index 9`
contract. Do not blindly replace constants from this one boundary and do not
repeat either prior undifferentiated probe. Public truce, expiry, decision, and
action readiness remain unchanged; `GEN-034` is still unresolved.

## Root-child enumeration follow-up

A fresh branch from parent baseline
`4dc8b650a0056f31afb56880c6ff1d3f22702097` added a second private-only
stage before the stale root capacity gate. It uses the runtime vector bounds,
caps collection at 16 children, and records every child vtable plus the number
and last index of matches to the exact-build scripted-effect vtable. The
production `19/14/index 9` contract, public wire, readiness, and all action
paths are unchanged.

The focused private source contract passed `4/4`; the native game-access
fixture and fresh instrumented MSVC build also passed. The required offline
gate bound `open_kaishek`
`17caa288eb980aab0b652358e9e94a9901131619` and CLI JAR SHA-256
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
The `ck3-war-days-trigger-11906` preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-root-child-capture-20260902T171309\open-kaishek-preflight.json`,
SHA-256
`614026B2BB82805324323083CF2CD5EDD372707BB86A9E72954FA321C4E307ED`.
Candidate identities were:

- `xar_ck3_bridge.dll` SHA-256
  `E4991667AA7B34620A9103B98B3099931DEDC1571831C729559BB47F68311BB9`;
- `xar_ck3_bridge_injector.exe` SHA-256
  `728FDA6F9A995FB52D818909C6E40546CCFD1E0D36F15979E383C646CBADA7A8`.

The single paused live attempt retained:

- report
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-root-child-capture-20260902T171309\live\report.json`,
  SHA-256
  `1E24C2B4A1DD298DA3D8AC8EDF9360836A2E71724BB967D12621AFF8689367C7`;
- private JSONL beside it, SHA-256
  `83EAD5659D71E6877EFCB1641EA319B371C5E623FCA76442558BD8FFF30AE93E`.

Both rows are identical and report `root_child_capture_status=complete`,
`capture_limit=12`, `completed=12`, and no failed index. In order, the child
vtable RVAs are:

```text
0: 0x44D27B8   1: 0x44D27B8   2: 0x44DF210   3: 0x44D1E18
4: 0x44D27B8   5: 0x444B548   6: 0x44CF0F8   7: 0x44CF0F8
8: 0x44D27B8   9: 0x44CF0F8  10: 0x44CF0F8  11: 0x44CF0F8
```

The exact scripted-effect vtable RVA `0x44CF0F8` therefore has five matches,
at indices `6, 7, 9, 10, 11`; vtable identity alone does not locate a unique
truce script child. `root_scripted_match_count=5` and the stored
`root_scripted_match_index=11` is only the last match, not a uniqueness claim.
The attempt consequently remains at the same expected
`root_capacity_mismatch` return and never evaluates duration.

This is a useful negative result and closes the vtable-only hypothesis. The
next smallest distinct private capture is limited to those five candidate
children: record each selector count, template pointer/vtable, and only enough
default subtree shape to distinguish the unique `cadd_truce` script. Do not
repeat root enumeration and do not promote index 9 merely because it was the
old hard-coded value. Cleanup and source invariants were GREEN, no mutation or
time advance was sent, and `GEN-034` readiness remains unchanged.
