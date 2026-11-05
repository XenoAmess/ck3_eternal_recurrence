# Materialize the installed EVENT pair before history lookup (2026-11-05)

Original527 remains SETTLED/APPLIED, with no repeated control. Recovery38 passed the strict completed-EVENT batch admission and reached the real Controller and history publisher. It then failed in RootActionHistoryMaterialSourceFactory.captureActual before the effect-sidecar load: actualArchivedVerifier was queried before the operation had been materialized in the new catalog.

The registry's archived-verifier accessor only reads its map. Its existing actualActionBinding accessor runs the installed typed family decoder and retains both the action and its paired archived verifier. The EVENT family and its producer/decoder/verifier sources were already installed and declared; its constructor does not prepare, observe, query or dispatch a Native action.

One guarded lookup now precedes the original archived-verifier lookup. It runs only for the existing EVENT observer schema and the exact original positive1..999999999 option grammar. The actual installed decoder and factory still validate/materialize the pair. The later action lookup, Missing rejection, physical path and all non-EVENT lookup order remain unchanged. Root owner/Game/source/session, action/composite identity, full domain replay, producer source, compatible result/evidence and the previous fresh READ wrapper remain mandatory.

Necessary typing compiled one production TU successfully in9.3197984 seconds, producing ten SourceFile family classes with identical complete structure. Independent source review verified the single owned inverse. No new lazy-binding mirror test or old62 rerun was made: these do not exercise the private installed history consumer. Actual recovery39 history publication, cycle completion, LOOP and new SAVE days remain separate runtime acceptance.

Model63 returned a complete HTTP200/DONE JSON proposal in10.1360550 seconds, TTFT6.5819701, reported51029+589 tokens. Its narrow EVENT guard and lookup semantics match the independently completed owner change. The raw unified-diff headers required mechanical repair and were not applied or compiled; the owner candidate had already been written before consuming the full response. No literal model lines were copied, and no retry was made. The owner uses a fully qualified schema constant and an explanatory comment.

The change does not reopen527, replace its command/body/ACK/deadline, create a cycle or relax any verifier. Raw hosted test payloads remain D-only. See [the source and evidence index](../maintenance/2026-11-05-event-history-family-materialization-sources.json).

Later actual39 evidence: history ACTION528 and zero-day RETAIN529/SETTLE530 were committed. The remaining completion failure was a distinct Sway READ verifier consumer, addressed in [the next narrow wiring change](2026-11-05-sway-following-fresh-read-wiring.md). No ordinary LOOP or new SAVE acceptance follows from those committed cycle events.
