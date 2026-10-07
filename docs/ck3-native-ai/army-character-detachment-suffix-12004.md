# Character detachment suffix — CK3 1.20.0.4

Frozen source: CK3 **1.20.0.4**, Steam **25734779**, EXE SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
The concrete existing production partial is
`actually_selected28CBE70_inner_effects` in the current detachment DATA pure
consumer's nonnull Character1B8 branch. Outer invalid CharacterID and null1B8
cases already have independent no-call results.

The old complete semantic wrapper `28CBE70..28CC079` was held in a528B cache;
seven trailing padding bytes were excluded. Root's cached runtime ordinal
140151 gave candidate `28CBE50`. The candidate was not bound from its address:
Root separately approved one521B read, and the complete actual
**`28CBE50..28CC059`** matched every old instruction, ordinary control branch,
member/literal operand and ordered relative/RIP edge. Owner current31 confirmed
no earlier actual4 paired receipt. External proof is
`army-future-dates-12004/character-suffix-map01/FAMILY-MAP.json` and its DETAIL.
Fresh cost: **521 actual4 bytes/one read**, no old EXE, new metadata, hashes,
padding or selected helper expansion. This lane's intentional cumulative source
cost is now **1265 bytes/nine reads**; previous milestone costs stay historical.

The wrapper captures Character1B8 once as its initial extension and saves the
passed Province pointer. Null initial extension returns immediately. Otherwise
it reads extensionF8 fullID, resolves ArRg through registry`5D1F340` and
fallback`5D1F338`, then Army through registry`5D1DE48`/fallback`5D1DE50` and
ArRg140, then Unit through registry`5D1E380`/fallback`5D1E378` and Army124.
Selectors use low24 slot indexes, unsigned count2C and complete object10 ID
equality; each later requested member is only read when its registry is
nonnull. A missing slot chooses the source fallback. The saved Unit pointer
is used later, rather than re-resolving that Unit after the Province mutator.

After these selectors it stores initial extensionF8=`0xFFFFFFFF`. It then
reloads Character1B8; a nonnull reloaded extension receives full
QWORD100=`0xFFFFFFFF029C77F8`. This is a source-defined extension reset,
not a Character return value or an observed post-call state.

The wrapper calls actual origin getter **`28B1820(Character)`**. Its returned
object's DWORD85C is compared with `0x50726F76` (`Prov`). A non-Prov result
exits after the reset; Prov selects actual **`28B2710(Character, origin,0,0)`**.
Both helper effects remain unclosed; neither is invoked as a readonly getter
from this source proof. Cached metadata gives the getter's selected first
runtime interval399B and the mutator's first45B fragment; the mutator fragment
is not a complete method. Separate finite plans must precede new body reads.

After the mutator, the saved Unit174 owner is freshly resolved through Character
registry`5C67568`/fallback`5C67570`, comparing complete ID at18. Owner1C0 selects
its+318 context or source fallback`5459D38`; context DWORD+C zero exits. Nonzero
loads current GameState through`5C68C50` and copies its full QWORD+8 into the
already held readonly date constructor **`2C54320`** with saved Unit, original
passed Province and getter-returned origin. Only **signed low-DWORD** result
strictly greater than the captured current low-DWORD writes the constructor's
whole QWORD into freshly reloaded Character1B8+100. Equal/earlier leaves the
source sentinel. Entry date/owner/context are not the source's post-mutator
rereads and cannot stand in for those effects.

```mermaid
flowchart TD
  A[Actual28CBE50 Character plus passed Province] --> E{Captured Character1B8 nonnull}
  E -->|null| R[Return without suffix writes]
  E -->|nonnull| S[ExtensionF8 fullID; source ArRg Army Unit selectors]
  S --> C[Initial extensionF8 FFFFFFFF]
  C --> N{Reloaded Character1B8 nonnull}
  N -->|yes| Z[QWORD100 FFFFFFFF029C77F8]
  N -->|no| G[Reached origin getter28B1820]
  Z --> G
  G -. getter source/effects unknown .-> P{Returned object85C Prov}
  P -->|no| R
  P -->|yes| M[Reached28B2710 Character origin zero zero]
  M -. tracked mutator effects unknown .-> O[Saved Unit174 owner; fresh context count]
  O --> T{Context count nonzero}
  T -->|no| R
  T -->|yes| D[Fresh whole GameState date; known2C54320 readonly constructor]
  D --> B{Result signed lowDWORD greater than current}
  B -->|no| R
  B -->|yes| W[Reload Character1B8; write full outputQWORD100]
  W --> R
```

Root centrally executed the separately approved actual origin getter interval
**`28B1820..28B19AF`**,399B/one read, with101 completely decoded instructions.
Receipt is `character-origin-map01/SELECTED-GETTER-CAPTURE.json`. Its own body
has no non-stack writes; this does **not** close readonly behavior of its three
selected calls. Total intentional fresh source cost is now1664B/ten reads,
including this Root-owned capture once.

The getter tests Character1C0. Nonnull selects capital helper`28B1CB0`; a Prov
result returns immediately. Otherwise it reads first title ID from fresh
Character1C0's1E0 vector when1EC is nonzero, or Character1D0's68 vector when74
is nonzero, or fullID`FFFFFFFF`. Through held Title registry`5D1DAF8` and
fallback`5D1DAE0` it selects that title, then titleE4's second title. Definition
pointer48's DWORD64 equal2 selects the first title ID in second title110 when
11C is nonzero, otherwise sentinel; this third title role selects
`230F8E0(title)` at`28B194B`. Other definition values use second title338
directly. A Prov output returns; otherwise the getter continues.

The fallback ladder then checks fresh Character1B8: nonnull selects
`28B1750(Character)` at`28B1972`, returning immediately if its output is Prov.
Next Character1B0's268 pointer is tested for Prov; a miss/null1B0 returns the
source fallback Province pointer from`5D1E390`. Source counts here test
**nonzero**, not positive, and complete ID/generation equality is retained.

The existing actual4 detachment binding already identifies capital helper
`28B1CB0`; the new origin getter is not installed or invoked. Its type2 Title
callee has no containing cached runtime interval, and its selected nonnull
extension helper's first cached interval is30B; neither body's effects are
closed by this399B capture. Only necessary selected helper sources may receive
a further finite plan. Independent source-defined direct-field/early-return
arms should be implemented without demanding every unused fallback branch.
Crucially, the parent clears extensionF8/QWORD100 before calling this getter:
an origin queried from the standing pre-reset state is not automatically the
source's post-reset origin. Any after-reset projection must apply the known
reset to the helper's actual source inputs rather than silently substituting
the current native getter output.

```mermaid
flowchart TD
  A[Actual28B1820 Character] --> C{Character1C0 nonnull}
  C -->|yes| K[Known capital-role28B1CB0]
  K --> P{Capital output Prov}
  P -->|yes| R[Return selected Province]
  P -->|no| T[First title ID; titleE4; actual Title selectors]
  T --> D{Definition48 type64 equals2}
  D -->|no| V[Second title338 pointer]
  D -->|yes| Q[Third title; selected230F8E0]
  Q -. selected source unknown .-> H{Output Prov}
  V --> H
  H -->|yes| R
  H -->|no| E{Fresh Character1B8 nonnull}
  C -->|no| E
  E -->|yes| G[Selected28B1750 Character extension origin]
  G -. selected source unknown .-> X{Output Prov}
  X -->|yes| R
  X -->|no| B[Character1B0 plus268 Prov test]
  E -->|no| B
  B -->|Prov| R
  B -->|miss| F[Source fallback5D1E390]
  F --> R
```

The next concrete same-Army MCP input leaf is
`current_character_detachment_inputs_v1`. It retains every existing query's
incoming native index and passed Province, rather than merging calls that happen
to select the same Character. Its standing observations are current Character1B8,
extensionF8 and whole signed64 extension100, plus the wrapper's current
extension-to-ArRg-to-Army-to-saved-Unit selection roles. Army140 is demanded only
when the Army registry is nonnull; Unit124 is demanded only when the Unit registry
is nonnull. An unused missing ID cannot invalidate a source fallback selection.

Invalid Character fullID`FFFFFFFF` and a known null current1B8 have independent
no-suffix results. A known nonnull extension selects independently known reset
descriptors: F8=`FFFFFFFF` and whole100=`FFFFFFFF029C77F8` (signed64
`-4251158536`). These constant values do not require the old fields to be readable.
The source's first F8 store targets the captured extension; its second store
targets a freshly reloaded Character1B8 when nonnull. A standing query does not
observe that reload after a write. The descriptors therefore preserve those two
target roles and cannot credit an observed reset, reached getter, post-reset
origin or computed suffix date. Current selector completeness is separate from
reset descriptor completeness and from whole suffix readiness.

```mermaid
flowchart TD
  A[Same-query incoming Character and passed Province] --> I{Character ID invalid}
  I -->|yes| N[Independent no suffix result]
  I -->|no| E{Current Character1B8 pointer known}
  E -->|null| N
  E -->|nonnull| F[Observed extensionF8 and whole100; optional before values]
  E -->|unread| U[Partial current extension input]
  F --> R[Independent source constant reset descriptors]
  F --> C[Current source ArRg Army savedUnit selectors]
  C --> S[Independent current source-chain readiness]
  R -. actual reset and fresh reload not observed .-> G[Post-reset origin getter]
  G -. selected helper sources unknown .-> D[Post-mutator context and computed date]
```

State is **research / complete direct wrapper and own origin-getter source**;
the current input leaf is **AUTHORED_NOTRUN**, an independent five-file candidate.
Native DTO, inline reader and serializer live in
`army_current_character_detachment_inputs_v1.hpp`,
`ck3_12004_current_character_detachment_inputs.hpp` and
`army_current_character_detachment_inputs_serializer_v1.hpp`. The exact4 binder
`BindCurrentCharacterDetachmentInputs12004` supplies the source role only;
`ReadCurrentCharacterDetachmentInputs12004` performs software reads from the
same-query seed and executes no native helper. Python
`normalize_current_character_detachment_inputs_v1` preserves its strict optional
wire; `project_current_character_detachment_inputs_v1` supplies the independent
`current_character_detachment_suffix_v1` result. No shared hook was applied here.
External `CHARACTER-INPUTS-ROOT-DELIVERY.json` and
`character-current-source/SHARED-HOOK-RECIPE.md` provide concrete Root adoption
fragments; Root owns the unified producer, complete registered consumer and
paused exact4 snapshot qualification. This increment used no new EXE bytes.
No native call, import, test, build, SDK query or paused artifact is credited.
Selected origin-helper source closure remains necessary for origin observation.
Mutator/post-call gaps stay selected dependencies, with no forecast prerequisite
added to current legal OODA or migration acceptance.
