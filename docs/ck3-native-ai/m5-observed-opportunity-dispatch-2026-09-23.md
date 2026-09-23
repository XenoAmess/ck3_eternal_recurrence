# M5 observed opportunity dispatch (2026-09-23)

Status: **static-ready analytic dispatch; no formal M5 action or live joint
selection**. The exact game remains CK3 `1.19.0.6-steam23530548`, EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
This adds to the earlier [single-frame dispatch](m5-single-frame-dispatch-2026-09-22.md)
without changing public MCP capability or the production turn strategy.

## Why another selector entry exists

The existing `m5_joint_budget_selector` can reserve one candidate and reject
duplicate gold, army, ally, character and commitment claims, but it requires a
caller to supply `benefit_units` and five separate cost-unit values. No live
artifact currently provides a common utility scale for those values. They are
valid fixture inputs and are not an observed production payoff.

`m5_observed_opportunity_selector` accepts only proposals already approved by
their own formal domain policy. It does not compare native stewardship skill,
opinion delta, military power or alliance projections as though they shared a
unit. It filters the proposals using one full paused-frame identity and the
actual shared resources that are already observable:

- current gold plus each proposal's native or formal-policy gold cost and
  reserve;
- active and pending war slots;
- exact controllable army IDs and projected supply margin for war proposals;
- exact ally, character and long-term commitment keys;
- the existing commitment ledger, so two subpolicies cannot reserve the same
  army, ally, character, council seat, building slot or diplomatic promise.

Eligible proposals are ordered by least observed shared commitment: war slot,
army count, ally count, gold, commitment-key count, character count, then
supply margin and stable ID. This ordering is an explicit arbitration policy,
not an inferred native utility. A positive selection remains analytic and
returns no typed step.

`M5FrameDispatcher.choose_observed` is the reusable entry. It shares the same
single-writer reservation as the earlier assessed selector: after it reserves
one proposal, another call in the same paused frame cannot select a second
action. Its reservation records the chosen source policy and the resulting
gold, war-slot and identity claims.

## Existing proposal adapters

| Domain | Existing source consumed | Observed cost/commitment retained | Current boundary |
| --- | --- | --- | --- |
| Council | normalized Council19 steward observation plus `council-composition-steward-v1` action-ready decision | chosen CharacterID, incumbent/candidate stewardship, exclusive steward seat | Static adapter ready; no same-frame multi-domain live artifact |
| Building | `domain_construction_private_transport_v1` `status=selected` query | exact barony/province/building/slot, stock gold cost, formal 20M reserve, permanent slot key | Static adapter ready; typed building path remains independently gated |
| Diplomacy | `faction_gift_formal_candidate_v1` `status=selected` choice | faction/recipient identity, exact gift gold, 10M reserve, opinion delta and unique gift key | Static adapter ready; gift result still needs its own durable receipt |
| War | existing final-legal declaration and war-entry assessment | none admitted yet | A proposal still needs exact army claims, projected route supply, possible participant/ally commitments, campaign cost and exit commitment on this same frame |
| First-heir marriage | R0133 final-legal rows and five private alliance projections | none admitted yet | R0133's eight pairs all had `both_have_realm_data=false` and `would_attempt_if_accepted=false`; marriage/betrothal result and long-term alliance commitment remain unobserved |

R0133 remains read-only evidence: 657 distinct final-legal first-heir rows and
five successful projection reads, with zero observed alliance payoff in the
sample. This selector does not turn that count into a marriage proposal. It
also does not convert the Robert war power ratios into a war proposal because
power alone omits the resource and exit observations above.

## Focused fixture boundary and next live input

The focused fixture builds proposals using the exact field shapes already
returned by the council, construction and faction-gift formal paths. A
zero-gold steward replacement is selected when its seat is free. When the
same-frame commitment ledger already owns that seat, the result changes to the
lower-gold feasible faction gift; a second dispatch call cannot reserve the
building as well. This proves real resource arbitration behavior, but its
numbers and characters are fixtures and are not CK3 live outcomes.

The next read-only run should bracket current council, construction,
faction-gift, declaration/war-entry and first-heir queries with one snapshot
identity and persist the existing commitment ledger in that frame. War joins
only after the private prewar readers publish army/supply/participant/exit
claims. Marriage joins only after a candidate with an observed material
marriage or betrothal result and alliance commitment is available. Then a
formal consumer must submit exactly one selected typed action, prove an
independent material postcondition, consume the next turn and exercise the
required recovery path. Until those gates pass, G2-M5 remains `not_started`.
