package org.xar.ck3.control.application.checkpoint;

import java.io.IOException;
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
    @FunctionalInterface public interface SeedAdoptionPort { SeedAdoption freezeFirst(CheckpointPair pair, ActionReceipt appliedSave) throws IOException; }
    private static final class AttemptContext {
        private final CheckpointRequest request; private final Optional<FileWitness> before;
        private FileWitness prior; private volatile CheckpointPair pair;
        private AttemptContext(CheckpointRequest request, Optional<FileWitness> before) { this.request = request; this.before = before; }
    }
    private final CheckpointFiles files; private final DriverCheckpointStore drivers; private final CheckpointRequest.ObservationPort observations;
    private final Path evidenceRoot; private final Clock clock; private final SeedAdoptionPort seeds; private volatile ActionCoordinatorPort actions;
    @FunctionalInterface public interface BorrowedSession { org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session current() throws IOException; }
    private ActionPorts.OutcomeArchive evidenceArchive;
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
            AttemptContext original = new AttemptContext(request, files.observe(request.expectedSavePath()));
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
        if(context==null)return new CheckpointResult.Unknown(originalActionId,"original private SAVE context is unavailable; never submit",Optional.empty());
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
        AttemptContext context = contexts.get(command.actionId());
        if (context == null) return new ActionPorts.Pending("original SAVE context unavailable; do not submit again", List.of());
        if (!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || ack.outbound().isEmpty()
                ||!ack.requestId().equals(attempt.requestId())||!attempt.preparedRequest().step().equals("save-checkpoint"))
            return new ActionPorts.Pending("actual positive Native SAVE ACK and original prepared outbound are absent", List.of());
        synchronized (context) {
            try {
                if (context.pair != null) return verifiedEffect(command, attempt, context.pair,ack);
                Optional<FileWitness> observed = files.observe(context.request.expectedSavePath());
                if (observed.isEmpty() || context.before.filter(observed.orElseThrow()::equals).isPresent()) return new ActionPorts.Pending("SAVE physical file has not changed", List.of());
                FileWitness current = observed.orElseThrow();
                if (current.reference().bytes() == 0) return new ActionPorts.Pending("SAVE physical file is still empty", List.of(current.reference()));
                if (!current.equals(context.prior)) { context.prior = current; return new ActionPorts.Pending("SAVE awaits second stable physical observation", List.of(current.reference())); }
                var ready = poststate(command,attempt,context,ack); requireSavedFrame(command, ready, context.request.lineageId());
                ExactRef ackRef = publish(command.actionId() + "-ack.json", ack.originalPacket());
                DriverCheckpointStore.Anchor anchor = drivers.persist(command.actionId(), current, ready.observed(), context.request.lineageId());
                CheckpointPair pair = new CheckpointPair(current, anchor.driver(), ready.observed(), context.request.lineageId(), anchor.historyIndex(), command.actionId(), ackRef, clock.instant());
                drivers.verify(pair); publish(command.actionId() + "-pair.json", CheckpointPairCodec.encode(pair)); context.pair = pair;
                return verifiedEffect(command, attempt, pair,ack);
            } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); return new ActionPorts.Pending("SAVE poststate observation interrupted", List.of()); }
            catch (IOException | IllegalArgumentException failure) { return new ActionPorts.Pending("SAVE physical pair pending: " + failure.getMessage(), List.of()); }
        }
    }
    private ActionPorts.PostconditionResult verifiedEffect(ActionCommand command, ActionState.Attempt attempt, CheckpointPair pair,NativeActionPort.AckReceived ack) throws IOException, InterruptedException {
        drivers.verify(pair); var ready = poststate(command,attempt,Objects.requireNonNull(contexts.get(command.actionId())),ack); requireSavedFrame(command, ready, pair.lineageId());
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
                actual, new ObservationProvenance.Push(ready.observed().frame().snapshotId(),ready.observed().frame().identity().nativeRevision(),ready.nativeEvidence()), ready.observedAt(), ready.nativeEvidence(),
                List.of(proof,savedDriver)));
    }
    private static void requireSavedFrame(ActionCommand command, CheckpointRequest.Readiness ready, String lineage) {
        var before = command.before(); var after = ready.observed();
        StrictJson.require(before.machineId().equals(after.machineId()) && before.game().equals(after.game()) && command.sessionId().equals(ready.sessionId())
                && command.source().equals(ready.source()) && lineage.equals(ready.lineageId()) && ready.mapReady() && ready.paused()
                && before.frame().episodeRunId().equals(after.frame().episodeRunId()) && before.frame().identity().player().equals(after.frame().identity().player())
                && before.frame().identity().dateRaw().equals(after.frame().identity().dateRaw())
                && after.frame().revision().compareTo(before.frame().revision()) >= 0 && after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) >= 0,
                "native SAVE poststate crossed Game/session/source/date/actor/episode/lineage");
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
