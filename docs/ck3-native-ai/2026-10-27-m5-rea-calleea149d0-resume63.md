# M5: A149D0 shared-table return, resume63

`machine_id: xenoamess-full-tower-eb9d2c1186`. Actual observations are UTC 2026-10-26; this filename uses local 2026-10-27 (Asia/Shanghai). This is finite normal-path research, with no Java edit or game qualification.

The [119-byte caller](2026-10-26-m5-rea-callee24c5260-resume63.md) leaves its original receiver in RCX when calling A149D0, then reads QWORD `[returned RAX+F10]`. The new body shows no read, save or dereference of that incoming RCX. Its local return selection uses a shared slot, rather than an explicit per-contract table selection.

Actual `.4` RF is `[A149D0,A14A27,51095E8]`: 87 bytes, 18 instructions. Both RIP-relative QWORD loads resolve independently to `imagebase+5D1DED0`. A nonzero first load branches to A14A22 and returns that RAX. The zero path calls opaque `3F8B640`, reloads the same slot at A14A1B, and returns the reload on normal return. The helper's return value is discarded. The result is full RAX pointer bits, not a Boolean AL/EAX.

The helper receives RCX=1, RDX=newRSP+20, R8D=0 and R9D=100. The local 16-byte area contains an address of `imagebase+448D018` at +0, dword 30 at +8, and byte 0 at +C. Bytes +D..F have no visible initialization here. MOVAPS/MOVDQA move all 16 bytes; this does not prove a fully initialized structure. LEA forms addresses, without reading the addressed literal. No literal or global value was independently captured.

The body has stack-local explicit stores and one opaque call. It does not prove helper initialization, purity, absence of side effects, a nonnull reload, or exception-path closure. Mutable global contents and opaque effects can still depend on wider state. The finite result only closes this local getter mechanism.

Current source `ck3_autonomous_player/native_bridge/src/prewar_additional_supporters12004.cpp` (28503 bytes, SHA `af3a71572c88ff9d97b9f28e880c0ec0bc0858ffdced94750ab8f2afcf541860`) binds this slot as `subject_contract_database_slot` at line 426. This is a SOURCE_CONTRACT name. Lines 487-490 consume database **+F00** for ForcedRound; C2 consumes **+F10**. Their term identity must remain distinct. The [historical .2 note](ck3-1.20.0.2-prewar-participants.md) already warns against treating F10 as the F00 war obligation; it does not establish the current .4 F10 name. The [106-byte comparison](2026-10-27-m5-rea-callee24c3be0-resume63.md) remains valid with its loaded-key identity UNKNOWN.

Case root: `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m5-calleea149d0-01`. Original records:

- `CASE-RECEIPT01.json`: 7192 bytes, SHA `977bef29f6aacdeb6a4032374c87b15d3ad7eb9bb9df96a468b9724184266ccf`.
- `CROSSCHECK01.json`: 2920 bytes, SHA `d5a46fbd1835fc0c7dfab02689133a452be8ca59b30fa2af0f1f1321f8e297e5`.
- Raw87 SHA `fc598f0c9743e7ad9a7025c67d9f2546882c36b85d9b708df52dd20cd6fa41dc`; it differs from the old .2 expected hash, which was not current-body proof.
- `CASE-CLOSED01.json`: 2099 bytes, SHA `f27a91615b29e5f1f73dbf07843db74e0b02f5c909bd25ba14dc81f919a42a90`.

Capstone/Rizin ordered bytes, five independently calculated relative targets, hand-listed three blocks/three edges and the sole RET A14A26 match. Flat evidence equals bundle record by value/type. Rizin's guessed stack argument, MOVDQA `type=null`, automatic string/global-zero annotations and large-string warnings remain preserved, without semantic authority.

Actual minimal close was 20:51:18.603Z, before the 20:56:11.809996Z deadline; four owned PIDs were absent. Native peaks were 25108480 bytes (decoder) and 592453632 (Rizin), with no limit reached; service.close succeeded. Node heap was 128 MiB; outer Job0/joint peak remain unmeasured. Close preceded domain review. No provider ran afterward. Next reuse should locate current F10 registration provenance, without automatically following the helper or promoting this result to arrival, victory, live-world or Java execution authority.
