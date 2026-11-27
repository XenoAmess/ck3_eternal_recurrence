package org.xar.ck3.control.application.session;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.DateTimeException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.NavigableMap;
import java.util.Optional;
import java.util.TreeMap;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverActionHistoryState;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.ContinuityBatchJournal.RetainedReadDriver;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Replays historical Driver data from the authenticated imported successor and its canonical publications. */
final class CommittedImportedDriverHistory {
    private CommittedImportedDriverHistory() { }

    record Data(DriverSnapshotFacts.Known facts, ExactRef fullDriver, SemanticEvidence latestCycle) { }

    static Data read(Session same, CommittedImportedSettledFrontier.Data settled, OutcomeArchive archive) throws IOException {
        var historical = settled.history();
        var head = same.head();
        StrictJson.require(!head.snapshotNeedsRecovery() && head.indexRepairs().isEmpty()
                && ContinuityJson.same(head.state().toJson(), historical.current().toJson()),
                "committed imported Driver history requires its held settled Writer head");
        try {
            return archive.withSession(same).inSameGameHistoricalRecoveryScope(same, originals -> {
                var retained = readRebind(same, historical.original(), settled.owner(), originals);
                var pending = new HashMap<String, ActionReceipt>();
                var missing = new TreeMap<Long, ActionReceipt>();
                for (var action : settled.successorActions()) {
                    StrictJson.require(pending.putIfAbsent(action.command().actionId(), action) == null
                                    && missing.putIfAbsent(action.sequence(), action) == null,
                            "committed imported Driver requires unique successor actions");
                }
                var publications = new ArrayList<DriverActionHistoryState.Publication>();
                var actuals = new ArrayList<ActionReceipt>();
                SemanticEvidence latest = historical.original().archivedSemantic();
                for (var edge : historical.suffix()) {
                    switch (edge.kind()) {
                        case WriterContracts.DRIVER_ACTION_HISTORY_KIND -> {
                            var details = ContinuityJson.parseObject(edge.details(), ContinuityJson.LEDGER_MAX_BYTES);
                            var actual = pending.remove(StrictJson.text(details.get("action_id")));
                            StrictJson.require(actual != null && actual.sequence() <= edge.before().sequence(),
                                    "committed imported Driver publication has no unique settled successor action");
                            retained = ContinuityBatchJournal.retainCapturedAction(same, edge, retained,
                                    settled.canonicalActions(), originals, publications, actuals);
                            missing.remove(actual.sequence());
                        }
                        case WriterContracts.DRIVER_READ_HISTORY_KIND -> retained = ContinuityBatchJournal.retainCapturedRead(
                                same, settled.owner(), edge, retained, originals, List.of(), false);
                        case OrdinaryCycleTransitions.CYCLE_KIND -> {
                            var details = ContinuityJson.parseObject(edge.details(), ContinuityJson.LEDGER_MAX_BYTES);
                            if (!"SETTLE".equals(StrictJson.text(details.get("operation")))) continue;
                            requireCoverage(missing, edge.before().sequence());
                            latest = OrdinaryCycleTransitions.semanticFromJson(details.get("semantic"));
                            retained = retainSemantic(latest, retained, originals);
                        }
                        default -> {
                            // The settled frontier reader already authenticated the remaining Writer events.
                        }
                    }
                }
                requireCoverage(missing, head.state().sequence());
                DriverActionHistoryState.requireOriginals(same, publications, actuals, originals);
                StrictJson.require(latest.equals(settled.latestCycle()) && head.digest().equals(same.head().digest()),
                        "committed imported Driver lost the latest settled cycle or its held Writer head");
                return new Data(retained.facts(), retained.fullDriver(), latest);
            });
        } catch (UncheckedIOException failure) {
            throw failure.getCause();
        } catch (IllegalArgumentException | ArithmeticException | DateTimeException failure) {
            throw new IOException("invalid committed imported Driver history: " + failure.getMessage(), failure);
        }
    }

    static RetainedReadDriver readRebind(Session same, CommittedImportedRebindOriginal.Data original,
            SessionIdentity owner, OutcomeArchive originals) throws IOException {
        var seed = DriverSnapshotFacts.RestoreSeedSupplement.readAttachment(same, original.attachment(), owner);
        var semantic = original.archivedSemantic();
        var full = semantic.originalDriver();
        StrictJson.require(seed.fullDriver().equals(full),
                "committed imported REBIND SEM changed its attached full Driver");
        new NativeSemanticEvidenceVerifier((borrowed, ref, maximum) -> {
            StrictJson.require(borrowed == same && ref.bytes() <= maximum,
                    "committed imported REBIND SEM crossed its held Writer or original size");
            return ref.equals(semantic.originalNativePacket()) ? originals.loadNativeFrame(ref)
                    : originals.loadFullMaterial(ref).bytes();
        }).verify(same, owner, semantic);
        var driver = DriverStateSnapshot.decodeComplete(originals.loadFullMaterial(full).bytes());
        var stamp = new DriverSnapshotFacts.Stamp(seed.driverVersion(), seed.episodeEpoch(), owner.game(),
                driver.session().episodeRunId(), full.sha256());
        var facts = new DriverSnapshotFacts.Known(driver, stamp, seed.originalHistoryBasis(), List.of(),
                seed.auxiliary(), seed.loop(), Optional.empty());
        return retainSemantic(semantic, new RetainedReadDriver(facts, full), originals);
    }

    private static RetainedReadDriver retainSemantic(SemanticEvidence semantic, RetainedReadDriver previous,
            OutcomeArchive originals) {
        var full = semantic.originalDriver();
        var stamp = ContinuityJson.parseObject(originals.loadMaterial(semantic.driverStamp()).bytes(),
                ContinuityJson.DOCUMENT_MAX_BYTES);
        var expected = previous.facts().stamp();
        StrictJson.require(full.bytes() == previous.fullDriver().bytes() && full.sha256().equals(previous.fullDriver().sha256())
                && StrictJson.integer(stamp.get("driver_version"), 0, StrictJson.MAX_SAFE_INTEGER) == expected.driverVersion()
                && StrictJson.integer(stamp.get("episode_epoch"), 0, StrictJson.MAX_SAFE_INTEGER) == expected.episodeEpoch(),
                "committed imported SEM differs from the replayed complete Driver and version");
        var captured = ContinuityBatchJournal.captureSettledSemanticBody(semantic, originals);
        return ContinuityBatchJournal.retainSettledCapabilities(semantic, previous, originals, captured, true);
    }

    private static void requireCoverage(NavigableMap<Long, ActionReceipt> missing, long through) throws IOException {
        var earliest = missing.firstEntry();
        if (earliest != null && earliest.getKey() <= through) {
            var action = earliest.getValue();
            throw new IOException("committed imported Driver is missing its ACTION publication for "
                    + action.command().actionId() + ":" + action.sequence());
        }
    }
}
