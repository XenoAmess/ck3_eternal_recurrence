# Resume63 C15: caller2787C10 forwards the batch inputs

machine_id: `xenoamess-full-tower-eb9d2c1186`. Actual2026-10-27T01:01Z; independent review followed. Review through12:00Z. CALL2787FC1 is a real instruction targeting2785FD0 in the local normal-flow graph. Its five batch arguments are forwarded from entry inputs. The incoming dispatcher, input constructors and natural trigger remain UNKNOWN.

## Fixed observation and independent checks

Current PE:101040248 B, SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`, imagebase140000000. Fresh RF row135954 at file98470104 matched `107c7802db83780290072705`, tuple[2787C10,27883DB,5270790]. New observation was12 metadata+1995 body=2007 B; no callee, neighboring body, global value, unwind body or external tail was followed.

Installed Capstone5.0.7 and official REA/Rizin0.9.1 returned469 contiguous instructions covering1995 B, equal by VA/size/bytes. Independent raw arithmetic checked74 branches,42 direct CALLs and16 RIP targets. The raw CFG has95 internal heads/162 internal edges plus one address-only external node: provider total96 nodes/163 edges. All469 instructions are locally graph reachable. Removing CALL2787FC1 disconnects the external tail in the normal returning-callee model; this is not a path-satisfiability, termination or exception proof.

There is no RET or explicit trap in this RF. The unique noncall tail is27883D6 `e9d5f44800` to2C178B0. Rizin reports484 stderr B: four maxregion warnings plus `ERROR: Cannot find function at 0x142c178b0`. The last graph node has an address and no body. The query did not read outside code; full-return and abnormal-path closure remain PARTIAL. Exit0 is not clean-stderr or whole-function success.

## Five forwarded pointers

Let entryRSP=E; after eight pushes and SUB248, fixedS=E-288(hex). Normal Win64 nonvolatile-register preservation is assumed across opaque calls.

| Batch2785FD0 input | Source in this RF |
| --- | --- |
| RCX O | entryRCX saved inRSI |
| RDX A | entryR9 saved inR14/home[E+20], restored after optional loop |
| R8 B | incoming fifth qword[E+28], reloaded[S+2B0] |
| R9 X | entryRDX saved inR13 |
| stack fifth qword U | entryR8 V homed[E+18], reloaded[S+2A0] then stored[S+20] |

Thus U=V is a pointer. It is not the low-byte1 argument that the downstream member writer2603AF0 receives. No explicit store changes this home slot before reload; opaque alias effects on the pointed data remain unknown.

Entry V selects memory64(V+8); when the selected object's+1C0 is zero, memory64(V) is used instead. This does not identify old/new/heir objects. An optional loop consumes the supplied A pointer-roster and B32*i companion records using A+C signed count. It does not construct A/B or prove their lengths and domain identities.

The body performs writes and opaque calls before and after the batch call. After2787FC1 it tests a saved incoming byte inBPL, rather than targetAL/RAX. There is no direct U+10 or member-row/new-append postcondition read. Conditional ID substitutions through registries5D1EC10/78 are visible; object classes and faction-target binding are unproved. It is not a pure validation body.

## Cost and close

| Actual measurement | Result |
| --- | --- |
| decoder Owned wall / Job peak | 497ms /25935872 B |
| REA service / Rizin Job peak | 4193ms /591753216 B |
| authority to bind / first minimum close | 20.979s /38.786s |
| first minimum close | 01:02:00.470Z; four exact PIDs absent |
| original close deadline | 01:07:21.684172Z; met |
| final rich receipt | 01:13:53.126Z; T0+751.442s |

Decoder explicit PE IO was202082503 B; provider repeated1995 body B and SDK identity/parser IO are separate. Physical IO, full preparation/research time, joint peak/Job0 and speed/token benefit were not measured. Original minimum close keeps PAYLOAD_UNASSESSED and active_exec_sessions=UNKNOWN; the outer tool later exited0 without rewriting it.

Both sole gzip exports retain original/compressed SHA and exact RAM roundtrip: flat384086 B/gzip39062 B, portable384362 B/gzip39250 B. No uncompressed export copy was written. Final READY forecast503808 B corrected preliminary PLAN462848 B before execution. Case cap512KiB; final point34files/4dirs/logical282030 B, page+directory upper385024 B. This is not measured Native allocation or a historical peak; release0.

The first owner CFG checker rejected the external stub before writing CROSSCHECK. A held-JSON-only correction added the address-only node; it did not repeat sampling. Receipt draft9189 B was refused by a write-before8KiB guard; compact final7171 B was created. Original close, bytes and failures remain.

## Remaining source boundary and Java consequence

[C14](resume63-m1-inbound2785fd0-text-result.md) only located this raw E8; C15 supplies the separate boundary and argument evidence. The next missing source is the incoming2787C10 dispatcher and constructors of O/X/V/A/B. The tail587 B RF is metadata navigation only; completing it would not establish that producer.

The actual actor/frame, natural inheritance, new append and target rebinding stay UNKNOWN. Java ordinary-risk/persistent validity retains cold/episode clearing and does not replay old member/risk state. No Java, Game, Steam, Shared or native-dossier qualification is granted.

[Receipt](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-caller2787c10-01/CASE-RECEIPT01.json>):7171 B, SHA `6744b9211d604051a0765aefd6ccdbb060a5c285a639a59c4f3da43bc5458f71`.
[Independent review](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-caller2787c10-01/INDEPENDENT-M1-CALLER1995-REVIEW01.json>):8187 B, SHA `ca8ddb1fcbda56e3560dc2849091b3de9c11069e531787baeb994b6cb3697829`.
