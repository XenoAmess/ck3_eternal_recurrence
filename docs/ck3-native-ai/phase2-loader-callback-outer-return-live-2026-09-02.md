# Phase-two loader callback outer return live mapping (2026-09-02)

The single authorized private run mapped the sequence-2 normal return from
eight static candidates to continuation RVA **`0x88B5E1`**. This is a GREEN
caller-identity result, not loader readiness.

## Provenance

The clean baseline was `062548173d717b6bcc8234cfb3bee0df1eb7be4c`.
The run used current `open_kaishek`
`425514e2e937bb829b2415f9da7870609e9c736f`; the CLI JAR SHA-256 remained
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
The supporting preflight is
`Z:\ck3_mod_rewrite_process_assets\zg361\open-kaishek-support-20260902T1807\phase2-outer-caller-preflight.json`,
SHA-256
`80FC14AF5081A85ECBCAC998FDCF8FE26A11644E24407865D24EB8EF2CB70823`.
Parser, IR, and synthetic runtime were GREEN; the validator retained its known
full-root schema-only RED.

The private probe compiled with MSVC x64 `/W4 /WX /O2` and passed self-test.
Its executable SHA-256 was
`BA65B217FE7F15E69B4EB14C5C4251032B58E66F62BCB6A30D769E6DC26BFDBD`.
The exact CK3 executable remained `1.19.0.6`, SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

## Result

The only 60-second run produced
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\outer-return-caller-observation.json`,
SHA-256
`D694436E19762B1449FBEE38090A29C4451B64B332015646056868E9861C5CC1`.
It closed `GREEN / seq2-outer-caller-continuation-mapped` after 60.241 seconds.

The probe retained the complete ordered boundary for each callback: callback
entry, same-thread return, same-thread `0x3B9ACC4` vector exhaustion, then
`0x3B9ACE0` normal return with `[RSP]` read before `ret`.

| Sequence | Node | Outer continuation | Frozen-candidate match |
| --- | --- | --- | --- |
| 1 | `CGameConceptTypeDatabase` | `0x2041D91` | yes |
| 2 | `CJominiLoadScreenDatabase` | `0x88B5E1` | yes |

Thus sequence 2 selects callsite `0x88B5DC`, continuation `0x88B5E1`, and
PDATA owner `[0x88B480,0x88B649)` with unwind RVA `0x4C42814`.

## Bounded outer teardown and next stop point

`0x88B5E1` is the selected outer continuation, not a point that needs another
observation. Its bounded path through the end of PDATA function
`[0x88B480,0x88B649)` contains only local teardown:

- `0x88B5E2` addresses the local pair at `[rbp+0x170]`, and `0x88B5E9`
  calls teardown helper `0x82D880`; it returns at `0x88B5EE`;
- the array at `[rbp+0x00]`, count `[rbp+0x0C]`, is walked with stride
  `0x148`; each live element calls `0x823D90` at `0x88B603`;
- `0x88B62C` dispatches the allocator release for the array, followed by the
  epilogue at `0x88B630` and normal `ret` at `0x88B648`.

No wait meaning is assigned to these teardown helpers. The next distinct
observation candidate is **`0x88B648`**, where `[RSP]` is the exact return
address of this selected outer caller. It requires separate authorization;
repeating `0x88B5E1` would add no evidence.

Phase two remains **native-readiness RED + not-live**. All five private
breakpoint bytes were restored, the isolated CK3 process terminated, the real
profile was not targeted, and CK3/probe process counts returned to zero.
