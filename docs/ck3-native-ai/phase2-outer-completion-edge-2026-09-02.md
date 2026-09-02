# Phase-two outer completion edge (2026-09-02)

The runtime continuation `0x3B9CFD2` is now statically bound to a direct
post-init completion-state edge. No CK3 process was started for this package.

The exact logical owner spans `[0x3B9CF50,0x3B9D04D)` and has three chained
PDATA ranges: `[0x3B9CF50,0x3B9CF72)`, `[0x3B9CF72,0x3B9CFCC)`, and
`[0x3B9CFCC,0x3B9D04D)`. Its 253 bytes have SHA-256
`63B6E134E77569D6E261BD9B99091BCEF5D41F531F5F67592C64BC890EDAEA83`.

The bounded CFG is unambiguous:

- `0x3B9CFCF` calls slot 2 of the callback object at `[RBX+0x38]`;
- the prior live evidence returns from the selected `0x88B480` callback to
  `0x3B9CFD2`;
- `0x3B9CFD2` loads `EAX=2`, and `0x3B9CFD7` atomically exchanges that value
  into state `[RBX+0x60]`;
- the remainder records elapsed time in `[RBX+0x68]` from start time
  `[RBX+0x70]`, then returns true at `0x3B9D039`;
- the already-busy path returns false at `0x3B9D046`, while a null callback
  reaches the trap at `0x3B9D047`.

Thus `0x3B9CFD7` is a directly proven post-init callback-completion edge; it
does not require another live observation. The helper has 1267 direct call
sites across the exact executable, so those generic callers were deliberately
not expanded and no unique higher loader owner is inferred from their count.

The reproducible extractor artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\outer-completion-edge-static-extract.json`,
SHA-256 `D831486D634D17BD2DEF3607AE2E72F99DB16B4682823B80EE291DAD7450158B`.
No public bridge, production loader, or readiness changed. Phase two remains
**native-readiness RED + static post-init edge bound**.
