# Feast planner semantic seam: bounded native trace (CK3 1.19.0.6)

This is read-only research for the private `activity_feast` planner after the
C81 exact slot-25 callback. It does not establish a legal feast on the current
Robert save, a full semantic sample, a new query, or an activity action.

## Frozen evidence

- The inspected `ck3.exe` SHA-256 is
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
  (1.19.0.6; image base `0x140000000`).
- `CActivityListDetailHostView` primary vtable RVA `0x4166528` has slot 25 at
  `0x15051F0`, slot 26 at `0x1505230`, slot 27 at `0x1505330`, and slot 29 at
  `0x1505340`. These are image-relative function addresses, not live objects.
- Slot 27 merely returns `HostView+0x268` (`CActivityType*`) plus `0x2030`;
  slot 29 returns that type pointer plus `0x1F8`. The latter offset is the
  third trigger input of the slot-25 final evaluator. Neither getter evaluates
  a legal location, selected configuration, configured cost, or a final
  `can_start` result.
- Slot 26 reads the HostView's handler at `+0xD0`, calls `0xA79700` with value
  `0x65`, and eventually tail-calls a HostView virtual method at `+0x20`.
  Its effect and payload semantics are unresolved. It cannot be used as a
  read-only planner collector on this evidence.
- The final evaluator `0x28CFC50` calls trigger evaluator `0x33C9140` on
  `CActivityType+0x38`, then `+0x118` or `+0x2D8`, followed by `0x33C8FE0`
  on `+0x1F8`. It returns the final boolean and optional failure text through
  C81. The static trace does not assign the script-level `is_shown`,
  `can_start`, location or cost meaning to each native offset.
- The original character/type-only callers of `0x28CFB70` are `0x96F310`
  (`.pdata 0x96F310..0x96F3CF`, boolean wrapper) and `0x96F3D0`
  (`.pdata 0x96F3D0..0x96F4B7`, caller-owned 32-byte failure-text wrapper).
  Both build a tagged character target through `0x96A130`; neither supplies
  a selected location, options, intent, guests or an activity command payload.
  The former calls `0x28CFB70` at `0x96F33F` without failure text; the latter
  calls it at `0x96F42C` with the text output. These are prerequisites, not
  a complete start-eligibility result.
- `0x28CFB70` (`.pdata 0x28CFB70..0x28CFC47`) first calls another native
  check at `0x28CFBE7 -> 0x28CFA40`, then other flag checks and the known
  `0x28CFC50` evaluator at `0x28CFC1D`. The exact script-level meaning of
  `0x28CFA40` and of each native branch remains unresolved.
- The original `CStartActivityCommand` validator is primary slot 6
  `0x26C8070 -> 0x219A8B0`. It builds a tagged character target from the
  command's full character ID at `+0x08`, then calls the **same** `0x28CFB70`
  at `0x219AB02` with optional failure text. A false result branches to
  `0x219B861`, but a true result continues payload validation. In particular,
  `0x219AB2B -> 0x2CE2C80` consumes the activity type, command character ID
  and another resolved identity, and the return is compared against command
  `+0x10` at `0x219AB3A`. The meaning of this call and field is not proven.
  The validator also traverses a command list at `+0x4C8` in 32-byte steps
  before the prerequisite call; its elements remain opaque.

Reproduce the function trace with the repository's
`native_bridge/research/disasm_ck3.py` using RVAs `0x1505230` (size `0x110`),
`0x1505330` (size `0x20`), `0x1505340` (size `0x20`), `0x28CFC50`
(size `0x190`), `0x96F310` (size `0xC0`), `0x96F3D0` (size `0xE8`),
`0x28CFB70` (size `0xD8`) and the validator span
`0x219AAF0..0x219AB45` against the exact executable. The vtable slots are
eight-byte entries at `0x4166528 + 8 * slot`. The C106 trace only read the
frozen executable; it did not launch or attach to CK3.

## Decision boundary and next native address

The frozen `feast.txt` has player-facing visibility, adult/cooldown planning
gates, a single-location planner and configured resource cost. The current
Robert actor's cooldown, final native location/configuration and affordability
have not been observed. A static script gate or a positive slot-25 boolean
cannot fill the complete `read_semantics` callback required by the private
source adapter.

```mermaid
flowchart LR
    A[HostView slot 25] --> B[0x28CFC50 trigger boolean and text]
    C[UI 0x96F310 / 0x96F3D0] --> P[0x28CFB70 character/type prerequisite]
    V[0x219A8B0 command validator] --> P
    P --> B
    V --> Q[additional payload validation]
    Q -. unknown: 0x219AB2B to 0x2CE2C80 and +0x10 .-> F[legal locations, configuration, cost and can_start]
    D[slot 27: type + 0x2030] -. meaning unresolved .-> F
    E[slot 26: 0xA79700 dispatch] -. payload and effect unresolved .-> F
```

The next bounded reverse step is `0x219A8B0` after its prerequisite call:
resolve `0x219AB2B -> 0x2CE2C80`, the comparison with command `+0x10`,
and the sources and meanings of the remaining `0x508` payload fields. The
earlier `0x1505230 -> 0xA79700` and `CActivityType+0x2030` consumer remain
possible planner collection leads, but their semantics are unproved. Only a
verified native operation that yields copied legal locations, selected keys,
authoritative configured cost and final shown/can-start may be wired to
`read_semantics`. Calling `0x28CFB70` alone cannot supply those fields or
establish that a command would pass the remaining validator branches.
Then a paired paused Robert frame must test the current feast legality before
any consumer is enabled. No CK3 process was started or attached in this work.

## H3911 follow-up: payload and UI dispatch boundary

The frozen executable was rehashed as
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
This bounded trace narrows the missing semantic operation; it does not
identify a legal feast or provide a planning collector.

- At `0x219AB2B`, the validator passes the command's activity type, character
  ID, and resolved character object to `0x2CE2C80`. One branch of that callee
  uses `CActivityType+0xE98`; the other reads `CActivityType+0xEA0`. The
  result is compared with command `+0x10` at `0x219AB3A`; the global
  predicate at `0x28BCEB0` selects the branch. These addresses prove a
  further type/payload identity check after the prerequisite. They do not
  establish a province, selected option, configured cost, or `can_start`.
- If the comparison passes, `0x219ABCE` calls `0x2517900` with command
  `+0x10`, the command character ID, and the previously resolved object.
  That function begins with a virtual predicate on the supplied object and
  checks further fields. It is not a stand-alone location or affordability
  evaluator on this evidence.
- The AI path's `0x18E1160`, previously described as building command data,
  actually copies an already populated object into a destination: it copies
  the first `0x30` bytes, clones several owned containers, and handles the
  list at `+0x4C8`. It does not show how stable activity, location, options,
  invites, or costs were selected. The original producer of that source
  object remains the construction lead.
- In the caller, `0x18E0BB4` invokes `0x18DF5B0` with an output at stack
  `+0x188`; the path then calls `0x28CD3C0` at `0x18E0C3F` and `0x28CD8E0`
  at `0x18E0C61` while preparing an object at stack `+0x1020`. Immediately
  before the copy, `0x18E10BB` supplies a populated source pointer in `RDX`
  to `0x18E1160`. The writer and layout relationship among those objects is
  not yet decoded; this is a bounded provenance trail, not a field map.
- `0x18DF5B0` starts from AI manager/type inputs, builds 16-byte candidate
  rows, and reaches selection arithmetic before returning. `0x28CD3C0`
  writes into its caller-supplied object and expands a local pointer array;
  `0x28CD8E0` also writes through caller-supplied output and traverses type
  data at `+0xA88`/`+0x3E30`. Their caller-controlled output layouts and
  side effects are not proven safe for a player-facing paused read. Calling
  them to manufacture a supposedly authoritative default configuration
  would copy the AI route rather than observe the player's planner.
- HostView slot 26 at `0x1505230` calls `0xA79700` with event ID `0x65`.
  `0xA79700` routes through an event handler and can update a handler-owned
  list via `0xA95A40`; calling slot 26 as a supposedly read-only semantic
  collector would be unjustified.
- The primary HostView vtable starts at `0x4166528` and ends with slot 29
  (`0x1505340`); the following qword at slot position 30 is the secondary
  vtable's COL, immediately before the secondary vtable at `0x4166620`.
  Thus there is no unexamined primary slot after 29 that directly supplies
  the complete location/configuration/cost sample.

Reproduce the bounded spans with `native_bridge/research/disasm_ck3.py` at
`0x219A8B0` (size `0x280`), `0x219AB20` (size `0x100`), `0x2CE2C80`
(size `0x70`), `0x2517900` (size `0x200`), `0x28BCEB0` (size `0x60`),
`0x18E1160` (size `0x220`), `0x18E0B90` (size `0x140`), `0x18E1080`
(size `0x90`), `0x1505230` (size `0x100`), and `0xA79700`
(size `0x150`). All are RVAs against the exact executable above.

This AI provenance does not expose a safe player-side collector. The next
construction task is to locate a non-mutating planner getter for legal
locations, selected configuration, authoritative configured cost and final
`can_start`, then map its outputs to the validator's `+0x10` and `+0x4C8`
consumers. Only then can `read_semantics` safely copy a complete feast sample
in the private application-main glue. The H3911 driver contains no activity
snapshot, so it cannot establish current feast eligibility or cost. No CK3
process was started for this follow-up.

## Planner state getter lead (same exact build)

The original `game/gui/window_activity_planner.gui` is SHA-256
`ADB96B79A36E43F444410B85A80D0E393A2CC1B3D0D6380EA76EB2F515D382C7`.
Its start button at lines 1758-1767 binds
`ActivityPlanner.CanProgressPlanningStage` and
`GetCanProgressPlanningStageTooltip`; lines 1744-1746 and 1978-1990 bind
`ActivityPlanner.AccessCostBreakdown`. The button's `onclick` is
`ProgressPlanningStage`, an operation that must not be used for a read-only
capture. The GUI also reads `GetSelectedSpecialOption` and
`GetSelectedHostIntent`. A progress boolean may describe an intermediate
planning stage, so it cannot be renamed to final `can_start` without the
stage value and command validation.

The EXE embeds `source\\interface\\activity_planner_window.cpp` beside these
binding names. RTTI for `CActivityPlanner` is at type descriptor RVA
`0x52395F8`. Its object-offset-0 COL is `0x46A49B8`, primary vtable
`0x41205F0`; an object-offset-`0x10` COL is `0x46A4990`, secondary vtable
`0x41206C8`. This distinguishes the planning object from the already bound
`CActivityListDetailHostView` (`0x4166528`). The same EXE supplies a bounded
owner path: `CIngameInterfaceHandler` initializer `0xA734B0` calls `0xA90430`
at `0xA7519E`. `0xA90430` allocates `0x73A0` bytes, calls the planner
constructor `0x10AC080` at `0xA90459`, then publishes the returned pointer at
`handler+0x3C0` (`0xA90468`). The constructor writes `planner+0xD0 = handler`
at `0x10AC0F3`, allowing a fresh owner round-trip. The existing private
activity binder already resolves this handler from
`*(module+0x570F7B8) -> idler -> handler`; it currently reads the separate
HostView at `handler+0x3D8`. Thus a paused query can read `handler+0x3C0`
afresh and check the exact primary/secondary vtables and owner round-trip.
The published pointer is replaced and the old object destroyed in `0xA90430`,
so it cannot be cached between frames. This static constructor path does not
prove the planner is present, selected for `activity_feast`, or populated on
H3911's opening paused frame.

The exact GUI `AccessCostBreakdown` binding registers at `0x1590B9` /
`0x1590FE`; wrappers `0x10B57D0` / `0x10B57E0` reach the pure accessor
`0x10AB170`, which only returns `planner+0x1AD8`. The result is the address
of a planner-owned embedded cost object, not a copied cost value. The next
same-shape object begins at `planner+0x23E8` (`0x910` stride). Constructor
`0x10AC352` initializes the first object; it does not price a selected feast.
Any future query must copy values while its freshly checked planner/frame is
held and must establish that the object was refreshed.

`CActivityPlanner` vtable slot 12 (`0x10AE180`) calls `0x10B2B30`, which
clears `+0x1AD8` via `0x10AAFD0` and recomputes through `0x10B6A60`,
`0x10CC1E0`, and `0x3DDB850`. This is a write path, not an observer. A bounded
trace of `0x10B2B30..0x10B2EFC` found no planner generation, valid or timestamp
write after the recomputation. The `0xA90430` creation path invokes vtable
slot 7 and conditionally slot 4, not slot 12; thus it does not prove that
the cost object is fresh before the planner window opens. Empty cost data
cannot be interpreted as zero cost.

The `CanProgressPlanningStage` boolean wrapper `0x10B4D20` calls evaluator
`0x10B0DA0` (optional native string output). This branches on
`planner+0x1AB0` stages 0..5. Only stage 5 constructs a temporary
`CStartActivityCommand` and calls its slot 6 validator; other stages decide
whether the current planning stage may advance. The constructor sets stage
to `2`, so `CanProgressPlanningStage=true` at that stage is not final
`can_start`. Neither the current snapshot schema nor the constructor path
proves a selected feast, complete configuration, authoritative costs or
player-stage final eligibility on H3911's paused frame.

## Proven handler-update caller of planner slot 12

The handler's primary vtable slot 7 points to update function `0xA75C40`.
Within it, `0xA76ABC` sets `rdi = handler+0x98`, and
`0xA76AD8..0xA76B9D` iterates `0xA4` pointer slots. The planner publication
at `handler+0x3C0` is table index `(0x3C0-0x98)/8 = 0x65`, so this path
includes it. For each non-null view, `0xA76B55` calls primary vtable slot 7.
Only on true does `0xA76B65` invoke slot 11; the `CActivityPlanner` slot 11
target `0xAA33F0` tail-jumps through slot 12 (`[vtable+0x60]`) to
`0x10AE180`, which calls the cost recomputation `0x10B2B30` at `0x10AE1AA`.
The planner slot 7 implementation is shared `0x1F30970`, which returns false
when `planner+0x78` has no attached widget and otherwise tests the widget's
visibility state. This is an actual runtime caller, conditional on the
planner widget visibility gate. It does not establish that the H3911 paused
frame has an attached/visible planner widget, a selected feast, or a complete
configuration. The creation path invokes slot 7 and conditionally slot 4,
but not slot 11/12.

```mermaid
flowchart TD
    H[CIngameInterfaceHandler slot 7 update] --> L[scan handler+0x98, 0xA4 views]
    L --> P[planner at table index 0x65]
    P --> V{planner slot 7 widget visibility}
    V -- false --> U[cost freshness unknown]
    V -- true --> S[slot 11 thunk to slot 12]
    S --> R[0x10B2B30 clears and recomputes cost]
    R -. no verified generation or paused query order .-> U
```

No read-only freshness/authoritative marker has been identified in the
recomputed `+0x1AD8` container or surrounding planner fields. A caller can
read a fresh planner pointer, attached-widget presence, stage and selected
type/configuration without changing state, but those fields alone do not
prove that slot 12 completed before the paused query or that its output is a
final configured feast cost. They are a narrow private diagnostic readout,
not a complete semantic collector or `can_start` answer. The next executable
diagnostic is an official paused-frame capture of those fields with the
planner window closed, followed by a separately bounded visible-window
capture or a proven independent native cost evaluator. Any visual step must
follow the current CK3 owner and minimize the window afterward. If the
selected configuration or cost validity cannot be established,
`configured_cost` and `can_start` remain typed unknown. No activity action or
private semantic callback is eligible on this evidence alone; absent planner
context must be reported as absent, not synthesized from `feast.txt` or the
AI activity path.
