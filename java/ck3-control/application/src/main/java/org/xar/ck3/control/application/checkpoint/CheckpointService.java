package org.xar.ck3.control.application.checkpoint;

import java.io.IOException;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.continuity.ContinuityJson;
import java.math.BigDecimal;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;
import org.xar.ck3.control.application.lifecycle.SeedStore;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Shared SAVE path. Execute once, observe twice, persist complete Driver, verify pair, reconcile read-only. */
public final class CheckpointService implements ActionPorts.PostconditionPort {
    /** SAVE is streamed by its physical file producer; it is never a generic small native packet. */
    private static final long MAXIMUM_SAVE_BYTES = 1024L * 1024L * 1024L;
    private static final int MAXIMUM_DIAGNOSTIC_WITNESS_BYTES = 65536;
    @FunctionalInterface public interface SeedAdoptionPort { SeedAdoption freezeFirst(CheckpointPair pair, ActionReceipt appliedSave) throws IOException; }
    private sealed interface FileBasis permits KnownBefore, ColdAfterAck { }
    private record KnownBefore(Optional<FileWitness> file) implements FileBasis {
        private KnownBefore { Objects.requireNonNull(file); }
    }
    /** The old physical before is unavailable. This distinct basis never asserts that it was absent. */
    private record ColdAfterAck(Instant acknowledgedAt, ExactRef originalReceipt) implements FileBasis {
        private ColdAfterAck { Objects.requireNonNull(acknowledgedAt); Objects.requireNonNull(originalReceipt); }
    }
    private record ColdBinding(Path savePath, String lineageId) { }
    private volatile ColdBinding coldBinding;
    private static final class AttemptContext {
        private final CheckpointRequest request; private final FileBasis basis;
        private FileWitness prior; private volatile CheckpointPair pair;
        private AttemptContext(CheckpointRequest request, FileBasis basis) { this.request = request; this.basis = basis; }
    }
    private final CheckpointFiles files; private final DriverCheckpointStore drivers; private final CheckpointRequest.ObservationPort observations;
    private final Path evidenceRoot; private final Clock clock; private final SeedAdoptionPort seeds; private volatile ActionCoordinatorPort actions;
    @FunctionalInterface public interface BorrowedSession { org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session current() throws IOException; }
    @FunctionalInterface public interface OriginalCollectionWork { CheckpointResult collect(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) throws IOException; }
    @FunctionalInterface public interface OriginalCollectionScope { CheckpointResult collect(OriginalCollectionWork work) throws IOException; }
    private ActionPorts.OutcomeArchive evidenceArchive;
    private volatile OriginalCollectionScope originalCollection;
    private BorrowedSession evidenceSession;
    private CheckpointCommitVerifier.WriterLeaseVerifier evidenceAuthority;
    /** Install the same original writer archive once, before this service enters the executable catalog. */
    public synchronized void bindEvidence(ActionPorts.OutcomeArchive archive,BorrowedSession sessions,CheckpointCommitVerifier.WriterLeaseVerifier authority) {
        StrictJson.require(evidenceArchive==null,"SAVE original evidence writer is already bound");
        evidenceArchive=Objects.requireNonNull(archive);evidenceSession=Objects.requireNonNull(sessions);evidenceAuthority=Objects.requireNonNull(authority);
    }
    private final ConcurrentHashMap<String,AttemptContext> contexts = new ConcurrentHashMap<>();
    private record OriginalQuery(AttemptContext context,Instant deadline) { }
    private final ThreadLocal<OriginalQuery> originalQuery=new ThreadLocal<>();
    /** Bind actions once after registering this same instance as the SAVE PostconditionPort. */
    public CheckpointService(CheckpointFiles files, DriverCheckpointStore drivers, CheckpointRequest.ObservationPort observations, Path evidenceRoot, Clock clock, SeedAdoptionPort seeds) {
        this.files = Objects.requireNonNull(files); this.drivers = Objects.requireNonNull(drivers); this.observations = Objects.requireNonNull(observations);
        this.evidenceRoot = Objects.requireNonNull(evidenceRoot); this.clock = Objects.requireNonNull(clock); this.seeds = Objects.requireNonNull(seeds); StrictJson.require(evidenceRoot.isAbsolute(), "configured checkpoint evidence root required");
    }
    public synchronized void bindActions(ActionCoordinatorPort authority) {
        if (actions != null) throw new IllegalStateException("checkpoint action authority already bound"); actions = Objects.requireNonNull(authority);
    }
    public synchronized void bindOriginalCollection(OriginalCollectionScope scope) {
        StrictJson.require(originalCollection == null && actions == null && evidenceArchive != null && coldBinding != null,
                "original collection must be installed once by the bound source before actions");
        originalCollection = Objects.requireNonNull(scope);
    }
    /** Installed only by the same Root stage, before this service joins the executable catalog. */
    public synchronized void bindColdRecovery(Path actualSavePath, String actualLineageId) {
        Objects.requireNonNull(actualSavePath); StrictJson.text(actualLineageId);
        StrictJson.require(actions == null && coldBinding == null && evidenceArchive != null,
                "cold SAVE recovery must be installed once by the bound source before actions");
        StrictJson.require(actualSavePath.isAbsolute() && actualSavePath.getFileName() != null
                && actualSavePath.getFileName().toString().equals("xar_checkpoint.ck3"), "actual absolute configured SAVE path required");
        coldBinding = new ColdBinding(actualSavePath, actualLineageId);
    }
    /** A stage may bind the real SeedStore after constructing this service, using its exact same link. */
    public void requireSeedAdoptionPort(SeedAdoptionPort expected)throws IOException {
        if(seeds!=Objects.requireNonNull(expected))throw new IOException("SAVE seed adoption belongs to another staged link");
    }
    public void requireSeedStore(SeedAdoptionPort expected,SeedStore actual)throws IOException {
        requireSeedAdoptionPort(expected);Objects.requireNonNull(actual).requireBacking(files,drivers);
    }
    public CheckpointResult checkpoint(CheckpointRequest request) throws InterruptedException {
        Objects.requireNonNull(request); if (actions == null) throw new IllegalStateException("unique action coordinator is not bound");
        String id = request.saveCommand().actionId(); ActionReceipt receipt = null;
        try {
            if (!clock.instant().isBefore(request.saveCommand().deadline())) return new CheckpointResult.Unknown(id, "SAVE deadline expired before submit", Optional.empty());
            AttemptContext original = new AttemptContext(request, new KnownBefore(files.observe(request.expectedSavePath())));
            AttemptContext prior = contexts.putIfAbsent(id, original);
            if (prior != null && !prior.request.equals(request)) throw new IllegalArgumentException("same SAVE action ID changed request");
            // Coordinator alone decides whether this ID has already been submitted. No loop retries execute.
            receipt = actions.execute(request.saveCommand());
            while (!receipt.settled() && clock.instant().isBefore(request.saveCommand().deadline())) {
                Thread.sleep(Math.min(100, Math.max(1, java.time.Duration.between(clock.instant(), request.saveCommand().deadline()).toMillis())));
                receipt = actions.reconcile(id);
            }
            return materialized(contexts.get(id),receipt);
        } catch (IOException | IllegalArgumentException failure) { return new CheckpointResult.Unknown(id, failure.toString(), Optional.ofNullable(receipt)); }
    }
    /** Collect the original attempt once; never prepare, execute or resend a native SAVE. */
    public CheckpointResult queryOriginal(String originalActionId,Instant freshDeadline)throws InterruptedException {
        StrictJson.text(originalActionId);Objects.requireNonNull(freshDeadline);
        AttemptContext context=contexts.get(originalActionId);
        if(context==null) {
            if (originalCollection == null) return new CheckpointResult.Unknown(originalActionId,"original collection scope unavailable; never submit",Optional.empty());
            Instant now=clock.instant();
            if(!now.isBefore(freshDeadline))return new CheckpointResult.Unknown(originalActionId,"original SAVE query deadline expired; zero dispatch",Optional.empty());
            Instant maximum=now.plus(ActionObservationWindow.MAXIMUM_WINDOW);
            Instant bounded=freshDeadline.isBefore(maximum)?freshDeadline:maximum;
            if(Thread.interrupted())throw new InterruptedException("original SAVE query interrupted before collection");
            try {
                CheckpointResult result = originalCollection.collect(new OriginalCollectionWork() {
                    @Override public CheckpointResult collect(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) throws IOException {
                        return collectColdApplied(originalActionId, same, bounded);
                    }
                });
                if (Thread.interrupted()) throw new InterruptedException("original SAVE collection interrupted; no dispatch");
                return result;
            } catch (IOException | IllegalArgumentException | java.io.UncheckedIOException failure) {
                return new CheckpointResult.Unknown(originalActionId, failure.toString(), Optional.empty());
            }
        }
        if(actions==null)throw new IllegalStateException("unique action coordinator is not bound");
        Instant now=clock.instant();
        if(!now.isBefore(freshDeadline))return new CheckpointResult.Unknown(originalActionId,"original SAVE query deadline expired; zero dispatch",Optional.empty());
        if(originalQuery.get()!=null)return new CheckpointResult.Unknown(originalActionId,"nested original SAVE query is unavailable; zero dispatch",Optional.empty());
        Instant maximum=now.plus(ActionObservationWindow.MAXIMUM_WINDOW);
        Instant bounded=freshDeadline.isBefore(maximum)?freshDeadline:maximum;
        ActionReceipt receipt=null;originalQuery.set(new OriginalQuery(context,bounded));
        try {
            if(Thread.interrupted())throw new InterruptedException("original SAVE query interrupted before collection");
            receipt=actions.reconcile(originalActionId);
            if(!clock.instant().isBefore(bounded))return new CheckpointResult.Unknown(originalActionId,"original SAVE read window expired during collection; zero dispatch",Optional.of(receipt));
            return materialized(context,receipt);
        } catch(IOException|IllegalArgumentException failure) {
            return new CheckpointResult.Unknown(originalActionId,failure.toString(),Optional.ofNullable(receipt));
        } finally {originalQuery.remove();}
    }
    /** Re-collect a canonical already-applied SAVE without recreating a lost pre-dispatch context. */
    private CheckpointResult collectColdApplied(String actionId,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same, Instant deadline) throws IOException {
        ActionPorts.OutcomeArchive archive;
        CheckpointCommitVerifier.WriterLeaseVerifier authority;
        ColdBinding installed;
        synchronized (this) { archive = evidenceArchive; authority = evidenceAuthority; installed = coldBinding; }
        if (archive == null || authority == null || installed == null) throw new IOException("source-installed original SAVE collection is unavailable");
        authority.require(same);
        var head = same.head();
        var bound = archive.withSession(same);
        ActionReceipt receipt = ContinuityActionJournal.lookup(head.state(), actionId, bound)
                .orElseThrow(() -> new IOException("original SAVE is absent from the actual current canonical chain"));
        try {
            requireCollectionTime(deadline);
            var command = receipt.command();
            StrictJson.require(command.actionId().equals(actionId)
                    && command.operation().equals(new OperationKey("save-checkpoint"))
                    && command.origin() instanceof CommandOrigin.Gameplay
                    && command.origin().machineId().equals(head.state().machineId())
                    && receipt.bodySha256().equals(ActionCodec.bodySha256(command))
                    && receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                    && receipt.state() instanceof ActionState.Settled settled
                    && settled.settlement() instanceof ActionState.Applied,
                    "original collection requires this exact canonical settled gameplay SAVE");
            var state = (ActionState.Settled) receipt.state();
            var attempt = state.attempt();
            if (!(state.dispatch() instanceof NativeActionPort.AckReceived ack))
                throw new IOException("settled SAVE has no original native acknowledgement");
            StrictJson.require(ack.nativeOk() && ack.requestId().equals(attempt.requestId())
                    && attempt.preparedRequest().step().equals("save-checkpoint")
                    && command.origin().acceptsGuard(attempt.guard().origin())
                    && attempt.guard().source().equals(command.source())
                    && attempt.guard().sessionId().equals(command.sessionId())
                    && attempt.guard().operation().equals(command.operation())
                    && ack.outbound().isPresent(), "original SAVE changed its prepared request, source, session or positive ACK");
            ack.custody().orElseThrow(() -> new IOException("original SAVE ACK custody is unavailable")).verify(ack);
            var requestRef = bound.requestReferenceOf(attempt.preparedRequest());
            var dispatchRef = bound.referenceOf(ack);
            var receiptRef = bound.receiptReferenceOf(receipt);
            StrictJson.require(bound.loadRequest(requestRef).equals(attempt.preparedRequest())
                    && bound.load(dispatchRef).equals(ack)
                    && bound.loadReceipt(receiptRef).equals(receipt), "original SAVE archive readback changed its complete receipt/Attempt/ACK");
            ActionEffects.validate(command, attempt, ack, state.settlement());
            var effect = ((ActionState.Applied) state.settlement()).observation();
            StrictJson.require(effect.source().equals(command.source())
                    && effect.sessionId().equals(command.sessionId())
                    && effect.observerSchema().equals(CheckpointRequestFactory.OBSERVER_SCHEMA)
                    && effect.supportingEvidence().size() == 2,
                    "original SAVE lacks its exact installed poststate and two immutable pair/Driver roles");
            byte[] pairBytes = bound.loadMaterial(effect.supportingEvidence().getFirst()).bytes();
            CheckpointPair pair = CheckpointPairCodec.decode(pairBytes);
            StrictJson.require(java.util.Arrays.equals(CheckpointPairCodec.encode(pair), pairBytes)
                    && pair.saveActionId().equals(actionId)
                    && pair.lineageId().equals(installed.lineageId())
                    && Path.of(pair.save().reference().path()).equals(installed.savePath()),
                    "original SAVE pair changed its action, complete body, configured path or lineage");
            requireCollectedContinuation(command.before(), pair.frame());
            requireCollectedContinuation(pair.frame(), effect.after());
            byte[] ackPacket = ack.originalPacket();
            StrictJson.require(pair.nativeAckRef().bytes() == ackPacket.length
                    && pair.nativeAckRef().sha256().equals(ActionCodec.sha256(ackPacket)),
                    "paired SAVE ACK differs from the actual original raw acknowledgement");
            FileWitness ackFile = files.observe(Path.of(pair.nativeAckRef().path()))
                    .orElseThrow(() -> new IOException("paired original SAVE ACK file is unavailable"));
            StrictJson.require(ackFile.reference().equals(pair.nativeAckRef())
                    && java.util.Arrays.equals(files.read(ackFile, ackPacket.length), ackPacket),
                    "paired original SAVE ACK physical readback changed");
            byte[] driverBytes = bound.loadMaterial(effect.supportingEvidence().get(1)).bytes();
            var savedDriver = drivers.readArchivedSnapshot(pair, driverBytes);
            StrictJson.require(java.util.Arrays.equals(savedDriver.encode(), driverBytes),
                    "original complete saved Driver archive differs from its exact bytes");
            var physicalDriver = drivers.readVerifiedOriginal(pair, savedDriver.session());
            StrictJson.require(java.util.Arrays.equals(physicalDriver.encode(), driverBytes),
                    "physical saved Driver differs from the original archived Driver");
            drivers.verify(pair);
            authority.require(same);
            StrictJson.require(same.head().digest().equals(head.digest())
                    && same.head().state().sequence() == head.state().sequence(),
                    "original SAVE collection changed its actual locked canonical head");
            requireCollectionTime(deadline);
            SeedAdoption seed = Objects.requireNonNull(seeds.freezeFirst(pair, receipt));
            requireCollectionTime(deadline);
            drivers.verify(pair);
            files.verify(ackFile);
            authority.require(same);
            StrictJson.require(same.head().digest().equals(head.digest())
                    && same.head().state().sequence() == head.state().sequence()
                    && ContinuityActionJournal.lookup(same.head().state(), actionId, bound).filter(receipt::equals).isPresent(),
                    "original SAVE collection no longer retains its identical canonical receipt/head");
            return new CheckpointResult.Confirmed(pair, pair.nativeAckRef(), pair.frame(), BigDecimal.ZERO, receipt, seed);
        } catch (IOException | IllegalArgumentException | java.io.UncheckedIOException failure) {
            return new CheckpointResult.Unknown(actionId, failure.toString(), Optional.of(receipt));
        }
    }
    private void requireCollectionTime(Instant deadline) throws IOException {
        if (Thread.currentThread().isInterrupted()) throw new IOException("original SAVE collection interrupted; no dispatch");
        if (!clock.instant().isBefore(deadline)) throw new IOException("original SAVE collection bounded read deadline expired; no dispatch");
    }
    private static void requireCollectedContinuation(ObservationIdentity before, ObservationIdentity after) {
        StrictJson.require(before.machineId().equals(after.machineId()) && before.game().equals(after.game())
                && before.frame().episodeRunId().equals(after.frame().episodeRunId())
                && before.frame().identity().player().equals(after.frame().identity().player())
                && before.frame().identity().dateRaw().equals(after.frame().identity().dateRaw())
                && before.observationVersion() == after.observationVersion()
                && after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) >= 0,
                "original SAVE pair crossed Game/episode/player/date/version or regressed its persistent native revision");
    }

    private CheckpointResult materialized(AttemptContext context,ActionReceipt receipt)throws IOException {
        CheckpointRequest request=Objects.requireNonNull(context).request;String id=request.saveCommand().actionId();
        StrictJson.require(receipt.command().actionId().equals(id)
                &&receipt.bodySha256().equals(ActionCodec.bodySha256(request.saveCommand()))
                &&java.util.Arrays.equals(ActionCodec.encodeCommand(receipt.command()),ActionCodec.encodeCommand(request.saveCommand())),
                "SAVE collection changed its original command identity or complete body");
        if(receipt.outcome()==ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH||receipt.outcome()==ActionReceipt.Outcome.REJECTED_CONFIRMED)
            return new CheckpointResult.Rejected(id,"native SAVE rejected",receipt);
        CheckpointPair pair=context.pair;
        if(receipt.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED||pair==null)
            return new CheckpointResult.Unknown(id,"SAVE ACK, physical pair or native poststate remains unconfirmed; never resubmit",Optional.of(receipt));
        drivers.verify(pair);
        SeedAdoption seed=Objects.requireNonNull(seeds.freezeFirst(pair,receipt));
        BigDecimal days=request.baseline().map(old->new BigDecimal(pair.frame().frame().identity().dateRaw().subtract(old.frame().frame().identity().dateRaw()))
                .divideToIntegralValue(BigDecimal.valueOf(24))).orElse(BigDecimal.ZERO);
        return new CheckpointResult.Confirmed(pair,pair.nativeAckRef(),pair.frame(),days,receipt,seed);
    }
    private Instant observationDeadline(ActionCommand command,AttemptContext context) {
        Instant actual=ActionObservationWindow.deadline(command);
        OriginalQuery query=originalQuery.get();
        if(query==null)return actual;
        StrictJson.require(query.context()==context
                &&command.actionId().equals(context.request.saveCommand().actionId())
                &&clock.instant().isBefore(query.deadline()),"SAVE query escaped its private original attempt or bounded read deadline");
        return actual.isBefore(query.deadline())?actual:query.deadline();
    }
    private CheckpointRequest.Readiness poststate(ActionCommand command,ActionState.Attempt attempt,AttemptContext context,NativeActionPort.AckReceived ack)
            throws IOException,InterruptedException {
        Instant deadline=observationDeadline(command,context);
        if(!ActionReconciliationScope.activeFor(command))return observations.observe(deadline);
        var held=ActionReconciliationScope.requireFrame(command,attempt);
        var identity=ActionReconciliationScope.requireIdentity(command,attempt);
        var push=ActionReconciliationScope.requireObservationGuard(command,attempt);
        StrictJson.require(clock.instant().isBefore(deadline)
                &&held.identity().equals(identity.factual())&&held.originalEvidence().equals(push.nativeEvidence()),
                "actual original SAVE poststate escaped its held reconciliation source or deadline");
        ActionPorts.OutcomeArchive archive;BorrowedSession sessions;CheckpointCommitVerifier.WriterLeaseVerifier authority;
        synchronized(this){archive=evidenceArchive;sessions=evidenceSession;authority=evidenceAuthority;}
        if(archive==null||sessions==null||authority==null)throw new IOException("same-writer SAVE original evidence archive is not installed");
        var same=sessions.current();authority.require(same);
        var original=archive.withSession(same).loadReceipt(identity.pending().originalReceipt());
        StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(command),ActionCodec.encodeCommand(original.command()))
                &&ActionTransitions.attempt(original.state()).filter(attempt::equals).isPresent()
                &&ActionTransitions.dispatch(original.state()).filter(ack::equals).isPresent(),
                "SAVE physical materialization requires the exact archived prepared request and positive original ACK");
        var semantic=held.semantic();
        return new CheckpointRequest.Readiness(held.identity(),held.source(),held.sessionId(),context.request.lineageId(),
                org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(semantic.get("map_ready"),"map_ready"),
                org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(semantic.get("paused"),"paused"),false,
                "actual held original SAVE effect data; no new SAVE or ordinary planning permission",
                held.originalEvidence(),held.observedAt());
    }
    @Override public ActionPorts.PostconditionResult observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        if (!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || ack.outbound().isEmpty()
                ||!ack.requestId().equals(attempt.requestId())||!attempt.preparedRequest().step().equals("save-checkpoint"))
            return new ActionPorts.Pending("actual positive Native SAVE ACK and original prepared outbound are absent", List.of());
        AttemptContext context = contexts.get(command.actionId());
        try {
            if (context == null) context = recoverColdContext(command, attempt, ack);
        } catch (IOException | IllegalArgumentException failure) {
            return new ActionPorts.Pending("original cold SAVE context pending: " + failure.getMessage(), List.of());
        }
        synchronized (context) {
            try {
                if (context.basis instanceof ColdAfterAck cold) requireColdScope(command, attempt, ack, cold);
                if (context.pair != null) return verifiedEffect(command, attempt, context.pair,ack);
                Optional<FileWitness> observed = files.observe(context.request.expectedSavePath());
                if (observed.isEmpty() || context.basis instanceof KnownBefore known
                        && known.file().filter(observed.orElseThrow()::equals).isPresent())
                    return new ActionPorts.Pending("SAVE physical file has not changed", List.of());
                FileWitness current = observed.orElseThrow();
                if (context.basis instanceof ColdAfterAck cold) {
                    java.math.BigInteger acknowledgedNs = java.math.BigInteger.valueOf(cold.acknowledgedAt().getEpochSecond())
                            .multiply(java.math.BigInteger.valueOf(1_000_000_000L))
                            .add(java.math.BigInteger.valueOf(cold.acknowledgedAt().getNano()));
                    if (new java.math.BigInteger(current.identity().mtimeNs()).compareTo(acknowledgedNs) <= 0)
                        return new ActionPorts.Pending("cold SAVE physical file does not postdate its original ACK",
                                diagnosticWitness(command, current, "cold_file_not_after_ack"));
                }
                if (current.reference().bytes() == 0) return new ActionPorts.Pending("SAVE physical file is still empty", diagnosticWitness(command, current, "empty_file"));
                if (current.reference().bytes() > MAXIMUM_SAVE_BYTES)
                    return new ActionPorts.Pending("SAVE physical file exceeds its independent finite observation budget", diagnosticWitness(command, current, "save_budget_exceeded"));
                if (!current.equals(context.prior)) { context.prior = current; return new ActionPorts.Pending("SAVE awaits second stable physical observation", diagnosticWitness(command, current, "first_stable_observation")); }
                var ready = poststate(command,attempt,context,ack); requireSavedFrame(command, attempt, ready, context.request.lineageId());
                ExactRef ackRef = publish(command.actionId() + "-ack.json", ack.originalPacket());
                DriverCheckpointStore.Anchor anchor = drivers.persist(command.actionId(), current, ready.observed(), context.request.lineageId());
                CheckpointPair pair = new CheckpointPair(current, anchor.driver(), ready.observed(), context.request.lineageId(), anchor.historyIndex(), command.actionId(), ackRef, clock.instant());
                drivers.verify(pair); publish(command.actionId() + "-pair.json", CheckpointPairCodec.encode(pair)); context.pair = pair;
                return verifiedEffect(command, attempt, pair,ack);
            } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); return new ActionPorts.Pending("SAVE poststate observation interrupted", List.of()); }
            catch (IOException | IllegalArgumentException failure) { return new ActionPorts.Pending("SAVE physical pair pending: " + failure.getMessage(), List.of()); }
        }
    }
    private AttemptContext recoverColdContext(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack) throws IOException {
        ColdBinding installed = coldBinding;
        if (installed == null || !ActionReconciliationScope.activeFor(command))
            throw new IOException("source-installed original SAVE reconciliation context unavailable; never submit");
        StrictJson.require(command.operation().equals(new OperationKey("save-checkpoint")), "cold recovery is only the original SAVE primitive");
        var identity = ActionReconciliationScope.requireIdentity(command, attempt);
        var custody = ack.custody().orElseThrow(() -> new IOException("original SAVE ACK chronology unavailable"));
        custody.verify(ack);
        ColdAfterAck basis = new ColdAfterAck(custody.responseReceived().observedAt(), identity.pending().originalReceipt());
        requireColdScope(command, attempt, ack, basis);
        // No historical pair or day accounting is reconstructed. This empty baseline is never a physical-before proof.
        CheckpointRequest request = new CheckpointRequest(command, installed.savePath(), installed.lineageId(), Optional.empty());
        AttemptContext created = new AttemptContext(request, basis);
        AttemptContext prior = contexts.putIfAbsent(command.actionId(), created);
        if (prior == null) return created;
        StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(command), ActionCodec.encodeCommand(prior.request.saveCommand())),
                "cold SAVE action ID changed its complete canonical command");
        return prior;
    }
    private void requireColdScope(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack, ColdAfterAck basis) throws IOException {
        StrictJson.require(ActionReconciliationScope.activeFor(command), "cold SAVE escaped its original reconciliation callback");
        var identity = ActionReconciliationScope.requireIdentity(command, attempt);
        var provenance = ActionReconciliationScope.requireProvenance(command, attempt);
        StrictJson.require(provenance instanceof ObservationProvenance.FreshSnapshotQuery query
                && query.basis() instanceof ObservationProvenance.ColdAfterAcknowledgement cold
                && cold.originalReceipt().equals(identity.pending().originalReceipt()), "cold SAVE needs this current canonical original ACK's actual independent READ");
        ActionPorts.OutcomeArchive archive; BorrowedSession sessions; CheckpointCommitVerifier.WriterLeaseVerifier authority;
        synchronized (this) { archive = evidenceArchive; sessions = evidenceSession; authority = evidenceAuthority; }
        if (archive == null || sessions == null || authority == null) throw new IOException("same-writer original SAVE archive unavailable");
        var same = sessions.current(); authority.require(same);
        var original = archive.withSession(same).loadReceipt(basis.originalReceipt());
        StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(command), ActionCodec.encodeCommand(original.command()))
                && ActionTransitions.attempt(original.state()).filter(attempt::equals).isPresent()
                && ActionTransitions.dispatch(original.state()).filter(ack::equals).isPresent(), "cold SAVE changed canonical prepared command/Attempt/ACK");
        var current = archive.withSession(same).loadReceipt(identity.pending().originalReceipt());
        StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(command), ActionCodec.encodeCommand(current.command()))
                && ActionTransitions.attempt(current.state()).filter(attempt::equals).isPresent()
                && ActionTransitions.dispatch(current.state()).filter(ack::equals).isPresent(),
                "cold SAVE current canonical observation no longer retains the same original command/Attempt/ACK");
        var custody = ack.custody().orElseThrow(() -> new IOException("original SAVE ACK chronology unavailable")); custody.verify(ack);
        StrictJson.require(custody.responseReceived().observedAt().equals(basis.acknowledgedAt()), "cold SAVE original acknowledgement time changed");
        authority.require(same);
    }
    private ObservationProvenance actualProvenance(ActionCommand command, ActionState.Attempt attempt,
            CheckpointRequest.Readiness ready, byte[] nativePacket) throws IOException {
        ObservationProvenance provenance;
        if (ActionReconciliationScope.activeFor(command)) {
            provenance = ActionReconciliationScope.requireProvenance(command, attempt);
        } else {
            var packet = ContinuityJson.parseObject(java.util.Arrays.copyOfRange(nativePacket, 4, nativePacket.length), nativePacket.length);
            if (packet.has("read_request_id")) throw new IOException("correlated SAVE READ lacks its source-qualified original provenance");
            provenance = new ObservationProvenance.Push(ready.observed().frame().snapshotId(), ready.observed().frame().identity().nativeRevision(), ready.nativeEvidence());
        }
        provenance.validate(ready.observed(), ready.nativeEvidence());
        return provenance;
    }
    private ActionPorts.PostconditionResult verifiedEffect(ActionCommand command, ActionState.Attempt attempt, CheckpointPair pair,NativeActionPort.AckReceived ack) throws IOException, InterruptedException {
        drivers.verify(pair); var ready = poststate(command,attempt,Objects.requireNonNull(contexts.get(command.actionId())),ack); requireSavedFrame(command, attempt, ready, pair.lineageId());
        ActionPorts.OutcomeArchive archive; BorrowedSession sessions; CheckpointCommitVerifier.WriterLeaseVerifier authority;
        synchronized(this){archive=evidenceArchive;sessions=evidenceSession;authority=evidenceAuthority;}
        if(archive==null||sessions==null||authority==null)throw new IOException("same-writer SAVE original archive is not installed");
        var same=sessions.current();authority.require(same);var bound=archive.withSession(same);
        byte[] nativePacket=bound.loadNativeFrame(ready.nativeEvidence());
        StrictJson.require(nativePacket.length>4,"actual archived post-SAVE native frame is absent");
        RawJson pairMaterial=new RawJson(CheckpointPairCodec.encode(pair));ExactRef proof=bound.preserveMaterial(pairMaterial);
        byte[] savedDriverBytes=files.read(pair.driver(),DriverCheckpointStore.MAX_DRIVER_BYTES);drivers.readArchivedSnapshot(pair,savedDriverBytes);
        RawJson savedDriverMaterial=new RawJson(savedDriverBytes);ExactRef savedDriver=bound.preserveMaterial(savedDriverMaterial);
        StrictJson.require(savedDriverMaterial.equals(bound.loadMaterial(savedDriver)),"actual complete saved Driver archive readback differs");
        StrictJson.require(pairMaterial.equals(bound.loadMaterial(proof)),"actual paired SAVE material archive readback differs");
        List<ExpectedValue> actual = List.of(new ExpectedInteger(new FieldKey("date_raw"), ready.observed().frame().identity().dateRaw()),
                new ExpectedInteger(new FieldKey("played_character_id"), ready.observed().frame().identity().player()), new ExpectedBoolean(new FieldKey("checkpoint_pair_verified"), true));
        return new ActionPorts.EffectObserved(new ActionState.EffectObservation(ready.observed(), command.source(), ready.sessionId(), CheckpointRequestFactory.OBSERVER_SCHEMA,
                actual, actualProvenance(command, attempt, ready, nativePacket), ready.observedAt(), ready.nativeEvidence(),
                List.of(proof,savedDriver)));
    }
    private static void requireSavedFrame(ActionCommand command, ActionState.Attempt attempt, CheckpointRequest.Readiness ready, String lineage) throws IOException {
        var before = command.before(); var after = ready.observed();
        boolean actualColdReconnect = false;
        if (ActionReconciliationScope.activeFor(command)) {
            var identity = ActionReconciliationScope.requireIdentity(command, attempt);
            var provenance = ActionReconciliationScope.requireProvenance(command, attempt);
            actualColdReconnect = identity.connectionGeneration().compareTo(attempt.guard().connectionGeneration()) > 0
                    && provenance instanceof ObservationProvenance.FreshSnapshotQuery query
                    && query.basis() instanceof ObservationProvenance.ColdAfterAcknowledgement cold
                    && cold.originalReceipt().equals(identity.pending().originalReceipt());
            if (actualColdReconnect) {
                StrictJson.require(ActionReconciliationScope.requireFrame(command, attempt).identity().equals(after)
                        && identity.nativeEvidence().equals(ready.nativeEvidence()), "cold SAVE public reset requires the actual held original frame");
                provenance.validate(after, ready.nativeEvidence());
            }
        }
        StrictJson.require(before.machineId().equals(after.machineId()) && before.game().equals(after.game()) && command.sessionId().equals(ready.sessionId())
                && command.source().equals(ready.source()) && lineage.equals(ready.lineageId()) && ready.mapReady() && ready.paused()
                && before.frame().episodeRunId().equals(after.frame().episodeRunId()) && before.frame().identity().player().equals(after.frame().identity().player())
                && before.frame().identity().dateRaw().equals(after.frame().identity().dateRaw())
                && (actualColdReconnect || after.frame().revision().compareTo(before.frame().revision()) >= 0)
                && after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) >= 0,
                "native SAVE poststate crossed Game/session/source/date/actor/episode/lineage");
    }
    /** Immutable UNKNOWN diagnostic DATA. It cannot qualify a physical pair or replace a later file observation. */
    private List<ExactRef> diagnosticWitness(ActionCommand command, FileWitness witness, String phase) throws IOException {
        ActionPorts.OutcomeArchive archive;BorrowedSession sessions;CheckpointCommitVerifier.WriterLeaseVerifier authority;
        synchronized(this){archive=evidenceArchive;sessions=evidenceSession;authority=evidenceAuthority;}
        if(archive==null||sessions==null||authority==null)return List.of();
        var same=sessions.current();authority.require(same);var bound=archive.withSession(same);
        ObjectNode row=StrictJson.object();row.put("schema","xar.java-checkpoint-diagnostic-witness/v1");
        row.put("action_id",command.actionId());row.put("action_body_sha256",ActionCodec.bodySha256(command));
        row.put("phase",phase);row.set("witness",CheckpointPairCodec.fileWitnessToJson(witness));
        byte[] canonical=ContinuityJson.canonical(row);
        StrictJson.require(canonical.length<=MAXIMUM_DIAGNOSTIC_WITNESS_BYTES,"finite original SAVE diagnostic witness required");
        RawJson material=new RawJson(canonical);ExactRef original=bound.preserveMaterial(material);
        StrictJson.require(original.bytes()==canonical.length && original.sha256().equals(ActionCodec.sha256(canonical))
                && material.equals(bound.loadMaterial(original)),"immutable SAVE diagnostic witness archive differs");
        authority.require(same);return List.of(original);
    }

    private ExactRef publish(String name, byte[] raw) throws IOException {
        Path path = evidenceRoot.resolve(name); var existing = files.observe(path);
        if (existing.isPresent()) {
            if (!existing.orElseThrow().reference().sha256().equals(DriverCheckpointStore.sha256(raw))) throw new IOException("immutable checkpoint evidence conflict");
            return existing.orElseThrow().reference();
        }
        return files.createNew(path, raw).reference();
    }
}
