# H3937 dynamic target siege: disabled read-only stage

Status: static candidate on #612 integrated commit
`9b54496a5e2cb4b57f4548926a72ed9d30299d46`. No CK3 run, no new
DLL, no prepared-state rebind and no live result are claimed by this change.
`H3937_TARGET_LIVE_AUTHORIZED` remains hard false. This module is an **inner**
collector only; it neither starts a managed session nor proves outer cleanup.

The existing combined collector reads the stationary friendly Province 2610
and one-day local contact. Those two reads do not describe a route toward the
currently besieged enemy Province. The H3937 source case placed that enemy at
2629, but 2629 is only a historical anchor. The new stage selects a target
from the same-session, current war/army/strength rows using the existing
primary-defender siege-relief assessment. If no eligible stationary sieging
enemy and single idle controllable army are proven, it stops. If multiple
candidates exist, the existing assessment's recorded policy chooses lowest
war score, then WarID, ArmyID and ProvinceID; the receipt preserves its
candidate count and selection. This is a read target, not a move decision.

## Read order and checks

The caller must own one paused managed session and all exact H3937 source,
DLL, injector, rebind, screen and lifecycle checks described by the combined
outer contract. The inner stage calls the combined S0/Q1/S1/Q2/S2 collector,
then reobserves S2 exactly before doing any more work. It issues only these
additional native read steps:

| Step | Native read | Required binding |
| --- | --- | --- |
| Q3 | `query-army-strengths-v1` | Every army in the current native-published war scope; available result and normalized S3 strength cache, exact snapshot/revision/query sequence. |
| Q4 | `query-province-local-siege-v1-<dynamic target>` | Target from the current eligible sieging enemy; available occupation/siege fields at the exact native revision and date. A null active-siege pointer remains an observation, not participant proof. |
| Q5 | `preview-move-army-<subject>-to-<dynamic target>` | Full route starts at the current subject Province and ends at the selected target; preview metadata binds public/native revision, snapshot, episode, connection generation and date. |
| Q6 | `query-route-contact-horizon-v1` for the dynamic target | Sorted current nonretreating enemy IDs match the complete **native-published** hostile scope. The one-day native timeline and every subject/enemy current Province and remaining route match S5 and the Q5 preview. |

For every Q3–Q6, `S_i` and `S_{i+1}` must keep the paused date,
snapshot ID, public/native revision, episode, connection generation and the
complete native-published war/army route scope. Exactly one query-only native
history row with the exact command and raw response must be appended. Result
and snapshot cache comparisons are structural, not an `accepted` bit alone.
The receipt retains all frames and raw envelopes, including bounded RED
attempts. It does not treat the strength counter as a cross-family clock;
ordered history proves the sequence.

`observed=true` means these **read-only, native-published** observations are
internally consistent. It does not certify that the war roster includes every
physical army. A `physical_army_inventory_check` included in Q6 must be valid
and explicitly say `date_or_action_authorized=false`; its absence does not
upgrade the result. The receipt always says
`physical_army_inventory_completeness_proven=false`,
`participant_scope_proven=false`, `forecast_qualified=false`,
`first_hop_contact_observed=false`, `outer_session_cleanup_verified=false`,
`action_authorized=false`, and `date_advance_authorized=false`.

## Remaining route and action gap

For a route such as H3937's two-leg path, a full-target one-day contact
query does not establish the proposed first-hop action. A later separately
reviewed stage must use the same live frame to preview the literal
`[first_hop]` route and query every eligible hostile against that hop. It
must also bind current physical inventory completeness, separately account
for retreating hostile armies, prove siege participants/offsite partition and
qualified combat or contractually bounded provisional risk, then satisfy the
formal move/date selector and fresh source/outer cleanup gates. War cash and
forecast readiness remain independent. Neither a Q6 contact-free bit nor this
stage can grant a move, attack, one-day advance or first-hop authorization.

Synthetic normal and `-O` unit tests cover the disabled gate, a dynamically
selected historical and nonhistorical target, unchanged same-frame positive
reads, missing current siege, partial strength/Province, stale strength cache
and preview, hostile position or route mismatch, invalid physical-mailbox
candidate and an intervening history row. These tests exercise contract
behavior only; they are not native H3937 or formal planner evidence.
