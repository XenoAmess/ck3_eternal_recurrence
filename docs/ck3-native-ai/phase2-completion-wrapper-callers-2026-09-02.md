# Phase-two completion wrapper callers (2026-09-02)

This exact-build static package freezes the scheduling boundary outside
completion wrapper `[0x3B9E030,0x3B9E266)`. It did not start CK3 and does not
repeat the already-frozen consumer internals.

The executable contains 618 instruction-bound direct calls to `0x3B9E030`
owned by 525 PDATA functions. Of those functions, 432 call it once and 93 call
it twice. The canonical callsite-list SHA-256 is
`32B88FEACB2D43E2284C116C53A448D8C1F14FDBD4B2BFB97C0725622E861A8C`;
the caller-function-list SHA-256 is
`DFEF530E330DEEEC2154A5A8D826605A46EC46C8E670249162FC0586938715C5`.
This fan-out does not identify a unique selected runtime owner.

Three nearby concrete callsites expose the bounded condition shapes without
expanding the other template-family callers:

- `0x3B8AB00` is skipped by an empty-range equality; its surviving path calls
  the wrapper once.
- `0x3B9B87C` requires a nonempty range, mode other than 3, and a derived batch
  count other than 1.
- `0x3B9DB04` is unconditional once per invocation of
  `[0x3B9DA60,0x3B9DBAD)`.

Inside the wrapper, consumer calls `0x3B9E10B` and `0x3B9E175` both precede
the producer loop `0x3B9E230..0x3B9E246`. After the selected producer publishes
state 2, the current invocation can only process remaining producer entries,
execute teardown `0x3B9E248..0x3B9E264`, and return at `0x3B9E265`. There is
no self-call or branch back to either consumer. A later consumer tick therefore
requires a new external wrapper invocation, and none is guaranteed by this
function itself.

## Producer carrier versus consumer ring

The bounded task builder `[0x3B9DBB0,0x3B9DD4E)` (PDATA unwind
`0x4F10158`, bytes SHA-256
`3EC3E5D8366717B979C04125CBF8EAD0D2AF6D42DB9930E0CA48D8DB89FCF05A`)
allocates a `0x78`-byte task, initializes state `[task+0x60]=0` and reference
count `[task+0x64]=1`, then stores it at descriptor offset `+0x18`. The
descriptor is always appended to the wrapper's fifth-argument producer list at
`0x3B9DCE6`.

The consumer carrier is separate. Only queued mode increments the task
reference count and calls `[0x3B9EBD0,0x3B9ED27)` at `0x3B9DCD9`; that function
writes the task pointer into its ring at `0x3B9ED05` and advances the tail at
`0x3B9ED0E`. In synchronous mode this enqueue is skipped. The wrapper uses the
same mode condition: queued mode branches from `0x3B9E214` directly to teardown,
whereas synchronous mode iterates the producer list at `0x3B9E230` and calls the
state-2 publisher.

This closes the raw-live discrepancy. The retained runner report SHA-256 is
`DD6F61C871AD371F3BCE843BDA864E7D6317267AE839CB7A65EC399CCD4098A8`;
its terminal evidence index SHA-256 is
`7E6B405A03C0E3F4A799F5836C6FACC4E6261E6C3E997886D0D01FFB32876487`.
The consumer hook was installed with failure code zero and executed 1,908
times, but observed no state 2/3 task and no selected callback, while the
producer publish at `0x3B9CFD7` was observed. This is evidence for two carrier
paths, not hook failure: the synchronously published task was never a member of
the consumer ring scanned at `0x3B9DEA7`.

The next distinct observation is wrapper entry `0x3B9E030`. Before replaying
its exact 15-byte prologue, read `[RSP]` to map the runtime return address to one
of the frozen callsites by subtracting five, `RCX` for the scheduler owner, and
`[RSP+0x28]` for the fifth-argument producer-list carrier. Entry/return counts
then establish lifetime without observing the unrelated consumer ring again.
Only after this runtime owner and carrier are known should a caller-specific
continuation be selected. No thread or OS-wait semantics are inferred, and
public ABI/readiness remain unchanged.

The reproducible extractor artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\completion-wrapper-callers-static-extract.json`,
SHA-256 `353599579C6415FCE0D8C5A8164EF1BE8E8A1F53BD7A97A44AC4D2B2D357EA1F`.
