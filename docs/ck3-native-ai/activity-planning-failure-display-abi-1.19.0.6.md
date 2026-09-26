# Activity planning failure display ABI (CK3 1.19.0.6)

This is a static, exact-build continuation of the private feast planning
reader. It closes the **second argument's storage and text lifetime** at
`CActivityListDetailHostView::CanPlanActivity` slot 25. It does not establish a
stable failure key, complete planning semantics, a live paused capture, or an
activity action.

## Frozen image and reproducible ranges

- `ck3.exe` SHA-256:
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`;
  image base `0x140000000`.
- The repository's `native_bridge/research/disasm_ck3.py`, run with this exact
  executable, disassembles RVAs `0x15051F0` (size `0x40`), `0x28CFC50`
  (size `0x190`), `0x96F4C0` (size `0xF0`), `0x7E97D0` (size `0x60`),
  `0x33C9140` (size `0x160`), and `0x33C8FE0` (size `0x140`).

## Caller-owned output and lifetime

The normal slot-25 method at `0x15051F0` puts its incoming `RDX` into
`[RSP+0x20]` at `0x150521A`, so the same pointer becomes the **fifth** argument
of final evaluator `0x28CFC50`. It does not construct that argument. A separate
native wrapper at `0x96F4C0` provides a concrete caller pattern: it zeroes the
first eight bytes and the size at `+0x10`, sets capacity `+0x18` to `15`,
null-terminates the inline buffer, then passes the output pointer as the fifth
argument at `0x96F515` before calling `0x28CFC50` at `0x96F523`. This is the
32-byte MSVC small-string layout. The wrapper returns the still-owned output
string to its caller; it does **not** destroy it.

The same image has a string destructor at `0x7E97D0`: it frees the buffer when
capacity is at least `16` through the game's allocator and resets size to zero,
capacity to `15`, and the first inline byte to NUL. The final evaluator uses
this destructor for its temporary rendered string at `0x28CFDB7`. A private
caller must deep-copy the returned bytes while the output string is alive and
release an allocated output with this exact-build destructor. It must not use
the agent DLL's unrelated allocator to free native string storage.

The output is **display text**, not a stable key. On the third-trigger false
path, `0x28CFCF8` passes the output string to `0x963A80`, builds a temporary
rendering object, and at `0x28CFDB1` appends its rendered bytes and length via
`0x81B220`. The temporary is then destroyed at `0x28CFDB7`. The first two
trigger evaluators at `0x33C9140` receive the same output pointer in `R8` and
can write failure display through their own evaluation path. The third
evaluator at `0x33C8FE0` receives the output pointer conditionally. When the
fifth argument is null, the final evaluator cannot populate display text.

## Remaining private reader boundary

The private binder and source adapter now accept a false result with a
nonempty copied `failure_display_text` and an absent `failure_display_key`.
The observer represents the absent key as typed
`unknown/native_stable_key_unresolved`, while preserving the text as known.
This needs no schema change because the observer's typed fields already
represent that combination. A partially populated key reference or empty
false-path text still fails the capture. The call chain above proves only the
native byte-string text output; it does not expose a separately copied stable
localization key or prove that every false path returns nonempty text. Treating
the text as a key, deriving a key from English output, or forcing a synthetic
key would make the contract false.

The next narrow implementation is an exact-build, application-main paused
probe that initializes this caller-owned string, invokes slot 25 once on a
freshly resolved `activity_feast` HostView, copies the boolean and optional
text before the native destructor, and records empty-text false paths as such.
The source adapter can now carry a typed missing key with known text. If the
probe finds an empty false-path text, the next narrow change must first trace
that native path and give the text its own typed missing reason; no empty text
is advertised as a known display. Complete native
locations, configuration, authoritative cost, shown/can-start, and the private
application-main invocation are still required by the existing P0 snapshot
contract. No CK3 instance was launched for this research.
