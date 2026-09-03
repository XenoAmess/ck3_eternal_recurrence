# G2 truce preview-entry observer seam (2026-09-03)

## Result

`[static-ready-no-launch]` The next minimal passive seam is now frozen at the
shared `CAddTruce` preview method, after its unwind-described prolog. This work
did not start or attach to CK3, install a hook, execute an effect, call the
duration evaluator, or change an action/readiness/public wire.

This is a narrow activation observer, not an `evaluated_days` solution. A hit
would prove that a game-native read-only description traversal reached an exact
`CAddTruce` object. It cannot produce duration because the whole preview
function neither calls evaluator `0x3373000` nor consumes `this+0x108`.

## Why this is the distinct seam

The previous observer covered evaluator calls `0x2EDAF0F` and `0x2EDB59E` in
virtual slot 22. Exact CFG and the zero-hit live show that those calls belong to
the mutating execute methods, so a paused run that issues no termination or
Context effect is expected not to reach them.

Both `CAddTruce` specializations instead expose the same read-only preview at
virtual slot 23:

| Type | Exact vtable | Slot address | Preview target |
| --- | --- | --- | --- |
| `CAddTruceEffect<0>` | `0x4461CA8` | `0x4461D60` | `0x2E87140` |
| `CAddTruceEffect<1>` | `0x4461D70` | `0x4461E28` | `0x2E87140` |

The function address occurs in eight exact-build vtable slots, not only these
two. Any future telemetry must therefore record `[RCX]` and accept a row as
`CAddTruce` only when it equals one of the two exact vtables above. An unfiltered
hit count would be ambiguous.

## Exact seam and ABI

The preview owns PDATA `0x2E87140..0x2E8723B`, unwind RVA `0x4DF9914`.
The unwind header fixes its prolog length at `0x15`, so the smallest convenient
post-prolog detour window is:

- patch RVA `0x2E87155`;
- continuation RVA `0x2E87165`;
- 16-byte anchor
  `488B024D8BF04C8BD2488BF966833804`;
- anchor SHA-256
  `F5B206324844555C64D660A376350E28C0E9710717BA121E04B380415254FC63`;
- full function SHA-256
  `941E91BF0B43EB8029940BA378D75A7CF6B65DB1431B126B7265FAD84EDE7E1F`.

The anchor is five complete instructions: `[RDX] -> RAX`, `R8 -> R14`,
`RDX -> R10`, `RCX -> RDI`, then `cmp word ptr [RAX],4`. A future observer
can sample the original incoming registers before replaying those bytes:

| Register | Exact local data flow | Minimum useful telemetry |
| --- | --- | --- |
| `RCX` | effect `this`, then preserved in `RDI` | pointer and exact `[RCX]` vtable |
| `RDX` | preview source/context, first dereferenced, then preserved in `R10` | pointer only |
| `R8` | preview output/collector, preserved in `R14`, later used for virtual call `[R14]+8` | pointer only |

The known execute layout makes `RCX+0x108` the duration script-value address.
At this seam it is identity/provenance only: the observer must not invoke the
evaluator or claim the address contents are days. The native preview itself
reads `this+0x10` and `this+0x60`, not `this+0x108`.

## Observer boundary

A later implementation, if scheduled, should be default-off and private. It
needs only a counter and the five pointer/identity fields above, exact vtable
filtering, register/flag preservation, and byte-exact anchor replay. It must not
change a branch, return value, object state, evaluator count, timing policy, or
execute slot 22. This is an observer, not a guard.

No broader global evaluator hook is justified by current evidence. It would
intercept unrelated script-value evaluations, while the preview has no proven
data-flow to duration. After a preview hit there is no statically justified
next duration seam; new native evidence is required before widening scope.

## Reproducible static evidence

- extractor:
  [`extract_g2_truce_preview_entry_observer_seam.py`](../../ck3_autonomous_player/native_bridge/research/extract_g2_truce_preview_entry_observer_seam.py);
- frozen contract:
  [`g2_truce_preview_entry_observer_seam_v1.json`](../../ck3_autonomous_player/native_bridge/research/g2_truce_preview_entry_observer_seam_v1.json);
- focused test:
  [`test_g2_truce_preview_entry_observer_seam.py`](../../ck3_autonomous_player/tests/unit/test_g2_truce_preview_entry_observer_seam.py).

The extractor binds CK3 `1.19.0.6` executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
the PDATA/unwind prolog, full function and anchor hashes, both exact vtable
slots, all eight shared pointer references, register flow, absence of the
duration evaluator, and absence of a `+0x108` read. `evaluated_days`, expiry,
decision, action and `GEN-034` readiness remain unchanged and unresolved.

## Implemented private observer candidate

The seam now has an independent, default-off implementation:

- `g2_truce_preview_entry_observer_v1.hpp/.cpp` owns one exact 16-byte
  post-prolog detour and byte-for-byte replay;
- the thunk preserves flags, all volatile integer registers, and volatile
  `XMM0..XMM5` before calling the recorder;
- the recorder safely reads only `[RCX]`, rejects every object whose vtable is
  not exactly `module_base+0x4461CA8` or `module_base+0x4461D70`, then records
  only the accepted traversal count/type and the original `RCX/RDX/R8`
  pointers;
- it neither calls `0x3373000` nor reads or derives `this+0x108`; no duration,
  expiry, decision, action, return value, object state, or public readiness is
  produced;
- install remains exact-build, suspended-primary-thread, and production-
  override closed. The hot recorder has no allocation, lock, clock, thread-ID
  query, or syscall.

The focused native fixture covers exact-vtable acceptance, unrelated-vtable
rejection, default-off/exact-build refusal, detour construction, exact anchor
replay, uninstall, and byte restoration. The Python source-contract test binds
the exact EXE/hash, PDATA/unwind boundary, function and anchor hashes, forbidden
duration access, and the unapplied default-OFF integration snippet.

The shared `bridge.cpp` and `CMakeLists.txt` now contain the default-OFF
diagnostic-only wiring. The exact reviewable integration slice is frozen in
[`g2_truce_preview_entry_observer_v1_wiring.diff`](../../ck3_autonomous_player/native_bridge/research/g2_truce_preview_entry_observer_v1_wiring.diff).
The Python native driver forwards the private observer block under diagnostics,
the service exposes it only through `bridge_diagnostics`, and MCP's existing
`ck3_get_bridge_diagnostics` tool uses that path. It remains absent from the
hello capability list and from routable gameplay steps. This candidate is
therefore `static-ready-no-launch`, not installed and not live. A later preview
hit would establish only exact `CAddTruce` preview traversal; it still cannot
promote `evaluated_days`.
