# Actual4 next linked collection after the direct carrier

Source-first seal: 2026-10-09 Asia/Shanghai / W41. Independent source base
`0d13fd93f6c23741dfefc37f9e64cbdbe057351f`. Exact game
**1.20.0.4 / Steam25734779**, existing EXE pin
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
Root alone owns Game/SDK/runtime and qualification. This package invokes none.

## Entry and exact source cost

The [preceding actual4 carrier](battle-person-next-direct-carrier-12004.md)
ends or skips to actual `291CDEB`. The old `2921AB0` name was only a locator.
A first new **11B** read `[291CDEB,291CDF6)` decodes `RDX=R14` Character,
`RCX=R13` selected Model, then `291CDF1 CALL2921A90`. Cached runtime-function
ordinal141270 gives `[2921A90,292204B)`; only this **1467B** callee was read.
Both captures decode completely. Cumulative new EXE I/O is **1478B / 2 reads**,
old EXE I/O 0, new pdata/unwind 0, scans/hashes/tests/builds/Game 0. The earlier
328B and Native41 fixtures are not reread or rerun.

Receipts are under
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/person-after-carrier41/`:
`actual-callsite01/SOURCE-CAPTURE.json`, `ACTUAL-HELPER-EXTENT.json`, and
`actual-helper02/SOURCE-CAPTURE.json`; the last directory holds complete
`2921A90.asm`. This is a new actual4 body, not a guessed old-RVA offset.

## Native receiver, demand and contribution tree

At `2921AB7`, Character QWORD1C8 is read. Present selects its DWORD B68 full ID;
absent supplies `FFFFFFFF`. Absence does **not** skip the helper. At `2921AD2`,
the actual registry QWORD slot is `module+5D1EB80`. A null registry selects the
actual fallback object QWORD slot `module+5D1EB38`. Otherwise the requested ID's
low24 bits index the registry: unsigned count+2C, table QWORD+20, stride16 and
pointer+8. A nonnull candidate's complete DWORD+8 must equal the full requested
ID; range, null and mismatch choose the same fallback.

Selected object's DWORD+C must be `446F6D69`, then DWORD+8 must differ from
`FFFFFFFF`; either observed failed gate returns zero source occurrences. An
unread required operand is partial, never a fabricated failed gate. This
concrete role is called `linked_object_b68`; a different typed legitimacy
getter or a guessed semantic name is not its source proof.

The first numerical family reads selected object's QWORD+60 and signed DWORD
count+6C, traversing pointers at stride8 in raw order. At `2921B50..2921B63`,
each pointer's inline PC+1778 is passed to the already proved actual4 `2438830`,
destination selected Model+10, weight100000. Duplicate pointers remain duplicate
occurrences. There is no pre-call PC-empty test: an observed count0 PC still
contributes one source occurrence with empty arrays. Zero list count contributes
zero occurrences. Negative list counts are not source-known empty; this observer
retains the raw signed count and marks its traversal partial.

PC field decoding reuses the preceding actual4 source-use closure: signed
count+C, keys QWORD pointer0/U16 stride2, values QWORD pointer68/I64 stride8.
Copies preserve ordering, repeated keys, key0/FFFF and signed Q64 extrema. No
source PC+74, destination baseline, merger callback or initializer is read.

Only after the direct list does the native helper read selected object's
definition QWORD+30. It tests definition signed DWORD B8C first; when it is0,
it tests signed DWORD BBC. Both0 returns immediately. A nonzero tested count
demands Character classifier `2A38030`, initializes a local temporary container
through `24FBAC0`, chooses B80/B8C for classifier2 or BB0/BBC for classifier0,
and calls `2872300` for each selected row before `24FD2D0`, `2303380` and
`2303490`. The completed local header is passed to `291B4D0`. Classifier,
evaluated row output and temporary-header semantics are unclosed in this packet.
Their exact local reason is `conditional_modifier_2a38030_2872300_unobserved`.
No classifier result, stale temporary vector or zero substitute is published.
Observed B8C/BBC both0 may release this unused family as known empty.

```mermaid
flowchart TD
  E[Actual291CDF1: selected Model / same Character] --> C[Character1C8]
  C -->|present| I[Carrier DWORD B68 full ID]
  C -->|absent| N[Full ID FFFFFFFF]
  I --> R[Actual registry5D1EB80: index low24 / stride16 / full ID8 equality]
  N --> R
  R -->|missing registry or rejected candidate| F[Actual fallback slot5D1EB38]
  R -->|matching candidate| S[Selected linked object]
  F --> S
  S --> G{MagicC 446F6D69 then ID8 differs FFFFFFFF}
  G -->|observed gate false| Z[Helper known zero]
  G -->|true| L[Actual QWORD list60 / signed count6C / stride8]
  L --> D[Each source pointer +1778 PC: one unit100000 occurrence]
  D --> P[Raw keys0 U16 / values68 signedQ64 / countC]
  P --> U[Independent direct family / independently copied rows]
  D --> T[Definition30: B8C then if zero BBC]
  T -->|both zero| K[Conditional family known empty]
  T -. nonzero: exact demanded dependency .-> X[2A38030 classifier / 2872300 evaluated row / temporary header]
  X -. unclosed .-> Y[291B4D0 local header -> Model]
  U --> Q[Same MCP optional following_2921a90]
  K --> Q
```

## Minimal same-query contract and qualification boundary

New optional leaf `following_2921a90` uses schema
`xar.ck3.person-following-2921a90-12004-v1`. Root's existing actual4 battle query
resolves the requested full Character ID. Reuse the source-closed owned-model
association Character1B0→scratch258→Model, requiring Model8==that same Character;
the getter identity is retained but not called. Selected Model+10 is opaque
destination provenance, not a fresh or historical stage baseline.

The direct family retains actual registry resolution, selected object, list
count/address and each ordered row's object/PC identity, physical count, arrays,
readiness and precise copy reason. A partial row does not erase independently
read later rows. Family emission requires its complete row set; a row emitter
releases an independently complete row. The whole helper requires both direct
and conditional families ready. Empty PCs emit one ordered unit request; empty
lists emit none. The request type is an existing operand-only dataclass, giving
no actual4 merger, six-skill, full-person or complete Entry credit.

Implementation must reach the existing `ck3_query_battle_terminal_transition_v1`
requested-Character route, genuine private serializer, main normalizer,
NativeDriver, Service and registered MCP. Native whole fixture and its sole
registered consumer are authored but NOTRUN here; Root owns FIRST. Controls
will exercise mapped signed/repeated/empty PCs, duplicate pointer rows, actual
fallback, full-generation-ID mismatch, failed selected magic/ID, independently
ready rows after partial copies and a demanded conditional family. No new action
or counter-policy is introduced. Following29226A0 is outside this package.

## Authored production route and sole FIRST recipe

The candidate adds `ck3_12004_person_following_2921a90.hpp/.cpp`. Its reader
reuses the already installed exact4 `PersonCarrierDirect12004Bindings` guarded
copy callback, never invoking a getter. `CurrentPersonSample` publishes this
new sibling before the existing actual4 early return; the private current-person
serializer appends it to the genuine terminal frame. The main Python normalizer
adds the optional exact field and full Character-ID join. Existing NativeDriver,
Service and `ck3_query_battle_terminal_transition_v1` dispatch carry the frame
unchanged apart from normalizing native decimal Q64 strings into strict integers.
No new factory, action, Service branch or SDK endpoint is installed.

`normalize_person_following_2921a90_12004` retains independently copied rows.
The three public emitters require whole-helper readiness, direct-family
readiness, or one original `native_index` row respectively. Normalization is
idempotent through Driver, Service and the emitter. A physically empty PC row
remains one unit request. A partial first/repeated row does not hide the later
empty or nonempty copied row. Nonzero conditional counts preserve the exact
classifier/evaluator gap and cannot make the whole helper ready.

New target `xar_ck3_12004_person_following_2921a90_mcp_test`, CTest
`xar_ck3_12004_person_following_2921a90_mcp_first`, links the complete production
Bridge and Runtime closure, with no stubs or omitted production objects. It
authors ten ORIGINAL whole `command_result` controls: mapped ordered `[A,B,A,C]`
PCs where B is empty; empty direct list; absent carrier selecting a valid actual
fallback; full generation mismatch fallback; wrong selected magic; fallback
ID sentinel; unread A values with later B/C preserved; demanded B8C; demanded
negative BBC after B8C0; and a negative direct count. Both terminal samples use
the same actual source state. The full requested enemy ID differs from the
fixture player. These fixture IDs are not real-game query inputs.

The sole registered Python node is
`test_person_following_2921a90_12004_registered_mcp.py::test_person_following_2921a90_12004_registered_mcp_whole_packets`.
Root supplies `PYTHONPATH=<adopted-source>/ck3_autonomous_player/src` and
`CK3_PERSON_FOLLOWING_2921A90_12004_MCP_WIRE_DIR=<new ten-whole directory>`.
It consumes the complete original packets through actual NativeDriver primitive,
main normalizer, Service and registered MCP, then the genuine three emitters.
Only request correlation and the qualified snapshot/hello transport seam are
fixtures. Original bodies, signed extrema, duplicated PCs/keys and unknown
conditional values are not repaired or replaced by the consumer.

Source review is complete; **build, native FIRST and registered FIRST are
NOTRUN** in this candidate. The source diff is not native, fixture-live or
production-live qualification. Root records the actual adopted source, build
closure and new receipts. Historical Native41 qualified cases are not replayed.
