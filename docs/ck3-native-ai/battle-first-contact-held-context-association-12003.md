# First-contact held Character context and independent knight value (.3)

This is source research for CK3 1.20.0.3 / Steam build 25652598. The frozen EXE
is `artifacts/migrations/2026-10-02/installed-build/binaries/ck3.exe`, with the
previously recorded SHA-256
`94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`.
No game operation, native callback, whole-file hash, or whole-file scan was used.
Research was sealed on 2026-10-06 before the dedicated pure consumer was added.

The immediate useful result is a current-input special-knight stat calculation.
Its inputs already exist in `combat_v3.armies[].knights`. A historical person
baseline is unnecessary for this bounded calculation. Complete first-contact
admission, constructor final inputs, full person preparation, and full Entry
forecast remain separate capabilities.

## Actual context identity

`28BFC70` returns a **Character**, not a modifier model. A landed Character selects
the valid related Character through `+1C0 -> +1C0 -> +28`, otherwise self; the
unlanded branch resolves the employer ID at the `+1B8` carrier. `2C06D30` reads
linked-knight prowess at `+EC`, applies the lower bound one, and uses that selected
Character for `2C06B00`. Linked and selected Character full IDs can differ.

`2C06B00` obtains the selected Character's modifier receiver through `28C3AE0`:
Character `+1B0 -> carrier+258 -> model`. If `model+8` is the selected Character,
the returned receiver is the **address** `model+10`; otherwise the receiver is
the actual fallback at `5D67B90`. A cold fallback is not invented as zero.
Mode zero reads the sparse aggregate at receiver `+68`, keys `C1..C9` in order.
The operands are `Q`, selected carrier `+350`, selected carrier `+358`, then
signed selected Character skill fields `EC,D8,E4,E8,DC,E0` multiplied by Q.
An absent selected `+1C0` carrier contributes real zero for the two carrier
operands. `2C4D680` uses signed maximum decomposition on its large-product branch.

`CurrentRawNumericInputs` in the production native battle reader uses the same
physical matching-owner branch and emits `context_source="model_inline"` with
the actual aggregate and weighted rows. Thus, inside an explicitly supplied
current sample, matching selected full ID and a `model_inline` person row
identify this current held model. The existing census records model presence,
owner presence, owner full ID, and owner match. No new descriptor observer is
needed to identify this branch. Separate requests do not become one native
sample merely because their full IDs match.

The paired preparation path copies the old owner into a **different new model**
and calls `291C0D0` with that new model. Equal owner IDs do not prove that this
new model is the held `carrier+258` model. No current final context is used as a
historical prior, and held-current `291F260` weights retain that scope.

```mermaid
flowchart TD
  L[Linked knight Character: prowess EC] --> S[28BFC70 selected Character]
  S --> H[28C3AE0: Character1B0 carrier258]
  H --> M{model8 equals selected Character?}
  M -->|yes| A[ADDRESS held model10]
  M -->|no| F[Actual fallback5D67B90]
  A --> K[2C06B00 mode0: C1..C9 and actual operands]
  F --> K
  L --> P[max signed prowess1]
  K --> V[26344C0 current-input six stats]
  P --> V
  N[Distinct new291C0D0 model] -. unknown historical association .-> A
  E[Earlier constructor effects and transitive callees] -. unknown final held association .-> K
  V --> I[Bounded initial special-knight value]
  I -. admission and final stage unknown .-> Z[Full Entry forecast]
```

## Last named constructor source stage

The cached full `2586ED0` body is `[2586ED0,25870A1)`, 465 bytes, SHA-256
`f6775f254e57860f5dc6d442f2dc4ea0d04e3d7c6ab107d628024b28b89e0c28`.
It is called at `247AB22`; `247AB1F` is RCX setup. After it returns, the caller
loads Combat Province `+6B8` and reaches final side refresh at `247AB32/41`
without another preparation, selector, or rebuild instruction in that interval.
This does not establish held Character stability over the whole constructor.

The following three immediate source helpers were closed with bounded seeks
and their chained `.pdata`/unwind pieces. Logical function extents are complete;
arbitrary transitive callbacks were not audited.

| Native order | Helper and logical extent | Actual numeric/storage role |
| --- | --- | --- |
| Per side, call `2586EFB` | `25870B0..25873BC`, 780 B | Resolve the side's Army IDs and Regiment IDs, admit ordinary regiments or the special first-row qualifier, sum signed Regiment `+38` counts, classify Army `+180` supply against loaded thresholds, and return loaded rule `F20/F30/F40` according to low/next counts versus half the total. Normal body writes stack only; the caller appends the returned nonzero `+40` source. |
| Call `2586F2A` | `25873C0..2587563`, 419 B | Resolve first defender Army/Unit/owner and evaluate `2C09D30(owner, Combat Province)`. On true, write **Combat+6FE=1**, then evaluate Province ordinals `1EB` and conditional `1D6`; a positive wrapped sum appends loaded rule `F10` on side one. Province getters have a Province receiver, not the selected Character model. |
| Call `2586FC2` | `2587570..258792A`, 954 B | For each side's first Army owner, mode-zero `2BCA620` selects a provider/fallback PC. Government bit29 then living-first selected Land and negative Land `+318` demand mode-three `2BCA620`. Admitted ObDG `+40` PCs append at Q. All selection branches and source occurrences remain native-ordered. |

`25873C0` has no direct selected-Character/model write. Its Character predicate,
lazy rules/provider initialization, and income evaluation remain transitive
dependencies; their absence from direct body stores is not a no-mutation proof.
Negative income values retain the existing precise evaluated accounting gap.
The already closed religious branch and `2586C90` Combat advantage append were
reused, not recaptured. The append storage is distinct from Character context.

```mermaid
flowchart LR
  C[247AB22 calls2586ED0] --> S[Per-side25870B0 source selection]
  S --> A[2586C90 Combat advantage append]
  A --> H[25873C0 holding source]
  H --> W[Combat6FE and Province numeric sources]
  W --> D[2587570 debt and government-Land sources]
  D --> R[Existing religious source branch]
  R --> F[Return then247AB32/41 final refresh]
  H -. transitive Character predicate unknown .-> U[Final held Character association unclosed]
  D -. evaluated income / lazy provider effects unknown .-> U
  E[Earlier constructor callees] -. unknown .-> U
```

## Existing query inputs and minimum consumer

The native query already publishes the required positive numeric source. The
production `combat_contract` normalizer accepts a selected Character full ID,
exact modifier indices `193..201`, nine signed Q64 modifiers and operands,
plus linked member identity/prowess and loaded signed damage/toughness multipliers.
The selected-context diagnostic can be unavailable while the independently
observed scalar and Province-evaluated stats remain available.

The existing `knight_inputs_from_current_observation_12003` and
`compute_knight_stat_cache_at_stage_12003` implement the exact sparse arithmetic.
The older current-entry association calculates from the observed scalar instead
and does not provide this raw-input batch value. The minimum addition is a
dedicated pure consumer of a **normalized combat query**, retaining Army/member
order, per-member numeric readiness, computed six-cache values, actual observed
scalar/stats, and diagnostic comparisons. It reuses those two functions and
adds no native field or new arithmetic kernel.

Required bridge parameters are already available: Army full ID, member Regiment
full ID, linked Character full ID and signed prowess, selected Character full ID,
`modifier_raw[9]`, `operand_raw[9]`, `loaded_damage_multiplier`, and
`loaded_toughness_multiplier`. Target Province is provenance for this special
branch, not an arithmetic operand. Unavailable raw context must retain the
first exact missing operand/selected identity while preserving observed values.

The result is `frozen_current_character_values` projected to a caller-conditioned
initial special-knight cache. It does not write an Entry, predict Army admission,
invent future occupants, or declare these inputs held across `2586ED0`.

## Frozen fixture and evidence

One new compound consumer fixture should use the real production normalizer
and existing stat kernel with a nonempty selected C1..C9 array, distinct linked
and selected Character IDs, signed values, nonzero and zero operands, loaded
multipliers, and observed stats different from the computed estimate. A second
member with unavailable raw context must preserve its current scalar/stats and
not erase the first member's ready value. No old producer or kernel test is rerun.

A later native identity fixture can hold model A at selected carrier `+258` and
place a different preparation model B with the same owner but different keys.
The actual getter must read A; the fixture must not infer B from owner equality.
An actual initialized nonempty fallback is a separate valid branch. This is a
fixture proposal, not a new native implementation or a completed constructor test.

External packet:
`Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/person-stage-chain/entry-held-association/`.
`SOURCE-PINS.json` pins every new cached binary and the assembled logical helpers;
`READ-COST.json` records 2,681 physical EXE bytes read: 2,153 code, 360 `.pdata`,
164 saved unwind bytes, and four duplicate unwind bytes before harness failure.
Of the code, 189 bytes `[25874A6,2587563)` repeat the previously closed holding
tail and receive **zero new source credit**. New unique code credit is 1,964 B;
code plus metadata credit is 2,488 B. The failed exclusive metadata write is
preserved under `capture-025873C0-complete/FAILED-ATTEMPT.json`; the corrected
continuation reuses that attempt's saved pieces. No capability RED was inferred.

Related contracts: [final stat refresh](battle-first-contact-final-stat-refresh-12003.md),
[constructor religion sources](combat-constructor-religion-sources-12003.md),
[retained current rules](battle-retained-current-rule-contributions-12003.md),
and [person stage chain](battle-person-stage-chain-12003.md).

## Delivered bounded consumer

`simulation/battle_current_special_knight_value_12003.py` exposes
`estimate_current_special_knight_initial_stats_12003(normalized_combat_inputs,
source_provenance=...) -> dict`. It consumes the existing `armies[].knights`
leaf directly. No production normalizer, arithmetic kernel, native collector,
service, or runtime source was changed by this child.

The result preserves member/Army identities and order, the actual selected
Character full ID and `frozen_current_character_values` stage, per-member missing
numeric fields, raw-backed effectiveness and all six initial cache fields,
the independent current scalar/stats, and diagnostic equality comparisons.
`all_observed_member_inputs_ready` is strictly this bounded numeric readiness.
Ready-member role sums explicitly count partial members and do not forecast
admission or native aggregate behavior. Known empty rosters have zero observed
members; they are not presented as a positive nonempty-value demonstration.

One new compound case passed once at **2026-10-06 07:10:17 Asia/Shanghai**, 1/1,
0.035 s, through the actual full production combat normalizer at source
`586db26b019ec5010fa9f8841999e2ec6520bec4` and the existing exact knight kernel.
The nonempty selected Character is 29829, distinct from linked IDs 56513/56514.
The computed effectiveness is 173100; the first knight's damage/toughness are
8655000/1731000 and the second's are 60585000/12117000. Both can qualify together.
Missing raw context and a separately missing loaded coefficient retain precise
gaps and independent ready values. Signed terms and zero-operand lookup skips
are exercised; the original source observation is preserved.

Receipt: `entry-held-association/CURRENT-VALUE-ATTEMPT-01.json`. No old case,
sibling producer case, native target, or game operation ran. This consumer is
**static-ready**. It can be attached to the existing combat-query response in
the next ordinary source package; this child does not hot-edit the active runtime.
It leaves full Entry/person readiness false. The first missing value when this
slice is partial is an existing `effectiveness_context.operand_raw[i]`, selected
Character identity, sparse modifier, or loaded multiplier, not a new descriptor.
