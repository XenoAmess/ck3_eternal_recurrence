# Resume63 C13: batch roster to caller gate and byte1 writer

machine_id: `xenoamess-full-tower-eb9d2c1186`. Observed2026-10-26; fresh owner scope through2026-10-27T12:00Z. This is an offline static observation, with no paused-game or loaded-actor authorization.

The exact RF `2785FD0..27866AD` supplies a real CALL to `2603AF0` at `2786593`. It iterates a pointer roster alongside32-byte records, runs its own gate, then passes outgoing fifth lowbyte1 to the writer. The caller does not test writer success or recheck each member afterward. Input constructors and natural trigger remain UNKNOWN; longest prefix was only a selection reason.

## Scope and method

Current PE:1.20.0.4/build25734779,101040248 B, SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`, imagebase140000000. Fresh row135948 at file98470032 was `d05f7802ad66780274062705`, exactly RF `[2785FD0,27866AD,5270674]`. Only12 metadata B and1757 body B were newly requested; no new header/table search. Rizin reread1757 body B separately. Scoped cache miss is not global absence.

Existing Capstone and official REA used fixed ranges with calls/hasnext/jmp.after disabled. Both decoders matched all433 instructions/1757 B. Raw signed arithmetic independently matched84 branches,13 direct calls and28 RIP targets;113 blocks/185 normal edges, soleRET27866AC, no explicit trap or outside noncall edge. Graph reachability does not prove path feasibility; opaque calls/unwind were not followed.

Raw SHA `8364d40bb129c8a759f1f04619efb998d67f70ba0d30960d439c30a10def5ac5`. Sole gzip flat/bundle retain original/compressed hashes and RAM roundtrip/deep equality. The440 B of Rizin warnings remain in the original. M1 independently checked the bytes, targets, CFG and data flow. Its first RIP parser misplaced displacement in two CMP-rip-imm8 instructions. ModRM parsing corrected all28 targets without another provider.

## Source and normal control flow

Entry inputs are O=RCX, A=RDX, B=R8 and X=R9. A separate U=QWORD(entryRSP+28) is an incoming pointer, distinct from the outgoing writer fifth byte. Their classes and producers are unproven.

N=signextendedDWORD[A+C] is captured once. For i<N, P=QWORD(QWORD[A]+8*i), with parallel record Q=QWORD[B]+32*i. A/B construction and the parallel-count contract remain unknown. O+E68/O+BA8/O+E98 use visible generation-aware resolvers; their business names are not assigned. P+1C0/+1D0 and two comparisons against Q-held object IDs can skip an iteration. Tags do not identify a natural trigger.

The precheck faction F is locally validated by raw tag46616374, fullID+10 and BYTE(QWORD[F+20]+E5C)!=0. E5C has no proved loader/default/inherit_membership binding. At6496 the caller invokes2C7DED0(P,F,&pack,null), with initial five bytes [1,1,0,0,0]; AL0 skips the iteration. Opaque code receives pack, so its initial value cannot be assumed stable.

P+1B8->+110 supplies an old ID orFFFFFFFF. Equality with precheckF+10 skips the writer. A nonzero28CB780(P) can lead to opaque2A6E270 before continuing; removal or notification meaning is not established. Writer F is freshly resolved from O+BA8 after opaque calls, so its equality with precheckF, and unchanged target, are not proved.

At657B caller[RSP+20] lowbyte=1; at6580 R9=&5C86E98 (contents unread); at6587 R8D=FFFFFFFF, yielding00000000FFFFFFFF; at658D EDX=DWORD[P+18]; at6590 RCX=reloadedR15. These setup sites and the prior caller gate dominate CALL6593 in the encoded normal graph. If the writer reaches its flag branch, byte1 bypasses its two visible2C7DED0 calls. Its earlier duplicate precheck can still return. This caller already has a prior gate, so byte1 does not mean absence of validation.

After CALL the loop advances i without testing RAX/AL or rereading that member's row. Afterloop opaque2A6E270/leader resolution may store U+10. That output and existing-member skip do not prove append. Nonstack stores preclude purity credit.

## Actual cost and terminal state

| Measurement | Actual |
| --- | --- |
| Decoder / owned peak |567ms /26267648 B |
| REA service / Rizin peak |4366ms /592920576 B |
| Authority issued to bind |193483ms |
| Issued to first minimum close |237002ms; bind to close43519ms |
| Minimum close |23:38:32.535Z, before23:40:35.533559Z deadline |
| Owned PIDs |four absent; remaining0 |
| Later final receipt from T0 |900048ms; preparation/research total unmeasured |
| Explicit decoder PE read requests |202082265 B; SDK/parser and repeated body additional |
| Outer joint peak / Job0 / speed or token benefit |NOT_MEASURED |

Completed owners require followup_task; ordinary messages suffice while running. Unused windows are not provider work. Original minimum close keeps PAYLOAD_UNASSESSED; later review and receipt do not rewrite it. Case hardcap512KiB; final logical256261 B and conservative postreceipt upper372736 B are point/upper values, not measured allocation or historical peak. Physical release0.

## Consumer boundary and exact records

Java's inheritance input design needs an actual trigger, candidate/actor and same-frame source contract. This static caller does not grant GameKnown, persistent validity or current ordinary-risk input. Preserve cold/episode clear and do not replay old member/risk state. No Java, DTO, policy, Game or Steam change was made. The other three raw caller candidates were not sampled.

The [final receipt](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-caller2785fd0-01/CASE-RECEIPT01.json>) is8608 B/SHA `1ebefe2395249b23b53173635c843374e118419f133415d8b47f7580759d4db3`; it pins the plan, actual argv, raw, both exports, cost and original close. The [independent M1 review](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-caller2785fd0-01/INDEPENDENT-M1-CALLER1757-REVIEW01.json>) is7513 B/SHA `a12e0e4205c23c25f849e89be1d451a011806e639483581f3d90fc7a761cb151`. [Source index](sources.json) retains the small exact refs. No Shared/native-dossier credit follows.
