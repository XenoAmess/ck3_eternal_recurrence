# Physical Entry association at actual writeback

The exact-build function `2657AA0` is the physical Entry cache writer. Its original RCX is retained in RBX; original RDX is Province. It resolves the full Regiment ID at Entry+8, calls `26344A0` at `2657AEF`, and copies the returned six stats to Entry+30/+38/+40/+48/+50/+58 before RET2657B27. Root's single 136B capture is [the actual source evidence](Z:/ck3_mod_rewrite_process_assets/g2-background-20261010/person-physical-entry-frontier/actual-entry-writer01/SOURCE-CAPTURE.json). The frozen build is 1.20.0.4/25734779, SHA `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.

This source package adds a scope around that actual writer and reuses the existing two Knight consumption observers. Nested wrapper records retain their original output scratch identity and independently copied Ci contexts. After the original writer returns once, the scope attaches an owned copy of the actual Entry identity, Province, full Regiment handle, six postwrite cache fields and raw unsigned RAX return to the exact nested wrapper sequences. Current query pointers are never substituted for that historical writeback.

The original writer return is the last loaded screen Q64 bits, not an Entry pointer. The detour therefore has a `uint64_t` return and preserves it unchanged. Its displaced 16-byte prefix includes a RIP-relative load. The 36-byte trampoline preserves the first six push/sub bytes, expands the load into `mov r8,base+5D1F340; mov r8,[r8]`, preserves `mov r9,rdx`, and jumps to `base+2657AB0`. The expansion uses only R8, already overwritten by the original instruction, and adds no call, stack adjustment or flag change.

```mermaid
flowchart TD
  W["Actual writer scope: Entry + Province"] --> O["Original2657AA0 exactly once"]
  O --> G["26344A0 resolves native stat branch"]
  G --> K["Existing wrapper + nine actual context-return captures"]
  K --> R["Immutable wrapper record; scratch identity retained"]
  O --> C["Original six Entry cache writes complete"]
  C --> P["Copy actual Entry postwrite + raw original RAX"]
  P --> A["Attach to exact nested wrapper sequence"]
  R --> A
  A --> Q["Existing combat MCP + ordinary Service numerical projection"]
  D["Direct query scratch outside writer scope"] --> U["Unassociated query event remains distinct"]
  Q -. "not a complete historical Person or Entry simulation" .-> F["FullPerson / FullEntry incomplete"]
```

The physical association does not depend on equality of the copied numeric fields. A mismatch is published as a comparison result; an auxiliary copy failure preserves the association and precise unavailable fields. Neither case suppresses the original native operation. A direct `26344A0` query remains `bridge_query_scratch`; an unclassified wrapper remains unclassified. Only a completed actual writer scope grants `native_physical_entry_writer` provenance.

The optional per-event writeback preserves old packets and the existing MCP arguments. It makes native cache production observable and allows the exact per-Ci arithmetic projection to be compared with both wrapper output and physical postwrite. It does not grant complete Person, Entry, battle outcome, ordinary action or G2 milestone credit. Root has qualified this package offline as described below; no actual game capture is claimed.

The sole synthetic fixture deliberately supplies max17/siege-111/pursuit222/screen-333 in its typed original callback. These test signed cache transfer and the unsigned return bit pattern, not the native Knight branch's ancillary arithmetic (which remains zero in the source-derived projector). Its damage/toughness follow the actual Ci calculation. The expected four numerical mismatches remain visible while all six wrapper-to-Entry copies match. No comparison mismatch is converted into a loss of physical association.

## Actual Native67 qualification, 2026-10-10 / W41

Root's retry03 passed the one new native whole and its sole registered MCP /
Service / real NativeDriver consumer at **2026-10-10 00:18:23.323875–00:18:42.823002
UTC** (08:18 CST). It compiled one corrected fixture and relinked that fixture,
with **zero production recompiles and zero Runtime/archive/DLL relinks**. The
original attempt's 456 successful compilation inputs and production link
results were retained. Root then sealed the [Native67 canonical qualification](Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/entry-live-fix67/ROOT-PARENT-RUNTIME-INCREMENTAL-DLL.json)
at **00:19:41.987988–00:19:43.548727 UTC**.

The physical source pins remain separate:

| Role | Exact source pin |
| --- | --- |
| Compiled production, serializer and unchanged Python consumer | `f19c1e4ffcb2bf7a7ac66b67970d4ab2f8342b45` |
| Fixture copier initialization correction | `9aa48214f8177e2011370965b16bdf535f837c97` |
| Final compiled fixture / qualification source | `813458e9c2c1ef4f5cdbee02c17613a680996643` |

Both preceding RED attempts remain evidence:

* **attempt01:** native FIRST exited 1 at the required context-PC assertion.
  The fixture had omitted initialization of the shared Native65 aggregate-PC
  copier. Its production helper correctly returned
  `preparation_pc_copier_not_configured`. The nine-line fixture correction
  configures the existing Memory/PersonCarrier copier without invoking either
  preparation original. Preparation call counts remain zero and historical
  preparation metadata remains absent.
* **retry02:** native FIRST exited 1 at the whole serializer literal assertion
  during 00:12:35.688312–00:12:49.410838 UTC. Production `Raw64` emits lossless
  quoted decimal uint64 values; the fixture had searched for unquoted digits.
  The one-line correction requires the exact quoted
  `original_return_value` string `18446744073709551283`. The complete value,
  sidecar/origin checks and all other assertions remain required.

The final whole retains writer/wrapper/context original call counts **1/2/18**,
two distinct physical-writer and direct-scratch events, nine independently
copied Ci contexts per event, six signed cache fields and the full unsigned
writer return. The registered consumer checks the production numerical
projection and all physical cache comparisons. This is **static-ready** native
and registered-consumer qualification. It does not qualify native hook
installation in a running game, an actual physical Entry capture, FullPerson,
FullEntry, a battle terminal result or new G2 progress. Native68's separate
current-row publication/join remains outside this qualification.
