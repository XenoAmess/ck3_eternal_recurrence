package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.council.*;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** One held Council transaction: durable helper STATUS, later published frame, durable receipt query/STATUS. */
public final class NativeCouncilAssignmentEffects implements NativeEffectRegistry.Observer {
    public static final String REJECTION_SCHEMA = "xar.java.council-assignment-native-rejection/v1";
    public static final String SCHEMA = "xar.java.council-assignment-original-basis/v1";
    private final CouncilContinuationCoordinator continuation;
    private final CouncilContinuationPolicy policy;
    private final NativeEffectSnapshots snapshots;
    private final ActionPorts.OutcomeArchive archive;
    private final NativeEffectEvidence.FrameLoader frames;
    private final Supplier<ContinuityStorePort.Session> originalSession;
    private final Clock clock;
    private final int maximumContinuations;
    private static final String SEAT_SCHEMA = "xar.java.council-assignment-current-seat-basis/v1";
    private static final String TUPLE_SCHEMA = "xar.java.council-current-seat-observation/v1";
    @FunctionalInterface public interface RecoverySeatReader {
        List<PlanningReadReceipt> read(ContinuityStorePort.Session same,
                CouncilContinuationCoordinator.RecoveryOriginal original, GuardEvidence sameCaptureObservation,
                java.time.Instant deadline) throws IOException, InterruptedException;
    }
    private final RecoverySeatReader recoverySeats;
    private final NativeCouncilReadPort.ReplayConfiguration recoverySeatReplay;
    public NativeCouncilAssignmentEffects(CouncilContinuationCoordinator continuation, CouncilContinuationPolicy policy,
            NativeEffectSnapshots snapshots, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames,
            Supplier<ContinuityStorePort.Session> originalSession, Clock clock, int maximumContinuations) {
        this(continuation, policy, snapshots, archive, frames, originalSession, clock, maximumContinuations, null, null);
    }
    public NativeCouncilAssignmentEffects(CouncilContinuationCoordinator continuation, CouncilContinuationPolicy policy,
            NativeEffectSnapshots snapshots, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames,
            Supplier<ContinuityStorePort.Session> originalSession, Clock clock, int maximumContinuations,
            RecoverySeatReader recoverySeats, NativeCouncilReadPort.ReplayConfiguration recoverySeatReplay) {
        this.recoverySeats = recoverySeats; this.recoverySeatReplay = recoverySeatReplay;
        StrictJson.require((recoverySeats == null) == (recoverySeatReplay == null), "recovered Council seat reader and pure replay configuration must be installed together");
        this.continuation = Objects.requireNonNull(continuation); this.policy = Objects.requireNonNull(policy); this.snapshots = Objects.requireNonNull(snapshots);
        this.archive = Objects.requireNonNull(archive); this.frames = Objects.requireNonNull(frames); this.originalSession = Objects.requireNonNull(originalSession);
        this.clock = Objects.requireNonNull(clock); StrictJson.require(maximumContinuations >= 3 && maximumContinuations <= MAX_ACTIVE_REQUESTS, "bounded complete Council continuation budget required");
        this.maximumContinuations = maximumContinuations;
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        StrictJson.require(command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN), "exact private Council observer required");
        if (!(dispatch instanceof NativeActionPort.AckReceived original)) return NativeEffectRegistry.Projected.pending("original Council result unknown; collect its original request only", List.of(attempt.guard().nativeEvidence()));
        var context = GovernanceActionScope.current(command); var same = context.session(command); var scope = context.mailbox(command);
        var results = new ArrayList<CouncilContinuationReceipt>();
        try {
            CouncilContinuationPolicy.requireOriginalPending(command, attempt, original);
            var prior = continuation.retained(same);
            // A resumed operation has no live mailbox authority. Existing rows are not reissued under new nonces.
            StrictJson.require(prior.isEmpty() || !prior.getFirst().request().scope().parentActionId().equals(command.actionId()), "existing Council continuation chain is collect-only outside its original live call");
            // The canonical core alone may rotate a different already-settled original scope before first issue.
            CouncilContinuationPolicy.Progress progress = CouncilContinuationPolicy.replay(command, attempt, original, List.of(), archive.withSession(same));
            for (int count = 0; progress.next().isPresent(); count++) {
                StrictJson.require(count < maximumContinuations && clock.instant().isBefore(ActionObservationWindow.deadline(command)), "Council continuation deadline/budget exhausted; original requests retained, no requeue");
                Stage next = progress.next().orElseThrow();
                if (next == Stage.RECEIPT_QUERY) snapshots.read(command, attempt); // require actual newer Native+Driver material before receipt issue
                CouncilContinuationReceipt receipt = continuation.continueOnce(same, command, attempt, next, ActionObservationWindow.deadline(command)); results.add(receipt);
                if (receipt.status() != Status.ACK) return NativeEffectRegistry.Projected.pending("Council continuation result UNKNOWN; collect exact original ID only", List.of(receipt.latestRecord()));
                prior = continuation.retained(same);
                progress = CouncilContinuationPolicy.replay(command, attempt, original, prior, archive.withSession(same));
                if (progress.next().filter(stage -> stage == Stage.HELPER_STATUS || stage == Stage.RECEIPT_STATUS).isPresent()) {
                    try { Thread.sleep(10); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); return NativeEffectRegistry.Projected.pending("Council continuation interrupted; no new request after scope exits", List.of(receipt.latestRecord())); }
                }
            }
            if (progress.helper().filter(value -> value.status() == CouncilActionCodec.AckStatus.REJECTED_BEFORE_SUBMIT).isPresent()) {
                var helper = progress.helper().orElseThrow();
                if (helper.disposition() != CouncilActionCodec.HelperDisposition.REJECTED_WITHOUT_INVOCATION)
                    return NativeEffectRegistry.Projected.pending("Council helper remains unresolved: " + helper.disposition() + "; preserve original and do not replay", results.stream().map(CouncilContinuationReceipt::latestRecord).toList());
                var bound = archive.withSession(same);
                continuation.verifyCanonicalChain(same, same.head(), results);
                policy.requirePreflight(command, attempt, results.getFirst().request().supportingEvidence(), bound, original);
                ExactRef basis = preserveRejection(command, attempt, results, helper, bound);
                var rejected = reject(command, attempt, helper, basis);
                // The real producer retains no pending ACK for this rejected helper. There is no receipt RPC to issue.
                scope.complete(results.getLast().outcome().orElseThrow());
                return rejected;
            }
            StrictJson.require(progress.receipt().filter(value -> value.status() == CouncilActionCodec.ReceiptStatus.APPLIED).isPresent(), "Council original native receipt did not verify incumbent assignment");
            var pair = snapshots.read(command, attempt); var boundArchive = archive.withSession(same);
            continuation.verifyCanonicalChain(same, same.head(), results);
            policy.requirePreflight(command, attempt, results.getFirst().request().supportingEvidence(), boundArchive, original);
            RawJson compatible = compatible(progress.receipt().orElseThrow());
            var projected = project(command, attempt, pair, progress.receipt().orElseThrow(), compatible, List.of());
            ExactRef basis = preserve(command, attempt, pair, results, compatible, boundArchive);
            projected = NativeEffectSnapshots.withEvidence(projected, List.of(basis));
            NativeActionPort.DispatchOutcome last = results.getLast().outcome().orElseThrow();
            // All result/event/body/native-frame originals are durable before releasing the one mailbox.
            scope.complete(last);
            return projected;
        } catch (IOException failure) { throw new UncheckedIOException("original Council continuation/effect evidence unavailable; never replay", failure); }
    }
    public NativeEffectRegistry.Projected observeRecovered(ContinuityStorePort.Session same, ActionCommand command,
            ActionState.Attempt originalAttempt, NativeActionPort.AckReceived originalAck, java.time.Instant observationDeadline,
            List<PlanningReadReceipt> originalPreflight) throws IOException, InterruptedException {
        Objects.requireNonNull(observationDeadline); Objects.requireNonNull(originalPreflight);
        var role = continuation.currentRecoveryOriginal(same, command.actionId());
        role.requireCurrent();
        StrictJson.require(command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN)
                && role.command().equals(command) && role.attempt().equals(originalAttempt) && role.originalAck().equals(originalAck),
                "recovered Council changed its actual original command/attempt/positive ACK");
        CouncilContinuationPolicy.requireOriginalPending(command, originalAttempt, originalAck);
        java.time.Instant bound = ActionObservationWindow.deadline(command);
        java.time.Instant until = observationDeadline.isBefore(bound) ? observationDeadline : bound;
        StrictJson.require(clock.instant().isBefore(until), "recovered Council read-only observer window expired");
        var boundArchive = archive.withSession(same);
        var results = new ArrayList<CouncilContinuationReceipt>();
        var policyScope = policy.beginRecovery(same, role, List.copyOf(originalPreflight));
        try {
            for (Retained old : continuation.retained(same)) {
                if (!old.request().scope().parentActionId().equals(command.actionId())) continue;
                role.requireCurrent();
                CouncilContinuationReceipt receipt = continuation.recover(same, old.request().requestId(), until);
                results.add(receipt);
                if (receipt.status() != Status.ACK)
                    return NativeEffectRegistry.Projected.pending("original Council continuation remains UNKNOWN; collect only, never reissue",
                            List.of(receipt.latestRecord()));
            }
            if (!results.isEmpty()) continuation.verifyCanonicalChain(same, same.head(), results);
            var prior = results.isEmpty() ? List.<Retained>of() : retained(results, boundArchive);
            var progress = CouncilContinuationPolicy.replayRecovered(command, originalAttempt, originalAck, prior, boundArchive);
            for (int count = 0; progress.next().isPresent(); count++) {
                role.requireCurrent();
                StrictJson.require(count < maximumContinuations && results.size() < MAX_ACTIVE_REQUESTS
                        && clock.instant().isBefore(until), "recovered Council observer deadline/budget exhausted; no assignment replay");
                Stage next = progress.next().orElseThrow();
                if (next == Stage.RECEIPT_QUERY) snapshots.readRecovered(role);
                CouncilContinuationReceipt receipt = continuation.continueOnce(same, command, originalAttempt, next, until);
                results.add(receipt);
                if (receipt.status() != Status.ACK)
                    return NativeEffectRegistry.Projected.pending("recovered Council request UNKNOWN; retain its exact original ID",
                            List.of(receipt.latestRecord()));
                continuation.verifyCanonicalChain(same, same.head(), results);
                prior = retained(results, boundArchive);
                progress = CouncilContinuationPolicy.replayRecovered(command, originalAttempt, originalAck, prior, boundArchive);
                if (progress.next().filter(stage -> stage == Stage.HELPER_STATUS || stage == Stage.RECEIPT_STATUS).isPresent())
                    Thread.sleep(10);
            }
            role.requireCurrent();
            StrictJson.require(!results.isEmpty(), "recovered Council has no complete actual continuation chain");
            continuation.verifyCanonicalChain(same, same.head(), results);
            policy.requirePreflight(command, originalAttempt, results.getFirst().request().supportingEvidence(), boundArchive, originalAck);
            if (progress.helper().filter(value -> value.status() == CouncilActionCodec.AckStatus.REJECTED_BEFORE_SUBMIT).isPresent()) {
                var helper = progress.helper().orElseThrow();
                if (helper.disposition() != CouncilActionCodec.HelperDisposition.REJECTED_WITHOUT_INVOCATION)
                    return NativeEffectRegistry.Projected.pending("recovered Council helper unresolved; never replay original assignment",
                            results.stream().map(CouncilContinuationReceipt::latestRecord).toList());
                ExactRef basis = preserveRejection(command, originalAttempt, results, helper, boundArchive);
                role.requireCurrent();
                return reject(command, originalAttempt, helper, basis);
            }
            StrictJson.require(progress.receipt().filter(value -> value.status() == CouncilActionCodec.ReceiptStatus.APPLIED).isPresent(),
                    "recovered Council lacks its independent verified native assignment receipt");
            var applied = progress.receipt().orElseThrow();
            requireReceiptQueryFrame(results, applied);
            StrictJson.require(recoverySeats != null && recoverySeatReplay != null,
                    "actual current Council seat reader/replay is not installed; no receipt or assignment replay");
            var checkpoint = role.seatCheckpoint();
            NativeEffectSnapshots.Pair pair;
            GuardEvidence observation;
            ObservationProvenance provenance;
            ExactRef tuple;
            if (checkpoint.isPresent()) {
                tuple = checkpoint.orElseThrow().tuple();
                var retainedObservation = loadSeatTuple(tuple, command, originalAttempt, frames, boundArchive);
                pair = retainedObservation.pair(); observation = retainedObservation.guard(); provenance = retainedObservation.provenance();
            } else {
                pair = snapshots.readRecovered(role); observation = role.observationGuard(); provenance = role.observationProvenance();
                tuple = preserveSeatTuple(command, originalAttempt, pair, observation, provenance, boundArchive);
            }
            role.requireCurrent();
            RawJson compatible = compatible(progress.receipt().orElseThrow());
            StrictJson.require(provenance instanceof ObservationProvenance.FreshSnapshotQuery,
                    "recovered Council after frame requires its actual same-occurrence fresh READ provenance");
            frames.verifyFreshSnapshotQuery((ObservationProvenance.FreshSnapshotQuery) provenance, pair.after(), boundArchive);
            requireSeatReadAfterReceipt(results, provenance, pair, boundArchive);
            if (checkpoint.isEmpty()) role.checkpointSeatTuple(tuple);
            StrictJson.require(role.seatCheckpoint().filter(value -> value.tuple().equals(tuple)).isPresent(),
                    "same-capture Council tuple has no actual canonical checkpoint; no QUERY is authorized");
            List<PlanningReadReceipt> seatReads;
            try { seatReads = List.copyOf(recoverySeats.read(same, role, observation, until)); }
            catch (IOException failure) { throw new IOException("current Council seat observation unavailable; retained same-capture tuple="
                    + tuple.sha256() + ":" + tuple.bytes(), failure); }
            var seat = CouncilRecoverySeatProof.require(command, originalAttempt, applied, pair, observation, seatReads,
                    recoverySeatReplay.definitions(), recoverySeatReplay.connectedVersion(), recoverySeatReplay.connectedSha256());
            requireReadOriginals(seatReads, boundArchive);
            requireDistinctSeatRequests(results, originalAttempt, seatReads);
            requireCanonicalSeatReads(role, tuple, seatReads, boundArchive);
            continuation.verifyCanonicalSeatCheckpoint(same, same.head(),
                    new Scope(command.actionId(), ActionCodec.bodySha256(command), originalAttempt.requestId()),
                    tuple, seatReads.stream().map(boundArchive::readReferenceOf).toList());
            role.requireCurrent();
            var projected = projectRecoveredSeat(command, originalAttempt, pair, applied, seat, compatible, List.of(), provenance);
            ExactRef chain = preserveSeatChain(command, originalAttempt, pair, results, compatible, tuple, seatReads, boundArchive);
            ExactRef basis = preserveRecovered(command, originalAttempt, pair, observation, chain, compatible, seatReads, boundArchive);
            role.requireCurrent();
            return NativeEffectSnapshots.withEvidence(projected, List.of(basis, chain));
        } finally { policyScope.close(); }
    }
    private static List<Retained> retained(List<CouncilContinuationReceipt> receipts, ActionPorts.OutcomeArchive archive) {
        return receipts.stream().map(receipt -> new Retained(receipt.latestRecord(),
                CouncilContinuationCodec.decodeEntry(exact(receipt.latestRecord(), archive).bytes()))).toList();
    }
    /** Full generic v3 basis first: the existing archive and writer discover and qualify every reconciliation original. */
    private static ExactRef preserveRecovered(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            GuardEvidence observation, ExactRef chain, RawJson compatible, List<PlanningReadReceipt> seatReads,
            ActionPorts.OutcomeArchive archive) {
        StrictJson.require(observation.origin() instanceof CommandOrigin.Reconciliation
                && pair.reconciliation().filter(identity -> identity.sameGuardFrame(observation.origin().requireReconciliation())).isPresent(),
                "Council recovered Pair lost its same-occurrence actual Root reconciliation guard");
        var identity = observation.origin().requireReconciliation(); var pending = identity.pending();
        StrictJson.require(pending.actionId().equals(command.actionId()) && pending.bodySha256().equals(ActionCodec.bodySha256(command))
                && pending.requestId().equals(attempt.requestId()) && pending.originalBefore().equals(command.before())
                && observation.operation().equals(command.operation()) && observation.authorityId().equals(attempt.guard().authorityId())
                && identity.factual().equals(pair.after().identity()) && identity.source().equals(pair.after().source())
                && identity.sessionId().equals(pair.after().sessionId()) && identity.connectionGeneration().equals(pair.after().connectionGeneration())
                && identity.nativeEvidence().equals(pair.after().originalEvidence())
                && identity.evidence().observationManifest().equals(NativeEffectEvidence.basis(pair.after()).driverFacts()),
                "Council recovered observation crossed original pending or actual after frame");
        identity.requireOriginalConnection(attempt.guard());
        for (var frame : List.of(pair.before(), pair.after())) {
            var original = NativeEffectEvidence.basis(frame);
            StrictJson.require(original.nativeFrame().sha256().equals(ActionCodec.sha256(archive.loadNativeFrame(original.nativeFrame())))
                    && original.driverFacts().equals(archive.materialReferenceOf(archive.loadFullMaterial(original.driverFacts()))),
                    "recovered Council complete frame originals changed");
        }
        ExactRef material = archive.preserveMaterial(compatible);
        var row = StrictJson.object().put("schema", NativeEffectEvidence.RECONCILIATION_SCHEMA)
                .put("command_body_sha256", ActionCodec.bodySha256(command)).put("request_id", attempt.requestId());
        row.set("before", frame(NativeEffectEvidence.basis(pair.before())));
        row.set("after", frame(NativeEffectEvidence.basis(pair.after())));
        row.set("compatible_material", material.toJson());
        var independent = row.putArray("independent_reads");
        for (var read : seatReads) independent.add(archive.readReferenceOf(read).toJson());
        row.putArray("supporting_materials").add(chain.toJson());
        row.set("reconciliation_guard", CommandOriginCodec.guard(observation));
        RawJson body = new RawJson(StrictJson.canonical(row)); ExactRef result = archive.preserveMaterial(body);
        StrictJson.require(body.equals(archive.loadMaterial(result)) && compatible.equals(archive.loadMaterial(material)),
                "recovered Council generic v3 evidence changed");
        return result;
    }
    private static CouncilContinuationPolicy.Progress replayChain(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.AckReceived original, List<Retained> rows, ActionPorts.OutcomeArchive archive) throws IOException {
        boolean recovered = rows.stream().anyMatch(row -> archive.loadReceipt(row.request().originalParentReceipt()).state() instanceof ActionState.Unknown);
        return recovered ? CouncilContinuationPolicy.replayRecovered(command, attempt, original, rows, archive)
                : CouncilContinuationPolicy.replay(command, attempt, original, rows, archive);
    }
    public NativeRecordedEvidenceVerifier.Binding archivedVerifier(ExactRef actualDefinitionSource) {
        return archivedVerifier(actualDefinitionSource, continuation, policy, frames, originalSession, recoverySeatReplay);
    }
    /** Pure archive replay is available before a new Game has any adopted Driver; it captures no old Game owner. */
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(ExactRef actualDefinitionSource,
            CouncilContinuationCoordinator continuation, CouncilContinuationPolicy policy,
            NativeEffectEvidence.FrameLoader frames, Supplier<ContinuityStorePort.Session> originalSession) {
        return archivedVerifier(actualDefinitionSource, continuation, policy, frames, originalSession, null);
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(ExactRef actualDefinitionSource,
            CouncilContinuationCoordinator continuation, CouncilContinuationPolicy policy,
            NativeEffectEvidence.FrameLoader frames, Supplier<ContinuityStorePort.Session> originalSession,
            NativeCouncilReadPort.ReplayConfiguration recoverySeatReplay) {
        return new NativeRecordedEvidenceVerifier.Binding(new OperationKey(CouncilActionCodec.PRIVATE_ASSIGN), actualDefinitionSource,
                (head, parent, archive) -> {
                    try {
                        var same = originalSession.get(); var settled = (ActionState.Settled) parent.state();
                        if (settled.settlement() instanceof ActionState.Rejected rejected) {
                            verifyRejected(same, head, parent, settled, rejected, continuation, policy, archive);
                            return;
                        }
                        StrictJson.require(settled.settlement() instanceof ActionState.Applied && settled.dispatch() instanceof NativeActionPort.AckReceived, "private Council archived verifier requires its actual primitive effect/original pending ACK");
                        var effect = ((ActionState.Applied) settled.settlement()).observation();
                        StrictJson.require(!effect.supportingEvidence().isEmpty(), "private Council requires its complete original evidence leaf");
                        RawJson body = exact(effect.supportingEvidence().getFirst(), archive);
                        NativeEffectEvidence.Original recovered = null;
                        if (NativeEffectEvidence.RECONCILIATION_SCHEMA.equals(StrictJson.text(StrictJson.parse(body.bytes()).get("schema")))) {
                            recovered = NativeEffectEvidence.load(parent, archive, frames);
                            StrictJson.require(recovered.reconciliationGuard().isPresent() && recovered.frames().reconciliation().isPresent()
                                    && recovered.supportingMaterials().size() == 1,
                                    "Council recovered v3 basis requires its exact actual guard and sole strict original chain leaf");
                            body = exact(recovered.supportingMaterials().getFirst(), archive);
                        } else StrictJson.require(effect.supportingEvidence().size() == 1,
                                "legacy Council v1 requires one complete original evidence leaf");
                        var parsed = StrictJson.parse(body.bytes());
                        boolean currentSeat = SEAT_SCHEMA.equals(StrictJson.text(parsed.get("schema")));
                        var fields = new java.util.HashSet<>(Set.of("schema", "command_body_sha256", "original_request_id", "before", "after", "continuations", "compatible_material"));
                        if (currentSeat) fields.addAll(Set.of("seat_reads", "observation_tuple"));
                        var row = StrictJson.object(parsed, Set.copyOf(fields));
                        StrictJson.require((currentSeat || SCHEMA.equals(StrictJson.text(row.get("schema")))) && parent.bodySha256().equals(StrictJson.text(row.get("command_body_sha256")))
                                && settled.attempt().requestId().equals(StrictJson.text(row.get("original_request_id"))), "Council evidence leaf crossed canonical parent/original attempt");
                        Complete before = frames.load(frameBasis(row.get("before")), archive), after = frames.load(frameBasis(row.get("after")), archive);
                        StrictJson.require(before.identity().equals(parent.command().before()) && before.source().equals(parent.command().source()) && before.sessionId().equals(parent.command().sessionId())
                                && before.originalEvidence().equals(settled.attempt().guard().nativeEvidence()), "Council archived original before-frame changed");
                        StrictJson.require(after.identity().equals(effect.after()) && after.source().equals(effect.source()) && after.sessionId().equals(effect.sessionId())
                                && after.observedAt().equals(effect.observedAt()) && after.originalEvidence().equals(effect.originalEvidence()), "Council archived actual post-frame changed");
                        var pair = recovered == null ? new NativeEffectSnapshots.Pair(before, after)
                                : new NativeEffectSnapshots.Pair(before, after, recovered.frames().reconciliation());
                        if (recovered != null) StrictJson.require(NativeEffectEvidence.basis(recovered.frames().before()).equals(frameBasis(row.get("before")))
                                && NativeEffectEvidence.basis(recovered.frames().after()).equals(frameBasis(row.get("after"))),
                                "recovered Council chain frames differ from its complete generic v3 basis");
                        var chain = decodeChain(row.get("continuations"), archive);
                        continuation.verifyCanonicalChain(same, head, chain);
                        policy.requirePreflight(parent.command(), settled.attempt(), chain.getFirst().request().supportingEvidence(), archive, (NativeActionPort.AckReceived) settled.dispatch());
                        var retained = chain.stream().map(receipt -> new Retained(receipt.latestRecord(), CouncilContinuationCodec.decodeEntry(exact(receipt.latestRecord(), archive).bytes()))).toList();
                        var progress = replayChain(parent.command(), settled.attempt(), (NativeActionPort.AckReceived) settled.dispatch(), retained, archive);
                        StrictJson.require(progress.next().isEmpty() && progress.receipt().isPresent(), "archived Council chain is incomplete");
                        RawJson compatible = exact(ExactRef.fromJson(row.get("compatible_material")), archive);
                        StrictJson.require(compatible.equals(compatible(progress.receipt().orElseThrow()))
                                && (recovered == null || recovered.compatibleResult().equals(compatible)),
                                "Council history projection differs from original native receipt or recovered v3 basis");
                        NativeEffectRegistry.Projected replayed;
                        if (currentSeat) {
                            StrictJson.require(recovered != null && recoverySeatReplay != null,
                                    "current-seat Council basis requires its actual Root-installed pure replay decoder and reconciliation closure");
                            requireReceiptQueryFrame(chain, progress.receipt().orElseThrow());
                            requireSeatReadAfterReceipt(chain, effect.provenance(), pair, archive);
                            var seatReads = loadSeatReads(row.get("seat_reads"), archive);
                            requireDistinctSeatRequests(chain, settled.attempt(), seatReads);
                            StrictJson.require(seatReads.equals(recovered.independentReads()), "current Council seat read closure differs from generic evidence");
                            var observation = recovered.reconciliationGuard().orElseThrow();
                            continuation.verifyCanonicalSeatCheckpoint(same, head,
                                    new Scope(parent.command().actionId(), parent.bodySha256(), settled.attempt().requestId()),
                                    ExactRef.fromJson(row.get("observation_tuple")), seatReads.stream().map(archive::readReferenceOf).toList());
                            requireSeatTuple(ExactRef.fromJson(row.get("observation_tuple")), parent.command(), settled.attempt(), pair,
                                    observation, effect.provenance(), archive);
                            StrictJson.require(effect.provenance() instanceof ObservationProvenance.FreshSnapshotQuery,
                                    "current Council seat lost its actual fresh READ provenance");
                            frames.verifyFreshSnapshotQuery((ObservationProvenance.FreshSnapshotQuery) effect.provenance(), after, archive);
                            var seat = CouncilRecoverySeatProof.require(parent.command(), settled.attempt(), progress.receipt().orElseThrow(), pair,
                                    observation, seatReads, recoverySeatReplay.definitions(), recoverySeatReplay.connectedVersion(), recoverySeatReplay.connectedSha256());
                            replayed = projectRecoveredSeat(parent.command(), settled.attempt(), pair, progress.receipt().orElseThrow(), seat,
                                    compatible, effect.supportingEvidence(), effect.provenance());
                        } else if (recovered == null) replayed = project(parent.command(), settled.attempt(), pair,
                                progress.receipt().orElseThrow(), compatible, effect.supportingEvidence());
                        else {
                            StrictJson.require(recovered.independentReads().isEmpty(), "legacy recovered Council basis must not hide independent seat reads");
                            StrictJson.require(effect.provenance() instanceof ObservationProvenance.FreshSnapshotQuery,
                                    "recovered Council archive lost its actual fresh READ provenance");
                            frames.verifyFreshSnapshotQuery((ObservationProvenance.FreshSnapshotQuery) effect.provenance(), after, archive);
                            replayed = projectRecovered(parent.command(), settled.attempt(), pair, progress.receipt().orElseThrow(),
                                    compatible, effect.supportingEvidence(), effect.provenance());
                        }
                        NativeEffectEvidence.requireSame(settled.settlement(), replayed, compatible);
                    } catch (IOException failure) { throw new UncheckedIOException("canonical Council continuation replay unavailable", failure); }
                });
    }
    private static NativeEffectRegistry.Projected reject(ActionCommand command, ActionState.Attempt attempt,
            CouncilActionCodec.Ack helper, ExactRef original) {
        StrictJson.require(helper.status() == CouncilActionCodec.AckStatus.REJECTED_BEFORE_SUBMIT && !helper.helperInvoked()
                && !helper.queueAcceptanceObserved() && !helper.verificationPending()
                && helper.disposition() == CouncilActionCodec.HelperDisposition.REJECTED_WITHOUT_INVOCATION,
                "only source-qualified genuine noninvocation may settle Council rejection");
        var rejected = new ActionState.Rejected(attempt.requestId(), "native_council_rejected_before_submit:" + helper.failure(), original);
        ActionEffects.validate(command, attempt, rejected);
        return new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(rejected), Optional.empty());
    }
    private static ExactRef preserveRejection(ActionCommand command, ActionState.Attempt attempt, List<CouncilContinuationReceipt> receipts,
            CouncilActionCodec.Ack helper, ActionPorts.OutcomeArchive archive) {
        var row = StrictJson.object().put("schema", REJECTION_SCHEMA).put("command_body_sha256", ActionCodec.bodySha256(command)).put("original_request_id", attempt.requestId());
        var chain = row.putArray("continuations");
        for (var receipt : receipts) {
            var item = chain.addObject(); item.set("entry", receipt.latestRecord().toJson());
            item.set("result_domain_payload", receipt.resultDomainPayload().toJson()); item.set("result_event", receipt.resultEvent().toJson());
        }
        row.set("compatible_material", archive.preserveMaterial(new RawJson(helper.original().bytes())).toJson());
        RawJson body = new RawJson(StrictJson.canonical(row)); ExactRef ref = archive.preserveMaterial(body);
        StrictJson.require(body.equals(archive.loadMaterial(ref)), "Council native rejection archive changed"); return ref;
    }
    private static void verifyRejected(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent,
            ActionState.Settled settled, ActionState.Rejected rejected, CouncilContinuationCoordinator continuation,
            CouncilContinuationPolicy policy, ActionPorts.OutcomeArchive archive) throws IOException {
        var row = StrictJson.object(StrictJson.parse(exact(rejected.originalEvidence(), archive).bytes()), Set.of("schema", "command_body_sha256", "original_request_id", "continuations", "compatible_material"));
        StrictJson.require(REJECTION_SCHEMA.equals(CouncilCodec.text(row, "schema")) && parent.bodySha256().equals(CouncilCodec.text(row, "command_body_sha256"))
                && settled.attempt().requestId().equals(CouncilCodec.text(row, "original_request_id")) && settled.dispatch() instanceof NativeActionPort.AckReceived, "Council rejection crossed its canonical original command/attempt");
        var chain = decodeChain(row.get("continuations"), archive);
        continuation.verifyCanonicalChain(same, head, chain);
        policy.requirePreflight(parent.command(), settled.attempt(), chain.getFirst().request().supportingEvidence(), archive,
                (NativeActionPort.AckReceived) settled.dispatch());
        var retained = chain.stream().map(receipt -> new Retained(receipt.latestRecord(), CouncilContinuationCodec.decodeEntry(exact(receipt.latestRecord(), archive).bytes()))).toList();
        var progress = replayChain(parent.command(), settled.attempt(), (NativeActionPort.AckReceived) settled.dispatch(), retained, archive);
        StrictJson.require(progress.next().isEmpty() && progress.receipt().isEmpty() && progress.helper().isPresent(), "Council rejection requires the complete original helper-only terminal chain");
        var helper = progress.helper().orElseThrow();
        RawJson compatible = exact(ExactRef.fromJson(row.get("compatible_material")), archive);
        var replayed = reject(parent.command(), settled.attempt(), helper, rejected.originalEvidence());
        StrictJson.require(replayed.result() instanceof ActionPorts.RejectionObserved actual && actual.rejection().equals(rejected)
                && replayed.compatibleResult().isEmpty() && compatible.equals(new RawJson(helper.original().bytes())), "Council original native rejection replay differs from proposed settlement");
    }
    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            CouncilActionCodec.Receipt receipt, RawJson compatible, List<ExactRef> supporting) {
        StrictJson.require(receipt.status() == CouncilActionCodec.ReceiptStatus.APPLIED, "Council ACK/rejection is not independent applied material");
        Complete after = pair.after(); var id = after.identity().frame().identity();
        StrictJson.require(receipt.postSnapshotId().equals("native:" + id.nativeRevision()) && receipt.postNativeRevision().equals(id.nativeRevision())
                && receipt.postPublicRevision().equals(id.nativeRevision()) && receipt.postDateRaw() == id.dateRaw().intValueExact()
                && receipt.ownerId() == id.player().intValueExact() && !after.observedAt().isBefore(attempt.submittedAt()), "Council receipt differs from real fresh after Native+Driver frame");
        List<ExpectedValue> actual = List.of(new ExpectedText(new FieldKey("council.position_key"), receipt.position().key()),
                new ExpectedInteger(new FieldKey("council.incumbent_character_id"), java.math.BigInteger.valueOf(receipt.incumbentId())),
                new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true));
        StrictJson.require(org.xar.ck3.control.g2.planning.ProposalLifecycle.compare(command.expected(), after.identity(), after.source(), NativeGovernanceEffects.SCHEMA, actual)
                == org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH, "Council actual incumbent did not meet the requested postcondition");
        var observation = new ActionState.EffectObservation(after.identity(), after.source(), after.sessionId(), NativeGovernanceEffects.SCHEMA, actual,
                new ObservationProvenance.Push(after.identity().frame().snapshotId(), id.nativeRevision(), after.originalEvidence()), after.observedAt(), after.originalEvidence(), supporting);
        ActionEffects.validate(command, attempt, new ActionState.Applied(observation));
        return new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(observation), Optional.of(compatible));
    }
    private static NativeEffectRegistry.Projected projectRecovered(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            CouncilActionCodec.Receipt receipt, RawJson compatible, List<ExactRef> supporting, ObservationProvenance provenance) {
        StrictJson.require(receipt.status() == CouncilActionCodec.ReceiptStatus.APPLIED, "Council ACK/rejection is not independent applied material");
        Complete after = pair.after(); var id = after.identity().frame().identity();
        StrictJson.require(receipt.postSnapshotId().equals("native:" + id.nativeRevision()) && receipt.postNativeRevision().equals(id.nativeRevision())
                && receipt.postPublicRevision().equals(id.nativeRevision()) && receipt.postDateRaw() == id.dateRaw().intValueExact()
                && receipt.ownerId() == id.player().intValueExact() && !after.observedAt().isBefore(attempt.submittedAt()), "Council receipt differs from real fresh after Native+Driver frame");
        List<ExpectedValue> actual = List.of(new ExpectedText(new FieldKey("council.position_key"), receipt.position().key()),
                new ExpectedInteger(new FieldKey("council.incumbent_character_id"), java.math.BigInteger.valueOf(receipt.incumbentId())),
                new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true));
        StrictJson.require(org.xar.ck3.control.g2.planning.ProposalLifecycle.compare(command.expected(), after.identity(), after.source(), NativeGovernanceEffects.SCHEMA, actual)
                == org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH, "Council actual incumbent did not meet the requested postcondition");
        var observation = new ActionState.EffectObservation(after.identity(), after.source(), after.sessionId(), NativeGovernanceEffects.SCHEMA, actual,
                Objects.requireNonNull(provenance), after.observedAt(), after.originalEvidence(), supporting);
        ActionEffects.validate(command, attempt, new ActionState.Applied(observation));
        return new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(observation), Optional.of(compatible));
    }
    private static ExactRef preserve(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            List<CouncilContinuationReceipt> receipts, RawJson compatible, ActionPorts.OutcomeArchive archive) {
        var body = StrictJson.object().put("schema", SCHEMA).put("command_body_sha256", ActionCodec.bodySha256(command)).put("original_request_id", attempt.requestId());
        body.set("before", frame(NativeEffectEvidence.basis(pair.before()))); body.set("after", frame(NativeEffectEvidence.basis(pair.after())));
        var chain = body.putArray("continuations");
        for (CouncilContinuationReceipt receipt : receipts) chain.addObject().set("entry", receipt.latestRecord().toJson());
        for (int index = 0; index < receipts.size(); index++) {
            ObjectNode item = (ObjectNode) chain.get(index); CouncilContinuationReceipt receipt = receipts.get(index);
            item.set("result_domain_payload", receipt.resultDomainPayload().toJson()); item.set("result_event", receipt.resultEvent().toJson());
        }
        body.set("compatible_material", archive.preserveMaterial(compatible).toJson());
        RawJson material = new RawJson(StrictJson.canonical(body)); ExactRef result = archive.preserveMaterial(material);
        StrictJson.require(material.equals(archive.loadMaterial(result)), "Council effect leaf archive changed"); return result;
    }
    private static List<CouncilContinuationReceipt> decodeChain(JsonNode raw, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(raw.isArray() && raw.size() >= 1 && raw.size() <= MAX_ACTIVE_REQUESTS, "complete bounded Council issued/result chain required");
        var result = new ArrayList<CouncilContinuationReceipt>();
        for (JsonNode item : raw) {
            ObjectNode row = StrictJson.object(item, Set.of("entry", "result_domain_payload", "result_event")); ExactRef ref = ExactRef.fromJson(row.get("entry"));
            Entry entry = CouncilContinuationCodec.decodeEntry(exact(ref, archive).bytes());
            result.add(new CouncilContinuationReceipt(entry.request(), entry.status(), entry.outcome().map(archive::load), entry.issued().orElseThrow(), ref,
                    ExactRef.fromJson(row.get("result_domain_payload")), ExactRef.fromJson(row.get("result_event"))));
        }
        return List.copyOf(result);
    }
    /** Exact original receipt occurrence is separate from the new current-seat observation. */
    private static void requireReceiptQueryFrame(List<CouncilContinuationReceipt> chain, CouncilActionCodec.Receipt applied) {
        StrictJson.require(!chain.isEmpty(), "actual original Council receipt chain required");
        var query = chain.stream().filter(value -> value.request().stage() == Stage.RECEIPT_QUERY).findFirst().orElseThrow();
        var terminal = chain.getLast();
        StrictJson.require(terminal.request().stage() == Stage.RECEIPT_QUERY || terminal.request().stage() == Stage.RECEIPT_STATUS,
                "original applied Council receipt must come from its actual receipt-query group");
        var expected = query.request().guard().observed().frame().identity();
        var actual = terminal.request().guard().observed().frame().identity();
        StrictJson.require(applied.status() == CouncilActionCodec.ReceiptStatus.APPLIED
                && expected.nativeRevision().equals(actual.nativeRevision()) && expected.dateRaw().equals(actual.dateRaw())
                && expected.player().equals(actual.player())
                && applied.postSnapshotId().equals("native:" + actual.nativeRevision())
                && applied.postNativeRevision().equals(actual.nativeRevision()) && applied.postPublicRevision().equals(actual.nativeRevision())
                && applied.postDateRaw() == actual.dateRaw().intValueExact() && applied.ownerId() == actual.player().intValueExact(),
                "original Council receipt differs from its own actual receipt-query Native frame");
    }
    private record SeatObservation(NativeEffectSnapshots.Pair pair, GuardEvidence guard, ObservationProvenance provenance) { }
    /** Archived tuple DATA is rebuilt, never installed as a new current Native/Root permission. */
    private static SeatObservation loadSeatTuple(ExactRef ref, ActionCommand command, ActionState.Attempt attempt,
            NativeEffectEvidence.FrameLoader frames, ActionPorts.OutcomeArchive archive) {
        var row = StrictJson.object(StrictJson.parse(exact(ref, archive).bytes()),
                Set.of("schema", "command_body_sha256", "original_request_id", "before", "after", "reconciliation_guard", "provenance"));
        StrictJson.require(TUPLE_SCHEMA.equals(StrictJson.text(row.get("schema")))
                && ActionCodec.bodySha256(command).equals(StrictJson.text(row.get("command_body_sha256")))
                && attempt.requestId().equals(StrictJson.text(row.get("original_request_id"))),
                "archived current Council tuple crossed its actual command/original attempt");
        var observation = CommandOriginCodec.guard(row.get("reconciliation_guard"));
        StrictJson.require(observation.origin() instanceof CommandOrigin.Reconciliation,
                "archived current Council tuple requires its original reconciliation DATA");
        var before = frames.load(frameBasis(row.get("before")), archive);
        var after = frames.load(frameBasis(row.get("after")), archive);
        var pair = new NativeEffectSnapshots.Pair(before, after, Optional.of(observation.origin().requireReconciliation()));
        var provenance = ObservationProvenanceCodec.decode(row.get("provenance"));
        requireSeatTuple(ref, command, attempt, pair, observation, provenance, archive);
        return new SeatObservation(pair, observation, provenance);
    }
    private static void requireCanonicalSeatReads(CouncilContinuationCoordinator.RecoveryOriginal role, ExactRef tuple,
            List<PlanningReadReceipt> reads, ActionPorts.OutcomeArchive archive) throws IOException {
        var checkpoint = role.seatCheckpoint().orElseThrow();
        StrictJson.require(checkpoint.tuple().equals(tuple) && checkpoint.reads().size() == reads.size(),
                "current Council seat list differs from its actual canonical checkpoint");
        for (int index = 0; index < reads.size(); index++) {
            var retained = checkpoint.reads().get(index); var actual = reads.get(index);
            StrictJson.require(retained.request().equals(actual.request()) && retained.requestId().equals(actual.requestId())
                    && retained.contractId().equals(actual.contractId())
                    && retained.known().filter(archive.readReferenceOf(actual)::equals).isPresent()
                    && retained.outcome().filter(archive.referenceOf(actual.original())::equals).isPresent(),
                    "current Council seat result/ACK/read ID has no exact canonical checkpoint navigation");
        }
    }
    private static void requireSeatReadAfterReceipt(List<CouncilContinuationReceipt> chain, ObservationProvenance proof,
            NativeEffectSnapshots.Pair pair, ActionPorts.OutcomeArchive archive) throws IOException {
        StrictJson.require(proof instanceof ObservationProvenance.FreshSnapshotQuery && !chain.isEmpty(),
                "current Council seat requires the actual independent fresh READ after its original applied receipt");
        var fresh = (ObservationProvenance.FreshSnapshotQuery) proof;
        var prior = chain.getLast().outcome().orElseThrow();
        var loaded = archive.load(fresh.readAcknowledgement());
        StrictJson.require(prior instanceof NativeActionPort.AckReceived && loaded instanceof NativeActionPort.AckReceived,
                "actual old receipt ACK and independent fresh-read ACK required");
        var previous = (NativeActionPort.AckReceived) prior;
        var current = (NativeActionPort.AckReceived) loaded;
        var previousCustody = previous.custody().orElseThrow();
        var currentCustody = current.custody().orElseThrow();
        previousCustody.verify(previous); currentCustody.verify(current);
        var before = previousCustody.session(); var after = currentCustody.session();
        StrictJson.require(current.nativeOk() && fresh.requestId().equals(current.requestId())
                && !current.requestId().equals(previous.requestId())
                && before.machineId().equals(after.machineId()) && before.game().equals(after.game())
                && before.sessionId().equals(after.sessionId())
                && after.connectionGeneration().compareTo(before.connectionGeneration()) >= 0
                && !currentCustody.writeEntered().observedAt().isBefore(previousCustody.responseReceived().observedAt())
                && !pair.after().observedAt().isBefore(previousCustody.responseReceived().observedAt()),
                "current Council seat fresh READ precedes or crosses its original applied receipt");
        if (previousCustody.custodyEpoch().equals(currentCustody.custodyEpoch())) {
            StrictJson.require(before.equals(after)
                    && currentCustody.writeEntered().order().compareTo(previousCustody.responseReceived().order()) > 0,
                    "current Council seat fresh READ lost exact same-epoch receipt-before-read chronology");
        }
    }
    private static void requireDistinctSeatRequests(List<CouncilContinuationReceipt> chain, ActionState.Attempt original,
            List<PlanningReadReceipt> reads) {
        var ids = new java.util.HashSet<String>(); ids.add(original.requestId());
        for (var old : chain) StrictJson.require(ids.add(old.request().requestId()), "original Council request identity repeated");
        for (var read : reads) StrictJson.require(ids.add(read.requestId()), "current Council seat reused an original assignment/continuation request");
    }
    private static void requireReadOriginals(List<PlanningReadReceipt> reads, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(!reads.isEmpty() && reads.size() <= 16, "bounded complete actual Council seat reads required");
        for (var read : reads) {
            var ref = archive.readReferenceOf(read);
            StrictJson.require(read.equals(archive.loadRead(ref)), "current Council seat receipt changed after archive");
            NativeRecordedEvidenceVerifier.requireRead(read, archive);
        }
    }
    private static ObjectNode seatTuple(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            GuardEvidence guard, ObservationProvenance provenance) {
        var row = StrictJson.object().put("schema", TUPLE_SCHEMA).put("command_body_sha256", ActionCodec.bodySha256(command))
                .put("original_request_id", attempt.requestId());
        row.set("before", frame(NativeEffectEvidence.basis(pair.before())));
        row.set("after", frame(NativeEffectEvidence.basis(pair.after())));
        row.set("reconciliation_guard", CommandOriginCodec.guard(guard));
        row.set("provenance", ObservationProvenanceCodec.encode(provenance));
        return row;
    }
    private static ExactRef preserveSeatTuple(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            GuardEvidence guard, ObservationProvenance provenance, ActionPorts.OutcomeArchive archive) {
        RawJson body = new RawJson(StrictJson.canonical(seatTuple(command, attempt, pair, guard, provenance)));
        ExactRef ref = archive.preserveMaterial(body);
        StrictJson.require(body.equals(exact(ref, archive)), "complete current Council observation tuple changed"); return ref;
    }
    private static void requireSeatTuple(ExactRef ref, ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            GuardEvidence guard, ObservationProvenance provenance, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(exact(ref, archive).equals(new RawJson(StrictJson.canonical(seatTuple(command, attempt, pair, guard, provenance)))),
                "current Council observation tuple lost its exact same-capture guard/frame/FreshQuery");
    }
    private static ExactRef preserveSeatChain(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            List<CouncilContinuationReceipt> chain, RawJson compatible, ExactRef tuple, List<PlanningReadReceipt> reads,
            ActionPorts.OutcomeArchive archive) {
        var row = StrictJson.object().put("schema", SEAT_SCHEMA).put("command_body_sha256", ActionCodec.bodySha256(command))
                .put("original_request_id", attempt.requestId());
        row.set("before", frame(NativeEffectEvidence.basis(pair.before())));
        row.set("after", frame(NativeEffectEvidence.basis(pair.after())));
        var entries = row.putArray("continuations");
        for (var receipt : chain) {
            var entry = entries.addObject(); entry.set("entry", receipt.latestRecord().toJson());
            entry.set("result_domain_payload", receipt.resultDomainPayload().toJson());
            entry.set("result_event", receipt.resultEvent().toJson());
        }
        row.set("compatible_material", archive.preserveMaterial(compatible).toJson());
        row.set("observation_tuple", tuple.toJson());
        var encoded = row.putArray("seat_reads");
        for (var read : reads) encoded.add(archive.readReferenceOf(read).toJson());
        RawJson body = new RawJson(StrictJson.canonical(row)); ExactRef ref = archive.preserveMaterial(body);
        StrictJson.require(body.equals(exact(ref, archive)), "current Council seat and original receipt chain changed"); return ref;
    }
    private static List<PlanningReadReceipt> loadSeatReads(JsonNode array, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(array != null && array.isArray() && !array.isEmpty() && array.size() <= 16,
                "bounded archived current Council seat group required");
        var reads = new ArrayList<PlanningReadReceipt>();
        for (var value : array) {
            ExactRef ref = ExactRef.fromJson(value); var read = archive.loadRead(ref);
            StrictJson.require(ref.equals(archive.readReferenceOf(read)), "archived Council seat read locator changed"); reads.add(read);
        }
        requireReadOriginals(reads, archive); return List.copyOf(reads);
    }
    private static NativeEffectRegistry.Projected projectRecoveredSeat(ActionCommand command, ActionState.Attempt attempt,
            NativeEffectSnapshots.Pair pair, CouncilActionCodec.Receipt original, CouncilModels.Candidates current,
            RawJson compatible, List<ExactRef> supporting, ObservationProvenance provenance) {
        Complete after = pair.after();
        StrictJson.require(original.status() == CouncilActionCodec.ReceiptStatus.APPLIED
                && current.seat().position() == original.position() && current.seat().incumbentId().isPresent()
                && current.seat().incumbentId().getAsInt() == original.incumbentId(), "current Council seat differs from independently verified original assignment receipt");
        List<ExpectedValue> actual = List.of(new ExpectedText(new FieldKey("council.position_key"), current.seat().position().key()),
                new ExpectedInteger(new FieldKey("council.incumbent_character_id"), java.math.BigInteger.valueOf(current.seat().incumbentId().getAsInt())),
                new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true));
        StrictJson.require(org.xar.ck3.control.g2.planning.ProposalLifecycle.compare(command.expected(), after.identity(), after.source(), NativeGovernanceEffects.SCHEMA, actual)
                == org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH, "current independently read Council seat did not meet requested postcondition");
        var observed = new ActionState.EffectObservation(after.identity(), after.source(), after.sessionId(), NativeGovernanceEffects.SCHEMA, actual,
                Objects.requireNonNull(provenance), after.observedAt(), after.originalEvidence(), supporting);
        ActionEffects.validate(command, attempt, new ActionState.Applied(observed));
        return new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(observed), Optional.of(compatible));
    }
    private static RawJson compatible(CouncilActionCodec.Receipt receipt) { return new RawJson(receipt.original().bytes()); }
    private static ObjectNode frame(NativeEffectEvidence.FrameBasis frame) { var row = StrictJson.object(); row.set("native_frame", frame.nativeFrame().toJson()); row.set("driver_facts", frame.driverFacts().toJson()); return row; }
    private static NativeEffectEvidence.FrameBasis frameBasis(JsonNode raw) { var row = StrictJson.object(raw, Set.of("native_frame", "driver_facts")); return new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(row.get("native_frame")), ExactRef.fromJson(row.get("driver_facts"))); }
    private static RawJson exact(ExactRef ref, ActionPorts.OutcomeArchive archive) { RawJson raw = archive.loadMaterial(ref); StrictJson.require(ref.bytes() == raw.bytes().length && ref.sha256().equals(ActionCodec.sha256(raw.bytes())), "Council original material bytes/SHA differ"); return raw; }
}
