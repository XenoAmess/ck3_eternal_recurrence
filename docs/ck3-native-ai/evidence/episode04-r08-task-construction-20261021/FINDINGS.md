# R08: a concrete task-construction and dispatch edge

Machine: `desktop-3fevhd2-1c74096080`. Observed on 2026-10-21 UTC; the exact extraction time and file identity are in `SOURCE.actual.json`. This is static research of the retained CK3 1.20.0.4 image with SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`. It does not qualify a running game.

The newly verified static chain is:

`28F6FCB CALL 2901B30 -> std::function reference wrapper -> 3F91AD0 / 3F91650 -> job+38 -> vtable 47643C0 slot+10 -> 2909460 -> 290DC00`.

`2909460` is a complete nine-byte leaf thunk: `MOV RCX,[RCX+8]; JMP 290DC00`. `2909470` constructs the same vtable at the destination and copies the source object's +8 pointer. Thus this dispatch object's +8 holds the task; task+0 remains the scheduler's atomic cursor. RTTI names a `std::_Func_impl_no_alloc` reference wrapper around a Character-array parallel-for specialization. The complete type name is retained in the bounded type-descriptor bytes, without demangling a business name into it.

`2901B30` allocates 0x1B0 bytes and builds the task at allocation+0x130. It copies the configuration into task+8 and writes task+68 from the input capture's +40, task+70 from capture+48. Its stack wrapper receives vtable 47643C0 and this task pointer, then is passed to 3F91AD0. In 3F91650 the wrapper clone result is stored at new job+38; the async path submits that job through 3F92670. 3F91AD0 also has a synchronous fallback that invokes the already-held worker 3F909F0. These are static paths, not proof that a particular live job took either path.

The newly decoded caller 28F6AA0 selects a bank with byte [entryRCX+4CB8]. For this maintenance task, its descriptor is entryRCX+2630+bank*2640, and count is descriptor+C. The inline context contains entryRDX+8 and entryRCX+4D08. The same caller separately computes unsigned [entryRDX+9C] modulo 30 and uses that remainder for a different descriptor at entryRCX+E0+bank*2640+remainder*18. This 30-bucket calculation must not be substituted for the maintenance task's fixed bank-array selection.

Still open: the producer and membership rules of the selected +2630 array; the caller's actual scheduling occasions; same-instance job/task/Character membership in a live window; raw c/d writers; and the business joins to an actual debit, payer and cadence. No c/d component is classified as military here. No native instrumentation, build, SYSTEM change, SDK action or game step was performed.

The binary spans and selected instructions are a small reproducible source record. Incoming byte locators are only locators; the listed edges were then checked at decoded instruction boundaries and, where present, against unique PE exception-table ranges. The retained whole-image SHA is reused; before/after stat identity was checked, without rehashing the whole EXE. Review retention on 2026-10-28; this record is not an indefinite protection grant.
