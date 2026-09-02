# Phase-two selected outer return live mapping (2026-09-02)

The single authorized private 60-second run mapped the normal return of the
selected owner `[0x88B480,0x88B649)` to exact runtime continuation
**`0x3B9CFD2`**. This is a GREEN read-only mapping result, not loader readiness.

The run reused current `open_kaishek` commit
`425514e2e937bb829b2415f9da7870609e9c736f` and preflight artifact
`Z:\ck3_mod_rewrite_process_assets\zg361\open-kaishek-support-20260902T1807\phase2-outer-caller-preflight.json`
(SHA-256 `80FC14AF5081A85ECBCAC998FDCF8FE26A11644E24407865D24EB8EF2CB70823`).
The probe built with MSVC x64 `/W4 /WX /O2`, passed self-test, and had SHA-256
`AE3861D2C84522363208F8484AED131F785E5C055CCFDC8D57E07DEDAABE0AF0`.

The live artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\selected-outer-return-observation-20260902T1838.json`,
SHA-256 `F10CDD414FA4EDD74E256BB2D084C8F5117467B32E7CCB3E70F5CAB45B9A4958`.
It retained the ordered sequence-2 boundary: callback entry/return, same-thread
vector exhaustion at `0x3B9ACC4`, inner normal return `0x3B9ACE0` to
`0x88B5E1`, bounded teardown, then normal return `0x88B648`. Reading `[RSP]`
there produced `0x3B9CFD2`, on the same thread and inside the exact CK3 image.

All breakpoint bytes were restored, the isolated process terminated, and CK3
and probe process counts returned to zero. The old 300-second timeout was not
repeated. No public bridge, loader mutation, or readiness state changed.

The next distinct stop point is `0x3B9CFD2`. Before any further live run, its
containing PDATA function and bounded local CFG/call context must be frozen
statically. No wait or post-init meaning is assigned yet. Phase two remains
**native-readiness RED + private-live evidence only**.
