# M4 actor context inner constructor8895D0, actual1.20.0.4

The actual actor-scope parentB17C70 calls8895D0 atB17C98 with RCX=outer output+18. The outer view is0x168 bytes,360 decimal. This source increment closes the child constructor and its necessary virtual operands and provides a pure readonly projection consumed by the parent. It invokes no native constructor, allocator or evaluator.

The existing actual4 constructor130B is reused. Its embedded allocator vptr is module448D2A0, with a backing object at module54DE2E0. Five exact Q64 data slots establish the current path:448D2B0->855830;448D2C0->8558B0;448D2D8->8895C0;54DE2E0->4489F68;4489F78->8571C0. The same855830 wrapper58B and8571C0 body14B are reused. The current8B8895C0 adapter returns `[RCX+C8]`, the backing object assigned by this constructor. The constructor passes a known zero RDX and alignment8 through the wrapper;8571C0 returns without writes at8571CD. Its nonzero path is not reached by this setup.

The current15B8558B0 slot20 leaf sets data to allocator+8 and capacity to8. This is the actual current object's value; other constructor capacities are not reused. Final inner fields are:

| Child-relative offset | Width | Defined final source value |
| --- | --- | --- |
| `00` | Q64 | self+20 |
| `08` | U32 | 8 |
| `0C` | U32 | 0 |
| `10` | Q64 | self+18 |
| `18` | Q64 | module+448D2A0 |
| `E0` | Q64 | module+54DE2E0 |

Only `[0,20)` and `[E0,E8)` are defined,40 bytes. The inline buffer and other untouched bytes retain a false defined-byte mask. Neither initialized padding nor a whole-byte-equal native scope is claimed.

`ProjectM4FactorActorInnerInit12004(module_base, executable_sha256, frame_key, output)` produces continuation08c's child DTO. It requires the exact actual4 SHA and emits two self-relative pointer operations `{0,20}` and `{10,18}`. Their raw placeholders are interpreted only together with those operations; they are not observed null native pointers. The parent applies them after copying into its final nonmovable owned0x168-byte scope. Module, SHA and the original uint64 snapshot-revision frame key travel unchanged.

The ordinary parent readonly overload invokes this source-closed pure projection internally. Supplied arbitrary child `complete_source` flags are not the ordinary query input. The resulting buffer is an owned source-equivalent scope; it does not prove the original caller's native stack context. Continuation12c's dynamic expression still requires a supplied exact same-frame original context/evaluation witness. Its constant branch remains scope-independent.

Evidence is external continuation48c `SOURCE-FROZEN.json`, `SOURCE-PLAN.json`, `SOURCE-GRAPH.md`, `CONSTRUCTOR-REUSE.json`, `VTABLE-NAMED-SLOTS.json`, `REACHED-ALLOCATOR-SLOTS.json`, and the two complete new leaf sources. New finite source totals63B: five Q64 data slots40B and two leaf bodies23B. Reused code is202B. No old EXE, whole-image hash, PE parse, section/census scan, native initializer, query, Game or Git call occurs in this packet.

The fresh no-main `RunActualContext8895D0NewCases12004()` fragment belongs to the unique03/10 connected qualification. Worker validation and actual observation remain absent; source closure alone supplies no live M4 result.
