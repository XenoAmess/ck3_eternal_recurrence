# `hc-workforce` Route-B capture producer: production choreography audit

Status: **offline-audited / capture-entry RED / live-pending**

Audit base: canonical commit `1341251`. This audit did not start CK3, did not
modify the shared runner, did not write product variables, and did not treat an
option ACK or fixture output as a business result.

## Conclusion

The current Route-B capture producer cannot reach a real pre-B
`zg361we.360` frame from the registered canonical seed by its implemented
choreography.

This is not evidence that the product event or provider is broken. It is a
specific reachability gap between the seed and the capture entry:

1. the seed is paused before a Workforce case exists;
2. the producer performs no timeline advance after restoring that seed;
3. the transition fixture is shown only after AL is state 4 and Central's
   M360 source is already READY;
4. the Central stage-11 effect prepares that source and immediately calls the
   production resume seam in the same effect invocation; and
5. with the seed's owner still AI, the resume seam synchronously consumes the
   READY source through Route A instead of exposing `zg361we.360`.

There is therefore no script-proven stable rendered frame satisfying the
current fixture gate (`owner is AI`, `source_status=1`, no queued M360 event)
on the natural path from this seed. A new live attempt with the current entry
would be expected to stop at the fixture-event wait; it must not be described
as a Route-B product RED.

## Frozen seed evidence

The registered contract is `tools/zg361_phase2_seed_contract.json`. Its real
source save and observed paused frame are:

| Field | Frozen value |
|---|---|
| save | `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-r9-20260904-074005\attempt-live\native-state\profile\save games\xar_checkpoint.ck3` |
| bytes | `53,517,622` |
| SHA-256 | `bfc73fd9e7e80145cdf39aabc66bc2d731881122adab0cc0ba675fa07d1e6733` |
| product source commit | `e332c3bdfe3d5bedf0f3d1a3d028c7c3a6ee4560` |
| paused date | `53146920` |
| played subject | CharacterID `29037` (`han_6875`) |
| selected Workforce owner | CharacterID `32904` |

The same run's `artifacts-live/provider-probes.json` observed no active event.
Its Workforce query was `status=unavailable`,
`unavailable_reason=variable_context_unavailable`; the AL identity and all
collective fields were `case_unavailable`, and
`workforce_collective_ready=false`. The AI-owned B1 query did succeed for the
same owner/subject and observed cycle `1`, case `1`, state `1`, active `true`,
operation `39` (`roster_lock`), with owner `is_ai=true`. Thus the selector IDs
are real, but they are not a pre-M360 case.

The seed contract itself already warns that selector capture does not prove
the four domain providers ready. This audit preserves that boundary.

## What the current producer actually does

`run_phase2_hc_workforce_route_b_checkpoint_capture_scenario` implements the
following zero-game-day choreography after the managed session has loaded the
canonical save:

| Order | Operation | Timeline effect | Required observation |
|---:|---|---|---|
| 1 | query the paused seed snapshot | none | player `29037`, date `53146920` |
| 2 | install the acceptance-only Workforce transition fixture and hash-bind the cumulative projection | disk-only | product and fixture tree hashes |
| 3 | save and restore one activation checkpoint | no intended date advance | same player/date |
| 4 | if restoration exposes the unrelated B2 PIP card, execute its dedicated action cell | option selection only | exact `zg361b2.26` identity; this card was not active in the frozen seed frame |
| 5 | call `wait_for_phase2_exact_event` for `zga_phase2_workforce.1` | **none**; snapshot polling for 30 wall-clock seconds | exact fixture event |
| 6 | select fixture option 1 to change player `29037 -> 32904`; hidden `.2` calls the product resume seam | no intended date advance | exact owner/subject scopes |
| 7 | wait for the real `zg361we.360`, verify A/B/C shown and enabled, then freeze | none | owner played; distinct subject; exact date/lineage |

Step 5 is the present stopping point. The wait helper explicitly performs no
timeline input; it neither resumes the map nor executes a bounded day step.
Installing and reloading the fixture cannot create the missing business state.

## Exact fixture prerequisite

The automatic `zga_phase2_workforce_summon_gui` requires all of the following
on the played subject before it can create `zga_phase2_workforce.1`:

- the subject is non-AI and has not started/completed this fixture transition;
- `zg361_case_al_owner/subject/cycle_serial/case_serial/state/active` exist;
- `zg361_case_al_subject=this`, `state=4`, and `active=1`;
- `zg361_we_al_external_stage_receipts_verified=1`;
- `zg361_we_m360_event_queued` does not exist;
- the AL owner is alive, AI, and an eligible celestial liege;
- on that owner, `zg361_p2c_m360_source_status=1`, source owner is itself,
  source subject is the played subject, and source AL cycle/case equal the
  subject's active AL tuple.

The canonical seed proves none of the AL/source conditions; its real Workforce
provider instead reports that no case variable context is available.

## Production antecedent and time ledger

The following is the shortest **known product ordering**, not a claim that the
current seed can complete every gate. Exact scheduled offsets are stated where
the scripts freeze them; data-dependent waits remain explicitly unknown.

### B1 publication before Central can start

The seed fixture invoked the shipped `zg361_b1_open_cycle_effect` at D+0. The
live provider confirms cycle/case `1/1`, state 1, operation 39. The shipped B1
schedule then has these fixed anchors:

| Offset from B1 open | Event/action | Product transition |
|---:|---|---|
| D+180 | hidden `zg361b1.100` | mid-cycle dispatcher; manager state 1 -> 2 |
| D+240 | hidden `zg361b1.101` | peer/self-evidence window; manager state 2 -> 3 |
| D+241 | player `zg361b1.200` when self-review is available | the played subject must choose honest/exaggerated/conservative; AI subjects choose honest automatically |
| D+300 | hidden `zg361b1.102` | freeze facts and run review |
| D+301 | player `zg361b1.201` only when the frozen shadow policy exposes it | accept or supplement the non-final shadow grade |
| D+330 | hidden `zg361b1.103` | shadow deadline and quota-book submission |
| earliest D+331 | hidden `zg361b1.110` when the common-superior bank is ready | close the bank |
| earliest D+332 | hidden `zg361b1.111` | enter manager calibration |

Publication is not fixed at D+332. Pending calibration can schedule its own
30/31-day work, roster and common-superior readiness can delay the bank, and a
visible player event blocks time until selected. Only a genuine
`zg361_apply_pending_grades_effect` may call
`zg361_b1_mark_published_effect` and then
`zg361_p2c_on_review_published_effect`. The latter freezes Central stage 1 and
schedules its first pump at D+2.

### Central stages 1-11

Central is strictly serial: Career/HC, Compensation, Promotion/PIP, Incident
X/Y/Z, Metrics, Credit/Project, Career/Learning, Manager/Governance, then
Workforce/Endgame. A terminal stage schedules the next pump at D+2. Domain
cards and handoffs may add D+1 transitions and may stop on real user action or
external receipts, so `10 * 2 days` is only a pump-spacing lower bound, not an
end-to-end duration.

The Workforce stage first requires the subject's six real Career/HC partition
variables, then invokes `zg361_we_open_portfolio_effect`. AB -> AC -> AD -> AL
use their real product operations and D+1 transition gaps. At AL launch an AI
owner silently executes M355/M356 Route A; a player owner instead sees
`zg361we.355`, followed immediately by `zg361we.356` after a valid choice.
The AL case then waits with `zg361_we_portfolio_status=5` and
`zg361_we_awaiting_al_357_359=1` for the real B1 #357 and B2 #358/#359
receipts.

Once those receipts exist, one stage-11 pump executes this exact order:

1. `zg361_b2_submit_completed_al_receipts_effect` verifies and publishes the
   three external receipts and advances the exact AL tuple to state 4;
2. `zg361_p2c_prepare_m360_source_effect` freezes the three-manager source and
   may set `zg361_p2c_m360_source_status=1`;
3. in the same `if` branch, status 1 immediately calls
   `zg361_we_resume_m360_from_central_source_effect`;
4. the resume seam schedules the AL stage-04 deadline; when ticket owner is
   AI it materializes and applies M360 Route A, otherwise it writes
   `zg361_we_m360_event_queued=1` plus the owner/subject/cycle/case tuple and
   triggers the real `zg361we.360`.

For this seed the observed owner `32904` is AI. Consequently the natural
status-1 branch chooses step 4's AI Route A. The fixture cannot run between
steps 2 and 3 because those are synchronous statements within one effect, not
separate dated events.

### Three-cycle provider maturity

Even reaching any first-cycle `.360` is not enough for this capture producer
to publish its strict registry. The existing postcondition verifier requires
the current M360 receipt to be backed by a mature, strictly ordered three-cycle
Workforce history and a ready M361 charter gate. Therefore a usable source
must either already contain two prior genuine history cycles or genuinely run
earlier cycles before capturing Route B in the third. The current provider is
case-unavailable and cannot prove such prior history; the observed B1 cycle 1
makes assuming it unsafe.

The exact re-open date and choices for three complete review/Central/Workforce
cycles cannot be derived from the current provider packet. No finite calendar
duration from date `53146920` to a provider-sealable pre-B frame is therefore
claimed.

## Post-action provider seal

After selecting Route B, the ACK must retain
`business_receipt_claimed=false`. The fixture's typed `.3` handoff must return
play to subject `29037` without a date change. Only then may the existing
Workforce query seal the numeric cycle/case identity and all 13 fact groups:

1. exact owner/subject/cycle/case;
2. M360 receipt state 4, choice 2;
3. Route-B collective sealed, consumed and settled;
4. three distinct cohort IDs and manager IDs;
5. each cohort's forced count equals quota;
6. every cohort's exception count is zero;
7. every cohort's manager cost is zero;
8. aggregate members/quota/forced/exception/cost conserve the cohort totals,
   with total quota in 1..6;
9. exactly three strictly increasing history cycles ending at the current
   cycle;
10. each history slot has distinct positive #357/#358/#359 receipt IDs and
    hashes;
11. the M361 charter gate is ready in the same AL case at state 5;
12. charter evidence count is 3, ready, and not yet consumed; and
13. adopted cycle equals current cycle, effective cycle equals current+1, with
    positive prepared report and charter IDs.

All provider readiness flags, including `same_frame_ready`, must be true. The
query frame must remain paused, played as the subject, and match the last
provider revision/date. Numeric cycle/case values are deliberately not guessed
from the pre-action generic event scopes; they become checkpoint identity only
after this provider observation.

The separate career-HC provider is default-off for the B4 registry. If it is
explicitly enabled later, it must be provider-observed in the same paused
revision/date and match the Workforce owner/subject/cycle/case plus the real
state-4 choice-2 receipt. Its transport or capability ACK cannot replace that
observation.

## Remaining unknowns and next live entry

The current evidence does not prove:

- that Central's stewardship-ordered primary subject will be CharacterID
  `29037`;
- that `29037` is a celestial-liege/duke-or-higher manager eligible for M360;
- that three distinct M360-ready managers and total quota 1..6 will exist;
- that the required Career/HC partition and all stages 1-10 will close rather
  than WAIT/N/A/RED;
- that two earlier, genuine Workforce history cycles exist (the current
  provider cannot expose a Workforce case);
- the exact B1 calibration/publication date, annual re-open dates, domain
  choices, or total elapsed days; or
- whether fixture activation restore will expose a pending B2 card, although
  the frozen seed frame itself had no active event.

The shortest honest construction is an acceptance-only **earlier typed owner
handoff** at a real pre-resume WAIT boundary, before a stage-11 pump can prepare
and immediately consume the source. It must bind the exact Central/AL tuple,
must not write any `zg361_*` fact, and must leave all receipt/source creation to
the shipped product. Alternatively, supply a real checkpoint already played
as the exact owner with two mature history cycles and resume the genuine third
cycle. Neither entry exists or is proven by this audit.

Until one of those paths produces a paused real `zg361we.360` with option B
shown/enabled and the post-action 13-fact seal, readiness remains
`static-ready-live-pending` and the strict checkpoint registry remains absent.

## Offline verification

```powershell
py tools/test_zg361_phase2_hc_workforce_route_b_choreography_audit.py -q
```
