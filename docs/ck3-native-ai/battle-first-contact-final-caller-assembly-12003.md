# Final first-contact caller assembly after2586ED0, exact1.20.0.3

The immediate caller after2586ED0 is source-closed. The next minimum increment
is a pure join of explicit ordinary/MAA getter-stage results to the already
constructed side Entry occurrences, followed by the existing six-cache setter.
This slice requires no new native field or callee. It does not reconstruct the
preceding constructor, complete person preparation, or future stage mutations.

Frozen CK3 1.20.0.3 / Steam25652598, EXE SHA256
94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6.
All source below is reused cached exact-build evidence. Zero new EXE bytes,
native calls, game operations, builds, tests or wire consumptions in this package.

## Exact immediate caller

247AB1F is the instruction setting RCX=Combat;247AB22 calls2586ED0.
The following slice, through the final side call, is:

| Address | Actual instruction | Required model input |
| --- | --- | --- |
| 247AB27 | RDX = QWORD[Combat+6B8] | Final Combat Province, separate from initial Army Province |
| 247AB2E | RCX = Combat+20 | Side0 ordered levy and MAA entries |
| 247AB32 | call2651070 | All side0 entries receive getter evaluation and six-cache writes |
| 247AB37 | RDX = QWORD[Combat+6B8] | Caller reloads the final Province for side1 |
| 247AB3E | RCX = retained side1 pointer Combat+368 | Side1 ordered levy and MAA entries |
| 247AB41 | call2651070 | All side1 entries receive getter evaluation and six-cache writes |

There is no Character preparation, commander selection, source append, culture
callback or accolade rebuild instruction between the return of2586ED0 and
these two calls. Such inputs belong to the entered stage; this caller does
not generate their changed values. The earlier2650A80 Side+110 aggregate
must not be used as the MAA getter's fresh11E1350 accolade scratch: the latter
is independently rebuilt by30C4360 from the linked source occurrences.

2651070 loops side levy storage+28/count+34 before MAA storage+40/count+4C,
each with stride60. No current-quantity or main-phase eligibility gate appears
in this loop. 2657AC0 resolves full RegimentID at Entry+8, including its native
fallback path, calls26344C0 with the final Province, then writes only
Entry+30 i32 and Entry+38/+40/+48/+50/+58 q64. Identity, starting, current,
soft casualty and result-row fields remain entering-stage values.

~~~mermaid
flowchart TD
  E["Explicit caller-owned post2586ED0 state"] --> P["247AB27 Combat+6B8 Province"]
  P --> S0["247AB32 side0"]
  S0 --> S1["247AB37 reload Province;247AB41 side1"]
  S0 --> L["2651070 levy stored order"]
  S1 --> L
  L --> M["2651070 MAA stored order"]
  M --> R["2657AC0 full Regiment resolve/fallback"]
  R --> D{"26344C0 source dispatch"}
  D --> O["Ordinary exact five Character getters + max0"]
  D --> A["MAA source-derived six getter"]
  D --> K["Special knight: existing separate linked/selected primitive"]
  O --> J["Join exact side/bucket occurrence + Army/Regiment + final Province"]
  A --> J
  K --> J
  J --> W["Existing final setter: only six Entry cache fields"]
  I["Explicit changed-stage result or declared held-current source result"] --> J
  E -.-> U["Earlier constructor / complete person preparation still separate"]
~~~

## Closed dependency and minimum pure contract

The same-query ordinary_stat_inputs_v1 and maa_stat_inputs_v1 reconstruct
the frozen-current source-derived getter. They are usable source values; they
are not observations of a new post-effect stage. An assembly caller chooses
one of two explicit input modes for each occurrence:

- Explicit named-stage result from the ordinary/MAA lower pure APIs, using the
  supplied prepared Character/extra/culture/selector/accolade/environment inputs.
- A declared held-current source result, conditional on keeping those operands
  at their observed values in this modeled call. The source stage name and
  that assumption stay in the ledger; they are not renamed into an observed
  historical or future final stage.

The occurrence binding carries side_index, bucket, bucket_index,
native_carmy_id, regiment_id and source_combat_province_id. The assembly
joins these to the caller-owned post2586ED0 condition. An ordinary result
may be in either bucket, because26344C0 dispatch is a native source property
and is not inferred solely from the bucket name. A MAA result must use its
actual MAA occurrence. A native fallback result remains explicit with its
requested Entry Regiment identity and actual resolved source identity.

Use existing ordinary_six_stats_to_final_stat_input_12003 or
maa_six_stats_to_final_stat_input_12003 to create the final tuple with callsite
247AB32 for side0 or247AB41 for side1. Keep the getter result's real stage,
source ledger and full_getter_construction_ready. Then use
apply_first_contact_final_stat_refresh_12003 once over the ordered tuples.
Missing results produce partial, explicitly unrefreshed rows. Special knight
rows use the existing independent primitive and are not misclassified as MAA.

No effective_stats or cached Entry final tuple is used as a new MAA baseline.
Initial initialization_context_stats belongs to264DE30 at Army.currentProvince
and is not the endstage input. Query target Province must match the supplied
Combat Province for MAA environmental inputs. An ordinary getter does not
use the Province internally, but its final setter tuple still carries the
caller binding and exact callsite.

The pure minimum packet contains an unexecuted implementation recipe for this
join. Its only imports are the already qualified ordinary/MAA adapter and
existing final setter. It does not calculate new getter formulas or publish
another readonly capability. Production implementation and one genuinely new
integration case are the next coding package; earlier tests and wires need
not be repeated.

## Source references and readiness

- Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/battle-knight-entry-future-12003/outer-membership/evidence/0247a820-span.txt,247AB1F..247AB41: exact caller.
- Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/battle-knight-entry-refresh-12003/injury-order/slice-02651070-89.txt: whole-side bucket order.
- Same injury-order/slice-02657AC0-88.txt: requested full Regiment resolve and six stores.
- [Final stat formula and setter](battle-first-contact-final-stat-refresh-12003.md).
- [Ordinary and MAA getter sources](battle-ordinary-maa-changed-stage-stats-12003.md): five ordinary formulas, qualified current MAA source groups, and explicit lower stage APIs.

Readiness: research closure of the immediate final caller and an implementable
pure assembly contract. Ordinary/MAA current source getter qualification is
reused as its existing scope. No new static-ready implementation, complete
Entry, actual constructor execution, future forecast or live credit is claimed.

External delivery:
Z:/ck3_mod_rewrite_process_assets/g2-background-round6-20261006/final-entry-caller-assembly/.
