# Stage 10 same-process Python contract resume

Date: 2026-09-12 (Asia/Shanghai)

## Problem and scope

The Stage 10 player-publication operator previously exposed only `status`,
`run-stage10`, and `cleanup`. When an unknown vanilla event correctly produced a
pre-selection RED, a newly added Python event contract could not be loaded into
the retained paused CK3 process. The only operational path was cleanup and a new
gameplay launch, even though no DLL, game file, launch setting, load order, save,
or runtime environment had changed.

The operator now exposes `retry-stage10`. It delegates admission to the existing
AF5 repaired-activation validator and reloads only the Python gameplay-policy
modules plus the Stage 10 action module. The retry is admitted only while the
same CK3 PID and bridge connection generation remain paused and healthy. It
rejects changes to checkpoint, product tree, production projection, DLL,
injector, game rules, state/artifact directories, pipes, or round identity.

## Bounded continuation contract

The action carries the failed attempt's `progress` object into the retry. It
requires the original timeline origin, the exact `origin + 120 days` absolute
deadline, the prior interrupt list, and the preserved unexpected-event key.
The resumed action therefore consumes the remainder of the original window; it
does not receive another 120 days. The evidence records the resume date, retained
deadline, retained interrupt count, and preserved event key.

Resume is unavailable after any event selection or terminal acknowledgement was
attempted. A failed input remains RED and cannot be silently repeated. The
original per-attempt RED artifact remains preserved, and the repaired activation
records the old/new code commits together with the unchanged live binding.

## Verification and operational state

Focused normal and optimized tests both pass `12/12`. They cover cold execution,
retained-deadline continuation, progress transfer on attempt 2, and refusal after
input. Python compilation also passes. No broad suite or CK3 launch was used for
this Python-only operator change.

Current round R502 and old round R501 are terminated; no CK3 instance is alive.
P1 remains `8/9`, and P2 remains `LOCKED`. The next bounded attempt may use the
new control only if it encounters a new pre-selection vanilla-contract RED while
the current gameplay process is still retained.
