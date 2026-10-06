# Current prisoner release, ransom, execution and retention tree — CK3 1.20.0.3

Native AI and player strategy input ledger with an external read-only kinship source candidate. Initial source-tree cutoff **2026-10-06 23:45 Asia/Shanghai**; later parent-authorized construction remains uncompiled and shared hooks are external. This child has made no game, SDK, process, build, import, test, Git or EXE operation. Its readiness is **research**. It reuses the existing g104 release observer's **static-ready** qualification and the already completed received self-ransom loop; neither is rerun.

## Build, scope and evidence

- Ordinary Robert campaign, played character **29829**. War and religion research/execution authorization is open. This packet performs only source research.
- Exact CK3 **1.20.0.3 Crozier / Steam 25652598**, EXE SHA-256 **94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6**, reused from existing .3 contracts.
- Actual installed Steam prison source: **222,958 bytes**, pinned SHA-256 **1bb43b3c2061212af8d41b11314ff4e569af2a3506319f820d05877a7762abc5**. This child read that text once with parent authorization, without rehashing it. [Line-numbered source excerpts](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/prisoner-release/next-observations/native-ai-tree/CURRENT-STOCK-AI-EXCERPTS.txt) preserve the current AI blocks.
- The ignored repository game copy is not the current source. [STOCK-PIN.json](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/prisoner-release/STOCK-PIN.json) is reused.
- Read first: [native index](Z:/gb0/docs/ck3-native-ai/README.md), [historical prisoner tree](Z:/gb0/docs/ck3-native-ai/prisoner-crime-ransom-ai.md), [current family/ransom substrate](Z:/gb0/docs/ck3-native-ai/ck3-1.20.0.2-prisoner-ransom-native.md), [war retention provider](Z:/gb0/docs/ck3-native-ai/ck3-1.20.0.2-prisoner-war-retention.md), [three-source retention ledger](Z:/gb0/docs/ck3-native-ai/h2825-prisoner-war-retention-source-2026-09-28.md), [release value inputs](Z:/gb0/docs/ck3-native-ai/prisoner-release-value-inputs-2026-09-27.md) and [war termination](Z:/gb0/docs/ck3-native-ai/war-termination.md).
- The 1.19 tree's religious exclusion and the .2 article's original live-pending cutoff are historical facts. They do not impose current restrictions or describe current .3 live readiness. Their old addresses and old eleven-option release inventory are not ported here.
- Main source read-only baseline is Z:/gb0. Publication, central reports and integration belong to Root.

## What the current source establishes

The file defines separate interaction opportunity/score trees. It does **not** expose a single script which chooses the best of ransom, release, execution and keeping. Native cadence/selection/arbitration among these opportunities remains unmapped in this packet. Keeping a prisoner can be the observed result of not taking another opportunity; it is not proven to carry a separately evaluated native utility.

Authored cadence values are recorded as raw tier values; this packet does not derive scheduler timing from them.

| Interaction | AI candidate scope | Raw cadence by tier | Sender and answer distinction |
| --- | --- | --- | --- |
| ransom_interaction | prisoners; prisoner redirects to secondary_recipient; a nonruler with liege redirects payer to recipient (1886–1906, 2425–2435) | barony 36; county through hegemony 6 | Sender willingness 2437–2548; payer acceptance 2238–2422 |
| pay_ransom_interaction | family/spouses/scripted relations/liege, plus neighboring rulers/peer vassals/top-realm domicile owners with max 5 (3299–3310) | barony 0; other tiers 6 | Payer initiates to jailer; secondary_recipient is prisoner; sender 3324–3650 |
| ransom_me_interaction | self; redirect finds the jailer (3654 onward, 4161–4163) | barony 72; county/duchy 24; kingdom through hegemony 12 | Prisoner/payer initiates; jailer acceptance 3976–4139; sender 4165–4279 |
| release_from_prison_interaction | prisoners (6460–6462) | **barony 12; all higher tiers 1** (6463–6470) | Sender 6472–6710; recipient acceptance 5999–6457; auto-accept 5986–5997 |
| execute_prisoner_interaction | prisoners (6722–6724) | barony 72; other tiers 12 | Sender 6735–7048; auto_accept=yes at 7720 |

The current release cadence differs from the old fixed-frequency summary. The current execution tree has **three** direct factor=0 modifiers, including the county-or-higher inheritance branch at 7032–7047; the old two-zero summary is incomplete for this installed source.

## Source-first overview

Solid edges below mean current stock semantics or already bound source, not fresh CK3 results. Dashed edges are explicitly unclosed native runtime/observation branches.

~~~mermaid
flowchart TD
    P["Robert 29829 ordinary paused campaign"] --> C["Existing complete native prisoner collection<br/>full prisoner ID and jailer"]
    C --> K{"Independent current stock opportunity"}
    K --> R["Ransom<br/>final redirected payer and prisoner<br/>native option, quote, Can Send and answer"]
    K --> L["Release<br/>13 authored options and puppet_or_actor<br/>final Can Send and native auto-accept"]
    K --> E["Execution<br/>native default/selected method<br/>final Can Send and on-send costs"]
    R --> RS["Sender score: payment, greed, relations,<br/>struggle and three suppression branches"]
    L --> LS["Sender score: conditions, revenge,<br/>peace/time/compassion/family, struggle,<br/>feud, house unity and prison break"]
    E --> ES["Sender score: opinion/compassion,<br/>reason, inheritance, revenge, rite,<br/>struggle, nomad and realm inheritance"]
    RS -. "native scheduler/arbitration unknown" .-> N["Native chooses an opportunity or retains custody"]
    LS -. "native scheduler/arbitration unknown" .-> N
    ES -. "native scheduler/arbitration unknown" .-> N
    C --> W["Existing per-war participant/primary/succession/custody source"]
    W --> WT["Generic PoW pair and separate FP3 House rule"]
    WT -. "exit reachability and actual settlement separate" .-> N
    L --> G["g104 existing whole5wire / registered MCP102 GREEN<br/>static-ready final ordinary release input"]
    G -. "fresh current paused result not acquired here" .-> F["Root's same MCP read-only observation"]
    F -. "missing native kinship/relationship/value inputs" .-> CP["Future player comparison and typed action"]
~~~

### Jailer ransom

The sender's base is 0. Full gold or extortionate_gold adds 100. Current_gold adds 100 only with payer gold >=25 and prisoner time_in_prison >1 year (2440–2457). Positive greed contributes its actual value to full payment (2459–2466). Rival and nemesis of the prisoner subtract 100 and 300 (2468–2476). Favor within the jailer's vassal/liege relationship adds 100 (2478–2487). Struggle involvement/catalyst/agenda can add -100 or +200 (2489–2525).

Three branches multiply the **sender score** by zero: puppet_or_actor at war; a human payer at war or a prisoner refusal flag; prisoner being_prisonbroken_by_laamp (2527–2547). These do not establish a player Can Send refusal. Current outgoing policy can make an independent value choice after the native final legality/answer is observed.

Payer acceptance is a separate base-0 score (2238–2422). It uses payer greed, payer/prisoner identity (+100 for paying for self), family/spouse/friend/lover/parent relations, rival (-200) and nemesis (-500) of the prisoner, dynasty identity, intimidation/cowed and a celestial helper. A payer who is the prisoner is not the same shape as a redirected liege. The existing provider and the other child cover exact selected payment/quote/answer construction; this packet does not duplicate their implementation.

Received self-ransom acceptance gives full gold +50, qualifying current payment +25, rival -55, nemesis -300 and war with prisoner -300; it also reads hook, feud, dread relationship and celestial/herd/influence branches (3976–4139). The +0 WANTS_MORE_GOLD explanatory modifier is not itself a rejection gate. The authored payment threshold is not a material receipt.

### Release

The final ordinary branch has every one of the **13** authored options off. The auto_accept expression tests ten named condition flags (5986–5997); it does not justify calling every auto-accepted selection an unconditional release. The already qualified provider proves the complete all13-off selection and finalized puppet_or_actor custody. Nonzero change_prison/make_puppet or another selection needs its own exact outcome/role interpretation.

Current sender weights include:

- Selected conversion +20 and a further +100 for a vassal; renounce claims +30; banish +50; vows +30; recruit +10; disfigure +30; blind +20; castrate +50 (6475–6513).
- Rival/nemesis or exposed spouse betrayal gives -40 when the jailer is not forgiving; very high vengefulness adds another -100 under the same relation condition (6514–6550).
- While the jailer is not at war, child/compassion/time branches add 10; medium compassion requires a nonplayable prisoner and >3 years, weaker compassion >5 years (6551–6593).
- Close family can add 10 after >1 year for a nonplayable prisoner, with compassion/opinion qualifications; own child can add 40 for a nonplayable prisoner with the specified compassion threshold (6594–6625).
- Struggle catalyst/agenda/greed/compassion can add -100 or +200 (6626–6682); family feud gives -50 (6683–6689); Byzantine-vassal vows -10 (6690–6698); house-unity helper receives VALUE=100 (6700–6702); active prison break multiplies the score by zero (6703–6709).

War suppresses the positive compassion/family modifiers; it does not multiply the whole release score by zero. Source helper bodies (house unity, feud, struggle and conditional religious outcomes) are not fully expanded or scored by this packet.

The on-accept source separately grants released_from_prison opinion, House relation changes, minor_dread_loss and sadistic/callous stress; it can grant conditional struggle prestige, tier-based legitimacy and FP3-CB prestige effects. These are on-accept consequences. The ten final on-send costs neither price them nor show actual benefits. The new source does not infer numeric values of these named script constants from old versions.

### Execution

Current execution starts at 0, adds inverse opinion and -ai_compassion, discourages execution of children by a compassionate actor, and contains dynasty/extended/close-family penalties conditioned on the actor's rite doctrines (6738–6773). The literal NOT doctrine conditions are preserved from current source; this packet does not replace them with a guessed crime model.

Execution reason plus sadistic/lunatic gives +50. Execution reason plus positive greed and a title inheritable from the prisoner gives +20. Very high greed can give +35 for the same inheritance opportunity without an execution reason. Vengefulness with rival/nemesis/exposed spouse betrayal gives +20 with a reason or +35 at the stronger threshold without that requirement (6774–6831).

The no-motive NOR at 6834–6851 multiplies the score by zero when no execution reason, rivalry, spouse betrayal, inherit-able title or lunatic condition applies. Struggle importance/supporter/detractor branches, nomadic beheading/strength/rank inputs and rite/tenet checks also alter the score (6853–7024). Active prison break is another zero (7025–7031).

**Current third zero:** a prisoner who is vassal or below, holds a nonlandless county-or-higher title, and whose current heir is already a landed ruler with a different top liege, causes factor=0 (7032–7047). Primary-title tier alone and the PoW reader's first three primary-title successors do not evaluate this any_held_title predicate.

is_available checks is_at_war=no only when is_ai=yes (7050–7055). Player wartime execution legality is therefore a separate native final result, not denied by this stock AI restriction. Final validity also reads strong hook, torture, struggle prohibition, purge and current puppet custody; source declares a diarchy prestige surcharge (7063–7104). Seven execution flags and auto-accept are preserved at 7606–7720. There is no current execution preview/action qualification in this packet.

### War retention

Generic PoW source reads both participant sets, each primary and the primary title's first three ordered successors, then actual custody/jailer. It yields jailer -> prisoner pairs for that exact war's generic release effect. The current provider already exists in ck3_12002_prisoner_war_retention.cpp and is admitted through the .3 reuse contract.

FP3 free-House-member CB is a different branch: House matching, defender custody, CB-specific release/invalidation and prestige effects. Generic PoW exit effects are skipped for that CB in the previously frozen source. This packet reuses that admitted/source ledger; it has not reread or newly hashed war-effect/CB text. Current installed release text at 5304–5331 directly preserves the personal-release FP3 prestige branch.

A complete empty generic pair list rejects only that matching rule. It is not a zero retention valuation. Actual exit option availability and settlement are separate reads. No historical WarID or historical empty pair is projected onto Root's current campaign.

## Current strategy construction gap

The current source [prisoner_ransom_formal_consumer.py](Z:/gb0/ck3_autonomous_player/src/xar_autoplayer/prisoner_ransom_formal_consumer.py:138) chooses the largest positive ordinary gold/current_gold quote among unrelated non-child prisoners whose primary_title_tier_raw is null or **1**. It requires final Can Send/answer and same-frame complete per-war source. It excludes every prisoner in either release-candidate array, actual release pairs and FP3 CBs. It runs before the existing life-advance/route-horizon steps, after collection ingestion. This is the implemented minimum strategy; the outgoing tier cap remains unchanged.

The received-offer path [strategy.py](Z:/gb0/ck3_autonomous_player/src/xar_autoplayer/strategy.py:2617) has a different minimum policy: positive ordinary gold, actual pending roles, same-frame complete unrelated/non-child custody, no current war and native accept legal/executable. It retains quality gaps for title political value and greed/rivalry/feud. Existing source metadata records proactive_outgoing_tier_cap_changed=false.

Reuse the **70766 / 56-gold received self-ransom production-live loop** and h9543 receipt once. The prisoner left the player collection and gold increased by 56 after the independent reads. That loop does not qualify arbitrary outgoing ransoms, current release, execution or complete native utility. It is not to be replayed.

There is no implemented cross-action comparator for release/ransom/execute/retain demonstrated here. These are concrete missing inputs/consumers, not safety blockers:

| Required native input | Proven participation | Existing output / lowest-cost next step |
| --- | --- | --- |
| Fresh ordinary release legality/acceptance/costs | Current native final context; g104 source+whole fixture | Existing unconditional_release_preview, all13 keys/mask/puppet, can_send, acceptance and ten cost rows; Root reads once using the current ordinal/revision. No new bytes or qualification rerun. |
| Selected negotiated condition, final roles, exact quote/answer | Current release/ransom authored scopes | Owned by the other two children; consume their named exact branch results before a dependent choice. No alternate API or duplicate implementation here. |
| Close and extended family | Release 6612; execution 6763/6770; payer acceptance 2304/2326 | **Missing from current prisoner wire. Reuse already admitted bool(Character*,Character*) native predicates 0x29120A0 and 0x2912290 in the same collection reader.** Keep child/dynasty fields intact; they do not substitute kinship. |
| Rival/nemesis, current opinion, exposed spouse betrayal, feud | Release 6514–6550/6683; ransom 2468–2476; execute 6738/6794 | No current prisoner-row result or fully closed callable/layout in this child. Next source/ABI work maps these exact predicates for the existing selected prisoner and finalized jailer. Do not substitute same_house or same_dynasty. |
| time_in_prison, age/playability, ai_compassion/ai_vengefulness/ai_greed | Release 6551–6625 and ransom 2440–2466 | Current prisoner wire lacks the duration/personality terms. Native query must expose actual values or these exact compiled branch results in the same context; numeric threshold expansion is a quality input, not an extra permission gate. |
| Execution reason and final selected-method legality | Execute 6777/6838, 7063–7104 | Next same-query execution preview reuses definition lookup, owned current context/default option picker, refresh/finalize, native validator, cost and auto-accept. It must read the selected native method. Reason/tyranny/outcome valuation remains distinct; no old reflection string is treated as callable. |
| Every held county+ title, current heir, realm membership | Execute third zero 7032–7047 | Existing primary-title metadata and generic PoW successors cover narrower predicates. Map/observe the full held-title/current-heir/top-liege branch before consuming it. No inference from one title tier. |
| War PoW matching | Current admitted participant/succession/custody reader | Existing query-war-prisoner-release-pairs-v1-WarID; one fresh same-frame read per actual active WarID. No new observer needed for the generic source graph. |
| Dread/title and actual post-release consequences | Current on-accept 5105–5125, 5227, 5304–5331 | played_dread_raw, primary_title_tier_raw, House/Dynasty already exist; reuse them. Add precise same-frame opinion/stress/legitimacy/House/struggle outcomes only for a selected value branch. A new generic effect-preview engine is unnecessary. |

## Exact next read-only observer: native kinship in the existing collection

This is the cheapest new source construction now identified, after Root's existing preview read. It requires **zero new EXE bytes**.

Existing [header](Z:/gb0/ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12002_family_obligations_break_penalty.hpp:11) binds kCloseFamilyRva=0x29120A0 and kCloseOrExtendedFamilyRva=0x2912290 as bool(void*,void*). [Existing ABI](Z:/gb0/ck3_autonomous_player/native_bridge/research/ck3_12002_family_obligations_break_penalty_abi.json) preserves full spans 0x29120A0–0x291222B and 0x2912290–0x29122EE. The .3 [reuse manifest](Z:/gb0/ck3_autonomous_player/native_bridge/research/ck3_1_20_0_3_abi_reuse.json:1122) classifies that manifest PASS and includes the 395-byte close-family span with SHA-256 c76f9193664d349b6919ee9ae363c995d4aee6278b09d2e9a9278da3e7c3fecc. No new binary proof is necessary.

Construction route:

1. Extend the existing current player-prisoner collection's source sample at the point where it has already resolved the played character and each full prisoner ID. Evaluate native close-family and close-or-extended-family for the exact prisoner/played pair.
2. Copy those two booleans into the same first/second source sample and existing normalized prisoner row; preserve all existing child, House, Dynasty, title and dread fields. These are **new observations**, not renamings of existing ones.
3. Reuse existing .3 admission/compatibility binding and the two callable predicates. Do not call the unrelated complete family-break penalty reader or reproduce its marriage/rite/resource dependencies.
4. Add one new actual whole-collection producer and one first registered collection consumer for those new values only, after Root adopts a concrete implementation. The test should contain a non-child close-family example distinct from same dynasty, and an unrelated example, so it proves real additional information. No existing g104 or ransom test is rerun.
5. Root reads that extended same MCP once in a fresh paused frame. That promotes only the kinship observer to a production-live primitive. A future chosen release still needs independent custody and material aftermath.

Parent subsequently authorized construction. Seven new source files now deliver the DTO, two-predicate reader .inc, serializer .inc, strict Python contract, new six-case whole producer, registered MCP compound and CMake fragment. [Sealed FIRST plan](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/prisoner-release/next-observations/native-ai-tree/KINSHIP-FIRST-PLAN.json), [external shared hooks](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/prisoner-release/next-observations/native-ai-tree/shared-hooks.apply-patch) and [integration/first recipe](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/prisoner-release/next-observations/native-ai-tree/INTEGRATION-AND-FIRST-RECIPE.md) specify adoption. The child wrote the hooks externally; the parent subsequently adopted them in the isolated tree as recorded below. Build/import/fixture/registered execution are all NOTRUN. For the other missing predicates, no callable RVA is claimed; a subsequent finite new-byte proposal must precede any EXE read.

## Legal fresh query recipes, not executed here

For the closed ordinary release branch, Root uses the **existing** registered tool:

~~~text
ck3_query_player_prisoner_collection_private_v1(expected_revision=R, ransom_ordinal=0)
# Inspect the returned complete collection and actual current source_ordinal=k.
ck3_query_player_prisoner_collection_private_v1(expected_revision=R, ransom_ordinal=k)
# Omit the second call when k=0 and the first result already evaluated that row.
~~~

R is the current public revision from Root's fresh paused Robert snapshot; native revision/date/full prisoner ID and jailer come from that result. This selects a current row, not historical 61540 or 70766. The result is an observation even when can_send=false. The compiled g104 data is not deployed/live by this packet; Root must use its matching admitted runtime before the query.

For the closed generic war source, the existing driver step is:

~~~text
driver.execute_step("query-war-prisoner-release-pairs-v1-<current-full-WarID>", expected_revision=R)
~~~

Root takes WarIDs from the current snapshot's complete active_wars and reads each at R with the same paused native frame. The stock FP3 branch and generic pair result remain separate. There is no new registered war-MCP name invented by this recipe. Source/byte/fixture closure permits a fresh read; it does not imply current runtime deployment or an actual empty result.

For incoming ordinary gold, reuse the existing pending-context and collection observation routes. A future fresh offer is selected from the current pending full ID and current roles; it cannot replay the resolved 70766 request. No query/action recipe is claimed closed for execution, full native score arbitration, duration/rivalry/feud or the full execution inheritance branch.

## Delivery and honest boundary

[Source evidence](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/prisoner-release/next-observations/native-ai-tree/SOURCE-EVIDENCE.json), [Root delivery](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/prisoner-release/next-observations/ROOT-DELIVERY.json) and [Oct6/W41 fields](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/prisoner-release/next-observations/OCT6-W41-FIELDS.json) are external review artifacts. Own package: research, source tree and implemented source candidate; no static-ready or live promotion. Reused ordinary-release input: static-ready. Reused received self-ransom: one production-live loop. New live observations/actions/days: **0**.

The parent adopted the seven native-kinship files and collection header, serializer, mailbox, strict transport and CMake hooks into the isolated prisoner-release source tree on 2026-10-07. The existing registered collection query evaluates native kinship for its selected ransom_ordinal; old serializer callers without the optional kinship array remain schema 6, while this bound mailbox emits schema 7. The source is uncompiled and its six-case FIRST is NOTRUN. [Integration and FIRST recipe](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/prisoner-release/next-observations/native-ai-tree/INTEGRATION-AND-FIRST-RECIPE.md) records producer and registered-consumer arguments. The Oct7 follow-on [negotiated-condition topic](prisoner-ransom-negotiated-current-inputs-12003.md) now connects nonzero release options through the same MCP/Driver/native collection path; its independent new six-case FIRST remains NOTRUN and does not alter the kinship cases.

Root can adopt this current-build tree and isolated source commit into the canonical topic, index and reports before the sole new FIRST. The current field gap is an observation task, not a reason to keep emitting null indefinitely or to reopen completed FIRST qualifications.
