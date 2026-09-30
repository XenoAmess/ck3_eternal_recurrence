# H3937 noncanonical slot diagnostics — 2026-09-30

## Actual blocker

R0121 (`desktop-3fevhd2-1c74096080--vanilla--R0121`, execution
`6e2edcfd-ed5e-4c1b-9997-e552c1744dcd`) returned six accepted/available
read-only query envelopes. The overall result remains RED, with zero formally
certified six-read runs. The final route-contact receipt reports inventory
`partial`: 2048 scanned, 1604 empty, 436 canonical, 8 noncanonical and 8
unresolved. Its `same_source_across_route=false` is also gated by both scans
being complete and does not alone prove a physical source change.

The exact #685 producer (`e7c0727b7e851de803f79ce04806feccfa33149d`) rejects a
positive, slot-matching CUnit if its raw kind is nonzero, its CArmy full ID
cannot resolve, or its resolved CArmy backlink is a different full CUnit ID.
The old wire keeps only counts and canonical rows. It cannot identify which
of these reasons applies to the actual eight slots. No fleet or stale-slot
classification is inferred from those counts.

## Narrow source candidate

The existing route-contact command attaches additive
`physical_army_inventory_diagnostics.before/after` result siblings. The original
strict physical-inventory field set and canonical unit rows are unchanged.
Each records the original reader status and its two original scans. Each scan
binds date, war, subject and storage capacity, with at most 32 noncanonical
samples plus the complete noncanonical count and a `truncated` flag.

Samples contain slot index, full public CUnit ID, raw kind, whether CArmy
resolution was attempted, its requested full ID, resolution success, the
resolved CArmy's canonical CUnit backlink and the classifier reason. A nonzero
kind retains the original short circuit: it never reads the +0x178 CArmy field.
No process addresses are published. Reasons remain observations; they do not
authorize skipping a slot or grant a gameplay/date action.

Diagnostics live outside `PhysicalArmyInventoryV1`. Its fields, default
equality and the original reader/mailbox completeness and source fences remain
unchanged. The existing CArmy resolver, including its full-generation identity
check and `-1` rejection rule, is unchanged. No additional native query,
capability, command or mutation is introduced.

## Verification and consumption

The new focused C++ fixture directly includes the production reader TU to
exercise its actual private classifier without running the old game-access
matrix. It covers canonical acceptance, kind 1 and unknown nonzero kinds,
unresolved CArmy IDs, full-generation backlink mismatch, the 32-sample bound
and diagnostic JSON binding. Root authorized only this focused native fixture
compile/run; full native pair compilation remains pending the reviewed freeze.

Build only the frozen pair with the existing H3937 inventory mailbox option,
plus target `xar_ck3_physical_inventory_diagnostics_v1_test`, then run CTest
with exact regex `^xar_ck3_native_bridge_physical_inventory_diagnostics_v1$`.
Record the actual DLL/injector hashes and compile flags. The next run requires
a new source-matched binary binding, prepared state, rebind, native preflight,
operator profile and fresh root-owned run ID/screen/Steam/GO. Existing R0121
state and source stay historical. A new binary cannot be authorized by changing
only the old run config.

## Existing evidence

- `C:/h3937-go-sdk-20260930/attempt-12/receipt.json` binds the original small
  six-envelope slice; envelopes 02 and 06 contain the matching aggregate counts.
- `C:/h3937-go-sdk-20260930/attempt-13/inventory-binding.json` isolates the
  final inventory predicate without changing it.
- `C:/h3937-go-sdk-20260930/attempt-16/existing-evidence-summary.json` and
  `log-tail-scan.json` record the bounded raw-evidence search.
- `C:/h3937-r0121-inventory-reverse-20260930/attempt-01/freeze.json`
  (`BF7FC3B84DA0538DD20492685790AC7FA67DAB6256E4F3009D1761CA7157A660`)
  binds the independent exact-build source classification.

No CK3, MCP, pipe, screen operation or native build was performed while
preparing this source candidate. R0121 cleanup and its RED result are retained.

## Canonical source adaptation recipe, 2026-09-30

The original candidate and its recorded build remain historical evidence. The external read-only source recipe now targets canonical base `c69260e65b63bf8f8b8ae42e3aee8f2a68561660` and carries the full original physical inventory producer, route status contract/production, mailbox, private OFF option and receipt serializer together with these diagnostics. It preserves current ROLE error helpers and all other canonical code. A resulting canonical tree has different bytes; this recipe does not certify its build, binary pair, tests or live result.


## ie 隔离源码交付（2026-09-30）

本次仅在固定 ie 起点 `d5f3c51215439b23f578c8973d5d74ac01f1493c` 上接入冻结的 H3937 producer 与 single consumer 源码。master 冻结点为 `c69260e65b63bf8f8b8ae42e3aee8f2a68561660`；未接收冻结点之后的 master 内容，只交付 ie。

复用的 fixture、pair、no-launch 与实机记录分别绑定其原始执行树。旧 `0d06` pair 不认证本次适配后的原生树；本次没有构建、启动游戏或认证六读，formal 仍为 0。Steam 持续离线。
