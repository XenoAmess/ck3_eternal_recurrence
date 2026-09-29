# Collect Taxes replacement value: exact-build probe

Status: **static research; native paired evaluator unresolved**. No CK3 session,
candidate DLL, action, or new gameplay capability was produced by this probe.
It is scoped to an occupied ordinary steward seat using `task_collect_taxes`.

## Frozen inputs

- CK3 `1.19.0.6`, `ck3.exe` SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- `common/council_tasks/00_steward_tasks.txt` SHA-256
  `B3087378E04D0CDF7B1C1BEBF97FD17E36D8684DDD157D4FB0647B1D5681FC4B`:
  `task_collect_taxes` applies `domain_tax_mult=1`, scaled by
  `steward_collect_taxes_total_scale` in `council_owner_modifier`.
- `common/script_values/99_steward_values.txt` SHA-256
  `6A4AC7C1E575E54FBA4A3BE06F58146F753629622491FDDAE25D09C439699C3B`:
  lines 63-136 define base `stewardship / 2`, conditional tax-man,
  erudition, family-business, consulted-house and bookkeeping additions, then
  divide by 100. The family/house terms depend on the proposed councillor and
  owner relationship; a skill difference is not a full result.
- `common/scripted_triggers/00_councillor_triggers.txt` SHA-256
  `D7A10D08D2F73D770B56A375ECEBCBE02486038B4E9648B492BEE786A482C9C2`:
  lines 985-995 contain the candidate-dependent family-business and
  consulted-house predicates.
- R700 private same-frame final-gates artifact
  `g2-m4-council-r696-checkpoint-readonly-72882e69-v2/live-r700/raw-terminal-result.json`
  already exposes the occupied incumbent, candidate IDs, signed stewardship,
  candidate legality and fireability. In that frame incumbent `33433` has
  stewardship `16`, while candidate `32716` has `12`. Their base tax scales
  alone are `0.08` and `0.06` (Q100000 `8000` and `6000`); the full native
  values and opportunity costs were not observed. This R700 query also does
  not prove that `task_collect_taxes` was the active task in that frame; the
  pair is an illustrative target for a later task-bound read.

## Compiled entry search

The authored `task_collect_taxes` and
`steward_collect_taxes_total_scale` strings are absent from this EXE, as
expected for dynamically loaded script data. `council_owner_modifier` occurs
at RVA `0x429C578` and `0x4415D46`; the first is referenced in a global
name/ID table at RVA `0x42C1358` (ID `0x2E27`). No direct `.text` RIP reference
to that key establishes a task-specific evaluator.

`GetCouncilOwnerModifier` occurs only as the longer reflection name
`GetCouncilOwnerModifierDescFor` at RVA `0x4415BE0`. Its sole direct RIP use is
the registration sequence at RVA `0x59D429..0x59D46E`, whose helper is
`0x2D6F8F0`; this is a GUI description registration, not proof of a numeric
modifier value or an alternate-candidate scope. The adjacent reflection names
are `GetCouncilModifierDescFor` and `GetCouncillorModifierDescFor`. Similarly,
the only `GetModifierValue` prefix found is `GetModifierValueFor` at RVA
`0x440F218`, referenced at `0x58C8B6`. Neither name proves a paired numeric
evaluation contract.

The known `ActiveCouncilTask` value-progress evaluator `0x2D650A0` reads
`CouncilTaskType+0x14E0` and constructs active task scopes before calling
`0x9698B0` at `0x2D65291`; its callsites at `0x23BAC2A` and `0x27E8260`
serve progress, not the `council_owner_modifier` tax value. A scan of direct
relative calls to the generic script-value evaluator `0x3373000` found many
callers, but none is yet bound to this task field and candidate-scope context.
The older truce direct-evaluator experiment also exited before its first
return, so a standalone call must not be inferred safe from its signature.

## Decision boundary and next probe

The existing R700 reader already covers seat occupancy, ability and final
eligibility. Adding those fields again, or publishing a Q100000 result from
`stewardship/200` alone, would falsely imply that a replacement increases
taxes. No replacement is ready on this evidence.

The next bounded native probe should locate the `CouncilTaskType` owner
modifier field and its actual application callsite, then prove the caller's
owner/councillor scope objects and the returned numeric scale. Only after an
exact-build, side-effect-free paired read can a private projection compare
incumbent `33433` with R700 candidate `32716` and carry the incumbent-firing
cost. The public council query, action and advertisement remain OFF until
their existing gates are met.
