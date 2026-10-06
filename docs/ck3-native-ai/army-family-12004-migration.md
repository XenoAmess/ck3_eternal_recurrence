# Army and World migration to CK3 1.20.0.4

The installed Steam build 25734779 has native version text `1.20.0.4` and
EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
Both `.text` and `.rdata` changed. This migration uses independent `.4` address
binders and the existing software DTOs and readers; it does not pass an old
build hash to an old image binder.

The implementation starts from adopted source
`caa4adc3d1278e324cf4ec19774028e9b9138e28`. The existing partial core observation
is separate from a complete gameplay snapshot. Army strength queries currently
call the complete snapshot reader first. The central entry owner will connect
the migrated resource, relationship, event and World families before enabling
that complete `.4` snapshot path.

## Closed World source

| Native entry | Old `.3` RVA | Actual `.4` RVA | Complete body bytes |
| --- | --- | --- | --- |
| War participant predicate | `2494B60` | `2494B40` | 130 |
| Attacker-relative war score | `249AC40` | `249AC20` | 429 |
| Character capital | `28B1CD0` | `28B1CB0` | 187 |
| Default raise Province selector | `24A51B0` | `24A5190` | 912 |

The cached `.pdata` ordinal selects each candidate; actual complete instruction
bytes, preserved member operands, local control flow and ordered relative/RIP
edges establish these mappings. No global RVA shift is inferred. The actual
War storage constructor `2A83C40` to `2A83C20` preserves the RIP references to
registry slot `5D1DE58`, including its pointer publication store.

The World packet also records actual use operands for `GameData+2EBE0`, manager
storage `+20`, War ID `+8`, sides `+20/+80`, CB `+100`, start date `+E0`, targets
`+270/+278/+27C`, leaders `+288/+28C`, claimant `+290` and ended byte `+358`.
Participant ID `+8` comes from the actual callback operand selected by the
participant predicate's RIP reference. The complete 1,328-byte native War
registry iterator preserves the storage indexing operands; the participant
constructor preserves the capacity/count qword at side header +10/+14.
The two-build finite reads for this
packet total 7,354 bytes in 52 calls; whole EXE reads, hashes, PE reparses,
builds, tests, game and SDK operations are zero.

The original 18-byte claimant witness truncated its second instruction. That
partial receipt remains preserved. Only its missing three bytes per build were
read to complete the 21-byte witness; the captured prefix was reused.

Evidence: [World profile source packet](Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/army-family-12004/world-mapping/WORLD-PROFILE-SOURCE-CLOSED.json),
[central core slot proof](Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/core-global-slots/CORE-GLOBAL-MAP.json),
[global build delta](Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/global-pe-diff/COMPACT-PE-DIFF-SUMMARY.json).

## Integration and readiness

```mermaid
flowchart TD
  F[Exact installed 1.20.0.4 freeze] --> C[Actual .4 core binder]
  F --> M[Cached pdata candidates and finite instruction proof]
  M --> W[Independent .4 World binder]
  M -. source closure in progress .-> A[Independent .4 Army and support binders]
  C --> S[Central complete snapshot integration]
  W --> S
  A -. pending family integration .-> S
  S -. FIRST NOTRUN .-> Q[Existing whole Army strength query and serializer]
  Q -. FIRST NOTRUN .-> P[Existing strict Driver, Service and registered MCP]
```

World is source closed and implemented. Native compilation, new fixture,
complete `.4` snapshot, paused query and live qualification are NOTRUN here.
Army/roster/commander/supply are the next source implementation increments in
this same package. Missing source fields go to the finite mapper with their
actual producer and consumer; a disabled or null field does not close migration.

The separately qualified version-independent MCP compact-result change already
preserves the full structured Army payload. It is not rerun for this migration
and does not provide new-build gameplay or measured production speedup credit.
