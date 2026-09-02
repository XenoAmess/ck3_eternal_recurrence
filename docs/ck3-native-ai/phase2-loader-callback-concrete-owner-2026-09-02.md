# Phase-two concrete loader callback owner (2026-09-02)

This package follows only the concrete callback RVA `0x2045330` obtained from
the preceding entry/return observation. It binds the callback's sole direct
construction path and containing RTTI-owned code body without starting CK3,
scanning unrelated executable domains, or widening the public bridge.

## Preflight and artifact

The required offline preflight used `open_kaishek`
`17caa288eb980aab0b652358e9e94a9901131619`. Its artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\concrete-owner-open-kaishek-preflight.json`,
SHA-256
`642A7293BB33ECBBA644585941F5352A27DACD4F103271898A476DC592F0ED66`.
Parser/IR/runtime are GREEN and the full-root validator retains the known
schema-only RED. This is offline acceleration, not CK3 live evidence.

The exact-build extractor output is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\concrete-callback-owner-extract.json`,
SHA-256
`972538E9301963269BC38E2ED15B4105F2FC7053E88FD260FED881D5A6E2A68A`.
It is bound to CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

## Direct construction and source owner

The concrete callback is a 14-byte leaf trampoline at
`[0x2045330,0x204533E)`. Its exact shape is:

1. load the global object pointer at RVA `0x570C0F0`;
2. load that object's vptr;
3. tail-jump through vtable slot 2.

The executable contains exactly one bounded RIP-relative construction
reference to this callback: `lea rax,[rip+...]` at RVA `0x8235A5`. It lies in
the single PDATA function `[0x823570,0x823647)`, whose bytes have SHA-256
`1BC7728BEC32836A5E9FD6188BA51A727F6633D87A37BD8BB1B47DA4E9352C55`
and unwind RVA `0x4C3F330`. The body loads the already observed wrapper vtable
RVA `0x408A450` and passes its local callback wrappers to the registration
target `0x2043D80` at callsite `0x8235FD`.

The code owner RVA `0x823570` appears in exactly two absolute virtual slots,
both slot index 23:

- `CInterfaceApplication` vtable RVA `0x4093158`, slot RVA `0x4093210`;
- `CGameApplication` vtable RVA `0x428BC78`, slot RVA `0x428BD30`.

The reliable bounded identity is therefore the shared
`CInterfaceApplication`/`CGameApplication` virtual-slot-23 registration body.
The code body and construction reference are unique, but the class vtable
owner is intentionally recorded as the base/derived pair. No method name is
invented without source symbols.

## Boundary and next entry

No CK3 process was started and phase two remains
**native-readiness RED + not-live**. The callback's global object runtime type,
the business meaning of its slot 2, later stalled-node identity, source-file
attribution, and loader readiness remain unknown.

A later stalled-node private observation is not necessary to close this
static package and was not performed. If loader diagnosis still requires it,
the next separately authorized entry is one bounded capture of the global
object vptr/slot-2 identity for the later stalled-node callback. It must not
repeat the existing `database_callback_stall` timeout, generalize this first
callback to every node, or change public bridge/readiness state.
