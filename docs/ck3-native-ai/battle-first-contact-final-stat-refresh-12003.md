# First-contact final stat refresh, exact 1.20.0.3

This source-bound pure increment connects explicitly prepared Character values
to the final six Entry cache writes in the create-new contact constructor.
It does not treat the stored current final Character context as a prior
preparation baseline. Initial Army Province and final Combat Province remain
separate inputs. Complete Entry construction and live readiness remain partial.

Frozen build: CK3 1.20.0.3, Steam25652598, EXE SHA256
94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6.
This package reuses the source captures below and reads zero additional EXE
bytes. All execution is pure Python over supplied files.

## Native order and distinct storage

264DE30 initializes each newly admitted Army's rows using 24E0EB0, that
Army's current Province. The outer 247A330 constructor creates the Combat,
selects and stores both commanders, refreshes sums and width, then performs:

| Ordered call site | Operation | Storage and dependency |
| --- | --- | --- |
| 247A9EC, 247AAAD | Adjacency source append, with defender 1A4 exclusion | 2586C90 modifies Combat advantage and append ledger; it does not replace Character context |
| 247AADD, 247AB09 | Terrain source append | Same Combat advantage ledger |
| 247AB0E, 247AB17 | 2650A80, side0 then side1 | Rebuild CombatSide+110 accolade aggregate from ordered MAA linked Characters; body has no Character model write |
| 247AB1F | 2586ED0 | Additional advantage sources, separate from six Entry stats |
| 247AB32, 247AB41 | 2651070, side0 then side1 | Combat+6B8 Province; each side levy then MAA in stored order |
| Each 2657AC0 | 26344C0 getter then six stores | Entry+30 i32 max size; +38 siege; +40 damage; +48 toughness; +50 pursuit; +58 screen |

2657AC0 does not write Entry identity, starting, current, soft casualties or
result-row headers. A retained zero-current row still receives its stat refresh.
The final calls cover the whole side, including rows that were already present.
Equal Army-current and Combat Province permits the existing query tuple at
the initial frozen-current stage; it does not make a post-effect tuple an
initial-stage tuple. A different Province requires the corresponding getter
operands and cannot reuse the target tuple under another label.

~~~mermaid
flowchart TD
  A["264DE30: new Army rows, Army current Province"] --> B["Combat created; commanders stored; width refreshed"]
  B --> C["Adjacency and terrain: Combat advantage ledger"]
  C --> D["2650A80 side0 then side1: Side+110 accolade aggregate"]
  D --> E["2586ED0 additional advantage"]
  E --> F["247AB32 side0 at Combat+6B8"]
  F --> G["247AB41 side1 at Combat+6B8"]
  F --> H["2651070: levy then MAA, stored order"]
  G --> H
  H --> I["2657AC0: only six Entry cache stores"]
  I --> K["Special knight: linked Character prowess + selected Character context"]
  I -.-> U["Ordinary/MAA changed-stage getter inputs, partial when absent"]
  P["Explicit person stage context and six-skill projection"] --> K
  V["28BFC70 selected full Character ID"] --> K
  K --> W["2C06B00 C1..C9; 2C06D30 damage/toughness"]
~~~

## Closed special-knight formula

2634880 selects the special branch using actual Regiment identity and linked
Character. 26344C0 resolves Regiment+148 Character, then 2C06D30 uses its
signed prowess+EC, max(1, prowess). The Province argument is unused in this
branch. 28BFC70 may select a different Character for effectiveness; the selected
Character's context and skill fields must never be replaced with the knight's.

2C06B00 starts with Q=100000 and adds nine terms, in C1..C9 order:

| Key | Selected Character operand |
| --- | --- |
| C1 | 100000 |
| C2, C3 | Character+1C0 carrier+350 and +358 signed q64, or real zero when carrier absent |
| C4 | selected prowess signed32 * Q |
| C5 | selected diplomacy signed32 * Q |
| C6 | selected intrigue signed32 * Q |
| C7 | selected learning signed32 * Q |
| C8 | selected martial signed32 * Q |
| C9 | selected stewardship signed32 * Q |

Mode0 2C4D680 returns zero before modifier lookup when the operand is zero.
Otherwise it reads the selected context aggregate at +68. The sparse reader,
including exact empty versus missing semantics, is reused from the existing
numeric module. A nonzero missing operand or property produces a partial result.

The 2C4D680 large-product branch differs from the general numeric component
helper: it decomposes the signed maximum operand, truncates maximum/Q toward
zero, multiplies the remainder by the signed minimum, then wraps the integral
and fractional sum to signed64. The new dedicated helper follows this cached
body; the existing component helper is unchanged.

2C06D30 writes (max_size, siege, damage, toughness, pursuit, screen) =
(0, 0, wrap64(max(1, linked prowess) * effectiveness * loaded damage int32),
wrap64(max(1, linked prowess) * effectiveness * loaded toughness int32), 0, 0).
The intermediate products and the C1..C9 additions wrap signed64. There is no
extra alive check or negative-effectiveness clamp in the inspected branch.

## Reachable pure interface and next inputs

The dedicated simulation module accepts explicit PersonStatStage12003 values,
including full Character ID, logical stage name, context, six skill cache
points, and the 1C0 carrier operands. Its adapter also accepts the existing
normalized current knight effectiveness_context C1..C9 observation as a
frozen-current evaluation, without promoting it to a historical prior stage.

The final refresh accepts computed knight tuples or explicitly evaluated
endstage six-stat tuples. It binds each tuple to side, bucket occurrence, full
Army/Regiment identity, Combat Province, and the exact side call site, then
replaces the six cache fields in native order. Missing ordinary/MAA inputs leave
those rows explicitly unrefreshed, while closed knight rows remain useful.
The result reports per-row readiness and keeps complete Entry, native execution,
historical stage observation and game-day advancement false.

The same module's initial_entry_stats_from_combat_regiment_12003 consumes
the normalized Army and Regiment from the existing combat query. When actual
Army.current_province_id equals the requested target, it selects the existing
effective_stats tuple and does not demand any extra field or read. When they
differ, it selects the optional initialization_context_stats tuple exclusively,
with source_target_province_id equal to the actual Army Province. A missing,
unavailable or different-Province initial tuple remains partial; the target
tuple is never substituted. The returned six cache values are named
frozen-current inputs to a caller-conditioned initial stage, separate from the
post-effect final refresh. Full Army/Regiment IDs and initial Province are
preserved in the result. Admission and result-row initialization remain separate.

The person stage chain can provide an explicitly named conditional context
and six-skill projection to this interface. A partial preparation chain can
support a named intermediate-stage calculation; it cannot be silently labeled
the constructor's final stage. Missing ordinary/MAA endstage operands should
be added through the existing getter/query path by the native owner. Current
holding/commander/geometry sources are owned by the parallel terrain package.

## Reused evidence

- g2-resume-20261004/battle-knight-entry-future-12003/outer-membership/evidence/0247a820-span.txt: final constructor sequence.
- g2-resume-20261004/battle-knight-entry-refresh-12003/injury-order/body-2650A80-21B.txt: complete Side+110 rebuild.
- Same injury-order/slice-02651070-89.txt and slice-02657AC0-88.txt: bucket order and exact cache stores.
- Same injury-order/slice-026344C0-90.txt and slice-02C06D30-8D.txt: special-knight branch and direct products.
- g2-background-round2-20261005/actual-entry-context/capture-02C06B00-body/region-02C06B00.asm and capture-02C4D680-body/region-02C4D680.asm: nine operands and exact scaled multiplication.
- [Selected Character context](battle-knight-effectiveness-context-12003.md), including first-contact Province/admission appendix, and [existing current Entry association](battle-current-knight-entry-refresh-12003.md).

Focused validation and artifact receipt are recorded in the external
g2-background-round4-20261005/first-contact-final-preparation packet.

The single new focused case passed on 2026-10-05, 1/1 GREEN in 0.3682 seconds.
It connects a named person-chain frontier and cache projection, computes a
distinct selected Character's effectiveness, refreshes a zero-current knight
and retained rows in both sides, and rejects a different-Province ordinary
tuple while preserving the original frame and all troop/result accounts.
Its direct current-observation adapter reaches the same arithmetic without
claiming a prior stage. The first attempt was harness RED because the fixture
added an MAA row without updating its counter census; that attempt is retained.
The corrected new fixture passed once. No old test, native build, additional
EXE read or game operation was performed.

Readiness: the named-stage knight calculator and supplied final six-cache
write primitive are static-ready. The constructor's full changed context,
ordinary/MAA source-derived new-stage evaluation, complete person preparation,
complete Entry and live operation remain partial. The current-stage native
observations retain their earlier qualification, without new live credit.

The additional initial-Province adapter has its own new focused case. The
optional same-query observer is implemented by the parallel replenishment
owner; this package does not duplicate its native code, bindings or normalizer.
That adapter case passed 1/1 GREEN once in 0.2343 seconds. It covers equal
reuse, unequal selection, genuine zero/negative values, unavailable and
wrong-Province leaf, and unknown Army Province. The earlier final-refresh
case was not rerun. Native qualification of the new optional observer remains
with the central build and its owning package.
