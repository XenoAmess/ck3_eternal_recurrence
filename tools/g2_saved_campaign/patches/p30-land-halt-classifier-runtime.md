# P30 land-route Halt classification archive

The portable module requires a `bind_gameplay_frame(body, *, initial_frame, game_pid)` callback. Supply the existing reviewed gameplay-start validator; it must reject a mismatched Game, actor, episode, date, or source frame. Returning a bare unvalidated body is not an integration.

Dispatch this helper before the ordinary classifier and delegate unchanged when it returns `None`. A successful native Halt ACK remains `unsafe_route_halt_submitted_pending`; the full starting route tuple must reach the existing independent readback watcher. It grants no stopped-army, contact-free, or business result. The exact native pre-submit validator veto returns `halt_validator_rejected_route_retained_observed` with zero action/business/date credit; it never becomes an accepted Halt. The two subsequent one-day observation phases use the existing exact-day clock classifier without a new timing or contact-free contract.

[p30-land-halt-classifier-runtime.patch](p30-land-halt-classifier-runtime.patch) preserves the complete deployed narrow delta from runtime base cea62c06 to de0077f8. It is historical external queue integration, not a patch to a general public runner. The [portable module](../land_route_halt_outcome.py) replaces one global binding dependency with an injected callback and corrects the CUnit range to include zero. This compatibility correction is covered by an Army 0 fixture and has not changed the live de0077 classifier.

The private production tests exercised SDK30 Service.auto_turn → Driver.execute_step → the real queue AST loader. The portable tests below use explicit synthetic packets and test classification only. Neither fixtures nor the source archive claim a new native action, replay, or date advance. No SDK namespace import is needed by the portable module. A deployment that uses the private AST loader must add the helper through an explicit supported wrapper; do not rely on a dynamically assigned alias being loaded.

Run from the public repository root after copying only the two portable files:

`python -B -m unittest discover -s tests/unit -p test_land_route_halt_outcome.py -v`

Public common-runner integration and live Army 0 execution remain unverified. No complete runtime classifier, machine paths, PID, UUID, or frozen owner metadata is part of the portable module or its fixtures.
