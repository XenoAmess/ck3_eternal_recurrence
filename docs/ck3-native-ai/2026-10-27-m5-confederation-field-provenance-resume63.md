# M5: provenance of the same-confederation ID filter

Review machine_id: `xenoamess-full-tower-eb9d2c1186`. This is a 2026-10-27 local-date note for an existing-source review observed on 2026-10-26 UTC. Capacity63 authorized this new complete document <=8 KiB under the Root Z4MiB pool through 17:40:26.824464Z. No new PE/provider, build, Java source, game or runtime operation was performed.

## What the field can now be called

The [69-byte normal-path review](2026-10-27-m5-rea-callee2b9d260-normal-path-resume63.md) established only a raw comparison. For a fault-free normal return, let A and B be the separately observed root/candidate DWORDs at `Character+1C8 -> +80`, substituting FFFFFFFF for a null component. AL is true exactly when A and B both differ from FFFFFFFF and their entire DWORDs are equal. EAX is not a normalized boolean.

The existing actual4 production source explicitly names this exact chain **ConfederationID**:

- [prewar_potential_supporters12004.cpp](../../ck3_autonomous_player/native_bridge/src/prewar_potential_supporters12004.cpp:21), 19962 bytes, SHA-256 `27c65323200501d803ac04765606ad8b9c1b56a02bbb26838d70b2186b1874af`.
- [Its shared contract](../../ck3_autonomous_player/native_bridge/include/xar_bridge/prewar_potential_supporters12004.hpp:68), 5300 bytes, SHA-256 `2cea4fbc6f1604c7c1a24a15e87f2ef29527c0a8f1ec97ee9a2a3aba76c55ea5`.

The cpp constants are CharacterConfederationComponentOffset=1C8 and ComponentConfederationIdOffset=80. ReadConfederationSource:189-217 reads the signed32 ID, treats absent component or native -1 as an observed empty source, resolves the ID through storage slot5D1EB78/fallback5D1EB50, and reads that object's CharacterID members at +18/count+24. ResolveComponent:44-60 checks full ID+8, low24 index, storage table+20/count+2C, stride16/+8 object, and rejects a fallback object. BindPrewarPotentialSupportersImage12004:317-332 requires the exact4 executable SHA and enabled existing core/alliance bindings before constructing those slots. This is a source contract, not a fresh installed/loaded observation.

Therefore C4 can be described as **same valid ConfederationID under the existing actual4 source contract**, with native FFFFFFFF meaning absent. It is neither a soldier count nor a faith/culture/Army field. Equal low24 indices with different generation bits are not equal IDs. Zero is not the absent sentinel in this leaf.

## Independent retained-byte cross-check

The existing actual4 collector input was read, without opening an EXE:

`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/shared-span-cache/new-01A23FF0-01A24F1F.bin`

3887 bytes, SHA-256 `63e70c6e8c2c0e81864721c5e0f2c5a58ccb9e40a5e5385e8da1b9a1b419782a`.

Its exact paired decoding is:

`Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261007/battle-pursuit/migration-steam25734779/war-score-membership/actual4-domain/war-map/first01/WarEntryNetworkCollector1A24010-DETAIL.json`

673328 bytes, SHA-256 `b4b40ee27dd46ac624c25c875c0f805cc78038b519c09c9671362f222e45d150`.

This review checked every recorded instruction's ordered offset, size and raw bytes against the 3887-byte input: 1011 contiguous instructions matched through the declared end. This verifies the retained decoding against its source bytes; it is not a new independent full decoder or a current native execution.

The narrow source region independently agrees with the production field and member resolver:

| Actual RVA | Raw operation and bounded meaning |
| --- | --- |
| 1A24B96 / 1A24BA2 | MOV RAX,[R9+1C8]; on nonnull MOV EDX,[RAX+80], otherwise EDX=FFFFFFFF. |
| 1A24BAF | `4c8b05c29f2f04`; signed RIP displacement gives slot5D1EB78. |
| 1A24BBB-1A24BDE | low24 index, storage count2C/table20, object stride16/+8, full DWORD object+8 equals original EDX. |
| 1A24BE0 | `488b05699f2f04`; signed RIP displacement gives fallback slot5D1EB50. |
| 1A24BE7-1A24C00 | object+18 begin, signed count+24, four-byte member elements. |
| 1A24C02-1A24C49 | member resolution verifies full CharacterID+18, then skips the source owner. |

The same collector inlines the C4 comparison at 1A24161-1A2419F, 1A247C7-1A24805 and 1A24D31-1A24D6F: both IDs must be non--1; equality skips that candidate when the optional filter is enabled. It also calls the retained helper1A20040 for other source paths. This links the ID filter to ordered strategic-network candidate filtering, not to candidate arrival or victory.

Historical acquisition `machine_id: unknown` remains unknown: these collector sidecar/map records lack a source-machine witness. The recovered historical build linkage names .4 / build25734779 / SHA98702f88..., as recorded in [the retained-source account](planner-war-entry-power-frontier-20261026.md:70); reading the bytes now does not retroactively supply that identity or requalify an installed process.

## Naming boundary and remaining question

The [older named GetConfederation source](war-film-declaration-relationship-network-2026-09-23.md:39) is explicitly 1.19.0.6, SHA2d00ff31..., machine_id unknown. Its saved static.json is 120243 bytes / `78b0cddf5dedd081972379470b9b992088761ec1f5d6a6949eea724380bc5de7`. It includes string4100BF8 -> registration5063DE/50644C -> callback2621B50 -> complete getter2601D20-2601D42, 34 bytes. That getter reads the older Character+1C0 -> DWORD80. It supports the historical name only. It is not an actual4 registration/getter proof and no uniform address or layout shift is inferred.

No extra named4 GetConfederation registration/getter was present in the specifically reviewed source/cache navigation or REA63's held references. This does not establish that none exists anywhere. The field's current name is supported by the explicit existing actual4 production contract and its matching retained ID/member source; a new native named-getter claim remains ungranted.

C4's original sampling close remains LATE by78.399 seconds; combined128 Rizin RAM decoding was not executed after unsupported omj. This note neither repairs that historical process result nor claims dual-decoder/whole-case PASS.

No new query is needed to repeat the closed 69-byte predicate. A more useful candidate for the remaining caller gate is the actual C2 call at24C52B4 (`e827e9ffff`) to24C3BE0. RCX is C2's original receiver; RDX is its separately obtained qword key. Nonzero callee AL makes C2 false. The retained runtime index gives RF[24C3BE0,24C3C4A),106 bytes, unwind5109DB0. Exact-name checks in the shared-span cache, native71-continuation-20261010, REA cases and resume61/62 batch filenames found no held body. That finite check is not a whole-library absence proof.

The next falsifiable question would be whether those106 bytes compare a current/default term or implement a different predicate. Key membership alone cannot prove non-default value. Callees, global values, initializer effects and exception paths stay opaque unless separately acquired. This is a proposed source question only: no fresh PLAN, capacity execution card or backend was started, and no bridge/write/arrival/win-probability authority is granted.
