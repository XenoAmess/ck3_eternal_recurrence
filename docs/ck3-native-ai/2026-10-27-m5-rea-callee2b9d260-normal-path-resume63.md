# M5: 2B9D260 normal return paths and the failed sampling window

machine_id: xenoamess-full-tower-eb9d2c1186. Local date: 2026-10-27 Asia/Shanghai. Independent check: 2026-10-26T16:33:31.780Z; review file: 16:34:57.662Z.

The leaf's normal return logic is now supported by the retained raw bytes, Capstone rows and independent instruction/branch arithmetic. **The sampling case remains LATE by 78.399 seconds, and its Rizin combined-RAM decode failed.** These are separate conclusions; neither the original close nor its M5_PENDING history was changed.

[Independent review JSON](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-tail01/INDEPENDENT-M5-REVIEW01.json>): **5614 bytes**, SHA `91ef2b4abfdf1ff61fbca6ec71155dc9e09c9825fdba74f40d0e78e1c5596ee1`. This and the <=4 KiB document use a separately authorized post-close metadata scope; no new provider, PE, SDK, game, build or Java source operation occurred.

## Evidence and normal-flow closure

The same recorded .4 EXE SHA is `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`. The [old 64-byte prefix](2026-10-27-m5-rea-callee2b9d260-prefix-resume63.md) was reused. Only [2B9D2A0,2B9D2E0), 64 new bytes, was acquired. New64 SHA is `2a7ec569281a76e975de44e1d4ec82fbdec972e71f4d97d04393795abc891475`; stitched128 SHA is `8b99fbb6de23dc4763b1964d1fb5853aff032482cf9fb79193c1e8921cda50fb`.

The first new byte completes old 0F94 as **0F94C0, SETE AL** at 2B9D29E. C3 at 2A1 is RET. At external target 2A2, **32C0** is XOR AL,AL, followed by C3/RET at 2A4. Opcode/ModR/M arithmetic independently confirms these four instructions.

All 21 reachable rows match their retained raw bytes. Six signed short-jump targets were recomputed. Entry-based traversal closes **69 bytes, 10 blocks, 12 edges**, with RETs at 2B9D2A1 and 2B9D2A4, no call, external edge or explicit data-memory write. Reachable69 SHA is `a8d3a287e71ac776278bf065d85921890ae4742cee77da5d2efc99ba1bf8a823`. The other **59 bytes** contain padding/neighbor code and are not attributed to this callee. The retained no-cover .pdata result does not prove unwind/fault semantics.

REA p8 independently matches new64, but unsupported **omj** prevented the combined128 p8/pDj steps. Provider exit0 did not make those commands successful. This is not a 21-instruction dual-decoder PASS or a Rizin CFG result. The first17 byte/size/VA checks from C3 remain reusable, including rejection of its two wrong ESIL literals.

## Returned value

Let A be the first actual root read and B the later candidate read. Each reads qword object+1C8, then dword pointed+80 when nonnull, otherwise raw DWORD FFFFFFFF.

Both sentinel branches reach XOR AL,AL/RET. Otherwise CMP ECX,EAX is followed immediately by SETE AL/RET. On normal fault-free paths:

`AL = (A != FFFFFFFF && B != FFFFFFFF && A == B) ? 1 : 0`

`EAX = (B & FFFFFF00) | AL`

Only the low byte is Boolean. For example, derived B=FFFFFFFF yields false AL but EAX=FFFFFF00; this is arithmetic, not a runtime sample. A separate RAM check of 196 pointer-presence/zero/high-bit/sentinel combinations agrees with the instruction derivation; it is not JUnit, native execution or game qualification.

No additional bytes are needed for this leaf's normal AL decision. Field meaning, actual producer/consumer freshness, valid object domains, faults, loaded rules and the surrounding network's world meaning remain unknown. The reads are sequential, not an atomic snapshot guarantee. This establishes no Java ABI shortcut, effective force, arrival or win probability.

The actual case consumed 258.399 seconds against 180 seconds. Provider close was timely at 16:21:13.898Z; owned-PID absence was read at 16:24:41.429Z; final close was late at 16:24:41.431Z. Owned children were zero, while outer Job0/peak were not measured and Shared qualification was not granted. The original RED evidence remains intact.

