# R213 regular-core explicit null, and the next genuine opportunity

R213 source/runtime was `3661e495bc45490238992d3f2850e75558566922`, native a36/exact CK3 1.20.0.4. The one-day R06 episode ran Mar4→Mar5, raw53148408→53148432, Army0/fullCArmy0 at2170. Native Can and chunkCan were true and the conditional q target was positive; those are eligibility/prepared-request facts, not the dispatcher calling the core. Root's physical inventory summary remained37 unique slots and6674 soldiers. No instruction-local ADD is qualified.

## What the actual wire says

This was an explicit native JSON null, not a missing/wrong key or a FullArmy normalization loss. Query48 (`step-201-de7204724cc2`, baseline native137) and query49 (`step-208-5c6e98903bb9`, after native140) both contain the exact literal `"actual_army_regular_core_observations_v1": null` in their immutable native response prefixes. The field begins at response-relative byte3135 in both. Retained request lines prove `army_ids:[0]` and `army_strengths_profile:"observed_history_full_v1"`.

The portable cuts retain only8192 response-prefix bytes per query plus each305B request line. Whole response hashes were reused from the existing FullArmy proofs, not recalculated. They are provenance references, not a new whole-file verification. Initial discovery additionally read128KiB at each response's start and end:524288B total. No full10MB response or25MB arrival result was parsed/hashed in this investigation. The exact small156680B R06 result and its original refs remain the authoritative window metadata.

`army_strengths_profile_contract.py` requires all nine retained keys in observed_history_full_v1; ordinary_core_v1 intentionally omits them. `war_contract.py` explicitly assigns every present family through `normalize_army_observed_phase_family_12004`; that function returns None unchanged when input is null. `FullArmyResultClient.normalized_full` expands shared inputs, validates the echoed profile and applies this production row normalizer. It does not silently delete the core field.

## Why installed and null can coexist

`ReadSampledArmyRegularCoreJournal12004` in army_regular_core_passive_12004.cpp:792 first returns nullopt when sampling is not readable or qualified_records is0. Qualified means observed plus original_called plus original_returned (52–58). The hook can retain an unqualified invocation; Publish587–597 assigns its sequence whenever its permit can publish. Thus an enabled/installed observer alone does not imply an exported qualified record.

The serializer in army_observed_phase_query_12004.hpp:113 subsequently filters the retained journal by **captured entry** Army-refresh occurrences, matching resolved_full_id against the queried full CArmy ID. A filtered empty vector is explicitly serialized as null. A query-time roster is not used to repair missing historical membership. Therefore null can mean no qualified retained core journal, or no matching retained entry for this subject. The separate sampling query reports actual retained/qualified counts.

R213's before-day ON readback proves regular_core installed/available/capture=true, epoch3, retained0, qualified0, readiness awaiting_sample. It did not retain a second enabled sampling readback after the day and before OFF/clear. The cleanup OFF query then proves counters cleared; it cannot reconstruct the previous enabled window. Consequently this episode cannot exclusively distinguish no core publication from retained-but-unqualified or unmatched core records. The exported field itself, its producer and the normalization behavior are closed facts; no missing key is being left unexplained.

Natural-phase sampling OFF is not the cause of losing the parent TLS identity. `InvokeArmyNaturalPhaseScope12004` constructs observed phase, manager/game/date/event and roster at151–185 outside the sampling permit branch, installs it in TLS during the original call, and the regular-core child copies that active scope. It is not necessary to enable every observation family merely to supply the child's genuine parent.

## The core is not a daily ADD promise

The hook observes only2A98AC0 at literal parent return2A9A8E2. Its actual4 post-date caller2A9A570 saves GameState+C0 at2A9A655, masks02 at2A9A65D, tests the saved value at2A9A8D5 and conditionally calls2A98AC0 at2A9A8DD. This is separate from unsigned storedD%30 Army supply buckets and the unconditional daily assault call.

The exact4 calendar producer is already closed in `native71-calendar-month-flag-12004.md`: actual229C540 prefix344B, SHA3895e9d1054d97f41460e3225cd026c4713ea9f409769d198851b4f2070e9e6b. It derives tomorrow's native DOM using the actual4 tables, clears the previous mask02 at229C676, selects02 only for DOM0 and stores the BYTE at229C68D. This is an actual native DOM0 predicate, not a free-standing claim that every displayed first day must yield ADD.

The R213 captured before-day current C0 is0/mask02false. That is current input, not the historical register from an already-run future callback. Mar4→5 is not a source-derived next-month opportunity merely because q1 and Can are true. A fresh Mar5 normal S0 has Apr1/raw53149080 as the next calendar candidate,27 exact days later; stage26 days to Mar31/raw53149056, then independently read the already-published `source_derived_next_daily_supply_frame_inputs_v1.source_derived_next_calendar_day_u8` with its ready/full64/day provenance and require actual nextCalendarDay0 before arming the one-day observation. This package did not extract that calendar child from the large current response, and grants it no current ready credit.

At that actual paused pre-opportunity frame, recheck same identity/location/route/eligibility/prepared operands, enable only scoped regular_core for the actual full CArmy ID, and independently read ON/epoch/empty baseline. Advance one day with the existing unique clock owner. After the full result and **before OFF**, independently query the existing all-family sampling status once. Feed both actual ON query results and the actual full row to the new pure classifier. Then use existing physical/core projectors on retained events and preserve all retention/provenance gaps. No future callback, positive q, ADD or troop increase is promised.

## Minimal reusable source delta

`army_regular_core_capture_status_12004.py` is a new pure bridge helper. It distinguishes full-profile missing key, explicit null, ordinary not_requested, missing after-readback, cleared/changed epoch, no retained publication, retained unqualified records and no exported subject match. It calls the existing strict sampling and core-family normalizers and grants no callback/ADD credit. No native change, new query, flag, CMake target or native build is required.

The next actor needs only this read-only insertion after the post-day full and before any OFF call:

```python
after_sampling = sampling(None, 'all')  # existing actual query helper
capture_status = classify_regular_core_capture_window_12004(
    after['army'], profile='observed_history_full_v1',
    before_sampling=result['sampling_ON'], after_sampling=after_sampling)
client.checkpoint('R06-CORE-CAPTURE-STATUS', capture_status)
```

It must preserve the actual readback, not synthesize it from the eventual cleanup counters. This is a source integration contract for the next actor; the old R213 execution and old source are not rewritten.

One focused compound actually passed: both original null byte cuts, production profile/family/sampling consumers, new classifier, actual missing-after status and synthetic retained0/unqualified/subject-mismatch/post-OFF/missing-key counterexamples. The profile wrapper is explicitly minimal synthetic DTO; it is not a reconstructed complete Driver packet. Existing consumer/native matrices were not rerun. `verify_tiny.py` is a standalone stdlib byte-cut verifier.

Video boundary: safe to say the observer was installed/enabled, the one actual day completed, the physical total stayed unchanged and native exported null. Unsafe to say native refill was disabled, no native core invocation happened, the normalizer lost an event, q1 guaranteed an ADD, or a payment/cadence was proved. Research/business/dynamic credit is not advanced by this diagnostic package.
