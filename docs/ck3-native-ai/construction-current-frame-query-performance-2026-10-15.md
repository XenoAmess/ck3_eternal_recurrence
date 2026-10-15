# Construction current-state queries without transcript exports (2026-10-15)

The current-cash query used by ordinary construction planning exported the complete
Native command history twice, although its normalizer and metadata projection
only read the current frame and cash packet. The fix passes the existing
`include_native_command_history=False` option. Both before and after snapshots,
the same request, and the complete paused-frame comparison remain in place.

The wartime construction observation also used a full snapshot solely for
current actor, frame, treasury, active-war and army fields. It now uses the
existing `_query_context_snapshot` reader. The construction source query already
used that reader. Drivers without the finite reader retain the original fallback.
No native capability, candidate selection, cooldown, reserve, action admission,
postcondition, or query count changes.

## Actual closed P04 window

Evidence is continuation40-cold-prep/ROOT-P04-PERFORMANCE-WINDOW-RESULT.json,
SHA256 `06542b5a73d9ba398ca778a5459a5e89473a212a00f5e8c7ac38b08c993362a4`,
plus immutable p04-responses 0016 through 0766 and their settled CUMULATIVE-TURN
receipts. Root's full window observed 682 game days in 1132.139396 seconds
(1.66002844 seconds/day). The 359 AUTO calls took 996.998498 seconds.
Ten actual SAVEs took 67.403140 seconds, 360 METRICS took 3.429700 seconds,
and ten SEMANTIC calls took 0.081958 seconds. The remaining 64.226100 seconds
between processing totals and wall time are not separately attributed.

| AUTO selected step | Calls | Whole AUTO seconds | Planning seconds | Observed days |
| --- | ---: | ---: | ---: | ---: |
| life-advance | 76 | 484.922 | 250.632 | 682 |
| query-declarable-wars | 29 | 296.405 | 139.158 | 0 |
| query-war-results-window-v1 | 75 | 61.582 | 54.035 | 0 |
| construction receipt | 48 | 51.474 | 17.470 | 0 |
| war-entry assessment | 117 | 42.107 | 25.683 | 0 |
| construction submit | 2 | 21.090 | 13.407 | 0 |

The construction planning stage accumulated 327.744495 seconds across 231 calls:
190.941011 seconds inside 35 life-advance AUTO calls, 118.430239 seconds inside
29 declarable AUTO calls, 12.101982 seconds in the two submit AUTO calls, and
only 1.989758 seconds in the 48 receipt AUTO calls. These stages are included in
normal planning; different stage totals must not be added together.

Actual AUTO707 took 16.159926 seconds, with 13.178947 seconds in normal planning
and 12.519649 accumulated construction-planner seconds. Its retained current-cash
DTO supplies the portable fixture. AUTO385 shows the same pattern:
16.172550 / 13.019311 / 12.346492 seconds. Multiple internal planning passes can
run the construction consumer within one ordinary AUTO.

This establishes an unnecessary history-copy path; it does not establish that
all 327.744495 seconds are Python copying. Current-cash execution also waits for
Native. No cash-specific inner send/wait or snapshot timer exists in this window.
Likewise, declarable whole-query residual is not a measured Native CPU floor.

## Useful next measurements

The three largest grounded areas are construction planning, declarable execution
outside normal planning (157.246476 seconds), and persistence. The existing
full-state persistence stage totals 143.703372 seconds, including
132.242241 seconds in temporary-file writes; it overlaps action and SAVE paths.
For a future SDK, four narrow cash-query timers (before snapshot, send/wait,
after snapshot, normalize) would distinguish the remaining costs without adding
queries. P06 latency and throughput must be measured from its actual completed
responses; no speedup is claimed before that observation.

A bounded offline object-copy surrogate using 4000 history rows, each with eight
nested records, measured median 0.200364 seconds before and 0.000133 seconds after.
This is Python-copy timing with a fake endpoint, not CK3 performance or a Java
comparison. The external actual-packet equivalence run passed 18 focused checks.

## Receipts, cooldowns and saving

P04's 48 construction receipt observations refer to five previous action IDs:
47 were in progress and one completed. No receipt performed a new submission.
The accounting recorded 29 construction-material observations, two new starts
and one first completion; material observation counts are not buildings completed.

All ten SAVEs bind to six life-advance calendar boundaries, one council material
receipt, two new construction-start receipts (AUTO176 and AUTO530), and the first
construction completion (AUTO408). The current 90-day calendar helper already
excludes generic construction-material observations from immediate critical SAVE.
No extra SAVE from a progress-only construction receipt was found.

P05 AUTO32/34/36/38, mentioned by Root, observe four different existing building
action IDs at the same date. All report in-progress and
`selected_query_performed_new_submission=False`; they are not four submissions
or completions. Their whole AUTO times alone do not isolate the newly installed
process-identity cache's benefit.

Actual P04 plans show the existing six-domain three-no-action-check / 30-day
cooldowns (construction 64 skips, council 229, lifestyle/crown/feast 224 each,
ransom 107). Declaration cooldown was active in 130 of 359 returned AUTO bodies,
including AUTO77 with exactly 30 days remaining. Family cooldown was inactive in
the 76 bodies that included its state; this window does not demonstrate an active
family cooldown. The fix preserves these rules.

## Validation and provenance

Portable tests:
`python -B -X utf8 -m unittest discover -s ck3_autonomous_player/tests/unit -p test_construction_current_frame_history_free.py -v`

Six tests cover the original retained cash packet, no transcript export,
unchanged single request and before/after reads, stale frame/actor/event guards,
permission and initial revision guards, legacy fallback, and wartime binding.
The endpoint is simulated throughout; no Game, SDK or desktop operation occurs.

External candidate: `construction-unused-history-fix01/DELIVERY.json`,
SHA256 `35910aca76ef42a180b424a92a5c394f85d23406d316831d3eaa3a026fe1f9e7`.
P05-base leaves: cash `a152772ad27acc4115610ceaa90b236b1dcbce53ea37f5f6694d61807244c300`,
construction transport `c51d463f206fc4c05ded463aa97bc7392b0a4e7daf770a066348c72bc73ace8d`.
Durable W applies only the two performance hunks and preserves unrelated existing
source differences. Runtime freeze and actual deployment belong to Root.

Derived per-AUTO evidence is external `p04-closed-auto-cost-review01`.
It contains scalar summaries and exact original-response pins, not duplicated
raw Driver or full response payloads. Candidate/evidence review is due 2026-10-22;
retention beyond that needs the then-current integration/comparison purpose.
