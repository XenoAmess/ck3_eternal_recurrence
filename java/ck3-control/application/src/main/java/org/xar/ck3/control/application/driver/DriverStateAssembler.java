package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionSnapshotReader;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.session.FrozenDriverSnapshotSupplier;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Complete Driver producer on the existing coordinator/writer lease; never a physical store or second writer. */
public final class DriverStateAssembler implements FrozenDriverSnapshotSupplier.StateAuthority, DriverObservationFacts.Reader {
    public synchronized void bindEarlyExecuteFailureSource(org.xar.ck3.control.application.history.DriverEarlyExecuteFailure.Source actual,
            ActionPorts.OutcomeArchive archive,org.xar.ck3.control.application.action.RootReadContractCatalog catalog){
        Objects.requireNonNull(actual);actual.requireOwner(this,actual.journal(),archive,catalog);
        StrictJson.require(earlyFailureSource==null||earlyFailureSource==actual,"another private early failure issuer bound");earlyFailureSource=actual;
    }
    public synchronized void requireEarlyExecuteFailureSource(org.xar.ck3.control.application.history.DriverEarlyExecuteFailure.Source actual){
        StrictJson.require(actual!=null&&earlyFailureSource==actual,"actual once-installed early issuer required");
    }
    public record Frozen(DriverSnapshotFacts.State state, ActionJournal.Snapshot actions, Optional<String> activeActionId) { }
    @FunctionalInterface public interface DriverWork<T> { T run(Frozen frozen) throws IOException; }
    public record FrozenObservation(DriverSnapshotFacts.Known state, ActionJournal.Snapshot actions,
            Optional<String> activeActionId, DriverObservationFacts facts) {
        public FrozenObservation {
            Objects.requireNonNull(state); Objects.requireNonNull(actions); Objects.requireNonNull(activeActionId); Objects.requireNonNull(facts);
            StrictJson.require(state.stamp().driverVersion()==facts.driverVersion()
                    && state.stamp().episodeEpoch()==facts.episodeEpoch()
                    && Arrays.equals(state.driver().encode(),facts.driver().encode()),"frozen semantic facts crossed complete Driver version");
        }
        public DriverStateSnapshot projection() { return projectObservation(state,actions,activeActionId); }
        public Frozen driver() { return new Frozen(state,actions,activeActionId); }
    }
    @FunctionalInterface public interface ObservationWork<T> { T run(FrozenObservation frozen) throws IOException; }
    private org.xar.ck3.control.application.history.DriverEarlyExecuteFailure.Source earlyFailureSource;
    private final ActionSnapshotReader actions;
    private org.xar.ck3.control.application.action.PhysicalActionRegistry presentationSource;
    private static final ThreadLocal<org.xar.ck3.control.application.action.PhysicalActionRegistry.VerifiedPresentations> verifiedPresentation=new ThreadLocal<>();
    public synchronized void bindPresentationSource(org.xar.ck3.control.application.action.PhysicalActionRegistry actual){
        StrictJson.require(presentationSource==null||presentationSource==actual,"Driver presentation source cannot be replaced");
        presentationSource=Objects.requireNonNull(actual);
    }
    @FunctionalInterface private interface PresentationWork<T>{T run()throws IOException;}
    private <T>T presentationScope(ActionJournal.Snapshot snapshot,PresentationWork<T> work)throws IOException{
        var source=presentationSource;if(source==null)return work.run();
        var before=verifiedPresentation.get();var scope=source.verified(checkpointArchive(null).session(),snapshot);
        verifiedPresentation.set(scope);
        try{return work.run();}finally{if(before==null)verifiedPresentation.remove();else verifiedPresentation.set(before);}
    }
    private final DriverFactsRepository facts;
    private final DriverObservationFacts.Reader observationProducer;
    private final ThreadLocal<Integer> readFreezeDepth=ThreadLocal.withInitial(() -> 0);
    /** Private custody for this exact raw observation callback; no DATA constructor or public callback can mint it. */
    private final ThreadLocal<RawCheckpointContext> rawCheckpointContext=new ThreadLocal<>();
    private final ThreadLocal<PlanningReadCallbackScope> planningReadCallback=new ThreadLocal<>();
    /** Custody for one actual observation callback. Only the assembler creates this token. */
    public final class PlanningReadCallbackScope {
        private final ContinuityStorePort.Session same;private final String head;
        private PlanningReadCallbackScope(ContinuityStorePort.Session same,String head){this.same=same;this.head=head;}
        public void requireCurrent(ContinuityStorePort.Session actual)throws IOException {
            StrictJson.require(planningReadCallback.get()==this&&same==actual&&head.equals(actual.head().digest()),
                    "public planning read callback left its actual writer/observation scope");
        }
    }
    public Optional<PlanningReadCallbackScope> currentPlanningReadCallback(ContinuityStorePort.Session same)throws IOException {
        var current=planningReadCallback.get();if(current==null)return Optional.empty();current.requireCurrent(same);return Optional.of(current);
    }
    private static final class RawCheckpointContext {
        private final ContinuityStorePort.Session session;private final NativeObservationPort.ObservedFrame nativeFrame;
        private final DriverSnapshotFacts.Known before;private final DriverObservationFacts completed;private final String head;
        private RawCheckpointPublication publication;
        private RawCheckpointContext(ContinuityStorePort.Session session,NativeObservationPort.ObservedFrame nativeFrame,
                DriverSnapshotFacts.Known before,DriverObservationFacts completed,String head) {
            this.session=session;this.nativeFrame=nativeFrame;this.before=before;this.completed=completed;this.head=head;
        }
    }
    private record RawCheckpointOpening(RawCheckpointContext context,ActionReceipt action,
            org.xar.ck3.control.application.action.ActionState.Attempt attempt,
            org.xar.ck3.control.application.action.NativeActionPort.AckReceived ack,ExactRef originalAck,
            DriverObservationAssembler.Complete heldFrame) { }
    private record RawCheckpointPublication(RawCheckpointOpening opening,DriverSnapshotFacts.Known after,
            ExactRef originalRow,ExactRef originalSave) { }
    private record CheckpointArchive(ContinuityStorePort.Session session,ActionPorts.OutcomeArchive originals) { }
    private void requireNoRawObservationMutation() {
        StrictJson.require(rawCheckpointContext.get()==null,"an immutable raw observation permits only its private original-SAVE publication");
    }
    private CheckpointArchive checkpointArchive(ContinuityStorePort.Session required) {
        synchronized(this) {
            CandidateScope staged=candidateScope.get();
            if(pendingNextCapabilityTransfer!=null)StrictJson.require(staged!=null&&staged.transfer()==pendingNextCapabilityTransfer,"NEXT SAVE requires its explicit candidate archive/session scope");
            ContinuityStorePort.Session same;ActionPorts.OutcomeArchive originals;
            if(staged!=null) {same=Objects.requireNonNull(staged.sessions().get());StrictJson.require(same==staged.session(),"NEXT SAVE crossed its borrowed Session");originals=staged.archive().withSession(same);}
            else {StrictJson.require(historyArchive!=null&&historySession!=null,"actual SAVE archive is unbound");same=Objects.requireNonNull(historySession.get());originals=historyArchive.withSession(same);}
            StrictJson.require(required==null||required==same,"nested SAVE publication crossed its original raw writer Session");return new CheckpointArchive(same,originals);
        }
    }
    private RawCheckpointOpening checkpointOpening(RawCheckpointContext context,DriverSnapshotFacts.Known known,
            ActionSnapshotReader.Lease lease) throws IOException {
        StrictJson.require(rawCheckpointContext.get()==context&&context.publication==null&&known==context.before,
                "nested SAVE requires its identical opening Driver and one unused raw scope");
        String actionId=lease.activeActionId().orElseThrow(()->new IllegalArgumentException("original SAVE action scope absent"));
        ActionReceipt action=lease.find(actionId).orElseThrow();var command=action.command();
        StrictJson.require(command.operation().value().equals("save-checkpoint")&&command.origin() instanceof CommandOrigin.Gameplay&&!action.settled(),
                "only the actual original unresolved SAVE can publish inside this raw observation");
        var attempt=org.xar.ck3.control.application.action.ActionTransitions.attempt(action.state()).orElseThrow();
        var dispatch=org.xar.ck3.control.application.action.ActionTransitions.dispatch(action.state()).orElseThrow();
        StrictJson.require(dispatch instanceof org.xar.ck3.control.application.action.NativeActionPort.AckReceived,"original SAVE ACK is unavailable");
        var ack=(org.xar.ck3.control.application.action.NativeActionPort.AckReceived)dispatch;
        StrictJson.require(ack.nativeOk()&&ack.outbound().isPresent()&&ack.requestId().equals(attempt.requestId())
                &&attempt.preparedRequest().step().equals("save-checkpoint"),"positive original SAVE ACK/prepared Attempt required");
        var held=org.xar.ck3.control.application.action.ActionReconciliationScope.requireFrame(command,attempt);
        var identity=org.xar.ck3.control.application.action.ActionReconciliationScope.requireIdentity(command,attempt);
        var guard=org.xar.ck3.control.application.action.ActionReconciliationScope.requireObservationGuard(command,attempt);
        StrictJson.require(context.session.head().digest().equals(context.head)&&lease.snapshot().headSha256().equals(context.head)
                &&identity.factual().equals(held.identity())&&guard.nativeEvidence().equals(held.originalEvidence())
                &&held.originalEvidence().bytes()==context.nativeFrame.originalPacket().length
                &&held.originalEvidence().sha256().equals(DriverJson.sha256(context.nativeFrame.originalPacket())),
                "nested SAVE lost its original writer head or held raw Native packet");
        var assembled=new DriverObservationAssembler().assemble(context.nativeFrame,context.completed,held.originalEvidence());
        StrictJson.require(assembled instanceof DriverObservationAssembler.Complete&&assembled.equals(held),
                "nested SAVE held frame differs from this exact original Native/Driver observation");
        var originals=checkpointArchive(context.session).originals();
        // The actual archive loader replays the sole protocol decoder's prepared/outbound binding, including request/step/revision/arguments.
        ExactRef originalReceipt=originals.receiptReferenceOf(action);
        StrictJson.require(identity.pending().originalReceipt().equals(originalReceipt)&&originals.loadReceipt(originalReceipt).equals(action),
                "original canonical SAVE receipt/outbound archive differs");
        ExactRef originalAck=originals.referenceOf(ack);StrictJson.require(originals.load(originalAck).equals(ack),"original SAVE ACK archive differs");
        lease.assertCurrent();return new RawCheckpointOpening(context,action,attempt,ack,originalAck,held);
    }
    @FunctionalInterface public interface CapabilityObservation {
        Optional<DriverCapabilityStateProducer.InitialAuxiliary> observe(NativeObservationPort.ObservedFrame actual,DriverSnapshotFacts.Known current);
    }
    private CapabilityObservation capabilityObservation;
    private ActionPorts.OutcomeArchive historyArchive;
    private java.util.function.Supplier<ContinuityStorePort.Session> historySession;
    private NextCapabilityTransfer pendingNextCapabilityTransfer;
    private record CandidateScope(ContinuityStorePort.Session session,NextCapabilityTransfer transfer,CapabilityObservation observation,
            ActionPorts.OutcomeArchive archive,java.util.function.Supplier<ContinuityStorePort.Session> sessions) { }
    private final ThreadLocal<CandidateScope> candidateScope=new ThreadLocal<>();
    @FunctionalInterface public interface CandidateWork<T> { T run() throws IOException; }
    public DriverStateAssembler(ActionSnapshotReader actions, DriverFactsRepository facts,
            DriverObservationFacts.Reader actualObservationFactsProducer) {
        this.actions=Objects.requireNonNull(actions); this.facts=Objects.requireNonNull(facts);
        observationProducer=Objects.requireNonNull(actualObservationFactsProducer);
    }
    public synchronized void bindCapabilityObservation(CapabilityObservation actualProducer) {
        StrictJson.require(capabilityObservation==null,"one actual capability observation producer required");
        capabilityObservation=Objects.requireNonNull(actualProducer);
    }
    public synchronized void bindHistoryArchive(ActionPorts.OutcomeArchive actualArchive,java.util.function.Supplier<ContinuityStorePort.Session> originalSession) {
        StrictJson.require(historyArchive==null,"one actual history archive owner required");historyArchive=Objects.requireNonNull(actualArchive);historySession=Objects.requireNonNull(originalSession);
    }


    private record PreclockSourceBinding(DriverPreclockExpectationSource source,List<ExactRef> sources) { }
    private PreclockSourceBinding preclockExpectationSource;
    /** Root binds its actual installed natural-original producer; data cannot supply an alternative source. */
    public synchronized void bindPreclockExpectationSource(DriverPreclockExpectationSource actual) {
        Objects.requireNonNull(actual);
        if(preclockExpectationSource!=null&&preclockExpectationSource.source()==actual)return;
        List<ExactRef> sources=List.copyOf(actual.sources());
        StrictJson.require(!sources.isEmpty()&&sources.size()<=64&&sources.stream().distinct().count()==sources.size()
                &&sources.stream().allMatch(ref->ref.bytes()>0),"finite actual preclock source closure required");
        var binding=new PreclockSourceBinding(actual,sources);
        if(pendingNextCapabilityTransfer!=null&&!pendingNextCapabilityTransfer.activated) {
            var transfer=pendingNextCapabilityTransfer;
            StrictJson.require(transfer.preclockSource==null||transfer.preclockSource.source()==actual,"NEXT preclock source already has another candidate owner");
            transfer.preclockSource=binding;return;
        }
        StrictJson.require(preclockExpectationSource==null,"preclock expectation source belongs to another installed owner");
        preclockExpectationSource=binding;
    }
    /** Uses the private live committed capture of the installed source; never dispatches, observes or rewrites an action. */
    public void publishPreclockExpectation(ContinuityStorePort.Session same) throws IOException {
        requireOutsideObservationScope(same);PreclockSourceBinding installed;ActionPorts.OutcomeArchive originals;
        synchronized(this) {
            installed=preclockExpectationSource;
            StrictJson.require(installed!=null&&historyArchive!=null&&pendingNextCapabilityTransfer==null,
                    "actual active installed preclock source/archive required; staged NEXT cannot publish ordinary expectation");
            originals=historyArchive.withSession(same);
        }
        StrictJson.require(installed.source().sources().equals(installed.sources()),"installed preclock source closure changed");
        DriverPreclockExpectationSource.Capture actual=Objects.requireNonNull(installed.source().current(same,this));
        installed.source().requireCurrent(same,this,actual);
        var publication=DriverPreclockExpectationProducer.prepare(same,actual,originals,installed.sources());
        // The canonical natural-domain commit is already durable. This is its deterministic, source-bound full Driver projection.
        try { actions.withFrozen(same,lease -> facts.locked(state -> {
            lease.assertCurrent();
            StrictJson.require(state==publication.before(),"preclock expectation crossed its exact current full Driver owner");
            var before=publication.before();var expected=before.stamp();var afterDriver=publication.replacement();
            var afterStamp=new DriverSnapshotFacts.Stamp(Math.addExact(expected.driverVersion(),1),expected.episodeEpoch(),
                    expected.game(),expected.episodeRunId(),DriverJson.sha256(afterDriver.encode()));
            var after=new DriverSnapshotFacts.Known(afterDriver,afterStamp,before.originalHistoryBasis(),before.actionRows(),
                    publication.auxiliary(),before.loop(),Optional.empty());
            try { installed.source().requireCurrent(same,this,actual); }
            catch(IOException failure) { throw new UncheckedIOException(failure); }
            lease.assertCurrent();
            requireNoRawObservationMutation();facts.compareAndSet(expected,after);return null;
        })); } catch(UncheckedIOException failure) { throw failure.getCause(); }
    }

    private record OperatorSourceBinding(DriverOperatorRebindSource source,List<ExactRef> sources) { }
    private OperatorSourceBinding operatorRebindSource;
    /** Installs the sole private Root operator issuer. An arbitrary replacement or receipt cannot bind itself. */
    public synchronized void bindOperatorRebindSource(DriverOperatorRebindSource actual) {
        Objects.requireNonNull(actual);
        if(operatorRebindSource!=null&&operatorRebindSource.source()==actual)return;
        List<ExactRef> sources=List.copyOf(actual.sources());
        StrictJson.require(!sources.isEmpty()&&sources.size()<=128&&sources.stream().distinct().count()==sources.size()
                &&sources.stream().allMatch(ref->ref.bytes()>0),"finite exact installed operator source closure required");
        var binding=new OperatorSourceBinding(actual,sources);
        if(pendingNextCapabilityTransfer!=null&&!pendingNextCapabilityTransfer.activated) {
            var transfer=pendingNextCapabilityTransfer;
            StrictJson.require(transfer.operatorSource==null||transfer.operatorSource.source()==actual,"NEXT operator source has another candidate issuer");
            transfer.operatorSource=binding;return;
        }
        StrictJson.require(operatorRebindSource==null,"one active operator issuer required");operatorRebindSource=binding;
    }
    /** This constructor is private: only the actual source-bound canonical Window/CAS path can issue a publication. */
    public static final class PublishedOperatorRebind {
        private final DriverStateAssembler owner;private final OperatorSourceBinding installed;
        private final DriverOperatorRebindSource.Capture capture;private final DriverOperatorRebindProducer.Publication actual;
        private PublishedOperatorRebind(DriverStateAssembler owner,OperatorSourceBinding installed,
                DriverOperatorRebindSource.Capture capture,DriverOperatorRebindProducer.Publication actual) {
            this.owner=owner;this.installed=installed;this.capture=capture;this.actual=actual;
        }
        public DriverSnapshotFacts.Known before(){return actual.before();}
        public DriverSnapshotFacts.Known after(){return actual.after();}
        public WriterContracts.Receipt actualReceipt(){return capture.actualReceipt();}
        public ExactRef originalSource(){return actual.originalSource();}
        public ExactRef originalDriver(){return actual.originalDriver();}
        public PublishedOperatorRebind requireCurrent(ContinuityStorePort.Session same) throws IOException {
            owner.requirePublishedOperatorRebind(same,this);return this;
        }
    }
    /** The changed-actor Window commit must already be durable; publication leaves every immutable observation scope first. */
    public PublishedOperatorRebind publishOperatorRebind(ContinuityStorePort.Session same) throws IOException {
        requireOutsideObservationScope(same);OperatorSourceBinding installed;ActionPorts.OutcomeArchive originals;
        synchronized(this) {
            installed=operatorRebindSource;
            StrictJson.require(installed!=null&&historyArchive!=null&&pendingNextCapabilityTransfer==null,"active installed operator source/archive required");
            originals=historyArchive.withSession(same);
        }
        StrictJson.require(installed.source().sources().equals(installed.sources()),"operator installed source closure changed");
        var capture=Objects.requireNonNull(installed.source().current(same,this));installed.source().requireCurrent(same,this,capture);
        final PublishedOperatorRebind[] result=new PublishedOperatorRebind[1];
        try {actions.withFrozen(same,lease->facts.locked(state->{
            StrictJson.require(state==capture.actualKnown(),"operator lost its identical full Driver predecessor");
            var canonical=lease.find(capture.originalCommand().actionId()).orElseThrow();
            DriverOperatorRebindProducer.Publication publication;
            try {
                publication=DriverOperatorRebindProducer.prepare(same,capture,originals,installed.sources(),canonical);
                installed.source().requireCurrent(same,this,capture);
            }catch(IOException failure){throw new UncheckedIOException(failure);}
            synchronized(this){StrictJson.require(operatorRebindSource==installed&&pendingNextCapabilityTransfer==null,"operator issuer ownership changed");}
            var proof=new PublishedOperatorRebind(this,installed,capture,publication);
            lease.assertCurrent();requireNoRawObservationMutation();facts.compareAndSet(publication.before().stamp(),publication.after());
            result[0]=proof;return null;
        }));}catch(UncheckedIOException failure){throw failure.getCause();}
        return Objects.requireNonNull(result[0]);
    }
    private void requirePublishedOperatorRebind(ContinuityStorePort.Session same,PublishedOperatorRebind proof) throws IOException {
        StrictJson.require(proof.owner==this,"operator publication belongs to another Driver authority");
        synchronized(this){StrictJson.require(operatorRebindSource==proof.installed&&pendingNextCapabilityTransfer==null,"operator issuer is no longer active");}
        StrictJson.require(proof.installed.source().sources().equals(proof.installed.sources()),"operator installed source closure changed");
        DriverOperatorRebindProducer.requireCommitted(same,proof.capture,proof.installed.sources(),false);
        withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual operator Driver unavailable");
            var current=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(current.stamp().equals(proof.after().stamp())&&Arrays.equals(current.driver().encode(),proof.after().driver().encode())
                    &&current.auxiliary().equals(proof.after().auxiliary()),"operator publication no longer names the actual exact Driver/auxiliary");
            proof.installed.source().requirePublished(same,this,proof.capture,current);return null;
        });
    }

    private record PendingEpisodeSourceBinding(DriverPendingEpisodeSource source,List<ExactRef> sources) { }
    private PendingEpisodeSourceBinding pendingEpisodeSource;
    private static final class PendingChildScope {
        private final DriverStateAssembler owner;private final PendingEpisodeSourceBinding installed;
        private final PendingEpisodePublication publication;private final ActionCommand parent,child;private final ContinuityStorePort.Session session;
        private DriverSnapshotFacts.Known expected;
        private PendingChildScope(DriverStateAssembler owner,PendingEpisodeSourceBinding installed,PendingEpisodePublication publication,
                ActionCommand parent,ActionCommand child,ContinuityStorePort.Session session) {
            this.owner=owner;this.installed=installed;this.publication=publication;this.parent=parent;this.child=child;this.session=session;expected=publication.after();
        }
        private DriverStateAssembler owner(){return owner;}private PendingEpisodeSourceBinding installed(){return installed;}
        private PendingEpisodePublication publication(){return publication;}private ActionCommand parent(){return parent;}
        private ActionCommand child(){return child;}private ContinuityStorePort.Session session(){return session;}
    }
    private static final ThreadLocal<PendingChildScope> pendingChildScope=new ThreadLocal<>();
    @FunctionalInterface public interface PendingWork<T>{T run() throws IOException;}
    public sealed interface PendingEpisodePublication permits PublishedPending,PublishedPendingMutation,RecoveredPending {
        DriverSnapshotFacts.Known before();
        DriverSnapshotFacts.Known after();
        ExactRef canonicalDomainRef();
        WriterContracts.Receipt actualReceipt();
        ExactRef originalSource();
        PendingEpisodePublication requireCurrent(ContinuityStorePort.Session same) throws IOException;
    }
    /** Installs the actual Root issuer, never an independently supplied projection/cause DATA object. */
    public synchronized void bindPendingEpisodeSource(DriverPendingEpisodeSource actual) {
        Objects.requireNonNull(actual);
        if(pendingEpisodeSource!=null&&pendingEpisodeSource.source()==actual)return;
        List<ExactRef> sources=List.copyOf(actual.sources());
        StrictJson.require(!sources.isEmpty()&&sources.size()<=64&&sources.stream().distinct().count()==sources.size()
                &&sources.stream().allMatch(ref->ref.bytes()>0),"finite complete pending-episode source closure required");
        var binding=new PendingEpisodeSourceBinding(actual,sources);
        if(pendingNextCapabilityTransfer!=null&&!pendingNextCapabilityTransfer.activated) {
            var transfer=pendingNextCapabilityTransfer;
            StrictJson.require(transfer.pendingEpisodeSource==null||transfer.pendingEpisodeSource.source()==actual,"NEXT pending source has another candidate issuer");
            transfer.pendingEpisodeSource=binding;return;
        }
        StrictJson.require(pendingEpisodeSource==null,"one active pending-episode issuer required");pendingEpisodeSource=binding;
    }
    /** Actual initial CAS result. It cannot be decoded, reconstructed or used as final M3/UI completion. */
    public static final class PublishedPending implements PendingEpisodePublication {
        private final DriverStateAssembler owner;private final PendingEpisodeSourceBinding installed;
        private final DriverPendingEpisodeSource.Capture capture;private final DriverPendingEpisodeProducer.Publication actual;
        private PublishedPending(DriverStateAssembler owner,PendingEpisodeSourceBinding installed,
                DriverPendingEpisodeSource.Capture capture,DriverPendingEpisodeProducer.Publication actual) {
            this.owner=owner;this.installed=installed;this.capture=capture;this.actual=actual;
        }
        public DriverSnapshotFacts.Known before(){return actual.before();}
        public DriverSnapshotFacts.Known after(){return actual.after();}
        public DriverPendingEpisodeProjection projection(){return capture.canonicalProjection();}
        public ExactRef projectionOriginal(){return capture.projectionOriginal();}
        public ExactRef canonicalDomainRef(){return capture.canonicalDomainRef();}
        public WriterContracts.Receipt actualReceipt(){return capture.actualReceipt();}
        public ExactRef originalSource(){return actual.originalSource();}
        public PublishedPending requireCurrent(ContinuityStorePort.Session same) throws IOException {
            owner.requirePublishedPending(same,this);return this;
        }
    }
    /** Replays the committed v2 child and non-final reducer before publishing the real new actor/run/epoch with its UI obligation. */
    public PublishedPending publishPendingEpisode(ContinuityStorePort.Session same) throws IOException {
        requireOutsideObservationScope(same);PendingEpisodeSourceBinding installed;ActionPorts.OutcomeArchive originals;
        synchronized(this) {
            installed=pendingEpisodeSource;
            StrictJson.require(installed!=null&&historyArchive!=null&&pendingNextCapabilityTransfer==null,
                    "active actual pending-episode source/archive required");originals=historyArchive.withSession(same);
        }
        StrictJson.require(installed.source().sources().equals(installed.sources()),"pending issuer source closure changed");
        var capture=Objects.requireNonNull(installed.source().current(same,this));installed.source().requireCurrent(same,this,capture);
        var publication=DriverPendingEpisodeProducer.prepare(same,capture,originals,installed.sources());
        var proof=new PublishedPending(this,installed,capture,publication);
        try {actions.withFrozen(same,lease->facts.locked(state->{
            lease.assertCurrent();StrictJson.require(state==publication.before(),"pending episode lost its actual full predecessor");
            synchronized(this){StrictJson.require(pendingEpisodeSource==installed&&pendingNextCapabilityTransfer==null,"pending issuer ownership changed");}
            try{installed.source().requireCurrent(same,this,capture);}catch(IOException failure){throw new UncheckedIOException(failure);}
            lease.assertCurrent();requireNoRawObservationMutation();facts.compareAndSet(publication.before().stamp(),publication.after());return null;
        }));}catch(UncheckedIOException failure){throw failure.getCause();}
        return proof;
    }
    private void requirePublishedPending(ContinuityStorePort.Session same,PublishedPending proof) throws IOException {
        StrictJson.require(proof.owner==this,"pending publication belongs to another Driver authority");
        synchronized(this){StrictJson.require(pendingEpisodeSource==proof.installed&&pendingNextCapabilityTransfer==null,"pending publication issuer is no longer installed");}
        StrictJson.require(proof.installed.source().sources().equals(proof.installed.sources()),"pending publication code closure changed");
        DriverPendingEpisodeProducer.requireCommitted(same,proof.capture,proof.installed.sources(),false);
        withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual pending Driver owner unavailable");
            var current=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(current.stamp().equals(proof.after().stamp())&&Arrays.equals(current.driver().encode(),proof.after().driver().encode())
                    &&current.auxiliary().equals(proof.after().auxiliary()),"pending publication no longer names the actual same Driver/UI obligation");
            proof.installed.source().requirePublished(same,this,proof.capture,current);return null;
        });
    }
    /** Genuine finite mutation CAS result, including the final report only after the actual private M3 finalization. */
    public static final class PublishedPendingMutation implements PendingEpisodePublication {
        private final DriverStateAssembler owner;private final PendingEpisodeSourceBinding installed;
        private final DriverPendingEpisodeSource.Mutation capture;private final DriverPendingEpisodeProducer.MutationPublication actual;
        private PublishedPendingMutation(DriverStateAssembler owner,PendingEpisodeSourceBinding installed,
                DriverPendingEpisodeSource.Mutation capture,DriverPendingEpisodeProducer.MutationPublication actual) {
            this.owner=owner;this.installed=installed;this.capture=capture;this.actual=actual;
        }
        public DriverSnapshotFacts.Known before(){return actual.before();}
        public DriverSnapshotFacts.Known after(){return actual.after();}
        public DriverPendingEpisodeSource.MutationPhase phase(){return capture.change().phase();}
        public org.xar.ck3.control.application.lifecycle.SuccessorUiObligation obligation(){return capture.afterObligation();}
        public ExactRef canonicalDomainRef(){return capture.canonicalDomainRef();}
        public WriterContracts.Receipt actualReceipt(){return capture.actualReceipt();}
        public ExactRef originalSource(){return actual.originalSource();}
        public Optional<ExactRef> originalResult(){return actual.originalResult();}
        public PublishedPendingMutation requireCurrent(ContinuityStorePort.Session same) throws IOException {
            owner.requirePublishedPendingMutation(same,this);return this;
        }
    }
    public PublishedPendingMutation publishPendingEpisodeMutation(ContinuityStorePort.Session same) throws IOException {
        requireOutsideObservationScope(same);PendingEpisodeSourceBinding installed;ActionPorts.OutcomeArchive originals;
        synchronized(this) {
            installed=pendingEpisodeSource;StrictJson.require(installed!=null&&historyArchive!=null&&pendingNextCapabilityTransfer==null,
                    "actual pending mutation source/archive required");originals=historyArchive.withSession(same);
        }
        StrictJson.require(installed.source().sources().equals(installed.sources()),"pending mutation code closure changed");
        var capture=Objects.requireNonNull(installed.source().currentMutation(same,this));installed.source().requireMutation(same,this,capture);
        var publication=DriverPendingEpisodeProducer.prepareMutation(same,capture,originals,installed.sources());
        var proof=new PublishedPendingMutation(this,installed,capture,publication);
        try {actions.withFrozen(same,lease->facts.locked(state->{
            lease.assertCurrent();StrictJson.require(state==publication.before(),"pending mutation lost its actual current full Driver");
            synchronized(this){StrictJson.require(pendingEpisodeSource==installed&&pendingNextCapabilityTransfer==null,"pending mutation issuer changed");}
            try{installed.source().requireMutation(same,this,capture);}catch(IOException failure){throw new UncheckedIOException(failure);}
            lease.assertCurrent();requireNoRawObservationMutation();facts.compareAndSet(publication.before().stamp(),publication.after());return null;
        }));}catch(UncheckedIOException failure){throw failure.getCause();}
        return proof;
    }
    private void requirePublishedPendingMutation(ContinuityStorePort.Session same,PublishedPendingMutation proof) throws IOException {
        StrictJson.require(proof.owner==this,"pending mutation belongs to another Driver authority");
        synchronized(this){StrictJson.require(pendingEpisodeSource==proof.installed&&pendingNextCapabilityTransfer==null,"pending mutation issuer no longer installed");}
        StrictJson.require(proof.installed.source().sources().equals(proof.installed.sources()),"pending mutation code closure changed");
        DriverPendingEpisodeProducer.requireMutationCommitted(same,proof.capture,proof.installed.sources(),false);
        withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual published pending mutation unavailable");
            var current=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(current.stamp().equals(proof.after().stamp())&&Arrays.equals(current.driver().encode(),proof.after().driver().encode())
                    &&current.auxiliary().equals(proof.after().auxiliary()),"pending mutation no longer names the actual same Driver/obligation");
            proof.installed.source().requirePublishedMutation(same,this,proof.capture,current);return null;
        });
    }
    /** Genuine same-source recovered publication. Issued only after recorded imports/ACTIONs replay and exact current owner checks; no CAS. */
    public static final class RecoveredPending implements PendingEpisodePublication {
        private final DriverStateAssembler owner;private final PendingEpisodeSourceBinding installed;
        private final DriverPendingEpisodeSource.Recovery capture;private final DriverPendingEpisodeSource.ReplayedRecovery actual;
        private RecoveredPending(DriverStateAssembler owner,PendingEpisodeSourceBinding installed,
                DriverPendingEpisodeSource.Recovery capture,DriverPendingEpisodeSource.ReplayedRecovery actual){
            this.owner=owner;this.installed=installed;this.capture=capture;this.actual=actual;
        }
        public DriverSnapshotFacts.Known before(){return actual.originalBefore();}
        public DriverSnapshotFacts.Known after(){return actual.actualAfter();}
        public ExactRef canonicalDomainRef(){return actual.canonicalDomain();}
        public WriterContracts.Receipt actualReceipt(){return actual.latestReceipt();}
        public ExactRef originalSource(){return actual.originalSource();}
        public ExactRef actualDriverOriginal(){return actual.actualDriverOriginal();}
        public RecoveredPending requireCurrent(ContinuityStorePort.Session same)throws IOException {
            owner.requirePendingCommitted(same,this);owner.withFrozenFacts(same,frozen->{requireRecoveredState(after(),frozen.state());return null;});return this;
        }
    }
    /** The installed private Root requalifies its actual historical/M3 scope before this read-only reconstruction. */
    public RecoveredPending recoverPendingEpisodePublication(ContinuityStorePort.Session same)throws IOException {
        Objects.requireNonNull(same);PendingEpisodeSourceBinding installed;ActionPorts.OutcomeArchive originals;
        synchronized(this){installed=pendingEpisodeSource;StrictJson.require(installed!=null&&historyArchive!=null&&pendingNextCapabilityTransfer==null
                &&installed.source() instanceof DriverPendingEpisodeSource.Recovering,"actual recovering pending issuer/archive required");originals=historyArchive.withSession(same);}
        var source=(DriverPendingEpisodeSource.Recovering)installed.source();
        StrictJson.require(source.sources().equals(installed.sources()),"recovery source closure changed");
        var capture=Objects.requireNonNull(source.currentRecovery(same,this));source.requireRecovery(same,this,capture);
        var replayed=DriverPendingEpisodeSource.replayRecovery(same,capture,originals,installed.sources());
        var proof=new RecoveredPending(this,installed,capture,replayed);
        withFrozenFacts(same,frozen->{
            synchronized(this){StrictJson.require(pendingEpisodeSource==installed&&pendingNextCapabilityTransfer==null,"recovery issuer changed");}
            requireRecoveredState(replayed.actualAfter(),frozen.state());source.requireRecovery(same,this,capture);
            source.requireRecovered(same,this,capture,proof,(DriverSnapshotFacts.Known)frozen.state());return null;
        });return proof;
    }
    private static void requireRecoveredState(DriverSnapshotFacts.Known expected,DriverSnapshotFacts.State actual) {
        StrictJson.require(actual instanceof DriverSnapshotFacts.Known,"actual recovered Driver owner unavailable");var current=(DriverSnapshotFacts.Known)actual;
        StrictJson.require(current.stamp().equals(expected.stamp())&&Arrays.equals(current.driver().encode(),expected.driver().encode())
                &&current.auxiliary().equals(expected.auxiliary())&&current.originalHistoryBasis().equals(expected.originalHistoryBasis())
                &&current.actionRows().equals(expected.actionRows()),"recovered publication differs from the actual whole canonical Driver/coverage/obligation");
    }
    /** Qualification is limited to one genuine pending parent's exact new-subject UI child. The coordinator retains all submission authority. */
    public <T>T withPendingEpisodeChildScope(ContinuityStorePort.Session same,PendingEpisodePublication publication,
            ActionCommand originalParent,ActionCommand actualChild,PendingWork<T> work) throws IOException {
        Objects.requireNonNull(publication);Objects.requireNonNull(originalParent);Objects.requireNonNull(actualChild);Objects.requireNonNull(work);
        StrictJson.require(pendingChildScope.get()==null,"one actual pending-child projection scope required");
        publication.requireCurrent(same);PendingEpisodeSourceBinding installed;
        synchronized(this){installed=pendingEpisodeSource;StrictJson.require(installed!=null&&pendingNextCapabilityTransfer==null,"active pending-child source unavailable");}
        var obligation=org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec.decode(
                DriverJson.encode(publication.after().auxiliary().get(org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.AUXILIARY_KEY)));
        StrictJson.require(obligation.blocksOrdinaryActionsAndSave()&&originalParent.origin() instanceof CommandOrigin.LifecycleTerminal
                &&originalParent.operation().value().equals("continue-as-reconciled-successor")
                &&originalParent.actionId().equals(obligation.binding().parentActionId())
                &&ActionCodec.bodySha256(originalParent).equals(obligation.binding().parentBodySha256())
                &&actualChild.origin() instanceof CommandOrigin.Gameplay&&observationSubject(actualChild,publication.after())
                &&actualChild.source().equals(originalParent.source())&&actualChild.sessionId().equals(originalParent.sessionId()),
                "pending child lost its genuine parent/new subject/source/session");
        // This new child uses its genuine continuation token's fresh deadline. The original parent body/deadline is immutable.
        installed.source().requireChild(same,this,publication,originalParent,actualChild);
        withFrozenFacts(same,frozen->{
            var parent=frozen.actions().actions().stream().filter(value->value.command().equals(originalParent)).toList();
            StrictJson.require(parent.size()==1&&(parent.getFirst().state() instanceof ActionState.CompositeRunning
                    ||parent.getFirst().state() instanceof ActionState.CompositeUnknown),"pending child's actual canonical continuation parent unavailable");
            return null;
        });
        pendingChildScope.set(new PendingChildScope(this,installed,publication,originalParent,actualChild,same));
        try{return work.run();}finally{pendingChildScope.remove();}
    }
    private static Optional<PendingChildScope> qualifiedPendingChild(DriverSnapshotFacts.Known state,ActionJournal.Snapshot durable) {
        PendingChildScope scope=pendingChildScope.get();if(scope==null)return Optional.empty();
        synchronized(scope.owner()){if(scope.owner().pendingEpisodeSource!=scope.installed())return Optional.empty();}
        var expected=scope.expected;
        if(!state.stamp().equals(expected.stamp())||!Arrays.equals(state.driver().encode(),expected.driver().encode())
                ||!Objects.equals(state.auxiliary().get(org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.AUXILIARY_KEY),
                        expected.auxiliary().get(org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.AUXILIARY_KEY)))return Optional.empty();
        var active=org.xar.ck3.control.application.action.ActionCommandScope.current();if(active.isEmpty())return Optional.empty();
        var parent=durable.actions().stream().filter(value->value.command().equals(scope.parent())
                &&(value.state() instanceof ActionState.CompositeRunning||value.state() instanceof ActionState.CompositeUnknown)).toList();
        if(parent.size()!=1)return Optional.empty();
        var stateOfParent=parent.getFirst().state();
        var execution=stateOfParent instanceof ActionState.CompositeRunning running?running.execution():((ActionState.CompositeUnknown)stateOfParent).execution();
        boolean reserved=false;
        for(var child:execution.children()) {
            if(child.actionId().equals(scope.child().actionId())) {
                if(!child.bodySha256().equals(ActionCodec.bodySha256(scope.child())))return Optional.empty();reserved=true;
            }else if(durable.actions().stream().noneMatch(actual->actual.command().actionId().equals(child.actionId())
                    &&actual.bodySha256().equals(child.bodySha256())&&actual.settled()))return Optional.empty();
        }
        if(!reserved)return Optional.empty();
        if(active.filter(scope.child()::equals).isPresent())return Optional.of(scope);
        // Only the source-qualified DATE child can contain the existing bounded Life composite.
        if(!scope.child().operation().value().equals("life-advance"))return Optional.empty();
        var life=durable.actions().stream().filter(value->value.command().equals(scope.child())&&value.state() instanceof ActionState.CompositeRunning).toList();
        if(life.size()!=1)return Optional.empty();
        var children=((ActionState.CompositeRunning)life.getFirst().state()).execution().children();
        if(children.isEmpty()||children.size()>3||!children.getLast().actionId().equals(active.orElseThrow().actionId())
                ||!children.getLast().bodySha256().equals(ActionCodec.bodySha256(active.orElseThrow()))
                ||!active.orElseThrow().source().equals(scope.child().source())||!active.orElseThrow().sessionId().equals(scope.child().sessionId())
                ||active.orElseThrow().deadline().isAfter(scope.child().deadline())||!observationSubject(active.orElseThrow(),state))return Optional.empty();
        for(var child:children)if(!child.actionId().equals(active.orElseThrow().actionId())
                &&durable.actions().stream().noneMatch(value->value.command().actionId().equals(child.actionId())
                    &&value.bodySha256().equals(child.bodySha256())&&value.settled()))return Optional.empty();
        return Optional.of(scope);
    }
    /** This private product permits physical inspection only; it contains no executable operation or readiness grant. */
    public static final class PendingChildPhysical {
        private final DriverStateAssembler issuer;
        private final PendingChildScope scope;
        private PendingChildPhysical(DriverStateAssembler issuer,PendingChildScope scope){this.issuer=issuer;this.scope=scope;}
        public ActionCommand originalParent(){return scope.parent();}
        public ActionCommand exactChild(){return scope.child();}
    }
    /** Only the coordinator's exact reserved child in the genuine installed pending scope can bypass ordinary capability projection. */
    public Optional<PendingChildPhysical> pendingChildPhysical(ContinuityStorePort.Session same,
            DriverObservationAssembler.Complete frame,DriverSnapshotFacts.Known actual) throws IOException {
        PendingChildScope scope=pendingChildScope.get();if(scope==null)return Optional.empty();
        StrictJson.require(scope.owner()==this&&scope.session()==same,"pending physical inspection crossed its original writer Session");
        return withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state()==actual,"pending physical inspection requires the identical actual frozen Driver");
            var qualified=qualifiedPendingChild(actual,frozen.actions()).orElseThrow(()->new IllegalArgumentException("actual pending child reservation unavailable"));
            StrictJson.require(frame.identity().game().equals(actual.stamp().game())
                    &&frame.identity().frame().episodeRunId().equals(actual.stamp().episodeRunId())
                    &&frame.identity().frame().identity().player().equals(actual.driver().session().actorId())
                    &&frame.source().equals(qualified.child().source())
                    &&frame.sessionId().equals(qualified.child().sessionId()),"pending physical inspection crossed its actual new subject/source/session");
            qualified.installed().source().requireChild(same,this,qualified.publication(),qualified.parent(),qualified.child());
            return Optional.of(new PendingChildPhysical(this,qualified));
        });
    }
    /** Private custody of the genuine pending publication's exact current Driver after its bounded actual child publications. */
    public static final class QualifiedPendingCurrent {
        private final DriverStateAssembler owner;private final ContinuityStorePort.Session session;
        private final PendingEpisodePublication publication;private final DriverSnapshotFacts.Known actualKnown;
        private final ExactRef actualDriverOriginal;private final String head;
        private QualifiedPendingCurrent(DriverStateAssembler owner,ContinuityStorePort.Session session,PendingEpisodePublication publication,
                DriverSnapshotFacts.Known known,ExactRef driver,String head) {
            this.owner=owner;this.session=session;this.publication=publication;actualKnown=known;actualDriverOriginal=driver;this.head=head;
        }
        public DriverSnapshotFacts.Known actualKnown(){return actualKnown;}
        public ExactRef actualDriverOriginal(){return actualDriverOriginal;}
        public QualifiedPendingCurrent requireCurrent(ContinuityStorePort.Session same) throws IOException {
            StrictJson.require(same==session&&same.head().digest().equals(head),"pending current custody escaped its original writer/head");
            owner.requirePendingCommitted(same,publication);
            owner.withFrozenFacts(same,frozen->{StrictJson.require(frozen.state()==actualKnown,"pending current custody no longer names the actual frozen Driver");return null;});
            return this;
        }
    }
    private void requirePendingCommitted(ContinuityStorePort.Session same,PendingEpisodePublication proof) throws IOException {
        PendingEpisodeSourceBinding installed;
        if(proof instanceof PublishedPending initial) {
            StrictJson.require(initial.owner==this,"pending publication belongs to another Driver");installed=initial.installed;
            DriverPendingEpisodeProducer.requireCommitted(same,initial.capture,installed.sources(),false);
        }else if(proof instanceof RecoveredPending recovered) {
            StrictJson.require(recovered.owner==this,"recovered publication belongs to another Driver");installed=recovered.installed;
            var replayed=DriverPendingEpisodeSource.replayRecovery(same,recovered.capture,historyArchive.withSession(same),installed.sources());
            requireRecoveredState(recovered.actual.actualAfter(),replayed.actualAfter());
            StrictJson.require(replayed.originalSource().equals(recovered.originalSource())&&replayed.actualDriverOriginal().equals(recovered.actualDriverOriginal())
                    &&replayed.canonicalDomain().equals(recovered.canonicalDomainRef())&&replayed.latestReceipt().equals(recovered.actualReceipt()),"recovered actual canonical edges changed");
        }else {
            var mutation=(PublishedPendingMutation)proof;StrictJson.require(mutation.owner==this,"pending mutation belongs to another Driver");installed=mutation.installed;
            DriverPendingEpisodeProducer.requireMutationCommitted(same,mutation.capture,installed.sources(),false);
        }
        synchronized(this){StrictJson.require(pendingEpisodeSource==installed&&pendingNextCapabilityTransfer==null,"actual pending issuer changed");}
        StrictJson.require(installed.source().sources().equals(installed.sources()),"pending source code closure changed");
    }
    /** Available only while the already qualified exact child scope is active; expected advances only in the sole actual ACTION CAS below. */
    public QualifiedPendingCurrent currentPendingEpisodeChildScope(ContinuityStorePort.Session same,PendingEpisodePublication proof) throws IOException {
        var scope=pendingChildScope.get();StrictJson.require(scope!=null&&scope.owner()==this&&scope.session()==same&&scope.publication()==proof,
                "actual pending child scope unavailable");requirePendingCommitted(same,proof);
        return withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual pending Driver unavailable");var current=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(qualifiedPendingChild(current,frozen.actions()).isPresent(),"pending child scope lost its actual bounded reservation/current CAS");
            var reference=historyArchive.withSession(same).materialReferenceOf(RawJson.fullMaterial(current.driver().encode()));
            return new QualifiedPendingCurrent(this,same,proof,current,reference,same.head().digest());
        });
    }
    /** Reopens the real bounded child ACTION publications after submit returns; no caller-supplied version or receipt can advance this custody. */
    public QualifiedPendingCurrent requirePendingEpisodeChildCurrent(ContinuityStorePort.Session same,PendingEpisodePublication proof,
            ActionCommand originalParent,ActionCommand exactSettledChild) throws IOException {
        requirePendingCommitted(same,proof);ActionPorts.OutcomeArchive originals=historyArchive.withSession(same);
        return withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"pending current full Driver unavailable");var current=(DriverSnapshotFacts.Known)frozen.state();
            var baseline=proof.after();StrictJson.require(current.stamp().game().equals(baseline.stamp().game())
                    &&current.stamp().episodeEpoch()==baseline.stamp().episodeEpoch()&&current.stamp().episodeRunId().equals(baseline.stamp().episodeRunId())
                    &&current.auxiliary().equals(baseline.auxiliary())&&current.originalHistoryBasis().equals(baseline.originalHistoryBasis()),"pending child changed its actual episode/obligation owner");
            var obligation=org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec.decode(DriverJson.encode(
                    baseline.auxiliary().get(org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.AUXILIARY_KEY)));
            StrictJson.require(obligation.blocksOrdinaryActionsAndSave()&&originalParent.actionId().equals(obligation.binding().parentActionId())
                    &&ActionCodec.bodySha256(originalParent).equals(obligation.binding().parentBodySha256())
                    &&originalParent.operation().value().equals("continue-as-reconciled-successor")&&originalParent.origin() instanceof CommandOrigin.LifecycleTerminal
                    &&exactSettledChild.origin() instanceof CommandOrigin.Gameplay&&observationSubject(exactSettledChild,current)
                    &&exactSettledChild.source().equals(originalParent.source())&&exactSettledChild.sessionId().equals(originalParent.sessionId()),"pending current lost its genuine parent/new-subject source binding");
            var parent=frozen.actions().actions().stream().filter(value->value.command().equals(originalParent)).findFirst().orElseThrow();
            var parentExecution=compositeExecution(parent.state());
            StrictJson.require(parentExecution.children().stream().anyMatch(value->value.actionId().equals(exactSettledChild.actionId())
                    &&value.bodySha256().equals(ActionCodec.bodySha256(exactSettledChild))),"pending child is not the actual original parent's reserved full body");
            var child=frozen.actions().actions().stream().filter(value->value.command().equals(exactSettledChild)&&value.settled()).findFirst().orElseThrow();
            PendingEpisodeSourceBinding installed; synchronized(this){installed=pendingEpisodeSource;StrictJson.require(installed!=null,"actual pending child issuer unavailable");}
            installed.source().requireChild(same,this,proof,originalParent,exactSettledChild);
            var allowed=new java.util.LinkedHashMap<String,ActionReceipt>();allowed.put(child.command().actionId(),child);
            if(exactSettledChild.operation().value().equals("life-advance")) {
                var children=compositeExecution(child.state()).children();StrictJson.require(!children.isEmpty()&&children.size()<=3,"bounded pending Life children required");
                for(var reserved:children) {
                    var primitive=frozen.actions().actions().stream().filter(value->value.command().actionId().equals(reserved.actionId())
                            &&value.bodySha256().equals(reserved.bodySha256())&&value.settled()).findFirst().orElseThrow();
                    StrictJson.require(primitive.command().source().equals(exactSettledChild.source())&&primitive.command().sessionId().equals(exactSettledChild.sessionId())
                            &&!primitive.command().deadline().isAfter(exactSettledChild.deadline())&&observationSubject(primitive.command(),current),"pending Life primitive crossed its bounded source/subject/deadline");
                    allowed.put(primitive.command().actionId(),primitive);
                }
            }
            var priorIds=baseline.actionRows().stream().map(DriverSnapshotFacts.ActionRow::actionId).collect(java.util.stream.Collectors.toSet());
            var additions=current.actionRows().stream().filter(value->!priorIds.contains(value.actionId())).toList();
            StrictJson.require(additions.size()==allowed.size()&&current.actionRows().containsAll(baseline.actionRows()),"pending current includes another action or missing child publication");
            var publications=new ArrayList<DriverActionHistoryState.CommittedCoverage>();
            for(var row:additions) {
                var actual=allowed.get(row.actionId());StrictJson.require(actual!=null&&actual.bodySha256().equals(row.bodySha256())&&actual.sequence()==row.durableSequence(),"pending coverage crossed its actual child");
                publications.add(DriverActionHistoryState.findCommittedCoverage(same,actual,originals).orElseThrow());
            }
            publications.sort(java.util.Comparator.comparingLong(value->value.publication().beforeVersion()));
            long version=baseline.stamp().driverVersion();ExactRef driver=originals.materialReferenceOf(RawJson.fullMaterial(baseline.driver().encode()));
            for(var committed:publications) {
                var value=committed.publication();StrictJson.require(value.beforeVersion()==version&&value.afterVersion()==Math.addExact(version,1)
                        &&value.episodeEpoch()==baseline.stamp().episodeEpoch()&&value.beforeDriver().equals(driver),"pending ACTION publications are not the exact contiguous full Driver chain");
                version=value.afterVersion();driver=value.afterDriver();
            }
            StrictJson.require(version==current.stamp().driverVersion()&&Arrays.equals(originals.loadFullMaterial(driver).bytes(),current.driver().encode()),"pending child publications do not reach the actual full Driver");
            return new QualifiedPendingCurrent(this,same,proof,current,driver,same.head().digest());
        });
    }
    private static org.xar.ck3.control.application.action.CompositeExecution compositeExecution(ActionState state) {
        if(state instanceof ActionState.CompositeRunning running)return running.execution();
        if(state instanceof ActionState.CompositeUnknown unknown)return unknown.execution();
        if(state instanceof ActionState.CompositeSettled settled)return settled.execution();
        throw new IllegalArgumentException("actual canonical composite execution required");
    }

    /** Opaque ownership transfer, minted only from the actual already committed NEXT producer. */
    public static final class NextCapabilityTransfer {
        private final DriverStateAssembler issuer;
        private final org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption original;
        private final DriverSnapshotFacts.Known published;
        private final WriterContracts.Head basis;
        private final CapabilityObservation oldObservation;
        private final ActionPorts.OutcomeArchive oldArchive;
        private final java.util.function.Supplier<ContinuityStorePort.Session> oldSession;
        private String auxiliarySha256;
        private boolean activated;
        private PreclockSourceBinding preclockSource;
        private PendingEpisodeSourceBinding pendingEpisodeSource;
        private OperatorSourceBinding operatorSource;
        private NextCapabilityTransfer(DriverStateAssembler issuer,
                org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption original,
                DriverSnapshotFacts.Known published,WriterContracts.Head basis,CapabilityObservation oldObservation,
                ActionPorts.OutcomeArchive oldArchive,java.util.function.Supplier<ContinuityStorePort.Session> oldSession) {
            this.issuer=issuer;this.original=original;this.published=published;this.basis=basis;
            this.oldObservation=oldObservation;this.oldArchive=oldArchive;this.oldSession=oldSession;
            auxiliarySha256=DriverJson.sha256(DriverJson.encode(published.auxiliary()));
        }
        public void requireCurrent(ContinuityStorePort.Session same) throws IOException { issuer.requireNextTransfer(same,this); }
    }
    NextCapabilityTransfer prepareNextCapabilityTransfer(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption original,
            CapabilityObservation oldObservation,ActionPorts.OutcomeArchive oldArchive,
            java.util.function.Supplier<ContinuityStorePort.Session> oldSession) throws IOException {
        requireOutsideObservationScope(same);Objects.requireNonNull(original).requireCurrent(same);
        same.requireCommitted(original.commit().prepared(),original.commit().receipt());
        return withFrozenFacts(same,frozen -> {
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"NEXT requires the sole published full Driver");
            var current=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(current.stamp().equals(original.published().stamp())
                    &&Arrays.equals(current.driver().encode(),original.published().driver().encode())
                    &&current.auxiliary().equals(original.published().auxiliary()),"NEXT ownership must be staged before any new observation/cache publication");
            synchronized(this) { StrictJson.require(capabilityObservation==oldObservation&&historyArchive==oldArchive&&historySession==oldSession,
                    "NEXT transfer crossed the exact installed old runtime"); }
            var transfer=new NextCapabilityTransfer(this,original,current,same.head(),oldObservation,oldArchive,oldSession);
            synchronized(this){StrictJson.require(pendingNextCapabilityTransfer==null,"one staged NEXT capability owner required");pendingNextCapabilityTransfer=transfer;}
            return transfer;
        });
    }
    private void requireNextTransfer(ContinuityStorePort.Session same,NextCapabilityTransfer transfer) throws IOException {
        StrictJson.require(transfer.issuer==this&&!transfer.activated,"NEXT candidate ownership is unavailable or already consumed");
        same.requireCommitted(transfer.original.commit().prepared(),transfer.original.commit().receipt());
        same.requireHistoricalState(transfer.basis.state().sequence(),transfer.basis.digest());
        withFrozenFacts(same,frozen -> {
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"NEXT lost its actual full Driver");
            var current=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(current.stamp().equals(transfer.published.stamp())
                    &&Arrays.equals(current.driver().encode(),transfer.published.driver().encode())
                    &&DriverJson.sha256(DriverJson.encode(current.auxiliary())).equals(transfer.auxiliarySha256),
                    "NEXT full Driver or tracked candidate auxiliary changed");
            synchronized(this) { StrictJson.require(capabilityObservation==transfer.oldObservation&&historyArchive==transfer.oldArchive&&historySession==transfer.oldSession,
                    "NEXT old runtime binding changed before activation"); }
            return null;
        });
    }
    void requireNextCandidate(ContinuityStorePort.Session same,NextCapabilityTransfer transfer,
            org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption original,
            DriverStateAssembler expectedAuthority) throws IOException {
        StrictJson.require(expectedAuthority==this&&transfer.original==original,"NEXT candidate belongs to another exact adoption or Driver authority");
        requireNextTransfer(same,transfer);
    }
    private void requireStagedNextOwner(ContinuityStorePort.Session same,NextCapabilityTransfer transfer) throws IOException {
        StrictJson.require(transfer.issuer==this&&!transfer.activated,"staged NEXT owner is unavailable");
        same.requireCommitted(transfer.original.commit().prepared(),transfer.original.commit().receipt());
        same.requireHistoricalState(transfer.basis.state().sequence(),transfer.basis.digest());
        synchronized(this){StrictJson.require(pendingNextCapabilityTransfer==transfer&&capabilityObservation==transfer.oldObservation
                &&historyArchive==transfer.oldArchive&&historySession==transfer.oldSession,"staged NEXT old binding changed");}
        withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"staged NEXT full Driver missing");var known=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(known.stamp().game().equals(transfer.original.replacement().newGame())
                    &&known.stamp().episodeEpoch()==transfer.published.stamp().episodeEpoch()
                    &&known.stamp().episodeRunId().equals(transfer.published.stamp().episodeRunId())
                    &&known.driver().session().pipeName().equals(transfer.original.replacement().pipeName()),"staged NEXT crossed its actual replacement Game/episode");return null;
        });
    }
    <T>T withCandidateScope(ContinuityStorePort.Session same,NextCapabilityTransfer transfer,CapabilityObservation observation,
            ActionPorts.OutcomeArchive archive,java.util.function.Supplier<ContinuityStorePort.Session> sessions,CandidateWork<T> work) throws IOException {
        requireStagedNextOwner(same,transfer);Objects.requireNonNull(work);
        CandidateScope previous=candidateScope.get();
        if(previous!=null)StrictJson.require(previous.session()==same&&previous.transfer()==transfer&&previous.observation()==observation
                &&previous.archive()==archive&&previous.sessions()==sessions,"nested NEXT scope crossed its exact owner");
        CandidateScope actual=new CandidateScope(same,transfer,observation,archive,sessions);candidateScope.set(actual);
        try{return work.run();}finally{if(previous==null)candidateScope.remove();else candidateScope.set(previous);}
    }
    void requireCandidateScope(ContinuityStorePort.Session same,NextCapabilityTransfer transfer) throws IOException {
        requireStagedNextOwner(same,transfer);CandidateScope scope=candidateScope.get();
        StrictJson.require(scope!=null&&scope.session()==same&&scope.transfer()==transfer,"candidate planning requires its explicit actual NEXT scope");
    }
    void requireNextPacket(ContinuityStorePort.Session same,NextCapabilityTransfer transfer,NativeObservationPort.ObservedFrame actual) throws IOException {
        requireNextTransfer(same,transfer);var loaded=transfer.original.loadedObservation();
        StrictJson.require(loaded.session().equals(actual.session())&&loaded.snapshotId().equals(actual.snapshotId())
                &&loaded.nativeRevision().equals(actual.nativeRevision())&&loaded.observedAt().equals(actual.observedAt())
                &&loaded.state().equals(actual.state())&&Arrays.equals(loaded.originalPacket(),actual.originalPacket()),
                "NEXT capability preparation requires the exact original private loaded observation");
    }
    /** CAS and its ownership cursor advance together, so a failed caller can retry only the same retained publication. */
    void publishNextCapabilityInputs(ContinuityStorePort.Session same,NextCapabilityTransfer transfer,
            DriverCapabilityStateProducer.InitialAuxiliary publication) throws IOException {
        StrictJson.require(transfer.issuer==this&&!transfer.activated&&publication.expectedStamp().equals(transfer.published.stamp()),"NEXT publication belongs to another candidate");
        actions.withFrozen(same,lease -> facts.locked(state -> {
            lease.assertCurrent();StrictJson.require(state instanceof DriverSnapshotFacts.Known,"NEXT lost complete Driver before capability CAS");
            var current=(DriverSnapshotFacts.Known)state;
            String resultSha=DriverJson.sha256(DriverJson.encode(publication.auxiliary()));
            if(transfer.auxiliarySha256.equals(resultSha)&&current.auxiliary().equals(publication.auxiliary()))return null;
            StrictJson.require(publication.expectedAuxiliarySha256().equals(transfer.auxiliarySha256)
                    &&current.stamp().equals(transfer.published.stamp())&&Arrays.equals(current.driver().encode(),transfer.published.driver().encode()),"stale NEXT candidate capability publication");
            requireNoRawObservationMutation();facts.publishCapabilityInputs(publication.expectedStamp(),publication.expectedAuxiliarySha256(),publication);
            transfer.auxiliarySha256=resultSha;lease.assertCurrent();return null;
        }));
    }
    void noteNextCapabilityPublication(ContinuityStorePort.Session same,NextCapabilityTransfer transfer,
            DriverCapabilityStateProducer.InitialAuxiliary publication) throws IOException {
        StrictJson.require(transfer.issuer==this&&!transfer.activated&&publication.expectedStamp().equals(transfer.published.stamp())
                &&publication.expectedAuxiliarySha256().equals(transfer.auxiliarySha256),"NEXT publication did not originate at its retained candidate state");
        withFrozenFacts(same,frozen -> {
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"NEXT publication lost Driver owner");
            var current=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(current.stamp().equals(transfer.published.stamp())&&Arrays.equals(current.driver().encode(),transfer.published.driver().encode())
                    &&current.auxiliary().equals(publication.auxiliary()),"NEXT candidate publication was not the actual sole repository CAS");
            transfer.auxiliarySha256=DriverJson.sha256(DriverJson.encode(current.auxiliary()));return null;
        });
    }
    void activateNextCapabilityTransfer(ContinuityStorePort.Session same,NextCapabilityTransfer transfer,
            org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.NextBaselineBinding baseline,
            CapabilityObservation newObservation,ActionPorts.OutcomeArchive newArchive,
            java.util.function.Supplier<ContinuityStorePort.Session> newSession) throws IOException {
        Objects.requireNonNull(transfer);Objects.requireNonNull(baseline);
        CapabilityObservation targetObservation=Objects.requireNonNull(newObservation);
        ActionPorts.OutcomeArchive targetArchive=Objects.requireNonNull(newArchive);
        java.util.function.Supplier<ContinuityStorePort.Session> targetSession=Objects.requireNonNull(newSession);
        requireOutsideObservationScope(same);requireStagedNextOwner(same,transfer);Objects.requireNonNull(baseline).requireCurrent(same);
        StrictJson.require(baseline.proof()==transfer.original.proof()&&baseline.parent().command().actionId().equals(transfer.original.parent().command().actionId())
                &&Arrays.equals(baseline.firstCheckpoint().originalDriver().encode(),transfer.published.driver().encode()),"NEXT callback baseline belongs to another private adoption or first SAVE");
        withFrozenFacts(same,frozen -> {
            var known=(DriverSnapshotFacts.Known)frozen.state();var observed=known.observation().orElseThrow();
            StrictJson.require(known.stamp().equals(baseline.driverStamp())&&Arrays.equals(known.driver().encode(),baseline.driver().encode())
                    &&DriverJson.sha256(DriverJson.encode(known.auxiliary())).equals(transfer.auxiliarySha256),"NEXT activation lost its exact first-SAVE Driver or tracked candidate auxiliary");
            StrictJson.require(observed.transport().game().equals(transfer.original.replacement().newGame())
                    &&observed.transport().sessionId().equals(transfer.original.replacement().sessionId())
                    &&known.driver().session().pipeName().equals(transfer.original.replacement().pipeName()),"NEXT actual new physical observation required before callback activation");
            synchronized(this) {
                StrictJson.require(transfer.issuer==this&&!transfer.activated&&pendingNextCapabilityTransfer==transfer
                        &&capabilityObservation==transfer.oldObservation&&historyArchive==transfer.oldArchive&&historySession==transfer.oldSession,"NEXT old owner raced activation validation");
            }
            return null;
        });
        // The caller still holds the original writer. Every source/baseline/facts check, including the frozen lease's
        // trailing assertCurrent, has returned successfully before these final ownership assignments may begin.
        synchronized(this) {
            StrictJson.require(transfer.issuer==this&&!transfer.activated&&pendingNextCapabilityTransfer==transfer
                    &&capabilityObservation==transfer.oldObservation&&historyArchive==transfer.oldArchive&&historySession==transfer.oldSession,"NEXT old owner raced final activation");
            capabilityObservation=targetObservation;historyArchive=targetArchive;historySession=targetSession;
            preclockExpectationSource=transfer.preclockSource;
            pendingEpisodeSource=transfer.pendingEpisodeSource;
            operatorRebindSource=transfer.operatorSource;
            transfer.activated=true;pendingNextCapabilityTransfer=null;
        }
    }

    public <T>T withFrozenFacts(DriverWork<T> work) throws IOException {
        Objects.requireNonNull(work);
        try {
            return actions.withFrozen(lease -> facts.locked(state -> {
                lease.assertCurrent();
                try { return frozenWork(work,new Frozen(state,lease.snapshot(),lease.activeActionId())); }
                catch(IOException failure) { throw new UncheckedIOException(failure); }
            }));
        } catch(UncheckedIOException failure) { throw failure.getCause(); }
    }

    /** Explicitly joins the original writer Session. It never asks the OS for a second writer lock. */
    public <T>T withFrozenFacts(ContinuityStorePort.Session borrowed, DriverWork<T> work) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(work);
        try {
            return actions.withFrozen(borrowed,lease -> facts.locked(state -> {
                lease.assertCurrent();
                try { T result=frozenWork(work,new Frozen(state,lease.snapshot(),lease.activeActionId())); lease.assertCurrent(); return result; }
                catch(IOException failure) { throw new UncheckedIOException(failure); }
            }));
        } catch(UncheckedIOException failure) { throw failure.getCause(); }
    }
    /** Must be checked before preview/commit, so a wrong caller cannot commit and discover the old freeze afterwards. */
    public void requireOutsideObservationScope(ContinuityStorePort.Session original) {
        Objects.requireNonNull(original);StrictJson.require(readFreezeDepth.get()==0,"read-history publication must leave every immutable Driver read scope first");
    }
    private <T>T frozenWork(DriverWork<T> work,Frozen frozen) throws IOException {
        int prior=readFreezeDepth.get();readFreezeDepth.set(prior+1);
        try{return presentationScope(frozen.actions(),()->work.run(frozen));}finally{if(prior==0)readFreezeDepth.remove();else readFreezeDepth.set(prior);}
    }

    /** Same-session observation publication only; this is not a ledger writer or an action retry. */
    public DriverSnapshotFacts.Known publishCapabilityInputs(ContinuityStorePort.Session borrowed,
            DriverSnapshotFacts.Stamp expected,String expectedAuxiliarySha256,
            DriverCapabilityStateProducer.InitialAuxiliary actual) throws IOException {
        Objects.requireNonNull(borrowed);Objects.requireNonNull(actual);
        return actions.withFrozen(borrowed,lease -> facts.locked(state -> {
            lease.assertCurrent();
            requireNoRawObservationMutation();facts.publishCapabilityInputs(expected,expectedAuxiliarySha256,actual);
            lease.assertCurrent();return (DriverSnapshotFacts.Known)facts.locked(next -> next);
        }));
    }

    /** Actual zero-day read event has already committed under this original writer; only the sole Driver CAS remains. */
    public void publishReadHistory(ContinuityStorePort.Session borrowed,DriverReadHistoryPublisher.Publication original,
            WriterContracts.Prepared prepared,WriterContracts.Receipt receipt) throws IOException {
        Objects.requireNonNull(original);original.requireCurrent(borrowed,prepared);borrowed.requireCommitted(prepared,receipt);
        StrictJson.require(prepared.request().kind().equals(WriterContracts.DRIVER_READ_HISTORY_KIND),"wrong committed read-history kind");
        actions.withFrozen(borrowed,lease -> facts.locked(state -> {
            lease.assertCurrent();StrictJson.require(state instanceof DriverSnapshotFacts.Known,"actual complete Driver unavailable after read commit");
            var known=(DriverSnapshotFacts.Known)state;var before=original.before();var replacement=original.replacement();
            var expected=before.stamp();var after=new DriverSnapshotFacts.Stamp(Math.addExact(expected.driverVersion(),1),expected.episodeEpoch(),
                    expected.game(),expected.episodeRunId(),DriverJson.sha256(replacement.encode()));
            var marker=new OpportunityJson.Obj(Map.of("event_identity",new OpportunityJson.Text(receipt.eventIdentity()),
                    "request_sha256",new OpportunityJson.Text(DriverJson.sha256(prepared.request().details()))));
            if(known.stamp().equals(after)&&Arrays.equals(known.driver().encode(),replacement.encode())
                    &&marker.equals(known.auxiliary().get("driver_read_publication")))return null;
            StrictJson.require(known.stamp().equals(expected)&&Arrays.equals(known.driver().encode(),before.driver().encode())
                    &&replacement.session().equals(before.driver().session())&&replacement.commandHistory().size()>before.driver().commandHistory().size(),"stale read-history complete Driver CAS");
            for(int i=0;i<before.driver().commandHistory().size();i++)StrictJson.require(Arrays.equals(
                    before.driver().commandHistory().get(i).originalRow().json(),replacement.commandHistory().get(i).originalRow().json()),"read publication rewrote original history prefix");
            for(int i=before.driver().commandHistory().size();i<replacement.commandHistory().size();i++) {
                byte[] originalRow=replacement.commandHistory().get(i).originalRow().json();var row=DriverJson.object(originalRow,DriverJson.MAX_NATIVE_BYTES);
                long index=row.members().containsKey(org.xar.ck3.control.application.history.DriverPostKnownReadFailureRowProducer.SOURCE_FIELD)
                        ?org.xar.ck3.control.application.history.DriverPostKnownReadFailureRowProducer.decode(originalRow).index()
                        :row.members().containsKey(org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryRowProducer.SOURCE_FIELD)
                        ?org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryRowProducer.decode(originalRow).index()
                        :row.members().containsKey(org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer.SOURCE_FIELD)
                        ?org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer.decode(originalRow).index()
                        :row.members().containsKey(org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer.SOURCE_FIELD)
                        ?org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer.decode(originalRow).index()
                        :row.members().containsKey(org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer.SOURCE_FIELD)
                        ?org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer.decode(originalRow).index()
                        :row.members().containsKey(org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer.SOURCE_FIELD)
                        ?org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer.decode(originalRow).index()
                        :row.members().containsKey(org.xar.ck3.control.application.history.DriverFailedReadHistoryRowProducer.SOURCE_FIELD)
                        ?org.xar.ck3.control.application.history.DriverFailedReadHistoryRowProducer.decode(originalRow).index()
                        :row.members().containsKey(org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD)
                        ?org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.decode(originalRow).index()
                        :row.members().containsKey(org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.SOURCE_FIELD)
                        ?org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.decode(originalRow).index()
                        :row.members().containsKey(org.xar.ck3.control.application.history.DriverObservedHistoryRowProducer.SOURCE_FIELD)
                        ?org.xar.ck3.control.application.history.DriverObservedHistoryRowProducer.decode(originalRow).index()
                        :org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.decode(originalRow).index();
                StrictJson.require(index==i+1L,"actual retained finite read row index changed");
            }
            var auxiliary=new java.util.LinkedHashMap<>(known.auxiliary().members());auxiliary.put("driver_read_publication",marker);
            if(original.containsFailures()) {
                // A failed attempt has only its original before-frame. It cannot lend that old source to the new history version.
                auxiliary.put("capability_observed_native_source",OpportunityJson.Nil.INSTANCE);
                auxiliary.put(org.xar.ck3.control.application.capabilities.DriverRuntimeCapabilities.AUXILIARY_KEY,OpportunityJson.Nil.INSTANCE);
            }
            requireNoRawObservationMutation();facts.compareAndSet(expected,new DriverSnapshotFacts.Known(replacement,after,known.originalHistoryBasis(),known.actionRows(),
                    new OpportunityJson.Obj(auxiliary),known.loop(),Optional.empty()));
            lease.assertCurrent();return null;
        }));
    }

    public <T>T withFrozenObservation(NativeObservationPort.ObservedFrame actual,
            ContinuityStorePort.Session borrowed, ObservationWork<T> work) throws IOException {
        return withObservation(actual,borrowed,work,true);
    }
    /** Private provenance for a read-only public planning input view. It is neither readiness nor
     * an action/transition permit and cannot outlive this identical immutable raw observation. */
    public final class ReadOnlyPlanningScope {
        private final RawCheckpointContext retained;
        private final DriverObservationAssembler.Complete frame;
        private final DriverSnapshotFacts.Known known;
        private final Instant deadline;
        private final Map<ExactRef,WriterContracts.Pin> sourcePins=new HashMap<>();
        private ReadOnlyPlanningScope(RawCheckpointContext retained,DriverObservationAssembler.Complete frame,
                DriverSnapshotFacts.Known known,Instant deadline) {
            this.retained=retained;this.frame=frame;this.known=known;this.deadline=deadline;
        }
        public void requireCurrent() throws IOException {
            requireRawPlanningContext(retained,known,deadline);
            for(var pin:sourcePins.values())retained.session.verifyPin(pin);
        }
        public void requireInputs(DriverObservationAssembler.Complete actual,DriverSnapshotFacts.Known current)throws IOException {
            requireCurrent();StrictJson.require(actual==frame&&current==known,
                    "read-only planning input view cannot be lent to another equal-looking frame or Driver");
        }
        public void verifySource(ExactRef actual)throws IOException {
            requireCurrent();if(!sourcePins.containsKey(actual)){var pin=retained.session.capturePin(actual,WriterContracts.MAX_PIN_BYTES);retained.session.verifyPin(pin);sourcePins.put(actual,pin);}requireCurrent();
        }
    }
    /** Only the real raw callback can obtain this private source provenance; no DTO can mint it. */
    public ReadOnlyPlanningScope openReadOnlyPlanningScope(ContinuityStorePort.Session same,
            DriverObservationAssembler.Complete frame,DriverSnapshotFacts.Known known,Instant deadline)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(frame);Objects.requireNonNull(known);Objects.requireNonNull(deadline);
        RawCheckpointContext retained=rawCheckpointContext.get();
        StrictJson.require(retained!=null&&retained.session==same&&retained.before==known&&retained.publication==null,
                "public planning inputs require the identical current raw observation and original writer");
        var originals=checkpointArchive(same).originals();
        StrictJson.require(Arrays.equals(originals.loadNativeFrame(frame.originalEvidence()),retained.nativeFrame.originalPacket()),
                "public planning frame lost its actual archived raw Native packet");
        var joined=new DriverObservationAssembler().assemble(retained.nativeFrame,retained.completed,frame.originalEvidence());
        StrictJson.require(joined instanceof DriverObservationAssembler.Complete&&joined.equals(frame),
                "public planning frame is not the actual complete same-subject raw Native/Driver join");
        var scope=new ReadOnlyPlanningScope(retained,frame,known,deadline);scope.requireCurrent();return scope;
    }
    /** Full raw terminal provenance retains the real missing/changed subject. No Complete or
     * lifecycle/action identity is constructed to describe its three terminal planning roles. */
    public final class ReadOnlyTerminalPlanningScope {
        private final RawCheckpointContext retained;
        private final DriverObservationAssembler.FullSnapshot full;
        private final DriverSnapshotFacts.Known known;
        private final Instant deadline;
        private final Map<ExactRef,WriterContracts.Pin> sourcePins=new HashMap<>();
        private ReadOnlyTerminalPlanningScope(RawCheckpointContext retained,DriverObservationAssembler.FullSnapshot full,
                DriverSnapshotFacts.Known known,Instant deadline) {
            this.retained=retained;this.full=full;this.known=known;this.deadline=deadline;
        }
        public void requireCurrent()throws IOException {requireRawPlanningContext(retained,known,deadline);for(var pin:sourcePins.values())retained.session.verifyPin(pin);}
        public void requireInputs(DriverObservationAssembler.FullSnapshot actual,DriverSnapshotFacts.Known current)throws IOException {
            requireCurrent();StrictJson.require(actual==full&&current==known,"terminal planning inventory left its identical full raw subject");
        }
        public void verifySource(ExactRef actual)throws IOException {
            requireCurrent();if(!sourcePins.containsKey(actual)){var pin=retained.session.capturePin(actual,WriterContracts.MAX_PIN_BYTES);retained.session.verifyPin(pin);sourcePins.put(actual,pin);}requireCurrent();
        }
    }
    public ReadOnlyTerminalPlanningScope openReadOnlyTerminalPlanningScope(ContinuityStorePort.Session same,
            DriverObservationAssembler.FullSnapshot full,DriverSnapshotFacts.Known known,Instant deadline)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(full);Objects.requireNonNull(known);Objects.requireNonNull(deadline);
        RawCheckpointContext retained=rawCheckpointContext.get();
        StrictJson.require(retained!=null&&retained.session==same&&retained.before==known&&retained.publication==null
                &&full.actual()==retained.nativeFrame&&full.facts()==retained.completed,
                "terminal capability inventory requires its actual full raw callback and writer");
        var originals=checkpointArchive(same).originals();
        StrictJson.require(Arrays.equals(originals.loadNativeFrame(full.originalEvidence()),retained.nativeFrame.originalPacket()),
                "terminal planning inventory lost its actual archived Native packet");
        var joined=new DriverObservationAssembler().projectFull(retained.nativeFrame,retained.completed,full.originalEvidence());
        StrictJson.require(joined.semantic().equals(full.semantic())&&joined.fullBindingSha256().equals(full.fullBindingSha256()),
                "terminal planning inventory substituted its full Native/Driver semantic projection");
        var scope=new ReadOnlyTerminalPlanningScope(retained,full,known,deadline);scope.requireCurrent();return scope;
    }
    private void requireRawPlanningContext(RawCheckpointContext retained,DriverSnapshotFacts.Known known,Instant deadline)throws IOException {
        StrictJson.require(rawCheckpointContext.get()==retained&&retained.publication==null
                &&retained.before==known&&Instant.now().isBefore(deadline)
                &&retained.session.head().digest().equals(retained.head),
                "read-only planning inputs left their actual raw scope, deadline or writer head");
        StrictJson.require(facts.locked(state->state)==known&&known.observation().filter(retained.completed::equals).isPresent(),
                "read-only planning inputs left their identical actual Driver/native facts");
    }
    /** Pure observation/recovery data only: no capability, token or domain publication and no ordinary eligibility. */
    public <T>T withFrozenRawObservation(NativeObservationPort.ObservedFrame actual,
            ContinuityStorePort.Session borrowed, ObservationWork<T> work) throws IOException {
        return withObservation(actual,borrowed,work,false);
    }
    private <T>T withObservation(NativeObservationPort.ObservedFrame actual,
            ContinuityStorePort.Session borrowed,ObservationWork<T> work,boolean publishCapabilities) throws IOException {
        Objects.requireNonNull(actual); Objects.requireNonNull(borrowed); Objects.requireNonNull(work);
        requireFreshObservationOutsideFreeze();
        try {
            return actions.withFrozen(borrowed,lease -> facts.locked(state -> {
                int prior=readFreezeDepth.get();readFreezeDepth.set(prior+1);
                try{return observeLocked(actual,borrowed,lease,work,publishCapabilities);}finally{if(prior==0)readFreezeDepth.remove();else readFreezeDepth.set(prior);}
            }));
        } catch(UncheckedIOException failure) { throw failure.getCause(); }
    }

    private <T>T observeLocked(NativeObservationPort.ObservedFrame actual,ContinuityStorePort.Session borrowed,
            ActionSnapshotReader.Lease lease,ObservationWork<T> work,boolean publishCapabilities) {
        lease.assertCurrent();
        StrictJson.require(facts.locked(state -> state) instanceof DriverSnapshotFacts.Known,"full Driver state unavailable for semantic observation");
        var known=(DriverSnapshotFacts.Known)facts.locked(state -> state);
        DriverObservationFacts.Result supplied=observationProducer.read(actual);
        if(supplied instanceof DriverObservationFacts.Unavailable missing)
            throw new IllegalStateException("actual frozen Driver observation unavailable: "+String.join(",",missing.reasons()));
        DriverObservationFacts observed=((DriverObservationFacts.Known)supplied).facts();
        if(publishCapabilities)observed=initializeOrdinaryGoal(actual,observed,lease);
        var observedOwner=(DriverSnapshotFacts.Known)facts.locked(state -> state);
        facts.replaceObservation(observedOwner.stamp(),observed);
        DriverObservationFacts completed=publishCapabilities?publishCapabilityObservation(actual,observed):observed;
        var current=(DriverSnapshotFacts.Known)facts.locked(state -> state);
        RawCheckpointContext raw=publishCapabilities?null:new RawCheckpointContext(borrowed,actual,current,completed,lease.snapshot().headSha256());
        StrictJson.require(rawCheckpointContext.get()==null,"raw checkpoint observation cannot recursively replace an existing scope");
        StrictJson.require(planningReadCallback.get()==null,"planning observation callback cannot recursively replace its actual scope");
        if(raw!=null)rawCheckpointContext.set(raw);
        planningReadCallback.set(new PlanningReadCallbackScope(borrowed,lease.snapshot().headSha256()));
        try {
            T result=presentationScope(lease.snapshot(),()->work.run(new FrozenObservation(current,lease.snapshot(),lease.activeActionId(),completed)));
            var after=(DriverSnapshotFacts.Known)facts.locked(state -> state);
            if(raw!=null&&raw.publication!=null) {
                var saved=raw.publication;
                StrictJson.require(saved.opening().context()==raw&&raw.before==current&&saved.after()==after&&after.observation().isEmpty()
                        &&lease.find(saved.opening().action().command().actionId()).filter(saved.opening().action()::equals).isPresent()
                        &&lease.snapshot().headSha256().equals(raw.head),"raw SAVE callback changed another Driver/action/head or retained obsolete semantic facts");
            }else StrictJson.require((raw==null||after==current)&&after.stamp().equals(current.stamp())&&after.observation().filter(completed::equals).isPresent(),
                    "Driver observation changed inside its frozen read scope");
            lease.assertCurrent();return result;
        }
        catch(IOException failure) { throw new UncheckedIOException(failure); }
        finally {planningReadCallback.remove();if(raw!=null)rawCheckpointContext.remove();}
    }

    /** Existing immutable material only; the publisher/bootstrap must have archived this exact version already. */
    public static ExactRef currentEvidence(Frozen frozen,DriverSnapshotFacts.Stamp expected,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(frozen); Objects.requireNonNull(expected); Objects.requireNonNull(archive);
        StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"full current Driver evidence unavailable");
        var known=(DriverSnapshotFacts.Known)frozen.state();
        StrictJson.require(known.stamp().equals(expected),"current Driver evidence crossed owner version");
        byte[] wire=known.driver().encode();
        StrictJson.require(wire.length<=RawJson.MAXIMUM_BYTES,"current Driver exceeds the qualified immutable material lane; no truncation");
        ExactRef exact=archive.materialReferenceOf(RawJson.fullMaterial(wire));
        StrictJson.require(exact.bytes()==wire.length && exact.sha256().equals(DriverJson.sha256(wire)),"current full Driver archive differs");
        return exact;
    }

    /** Sole post-commit CAS for the private actual archived-material publisher; validation ends before mutation. */
    void publishActionHistory(ContinuityStorePort.Session same,DriverActionHistoryPublisher.Publication publication) throws IOException {
        requireOutsideObservationScope(same);Objects.requireNonNull(publication);
        try {actions.withFrozen(same,lease -> facts.locked(state -> {
            StrictJson.require(state instanceof DriverSnapshotFacts.Known,"actual complete ACTION history predecessor unavailable");
            var before=(DriverSnapshotFacts.Known)state;
            try {publication.requireCurrent(same,this,before,lease);}catch(IOException failure){throw new UncheckedIOException(failure);}
            StrictJson.require(before.actionRows().stream().noneMatch(row->row.actionId().equals(publication.coverage().actionId())),
                    "same actual action already has original history coverage");
            var rows=new ArrayList<>(before.actionRows());rows.add(publication.coverage());
            var after=new DriverSnapshotFacts.Known(publication.replacement(),publication.after(),before.originalHistoryBasis(),rows,
                    before.auxiliary(),before.loop(),Optional.empty());
            var pending=qualifiedPendingChild(before,lease.snapshot()).filter(scope->org.xar.ck3.control.application.action.ActionCommandScope.current()
                    .filter(value->value.actionId().equals(publication.coverage().actionId())).isPresent());
            lease.assertCurrent();requireNoRawObservationMutation();facts.compareAndSet(before.stamp(),after);
            // This private custody advances only after the sole validated actual ACTION CAS, never from an incoming version or DTO.
            pending.ifPresent(scope->scope.expected=after);return null;
        }));}catch(UncheckedIOException failure){throw failure.getCause();}
    }

    /** Publishes the history adapter's original compatible row, never a result synthesized from expected effects. */
    public void publishOriginalHistory(DriverSnapshotFacts.Stamp expected,ActionReceipt actual,
            DriverStateSnapshot.HistoryEntry originalRow,ExactRef originalHistoryRow) {
        Objects.requireNonNull(expected);Objects.requireNonNull(actual);Objects.requireNonNull(originalRow);Objects.requireNonNull(originalHistoryRow);
        StrictJson.require(originalHistoryRow.bytes()==originalRow.originalRow().json().length
                && originalHistoryRow.sha256().equals(DriverJson.sha256(originalRow.originalRow().json())),"original compatible history row evidence differs");
        actions.withFrozen(lease -> facts.locked(state -> {
            lease.assertCurrent();StrictJson.require(state instanceof DriverSnapshotFacts.Known,"full Driver predecessor unavailable");
            var before=(DriverSnapshotFacts.Known)state;
            StrictJson.require(before.stamp().equals(expected),"stale history Driver CAS");
            ActionReceipt current=lease.find(actual.command().actionId()).orElseThrow(() -> new IllegalArgumentException("original durable action absent"));
            StrictJson.require(current.equals(actual) && current.settled(),"history projection requires the actual settled action receipt");
            StrictJson.require(actual.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                    ? actual.command().before().game().equals(expected.game())&&actual.command().before().frame().episodeRunId().equals(before.driver().session().episodeRunId())
                    : actual.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.LifecycleTerminal terminal
                        &&sameLifecycleSubject(terminal.identity(),before,true),"history row crossed actual Game/episode/terminal subject");
            StrictJson.require(before.actionRows().stream().noneMatch(row -> row.actionId().equals(actual.command().actionId())),"original action history row already published");
            StrictJson.require(originalRow.index()==before.driver().commandHistory().size()+1L,"original history row must append contiguously");
            var row=DriverJson.object(originalRow.originalRow().json(),DriverJson.MAX_NATIVE_BYTES);
            StrictJson.require(!row.members().containsKey(DriverActionHistoryCodec.SOURCE_FIELD),
                    "new ACTION source metadata requires its private committed publication; the legacy adapter cannot grant it");
            boolean originalOk=actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED;
            StrictJson.require(OpportunityJson.text(row.get("command"),"command").equals(actual.command().operation().value())
                    && OpportunityJson.bool(row.get("ok"),"ok")==originalOk,"original action/history outcome disagrees");
            var history=new ArrayList<>(before.driver().commandHistory());history.add(originalRow);
            var old=before.driver();
            var driver=new DriverStateSnapshot.Complete(old.session(),history,old.lastCheckpoint(),old.rollbackWarFailure(),
                    old.managedRestoreTransaction(),old.successionExpectation(),old.successionLifecycle(),old.campaignGoal(),old.rollbackWarFailures());
            var coverage=new ArrayList<>(before.actionRows());
            coverage.add(new DriverSnapshotFacts.ActionRow(actual.command().actionId(),actual.bodySha256(),actual.sequence(),originalRow.index(),originalHistoryRow));
            var stamp=new DriverSnapshotFacts.Stamp(Math.addExact(expected.driverVersion(),1),expected.episodeEpoch(),expected.game(),expected.episodeRunId(),DriverJson.sha256(driver.encode()));
            requireNoRawObservationMutation();facts.compareAndSet(expected,new DriverSnapshotFacts.Known(driver,stamp,before.originalHistoryBasis(),coverage,before.auxiliary(),before.loop(),Optional.empty()));
            lease.assertCurrent();return null;
        }));
    }

    @Override public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) throws IOException {
        Objects.requireNonNull(work);
        try {
            return actions.withFrozen(lease -> facts.locked(state -> {
                lease.assertCurrent();RawCheckpointContext raw=rawCheckpointContext.get();
                Optional<RawCheckpointOpening> opening=Optional.empty();
                if(raw!=null&&state instanceof DriverSnapshotFacts.Known known&&lease.activeActionId().isPresent()
                        &&lease.find(lease.activeActionId().orElseThrow()).filter(value->value.command().operation().value().equals("save-checkpoint")).isPresent()) {
                    try{opening=Optional.of(checkpointOpening(raw,known,lease));}catch(IOException failure){throw new UncheckedIOException(failure);}
                }
                final Optional<RawCheckpointOpening> qualified=opening;
                DriverStateSnapshot projection;
                try{projection=presentationScope(lease.snapshot(),()->qualified.isPresent()?projectObservation((DriverSnapshotFacts.Known)state,lease.snapshot(),lease.activeActionId(),qualified)
                        :project(state,lease.snapshot(),lease.activeActionId()));}
                catch(IOException failure){throw new UncheckedIOException(failure);}
                AtomicBoolean open=new AtomicBoolean(true); AtomicBoolean published=new AtomicBoolean();
                try {
                    return work.run(projection,(expected,replacement) -> {
                        StrictJson.require(open.get() && !published.get(),"Driver snapshot publisher lease is closed or already used");
                        lease.assertCurrent();
                        StrictJson.require(state instanceof DriverSnapshotFacts.Known && projection instanceof DriverStateSnapshot.Complete,
                                "incomplete Driver cannot publish a checkpoint");
                        DriverSnapshotFacts.Known known=(DriverSnapshotFacts.Known)state;
                        if(raw!=null)StrictJson.require(rawCheckpointContext.get()==raw&&qualified.isPresent()&&raw.publication==null&&raw.before==known,
                                "only one source-qualified original SAVE publication may mutate this raw scope");
                        StrictJson.require(Arrays.equals(known.driver().encode(),expected.encode()),"checkpoint expected another Driver version");
                        String actionId=lease.activeActionId().orElseThrow(() -> new IllegalArgumentException("SAVE must borrow its actual coordinator action scope"));
                        ActionReceipt action=lease.find(actionId).orElseThrow(() -> new IllegalArgumentException("actual durable SAVE receipt absent"));
                        validateCheckpoint(expected,replacement,action,known.stamp());
                        var last=replacement.commandHistory().getLast();
                        OpportunityJson.Obj row=DriverJson.object(last.originalRow().json(),DriverJson.MAX_NATIVE_BYTES);
                        OpportunityJson.Obj checkpoint=OpportunityJson.object(OpportunityJson.object(row.get("result"),"result").get("checkpoint"),"checkpoint");
                        ExactRef save=new ExactRef(OpportunityJson.text(checkpoint.get("path"),"path"),
                                OpportunityJson.integer(checkpoint.get("size"),"size").longValueExact(),OpportunityJson.text(checkpoint.get("sha256"),"sha256"));
                        List<DriverSnapshotFacts.ActionRow> coverage=new ArrayList<>(known.actionRows());
                        coverage.removeIf(entry -> entry.actionId().equals(actionId));
                        var bound=checkpointArchive(raw==null?null:raw.session);ActionPorts.OutcomeArchive originals=bound.originals();
                        RawJson originalRow=new RawJson(last.originalRow().json());ExactRef retainedRow=originals.preserveMaterial(originalRow);
                        StrictJson.require(originalRow.equals(originals.loadMaterial(retainedRow)),"actual original SAVE history row archive differs");
                        coverage.add(new DriverSnapshotFacts.ActionRow(actionId,action.bodySha256(),action.sequence(),last.index(),retainedRow));
                        var stamp=new DriverSnapshotFacts.Stamp(Math.addExact(known.stamp().driverVersion(),1),known.stamp().episodeEpoch(),
                                known.stamp().game(),replacement.session().episodeRunId(),DriverJson.sha256(replacement.encode()));
                        var auxiliary=new java.util.LinkedHashMap<>(known.auxiliary().members());
                        if(auxiliary.containsKey("rollback_war_failures_migration_required")) {
                            OpportunityJson.bool(auxiliary.get("rollback_war_failures_migration_required"),"rollback_war_failures_migration_required");
                            auxiliary.put("rollback_war_failures_migration_required",new OpportunityJson.Bool(false));
                        }
                        var next=new DriverSnapshotFacts.Known(replacement,stamp,known.originalHistoryBasis(),coverage,new OpportunityJson.Obj(auxiliary),known.loop(),Optional.empty());
                        RawCheckpointPublication saved=null;
                        if(raw!=null) {
                            var rechecked=checkpointOpening(raw,known,lease);var original=qualified.orElseThrow();
                            StrictJson.require(rechecked.action().equals(original.action())&&rechecked.attempt().equals(original.attempt())
                                    &&rechecked.ack().equals(original.ack())&&rechecked.originalAck().equals(original.originalAck())
                                    &&rechecked.heldFrame().equals(original.heldFrame())&&save.bytes()>0,"nested SAVE original ACK/Attempt/frame changed before CAS");
                            saved=new RawCheckpointPublication(original,next,retainedRow,save);
                        }
                        lease.assertCurrent();facts.compareAndSet(known.stamp(),next);
                        if(raw!=null)raw.publication=Objects.requireNonNull(saved);
                        published.set(true);lease.assertCurrent();
                    });
                } catch(IOException failure) { throw new UncheckedIOException(failure); }
                finally { open.set(false); }
            }));
        } catch(UncheckedIOException failure) { throw failure.getCause(); }
    }

    /** Original lifecycle reducer prepares the full replacement privately; only its small digest delta enters the ledger. */
    public void publishCommitted(DriverSnapshotFacts.Stamp expected, DriverStateSnapshot.Complete replacement,
            OpportunityJson.Obj auxiliary, WriterContracts.Prepared originalPrepared, WriterContracts.Receipt actualReceipt) {
        Objects.requireNonNull(expected); Objects.requireNonNull(replacement); Objects.requireNonNull(auxiliary);
        Objects.requireNonNull(originalPrepared); Objects.requireNonNull(actualReceipt);
        actions.withFrozen(lease -> facts.locked(state -> {
            lease.assertCurrent(); StrictJson.require(state instanceof DriverSnapshotFacts.Known,"complete Driver predecessor required");
            DriverSnapshotFacts.Known before=(DriverSnapshotFacts.Known)state;
            StrictJson.require(before.stamp().equals(expected),"lifecycle Driver version CAS failed");
            var committed=originalPrepared.reduced().toJson();
            committed.put("sequence",Math.addExact(originalPrepared.predecessor().state().sequence(),1));
            committed.put("last_event_identity",originalPrepared.request().identity());
            StrictJson.require(actualReceipt.disposition()!=WriterContracts.Disposition.NO_CHANGE
                    && actualReceipt.eventIdentity().equals(originalPrepared.request().identity())
                    && ContinuityJson.same(actualReceipt.head().toJson(),committed)
                    && actualReceipt.head().sequence()==lease.snapshot().ledgerSequence()
                    && ContinuityJson.digest(actualReceipt.head().toJson()).equals(lease.snapshot().headSha256())
                    && actualReceipt.head().sequence()>originalPrepared.predecessor().state().sequence(),"actual original writer commit does not bind lifecycle replacement");
            OpportunityJson.Obj details=DriverJson.object(originalPrepared.request().details(),DriverJson.MAX_NATIVE_BYTES);
            OpportunityJson.Obj delta=OpportunityJson.object(details.get("driver_snapshot"),"driver_snapshot");
            StrictJson.require(OpportunityJson.integer(delta.get("expected_version"),"expected_version").longValueExact()==expected.driverVersion()
                    && OpportunityJson.integer(delta.get("expected_epoch"),"expected_epoch").longValueExact()==expected.episodeEpoch()
                    && expected.driverSha256().equals(OpportunityJson.text(delta.get("before_sha256"),"before_sha256"))
                    && DriverJson.sha256(replacement.encode()).equals(OpportunityJson.text(delta.get("after_sha256"),"after_sha256")),"durable lifecycle delta differs from complete Driver replacement");
            long nextEpoch=OpportunityJson.integer(delta.get("next_epoch"),"next_epoch").longValueExact();
            StrictJson.require(nextEpoch==expected.episodeEpoch() || nextEpoch==Math.addExact(expected.episodeEpoch(),1),"lifecycle epoch must stay or advance once");
            // The actual new Game generation is part of the domain's committed, typed after evidence.
            OpportunityJson.Obj generation=OpportunityJson.object(details.get("driver_after_game"),"driver_after_game");
            long pid=OpportunityJson.integer(generation.get("pid"),"pid").longValueExact();
            String birth=OpportunityJson.text(generation.get("creation_filetime"),"creation_filetime");
            var decimal=new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(birth);
            var game=new org.xar.ck3.control.contracts.GameGeneration(pid,
                    new org.xar.ck3.control.contracts.PythonOnlyUInt64(new java.math.BigInteger(decimal.decimal())));
            var stamp=new DriverSnapshotFacts.Stamp(Math.addExact(expected.driverVersion(),1),nextEpoch,game,
                    replacement.session().episodeRunId(),DriverJson.sha256(replacement.encode()));
            // Row coverage must be republished from the original action-history producer after an episode/branch transition.
            List<DriverSnapshotFacts.ActionRow> rows=replacement.session().equals(before.driver().session()) ? before.actionRows() : List.of();
            requireNoRawObservationMutation();facts.compareAndSet(expected,new DriverSnapshotFacts.Known(replacement,stamp,before.originalHistoryBasis(),rows,auxiliary,before.loop(),Optional.empty()));
            lease.assertCurrent(); return null;
        }));
    }

    /** Shared lifecycle auxiliary DATA projection. This does not validate membership, mint a Known, adopt or publish. */
    public static OpportunityJson.Obj lifecyclePublishedAuxiliary(OpportunityJson.Obj actualReductionAuxiliary,
            WriterContracts.Request actualLifecycleRequest,WriterContracts.Receipt actualReceipt) {
        Objects.requireNonNull(actualReductionAuxiliary);Objects.requireNonNull(actualReceipt);
        StrictJson.require(actualLifecycleRequest.kind().equals(org.xar.ck3.control.application.lifecycle.LifecycleChild.KIND),"actual lifecycle request kind required");
        var details=DriverJson.object(actualLifecycleRequest.details(),DriverJson.MAX_NATIVE_BYTES);
        var delta=OpportunityJson.object(details.get("driver_snapshot"),"driver_snapshot");String auxiliarySha=DriverJson.sha256(DriverJson.encode(actualReductionAuxiliary));
        StrictJson.require(auxiliarySha.equals(OpportunityJson.text(delta.get("auxiliary_after_sha256"),"auxiliary_after_sha256")),"lifecycle original reduction auxiliary differs");
        var marker=new OpportunityJson.Obj(Map.of("event_identity",new OpportunityJson.Text(actualReceipt.eventIdentity()),
                "request_sha256",new OpportunityJson.Text(DriverJson.sha256(actualLifecycleRequest.details())),"original_auxiliary_sha256",new OpportunityJson.Text(auxiliarySha)));
        return actualReductionAuxiliary.with("lifecycle_publication",marker);
    }

    /** Read-only completion of a genuine canonical historical lifecycle commit under the original Session. */
    public void publishCommitted(ContinuityStorePort.Session borrowed,DriverSnapshotFacts.Stamp expected,
            DriverStateSnapshot.Complete replacement,OpportunityJson.Obj auxiliary,
            WriterContracts.Prepared originalPrepared,WriterContracts.Receipt actualReceipt) throws IOException {
        Objects.requireNonNull(borrowed);Objects.requireNonNull(expected);Objects.requireNonNull(replacement);Objects.requireNonNull(auxiliary);
        Objects.requireNonNull(originalPrepared);Objects.requireNonNull(actualReceipt);
        // The sole writer reads and verifies the actual immutable canonical event, including the full historical predecessor/reducer.
        borrowed.requireCommitted(originalPrepared,actualReceipt);
        actions.withFrozen(borrowed,lease -> facts.locked(state -> {
            lease.assertCurrent();StrictJson.require(state instanceof DriverSnapshotFacts.Known,"complete Driver lifecycle predecessor unavailable");
            var before=(DriverSnapshotFacts.Known)state;
            OpportunityJson.Obj details=DriverJson.object(originalPrepared.request().details(),DriverJson.MAX_NATIVE_BYTES);
            OpportunityJson.Obj delta=OpportunityJson.object(details.get("driver_snapshot"),"driver_snapshot");
            String afterSha=DriverJson.sha256(replacement.encode());
            StrictJson.require(originalPrepared.request().kind().equals(org.xar.ck3.control.application.lifecycle.LifecycleChild.KIND)
                    &&OpportunityJson.integer(delta.get("expected_version"),"expected_version").longValueExact()==expected.driverVersion()
                    &&OpportunityJson.integer(delta.get("expected_epoch"),"expected_epoch").longValueExact()==expected.episodeEpoch()
                    &&expected.driverSha256().equals(OpportunityJson.text(delta.get("before_sha256"),"before_sha256"))
                    &&afterSha.equals(OpportunityJson.text(delta.get("after_sha256"),"after_sha256")),"canonical lifecycle delta differs from original complete Driver replacement");
            StrictJson.require(DriverJson.sha256(DriverJson.encode(auxiliary)).equals(OpportunityJson.text(delta.get("auxiliary_after_sha256"),"auxiliary_after_sha256")),"canonical lifecycle auxiliary differs from actual reducer replacement");
            long nextEpoch=OpportunityJson.integer(delta.get("next_epoch"),"next_epoch").longValueExact();
            StrictJson.require(nextEpoch==expected.episodeEpoch()||nextEpoch==Math.addExact(expected.episodeEpoch(),1),"lifecycle epoch advances at most once");
            OpportunityJson.Obj generation=OpportunityJson.object(details.get("driver_after_game"),"driver_after_game");
            var game=new org.xar.ck3.control.contracts.GameGeneration(OpportunityJson.integer(generation.get("pid"),"pid").longValueExact(),
                    new org.xar.ck3.control.contracts.PythonOnlyUInt64(new java.math.BigInteger(new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(
                            OpportunityJson.text(generation.get("creation_filetime"),"creation_filetime")).decimal())));
            var afterStamp=new DriverSnapshotFacts.Stamp(Math.addExact(expected.driverVersion(),1),nextEpoch,game,replacement.session().episodeRunId(),afterSha);
            OpportunityJson.Obj publishedAuxiliary=lifecyclePublishedAuxiliary(auxiliary,originalPrepared.request(),actualReceipt);
            OpportunityJson.Obj publication=OpportunityJson.object(publishedAuxiliary.get("lifecycle_publication"),"lifecycle_publication");
            if(before.stamp().equals(afterStamp)) {
                StrictJson.require(Arrays.equals(before.driver().encode(),replacement.encode())&&publication.equals(before.auxiliary().get("lifecycle_publication")),"historical lifecycle idempotent publication differs from actual owner provenance");
                lease.assertCurrent();return null;
            }
            StrictJson.require(before.stamp().equals(expected),"historical lifecycle Driver CAS predecessor drift");
            List<DriverSnapshotFacts.ActionRow> coverage=new ArrayList<>(replacement.session().equals(before.driver().session())?before.actionRows():List.of());
            OpportunityJson.Obj domainDelta=OpportunityJson.object(details.get("delta"),"delta");
            if(domainDelta.members().containsKey("history_binding")) {
                var binding=org.xar.ck3.control.application.lifecycle.LifecycleHistoryBinding.fromJson(
                        org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(domainDelta.get("history_binding")));
                StrictJson.require(replacement.session().equals(before.driver().session())&&"DEATH_RECORDED".equals(OpportunityJson.text(details.get("phase"),"phase"))
                        &&"death-terminal".equals(OpportunityJson.text(details.get("operation"),"operation"))
                        &&binding.actionId().equals(OpportunityJson.text(details.get("parent_action_id"),"parent_action_id"))
                        &&binding.parentBodySha256().equals(OpportunityJson.text(details.get("parent_body_sha256"),"parent_body_sha256"))
                        &&originalPrepared.request().evidence().contains(binding.originalRow())
                        &&binding.historyIndex()==replacement.commandHistory().size()
                        &&replacement.commandHistory().size()==before.driver().commandHistory().size()+1,"actual canonical terminal history binding differs");
                for(int index=0;index<before.driver().commandHistory().size();index++)StrictJson.require(Arrays.equals(before.driver().commandHistory().get(index).originalRow().json(),replacement.commandHistory().get(index).originalRow().json()),"lifecycle terminal rewrote preceding history");
                byte[] original=replacement.commandHistory().getLast().originalRow().json();OpportunityJson.Obj row=DriverJson.object(original,DriverJson.MAX_NATIVE_BYTES);
                StrictJson.require(binding.originalRow().bytes()==original.length&&binding.originalRow().sha256().equals(DriverJson.sha256(original))
                        &&"death-terminal".equals(OpportunityJson.text(row.get("command"),"command"))&&OpportunityJson.bool(row.get("ok"),"ok")
                        &&Objects.equals(row.get("result"),domainDelta.get("result")),"published terminal history differs from archived canonical row/result");
                StrictJson.require(coverage.stream().noneMatch(existing -> existing.actionId().equals(binding.actionId())),"lifecycle terminal row was already covered");
                coverage.add(new DriverSnapshotFacts.ActionRow(binding.actionId(),binding.parentBodySha256(),
                        Math.addExact(originalPrepared.predecessor().state().sequence(),1),binding.historyIndex(),binding.originalRow()));
            } else if(replacement.session().equals(before.driver().session()))StrictJson.require(Arrays.equals(replacement.encode(),before.driver().encode()),"same-episode lifecycle history change requires original canonical history binding");
            requireNoRawObservationMutation();facts.compareAndSet(expected,new DriverSnapshotFacts.Known(replacement,afterStamp,before.originalHistoryBasis(),coverage,publishedAuxiliary,before.loop(),Optional.empty()));
            lease.assertCurrent();return null;
        }));
    }

    @Override public DriverObservationFacts.Result read(NativeObservationPort.ObservedFrame actual) {
        Objects.requireNonNull(actual);
        requireFreshObservationOutsideFreeze();
        return actions.withFrozen(lease -> facts.locked(state -> {
            lease.assertCurrent();
            if (!(state instanceof DriverSnapshotFacts.Known known)) return new DriverObservationFacts.Unavailable(((DriverSnapshotFacts.Unavailable)state).reasons());
            DriverObservationFacts.Result result=observationProducer.read(actual);
            if (result instanceof DriverObservationFacts.Known supplied) {
                StrictJson.require(supplied.facts().driverVersion()==known.stamp().driverVersion()
                        && supplied.facts().episodeEpoch()==known.stamp().episodeEpoch()
                        && Arrays.equals(supplied.facts().driver().encode(),known.driver().encode()),"semantic provider does not hold the actual complete Driver version");
                DriverObservationFacts observed=initializeOrdinaryGoal(actual,supplied.facts(),lease);
                var observedOwner=(DriverSnapshotFacts.Known)facts.locked(current -> current);
                facts.replaceObservation(observedOwner.stamp(),observed);
                result=new DriverObservationFacts.Known(publishCapabilityObservation(actual,observed));
            }
            lease.assertCurrent(); return result;
        }));
    }
    /** A caller inside a frozen read must borrow that actual observation, never recapture and replace it. */
    private void requireFreshObservationOutsideFreeze() {
        StrictJson.require(readFreezeDepth.get()==0,"fresh Driver observation cannot replace an immutable Driver read scope; borrow its existing actual observation");
    }
    /** First ordinary intent after actual observation; raw restore, staged NEXT and UNKNOWN retain their original Driver. */
    private DriverObservationFacts initializeOrdinaryGoal(NativeObservationPort.ObservedFrame actual,
            DriverObservationFacts observed,ActionSnapshotReader.Lease lease) {
        synchronized(this) { if(pendingNextCapabilityTransfer!=null || candidateScope.get()!=null)return observed; }
        if(lease.activeActionId().isPresent() || lease.snapshot().actions().stream().anyMatch(row -> !row.settled()))return observed;
        var before=(DriverSnapshotFacts.Known)facts.locked(state -> state);
        Optional<DriverStateSnapshot.Complete> candidate=DriverOrdinaryGoalInitialization.prepare(before,observed,actual);
        if(candidate.isEmpty())return observed;
        DriverStateSnapshot.Complete replacement=candidate.orElseThrow();
        var expected=before.stamp();
        var stamp=new DriverSnapshotFacts.Stamp(Math.addExact(expected.driverVersion(),1),expected.episodeEpoch(),
                expected.game(),expected.episodeRunId(),DriverJson.sha256(replacement.encode()));
        var after=new DriverSnapshotFacts.Known(replacement,stamp,before.originalHistoryBasis(),before.actionRows(),
                before.auxiliary(),before.loop(),Optional.empty());
        lease.assertCurrent();requireNoRawObservationMutation();
        synchronized(this) {
            StrictJson.require(pendingNextCapabilityTransfer==null && candidateScope.get()==null,
                    "ordinary goal initialization crossed staged NEXT custody");
            facts.compareAndSet(expected,after);
        }
        // Re-project this same received packet against the new full Driver. No Native request is sent.
        DriverObservationFacts.Result refreshed=observationProducer.read(actual);
        StrictJson.require(refreshed instanceof DriverObservationFacts.Known,
                "ordinary goal initialization lost its actual same-frame Driver manifest");
        DriverObservationFacts completed=((DriverObservationFacts.Known)refreshed).facts();
        StrictJson.require(completed.driverVersion()==stamp.driverVersion() && completed.episodeEpoch()==stamp.episodeEpoch()
                && Arrays.equals(completed.driver().encode(),replacement.encode())
                && completed.transport().equals(observed.transport()) && completed.snapshotId().equals(observed.snapshotId())
                && completed.nativeRevision().equals(observed.nativeRevision())
                && completed.nativeStateSha256().equals(observed.nativeStateSha256())
                && completed.publicRevision().equals(observed.publicRevision()) && completed.source().equals(observed.source())
                && completed.observationVersion()==observed.observationVersion(),
                "ordinary goal initialization changed original Native/frame/source identity");
        lease.assertCurrent();return completed;
    }
    private DriverObservationFacts publishCapabilityObservation(NativeObservationPort.ObservedFrame actual,DriverObservationFacts observed) {
        CapabilityObservation producer;
        CandidateScope staged=candidateScope.get();
        synchronized(this) {
            if(pendingNextCapabilityTransfer!=null)StrictJson.require(staged!=null&&staged.transfer()==pendingNextCapabilityTransfer,"staged NEXT observation cannot invoke the old runtime callback");
            producer=staged==null?capabilityObservation:staged.observation();
        }
        if(producer==null)return observed;
        var current=(DriverSnapshotFacts.Known)facts.locked(state -> state);
        Optional<DriverCapabilityStateProducer.InitialAuxiliary> publication=producer.observe(actual,current);
        if(publication.isEmpty())return observed;
        var actualPublication=publication.orElseThrow();
        requireNoRawObservationMutation();facts.publishCapabilityInputs(current.stamp(),actualPublication.expectedAuxiliarySha256(),actualPublication);
        if(staged!=null)staged.transfer().auxiliarySha256=DriverJson.sha256(DriverJson.encode(actualPublication.auxiliary()));
        // Reuse the identical actual packet/public-revision producer; the final manifest includes the new source refs.
        var refreshed=observationProducer.read(actual);
        StrictJson.require(refreshed instanceof DriverObservationFacts.Known,"capability publication lost its actual same-frame Driver manifest");
        var completed=((DriverObservationFacts.Known)refreshed).facts();facts.replaceObservation(current.stamp(),completed);return completed;
    }

    public static DriverStateSnapshot project(DriverSnapshotFacts.State state, ActionJournal.Snapshot durable,
            Optional<String> activeActionId) {
        return projectInternal(state,durable,activeActionId,Optional.empty());
    }
    /** Only the current coordinator-owned parent can be unresolved while reading its own surviving history. */
    public static DriverStateSnapshot projectHistory(DriverSnapshotFacts.Known state,ActionJournal.Snapshot durable,
            Optional<String> activeActionId,ActionCommand actualParent) {
        Objects.requireNonNull(actualParent);
        return projectInternal(state,durable,activeActionId,Optional.of(actualParent));
    }
    /** A current INTENT/known attempt may obtain its guard/poststate. An UNKNOWN is never made eligible by scope. */
    public static DriverStateSnapshot projectObservation(DriverSnapshotFacts.Known state,ActionJournal.Snapshot durable,
            Optional<String> activeActionId) {
        return projectObservation(state,durable,activeActionId,Optional.empty());
    }
    private static DriverStateSnapshot projectObservation(DriverSnapshotFacts.Known state,ActionJournal.Snapshot durable,
            Optional<String> activeActionId,Optional<RawCheckpointOpening> checkpoint) {
        Optional<PendingChildScope> pending=qualifiedPendingChild(state,durable);
        Optional<ActionCommand> active=org.xar.ck3.control.application.action.ActionCommandScope.current()
                .filter(command -> activeActionId.filter(command.actionId()::equals).isPresent());
        if(active.isEmpty())active=durable.actions().stream().filter(action -> activeActionId.filter(action.command().actionId()::equals).isPresent()).map(ActionReceipt::command).findFirst();
        active=active.filter(command -> observationSubject(command,state));
        Optional<ActionCommand> ancestor=Optional.empty();
        if(pending.isPresent()) {
            var scope=pending.orElseThrow();active=org.xar.ck3.control.application.action.ActionCommandScope.current();
            var ancestors=active.filter(scope.child()::equals).isPresent()?List.of(scope.parent()):List.of(scope.parent(),scope.child());
            return projectInternal(state,durable,activeActionId,active,ancestors,checkpoint);
        }
        if(active.isPresent()&&org.xar.ck3.control.application.action.ActionCommandScope.current().filter(active.orElseThrow()::equals).isPresent()) {
            ActionCommand current=active.orElseThrow();
            for(ActionReceipt parent:durable.actions())if(parent.state() instanceof ActionState.CompositeRunning running
                    &&running.execution().children().stream().anyMatch(child -> child.actionId().equals(current.actionId())
                        &&child.bodySha256().equals(org.xar.ck3.control.application.action.ActionCodec.bodySha256(current)))) {
                boolean pendingParent=pending.filter(scope->scope.parent().equals(parent.command())&&scope.child().equals(current)).isPresent();
                StrictJson.require((ancestor.isEmpty()||pendingParent&&ancestor.filter(parent.command()::equals).isPresent())
                        &&(observationSubject(parent.command(),state)||pendingParent)
                        &&parent.command().source().equals(current.source())&&parent.command().sessionId().equals(current.sessionId())
                        &&(pendingParent||!current.deadline().isAfter(parent.command().deadline())),"current child crossed its sole durable parent/source/deadline");
                if(pendingParent)StrictJson.require(current.origin() instanceof CommandOrigin.Gameplay&&observationSubject(current,state),
                        "qualified pending child lost its actual new subject");
                else if(parent.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.LifecycleTerminal terminal)
                    StrictJson.require(current.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.LifecycleTerminal child
                            &&terminal.identity().sameSession(child.identity())
                            &&parent.command().operation().value().equals("continue-as-reconciled-successor")
                            &&current.operation().value().equals("continue-death-succession-modal-v1"),"terminal scope is restricted to the actual successor modal child");
                else StrictJson.require(current.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay,"ordinary parent requires an ordinary current child");
                for(var sibling:running.execution().children())if(!sibling.actionId().equals(current.actionId()))
                    StrictJson.require(durable.actions().stream().anyMatch(actual -> actual.command().actionId().equals(sibling.actionId())
                            &&actual.bodySha256().equals(sibling.bodySha256())&&actual.settled()),"current child has an unresolved or changed sibling");
                ancestor=Optional.of(parent.command());
            }
        }
        return projectInternal(state,durable,activeActionId,active,ancestor.stream().toList(),checkpoint);
    }
    private static boolean observationSubject(ActionCommand command,DriverSnapshotFacts.Known state) {
        return command.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay gameplay
                ? gameplay.before().game().equals(state.stamp().game())&&gameplay.before().frame().episodeRunId().equals(state.stamp().episodeRunId())
                    &&gameplay.before().frame().identity().player().equals(state.driver().session().actorId())
                : command.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.LifecycleTerminal terminal&&sameLifecycleSubject(terminal.identity(),state,true);
    }
    private static DriverStateSnapshot projectInternal(DriverSnapshotFacts.State state,ActionJournal.Snapshot durable,
            Optional<String> activeActionId,Optional<ActionCommand> allowedParent) {
        return projectInternal(state,durable,activeActionId,allowedParent,Optional.empty());
    }
    private static DriverStateSnapshot projectInternal(DriverSnapshotFacts.State state,ActionJournal.Snapshot durable,
            Optional<String> activeActionId,Optional<ActionCommand> allowedParent,Optional<ActionCommand> actualAncestor) {
        return projectInternal(state,durable,activeActionId,allowedParent,actualAncestor.stream().toList());
    }
    private static DriverStateSnapshot projectInternal(DriverSnapshotFacts.State state,ActionJournal.Snapshot durable,
            Optional<String> activeActionId,Optional<ActionCommand> allowedParent,List<ActionCommand> actualAncestors) {
        return projectInternal(state,durable,activeActionId,allowedParent,actualAncestors,Optional.empty());
    }
    private static DriverStateSnapshot projectInternal(DriverSnapshotFacts.State state,ActionJournal.Snapshot durable,
            Optional<String> activeActionId,Optional<ActionCommand> allowedParent,List<ActionCommand> actualAncestors,
            Optional<RawCheckpointOpening> checkpoint) {
        Objects.requireNonNull(state);Objects.requireNonNull(durable);Objects.requireNonNull(activeActionId);
        if (state instanceof DriverSnapshotFacts.Unavailable missing) return new DriverStateSnapshot.Incomplete(missing.reasons());
        DriverSnapshotFacts.Known known=(DriverSnapshotFacts.Known)state; List<String> missing=new ArrayList<>();
        if (!(durable.originalHistory() instanceof ActionJournal.BoundHistoryBasis bound)
                || !bound.originalDriverHistory().equals(known.originalHistoryBasis())) missing.add("original_full_history_baseline_not_bound_in_canonical_writer");
        Map<String,DriverSnapshotFacts.ActionRow> rows=new HashMap<>(); known.actionRows().forEach(row -> rows.put(row.actionId(),row));
        // These exact source-validated Life controls retain their effects without a second recorder row.
        var prefixControls = new java.util.HashSet<ActionReceipt>();
        for (ActionReceipt parent : durable.actions()) {
            if (!(parent.state() instanceof ActionState.CompositeSettled settled)
                    || !parent.command().before().game().equals(known.stamp().game())
                    || !parent.command().before().frame().episodeRunId().equals(known.driver().session().episodeRunId())) continue;
            boolean cancelledInitialization = settled.settlement() instanceof ActionState.CompositeControlApplied control
                    && org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(parent.command().operation().value())
                    && settled.execution().handlerId().equals(org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER)
                    && control.observation().semantic().actual().contains(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText(
                            new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("progress_status"), "initialization_cancelled"));
            boolean rejectedInitialization = settled.settlement() instanceof ActionState.CompositeRejected rejected
                    && org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(parent.command().operation().value())
                    && settled.execution().handlerId().equals(org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER)
                    && rejected.evidence().isEmpty();
            if (!(settled.settlement() instanceof ActionState.LifeControlPrefixInterrupted) && !cancelledInitialization && !rejectedInitialization) continue;
            var children = settled.execution().children().stream().map(child -> durable.actions().stream()
                    .filter(value -> child.actionId().equals(value.command().actionId())).findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("settled Life control child is absent from canonical Driver actions"))).toList();
            if (rejectedInitialization)
                org.xar.ck3.control.application.advance.LifeAdvanceComposite.requireRejectedInitialization(parent.command(), settled.execution(), children);
            org.xar.ck3.control.application.action.ActionEffects.validateCompositeChildren(parent.command(), settled.execution(), settled.settlement(), children);
            if (cancelledInitialization) {
                StrictJson.require(!parent.visibleGameplay() && !parent.eligibleAdvance() && parent.applied().isEmpty(),
                        "cancelled Life initialization must not carry gameplay or advance credit");
                prefixControls.add(parent);
            }
            if (rejectedInitialization) {
                StrictJson.require(!parent.visibleGameplay() && !parent.eligibleAdvance() && parent.applied().isEmpty(),
                        "rejected Life initialization must not carry gameplay or advance credit");
                prefixControls.add(parent);
            }
            prefixControls.addAll(children);
        }
        for(ActionReceipt action:durable.actions()) {
            var presentation=verifiedPresentation.get();
            if(presentation!=null&&presentation.contains(action))continue;
            boolean gameplay=action.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay;
            boolean lifecycle=action.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.LifecycleTerminal;
            boolean operator=action.command().expectation() instanceof org.xar.ck3.control.application.action.CommandExpectation.OperatorRebind;
            if(!gameplay&&!lifecycle) {
                if(!action.settled())missing.add("unreconciled_frontend_action:"+action.command().actionId());
                continue;
            }
            boolean currentSave=activeActionId.filter(action.command().actionId()::equals).isPresent()
                    && action.state() instanceof ActionState.AckReceived
                    && "save-checkpoint".equals(action.command().operation().value()) && action.ack().filter(ack -> ack.nativeOk()).isPresent();
            if (!action.settled()) {
                boolean currentParent=allowedParent.filter(action.command()::equals).isPresent()
                        && activeActionId.filter(action.command().actionId()::equals).isPresent()
                        && (action.state() instanceof ActionState.IntentDurable || action.state() instanceof ActionState.Submitting
                            || action.state() instanceof ActionState.AckReceived || action.state() instanceof ActionState.CompositeRunning
                            ||action.state() instanceof ActionState.Unknown&&checkpoint.filter(value->value.context().before==known
                                    &&value.action().equals(action)).isPresent());
                boolean currentAncestor=actualAncestors.contains(action.command())
                        &&(action.state() instanceof ActionState.CompositeRunning
                            ||action.state() instanceof ActionState.CompositeUnknown&&qualifiedPendingChild(known,durable)
                                .filter(scope->scope.parent().equals(action.command())).isPresent());
                if (!currentSave && !currentParent && !currentAncestor) missing.add("unreconciled_action:"+action.command().actionId());
                continue;
            }
            if(operator) {
                var expected=((org.xar.ck3.control.application.action.CommandExpectation.OperatorRebind)action.command().expectation()).expected();
                expected.validateCommand(action.command());
                if(!action.command().origin().game().equals(known.stamp().game())||!expected.episodeRunId().equals(known.stamp().episodeRunId())
                        ||expected.episodeEpoch()!=known.stamp().episodeEpoch())continue;
                if(DriverOperatorNonRebindOriginals.isRecordedNonRebound(action))continue;
                if(!(action.state() instanceof ActionState.Settled settled)||!(settled.settlement() instanceof ActionState.OperatorRebound rebound)) {
                    missing.add("actual_operator_identity_settlement_unavailable:"+action.command().actionId());continue;
                }
                expected.validateCompletion(rebound.observation());
                // This typed canonical settlement retains the original operator evidence and its one identity CAS.
                // The actual canonical append/archive verifier validates that closed source; no Python recorder or second version exists.
                continue;
            }else if(gameplay) {
                if(!action.command().before().game().equals(known.stamp().game())||!action.command().before().frame().episodeRunId().equals(known.driver().session().episodeRunId()))continue;
            } else {
                var terminal=action.command().origin().requireLifecycleTerminal();
                if(!sameLifecycleSubject(terminal,known,false))continue;
                String operation=action.command().operation().value();
                if(java.util.Set.of("death-terminal","continue-as-reconciled-successor","start-next-episode").contains(operation)) {
                    ActionState.Settlement settlement=action.state() instanceof ActionState.CompositeSettled settled?settled.settlement():null;
                    if(!(settlement instanceof ActionState.LifecycleApplied applied)){missing.add("actual_lifecycle_settlement_unavailable:"+action.command().actionId());continue;}
                    applied.proof().validateParent(action.command());
                } else if(!operation.equals("continue-death-succession-modal-v1")){missing.add("unknown_terminal_history_operation:"+action.command().actionId());continue;}
            }
            if (action.state() instanceof ActionState.CompositeSettled settled
                    && settled.settlement() instanceof ActionState.CompositeNoGameplayWrite) {
                org.xar.ck3.control.application.action.ActionEffects.validateComposite(
                        action.command(), settled.execution(), settled.settlement());
                continue; // The verified no-write terminal has no Native command-history row or cycle credit.
            }
            if (action.state() instanceof ActionState.CompositeSettled settled
                    && settled.settlement() instanceof ActionState.LifeControlPrefixInterrupted) {
                continue; // The verified interrupted prefix has no Native command-history row or cycle credit.
            }
            DriverSnapshotFacts.ActionRow coverage=rows.get(action.command().actionId());
            if (coverage==null && prefixControls.contains(action)) continue; // Exact canonical child needs no second recorder row.
            if(coverage==null || !coverage.bodySha256().equals(action.bodySha256()) || coverage.durableSequence()>action.sequence()) {
                missing.add("original_history_row_unavailable:"+action.command().actionId()); continue;
            }
            if(coverage.coverageSource() instanceof DriverSnapshotFacts.CanonicalOnly) {
                if(coverage.durableSequence()!=action.sequence())missing.add("canonical_action_source_sequence_disagrees:"+action.command().actionId());
                continue;
            }
            OpportunityJson.Obj row=DriverJson.object(known.driver().commandHistory().get(Math.toIntExact(coverage.historyIndex()-1)).originalRow().json(),DriverJson.MAX_NATIVE_BYTES);
            boolean ok=OpportunityJson.bool(row.get("ok"),"history.ok");
            if(row.members().containsKey(DriverActionHistoryCodec.SOURCE_FIELD)&&coverage.durableSequence()!=action.sequence())
                missing.add("original_action_source_sequence_disagrees:"+action.command().actionId());
            boolean originalOk=row.members().containsKey(DriverActionHistoryCodec.SOURCE_FIELD)?DriverActionHistoryCodec.recordedOk(action,row)
                    :action.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED;
            if (!action.command().operation().value().equals(OpportunityJson.text(row.get("command"),"command"))
                    || ok!=originalOk) missing.add("original_history_result_disagrees:"+action.command().actionId());
        }
        for(var row:known.driver().commandHistory()) {
            OpportunityJson.Obj original=DriverJson.object(row.originalRow().json(),DriverJson.MAX_NATIVE_BYTES);
            OpportunityJson.text(original.get("command"),"command"); OpportunityJson.bool(original.get("ok"),"ok");
        }
        return missing.isEmpty() ? known.driver() : new DriverStateSnapshot.Incomplete(missing);
    }
    private static boolean sameLifecycleSubject(org.xar.ck3.control.application.action.LifecycleIdentity identity,DriverSnapshotFacts.Known known,boolean requireObserved) {
        var subject=identity.subject();
        if(!identity.game().equals(known.stamp().game())||!subject.characterId().equals(known.driver().session().actorId())
                ||!subject.episodeRunId().equals(known.stamp().episodeRunId())||subject.episodeEpoch()!=known.stamp().episodeEpoch()
                ||subject.driverVersion()>known.stamp().driverVersion())return false;
        if(known.observation().isEmpty())return !requireObserved;
        var actual=known.observation().orElseThrow().transport();return identity.machineId().equals(actual.machineId())&&identity.sessionId().equals(actual.sessionId())
                &&identity.connectionGeneration().equals(actual.connectionGeneration());
    }
    private static void validateCheckpoint(DriverStateSnapshot.Complete before,DriverStateSnapshot.Complete after,ActionReceipt action,DriverSnapshotFacts.Stamp stamp) {
        StrictJson.require("save-checkpoint".equals(action.command().operation().value())
                && action.command().before().game().equals(stamp.game()) && stamp.game().pid()==before.session().bridgePid()
                && action.command().before().frame().episodeRunId().equals(before.session().episodeRunId())
                && action.command().before().frame().identity().player().equals(before.session().actorId()),"checkpoint publication crossed actual action/episode");
        StrictJson.require(before.session().equals(after.session()) && after.commandHistory().size()==before.commandHistory().size()+1,"checkpoint appends exactly one full history row");
        for(int i=0;i<before.commandHistory().size();i++) StrictJson.require(Arrays.equals(before.commandHistory().get(i).originalRow().json(),after.commandHistory().get(i).originalRow().json()),"checkpoint rewrote existing history");
        StrictJson.require(after.rollbackWarFailure() instanceof DriverStateSnapshot.NullValue
                && after.rollbackWarFailures() instanceof DriverStateSnapshot.Value failures
                && DriverJson.object(wrap(failures.json()),DriverJson.MAX_NATIVE_BYTES).get("value").equals(new OpportunityJson.Arr(List.of())),
                "new SAVE anchor must reset the original rollback failure collection and singular projection");
        StrictJson.require(DriverJson.same(before.managedRestoreTransaction(),after.managedRestoreTransaction()) && DriverJson.same(before.successionExpectation(),after.successionExpectation())
                && DriverJson.same(before.successionLifecycle(),after.successionLifecycle()) && DriverJson.same(before.campaignGoal(),after.campaignGoal()),"checkpoint changed original business state");
        OpportunityJson.Obj row=DriverJson.object(after.commandHistory().getLast().originalRow().json(),DriverJson.MAX_NATIVE_BYTES);
        OpportunityJson.Obj checkpoint=OpportunityJson.object(OpportunityJson.object(row.get("result"),"result").get("checkpoint"),"checkpoint");
        StrictJson.require(OpportunityJson.bool(row.get("ok"),"ok") && "save-checkpoint".equals(OpportunityJson.text(row.get("command"),"command"))
                && action.command().actionId().equals(OpportunityJson.text(checkpoint.get("java_action_id"),"java_action_id"))
                && after.lastCheckpoint() instanceof DriverStateSnapshot.Value value
                && DriverJson.object(value.json(),DriverJson.MAX_NATIVE_BYTES).equals(checkpoint),"actual saved row and last checkpoint differ");
    }
    private static byte[] wrap(byte[] value) {
        byte[] prefix="{\"value\":".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        byte[] result=new byte[prefix.length+value.length+1]; System.arraycopy(prefix,0,result,0,prefix.length);
        System.arraycopy(value,0,result,prefix.length,value.length);result[result.length-1]='}';return result;
    }
}
