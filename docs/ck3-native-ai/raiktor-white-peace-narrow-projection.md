# Raiktor white-peace narrow projection

Status: `static-ready / live=false` (2026-09-13, exact build 1.19.0.6).

## Problem and boundary

GEN-034 needs `continue / white_peace / surrender` terms on one paused frame.
The generic loaded-effect termination preview is not a viable input: two real
runs crashed in CK3 RVA `0x334C668`. That RED remains open and its production
dispatch remains disabled.

The replacement is
`raiktor_white_peace_narrow_projection_provider.py`. Provider v2 is a read-only Python
composition over the existing safe `ck3_query_war_termination_options` and
`ck3_query_war_termination_terms` results. It accepts only the primary attacker
in `raiktor_claim_cb`, and requires the snapshot, both query receipts and the
surrender aggregate session to agree on process, connection generation,
episode, snapshot, revisions, date, WarID and CB identity. It adds no mailbox
command, ABI, native reader or mutation.

The v2 observation separates consequence evidence from current execution
availability. An explicit native rejection of the outbound white-peace option
no longer erases exact-build white-peace terms. The observation preserves that
rejection and the same-frame surrender execution state for the downstream
eligibility gate. Missing terms evidence and a CB that forbids white peace
remain blockers.

## Exact-build projection

The terms source is
`game/common/casus_belli_types/00_event_war.txt`, SHA-256
`BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707`.
The truce helper source is `game/common/scripted_effects/00_war_effects.txt`,
SHA-256
`A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D`.
Both are already frozen by the normalized Raiktor terms query together with
CK3 executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

| Domain | White-peace value | Evidence rule |
|---|---|---|
| execution state | native white-peace and surrender option state | copied from the same-frame options query; it gates execution downstream, not consequence projection |
| declared claims | retained; weak claims strengthened | exact `on_white_peace` target-title loop |
| primary gold transfer | `0` | no primary transfer exists in the exact white-peace branch |
| attacker prestige | `cb_prestige_factor * -5` | the branch runs the same `setup_claim_cb(victory=no)` before its literal multiplier |
| prisoner releases | same current release pairs | both branches call `show_pow_release_message_effect` |
| favor hook | same boolean | both branches use the identical attacker-to-claimant conditional |
| truce duration | same evaluated day count | white peace and defeat both use `standard_truce_duration_days` in the same direction |
| titles / hostages | no holder change; no hostage variant | exact branch plus `allow_hostages=no` |

The shared-expression rule does not relabel the surrender result as white
peace. Only the value of the common input or conditional is copied; the
white-peace disposition remains separately identified.

## Explicit uncertainty

The provider does not turn absent observations into zero. It carries these
effects as unobserved for the downstream versioned utility model:

- attacker and defender trait-dependent stress;
- defender accolade glory and attacker accolade white-peace prestige;
- ally fame deltas;
- glory-hound and antagonistic-clan opinion rows;
- LAAMP settlement outside the CB effect.

This is sufficient for a bounded comparison because the model has a versioned
per-unobserved-effect penalty. It is not a full effect preview and does not by
itself authorize white peace or surrender.

## Verification and next live step

Focused tests pass normal and optimized modes, `6/6` each. They cover a full
projection into the existing same-frame comparator, session drift, explicit
native unavailability with preserved terms, missing truce duration, wrong CB
and missing inputs. The
representative projection compares attacker prestige `-35.0` under white peace
with `-70.0` under surrender while preserving the exact terms distinctions.

GEN-034-C remains open until one bounded managed CK3 session supplies a real
same-frame projection and the new strategy utility model evaluates it. That run
must use the next CK3 round, must not call the disabled broad preview, and does
not justify a long-running scenario matrix.

## Same-unit immediate-exit evaluator

`raiktor_exit_utility_evaluator.py` consumes the projection, its hash-bound
surrender aggregate session, the versioned budget profile and the versioned
utility model. It maps both immediate exits into the same nine-feature
`strategy_utility_q100000` vector. Gold and prestige use truncating Q100000
multiplication; discrete claims, favors, truce days, prisoner releases, title
changes, hostage transfers and proven war-bound soldier losses use direct
integer coefficients.

The evaluator applies the model's bounded per-effect uncertainty penalty to
seven white-peace effects and nine surrender effects that the narrow queries do
not value. It also applies the existing option-specific hard budgets before
reporting a pairwise preference. Generic current regiment strength is not
relabelled as a proven surrender loss. In the representative fixture, white
peace scores `-29,025,000` and surrender scores `-74,725,000`; white peace is
nevertheless ineligible because that frame would grant a favor while the
versioned white-peace budget forbids one. This illustrates why the certificate
keeps utility and budget eligibility separate.

The output is comparison evidence only. It deliberately has no continue-war
utility, full three-way recommendation, action literal or submission authority.
The focused projection-plus-evaluator tests pass `10/10` in normal and optimized
Python. GEN-034-C remains `blocked_live`: one bounded production frame must
prove the same projection/evaluation path before C can close. The next
integration package will value continue separately from measured strategic
power, then produce the one three-way decision required by GEN-034-D.

## Bounded production runner

`run_gen034_white_peace_evaluation_live_acceptance.py` reuses the managed
cold-checkpoint session owner. It admits exactly one options query followed by
one narrow terms query at the same paused public revision, then runs the
projection and immediate-exit evaluator in process. Native command history
must contain exactly those two successful reads. The runner also requires the
crash-prone broad preview family to be absent from advertised action steps.

The runner never advances time, submits a war-exit action, or enables continue
valuation. Its focused tests pass `4/4` in normal and optimized Python. The
next action is its no-launch admission against the frozen R459 checkpoint,
followed by one managed current round R640 only if every immutable identity is
GREEN.
