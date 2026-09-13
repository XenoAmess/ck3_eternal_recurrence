# G2 Raiktor three-way exit recommendation v2

Status: **static-ready / production input path defined / live action pending**.

## Problem closed by this package

The legacy `raiktor-campaign-dominance-certificate-v1` consumer required a
complete campaign outcome forecast, encounter distribution, finance endurance
and continue/surrender utility intervals. No production producer exists for
that combined object. GEN-034-A later delivered a narrower production-live
fact: a stable same-frame measurement of both war leaders' strategic power.
Keeping the old forecast object as the only route to a recommendation left the
new observation disconnected from GEN-034-D.

`raiktor_three_way_exit_recommendation.py` adds the intended minimal policy
path. It composes:

- the existing white-peace versus surrender utility evaluation;
- the v2 measured-power dominance certificate;
- the repository budget profile and versioned utility model already bound by
  the immediate-exit evaluation.

The old full-forecast v1 remains a valid research and quality-improvement
target. It is no longer a prerequisite for this bounded Raiktor exit loop.

## Continue-war value

Continue is not relabelled as a win probability or campaign forecast. Its
base utility is zero, then the model's existing
`measured-power-relation-penalty-v1` subtracts one versioned tail penalty:

| Measured relation | Continue penalty |
|---|---:|
| actor stronger | `0` |
| equal | `10,000,000` |
| opponent stronger | `50,000,000` |

These values come from
`ck3_autonomous_player/strategies/raiktor_exit_utility_v1.json`; they are
replaceable strategy configuration, not native-AI behavior or a claim about
the campaign's true outcome. White peace and surrender retain their observed
terms, hard-budget eligibility and bounded unobserved-effect penalties.

The provider compares all eligible options in the shared
`strategy_utility_q100000` unit. It publishes a unique recommendation only
when the leading utility exceeds the runner-up by the budget profile's
`minimum_switch_margin_raw`. Otherwise it returns
`three_way_underdetermined`.

## Same-frame and action rules

The immediate-exit and power certificates must agree on snapshot/public/native
revision, date, connection generation, episode, PID, WarID, player and primary
opponent. Missing power is a typed blocker; cross-frame evidence is rejected.

Static fixtures may exercise the choice rule, but cannot produce an action.
Only a unique recommendation with production-live immediate-exit inputs and a
production-live measured-power certificate emits one of:

- `resume-map` for continue;
- `offer-white-peace-{WarID}` for white peace;
- `surrender-war-{WarID}` for surrender.

The certificate fixes `single_action_only=true`. It also freezes route-specific
postconditions. A termination route requires old WarID absence, frozen gold,
prestige and claim disposition, directional truce days/expiry, prisoner and
favor results, source-specific war-regiment cleanup, and postwar checkpoint
cold-restore rebinding. A continue route requires the same war/player/episode
and an observed resumed successor revision.

Emitting a plan does not claim the command ran. `action_submitted`,
`postcondition_verified` and `gen034_closed` remain false until the bounded
managed runner produces those observations.

## Verification and remaining live work

Focused normal and optimized Python tests pass `7/7` in each mode. They cover
all three winners, insufficient winning margin, missing measured power,
cross-frame rejection, static-input action suppression and the production-live
single-action mapping. No CK3 process or desktop resource was used.

GEN-034-D now has a concrete recommendation/action contract, but remains
`blocked_live`. GEN-034-C must first reach a white-peace-admitted paused frame.
At that same frame the managed path must take two stable strategic-power reads,
run this recommendation once, submit its single action, verify the relevant
postconditions, save a checkpoint and cold-restore it. The existing R471 power
certificate is evidence for the native query/provider, not a reusable value at
the later horizon because its paused frame differs.

## Bounded same-frame recommendation runner

`run_gen034_three_way_recommendation_live_acceptance.py` prepares the read-only
half of that lifecycle. From an already admitted horizon checkpoint it performs
exactly one termination-options query, one narrow terms query and two stable
strategic-power queries. The before/between/after snapshots must remain on the
same paused identity, and native history must contain exactly those four reads.

The runner builds a fresh v2 dominance certificate on that frame and invokes
the recommendation provider in the same process. A GREEN report requires one
production recommendation and one typed planned action. It records the plan but
contains no action submission, time advance or exit mutation. Focused normal
and optimized tests pass `4/4`, and the CLI surface loads successfully without
starting CK3. This avoids spending another live run merely to refresh R471's
stale-frame value; the later action runner can consume the frozen same-frame
recommendation artifact.

## Exact action admission

`raiktor_three_way_exit_action_gate.py` is the final side-effect-free handoff
before the managed executor. It validates the recommendation certificate hash,
then binds its action to the current paused snapshot's revision, date,
connection generation, episode, PID, WarID, player and primary opponent. An
active event blocks the handoff. The exact action step must be advertised;
white peace and surrender additionally require their typed bridge capability.

On success the gate emits one hash-bound authorization with the expected
revision and the recommendation's postcondition plan. It never invokes the
command, and explicitly leaves ACK, postcondition, cold restore and GEN-034
closure false. Static recommendations, stale snapshots, missing actions or
missing capabilities remain blocked. Focused normal and optimized suites pass
`18/18` across the recommendation, runner and action-gate contracts. The
read-only recommendation runner now records this authorization in its report.

## Post-action prestige observation

GEN-034-D can now observe the player's post-action prestige after the old WarID
has disappeared. The additive `played_character_prestige` state-snapshot field
reuses the exact `extension+0x130` signed Q100000 leaf already exercised by the
war-exit terms reader. Legacy snapshots may omit it; malformed fixed-point
objects fail closed.

This closes only the offline visibility gap. The action executor must still
bind the pre-action balance and delta from the recommendation terms, submit one
authorized action, then compare the next paused snapshot before accepting the
prestige postcondition. Native fixture and focused normal/optimized Python
tests are GREEN; production-live evidence remains pending under the owner's
CK3-use hold.
