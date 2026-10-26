# M5: actual 24C3BE0 byte/default comparison and caller gate

machine_id: `xenoamess-full-tower-eb9d2c1186`. Observations: 2026-10-26 UTC; local document date: 2026-10-27. This bounded study uses the installed official REA6.8/Rizin service and the existing Capstone research tool. No Java/native production source or game process was changed.

The [same-confederation field study](2026-10-27-m5-confederation-field-provenance-resume63.md) remains SOURCE_CONTRACT. Its "valid" C4 IDs mean non-FFFFFFFF DWORDs; the C4 leaf does not resolve that ID, prove a current entity/member or establish snapshot stability.

## Originals and preserved execution history

Parent P is `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m5-callee24c3be0-01`; successor R is `P/rea02`. All files remain within the original complete4MiB parent budget:239316 logical bytes/50files; native allocation/peak unmeasured.

| Original | Bytes / SHA-256 |
| --- | --- |
| P/CAPSTONE-DIRECT-STDOUT01.json | 6943 / `4d62d888ae84ca3300ed90f14afff2352750ab02e07256bb1f86dabbdb6295fd` |
| P/raw/body-024C3BE0-024C3C4A.bin | 106 / `612f18274f373c723a3d3b508cfcb3132dfdb1e08a71096e54dab0a35f965f90` |
| R/REA-DIRECT-EVIDENCE01.json | 29450 / `29a96f8b9491ae2fb469143d8572e1a8ccef497a4f187b68d76d072d29c11280` |
| R/REA-DIRECT-BUNDLE01.json | 29726 / `77fac735e62ad961b04025cf8d75da17ee5b2d6f66866c54e620dbe152758145` |
| R/CROSSCHECK01.json | 3864 / `683944a60724c411530e3b5f34d0398de6bdc44b0e5c46d3ea8e260660f1c428` |
| R/CASE-RECEIPT01.json | 7880 / `24715309e29ba9488c2a5b0c9b7e7169fc2ba1e59346b0c2b01960faa01e011d` |
| R/CASE-CLOSED01.json | 1516 / `6c06501ac35b369f08e8aa020c97e139b092920873e374f0bb500b6b4332ac7a` |

The current PE was SHA98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518,101040248B. Fresh pdata row128550 is [24C3BE0,24C3C4A,5109DB0], exactly106B. Capstone captured it at17:29:53.597Z. The first card was120work+60close. Its REA entry correctly rejected `Expired route` before any REA provider or digest; the actual106B decoder had already succeeded. P/CASE-CLOSED01.json is1505B/`a846a81ac8209f88efa32a714fb41271d69405c48091d83ad1dbd10d99843b01`,17:30:28.922Z, on time with0owned. This is one-stage closure, not a successful two-stage case.

Preparation01 incorrectly replaced the first metadata.update and truncated the decoder. This was caught before PE/provider execution; READY was withdrawn and complete02 controls/PLAN used. Failed preparation/check files remain. Syntax PASS did not establish control flow.

Root separately authorized the REA-only successor at300work+60close. It reused106B and explicitly counted Rizin's106B reread; no second Capstone body was acquired. After final argv was prepared, execution immediately froze the fresh card, invoked REA, and performed minimal close before analysis. Rizin PID300316/owned-host67336 spawned17:40:28.280Z, exited0/closed17:40:31.919Z; service.close succeeded. Observed peak owned-job memory was592646144B under1GiB, without limitReached. Minimal close17:40:36.227Z was42.576s after card T0 and before17:45:53.651197Z, with both PIDs absent. Provider command wall was4282ms. This is not whole-research time or a performance comparison. Outer Job0/joint peak remain NOT_MEASURED; Shared qualification is NOT_GRANTED.

## What the normal paths actually compute

Inputs are RCX=receiver S and RDX=key pointer K. The original K is kept in RDI; its qword copy at local rsp30 is passed to A11F60. That callee is not re-sampled. Its historical complete iterator model is [already reused](2026-10-26-m5-rea-callee24c5260-resume63.md), with original machine/provenance limits unchanged.

The106B body has31instructions,5blocks,6normal edges, one opaque CALL at24C3C06 toA11F60, and one RET at24C3C49. Raw signed rel32/rel8 arithmetic, ordered bytes/addresses/sizes and the complete local graph match both decoders. There are no external noncall jumps.

A precise fault-free normal-path model is:

```text
beginBefore = QWORD[S+38]
endBefore   = beginBefore + signextend32(DWORD[S+44])*8
P           = A11F60(beginBefore,endBefore,&localKeyCopy)
beginAfter  = QWORD[S+38]                     // reread after opaque call
endAfter    = beginAfter + signextend32(DWORD[S+44])*8
if P == endAfter:
    V = 0
else:
    I32 = low32(SAR64(wrapping64(P-beginAfter),3))
    V = 0 if signed(I32)<0 else BYTE[QWORD[S+68]+signextend32(I32)]
AL = 1 if V == BYTE[K+9F28] else 0
```

The signed branch tests EAX, not the full64-bit shifted difference. There is no separate visible index<countAfter check. Caller-valid copied extents may justify a valid index, but the body alone does not prove collection stability or memory safety across A11F60. Full EAX/RAX is not normalized: SETE only replaces AL. Stack save/local writes are explicit; an opaque callee can have additional effects. Rizin's automatic `is-pure=true` is not accepted as a purity proof.

A useful counterexample is a missing lookup: V becomes0, so AL can still be1 when K+9F28 is0, or0 when that byte is nonzero. "Missing key means false" is not this leaf's contract. Likewise signed64 index negativity cannot replace the low32 signed test.

Rizin's JMP at24C3C32 preserves another tool-text defect: rawEB02, disasm and jump target correctly giveVA1424C3C36, while ESIL says142583C36. The original is retained; the ESIL literal is rejected. Loader warnings about skipped large string regions grant no string-search coverage. No extra backend was run to repair those observations.

## Domain source contract and parent use

Existing actual4 [prewar_additional_supporters12004.cpp](../../ck3_autonomous_player/native_bridge/src/prewar_additional_supporters12004.cpp:298),28503B/SHA`af3a71572c88ff9d97b9f28e880c0ec0bc0858ffdced94750ab8f2afcf541860`, calls term+9F28 a uint8 default_level. Its ForcedRound reads contract+38/+44 qword keys, takes the first matching term, reads the parallel active byte at contract+68 and skips active==default. Thus **default-level comparison** is supported by an existing actual4 SOURCE_CONTRACT. This does not independently bind C2's singleton-return+F10 key to a named loaded term.

The [actual C2 parent](2026-10-26-m5-rea-callee24c5260-resume63.md) at24C52B4 passes the same original receiver/key. It first requires its own lookup-present gate, then returns AL1 only when this child returns AL0. Under a stable valid collection, this is a present key whose active byte differs from its definition's default byte. The parent and child perform separate lookups and post-call end reads; stability/purity is not assumed in the raw model.

This closes the local equality mechanism. Loaded key identity at A149D0-return+F10, the mandatory gate's loaded predicate at1D65640-return+EF0->+1930, initializer effects, cache lifetime and real world/current-frame qualification remain open. Those binding/producer edges are the next questions; this note starts no query.

## Java scope remains separate

Host actually passed the related whole classes: APP94 FamilyResultReducer8, FamilyPendingProducer6 and FamilyRecordedBetrothalFulfillment6; the later native-transport material-continuation class passed7. All27 had0failures/errors/skips. R/CASE-RECEIPT01.json pins the four actual XML files and observation times.

The two earlier Keep->Replace failures concerned preserving observed plan details, not date replay. The fix checks baseline fields, no command, unchanged material, relation and held reasons; cadence checks same-day convergence, next-day reread and source-date separation. This is SOURCE+LOCALTEST, not an LS MaterialStore integration or game acceptance. The106B study creates no Java ABI or Native-submit authority, and strategic +308 still does not establish effective arrival or victory.
