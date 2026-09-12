# R503/R504 Stage 10 provider-readiness RED and fix

Date: 2026-09-12 (Asia/Shanghai)

## Live result

Old round R503 terminated before current round R504/PID `214796` became the
sole CK3 process. R504 passed the loader in 62.79 seconds with 303 database
callbacks and zero fatal signatures. It then advanced 36 game days, drained ten
known event windows, and paused on the target `zg361mg.120`, instance `28`.
No target option or acknowledgement was attempted.

The preserved direct RED is
`28EB9B11BA023A44839D7F6A6F0D4991F87196E06D22581AAFC4811ED3E35F0B`.
Its exact native provider frame binds player/subject `27181` and owner `36354`;
the F case is `state=5`, `active=false`, with matching owner and subject. This
matches the event trigger in `zg361_manager_governance_runtime_events.txt`,
which requires F state 5 and inactive before the player-visible event can open.

## Root cause and minimum correction

The Stage 10 action incorrectly required the manager-governance provider's
aggregate `readiness.ready`. That aggregate also waits for unrelated
distribution-settlement lifecycle fields. In the target frame those future
fields are correctly unavailable, so aggregate readiness is false even though
the F case and Stage 10 event are terminal. This is an acceptance-contract RED,
not a mod gameplay RED.

The provider gate now requires only the fields used by this acceptance claim:
subject binding, case identity, same-frame readiness, exact owner/subject, and
F `state=5 / active=false`. The hot-resume admission also accepts a preserved
target-event postcondition RED in addition to an unknown vanilla-event RED,
provided no input was attempted. It retains the original timeline origin,
absolute 120-day deadline, current PID, and bridge generation.

Focused normal and optimized action/operator tests both pass `14/14`; Python
compilation and diff checks pass. No broad test, new CK3 launch, mod change,
DLL change, or extended runtime was added.

The frozen operator was built before the target-event retry admission existed,
so its one permitted `retry-stage10` request was rejected before module reload:
`accepted=false / no completed pre-selection contract RED on a retained
session`. This RED is retained in the operator stdout. It did not change the
CK3 process, date, event, or input state. Sending another retry or manually
acknowledging the event would add no business evidence because the acceptance
contract explicitly says that event ACK is not a business postcondition.

`tools/extract_zg361_stage10_terminal_gate.py` now performs the offline recovery
from the immutable RED artifact. It accepts only a real paused `.120`, exact
event root and F-ticket scopes, the same snapshot/revision/native revision for
the event and provider queries, the exact player/owner binding, F
`state=5 / active=false`, the original 120-day deadline, and no target ACK. It
deliberately ignores only the provider's aggregate readiness while still
requiring `subject_binding_ready`, `case_identity_ready`, and
`same_frame_ready`. A wrong case, frame, scope, hash, deadline, target event, or
post-target selection remains RED.

The recovered Stage 10 gate is `395FACA70454A5A034F20475E8EA37D7A0A36A4B1E0C9375C584AE4F3920014A`.
It hash-binds the original direct RED
`28EB9B11BA023A44839D7F6A6F0D4991F87196E06D22581AAFC4811ED3E35F0B`
and activation `68CDC62E721DB3D25019CBCB59D74285243EC21FC465694C729A6BD4CCB43117`.
Extractor normal/optimized tests pass `3/3`; the current product delta was
checked with B1 runtime normal/optimized `76/76`, `validate_local.py`, and the
reproducible 1,031-file release build.

R504 then completed its one managed cleanup. Canonical and managed cleanup are
GREEN with empty final CK3 inventory; their SHA-256 values are
`28D2C57AE59E2B9B1C84B45862D831129C9255EE68BF9326DD7A1F7B5D03C235`
and `FEC3801165DFFEFB7EEE5B4C36F9B0DDF06FD4A18346AD2323AFDFE5BB2959C3`.
Current round R504 and old round R503 are terminated. P1 evidence assembly is
the next offline step; P2 remains `LOCKED` until that nine-gate manifest is
GREEN.
