package org.xar.ck3.control.application.readiness;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.LifecycleExpectedPostcondition;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverTransportNoticeStability;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.OriginalTerminalPlanning;
import org.xar.ck3.control.application.planning.campaign.PublicTerminalDataContext;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Goal;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Real held-pipe collector. Concrete transport imports belong to native-transport, never application. */
public final class NativeReadinessCollector implements SessionPorts.ObservationPort, ReadinessAuthority {
    /** Historical source qualification is optional; ordinary runtime consumes the real received frame without it. */
    @FunctionalInterface public interface SourceAuthority {
        SourceQualification verify(ContinuityStorePort.Session borrowed, SessionIdentity identity, Complete frame,
                Known driver, NativeGameTransport.TransportDiagnostics received, GameLifecycle.Running process,
                Instant deadline) throws IOException;
    }
    /** Includes large source/EXE witnesses without weakening the writer's finite artifact-pin boundary. */
    @FunctionalInterface public interface SourceGuard {
        void assertCurrent(ContinuityStorePort.Session borrowed) throws IOException;
    }
    public record SourceQualification(Optional<ExactRef> proof, Optional<SourceGuard> guard) {
        public SourceQualification(ExactRef proof,SourceGuard guard) {this(Optional.of(proof),Optional.of(guard));}
        public SourceQualification {
            Objects.requireNonNull(proof); Objects.requireNonNull(guard);
            require(proof.isPresent()==guard.isPresent(),"historical proof and its guard must both be present or absent");
            proof.ifPresent(actual->require(actual.bytes()>0&&actual.bytes()<=ReadinessArchive.Role.SOURCE_PROOF.maximumBytes(),
                    "bounded historical source proof required"));
        }
        public static SourceQualification none(){return new SourceQualification(Optional.empty(),Optional.empty());}
        public void assertCurrent(ContinuityStorePort.Session borrowed)throws IOException {
            if(guard.isPresent())guard.orElseThrow().assertCurrent(borrowed);
        }
    }
    public record PlanningInputs(Set<OperationKey> actionSteps, Set<String> bridgeCapabilities,
            Optional<Obj> battleSpeedReadiness, List<ExternalFact> actionFacts, Optional<Goal> campaignGoal,
            Optional<Obj> crossRunPlan, boolean initialLifestyleFocusRequired, Optional<BatchRequest> offlineAnalysis,
            Optional<org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsReadValue.CoreAvailabilityInvalidation> armyCoreInvalidation) {
        public PlanningInputs {
            actionSteps = Set.copyOf(actionSteps); bridgeCapabilities = Set.copyOf(bridgeCapabilities); actionFacts = List.copyOf(actionFacts);
            Objects.requireNonNull(battleSpeedReadiness); Objects.requireNonNull(campaignGoal); Objects.requireNonNull(crossRunPlan);
            Objects.requireNonNull(offlineAnalysis);Objects.requireNonNull(armyCoreInvalidation);
        }
        public PlanningInputs(Set<OperationKey> actions,Set<String> capabilities,Optional<Obj> speed,List<ExternalFact> facts,
                Optional<Goal> goal,Optional<Obj> crossRun,boolean lifestyle,Optional<BatchRequest> offline) {
            this(actions,capabilities,speed,facts,goal,crossRun,lifestyle,offline,Optional.empty());
        }
        public Obj planningSnapshot(Complete frame,Known driver) {
            return armyCoreInvalidation.map(value->value.planningSnapshot(frame,driver)).orElse(frame.semantic());
        }
    }
    @FunctionalInterface public interface PlanningInputsPort {
        PlanningInputs collect(ContinuityStorePort.Session borrowed, Complete frame, Known driver,
                Obj receivedCapabilities, Instant deadline) throws IOException;
    }
    /** The same actual factory explicitly binds its read-only public inputs; an old ordinary lambda cannot substitute. */
    public interface PublicPlanningInputsPort extends PlanningInputsPort {
        PlanningInputs collectPublic(ContinuityStorePort.Session borrowed, Complete frame, Known driver,
                Obj receivedCapabilities, Instant deadline) throws IOException;
        OriginalTerminalPlanning.Input collectPublicTerminal(ContinuityStorePort.Session borrowed,
                DriverObservationAssembler.FullSnapshot frame, Known driver, Obj receivedCapabilities,
                Instant deadline) throws IOException;
    }
    @FunctionalInterface public interface ObservationSessionAuthority {
        /** Root installs the sole real writer's requireSession; this rejects another instance, thread or escaped session. */
        void require(ContinuityStorePort.Session borrowed) throws IOException;
    }
    @FunctionalInterface public interface ActiveObservationSession {
        /** The sole writer's activeSession getter; absence is not an escaped or foreign session. */
        Optional<ContinuityStorePort.Session> current() throws IOException;
    }
    @FunctionalInterface public interface PhysicalSemanticCapture {
        /** The one actual pure physical producer; it must skip capability hooks, planning inputs and publication. */
        SemanticEvidence capture(ContinuityStorePort.Session borrowed, SessionIdentity owner, Instant deadline) throws IOException;
    }
    /** Root verifies actual admitted Driver and episode provenance before returning its current actor. */
    @FunctionalInterface public interface AdmittedActorAuthority {
        BigInteger require(ContinuityStorePort.Session borrowed, SessionIdentity owner, Complete frame,
                Known actualDriver, Instant deadline) throws IOException;
    }
    /** Root's actual private NEXT stage/adoption admission; neither method can grant ordinary Ready or a planning lease. */
    public interface FirstCheckpointAdmission {
        void requireStage(ContinuityStorePort.Session borrowed, SessionIdentity owner, Instant deadline) throws IOException;
        BigInteger requirePhysical(ContinuityStorePort.Session borrowed, SessionIdentity owner, Complete actualFrame,
                Known actualDriver, SemanticEvidence actualSemantic, SourceQualification actualSource, Instant deadline) throws IOException;
    }
    @FunctionalInterface public interface LifecycleParentAuthority {
        /** Actual same-writer lifecycle service must replay the committed canonical episode and complete published Driver. */
        void require(ContinuityStorePort.Session borrowed, ActionReceipt actualParent) throws IOException;
    }
    /** Root binds the one real M7 producer; the exact newly constructed request is still inside the native/Driver/source scope. */
    @FunctionalInterface public interface ReadyPublication {
        void publish(ContinuityStorePort.Session borrowed, PlanningRequest request, Complete frame, Known driver,
                SourceQualification sources) throws IOException;
    }
    @FunctionalInterface public interface PlanningWork<T> {
        T apply(PlanningRequest original, LeaseSnapshot actualLease) throws IOException;
    }
    /** Root binds its existing physical-origin authority, which accepts an actual raw player/terminal frame. */
    @FunctionalInterface public interface PublicSourceAuthority {
        SourceQualification verify(ContinuityStorePort.Session borrowed, SessionIdentity owner,
                DriverObservationAssembler.FullSnapshot actual, Known driver,
                NativeGameTransport.TransportDiagnostics received, GameLifecycle.Running process,
                Instant deadline) throws IOException;
    }
    @FunctionalInterface public interface PublicPlanningWork<T> {
        T apply(PublicPlanningObservation actual) throws IOException;
    }
    /** Public DATA remains usable for nonready planning; only the Ready variant contains an original request. */
    public sealed interface PublicPlanningObservation permits PublicReady, PublicObserved {
        PublicPlanningFrame frame();
        default void assertCurrent(ContinuityStorePort.Session borrowed) throws IOException { frame().assertCurrent(borrowed); }
    }
    public static final class PublicReady implements PublicPlanningObservation {
        private final PublicPlanningFrame frame;
        private final SessionPorts.Ready ready;
        private final LeaseSnapshot lease;
        private PublicReady(PublicPlanningFrame frame, SessionPorts.Ready ready, LeaseSnapshot lease) {
            this.frame = frame; this.ready = ready; this.lease = lease;
        }
        @Override public PublicPlanningFrame frame() { return frame; }
        public SessionPorts.Ready ready() { return ready; }
        public LeaseSnapshot lease() { return lease; }
    }
    public static final class PublicObserved implements PublicPlanningObservation {
        private final PublicPlanningFrame frame;
        private final Optional<SessionPorts.Observation> observation;
        private PublicObserved(PublicPlanningFrame frame, Optional<SessionPorts.Observation> observation) {
            this.frame = frame; this.observation = observation;
            require(observation.stream().noneMatch(SessionPorts.Ready.class::isInstance), "observed DATA cannot contain Ready");
        }
        @Override public PublicPlanningFrame frame() { return frame; }
        /** Empty means that an incomplete native/player/canonical join could not enter the ordinary producer. */
        public Optional<SessionPorts.Observation> observation() { return observation; }
    }
    /** Its private construction and exact active callback distinguish authentic current DATA from copied records. */
    public static final class PublicPlanningFrame implements PublicTerminalDataContext {
        private final NativeReadinessCollector owner;
        private final DriverObservationAssembler.FullSnapshot snapshot;
        private final Known driver;
        private final DriverStateSnapshot canonicalDriver;
        private final List<ActionReceipt> actions;
        private final DriverObservationAssembler.Result joined;
        private final Optional<NativeReadiness.Assessment> assessment;
        private final Optional<Obj> receivedCapabilities;
        private final SourceQualification source;
        private final ExactRef hello, heartbeat, originalDriver;
        private final Optional<SemanticEvidence> semantic;
        private final Instant until;
        private PublicPlanningFrame(NativeReadinessCollector owner, DriverObservationAssembler.FullSnapshot snapshot,
                Known driver, DriverStateSnapshot canonicalDriver, List<ActionReceipt> actions,
                DriverObservationAssembler.Result joined, Optional<NativeReadiness.Assessment> assessment,
                Optional<Obj> receivedCapabilities, SourceQualification source, ExactRef hello,
                ExactRef heartbeat, ExactRef originalDriver, Optional<SemanticEvidence> semantic, Instant until) {
            this.owner = owner; this.snapshot = snapshot; this.driver = driver; this.canonicalDriver = canonicalDriver;
            this.actions = List.copyOf(actions); this.joined = joined; this.assessment = assessment;
            this.receivedCapabilities = receivedCapabilities; this.source = source; this.hello = hello;
            this.heartbeat = heartbeat; this.originalDriver = originalDriver; this.semantic = semantic; this.until = until;
        }
        public DriverObservationAssembler.FullSnapshot snapshot() { return snapshot; }
        public Known driver() { return driver; }
        public DriverStateSnapshot canonicalDriver() { return canonicalDriver; }
        public List<ActionReceipt> actions() { return actions; }
        public DriverObservationAssembler.Result joined() { return joined; }
        public Optional<NativeReadiness.Assessment> assessment() { return assessment; }
        public Optional<Obj> receivedCapabilities() { return receivedCapabilities; }
        public SourceQualification sourceQualification() { return source; }
        @Override public Optional<ExactRef> originalSourceProof() { return sourceQualification().proof(); }
        public ExactRef originalHello() { return hello; }
        public ExactRef originalHeartbeat() { return heartbeat; }
        public ExactRef originalDriver() { return originalDriver; }
        public Optional<SemanticEvidence> ordinarySemantic() { return semantic; }
        public Instant validUntil() { return until; }
        public void assertCurrent(ContinuityStorePort.Session borrowed) throws IOException { owner.assertPublicFrame(this, borrowed); }
        /** Uses the sole real input producer for Complete DATA without publishing Ready or M7. */
        public PlanningInputs collectInputs(ContinuityStorePort.Session borrowed, Instant deadline) throws IOException {
            assertCurrent(borrowed); Objects.requireNonNull(deadline);
            require(owner.clock.instant().isBefore(deadline), "public planning input deadline expired");
            require(joined instanceof Complete && receivedCapabilities.isPresent(),
                    "public ordinary inputs require a real Complete player join and received capabilities");
            Instant bounded = deadline.isBefore(until) ? deadline : until;
            PlanningInputs result;
            PlanningReadScope ordinary = owner.planningReadScope.get();
            if (ordinary != null) {
                require(ordinary.borrowed() == borrowed && ordinary.captured().lease().frame() == joined
                        && ordinary.captured().lease().driver() == driver
                        && semantic.filter(ordinary.captured().lease().semantic()::equals).isPresent(),
                        "public ordinary inputs crossed their exact original planning lease");
                result = owner.planningInputs.collect(borrowed, (Complete) joined, driver, receivedCapabilities.orElseThrow(), bounded);
            } else {
                require(semantic.isEmpty(), "ordinary public planning inputs escaped their actual original scope");
                require(owner.planningInputs instanceof PublicPlanningInputsPort, "actual read-only public planning input producer is not installed");
                PublicPlanningInputsPort actual = (PublicPlanningInputsPort) owner.planningInputs;
                result = actual.collectPublic(borrowed, (Complete) joined, driver, receivedCapabilities.orElseThrow(), bounded);
            }
            assertCurrent(borrowed); return result;
        }
        /** Raw full terminal DATA consumes the actual terminal inventory/goal/cross-run producer without Complete. */
        public OriginalTerminalPlanning.Input collectTerminalInputs(ContinuityStorePort.Session borrowed,
                Instant deadline) throws IOException {
            assertCurrent(borrowed); Objects.requireNonNull(deadline);
            require(owner.clock.instant().isBefore(deadline), "public terminal input deadline expired");
            require(owner.planningReadScope.get() == null && semantic.isEmpty(),
                    "public terminal inputs require their actual raw observation scope");
            require(receivedCapabilities.isPresent(), "actual received raw full terminal capabilities are unavailable");
            require(owner.planningInputs instanceof PublicPlanningInputsPort,
                    "actual read-only public terminal input producer is not installed");
            PublicPlanningInputsPort actual = (PublicPlanningInputsPort) owner.planningInputs;
            OriginalTerminalPlanning.Input result = Objects.requireNonNull(actual.collectPublicTerminal(borrowed,
                    snapshot, driver, receivedCapabilities.orElseThrow(), deadline.isBefore(until) ? deadline : until),
                    "actual terminal input producer returned no DATA");
            List<Obj> history = driver.driver().commandHistory().stream()
                    .map(row -> DriverJson.object(row.originalRow().json(), DriverJson.MAX_NATIVE_BYTES)).toList();
            require(result.snapshot().equals(snapshot.semantic()) && result.history().equals(history),
                    "public terminal input producer changed the actual full snapshot or complete history");
            assertCurrent(borrowed); return result;
        }
    }
    @FunctionalInterface public interface HeldReadWork<T> {
        T apply(Complete actualFrame) throws IOException;
    }
    @FunctionalInterface public interface PlanningEvidenceVerifier {
        /** Actual shared manifest/original reader, with only its explicitly versioned evidence-wrapper equivalence. */
        void requireEquivalent(ContinuityStorePort.Session borrowed, PlanningRequest original, LeaseSnapshot actualLease) throws IOException;
        /** Existing verifiers retain their strong contract; Root can compare the already-held planning DATA. */
        default void requireEquivalent(ContinuityStorePort.Session borrowed, PlanningRequest original, LeaseSnapshot actualLease,
                Set<String> nativeOwnedNoticeKeys) throws IOException {
            requireEquivalent(borrowed,original,actualLease);
        }
    }
    /** Pure current-frame projection only. This port must not call planning reads or their guards. */
    public record ExecutableCapabilities(Set<OperationKey> actionSteps, Set<String> bridgeCapabilities, Optional<Obj> battleSpeedReadiness) {
        public ExecutableCapabilities {
            actionSteps = Set.copyOf(actionSteps); bridgeCapabilities = Set.copyOf(bridgeCapabilities); Objects.requireNonNull(battleSpeedReadiness);
        }
    }
    @FunctionalInterface public interface CapabilitiesPort {
        ExecutableCapabilities collect(ContinuityStorePort.Session borrowed, Complete frame, Known driver,
                Obj receivedCapabilities, Instant deadline) throws IOException;
    }
    private record Captured(LeaseSnapshot lease, ExecutableCapabilities capabilities, NativeReadiness.Assessment assessment,
            SourceQualification source, Optional<Pin> sourceProof, String lockedHead, Instant deadline, PhysicalCapture physical) { }
    private record PlanningReadScope(ContinuityStorePort.Session borrowed, Captured captured) { }
    private static final class PlanningRoundScope {
        private final ContinuityStorePort.Session borrowed;
        private Captured captured;
        private org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame retainedPacket;
        private PlanningRoundScope(ContinuityStorePort.Session borrowed) { this.borrowed = borrowed; }
    }
    @FunctionalInterface public interface PlanningRoundWork<T> { T run() throws IOException, InterruptedException; }
    private record HeldReadScope(ContinuityStorePort.Session borrowed, PhysicalCapture captured,
            ReadinessAuthority.PhysicalReadLease lease,
            org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame original,
            boolean completeHistory, NativeReadiness.Assessment readiness) { }
    private record PhysicalCapture(Complete frame, Known driver, RootNativeCapabilities.Projection received,
            SemanticEvidence semantic, ExactRef hello, ExactRef heartbeat, SourceQualification source,
            Optional<Pin> sourceProof, String lockedHead, Instant deadline, Instant validUntil,
            org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame original,Set<String> nativeOwnedNoticeKeys) { }
    private record PublicScope(ContinuityStorePort.Session borrowed, PublicPlanningFrame frame, List<Pin> pins,
            String head, Instant deadline) { }
    private record PublicAttempt<T>(boolean ordinary, T result) { }
    private enum CaptureMode { ORDINARY, FIRST_CHECKPOINT, CURRENT }
    @FunctionalInterface private interface CaptureWork<T> { T run(Captured captured) throws IOException; }
    @FunctionalInterface private interface PhysicalWork<T> { T run(PhysicalCapture captured) throws IOException; }
    @FunctionalInterface private interface PublicFrameWork<T> { T run(PublicPlanningFrame actual) throws IOException; }
    private final SessionIdentity identity;
    private final ContinuityStorePort store;
    private final NativeGameTransport transport;
    private final DriverStateAssembler driver;
    private final DriverObservationAssembler assembler;
    private final GameLifecycle.Port lifecycle;
    private final ReadinessArchive archive;
    private final NativeSemanticEvidenceVerifier verifier;
    private final SourceAuthority sourceAuthority;
    private final CapabilitiesPort capabilities;
    private final PlanningInputsPort planningInputs;
    private final NativeReadiness.Policy policy;
    private final NativeReadiness.StableGate gate;
    private final Duration validity;
    private final Clock clock;
    private final ThreadLocal<PlanningReadScope> planningReadScope = new ThreadLocal<>();
    private final ThreadLocal<PlanningRoundScope> planningRoundScope = new ThreadLocal<>();
    private final ThreadLocal<HeldReadScope> heldReadScope = new ThreadLocal<>();
    private final ThreadLocal<ContinuityStorePort.Session> firstCheckpointScope = new ThreadLocal<>();
    private final ThreadLocal<PublicScope> publicPlanningScope = new ThreadLocal<>();
    private volatile ObservationSessionAuthority observationSession;
    private volatile LifecycleParentAuthority lifecycleParent;
    private volatile ActiveObservationSession activeObservationSession;
    private volatile PhysicalSemanticCapture physicalSemanticCapture;
    private volatile ReadyPublication readyPublication;
    private volatile PlanningEvidenceVerifier planningEvidence;
    private volatile AdmittedActorAuthority admittedActor;
    private volatile PublicSourceAuthority publicSourceAuthority;
    public NativeReadinessCollector(SessionIdentity identity, ContinuityStorePort store, NativeGameTransport transport,
            DriverStateAssembler driver, DriverObservationAssembler assembler, GameLifecycle.Port lifecycle,
            ReadinessArchive archive, NativeSemanticEvidenceVerifier verifier, SourceAuthority sourceAuthority,
            CapabilitiesPort capabilities, PlanningInputsPort planningInputs,
            NativeReadiness.Policy policy, Duration validity, Clock clock) {
        this.identity = Objects.requireNonNull(identity); this.store = Objects.requireNonNull(store);
        this.transport = Objects.requireNonNull(transport); this.driver = Objects.requireNonNull(driver);
        this.assembler = Objects.requireNonNull(assembler); this.lifecycle = Objects.requireNonNull(lifecycle);
        this.archive = Objects.requireNonNull(archive); this.verifier = Objects.requireNonNull(verifier);
        this.sourceAuthority = Objects.requireNonNull(sourceAuthority);
        this.capabilities = Objects.requireNonNull(capabilities);
        this.planningInputs = Objects.requireNonNull(planningInputs); this.policy = Objects.requireNonNull(policy);
        this.validity = Objects.requireNonNull(validity); this.clock = Objects.requireNonNull(clock);
        require(!validity.isNegative() && !validity.isZero() && validity.compareTo(Duration.ofMinutes(1)) <= 0,
                "explicit finite readiness freshness interval required");
        gate = new NativeReadiness.StableGate(policy);
    }
    public SessionIdentity identity() { return identity; }
    public synchronized void bindObservationSession(ObservationSessionAuthority actualWriter) {
        require(observationSession == null, "one actual original writer observation authority required");
        observationSession = Objects.requireNonNull(actualWriter);
    }
    public synchronized void bindPublicSourceAuthority(PublicSourceAuthority actualPhysicalOriginVerifier) {
        require(publicSourceAuthority == null, "one actual public physical-origin authority required");
        require(publicPlanningScope.get() == null, "public physical-origin authority cannot change in an observation");
        publicSourceAuthority = Objects.requireNonNull(actualPhysicalOriginVerifier);
    }
    public synchronized void bindActiveObservationSession(ActiveObservationSession actualWriter) {
        require(activeObservationSession == null, "one actual writer active-session getter required");
        activeObservationSession = Objects.requireNonNull(actualWriter);
    }
    public synchronized void bindPhysicalSemanticCapture(PhysicalSemanticCapture actualPureProducer) {
        require(physicalSemanticCapture == null, "one actual pure physical SEM producer required");
        physicalSemanticCapture = Objects.requireNonNull(actualPureProducer);
    }
    public synchronized void bindLifecycleParentAuthority(LifecycleParentAuthority actualCommittedEpisodeVerifier) {
        require(lifecycleParent == null, "one actual canonical lifecycle episode authority required");
        lifecycleParent = Objects.requireNonNull(actualCommittedEpisodeVerifier);
    }
    public synchronized void bindReadyPublication(ReadyPublication actualProducer) {
        require(readyPublication == null, "one actual exact-request Ready publication producer required");
        readyPublication = Objects.requireNonNull(actualProducer);
    }
    public synchronized void bindPlanningEvidence(PlanningEvidenceVerifier actualOriginalsVerifier) {
        require(planningEvidence == null, "one actual original-planning evidence verifier required");
        planningEvidence = Objects.requireNonNull(actualOriginalsVerifier);
    }
    public synchronized void bindAdmittedActorAuthority(AdmittedActorAuthority actualAdmittedDriver) {
        require(admittedActor == null, "one actual admitted Driver actor authority required");
        require(planningReadScope.get() == null && heldReadScope.get() == null && firstCheckpointScope.get() == null, "actor authority cannot change inside a frozen observation");
        admittedActor = Objects.requireNonNull(actualAdmittedDriver);
    }

    /** Rejoin after a real Root READ commit within this same original writer planning callback. */
    public boolean prepareReadPublicationReplan(ContinuityStorePort.Session borrowed) throws IOException {
        Objects.requireNonNull(borrowed);
        PlanningRoundScope round = planningRoundScope.get();
        if (round == null || round.captured == null) return false;
        require(round.borrowed == borrowed, "read-publication replan borrowed another actual writer");
        require(planningReadScope.get() == null && heldReadScope.get() == null && publicPlanningScope.get() == null,
                "read-publication replan must leave the original frozen scope");
        driver.requireOutsideObservationScope(borrowed);
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer observation authority is not installed"); actualWriter.require(borrowed);
        round.retainedPacket = round.captured.physical().original();
        round.captured = null;
        return true;
    }

    /** One real writer planning round retains its first Ready frame until policy reads finish. */
    public <T> T withPlanningRound(ContinuityStorePort.Session borrowed, PlanningRoundWork<T> work)
            throws IOException, InterruptedException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(work);
        require(planningRoundScope.get() == null && planningReadScope.get() == null, "one original planning round per thread required");
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual writer observation authority is not installed"); actualWriter.require(borrowed);
        require(identity.machineId().equals(borrowed.head().state().machineId()), "planning round belongs to another machine");
        planningRoundScope.set(new PlanningRoundScope(borrowed));
        try { return work.run(); } finally { planningRoundScope.remove(); }
    }
    private <T> T retainedPlanningRead(PlanningRoundScope round, ContinuityStorePort.Session borrowed,
            ObservationIdentity expected, Instant deadline, ReadinessAuthority.CheckedWork<T> work) throws IOException {
        require(round.borrowed == borrowed, "planning round cannot borrow another writer Session");
        Captured captured = Objects.requireNonNull(round.captured);
        require(lifecycle.inspect(identity.game(), deadline) instanceof GameLifecycle.Running, "actual planning Game is no longer Running");
        transport.acceptedSnapshotRevision(captured.physical().original()).requireOriginal(transport.currentSnapshot(deadline));
        return driver.withFrozenFacts(borrowed, frozen -> {
            require(frozen.state() instanceof Known, "planning round lost its actual frozen full Driver: kind");
            Known current = (Known) frozen.state();
            Known retained = captured.lease().driver();
            // Capability publication may update auxiliary under the sole owner CAS while this round keeps
            // its original captured frame. Every other Driver fact and unresolved action stays frozen.
            require(current.stamp().equals(retained.stamp()), "planning round lost its actual frozen full Driver: stamp");
            require(current.driver().equals(retained.driver()), "planning round lost its actual frozen full Driver: fullDriver");
            require(current.originalHistoryBasis().equals(retained.originalHistoryBasis()), "planning round lost its actual frozen full Driver: historyBasis");
            require(current.actionRows().equals(retained.actionRows()), "planning round lost its actual frozen full Driver: actionRows");
            require(current.loop().equals(retained.loop()), "planning round lost its actual frozen full Driver: loop");
            require(current.observation().equals(retained.observation()), "planning round lost its actual frozen full Driver: observation");
            require(DriverStateAssembler.projectObservation(captured.lease().driver(), frozen.actions(), frozen.activeActionId())
                    instanceof DriverStateSnapshot.Complete, "unresolved actions cannot reuse a planning lease");
            return inPlanningScope(borrowed, captured, same -> borrowedPlanningRead(planningReadScope.get(), borrowed, expected, deadline, work));
        });
    }

    @Override public SessionPorts.Observation observe(SessionIdentity expected, Instant deadline) throws IOException, InterruptedException {
        require(identity.equals(expected), "collector belongs to another owned session");
        try { return store.locked(borrowed -> observeBorrowed(borrowed, expected, deadline, deadline)); }
        catch (InterruptedIOException interrupted) { throw interrupted(interrupted); }
    }
    /** Borrows the caller's still-active original writer. The returned observation has left the frozen Driver scope. */
    public SessionPorts.Observation observe(ContinuityStorePort.Session borrowed, SessionIdentity expected,
            Instant deadline) throws IOException, InterruptedException {
        try { return observeBorrowed(borrowed, expected, deadline, deadline); }
        catch (InterruptedIOException interrupted) { throw interrupted(interrupted); }
    }
    public SessionPorts.Observation observe(ContinuityStorePort.Session borrowed, SessionIdentity expected,
            Instant readinessDeadline, Instant planningDeadline) throws IOException, InterruptedException {
        try { return observeBorrowed(borrowed, expected, readinessDeadline, planningDeadline); }
        catch (InterruptedIOException interrupted) { throw interrupted(interrupted); }
    }
    @Override public SessionPorts.Observation observe(SessionIdentity expected, Instant readinessDeadline, Instant planningDeadline) throws IOException, InterruptedException {
        require(identity.equals(expected), "collector belongs to another owned session");
        try { return store.locked(borrowed -> observeBorrowed(borrowed, expected, readinessDeadline, planningDeadline)); }
        catch (InterruptedIOException interrupted) { throw interrupted(interrupted); }
    }
    /** The two public entries share this one actual producer; it never opens another writer lock. */
    private SessionPorts.Observation observeBorrowed(ContinuityStorePort.Session borrowed, SessionIdentity expected,
            Instant readinessDeadline, Instant planningDeadline) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(expected); Objects.requireNonNull(readinessDeadline); Objects.requireNonNull(planningDeadline);
        require(identity.equals(expected), "collector belongs to another owned session");
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer observation authority is not installed");
        actualWriter.require(borrowed);
        require(identity.machineId().equals(borrowed.head().state().machineId()), "observation writer/source machine differs");
        require(planningReadScope.get() == null, "a frozen observation callback cannot recursively collect another observation");
        try {
            PlanningRoundScope round = planningRoundScope.get();
            require(round == null || round.borrowed == borrowed && round.captured == null,
                    "planning round already holds its original Ready observation");
            if (round != null && round.retainedPacket != null) {
                var original = round.retainedPacket; round.retainedPacket = null;
                return rejoinRetained(borrowed, original, planningDeadline, round);
            }
            return capture(borrowed, readinessDeadline, planningDeadline, captured -> inPlanningScope(borrowed, captured, sameCapture -> {
                SessionPorts.Observation result = createObservation(borrowed, sameCapture, planningDeadline);
                if (round != null && result instanceof SessionPorts.Ready) round.captured = sameCapture;
                return result;
            }));
        } catch (IllegalArgumentException | IllegalStateException failure) {
            gate.reset();
            ExactRef diagnostic = diagnostic(borrowed, failure);
            return new SessionPorts.ObservationUnavailable(reason(failure), diagnostic);
        }
    }

    /**
     * Rejoins a retained physical packet through the existing transport/driver producers.
     * This does not call transport.observe or freshFullState; it uses the original receiver occurrence.
     */
    private SessionPorts.Observation rejoinRetained(ContinuityStorePort.Session borrowed,
            org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame original,
            Instant deadline, PlanningRoundScope round) throws IOException {
        // A changed receiver occurrence uses the existing fresh capture; never swallow I/O or writer failures.
        var current = transport.currentSnapshot(deadline);
        if (current != original) return capture(borrowed, deadline, captured -> inPlanningScope(borrowed, captured, sameCapture -> {
            SessionPorts.Observation result = createObservation(borrowed, sameCapture, deadline);
            if (result instanceof SessionPorts.Ready) round.captured = sameCapture;
            return result;
        }));
        transport.acceptedSnapshotRevision(original).requireOriginal(current);

        // Use the existing driver.withFrozenObservation to join the original packet with current Driver facts
        return driver.withFrozenObservation(original, borrowed, frozen -> {
            require(frozen.projection() instanceof DriverStateSnapshot.Complete, "read-publication rejoin cannot reuse unresolved or incomplete Driver history");
            // Preserve the original packet reference for qualification
            ExactRef originalRef = preserve(borrowed, ReadinessArchive.Role.NATIVE_PACKET, original.originalPacket());

            // Qualify the physical capture using the existing producers
            return qualifyPhysical(borrowed, deadline, borrowed.head().digest(), original, frozen.state(), frozen.facts(), originalRef, physical -> {
                // Create the captured state from the physical qualification
                return fromPhysical(borrowed, deadline, physical, captured -> {
                    // Enter the planning scope and create the observation
                    return inPlanningScope(borrowed, captured, sameCapture -> {
                        SessionPorts.Observation result = createObservation(borrowed, sameCapture, deadline);
                        if (round != null && result instanceof SessionPorts.Ready) round.captured = sameCapture;
                        return result;
                    });
                });
            });
        });
    }
    /**
     * Root public actions obtain their actual request, M7 publication and domain preparation within one held
     * Native/Driver/source lease. Root flushes deferred READ publication after this scope exits, then decides
     * whether the command requires a new plan before dispatch. Failed readiness never calls the consumer.
     */
    public <T> T withOwnedPlanning(ContinuityStorePort.Session borrowed, SessionIdentity expected, Instant deadline,
            PlanningWork<T> work) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(expected); Objects.requireNonNull(deadline); Objects.requireNonNull(work);
        require(identity.equals(expected), "public planning belongs to another owned physical session");
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer observation authority is not installed");
        actualWriter.require(borrowed);
        require(identity.machineId().equals(borrowed.head().state().machineId()), "public planning writer/source machine differs");
        require(planningReadScope.get() == null, "public planning cannot recursively replace an active frozen observation");
        return capture(borrowed, deadline, captured -> inPlanningScope(borrowed, captured, sameCapture -> {
            SessionPorts.Observation observation = createObservation(borrowed, sameCapture, deadline);
            if (!(observation instanceof SessionPorts.Ready ready))
                throw new IOException("actual public planning readiness is unavailable: " + observation);
            return work.apply(ready.request(), sameCapture.lease());
        }));
    }

    /**
     * Public PLAN/EXECUTE context includes authentic running, terminal and unresolved frames. It uses only
     * the already received packet; nonready DATA never enters action admission or M7. Its consumer may
     * explicitly request the sole real planning inputs for an actual Complete join.
     */
    public <T> T withOwnedPublicPlanning(ContinuityStorePort.Session borrowed, SessionIdentity expected,
            Instant callerDeadline, PublicPlanningWork<T> work) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(expected); Objects.requireNonNull(callerDeadline); Objects.requireNonNull(work);
        require(identity.equals(expected), "public planning belongs to another owned physical session");
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer observation authority is not installed"); actualWriter.require(borrowed);
        require(identity.machineId().equals(borrowed.head().state().machineId()), "public planning writer/source machine differs");
        require(publicPlanningScope.get() == null && planningReadScope.get() == null && heldReadScope.get() == null
                && firstCheckpointScope.get() == null, "public planning cannot replace an active frozen observation");
        PublicSourceAuthority actualSources = publicSourceAuthority;
        require(actualSources != null, "actual public physical-origin authority is not installed");
        Instant deadline = callerDeadline;
        require(clock.instant().isBefore(deadline), "public planning deadline expired before held-frame lookup");
        String head = borrowed.head().digest();
        try { synchronized (transport) {
            var actual = transport.currentSnapshot(deadline);
            require(actual.session().machineId().equals(identity.machineId()) && actual.session().game().equals(identity.game())
                    && actual.session().sessionId().equals(identity.sessionId()), "public held Native crossed collector owner");
            ExactRef original = preserve(borrowed, ReadinessArchive.Role.NATIVE_PACKET, actual.originalPacket());
            PublicAttempt<T> attempt = driver.withFrozenRawObservation(actual, borrowed, frozen -> {
                var full = assembler.projectFull(actual, frozen.facts(), original);
                var joined = assembler.assemble(actual, frozen.facts(), original);
                var canonical = frozen.projection();
                GameLifecycle.Observation observed = lifecycle.inspect(identity.game(), deadline);
                require(observed instanceof GameLifecycle.Running running && running.measured().equals(identity.game()),
                        "public planning requires the actual independently measured Game");
                var received = transport.diagnostics();
                Instant until = requirePublicReceived(actual, received, deadline);
                SourceQualification source = Objects.requireNonNull(actualSources.verify(borrowed, identity, full,
                        frozen.state(), received, (GameLifecycle.Running) observed, deadline), "actual public source authority returned no qualification");
                source.assertCurrent(borrowed);
                ExactRef hello = preserve(borrowed, ReadinessArchive.Role.HELLO, received.originalHello().orElseThrow().original().packet().value());
                ExactRef heartbeat = preserve(borrowed, ReadinessArchive.Role.HEARTBEAT, received.latestHeartbeat().orElseThrow().original().packet().value());
                ExactRef originalDriver = preserve(borrowed, ReadinessArchive.Role.DRIVER, frozen.state().driver().encode());
                RootNativeCapabilities.Projection projection = RootNativeCapabilities.projectPublicFull(full, frozen.state(),
                        received, (GameLifecycle.Running) observed, clock.instant(), deadline, validity);
                Optional<Obj> receivedCapabilities = Optional.of(projection.capabilities());
                Optional<NativeReadiness.Assessment> assessment = Optional.empty();
                if (joined instanceof Complete complete) {
                    // Admitted actor verification remains in the original ordinary producer below.
                    assessment = Optional.of(NativeReadiness.assess(complete, projection.capabilities(),
                            policyFor(frozen.state().driver().session().actorId())));
                }
                var frame = new PublicPlanningFrame(this, full, frozen.state(), canonical, frozen.actions().actions(), joined,
                        assessment, receivedCapabilities, source, hello, heartbeat, originalDriver, Optional.empty(), until);
                List<Pin> pins = publicPins(borrowed, frame);
                return inPublicScope(borrowed, frame, pins, head, deadline, scoped -> {
                    if (canonical instanceof DriverStateSnapshot.Complete && assessmentReady(scoped.assessment()))
                        return new PublicAttempt<T>(true, null);
                    gate.reset();
                    return new PublicAttempt<T>(false, work.apply(new PublicObserved(scoped, Optional.empty())));
                });
            });
            if (!attempt.ordinary()) return attempt.result();
            // Raw observation cannot publish executable capabilities. Leave that scope before the actual
            // ordinary producer processes this same cached packet. There is no second Native observe.
            require(head.equals(borrowed.head().digest()), "writer changed between raw and ordinary public planning");
            return driver.withFrozenObservation(actual, borrowed, frozen -> {
                require(frozen.projection() instanceof DriverStateSnapshot.Complete,
                        "public ordinary planning lost its actual canonical history");
                return qualifyPhysical(borrowed, deadline, head, actual, frozen.state(), frozen.facts(), original,
                        physical -> fromPhysical(borrowed, deadline, physical, captured -> inPlanningScope(borrowed, captured, same -> {
                            SessionPorts.Observation observation = createObservation(borrowed, same, deadline);
                            var full = assembler.projectFull(actual, frozen.facts(), original);
                            var frame = new PublicPlanningFrame(this, full, frozen.state(), frozen.projection(), frozen.actions().actions(),
                                    physical.frame(), Optional.of(same.assessment()), Optional.of(same.lease().capabilities()), physical.source(),
                                    physical.hello(), physical.heartbeat(), physical.semantic().originalDriver(), Optional.of(physical.semantic()), physical.validUntil());
                            PublicPlanningObservation result = observation instanceof SessionPorts.Ready ready
                                    ? new PublicReady(frame, ready, same.lease()) : new PublicObserved(frame, Optional.of(observation));
                            return inPublicScope(borrowed, frame, publicPins(borrowed, frame), head, deadline, ignored -> work.apply(result));
                        })));
            });
        } } catch (IOException | RuntimeException failure) { gate.reset(); throw failure; }
    }
    private static boolean assessmentReady(Optional<NativeReadiness.Assessment> actual) {
        return actual.isPresent() && actual.orElseThrow().ready() && !actual.orElseThrow().terminal();
    }
    /** Actual framed HELLO/heartbeat and source checks apply even when no player identity can form Complete. */
    private Instant requirePublicReceived(org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame actual,
            NativeGameTransport.TransportDiagnostics received, Instant deadline) {
        require(received.receivedState() == NativeGameTransport.ReceivedState.HELLO_VERIFIED && received.terminalFailure().isEmpty()
                && received.session().filter(actual.session()::equals).isPresent(), "public actual held transport is unavailable");
        var hello = received.originalHello().orElseThrow(() -> new IllegalStateException("public actual original hello absent"));
        var heartbeat = received.latestHeartbeat().orElseThrow(() -> new IllegalStateException("public actual original heartbeat absent"));
        Instant now = clock.instant();
        require(now.isBefore(deadline) && !actual.observedAt().isAfter(now) && !actual.observedAt().isAfter(deadline)
                && !hello.observedAt().isAfter(actual.observedAt()) && !heartbeat.observedAt().isBefore(hello.observedAt())
                && !heartbeat.observedAt().isAfter(now) && !heartbeat.observedAt().isAfter(deadline), "public original snapshot or heartbeat is future/pre-hello or its caller deadline expired");
        Obj helloBody = RootNativeCapabilities.framedObject(hello.original().packet().value());
        Obj heartbeatBody = RootNativeCapabilities.framedObject(heartbeat.original().packet().value());
        require(new Text("hello").equals(helloBody.get("type")) && new Text("heartbeat").equals(heartbeatBody.get("type"))
                && BigInteger.ONE.equals(integer(helloBody.get("protocol_version"), "protocol_version"))
                && BigInteger.ONE.equals(integer(heartbeatBody.get("protocol_version"), "protocol_version")), "public original protocol-v1 notice required");
        require(heartbeat.original().kind() == NativeWire.NoticeKind.HEARTBEAT && hello.original().pid() == identity.game().pid()
                && hello.original().connectionGeneration().equals(actual.session().connectionGeneration())
                && integer(helloBody.get("pid"), "pid").equals(BigInteger.valueOf(identity.game().pid()))
                && integer(helloBody.get("connection_generation"), "connection_generation").equals(actual.session().connectionGeneration())
                && hello.original().capabilities().contains("game.state.snapshot") && bool(helloBody.get("ck3_build_match"), "ck3_build_match")
                && new Text("ready").equals(helloBody.get("game_adapter_status")), "public actual Game/generation/exact-build adapter differs");
        return deadline;
    }
    private List<Pin> publicPins(ContinuityStorePort.Session borrowed, PublicPlanningFrame frame) throws IOException {
        List<Pin> pins = new ArrayList<>();
        for (ExactRef ref : List.of(frame.snapshot().originalEvidence(), frame.snapshot().facts().semanticFactsEvidence(),
                frame.originalHello(), frame.originalHeartbeat(), frame.originalDriver())) {
            Pin pin = borrowed.capturePin(ref, org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
            require(pin.reference().equals(ref), "public original pin differs from its actual reference"); pins.add(pin);
        }
        sourcePin(borrowed,frame.sourceQualification()).ifPresent(pins::add);
        return List.copyOf(pins);
    }
    private <T> T inPublicScope(ContinuityStorePort.Session borrowed, PublicPlanningFrame frame, List<Pin> pins,
            String head, Instant deadline, PublicFrameWork<T> work) throws IOException {
        require(publicPlanningScope.get() == null, "public planning cannot replace an active original callback");
        PublicScope scope = new PublicScope(borrowed, frame, pins, head, deadline);
        publicPlanningScope.set(scope);
        try {
            frame.assertCurrent(borrowed);
            T result = work.run(frame);
            frame.assertCurrent(borrowed); return result;
        } finally { publicPlanningScope.remove(); }
    }
    private void assertPublicFrame(PublicPlanningFrame exact, ContinuityStorePort.Session borrowed) throws IOException {
        PublicScope active = publicPlanningScope.get();
        require(active != null && active.borrowed() == borrowed && active.frame() == exact,
                "public planning DATA escaped its original writer callback");
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer authority absent"); actualWriter.require(borrowed);
        require(clock.instant().isBefore(active.deadline()) && clock.instant().isBefore(exact.validUntil()),
                "public planning original freshness/deadline expired");
        require(active.head().equals(borrowed.head().digest()), "public planning changed its original writer head");
        exact.sourceQualification().assertCurrent(borrowed);
        for (Pin pin : active.pins()) borrowed.verifyPin(pin);
        var current = transport.currentSnapshot(active.deadline()); var original = exact.snapshot().actual();
        // Public DATA must retain its original received occurrence even if raw bytes and time repeat.
        transport.acceptedSnapshotRevision(original).requireOriginal(current);
        require(current.session().equals(original.session()) && current.snapshotId().equals(original.snapshotId())
                && current.nativeRevision().equals(original.nativeRevision()) && current.observedAt().equals(original.observedAt())
                && Arrays.equals(current.originalPacket(), original.originalPacket()), "public planning changed its actual held Native packet");
    }

    /** One scope covers the complete producer and its consumer; registered reads borrow this exact lease. */
    private <T> T inPlanningScope(ContinuityStorePort.Session borrowed, Captured captured, CaptureWork<T> work) throws IOException {
        require(planningReadScope.get() == null, "planning cannot replace another frozen observation scope");
        PlanningReadScope scope = new PlanningReadScope(borrowed, captured);
        planningReadScope.set(scope);
        try { return borrowedPlanningRead(scope, borrowed, captured.lease().frame().identity(), captured.deadline(),
                lease -> work.run(captured)); }
        finally { planningReadScope.remove(); }
    }

    /** Shared actual producer for ordinary auto observations and public actions. */
    private SessionPorts.Observation createObservation(ContinuityStorePort.Session borrowed, Captured captured,
            Instant deadline) throws IOException {
        PlanningReadScope scope = planningReadScope.get();
        require(scope != null && scope.borrowed() == borrowed && scope.captured() == captured,
                "actual planning request producer requires its original held scope");
        NativeReadiness.Assessment assessed = gate.observe(captured.assessment());
        if (!assessed.ready()) {
            if (assessed.status() == NativeReadiness.Status.WAITING)
                return new SessionPorts.Waiting(assessed.reason(), captured.lease().semantic().semantic());
            return new SessionPorts.ObservationUnavailable(assessed.reason(), captured.lease().semantic().semantic());
        }
        Complete frame = captured.lease().frame();
        PlanningInputs inputs = planningInputs.collect(borrowed, frame, captured.lease().driver(), captured.lease().capabilities(), deadline);
        require(inputs.actionSteps().equals(captured.capabilities().actionSteps())
                && inputs.bridgeCapabilities().equals(captured.capabilities().bridgeCapabilities())
                && inputs.battleSpeedReadiness().equals(captured.capabilities().battleSpeedReadiness()),
                "planning queries changed the fixed current executable-capability projection");
        List<Obj> history = captured.lease().driver().driver().commandHistory().stream()
                .map(row -> DriverJson.object(row.originalRow().json(), DriverJson.MAX_NATIVE_BYTES)).toList();
        Obj planningSnapshot=inputs.planningSnapshot(frame,captured.lease().driver());
        require(planningSnapshot.equals(frame.semantic()),"Core availability must refresh through the ordinary observation before Ready");
        PlanningObservation observations = new PlanningObservation(frame.semantic(), history, inputs.actionSteps(),
                inputs.bridgeCapabilities(), inputs.battleSpeedReadiness(), inputs.actionFacts(), inputs.campaignGoal(),
                inputs.crossRunPlan(), inputs.initialLifestyleFocusRequired());
        PlanningRequest request = new PlanningRequest(frame.identity(), frame.source(), frame.sessionId(), deadline, observations);
        ReadyPublication publication = readyPublication;
        require(publication != null, "actual same-request M7 Ready publication producer is not installed");
        captured.source().assertCurrent(borrowed); verifyOptionalPin(borrowed,captured.sourceProof());
        publication.publish(borrowed, request, frame, captured.lease().driver(), captured.source());
        captured.source().assertCurrent(borrowed); verifyOptionalPin(borrowed,captured.sourceProof());
        SessionPorts.CheckpointEligibility eligibility = checkpointEligibility(frame.semantic());
        return new SessionPorts.Ready(request, eligibility, inputs.offlineAnalysis(), Optional.of(captured.lease().semantic()));
    }

    private static InterruptedException interrupted(InterruptedIOException original) {
        Thread.currentThread().interrupt();
        InterruptedException result = new InterruptedException(original.getMessage()); result.initCause(original); return result;
    }

    /**
     * Pure consumers inside an immutable Driver/history scope must borrow an already active collector lease.
     * Absence is an explicit refusal before Native I/O; this method never captures or refreshes another frame.
     */
    public <T> T borrowCurrent(ContinuityStorePort.Session borrowed, ObservationIdentity expected, Instant deadline,
            ReadinessAuthority.CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(expected); Objects.requireNonNull(deadline); Objects.requireNonNull(work);
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer observation authority is not installed");
        actualWriter.require(borrowed);
        PlanningReadScope active = planningReadScope.get();
        require(active != null, "pure Driver/history consumer requires an already active actual collector lease");
        return borrowedPlanningRead(active, borrowed, expected, deadline, work);
    }

    /**
     * Borrows the actual ordinary lease during frozen action preparation. Empty means that no collector or
     * immutable Driver scope exists; every invalid active scope fails before a caller can choose fresh observation.
     */
    public <T> Optional<T> withActiveCurrent(ContinuityStorePort.Session borrowed, ObservationIdentity expected,
            Instant callerDeadline, ReadinessAuthority.CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(expected); Objects.requireNonNull(callerDeadline); Objects.requireNonNull(work);
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer observation authority is not installed");
        actualWriter.require(borrowed);
        require(identity.machineId().equals(borrowed.head().state().machineId())
                && identity.machineId().equals(expected.machineId()) && identity.game().equals(expected.game()),
                "active ordinary lease crossed its actual writer/physical owner");
        Instant deadline = callerDeadline;
        require(clock.instant().isBefore(deadline), "active ordinary lease caller deadline expired");
        require(firstCheckpointScope.get() == null && heldReadScope.get() == null,
                "physical-only read or first-checkpoint scope cannot supply an ordinary planning lease");
        PlanningReadScope active = planningReadScope.get();
        if (active != null) return Optional.of(borrowedPlanningRead(active, borrowed, expected, deadline,
                lease -> Objects.requireNonNull(work.apply(lease), "active ordinary lease mapper returned null")));
        driver.requireOutsideObservationScope(borrowed);
        return Optional.empty();
    }

    /** Typed ordinary read admission over the existing actual held lease; no recursive observation is available. */
    public <T> T currentHeldRead(ContinuityStorePort.Session borrowed, PlanningReadRequest original,
            ReadinessAuthority.CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(original); Objects.requireNonNull(work);
        require(original.origin() instanceof CommandOrigin.Gameplay, "held ordinary read cannot borrow another origin mode");
        return borrowCurrent(borrowed, original.before(), original.deadline(), lease -> {
            require(lease.frame().identity().equals(original.before()) && lease.frame().source().equals(original.source())
                    && lease.frame().sessionId().equals(original.sessionId()),
                    "held read changed its actual original frame/source/session");
            return work.apply(lease);
        });
    }

    /** The sole issuer joins received Native bytes to the existing frozen Driver; it never samples or publishes. */
    public <T> T withHeldReadScope(ContinuityStorePort.Session borrowed, SessionIdentity expected, Instant callerDeadline,
            HeldReadWork<T> work) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(expected); Objects.requireNonNull(callerDeadline); Objects.requireNonNull(work);
        require(identity.equals(expected), "held read belongs to another actual physical owner");
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer observation authority is not installed");
        actualWriter.require(borrowed);
        require(identity.machineId().equals(borrowed.head().state().machineId()), "held read writer/source machine differs");
        Instant deadline = callerDeadline;
        require(clock.instant().isBefore(deadline), "held read deadline expired before any held-frame lookup");
        require(firstCheckpointScope.get() == null, "first checkpoint cannot issue ordinary held reads");
        HeldReadScope active = heldReadScope.get();
        if (active != null) return borrowedHeldRead(active, borrowed, active.lease().frame().identity(), deadline,
                lease -> work.apply(lease.frame()));
        PlanningReadScope planning = planningReadScope.get();
        if (planning != null) return borrowedPlanningRead(planning, borrowed, planning.captured().lease().frame().identity(),
                deadline, lease -> {
                    // Retain the actual outer physical capture and frozen Driver, without another observation or READ.
                    PhysicalCapture physical=planning.captured().physical();
                    require(lease.frame()==physical.frame() && lease.driver()==physical.driver()
                            && lease.semantic().equals(physical.semantic()), "planning read lost its original physical capture");
                    var physicalLease=new ReadinessAuthority.PhysicalReadLease(lease.frame(),lease.driver(),lease.capabilities(),
                            lease.semantic(),lease.bridgeCapabilities(),lease.originalHello(),lease.originalHeartbeat(),
                            lease.validUntil(),lease.originalSourceQualification());
                    NativeReadiness.Assessment assessed=gate.observe(planning.captured().assessment());
                    var scope=new HeldReadScope(borrowed,physical,physicalLease,physical.original(),true,assessed);
                    require(heldReadScope.get()==null,"original planning read cannot replace an active physical source");
                    heldReadScope.set(scope);
                    try { return borrowedHeldRead(scope,borrowed,lease.frame().identity(),deadline,current -> work.apply(current.frame())); }
                    finally { heldReadScope.remove(); }
                });
        require(publicPlanningScope.get() == null, "raw public planning DATA cannot issue an ordinary held read");
        String head = borrowed.head().digest();
        var actual = transport.currentSnapshot(deadline);
        require(actual.session().machineId().equals(identity.machineId()) && actual.session().game().equals(identity.game())
                && actual.session().sessionId().equals(identity.sessionId()), "received held Native crossed collector owner");
        ExactRef original = preserve(borrowed, ReadinessArchive.Role.NATIVE_PACKET, actual.originalPacket());
        return driver.withFrozenFacts(borrowed, frozen -> {
            require(frozen.state() instanceof Known, "held read requires the actual complete Driver facts");
            Known known = (Known) frozen.state();
            boolean completeHistory = DriverStateAssembler.projectObservation(known, frozen.actions(), frozen.activeActionId()) instanceof DriverStateSnapshot.Complete;
            DriverObservationFacts facts = known.observation().orElseThrow(
                    () -> new IllegalStateException("held read has no actual same-version Driver observation"));
            return qualifyPhysical(borrowed, deadline, head, actual, known, facts, original, physical -> {
                NativeReadiness.Policy actualPolicy = policy;
                AdmittedActorAuthority admitted = admittedActor;
                if (admitted != null) actualPolicy = policyFor(Objects.requireNonNull(admitted.require(borrowed, identity,
                        physical.frame(), known, deadline), "actual admitted Driver returned no actor"));
                NativeReadiness.Assessment assessed = gate.observe(NativeReadiness.assess(physical.frame(), physical.received().capabilities(), actualPolicy));
                Set<String> advertised = Set.copyOf(transport.diagnostics().originalHello().orElseThrow().original().capabilities());
                var lease = new ReadinessAuthority.PhysicalReadLease(physical.frame(), known, physical.received().capabilities(),
                        physical.semantic(), advertised, physical.hello(), physical.heartbeat(), physical.validUntil(), physical.source().proof());
                // Unpaused/nonready data may explain a typed stale collection result; it cannot issue the read guard below.
                var scope = new HeldReadScope(borrowed, physical, lease, actual, completeHistory, assessed);
                require(heldReadScope.get() == null && planningReadScope.get() == null, "held scope cannot replace another observation");
                heldReadScope.set(scope);
                try { return borrowedHeldRead(scope, borrowed, lease.frame().identity(), deadline, current -> work.apply(current.frame())); }
                finally { heldReadScope.remove(); }
            });
        });
    }

    /**
     * Physical DATA for a separately authenticated canonical cleanup child. This never projects executable
     * actions or Ready: the Root guard must authenticate the exact reserved child and running-map pause itself.
     * A paused result must leave this scope before the caller uses the original ordinary guard path.
     */
    @Override public <T> T currentDerivedCleanup(ContinuityStorePort.Session borrowed, ObservationIdentity expected,
            Instant callerDeadline, ReadinessAuthority.PhysicalReadWork<T> work) throws IOException {
        Objects.requireNonNull(expected); Objects.requireNonNull(work); Objects.requireNonNull(callerDeadline);
        return withHeldReadScope(borrowed, identity, callerDeadline, frame -> {
            ObservationIdentity actual = frame.identity();
            require(expected.machineId().equals(actual.machineId()) && expected.game().equals(actual.game())
                    && expected.frame().episodeRunId().equals(actual.frame().episodeRunId())
                    && expected.frame().identity().player().equals(actual.frame().identity().player()),
                    "derived cleanup physical frame crossed actual Game/episode/actor");
            PlanningReadScope planning = planningReadScope.get();
            if (planning != null) return borrowedPlanningRead(planning, borrowed, actual, callerDeadline, lease ->
                    work.apply(new ReadinessAuthority.PhysicalReadLease(lease.frame(), lease.driver(), lease.capabilities(),
                            lease.semantic(), lease.bridgeCapabilities(), lease.originalHello(), lease.originalHeartbeat(),
                            lease.validUntil(), lease.originalSourceQualification())));
            HeldReadScope held = heldReadScope.get();
            require(held != null, "derived cleanup physical frame escaped its actual held scope");
            return borrowedHeldRead(held, borrowed, actual, callerDeadline, work);
        });
    }

    /** One real held source covers the registered read and both guards, including inside outer planning. */
    @Override public <T> T withOriginalReadSource(ContinuityStorePort.Session borrowed, PlanningReadRequest original,
            ReadinessAuthority.PhysicalReadWork<T> work) throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(work);
        require(original.origin() instanceof CommandOrigin.Gameplay,"original read source requires its actual gameplay origin");
        return withHeldReadScope(borrowed,identity,original.deadline(),frame -> currentHeldOriginal(borrowed,original,work));
    }

    /** Dedicated late-original admission never invokes the ordinary current/capture path. */
    @Override public <T> T currentHeldOriginal(ContinuityStorePort.Session borrowed, PlanningReadRequest original,
            ReadinessAuthority.PhysicalReadWork<T> work) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(original); Objects.requireNonNull(work);
        require(original.origin() instanceof CommandOrigin.Gameplay, "held original cannot borrow another origin");
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual writer observation authority is not installed"); actualWriter.require(borrowed);
        HeldReadScope active = heldReadScope.get();
        if (active == null && planningReadScope.get() != null)
            return withHeldReadScope(borrowed, identity, original.deadline(), frame -> currentHeldOriginal(borrowed, original, work));
        if (active == null && planningReadScope.get() == null) {
            PlanningRoundScope round = planningRoundScope.get();
            if (round != null && round.captured != null) {
                return retainedPlanningRead(round, borrowed, original.before(), original.deadline(),
                        lease -> currentHeldOriginal(borrowed, original, work));
            }
        }
        require(active != null, "original read requires an already active actual held scope; Native refresh is forbidden");
        require(active.completeHistory() && active.readiness().ready(),
                "actual held original-read admission is unavailable: " + active.readiness().reason());
        return borrowedHeldRead(active, borrowed, original.before(), original.deadline(), lease -> {
            requireReadOriginal(original, lease.frame()); return work.apply(lease);
        });
    }

    /** Complete is public data; only this exact object inside the actual held producer callback is admitted. */
    public void requireHeldFrame(ContinuityStorePort.Session borrowed, Complete exact) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(exact);
        PlanningReadScope planning = planningReadScope.get();
        if (planning != null) {
            borrowCurrent(borrowed, exact.identity(), planning.captured().deadline(), lease -> {
                require(lease.frame() == exact, "frame was not issued by this actual active planning scope"); return null;
            }); return;
        }
        HeldReadScope active = heldReadScope.get();
        require(active != null, "actual held frame escaped its owned scope");
        borrowedHeldRead(active, borrowed, exact.identity(), active.captured().deadline(), lease -> {
            require(lease.frame() == exact, "frame was not issued by this actual active held scope"); return null;
        });
    }
    private static void requireReadOriginal(PlanningReadRequest original, Complete frame) {
        require(frame.identity().equals(original.before()) && frame.source().equals(original.source())
                && frame.sessionId().equals(original.sessionId()), "held original changed its actual frame/source/session");
    }
    private <T> T borrowedHeldRead(HeldReadScope active, ContinuityStorePort.Session borrowed, ObservationIdentity expected,
            Instant deadline, ReadinessAuthority.PhysicalReadWork<T> work) throws IOException {
        require(active.borrowed() == borrowed && active.lease().frame().identity().equals(expected),
                "held read changed original writer or actual observation");
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual writer observation authority is not installed"); actualWriter.require(borrowed);
        assertHeldRead(active, deadline);
        T result = work.apply(active.lease());
        assertHeldRead(active, deadline);
        return result;
    }
    private void assertHeldRead(HeldReadScope active, Instant deadline) throws IOException {
        PhysicalCapture captured = active.captured();
        require(clock.instant().isBefore(deadline) && clock.instant().isBefore(captured.deadline())
                && clock.instant().isBefore(captured.validUntil()), "actual held read freshness/deadline expired");
        require(captured.lockedHead().equals(active.borrowed().head().digest()), "writer changed during held observation-only read");
        captured.source().assertCurrent(active.borrowed()); verifyOptionalPin(active.borrowed(),captured.sourceProof());
        var actual = transport.currentSnapshot(deadline);
        // Equal raw bytes and a fixed observed time cannot identify a received A/B/A occurrence.
        // The sole receiver must bind this current frame to the original physical capture as well.
        transport.acceptedSnapshotRevision(active.original()).requireOriginal(actual);
        require(actual.session().equals(active.original().session()) && actual.snapshotId().equals(active.original().snapshotId())
                && actual.nativeRevision().equals(active.original().nativeRevision()) && actual.observedAt().equals(active.original().observedAt())
                && Arrays.equals(actual.originalPacket(), active.original().originalPacket()), "actual held Native changed inside original-read scope");
    }

    /** Original action/read callers retain their deadline while borrowing the one actual source/SEM graph. */
    @Override public <T> T current(ContinuityStorePort.Session borrowed, ObservationIdentity expected, Instant callerDeadline,
            ReadinessAuthority.CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(expected); Objects.requireNonNull(work); Objects.requireNonNull(callerDeadline);
        Instant deadline = callerDeadline;
        require(clock.instant().isBefore(deadline), "caller readiness deadline expired before any native query");
        PlanningReadScope active = planningReadScope.get();
        if (active != null) return borrowedPlanningRead(active, borrowed, expected, deadline, work);
        PlanningRoundScope round = planningRoundScope.get();
        if (round != null && round.captured != null) return retainedPlanningRead(round, borrowed, expected, deadline, work);
        return captureCurrent(borrowed, deadline, captured -> {
            NativeReadiness.Assessment stable = gate.observe(captured.assessment());
            require(captured.assessment().ready(), "actual held frame does not pass native readiness: " + captured.assessment().reason());
            ObservationIdentity actual = captured.lease().frame().identity();
            require(expected.machineId().equals(actual.machineId()) && expected.game().equals(actual.game())
                    && expected.frame().episodeRunId().equals(actual.frame().episodeRunId())
                    && expected.frame().identity().player().equals(actual.frame().identity().player()),
                    "guard expected another actual held Game/episode/actor");
            require(!expected.equals(actual) || stable.ready(), "current frame has not passed the configured stability/pump gate: " + stable.reason());
            // Preserve the actual current revision for the coordinator's typed pre-dispatch mismatch result.
            // Rejecting it here would strand INTENT without the real zero-dispatch proof.
            require(planningReadScope.get() == null, "current read cannot replace another frozen observation scope");
            planningReadScope.set(new PlanningReadScope(borrowed, captured));
            try { return work.apply(captured.lease()); }
            finally { planningReadScope.remove(); }
        });
    }

    /**
     * Root public state/capability reads bind to the owned physical session and the current authoritative Driver.
     * A legal episode transition does not retain the bootstrap observation as an expected actor/episode.
     * The installed callback is observation-only; its registered query guards borrow this exact frozen lease.
     */
    public <T> T currentOwned(ContinuityStorePort.Session borrowed, SessionIdentity expected, Instant callerDeadline,
            ReadinessAuthority.CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(expected); Objects.requireNonNull(work); Objects.requireNonNull(callerDeadline);
        require(identity.equals(expected), "public read belongs to another owned physical session");
        Instant deadline = callerDeadline;
        require(clock.instant().isBefore(deadline), "caller readiness deadline expired before any native query");
        PlanningReadScope active = planningReadScope.get();
        if (active != null)
            return borrowedPlanningRead(active, borrowed, active.captured().lease().frame().identity(), deadline, work);
        PlanningRoundScope round = planningRoundScope.get();
        if (round != null && round.captured != null)
            return retainedPlanningRead(round, borrowed, round.captured.lease().frame().identity(), deadline, work);
        return capture(borrowed, deadline, captured -> {
            NativeReadiness.Assessment assessed = gate.observe(captured.assessment());
            require(assessed.ready(), "current owned session has not passed native readiness: " + assessed.reason());
            require(planningReadScope.get() == null, "public read cannot recursively replace a frozen observation");
            PlanningReadScope scope = new PlanningReadScope(borrowed, captured);
            planningReadScope.set(scope);
            try { return borrowedPlanningRead(scope, borrowed, captured.lease().frame().identity(), deadline, work); }
            finally { planningReadScope.remove(); }
        });
    }

    /**
     * Captures only actual post-lifecycle facts before any ordinary planning query can publish another Driver history row.
     * The real lifecycle authority, not a receipt constructor or this SEM, qualifies the committed published episode.
     * This is not an ordinary Ready assessment: the next full plan still passes the configured readiness/stability policy.
     */
    public SemanticEvidence semanticAfterLifecycle(ContinuityStorePort.Session borrowed, SessionIdentity owner,
            ActionReceipt actualParent, Instant deadline) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(owner); Objects.requireNonNull(actualParent); Objects.requireNonNull(deadline);
        require(identity.equals(owner), "post-lifecycle SEM belongs to another owned physical session");
        ObservationSessionAuthority originalWriter = observationSession;
        require(originalWriter != null, "actual original writer observation authority is not installed");
        originalWriter.require(borrowed);
        require(identity.machineId().equals(borrowed.head().state().machineId()), "post-lifecycle writer/source machine differs");
        require(planningReadScope.get() == null && heldReadScope.get() == null && firstCheckpointScope.get() == null,
                "post-lifecycle SEM cannot replace an active frozen read or first-checkpoint scope");
        ActionCommand command = actualParent.command();
        require(command.origin() instanceof CommandOrigin.LifecycleTerminal, "only an actual terminal lifecycle parent can request post-lifecycle SEM");
        var operation = command.lifecycleExpected().operation();
        require(operation == LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR
                || operation == LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,
                "death recording, modal Close and ordinary actions cannot acquire post-lifecycle episode SEM");
        require(actualParent.state() instanceof ActionState.CompositeSettled settled
                && settled.settlement() instanceof ActionState.LifecycleApplied,
                "post-lifecycle SEM requires a canonically settled typed lifecycle result; ACK or UNKNOWN is unavailable");
        var before = command.lifecycleBefore();
        require(before.machineId().equals(owner.machineId()) && before.game().equals(owner.game())
                && before.sessionId().equals(owner.sessionId()) && command.sessionId().equals(owner.sessionId()),
                "post-lifecycle parent crossed the actual physical owner");
        LifecycleParentAuthority committed = lifecycleParent;
        require(committed != null, "actual committed lifecycle episode/Driver verifier is not installed");
        require(clock.instant().isBefore(deadline), "post-lifecycle SEM deadline expired before any Native I/O");
        committed.require(borrowed, actualParent);
        PhysicalSemanticCapture physical = physicalSemanticCapture;
        require(physical != null, "actual pure physical SEM producer is not installed");
        SemanticEvidence semantic = physical.capture(borrowed, owner, deadline);
        verifier.verify(borrowed, owner, semantic);
        require(semantic.frame().machineId().equals(owner.machineId()) && semantic.frame().game().equals(owner.game()),
                "actual pure post-lifecycle SEM crossed the committed physical owner");
        // Capture has exited the Driver freeze. The published full Driver must still be the exact committed one.
        committed.require(borrowed, actualParent);
        require(clock.instant().isBefore(deadline), "post-lifecycle SEM qualification exhausted the caller deadline");
        return semantic;
    }

    /**
     * Revalidates the actual archived planning input against this one current physical lease.
     * It never fabricates fresh planning fields or recursively executes the planning-input factories.
     */
    public <T> T currentPlanning(ContinuityStorePort.Session borrowed, PlanningRequest original, ActionCommand command,
            Instant callerDeadline, PlanningWork<T> work) throws IOException {
        Objects.requireNonNull(original); Objects.requireNonNull(command); Objects.requireNonNull(callerDeadline); Objects.requireNonNull(work);
        require(command.origin() instanceof CommandOrigin.Gameplay && original.before().equals(command.before())
                && original.source().equals(command.source()) && original.sessionId().equals(command.sessionId()),
                "current planning validation needs the exact original ordinary request and command");
        Instant deadline = callerDeadline;
        if (command.deadline().isBefore(deadline)) deadline = command.deadline();
        return currentPlanning(borrowed, original, deadline, work);
    }
    /** Read-only completion validates its actual request without inventing an ActionCommand. */
    public <T> T currentPlanning(ContinuityStorePort.Session borrowed, PlanningRequest original, Instant callerDeadline,
            PlanningWork<T> work) throws IOException {
        Objects.requireNonNull(original); Objects.requireNonNull(callerDeadline); Objects.requireNonNull(work);
        Instant deadline = callerDeadline.isBefore(original.deadline()) ? callerDeadline : original.deadline();
        return current(borrowed, original.before(), deadline, lease -> {
            require(original.before().equals(lease.frame().identity()) && original.source().equals(lease.frame().source())
                    && original.sessionId().equals(lease.frame().sessionId()), "current planning origin/source/session drift requires a new ordinary plan");
            PlanningEvidenceVerifier verifier = planningEvidence;
            require(verifier != null, "actual complete planning manifest/original verifier is not installed");
            verifier.requireEquivalent(borrowed, original, lease, planningReadScope.get().captured().physical().nativeOwnedNoticeKeys());
            require(original.observations().actionSteps().equals(lease.executableSteps())
                    && original.observations().bridgeCapabilities().equals(lease.bridgeCapabilities()),
                    "actual executable planning projection changed; re-enter ordinary planning");
            return work.apply(original, lease);
        });
    }

    public Set<String> activeNativeOwnedNoticeKeys(ContinuityStorePort.Session borrowed, LeaseSnapshot expected) {
        PlanningReadScope active = planningReadScope.get();
        require(active != null, "no active planning read scope");
        require(active.borrowed() == borrowed, "borrowed session mismatch");
        require(active.captured().lease() == expected, "stale or foreign lease");
        return active.captured().physical().nativeOwnedNoticeKeys();
    }

    /** Registered reads borrow the actual outer planning/public observation and cannot replace frozen Driver facts. */
    private <T> T borrowedPlanningRead(PlanningReadScope active, ContinuityStorePort.Session borrowed,
            ObservationIdentity expected, Instant callerDeadline, ReadinessAuthority.CheckedWork<T> work) throws IOException {
        Captured captured = active.captured();
        try {
            require(active.borrowed() == borrowed, "planning read attempted another writer Session inside the frozen observation");
            require(captured.lease().frame().identity().equals(expected), "planning read must use the exact outer frozen observation origin");
            require(clock.instant().isBefore(captured.lease().validUntil()) && clock.instant().isBefore(captured.deadline()) && clock.instant().isBefore(callerDeadline),
                    "outer frozen observation/deadline expired during planning reads: checked_at=" + clock.instant() + ", lease_until=" + captured.lease().validUntil() + ", scope_deadline=" + captured.deadline() + ", caller_deadline=" + callerDeadline);
            require(captured.lockedHead().equals(borrowed.head().digest()), "writer changed before borrowed planning read");
            captured.source().assertCurrent(borrowed); verifyOptionalPin(borrowed,captured.sourceProof());
            T result = work.apply(captured.lease());
            captured.source().assertCurrent(borrowed); verifyOptionalPin(borrowed,captured.sourceProof());
            require(captured.lockedHead().equals(borrowed.head().digest()), "writer changed inside borrowed observation-only planning read");
            require(clock.instant().isBefore(captured.lease().validUntil()) && clock.instant().isBefore(captured.deadline()) && clock.instant().isBefore(callerDeadline),
                    "outer frozen observation/deadline expired before planning read publication: checked_at=" + clock.instant() + ", lease_until=" + captured.lease().validUntil() + ", scope_deadline=" + captured.deadline() + ", caller_deadline=" + callerDeadline);
            return result;
        } catch (IOException | RuntimeException failure) { gate.reset(); throw failure; }
    }

    /** Uses the same collector and the sole writer's current Session; a nested OS lock is never opened. */
    public CheckpointRequest.ObservationPort checkpoint(String lineageId) {
        org.xar.ck3.control.contracts.StrictJson.text(lineageId);
        return new CheckpointRequest.ObservationPort() {
            @Override public CheckpointRequest.Readiness observe(Instant deadline) throws InterruptedException {
                return collect(Optional.empty(), deadline);
            }
            @Override public CheckpointRequest.Readiness observeForPreparation(ObservationIdentity expected, Instant deadline)
                    throws InterruptedException {
                return collect(Optional.of(Objects.requireNonNull(expected)), deadline);
            }
            private CheckpointRequest.Readiness collect(Optional<ObservationIdentity> expected, Instant deadline)
                    throws InterruptedException {
                try {
                    ActiveObservationSession sessions = activeObservationSession;
                    require(sessions != null, "actual writer active-session getter is not installed");
                    Optional<ContinuityStorePort.Session> active = Objects.requireNonNull(sessions.current(),
                            "actual writer returned no active-session result");
                    if (active.isPresent()) return collectBorrowed(active.orElseThrow(), expected, deadline);
                    return store.locked(borrowed -> collectBorrowed(borrowed, expected, deadline));
                } catch (InterruptedIOException interrupted) {
                    Thread.currentThread().interrupt(); throw new InterruptedException(interrupted.getMessage());
                } catch (IOException failure) { throw new UncheckedIOException("actual checkpoint readiness unavailable", failure); }
            }
            private CheckpointRequest.Readiness collectBorrowed(ContinuityStorePort.Session borrowed,
                    Optional<ObservationIdentity> expected, Instant deadline) throws IOException {
                if (expected.isEmpty()) return checkpointBorrowed(borrowed, lineageId, deadline);
                return withHeldReadScope(borrowed, identity, deadline, frame -> {
                    HeldReadScope held = heldReadScope.get();
                    require(held != null && held.lease().frame() == frame && frame.identity().equals(expected.orElseThrow()),
                            "SAVE preparation changed its actual original received planning frame");
                    Obj semantic = frame.semantic();
                    boolean eligible = held.completeHistory() && held.readiness().ready()
                            && checkpointEligibility(semantic) == SessionPorts.CheckpointEligibility.SAFE;
                    return new CheckpointRequest.Readiness(frame.identity(), frame.source(), frame.sessionId(), lineageId,
                            bool(semantic.get("map_ready"), "map_ready"), bool(semantic.get("paused"), "paused"), eligible,
                            eligible ? "actual received planning frame and complete Driver are checkpoint eligible"
                                    : "actual original planning frame is not checkpoint eligible",
                            held.lease().semantic().originalNativePacket(), frame.observedAt());
                });
            }
        };
    }
    /**
     * Physical first-SAVE observations for Root's actual private NEXT stage. This port does not construct an
     * ordinary lease, collect domain capabilities, publish M7, or authorize gameplay/planning reads.
     * Root must supply the same port to the checkpoint request factory and service and recheck its private stage.
     */
    public CheckpointRequest.ObservationPort checkpointFirst(String lineageId, FirstCheckpointAdmission actual) {
        org.xar.ck3.control.contracts.StrictJson.text(lineageId); Objects.requireNonNull(actual);
        NativeReadiness.StableGate firstCheckpointGate = new NativeReadiness.StableGate(policy);
        return deadline -> {
            try {
                ActiveObservationSession sessions = activeObservationSession;
                require(sessions != null, "actual writer active-session getter is not installed");
                Optional<ContinuityStorePort.Session> active = Objects.requireNonNull(sessions.current(),
                        "actual writer returned no active-session result");
                if (active.isPresent()) return checkpointFirstBorrowed(active.orElseThrow(), lineageId, actual, firstCheckpointGate, deadline);
                return store.locked(borrowed -> checkpointFirstBorrowed(borrowed, lineageId, actual, firstCheckpointGate, deadline));
            } catch (InterruptedIOException interrupted) {
                firstCheckpointGate.reset();
                Thread.currentThread().interrupt(); throw new InterruptedException(interrupted.getMessage());
            } catch (IOException failure) {
                firstCheckpointGate.reset(); throw new UncheckedIOException("actual first-checkpoint physical readiness unavailable", failure);
            } catch (RuntimeException failure) { firstCheckpointGate.reset(); throw failure; }
        };
    }
    private CheckpointRequest.Readiness checkpointFirstBorrowed(ContinuityStorePort.Session borrowed, String lineageId,
            FirstCheckpointAdmission actual, NativeReadiness.StableGate firstCheckpointGate, Instant deadline) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(deadline);
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer observation authority is not installed");
        actualWriter.require(borrowed);
        require(identity.machineId().equals(borrowed.head().state().machineId()), "first-checkpoint writer/source machine differs");
        require(clock.instant().isBefore(deadline), "actual first-checkpoint deadline expired");
        require(planningReadScope.get() == null && firstCheckpointScope.get() == null,
                "first checkpoint cannot replace an active frozen observation");
        firstCheckpointScope.set(borrowed);
        try {
            actual.requireStage(borrowed, identity, deadline);
            return capturePhysical(borrowed, deadline, CaptureMode.FIRST_CHECKPOINT, captured -> {
                BigInteger actor = Objects.requireNonNull(actual.requirePhysical(borrowed, identity, captured.frame(),
                        captured.driver(), captured.semantic(), captured.source(), deadline), "actual first-checkpoint admission returned no actor");
                NativeReadiness.Assessment assessed = firstCheckpointGate.observe(NativeReadiness.assess(captured.frame(),
                        captured.received().capabilities(), policyFor(actor)));
                Obj semantic = captured.frame().semantic();
                boolean eligible = assessed.ready() && checkpointEligibility(semantic) == SessionPorts.CheckpointEligibility.SAFE;
                actual.requireStage(borrowed, identity, deadline);
                return new CheckpointRequest.Readiness(captured.frame().identity(), captured.frame().source(),
                        captured.frame().sessionId(), lineageId, bool(semantic.get("map_ready"), "map_ready"),
                        bool(semantic.get("paused"), "paused"), eligible,
                        eligible ? "actual admitted NEXT-stage physical first-checkpoint observation is eligible"
                                : assessed.ready() ? "foreground or terminal state blocks first SAVE" : assessed.reason(),
                        captured.semantic().originalNativePacket(), captured.frame().observedAt());
            });
        } catch (IOException | RuntimeException failure) { firstCheckpointGate.reset(); throw failure; }
        finally { firstCheckpointScope.remove(); }
    }
    private CheckpointRequest.Readiness checkpointBorrowed(ContinuityStorePort.Session borrowed, String lineageId,
            Instant deadline) throws IOException {
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer observation authority is not installed");
        actualWriter.require(borrowed);
        require(planningReadScope.get() == null, "checkpoint cannot replace an active frozen planning observation");
        return capture(borrowed, deadline, captured -> {
            Complete frame = captured.lease().frame(); Obj semantic = frame.semantic();
            NativeReadiness.Assessment assessed = gate.observe(captured.assessment());
            boolean eligible = assessed.ready() && checkpointEligibility(semantic) == SessionPorts.CheckpointEligibility.SAFE;
            return new CheckpointRequest.Readiness(frame.identity(), frame.source(), frame.sessionId(), lineageId,
                    bool(semantic.get("map_ready"), "map_ready"), bool(semantic.get("paused"), "paused"), eligible,
                    eligible ? "actual same-lock native and complete Driver are checkpoint eligible"
                            : assessed.ready() ? "foreground or terminal state blocks SAVE" : assessed.reason(),
                    captured.lease().semantic().originalNativePacket(), frame.observedAt());
        });
    }

    private <T> T capture(ContinuityStorePort.Session borrowed, Instant deadline, CaptureWork<T> work) throws IOException {
        return capture(borrowed, deadline, deadline, work);
    }
    private <T> T captureCurrent(ContinuityStorePort.Session borrowed, Instant deadline, CaptureWork<T> work) throws IOException {
        try { return capturePhysical(borrowed, deadline, deadline, CaptureMode.CURRENT, physical -> fromPhysical(borrowed, deadline, physical, work)); }
        catch (IOException | RuntimeException failure) { gate.reset(); throw failure; }
    }
    private <T> T capture(ContinuityStorePort.Session borrowed, Instant ioDeadline, Instant scopeDeadline, CaptureWork<T> work) throws IOException {
        try { return captureActual(borrowed, ioDeadline, scopeDeadline, work); }
        catch (IOException | RuntimeException failure) { gate.reset(); throw failure; }
    }
    private <T> T captureActual(ContinuityStorePort.Session borrowed, Instant ioDeadline, Instant scopeDeadline, CaptureWork<T> work) throws IOException {
        return capturePhysical(borrowed, ioDeadline, scopeDeadline, CaptureMode.ORDINARY, physical -> fromPhysical(borrowed, scopeDeadline, physical, work));
    }
    private <T> T fromPhysical(ContinuityStorePort.Session borrowed, Instant deadline, PhysicalCapture physical,
            CaptureWork<T> work) throws IOException {
            NativeReadiness.Policy actualPolicy = policy;
            AdmittedActorAuthority actorAuthority = admittedActor;
            if (actorAuthority != null) actualPolicy = policyFor(Objects.requireNonNull(actorAuthority.require(borrowed,
                    identity, physical.frame(), physical.driver(), deadline), "actual admitted Driver authority returned no actor"));
            NativeReadiness.Assessment assessment = NativeReadiness.assess(physical.frame(), physical.received().capabilities(), actualPolicy);
            ExecutableCapabilities installed = capabilities.collect(borrowed, physical.frame(), physical.driver(), physical.received().capabilities(), deadline);
            Map<String, Value> advertised = new LinkedHashMap<>(physical.received().capabilities().members());
            advertised.put("action_steps", new Arr(installed.actionSteps().stream().map(OperationKey::value).sorted().map(value -> (Value) new Text(value)).toList()));
            advertised.put("bridge_capabilities", new Arr(installed.bridgeCapabilities().stream().sorted().map(value -> (Value) new Text(value)).toList()));
            LeaseSnapshot lease = new LeaseSnapshot(physical.frame(), physical.driver(), new Obj(advertised), physical.semantic(),
                    installed.actionSteps(), installed.bridgeCapabilities(), physical.hello(), physical.heartbeat(), physical.validUntil(), physical.source().proof());
            return work.run(new Captured(lease, installed, assessment, physical.source(), physical.sourceProof(), physical.lockedHead(), deadline, physical));
    }
    private NativeReadiness.Policy policyFor(BigInteger actualActor) {
        return new NativeReadiness.Policy(policy.coldCheckpoint(), policy.allowTerminal(), Optional.of(actualActor),
                policy.stableFor(), policy.requirePostReadyPump());
    }
    private <T> T capturePhysical(ContinuityStorePort.Session borrowed, Instant deadline, CaptureMode mode,
            PhysicalWork<T> work) throws IOException {
        return capturePhysical(borrowed,deadline,deadline,mode,work);
    }
    private <T> T capturePhysical(ContinuityStorePort.Session borrowed, Instant ioDeadline, Instant scopeDeadline, CaptureMode mode,
            PhysicalWork<T> work) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(ioDeadline); Objects.requireNonNull(scopeDeadline); Objects.requireNonNull(work);
        ObservationSessionAuthority actualWriter = observationSession;
        require(actualWriter != null, "actual original writer observation authority is not installed");
        actualWriter.require(borrowed);
        require(identity.machineId().equals(borrowed.head().state().machineId()), "actual readiness writer/source machine differs");
        require(mode == CaptureMode.FIRST_CHECKPOINT ? firstCheckpointScope.get() == borrowed : firstCheckpointScope.get() == null,
                "first-checkpoint physical admission cannot recursively capture another observation");
        require(planningReadScope.get() == null && heldReadScope.get() == null && publicPlanningScope.get() == null,
                "a frozen read observation cannot capture another native sample");
        require(clock.instant().isBefore(ioDeadline), "actual readiness deadline expired");
        String lockedHead = borrowed.head().digest();
        org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame actual;
        try {
            if (mode == CaptureMode.CURRENT) {
                actual = transport.currentSnapshot(ioDeadline);
            } else {
                actual = transport.observe(ioDeadline, validity);
            }
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt(); InterruptedIOException failure = new InterruptedIOException("native readiness interrupted"); failure.initCause(interrupted); throw failure;
        } catch (UncheckedIOException failure) { throw org.xar.ck3.control.application.planning.PlanningReadFailure.physical(failure); }
        require(actual.session().machineId().equals(identity.machineId()) && actual.session().game().equals(identity.game())
                && actual.session().sessionId().equals(identity.sessionId()), "actual held Native crossed collector session");
        ExactRef original = preserve(borrowed, ReadinessArchive.Role.NATIVE_PACKET, actual.originalPacket());
        DriverStateAssembler.ObservationWork<T> join = frozen -> {
            if (mode != CaptureMode.FIRST_CHECKPOINT)
                require(frozen.projection() instanceof DriverStateSnapshot.Complete, "complete canonical history/Driver is not available; unresolved actions cannot become ready");
            return qualifyPhysical(borrowed, ioDeadline, scopeDeadline, lockedHead, actual, frozen.state(), frozen.facts(), original, work);
        };
        return mode == CaptureMode.FIRST_CHECKPOINT ? driver.withFrozenRawObservation(actual, borrowed, join)
                : driver.withFrozenObservation(actual, borrowed, join);
    }
    /** One shared source/physical/SEM qualification producer for fresh and already received snapshots. */
    private <T> T qualifyPhysical(ContinuityStorePort.Session borrowed, Instant deadline, String lockedHead,
            org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame actual, Known known,
            DriverObservationFacts facts, ExactRef original, PhysicalWork<T> work) throws IOException {
        return qualifyPhysical(borrowed,deadline,deadline,lockedHead,actual,known,facts,original,work);
    }
    private <T> T qualifyPhysical(ContinuityStorePort.Session borrowed, Instant ioDeadline, Instant scopeDeadline, String lockedHead,
            org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame actual, Known known,
            DriverObservationFacts facts, ExactRef original, PhysicalWork<T> work) throws IOException {
        require(known.stamp().driverVersion() == facts.driverVersion() && known.stamp().episodeEpoch() == facts.episodeEpoch()
                && Arrays.equals(known.driver().encode(), facts.driver().encode()), "physical originals crossed the actual frozen full Driver version");
        DriverObservationAssembler.Result assembled = assembler.assemble(actual, facts, original);
        require(assembled instanceof Complete, "actual native/Driver observation join is incomplete: " + assembled);
        Complete frame = (Complete) assembled;
        Instant now = clock.instant();
        require(now.isBefore(ioDeadline) && !frame.observedAt().isAfter(now) && !frame.observedAt().isAfter(ioDeadline), "actual native observation freshness/deadline failed: observed_at=" + frame.observedAt() + ", checked_at=" + now + ", deadline=" + ioDeadline);
        GameLifecycle.Observation observed = lifecycle.inspect(identity.game(), ioDeadline);
        require(observed instanceof GameLifecycle.Running, "actual Game is not independently measured Running");
        NativeGameTransport.TransportDiagnostics diagnostics = transport.diagnostics();
        RootNativeCapabilities.Projection received = RootNativeCapabilities.project(frame, known, diagnostics,
                (GameLifecycle.Running) observed, now, ioDeadline, validity);
        SourceQualification qualified = Objects.requireNonNull(sourceAuthority.verify(borrowed, identity, frame,
                known, diagnostics, (GameLifecycle.Running) observed, ioDeadline), "actual source authority returned no qualification");
        qualified.assertCurrent(borrowed);
        Optional<Pin> sourceProof = sourcePin(borrowed,qualified);
        Instant sourceCheckedAt = clock.instant();
        byte[] semanticBytes = DriverJson.encode(frame.semantic()); byte[] driverBytes = known.driver().encode();
        ExactRef semantic = preserve(borrowed, ReadinessArchive.Role.SEMANTIC, semanticBytes);
        ExactRef fullDriver = preserve(borrowed, ReadinessArchive.Role.DRIVER, driverBytes);
        ExactRef stamp = preserve(borrowed, ReadinessArchive.Role.DRIVER_STAMP, NativeDriverStamp.encode(frame, known));
        Instant originalsPreservedAt = clock.instant();
        SemanticEvidence evidence = new SemanticEvidence(frame.identity(), semantic, original, stamp, fullDriver, frame.observedAt());
        verifier.verify(borrowed, identity, evidence);
        Instant semanticVerifiedAt = clock.instant();
        ExactRef hello = preserve(borrowed, ReadinessArchive.Role.HELLO, diagnostics.originalHello().orElseThrow().original().packet().value());
        ExactRef heartbeat = preserve(borrowed, ReadinessArchive.Role.HEARTBEAT, diagnostics.latestHeartbeat().orElseThrow().original().packet().value());
        // The unchanged packet remains inside this writer callback; cache age is not its operation budget.
        Instant validUntil = scopeDeadline;
        require(lockedHead.equals(borrowed.head().digest()), "writer changed before readiness publication");
        Instant checkedAt = clock.instant();
        require(checkedAt.isBefore(validUntil) && checkedAt.isBefore(scopeDeadline), "readiness/source verification exhausted its actual freshness window: observed_at=" + frame.observedAt() + ", joined_at=" + now + ", source_done=" + sourceCheckedAt + ", originals_preserved_at=" + originalsPreservedAt + ", semantic_verified_at=" + semanticVerifiedAt + ", checked_at=" + checkedAt + ", valid_until=" + validUntil + ", deadline=" + scopeDeadline + ", qualified.proof().isPresent()=" + qualified.proof().isPresent());
        qualified.assertCurrent(borrowed); verifyOptionalPin(borrowed,sourceProof);
        T result = work.run(new PhysicalCapture(frame, known, received, evidence, hello, heartbeat, qualified, sourceProof,
                lockedHead, scopeDeadline, validUntil, actual, DriverTransportNoticeStability.nativeOwnedNoticeKeys(
                        DriverJson.object(actual.state().bytes(),DriverJson.MAX_NATIVE_BYTES))));
        qualified.assertCurrent(borrowed); verifyOptionalPin(borrowed,sourceProof);
        Instant publishedAt = clock.instant();
        require(publishedAt.isBefore(validUntil) && publishedAt.isBefore(scopeDeadline), "readiness publication crossed its actual freshness/deadline: observed_at=" + frame.observedAt() + ", joined_at=" + now + ", source_done=" + sourceCheckedAt + ", originals_preserved_at=" + originalsPreservedAt + ", semantic_verified_at=" + semanticVerifiedAt + ", checked_at=" + publishedAt + ", valid_until=" + validUntil + ", deadline=" + scopeDeadline + ", qualified.proof().isPresent()=" + qualified.proof().isPresent());
        require(lockedHead.equals(borrowed.head().digest()), "writer changed inside observation-only readiness scope");
        return result;
    }
    private static Optional<Pin> sourcePin(ContinuityStorePort.Session borrowed,SourceQualification source)throws IOException {
        if(source.proof().isEmpty())return Optional.empty();
        ExactRef proof=source.proof().orElseThrow();
        Pin pin=borrowed.capturePin(proof,ReadinessArchive.Role.SOURCE_PROOF.maximumBytes());
        require(pin.reference().equals(proof),"historical source proof pin differs from its original");
        borrowed.verifyPin(pin);return Optional.of(pin);
    }
    private static void verifyOptionalPin(ContinuityStorePort.Session borrowed,Optional<Pin> pin)throws IOException {
        if(pin.isPresent())borrowed.verifyPin(pin.orElseThrow());
    }
    private ExactRef preserve(ContinuityStorePort.Session borrowed, ReadinessArchive.Role role, byte[] bytes) throws IOException {
        require(bytes.length > 0 && bytes.length <= role.maximumBytes(), "actual readiness material exceeds its role boundary");
        ExactRef retained = archive.preserve(borrowed, role, bytes);
        require(retained.bytes() == bytes.length && retained.sha256().equals(DriverJson.sha256(bytes)), "actual archive receipt differs from readiness bytes");
        return retained;
    }
    private ExactRef diagnostic(ContinuityStorePort.Session borrowed, RuntimeException failure) throws IOException {
        return preserve(borrowed, ReadinessArchive.Role.DIAGNOSTIC, DriverJson.encode(new Obj(Map.of(
                "machine_id", new Text(identity.machineId()), "session_id", new Text(identity.sessionId()),
                "observed_at", new Text(clock.instant().toString()), "reason", new Text(reason(failure))))));
    }
    public static SessionPorts.CheckpointEligibility checkpointEligibility(Obj semantic) {
        if (bool(semantic.get("one_life_terminal"), "one_life_terminal") || semantic.get("one_life_terminal_reason") instanceof Text)
            return SessionPorts.CheckpointEligibility.TERMINAL_PENDING;
        if (present(semantic.get("active_event")) || present(semantic.get("pending_character_interaction")))
            return SessionPorts.CheckpointEligibility.MODAL_PENDING;
        Value hint = semantic.get("top_exclusive_modal_choice_hint");
        if (hint instanceof Obj modal && new Text("present").equals(modal.get("status"))) return SessionPorts.CheckpointEligibility.MODAL_PENDING;
        return SessionPorts.CheckpointEligibility.SAFE;
    }
    private static boolean present(Value value) { return value != null && value != Nil.INSTANCE; }
    private static String reason(RuntimeException failure) {
        String value = failure.getClass().getSimpleName() + ": " + Objects.toString(failure.getMessage(), "actual readiness input unavailable");
        return value.length() <= 4096 ? value : value.substring(0, 4096);
    }
}

