package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence;
import org.xar.ck3.control.application.driver.DriverActionHistoryState;
import org.xar.ck3.control.application.session.SessionPorts.JournalKind;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.WriterContracts.HistoricalTransition;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Original same-Game action and cycle DATA at a settled batch boundary on an imported replacement. */
final class CommittedImportedSettledFrontier {
    private CommittedImportedSettledFrontier() { }

    record Data(CommittedImportedRebindOriginal.Historical history, SessionIdentity owner, G2Source source,
            String batchPrefix, long nextBatchSequence, List<String> consumedSuccessorBatches,
            ActionReceipt retiredResume, List<ActionReceipt> canonicalActions, List<ActionReceipt> successorActions,
            SemanticEvidence latestCycle, List<ConfirmedSave> confirmedSaves, Optional<String> openConfirmedSaveBatch,
            long committedSavedDays) {
        Data {
            consumedSuccessorBatches = List.copyOf(consumedSuccessorBatches);
            canonicalActions = List.copyOf(canonicalActions);
            successorActions = List.copyOf(successorActions);
            confirmedSaves = List.copyOf(confirmedSaves);
            openConfirmedSaveBatch = Objects.requireNonNull(openConfirmedSaveBatch);
        }
        CheckpointPair savedPair() {
            return confirmedSaves.isEmpty() ? history.original().pair() : confirmedSaves.getLast().pair();
        }
        long savedThroughSequence() {
            return confirmedSaves.isEmpty() ? history.original().rebind().sequence() : confirmedSaves.getLast().edge().sequence();
        }
    }

    record ConfirmedSave(HistoricalTransition edge, CheckpointPair pair, ActionReceipt receipt,
            ActionReceipt publisher, ContinuityBatchJournal.RetainedObservation observed) { }

    static Data read(Session same, CommittedImportedRebindOriginal.Historical history,
            OrdinaryCycleTransitions transitions, ActionPorts.OutcomeArchive archive) throws IOException {
        var head = same.head();
        var original = history.original();
        var rebounded = original.rebind().after();
        var owner = original.recoveryBasis().successor();
        var current = head.state();
        StrictJson.require(!head.snapshotNeedsRecovery() && head.indexRepairs().isEmpty()
                && ContinuityJson.same(current.toJson(), history.current().toJson())
                && head.documents().contains(original.rebind().eventPin()) && current.status() == ContinuityState.Status.RUNNING,
                "settled imported successor requires its actual held post-REBIND frontier");
        var boundary = rebounded.toJson().path(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
        StrictJson.require(JournalKind.BATCH_INTERRUPTED.name().equals(StrictJson.text(boundary.get("boundary")))
                && original.recoveryBasis().departed().equals(OrdinaryCycleTransitions.sessionFromJson(boundary.get("session"))),
                "settled imported successor lost its original interrupted batch");
        String lastDeparted = StrictJson.text(boundary.get("batch_id"));
        int separator = lastDeparted.lastIndexOf('-');
        StrictJson.require(separator > 0 && lastDeparted.substring(separator + 1).matches("0|[1-9][0-9]{0,15}"),
                "settled imported successor has no exact inherited batch prefix and sequence");
        String prefix = lastDeparted.substring(0, separator);
        long next = Math.addExact(Long.parseLong(lastDeparted.substring(separator + 1)), 1);
        StrictJson.safe(next, 1);
        long savedTicks = Math.subtractExact(rebounded.settledDateRaw(), rebounded.origin().startDateRaw());
        StrictJson.require(savedTicks >= 0 && savedTicks % 24 == 0 && rebounded.settledDateRaw()
                == original.pair().frame().frame().identity().dateRaw().longValueExact(),
                "settled imported successor requires its actual physical saved frontier");

        var currentRow = current.toJson();
        var terminalCycleRecord = ExactRef.fromJson(currentRow.path(OrdinaryCycleTransitions.STATE_FIELD).get("head"));
        return transitions.withLocked(same, () -> archive.withSession(same)
                .inSameGameHistoricalRecoveryScope(same, originals -> {
            var replay = new Replay(same, transitions, originals, rebounded, owner, prefix, next,
                    original.archivedSemantic().frame(), terminalCycleRecord, original.pair());
            var cursor = rebounded;
            var captured = new HashSet<>(head.documents());
            for (var edge : history.suffix()) {
                StrictJson.require(edge.sequence() == Math.addExact(cursor.sequence(), 1)
                        && captured.contains(edge.eventPin()) && ContinuityJson.same(cursor.toJson(), edge.before().toJson()),
                        "settled imported successor suffix crossed its original writer edge");
                requireSameImportedOrigin(rebounded, edge.after(), original.tombstone().reference(), owner);
                replay.replay(edge);
                cursor = edge.after();
            }
            String terminal = currentRow.path(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD).path("boundary").asText();
            boolean closedBatch = replay.openBatch == null
                    && (JournalKind.BATCH_FINISHED.name().equals(terminal) || JournalKind.BATCH_DEFERRED.name().equals(terminal));
            boolean confirmedSaveTail = replay.openBatch != null && JournalKind.SAVE_CONFIRMED.name().equals(terminal)
                    && !replay.saves.isEmpty() && replay.saves.getLast().edge().sequence() == current.sequence();
            StrictJson.require(replay.terminalCycle != null && replay.latestCycle == replay.terminalCycle.semantic()
                    && !replay.used.isEmpty() && (closedBatch || confirmedSaveTail)
                    && cursor.sequence() == current.sequence() && ContinuityJson.same(cursor.toJson(), current.toJson()),
                    "settled imported successor requires a completed cycle and its closed batch or final confirmed SAVE");
            var canonical = ContinuityActionJournal.receipts(current, originals);
            var unresolved = canonical.stream().filter(action -> !action.settled()).toList();
            StrictJson.require(unresolved.equals(List.of(replay.retiredResume))
                    && canonical.size() == replay.inherited.size() + replay.successor.size()
                    && canonical.containsAll(replay.inherited) && canonical.containsAll(replay.successor.values())
                    && ContinuityActionJournal.blockingUnresolved(same, head, originals, owner, canonical).isEmpty(),
                    "settled imported successor cannot discard an unresolved action or change its inherited action cut");
            var successor = List.copyOf(replay.successor.values());
            for (var root : ContinuityBatchJournal.ordinaryCycleRoots(successor)) {
                if (ordinarySave(root)) {
                    StrictJson.require(replay.saves.stream().anyMatch(save -> save.receipt().equals(root)),
                            "settled imported successor SAVE lacks its exact canonical confirmation");
                } else if (root.visibleGameplay() || root.eligibleAdvance())
                    StrictJson.require(replay.closedCycles.contains(originals.receiptReferenceOf(root)),
                            "settled imported successor gameplay lacks its original completed cycle");
            }
            StrictJson.require(transitions.importedTerminalCycleProof(same, owner, replay.terminalCycle.receipt(),
                    replay.terminalCycle.semantic()).isPresent()
                    && head.digest().equals(same.head().digest()),
                    "settled imported successor changed its completed branch or actual held head");
            long currentSavedTicks = Math.subtractExact(current.settledDateRaw(), rebounded.origin().startDateRaw());
            StrictJson.require(currentSavedTicks >= savedTicks && currentSavedTicks % 24 == 0,
                    "settled imported successor has invalid confirmed saved days");
            return new Data(history, owner, replay.source, prefix, replay.nextBatchSequence, replay.used,
                    replay.retiredResume, canonical, successor, replay.latestCycle, replay.saves,
                    confirmedSaveTail ? Optional.of(replay.openBatch) : Optional.empty(), currentSavedTicks / 24);
        }));
    }

    private static void requireSameImportedOrigin(ContinuityState rebind, ContinuityState current, ExactRef origin, SessionIdentity owner) {
        var original = rebind.toJson(); var state = current.toJson();
        StrictJson.require(current.status() == ContinuityState.Status.RUNNING
                && rebind.origin().equals(current.origin())
                && ContinuityJson.same(owner.game().toJson(), state.get("game_binding"))
                && ContinuityJson.same(origin.toJson(), state.get(WriterContracts.ORDINARY_IMPORTED_CYCLE_ORIGIN_FIELD))
                && Objects.equals(original.get(SavedContinuityBootstrap.FIELD), state.get(SavedContinuityBootstrap.FIELD))
                && Objects.equals(original.get("last_current_saved_cold"), state.get("last_current_saved_cold")),
                "settled imported successor changed the actual saved frontier, owner or imported origin");
    }

    private static void requireUnchangedPhysicalFrontier(HistoricalTransition edge) {
        var before = edge.before().toJson();
        var after = edge.after().toJson();
        StrictJson.require(edge.before().settledCycles() == edge.after().settledCycles()
                && edge.before().settledDateRaw() == edge.after().settledDateRaw()
                && Objects.equals(before.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD), after.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD))
                && Objects.equals(before.get(SavedCheckpointMaterialEvidence.FIELD), after.get(SavedCheckpointMaterialEvidence.FIELD)),
                "settled imported successor changed the actual saved frontier, owner or imported origin");
    }

    private static boolean ordinarySave(ActionReceipt action) {
        return action.command().operation().value().equals("save-checkpoint");
    }

    private record TerminalCycle(ActionReceipt receipt, SemanticEvidence semantic) { }

    private static final class Replay {
        private final Session same;
        private final OrdinaryCycleTransitions transitions;
        private final ActionPorts.OutcomeArchive archive;
        private final SessionIdentity owner;
        private final String batchPrefix;
        private final ExactRef terminalCycleRecord;
        private final List<ActionReceipt> inherited;
        private final Set<String> oldIds;
        private final ActionReceipt retiredResume;
        private final LinkedHashMap<String, ActionReceipt> successor = new LinkedHashMap<>();
        private final Set<ExactRef> closedCycles = new HashSet<>();
        private final Set<String> openActions = new HashSet<>();
        private final List<String> used = new ArrayList<>();
        private final List<ConfirmedSave> saves = new ArrayList<>();
        private final LinkedHashMap<String, ActionReceipt> savePublishers = new LinkedHashMap<>();
        private CheckpointPair savedPair;
        private long nextBatchSequence;
        private String openBatch;
        private long openedAtSequence;
        private long lastActionSequence;
        private ExactRef pendingCycle;
        private SemanticEvidence latestCycle;
        private TerminalCycle terminalCycle;
        private ObservationIdentity observed;
        private G2Source source;

        private Replay(Session same, OrdinaryCycleTransitions transitions, ActionPorts.OutcomeArchive archive,
                ContinuityState rebind, SessionIdentity owner, String prefix, long next, ObservationIdentity original,
                ExactRef terminalCycleRecord, CheckpointPair importedPair) {
            this.same = same; this.transitions = transitions; this.archive = archive; this.owner = owner;
            batchPrefix = prefix; nextBatchSequence = next; observed = original;
            this.terminalCycleRecord = terminalCycleRecord;
            this.savedPair = importedPair;
            inherited = ContinuityActionJournal.receipts(rebind, archive);
            oldIds = new HashSet<>(inherited.stream().map(action -> action.command().actionId()).toList());
            var pending = inherited.stream().filter(action -> !action.settled()).toList();
            StrictJson.require(pending.size() == 1 && pending.getFirst().state() instanceof ActionState.Unknown
                    && pending.getFirst().command().operation().value().equals("resume-map")
                    && pending.getFirst().ack().filter(org.xar.ck3.control.application.action.NativeActionPort.AckReceived::nativeOk).isPresent(),
                    "settled imported successor lost its one carried positive-ACK UNKNOWN original");
            retiredResume = pending.getFirst();
        }

        private void replay(HistoricalTransition edge) throws IOException {
            var request = new WriterContracts.Request(edge.kind(), edge.details(), List.of());
            StrictJson.require(request.identity().equals(edge.eventIdentity()), "settled imported successor event identity differs");
            var details = request.detailsObject();
            if (!OrdinaryCycleTransitions.BATCH_KIND.equals(edge.kind()) || !JournalKind.SAVE_CONFIRMED.name().equals(details.path("boundary").asText()))
                requireUnchangedPhysicalFrontier(edge);
            switch (edge.kind()) {
                case OrdinaryCycleTransitions.BATCH_KIND -> batch(edge, details);
                case WriterContracts.ACTION_LIFECYCLE_KIND -> action(edge, details);
                case OrdinaryCycleTransitions.CYCLE_KIND -> cycle(edge, request, details);
                case WriterContracts.DRIVER_ACTION_HISTORY_KIND -> driverAction(edge, request, details);
                case WriterContracts.DRIVER_READ_HISTORY_KIND -> driverRead(edge, details);
                case DomainBodies.IMPORT_KIND -> same.requireDomainImportContinuation(edge.before().sequence(),
                        ContinuityJson.digest(edge.before().toJson()), edge.sequence(), ContinuityJson.digest(edge.after().toJson()));
                default -> throw new IOException("unsupported canonical event in settled imported successor batch: " + edge.kind());
            }
        }

        private void batch(HistoricalTransition edge, ObjectNode details) throws IOException {
            var boundary = JournalKind.valueOf(StrictJson.text(details.get("boundary")));
            String id = StrictJson.text(details.get("batch_id"));
            if (boundary == JournalKind.SAVE_CONFIRMED) {
                confirmSave(edge, details, id);
                return;
            }
            StrictJson.require(owner.equals(OrdinaryCycleTransitions.sessionFromJson(details.get("session")))
                    && details.path("checkpoint_pair").isNull() && details.path("completed_cycle_proof").isNull()
                    && pendingCycle == null && openActions.isEmpty(),
                    "settled imported successor cannot cross an unfinished action, cycle, owner or new SAVE");
            if (boundary == JournalKind.BATCH_STARTED) {
                StrictJson.require(openBatch == null && id.equals(batchPrefix + "-" + nextBatchSequence),
                        "settled imported successor skipped an actual batch identity");
                openBatch = id;
                openedAtSequence = edge.sequence();
                used.add(id);
                nextBatchSequence = Math.addExact(nextBatchSequence, 1);
            } else {
                boolean actionlessDeferred = boundary == JournalKind.BATCH_DEFERRED && lastActionSequence < openedAtSequence;
                StrictJson.require((boundary == JournalKind.BATCH_FINISHED || actionlessDeferred) && id.equals(openBatch),
                        "settled imported successor requires its exact finished or actionless deferred batch");
                openBatch = null;
            }
            requireReduction(edge, OrdinaryCycleTransitions.replayCommittedBatchMetadata(edge.before(), owner, id, boundary, edge).toJson());
        }

        private void confirmSave(HistoricalTransition edge, ObjectNode details, String id) throws IOException {
            StrictJson.require(id.equals(openBatch) && pendingCycle == null && openActions.isEmpty() && latestCycle != null,
                    "settled imported successor SAVE requires its actual open batch and completed cycle");
            var cycle = edge.before().toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD);
            var receipt = ContinuityBatchJournal.requireHistoricalConfirmedSave(transitions, same, edge, owner, List.copyOf(successor.values()), archive,
                    latestCycle, StrictJson.integer(cycle.get("completed_cycles"), 0, StrictJson.MAX_SAFE_INTEGER),
                    ExactRef.fromJson(cycle.get("head")));
            var pair = CheckpointPairCodec.decode(ContinuityJson.canonical(details.get("checkpoint_pair")));
            StrictJson.require(receipt.sequence() > openedAtSequence && pair.lineageId().equals(savedPair.lineageId())
                    && saves.stream().noneMatch(save -> save.receipt().equals(receipt))
                    && edge.after().settledDateRaw() >= edge.before().settledDateRaw()
                    && edge.after().settledCycles() >= edge.before().settledCycles(),
                    "settled imported successor SAVE crossed its original lineage, batch or physical frontier");
            requireObservedContinuation(pair.frame());
            ContinuityBatchJournal.requireCommittedImportedMaterial(transitions, same, edge, details, owner, pair, receipt, archive);
            var evidence = ContinuityBatchJournal.readCommittedImportedSave(same, edge, owner, pair, receipt,
                    savePublishers.get(receipt.command().actionId()), archive);
            saves.add(evidence);
            savedPair = pair;
            observed = pair.frame();
        }

        private void action(HistoricalTransition edge, ObjectNode details) throws IOException {
            StrictJson.object(details, Set.of("evidence_id", "source", "receipt_ref"));
            StrictJson.require(openBatch != null && pendingCycle == null,
                    "settled imported successor action is outside its open batch or crossed a pending cycle");
            var ref = ExactRef.fromJson(details.get("receipt_ref"));
            var record = archive.loadRecord(ref);
            var receipt = record.receipt(); var command = receipt.command();
            StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay && command.origin().machineId().equals(owner.machineId())
                    && command.origin().game().equals(owner.game()) && command.sessionId().equals(owner.sessionId())
                    && receipt.sequence() == edge.sequence() && !oldIds.contains(command.actionId())
                    && record.previous().equals(ContinuityActionJournal.recordHead(edge.before()))
                    && (command.actionId() + ":" + receipt.sequence()).equals(StrictJson.text(details.get("evidence_id")))
                    && ContinuityJson.same(ProposalLifecycleCodec.source(command.source()), details.get("source")),
                    "settled imported successor action changed the owner, original chain or historical reservation");
            if (source == null) source = command.source();
            StrictJson.require(source.equals(command.source()), "settled imported successor crossed original action source");
            var previous = Optional.ofNullable(successor.get(command.actionId()));
            if (previous.isEmpty()) requireObservedContinuation(command.before());
            ActionTransitions.validate(previous, command, receipt.bodySha256(), receipt.state());
            if (ordinarySave(receipt) && receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED)
                savePublishers.put(command.actionId(), previous.orElseThrow());
            successor.put(command.actionId(), receipt);
            lastActionSequence = receipt.sequence();
            if (receipt.settled()) openActions.remove(command.actionId());
            else openActions.add(command.actionId());
            var next = edge.before().toJson();
            next.set(ContinuityActionJournal.STATE_FIELD, ref.toJson());
            requireReduction(edge, next);
        }

        private void cycle(HistoricalTransition edge, WriterContracts.Request request, ObjectNode details) throws IOException {
            StrictJson.require(openBatch != null && openActions.isEmpty()
                    && owner.equals(OrdinaryCycleTransitions.sessionFromJson(details.get("session"))),
                    "settled imported successor cycle crossed the action or batch owner");
            var receiptRef = ExactRef.fromJson(details.get("receipt_ref"));
            var receipt = archive.loadReceipt(receiptRef);
            StrictJson.require(receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED && !ordinarySave(receipt)
                    && receipt.equals(successor.get(receipt.command().actionId()))
                    && receipt.sequence() > openedAtSequence
                    && receiptRef.equals(archive.receiptReferenceOf(receipt)),
                    "settled imported successor cycle lacks its exact current action receipt");
            switch (StrictJson.text(details.get("operation"))) {
                case "RETAIN" -> {
                    StrictJson.require(pendingCycle == null && !closedCycles.contains(receiptRef),
                            "settled imported successor retained an action or cycle twice");
                    pendingCycle = receiptRef;
                }
                case "SETTLE" -> {
                    StrictJson.require(receiptRef.equals(pendingCycle) && closedCycles.add(receiptRef),
                            "settled imported successor must settle the exact retained cycle");
                    var recordRef = ExactRef.fromJson(details.get("cycle_record_ref"));
                    var original = archive.loadMaterial(recordRef);
                    StrictJson.require(original.equals(new RawJson(ContinuityJson.canonical(details.get("cycle_record")))),
                            "settled imported successor cycle record differs from its exact archive");
                    var semantic = OrdinaryCycleTransitions.semanticFromJson(details.get("semantic"));
                    if (recordRef.equals(terminalCycleRecord)) {
                        StrictJson.require(terminalCycle == null, "settled imported successor replayed its retained cycle twice");
                        // The held terminal proof reads these originals at the final frontier. Both
                        // semantic contracts must use that verification before the replay returns.
                        terminalCycle = new TerminalCycle(receipt,semantic);
                    } else {
                        transitions.requireImportedCycleSemantic(same, owner, receipt, semantic);
                    }
                    requireObservedContinuation(semantic.frame());
                    observed = semantic.frame();
                    latestCycle = semantic;
                    pendingCycle = null;
                }
                default -> throw new IOException("unsupported ordinary cycle during settled imported successor replay");
            }
            requireReduction(edge, transitions.reduce(edge.before(), request).toJson());
        }

        private void requireObservedContinuation(ObservationIdentity current) {
            var before = observed.frame(); var after = current.frame();
            StrictJson.require(observed.machineId().equals(current.machineId()) && observed.game().equals(current.game())
                    && observed.observationVersion() == current.observationVersion()
                    && before.episodeRunId().equals(after.episodeRunId())
                    && before.identity().player().equals(after.identity().player())
                    && before.identity().dateRaw().compareTo(after.identity().dateRaw()) <= 0
                    && before.identity().nativeRevision().compareTo(after.identity().nativeRevision()) <= 0
                    && before.revision().compareTo(after.revision()) <= 0,
                    "settled imported successor observation regressed its original REBIND or completed cycle");
        }

        private void driverRead(HistoricalTransition edge, ObjectNode details) {
            StrictJson.require(openBatch != null && openActions.isEmpty() && pendingCycle == null
                    && "xar.driver-read-publication/v1".equals(StrictJson.text(details.get("schema"))),
                    "settled imported successor READ requires the ordinary typed publication in an idle open batch");
            var readSource = org.xar.ck3.control.g2.common.G2Wire.source(details.get("source"));
            if (source == null) source = readSource;
            StrictJson.require(source.equals(readSource), "settled imported successor READ crossed the original business source");
            var next = edge.before().toJson();
            next.set(WriterContracts.DRIVER_READ_HISTORY_FIELD, details);
            requireReduction(edge, next);
            // The combined recovery reader must replay the exact typed receipts and complete before/after Driver.
        }

        private void driverAction(HistoricalTransition edge, WriterContracts.Request request, ObjectNode details) throws IOException {
            var actual = successor.get(StrictJson.text(details.get("action_id")));
            StrictJson.require(openBatch != null && actual != null && actual.settled(),
                    "settled imported successor Driver ACTION lacks the actual settled current batch action");
            var recorded = DriverActionHistoryState.decode(details, actual);
            StrictJson.require(recorded.predecessor().equals(ContinuityJson.digest(edge.before().toJson())),
                    "settled imported successor Driver ACTION changed its predecessor");
            DriverActionHistoryState.requireReduction(edge.before(), edge.after(), request, true);
            DriverActionHistoryState.requireOriginal(same, recorded, actual, archive);
        }
    }

    private static void requireReduction(HistoricalTransition edge, ObjectNode reduced) {
        reduced.put("sequence", edge.sequence()).put("last_event_identity", edge.eventIdentity());
        StrictJson.require(ContinuityJson.same(reduced, edge.after().toJson()),
                "settled imported successor event differs from its canonical reducer");
    }
}
