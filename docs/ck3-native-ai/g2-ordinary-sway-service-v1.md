# Ordinary Sway in the complete planner

2026-10-16. Public source is wired and three portable integration compounds pass. This package does not install a running SDK or operate CK3. Original G2 remains M0–M7, **6/8**; M6/M7 remain in progress, with zero new game days or continuous-window credit.

## Source behavior

[Service](../../ck3_autonomous_player/src/xar_autoplayer/bridge/service.py) now obtains the normal selected plan before staging optional Sway. It captures a compact copy of the existing same-frame semantic and Root inputs inside the ordinary planner; no extra Root refresh, target sweep or Native query occurs there. Events, interactions, war actions and other selected work retain priority. Only a selected ordinary life-advance can stage Sway.

The [adapter](../../ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_sway_service_v1.py) runs outside the planning-view lock and after the existing before-submit decision hook. It reuses the public pure scheduler and existing formal consumer, UUID ledger, typed query/start, independent receipt, pending recovery and following/lifecycle writers. An actual new Start owns that turn; an unavailable/no-op/read-only observation obtains a fresh full ordinary plan and executes it, retaining the optional receipt and correct following-plan ownership. It does not use the bounded runner's forced checkpoint/break.

Pending recovery and applied observation are monthly. Two completed checks without a real operation enter 30-game-day cooldown. Nomination follows the current direct landed vassal frontier in its observed order, rotating fairly; it is not a native highest-value ranking or a gift score. Final terms, legality and the existing opinion policy remain with the original formal consumer. The lifecycle target predicate now accepts the same positive full32 CharacterIDs as that consumer.

The real family read-only retry can update the wrapper revision while retaining older captured optional inputs. Before any scheduler/ledger read, staging compares those two frames. A mismatch retains the current ordinary step without optional IO, state mutation or cooldown. It does not refresh Root to conceal the mismatch.

## Portable verification

[Three compounds](../../ck3_autonomous_player/tests/unit/test_ordinary_sway_service_v1.py) directly import current public Service and execute its complete normal planner, strategy, auto, formal consumer and following/lifecycle chain. There is no historical Git loader, source patching, replacement internal planner or external-drive fixture dependency.

The [compact fixture](../../ck3_autonomous_player/tests/fixtures/ordinary_sway_fullplanner_v1.json) pins six actual closed receipts, retaining the complete Root body and semantic shape. Capability lists and SAVE metadata are bounded projections. Peaceful/UI/cooldown variants, all Native execution/readback/completion and the family retry OS identity boundary are explicitly synthetic.

One new public integration run on source parent 09b83be4b46dc1938d05ccca65023905c99a8431 passed all three compounds in 0.133 seconds:

- Actual closed war Root preserves the prior selected war-window policy; synthetic peace performs one Start, independent readback, following consumption and monthly lifecycle observation.
- Two no-ops cause 30-day cooldown; absent Root preserves checkpoint history and ordinary progress.
- The real family failure/retry increments revision, then the old optional frame causes zero adapter input reads, no cooldown and a fresh ordinary advance.

This is the portable current-source adoption check for the already closed [V3 whole-planner evidence](g2-remaining-evidence-2026-10-16/SWAY-FULLPLANNER-VERIFICATION.json). Old scheduler, stock/parser, V1/V2 and terminal matrices were not replayed. A focused static-CI step covers this new file; the exact new commit's CI status is recorded separately.

## Remaining evidence

Current campaign Native Start, a matching useful terminal, independently named material benefit and ordinary play afterward remain unobserved for this hook. Source wiring and synthetic ACKs do not complete M6. No broader scheme family, new Native API, government qualification, throughput result or runtime deployment is included. Python/closed-JSON integration has no new Paradox corpus; open_kaishek is not applicable.

External preparation and original run receipts are under D:/codex-ck3-demos/2026-10-14-robert-30year/g2-m-gap-research-20261016. The research peak is limited to 1 MiB and subject to storage policy 1.0.0; recording capacity is separate.
