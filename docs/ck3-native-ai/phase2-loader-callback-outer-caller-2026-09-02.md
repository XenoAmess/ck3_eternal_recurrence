# Phase-two loader callback outer caller (2026-09-02)

This exact-build static package closes **NO-GO**: direct caller, callsite, and
continuation evidence cannot select the sequence-2 invocation from the eight
callers of `0x3B9AB00`. CK3 was not started, and the public bridge and readiness
state did not change.

The clean baseline is `26f2b0b9378f8417dd4a18eb6dd49077f9428224`.
The extractor output is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\outer-caller-static-extract.json`,
SHA-256
`494B4773E54DCAB0774B08CD1A361AE35A97BD5F07B748782083938BDCEA177A`.
It is bound to CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The immediately preceding current open_kaishek preflight was reused unchanged
(artifact SHA-256
`85C7FF727E9305314C2B5DF6F57FBA7D9ECC9ED1CAD8B30B24409276812984B5`).

All eight direct callsites belong to distinct PDATA functions. Each passes an
address of a caller-local 16-byte pair in `RCX`; none embeds the runtime node
name or concrete callback identity. Their verified continuations are:

`0x821E4A`, `0x88B5E1`, `0x1B39852`, `0x1E18C5B`, `0x1E21CD8`,
`0x203FF9B`, `0x2041D91`, and `0x3B9AEF9`.

Six continuations begin with `nop`, one immediately reads a global, and one
immediately jumps. None consumes a callee return value. Those shapes do not
encode `CJominiLoadScreenDatabase`, so using them to select a caller would be
an unsupported guess. The candidate count therefore remains 8 before and
after this bounded scan.

The next concrete observation point remains normal return RVA `0x3B9ACE0`.
After its epilogue, `[RSP]` is the exact return address and can be matched
directly against the eight continuations. That private live observation needs
separate authorization. This package does not expand into vector construction
or broader loader analysis. Phase two remains **native-readiness RED +
not-live**.
