# M5: independent review of the 2B9D260 prefix

machine_id: xenoamess-full-tower-eb9d2c1186. Local calendar date is 2026-10-27 (Asia/Shanghai); the independent check was 2026-10-26T16:11:14.361Z. This is a later source review, with no new PE/backend/decoder, game, SDK, build or Java source operation.

The actual case closed at 16:08:39.660Z within its 180-second window. Its M5_PENDING_AT_CLOSE history remains unchanged. The new [independent review JSON](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-prefix01/INDEPENDENT-M5-REVIEW01.json>) was written at 16:13:59.016Z: 4972 bytes, SHA-256 `ebd01b8e2e9a1e45d5bdd36fe01a6cd1e3e9724c71898325a678a67e67907a58`. Capacity63 separately authorized this <=4 KiB document and that <=8 KiB metadata file, with no new hold or query authority.

## Confirmed partial result

The recorded original .4 EXE SHA remains `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`. The bounded range is [2B9D260,2B9D2A0), exactly 64 bytes, raw SHA `257454d4ed0da2768dd07f7869c607fc31988977b8fcf66c87e7f57fa58f1e19`.

REA p8 matches all 64 retained bytes. The first 17 Capstone instructions match the first 17 Rizin pDj entries by VA, size and bytes, covering only 62 bytes. All six short-jump targets were independently recomputed from signed raw displacements. The two sentinel JE instructions at 2B9D295/29A both target **2B9D2A2**, outside the prefix.

Entry RCX is the caller's root and RDX its candidate. For each, the prefix loads qword +1C8; a nonnull pointer supplies dword +80, otherwise it uses raw DWORD FFFFFFFF. Either FFFFFFFF takes the external sentinel branch. Only both non-sentinel paths reach CMP ECX,EAX at 2B9D29C. These are unknown raw32 fields, with no proven military, relationship, ID or threshold meaning.

At 2B9D29E, **0F94 is incomplete**: ModR/M and any further operands are missing. It cannot establish a destination, final AL, RET or complete predicate. Rizin's split "invalid 0F" then "XCHG ESP,EAX" for byte94 is rejected as semantic evidence. The first 62 complete bytes have no CALL/RET or explicit memory write; this says nothing about the unobserved suffix.

Two JMP ESIL literals also disagree with the bytes: sites 2B9D272/28B report 142C2D279/292, while signed raw bytes, jump fields and disassembly agree on **142B9D279/292**. The incorrect ESIL text is retained but not used.

Fresh recorded .pdata search has no covering row. Neighbor raw rows decode to [2B9D1C0,2B9D258) and [2B9D320,2B9D364). This gap does not prove a leaf/function boundary or absent exception behavior. The complete normal CFG and returned AL remain UNKNOWN.

## Minimal next question

A separately authorized forward read of at most **[2B9D2A0,2B9D2E0), 64 new bytes**, covers the split instruction and all currently known external targets. Reuse the exact old64 and concatenate the new bytes; decode from known entry 2B9D260 or split start 2B9D29E. **2B9D2A0 is not an established instruction entry.**

The falsifiable hypothesis is normal AL = (A != FFFFFFFF && B != FFFFFFFF && A == B). It is not a Java contract. Counterexamples include SETE targeting something other than AL, a memory write, additional calls/branches/flag changes, a sentinel path not setting false AL before RET, extra zero/high-bit normalization, or any unclosed tail/transfer. Such observations retain PARTIAL and require a new bounded question, without automatic expansion.

The [existing 28BFCD0/A11F60 sources](2026-10-26-m5-rea-callee24c5260-resume63.md) remain reused with their historical provenance. This prefix supplies no new Java ABI, effective-force, arrival, win-probability or game-completion credit.

