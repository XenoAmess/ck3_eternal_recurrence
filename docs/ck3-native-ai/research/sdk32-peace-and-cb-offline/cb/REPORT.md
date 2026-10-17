# P32: actor-only CB prerequisite review (offline, not deployed)

Machine `xenoamess-full-tower-eb9d2c1186`; observed 2026-10-16T21:30:57.709023+00:00; CK3 1.20.0.4,
EXE SHA `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518` reused, no whole EXE rehash. Owner `/root` keeps SDK32/Game running.
No Game/MCP/Native invocation, live Driver read, SDK/DLL/W/index mutation, build or test rerun.

## Conclusion

The source permits hoisting some **type-specific hard predicates** as one-query negative gates.
Hungarian migration is the smallest clear source case: `00_event_war.txt:1419-1422` is
actor culture=mogyer AND actor faith's unreformed doctrine parameter. Neither clause reads
defender, selected title or claimant; no scripted-trigger recursion or temporary-scope write exists.
Do not infer its result from Robert's culture/name, location or zero rows; invoke the original
qualified predicate and record its actual boolean. True/unknown keeps the complete candidate set.

Claim has no hard `allowed_for_character` block: `00_claim.txt:42` is commented out.
Its title rules52-184 use claimant, title holder, weak claim and defender culture; even
mutually_exclusive_titles4-39 can read defender. The display block186-199 cannot replace
the hard predicate. Keep claim's current wide path; the earlier complete-claimant/title
inventory gaps are not solved by actor-only caching.

## Vanilla native path and exact ABI scope

Reused current `stock-cb-evaluator-prefix01.json` binds complete31F4520..31F4955:
`bool(type*, actor*, defender*, configurations*, bool arg5, bool arg6, text*)`.
Current ordinary calls use false,false,nullptr.31F45C5..46E1 makes actor-root,
defender-root and actor-root scopes, injecting attacker and defender names into all.
31F46F7 only bypasses the first block when arg6==true. With arg6=false and text=null:
31F4700..4719 evaluates rule+58;31F4728..473D evaluates type+48; either false exits
before31F47DA's configuration materializer. type+118 is only evaluated when arg5 istrue.
Defender-root type+1E8 remains in31F4776..4797; type+2B8 is also guarded byarg5.
Never set arg6=true to reuse a type-positive result: that would also skip mixed group rules.

New current static window `trigger-diagnostic-wrapper.json` proves37998D0(trigger*,scope*,text*)
tail-jumps372DF10(trigger*,scope*) at37998F6 when text==nullptr. This is the exact original
boolean predicate backend; use existing372DF10 only after its member meaning is qualified.
`actor-scope-constructor01.json` proves B17C70(void*scope,const Character*) -> scope,
0x168 bytes, root tag4 and full CharacterID at+8. Existing realm-law scope cleanup uses
889700 tail+118,889780 owned rows+100 and allocator release for+100/+18; a CB helper must
reuse that actual lifecycle, not memcpy borrowed scope pointers or leak owned native rows.
Named actor can be injected through373A0F0(scope+18, named-key, token16), following
31F45EA..4605; attacker key is the uint32 value at image+5D4BD94. token is kind4 plus
full-generation CharacterID at+8. No defender is supplied to the actor-only experiment.

**Remaining ABI gap:** source `allowed_for_character` -> actual type+48 loader binding
was not closed in this bounded review. Actor-root use alone does not prove field names.
31F20F0's parser and31F25FB..26AA's+48 field branch are found, but the on-disk literal
registry pair called2B10 does not directly map to parser runtime enum2B0F.372DF10 itself
is qualified by current direct calls; semantic source-to-member mapping is still pending.
The literal/pointer/switch locator attempts are preserved as locator-only, not semantic
proof.31F20F0's chained pdata fragments also are not independent function entries.
Next concrete entry: close the parser's caller-adjusted RCX and token registration/writer
of symbol pool+48/+54 consumed by3F4F8E0, or make a future read-only probe export the
actual token2B0F name and compiled member identity. Do not enable pruning on a guessed
name/offset. This gap does not block SDK32 or require a restart now.

## Group rule is not actor-only

Current group field rule+58 includes `herders_and_tributary_constraints`, defined
`00_war_and_peace_triggers.txt:1144-1195`: existsdefender, defender herder government,
tributary/suzerain and confederation relations, attacker-vs-defender tributary relations.
Thus the group block depends on recipient even though its root is actor. Never cache
the entire AI bitmap, group trigger, full evaluator false result, display predicates or
arg6 skip flag. `retaliation_cb` directly reads defender in its type hard block;
four adventurer invasion type blocks read defender's tier; all stay wide.

## Reviewed script-only opportunity set

The following29 exact installed type fields were manually reviewed for actor/global-only
dependencies; this is a source-backed candidate set, **not an enabled empirical whitelist**.
The JSON preserves every AST, exact source SHA and the recursively reviewed definitions.
World title/situation/liege/prisoner/contract collections here are rooted in actor or fixed
global keys, never the selected recipient. Cache lifetime is only one paused query; no
cross-day cache is proposed. Sources/compiled rules/mod or trigger override uncertainty
retains all targets. The old CB-only loaded-source review alone does not qualify these
recursive scripted-trigger definitions for a new runtime deployment.

|CB|P23 calls|P23 legal rows|P23 eval ms|Reviewed dependencies|
|---|---:|---:|---:|---|
|`hungarian_migration_cb`|38,292|0|322.225|Literal actor culture=mogyer AND actor faith doctrine parameter unreformed; no script-trigger calls.|
|`japan_imperial_expansion_cb`|38,292|0|105.356|Recursion closes through DLC, actor top-liege imperial tier/Japanese government and top-liege ceremonial title holder existence.|
|`japan_imperial_reconquest_cb`|38,292|0|85.001|Same closed actor/global dependencies as Japan expansion; defender predicate is a separate field.|
|`pam_investiture_conflict_cb`|38,292|288|72.417|Actor landed/faith plus fixed Christian Church situation phase and actor-faith council variable; DLC trigger is literal.|
|`leg_demand_fealty_cb`|38,292|0|71.908|Actor modifier and actor government flag only.|
|`duchy_conquest_cb`|38,292|0|70.702|can_use_conquest_cbs_trigger expands to actor government/rite/culture/law; actor adventurer exclusion.|
|`county_conquest_cb`|38,292|0|62.527|Same closed actor-only conquest trigger and adventurer exclusion.|
|`dissolve_empire_war`|38,292|0|70.566|Actor rite parameter/trait and two constant game-rule alternatives in empire_faith_gate_enabled_trigger.|
|`ireland_laudabiliter_conquest_cb`|38,292|0|65.486|Actor house existence and actor-house modifier only.|
|`fp3_unify_house_cb`|38,292|0|61.271|Actor house head, government/perk, independence and adventurer exclusion.|
|`de_jure_cb`|38,292|0|59.789|Actor culture innovation and actor government flags only.|
|`reclaim_relic_artifact_war`|38,292|6|55.417|Actor AI/zeal/tier/government, constant threshold100; no selected opponent.|
|`individual_county_de_jure_cb`|38,292|2|55.266|Actor culture innovation and nomadic government exclusion.|
|`individual_duchy_de_jure_cb`|38,292|2|53.610|Actor culture innovation and nomadic government exclusion.|
|`dismantle_byz_pretender_cb`|38,292|0|54.618|Named actor flag only.|
|`dismantle_holy_pretender_cb`|38,292|0|50.411|Named actor flag only.|
|`flowery_war_cb`|38,292|0|54.246|Actor faith parameter and actor prisoner collection/modifier only.|
|`imperial_reconquest_cb`|38,292|0|54.115|Roman-emperor trigger expands to actor owns either of two fixed empire TitleIDs.|
|`fp2_mediterranean_conquest_cb`|38,292|0|51.535|Actor landed/house modifier, controls three fixed duchies and adventurer exclusion.|
|`fp3_free_house_member_cb`|38,292|0|50.547|Actor house-head/government/perk and adventurer exclusion.|
|`sovereignty_cb`|38,292|0|49.176|Actor landed/nomadic government and conditional actor AI/tier only.|
|`ep3_laamp_peasant_war`|38,292|0|47.696|Actor adventurer government and supported-county variable-list existence only.|
|`china_hegemon_seize_duchy_cb`|38,292|0|46.791|Actor holds fixed title or minister title, plus fixed global dynastic-cycle situation parameter.|
|`china_hegemon_seize_county_cb`|38,292|0|44.285|Same actor-owned fixed-title alternatives/global situation as duchy form.|
|`ep3_laamp_raid_contract_cb`|38,292|0|44.508|Actor active-contract collection, matching a constant contract type.|
|`humiliation_cb`|38,292|0|40.827|Actor nomadic government and landed predicate only.|
|`artifact_war`|38,292|1|40.488|Actor has-any-artifact-claim predicate and actor adventurer exclusion; not claims against a selected recipient.|
|`county_struggle_cb`|38,292|0|17.991|Type field only excludes actor adventurer government. Group struggle rules are not hoisted.|
|`independence_war`|38,292|0|13.921|Type field only excludes actor administrative mechanic. Other group/recipient checks stay original.|

These29 fields cover 1,110,468 **existing** evaluator calls and 1.8726934s of P23
CB-first stock-evaluator wall. This is an opportunity upper bound only: some predicates
will be true; zero legal output does not prove an actor predicate false, and timing is
not CPU cost or a guaranteed saving. Additional single prechecks/scopes/profile overhead
must be measured. Hungarian alone currently took0.3222252s/38,292 calls in P23 (earlier
shadow0.7033334s with equal calls), so do not promise a stable0.7s saving. Claim took
0.1295594s and remains wide. The previous920 exposed rows/28.059% count reduction is
reused historical evidence, not acceptance of this proposal or SDK32 sec/game-day.

## Minimal future implementation / parity experiment

1. Close member source binding above; source guard includes actual CB definition plus
   all recursive trigger definitions and enabled override resolution. Unknown remainswide.
2. Extend `.4` candidate reader with onequery actor-hard result per qualifiedCB; call
   original372DF10 with freshly constructed actor-root/named-actor scope. Evaluate only
   the proven type-hard block; false yields empty candidate set, true/unknown uses the
   existing realm/independent candidate set. Still call stock31F4520 false,false for
   every retained target, preserving materialization and submit re-evaluation.
3. First shadow mode returns originalfull output and records boolean, precheck ns,
   source-qualified status, projected omitted calls and any baseline legal tuple whose
   type would have been omitted. No second N*C pass is necessary for this coverage check.
4. Only at a future owner-managed paused comparison: sameGame/actor/date and separate
   before/after native/public revisions; no intervening mutation. Compare full exposed
   tuples, claimant, ordered complete title lists, cost/shape availability, order and
   multiplicity. Record actual evaluatorcalls and total producer/MCPwall includingprechecks.
   Existing publiccost/nativeShape coverage0/920 remainsPARTIAL, not full parity.

No production patch is delivered until source-to-member semantics are qualified. This
bounded research ends with exact next entries; current30year stability work keepspriority.
