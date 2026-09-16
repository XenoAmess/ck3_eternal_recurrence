# LIFE2 current state: bounded private paused read candidate

Work package `G2-M4-LIFE2-PAUSED-CANDIDATE` closes only the observation wait
caused by slot43 coupling LIFE2 current state to LIFE4 window candidates.
The exact CK3 build is `1.19.0.6`, EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The frozen native source is master `39a9f29638f57cb3da846ff6b8f2b55ad3dff785`.

The source save and paired driver state are the qualified ordinary production
feudal R739 bytes: save SHA-256
`D8BDC3C44D21A6F94DC7E4C050DB464F6C5036D5BA7E66233354B171F3401474`
and driver SHA-256
`163850711947EACB8DFB3DEC82E39BAD332BD00BC119DBB36642ED701DE4FB1A`.
The candidate retains their original pipe binding from the driver state,
so the official cold-start checkpoint contract can verify the unmodified pair.
The actor/date are read again from the new paused native frame; old `native:3`
is historical evidence and is not assumed to be the new round's revision.

The controlled read sends only
`private-query-player-lifestyle-current-state-v1` with the current
`snapshot_id`, revision, date, actor and persisted episode ID. It requires a
typed available LIFE2 snapshot on that same frame, checks focus, XP, perk
points and owned-perk state, permits legal zero values, and verifies an
independent subsequent paused frame. LIFE4 final candidates remain typed
unavailable; no perk legality or selection is inferred. If progress is a real
typed absence, the read records evidence insufficient rather than inventing
XP or perk points. A malformed/unknown field or frame drift is RED.

The local no-launch preparation uses production `prepare_profile`,
`verify_profile` and `validate_cold_start_checkpoint_for_pipe`. Production
`mod_source_fingerprint` calls Git, so a pure Git archive is useful for
source-hash retention but cannot serve as the prepared profile's source.
The candidate therefore keeps its own clean frozen master clone as its
source. The work branch is never a runtime dependency. The runner has an
overall 360-second window, 300-second readiness budget and one bounded
private query; the sole CK3 owner allocates the real `R{n}` and reclaims the
process. Static tests and no-launch preflight do not confer paused-live or
formal production-consumption status. Public query/action registration and
capability advertising remain OFF.

## R755 canonical snapshot-ID RED

R755 reached the real paused production frame for actor `29829` on date raw
`53178312`. The request carried `expected_snapshot_id = native:3` and native
revision `3`, but the private read returned
`native_lifestyle_current_state_invalid_request` before any native source
sample. The report is
`C:/ck3_mod_rewrite_process_assets/g2-m4-life2-typed-stage-candidate-final3cc-20260916/candidate/live-R755/report.json`
(SHA-256 `B9FA0254D25D23300C23A09BA959A050D14B93535D8B4AB45193B0631CB50F98`).
It records zero gameplay actions, no manual input/date advance, public
registration/advertising OFF, and successful CK3 process reclamation.

The failure is a source contract contradiction: application-main constructs
snapshot identity as `native:<revision>`, while LIFE2 `ValidSnapshotId`
previously rejected every colon. The minimum fix preserves existing
colon-free fixture IDs and admits only `native:<positive uint64>` when its
parsed value equals `expected_native_revision`; empty, zero, leading-zero,
non-decimal, extra-colon, arbitrary-prefix, and overflow forms remain invalid.
This is static-ready only. A candidate rebuilt from the integrated fix must
repeat the paused private query before LIFE2 current state can be called live.
