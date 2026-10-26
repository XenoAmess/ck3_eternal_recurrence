# M1 finite caller29B7590

machine_id: `xenoamess-full-tower-eb9d2c1186`; 2026-10-26 UTC. The [stream locator](resume63-m1-inbound2603af0-text-result.md) supplied a raw candidate at29B75E6. Root separately authorized only the smallest complete RF `[29B7590,29B75F0)`96 B, with current row143255/unwind51095E8; no other five bodies or callee expansion.

Fresh current RF12 B matched `90759b02f0759b02e8951005` before the body read. Raw SHA is `38816d5b81774512b9cb9aea6a1dbe8d87e9ee441ba6e6ebcdbf8df09019ec61`. Capstone/Rizin25 instructions cover all96 B. Independent signed arithmetic confirms four conditional branches and the CALL at+0x56 to2603AF0; three RIP targets and hand-built6blocks/9edges match Rizin. The only RET is29B75EF. This candidate is now a real local direct call; the other five remain unverified raw matches.

Incoming RCX is saved inR10. The caller takes raw32 `[original+8]`, masks24 bits for a slot lookup through pointer5D1DE90, checks capacity+2C, reads base+20 and the16-byte slot's pointer+8, then compares object+10 with the full original ID. Any failed check loads fallback pointer5D1DE10. Both paths reach the same writer call; fallback success/non-nullness was not separately established.

| Argument at CALL2603AF0 | Observed transfer |
| --- | --- |
| RCX | resolved receiver or fallback |
| RDX | zero-extended DWORD `[original+C]` |
| R8 | MOVR8D,FFFFFFFF produces00000000FFFFFFFF, not64-bit minus1 |
| R9 | address5C96288 fromLEA; its content was not read |
| Fifth low byte | caller `[RSP+20]=0`, corresponding to callee entry `[RSP+28]`; higher bytes unknown |

All normal local branches converge on the call. The caller performs no qualification test on its result; ADD RSP/RET forwards the callee's raw RAX. Within the previously retained [writer](resume63-m1-member-validity-result.md), this zero byte cannot take the nonzero-byte bypass once that branch is reached. Its duplicate-membership precheck can still return before the flag. This is not a guarantee of successful membership or persistent validity.

The original input record's class, both ID producers, registry naming, R9 data and the actual natural/AI/GUI producer remain unknown. No target rebinding, inheritance trigger, whole-program validation guarantee, purity or opaque-call effects were established. The retained writer's local mechanism does not fill these source gaps.

Decoder419ms/owned-job peak25407488 B; REA service5981ms/Rizin peak592715776 B. Minimum close20:51:38.757Z was86.948s from the fresh T0, before20:56:11.809996Z; own four PIDs were absent. The initial metadata reader encountered ENOENT while that close's exec session was still running, then polled the original session to exit0; neither close nor provider was rerun. Original440 B stderr/four string-region warnings remain, with no full string-discovery claim.

M1's separate3645 B review SHA is `18168126bede6ef07523ed1eb4833ea0c17527ca292946f58604060ed6c652dd`; combined6373 B receipt SHA is `6706ce7b976f1d42823a3c4fa55c8a32419a1b70504005542c5cefa9ddcb7d03`. [Source index](sources.json) binds all originals. Native point212264 B plus32768 B directory guard and at most8192 B closing receipt gives253224 B under256KiB; it is not a historical peak or physical release. Outer joint peak/Job0, complete preparation/research time and token benefit remain unmeasured. No Game/Steam or Shared/native-dossier qualification.
