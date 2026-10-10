# Current mode0 Task block 31B4810 (1.20.0.4)

The actual current-base mode0 parent `31B4A10` reaches `31B4810` at `31B4A20` with RCX equal to the existing qualified Task and RDX equal to the null tooltip pointer. A nonzero returned AL makes the parent return false immediately; a zero returned AL lets the independently owned parent continue. The replacement mode1 path does not reach this child.

The complete held pdata interval is `[31B4810,31B495C)`, 332 bytes. Its exact span SHA is `05d4249e5892bb9d838e5ba67ffa2105aad285acddc46bf4396b865cee1cb5fd`. Cache-first acquisition required 332 new actual bytes through the shared D range claim. Exact build is CK3 1.20.0.4 / Steam25734779, image SHA `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.

`MOV31B4823` copies Task QWORD `+18`; `MOV31B4827` copies that pointed object's QWORD `+40`. The latter pointer supplies actual child RDX at `+2374` and R8 at `+1E38`. `MOV31B4839` supplies child ECX from Task DWORD `+44`. `CALL31B483C` reaches `31BDDA0` with those literal operands.

The selected null-tooltip branch returns raw AL 0 when child AL is zero. Only a nonzero child AL reaches `CMP31B4849`, reading Task DWORD `+40`; a value other than `FFFFFFFF` returns 0. The equal value reaches `TEST31B4853`, whose null tooltip skips the entire formatting tree and returns AL 1 at `31B4936`. No formatting allocation, virtual method or diagnostic call is reconstructed or invoked.

`ReadClergyTaskBlock31B4810Operands12004(read_context, ReadMemory, actual_task)` copies the mandatory literal inputs. `ResolveClergyTaskBlock31B4810NullTooltip12004` consumes a separately source-closed `ClergyTaskBlock31BDDA0Child12004`, matching actual callee and all three literal operands, then reads Task `+40` only on the reached nonzero-child path. An unavailable child or reached copy remains unavailable. `31BDDA0` was sent to 02 for an exclusive source owner rather than expanded here.

The existing base clergy producer owns exact4 binding, Task/full-owner qualification, its current paused transaction, capture epoch and before/after checks. The candidate reuses its read callback and actual Task; it creates no new frame, query or CanFire entry point and has no native fallback. Raw AL remains distinct from an unavailable observation. The new no-main cases join the current base packet composition, with no old fixture replay. This source packet supplies no live clergy result, appointment or M4 credit.
