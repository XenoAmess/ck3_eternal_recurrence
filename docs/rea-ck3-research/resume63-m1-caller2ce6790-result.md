# M1 finite caller2CE6790

machine_id: `xenoamess-full-tower-eb9d2c1186`; observations2026-10-26 UTC. This separately authorized query follows one of the [six raw E8 candidates](resume63-m1-inbound2603af0-text-result.md). It covers only RF `[2CE6790,2CE6A3D)`685 B/unwind52A4138, with fresh row155158/12 B matching `9067ce023d6ace0238412a05`. No other four unverified candidate bodies, callee bodies or global data values were followed.

Raw SHA `26095bd003bca5327e8fea86f434f530fbd564514fd764078c0d1ccc60569736` covers all685 B. Capstone and Rizin agree on160 instructions, ordered addresses/sizes/bytes. Independent raw signed arithmetic checks21 branches and8 direct calls; a hand-built normal graph matches all32 heads/51 edges. Every noncall branch remains inside the RF; the only RET is2CE6A3C, with no explicit trap instruction. Opaque calls, memory faults, exception paths and string-loop termination remain unresolved.

Incoming RCX is retained inRBP; original RDX inRSI. The first input's pointed record supplies tag4/rawID orFFFFFFFF. The local resolver uses pointer5C67568, low24 slot/capacity+2C,16-byte slot pointer+8 and fullID+18 comparison, else fallback5C67570. RDI holds that character/fallback pointer. Opaque `2B25980(entry+50,originalRDX,entry+10)` returns the second object, retained inRSI; its raw Fact tag+14/fullID+10 and the first object's Char tag+1C/fullID+18 are checked again before the writer. These are observed field/tag relations, not proof of the entry producer's domain role.

The actual direct CALL at2CE697F targets2603AF0. The following writes all dominate it in the normal instruction graph, with no intervening opaque call:

| Input | Transfer at this call |
| --- | --- |
| RCX | RSI, the2B25980 return pointer |
| RDX | zero-extended freshDWORD[RDI+18] |
| R8 | MOVR8D,FFFFFFFF gives00000000FFFFFFFF |
| R9 | LEA address5C99EE0; content not read |
| Fifth low byte | immediate1 atcaller[RSP+20], corresponding to callee entry[RSP+28]; higher bytes unknown |

This differs from the [96 B caller's zero byte](resume63-m1-caller29b7590-result.md). If the retained [writer](resume63-m1-member-validity-result.md) reaches its internal flag branch, this nonzero byte selects the local bypass of the two visible2C7DED0 calls. The duplicate-membership precheck can still return before the flag; neither this caller nor that local bypass proves successful append or absence of all validation. The caller's natural-inheritance/ordinary-AI/GUI source, input producers and the business meaning of this flag remain unknown. A prior summary's additional claim of an invalid-member return before the flag was unproven: held3B62 selects fallback and continues. The old C11 receipt/C12 crosscheck are preserved; this narrower conclusion supersedes that wording.

After the call, the caller does not test raw RAX as a success boolean. It rereads the character ID and second object's vector+48/count+54, scans32-byte rows at+8, and enters another opaque message path if no row is found. An already existing matching row also satisfies the check. ReturnRAX is path dependent and is not a normalized success contract.

Decoder458ms/owned-job peak26066944 B; REA service4149ms/Rizin peak591966208 B. Minimum close22:56:58.346Z was65.033s from the fresh authority T0 and preceded the23:01:53.313364Z deadline; four exact owned PIDs were absent. These are minimum-close/provider costs, not full preparation or research time. The original440 B stderr/four string-region warnings are retained. No full string-discovery, speed/token, outer joint-peak or Job0 claim is made.

Fixed data capture was RF12+body685; no new header/table search. The decoder's two whole-file streamed identity checks make202081193 B requested PE I/O including the697 B data; SDK identity/parser reads and Rizin's repeated685 B are additional, and physical I/O was not measured. Flat Evidence and portable bundle were serialized inRAM and retained as sole gzip files with original/compressed SHA and verified roundtrip, not plaintext copies. The original PAYLOAD_UNASSESSED close is immutable. [Source index](sources.json) binds the later mechanical receipt and independent review; no Game/Steam, Java, Shared or native-dossier qualification follows.
