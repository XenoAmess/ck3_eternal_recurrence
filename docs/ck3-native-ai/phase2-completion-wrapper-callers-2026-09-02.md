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

The next distinct observation is wrapper entry `0x3B9E030`. Reading `[RSP]`
before replaying its exact 15-byte prologue maps the runtime return address to
one of the frozen callsites by subtracting five. Counting entries would also
show whether the wrapper is externally reinvoked after the completion publish.
Only after that runtime owner is known should a caller-specific continuation be
selected. No thread or OS-wait semantics are inferred, and public ABI/readiness
remain unchanged.

The reproducible extractor artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\completion-wrapper-callers-static-extract.json`,
SHA-256 `6BF4F6E2A8BD68355F1E74C230D7FF66E65052FDFA045A7250BE6E5B28FE6EA3`.
