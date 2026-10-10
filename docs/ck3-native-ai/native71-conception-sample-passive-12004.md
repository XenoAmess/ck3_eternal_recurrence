# Native71 actual conception sample producer, 1.20.0.4

This producer observes a naturally reached `E46530` call and its return while
task19b's `2929B40` parent scope is active on the same thread. It forwards the
three original arguments once and returns the original signed64 RAX unchanged.
The query reads retained owned records. It performs no helper call, extra draw,
machine-body replay, seed regeneration, prediction or monthly scheduling.

Exact source pin: CK3 `1.20.0.4`, Steam build `25734779`, EXE SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The already held `[E46530,E46621)` body is241B, SHA-256
`73f7d36add188727a897301db67dbabc36637e44b9c8668c2b38762a1b6bb5ef`.
The helper ABI, inclusive0..10000000 returned sample and counter semantics were
closed in [the prior source topic](native71-conception-sample-comparison-12004.md).
That qualification is reused without another body execution or game/image read.

## Source tree and detour anchor

```mermaid
flowchart LR
  parent["19b natural 2929B40 active extent"] --> call["2929D94 CALL E46530; return2929D99"]
  call --> helper["Original receiver RCX; RDX0; R8D10000000"]
  helper --> state["DWORD0 plus2 modulo2^32; DWORD4 read only"]
  helper --> returned["Actual signed64 returned RAX"]
  call --> threshold["Actual caller RBX comparison threshold"]
  parent --> key["Shared13 clock identity, parent scope ordinal, thread, source full IDs"]
  state --> record["18b owned child entry/return record"]
  returned --> record
  threshold --> record
  key --> record
  record --> consumer["19b/20b exact parent join and signed comparison"]
```

The stolen prefix is exactly15B: `48895c2408 48896c2410 4889742418`,
three five-byte MOVs from RBX/RBP/RSI to the native caller's RSP home slots.
It contains no branch, CALL, relative displacement or RIP operand. The hook
patch is a14B `FF25 00000000 <entry-thunk-u64>` jump plus NOP. The29B trampoline copies
the15 held bytes and jumps to `E4653F`, before the fourth home-slot MOV. It
neither samples nor changes the native receiver. Install/uninstall use the
existing quiesced exact-anchor/protection/flush/rollback contract. Root owns
bridge lifecycle wiring and live installation; this leaf changes no shared
service, serializer, driver or CMake file.

The17B entry thunk is `49 89 D9` (`MOV R9,RBX`) followed by an absolute jump to
the four-argument C++ observer. It leaves RCX/RDX/R8, RSP and the genuine native
return address unchanged. The original is still called with its three genuine
arguments. The held body first references R9 at `E4655B MOV R9D,R10D`, which
overwrites and zero-extends all64 bits before any read. It saves incoming RBX
at `E46530` and restores it at `E465CF`. Thus the copied signed64 value is the
same RBX consumed by the caller's `2929D99 CMP RAX,RBX / JGE2929DC9`, after
the preceding positive-threshold gate. The trampoline and entry thunk occupy
one46B executable allocation. `THRESHOLD-ABI.json` pins this complete proof.

External source and provenance:

- `continuation-18/root-literal-source/helper-E46530.json` and existing `.bin`;
  no new duplicate body file.
- `continuation-18b/SOURCE-ANCHOR.json` pins the held source and stolen bytes.
- `continuation-18b/SOURCE-MECHANICS.json` records reuse of the existing64
  owned detour mechanics, with independent entry anchor and signed64 ABI.
- `continuation-18b/THRESHOLD-ABI.json` closes actual RBX capture and unused
  incoming R9 from the held241B source.
- `continuation-18b/research-plan.json` and rendered graph distinguish held
  source closure from prospective runtime observation.

## Parent admission and record

`ConceptionSampleParentScope12004` is shared with the19b parent and45b provider
child. Its parent key is `(clock_identity,parent_scope_id)`; `process_clock`
is the parent's shared13 entry sequence. It also carries the active flag,
thread ID, actual first/second Character pointers, full DWORD generation IDs,
and original third argument `sample_receiver`. The parent callback reads only
the current thread's active extent. No second parent hook is installed here.

Admission requires actual caller return RVA `2929D99`, original lower0 and
upper10000000, a matched nonzero receiver, and the same active parent thread.
Both Characters must still carry `Char` magic at+1C and the parent's full IDs
at+18. Calls outside that admission forward once and produce no causal child.

Each admitted invocation copies the receiver's two DWORDs before and after the
original call, its exact arguments, signed64 returned RAX, source pin, parent
key and shared13 before/return event coordinates. `threshold_at_sample` retains
the original caller's signed64 RBX; `threshold_capture_ready` requires the
matched parent/event/source identities and a positive threshold. When the sample
is also source ready, `comparison_at_sample_passed` records the exact signed
RAX<RBX predicate. The storage's native class
name remains unknown. The source transition check is DWORD0 plus2 with32-bit
wrap and unchanged DWORD4. Capture failures retain unavailable fields and
clear `causal_sample_ready`; they never suppress the original call or alter
its return. Expired parent extents, changed generations, event-domain/thread
mismatches and an out-of-source-domain return also clear readiness.

`ReadConceptionSampleObservations12004(clock_identity,parent_scope_id)` returns
retained copies for the one parent. Zero/zero returns the bounded retained
journal. The oldest/latest sequence and overwrite count describe the256-record
window. Journal ordinals are not process event timestamps. Optional child-return
delivery runs after original return and after releasing the journal lock. Root
and19b can copy that record;20b can consume its sample only with the exact same
parent key and source pin. A journal read never resolves a native object.

The serializer leaves `native_class_name` and `loaded_scalar_reconstruction`
null. It makes no probability, eligible-pair, pending
pregnancy, active pregnancy, birth or monthly claim.20b's threshold inputs and
the parent's actual AL/writes are separately qualified observations.

## New validation and remaining boundary

The new owned fixture exports `RunConceptionSamplePassiveFixture12004()` for
central10's one fresh19b/18b compound. It uses typed local originals that mutate
owned twoDWORD storage and return supplied signed64 values. It covers original
once, unchanged full-width return, counter wrap, read-only DWORD4, parent/thread/
receiver/full-ID admission, missing state, parent expiry/generation change and
query isolation. A new owned fake caller loads a full-width RBX and reaches the
installed entry thunk, preserving native ReturnPC and all three arguments;
the continuation calls the typed original. It does not execute the held helper
RNG body or repeat prior comparison
qualification.19b additionally connects its own active TLS parent to this child.

At candidate preparation, the new compound is pending central10 execution.
Compile/fixture success cannot establish that a live naturally reached sample
has been observed. Root owns actual build installation and future passive
runtime evidence. No live sample, current threshold or final comparison is
claimed by this source candidate alone.
