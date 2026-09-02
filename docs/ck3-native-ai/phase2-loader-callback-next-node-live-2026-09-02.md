# Phase-two loader callback next-node live observation (2026-09-02)

This package performed the single authorized exact-build private observation
at the statically bound node-loaded stop point. It closed GREEN with a narrower
result than loader readiness: after the last successful callback, the current
node vector was exhausted. There was no later node in that callback-loop
invocation.

## Preflight and build

The run used clean parent baseline
`3f90b664d6e9095bce079de47113da9c551a9787`. The current `open_kaishek`
checkout was `17caa288eb980aab0b652358e9e94a9901131619`; its CLI JAR SHA-256 was
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
The preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\next-node-open-kaishek-preflight.json`,
SHA-256
`85C7FF727E9305314C2B5DF6F57FBA7D9ECC9ED1CAD8B30B24409276812984B5`.
Parser, IR, and synthetic runtime were GREEN. The full-root validator retained
its known schema-only RED; the preflight is not CK3 live evidence.

The private probe was compiled with MSVC x64 `/W4 /WX /O2` and passed its
self-test. Its executable SHA-256 was
`E083CC03D5E9C24C46D97ACAFB24AE7FFAF83A81C3483C49679ACEF42EDD5603`.
It was bound to CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

## Live result

The only run used a 60,000 ms bound and an isolated user directory. Its live
artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\next-node-callback-observation.json`,
SHA-256
`A55D2E84D6842A7603DB96EC91A21B0A5D218221986E16B9B96CD8DD85847F05`.
It closed `GREEN / last-returned-callback-vector-exhausted` after 60.238
seconds.

| Sequence | Callback node | Concrete target | Return | Following transition |
| --- | --- | --- | --- | --- |
| 1 | `CGameConceptTypeDatabase` | `0x2045330` | same thread at 13.908 s | same-thread `0x3B9ACC4` vector exhausted |
| 2 | `CJominiLoadScreenDatabase` | `0x3455CA0` | same thread at 14.989 s | same-thread `0x3B9ACC4` vector exhausted |

The last successful callback was sequence 2. Its following transition hit the
statically bound exhausted-vector discriminator `0x3B9ACC4`; it did not hit
the node-loaded stop point `0x3B9AB53`. Consequently there is no next node,
node name, receiver, or receiver-null state to report for that invocation.
This is positive evidence of vector exhaustion, not an unavailable read.

## Boundary and next entry

The observation rules out a later node inside this callback-loop invocation as
the stall source. It does not identify which of the eight external callsites
invoked this function, nor what happens after the function returns. Phase two
therefore remains **native-readiness RED + not-live**; no bridge field,
production detour, or readiness gate changed.

The next bounded entry is to bind normal return RVA `0x3B9ACE0` to the exact
external caller continuation for the `CJominiLoadScreenDatabase` invocation.
The static slice already provides eight candidate continuations; stack return
address evidence is required before selecting one. No further live run is
authorized by this package, and this next-node capture must not be repeated.

Cleanup was GREEN: callback, continuation, node-loaded, and loop-exit bytes
were restored; the isolated CK3 process terminated; the real user profile was
not targeted; and no CK3 or probe process remained.
