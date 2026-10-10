# Construction owner modifier index4E — actual C86670

The owner-factor caller can now obtain its index4E signed-Q64 input through
a separate read-only, supplied-input leaf. The leaf selects the actual loaded
definition, computes the observed literal/zero branches, and accepts a
qualified virtual-output value only for the exact demanded dynamic operands.
It calls no constructor, interner, evaluator or gameplay function.

Target is CK3 1.20.0.4 / Steam25734779, executable SHA256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
Only the newly assigned [C86670,C867E1) source body was acquired: 369 bytes,
pdata row `[13133424,13133793,85197588]`, source SHA256
`149a6189a7a0647d02c3bdbf380811f391ec6476074151e5243e6ee2fc049b15`.
The source plan, exact literal decode, held helper inputs and API contract were
frozen before the production header. Existing actual4 named evaluator,
support constructors and intern source were reused without another capture.

## Actual arguments and output

The actual `2B9CBA0` parent CALL at `2B9CC13` supplies output `&rsp40` in RCX,
index `4E` in EDX and the `B17C70` context `&rsp70` in R8. The parent makes no
explicit R9 assignment. C86670 retains only RCX, sign-extended EDX and R8;
it contains no instruction that saves or reads incoming R9. Its `C86755`
instruction explicitly clears R9D before CALL `37542D0` at `C86763`.
Null evaluator R9 comes from this actual instruction, not a guessed parent
argument or a global ABI assumption.

The loaded named database getter `A07970` reads module+`5D1DD50`. C86670
reads provider+`EF0`, then the QWORD at signed-index×8. This caller's actual
index is4E. The new reader copies exactly that slot. It does not substitute
a canonical-name lookup or invent a table-capacity branch.

The complete retained actual4 `37542D0` source establishes:

- Definition+`70` null and byte+`7B` zero writes exact signed-Q64 zero without
  reading+`68`.
- Definition+`70` null and byte+`7B` nonzero copies signed-Q64+`68` unchanged.
- Definition+`70` nonnull calls expression+`8`, virtual slot+`30`, with a
  temporary Q64 initialized to zero. It copies the temporary's post-call
  QWORD to the original output. An unknown call cannot be replaced by that
  initialization zero or by the virtual call's return register.

Both the evaluator and C86670 return the original output address. The leaf
models its first signed-Q64 value. Negative values remain negative here;
the independently owned parent performs `CMP [RAX],0 / CMOVGE` and clamps
them to zero. Units and interpretation remain the parent's existing factor
contract; index4E is not used to infer an unobserved modifier value.

## Pure production interface and demanded context

`construction_owner_modifier_4e_c86670_12004.hpp` exposes:

```cpp
ConstructionModifier4EResult12004 ReadConstructionOwnerModifier4E12004(
    const ConstructionModifier4EAccess12004& access,
    const M4FactorActorContext12004& context,
    const ConstructionModifier4EVirtualOutput12004* virtual_output = nullptr)
    noexcept;
```

The result's `factor_input` directly supplies the existing
`ConstructionOwnerModifier4EInput12004` from the owner-factor leaf: original
receiver, exact uint64 frame key, index4E, optional signed-Q64 and source-ready
fact. The frame is the unchanged `CampaignRootFrameV1::snapshot_revision`
copied from the construction request's `expected_snapshot_revision`; it is
not hashed, recoded as public revision, or compared to an independent counter.

The context is the separately owned `M4FactorActorContext12004`, passed by
const reference. The selected original receiver and full CharacterID remain
distinct from a substituted played Character. A qualified prefix requires
defined raw DWORD0=4, QWORD8 equal to the zero-extended full actor ID and
DWORD10=FFFFFFFF, as well as the producer's actor-identity qualification.
The constant/zero branch does not dereference the supplied context and does
not demand unused inner initialization or padding. The dynamic branch
additionally requires `complete_source` for its demanded context.

The owned context is stable source-equivalent software storage; copy/move is
disabled by its producer. It is never called an observed original native
stack scope. Dynamic supplied values bind to the exact const context object
and its raw storage aliases `{context,null,context,support118}`. A natural
stack result needs an independently proved source-equivalence supplier;
actor ID or frame equality alone is insufficient.

The dynamic token also preserves selected definition, expression receiver,
observed vtable slot30, null evaluator R9, distinct original/temporary output
identities, completed qualified virtual call and optional post-call Q64.
The reader compares the actual definition's inline/heap string with the
supplied interned key's exact two-byte length and character bytes. It checks
the descriptor byte14=1 and DWORD18=FFFFFFFF rather than substituting another
named property. Missing or mismatched demanded operands keep output absent
and source_ready=false; a qualified zero remains present and available.

This closes a conditional numerical input, not generic expression evaluation
or complete native-call side effects. Existing trigger, variables and
modifier source may supply a qualified dynamic result; the leaf does not
reimplement their trees. Profiling, TLS/intern allocation, support allocation
and cleanup are not replayed. No native-evaluation occurrence is claimed.

## Integration and validation ownership

03 owns the parent mode3 provider and its single fresh compound fixture;
10 owns the new compound's centralized compilation/run. The production call
is `ReadConstructionOwnerModifier4E12004(...).factor_input`, supplied to05's
`ReadConstructionOwnerFactorInputs12004` and `EvaluateNullDetailFactor12004`
for the same original receiver/frame. 08/48 own context source, and their
prefix/complete status must stay separate.

The external recipe checks negative literal preservation followed by parent
clamp, flag-zero without reading raw+68, dynamic missing-value isolation,
qualified dynamic zero/negative, and wrong context/frame/generation/definition/
name/R9 rejection. This lane runs no fixture or compiler and replays no old
Entry, construction, role or calendar qualification. The centralized new
result must be recorded separately before claiming compiled readiness.

External source/delivery packet:
`D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-12c/`.
The repository, Git, Game and SDK are untouched by this lane.
