# Historical Unknown event replay: public DATA regression

The production change in `cf46f99926feb06ad067905aa366b37c5253adfa` replays the pinned historical Unknown knowledge input through the shared producer while ordinary planning continues to read current source knowledge. This test exercises that distinction with the original 14,197-byte canonical command.

The test starts with an empty isolated registry, then installs the frozen source-facts bytes and a declared fixture projection of only the registry entry's `source_facts.path`. The real trusted reader accepts the entry. Ordinary replay then changes 19 argument fields to the current known-source result, while historical replay still reproduces every canonical command byte after only the same `action_id` normalization used by the actual Root comparison. A subsequent ordinary replay remains known. An extra Unknown-audit field is rejected, and the restored historical input succeeds. All four input originals retain their exact bytes and hashes.

The first fixture compiled, then failed in `PlanningObservation` because the synthetic snapshot omitted its required `active_wars` array. That 1-error run remains preserved. The final fixture adds only the two required empty public-DATA arrays, `active_wars` and `player_armies`; these are synthetic fixture values and make no claim about the real world's wars or armies. The 77-byte delta leaves every canonical-command, audit, and original-input assertion unchanged.

The final verification compiled only the changed Test translation unit: exit 0, one class, 4.4918288 seconds. The same sole test method then passed: 1 test, 0 failures, 0 errors, 0 skips, process wall time 7.352654 seconds. The qualified 22 production classes were reused. No old method, production compilation, Native request, gameplay action, or GET ran. Both phases completed their strong post-fence and resource close.

The test reads only the configured pinned stock files through `TrustedEventSourceContext`, and writes only its temporary isolated state. Supply the five explicit `ck3.p064.canonical`, `.before`, `.entry`, `.facts`, and `.stock_root` properties recorded in the source index when running this external-data case. The test itself never writes the stock files or frozen originals.

This is a public producer DATA regression. It does not create a private Root issuer, prove the missing B21 produced vector, grant gameplay or SAVE authority, reproduce the entire live Runtime classpath, or measure performance. The unrelated P067 UNKNOWN action recovery remains separately constrained.

Exact source, first failure, final XML/stdout, resource and qualification pins are in [the evidence index](../maintenance/2026-11-06-historical-unknown-event-replay-data-test-sources.json).
