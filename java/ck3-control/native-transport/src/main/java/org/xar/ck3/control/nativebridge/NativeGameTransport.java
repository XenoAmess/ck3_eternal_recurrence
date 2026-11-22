package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.time.Clock;
import java.time.Duration;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.HashMap;
import java.util.Map;
import java.util.LinkedHashMap;
import java.lang.ref.WeakReference;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.FlorinUnitFullId;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiRootIndexFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiRootIndexFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiControlsFrameV2;
import org.xar.ck3.control.nativebridge.capabilities.registry.DateAdvanceFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.DateAdvanceFrameV1PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiControlsFrameV2PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PersonalGoldFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.PersonalGoldFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.ActorFoundationFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.ActorFoundationFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.ActorResourceLeafV2;
import org.xar.ck3.control.contracts.semantic.NativeSemanticFingerprint;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.application.action.PhysicalStatusIdentity;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.FullSnapshotEventOptionControl;
import org.xar.ck3.control.application.action.FullSnapshotGuiControl;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.action.FullSnapshotDateSentinelArm;
import org.xar.ck3.control.application.advance.PreparedCleanupEvidence;
import org.xar.ck3.control.application.action.PreparedCleanupPermit;
import org.xar.ck3.control.application.action.PreparedCleanupObservationPermit;
import org.xar.ck3.control.application.action.PreparedCleanupNativeOutcome;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.PlanningReadFailure;
import org.xar.ck3.control.application.action.PlanningReadFailureCodec;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.council.CouncilContinuationCoordinator;
import org.xar.ck3.control.application.action.council.CouncilContinuationPermit;
import org.xar.ck3.control.application.action.council.CouncilContinuationModel.Stage;
import org.xar.ck3.control.application.action.FrontendFrame;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeSnapshotWaitPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.NativeStepDiscriminator;
import org.xar.ck3.control.application.action.ExecutableStepBindings.Kind;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.NativePlanningReadPort;
import org.xar.ck3.control.application.action.ReadPermit;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.ReconciliationIdentity;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.SubmissionPermit;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** One held Game pipe. The application coordinator alone supplies single-use durable submission permits. */
public final class NativeGameTransport implements NativeActionPort, NativeSnapshotWaitPort, NativePlanningReadPort, NativeCoreFramePort, NativeFreshSnapshotPort, NativeFrontendRoutePort, AutoCloseable {
    private final NativePacketPort endpoint;
    private final NativePipeEndpoint.Config config;
    private final Clock chronologyClock;
    private final Optional<Duration> configuredReadTimeout;
    private final UUID custodyEpoch = UUID.randomUUID();
    private BigInteger chronologyOrder = BigInteger.ZERO;
    private Instant lastChronologyAt;
    private final Map<String, WrittenRequest> writtenRequests = new HashMap<>();
    private final Map<String, ReceivedResponse> originalResponses = new HashMap<>();
    private record WrittenRequest(TransportSession session, NativeRequestChronology.PacketIdentity packet,
            NativeRequestChronology.Event entered, Optional<NativeRequestChronology.Event> completed) { }
    private record ReceivedResponse(NativeRequestChronology.PacketIdentity packet, NativeRequestChronology.Event received) { }
    private final int maximumFramesPerOperation;
    private final int maximumSubmissions;
    private final List<NativePrivateActionPermission> privateActions;
    private record FrontendBootstrapAttempt(String requestId, NativeWire.Bytes packet,
            Optional<DispatchOutcome> outcome) { }
    private final Map<Primitive, FrontendBootstrapAttempt> frontendBootstrapAttempts =
            new java.util.EnumMap<>(Primitive.class);
    private final Set<String> sentRequestIds = new HashSet<>();
    private final Map<String, NativeWire.Bytes> originalOutboundPackets = new HashMap<>();
    private long retainedOutboundBytes;
    private final List<NativeWire.CommandResult> lateResults = new ArrayList<>();
    private int retainedResultBytes;
    private NativeWire.Hello hello;
    private Instant helloObservedAt;
    private ReceivedNotice latestHeartbeat;
    private ReceivedNotice latestPong;
    private ReceivedNotice latestError;
    private ReceivedNotice latestSnapshotDiagnostic;
    private BigInteger receivedSnapshotCount = BigInteger.ZERO;
    private BigInteger rejectedSnapshotCount = BigInteger.ZERO;
    private BigInteger snapshotPublishDiagnosticCount = BigInteger.ZERO;
    private NativeTransportDiagnostics.ReceivedSnapshot lastReceivedSnapshot;
    private NativeTransportDiagnostics.RejectedSnapshot lastRejectedSnapshot;
    private NativeTransportDiagnostics.AdoptionObservation adoptionDiagnostic = new NativeTransportDiagnostics.Unobserved();
    private PingAttempt handshakeAttempt;
    private HandshakePong handshakePong;
    private boolean diagnosticAccountingAvailable = true;
    private FreshSnapshotCapture pendingFreshSnapshot;
    /** One bounded original READ custody slot, not another canonical action or command store. */
    private static final class FreshSnapshotCapture {
        private final String requestId;
        private ObservedFrame frame;
        private NativeRequestChronology.Event received;
        private String invalid;
        private DispatchOutcome outcome;
        private FreshSnapshotCapture(String requestId){this.requestId=requestId;}
    }
    private NativeWire.Snapshot snapshot;
    private Instant snapshotObservedAt;
    private boolean snapshotUndelivered;
    private ObservedFrame acceptedSnapshotFrame;

    /** Receiver-owned live witness for an actual after-ACK snapshot occurrence. */
    public static final class AfterAcknowledgementSnapshot {
        private final NativeGameTransport issuer;
        private final ObservedFrame actual;
        private final AcceptedSnapshotRevision accepted;
        private final NativeRequestChronology setterChronology;
        private final NativeActionPort.AckReceived setter;

        private AfterAcknowledgementSnapshot(NativeGameTransport issuer, ObservedFrame actual,
                AcceptedSnapshotRevision accepted, NativeRequestChronology setterChronology,
                NativeActionPort.AckReceived setter) {
            this.issuer = issuer;
            this.actual = actual;
            this.accepted = accepted;
            this.setterChronology = setterChronology;
            this.setter = setter;
        }

        public ObservedFrame originalFrame() { return actual; }
        public AcceptedSnapshotRevision acceptedRevision() { return accepted; }
        public NativeRequestChronology setterChronology() { return setterChronology; }
        public UUID custodyEpoch() { return setterChronology.custodyEpoch(); }

        public void requireOriginal(NativeGameTransport actualHeld, ObservedFrame actual) throws IOException {
            if (issuer != actualHeld || this.actual != actual)
                throw new IOException("after-ACK witness requires its identical transport and received frame occurrence");
            var rebound = actualHeld.acceptedAfterAcknowledgement(actual, setter);
            if (rebound.accepted != accepted || !rebound.setterChronology.equals(setterChronology))
                throw new IOException("after-ACK witness no longer has its identical retained receiver and setter custody");
        }
    }

    public synchronized AfterAcknowledgementSnapshot acceptedAfterAcknowledgement(ObservedFrame actual,
            NativeActionPort.AckReceived setter) throws IOException {
        Objects.requireNonNull(actual); Objects.requireNonNull(setter);
        if (!setter.nativeOk()) throw new IOException("actual positive setter ACK required");
        if (closed || terminalFailure != null) throw new IOException("transport is closed or terminal");
        if (hello == null) throw new IOException("no held hello");
        var token = acceptedSnapshotRevision(actual);
        token.requireOriginal(actual);
        var chronology = originalRequestChronology(setter.requestId()).orElseThrow(
                () -> new IOException("setter chronology unavailable"));
        if (!chronology.equals(setter.custody().orElseThrow()))
            throw new IOException("setter chronology differs from ACK custody");
        if (!chronology.custodyEpoch().equals(custodyEpoch))
            throw new IOException("setter chronology epoch differs from transport");
        if (!chronology.session().equals(session()))
            throw new IOException("setter chronology session differs from transport");
        chronology.verify(setter);
        var outbound = originalOutboundPacket(setter.requestId()).orElseThrow(
                () -> new IOException("setter outbound packet unavailable"));
        if (!Arrays.equals(outbound.originalPacket(), setter.outbound().orElseThrow().originalPacket()))
            throw new IOException("setter outbound packet differs from ACK");
        var decoded = NativeWire.decode(setter.originalPacket());
        if (!(decoded instanceof NativeWire.CommandResult result)) throw new IOException("setter packet is not a command result");
        if (!result.requestId().equals(setter.requestId()) || !result.nativeOk())
            throw new IOException("setter command result differs from ACK");
        if (!Arrays.equals(result.payload().value(), setter.originalFrame().bytes()))
            throw new IOException("setter payload differs from ACK");
        var resultToken = result.result().token().map(value -> value.value());
        var setterToken = setter.originalResultToken().map(value -> value.bytes());
        if (resultToken.isPresent() != setterToken.isPresent())
            throw new IOException("setter result token presence differs from ACK");
        if (resultToken.isPresent() && !Arrays.equals(resultToken.get(), setterToken.get()))
            throw new IOException("setter result token bytes differ from ACK");
        var request = NativeWire.decodeExecuteRequest(outbound.originalPacket());
        if (!request.requestId().equals(setter.requestId()))
            throw new IOException("setter request id differs from ACK");
        var step = request.step();
        if (!step.equals("pause-map") && !step.equals("resume-map") && !step.equals("set-speed-1")
                && !step.equals("set-speed-2") && !step.equals("set-speed-3")
                && !step.equals("set-speed-4") && !step.equals("set-speed-5"))
            throw new IOException("setter step is not a valid timeline primitive");
        org.xar.ck3.control.application.advance.AdvancePrimitives.nativeResult(setter, step);
        if (!token.session().equals(actual.session()) || !token.session().equals(chronology.session()))
            throw new IOException("accepted snapshot differs from the actual setter and current held session");
        if (!token.snapshotId().equals(actual.snapshotId())) throw new IOException("accepted snapshot id differs from actual frame");
        if (!token.nativeRevision().equals(actual.nativeRevision())) throw new IOException("accepted native revision differs from actual frame");
        if (!token.originalPacket().equals(NativeRequestChronology.PacketIdentity.of(actual.originalPacket())))
            throw new IOException("accepted packet identity differs from actual frame");
        if (!token.received().observedAt().equals(actual.observedAt()))
            throw new IOException("accepted received time differs from actual frame observed time");
        if (token.received().order().compareTo(chronology.responseReceived().order()) <= 0)
            throw new IOException("accepted snapshot did not follow setter ACK");
        if (token.received().observedAt().isBefore(chronology.responseReceived().observedAt()))
            throw new IOException("accepted snapshot time regressed before setter ACK");
        return new AfterAcknowledgementSnapshot(this, actual, token, chronology, setter);
    }
    private BigInteger statePublicRevision = BigInteger.ZERO;
    private boolean stateConnected;
    private boolean stateRevisionAvailable=true;
    private boolean heldSnapshotInvalidated = false;
    public enum StateRevisionKind { HELLO, SNAPSHOT, DISCONNECTED }
    /** Unified packet and actual non-packet source revision DATA, never a live/readiness grant. */
    public static final class StateRevision {
        private final TransportSession session;
        private final NativeRequestChronology.Event received;
        private final BigInteger publicRevision;
        private final StateRevisionKind kind;
        private final Optional<NativePacketPort.Disconnection> disconnection;
        private StateRevision(TransportSession session,NativeRequestChronology.Event received,BigInteger revision,
                StateRevisionKind kind,Optional<NativePacketPort.Disconnection> disconnection) {
            this.session=session;this.received=received;publicRevision=revision;this.kind=kind;this.disconnection=disconnection;
        }
        public TransportSession session(){return session;}
        public NativeRequestChronology.Event received(){return received;}
        public BigInteger publicRevision(){return publicRevision;}
        public StateRevisionKind kind(){return kind;}
        public Optional<NativePacketPort.Disconnection> disconnection(){return disconnection;}
    }
    private StateRevision latestStateRevision;
    public synchronized Optional<StateRevision> latestStateRevision(){
        return stateRevisionAvailable?Optional.ofNullable(latestStateRevision):Optional.empty();
    }
    private OpportunityJson.Obj lastAcceptedSemantic;private OpportunityJson.Obj ownerCanonicalObj;private com.fasterxml.jackson.databind.JsonNode derivedJsonNode;
    private AcceptedSnapshotRevision latestAcceptedSnapshotRevision;
    private final Map<BigInteger, AcceptedSnapshotRevision> acceptedSnapshotRevisions = new LinkedHashMap<>();
    /** Original accepted receive DATA; only this receiver constructs it. No live-read or Ready authority. */
    public static final class AcceptedSnapshotRevision {
        private final WeakReference<ObservedFrame> original;
        private final TransportSession session;
        private final String snapshotId;
        private final BigInteger nativeRevision;
        private final NativeRequestChronology.Event received;
        private final BigInteger publicRevision;
        private final NativeRequestChronology.PacketIdentity packet;
        private AcceptedSnapshotRevision(ObservedFrame actual, NativeRequestChronology.Event received,
                BigInteger revision) throws IOException {
            original=new WeakReference<>(actual);session=actual.session();snapshotId=actual.snapshotId();
            nativeRevision=actual.nativeRevision();this.received=received;publicRevision=revision;
            packet=packetIdentity(actual.originalPacket());
        }
        public TransportSession session(){return session;}
        public String snapshotId(){return snapshotId;}
        public BigInteger nativeRevision(){return nativeRevision;}
        public NativeRequestChronology.Event received(){return received;}
        public BigInteger publicRevision(){return publicRevision;}
        public NativeRequestChronology.PacketIdentity originalPacket(){return packet;}
        /** Equal DATA cannot identify an occurrence: A/B/A may share bytes and a fixed clock. */
        public void requireOriginal(ObservedFrame actual) throws IOException {
            if(original.get()!=Objects.requireNonNull(actual))
                throw new IOException("accepted revision requires its identical actual received frame occurrence");
        }
    }
    /** No I/O; archived/reconstructed or expired originals cannot acquire a live receiver token. */
    public synchronized AcceptedSnapshotRevision acceptedSnapshotRevision(ObservedFrame actual) throws IOException {
        Objects.requireNonNull(actual);
        if(latestAcceptedSnapshotRevision!=null&&latestAcceptedSnapshotRevision.original.get()==actual)
            return latestAcceptedSnapshotRevision;
        for(var token:acceptedSnapshotRevisions.values())if(token.original.get()==actual)return token;
        throw new IOException("identical actual accepted snapshot occurrence is absent or outside its finite retained window");
    }
    /** Historical DATA after terminal/close, for NEXT accounting only; never a current read permission. */
    public synchronized Optional<AcceptedSnapshotRevision> latestAcceptedSnapshotRevision(){
        return Optional.ofNullable(latestAcceptedSnapshotRevision);
    }
    private void retainAcceptedSnapshotRevision(ObservedFrame actual, NativeRequestChronology.Event received,
            OpportunityJson.Obj semantic) throws IOException {
        BigInteger next=statePublicRevision;
        var currentNode=DriverJson.toNode(semantic);if(!NativeSemanticFingerprint.equivalent(currentNode,
                lastAcceptedSemantic==null?null:(lastAcceptedSemantic==ownerCanonicalObj&&derivedJsonNode!=null?derivedJsonNode:DriverJson.toNode(lastAcceptedSemantic))))next=next.add(BigInteger.ONE);
        if(next.compareTo(NativeWire.UINT64_MAX)>0)throw new IOException("actual received public revision exhausted uint64");
        var token=new AcceptedSnapshotRevision(actual,received,next);
        if(acceptedSnapshotRevisions.size()>=Math.max(4096,maximumFramesPerOperation))
            acceptedSnapshotRevisions.remove(acceptedSnapshotRevisions.keySet().iterator().next());
        acceptedSnapshotRevisions.put(received.order(),token);latestAcceptedSnapshotRevision=token;
        statePublicRevision=next;lastAcceptedSemantic=semantic;ownerCanonicalObj=semantic;derivedJsonNode=currentNode;
        latestStateRevision=new StateRevision(session(),received,next,StateRevisionKind.SNAPSHOT,Optional.empty());
    }
    private boolean closed;
    private String terminalFailure;
    private byte[] lastOriginalPacket = new byte[0];
    private ReceivedReadEvidence latestReadEvidence;
    private record ReceivedReadEvidence(long bytes, String sha256) { }
    private MailboxScope activeMailbox;
    private String mailboxPoison;
    private List<String> unresolvedMailboxRequestIds = List.of();
    /** Archived optional READ deferral; never native completion or assignment reconciliation. */
    public record MailboxReadDeferral(TransportSession session, List<String> originalRequestIds,
            String failedRequestId, ExactRef diagnostic) {
        public MailboxReadDeferral {
            Objects.requireNonNull(session);originalRequestIds=List.copyOf(originalRequestIds);
            StrictJson.text(failedRequestId);Objects.requireNonNull(diagnostic);
            StrictJson.require(!originalRequestIds.isEmpty()&&originalRequestIds.contains(failedRequestId)&&diagnostic.bytes()>0,
                    "actual deferred read IDs and archived failure diagnostic required");
        }
    }
    private MailboxReadDeferral lastMailboxReadDeferral;
    /** Retained diagnostic DATA cannot complete or unlock any business action. */
    public synchronized Optional<MailboxReadDeferral> deferredMailboxRead(){return Optional.ofNullable(lastMailboxReadDeferral);}
    private static final String COUNCIL_ASSIGN = "private-assign-councillor-v1";
    private static final String COUNCIL_RECEIPT = "private-query-assign-councillor-receipt-v1";
    private static final String COUNCIL_STATUS = "private-council-application-main-status-v1";
    private record CouncilAssignment(String actionId, String bodySha256, String requestId, GuardEvidence guard,
            NativeRequest originalRequest) { }
    private static final Set<String> COUNCIL_MAILBOX_STEPS = Set.of(
            "private-query-council-composition-candidates-v1", "private-query-council-final-gates-v1",
            "private-assign-councillor-v1", "private-query-assign-councillor-receipt-v1",
            "private-council-application-main-status-v1");

    /** A private lane for one actual new ISSUED read, never reconstructed assignment custody. */
    private CouncilRecoveryRole activeCouncilRecovery;
    private final class CouncilRecoveryRole {
        private final Thread owner = Thread.currentThread();
        private final CouncilContinuationPermit issued;
        private final CouncilContinuationCoordinator.RecoveryOriginal original;
        private final String requestId;
        private final Stage stage;
        private final Instant deadline;
        private boolean writeClaimed;
        private boolean released;
        private CouncilRecoveryRole(CouncilContinuationPermit issued,
                CouncilContinuationCoordinator.RecoveryOriginal original, Instant deadline) {
            this.issued = issued; this.original = original; this.deadline = deadline;
            this.requestId = issued.requestId(); this.stage = issued.stage();
        }
        private void binding() throws IOException {
            if (activeCouncilRecovery != this || released || owner != Thread.currentThread()
                    || activeMailbox != null || mailboxPoison != null
                    || issued.recoveryOriginal().orElse(null) != original
                    || !requestId.equals(issued.requestId()) || stage != issued.stage())
                throw new IOException("recovered Council RPC escaped its exact private permit, stage or thread");
        }
        /** Invoked by dispatchOriginal immediately before recording and entering the actual new write. */
        private void consumeAtWrite() {
            try {
                binding();
                if (writeClaimed) throw new IOException("recovered Council RPC already claimed its one write");
                original.requireCurrent();
                writeClaimed = true;
                issued.consumeOnce();
                binding(); open(deadline); verifyEndpoint();
                requireRecoveredGuard(issued, original);
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
        }
    }

    private static final String COUNCIL_SEAT_QUERY = "private-query-council-composition-candidates-v1";
    private RecoveredSeatMailbox activeRecoveredSeatMailbox;
    /** This private marker adds no assignment, ISSUED permit or historical wire custody. */
    private final class RecoveredSeatMailbox {
        private final Thread owner = Thread.currentThread();
        private final CouncilContinuationCoordinator.RecoveryOriginal original;
        private final GuardEvidence observation;
        private final Instant deadline;
        private final MailboxScope scope;
        private final String position;
        private ReadPermit admitted;
        private String readBinding;
        private boolean released;
        private RecoveredSeatMailbox(CouncilContinuationCoordinator.RecoveryOriginal original,
                GuardEvidence observation, Instant deadline, MailboxScope scope) {
            this.original = original; this.observation = observation; this.deadline = deadline; this.scope = scope;
            this.position = org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation
                    .councilRequest(original.command(), original.attempt().requestId()).position().key();
        }
        private void current() throws IOException {
            if (activeRecoveredSeatMailbox != this || released || owner != Thread.currentThread()
                    || activeCouncilRecovery != null || mailboxPoison != null || terminalFailure != null || closed)
                throw new IOException("recovered seat mailbox escaped its actual private role, owner or live transport");
            scope.current();
            if (scope.unknownSeen || scope.readOnlyPrefixConsumed || scope.deferredReadDiagnostic != null)
                throw new IOException("recovered seat mailbox cannot continue an unknown or consumed READ prefix");
            requireRecoveredSeatGuard(original, observation, deadline);
        }
        private void authorize(ReadPermit permit, NativeRequest request, Instant requestDeadline) throws IOException {
            current();
            var guard = permit.guard(); var contract = permit.contract();
            var identity = observation.origin().requireReconciliation();
            if (admitted != null || requestDeadline.isAfter(deadline)
                    || !(permit.origin() instanceof CommandOrigin.Gameplay gameplay)
                    || !gameplay.before().equals(identity.factual()) || !guard.origin().equals(permit.origin())
                    || !guard.source().equals(observation.source()) || !guard.sessionId().equals(observation.sessionId())
                    || !guard.connectionGeneration().equals(observation.connectionGeneration())
                    || !guard.nativeEvidence().equals(observation.nativeEvidence())
                    || !guard.capabilityEvidence().equals(observation.capabilityEvidence())
                    || !guard.authorityId().equals(observation.authorityId())
                    || !guard.observedAt().equals(observation.observedAt())
                    || !guard.operation().equals(contract.operation())
                    || contract.permissionMode() != ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                    || contract.guardMode() != ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                    || contract.advertisedRequired() || request.requiredCapability().isPresent()
                    || !request.equals(permit.preparedRequest()) || !request.step().equals(contract.operation().value())
                    || permit.consumed() || sentRequestIds.contains(permit.requestId()))
                throw new IOException("recovered seat READ changed its real permit, same-capture frame/source/guard or deadline");
            if (readBinding != null && !readBinding.equals(permit.readGuard().originalBindingSha256()))
                throw new IOException("recovered seat READ changed its actual full binding between QUERY and STATUS");
            var fields = NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
            if (scope.attempted.isEmpty()) {
                if (!request.step().equals(COUNCIL_SEAT_QUERY)
                        || contract.wireProfile() != ReadContract.WireProfile.EXECUTE_STEP
                        || !fields.equals(StrictJson.object().put("position_key", position)))
                    throw new IOException("recovered seat mailbox begins only with its exact selected-position composition QUERY");
            } else if (!request.step().equals(COUNCIL_STATUS)
                    || contract.wireProfile() != ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS || !fields.isEmpty()
                    || !(scope.lastOutcome instanceof AckReceived ack) || !isCouncilPending(ack)) {
                throw new IOException("recovered seat mailbox STATUS requires its preceding actual pending ACK");
            }
            if (readBinding == null) readBinding = permit.readGuard().originalBindingSha256();
            admitted = permit;
        }
        private void dispatch(String requestId, String step, boolean continuation) throws IOException {
            current();
            if (continuation || admitted == null || !admitted.requestId().equals(requestId)
                    || !admitted.preparedRequest().step().equals(step)
                    || activeMailbox.actualReads.get(requestId) != admitted)
                throw new IOException("only the exact admitted recovered-seat READ may enter this write");
        }
    }

    private void requireRecoveredSeatGuard(CouncilContinuationCoordinator.RecoveryOriginal original,
            GuardEvidence observation, Instant deadline) throws IOException {
        original.requireCurrent();
        var command = original.command(); var attempt = original.attempt();
        var before = attempt.guard(); Instant now = Instant.now();
        if (!(observation.origin() instanceof CommandOrigin.Reconciliation)
                || !observation.equals(original.observationGuard()) || hello == null
                || !now.isBefore(deadline) || !now.isBefore(observation.validUntil()) || observation.observedAt().isAfter(now)
                || !config.sessionId().equals(command.sessionId()) || !command.sessionId().equals(observation.sessionId())
                || !observation.sessionId().equals(before.sessionId())
                || !hello.connectionGeneration().equals(observation.connectionGeneration())
                || !observation.source().equals(command.source()) || !observation.source().equals(before.source())
                || !observation.operation().equals(command.operation()) || !observation.operation().equals(before.operation())
                || !observation.authorityId().equals(before.authorityId()))
            throw new IOException("recovered seat scope changed its actual captured reconciliation guard or current HELLO/source");
        var identity = observation.origin().requireReconciliation(); var pending = identity.pending();
        if (!pending.actionId().equals(command.actionId()) || !pending.bodySha256().equals(ActionCodec.bodySha256(command))
                || !pending.requestId().equals(attempt.requestId()) || !pending.originalBefore().equals(command.before())
                || !identity.observedAt().equals(observation.observedAt()))
            throw new IOException("recovered seat scope differs from the unchanged actual original pending action");
        identity.requireOriginalConnection(before);
        org.xar.ck3.control.nativebridge.capabilities.governance.CouncilContinuationPolicy
                .requireOriginalPending(command, attempt, original.originalAck());
        requireIdentity(observation.origin()); requireRawEvidence(observation); requireLivingPausedMap();
    }

    /** Root and archive/checkpoint work runs outside the Native monitor; only its RPCs reenter it. */
    public <T> T withRecoveredSeatMailbox(CouncilContinuationCoordinator.RecoveryOriginal original,
            GuardEvidence sameCaptureObservation, Instant deadline, MailboxWork<T> work)
            throws IOException, InterruptedException {
        Objects.requireNonNull(original); Objects.requireNonNull(sameCaptureObservation);
        Objects.requireNonNull(deadline); Objects.requireNonNull(work);
        final RecoveredSeatMailbox seat;
        synchronized (this) {
            open(deadline);
            if (activeMailbox != null || activeCouncilRecovery != null || activeRecoveredSeatMailbox != null || mailboxPoison != null)
                throw new IOException("recovered seat mailbox cannot nest or replace unresolved Native custody");
            verifyEndpoint();
            requireRecoveredSeatGuard(original, sameCaptureObservation, deadline);
            MailboxScope scope = new MailboxScope();
            seat = new RecoveredSeatMailbox(original, sameCaptureObservation, deadline, scope);
            activeMailbox = scope; activeRecoveredSeatMailbox = seat;
        }
        try {
            T result = work.run(seat.scope);
            synchronized (this) {
                if (activeRecoveredSeatMailbox != seat || activeMailbox != seat.scope || seat.released
                        || terminalFailure != null || closed || mailboxPoison != null || seat.scope.unknownSeen)
                    throw new IOException("recovered seat callback cannot return after unknown or lost Native custody");
                original.requireCurrent();
                if (!seat.scope.attempted.isEmpty() && (!seat.scope.readOnlyPrefixConsumed || !seat.scope.completed))
                    throw new IOException("recovered seat callback must consume its full typed READ prefix and last actual terminal ACK");
            }
            return result;
        } finally {
            synchronized (this) {
                if (!seat.scope.attempted.isEmpty() && (seat.scope.unknownSeen || !seat.scope.completed
                        || !seat.scope.readOnlyPrefixConsumed)) {
                    mailboxPoison = "recovered seat READ remains unresolved; no producer may overwrite its actual custody";
                    unresolvedMailboxRequestIds = List.copyOf(seat.scope.attempted); latestReadEvidence = null;
                }
                seat.admitted = null; seat.released = true; seat.scope.released = true;
                if (activeMailbox == seat.scope) activeMailbox = null;
                if (activeRecoveredSeatMailbox == seat) activeRecoveredSeatMailbox = null;
            }
        }
    }


    @FunctionalInterface public interface MailboxWork<T> {
        T run(MailboxScope scope) throws IOException, InterruptedException;
    }
    /** Actual held-connection custody, never a native mailbox ticket or a replay permission. */
    public record MailboxDiagnostics(boolean scopeHeld, Optional<String> poison, List<String> unresolvedRequestIds) {
        public MailboxDiagnostics { Objects.requireNonNull(poison); unresolvedRequestIds = List.copyOf(unresolvedRequestIds); }
    }
    /** Root callers first hold the actual writer Session; they archive every original step before completing. */
    public final class MailboxScope {
        private final Thread owner = Thread.currentThread();
        private final List<String> attempted = new ArrayList<>();
        private final List<DispatchOutcome> originalOutcomes = new ArrayList<>();
        private final Map<String, ReadPermit> actualReads = new HashMap<>();
        private ExactRef deferredReadDiagnostic;
        private DispatchOutcome lastOutcome;
        private CouncilAssignment assignment;
        private boolean helperCompleted;
        private boolean helperRejectedBeforeSubmit;
        private boolean receiptPending;
        private boolean receiptCompleted;
        private boolean unknownSeen;
        private boolean completed;
        private boolean pendingSeen;
        private boolean readOnlyPrefixConsumed;
        private boolean released;
        private MailboxScope() { }
        public void complete(DispatchOutcome originalTerminal) throws IOException {
            synchronized (NativeGameTransport.this) {
                current();
                if (unknownSeen) throw new IOException("UNKNOWN mailbox requires explicit reconciliation; collecting evidence alone cannot unlock it");
                if (assignment != null && !receiptCompleted && !helperRejectedBeforeSubmit)
                    throw new IOException("private assignment remains open until its independent receipt terminal was consumed");
                if (originalTerminal != lastOutcome || !(originalTerminal instanceof AckReceived ack))
                    throw new IOException("mailbox completion requires its last actual original ACK, never a reconstructed receipt");
                if (!ack.nativeOk() && pendingSeen)
                    throw new IOException("a rejected status after pending cannot prove the mailbox was consumed");
                if (isCouncilTransportStatus(ack))
                    throw new IOException("pending or idle transport status is not a consumed native terminal result");
                completed = true;
            }
        }
        /** Consumes only this held, actually received READ prefix; it grants no submit or retry permission. */
        public void consumeReadOnlyPrefix(List<PlanningReadReceipt> originals) throws IOException {
            synchronized (NativeGameTransport.this) {
                current();
                if (unknownSeen || assignment != null || helperCompleted || helperRejectedBeforeSubmit
                        || receiptPending || receiptCompleted || readOnlyPrefixConsumed || terminalFailure != null || closed)
                    throw new IOException("read prefix cannot replace unknown, assignment, receipt or completed custody");
                List<PlanningReadReceipt> reads = List.copyOf(Objects.requireNonNull(originals));
                if (reads.isEmpty() || reads.size() > 3002 || reads.size() != attempted.size()
                        || reads.size() != originalOutcomes.size() || lastOutcome != reads.getLast().original())
                    throw new IOException("complete identical original mailbox READ prefix required");
                PlanningReadRequest first = reads.getFirst().request();
                String initialStep = first.operation().value();
                if (!initialStep.equals("private-query-council-composition-candidates-v1")
                        && !initialStep.equals("private-query-council-final-gates-v1"))
                    throw new IOException("only an original Council QUERY or GATES can begin a read prefix");
                NativeRequestChronology previous = null;
                for (int index = 0; index < reads.size(); index++) {
                    PlanningReadReceipt read = reads.get(index); String id = attempted.get(index);
                    ReadPermit permit = actualReads.get(id); WrittenRequest written = writtenRequests.get(id);
                    if (!id.equals(read.requestId()) || originalOutcomes.get(index) != read.original()
                            || permit == null || !permit.consumed() || written == null || written.completed().isEmpty()
                            || !permit.readGuard().equals(read.before()) || !permit.origin().equals(first.origin())
                            || !read.request().origin().equals(first.origin()) || !read.request().source().equals(first.source())
                            || !read.request().sessionId().equals(first.sessionId()) || !read.request().deadline().equals(first.deadline())
                            || !permit.contract().contractId().equals(read.contractId())
                            || !permit.preparedRequest().step().equals(index == 0 ? initialStep : COUNCIL_STATUS))
                        throw new IOException("mailbox READ prefix changed its consumed permit, frame, source or actual ACK");
                    try {
                        if (!permit.contract().prepare(read.request(), id).equals(permit.preparedRequest()))
                            throw new IOException("mailbox READ prefix changed its actual prepared request");
                        NativeRequestChronology actual = read.original().custody().orElseThrow(
                                () -> new IOException("mailbox READ original chronology unavailable"));
                        actual.verify(read);
                        if (!actual.session().equals(session()) || !actual.custodyEpoch().equals(custodyEpoch)
                                || previous != null && (actual.writeEntered().order().compareTo(previous.responseReceived().order()) <= 0
                                || actual.writeEntered().observedAt().isBefore(previous.responseReceived().observedAt())))
                            throw new IOException("mailbox READ prefix crossed this actual connection, epoch or response order");
                        previous = actual;
                        Object decoded = permit.contract().replay(read);
                        if (index < reads.size() - 1) {
                            if (!(decoded instanceof org.xar.ck3.control.governance.council.CouncilPrivateCodec.Pending))
                                throw new IOException("an earlier mailbox READ was not genuinely pending");
                        } else {
                            if (!(decoded instanceof org.xar.ck3.control.governance.council.CouncilPrivateCodec.Terminal terminal))
                                throw new IOException("mailbox READ prefix has no accepted typed terminal");
                            org.xar.ck3.control.governance.council.CouncilPrivateCodec.requireTerminalBinding(terminal,
                                    initialStep, org.xar.ck3.control.nativebridge.capabilities.governance.PrivateCouncilReads.nativeFrame(first));
                        }
                    } catch (RuntimeException invalid) {
                        throw new IOException("mailbox READ prefix failed its original registered decoder", invalid);
                    }
                }
                readOnlyPrefixConsumed = true;
                pendingSeen = false;
            }
        }
        /** Leaves only this original optional READ prefix, after a real current after guard and original archive check. */
        public void deferReadOnly(PlanningReadFailure live, ExactRef sharedFailureDiagnostic,
                ActionPorts.OutcomeArchive boundArchive) throws IOException {
            synchronized(NativeGameTransport.this) {
                current();Objects.requireNonNull(live);Objects.requireNonNull(sharedFailureDiagnostic);Objects.requireNonNull(boundArchive);
                if (activeRecoveredSeatMailbox != null) throw new IOException("recovered seat scope cannot convert unresolved custody to optional READ deferral");
                if(assignment!=null||terminalFailure!=null||closed||lastOutcome!=live.original()
                        ||attempted.isEmpty()||originalOutcomes.size()!=attempted.size()
                        ||new HashSet<>(attempted).size()!=attempted.size())
                    throw new IOException("read-only deferral requires this exact unassigned, nonterminal original mailbox prefix");
                verifyEndpoint();
                for(int index=0;index<attempted.size();index++) {
                    String id=attempted.get(index);ReadPermit permit=actualReads.get(id);
                    DispatchOutcome original=originalOutcomes.get(index);WrittenRequest written=writtenRequests.get(id);
                    if(permit==null||!permit.consumed()||written==null||written.completed().isEmpty()
                            ||!original.requestId().equals(id)||!permit.origin().equals(live.request().origin())
                            ||!permit.guard().source().equals(live.request().source()))
                        throw new IOException("deferred mailbox contains a non-READ, incomplete write or different actual frame/source");
                    String step=permit.preparedRequest().step();
                    if(index==0?!(step.equals("private-query-council-composition-candidates-v1")
                            ||step.equals("private-query-council-final-gates-v1")):!step.equals(COUNCIL_STATUS))
                        throw new IOException("read-only deferral permits only the actual Council QUERY/GATES then STATUS prefix");
                    if(index<attempted.size()-1&&(!(original instanceof AckReceived ack)||!isCouncilPending(ack)))
                        throw new IOException("read-only deferral cannot pass an unresolved or terminal earlier mailbox response");
                }
                ReadPermit last=actualReads.get(live.requestId());
                if(last==null||!last.readGuard().equals(live.before())||!last.preparedRequest().equals(live.prepared())
                        ||!PlanningReadFailure.returnedRead(live.original()))
                    throw new IOException("read-only deferral lost the actual last READ permit, preparation or returned-send proof");
                try {
                    org.xar.ck3.control.nativebridge.capabilities.governance.CouncilTechnicalReadFailures
                            .requireTechnicalReadFailure(live);
                } catch(RuntimeException outsideTechnicalDomain) {
                    throw new IOException("original Council READ is outside the shared technical failure domain",outsideTechnicalDomain);
                }
                requireIdentity(live.after().binding().origin());requireRawEvidence(live.after().binding());requireLivingPausedMap();
                try {
                    if(!PlanningReadFailureCodec.load(sharedFailureDiagnostic,boundArchive).equals(live))
                        throw new IOException("deferred READ diagnostic differs from the actual original failure and after guard");
                } catch(RuntimeException invalidArchive) {throw new IOException("deferred READ originals are not actually archived",invalidArchive);}
                verifyEndpoint();
                deferredReadDiagnostic=sharedFailureDiagnostic;
            }
        }
        private void current() throws IOException {
            if (released || activeMailbox != this || owner != Thread.currentThread() || completed || deferredReadDiagnostic!=null)
                throw new IOException("mailbox scope is absent, released, completed or owned by another caller");
        }
        private void record(DispatchOutcome outcome) {
            lastOutcome = outcome;
            if (outcome instanceof Unknown) unknownSeen = true;
            if (!(outcome instanceof RejectedBeforeDispatch)) {attempted.add(outcome.requestId());originalOutcomes.add(outcome);}
            if (outcome instanceof AckReceived ack && isCouncilTransportStatus(ack)) pendingSeen = true;
        }
    }
    public synchronized MailboxDiagnostics mailboxDiagnostics() {
        return new MailboxDiagnostics(activeMailbox != null, Optional.ofNullable(mailboxPoison), unresolvedMailboxRequestIds);
    }
    /** No automatic unlock: UNKNOWN requires a separately implemented, source-bound reconciliation protocol. */
    public synchronized <T> T withMailbox(Instant deadline, MailboxWork<T> work) throws IOException, InterruptedException {
        Objects.requireNonNull(work);
        if (activeCouncilRecovery != null) throw new IOException("recovered Council RPC cannot acquire an ordinary mailbox");
        open(deadline);
        if (activeMailbox != null || mailboxPoison != null) throw new IOException("held mailbox is already scoped or unresolved");
        awaitHello(deadline); verifyEndpoint();
        MailboxScope scope = new MailboxScope(); activeMailbox = scope;boolean returned=false;
        try {
            T result = work.run(scope);
            if (!scope.attempted.isEmpty() && !scope.completed && scope.deferredReadDiagnostic==null)
                throw new IOException("mailbox callback returned without a verified archived terminal ACK or original optional READ deferral");
            if(scope.deferredReadDiagnostic!=null) {
                if(terminalFailure!=null||closed)throw new IOException("terminal Native failure cannot leave as an optional READ deferral");
                verifyEndpoint();
                lastMailboxReadDeferral=new MailboxReadDeferral(session(),scope.attempted,scope.lastOutcome.requestId(),scope.deferredReadDiagnostic);
                latestReadEvidence=null;
            }
            returned=true;return result;
        } finally {
            if (!scope.attempted.isEmpty() && !scope.completed && !(returned&&scope.deferredReadDiagnostic!=null)) {
                mailboxPoison = "original mailbox attempt remains unresolved; no producer may overwrite its custody";
                unresolvedMailboxRequestIds = List.copyOf(scope.attempted);
                latestReadEvidence = null;
            }
            scope.released = true; activeMailbox = null;
        }
    }
    private static boolean isCouncilTransportStatus(AckReceived ack) {
        if (!ack.nativeOk() || ack.originalResultToken().isEmpty()) return false;
        try {
            var result = NativeWire.parse(ack.originalResultToken().orElseThrow().bytes());
            return result.isObject() && result.has("private_council_transport");
        } catch (IOException malformed) { return true; }
    }
    private DispatchOutcome recordMailboxOutcome(DispatchOutcome outcome) {
        if (activeMailbox != null) activeMailbox.record(outcome);
        return outcome;
    }
    private void requireDispatchScope(String step, boolean continuation, String requestId) throws IOException {
        if (activeRecoveredSeatMailbox != null) activeRecoveredSeatMailbox.dispatch(requestId, step, continuation);
        if (activeCouncilRecovery != null) throw new IOException("ordinary Native dispatch is blocked during the exact recovered Council RPC");
        if (mailboxPoison != null) throw new IOException(mailboxPoison);
        if (activeMailbox != null) {
            activeMailbox.current();
            if (activeMailbox.unknownSeen) throw new IOException("UNKNOWN mailbox cannot dispatch another request");
            if (activeMailbox.helperRejectedBeforeSubmit)
                throw new IOException("known non-invoked Council helper rejection permits only completion of its original ACK");
            if (activeMailbox.assignment != null && COUNCIL_MAILBOX_STEPS.contains(step) && !continuation)
                throw new IOException("private assignment status and receipt need the canonical durable continuation permit");
            if (activeMailbox.pendingSeen && !step.equals(COUNCIL_STATUS) && !step.equals(COUNCIL_RECEIPT))
                throw new IOException("only the held mailbox status or receipt may follow pending custody");
        }
        if (COUNCIL_MAILBOX_STEPS.contains(step) && activeMailbox == null)
            throw new IOException("council mailbox producers require one held scope across initial, status and terminal custody");
    }

    public NativeGameTransport(NativePipeEndpoint endpoint, int maximumFramesPerOperation, int maximumSubmissions) {
        this(endpoint, maximumFramesPerOperation, maximumSubmissions, List.of());
    }
    public NativeGameTransport(NativePipeEndpoint endpoint, int maximumFramesPerOperation, int maximumSubmissions,
            List<NativePrivateActionPermission> privateActions) {
        this(endpoint, endpoint.config(), maximumFramesPerOperation, maximumSubmissions, privateActions);
    }
    public NativeGameTransport(NativePipeEndpoint endpoint, int maximumFramesPerOperation, int maximumSubmissions,
            List<NativePrivateActionPermission> privateActions, Duration readTimeout) {
        this(endpoint, endpoint.config(), maximumFramesPerOperation, maximumSubmissions, privateActions, Clock.systemUTC(), readTimeout);
    }
    /** Same transport state machine with an original-producer replay packet source in offline tests. */
    NativeGameTransport(NativePacketPort endpoint, NativePipeEndpoint.Config config,
            int maximumFramesPerOperation, int maximumSubmissions) {
        this(endpoint, config, maximumFramesPerOperation, maximumSubmissions, List.of());
    }
    NativeGameTransport(NativePacketPort endpoint, NativePipeEndpoint.Config config,
            int maximumFramesPerOperation, int maximumSubmissions, List<NativePrivateActionPermission> privateActions) {
        this(endpoint, config, maximumFramesPerOperation, maximumSubmissions, privateActions, Clock.systemUTC());
    }
    /** Offline replay may supply a deterministic clock; real public endpoints always use system UTC. */
    NativeGameTransport(NativePacketPort endpoint, NativePipeEndpoint.Config config,
            int maximumFramesPerOperation, int maximumSubmissions, List<NativePrivateActionPermission> privateActions, Clock chronologyClock) {
        this(endpoint, config, maximumFramesPerOperation, maximumSubmissions, privateActions, chronologyClock, Optional.empty());
    }
    NativeGameTransport(NativePacketPort endpoint, NativePipeEndpoint.Config config,
            int maximumFramesPerOperation, int maximumSubmissions, List<NativePrivateActionPermission> privateActions, Clock chronologyClock, Duration readTimeout) {
        this(endpoint, config, maximumFramesPerOperation, maximumSubmissions, privateActions, chronologyClock, Optional.of(requirePositive(readTimeout)));
    }
    private static Duration requirePositive(Duration duration) {
        if (duration == null || duration.isNegative() || duration.isZero()) throw new IllegalArgumentException("explicit positive read timeout required");
        return duration;
    }
    private NativeGameTransport(NativePacketPort endpoint, NativePipeEndpoint.Config config,
            int maximumFramesPerOperation, int maximumSubmissions, List<NativePrivateActionPermission> privateActions, Clock chronologyClock, Optional<Duration> configuredReadTimeout) {
        this.endpoint = Objects.requireNonNull(endpoint); this.config = Objects.requireNonNull(config);
        this.chronologyClock = Objects.requireNonNull(chronologyClock);
        this.configuredReadTimeout = Objects.requireNonNull(configuredReadTimeout);
        this.privateActions = List.copyOf(privateActions); Set<String> operations = new HashSet<>();
        for (NativePrivateActionPermission permission : this.privateActions)
            if (!operations.add(permission.operation().value())) throw new IllegalArgumentException("duplicate private mutation registration");
        if (maximumFramesPerOperation < 1 || maximumFramesPerOperation > 65_536 || maximumSubmissions < 1 || maximumSubmissions > 1_000_000)
            throw new IllegalArgumentException("explicit finite frame/submission bounds required");
        this.maximumFramesPerOperation = maximumFramesPerOperation; this.maximumSubmissions = maximumSubmissions;
    }
    @FunctionalInterface
    public interface HelloPacketCustody { void retain(byte[] originalPacket) throws IOException; }
    private HelloPacketCustody initialHelloCustody;
    /** Retains the original first packet before parsing or accepting any of its claims. */
    public synchronized TransportSession awaitHello(Instant deadline, HelloPacketCustody custody) throws IOException, InterruptedException {
        Objects.requireNonNull(custody);
        if(hello!=null||initialHelloCustody!=null)throw new IOException("Fresh original hello custody required; no recapture/reconnect");
        initialHelloCustody=custody;
        try{return awaitHello(deadline);}finally{initialHelloCustody=null;}
    }
    public synchronized TransportSession awaitHello(Instant deadline) throws IOException, InterruptedException {
        open(deadline);
        try { endpoint.awaitConnection(deadline); }
        catch(IOException failure) {retainActualDisconnection(failure);throw failure;}
        if (hello == null) {
            Optional<NativeWire.Frame> first = read(deadline);
            if (first.isEmpty() || !(first.orElseThrow() instanceof NativeWire.Hello)) throw new IOException("original Native hello must be the first frame");
        }
        verifyEndpoint(); return session();
    }
    private static final class ArmyReadonlyBinding {
        private final org.xar.ck3.control.platform.ManagedGameSession owner;
        private final NativePacketPort softwareEndpoint;
        private final ExactRef bridge;
        private final org.xar.ck3.control.build.SharedSourceFiles.Witness artifact;
        private ArmyReadonlyBinding(org.xar.ck3.control.platform.ManagedGameSession owner,NativePacketPort software,
                ExactRef bridge,org.xar.ck3.control.build.SharedSourceFiles.Witness artifact){
            this.owner=owner;this.softwareEndpoint=software;this.bridge=bridge;this.artifact=artifact;
        }
    }
    /** Source mode is unbound until a qualified artifact/owner binding succeeds. HELLO alone never selects it. */
    public enum NativeSourceMode { DEFAULT_CONTROL, CURRENT_IDENTITY_READONLY }
    private NativeSourceMode selectedSourceMode;
    public synchronized Optional<NativeSourceMode> sourceMode(){return Optional.ofNullable(selectedSourceMode);}
    /** Compatibility check only: a default getter that finds no qualified source remains unbound. */
    public synchronized void requireSourceMode(NativeSourceMode requested)throws IOException{
        Objects.requireNonNull(requested);
        if(selectedSourceMode!=null&&selectedSourceMode!=requested)
            throw new IOException("actual Native source mode is already frozen to "+selectedSourceMode);
    }
    private void beginSourceBinding(NativeSourceMode requested)throws IOException{
        requireSourceMode(requested);
        if(selectedSourceMode==null&&(!writtenRequests.isEmpty()||!originalResponses.isEmpty()||!sentRequestIds.isEmpty()
                ||receivedSnapshotCount.signum()!=0||pendingFreshSnapshot!=null||snapshot!=null||acceptedSnapshotFrame!=null))
            throw new IOException("source mode cannot reinterpret an original request, pending read or received snapshot");
    }
    private void commitSourceBinding(NativeSourceMode requested){selectedSourceMode=requested;}
    private void requireWorldActionMode()throws IOException{
        if(selectedSourceMode==NativeSourceMode.CURRENT_IDENTITY_READONLY)
            throw new IOException("identity-only source mode cannot submit world commands");
    }
    private ArmyReadonlyBinding armyReadonlySource;
    private ArmyReadonlyBinding armyIdentity126Source;
    /** Explicit independent identity observation. This DATA is never a Full-clock/action receipt. */
    public sealed interface ArmyIdentityRead permits ArmyIdentityReceived,ArmyIdentityUnavailable { }
    public record ArmyIdentityUnavailable(NativeFreshSnapshotPort.Result original,String reason) implements ArmyIdentityRead {
        public ArmyIdentityUnavailable { Objects.requireNonNull(original);Objects.requireNonNull(reason); }
    }
    public static final class ArmyIdentityReceived implements ArmyIdentityRead {
        private final NativeFreshSnapshotPort.Received original;
        private final ExactRef source;
        private final OpportunityJson.Obj semantic;
        private ArmyIdentityReceived(NativeFreshSnapshotPort.Received original,ExactRef source,OpportunityJson.Obj semantic) {
            this.original=original;this.source=source;this.semantic=semantic;
        }
        public ObservedFrame frame(){return original.originalFrame();}
        public ExactRef source(){return source;}
        public OpportunityJson.Obj semantic(){return semantic;}
    }
    /** Does not select this source from wire labels, row shape or nativeTransport's default binding. */
    public synchronized Optional<ExactRef> bindArmyIdentity126Source(org.xar.ck3.control.platform.ManagedGameSession owner)throws IOException {
        requireSourceMode(NativeSourceMode.CURRENT_IDENTITY_READONLY);
        Objects.requireNonNull(owner).requireNativeTransport(this);
        var selected=owner.launchPlan().sources().review().bridgeDll();
        var bridge=new ExactRef(selected.path(),selected.bytes(),selected.sha256());
        if(!org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies.identityOnly126SourceMatches(bridge))return Optional.empty();
        if(full112Source!=null||full114Source!=null||armyReadonlySource!=null)
            throw new IOException("identity126 cannot replace a different bound source mode");
        if(armyIdentity126Source!=null) {
            if(armyIdentity126Source.owner!=owner||!armyIdentity126Source.bridge.equals(bridge))
                throw new IOException("identity126 source already belongs to another owner");
            requireArmyIdentity126Source(false);return Optional.of(bridge);
        }
        beginSourceBinding(NativeSourceMode.CURRENT_IDENTITY_READONLY);
        requireArmyIdentity126Owner(owner,bridge);
        armyIdentity126Source=new ArmyReadonlyBinding(owner,null,bridge,armyIdentity126Artifact(bridge));
        commitSourceBinding(NativeSourceMode.CURRENT_IDENTITY_READONLY);
        return Optional.of(bridge);
    }
    /** Identical software endpoint plus a real exact artifact witness; never a fabricated Managed owner. */
    synchronized void bindArmyIdentity126SoftwareSource(NativePacketPort original,ExactRef bridge)throws IOException {
        requireSourceMode(NativeSourceMode.CURRENT_IDENTITY_READONLY);
        if(endpoint!=Objects.requireNonNull(original)||endpoint instanceof NativePipeEndpoint||armyIdentity126Source!=null
                ||full112Source!=null||full114Source!=null||armyReadonlySource!=null)
            throw new IOException("identity126 fixture requires its original non-live unbound endpoint");
        beginSourceBinding(NativeSourceMode.CURRENT_IDENTITY_READONLY);
        armyIdentity126Source=new ArmyReadonlyBinding(null,original,bridge,armyIdentity126Artifact(bridge));
        commitSourceBinding(NativeSourceMode.CURRENT_IDENTITY_READONLY);
    }
    private static org.xar.ck3.control.build.SharedSourceFiles.Witness armyIdentity126Artifact(ExactRef bridge)throws IOException {
        if(!org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies.identityOnly126SourceMatches(bridge))
            throw new IOException("exact independent126 identity-only source required");
        var witness=org.xar.ck3.control.build.SharedSourceFiles.observe(java.nio.file.Path.of(bridge.path()));
        if(witness.source().bytes()!=bridge.bytes()||!witness.source().sha256().equalsIgnoreCase(bridge.sha256()))
            throw new IOException("identity126 source artifact changed");
        return witness;
    }
    private void requireArmyIdentity126Owner(org.xar.ck3.control.platform.ManagedGameSession owner,ExactRef bridge)throws IOException {
        owner.requireNativeTransport(this);var plan=owner.launchPlan();var selected=plan.sources().review().bridgeDll();
        if(!owner.generation().equals(config.game())||!owner.machineId().equals(config.machineId())||!owner.sessionId().equals(config.sessionId())
                ||!plan.pipeName().equals(config.pipeName())||!plan.bridgeVersion().equals(config.expectedBridgeVersion())
                ||!plan.adapterId().equals(config.expectedAdapterId())
                ||!plan.adapterId().equals(ExactCk3Build.CK3_121003_STEAM_26785313_FULL111.coreFullAdapterId())
                ||!plan.sources().review().gameExecutable().sha256().equalsIgnoreCase(ExactCk3Build.CK3_121003_STEAM_26785313.executableSha256())
                ||!bridge.equals(new ExactRef(selected.path(),selected.bytes(),selected.sha256())))
            throw new IOException("identity126 crossed actual owner/Game/machine/session/endpoint/source");
    }
    private ExactRef requireArmyIdentity126Source(boolean requireHello)throws IOException {
        var bound=armyIdentity126Source;
        if(closed||terminalFailure!=null||bound==null||full112Source!=null||full114Source!=null||armyReadonlySource!=null)
            throw new IOException("explicit identity126 mode is not current or is mixed");
        verifyEndpoint();
        if(bound.owner!=null)requireArmyIdentity126Owner(bound.owner,bound.bridge);
        else if(bound.softwareEndpoint!=endpoint||endpoint instanceof NativePipeEndpoint)
            throw new IOException("identity126 software source escaped its original endpoint");
        if(!org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies.identityOnly126SourceMatches(bound.bridge))
            throw new IOException("identity126 profile changed");
        org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(bound.artifact);
        if(requireHello) {
            if(hello==null||!hello.adapterId().equals(ExactCk3Build.CK3_121003_STEAM_26785313_FULL111.coreFullAdapterId())
                    ||!hello.gameSha256().equalsIgnoreCase(ExactCk3Build.CK3_121003_STEAM_26785313.executableSha256())
                    ||!hello.capabilities().contains(NativeFreshSnapshotPort.CAPABILITY)||!hello.capabilities().contains("game.state.snapshot"))
                throw new IOException("identity126 requires its exact current Full HELLO and read capabilities");
            var original=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
            if(!NativeWire.text(original.get("expected_ck3_version")).equals("1.21.0.3"))
                throw new IOException("identity126 HELLO version differs");
        }
        return bound.bridge;
    }
    private org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies.ObservationMode armyObservationMode() {
        return armyIdentity126Source==null
                ?org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies.ObservationMode.RICH
                :org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies.ObservationMode.IDENTITY_ONLY126;
    }

    private static final class Full112Binding {
        final org.xar.ck3.control.platform.ManagedGameSession owner;
        final NativePacketPort endpoint;
        final ExactRef bridge;
        final org.xar.ck3.control.build.SharedSourceFiles.Witness artifact;
        Full112Binding(org.xar.ck3.control.platform.ManagedGameSession owner,NativePacketPort endpoint,ExactRef bridge,
                org.xar.ck3.control.build.SharedSourceFiles.Witness artifact) {
            this.owner=owner;this.endpoint=endpoint;this.bridge=bridge;this.artifact=artifact;
        }
    }
    private Full112Binding full112Source;
    private static final class Full114Binding {
        final org.xar.ck3.control.platform.ManagedGameSession owner;
        final NativePacketPort endpoint;
        final ExactRef bridge;
        final org.xar.ck3.control.build.SharedSourceFiles.Witness artifact;
        Full114Binding(org.xar.ck3.control.platform.ManagedGameSession owner,NativePacketPort endpoint,ExactRef bridge,
                org.xar.ck3.control.build.SharedSourceFiles.Witness artifact) {
            this.owner=owner;this.endpoint=endpoint;this.bridge=bridge;this.artifact=artifact;
        }
    }
    private Full114Binding full114Source;
    /**
     * Explicit independent Native114 source custody; never selected by nativeTransport().
     * This binds the same wire Full profile to different exact artifact bytes, not a
     * runtime count or speed effect. Existing different-speed and mapped112 SAVE
     * checks remain unchanged; no Opening or additional domain permission is created.
     */
    public synchronized Optional<ExactRef> bindFull114Source(org.xar.ck3.control.platform.ManagedGameSession owner)throws IOException {
        requireSourceMode(NativeSourceMode.DEFAULT_CONTROL);
        Objects.requireNonNull(owner).requireNativeTransport(this);
        if(full112Source!=null)
            throw new IOException("independent114 source cannot replace an already bound corrected112 source");
        if(full114Source!=null&&full114Source.owner!=owner)
            throw new IOException("independent114 source cannot be borrowed by another managed owner");
        var selected=owner.launchPlan().sources().review().bridgeDll();
        var bridge=new ExactRef(selected.path(),selected.bytes(),selected.sha256());
        if(!Native114SourceProfile.matchesBridge(bridge)) {
            if(full114Source!=null)throw new IOException("bound independent114 source selection changed");
            return Optional.empty();
        }
        requireFull114Owner(owner,bridge);
        if(full114Source!=null) {
            if(full114Source.endpoint!=endpoint||!full114Source.bridge.equals(bridge))
                throw new IOException("independent114 source already belongs to another original endpoint/artifact");
            org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(full114Source.artifact);
            return Optional.of(bridge);
        }
        var witness=org.xar.ck3.control.build.SharedSourceFiles.observe(java.nio.file.Path.of(bridge.path()));
        if(witness.source().bytes()!=bridge.bytes()||!witness.source().sha256().equals(bridge.sha256()))
            throw new IOException("independent114 selected artifact bytes differ");
        beginSourceBinding(NativeSourceMode.DEFAULT_CONTROL);
        full114Source=new Full114Binding(owner,endpoint,bridge,witness);
        commitSourceBinding(NativeSourceMode.DEFAULT_CONTROL);
        return Optional.of(bridge);
    }
    private void requireFull114Owner(org.xar.ck3.control.platform.ManagedGameSession owner,ExactRef bridge)throws IOException {
        owner.requireNativeTransport(this);var plan=owner.launchPlan();var selected=plan.sources().review().bridgeDll();
        if(!owner.generation().equals(config.game())||!owner.machineId().equals(config.machineId())||!owner.sessionId().equals(config.sessionId())
                ||!plan.pipeName().equals(config.pipeName())||!plan.bridgeVersion().equals(config.expectedBridgeVersion())
                ||!plan.adapterId().equals(config.expectedAdapterId())
                ||!plan.adapterId().equals(ExactCk3Build.CK3_121003_STEAM_26785313_FULL111.coreFullAdapterId())
                ||!plan.sources().review().gameExecutable().sha256().equalsIgnoreCase(ExactCk3Build.CK3_121003_STEAM_26785313.executableSha256())
                ||!bridge.equals(new ExactRef(selected.path(),selected.bytes(),selected.sha256()))
                ||!Native114SourceProfile.matchesBridge(bridge))
            throw new IOException("independent114 source crossed its actual managed Game/machine/session/endpoint/selection");
    }
    private ExactRef requireFull114Source()throws IOException {
        var bound=full114Source;
        if(closed||terminalFailure!=null||bound==null||bound.endpoint!=endpoint||full112Source!=null)
            throw new IOException("independent114 explicit Managed source is not bound or current");
        verifyEndpoint();requireFull114Owner(bound.owner,bound.bridge);
        org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(bound.artifact);
        return bound.bridge;
    }
    /** Independent source/owner binding, never borrowed from Army permission or an action ticket.
     * Only the opaque actual Managed owner can bind; no artifact-only software binding exists. */
    public synchronized Optional<ExactRef> bindFull112Source(org.xar.ck3.control.platform.ManagedGameSession owner)throws IOException {
        requireSourceMode(NativeSourceMode.DEFAULT_CONTROL);
        Objects.requireNonNull(owner).requireNativeTransport(this);
        if(full112Source!=null&&full112Source.owner!=owner)
            throw new IOException("corrected112 source cannot be borrowed by another managed owner");
        var selected=owner.launchPlan().sources().review().bridgeDll();
        var bridge=new ExactRef(selected.path(),selected.bytes(),selected.sha256());
        if(!FullSnapshotClockControl.isMappedSave112Bridge(bridge)) {
            if(full112Source!=null)throw new IOException("bound corrected112 source selection changed");
            return Optional.empty();
        }
        if(full114Source!=null)throw new IOException("corrected112 cannot replace an explicitly bound independent114 source");
        requireFull112Owner(owner,bridge);
        if(full112Source!=null) {
            if(full112Source.owner!=owner||full112Source.endpoint!=endpoint||!full112Source.bridge.equals(bridge))
                throw new IOException("corrected112 source already belongs to another original owner/endpoint");
            org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(full112Source.artifact);return Optional.of(bridge);
        }
        var witness=org.xar.ck3.control.build.SharedSourceFiles.observe(java.nio.file.Path.of(bridge.path()));
        if(witness.source().bytes()!=bridge.bytes()||!witness.source().sha256().equals(bridge.sha256()))
            throw new IOException("corrected112 selected artifact bytes differ");
        beginSourceBinding(NativeSourceMode.DEFAULT_CONTROL);
        full112Source=new Full112Binding(owner,endpoint,bridge,witness);
        commitSourceBinding(NativeSourceMode.DEFAULT_CONTROL);return Optional.of(bridge);
    }
    private void requireFull112Owner(org.xar.ck3.control.platform.ManagedGameSession owner,ExactRef bridge)throws IOException {
        owner.requireNativeTransport(this);var plan=owner.launchPlan();var selected=plan.sources().review().bridgeDll();
        if(!owner.generation().equals(config.game())||!owner.machineId().equals(config.machineId())||!owner.sessionId().equals(config.sessionId())
                ||!plan.pipeName().equals(config.pipeName())||!plan.bridgeVersion().equals(config.expectedBridgeVersion())
                ||!plan.adapterId().equals(config.expectedAdapterId())
                ||!plan.adapterId().equals(ExactCk3Build.CK3_121003_STEAM_26785313_FULL111.coreFullAdapterId())
                ||!plan.sources().review().gameExecutable().sha256().equalsIgnoreCase(ExactCk3Build.CK3_121003_STEAM_26785313.executableSha256())
                ||!bridge.equals(new ExactRef(selected.path(),selected.bytes(),selected.sha256()))
                ||!FullSnapshotClockControl.isMappedSave112Bridge(bridge))
            throw new IOException("corrected112 source crossed its actual managed Game/machine/session/endpoint/selection");
    }
    private ExactRef requireFull112Source()throws IOException {
        var bound=full112Source;
        if(closed||terminalFailure!=null||bound==null||bound.endpoint!=endpoint)
            throw new IOException("corrected112 independent actual Managed source is not bound or current");
        verifyEndpoint();requireFull112Owner(bound.owner,bound.bridge);
        org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(bound.artifact);
        return bound.bridge;
    }
    public synchronized Optional<ExactRef> bindMappedSave112(org.xar.ck3.control.platform.ManagedGameSession owner)throws IOException {
        var selected=bindFull112Source(owner);if(selected.isEmpty())return Optional.empty();
        return Optional.of(requireMappedSave112());
    }
    private ExactRef requireMappedSave112()throws IOException {
        var bridge=requireFull112Source();
        if(requireFlorinFullClockSource()!=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111
                ||!hello.capabilities().contains("game.command.save-checkpoint"))
            throw new IOException("mapped112 SAVE requires its exact managed Full source and advertised SAVE capability");
        return bridge;
    }
    private static boolean supportedArmyReadonlyBridge(ExactRef ref){
        return ref!=null&&((ref.bytes()==13734912L&&ref.sha256().equals("cb98305c1eb99782cbce07e60f41800f798e155feda21754cda2caff8e8b889f"))
                ||(ref.bytes()==13761536L&&ref.sha256().equals("d9cb12a0e634e517ce6f72d9698e4ea9ab72fc3df606e8fcf34d3fee58c6805f")));
    }
    private static org.xar.ck3.control.build.SharedSourceFiles.Witness armyReadonlyArtifact(ExactRef ref)throws IOException {
        if(!supportedArmyReadonlyBridge(ref))throw new IOException("independent exact75/92 Army readonly source required");
        var witness=org.xar.ck3.control.build.SharedSourceFiles.observe(java.nio.file.Path.of(ref.path()));var file=witness.source();
        if(file.bytes()!=ref.bytes()||!file.sha256().equals(ref.sha256()))throw new IOException("Army readonly original artifact changed");
        return witness;
    }
    /** Source selection/custody, not a loaded-module-byte attestation or SAVE/action permission.
     * Natural registered readonlyMain is legal: no executing-action ticket is required here. */
    public synchronized Optional<ExactRef> bindArmyReadonlySource(org.xar.ck3.control.platform.ManagedGameSession owner)throws IOException {
        requireSourceMode(NativeSourceMode.DEFAULT_CONTROL);
        Objects.requireNonNull(owner).requireNativeTransport(this);
        if(!owner.generation().equals(config.game())||!owner.machineId().equals(config.machineId())||!owner.sessionId().equals(config.sessionId()))
            throw new IOException("Army readonly source crossed its actual managed endpoint identity");
        var selected=owner.launchPlan().sources().review().bridgeDll();var bridge=new ExactRef(selected.path(),selected.bytes(),selected.sha256());
        if(!supportedArmyReadonlyBridge(bridge))return Optional.empty();
        if(armyReadonlySource!=null){
            if(armyReadonlySource.owner!=owner||!armyReadonlySource.bridge.equals(bridge))throw new IOException("Army readonly source already belongs to another issuer");
            return Optional.of(bridge);
        }
        beginSourceBinding(NativeSourceMode.DEFAULT_CONTROL);
        armyReadonlySource=new ArmyReadonlyBinding(owner,null,bridge,armyReadonlyArtifact(bridge));
        commitSourceBinding(NativeSourceMode.DEFAULT_CONTROL);return Optional.of(bridge);
    }
    /** Existing package-private software-port test boundary only. No Managed/Root/receipt is fabricated.
     * A live NativePipeEndpoint can never obtain this artifact-only NoGame fixture binding. */
    synchronized void bindArmyReadonlySoftwareSource(NativePacketPort original,ExactRef actualArtifact)throws IOException {
        requireSourceMode(NativeSourceMode.DEFAULT_CONTROL);
        if(endpoint!=Objects.requireNonNull(original)||endpoint instanceof NativePipeEndpoint||armyReadonlySource!=null)
            throw new IOException("Army artifact fixture requires the identical non-live software endpoint");
        beginSourceBinding(NativeSourceMode.DEFAULT_CONTROL);
        armyReadonlySource=new ArmyReadonlyBinding(null,original,actualArtifact,armyReadonlyArtifact(actualArtifact));
        commitSourceBinding(NativeSourceMode.DEFAULT_CONTROL);
    }
    private void requireArmyReadonlySource()throws IOException {
        var bound=armyReadonlySource;if(bound==null)throw new IOException("nonempty Army Full requires an independently bound readonly source");
        verifyEndpoint();
        if(requireFlorinFullClockSource()!=ExactCk3Build.CK3_1210_STEAM_26757580)
            throw new IOException("Army readonly Full requires the exact BB3 read HELLO");
        if(bound.owner!=null){
            bound.owner.requireNativeTransport(this);var selected=bound.owner.launchPlan().sources().review().bridgeDll();
            if(!bound.owner.generation().equals(config.game())||!bound.owner.machineId().equals(config.machineId())
                    ||!bound.owner.sessionId().equals(config.sessionId())
                    ||!bound.bridge.equals(new ExactRef(selected.path(),selected.bytes(),selected.sha256())))
                throw new IOException("Army readonly source lost its current managed Game/session/selection");
        }else if(bound.softwareEndpoint!=endpoint||endpoint instanceof NativePipeEndpoint)
            throw new IOException("Army NoGame source escaped its identical software endpoint");
        if(!supportedArmyReadonlyBridge(bound.bridge))throw new IOException("Army readonly source profile changed");
        org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(bound.artifact);
    }

    private org.xar.ck3.control.platform.ManagedGameSession mappedSave61Owner;
    private org.xar.ck3.control.contracts.ExactRef mappedSave61Bridge;

    /** Bind only the identical opaque managed Game's selected DLL. A HELLO capability alone cannot opt in. */
    public synchronized Optional<org.xar.ck3.control.contracts.ExactRef> bindMappedSave61(
            org.xar.ck3.control.platform.ManagedGameSession owner)throws IOException {
        Objects.requireNonNull(owner);owner.verify();
        if(owner.nativeTransport()!=this || !owner.generation().equals(config.game())
                || !owner.machineId().equals(config.machineId()) || !owner.sessionId().equals(config.sessionId()))
            throw new IOException("mapped SAVE61 requires this identical managed Game/transport/session");
        var selected=owner.launchPlan().sources().review().bridgeDll();
        var bridge=new org.xar.ck3.control.contracts.ExactRef(selected.path(),selected.bytes(),selected.sha256());
        if(!FullSnapshotClockControl.isMappedSave61Bridge(bridge))return Optional.empty();
        if(mappedSave61Owner!=null && mappedSave61Owner!=owner)
            throw new IOException("mapped SAVE61 is already bound to another managed owner");
        if(requireFlorinFullClockSource()!=ExactCk3Build.CK3_1210_STEAM_26757580
                || !hello.capabilities().contains("game.command.save-checkpoint"))
            throw new IOException("mapped SAVE61 requires its exact BB3 HELLO and advertised SAVE capability");
        mappedSave61Owner=owner;mappedSave61Bridge=bridge;
        return Optional.of(requireMappedSave61());
    }
    private org.xar.ck3.control.contracts.ExactRef requireMappedSave61()throws IOException {
        var owner=mappedSave61Owner;var bridge=mappedSave61Bridge;
        if(owner==null || bridge==null)throw new IOException("mapped SAVE61 actual managed source is not installed");
        owner.verify();verifyEndpoint();
        var selected=owner.launchPlan().sources().review().bridgeDll();
        var current=new org.xar.ck3.control.contracts.ExactRef(selected.path(),selected.bytes(),selected.sha256());
        if(owner.nativeTransport()!=this || !owner.generation().equals(config.game())
                || !owner.sessionId().equals(config.sessionId()) || !owner.machineId().equals(config.machineId())
                || !current.equals(bridge) || !FullSnapshotClockControl.isMappedSave61Bridge(current)
                || requireFlorinFullClockSource()!=ExactCk3Build.CK3_1210_STEAM_26757580
                || !hello.capabilities().contains("game.command.save-checkpoint"))
            throw new IOException("mapped SAVE61 lost its exact managed source, current HELLO or SAVE capability");
        return bridge;
    }
    private boolean hotfixSave(NativeRequest request) {
        return request.step().equals("save-checkpoint") && hello!=null
                && ExactCk3Build.CK3_1210_STEAM_26757580.executableSha256().equalsIgnoreCase(hello.gameSha256());
    }
    private boolean current112Save(NativeRequest request) {
        return request.step().equals("save-checkpoint")&&hello!=null
                &&ExactCk3Build.CK3_121003_STEAM_26785313.executableSha256().equalsIgnoreCase(hello.gameSha256());
    }
    /** Pure DATA check, not a Full occurrence, action ticket or no-dispatch proof. Callers first verify their actual fresh/current source. */
    static void requireCurrent112SpeedData(ExactCk3Build profile,String step,RawJson originalState)throws IOException {
        if(profile!=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111||!step.matches("set-speed-[1-5]"))return;
        var state=NativeWire.object(NativeWire.parse(Objects.requireNonNull(originalState).bytes()));
        int current=NativeWire.integer(state.get("speed"),BigInteger.ONE,BigInteger.valueOf(5)).intValueExact();
        if(current!=Integer.parseInt(step.substring(10)))
            throw new IOException("corrected112 speed change is unqualified; only original same-speed zero-effect submission is supported");
    }
    private void requireCurrent112SpeedForPermit(SubmissionPermit permit,NativeRequest request,Instant deadline)throws IOException {
        if(hello==null||!ExactCk3Build.CK3_121003_STEAM_26785313.executableSha256().equalsIgnoreCase(hello.gameSha256())
                ||!request.step().matches("set-speed-[1-5]"))return;
        var profile=requireFlorinFullClockSource();
        if(!chronologyClock.instant().isBefore(deadline)||!chronologyClock.instant().isBefore(permit.guard().validUntil())
                ||heldSnapshotInvalidated||snapshot==null||acceptedSnapshotFrame==null)
            throw new IOException("corrected112 speed requires its original unexpired fresh Full/current proof");
        requireIdentity(permit.guard().origin());requireRawEvidence(permit.guard());
        acceptedSnapshotRevision(acceptedSnapshotFrame).requireOriginal(acceptedSnapshotFrame);
        if(!acceptedSnapshotFrame.session().equals(session())||!acceptedSnapshotFrame.nativeRevision().equals(permit.expectedRevision()))
            throw new IOException("corrected112 speed crossed its original current Full revision/session");
        requireFullSnapshotBuild(snapshot);
        requireCurrent112SpeedData(profile,request.step(),acceptedSnapshotFrame.state());
    }

    public synchronized NativeWire.Hello originalHello() throws IOException {
        if (hello == null) throw new IOException("original Native hello is unavailable"); return hello;
    }
    public enum PingWriteState { ENTERED, RETURNED, UNKNOWN }
    public record PingFailure(String exceptionType,String message) {
        public PingFailure {StrictJson.text(exceptionType);Objects.requireNonNull(message);}
    }
    /** Original control packet custody only. A returned write is not a received PONG or Driver readiness. */
    public record PingAttempt(TransportSession session,UUID custodyEpoch,ReceivedHello originalHello,String requestId,
            NativeWire.Bytes originalPacket,NativeRequestChronology.Event writeEntered,
            Optional<NativeRequestChronology.Event> writeCompleted,PingWriteState writeState,Optional<PingFailure> failure) {
        public PingAttempt {
            Objects.requireNonNull(session);Objects.requireNonNull(custodyEpoch);Objects.requireNonNull(originalHello);StrictJson.text(requestId);
            Objects.requireNonNull(originalPacket);Objects.requireNonNull(writeEntered);Objects.requireNonNull(writeCompleted);Objects.requireNonNull(writeState);Objects.requireNonNull(failure);
            StrictJson.require(originalHello.original().pid()==session.game().pid()&&originalHello.original().connectionGeneration().equals(session.connectionGeneration()),"original ping crossed held HELLO/session");
            StrictJson.require(writeCompleted.isEmpty()||writeState==PingWriteState.RETURNED,"only an actual returned write has completion chronology");
            writeCompleted.ifPresent(value->StrictJson.require(value.order().compareTo(writeEntered.order())>0&&!value.observedAt().isBefore(writeEntered.observedAt()),"ping write chronology differs"));
            StrictJson.require(writeState!=PingWriteState.ENTERED||writeCompleted.isEmpty()&&failure.isEmpty(),"entered ping cannot invent a completion/failure");
            StrictJson.require(writeState!=PingWriteState.UNKNOWN||failure.isPresent()&&writeCompleted.isEmpty(),"unknown ping needs original transfer failure");
            StrictJson.require(writeState!=PingWriteState.RETURNED||writeCompleted.isPresent()||failure.isPresent(),"returned ping needs chronology or actual post-write failure");
            validatePing(originalPacket.value(),requestId);
        }
    }
    public record HandshakePong(TransportSession session,UUID custodyEpoch,String requestId,ReceivedNotice originalPong,
            NativeRequestChronology.Event received) {
        public HandshakePong {
            Objects.requireNonNull(session);Objects.requireNonNull(custodyEpoch);StrictJson.text(requestId);Objects.requireNonNull(originalPong);Objects.requireNonNull(received);
            validatePong(originalPong,requestId,session.game().pid());
        }
    }
    /** No I/O, no new timestamp and no protocol/public qualification. Missing PONG stays explicit. */
    public record HandshakeDiagnostic(Optional<PingAttempt> attempt,Optional<HandshakePong> pong) {
        public HandshakeDiagnostic {
            Objects.requireNonNull(attempt);Objects.requireNonNull(pong);StrictJson.require(pong.isEmpty()||attempt.isPresent(),"PONG requires its actual original ping");
            pong.ifPresent(value->{PingAttempt original=attempt.orElseThrow();
                StrictJson.require(original.session().equals(value.session())&&original.custodyEpoch().equals(value.custodyEpoch())&&original.requestId().equals(value.requestId())
                        &&value.received().order().compareTo(original.writeEntered().order())>0&&!value.received().observedAt().isBefore(original.writeEntered().observedAt()),"PONG crossed actual original ping/session/order");
                original.writeCompleted().ifPresent(completed->StrictJson.require(value.received().order().compareTo(completed.order())>0&&!value.received().observedAt().isBefore(completed.observedAt()),"PONG predates original completed ping write"));
            });
        }
    }
    /** Sole actual Driver caller invokes this after successful original adoption, never on a refusal branch.
     * This sends no Game action and waits for no PONG/snapshot. Every original attempt is retained and never resent. */
    public synchronized PingAttempt startHandshake(Instant deadline)throws IOException,InterruptedException {
        if (activeCouncilRecovery != null || activeRecoveredSeatMailbox != null) throw new IOException("recovered Council RPC or seat scope cannot start another Native producer");
        open(deadline);if(hello==null)throw new IOException("original held HELLO and successful actual Driver adoption must precede ping");verifyEndpoint();
        if(handshakeAttempt!=null) {
            if(handshakeAttempt.failure().isPresent())throw new IOException("original ping transfer remains failed/unknown; no resend: "+handshakeAttempt.failure().orElseThrow().message());
            return handshakeAttempt;
        }
        String requestId="java-ping-"+UUID.randomUUID().toString().replace("-","");
        ObjectNode request=StrictJson.object();request.put("type","ping");request.put("protocol_version",1);request.put("request_id",requestId);
        byte[] original=NativeWire.packet(StrictJson.canonical(request));var entered=chronologyEvent();
        handshakeAttempt=new PingAttempt(session(),custodyEpoch,new ReceivedHello(hello,helloObservedAt),requestId,new NativeWire.Bytes(original),entered,Optional.empty(),PingWriteState.ENTERED,Optional.empty());
        boolean returned=false;
        try {
            endpoint.writePacket(original,deadline);returned=true;var completed=chronologyEvent();
            handshakeAttempt=new PingAttempt(session(),custodyEpoch,handshakeAttempt.originalHello(),requestId,handshakeAttempt.originalPacket(),entered,Optional.of(completed),PingWriteState.RETURNED,Optional.empty());
            verifyEndpoint();return handshakeAttempt;
        }catch(IOException failure){retainPingFailure(failure,returned);throw failure;}
        catch(InterruptedException interrupted){retainPingFailure(interrupted,returned);throw interrupted;}
        catch(RuntimeException failure){retainPingFailure(failure,returned);throw new IOException("actual original ping transport failed",failure);}
    }
    public synchronized HandshakeDiagnostic handshakeDiagnostics() {
        return new HandshakeDiagnostic(Optional.ofNullable(handshakeAttempt),Optional.ofNullable(handshakePong));
    }
    private void retainPingFailure(Exception failure,boolean returned) {
        retainActualDisconnection(failure);
        PingAttempt original=Objects.requireNonNull(handshakeAttempt);
        handshakeAttempt=new PingAttempt(original.session(),original.custodyEpoch(),original.originalHello(),original.requestId(),original.originalPacket(),
                original.writeEntered(),original.writeCompleted(),returned?PingWriteState.RETURNED:PingWriteState.UNKNOWN,
                Optional.of(new PingFailure(failure.getClass().getName(),failure.getMessage()==null?failure.toString():failure.getMessage())));
        if(terminalFailure==null)terminalFailure="original ping send failed; held Driver connection is unavailable: "+reason(failure);
    }
    private static void validatePing(byte[] original,String requestId) {
        try {
            StrictJson.require(original.length>=5&&original.length<=NativeWire.MAXIMUM_FRAME_BYTES+4,"bounded original ping packet required");
            int length=java.nio.ByteBuffer.wrap(original,0,4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt();
            StrictJson.require(length==original.length-4,"original ping frame length differs");
            ObjectNode row=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(original,4,original.length)));Set<String> names=new HashSet<>();row.fieldNames().forEachRemaining(names::add);
            StrictJson.require(names.equals(Set.of("type","protocol_version","request_id"))&&row.path("type").isTextual()&&row.get("type").textValue().equals("ping")
                    &&NativeWire.integer(row.get("protocol_version"),BigInteger.ONE,BigInteger.ONE).equals(BigInteger.ONE)
                    &&row.path("request_id").isTextual()&&row.get("request_id").textValue().equals(requestId),"exact original ping envelope required");
        }catch(IOException malformed){throw new IllegalArgumentException("invalid original ping DATA",malformed);}
    }
    private static void validatePong(ReceivedNotice original,String requestId,long pid) {
        try {
            NativeWire.Frame decoded=NativeWire.decode(original.original().packet().value());
            StrictJson.require(decoded instanceof NativeWire.Notice notice&&notice.kind()==NativeWire.NoticeKind.PONG
                    &&original.original().kind()==NativeWire.NoticeKind.PONG&&Arrays.equals(notice.payload().value(),original.original().payload().value()),"original PONG DATA differs");
            ObjectNode row=NativeWire.object(NativeWire.parse(original.original().payload().value()));
            StrictJson.require(row.path("request_id").isTextual()&&row.get("request_id").textValue().equals(requestId)
                    &&NativeWire.integer(row.get("pid"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).equals(BigInteger.valueOf(pid)),"PONG original request or actual Game PID differs");
        }catch(IOException malformed){throw new IllegalArgumentException("invalid original PONG DATA",malformed);}
    }
    private void retainHandshakePong(ReceivedNotice notice,NativeRequestChronology.Event received)throws IOException {
        if(handshakeAttempt==null)return;
        ObjectNode row=NativeWire.object(NativeWire.parse(notice.original().payload().value()));
        if(!row.path("request_id").isTextual()||!row.get("request_id").textValue().equals(handshakeAttempt.requestId()))return;
        try {
            var actual=new HandshakePong(session(),custodyEpoch,handshakeAttempt.requestId(),notice,received);
            if(handshakePong!=null&&!Arrays.equals(handshakePong.originalPong().original().packet().value(),notice.original().packet().value()))
                throw new IllegalArgumentException("conflicting original PONG packets for one retained ping");
            if(handshakePong==null)handshakePong=actual;
        }catch(IllegalArgumentException invalid){terminalFailure="original matching PONG identity/custody failed: "+reason(invalid);throw new IOException(terminalFailure,invalid);}
    }
    /** Immutable configured name; reading it neither opens nor reconnects a pipe. */
    public String pipeName() { return config.pipeName(); }
    public synchronized void verifyHeld(Instant deadline) throws IOException {
        open(deadline);
        if (hello == null) throw new IOException("actual original Native hello is required");
        verifyEndpoint();
    }
    /** No I/O and no delivery consumption. A received snapshot has no invented query request ID. */
    public synchronized Optional<ObservedFrame> latestObservedSnapshot() throws IOException {
        if (closed || terminalFailure != null) throw new IOException("held Native session is closed or terminal");
        if (hello == null || snapshot == null) return Optional.empty();
        return Optional.of(Objects.requireNonNull(acceptedSnapshotFrame,"actual accepted snapshot occurrence unavailable"));
    }
    /** Received evidence only: HELLO_VERIFIED is not a fresh process-running or semantic-readiness claim. */
    public enum ReceivedState { NO_HELLO, HELLO_VERIFIED, TERMINAL, CLOSED }
    public record ReceivedNotice(NativeWire.Notice original, Instant observedAt) {
        public ReceivedNotice { Objects.requireNonNull(original); Objects.requireNonNull(observedAt); }
    }
    public record ReceivedHello(NativeWire.Hello original, Instant observedAt) {
        public ReceivedHello { Objects.requireNonNull(original); Objects.requireNonNull(observedAt); }
    }
    public record TransportDiagnostics(ReceivedState receivedState, Optional<TransportSession> session,
            Optional<ReceivedHello> originalHello, Optional<ReceivedNotice> latestHeartbeat,
            Optional<ReceivedNotice> latestPong, Optional<ReceivedNotice> latestError,
            Optional<ReceivedNotice> latestSnapshotDiagnostic, Optional<String> terminalFailure,
            NativeWire.Bytes lastOriginalPacket, Optional<NativeTransportDiagnostics.Production> production) {
        public TransportDiagnostics {
            Objects.requireNonNull(receivedState); Objects.requireNonNull(session); Objects.requireNonNull(originalHello);
            Objects.requireNonNull(latestHeartbeat); Objects.requireNonNull(latestPong); Objects.requireNonNull(latestError);
            Objects.requireNonNull(latestSnapshotDiagnostic); Objects.requireNonNull(terminalFailure); Objects.requireNonNull(lastOriginalPacket);
            Objects.requireNonNull(production);
        }
        /** Historical constructor explicitly has no lifetime producer; it cannot invent four zero/null fields. */
        public TransportDiagnostics(ReceivedState receivedState, Optional<TransportSession> session, Optional<ReceivedHello> originalHello,
                Optional<ReceivedNotice> latestHeartbeat, Optional<ReceivedNotice> latestPong, Optional<ReceivedNotice> latestError,
                Optional<ReceivedNotice> latestSnapshotDiagnostic, Optional<String> terminalFailure, NativeWire.Bytes lastOriginalPacket) {
            this(receivedState,session,originalHello,latestHeartbeat,latestPong,latestError,latestSnapshotDiagnostic,terminalFailure,lastOriginalPacket,Optional.empty());
        }
    }
    /** Does no I/O and invents no mailbox/startup/readiness defaults when the original field is absent. */
    public synchronized TransportDiagnostics diagnostics() {
        ReceivedState state = closed ? ReceivedState.CLOSED : terminalFailure != null ? ReceivedState.TERMINAL
                : hello == null ? ReceivedState.NO_HELLO : ReceivedState.HELLO_VERIFIED;
        return new TransportDiagnostics(state, hello == null ? Optional.empty() : Optional.of(session()),
                hello == null ? Optional.empty() : Optional.of(new ReceivedHello(hello, helloObservedAt)),
                Optional.ofNullable(latestHeartbeat), Optional.ofNullable(latestPong), Optional.ofNullable(latestError),
                Optional.ofNullable(latestSnapshotDiagnostic), Optional.ofNullable(terminalFailure), new NativeWire.Bytes(lastOriginalPacket),
                diagnosticAccountingAvailable ? Optional.of(new NativeTransportDiagnostics.Production(custodyEpoch,hello == null ? Optional.empty() : Optional.of(session()),
                        receivedSnapshotCount,rejectedSnapshotCount,Optional.ofNullable(lastRejectedSnapshot),snapshotPublishDiagnosticCount,
                        Optional.ofNullable(lastReceivedSnapshot),adoptionDiagnostic)) : Optional.empty());
    }
    /** Called only by the actual Driver adopter after its original successful adoption, never by diagnostics. */
    public synchronized void recordAdoptionObserved() throws IOException {
        if (hello == null || closed || terminalFailure != null) throw new IOException("actual successful held Driver adoption is unavailable");
        if (adoptionDiagnostic instanceof NativeTransportDiagnostics.Observed observed && observed.refusal().isPresent())
            throw new IOException("original Driver adoption refusal is terminal and cannot become known null");
        adoptionDiagnostic = new NativeTransportDiagnostics.Observed(Optional.empty());
    }
    /** Typed original adoption failure only. Generic I/O/source failures must remain outside transport_refusal. */
    public synchronized void recordAdoptionRefused(NativeTransportDiagnostics.AdoptionRefusalReason reason, String exceptionType, String message) throws IOException {
        if (hello == null || closed) throw new IOException("original HELLO required before recording a Driver adoption refusal");
        if (adoptionDiagnostic instanceof NativeTransportDiagnostics.Observed observed && observed.refusal().isPresent()) return;
        if (terminalFailure != null) throw new IOException("an earlier terminal transport failure cannot be reclassified as Driver adoption refusal");
        var refusal = new NativeTransportDiagnostics.AdoptionRefusal(session(),new ReceivedHello(hello,helloObservedAt),reason,exceptionType,message);
        adoptionDiagnostic = new NativeTransportDiagnostics.Observed(Optional.of(refusal));
        terminalFailure = message;
    }
    public sealed interface CoreRead permits CoreReceived,CoreReadUnavailable {
        DispatchOutcome original();
    }
    /** A real core ACK occurrence from this held receiver; public CoreFrame DATA cannot construct it. */
    public static final class CoreReceived implements CoreRead {
        private final NativeGameTransport issuer;
        private final CoreFrame frame;
        private final AckReceived original;
        private final NativeRequestChronology custody;
        private final Instant validUntil;
        private boolean controlAttempted;
        private boolean guiRootIndexReadAttempted;
        private GuiRootIndexReadUnavailable unresolvedGuiRootIndexRead;
        private boolean guiWindowReadAttempted;
        private GuiWindowReadUnavailable unresolvedGuiWindowRead;
        private boolean riteDraftCostsReadAttempted;
        private RiteDraftCostsReadUnavailable unresolvedRiteDraftCostsRead;
        private boolean riteDoctrineReadAttempted;
        private RiteDoctrineReadUnavailable unresolvedRiteDoctrineRead;
        private boolean guiControlsReadAttemptedV2;
        private GuiControlsReadUnavailableV2 unresolvedGuiControlsReadV2;
        private CoreReceived(NativeGameTransport issuer,CoreFrame frame,AckReceived original,
                NativeRequestChronology custody,Instant validUntil) {
            this.issuer=issuer;this.frame=frame;this.original=original;this.custody=custody;this.validUntil=validUntil;
        }
        public CoreFrame frame(){return frame;}
        @Override public AckReceived original(){return original;}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actualHeld,Instant operationDeadline)throws IOException {
            Objects.requireNonNull(actualHeld).requireCoreOriginal(this,operationDeadline);
        }
    }
    /** Keeps the actual returned ACK/UNKNOWN/zero-dispatch evidence without manufacturing a different outcome. */
    public record CoreReadUnavailable(DispatchOutcome original,String reason) implements CoreRead {
        public CoreReadUnavailable {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    public sealed interface GuiRootIndexRead permits GuiRootIndexReceived, GuiRootIndexReadUnavailable {
        DispatchOutcome original();
    }
    /** Redacted read DATA from this receiver; never a complete GUI frame or control permit. */
    public static final class GuiRootIndexReceived implements GuiRootIndexRead {
        private final NativeGameTransport issuer;
        private final CoreReceived before;
        private final GuiRootIndexFrame frame;
        private final AckReceived original;
        private final NativeRequestChronology custody;
        private final Instant validUntil;
        private GuiRootIndexReceived(NativeGameTransport issuer, CoreReceived before, GuiRootIndexFrame frame,
                AckReceived original, NativeRequestChronology custody, Instant validUntil) {
            this.issuer=issuer;this.before=before;this.frame=frame;this.original=original;this.custody=custody;this.validUntil=validUntil;
        }
        public GuiRootIndexFrame frame(){return frame;}
        @Override public AckReceived original(){return original;}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual, Instant deadline)throws IOException {
            Objects.requireNonNull(actual).requireGuiRootIndexOriginal(this,deadline);
        }
    }
    public record GuiRootIndexReadUnavailable(DispatchOutcome original,String reason) implements GuiRootIndexRead {
        public GuiRootIndexReadUnavailable {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    /** Expected Core can only be the identical transport's original CoreReceived, never configuration DATA. */
    public synchronized GuiRootIndexRead readGuiRootIndexReceived(CoreReceived before, Instant deadline)throws InterruptedException {
        if(before!=null&&before.issuer==this&&before.unresolvedGuiRootIndexRead!=null)return before.unresolvedGuiRootIndexRead;
        String id="gui-root-index-"+UUID.randomUUID().toString().replace("-","");
        DispatchOutcome original;Instant until=deadline;
        try {
            Objects.requireNonNull(before);Objects.requireNonNull(deadline);before.requireOriginal(this,deadline);
            if(applicationExitAttempted||before.controlAttempted||before.guiRootIndexReadAttempted||unresolvedCoreControl!=null
                    ||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("root-index query requires unused current Core without active or uncertain controls");
            if(!(before.frame instanceof CoreFrame.Partial partial))throw new IOException("root-index requires the actual available Core prefix");
            GuiRootIndexFrame.requireExpectedCore(partial);
            if(!hello.capabilities().contains(CoreFrame.CAPABILITY))throw new IOException("original Core capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            until=readDeadline(deadline);final Instant queryUntil=until;
            var request=GuiRootIndexFramePublicCodec.request(partial,queryUntil);
            byte[] packet=NativeWire.execute(id,GuiRootIndexFrame.STEP,BigInteger.ZERO,GuiRootIndexFramePublicCodec.additionalFields(request).bytes());
            if(!GuiRootIndexFramePublicCodec.decodeRequestPacket(packet).equals(request))throw new IOException("root-index complete outgoing request roundtrip drift");
            original=retainReadOutcome(dispatchRead(id,packet,queryUntil,()->{
                requireBackgroundAtCoreWrite();
                try{before.requireOriginal(this,queryUntil);}catch(IOException invalid){throw new UncheckedIOException(invalid);}
                if(before.controlAttempted||before.guiRootIndexReadAttempted)throw new IllegalStateException("root-index Core source already consumed");
                before.guiRootIndexReadAttempted=true;
            }));
        }catch(IOException|RuntimeException invalid){
            if(sentRequestIds.contains(id))original=new Unknown(id,"root-index failed after actual query write; retain original, never replay: "+reason(invalid),retainedOutbound(id),Optional.empty());
            else original=zero(id,reason(invalid));
        }
        try {
            var frame=GuiRootIndexFramePublicCodec.decodeOutcome(original);var ack=(AckReceived)original;
            var custody=originalRequestChronology(ack.requestId()).orElseThrow(()->new IOException("actual root-index ACK custody unavailable"));
            var received=new GuiRootIndexReceived(this,before,frame,ack,custody,until);
            requireGuiRootIndexOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){
            var unavailable=new GuiRootIndexReadUnavailable(original,reason(invalid));
            if(before!=null&&before.issuer==this&&original instanceof Unknown)before.unresolvedGuiRootIndexRead=unavailable;
            return unavailable;
        }
    }
    private void requireGuiRootIndexOriginal(GuiRootIndexReceived actual,Instant deadline)throws IOException {
        Objects.requireNonNull(deadline);
        if(actual.issuer!=this||hello==null||closed||terminalFailure!=null)throw new IOException("root-index requires its identical live held receiver");
        actual.before.requireOriginal(this,deadline);Instant now=chronologyClock.instant();
        if(!now.isBefore(actual.validUntil)||!now.isBefore(deadline)||deadline.isAfter(actual.validUntil)
                ||actual.custody.responseReceived().observedAt().isAfter(now)||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)
                ||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("root-index escaped its original Core/query chronology");
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)
                ||!actual.before.guiRootIndexReadAttempted||!originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isPresent())
            throw new IOException("root-index crossed its original Game/session/connection/custody");
        actual.custody.verify(actual.original);
        var decoded=GuiRootIndexFramePublicCodec.decodeOutcome(actual.original);
        var outbound=actual.original.outbound().orElseThrow(()->new IOException("root-index original outbound missing"));
        var request=GuiRootIndexFramePublicCodec.decodeRequestPacket(outbound.originalPacket());
        if(!decoded.equals(actual.frame)||!request.expectedCore().equals(actual.before.frame)
                ||!request.deadlineUnixMs().equals(BigInteger.valueOf(actual.validUntil.toEpochMilli())))
            throw new IOException("root-index request/result differs from the identical retained Core or query window");
    }
    public sealed interface RiteDraftCostsRead permits RiteDraftCostsReceived, RiteDraftCostsReadUnavailable {
        DispatchOutcome original();
    }
    /** Redacted read DATA from this receiver; never a complete GUI frame or control permit. */
    public static final class RiteDraftCostsReceived implements RiteDraftCostsRead {
        private final NativeGameTransport issuer;
        private final CoreReceived before;
        private final RiteDraftCostsFrameV2 frame;
        private final AckReceived original;
        private final NativeRequestChronology custody;
        private final Instant validUntil;
        private RiteDraftCostsReceived(NativeGameTransport issuer, CoreReceived before, RiteDraftCostsFrameV2 frame,
                AckReceived original, NativeRequestChronology custody, Instant validUntil) {
            this.issuer=issuer;this.before=before;this.frame=frame;this.original=original;this.custody=custody;this.validUntil=validUntil;
        }
        public RiteDraftCostsFrameV2 frame(){return frame;}
        @Override public AckReceived original(){return original;}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual, Instant deadline)throws IOException {
            Objects.requireNonNull(actual).requireRiteDraftCostsOriginal(this,deadline);
        }
    }
    public record RiteDraftCostsReadUnavailable(DispatchOutcome original,String reason) implements RiteDraftCostsRead {
        public RiteDraftCostsReadUnavailable {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    /** Expected Core can only be the identical transport's original CoreReceived, never configuration DATA. */
    public synchronized RiteDraftCostsRead readRiteDraftCostsReceived(CoreReceived before, long expectedSourceRiteId, Instant deadline)throws InterruptedException {
        if(before!=null&&before.issuer==this&&before.unresolvedRiteDraftCostsRead!=null)return before.unresolvedRiteDraftCostsRead;
        String id="gui-rite-draft-costs-"+UUID.randomUUID().toString().replace("-","");
        DispatchOutcome original;Instant until=deadline;
        try {
            Objects.requireNonNull(before);Objects.requireNonNull(deadline);before.requireOriginal(this,deadline);
            if(applicationExitAttempted||before.controlAttempted||before.riteDraftCostsReadAttempted||unresolvedCoreControl!=null
                    ||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("rite-draft-costs query requires unused current Core without active or uncertain controls");
            if(!(before.frame instanceof CoreFrame.Partial partial))throw new IOException("rite-draft-costs requires the actual available Core prefix");
            GuiRootIndexFrame.requireExpectedCore(partial);RiteDraftCostsFrameV2.sourceRiteId(expectedSourceRiteId);
            if(!hello.capabilities().contains(CoreFrame.CAPABILITY))throw new IOException("original Core capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            until=readDeadline(deadline);final Instant queryUntil=until;
            var request=RiteDraftCostsFrameV2PublicCodec.request(partial,queryUntil,expectedSourceRiteId);
            byte[] packet=NativeWire.execute(id,RiteDraftCostsFrameV2.STEP,BigInteger.ZERO,RiteDraftCostsFrameV2PublicCodec.additionalFields(request).bytes());
            if(!RiteDraftCostsFrameV2PublicCodec.decodeRequestPacket(packet).equals(request))throw new IOException("rite-draft-costs complete outgoing request roundtrip drift");
            original=retainReadOutcome(dispatchRead(id,packet,queryUntil,()->{
                requireBackgroundAtCoreWrite();
                try{before.requireOriginal(this,queryUntil);}catch(IOException invalid){throw new UncheckedIOException(invalid);}
                if(before.controlAttempted||before.riteDraftCostsReadAttempted)throw new IllegalStateException("rite-draft-costs Core source already consumed");
                before.riteDraftCostsReadAttempted=true;
            }));
        }catch(IOException|RuntimeException invalid){
            if(sentRequestIds.contains(id))original=new Unknown(id,"rite-draft-costs failed after actual query write; retain original, never replay: "+reason(invalid),retainedOutbound(id),Optional.empty());
            else original=zero(id,reason(invalid));
        }
        try {
            var frame=RiteDraftCostsFrameV2PublicCodec.decodeOutcome(original);var ack=(AckReceived)original;
            var custody=originalRequestChronology(ack.requestId()).orElseThrow(()->new IOException("actual rite-draft-costs ACK custody unavailable"));
            var received=new RiteDraftCostsReceived(this,before,frame,ack,custody,until);
            requireRiteDraftCostsOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){
            var unavailable=new RiteDraftCostsReadUnavailable(original,reason(invalid));
            if(before!=null&&before.issuer==this&&original instanceof Unknown)before.unresolvedRiteDraftCostsRead=unavailable;
            return unavailable;
        }
    }
    private void requireRiteDraftCostsOriginal(RiteDraftCostsReceived actual,Instant deadline)throws IOException {
        Objects.requireNonNull(deadline);
        if(actual.issuer!=this||hello==null||closed||terminalFailure!=null)throw new IOException("rite-draft-costs requires its identical live held receiver");
        actual.before.requireOriginal(this,deadline);Instant now=chronologyClock.instant();
        if(!now.isBefore(actual.validUntil)||!now.isBefore(deadline)||deadline.isAfter(actual.validUntil)
                ||actual.custody.responseReceived().observedAt().isAfter(now)||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)
                ||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("rite-draft-costs escaped its original Core/query chronology");
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)
                ||!actual.before.riteDraftCostsReadAttempted||!originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isPresent())
            throw new IOException("rite-draft-costs crossed its original Game/session/connection/custody");
        actual.custody.verify(actual.original);
        var decoded=RiteDraftCostsFrameV2PublicCodec.decodeOutcome(actual.original);
        var outbound=actual.original.outbound().orElseThrow(()->new IOException("rite-draft-costs original outbound missing"));
        var request=RiteDraftCostsFrameV2PublicCodec.decodeRequestPacket(outbound.originalPacket());
        if(!decoded.equals(actual.frame)||!request.expectedCore().equals(actual.before.frame)
                ||!request.deadlineUnixMs().equals(BigInteger.valueOf(actual.validUntil.toEpochMilli())))
            throw new IOException("rite-draft-costs request/result differs from the identical retained Core or query window");
    }
    public sealed interface RiteDoctrineRead permits RiteDoctrineReceived,RiteDoctrineReadUnavailable { DispatchOutcome original(); }
    public static final class RiteDoctrineReceived implements RiteDoctrineRead {
        private final NativeGameTransport issuer;private final CoreReceived before;private final RiteDraftCostsReceived draft;
        private final RiteDoctrineFrameV1 frame;private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private boolean actionAttempted;
        private RiteDoctrineReceived(NativeGameTransport issuer,RiteDraftCostsReceived draft,RiteDoctrineFrameV1 frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.before=draft.before;this.draft=draft;this.frame=frame;this.original=original;this.custody=custody;this.validUntil=until;}
        public RiteDoctrineFrameV1 frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant deadline)throws IOException{Objects.requireNonNull(actual).requireRiteDoctrineOriginal(this,deadline);}
    }
    public record RiteDoctrineReadUnavailable(DispatchOutcome original,String reason)implements RiteDoctrineRead {public RiteDoctrineReadUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    private RiteDoctrineReceived latestRiteDoctrineQuery;
    /** Original current Core and actual native draft only; configuration cannot create query authority. */
    public synchronized RiteDoctrineRead readRiteDoctrineReceived(RiteDraftCostsReceived draft,Instant deadline)throws InterruptedException {
        CoreReceived before=draft==null?null:draft.before;
        if(before!=null&&before.issuer==this&&before.unresolvedRiteDoctrineRead!=null)return before.unresolvedRiteDoctrineRead;
        String id="rite-doctrine-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome original;Instant until=deadline;
        try {
            Objects.requireNonNull(draft);Objects.requireNonNull(deadline);draft.requireOriginal(this,deadline);
            if(applicationExitAttempted||before.controlAttempted||before.riteDoctrineReadAttempted||before.guiControlsReadAttemptedV2||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)throw new IOException("current Rite query requires an unused actual Core/draft without uncertain controls");
            if(!(before.frame instanceof CoreFrame.Partial core)||!(draft.frame instanceof RiteDraftCostsFrameV2.Partial source))throw new IOException("actual available same-transport Core/draft required");
            if(!hello.capabilities().contains(RiteDoctrineFrameV1.CAPABILITY))throw new IOException("actual current Rite doctrine capability absent");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            until=readDeadline(deadline);final Instant queryUntil=until;var request=RiteDoctrineFrameV1PublicCodec.query(core,queryUntil,source.draft().sourceRiteId());
            byte[] packet=NativeWire.execute(id,RiteDoctrineFrameV1.STEP,BigInteger.ZERO,RiteDoctrineFrameV1PublicCodec.additionalFields(request).bytes());
            if(!RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(packet).equals(request))throw new IOException("complete current Rite query roundtrip drift");
            original=retainReadOutcome(dispatchRead(id,packet,queryUntil,()->{requireBackgroundAtCoreWrite();try{draft.requireOriginal(this,queryUntil);}catch(IOException invalid){throw new UncheckedIOException(invalid);}if(before.controlAttempted||before.riteDoctrineReadAttempted)throw new IllegalStateException("original Rite Core query consumed");before.riteDoctrineReadAttempted=true;latestRiteDoctrineQuery=null;}));
        }catch(IOException|RuntimeException invalid){original=sentRequestIds.contains(id)?new Unknown(id,"current Rite query failed after write; preserve original, no replay: "+reason(invalid),retainedOutbound(id),Optional.empty()):zero(id,reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;original=new Unknown(id,"current Rite query interrupted after write; no replay",retainedOutbound(id),Optional.empty());Thread.currentThread().interrupt();}
        try {
            var frame=RiteDoctrineFrameV1PublicCodec.decodeOutcome(original);var ack=(AckReceived)original;
            if(frame.status()!=RiteDoctrineFrameV1.Status.AVAILABLE)throw new IOException("actual current Rite facts unavailable: "+frame.status().wire());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("actual current Rite query custody absent"));
            var received=new RiteDoctrineReceived(this,draft,frame,ack,custody,until);latestRiteDoctrineQuery=received;requireRiteDoctrineOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){latestRiteDoctrineQuery=null;var unavailable=new RiteDoctrineReadUnavailable(original,reason(invalid));if(before!=null&&before.issuer==this&&original instanceof Unknown)before.unresolvedRiteDoctrineRead=unavailable;return unavailable;}
    }
    private void requireRiteDoctrineOriginal(RiteDoctrineReceived actual,Instant deadline)throws IOException {
        Objects.requireNonNull(deadline);
        if(actual.issuer!=this||actual!=latestRiteDoctrineQuery||closed||terminalFailure!=null||applicationExitAttempted||actual.actionAttempted||actual.before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null)throw new IOException("actual unused current Rite query unavailable");
        actual.draft.requireOriginal(this,deadline);Instant now=chronologyClock.instant();
        if(!now.isBefore(deadline)||!now.isBefore(actual.validUntil)||deadline.isAfter(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.draft.custody.responseReceived().order())<=0)throw new IOException("Rite query escaped original Core/draft/deadline chronology");
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)||!originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isPresent())throw new IOException("Rite query crossed actual Game/session/connection/custody");
        actual.custody.verify(actual.original);var frame=RiteDoctrineFrameV1PublicCodec.decodeOutcome(actual.original);
        var request=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(actual.original.outbound().orElseThrow().originalPacket());var draft=((RiteDraftCostsFrameV2.Partial)actual.draft.frame).draft();
        if(!frame.equals(actual.frame)||request.action()!=RiteDoctrineFrameV1.Action.QUERY||!request.expectedCore().equals(actual.before.frame)||request.sourceRiteId()!=draft.sourceRiteId()||!request.deadlineUnixMs().equals(BigInteger.valueOf(actual.validUntil.toEpochMilli())))throw new IOException("Rite query differs from original Core/draft/source");
        var facts=frame.facts().orElseThrow();if(facts.sourceRiteId()!=draft.sourceRiteId()||facts.pietyCostRaw()!=draft.pietyCostRaw()||facts.pietyMissingSignedRaw()!=draft.pietyMissingSignedRaw()||facts.canEditEvaluated()&&facts.canEdit()!=draft.canEditRiteNative())throw new IOException("Rite source changed between actual draft and query");
    }
    /** Exactly one fixed effect from this receiver's private current query; no caller keys, pointers or ordinals. */
    public synchronized DispatchOutcome submitRiteDoctrineAction(RiteDoctrineReceived query,RiteDoctrineFrameV1.Action action,Instant deadline)throws InterruptedException {
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        String id="rite-doctrine-action-"+UUID.randomUUID().toString().replace("-","");
        try {
            Objects.requireNonNull(query);Objects.requireNonNull(action);requireRiteDoctrineOriginal(query,deadline);
            if(activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null||action==RiteDoctrineFrameV1.Action.QUERY)throw new IOException("fixed Rite effect cannot borrow another mailbox or query mode");
            var facts=query.frame.facts().orElseThrow();
            boolean admitted=switch(action){case QUERY->false;case OPEN_DYNASTIC_CATEGORY->facts.categoryAvailable();case SELECT_DYNASTIC->facts.selectable();case CONFIRM_EDIT->facts.confirmable();case QUERY_FINAL_CONFIRMATION,ACCEPT_FINAL_CONFIRMATION->false;};
            if(!admitted)throw new IOException("current fixed Rite effect lacks its actual evaluated prerequisites; known false is not an entire PAM OR evaluation");
            if(!hello.capabilities().contains(RiteDoctrineFrameV1.CAPABILITY))throw new IOException("actual current Rite doctrine capability absent");if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
            var original=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(query.original.outbound().orElseThrow().originalPacket());
            var request=RiteDoctrineFrameV1PublicCodec.action(original,action,deadline,new RiteDoctrineFrameV1PublicCodec.Lease(query.frame.providerGeneration(),query.frame.querySequence()));
            byte[] packet=NativeWire.execute(id,RiteDoctrineFrameV1.STEP,BigInteger.ZERO,RiteDoctrineFrameV1PublicCodec.additionalFields(request).bytes());
            if(!RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(packet).equals(request))throw new IOException("complete current Rite effect roundtrip drift");
            var outcome=dispatch(id,packet,deadline,()->{requireBackgroundAtCoreWrite();try{requireRiteDoctrineOriginal(query,deadline);}catch(IOException invalid){throw new UncheckedIOException(invalid);}if(query.actionAttempted||query.before.controlAttempted)throw new IllegalStateException("current Rite claim consumed");query.actionAttempted=true;query.before.controlAttempted=true;heldSnapshotInvalidated=true;latestRiteDoctrineQuery=null;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return unknown;}
            if(outcome instanceof AckReceived ack){
                try{var frame=RiteDoctrineFrameV1PublicCodec.decodeOutcome(ack);if(frame.status()==RiteDoctrineFrameV1.Status.INDETERMINATE){indeterminateCoreAcknowledgement=ack;unresolvedCoreControl=new Unknown(id,"current Rite callback indeterminate; retain original ACK and never replay",packet,Optional.of(ack.originalFrame()));return unresolvedCoreControl;}if(action==RiteDoctrineFrameV1.Action.CONFIRM_EDIT&&frame.status()==RiteDoctrineFrameV1.Status.CONFIRMATION_DISPATCHED)pendingRiteFinal=new RiteFinalPending(this,query,request,ack);}
                catch(IOException|RuntimeException malformed){indeterminateCoreAcknowledgement=ack;unresolvedCoreControl=new Unknown(id,"current Rite written result cannot be qualified; retain original and never replay: "+reason(malformed),packet,Optional.of(ack.originalFrame()));return unresolvedCoreControl;}
            }
            return outcome;
        }catch(IOException|RuntimeException invalid){if(sentRequestIds.contains(id)){unresolvedCoreControl=new Unknown(id,"current Rite effect failed after write; no replay: "+reason(invalid),retainedOutbound(id),Optional.empty());return unresolvedCoreControl;}return zero(id,reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;unresolvedCoreControl=new Unknown(id,"current Rite effect interrupted after write; no replay",retainedOutbound(id),Optional.empty());Thread.currentThread().interrupt();return unresolvedCoreControl;}
    }

    /** Private Stage1 occurrence. A configured boolean or a replayed public ACK cannot construct it. */
    public static final class RiteFinalPending {
        private final NativeGameTransport issuer;private final RiteDoctrineReceived query;
        private final RiteDoctrineFrameV1PublicCodec.Request stageOneRequest;
        private final AckReceived stageOne;private final Instant deadline;
        private RiteFinalReady latestReady;private RiteFinalPrepared prepared;
        private boolean finalAttempted;
        private RiteFinalPending(NativeGameTransport issuer,RiteDoctrineReceived query,
                RiteDoctrineFrameV1PublicCodec.Request request,AckReceived stageOne) {
            this.issuer=issuer;this.query=query;this.stageOneRequest=request;this.stageOne=stageOne;
            this.deadline=Instant.ofEpochMilli(request.deadlineUnixMs().longValueExact());
        }
        public AckReceived original(){return stageOne;}
        public Instant deadline(){return deadline;}
    }
    public sealed interface RiteFinalRead permits RiteFinalReady,RiteFinalWaiting,RiteFinalUnavailable {DispatchOutcome original();}
    /** Known asynchronous preparation only; this type has no conversion into final write authority. */
    public static final class RiteFinalWaiting implements RiteFinalRead {
        private final RiteDoctrineFrameV1 frame;private final AckReceived original;private final Instant validUntil;
        private RiteFinalWaiting(RiteDoctrineFrameV1 frame,AckReceived original,Instant validUntil){this.frame=frame;this.original=original;this.validUntil=validUntil;}
        public RiteDoctrineFrameV1 frame(){return frame;}
        @Override public AckReceived original(){return original;}
        public Instant validUntil(){return validUntil;}
    }
    public static final class RiteFinalReady implements RiteFinalRead {
        private final NativeGameTransport issuer;private final RiteFinalPending pending;
        private final RiteDoctrineFrameV1 frame;private final AckReceived original;
        private final NativeRequestChronology custody;private final Instant validUntil;
        private RiteFinalReady(NativeGameTransport issuer,RiteFinalPending pending,RiteDoctrineFrameV1 frame,
                AckReceived original,NativeRequestChronology custody,Instant until) {
            this.issuer=issuer;this.pending=pending;this.frame=frame;this.original=original;this.custody=custody;this.validUntil=until;
        }
        public RiteDoctrineFrameV1 frame(){return frame;}
        @Override public AckReceived original(){return original;}
        public Instant validUntil(){return validUntil;}
    }
    public record RiteFinalUnavailable(DispatchOutcome original,String reason)implements RiteFinalRead {
        public RiteFinalUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    public static final class RiteFinalPrepared {
        private final NativeGameTransport issuer;private final RiteFinalReady ready;private final String id;
        private final NativeWire.Bytes packet;private boolean called;private DispatchOutcome outcome;
        private RiteFinalPrepared(NativeGameTransport issuer,RiteFinalReady ready,String id,byte[] packet){this.issuer=issuer;this.ready=ready;this.id=id;this.packet=new NativeWire.Bytes(packet);}
        public String requestId(){return id;}
        public Instant deadline(){return ready.pending.deadline;}
        public NativeWire.Bytes originalPacket(){return packet;}
    }
    private RiteFinalPending pendingRiteFinal;
    /** New workflow checks the actual final capability before opening a modal; legacy v16 stays Stage1-only. */
    public synchronized DispatchOutcome submitRiteFinalOpening(RiteDoctrineReceived query,Instant deadline)throws InterruptedException {
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;
        if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        if(hello==null||!hello.capabilities().contains(RiteDoctrineFrameV1.FINAL_CAPABILITY))
            return zero("rite-final-open-"+UUID.randomUUID().toString().replace("-",""),"Actual final confirmation capability absent; modal was not opened");
        if(pendingRiteFinal!=null)return zero("rite-final-open-"+UUID.randomUUID().toString().replace("-",""),"Original final-confirmation preparation retained; no second modal");
        return submitRiteDoctrineAction(query,RiteDoctrineFrameV1.Action.CONFIRM_EDIT,deadline);
    }
    public synchronized RiteFinalPending retainRiteFinalPreparation(AckReceived actualStageOne)throws IOException {
        if(pendingRiteFinal==null||pendingRiteFinal.stageOne!=actualStageOne)throw new IOException("Identical actual Stage1 ACK from this receiver required");
        requireRiteFinalPending(pendingRiteFinal,pendingRiteFinal.deadline);return pendingRiteFinal;
    }
    private void requireRiteFinalPending(RiteFinalPending pending,Instant until)throws IOException {
        if(pending==null||pending.issuer!=this||pendingRiteFinal!=pending||closed||hello==null||terminalFailure!=null
                ||applicationExitAttempted||pending.finalAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null
                ||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
            throw new IOException("Original pending final confirmation unavailable or consumed");
        if(!hello.capabilities().contains(RiteDoctrineFrameV1.FINAL_CAPABILITY))throw new IOException("Actual final confirmation capability absent");
        Instant now=chronologyClock.instant();
        if(!now.isBefore(until)||!now.isBefore(pending.deadline)||until.isAfter(pending.deadline))throw new IOException("Final confirmation cannot refresh Stage1 deadline");
        requireCoreOriginal(pending.query.before,until);pending.query.draft.requireOriginal(this,until);
        if(!pending.query.actionAttempted||!pending.query.before.controlAttempted)throw new IOException("Actual Stage1 write was not consumed");
        var custody=pending.stageOne.custody().orElseThrow(()->new IOException("Actual Stage1 ACK custody absent"));custody.verify(pending.stageOne);
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)
                ||originalRequestChronology(pending.stageOne.requestId()).filter(custody::equals).isEmpty()
                ||custody.writeEntered().order().compareTo(pending.query.custody.responseReceived().order())<=0
                ||custody.responseReceived().observedAt().isAfter(now)||custody.responseReceived().observedAt().isAfter(pending.deadline))
            throw new IOException("Stage1 final source crossed its original session/custody/deadline");
        var actual=RiteDoctrineFrameV1PublicCodec.decodeOutcome(pending.stageOne);
        var request=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(pending.stageOne.outbound().orElseThrow().originalPacket());
        if(!request.equals(pending.stageOneRequest)||request.action()!=RiteDoctrineFrameV1.Action.CONFIRM_EDIT
                ||actual.status()!=RiteDoctrineFrameV1.Status.CONFIRMATION_DISPATCHED||!actual.nativeReturned()||!actual.nativeHandled()
                ||!actual.facts().orElseThrow().confirmable()||!actual.coreFrame().equals(pending.query.before.frame)
                ||actual.facts().orElseThrow().sourceRiteId()!=pending.query.frame.facts().orElseThrow().sourceRiteId())
            throw new IOException("Final source is not the actual successful original Stage1 query/action");
    }
    /** Readonly modal-origin check with the original Stage1 Core/source/lease/deadline, never a configured widget. */
    public synchronized RiteFinalRead readRiteFinalConfirmation(RiteFinalPending pending,Instant receiveDeadline)throws InterruptedException {
        String id="rite-final-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;byte[] packet=null;Instant until=receiveDeadline;
        try {
            Objects.requireNonNull(pending);Objects.requireNonNull(receiveDeadline);until=readDeadline(receiveDeadline);
            if(pending.deadline.isBefore(until))until=pending.deadline;requireRiteFinalPending(pending,until);
            if(pending.prepared!=null)throw new IOException("Original final request already prepared; no replacement readiness");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
            var request=RiteDoctrineFrameV1PublicCodec.finalQuery(pending.stageOneRequest);
            packet=NativeWire.execute(id,RiteDoctrineFrameV1.FINAL_STEP,BigInteger.ZERO,RiteDoctrineFrameV1PublicCodec.additionalFields(request).bytes());
            final Instant queryUntil=until;pending.latestReady=null;
            outcome=dispatchRead(id,packet,queryUntil,()->{requireBackgroundAtCoreWrite();try{requireRiteFinalPending(pending,queryUntil);}catch(IOException invalid){throw new UncheckedIOException(invalid);}});
            var frame=RiteDoctrineFrameV1PublicCodec.decodeOutcome(outcome);var ack=(AckReceived)outcome;
            if(frame.action()!=RiteDoctrineFrameV1.Action.QUERY_FINAL_CONFIRMATION
                    ||frame.status()!=RiteDoctrineFrameV1.Status.FINAL_CONFIRMATION_READY&&frame.status()!=RiteDoctrineFrameV1.Status.FINAL_CONFIRMATION_PENDING)
                return new RiteFinalUnavailable(outcome,"Native did not validate the actual Stage1-owned modal source");
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Final readiness actual custody absent"));
            requireRiteFinalObservation(pending,frame,ack,custody,queryUntil,queryUntil);
            if(frame.status()==RiteDoctrineFrameV1.Status.FINAL_CONFIRMATION_PENDING)return new RiteFinalWaiting(frame,ack,queryUntil);
            var ready=new RiteFinalReady(this,pending,frame,ack,custody,queryUntil);pending.latestReady=ready;requireRiteFinalReady(ready,queryUntil);return ready;
        }catch(IOException|RuntimeException invalid){
            if(pending!=null&&pending.issuer==this)pending.latestReady=null;
            if(outcome==null)outcome=sentRequestIds.contains(id)?new Unknown(id,"Readonly final readiness failed after write; retain original",packet==null?retainedOutbound(id):packet,Optional.empty()):zero(id,reason(invalid));
            return new RiteFinalUnavailable(outcome,reason(invalid));
        }catch(InterruptedException interrupted){
            if(!sentRequestIds.contains(id))throw interrupted;
            if(pending!=null&&pending.issuer==this)pending.latestReady=null;Thread.currentThread().interrupt();
            return new RiteFinalUnavailable(new Unknown(id,"Readonly final readiness interrupted after original write; no final authority",packet==null?retainedOutbound(id):packet,Optional.empty()),"Original readiness interrupted; retain without final action");
        }
    }
    private void requireRiteFinalReady(RiteFinalReady ready,Instant until)throws IOException {
        if(ready==null||ready.issuer!=this||ready.pending.latestReady!=ready)throw new IOException("Identical private final readiness required");
        requireRiteFinalObservation(ready.pending,ready.frame,ready.original,ready.custody,ready.validUntil,until);
    }
    private void requireRiteFinalObservation(RiteFinalPending pending,RiteDoctrineFrameV1 frame,AckReceived original,
            NativeRequestChronology custody,Instant validUntil,Instant until)throws IOException {
        requireRiteFinalPending(pending,until);Instant now=chronologyClock.instant();
        if(!now.isBefore(validUntil)||until.isAfter(validUntil)||custody.responseReceived().observedAt().isAfter(now)
                ||custody.responseReceived().observedAt().isAfter(validUntil)
                ||custody.writeEntered().order().compareTo(pending.stageOne.custody().orElseThrow().responseReceived().order())<=0
                ||!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)
                ||originalRequestChronology(original.requestId()).filter(custody::equals).isEmpty())
            throw new IOException("Final readiness crossed original Stage1 chronology/session");
        custody.verify(original);var decoded=RiteDoctrineFrameV1PublicCodec.decodeOutcome(original);
        var request=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(original.outbound().orElseThrow().originalPacket());
        if(!decoded.equals(frame)||!request.equals(RiteDoctrineFrameV1PublicCodec.finalQuery(pending.stageOneRequest)))
            throw new IOException("Final readiness changed original Stage1 Core/source/lease/body/deadline");
    }
    public synchronized RiteFinalPrepared prepareRiteFinalConfirmation(RiteFinalReady ready)throws IOException {
        Objects.requireNonNull(ready);
        if(ready.issuer==this&&ready.pending.prepared!=null)return ready.pending.prepared;
        requireRiteFinalReady(ready,ready.validUntil);
        var request=RiteDoctrineFrameV1PublicCodec.acceptFinal(ready.pending.stageOneRequest);
        String id="rite-final-accept-"+UUID.randomUUID().toString().replace("-","");
        byte[] packet=NativeWire.execute(id,RiteDoctrineFrameV1.FINAL_STEP,BigInteger.ZERO,RiteDoctrineFrameV1PublicCodec.additionalFields(request).bytes());
        if(!RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(packet).equals(request))throw new IOException("Final acceptance body drift");
        return ready.pending.prepared=new RiteFinalPrepared(this,ready,id,packet);
    }
    /** One fixed genericConfirm void invocation; its return never establishes persistence or a physical SAVE. */
    public synchronized DispatchOutcome submitRiteFinalConfirmation(RiteFinalPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);
        if(original.issuer!=this||original.ready.pending.prepared!=original)return zero(original.id,"Foreign final preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original final call has no reusable write authority");
        original.called=true;var ready=original.ready;DispatchOutcome dispatched=null;
        try {
            requireRiteFinalReady(ready,ready.validUntil);
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
            dispatched=dispatch(original.id,original.packet.value(),ready.validUntil,()->{
                requireBackgroundAtCoreWrite();try{requireRiteFinalReady(ready,ready.validUntil);}catch(IOException invalid){throw new UncheckedIOException(invalid);}
                if(ready.pending.finalAttempted)throw new IllegalStateException("Final callback claim consumed");
                ready.pending.finalAttempted=true;ready.pending.latestReady=null;heldSnapshotInvalidated=true;
            });
            if(dispatched instanceof Unknown unknown){unresolvedCoreControl=unknown;return original.outcome=unknown;}
            if(dispatched instanceof AckReceived ack){
                var frame=RiteDoctrineFrameV1PublicCodec.decodeOutcome(ack);
                if(frame.status()==RiteDoctrineFrameV1.Status.INDETERMINATE)throw new IOException("Native final callback indeterminate");
            }
            return original.outcome=dispatched;
        }catch(IOException|RuntimeException invalid){
            if(sentRequestIds.contains(original.id)){
                if(dispatched instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
                unresolvedCoreControl=new Unknown(original.id,"Final callback unqualified after original write; never replay: "+reason(invalid),original.packet.value(),dispatched instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());
                return original.outcome=unresolvedCoreControl;
            }
            return original.outcome=zero(original.id,reason(invalid));
        }catch(InterruptedException interrupted){
            if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();
            unresolvedCoreControl=new Unknown(original.id,"Final callback interrupted after original write; never replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;
        }
    }

    public sealed interface GuiControlsReadV2 permits GuiControlsReceivedV2,GuiControlsReadUnavailableV2 { DispatchOutcome original(); }
    public static final class GuiControlsReceivedV2 implements GuiControlsReadV2 {
        private final NativeGameTransport issuer;private final CoreReceived before;private final RiteDraftCostsReceived rite;
        private final GuiControlsFrameV2 frame;private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private boolean activationAttempted;
        private GuiControlsReceivedV2(NativeGameTransport issuer,CoreReceived before,RiteDraftCostsReceived rite,GuiControlsFrameV2 frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.before=before;this.rite=rite;this.frame=frame;this.original=original;this.custody=custody;this.validUntil=until;}
        public GuiControlsFrameV2 frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant deadline)throws IOException{Objects.requireNonNull(actual).requireGuiControlsOriginalV2(this,deadline);}
    }
    public record GuiControlsReadUnavailableV2(DispatchOutcome original,String reason)implements GuiControlsReadV2 {public GuiControlsReadUnavailableV2{Objects.requireNonNull(original);StrictJson.text(reason);}}
    private GuiControlsReceivedV2 latestGuiControlsQueryV2;
    /** Closed literal navigation choices; no arbitrary root/name/path/ordinal admission. */
    public enum NavigationAction {
        OPEN_FAITH(GuiControlsFrameV2.Window.BOTTOM,"faith_button"),OPEN_RITE_EDITOR(GuiControlsFrameV2.Window.FAITH,"edit_rite");
        private final GuiControlsFrameV2.Window window;private final String runtimeName;
        NavigationAction(GuiControlsFrameV2.Window window,String runtimeName){this.window=window;this.runtimeName=runtimeName;}
    }
    public synchronized GuiControlsReadV2 readNavigationGuiControlsV2(CoreReceived before,NavigationAction action,Instant deadline)throws InterruptedException {
        Objects.requireNonNull(action);return readGuiControlsV2(before,null,action.window,deadline);
    }
    public synchronized GuiControlsReadV2 readFaithGuiControlsV2(CoreReceived before,Instant deadline)throws InterruptedException{return readGuiControlsV2(before,null,GuiControlsFrameV2.Window.FAITH,deadline);}
    public synchronized GuiControlsReadV2 readRiteGuiControlsV2(RiteDraftCostsReceived rite,Instant deadline)throws InterruptedException{return readGuiControlsV2(rite==null?null:rite.before,rite,GuiControlsFrameV2.Window.RITE,deadline);}
    private GuiControlsReadV2 readGuiControlsV2(CoreReceived before,RiteDraftCostsReceived rite,GuiControlsFrameV2.Window selectedWindow,Instant deadline)throws InterruptedException {
        if(before!=null&&before.issuer==this&&before.unresolvedGuiControlsReadV2!=null)return before.unresolvedGuiControlsReadV2;
        String id="gui-controls-v2-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome original;Instant until=deadline;
        try{
            Objects.requireNonNull(before);Objects.requireNonNull(deadline);before.requireOriginal(this,deadline);
            if(applicationExitAttempted||before.controlAttempted||before.guiControlsReadAttemptedV2||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)throw new IOException("controls query requires an unused actual Core without pending writes");
            if(!(before.frame instanceof CoreFrame.Partial core))throw new IOException("actual available Core required");GuiControlsFrameV2.requireCore(core);
            java.util.OptionalLong source=java.util.OptionalLong.empty();var window=Objects.requireNonNull(selectedWindow);
            if(rite!=null){rite.requireOriginal(this,deadline);if(rite.before!=before||!(rite.frame instanceof RiteDraftCostsFrameV2.Partial partial))throw new IOException("actual identical transport draft source required");source=java.util.OptionalLong.of(partial.draft().sourceRiteId());window=GuiControlsFrameV2.Window.RITE;}
            if(!hello.capabilities().contains(GuiControlsFrameV2.QUERY_CAPABILITY))throw new IOException("actual current controls query capability absent");if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
            until=readDeadline(deadline);final Instant queryUntil=until;var request=GuiControlsFrameV2PublicCodec.query(core,queryUntil,window,source);byte[] packet=NativeWire.execute(id,request.operation().step(),BigInteger.ZERO,GuiControlsFrameV2PublicCodec.additionalFields(request).bytes());
            if(!GuiControlsFrameV2PublicCodec.decodeRequestPacket(packet).equals(request))throw new IOException("complete current controls request drift");
            original=retainReadOutcome(dispatchRead(id,packet,queryUntil,()->{requireBackgroundAtCoreWrite();try{before.requireOriginal(this,queryUntil);if(rite!=null)rite.requireOriginal(this,queryUntil);}catch(IOException invalid){throw new UncheckedIOException(invalid);}if(before.controlAttempted||before.guiControlsReadAttemptedV2)throw new IllegalStateException("original Core controls query consumed");before.guiControlsReadAttemptedV2=true;latestGuiControlsQueryV2=null;}));
        }catch(IOException|RuntimeException failure){original=sentRequestIds.contains(id)?new Unknown(id,"current controls query failed after write; preserve original only: "+reason(failure),retainedOutbound(id),Optional.empty()):zero(id,reason(failure));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;original=new Unknown(id,"current controls query interrupted after actual write; no replay",retainedOutbound(id),Optional.empty());Thread.currentThread().interrupt();}
        try{
            var frame=GuiControlsFrameV2PublicCodec.decodeOutcome(original);var ack=(AckReceived)original;var custody=originalRequestChronology(id).orElseThrow(()->new IOException("actual current controls custody absent"));
            var received=new GuiControlsReceivedV2(this,before,rite,frame,ack,custody,until);latestGuiControlsQueryV2=received;requireGuiControlsOriginalV2(received,until);return received;
        }catch(IOException|RuntimeException invalid){latestGuiControlsQueryV2=null;var unavailable=new GuiControlsReadUnavailableV2(original,reason(invalid));if(before!=null&&before.issuer==this&&original instanceof Unknown)before.unresolvedGuiControlsReadV2=unavailable;return unavailable;}
    }
    private void requireGuiControlsOriginalV2(GuiControlsReceivedV2 actual,Instant deadline)throws IOException {
        Objects.requireNonNull(deadline);if(actual.issuer!=this||actual!=latestGuiControlsQueryV2||closed||terminalFailure!=null||applicationExitAttempted||actual.activationAttempted||actual.before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null)throw new IOException("actual unused current controls query authority unavailable");
        actual.before.requireOriginal(this,deadline);if(actual.rite!=null)actual.rite.requireOriginal(this,deadline);Instant now=chronologyClock.instant();
        if(!now.isBefore(deadline)||!now.isBefore(actual.validUntil)||deadline.isAfter(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)throw new IOException("controls query escaped original Core/deadline/chronology");
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)||!originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isPresent())throw new IOException("controls crossed original Game/session/connection/custody");actual.custody.verify(actual.original);
        var frame=GuiControlsFrameV2PublicCodec.decodeOutcome(actual.original);var request=GuiControlsFrameV2PublicCodec.decodeRequestPacket(actual.original.outbound().orElseThrow().originalPacket());
        if(!frame.equals(actual.frame)||request.operation()!=GuiControlsFrameV2.Operation.QUERY||!request.expectedCore().equals(actual.before.frame)||!request.deadlineUnixMs().equals(BigInteger.valueOf(actual.validUntil.toEpochMilli())))throw new IOException("controls query differs from original Core/window/source");
        if(actual.rite==null){if(request.window()==GuiControlsFrameV2.Window.RITE||request.expectedSourceRiteId().isPresent())throw new IOException("Non-Rite observation borrowed a Rite source");}
        else {var source=((RiteDraftCostsFrameV2.Partial)actual.rite.frame).draft().sourceRiteId();if(request.window()!=GuiControlsFrameV2.Window.RITE||request.expectedSourceRiteId().isEmpty()||request.expectedSourceRiteId().getAsLong()!=source)throw new IOException("Rite query must derive source from same actual draft receipt");}
    }
    /** Select exactly one Native-admissible literal row from the same private query. Numeric child paths prove no ancestor names. */
    public synchronized DispatchOutcome submitNavigationGuiControlV2(GuiControlsReceivedV2 query,NavigationAction action,Instant deadline)throws InterruptedException {
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        try {
            Objects.requireNonNull(action);Objects.requireNonNull(query);requireGuiControlsOriginalV2(query,deadline);
            if(query.rite!=null||query.frame.window()!=action.window||!query.frame.queryAvailable())throw new IOException("Navigation requires its matching original literal root query");
            var admitted=query.frame.widgets().orElseThrow().stream().filter(w->w.runtimeName().equals(action.runtimeName)&&w.effectiveVisible()&&w.enabled()&&w.nativeCallbackAdmissible()).toList();
            if(admitted.size()!=1)throw new IOException("Exactly one Native-admissible literal navigation row required");
            return submitGuiControlsActivationV2(query,admitted.get(0),action,deadline);
        }catch(IOException|RuntimeException invalid){return zero("gui-nav-refused-"+UUID.randomUUID().toString().replace("-",""),reason(invalid));}
    }
    /** A row token from this exact actual query only. This API chooses no doctrine or runtime-name/ordinal selector. */
    public synchronized DispatchOutcome submitGuiControlsActivationV2(GuiControlsReceivedV2 query,GuiControlsFrameV2.Widget selected,Instant deadline)throws InterruptedException {
        return submitGuiControlsActivationV2(query,selected,null,deadline);
    }
    private DispatchOutcome submitGuiControlsActivationV2(GuiControlsReceivedV2 query,GuiControlsFrameV2.Widget selected,NavigationAction navigation,Instant deadline)throws InterruptedException {
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        String id="gui-activate-v2-"+UUID.randomUUID().toString().replace("-","");
        try{
            Objects.requireNonNull(query);Objects.requireNonNull(selected);requireGuiControlsOriginalV2(query,deadline);
            if(activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)throw new IOException("current UI activation cannot borrow business recovery/mailbox");
            var frame=query.frame;
            boolean selectedRite=navigation==null&&query.rite!=null&&frame.window()==GuiControlsFrameV2.Window.RITE&&frame.riteSourceVerified();
            boolean selectedNavigation=navigation!=null&&query.rite==null&&frame.window()==navigation.window&&selected.runtimeName().equals(navigation.runtimeName)
                    &&frame.widgets().orElseThrow().stream().filter(w->w.runtimeName().equals(navigation.runtimeName)&&w.effectiveVisible()&&w.enabled()&&w.nativeCallbackAdmissible()).count()==1;
            if(!(selectedRite||selectedNavigation)||!frame.queryAvailable()||frame.widgets().orElseThrow().stream().noneMatch(selected::equals)||!selected.effectiveVisible()||!selected.enabled()||!selected.nativeCallbackAdmissible())throw new IOException("Only the original admissible Rite row or unique fixed navigation literal may be activated");
            if(!hello.capabilities().contains(GuiControlsFrameV2.ACTIVATE_CAPABILITY))throw new IOException("actual current activation capability absent");if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
            var original=GuiControlsFrameV2PublicCodec.decodeRequestPacket(query.original.outbound().orElseThrow().originalPacket());var token=new GuiControlsFrameV2PublicCodec.SelectionToken(frame.queryGeneration().orElseThrow(),selected.widgetId());var request=GuiControlsFrameV2PublicCodec.activate(original,deadline,token);
            byte[] packet=NativeWire.execute(id,request.operation().step(),BigInteger.ZERO,GuiControlsFrameV2PublicCodec.additionalFields(request).bytes());
            var outcome=dispatch(id,packet,deadline,()->{requireBackgroundAtCoreWrite();try{requireGuiControlsOriginalV2(query,deadline);}catch(IOException invalid){throw new UncheckedIOException(invalid);}if(query.activationAttempted||query.before.controlAttempted)throw new IllegalStateException("original current activation claim consumed");query.activationAttempted=true;query.before.controlAttempted=true;heldSnapshotInvalidated=true;latestGuiControlsQueryV2=null;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return unknown;}
            if(outcome instanceof AckReceived ack&&ack.nativeOk()){
                try{var actual=GuiControlsFrameV2PublicCodec.decodeOutcome(ack);if(actual.status()==GuiControlsFrameV2.Status.INDETERMINATE){indeterminateCoreAcknowledgement=ack;unresolvedCoreControl=new Unknown(id,"current controls Native result indeterminate; preserve actual original ACK, never replay",packet,Optional.of(ack.originalFrame()));return unresolvedCoreControl;}}
                catch(IOException|RuntimeException malformed){indeterminateCoreAcknowledgement=ack;unresolvedCoreControl=new Unknown(id,"current activation positive ACK cannot be qualified; keep original, never replay: "+reason(malformed),packet,Optional.of(ack.originalFrame()));return unresolvedCoreControl;}
            }
            return outcome;
        }catch(IOException|RuntimeException failure){if(sentRequestIds.contains(id)){unresolvedCoreControl=new Unknown(id,"current activation failed after actual write; no replay: "+reason(failure),retainedOutbound(id),Optional.empty());return unresolvedCoreControl;}return zero(id,reason(failure));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;unresolvedCoreControl=new Unknown(id,"current activation interrupted after actual write; no replay",retainedOutbound(id),Optional.empty());Thread.currentThread().interrupt();return unresolvedCoreControl;}
    }

    public sealed interface GuiWindowRead permits GuiWindowReceived, GuiWindowReadUnavailable {
        DispatchOutcome original();
    }
    /** Redacted read DATA from this receiver; never a complete GUI frame or control permit. */
    public static final class GuiWindowReceived implements GuiWindowRead {
        private final NativeGameTransport issuer;
        private final CoreReceived before;
        private final GuiWindowFrame frame;
        private final AckReceived original;
        private final NativeRequestChronology custody;
        private final Instant validUntil;
        private GuiWindowReceived(NativeGameTransport issuer, CoreReceived before, GuiWindowFrame frame,
                AckReceived original, NativeRequestChronology custody, Instant validUntil) {
            this.issuer=issuer;this.before=before;this.frame=frame;this.original=original;this.custody=custody;this.validUntil=validUntil;
        }
        public GuiWindowFrame frame(){return frame;}
        @Override public AckReceived original(){return original;}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual, Instant deadline)throws IOException {
            Objects.requireNonNull(actual).requireGuiWindowOriginal(this,deadline);
        }
    }
    public record GuiWindowReadUnavailable(DispatchOutcome original,String reason) implements GuiWindowRead {
        public GuiWindowReadUnavailable {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    /** Expected Core can only be the identical transport's original CoreReceived, never configuration DATA. */
    public synchronized GuiWindowRead readGuiWindowReceived(CoreReceived before, String windowName, Instant deadline)throws InterruptedException {
        if(before!=null&&before.issuer==this&&before.unresolvedGuiWindowRead!=null)return before.unresolvedGuiWindowRead;
        String id="gui-named-window-"+UUID.randomUUID().toString().replace("-","");
        DispatchOutcome original;Instant until=deadline;
        try {
            Objects.requireNonNull(before);Objects.requireNonNull(deadline);before.requireOriginal(this,deadline);
            if(applicationExitAttempted||before.controlAttempted||before.guiWindowReadAttempted||unresolvedCoreControl!=null
                    ||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("named-window query requires unused current Core without active or uncertain controls");
            if(!(before.frame instanceof CoreFrame.Partial partial))throw new IOException("named-window requires the actual available Core prefix");
            GuiRootIndexFrame.requireExpectedCore(partial);GuiWindowFrame.windowName(windowName);
            if(!hello.capabilities().contains(CoreFrame.CAPABILITY))throw new IOException("original Core capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            until=readDeadline(deadline);final Instant queryUntil=until;
            var request=GuiWindowFramePublicCodec.request(partial,queryUntil,windowName);
            byte[] packet=NativeWire.execute(id,GuiWindowFrame.STEP,BigInteger.ZERO,GuiWindowFramePublicCodec.additionalFields(request).bytes());
            if(!GuiWindowFramePublicCodec.decodeRequestPacket(packet).equals(request))throw new IOException("named-window complete outgoing request roundtrip drift");
            original=retainReadOutcome(dispatchRead(id,packet,queryUntil,()->{
                requireBackgroundAtCoreWrite();
                try{before.requireOriginal(this,queryUntil);}catch(IOException invalid){throw new UncheckedIOException(invalid);}
                if(before.controlAttempted||before.guiWindowReadAttempted)throw new IllegalStateException("named-window Core source already consumed");
                before.guiWindowReadAttempted=true;
            }));
        }catch(IOException|RuntimeException invalid){
            if(sentRequestIds.contains(id))original=new Unknown(id,"named-window failed after actual query write; retain original, never replay: "+reason(invalid),retainedOutbound(id),Optional.empty());
            else original=zero(id,reason(invalid));
        }
        try {
            var frame=GuiWindowFramePublicCodec.decodeOutcome(original);var ack=(AckReceived)original;
            var custody=originalRequestChronology(ack.requestId()).orElseThrow(()->new IOException("actual named-window ACK custody unavailable"));
            var received=new GuiWindowReceived(this,before,frame,ack,custody,until);
            requireGuiWindowOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){
            var unavailable=new GuiWindowReadUnavailable(original,reason(invalid));
            if(before!=null&&before.issuer==this&&original instanceof Unknown)before.unresolvedGuiWindowRead=unavailable;
            return unavailable;
        }
    }
    private void requireGuiWindowOriginal(GuiWindowReceived actual,Instant deadline)throws IOException {
        Objects.requireNonNull(deadline);
        if(actual.issuer!=this||hello==null||closed||terminalFailure!=null)throw new IOException("named-window requires its identical live held receiver");
        actual.before.requireOriginal(this,deadline);Instant now=chronologyClock.instant();
        if(!now.isBefore(actual.validUntil)||!now.isBefore(deadline)||deadline.isAfter(actual.validUntil)
                ||actual.custody.responseReceived().observedAt().isAfter(now)||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)
                ||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("named-window escaped its original Core/query chronology");
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)
                ||!actual.before.guiWindowReadAttempted||!originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isPresent())
            throw new IOException("named-window crossed its original Game/session/connection/custody");
        actual.custody.verify(actual.original);
        var decoded=GuiWindowFramePublicCodec.decodeOutcome(actual.original);
        var outbound=actual.original.outbound().orElseThrow(()->new IOException("named-window original outbound missing"));
        var request=GuiWindowFramePublicCodec.decodeRequestPacket(outbound.originalPacket());
        if(!decoded.equals(actual.frame)||!request.expectedCore().equals(actual.before.frame)
                ||!request.deadlineUnixMs().equals(BigInteger.valueOf(actual.validUntil.toEpochMilli())))
            throw new IOException("named-window request/result differs from the identical retained Core or query window");
    }
    public sealed interface PersonalGoldRead permits PersonalGoldReceived,PersonalGoldReadUnavailable {
        DispatchOutcome original();
    }
    /** A read-only resource occurrence. Its nested Core DATA cannot become a Core control receipt. */
    public static final class PersonalGoldReceived implements PersonalGoldRead {
        private final NativeGameTransport issuer;
        private final PersonalGoldFrame frame;
        private final AckReceived original;
        private final NativeRequestChronology custody;
        private final Instant validUntil;
        private PersonalGoldReceived(NativeGameTransport issuer,PersonalGoldFrame frame,AckReceived original,
                NativeRequestChronology custody,Instant validUntil) {
            this.issuer=issuer;this.frame=frame;this.original=original;this.custody=custody;this.validUntil=validUntil;
        }
        public PersonalGoldFrame frame(){return frame;}
        @Override public AckReceived original(){return original;}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actualHeld,Instant deadline)throws IOException {
            Objects.requireNonNull(actualHeld).requirePersonalGoldOriginal(this,deadline);
        }
    }
    public record PersonalGoldReadUnavailable(DispatchOutcome original,String reason)implements PersonalGoldRead {
        public PersonalGoldReadUnavailable {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    public synchronized PersonalGoldRead readPersonalGoldFrameReceived(Instant deadline)throws InterruptedException {
        Instant until=readDeadline(Objects.requireNonNull(deadline));
        DispatchOutcome original=readPersonalGoldFrame(until);
        try {
            PersonalGoldFrame frame=PersonalGoldFramePublicCodec.decodeOutcome(original);var ack=(AckReceived)original;
            var custody=originalRequestChronology(ack.requestId()).orElseThrow(()->new IOException("actual personal-gold ACK custody unavailable"));
            var received=new PersonalGoldReceived(this,frame,ack,custody,until);
            requirePersonalGoldOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){return new PersonalGoldReadUnavailable(original,reason(invalid));}
    }
    private void requirePersonalGoldOriginal(PersonalGoldReceived actual,Instant deadline)throws IOException {
        Objects.requireNonNull(deadline);
        if(actual.issuer!=this||hello==null||closed||terminalFailure!=null)throw new IOException("personal gold requires its identical live held receiver");
        Instant now=chronologyClock.instant();
        if(!now.isBefore(actual.validUntil)||!now.isBefore(deadline)||deadline.isAfter(actual.validUntil)
                ||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)
                ||actual.custody.writeEntered().observedAt().isBefore(helloObservedAt))throw new IOException("personal gold escaped its original query window or HELLO chronology");
        verifyHeld(deadline);
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)
                ||!originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isPresent())
            throw new IOException("personal gold crossed its original Game/session/connection/custody");
        actual.custody.verify(actual.original);
        var decoded=PersonalGoldFramePublicCodec.decodeOutcome(actual.original);
        var originalHello=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
        if(!decoded.equals(actual.frame)||!decoded.build().matches(NativeWire.text(originalHello.get("expected_ck3_version")),hello.gameSha256())
                ||!hello.adapterId().equals(decoded.version().adapter())||!hello.capabilities().contains(decoded.version().capability()))
            throw new IOException("personal gold belongs to another exact executable, capability or original frame");
    }
    /** Independent paused resource query only; it does not refresh a full Snapshot or authorize a control. */
    public synchronized DispatchOutcome readPersonalGoldFrame(Instant deadline)throws InterruptedException {
        String id="personal-gold-"+UUID.randomUUID().toString().replace("-","");
        try {
            awaitHello(deadline);verifyEndpoint();
            var original=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
            var version=PersonalGoldFrame.Version.forSource(NativeWire.text(original.get("expected_ck3_version")),hello.gameSha256(),hello.adapterId());
            if(version.isEmpty()||!hello.capabilities().contains(version.orElseThrow().capability()))
                throw new IOException("standalone personal gold requires exact Florin identity and its advertised capability");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            return retainReadOutcome(dispatchRead(id,NativeWire.execute(id,version.orElseThrow().step(),BigInteger.ZERO,new byte[]{'{','}'}),readDeadline(deadline),()->{}));
        }catch(IOException|RuntimeException unavailable){return retainReadOutcome(zero(id,reason(unavailable)));}
    }
    public sealed interface ActorFoundationRead permits ActorFoundationReceived,ActorFoundationReadUnavailable {
        DispatchOutcome original();
    }
    /** A read-only resource occurrence. Its nested Core DATA cannot become a Core control receipt. */
    public static final class ActorFoundationReceived implements ActorFoundationRead {
        private final NativeGameTransport issuer;
        private final ActorFoundationFrame frame;
        private final AckReceived original;
        private final NativeRequestChronology custody;
        private final Instant validUntil;
        private ActorFoundationReceived(NativeGameTransport issuer,ActorFoundationFrame frame,AckReceived original,
                NativeRequestChronology custody,Instant validUntil) {
            this.issuer=issuer;this.frame=frame;this.original=original;this.custody=custody;this.validUntil=validUntil;
        }
        public ActorFoundationFrame frame(){return frame;}
        @Override public AckReceived original(){return original;}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actualHeld,Instant deadline)throws IOException {
            Objects.requireNonNull(actualHeld).requireActorFoundationOriginal(this,deadline);
        }
    }
    public record ActorFoundationReadUnavailable(DispatchOutcome original,String reason)implements ActorFoundationRead {
        public ActorFoundationReadUnavailable {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    public synchronized ActorFoundationRead readActorFoundationFrameReceived(Instant deadline)throws InterruptedException {
        Instant until=readDeadline(Objects.requireNonNull(deadline));
        DispatchOutcome original=readActorFoundationFrame(until);
        try {
            ActorFoundationFrame frame=ActorFoundationFramePublicCodec.decodeOutcome(original);var ack=(AckReceived)original;
            var custody=originalRequestChronology(ack.requestId()).orElseThrow(()->new IOException("actual actor-foundation ACK custody unavailable"));
            var received=new ActorFoundationReceived(this,frame,ack,custody,until);
            requireActorFoundationOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){return new ActorFoundationReadUnavailable(original,reason(invalid));}
    }
    private void requireActorFoundationOriginal(ActorFoundationReceived actual,Instant deadline)throws IOException {
        Objects.requireNonNull(deadline);
        if(actual.issuer!=this||hello==null||closed||terminalFailure!=null)throw new IOException("actor foundation requires its identical live held receiver");
        Instant now=chronologyClock.instant();
        if(!now.isBefore(actual.validUntil)||!now.isBefore(deadline)||deadline.isAfter(actual.validUntil)
                ||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)
                ||actual.custody.writeEntered().observedAt().isBefore(helloObservedAt))throw new IOException("actor foundation escaped its original query window or HELLO chronology");
        verifyHeld(deadline);
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)
                ||!originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isPresent())
            throw new IOException("actor foundation crossed its original Game/session/connection/custody");
        actual.custody.verify(actual.original);
        var decoded=ActorFoundationFramePublicCodec.decodeOutcome(actual.original);
        var originalHello=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
        if(!decoded.equals(actual.frame)||!decoded.build().matches(NativeWire.text(originalHello.get("expected_ck3_version")),hello.gameSha256())
                ||!hello.adapterId().equals(ActorFoundationFrame.ADAPTER))throw new IOException("actor foundation belongs to another exact executable or original frame");
    }
    /** Independent paused resource query only; it does not refresh a full Snapshot or authorize a control. */
    public synchronized DispatchOutcome readActorFoundationFrame(Instant deadline)throws InterruptedException {
        String id="actor-foundation-"+UUID.randomUUID().toString().replace("-","");
        try {
            awaitHello(deadline);verifyEndpoint();
            var original=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
            if(!ExactCk3Build.CK3_1210.matches(NativeWire.text(original.get("expected_ck3_version")),hello.gameSha256())
                    ||!hello.adapterId().equals(ActorFoundationFrame.ADAPTER)||!hello.capabilities().contains(ActorFoundationFrame.CAPABILITY))
                throw new IOException("standalone actor foundation requires exact Florin identity and its advertised capability");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            return retainReadOutcome(dispatchRead(id,NativeWire.execute(id,ActorFoundationFrame.STEP,BigInteger.ZERO,new byte[]{'{','}'}),readDeadline(deadline),()->{}));
        }catch(IOException|RuntimeException unavailable){return retainReadOutcome(zero(id,reason(unavailable)));}
    }
    public sealed interface ActorResourceLeafReadV2 permits ActorResourceLeafReceivedV2,ActorResourceLeafReadUnavailableV2 {
        DispatchOutcome original();
    }
    /** A read-only resource occurrence. Its nested Core DATA cannot become a Core control receipt. */
    public static final class ActorResourceLeafReceivedV2 implements ActorResourceLeafReadV2 {
        private final NativeGameTransport issuer;
        private final ActorResourceLeafV2 frame;
        private final AckReceived original;
        private final NativeRequestChronology custody;
        private final Instant validUntil;
        private ActorResourceLeafReceivedV2(NativeGameTransport issuer,ActorResourceLeafV2 frame,AckReceived original,
                NativeRequestChronology custody,Instant validUntil) {
            this.issuer=issuer;this.frame=frame;this.original=original;this.custody=custody;this.validUntil=validUntil;
        }
        public ActorResourceLeafV2 frame(){return frame;}
        @Override public AckReceived original(){return original;}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actualHeld,Instant deadline)throws IOException {
            Objects.requireNonNull(actualHeld).requireActorResourceLeafOriginalV2(this,deadline);
        }
    }
    public record ActorResourceLeafReadUnavailableV2(DispatchOutcome original,String reason)implements ActorResourceLeafReadV2 {
        public ActorResourceLeafReadUnavailableV2 {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    public synchronized ActorResourceLeafReadV2 readActorResourceLeafFrameReceivedV2(Instant deadline)throws InterruptedException {
        Instant until=readDeadline(Objects.requireNonNull(deadline));
        DispatchOutcome original=readActorResourceLeafFrameV2(until);
        try {
            ActorResourceLeafV2 frame=ActorResourceLeafV2.decodeOutcome(original);var ack=(AckReceived)original;
            var custody=originalRequestChronology(ack.requestId()).orElseThrow(()->new IOException("actual actor-resource-v2 ACK custody unavailable"));
            var received=new ActorResourceLeafReceivedV2(this,frame,ack,custody,until);
            requireActorResourceLeafOriginalV2(received,until);return received;
        }catch(IOException|RuntimeException invalid){return new ActorResourceLeafReadUnavailableV2(original,reason(invalid));}
    }
    private void requireActorResourceLeafOriginalV2(ActorResourceLeafReceivedV2 actual,Instant deadline)throws IOException {
        Objects.requireNonNull(deadline);
        if(actual.issuer!=this||hello==null||closed||terminalFailure!=null)throw new IOException("actor resource leaf v2 requires its identical live held receiver");
        Instant now=chronologyClock.instant();
        if(!now.isBefore(actual.validUntil)||!now.isBefore(deadline)||deadline.isAfter(actual.validUntil)
                ||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)
                ||actual.custody.writeEntered().observedAt().isBefore(helloObservedAt))throw new IOException("actor resource leaf v2 escaped its original query window or HELLO chronology");
        verifyHeld(deadline);
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)
                ||!originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isPresent())
            throw new IOException("actor resource leaf v2 crossed its original Game/session/connection/custody");
        actual.custody.verify(actual.original);
        var decoded=ActorResourceLeafV2.decodeOutcome(actual.original);
        var originalHello=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
        if(!decoded.equals(actual.frame)||!ActorResourceLeafV2.BUILD.matches(NativeWire.text(originalHello.get("expected_ck3_version")),hello.gameSha256())
                ||!hello.adapterId().equals(ActorResourceLeafV2.ADAPTER)||!hello.capabilities().contains(ActorResourceLeafV2.CAPABILITY))throw new IOException("actor resource leaf v2 belongs to another exact executable or original frame");
    }
    /** Independent paused resource query only; it does not refresh a full Snapshot or authorize a control. */
    public synchronized DispatchOutcome readActorResourceLeafFrameV2(Instant deadline)throws InterruptedException {
        String id="actor-resource-v2-"+UUID.randomUUID().toString().replace("-","");
        try {
            awaitHello(deadline);verifyEndpoint();
            var original=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
            if(!ExactCk3Build.CK3_1210.matches(NativeWire.text(original.get("expected_ck3_version")),hello.gameSha256())
                    ||!hello.adapterId().equals(ActorResourceLeafV2.ADAPTER)||!hello.capabilities().contains(ActorResourceLeafV2.CAPABILITY))
                throw new IOException("standalone actor resource leaf v2 requires exact Florin identity and its advertised capability");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            return retainReadOutcome(dispatchRead(id,NativeWire.execute(id,ActorResourceLeafV2.STEP,BigInteger.ZERO,new byte[]{'{','}'}),readDeadline(deadline),()->{}));
        }catch(IOException|RuntimeException unavailable){return retainReadOutcome(zero(id,reason(unavailable)));}
    }
    /** Standalone War identity/score READ projected as partial Full DATA; no rich Full or world-control role is granted. */
    public synchronized org.xar.ck3.control.nativebridge.capabilities.registry.FlorinWarIdentityPublicCodec.ProjectedRead
            readActiveWarsIdentityProjection(Instant deadline)throws InterruptedException {
        String id="war-identity-"+UUID.randomUUID().toString().replace("-","");
        Instant until=readDeadline(Objects.requireNonNull(deadline));
        DispatchOutcome original;
        try {
            awaitHello(until);verifyEndpoint();
            var source=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
            if(!ExactCk3Build.CK3_1210.matches(NativeWire.text(source.get("expected_ck3_version")),hello.gameSha256())
                    ||!hello.adapterId().equals(org.xar.ck3.control.contracts.semantic.FlorinWarIdentityCodec.ADAPTER)
                    ||!hello.capabilities().contains(org.xar.ck3.control.contracts.semantic.FlorinWarIdentityCodec.CAPABILITY))
                throw new IOException("standalone War identity requires exact Florin source and its advertised capability");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            original=retainReadOutcome(dispatchRead(id,NativeWire.execute(id,
                    org.xar.ck3.control.contracts.semantic.FlorinWarIdentityCodec.STEP,BigInteger.ZERO,new byte[]{'{','}'}),until,()->{}));
        }catch(IOException|RuntimeException invalid){
            original=retainReadOutcome(zero(id,reason(invalid)));
        }
        if(original instanceof AckReceived ack)try {
            var custody=originalRequestChronology(ack.requestId()).orElseThrow(()->new IOException("actual War identity ACK custody unavailable"));
            custody.verify(ack);
            if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)
                    ||custody.writeEntered().observedAt().isBefore(helloObservedAt)
                    ||custody.responseReceived().observedAt().isAfter(until))
                throw new IOException("War identity crossed its original HELLO/session/connection/deadline");
        }catch(IOException|RuntimeException invalid){
            return new org.xar.ck3.control.nativebridge.capabilities.registry.FlorinWarIdentityPublicCodec.UnavailableRead(original,reason(invalid));
        }
        return org.xar.ck3.control.nativebridge.capabilities.registry.FlorinWarIdentityPublicCodec.projectPartialFull(original);
    }

    public sealed interface FullClockRead permits FullClockReceived,FullClockReadUnavailable {
        NativeFreshSnapshotPort.Result original();
    }
    /** Native-only Full clock source; never an admitted Driver or a Root writer permit. */
    public static final class FullClockReceived implements FullClockRead {
        private final NativeGameTransport issuer;
        private final NativeFreshSnapshotPort.Received original;
        private final Instant validUntil;
        private boolean writeAttempted;
        private boolean personalCashReadAttempted;
        private PersonalCashReadUnavailable unresolvedPersonalCashRead;
        private boolean eventOptionsReadAttempted;
        private EventOptionsRead eventOptionsRead;
        private boolean guiReadAttempted;
        private GuiRead guiRead;
        private FullClockReceived(NativeGameTransport issuer,NativeFreshSnapshotPort.Received original,Instant validUntil){
            this.issuer=issuer;this.original=original;this.validUntil=validUntil;
        }
        @Override public NativeFreshSnapshotPort.Received original(){return original;}
        public ObservedFrame frame(){return original.originalFrame();}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant deadline)throws IOException{
            Objects.requireNonNull(actual).requireFullClockOriginal(this,deadline);
        }
    }
    public record FullClockReadUnavailable(NativeFreshSnapshotPort.Result original,String reason)implements FullClockRead {
        public FullClockReadUnavailable {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    public synchronized FullClockRead readFullClockFrameReceived(Instant deadline)throws InterruptedException{
        Instant until=readDeadline(Objects.requireNonNull(deadline));
        try {awaitHello(until);requireFlorinFullClockSource();}
        catch(IOException|RuntimeException invalid){
            var absent=new NativeFreshSnapshotPort.Unavailable(zero("full-clock-source-"+UUID.randomUUID().toString().replace("-",""),reason(invalid)),reason(invalid));
            return new FullClockReadUnavailable(absent,reason(invalid));
        }
        var read=readFreshFullState(until);
        if(!(read instanceof NativeFreshSnapshotPort.Received received))
            return new FullClockReadUnavailable(read,((NativeFreshSnapshotPort.Unavailable)read).reason());
        try {
            var source=new FullClockReceived(this,received,until);requireFullClockOriginal(source,until);return source;
        }catch(IOException|RuntimeException invalid){return new FullClockReadUnavailable(read,reason(invalid));}
    }
    private ExactCk3Build requireFlorinFullClockSource()throws IOException{
        if(hello==null)throw new IOException("actual Full clock HELLO unavailable");
        var original=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
        var profile=ExactCk3Build.florinCoreFullBuild(NativeWire.text(original.get("expected_ck3_version")),hello.gameSha256(),hello.adapterId());
        if(profile.filter(build->hello.adapterId().equals(build.coreFullAdapterId())).isEmpty()
                ||!hello.capabilities().contains(NativeFreshSnapshotPort.CAPABILITY)||!hello.capabilities().contains("game.state.snapshot"))
            throw new IOException("Full clock source requires exact Florin and both advertised full-state capabilities");
        requireCurrentFull111Source(profile.orElseThrow());
        return profile.orElseThrow();
    }
    /** Independent exact source custody; identical wire labels do not select or interchange artifact profiles. */
    private void requireCurrentFull111Source(ExactCk3Build profile)throws IOException {
        if(profile==ExactCk3Build.CK3_121003_STEAM_26785313_FULL111) {
            if(full114Source!=null)requireFull114Source();
            else requireFull112Source();
        }
    }
    /** Identity DATA from this already-held source. No READ, open/reconnect, delivery consumption or submit permit. */
    public synchronized ExactCk3Build fullClockProfileForPreparation(org.xar.ck3.control.application.action.ActionCommand command)throws IOException {
        Objects.requireNonNull(command);
        if(closed||terminalFailure!=null||hello==null||applicationExitAttempted)
            throw new IOException("clock preparation requires its already-held source");
        if(!(command.origin() instanceof CommandOrigin.Gameplay)
                ||!chronologyClock.instant().isBefore(command.deadline())
                ||!command.source().machineId().equals(config.machineId())
                ||!command.before().game().equals(config.game())||!command.sessionId().equals(config.sessionId())
                ||!command.source().exactBuild().equalsIgnoreCase(hello.gameSha256()))
            throw new IOException("clock preparation DATA crossed its original command source, Game, session or deadline");
        verifyEndpoint();
        // Stable source identity is not a new Full occurrence. In particular, a previous write's invalidation
        // cannot be cleared or requalified here; the existing coordinator/submit guards own those checks.
        return requireFlorinFullClockSource();
    }
    private void requireFullClockOriginal(FullClockReceived actual,Instant deadline)throws IOException{
        Objects.requireNonNull(deadline);
        if(actual.issuer!=this||closed||terminalFailure!=null||hello==null)throw new IOException("Full clock requires its identical live held receiver");
        var now=chronologyClock.instant();
        if(!now.isBefore(deadline)||!now.isBefore(actual.validUntil)||deadline.isAfter(actual.validUntil))
            throw new IOException("Full clock cannot extend or escape its original full READ window");
        verifyHeld(deadline);requireFlorinFullClockSource();
        var frame=actual.frame();var ack=actual.original.acknowledgement();
        var custody=ack.custody().orElseThrow(()->new IOException("actual Full clock read custody unavailable"));custody.verify(ack);
        if(heldSnapshotInvalidated||acceptedSnapshotFrame!=frame||!frame.session().equals(session())
                ||!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)
                ||!originalRequestChronology(ack.requestId()).filter(custody::equals).isPresent()
                ||custody.writeEntered().observedAt().isBefore(helloObservedAt)
                ||custody.responseReceived().observedAt().isAfter(now)||custody.responseReceived().observedAt().isAfter(actual.validUntil))
            throw new IOException("Full clock source is stale or crossed original Game/session/connection/custody");
        acceptedSnapshotRevision(frame).requireOriginal(frame);
        NativeFreshSnapshotPort.verifyOriginal(ack,frame,actual.original.snapshotReceived());
        requireFullSnapshotBuild((NativeWire.Snapshot)NativeWire.decode(frame.originalPacket()));
        var state=NativeWire.object(NativeWire.parse(frame.state().bytes()));
        // READ base support never expands the existing BB3 zero-Army control/action basis.
        if(requireFlorinFullClockSource()==ExactCk3Build.CK3_1210_STEAM_26757580
                ||requireFlorinFullClockSource()==ExactCk3Build.CK3_121003_STEAM_26785313_FULL111)
            StrictJson.require(state.path("player_armies").isArray()&&state.path("player_armies").isEmpty(),
                    "BB3 Full clock still requires its independently qualified empty-Army action basis");
        for(var entry:new com.fasterxml.jackson.databind.JsonNode[]{state.get("paused"),state.get("map_ready"),
                NativeWire.object(state.get("played_character")).get("alive")})
            if(entry==null||!entry.isBoolean()||!entry.booleanValue())
                throw new IOException("Full clock source requires its actual living paused map");
    }
    public sealed interface EventOptionsRead permits EventOptionsReceived, EventOptionsUnavailable {
        DispatchOutcome original();
    }
    /** Private producer occurrence: callers cannot synthesize the enabled option list or borrow another Full. */
    public static final class EventOptionsReceived implements EventOptionsRead {
        private final NativeGameTransport issuer;
        private final FullClockReceived before;
        private final AckReceived original;
        private final EventOptionControlResult.Assessment assessment;
        private final Instant validUntil;
        private EventOptionsReceived(NativeGameTransport issuer, FullClockReceived before, AckReceived original,
                EventOptionControlResult.Assessment assessment, Instant validUntil) {
            this.issuer=issuer;this.before=before;this.original=original;this.assessment=assessment;this.validUntil=validUntil;
        }
        @Override public AckReceived original(){return original;}
        public ObservedFrame fullFrame(){return before.frame();}
        public int eventInstanceId(){return assessment.eventInstanceId();}
        public List<EventOptionControlResult.Option> options(){return assessment.options();}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant deadline)throws IOException {
            Objects.requireNonNull(actual).requireEventOptionsOriginal(this,deadline);
        }
    }
    public record EventOptionsUnavailable(DispatchOutcome original,String reason)implements EventOptionsRead {
        public EventOptionsUnavailable {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    public synchronized EventOptionsRead readEventOptionsReceived(FullClockReceived before,int eventInstanceId,Instant deadline)throws InterruptedException {
        if(before!=null&&before.issuer==this&&before.eventOptionsRead!=null) {
            try {requireFullClockOriginal(before,deadline);requireEventInstance(before,eventInstanceId);
                if(before.eventOptionsRead instanceof EventOptionsReceived received)requireEventOptionsOriginal(received,deadline);
                return before.eventOptionsRead;
            }catch(IOException|RuntimeException invalid){return new EventOptionsUnavailable(zero("event-options-"+UUID.randomUUID(),reason(invalid)),reason(invalid));}
        }
        String id="event-options-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome original;
        try {
            Objects.requireNonNull(before);requireFullClockOriginal(before,deadline);requireEventInstance(before,eventInstanceId);
            if(applicationExitAttempted||before.writeAttempted||before.eventOptionsReadAttempted||unresolvedFullClockControl!=null
                    ||unresolvedCoreControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("event options require an unused actual paused Full without uncertain controls");
            var prepared=FullSnapshotEventOptionControl.query(before.frame().snapshotId(),before.frame().nativeRevision(),deadline,eventInstanceId);
            if(!hello.capabilities().contains(prepared.requiredCapability().orElseThrow()))throw new IOException("actual event option query capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            byte[] packet=NativeWire.execute(id,prepared.step(),before.frame().nativeRevision(),prepared.additionalFields().bytes());
            original=retainReadOutcome(dispatchRead(id,packet,deadline,()->{
                requireBackgroundAtCoreWrite();
                try {requireFullClockOriginal(before,deadline);requireEventInstance(before,eventInstanceId);}catch(IOException invalid){throw new UncheckedIOException(invalid);}
                if(before.writeAttempted||before.eventOptionsReadAttempted)throw new IllegalStateException("event option Full source is consumed");
                before.eventOptionsReadAttempted=true;
            }));
        }catch(IOException|RuntimeException invalid){
            original=sentRequestIds.contains(id)?new Unknown(id,"event query failed after write; retain original: "+reason(invalid),retainedOutbound(id),Optional.empty()):zero(id,reason(invalid));
        }
        EventOptionsRead read;
        try {
            if(!(original instanceof AckReceived ack))throw new IOException("event query has no actual received ACK");
            var assessment=EventOptionControlResult.decode(ack,FullSnapshotEventOptionControl.QUERY_STEP,before.frame().nativeRevision(),eventInstanceId);
            if(assessment.disposition()!=EventOptionControlResult.Disposition.OBSERVED)throw new IOException("event query did not observe options: "+assessment.status());
            var received=new EventOptionsReceived(this,before,ack,assessment,deadline);requireEventOptionsOriginal(received,deadline);read=received;
        }catch(IOException|RuntimeException invalid){read=new EventOptionsUnavailable(original,reason(invalid));}
        if(before!=null&&before.issuer==this&&before.eventOptionsReadAttempted)before.eventOptionsRead=read;
        return read;
    }
    private static void requireEventInstance(FullClockReceived before,int eventInstanceId)throws IOException {
        var state=NativeWire.object(NativeWire.parse(before.frame().state().bytes()));
        var active=NativeWire.object(state.get("active_event"));
        int actual=NativeWire.integer(active.get("instance_id"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();
        if(eventInstanceId<=0||actual!=eventInstanceId)throw new IOException("event occurrence differs from actual Full");
    }
    private void requireEventOptionsOriginal(EventOptionsReceived actual,Instant deadline)throws IOException {
        if(actual.issuer!=this||deadline==null||deadline.isAfter(actual.validUntil)||!chronologyClock.instant().isBefore(actual.validUntil))
            throw new IOException("event option occurrence escaped its receiver or original deadline");
        requireFullClockOriginal(actual.before,deadline);requireEventInstance(actual.before,actual.eventInstanceId());
        var custody=actual.original.custody().orElseThrow(()->new IOException("actual event query chronology unavailable"));custody.verify(actual.original);
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)
                ||!originalRequestChronology(actual.original.requestId()).filter(custody::equals).isPresent()
                ||custody.responseReceived().observedAt().isAfter(chronologyClock.instant())||custody.responseReceived().observedAt().isAfter(actual.validUntil))
            throw new IOException("event option occurrence crossed actual Game/session/connection/custody");
        var again=EventOptionControlResult.decode(actual.original,FullSnapshotEventOptionControl.QUERY_STEP,actual.before.frame().nativeRevision(),actual.eventInstanceId());
        if(!again.equals(actual.assessment))throw new IOException("event option occurrence changed from original ACK");
    }
    /** One standard option command from the actual enabled query. UNKNOWN retains the shared Full-control stop. */
    public synchronized DispatchOutcome submitEventOption(EventOptionsReceived options,NativeRequest prepared,Instant deadline)throws InterruptedException {
        if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;
        String id="event-select-"+UUID.randomUUID().toString().replace("-","");
        try {
            Objects.requireNonNull(options);Objects.requireNonNull(prepared);requireEventOptionsOriginal(options,deadline);
            var before=options.before;
            if(applicationExitAttempted||before.writeAttempted||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("event selection cannot borrow another continuation or reuse a write");
            int index=FullSnapshotEventOptionControl.selectedIndex(prepared.step());
            if(options.options().stream().noneMatch(option->option.nativeOptionIndex()==index&&option.enabled()))throw new IOException("requested authored option was not observed enabled");
            var expected=FullSnapshotEventOptionControl.select(before.frame().snapshotId(),before.frame().nativeRevision(),deadline,options.eventInstanceId(),index);
            if(!prepared.equals(expected))throw new IOException("event selection differs from exact Full/event/index preparation");
            if(!hello.capabilities().contains(prepared.requiredCapability().orElseThrow()))throw new IOException("actual event selection capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            var outcome=dispatch(id,NativeWire.execute(id,prepared.step(),before.frame().nativeRevision(),prepared.additionalFields().bytes()),deadline,()->{
                requireBackgroundAtCoreWrite();
                try {requireEventOptionsOriginal(options,deadline);}catch(IOException invalid){throw new UncheckedIOException(invalid);}
                if(before.writeAttempted)throw new IllegalStateException("original Full already entered a mutation");
                before.writeAttempted=true;heldSnapshotInvalidated=true;
            });
            if(outcome instanceof AckReceived ack) {
                try {
                    var assessment=EventOptionControlResult.decode(ack,prepared.step(),before.frame().nativeRevision(),options.eventInstanceId());
                    if(assessment.disposition()!=EventOptionControlResult.Disposition.UNKNOWN)return ack;
                    indeterminateFullClockAcknowledgement=ack;
                    outcome=new Unknown(ack.requestId(),"event selection effect uncertain; retain original and never replay",ack.outbound().orElseThrow().originalPacket(),Optional.of(ack.originalFrame()));
                }catch(IOException|RuntimeException invalid){
                    indeterminateFullClockAcknowledgement=ack;
                    outcome=new Unknown(ack.requestId(),"event selection ACK invalid; retain original and never replay: "+reason(invalid),ack.outbound().orElseThrow().originalPacket(),Optional.of(ack.originalFrame()));
                }
            }
            if(outcome instanceof Unknown unknown)unresolvedFullClockControl=unknown;
            return outcome;
        }catch(IOException|RuntimeException invalid){
            if(sentRequestIds.contains(id)) {
                unresolvedFullClockControl=new Unknown(id,"event selection failed after write; retain original and never replay: "+reason(invalid),retainedOutbound(id),Optional.empty());
                return unresolvedFullClockControl;
            }
            return zero(id,reason(invalid));
        }
    }
    public sealed interface GuiRead permits GuiReceived, GuiUnavailable {
        DispatchOutcome original();
    }
    /** Receiver-owned query occurrence. Equal serialized GUI data cannot replace its actual source. */
    public static final class GuiReceived implements GuiRead {
        private final NativeGameTransport issuer;
        private final FullClockReceived before;
        private final AckReceived original;
        private final GuiControlResult.Assessment assessment;
        private final Instant validUntil;
        private GuiReceived(NativeGameTransport issuer,FullClockReceived before,AckReceived original,
                GuiControlResult.Assessment assessment,Instant validUntil) {
            this.issuer=issuer;this.before=before;this.original=original;this.assessment=assessment;this.validUntil=validUntil;
        }
        @Override public AckReceived original(){return original;}
        public ObservedFrame fullFrame(){return before.frame();}
        public String rootName(){return assessment.rootName();}
        public BigInteger queryGeneration(){return assessment.queryGeneration();}
        public List<GuiControlResult.Control> controls(){return assessment.widgets();}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant deadline)throws IOException {
            Objects.requireNonNull(actual).requireGuiOriginal(this,deadline);
        }
    }
    public record GuiUnavailable(DispatchOutcome original,String reason)implements GuiRead {
        public GuiUnavailable {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    public synchronized GuiRead readGuiReceived(FullClockReceived before,String rootName,Instant deadline)throws InterruptedException {
        if(before!=null&&before.issuer==this&&before.guiRead!=null) {
            try {requireFullClockOriginal(before,deadline);
                if(before.guiRead instanceof GuiReceived received) {
                    requireGuiOriginal(received,deadline);
                    if(!received.rootName().equals(rootName))throw new IOException("cached GUI occurrence belongs to another root");
                }
                return before.guiRead;
            }catch(IOException|RuntimeException invalid){return new GuiUnavailable(zero("gui-query-"+UUID.randomUUID(),reason(invalid)),reason(invalid));}
        }
        String id="gui-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome original;
        try {
            Objects.requireNonNull(before);requireFullClockOriginal(before,deadline);
            if(applicationExitAttempted||before.writeAttempted||before.guiReadAttempted||unresolvedFullClockControl!=null
                    ||unresolvedCoreControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("GUI query requires an unused actual paused Full without uncertain controls");
            var prepared=FullSnapshotGuiControl.query(before.frame().snapshotId(),before.frame().nativeRevision(),deadline,rootName);
            if(!hello.capabilities().contains(prepared.requiredCapability().orElseThrow()))throw new IOException("actual GUI query capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            original=retainReadOutcome(dispatchRead(id,NativeWire.execute(id,prepared.step(),before.frame().nativeRevision(),prepared.additionalFields().bytes()),deadline,()->{
                requireBackgroundAtCoreWrite();
                try {requireFullClockOriginal(before,deadline);}catch(IOException invalid){throw new UncheckedIOException(invalid);}
                if(before.writeAttempted||before.guiReadAttempted)throw new IllegalStateException("GUI Full source is consumed");
                before.guiReadAttempted=true;
            }));
        }catch(IOException|RuntimeException invalid) {
            original=sentRequestIds.contains(id)?new Unknown(id,"GUI query failed after write; retain original: "+reason(invalid),retainedOutbound(id),Optional.empty()):zero(id,reason(invalid));
        }
        GuiRead read;
        try {
            if(!(original instanceof AckReceived ack))throw new IOException("GUI query has no actual received ACK");
            var assessment=GuiControlResult.decode(ack,FullSnapshotGuiControl.QUERY_STEP,before.frame().nativeRevision(),rootName,BigInteger.ZERO,BigInteger.ZERO);
            if(assessment.disposition()!=GuiControlResult.Disposition.OBSERVED)throw new IOException("GUI query did not observe controls: "+assessment.status());
            var received=new GuiReceived(this,before,ack,assessment,deadline);requireGuiOriginal(received,deadline);read=received;
        }catch(IOException|RuntimeException invalid){read=new GuiUnavailable(original,reason(invalid));}
        if(before!=null&&before.issuer==this&&before.guiReadAttempted)before.guiRead=read;
        return read;
    }
    private void requireGuiOriginal(GuiReceived actual,Instant deadline)throws IOException {
        if(actual.issuer!=this||deadline==null||deadline.isAfter(actual.validUntil)||!chronologyClock.instant().isBefore(actual.validUntil))
            throw new IOException("GUI occurrence escaped its receiver or original deadline");
        requireFullClockOriginal(actual.before,deadline);
        var custody=actual.original.custody().orElseThrow(()->new IOException("actual GUI query chronology unavailable"));custody.verify(actual.original);
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)
                ||!originalRequestChronology(actual.original.requestId()).filter(custody::equals).isPresent()
                ||custody.responseReceived().observedAt().isAfter(chronologyClock.instant())||custody.responseReceived().observedAt().isAfter(actual.validUntil))
            throw new IOException("GUI occurrence crossed actual Game/session/connection/custody");
        var again=GuiControlResult.decode(actual.original,FullSnapshotGuiControl.QUERY_STEP,actual.before.frame().nativeRevision(),actual.rootName(),BigInteger.ZERO,BigInteger.ZERO);
        if(!again.equals(actual.assessment))throw new IOException("GUI occurrence changed from original ACK");
    }
    /** One ordinary native control invocation from its observed enabled identity. No business completion credit. */
    public synchronized DispatchOutcome submitGuiControl(GuiReceived controls,NativeRequest prepared,Instant deadline)throws InterruptedException {
        if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;
        String id="gui-activate-"+UUID.randomUUID().toString().replace("-","");
        try {
            Objects.requireNonNull(controls);Objects.requireNonNull(prepared);requireGuiOriginal(controls,deadline);
            var before=controls.before;
            if(applicationExitAttempted||before.writeAttempted||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("GUI activation cannot borrow another continuation or reuse a write");
            var fields=NativeWire.object(NativeWire.parse(prepared.additionalFields().bytes()));
            var claim=NativeWire.object(fields.get("gui_control_v1"));
            String requestedId=NativeWire.text(claim.get("widget_id"));
            if(!requestedId.matches("[1-9][0-9]*"))throw new IOException("GUI activation requires canonical positive widget identity");
            BigInteger widgetId=new BigInteger(requestedId);
            if(controls.controls().stream().noneMatch(control->control.widgetId().equals(widgetId)&&control.activatable()))
                throw new IOException("GUI control was not observed visible, enabled and clickable");
            var expected=FullSnapshotGuiControl.activate(before.frame().snapshotId(),before.frame().nativeRevision(),deadline,controls.rootName(),controls.queryGeneration(),widgetId);
            if(!prepared.equals(expected))throw new IOException("GUI activation differs from exact Full/query/control preparation");
            if(!hello.capabilities().contains(prepared.requiredCapability().orElseThrow()))throw new IOException("actual GUI activation capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            var outcome=dispatch(id,NativeWire.execute(id,prepared.step(),before.frame().nativeRevision(),prepared.additionalFields().bytes()),deadline,()->{
                requireBackgroundAtCoreWrite();
                try {requireGuiOriginal(controls,deadline);}catch(IOException invalid){throw new UncheckedIOException(invalid);}
                if(before.writeAttempted)throw new IllegalStateException("original Full already entered a mutation");
                before.writeAttempted=true;heldSnapshotInvalidated=true;
            });
            if(outcome instanceof AckReceived ack) {
                try {
                    var assessment=GuiControlResult.decode(ack,prepared.step(),before.frame().nativeRevision(),controls.rootName(),controls.queryGeneration(),widgetId);
                    if(assessment.disposition()!=GuiControlResult.Disposition.UNKNOWN)return ack;
                    indeterminateFullClockAcknowledgement=ack;
                    outcome=new Unknown(ack.requestId(),"GUI activation effect uncertain; retain original and never replay",ack.outbound().orElseThrow().originalPacket(),Optional.of(ack.originalFrame()));
                }catch(IOException|RuntimeException invalid) {
                    indeterminateFullClockAcknowledgement=ack;
                    outcome=new Unknown(ack.requestId(),"GUI activation ACK invalid; retain original and never replay: "+reason(invalid),ack.outbound().orElseThrow().originalPacket(),Optional.of(ack.originalFrame()));
                }
            }
            if(outcome instanceof Unknown unknown)unresolvedFullClockControl=unknown;
            return outcome;
        }catch(IOException|RuntimeException invalid) {
            if(sentRequestIds.contains(id)) {
                unresolvedFullClockControl=new Unknown(id,"GUI activation failed after write; retain original and never replay: "+reason(invalid),retainedOutbound(id),Optional.empty());
                return unresolvedFullClockControl;
            }
            return zero(id,reason(invalid));
        }
    }
    public sealed interface PersonalCashRead permits PersonalCashReceived,PersonalCashReadUnavailable {
        DispatchOutcome original();
    }
    /** A private read occurrence tied to one actual Full and its original query window, without Driver authority. */
    public static final class PersonalCashReceived implements PersonalCashRead {
        private final NativeGameTransport issuer;
        private final FullClockReceived before;
        private final AckReceived original;
        private final NativeRequestChronology custody;
        private final RawCashCodec.NormalizedCurrentCash cash;
        private final PersonalCashVersion version;
        private final Instant validUntil;
        private PersonalCashReceived(NativeGameTransport issuer,FullClockReceived before,AckReceived original,
                NativeRequestChronology custody,RawCashCodec.NormalizedCurrentCash cash,Instant validUntil,PersonalCashVersion version){
            this.issuer=issuer;this.before=before;this.original=original;this.custody=custody;this.cash=cash;this.validUntil=validUntil;this.version=version;
        }
        @Override public AckReceived original(){return original;}
        public ObservedFrame fullFrame(){return before.frame();}
        public RawCashCodec.NormalizedCurrentCash cash(){return cash;}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant deadline)throws IOException{
            Objects.requireNonNull(actual).requirePersonalCashOriginal(this,deadline);
        }
    }
    public record PersonalCashReadUnavailable(DispatchOutcome original,String reason)implements PersonalCashRead {
        public PersonalCashReadUnavailable {Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    private enum PersonalCashVersion {
        LEGACY("query-war-cash-current-resources-v1","game.query.war-cash-current-resources.v1",RawCashCodec.SCHEMA),
        SIGNED_SCOPE("query-war-cash-current-resources-v2","game.query.war-cash-current-resources.v2",RawCashCodec.SIGNED_SCOPE_SCHEMA);
        final String step,capability,schema;
        PersonalCashVersion(String step,String capability,String schema){this.step=step;this.capability=capability;this.schema=schema;}
    }
    /** One read using the standard positive Native revision envelope; it does not refresh its Full source. */
    public synchronized PersonalCashRead readPersonalCashReceived(FullClockReceived before,Instant deadline)throws InterruptedException{
        return readPersonalCashReceived(before,deadline,PersonalCashVersion.LEGACY);
    }
    /** Explicit Native v2 DATA read; the default v1 read retains the qualified legacy cash scope. */
    public synchronized PersonalCashRead readPersonalCashSignedScopeReceived(FullClockReceived before,Instant deadline)throws InterruptedException{
        return readPersonalCashReceived(before,deadline,PersonalCashVersion.SIGNED_SCOPE);
    }
    private PersonalCashRead readPersonalCashReceived(FullClockReceived before,Instant deadline,PersonalCashVersion version)throws InterruptedException{
        if(before!=null&&before.issuer==this&&before.unresolvedPersonalCashRead!=null)return before.unresolvedPersonalCashRead;
        String id="personal-cash-"+UUID.randomUUID().toString().replace("-","");
        DispatchOutcome original;
        try{
            Objects.requireNonNull(before);Objects.requireNonNull(deadline);requireFullClockOriginal(before,deadline);
            if(applicationExitAttempted||before.writeAttempted||before.personalCashReadAttempted||unresolvedFullClockControl!=null
                    ||unresolvedCoreControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("personal cash requires an unused actual paused Full without active or uncertain controls");
            if(!hello.capabilities().contains(version.capability))throw new IOException("actual personal cash capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            byte[] fields=StrictJson.canonical(StrictJson.object().put("expected_snapshot_revision",before.frame().nativeRevision()));
            byte[] packet=NativeWire.execute(id,version.step,before.frame().nativeRevision(),fields);
            original=retainReadOutcome(dispatchRead(id,packet,deadline,()->{
                requireBackgroundAtCoreWrite();
                try{requireFullClockOriginal(before,deadline);}catch(IOException invalid){throw new UncheckedIOException(invalid);}
                if(before.writeAttempted||before.personalCashReadAttempted)throw new IllegalStateException("personal cash Full source is consumed");
                before.personalCashReadAttempted=true;
            }));
        }catch(IOException|RuntimeException invalid){
            if(sentRequestIds.contains(id))original=new Unknown(id,"personal cash failed after actual query write; retain original: "+reason(invalid),retainedOutbound(id),Optional.empty());
            else original=zero(id,reason(invalid));
        }
        try{
            if(!(original instanceof AckReceived ack))throw new IOException("personal cash has no actual received acknowledgement");
            var custody=originalRequestChronology(ack.requestId()).orElseThrow(()->new IOException("actual personal cash custody unavailable"));
            var cash=decodePersonalCash(ack,before,version);
            var actual=new PersonalCashReceived(this,before,ack,custody,cash,deadline,version);
            requirePersonalCashOriginal(actual,deadline);return actual;
        }catch(IOException|RuntimeException invalid){
            var unavailable=new PersonalCashReadUnavailable(original,reason(invalid));
            if(before!=null&&before.issuer==this&&original instanceof Unknown)before.unresolvedPersonalCashRead=unavailable;
            return unavailable;
        }
    }
    private RawCashCodec.NormalizedCurrentCash decodePersonalCash(AckReceived ack,FullClockReceived before,PersonalCashVersion version)throws IOException{
        if(!ack.nativeOk())throw new IOException("personal cash Native acknowledgement is not accepted");
        var result=NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow(()->new IOException("original personal cash result unavailable")).bytes()));
        if(!textEquals(result,"step",version.step))throw new IOException("personal cash result belongs to another operation");
        StrictJson.trueValue(result.get("accepted"));StrictJson.trueValue(result.get("private_build"));StrictJson.trueValue(result.get("read_only"));
        if(result.get("advertised")==null||!result.get("advertised").isBoolean()||result.get("advertised").booleanValue())
            throw new IOException("personal cash cannot claim public finance readiness");
        var raw=NativeWire.object(result.get("war_cash_current_resources"));
        if(!textEquals(raw,"schema",version.schema))throw new IOException("personal cash schema differs from its requested version");
        var projection=PersonalCashFullProjection.snapshotData(before.frame(),hello);
        var normalized=RawCashCodec.normalize(StrictJson.canonical(raw),projection.bytes());
        var state=NativeWire.object(NativeWire.parse(before.frame().state().bytes()));
        // The native Cash reader requires both Gold samples to equal its retained Full basis.
        // Absent/null wallet data stays unknown; a known value has no later-sampling exception.
        var wallet=normalized.metrics().currentTreasury();
        if(wallet.known()) {
            var fullWallet=NativeWire.object(state.get("played_character_gold"));
            var fullRaw=NativeWire.integer(fullWallet.get("raw"),BigInteger.valueOf(Long.MIN_VALUE),BigInteger.valueOf(Long.MAX_VALUE));
            var scale=BigInteger.valueOf(100000);
            NativeWire.integer(fullWallet.get("scale"),scale,scale);
            if(wallet.value().scale()!=100000||!wallet.value().raw().equals(fullRaw))
                throw new IOException("personal cash wallet differs from its actual Full");
        }
        requirePersonalCashScope(state,"active_wars","war_id",normalized.activeWarIds(),false);
        requirePersonalCashScope(state,"player_armies","army_id",normalized.playerArmyIds(),
                normalized.playerArmyIdDomain()==RawCashCodec.PlayerArmyIdDomain.FLORIN_SIGNED_FULL);
        return normalized;
    }
    private static void requirePersonalCashScope(ObjectNode state,String collection,String idField,List<BigInteger> expected,boolean signedUnits)throws IOException{
        var rows=state.get(collection);if(rows==null||!rows.isArray())throw new IOException("actual Full cash scope is unavailable: "+collection);
        var ids=new ArrayList<BigInteger>();
        for(var row:rows){
            var raw=NativeWire.object(row).get(idField);
            var id=signedUnits ? FlorinUnitFullId.fromJson(raw).asBigInteger()
                    : NativeWire.integer(raw,BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE));
            if(ids.contains(id))throw new IOException("actual Full cash scope repeats an identity");ids.add(id);
        }
        if(!ids.equals(expected))throw new IOException("personal cash scope differs from its actual Full: "+collection);
    }
    private void requirePersonalCashOriginal(PersonalCashReceived actual,Instant deadline)throws IOException{
        Objects.requireNonNull(deadline);
        if(actual.issuer!=this||closed||terminalFailure!=null||hello==null)throw new IOException("personal cash requires its identical live held receiver");
        var now=chronologyClock.instant();
        if(!now.isBefore(deadline)||!now.isBefore(actual.validUntil)||deadline.isAfter(actual.validUntil)
                ||actual.custody.responseReceived().observedAt().isAfter(now)||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)
                ||actual.custody.writeEntered().observedAt().isBefore(helloObservedAt))throw new IOException("personal cash escaped its original Full/query window");
        requireFullClockOriginal(actual.before,deadline);
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)
                ||!originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isPresent())
            throw new IOException("personal cash crossed original Game/session/connection/custody");
        actual.custody.verify(actual.original);
        if(!Arrays.equals(actual.cash.toJson(),decodePersonalCash(actual.original,actual.before,actual.version).toJson()))
            throw new IOException("personal cash differs from its original normalized data");
    }
    private Unknown unresolvedFullClockControl;
    // A real Date Status evaluation_failure is known failure DATA, not a fabricated world-dispatch UNKNOWN.
    private AckReceived failedDateEvaluation;
    private AckReceived indeterminateFullClockAcknowledgement;
    public synchronized Optional<AckReceived> originalIndeterminateFullClockAcknowledgement(String requestId){
        Objects.requireNonNull(requestId);
        return indeterminateFullClockAcknowledgement!=null&&indeterminateFullClockAcknowledgement.requestId().equals(requestId)
                ?Optional.of(indeterminateFullClockAcknowledgement):Optional.empty();
    }
    /** One prepared Native-only action, without inventing a Driver observation or writer authority. */
    public synchronized DispatchOutcome submitFullClockControl(FullClockReceived before,NativeRequest prepared,Instant deadline)throws InterruptedException{
        if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;
        String id="full-clock-"+UUID.randomUUID().toString().replace("-","");
        try {
            Objects.requireNonNull(before);Objects.requireNonNull(prepared);Objects.requireNonNull(deadline);requireFullClockOriginal(before,deadline);
            if(hotfixSave(prepared))requireMappedSave61();
            if(current112Save(prepared))requireMappedSave112();
            if(applicationExitAttempted||before.writeAttempted||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("Full clock source cannot reuse a write or borrow another active continuation");
            var expected=hotfixSave(prepared)
                    ?FullSnapshotClockControl.requestMappedSave61(requireMappedSave61(),before.frame().snapshotId(),before.frame().nativeRevision(),deadline)
                    :current112Save(prepared)
                        ?FullSnapshotClockControl.requestMappedSave112(requireMappedSave112(),before.frame().snapshotId(),before.frame().nativeRevision(),deadline)
                    :FullSnapshotClockControl.request(requireFlorinFullClockSource(),prepared.step(),before.frame().snapshotId(),before.frame().nativeRevision(),deadline);
            if(!prepared.equals(expected))throw new IOException("Full clock request differs from its exact canonical source preparation");
            requireCurrent112SpeedData(requireFlorinFullClockSource(),prepared.step(),before.frame().state());
            if(!hello.capabilities().contains(prepared.requiredCapability().orElseThrow()))throw new IOException("actual Full clock command capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            byte[] packet=NativeWire.execute(id,prepared.step(),before.frame().nativeRevision(),prepared.additionalFields().bytes());
            var outcome=dispatch(id,packet,deadline,()->{
                requireBackgroundAtCoreWrite();
                try {requireFullClockOriginal(before,deadline);}catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                if(hotfixSave(prepared))try{requireMappedSave61();}catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                if(current112Save(prepared))try{requireMappedSave112();}catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                try{requireCurrent112SpeedData(requireFlorinFullClockSource(),prepared.step(),before.frame().state());}
                catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                if(before.writeAttempted)throw new IllegalStateException("original Full clock source already entered a write");
                before.writeAttempted=true;heldSnapshotInvalidated=true;
            });
            return retainFullClockOutcome(outcome,prepared);
        }catch(IOException|RuntimeException invalid){
            if(sentRequestIds.contains(id)){
                unresolvedFullClockControl=new Unknown(id,"Full clock failed after actual write entry; never replay: "+reason(invalid),retainedOutbound(id),Optional.empty());
                return unresolvedFullClockControl;
            }
            return zero(id,reason(invalid));
        }
    }
    private static boolean fullClockPrepared(NativeRequest request){return request.additionalFields().objectFieldNames().contains("full_snapshot_clock_control");}
    private DispatchOutcome retainFullClockOutcome(DispatchOutcome outcome,NativeRequest request){
        if(outcome instanceof AckReceived ack){
            String uncertain=null;
            try {
                requireFlorinFullClockSource();
                var profile=ExactCk3Build.florinCoreFullBuild(
                        NativeWire.text(NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length))).get("expected_ck3_version")),hello.gameSha256(),hello.adapterId()).orElseThrow();
                requireFlorinFullTuple(NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes())),
                        FullSnapshotClockControlResult.SCHEMA,profile);
                var assessment=FullSnapshotClockControlResult.decode(ack,request.step());
                if(assessment.disposition()==FullSnapshotClockControlResult.Disposition.UNKNOWN)
                    uncertain="Native Full clock result is uncertain: "+assessment.queueStatus();
            }catch(IOException|RuntimeException malformed){uncertain="Native Full clock result failed its typed contract: "+reason(malformed);}
            if(uncertain!=null){
                indeterminateFullClockAcknowledgement=ack;
                unresolvedFullClockControl=new Unknown(ack.requestId(),uncertain+"; preserve original, never replay",ack.outbound().orElseThrow().originalPacket(),Optional.of(ack.originalFrame()));
                return unresolvedFullClockControl;
            }
        }
        if(outcome instanceof Unknown unknown)unresolvedFullClockControl=unknown;
        return outcome;
    }
    public sealed interface DateArmRead permits DateArmReceived,DateArmUnavailable {
        NativeFreshSnapshotPort.Result original();
    }
    /** A fresh Full source and the caller's separately frozen original advance deadline. */
    public static final class DateArmReceived implements DateArmRead {
        private final NativeGameTransport issuer;
        private final FullClockReceived full;
        private final Instant activeDeadline;
        private String armStep;
        private org.xar.ck3.control.reconciliation.LateOutcome.Status armed;
        private org.xar.ck3.control.reconciliation.LateOutcome.Status lastStatus;
        private boolean cancelAttempted;
        private DateArmReceived(NativeGameTransport issuer,FullClockReceived full,Instant activeDeadline){
            this.issuer=issuer;this.full=full;this.activeDeadline=activeDeadline;
        }
        @Override public NativeFreshSnapshotPort.Received original(){return full.original();}
        public ObservedFrame frame(){return full.frame();}
        public Instant validUntil(){return full.validUntil();}
        public Instant activeDeadline(){return activeDeadline;}
    }
    public record DateArmUnavailable(NativeFreshSnapshotPort.Result original,String reason)implements DateArmRead {
        public DateArmUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    /** The READ cutoff remains short; the active lease is frozen before that READ, never refreshed by a poll. */
    public synchronized DateArmRead readDateSentinelArmReceived(Instant originalAdvanceDeadline)throws InterruptedException{
        Objects.requireNonNull(originalAdvanceDeadline);
        var read=readFullClockFrameReceived(originalAdvanceDeadline);
        if(read instanceof FullClockReceived received)
            return new DateArmReceived(this,received,originalAdvanceDeadline);
        return new DateArmUnavailable(read.original(),((FullClockReadUnavailable)read).reason());
    }
    public synchronized DispatchOutcome submitDateSentinelArm(DateArmReceived before,NativeRequest prepared,Instant acknowledgementDeadline)throws InterruptedException{
        if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;
        String id="date-arm-"+UUID.randomUUID().toString().replace("-","");
        try{
            Objects.requireNonNull(before);Objects.requireNonNull(prepared);Objects.requireNonNull(acknowledgementDeadline);
            if(before.issuer!=this||before.armed!=null)throw new IOException("Date ARM requires its original private actual Full source");
            requireFullClockOriginal(before.full,acknowledgementDeadline);
            var expected=FullSnapshotDateSentinelArm.request(requireFlorinFullClockSource(),prepared.step(),before.frame().snapshotId(),before.frame().nativeRevision(),before.activeDeadline);
            if(!prepared.equals(expected))throw new IOException("Date ARM changed its original parent deadline or canonical Full preparation");
            var spec=AdvancePrimitives.armSpec(prepared.step());
            var state=NativeWire.object(NativeWire.parse(before.frame().state().bytes()));
            if(!state.path("date_raw").isIntegralNumber()||!state.path("date_raw").canConvertToInt()
                    ||!state.path("speed").isIntegralNumber()||!state.path("speed").canConvertToInt()
                    ||state.path("date_raw").intValue()!=spec.startingDateRaw()||state.path("speed").intValue()!=spec.speed())
                throw new IOException("Date ARM start or speed differs from its actual Full source");
            if(!chronologyClock.instant().isBefore(before.activeDeadline)||acknowledgementDeadline.isAfter(before.activeDeadline))
                throw new IOException("Date ARM cannot extend the original advance deadline");
            if(applicationExitAttempted||before.full.writeAttempted||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("Date ARM cannot reuse a write or another active continuation");
            if(!hello.capabilities().containsAll(Set.of(ClockStatusRead.ARM_CAP,ClockStatusRead.STATUS_CAP,ClockStatusRead.CANCEL_CAP,"game.guard.date-only-postday.v1")))
                throw new IOException("actual Date-only postday capabilities unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            byte[] packet=NativeWire.execute(id,prepared.step(),before.frame().nativeRevision(),prepared.additionalFields().bytes());
            var outcome=dispatch(id,packet,acknowledgementDeadline,()->{
                requireBackgroundAtCoreWrite();
                try{requireFullClockOriginal(before.full,acknowledgementDeadline);}catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                if(!chronologyClock.instant().isBefore(before.activeDeadline)||before.full.writeAttempted)throw new IllegalStateException("Date ARM original lease or write is consumed");
                before.full.writeAttempted=true;heldSnapshotInvalidated=true;
            });
            var retained=retainDateArmOutcome(outcome,prepared.step());
            if(retained instanceof AckReceived ack){
                var assessment=DateSentinelArmResult.decode(ack,prepared.step());
                if(assessment.disposition()==DateSentinelArmResult.Disposition.ARMED){
                    before.armStep=prepared.step();before.armed=assessment.status().orElseThrow();before.lastStatus=before.armed;
                }
            }
            return retained;
        }catch(IOException|RuntimeException invalid){
            if(sentRequestIds.contains(id)){
                unresolvedFullClockControl=new Unknown(id,"Date ARM failed after actual write entry; never replay: "+reason(invalid),retainedOutbound(id),Optional.empty());
                return unresolvedFullClockControl;
            }
            return zero(id,reason(invalid));
        }
    }
    private DispatchOutcome retainDateArmOutcome(DispatchOutcome outcome,String step){
        if(outcome instanceof AckReceived ack){
            String uncertain=null;
            try{if(DateSentinelArmResult.decode(ack,step).disposition()==DateSentinelArmResult.Disposition.UNKNOWN)uncertain="uncertain Date ARM result";}
            catch(IOException|RuntimeException invalid){uncertain="invalid Date ARM result: "+reason(invalid);}
            if(uncertain!=null){
                indeterminateFullClockAcknowledgement=ack;
                unresolvedFullClockControl=new Unknown(ack.requestId(),uncertain+"; preserve original, never replay",ack.outbound().orElseThrow().originalPacket(),Optional.of(ack.originalFrame()));
                return unresolvedFullClockControl;
            }
        }
        if(outcome instanceof Unknown unknown)unresolvedFullClockControl=unknown;
        return outcome;
    }
    private void requireDateSentinelOwner(DateArmReceived before,Instant deadline)throws IOException{
        Objects.requireNonNull(before);Objects.requireNonNull(deadline);
        if(before.issuer!=this||before.armed==null||closed||terminalFailure!=null)throw new IOException("actual original armed Date generation unavailable");
        verifyHeld(deadline);requireFlorinFullClockSource();
        var custody=before.original().acknowledgement().custody().orElseThrow(()->new IOException("original Date custody unavailable"));
        custody.verify(before.original().acknowledgement());
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch))throw new IOException("Date generation crossed original Game/session/connection");
    }
    /** Readonly same-generation status remains usable after the active deadline; it never extends that lease. */
    public synchronized DispatchOutcome readDateSentinelStatus(DateArmReceived before,Instant deadline)throws InterruptedException{
        String id="date-status-"+UUID.randomUUID().toString().replace("-","");
        DispatchOutcome dispatched=null;
        try{
            requireDateSentinelOwner(before,deadline);
            if(!hello.capabilities().contains(ClockStatusRead.STATUS_CAP))throw new IOException("Date status capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            var outcome=dispatchLifecycle(id,NativeWire.execute(id,ClockStatusRead.STEP,before.frame().nativeRevision(),new byte[]{'{','}'}),readDeadline(deadline),()->{});
            dispatched=outcome;
            if(outcome instanceof AckReceived ack){
                var status=ClockStatusRead.decode(ack);
                if(!status.generation().equals(before.armed.generation()))throw new IOException("Date status crossed the actual armed generation");
                if(status.state()!=org.xar.ck3.control.reconciliation.LateOutcome.State.IDLE
                        &&(status.startingDateRaw()!=before.armed.startingDateRaw()||status.targetDateRaw()!=before.armed.targetDateRaw()
                        ||status.speed()!=before.armed.speed()||status.mode()!=before.armed.mode()||status.armyCount()!=0))
                    throw new IOException("Date status changed original watch identity");
                before.lastStatus=status;
                retainDateEvaluationFailure(status,ack);
            }
            return outcome;
        }catch(IOException|RuntimeException invalid){
            if(dispatched instanceof AckReceived ack)return new Unknown(id,"Date status rejected after actual request: "+reason(invalid),ack.outbound().orElseThrow().originalPacket(),Optional.of(ack.originalFrame()));
            if(sentRequestIds.contains(id))return new Unknown(id,"Date status unavailable after actual request: "+reason(invalid),retainedOutbound(id),Optional.empty());
            return zero(id,"Date status rejected before write: "+reason(invalid));
        }
    }
    /** Pure cleanup only after the same actual generation reports paused; CANCEL never requests a pause. */
    public synchronized DispatchOutcome cancelDateSentinel(DateArmReceived before,Instant deadline)throws InterruptedException{
        return cancelDateSentinelChecked(before,null,deadline);
    }
    /** An ARMED status does not assert pause_observed; its cleanup requires this independent actual paused Full. */
    public synchronized DispatchOutcome cancelDateSentinel(DateArmReceived before,FullClockReceived actualPaused,Instant deadline)throws InterruptedException{
        return cancelDateSentinelChecked(before,Objects.requireNonNull(actualPaused),deadline);
    }
    private DispatchOutcome cancelDateSentinelChecked(DateArmReceived before,FullClockReceived actualPaused,Instant deadline)throws InterruptedException{
        if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;
        String id="date-cancel-"+UUID.randomUUID().toString().replace("-","");
        DispatchOutcome dispatched=null;
        try{
            requireDateSentinelOwner(before,deadline);
            requireDateEvaluationAvailable();
            if(before.cancelAttempted||before.lastStatus==null)throw new IOException("Date cleanup requires its actual generation and a fresh cleanup attempt");
            if(actualPaused!=null){
                requireFullClockOriginal(actualPaused,deadline);
                var initial=NativeWire.object(NativeWire.parse(before.frame().state().bytes()));
                var paused=NativeWire.object(NativeWire.parse(actualPaused.frame().state().bytes()));
                if(!org.xar.ck3.control.contracts.NativeCharacterId.fromJson(initial.path("played_character").get("character_id"))
                        .equals(org.xar.ck3.control.contracts.NativeCharacterId.fromJson(paused.path("played_character").get("character_id"))))
                    throw new IOException("Date cleanup Full crossed the original actor");
            }else if(!before.lastStatus.pauseObserved())throw new IOException("Date cleanup requires an independent paused Full or actual terminal pause observation");
            if(!hello.capabilities().contains(ClockStatusRead.CANCEL_CAP))throw new IOException("Date cleanup capability unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            String step=ClockStatusRead.CANCEL_PREFIX+before.armed.generation().decimal();
            var outcome=dispatchLifecycle(id,NativeWire.execute(id,step,before.frame().nativeRevision(),new byte[]{'{','}'}),deadline,()->{
                requireBackgroundAtCoreWrite();
                if(actualPaused!=null){
                    try{requireFullClockOriginal(actualPaused,deadline);}catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                    if(actualPaused.writeAttempted)throw new IllegalStateException("paused cleanup Full source is consumed");
                    actualPaused.writeAttempted=true;heldSnapshotInvalidated=true;
                }
                if(before.cancelAttempted)throw new IllegalStateException("Date cleanup is consumed");before.cancelAttempted=true;
            });
            dispatched=outcome;
            if(outcome instanceof AckReceived ack){
                var status=AdvancePrimitives.acknowledgedSentinel(ack,step);
                retainDateEvaluationFailure(status,ack);
                requireDateEvaluationAvailable();
                var result=NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));
                boolean idle=status.state()==org.xar.ck3.control.reconciliation.LateOutcome.State.IDLE&&textEquals(result,"status","available");
                boolean terminalUnchanged=(before.lastStatus.state()==org.xar.ck3.control.reconciliation.LateOutcome.State.TRIGGERED
                        ||before.lastStatus.state()==org.xar.ck3.control.reconciliation.LateOutcome.State.FAILED)
                        &&status.equals(before.lastStatus)&&textEquals(result,"status","available");
                if(!status.generation().equals(before.armed.generation())||(!idle&&!terminalUnchanged))
                    throw new IOException("Date CANCEL neither confirmed idle nor preserved its already terminal generation");
                before.lastStatus=status;
            }
            if(outcome instanceof Unknown unknown)unresolvedFullClockControl=unknown;
            return outcome;
        }catch(IOException|RuntimeException invalid){
            if(sentRequestIds.contains(id)){
                Optional<RawJson> original=Optional.empty();
                if(dispatched instanceof AckReceived ack){indeterminateFullClockAcknowledgement=ack;original=Optional.of(ack.originalFrame());}
                unresolvedFullClockControl=new Unknown(id,"Date cleanup uncertain after write; never replay: "+reason(invalid),retainedOutbound(id),original);return unresolvedFullClockControl;
            }
            return zero(id,reason(invalid));
        }
    }
    private Unknown unresolvedCoreControl;
    private AckReceived indeterminateCoreAcknowledgement;
    /** Passive access to the exact uncertain Native result; no query, resend, deadline or live role is created. */
    public synchronized Optional<AckReceived> originalIndeterminateCoreAcknowledgement(String requestId) {
        Objects.requireNonNull(requestId);
        return indeterminateCoreAcknowledgement!=null&&indeterminateCoreAcknowledgement.requestId().equals(requestId)
                ?Optional.of(indeterminateCoreAcknowledgement):Optional.empty();
    }
    /** The original current date claim, issued only from this receiver's actual Core occurrence. */
    public static final class CurrentDatePrepared {
        private final NativeGameTransport issuer;
        private final CoreReceived before;
        private final DateAdvanceFrameV1PublicCodec.Request request;
        private final String id;
        private final Instant deadline;
        private final NativeWire.Bytes packet;
        private boolean called,unknown,completed;
        private DispatchOutcome outcome;
        private DateAdvanceFrameV1 latestFrame;
        private DateAdvanceFrameV1 firstClaim;
        private CurrentDatePrepared(NativeGameTransport issuer,CoreReceived before,
                DateAdvanceFrameV1PublicCodec.Request request,String id,Instant deadline,byte[] packet) {
            this.issuer=issuer;this.before=before;this.request=request;this.id=id;this.deadline=deadline;this.packet=new NativeWire.Bytes(packet);
        }
        public String requestId(){return id;}
        public String operationId(){return request.operationId();}
        public Instant deadline(){return deadline;}
        public NativeWire.Bytes originalPacket(){return packet;}
        public int sourceDateRaw(){return request.expectedCore().prefix().dateRaw();}
        public Optional<DateAdvanceFrameV1> latestFrame(){return Optional.ofNullable(latestFrame);}
        public boolean originalUnknown(){return unknown;}
    }
    private CurrentDatePrepared preparedCurrentDate;
    /** Preparation archives the exact identity/body/deadline before the single action write. */
    public synchronized CurrentDatePrepared prepareCurrentDateAdvance(CoreReceived before,Instant deadline)throws IOException {
        Objects.requireNonNull(before);Objects.requireNonNull(deadline);requireCoreOriginal(before,deadline);
        if(unresolvedCoreControl!=null||unresolvedFullClockControl!=null)throw new IOException("Unresolved original control forbids another date action");
        if(activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null||applicationExitAttempted||before.controlAttempted)
            throw new IOException("Current date action requires an unused actual Core outside business/recovery/exit scopes");
        if(!(before.frame instanceof CoreFrame.Partial partial))throw new IOException("Actual partial Core required for current date action");
        if(!hello.capabilities().contains(DateAdvanceFrameV1.CAPABILITY))throw new IOException("Current date capability not advertised by the actual hello");
        if(preparedCurrentDate!=null) {
            var previous=preparedCurrentDate;
            if(previous.before==before&&previous.deadline.equals(deadline)&&!previous.called)return previous;
            if(!previous.completed||previous.unknown)throw new IOException("Original date claim unresolved; no replacement operation/id");
            var old=previous.request.expectedCore().prefix();var now=partial.prefix();
            if(now.dateRaw()<=old.dateRaw()||now.localPlayerId()!=old.localPlayerId()||now.playedCharacterId()!=old.playedCharacterId())
                throw new IOException("Next date action needs a genuinely newer Core from the same actual player/actor");
        }
        if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
        String id="date-advance-"+UUID.randomUUID().toString().replace("-","");
        String operation="date-op-"+UUID.randomUUID().toString().replace("-","");
        var request=DateAdvanceFrameV1PublicCodec.action(partial,deadline,operation);
        byte[] packet=NativeWire.execute(id,request.step().wire(),BigInteger.ZERO,DateAdvanceFrameV1PublicCodec.additionalFields(request).bytes());
        if(!DateAdvanceFrameV1PublicCodec.decodeRequestPacket(packet).equals(request))throw new IOException("Original date request roundtrip drift");
        return preparedCurrentDate=new CurrentDatePrepared(this,before,request,id,deadline,packet);
    }
    /** Exactly one action attempt. Native submitted does not establish a new day or SAVE. */
    public synchronized DispatchOutcome submitCurrentDateAdvance(CurrentDatePrepared original)throws InterruptedException {
        Objects.requireNonNull(original);
        if(original.issuer!=this||original!=preparedCurrentDate)return zero(original.id,"Foreign or superseded current date preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original date call has no reusable write authority");
        original.called=true;
        if(unresolvedCoreControl!=null)return original.outcome=unresolvedCoreControl;
        if(unresolvedFullClockControl!=null)return original.outcome=unresolvedFullClockControl;
        DispatchOutcome dispatched=null;
        try {
            requireCoreOriginal(original.before,original.deadline);
            if(original.before.controlAttempted||applicationExitAttempted||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("Original current date Core/scope already consumed");
            dispatched=dispatch(original.id,original.packet.value(),original.deadline,()->{
                requireBackgroundAtCoreWrite();
                if(original.before.controlAttempted)throw new IllegalStateException("Original current date Core consumed");
                original.before.controlAttempted=true;heldSnapshotInvalidated=true;
            });
            if(dispatched instanceof AckReceived ack) {
                var frame=DateAdvanceFrameV1PublicCodec.decodeOutcome(ack);
                original.latestFrame=frame;
                if(frame.claimFound())original.firstClaim=frame;
                if(frame.status()==DateAdvanceFrameV1.Status.INDETERMINATE||frame.accessCleanupUnknown())
                    return original.outcome=currentDateUnknown(original,"Native current date outcome indeterminate",ack);
                // A refused ACK remains the actual refused packet. It never authorizes another action.
            }
            if(dispatched instanceof Unknown unknown) {
                original.unknown=true;unresolvedCoreControl=unknown;
            }
            return original.outcome=dispatched;
        }catch(IOException|RuntimeException failure) {
            if(sentRequestIds.contains(original.id))return original.outcome=currentDateUnknown(original,"Date action unqualified after write: "+reason(failure),dispatched instanceof AckReceived ack?ack:null);
            return original.outcome=zero(original.id,reason(failure));
        }catch(InterruptedException interrupted) {
            if(!sentRequestIds.contains(original.id))throw interrupted;
            Thread.currentThread().interrupt();return original.outcome=currentDateUnknown(original,"Date action interrupted after original write entry",null);
        }
    }
    private Unknown currentDateUnknown(CurrentDatePrepared original,String why,AckReceived ack) {
        original.unknown=true;original.completed=false;
        if(ack!=null)indeterminateCoreAcknowledgement=ack;
        if(unresolvedCoreControl==null)unresolvedCoreControl=new Unknown(original.id,why+"; retain original, never replay",original.packet.value(),ack==null?Optional.empty():Optional.of(ack.originalFrame()));
        return unresolvedCoreControl;
    }
    /** Readonly status may outlive the original action deadline; it never changes the original claim body. */
    public synchronized DispatchOutcome queryCurrentDateAdvance(CurrentDatePrepared original,Instant receiveDeadline)throws InterruptedException {
        Objects.requireNonNull(original);Objects.requireNonNull(receiveDeadline);
        String id="date-status-"+UUID.randomUUID().toString().replace("-","");
        DispatchOutcome dispatched=null;
        byte[] packet=null;
        try {
            requireCurrentDateOriginalForQuery(original,receiveDeadline);
            var request=DateAdvanceFrameV1PublicCodec.query(original.request);
            packet=NativeWire.execute(id,request.step().wire(),BigInteger.ZERO,DateAdvanceFrameV1PublicCodec.additionalFields(request).bytes());
            var outcome=dispatchRead(id,packet,readDeadline(receiveDeadline),()->{});dispatched=outcome;
            if(outcome instanceof AckReceived ack) {
                var frame=DateAdvanceFrameV1PublicCodec.decodeOutcome(ack);
                if(frame.claimFound()) {
                    if(original.firstClaim!=null&&(!frame.claimSequence().equals(original.firstClaim.claimSequence())
                            ||!frame.generation().equals(original.firstClaim.generation())||!frame.ownerWitness().equals(original.firstClaim.ownerWitness())))
                        throw new IOException("Readonly status changed the original native claim/generation/before-owner");
                    if(original.firstClaim==null)original.firstClaim=frame;
                } else if(original.firstClaim!=null)throw new IOException("Readonly status lost the original native claim");
                original.latestFrame=frame;
                if(frame.status()==DateAdvanceFrameV1.Status.INDETERMINATE||frame.accessCleanupUnknown())currentDateUnknown(original,"Native date status indeterminate",ack);
                if(!original.unknown&&frame.status()==DateAdvanceFrameV1.Status.COMPLETED)original.completed=true;
            }
            return outcome;
        }catch(IOException|RuntimeException invalid) {
            // The action's original UNKNOWN remains sticky; a failed observation is not a new action.
            if(sentRequestIds.contains(id))return new Unknown(id,"Unqualified original date status observation; no action replay: "+reason(invalid),packet==null?retainedOutbound(id):packet,
                    dispatched instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());
            return zero(id,"Current date readonly status refused: "+reason(invalid));
        }
    }
    private void requireCurrentDateOriginalForQuery(CurrentDatePrepared original,Instant receiveDeadline)throws IOException {
        if(original.issuer!=this||original!=preparedCurrentDate||!original.called||!sentRequestIds.contains(original.id))
            throw new IOException("Readonly date status requires this receiver's original entered action");
        if(closed||terminalFailure!=null||hello==null||!chronologyClock.instant().isBefore(receiveDeadline))throw new IOException("Finite live receiver required for readonly date status");
        verifyHeld(receiveDeadline);
        var before=original.before;
        if(before.issuer!=this||!before.custody.session().equals(session())||!before.custody.custodyEpoch().equals(custodyEpoch)
                ||originalRequestChronology(before.original.requestId()).filter(before.custody::equals).isEmpty())throw new IOException("Date query crossed original Core receiver/session/custody");
        before.custody.verify(before.original);
        if(!CoreFramePublicCodec.decodeOutcome(before.original).equals(before.frame)
                ||!DateAdvanceFrameV1PublicCodec.decodeRequestPacket(original.packet.value()).equals(original.request))throw new IOException("Date query original Core/body changed");
        if(!Arrays.equals(retainedOutbound(original.id),original.packet.value()))throw new IOException("Date query original outbound identity changed");
        if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
    }

    /** Lifecycle observations never mint CoreReceived or infer living player status from the map flag. */
    public sealed interface SuccessionRead permits SuccessionReceived,SuccessionUnavailable { DispatchOutcome original(); }
    public static final class SuccessionReceived implements SuccessionRead {
        private final NativeGameTransport issuer;private final CurrentSuccessionLifecycleResult frame;private final AckReceived original;
        private final NativeRequestChronology custody;private final Instant validUntil;private boolean attempted;
        private SuccessionReceived(NativeGameTransport issuer,CurrentSuccessionLifecycleResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentSuccessionLifecycleResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual)throws IOException{Objects.requireNonNull(actual).requireSuccessionOriginal(this);}
    }
    public record SuccessionUnavailable(DispatchOutcome original,String reason)implements SuccessionRead {public SuccessionUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    public static final class SuccessionPrepared {
        private final NativeGameTransport issuer;private final SuccessionReceived query;private final String id;private final NativeWire.Bytes packet;
        private boolean called;private DispatchOutcome outcome;
        private SuccessionPrepared(NativeGameTransport issuer,SuccessionReceived query,String id,byte[] packet){this.issuer=issuer;this.query=query;this.id=id;this.packet=new NativeWire.Bytes(packet);}
        public String requestId(){return id;}public NativeWire.Bytes originalPacket(){return packet;}public Instant deadline(){return query.validUntil;}
    }
    private SuccessionReceived latestSuccessionQuery;
    private final java.util.Map<NativeCharacterId,SuccessionPrepared> preparedSuccessions=new java.util.LinkedHashMap<>();
    private void requireCurrentSuccessionHello(CurrentSuccessionLifecycle.Action action,Instant until)throws IOException,InterruptedException {
        awaitHello(until);verifyHeld(until);
        var raw=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
        var build=ExactCk3Build.CK3_121003_STEAM_26785313;
        if(!build.matches(NativeWire.text(raw.get("expected_ck3_version")),hello.gameSha256())||!build.coreFrameAdapterId().equals(hello.adapterId())||!hello.capabilities().contains(action.capability()))
            throw new IOException("Original exact current succession capability/tuple unavailable");
        if(applicationExitAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
            throw new IOException("Unresolved original controls or another lifecycle scope forbids a succession request");
        if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
    }
    public synchronized SuccessionRead readCurrentSuccessionDefault(Instant deadline)throws InterruptedException {
        String id="succession-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            Instant until=readDeadline(Objects.requireNonNull(deadline));requireCurrentSuccessionHello(CurrentSuccessionLifecycle.Action.QUERY_DEFAULT,until);
            var request=CurrentSuccessionLifecycle.queryRequest();var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));fields.put("core_control_deadline_unix_ms",until.toEpochMilli());
            outcome=retainReadOutcome(dispatchRead(id,NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields)),until,()->{latestSuccessionQuery=null;}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new SuccessionUnavailable(outcome,"No qualified original succession ACK");}
            var frame=CurrentSuccessionLifecycleResult.decodeOutcome(ack);
            if(frame.action()!=CurrentSuccessionLifecycle.Action.QUERY_DEFAULT)throw new IOException("Actual succession query returned another action");
            if(frame.ownerWitness().isPresent()&&!frame.ownerWitness().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Actual lifecycle owner crossed connection generation");
            if(frame.status()==CurrentSuccessionLifecycleResult.Status.INDETERMINATE||frame.effectAttempted()||frame.nativeReturned()||frame.claimSequence().signum()!=0)throw new IOException("Readonly lifecycle query uncertain or attempted an effect/claim");
            if(frame.status()!=CurrentSuccessionLifecycleResult.Status.AVAILABLE)return new SuccessionUnavailable(ack,frame.unavailableReason().orElseThrow());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Original lifecycle query custody missing"));
            var received=new SuccessionReceived(this,frame,ack,custody,until);latestSuccessionQuery=received;requireSuccessionOriginal(received);return received;
        }catch(IOException|RuntimeException invalid) {
            latestSuccessionQuery=null;
            if(sentRequestIds.contains(id)) {if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
                unresolvedCoreControl=new Unknown(id,"Original succession query unqualified after write; no effects/replay: "+reason(invalid),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());return new SuccessionUnavailable(unresolvedCoreControl,reason(invalid));}
            return new SuccessionUnavailable(zero(id,reason(invalid)),reason(invalid));
        }catch(InterruptedException interrupted) {
            if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();latestSuccessionQuery=null;
            unresolvedCoreControl=new Unknown(id,"Original succession query interrupted after write; effects blocked, no replay",retainedOutbound(id),Optional.empty());
            return new SuccessionUnavailable(unresolvedCoreControl,"Original succession query interrupted");
        }
    }
    private void requireSuccessionOriginal(SuccessionReceived query)throws IOException {
        if(query.issuer!=this||query!=latestSuccessionQuery||query.attempted||closed||terminalFailure!=null||applicationExitAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null)
            throw new IOException("Actual unused same-receiver succession query unavailable");
        Instant now=chronologyClock.instant();if(!now.isBefore(query.validUntil)||query.custody.writeEntered().observedAt().isBefore(helloObservedAt)||query.custody.responseReceived().observedAt().isAfter(now)||query.custody.responseReceived().observedAt().isAfter(query.validUntil))throw new IOException("Succession query escaped original finite chronology");
        verifyHeld(query.validUntil);
        if(!query.custody.session().equals(session())||!query.custody.custodyEpoch().equals(custodyEpoch)||originalRequestChronology(query.original.requestId()).filter(query.custody::equals).isEmpty())throw new IOException("Succession source crossed original Game/session/custody");
        query.custody.verify(query.original);
        var frame=CurrentSuccessionLifecycleResult.decodeOutcome(query.original);
        if(!frame.equals(query.frame)||frame.status()!=CurrentSuccessionLifecycleResult.Status.AVAILABLE||!frame.ownerWitness().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Actual typed lifecycle source changed");
        var request=CurrentSuccessionLifecycle.queryRequest();var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));fields.put("core_control_deadline_unix_ms",query.validUntil.toEpochMilli());
        if(!Arrays.equals(query.original.outbound().orElseThrow().originalPacket(),NativeWire.execute(query.original.requestId(),request.step(),BigInteger.ZERO,StrictJson.canonical(fields))))throw new IOException("Original succession query body/deadline changed");
    }
    public synchronized SuccessionPrepared prepareCurrentSuccessionContinue(SuccessionReceived query)throws IOException,InterruptedException {
        Objects.requireNonNull(query);requireWorldActionMode();requireSuccessionOriginal(query);requireCurrentSuccessionHello(CurrentSuccessionLifecycle.Action.CONTINUE_DEFAULT,query.validUntil);
        var frame=query.frame;var source=frame.source().orElseThrow();
        var dead=source.deadCharacter().orElseThrow();var previous=preparedSuccessions.get(dead);
        if(previous!=null){if(previous.query==query&&!previous.called)return previous;throw new IOException("Original predecessor Continue already prepared; no replacement source/ID");}
        if(preparedSuccessions.size()>=maximumSubmissions)throw new IOException("Finite original predecessor retention limit reached");
        var request=CurrentSuccessionLifecycle.continueRequest(frame.providerGeneration(),frame.querySequence(),source.deadCharacter().orElseThrow(),source.continueCharacter().orElseThrow());
        var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));fields.put("core_control_deadline_unix_ms",query.validUntil.toEpochMilli());String id="succession-continue-"+UUID.randomUUID().toString().replace("-","");
        var prepared=new SuccessionPrepared(this,query,id,NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields)));preparedSuccessions.put(dead,prepared);return prepared;
    }
    public synchronized DispatchOutcome submitCurrentSuccessionContinue(SuccessionPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);if(original.issuer!=this||preparedSuccessions.get(original.query.frame.source().orElseThrow().deadCharacter().orElseThrow())!=original)return zero(original.id,"Foreign or superseded succession preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original Continue cannot be replayed");original.called=true;
        if(unresolvedCoreControl!=null)return original.outcome=unresolvedCoreControl;if(unresolvedFullClockControl!=null)return original.outcome=unresolvedFullClockControl;
        DispatchOutcome outcome=null;
        try {
            requireWorldActionMode();requireSuccessionOriginal(original.query);requireCurrentSuccessionHello(CurrentSuccessionLifecycle.Action.CONTINUE_DEFAULT,original.deadline());
            outcome=dispatch(original.id,original.packet.value(),original.deadline(),()->{requireBackgroundAtCoreWrite();if(original.query.attempted)throw new IllegalStateException("Original Continue claim consumed");original.query.attempted=true;});
            if(outcome instanceof AckReceived ack) {
                var frame=CurrentSuccessionLifecycleResult.decodeOutcome(ack);var source=original.query.frame;
                if(frame.action()!=CurrentSuccessionLifecycle.Action.CONTINUE_DEFAULT||!frame.providerGeneration().equals(source.providerGeneration())||!frame.querySequence().equals(source.querySequence()))throw new IOException("Continue changed original action/private lease");
                if(frame.ownerWitness().isPresent()&&!frame.ownerWitness().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Continue ACK crossed actual connection owner");
                if(frame.source().isPresent()&&(!frame.source().orElseThrow().deadCharacter().equals(source.source().orElseThrow().deadCharacter())||!frame.source().orElseThrow().continueCharacter().equals(source.source().orElseThrow().continueCharacter())))throw new IOException("Continue ACK changed original predecessor/heir source");
                if(frame.status()==CurrentSuccessionLifecycleResult.Status.INDETERMINATE||frame.effectAttempted()&&frame.status()!=CurrentSuccessionLifecycleResult.Status.DISPATCHED)throw new IOException("Native Continue effect indeterminate; never replay");
            }
            if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return original.outcome=outcome;
        }catch(IOException|RuntimeException invalid) {
            if(sentRequestIds.contains(original.id)){if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;unresolvedCoreControl=new Unknown(original.id,"Original Continue unqualified after write; never replay: "+reason(invalid),original.packet.value(),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());return original.outcome=unresolvedCoreControl;}
            return original.outcome=zero(original.id,reason(invalid));
        }catch(InterruptedException interrupted) {
            if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(original.id,"Original Continue interrupted after write; no replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;
        }
    }

    /** Readonly target query, bound to this receiver's original Core and native response custody. */
    /** Actual UI query under the same receiver's original current Core. */
    public sealed interface DjcUiRead permits DjcUiReceived,DjcUiUnavailable {DispatchOutcome original();}
    public static final class DjcUiReceived implements DjcUiRead {
        private final NativeGameTransport issuer;private final CoreReceived before;private final NativeCharacterId target;
        private final CurrentDjcTargetWarQueryResult.CasusBelliKey cb;private final CurrentDjcDeclarationUiResult frame;
        private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private boolean actionAttempted;private DjcUiPrepared prepared;
        private DjcUiReceived(NativeGameTransport issuer,CoreReceived before,NativeCharacterId target,CurrentDjcTargetWarQueryResult.CasusBelliKey cb,
                CurrentDjcDeclarationUiResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.before=before;this.target=target;this.cb=cb;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentDjcDeclarationUiResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant until)throws IOException{Objects.requireNonNull(actual).requireDjcUiOriginal(this,until);}
    }
    public record DjcUiUnavailable(DispatchOutcome original,String reason)implements DjcUiRead {public DjcUiUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    public static final class DjcUiChoice {
        private final DjcUiReceived query;private final CurrentDjcDeclarationUiSource.Choice actual;
        private DjcUiChoice(DjcUiReceived query,CurrentDjcDeclarationUiSource.Choice actual){this.query=query;this.actual=actual;}
        public CurrentDjcDeclarationUiSource.SelectedTuple tuple(){return actual.tuple();}
    }
    public static final class DjcUiPrepared {
        private final NativeGameTransport issuer;private final DjcUiReceived query;private final DjcUiChoice choice;
        private final CurrentDjcDeclarationUi.Action action;private final String id;private final NativeWire.Bytes packet;private final Instant deadline;
        private boolean called;private DispatchOutcome outcome;
        private DjcUiPrepared(NativeGameTransport issuer,DjcUiReceived query,DjcUiChoice choice,CurrentDjcDeclarationUi.Action action,String id,byte[] packet,Instant deadline){this.issuer=issuer;this.query=query;this.choice=choice;this.action=action;this.id=id;this.packet=new NativeWire.Bytes(packet);this.deadline=deadline;}
        public String requestId(){return id;}public NativeWire.Bytes originalPacket(){return packet;}public Instant deadline(){return deadline;}
        public CurrentDjcDeclarationUi.Action action(){return action;}
    }
    public static final class DjcUiPendingSend {
        private final NativeGameTransport issuer;private final DjcUiPrepared send;private final AckReceived original;private final CurrentDjcDeclarationUiResult frame;
        private DjcUiWarningReady latestReady;private DjcUiWarningPrepared prepared;private boolean acceptAttempted;
        private DjcUiPendingSend(NativeGameTransport issuer,DjcUiPrepared send,AckReceived original,CurrentDjcDeclarationUiResult frame){this.issuer=issuer;this.send=send;this.original=original;this.frame=frame;}
        public AckReceived original(){return original;}public Instant deadline(){return send.deadline;}
    }
    public sealed interface DjcUiWarningRead permits DjcUiWarningReady,DjcUiWarningWaiting,DjcUiWarningUnavailable {DispatchOutcome original();}
    public static final class DjcUiWarningWaiting implements DjcUiWarningRead {
        private final CurrentDjcDeclarationUiResult frame;private final AckReceived original;private final Instant validUntil;
        private DjcUiWarningWaiting(CurrentDjcDeclarationUiResult frame,AckReceived original,Instant until){this.frame=frame;this.original=original;validUntil=until;}
        public CurrentDjcDeclarationUiResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
    }
    public static final class DjcUiWarningReady implements DjcUiWarningRead {
        private final NativeGameTransport issuer;private final DjcUiPendingSend pending;private final CurrentDjcDeclarationUiResult frame;
        private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private DjcUiWarningReady(NativeGameTransport issuer,DjcUiPendingSend pending,CurrentDjcDeclarationUiResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.pending=pending;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentDjcDeclarationUiResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
    }
    public record DjcUiWarningUnavailable(DispatchOutcome original,String reason)implements DjcUiWarningRead {public DjcUiWarningUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    public static final class DjcUiWarningPrepared {
        private final NativeGameTransport issuer;private final DjcUiWarningReady ready;private final String id;private final NativeWire.Bytes packet;
        private boolean called;private DispatchOutcome outcome;
        private DjcUiWarningPrepared(NativeGameTransport issuer,DjcUiWarningReady ready,String id,byte[] packet){this.issuer=issuer;this.ready=ready;this.id=id;this.packet=new NativeWire.Bytes(packet);}
        public String requestId(){return id;}public NativeWire.Bytes originalPacket(){return packet;}public Instant deadline(){return ready.pending.deadline();}
    }
    private DjcUiReceived latestDjcUi;private DjcUiPendingSend pendingDjcUiSend;
    private byte[] djcUiPacket(String id,CurrentDjcDeclarationUi.Action action,CoreReceived before,NativeCharacterId target,
            CurrentDjcTargetWarQueryResult.CasusBelliKey cb,BigInteger provider,BigInteger query,BigInteger choice,BigInteger origin,Instant originalDeadline)throws IOException {
        if(!(before.frame instanceof CoreFrame.Partial core))throw new IOException("Exact current Core DATA required");
        var request=CurrentDjcDeclarationUi.request(action,core,target,cb,provider,query,choice,origin);
        var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));fields.put("core_control_deadline_unix_ms",originalDeadline.toEpochMilli());
        return NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
    }
    public synchronized DjcUiRead readCurrentDjcDeclarationUi(CoreReceived before,NativeCharacterId target,CurrentDjcTargetWarQueryResult.CasusBelliKey cb,Instant deadline)throws InterruptedException {
        String id="djc-ui-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            Objects.requireNonNull(before);Objects.requireNonNull(target);Objects.requireNonNull(cb);requireCoreOriginal(before,deadline);
            if(applicationExitAttempted||before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||pendingDjcUiSend!=null&&!pendingDjcUiSend.acceptAttempted||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)throw new IOException("Current UI query cannot bypass an unresolved or pending action");
            if(!hello.capabilities().contains(CurrentDjcDeclarationUi.Action.QUERY_UI.capability()))throw new IOException("Actual current UI query capability absent");
            Instant until=readDeadline(deadline);if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
            byte[] packet=djcUiPacket(id,CurrentDjcDeclarationUi.Action.QUERY_UI,before,target,cb,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,until);
            outcome=retainReadOutcome(dispatchRead(id,packet,until,()->{requireBackgroundAtCoreWrite();try{requireCoreOriginal(before,until);}catch(IOException invalid){throw new UncheckedIOException(invalid);}if(before.controlAttempted)throw new IllegalStateException("UI source Core consumed before write");latestDjcUi=null;}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new DjcUiUnavailable(outcome,"Actual UI query has no qualified ACK");}
            var frame=CurrentDjcDeclarationUiResult.decodeOutcome(ack);requireDjcUiFrame(frame,CurrentDjcDeclarationUi.Action.QUERY_UI,before,target,cb);
            if(!frame.nativeOk())return new DjcUiUnavailable(ack,frame.unavailableReason().orElseThrow());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual UI query custody absent"));
            var received=new DjcUiReceived(this,before,target,cb,frame,ack,custody,until);latestDjcUi=received;requireDjcUiOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){latestDjcUi=null;return new DjcUiUnavailable(djcUiFailure(id,outcome,invalid),reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();latestDjcUi=null;unresolvedCoreControl=new Unknown(id,"Current UI read interrupted after write; no new action authority",retainedOutbound(id),Optional.empty());return new DjcUiUnavailable(unresolvedCoreControl,"Original UI query interrupted");}
    }
    private void requireDjcUiFrame(CurrentDjcDeclarationUiResult frame,CurrentDjcDeclarationUi.Action action,CoreReceived before,NativeCharacterId target,CurrentDjcTargetWarQueryResult.CasusBelliKey cb)throws IOException {
        if(frame.action()!=action||frame.status()==CurrentDjcDeclarationUiResult.Status.INDETERMINATE||!frame.cleanupKnown())throw new IOException("Current UI action/source cleanup is unqualified");
        if(frame.factsBefore().isPresent()&&!frame.factsBefore().orElseThrow().equals(((CoreFrame.Partial)before.frame).prefix()))throw new IOException("Actual UI Core differs from original source");
        if(frame.ownerWitness().isPresent()&&!frame.ownerWitness().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Current UI owner crossed original connection");
        if(frame.source().isPresent()&&(!frame.source().orElseThrow().target().equals(target)||frame.source().orElseThrow().casusBelli()!=cb))throw new IOException("Current UI target/CB source differs from actual intent");
    }
    private void requireDjcUiOriginal(DjcUiReceived actual,Instant until)throws IOException {
        if(actual==null||actual.issuer!=this||actual!=latestDjcUi||actual.actionAttempted||actual.before.controlAttempted||applicationExitAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||pendingDjcUiSend!=null&&!pendingDjcUiSend.acceptAttempted)throw new IOException("Identical unused private current UI query required");
        requireCoreOriginal(actual.before,until);Instant now=chronologyClock.instant();
        if(until.isAfter(actual.validUntil)||!now.isBefore(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)throw new IOException("UI query escaped original Core/deadline chronology");
        requireDjcUiCustody(actual.original,actual.custody);var decoded=CurrentDjcDeclarationUiResult.decodeOutcome(actual.original);
        if(!decoded.equals(actual.frame)||decoded.status()!=CurrentDjcDeclarationUiResult.Status.AVAILABLE)throw new IOException("UI query is not the identical actual available observation");
        requireDjcUiFrame(decoded,CurrentDjcDeclarationUi.Action.QUERY_UI,actual.before,actual.target,actual.cb);
        if(!Arrays.equals(actual.original.outbound().orElseThrow().originalPacket(),djcUiPacket(actual.original.requestId(),CurrentDjcDeclarationUi.Action.QUERY_UI,actual.before,actual.target,actual.cb,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,actual.validUntil)))throw new IOException("Original UI request body/deadline changed");
    }
    private void requireDjcUiCustody(AckReceived ack,NativeRequestChronology custody)throws IOException {
        custody.verify(ack);if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)||originalRequestChronology(ack.requestId()).filter(custody::equals).isEmpty())throw new IOException("Current UI response crossed original Game/session/custody");
    }
    public synchronized DjcUiChoice bindCurrentDjcChoice(DjcUiReceived query,CurrentDjcDeclarationUiSource.Choice actual)throws IOException {
        Objects.requireNonNull(actual);requireDjcUiOriginal(query,query.validUntil);
        if(!query.frame.source().orElseThrow().permitsSelection(actual))throw new IOException("Exact enabled private query row required; no ordinal or reconstructed tuple");return new DjcUiChoice(query,actual);
    }
    public synchronized DjcUiPrepared prepareCurrentDjcUiOpen(DjcUiReceived query)throws IOException{return prepareDjcUi(query,CurrentDjcDeclarationUi.Action.OPEN_UI,null);}
    public synchronized DjcUiPrepared prepareCurrentDjcUiSelection(DjcUiChoice choice)throws IOException {Objects.requireNonNull(choice);return prepareDjcUi(choice.query,CurrentDjcDeclarationUi.Action.SELECT_CHOICE,choice);}
    public synchronized DjcUiPrepared prepareCurrentDjcUiSend(DjcUiReceived query)throws IOException{return prepareDjcUi(query,CurrentDjcDeclarationUi.Action.SEND_UI,null);}
    private DjcUiPrepared prepareDjcUi(DjcUiReceived query,CurrentDjcDeclarationUi.Action action,DjcUiChoice choice)throws IOException {
        if(query!=null&&query.issuer==this&&query.prepared!=null){if(query.prepared.action!=action||query.prepared.choice!=choice)throw new IOException("One exact effect per actual UI query; cannot replace intent");return query.prepared;}
        requireDjcUiOriginal(query,query.validUntil);var source=query.frame.source().orElseThrow();
        if(!hello.capabilities().contains(action.capability()))throw new IOException("Actual fixed UI action capability absent");
        boolean admissible=switch(action){case OPEN_UI->source.permitsOpen();case SELECT_CHOICE->choice!=null&&choice.query==query&&source.permitsSelection(choice.actual);case SEND_UI->source.permitsSend();default->false;};
        if(!admissible)throw new IOException("Actual native UI before-source does not permit this fixed action");
        if(action==CurrentDjcDeclarationUi.Action.SEND_UI&&(!hello.capabilities().contains(CurrentDjcDeclarationUi.Action.QUERY_WARNING.capability())||!hello.capabilities().contains(CurrentDjcDeclarationUi.Action.ACCEPT_WARNING.capability())))throw new IOException("Cannot Send without actual warning readiness and once acceptance capabilities");
        String id="djc-ui-action-"+UUID.randomUUID().toString().replace("-","");byte[] packet=djcUiPacket(id,action,query.before,query.target,query.cb,query.frame.providerGeneration(),query.frame.querySequence(),choice==null?BigInteger.ZERO:choice.actual.nativeToken(),BigInteger.ZERO,query.validUntil);
        return query.prepared=new DjcUiPrepared(this,query,choice,action,id,packet,query.validUntil);
    }
    public synchronized DispatchOutcome submitCurrentDjcUi(DjcUiPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);if(original.issuer!=this||original.query.prepared!=original)return zero(original.id,"Foreign current UI preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original current UI call has no reusable write authority");original.called=true;DispatchOutcome outcome=null;
        try {
            var query=original.query;requireDjcUiOriginal(query,original.deadline);
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
            if(!Arrays.equals(original.packet.value(),djcUiPacket(original.id,original.action,query.before,query.target,query.cb,query.frame.providerGeneration(),query.frame.querySequence(),original.choice==null?BigInteger.ZERO:original.choice.actual.nativeToken(),BigInteger.ZERO,original.deadline)))throw new IOException("Prepared UI packet body drift");
            outcome=dispatch(original.id,original.packet.value(),original.deadline,()->{requireBackgroundAtCoreWrite();try{requireDjcUiOriginal(query,original.deadline);}catch(IOException invalid){throw new UncheckedIOException(invalid);}query.actionAttempted=true;query.before.controlAttempted=true;heldSnapshotInvalidated=true;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return original.outcome=unknown;}
            if(outcome instanceof AckReceived ack){var frame=CurrentDjcDeclarationUiResult.decodeOutcome(ack);requireDjcUiFrame(frame,original.action,query.before,query.target,query.cb);
                if(!frame.providerGeneration().equals(query.frame.providerGeneration())||!frame.querySequence().equals(query.frame.querySequence()))throw new IOException("UI effect ACK changed original private lease");
                if(original.action==CurrentDjcDeclarationUi.Action.SEND_UI&&frame.status()==CurrentDjcDeclarationUiResult.Status.SEND_DISPATCHED)pendingDjcUiSend=new DjcUiPendingSend(this,original,ack,frame);
            }return original.outcome=outcome;
        }catch(IOException|RuntimeException invalid){return original.outcome=djcUiFailure(original.id,outcome,invalid);}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(original.id,"Current UI effect interrupted after write; never replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;}
    }
    private DispatchOutcome djcUiFailure(String id,DispatchOutcome outcome,Exception invalid) {
        if(!sentRequestIds.contains(id))return zero(id,reason(invalid));
        if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
        unresolvedCoreControl=new Unknown(id,"Current UI original source/custody unqualified after write; no replay: "+reason(invalid),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());return unresolvedCoreControl;
    }

    public synchronized DjcUiPendingSend retainCurrentDjcUiSend(AckReceived actualSend)throws IOException {
        if(pendingDjcUiSend==null||pendingDjcUiSend.original!=actualSend)throw new IOException("Identical actual Send ACK from this receiver required");
        requireDjcUiPending(pendingDjcUiSend,pendingDjcUiSend.deadline());return pendingDjcUiSend;
    }
    private void requireDjcUiPending(DjcUiPendingSend pending,Instant until)throws IOException {
        if(pending==null||pending.issuer!=this||pendingDjcUiSend!=pending||closed||hello==null||terminalFailure!=null||applicationExitAttempted||pending.acceptAttempted
                ||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)throw new IOException("Original pending Send unavailable or consumed");
        if(!hello.capabilities().contains(CurrentDjcDeclarationUi.Action.QUERY_WARNING.capability())||!hello.capabilities().contains(CurrentDjcDeclarationUi.Action.ACCEPT_WARNING.capability()))throw new IOException("Actual warning query/accept capabilities absent");
        Instant now=chronologyClock.instant();if(!now.isBefore(until)||!now.isBefore(pending.deadline())||until.isAfter(pending.deadline()))throw new IOException("Warning phase cannot refresh original Send deadline");
        var query=pending.send.query;requireCoreOriginal(query.before,until);
        if(!pending.send.called||!query.actionAttempted||!query.before.controlAttempted||pending.send.action!=CurrentDjcDeclarationUi.Action.SEND_UI||query.prepared!=pending.send)throw new IOException("Actual original Send write was not consumed");
        var custody=pending.original.custody().orElseThrow(()->new IOException("Original Send custody absent"));requireDjcUiCustody(pending.original,custody);
        if(custody.writeEntered().order().compareTo(query.custody.responseReceived().order())<=0||custody.responseReceived().observedAt().isAfter(now)||custody.responseReceived().observedAt().isAfter(pending.deadline()))throw new IOException("Original Send escaped query chronology/deadline");
        var frame=CurrentDjcDeclarationUiResult.decodeOutcome(pending.original);requireDjcUiFrame(frame,CurrentDjcDeclarationUi.Action.SEND_UI,query.before,query.target,query.cb);
        if(!frame.equals(pending.frame)||frame.status()!=CurrentDjcDeclarationUiResult.Status.SEND_DISPATCHED||!frame.providerGeneration().equals(query.frame.providerGeneration())||!frame.querySequence().equals(query.frame.querySequence()))throw new IOException("Pending warning did not originate from this actual private Send");
        if(!Arrays.equals(pending.original.outbound().orElseThrow().originalPacket(),pending.send.packet.value()))throw new IOException("Original Send packet/body changed");
    }
    private byte[] djcWarningPacket(String id,CurrentDjcDeclarationUi.Action action,DjcUiPendingSend pending)throws IOException {
        var q=pending.send.query;return djcUiPacket(id,action,q.before,q.target,q.cb,pending.frame.providerGeneration(),pending.frame.querySequence(),BigInteger.ZERO,pending.frame.claimSequence(),pending.deadline());
    }
    private byte[] djcWarningAcceptPacket(String id,DjcUiWarningReady ready)throws IOException {
        var p=ready.pending;var q=p.send.query;return djcUiPacket(id,CurrentDjcDeclarationUi.Action.ACCEPT_WARNING,q.before,q.target,q.cb,ready.frame.providerGeneration(),ready.frame.querySequence(),BigInteger.ZERO,p.frame.claimSequence(),p.deadline());
    }
    public synchronized DjcUiWarningRead readCurrentDjcWarning(DjcUiPendingSend pending,Instant receiveDeadline)throws InterruptedException {
        String id="djc-ui-warning-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            Objects.requireNonNull(pending);Instant until=readDeadline(receiveDeadline);if(pending.deadline().isBefore(until))until=pending.deadline();requireDjcUiPending(pending,until);
            if(pending.prepared!=null)throw new IOException("Original warning acceptance already prepared; cannot replace readiness");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
            final Instant queryUntil=until;pending.latestReady=null;byte[] packet=djcWarningPacket(id,CurrentDjcDeclarationUi.Action.QUERY_WARNING,pending);
            outcome=retainReadOutcome(dispatchRead(id,packet,queryUntil,()->{requireBackgroundAtCoreWrite();try{requireDjcUiPending(pending,queryUntil);}catch(IOException invalid){throw new UncheckedIOException(invalid);}}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new DjcUiWarningUnavailable(outcome,"Actual warning has no qualified ACK");}
            var frame=CurrentDjcDeclarationUiResult.decodeOutcome(ack);var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual warning read custody absent"));
            var sourceQuery=pending.send.query;requireDjcUiFrame(frame,CurrentDjcDeclarationUi.Action.QUERY_WARNING,sourceQuery.before,sourceQuery.target,sourceQuery.cb);requireDjcUiCustody(ack,custody);
            if(frame.status()!=CurrentDjcDeclarationUiResult.Status.WARNING_READY&&frame.status()!=CurrentDjcDeclarationUiResult.Status.WARNING_PENDING)return new DjcUiWarningUnavailable(ack,frame.unavailableReason().orElse("Original warning not ready"));
            requireDjcUiWarningObservation(pending,frame,ack,custody,queryUntil,queryUntil);
            if(frame.status()==CurrentDjcDeclarationUiResult.Status.WARNING_PENDING)return new DjcUiWarningWaiting(frame,ack,queryUntil);
            if(frame.status()!=CurrentDjcDeclarationUiResult.Status.WARNING_READY)return new DjcUiWarningUnavailable(ack,frame.unavailableReason().orElse("Original warning not ready"));
            var ready=new DjcUiWarningReady(this,pending,frame,ack,custody,queryUntil);pending.latestReady=ready;return ready;
        }catch(IOException|RuntimeException invalid){if(pending!=null&&pending.issuer==this)pending.latestReady=null;return new DjcUiWarningUnavailable(djcUiFailure(id,outcome,invalid),reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();if(pending!=null&&pending.issuer==this)pending.latestReady=null;unresolvedCoreControl=new Unknown(id,"Warning read interrupted under original Send; never replay",retainedOutbound(id),Optional.empty());return new DjcUiWarningUnavailable(unresolvedCoreControl,"Original warning query interrupted");}
    }
    private void requireDjcUiWarningObservation(DjcUiPendingSend pending,CurrentDjcDeclarationUiResult frame,AckReceived ack,NativeRequestChronology custody,Instant validUntil,Instant until)throws IOException {
        requireDjcUiPending(pending,until);Instant now=chronologyClock.instant();
        if(!now.isBefore(validUntil)||until.isAfter(validUntil)||custody.responseReceived().observedAt().isAfter(now)||custody.responseReceived().observedAt().isAfter(validUntil)
                ||custody.writeEntered().order().compareTo(pending.original.custody().orElseThrow().responseReceived().order())<=0)throw new IOException("Warning observation escaped original Send chronology/deadline");
        requireDjcUiCustody(ack,custody);var query=pending.send.query;requireDjcUiFrame(frame,CurrentDjcDeclarationUi.Action.QUERY_WARNING,query.before,query.target,query.cb);
        if(!CurrentDjcDeclarationUiResult.decodeOutcome(ack).equals(frame)||!frame.providerGeneration().equals(pending.frame.providerGeneration())||frame.querySequence().signum()<=0
                ||frame.source().isEmpty()||!frame.source().orElseThrow().selected().equals(pending.frame.source().orElseThrow().selected()))throw new IOException("Warning changed original Core/source/provider/selected Send tuple");
        if(!Arrays.equals(ack.outbound().orElseThrow().originalPacket(),djcWarningPacket(ack.requestId(),CurrentDjcDeclarationUi.Action.QUERY_WARNING,pending)))throw new IOException("Warning request did not retain original Send ID/body/claim/deadline");
    }
    private void requireDjcUiWarningReady(DjcUiWarningReady ready,Instant until)throws IOException {
        if(ready==null||ready.issuer!=this||ready.pending.latestReady!=ready||ready.frame.status()!=CurrentDjcDeclarationUiResult.Status.WARNING_READY||!ready.frame.source().orElseThrow().permitsAccept())throw new IOException("Identical actual warning readiness with Native CanAccept required");
        requireDjcUiWarningObservation(ready.pending,ready.frame,ready.original,ready.custody,ready.validUntil,until);
    }
    public synchronized DjcUiWarningPrepared prepareCurrentDjcWarningAcceptance(DjcUiWarningReady ready)throws IOException {
        if(ready!=null&&ready.issuer==this&&ready.pending.prepared!=null)return ready.pending.prepared;
        requireDjcUiWarningReady(ready,ready.validUntil);String id="djc-ui-accept-"+UUID.randomUUID().toString().replace("-","");
        return ready.pending.prepared=new DjcUiWarningPrepared(this,ready,id,djcWarningAcceptPacket(id,ready));
    }
    public synchronized DispatchOutcome submitCurrentDjcWarningAcceptance(DjcUiWarningPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);if(original.issuer!=this||original.ready.pending.prepared!=original)return zero(original.id,"Foreign warning acceptance preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original warning acceptance has no reusable write authority");original.called=true;DispatchOutcome outcome=null;
        try {
            var ready=original.ready;requireDjcUiWarningReady(ready,ready.validUntil);
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
            if(!Arrays.equals(original.packet.value(),djcWarningAcceptPacket(original.id,ready)))throw new IOException("Prepared warning acceptance body drift");
            outcome=dispatch(original.id,original.packet.value(),ready.validUntil,()->{requireBackgroundAtCoreWrite();try{requireDjcUiWarningReady(ready,ready.validUntil);}catch(IOException invalid){throw new UncheckedIOException(invalid);}ready.pending.acceptAttempted=true;ready.pending.latestReady=null;heldSnapshotInvalidated=true;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return original.outcome=unknown;}
            if(outcome instanceof AckReceived ack){var frame=CurrentDjcDeclarationUiResult.decodeOutcome(ack);var q=ready.pending.send.query;requireDjcUiFrame(frame,CurrentDjcDeclarationUi.Action.ACCEPT_WARNING,q.before,q.target,q.cb);
                if(!frame.providerGeneration().equals(ready.frame.providerGeneration())||!frame.querySequence().equals(ready.frame.querySequence()))throw new IOException("Final warning ACK changed actual fresh warning witness lease");
            }return original.outcome=outcome;
        }catch(IOException|RuntimeException invalid){return original.outcome=djcUiFailure(original.id,outcome,invalid);}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(original.id,"Warning acceptance interrupted after write; never replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;}
    }

    /** A readonly cost observation never grants a private action or replacement UI-query lease. */
    public sealed interface DjcSelectedCostRead permits DjcSelectedCostReceived,DjcSelectedCostUnavailable {DispatchOutcome original();}
    public static final class DjcSelectedCostReceived implements DjcSelectedCostRead {
        private final CurrentDjcSelectedCostResult frame;private final AckReceived original;
        private DjcSelectedCostReceived(CurrentDjcSelectedCostResult frame,AckReceived original){this.frame=frame;this.original=original;}
        public CurrentDjcSelectedCostResult frame(){return frame;}@Override public AckReceived original(){return original;}
    }
    public record DjcSelectedCostUnavailable(DispatchOutcome original,String reason)implements DjcSelectedCostRead {
        public DjcSelectedCostUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}
    }
    private byte[] djcSelectedCostPacket(String id,DjcUiReceived query)throws IOException {
        if(!(query.before.frame instanceof CoreFrame.Partial core))throw new IOException("Original current Core required");
        var request=CurrentDjcSelectedCost.request(core,query.target,query.cb,query.frame.providerGeneration(),query.frame.querySequence());
        var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));fields.put("core_control_deadline_unix_ms",query.validUntil.toEpochMilli());
        return NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
    }
    public synchronized DjcSelectedCostRead readCurrentDjcSelectedCost(DjcUiReceived query)throws InterruptedException {
        String id="djc-cost-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            Objects.requireNonNull(query);requireDjcUiOriginal(query,query.validUntil);
            if(activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)throw new IOException("Cost query cannot bypass an active mailbox");
            if(!hello.capabilities().contains(CurrentDjcSelectedCost.CAPABILITY))throw new IOException("Actual readonly selected-cost capability absent");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native identity retention limit reached");
            var selected=query.frame.source().orElseThrow();
            if(!selected.interactionDefinitionVerified()||selected.loadedInterface()!=4||!selected.nativeConfirmation().orElse(false)
                    ||!selected.residentAvailable()||!selected.namedRootBound()||!selected.windowVisible()||selected.warningSourceAvailable()||selected.selected().isEmpty())
                throw new IOException("Actually selected typed resident declaration required; no implicit Open/Select/Send");
            byte[] packet=djcSelectedCostPacket(id,query);Instant until=query.validUntil;
            outcome=retainReadOutcome(dispatchRead(id,packet,until,()->{requireBackgroundAtCoreWrite();try{requireDjcUiOriginal(query,until);}catch(IOException invalid){throw new UncheckedIOException(invalid);}}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new DjcSelectedCostUnavailable(outcome,"Original readonly selected-cost query has no qualified ACK");}
            var frame=CurrentDjcSelectedCostResult.decodeOutcome(ack);
            if(!frame.providerGeneration().equals(query.frame.providerGeneration())||!frame.querySequence().equals(query.frame.querySequence()))throw new IOException("Selected-cost ACK changed the original private UI-query lease");
            if(frame.factsBefore().isPresent()&&!frame.factsBefore().equals(query.frame.factsBefore()))throw new IOException("Cost ACK changed its actual original Core");
            if(frame.ownerWitness().isPresent()&&!frame.ownerWitness().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Cost owner crossed original connection");
            if(frame.status()==CurrentDjcSelectedCostResult.Status.INDETERMINATE||!frame.cleanupKnown())throw new IOException("Native cost getter/cleanup is uncertain; original retained and no follow-up");
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual cost response chronology absent"));requireDjcUiCustody(ack,custody);
            Instant now=chronologyClock.instant();
            if(custody.writeEntered().order().compareTo(query.custody.responseReceived().order())<=0||custody.responseReceived().observedAt().isAfter(until)||custody.responseReceived().observedAt().isAfter(now))throw new IOException("Cost query escaped original private source chronology/deadline");
            requireDjcUiOriginal(query,until);
            if(!Arrays.equals(ack.outbound().orElseThrow().originalPacket(),packet))throw new IOException("Actual selected-cost request body/deadline differs");
            if(!frame.nativeOk())return new DjcSelectedCostUnavailable(ack,frame.unavailableReason().orElseThrow());
            if(!frame.factsBefore().equals(query.frame.factsBefore())||!frame.source().orElseThrow().matches(selected))throw new IOException("Actual cost source/selected tuple differs from original private query");
            return new DjcSelectedCostReceived(frame,ack);
        }catch(IOException|RuntimeException invalid){return new DjcSelectedCostUnavailable(djcUiFailure(id,outcome,invalid),reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(id,"Selected-cost read interrupted after write; never replay as control",retainedOutbound(id),Optional.empty());return new DjcSelectedCostUnavailable(unresolvedCoreControl,"Original selected-cost query interrupted");}
    }


    public sealed interface CuratedDecisionRead permits CuratedDecisionReceived,CuratedDecisionUnavailable { DispatchOutcome original(); }
    public static final class CuratedDecisionReceived implements CuratedDecisionRead {
        private final NativeGameTransport issuer;private final CoreReceived before;private final CurrentCuratedDecisionsResult frame;
        private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private boolean actionAttempted;private CuratedDecisionPrepared prepared;
        private CuratedDecisionReceived(NativeGameTransport issuer,CoreReceived before,CurrentCuratedDecisionsResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.before=before;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentCuratedDecisionsResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant until)throws IOException{Objects.requireNonNull(actual).requireCuratedDecisionOriginal(this,until);}
    }
    public record CuratedDecisionUnavailable(DispatchOutcome original,String reason)implements CuratedDecisionRead {public CuratedDecisionUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    public static final class CuratedDecisionPrepared {
        private final NativeGameTransport issuer;private final CuratedDecisionReceived query;private final String id;private final NativeWire.Bytes packet;
        private final CurrentCuratedDecisions.Action action;private final Optional<CurrentCuratedDecisions.DecisionKey> decision;private final CurrentCuratedDecisionsSource selected;
        private boolean called;private DispatchOutcome outcome;private CurrentCuratedDecisionsResult latestFrame;
        private CuratedDecisionPrepared(NativeGameTransport issuer,CuratedDecisionReceived query,CurrentCuratedDecisions.Action action,Optional<CurrentCuratedDecisions.DecisionKey> decision,CurrentCuratedDecisionsSource selected,String id,byte[] packet){this.issuer=issuer;this.query=query;this.action=action;this.decision=decision;this.selected=selected;this.id=id;this.packet=new NativeWire.Bytes(packet);}
        public String requestId(){return id;}public CurrentCuratedDecisions.Action action(){return action;}public Optional<CurrentCuratedDecisions.DecisionKey> decisionKey(){return decision;}public CurrentCuratedDecisionsSource selected(){return selected;}public NativeWire.Bytes originalPacket(){return packet;}public Instant deadline(){return query.validUntil;}
        public Optional<CurrentCuratedDecisionsResult> latestFrame(){return Optional.ofNullable(latestFrame);}
    }
    private CuratedDecisionReceived latestCuratedDecision;
    private byte[] curatedDecisionPacket(String id,CurrentCuratedDecisions.Action action,CoreReceived before,BigInteger provider,BigInteger query,Optional<CurrentCuratedDecisions.DecisionKey> decision,Instant until)throws IOException {
        if(!(before.frame instanceof CoreFrame.Partial core))throw new IOException("Exact current curatedDecision Core required");
        var request=CurrentCuratedDecisions.request(core,action,provider,query,decision);var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
        fields.put("core_control_deadline_unix_ms",until.toEpochMilli());return NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
    }
    private void requireCuratedDecisionScope(CoreReceived before,Instant until)throws IOException {
        Objects.requireNonNull(before);requireCoreOriginal(before,until);
        if(applicationExitAttempted||before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
            throw new IOException("Actual unused Core and resolved owner scope required for curatedDecision observation/reply");
        if(!(before.frame instanceof CoreFrame.Partial core)||core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)throw new IOException("Exact current267 Core required");
        CurrentLetter.requirePrefix(core.prefix());
    }
    public synchronized CuratedDecisionRead readCurrentCuratedDecisions(CoreReceived before,Instant deadline)throws InterruptedException {
        String id="curatedDecision-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            requireCuratedDecisionScope(before,deadline);
            if(!hello.capabilities().contains(CurrentCuratedDecisions.Action.QUERY.capability()))throw new IOException("Actual current curatedDecision query capability absent");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            Instant until=readDeadline(deadline);byte[] packet=curatedDecisionPacket(id,CurrentCuratedDecisions.Action.QUERY,before,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),until);
            outcome=retainReadOutcome(dispatchRead(id,packet,until,()->{requireBackgroundAtCoreWrite();try{requireCuratedDecisionScope(before,until);}catch(IOException invalid){throw new UncheckedIOException(invalid);}latestCuratedDecision=null;}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new CuratedDecisionUnavailable(outcome,"Actual curatedDecision query has no qualified ACK");}
            var frame=CurrentCuratedDecisionsResult.decodeOutcome(ack);requireCuratedDecisionFrame(frame,CurrentCuratedDecisions.Action.QUERY,before);
            if(frame.effectAttempted()||frame.nativeReturned()||frame.claimSequence().signum()!=0)throw new IOException("Readonly curatedDecision query unexpectedly attempted an effect/claim");
            if(frame.status()!=CurrentCuratedDecisionsResult.Status.AVAILABLE)return new CuratedDecisionUnavailable(ack,frame.unavailableReason().orElseThrow());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual curatedDecision query custody absent"));
            var received=new CuratedDecisionReceived(this,before,frame,ack,custody,until);latestCuratedDecision=received;
            requireCuratedDecisionOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){latestCuratedDecision=null;return new CuratedDecisionUnavailable(curatedDecisionFailure(id,outcome,invalid),reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();latestCuratedDecision=null;
            unresolvedCoreControl=new Unknown(id,"Actual curatedDecision query interrupted after write; preserve original, block effects",retainedOutbound(id),Optional.empty());return new CuratedDecisionUnavailable(unresolvedCoreControl,"Original curatedDecision query interrupted");}
    }
    private void requireCuratedDecisionFrame(CurrentCuratedDecisionsResult frame,CurrentCuratedDecisions.Action action,CoreReceived before)throws IOException {
        if(frame.action()!=action||frame.status()==CurrentCuratedDecisionsResult.Status.INDETERMINATE||!frame.cleanupKnown())throw new IOException("Actual curatedDecision action/cleanup uncertain");
        if(frame.factsBefore().isPresent()&&!frame.factsBefore().orElseThrow().equals(((CoreFrame.Partial)before.frame).prefix()))throw new IOException("Actual curatedDecision Core differs from original source");
        if(frame.owner().isPresent()&&!frame.owner().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Actual curatedDecision owner crossed connection");
        if(frame.effectAttempted()&&frame.status()!=CurrentCuratedDecisionsResult.dispatchedStatus(action))throw new IOException("Native curatedDecision effect unqualified; never replay");
    }
    private void requireCuratedDecisionCustody(AckReceived actual,NativeRequestChronology custody)throws IOException {
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)||originalRequestChronology(actual.requestId()).filter(custody::equals).isEmpty())throw new IOException("CuratedDecision crossed original Game/session/custody");
        custody.verify(actual);
    }
    private void requireCuratedDecisionOriginal(CuratedDecisionReceived actual,Instant until)throws IOException {
        Objects.requireNonNull(until);if(actual==null||actual.issuer!=this||actual!=latestCuratedDecision||actual.actionAttempted)throw new IOException("Original private curatedDecision query unavailable or consumed");
        requireCuratedDecisionScope(actual.before,until);Instant now=chronologyClock.instant();
        if(until.isAfter(actual.validUntil)||!now.isBefore(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("CuratedDecision query escaped original Core/deadline/chronology");
        requireCuratedDecisionCustody(actual.original,actual.custody);
        var frame=CurrentCuratedDecisionsResult.decodeOutcome(actual.original);requireCuratedDecisionFrame(frame,CurrentCuratedDecisions.Action.QUERY,actual.before);
        if(!frame.equals(actual.frame)||frame.status()!=CurrentCuratedDecisionsResult.Status.AVAILABLE)throw new IOException("Actual curatedDecision query frame changed");
        if(!Arrays.equals(actual.original.outbound().orElseThrow().originalPacket(),curatedDecisionPacket(actual.original.requestId(),CurrentCuratedDecisions.Action.QUERY,actual.before,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),actual.validUntil)))throw new IOException("Original curatedDecision query body/deadline changed");
    }
    public synchronized CuratedDecisionPrepared prepareCurrentCuratedDecision(CuratedDecisionReceived query,CurrentCuratedDecisions.Action action,Optional<CurrentCuratedDecisions.DecisionKey> decision)throws IOException {
        Objects.requireNonNull(query);Objects.requireNonNull(action);Objects.requireNonNull(decision);
        if(action==CurrentCuratedDecisions.Action.QUERY)throw new IOException("A query cannot prepare an effect");
        if(query.issuer==this&&query.prepared!=null){if(query.prepared.action!=action||!query.prepared.decision.equals(decision))throw new IOException("Original private query already prepared another fixed action");return query.prepared;}
        requireCuratedDecisionOriginal(query,query.validUntil);
        CurrentCuratedDecisions.requireRole(action,query.frame.providerGeneration(),query.frame.querySequence(),decision);
        if(!hello.capabilities().contains(action.capability()))throw new IOException("Actual fixed curated action capability absent");
        var selected=query.frame.source().orElseThrow();if(!selected.admits(action,decision))throw new IOException("Actual source does not admit this one fixed action");
        String id="curated-decision-effect-"+UUID.randomUUID().toString().replace("-","");
        return query.prepared=new CuratedDecisionPrepared(this,query,action,decision,selected,id,curatedDecisionPacket(id,action,query.before,query.frame.providerGeneration(),query.frame.querySequence(),decision,query.validUntil));
    }
    public synchronized DispatchOutcome submitCurrentCuratedDecision(CuratedDecisionPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);if(original.issuer!=this||original.query.prepared!=original)return zero(original.id,"Foreign curated action preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original curated action has no reusable write authority");original.called=true;DispatchOutcome outcome=null;
        try {
            var query=original.query;requireCuratedDecisionOriginal(query,original.deadline());
            if(!hello.capabilities().contains(original.action.capability())||!original.selected.admits(original.action,original.decision)||!query.frame.source().orElseThrow().equals(original.selected))throw new IOException("Actual original fixed action no longer admissible");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            if(!Arrays.equals(original.packet.value(),curatedDecisionPacket(original.id,original.action,query.before,query.frame.providerGeneration(),query.frame.querySequence(),original.decision,original.deadline())))throw new IOException("Original action packet/body drift");
            outcome=dispatch(original.id,original.packet.value(),original.deadline(),()->{requireBackgroundAtCoreWrite();try{requireCuratedDecisionOriginal(query,original.deadline());}catch(IOException invalid){throw new UncheckedIOException(invalid);}query.actionAttempted=true;query.before.controlAttempted=true;heldSnapshotInvalidated=true;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return original.outcome=unknown;}
            if(outcome instanceof AckReceived ack){
                var frame=CurrentCuratedDecisionsResult.decodeOutcome(ack);requireCuratedDecisionFrame(frame,original.action,query.before);
                if(!frame.providerGeneration().equals(query.frame.providerGeneration())||!frame.querySequence().equals(query.frame.querySequence())||!frame.decisionKey().equals(original.decision))throw new IOException("Action ACK changed original private lease or fixed key");
                var custody=originalRequestChronology(original.id).orElseThrow(()->new IOException("Actual action custody absent"));requireCuratedDecisionCustody(ack,custody);
                if(custody.writeEntered().order().compareTo(query.custody.responseReceived().order())<=0||custody.responseReceived().observedAt().isAfter(original.deadline())||custody.responseReceived().observedAt().isAfter(chronologyClock.instant()))throw new IOException("Action ACK escaped original query chronology/deadline");
                if(frame.successful()&&!frame.source().equals(query.frame.source()))throw new IOException("Action before-source differs from original private query");
                original.latestFrame=frame;
            }
            return original.outcome=outcome;
        }catch(IOException|RuntimeException invalid){return original.outcome=curatedDecisionFailure(original.id,outcome,invalid);}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(original.id,"Curated action interrupted after original write; never replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;}
    }
    private DispatchOutcome curatedDecisionFailure(String id,DispatchOutcome outcome,Exception invalid) {
        if(!sentRequestIds.contains(id))return zero(id,reason(invalid));
        if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
        unresolvedCoreControl=new Unknown(id,"CuratedDecision original source/custody unqualified after write; no replay: "+reason(invalid),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());return unresolvedCoreControl;
    }


    public sealed interface CourtierControlsRead permits CourtierControlsReceived,CourtierControlsUnavailable { DispatchOutcome original(); }
    public static final class CourtierControlsReceived implements CourtierControlsRead {
        private final NativeGameTransport issuer;private final CurrentCourtierControls.Product product;private final CurrentCourtierControls.Control control;private final CoreReceived before;private final CurrentCourtierControlsResult frame;
        private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private boolean actionAttempted;private CourtierControlsPrepared prepared;
        private CourtierControlsReceived(NativeGameTransport issuer,CoreReceived before,CurrentCourtierControls.Product product,CurrentCourtierControls.Control control,CurrentCourtierControlsResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.product=product;this.control=control;this.before=before;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentCourtierControlsResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}public CurrentCourtierControls.Product product(){return product;}public CurrentCourtierControls.Control control(){return control;}
        public void requireOriginal(NativeGameTransport actual,Instant until)throws IOException{Objects.requireNonNull(actual).requireCourtierControlsOriginal(this,until);}
    }
    public record CourtierControlsUnavailable(DispatchOutcome original,String reason)implements CourtierControlsRead {public CourtierControlsUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    public static final class CourtierControlsPrepared {
        private final NativeGameTransport issuer;private final CourtierControlsReceived query;private final String id;private final NativeWire.Bytes packet;
        private final CurrentCourtierControls.Action action;private final CurrentCourtierControlsSource selected;
        private boolean called;private DispatchOutcome outcome;private CurrentCourtierControlsResult latestFrame;
        private CourtierControlsPrepared(NativeGameTransport issuer,CourtierControlsReceived query,CurrentCourtierControls.Action action,CurrentCourtierControlsSource selected,String id,byte[] packet){this.issuer=issuer;this.query=query;this.action=action;this.selected=selected;this.id=id;this.packet=new NativeWire.Bytes(packet);}
        public String requestId(){return id;}public CurrentCourtierControls.Product product(){return query.product;}public CurrentCourtierControls.Control control(){return query.control;}public CurrentCourtierControls.Action action(){return action;}public CurrentCourtierControlsSource selected(){return selected;}public NativeWire.Bytes originalPacket(){return packet;}public Instant deadline(){return query.validUntil;}
        public Optional<CurrentCourtierControlsResult> latestFrame(){return Optional.ofNullable(latestFrame);}
    }
    private CourtierControlsReceived latestCourtierControls;
    private byte[] courtierControlsPacket(String id,CurrentCourtierControls.Action action,CoreReceived before,BigInteger provider,BigInteger query,CurrentCourtierControls.Product product,CurrentCourtierControls.Control control,Instant until)throws IOException {
        if(!(before.frame instanceof CoreFrame.Partial core))throw new IOException("Exact current courtierControls Core required");
        var request=CurrentCourtierControls.request(core,action,provider,query,product,control);var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
        fields.put("core_control_deadline_unix_ms",until.toEpochMilli());return NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
    }
    private void requireCourtierControlsScope(CoreReceived before,Instant until)throws IOException {
        Objects.requireNonNull(before);requireCoreOriginal(before,until);
        if(applicationExitAttempted||before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
            throw new IOException("Actual unused Core and resolved owner scope required for courtierControls observation/reply");
        if(!(before.frame instanceof CoreFrame.Partial core)||core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)throw new IOException("Exact current267 Core required");
        CurrentLetter.requirePrefix(core.prefix());
    }
    public synchronized CourtierControlsRead readCurrentCourtierControls(CoreReceived before,CurrentCourtierControls.Product product,CurrentCourtierControls.Control control,Instant deadline)throws InterruptedException {
        String id="courtierControls-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            Objects.requireNonNull(product);Objects.requireNonNull(control);requireCourtierControlsScope(before,deadline);
            if(!hello.capabilities().contains(CurrentCourtierControls.Action.QUERY_CONTROL.capability()))throw new IOException("Actual current courtierControls query capability absent");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            Instant until=readDeadline(deadline);byte[] packet=courtierControlsPacket(id,CurrentCourtierControls.Action.QUERY_CONTROL,before,BigInteger.ZERO,BigInteger.ZERO,product,control,until);
            outcome=retainReadOutcome(dispatchRead(id,packet,until,()->{requireBackgroundAtCoreWrite();try{requireCourtierControlsScope(before,until);}catch(IOException invalid){throw new UncheckedIOException(invalid);}latestCourtierControls=null;}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new CourtierControlsUnavailable(outcome,"Actual courtierControls query has no qualified ACK");}
            var frame=CurrentCourtierControlsResult.decodeOutcome(ack);requireCourtierControlsFrame(frame,CurrentCourtierControls.Action.QUERY_CONTROL,before,product,control);
            if(frame.effectAttempted()||frame.nativeReturned()||frame.claimSequence().signum()!=0)throw new IOException("Readonly courtierControls query unexpectedly attempted an effect/claim");
            if(frame.status()!=CurrentCourtierControlsResult.Status.AVAILABLE)return new CourtierControlsUnavailable(ack,frame.unavailableReason().orElseThrow());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual courtierControls query custody absent"));
            var received=new CourtierControlsReceived(this,before,product,control,frame,ack,custody,until);latestCourtierControls=received;
            requireCourtierControlsOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){latestCourtierControls=null;return new CourtierControlsUnavailable(courtierControlsFailure(id,outcome,invalid),reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();latestCourtierControls=null;
            unresolvedCoreControl=new Unknown(id,"Actual courtierControls query interrupted after write; preserve original, block effects",retainedOutbound(id),Optional.empty());return new CourtierControlsUnavailable(unresolvedCoreControl,"Original courtierControls query interrupted");}
    }
    private void requireCourtierControlsFrame(CurrentCourtierControlsResult frame,CurrentCourtierControls.Action action,CoreReceived before,CurrentCourtierControls.Product product,CurrentCourtierControls.Control control)throws IOException {
        if(frame.product()!=product||frame.control()!=control)throw new IOException("Courtier result product/control changed");
        if(frame.action()!=action||frame.status()==CurrentCourtierControlsResult.Status.INDETERMINATE||!frame.cleanupKnown())throw new IOException("Actual courtierControls action/cleanup uncertain");
        if(frame.factsBefore().isPresent()&&!frame.factsBefore().orElseThrow().equals(((CoreFrame.Partial)before.frame).prefix()))throw new IOException("Actual courtierControls Core differs from original source");
        if(frame.owner().isPresent()&&!frame.owner().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Actual courtierControls owner crossed connection");
        if(frame.effectAttempted()&&frame.status()!=CurrentCourtierControlsResult.dispatchedStatus(action))throw new IOException("Native courtierControls effect unqualified; never replay");
    }
    private void requireCourtierControlsCustody(AckReceived actual,NativeRequestChronology custody)throws IOException {
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)||originalRequestChronology(actual.requestId()).filter(custody::equals).isEmpty())throw new IOException("CourtierControls crossed original Game/session/custody");
        custody.verify(actual);
    }
    private void requireCourtierControlsOriginal(CourtierControlsReceived actual,Instant until)throws IOException {
        Objects.requireNonNull(until);if(actual==null||actual.issuer!=this||actual!=latestCourtierControls||actual.actionAttempted)throw new IOException("Original private courtierControls query unavailable or consumed");
        requireCourtierControlsScope(actual.before,until);Instant now=chronologyClock.instant();
        if(until.isAfter(actual.validUntil)||!now.isBefore(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("CourtierControls query escaped original Core/deadline/chronology");
        requireCourtierControlsCustody(actual.original,actual.custody);
        var frame=CurrentCourtierControlsResult.decodeOutcome(actual.original);requireCourtierControlsFrame(frame,CurrentCourtierControls.Action.QUERY_CONTROL,actual.before,actual.product,actual.control);
        if(!frame.equals(actual.frame)||frame.status()!=CurrentCourtierControlsResult.Status.AVAILABLE)throw new IOException("Actual courtierControls query frame changed");
        if(!Arrays.equals(actual.original.outbound().orElseThrow().originalPacket(),courtierControlsPacket(actual.original.requestId(),CurrentCourtierControls.Action.QUERY_CONTROL,actual.before,BigInteger.ZERO,BigInteger.ZERO,actual.product,actual.control,actual.validUntil)))throw new IOException("Original courtierControls query body/deadline changed");
    }
    public synchronized CourtierControlsPrepared prepareCurrentCourtierControlExecute(CourtierControlsReceived query)throws IOException {
        Objects.requireNonNull(query);var action=CurrentCourtierControls.Action.EXECUTE_CONTROL;
        if(query.issuer==this&&query.prepared!=null){if(query.prepared.action!=action)throw new IOException("Original prompt query already prepared the other action");return query.prepared;}
        requireCourtierControlsOriginal(query,query.validUntil);
        if(!hello.capabilities().contains(action.capability()))throw new IOException("Actual fixed known-instance reply capability absent");
        var selected=query.frame.source().orElseThrow();
        if(!selected.executeAdmissible())throw new IOException("Desired actual courtierControls source does not admit the single reviewed reply");
        String id="courtierControls-ack-"+UUID.randomUUID().toString().replace("-","");
        return query.prepared=new CourtierControlsPrepared(this,query,action,selected,id,courtierControlsPacket(id,action,query.before,query.frame.providerGeneration(),query.frame.querySequence(),query.product,query.control,query.validUntil));
    }
    public synchronized DispatchOutcome submitCurrentCourtierControlExecute(CourtierControlsPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);if(original.issuer!=this||original.query.prepared!=original)return zero(original.id,"Foreign courtierControls reply preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original courtierControls call has no reusable write authority");original.called=true;DispatchOutcome outcome=null;
        try {
            var query=original.query;requireCourtierControlsOriginal(query,original.deadline());
            if(!hello.capabilities().contains(original.action.capability())||!original.selected.executeAdmissible()||!query.frame.source().orElseThrow().equals(original.selected)||original.selected.product()!=query.product||original.selected.control()!=query.control)throw new IOException("Actual original fixed reply no longer admissible");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            if(!Arrays.equals(original.packet.value(),courtierControlsPacket(original.id,original.action,query.before,query.frame.providerGeneration(),query.frame.querySequence(),query.product,query.control,original.deadline())))throw new IOException("Original reply packet/body drift");
            outcome=dispatch(original.id,original.packet.value(),original.deadline(),()->{requireBackgroundAtCoreWrite();try{requireCourtierControlsOriginal(query,original.deadline());}catch(IOException invalid){throw new UncheckedIOException(invalid);}query.actionAttempted=true;query.before.controlAttempted=true;heldSnapshotInvalidated=true;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return original.outcome=unknown;}
            if(outcome instanceof AckReceived ack){
                var frame=CurrentCourtierControlsResult.decodeOutcome(ack);requireCourtierControlsFrame(frame,original.action,query.before,query.product,query.control);
                if(!frame.providerGeneration().equals(query.frame.providerGeneration())||!frame.querySequence().equals(query.frame.querySequence())||frame.product()!=query.product||frame.control()!=query.control)throw new IOException("Reply ACK changed original private lease");
                var custody=originalRequestChronology(original.id).orElseThrow(()->new IOException("Actual reply custody absent"));requireCourtierControlsCustody(ack,custody);
                if(custody.writeEntered().order().compareTo(query.custody.responseReceived().order())<=0||custody.responseReceived().observedAt().isAfter(original.deadline())||custody.responseReceived().observedAt().isAfter(chronologyClock.instant()))throw new IOException("Reply ACK escaped original query chronology/deadline");
                if(frame.successful()&&!frame.source().equals(query.frame.source()))throw new IOException("Reply before-source differs from original private query");
                original.latestFrame=frame;
            }
            return original.outcome=outcome;
        }catch(IOException|RuntimeException invalid){return original.outcome=courtierControlsFailure(original.id,outcome,invalid);}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(original.id,"CourtierControls reply interrupted after original write; never replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;}
    }
    private DispatchOutcome courtierControlsFailure(String id,DispatchOutcome outcome,Exception invalid) {
        if(!sentRequestIds.contains(id))return zero(id,reason(invalid));
        if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
        unresolvedCoreControl=new Unknown(id,"CourtierControls original source/custody unqualified after write; no replay: "+reason(invalid),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());return unresolvedCoreControl;
    }


    public sealed interface XqolThresholdRead permits XqolThresholdReceived,XqolThresholdUnavailable { DispatchOutcome original(); }
    public static final class XqolThresholdReceived implements XqolThresholdRead {
        private final NativeGameTransport issuer;private final int targetThreshold;private final CoreReceived before;private final CurrentXqolThresholdResult frame;
        private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private boolean actionAttempted;private XqolThresholdPrepared prepared;
        private XqolThresholdReceived(NativeGameTransport issuer,CoreReceived before,int targetThreshold,CurrentXqolThresholdResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.targetThreshold=targetThreshold;this.before=before;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentXqolThresholdResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}public int targetThreshold(){return targetThreshold;}
        public void requireOriginal(NativeGameTransport actual,Instant until)throws IOException{Objects.requireNonNull(actual).requireXqolThresholdOriginal(this,until);}
    }
    public record XqolThresholdUnavailable(DispatchOutcome original,String reason)implements XqolThresholdRead {public XqolThresholdUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    public static final class XqolThresholdPrepared {
        private final NativeGameTransport issuer;private final XqolThresholdReceived query;private final String id;private final NativeWire.Bytes packet;
        private final int instanceId;private final CurrentXqolThreshold.Action action;private final CurrentXqolThresholdSource selected;
        private boolean called;private DispatchOutcome outcome;private CurrentXqolThresholdResult latestFrame;
        private XqolThresholdPrepared(NativeGameTransport issuer,XqolThresholdReceived query,CurrentXqolThreshold.Action action,int instanceId,CurrentXqolThresholdSource selected,String id,byte[] packet){this.issuer=issuer;this.query=query;this.instanceId=instanceId;this.action=action;this.selected=selected;this.id=id;this.packet=new NativeWire.Bytes(packet);}
        public String requestId(){return id;}public int instanceId(){return instanceId;}public int targetThreshold(){return query.targetThreshold;}public CurrentXqolThreshold.Action action(){return action;}public CurrentXqolThresholdSource selected(){return selected;}public NativeWire.Bytes originalPacket(){return packet;}public Instant deadline(){return query.validUntil;}
        public Optional<CurrentXqolThresholdResult> latestFrame(){return Optional.ofNullable(latestFrame);}
    }
    private XqolThresholdReceived latestXqolThreshold;
    private byte[] xqolThresholdPacket(String id,CurrentXqolThreshold.Action action,CoreReceived before,BigInteger provider,BigInteger query,Optional<Integer> instanceId,int targetThreshold,Instant until)throws IOException {
        if(!(before.frame instanceof CoreFrame.Partial core))throw new IOException("Exact current xqolThreshold Core required");
        var request=CurrentXqolThreshold.request(core,action,provider,query,instanceId,targetThreshold);var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
        fields.put("core_control_deadline_unix_ms",until.toEpochMilli());return NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
    }
    private void requireXqolThresholdScope(CoreReceived before,Instant until)throws IOException {
        Objects.requireNonNull(before);requireCoreOriginal(before,until);
        if(applicationExitAttempted||before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
            throw new IOException("Actual unused Core and resolved owner scope required for xqolThreshold observation/reply");
        if(!(before.frame instanceof CoreFrame.Partial core)||core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)throw new IOException("Exact current267 Core required");
        CurrentLetter.requirePrefix(core.prefix());
    }
    public synchronized XqolThresholdRead readCurrentXqolThreshold(CoreReceived before,int targetThreshold,Instant deadline)throws InterruptedException {
        String id="xqolThreshold-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            CurrentXqolThreshold.requireTarget(targetThreshold);requireXqolThresholdScope(before,deadline);
            if(!hello.capabilities().contains(CurrentXqolThreshold.Action.QUERY_THRESHOLD.capability()))throw new IOException("Actual current xqolThreshold query capability absent");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            Instant until=readDeadline(deadline);byte[] packet=xqolThresholdPacket(id,CurrentXqolThreshold.Action.QUERY_THRESHOLD,before,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),targetThreshold,until);
            outcome=retainReadOutcome(dispatchRead(id,packet,until,()->{requireBackgroundAtCoreWrite();try{requireXqolThresholdScope(before,until);}catch(IOException invalid){throw new UncheckedIOException(invalid);}latestXqolThreshold=null;}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new XqolThresholdUnavailable(outcome,"Actual xqolThreshold query has no qualified ACK");}
            var frame=CurrentXqolThresholdResult.decodeOutcome(ack);requireXqolThresholdFrame(frame,CurrentXqolThreshold.Action.QUERY_THRESHOLD,before,targetThreshold);
            if(frame.effectAttempted()||frame.nativeReturned()||frame.claimSequence().signum()!=0)throw new IOException("Readonly xqolThreshold query unexpectedly attempted an effect/claim");
            if(frame.status()!=CurrentXqolThresholdResult.Status.AVAILABLE)return new XqolThresholdUnavailable(ack,frame.unavailableReason().orElseThrow());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual xqolThreshold query custody absent"));
            var received=new XqolThresholdReceived(this,before,targetThreshold,frame,ack,custody,until);latestXqolThreshold=received;
            requireXqolThresholdOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){latestXqolThreshold=null;return new XqolThresholdUnavailable(xqolThresholdFailure(id,outcome,invalid),reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();latestXqolThreshold=null;
            unresolvedCoreControl=new Unknown(id,"Actual xqolThreshold query interrupted after write; preserve original, block effects",retainedOutbound(id),Optional.empty());return new XqolThresholdUnavailable(unresolvedCoreControl,"Original xqolThreshold query interrupted");}
    }
    private void requireXqolThresholdFrame(CurrentXqolThresholdResult frame,CurrentXqolThreshold.Action action,CoreReceived before,int targetThreshold)throws IOException {
        if(frame.source().isPresent()&&frame.source().orElseThrow().targetThreshold()!=targetThreshold)throw new IOException("Threshold source target changed");
        if(frame.action()!=action||frame.status()==CurrentXqolThresholdResult.Status.INDETERMINATE||!frame.cleanupKnown())throw new IOException("Actual xqolThreshold action/cleanup uncertain");
        if(frame.factsBefore().isPresent()&&!frame.factsBefore().orElseThrow().equals(((CoreFrame.Partial)before.frame).prefix()))throw new IOException("Actual xqolThreshold Core differs from original source");
        if(frame.owner().isPresent()&&!frame.owner().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Actual xqolThreshold owner crossed connection");
        if(frame.effectAttempted()&&frame.status()!=CurrentXqolThresholdResult.dispatchedStatus(action))throw new IOException("Native xqolThreshold effect unqualified; never replay");
    }
    private void requireXqolThresholdCustody(AckReceived actual,NativeRequestChronology custody)throws IOException {
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)||originalRequestChronology(actual.requestId()).filter(custody::equals).isEmpty())throw new IOException("XqolThreshold crossed original Game/session/custody");
        custody.verify(actual);
    }
    private void requireXqolThresholdOriginal(XqolThresholdReceived actual,Instant until)throws IOException {
        Objects.requireNonNull(until);if(actual==null||actual.issuer!=this||actual!=latestXqolThreshold||actual.actionAttempted)throw new IOException("Original private xqolThreshold query unavailable or consumed");
        requireXqolThresholdScope(actual.before,until);Instant now=chronologyClock.instant();
        if(until.isAfter(actual.validUntil)||!now.isBefore(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("XqolThreshold query escaped original Core/deadline/chronology");
        requireXqolThresholdCustody(actual.original,actual.custody);
        var frame=CurrentXqolThresholdResult.decodeOutcome(actual.original);requireXqolThresholdFrame(frame,CurrentXqolThreshold.Action.QUERY_THRESHOLD,actual.before,actual.targetThreshold);
        if(!frame.equals(actual.frame)||frame.status()!=CurrentXqolThresholdResult.Status.AVAILABLE)throw new IOException("Actual xqolThreshold query frame changed");
        if(!Arrays.equals(actual.original.outbound().orElseThrow().originalPacket(),xqolThresholdPacket(actual.original.requestId(),CurrentXqolThreshold.Action.QUERY_THRESHOLD,actual.before,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),actual.targetThreshold,actual.validUntil)))throw new IOException("Original xqolThreshold query body/deadline changed");
    }
    public synchronized XqolThresholdPrepared prepareCurrentXqolThresholdSet(XqolThresholdReceived query)throws IOException {
        Objects.requireNonNull(query);var action=CurrentXqolThreshold.Action.SET_THRESHOLD;
        if(query.issuer==this&&query.prepared!=null){if(query.prepared.action!=action)throw new IOException("Original prompt query already prepared the other action");return query.prepared;}
        requireXqolThresholdOriginal(query,query.validUntil);
        if(!hello.capabilities().contains(action.capability()))throw new IOException("Actual fixed known-instance reply capability absent");
        var selected=query.frame.source().orElseThrow();
        int actualInstanceId=selected.prompt().event().orElseThrow(()->new IOException("Actual current known prompt absent")).instanceId();
        if(!selected.setAdmissible())throw new IOException("Desired actual xqolThreshold source does not admit the single reviewed reply");
        String id="xqolThreshold-ack-"+UUID.randomUUID().toString().replace("-","");
        return query.prepared=new XqolThresholdPrepared(this,query,action,actualInstanceId,selected,id,xqolThresholdPacket(id,action,query.before,query.frame.providerGeneration(),query.frame.querySequence(),Optional.of(actualInstanceId),query.targetThreshold,query.validUntil));
    }
    public synchronized DispatchOutcome submitCurrentXqolThresholdSet(XqolThresholdPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);if(original.issuer!=this||original.query.prepared!=original)return zero(original.id,"Foreign xqolThreshold reply preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original xqolThreshold call has no reusable write authority");original.called=true;DispatchOutcome outcome=null;
        try {
            var query=original.query;requireXqolThresholdOriginal(query,original.deadline());
            if(!hello.capabilities().contains(original.action.capability())||!original.selected.setAdmissible()||!query.frame.source().orElseThrow().equals(original.selected)||original.selected.prompt().event().filter(e->e.instanceId()==original.instanceId).isEmpty())throw new IOException("Actual original fixed reply no longer admissible");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            if(!Arrays.equals(original.packet.value(),xqolThresholdPacket(original.id,original.action,query.before,query.frame.providerGeneration(),query.frame.querySequence(),Optional.of(original.instanceId),query.targetThreshold,original.deadline())))throw new IOException("Original reply packet/body drift");
            outcome=dispatch(original.id,original.packet.value(),original.deadline(),()->{requireBackgroundAtCoreWrite();try{requireXqolThresholdOriginal(query,original.deadline());}catch(IOException invalid){throw new UncheckedIOException(invalid);}query.actionAttempted=true;query.before.controlAttempted=true;heldSnapshotInvalidated=true;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return original.outcome=unknown;}
            if(outcome instanceof AckReceived ack){
                var frame=CurrentXqolThresholdResult.decodeOutcome(ack);requireXqolThresholdFrame(frame,original.action,query.before,query.targetThreshold);
                if(!frame.providerGeneration().equals(query.frame.providerGeneration())||!frame.querySequence().equals(query.frame.querySequence())||frame.instanceId().filter(n->n==original.instanceId).isEmpty())throw new IOException("Reply ACK changed original private lease");
                var custody=originalRequestChronology(original.id).orElseThrow(()->new IOException("Actual reply custody absent"));requireXqolThresholdCustody(ack,custody);
                if(custody.writeEntered().order().compareTo(query.custody.responseReceived().order())<=0||custody.responseReceived().observedAt().isAfter(original.deadline())||custody.responseReceived().observedAt().isAfter(chronologyClock.instant()))throw new IOException("Reply ACK escaped original query chronology/deadline");
                if(frame.successful()&&!frame.source().equals(query.frame.source()))throw new IOException("Reply before-source differs from original private query");
                original.latestFrame=frame;
            }
            return original.outcome=outcome;
        }catch(IOException|RuntimeException invalid){return original.outcome=xqolThresholdFailure(original.id,outcome,invalid);}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(original.id,"XqolThreshold reply interrupted after original write; never replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;}
    }
    private DispatchOutcome xqolThresholdFailure(String id,DispatchOutcome outcome,Exception invalid) {
        if(!sentRequestIds.contains(id))return zero(id,reason(invalid));
        if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
        unresolvedCoreControl=new Unknown(id,"XqolThreshold original source/custody unqualified after write; no replay: "+reason(invalid),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());return unresolvedCoreControl;
    }


    public sealed interface XqolPromptRead permits XqolPromptReceived,XqolPromptUnavailable { DispatchOutcome original(); }
    public static final class XqolPromptReceived implements XqolPromptRead {
        private final NativeGameTransport issuer;private final CoreReceived before;private final CurrentXqolPromptResult frame;
        private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private boolean actionAttempted;private XqolPromptPrepared prepared;
        private XqolPromptReceived(NativeGameTransport issuer,CoreReceived before,CurrentXqolPromptResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.before=before;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentXqolPromptResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant until)throws IOException{Objects.requireNonNull(actual).requireXqolPromptOriginal(this,until);}
    }
    public record XqolPromptUnavailable(DispatchOutcome original,String reason)implements XqolPromptRead {public XqolPromptUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    public static final class XqolPromptPrepared {
        private final NativeGameTransport issuer;private final XqolPromptReceived query;private final String id;private final NativeWire.Bytes packet;
        private final int instanceId;private final CurrentXqolPrompt.Action action;private final CurrentXqolPromptSource selected;
        private boolean called;private DispatchOutcome outcome;private CurrentXqolPromptResult latestFrame;
        private XqolPromptPrepared(NativeGameTransport issuer,XqolPromptReceived query,CurrentXqolPrompt.Action action,int instanceId,CurrentXqolPromptSource selected,String id,byte[] packet){this.issuer=issuer;this.query=query;this.instanceId=instanceId;this.action=action;this.selected=selected;this.id=id;this.packet=new NativeWire.Bytes(packet);}
        public String requestId(){return id;}public int instanceId(){return instanceId;}public CurrentXqolPrompt.Action action(){return action;}public CurrentXqolPromptSource selected(){return selected;}public NativeWire.Bytes originalPacket(){return packet;}public Instant deadline(){return query.validUntil;}
        public Optional<CurrentXqolPromptResult> latestFrame(){return Optional.ofNullable(latestFrame);}
    }
    private XqolPromptReceived latestXqolPrompt;
    private byte[] xqolPromptPacket(String id,CurrentXqolPrompt.Action action,CoreReceived before,BigInteger provider,BigInteger query,Optional<Integer> instanceId,Instant until)throws IOException {
        if(!(before.frame instanceof CoreFrame.Partial core))throw new IOException("Exact current xqolPrompt Core required");
        var request=CurrentXqolPrompt.request(core,action,provider,query,instanceId);var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
        fields.put("core_control_deadline_unix_ms",until.toEpochMilli());return NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
    }
    private void requireXqolPromptScope(CoreReceived before,Instant until)throws IOException {
        Objects.requireNonNull(before);requireCoreOriginal(before,until);
        if(applicationExitAttempted||before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
            throw new IOException("Actual unused Core and resolved owner scope required for xqolPrompt observation/reply");
        if(!(before.frame instanceof CoreFrame.Partial core)||core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)throw new IOException("Exact current267 Core required");
        CurrentLetter.requirePrefix(core.prefix());
    }
    public synchronized XqolPromptRead readCurrentXqolPrompt(CoreReceived before,Instant deadline)throws InterruptedException {
        String id="xqolPrompt-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            requireXqolPromptScope(before,deadline);
            if(!hello.capabilities().contains(CurrentXqolPrompt.Action.QUERY_PROMPT.capability()))throw new IOException("Actual current xqolPrompt query capability absent");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            Instant until=readDeadline(deadline);byte[] packet=xqolPromptPacket(id,CurrentXqolPrompt.Action.QUERY_PROMPT,before,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),until);
            outcome=retainReadOutcome(dispatchRead(id,packet,until,()->{requireBackgroundAtCoreWrite();try{requireXqolPromptScope(before,until);}catch(IOException invalid){throw new UncheckedIOException(invalid);}latestXqolPrompt=null;}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new XqolPromptUnavailable(outcome,"Actual xqolPrompt query has no qualified ACK");}
            var frame=CurrentXqolPromptResult.decodeOutcome(ack);requireXqolPromptFrame(frame,CurrentXqolPrompt.Action.QUERY_PROMPT,before);
            if(frame.effectAttempted()||frame.nativeReturned()||frame.claimSequence().signum()!=0)throw new IOException("Readonly xqolPrompt query unexpectedly attempted an effect/claim");
            if(frame.status()!=CurrentXqolPromptResult.Status.AVAILABLE)return new XqolPromptUnavailable(ack,frame.unavailableReason().orElseThrow());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual xqolPrompt query custody absent"));
            var received=new XqolPromptReceived(this,before,frame,ack,custody,until);latestXqolPrompt=received;
            requireXqolPromptOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){latestXqolPrompt=null;return new XqolPromptUnavailable(xqolPromptFailure(id,outcome,invalid),reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();latestXqolPrompt=null;
            unresolvedCoreControl=new Unknown(id,"Actual xqolPrompt query interrupted after write; preserve original, block effects",retainedOutbound(id),Optional.empty());return new XqolPromptUnavailable(unresolvedCoreControl,"Original xqolPrompt query interrupted");}
    }
    private void requireXqolPromptFrame(CurrentXqolPromptResult frame,CurrentXqolPrompt.Action action,CoreReceived before)throws IOException {
        if(frame.action()!=action||frame.status()==CurrentXqolPromptResult.Status.INDETERMINATE||!frame.cleanupKnown())throw new IOException("Actual xqolPrompt action/cleanup uncertain");
        if(frame.factsBefore().isPresent()&&!frame.factsBefore().orElseThrow().equals(((CoreFrame.Partial)before.frame).prefix()))throw new IOException("Actual xqolPrompt Core differs from original source");
        if(frame.owner().isPresent()&&!frame.owner().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Actual xqolPrompt owner crossed connection");
        if(frame.effectAttempted()&&frame.status()!=CurrentXqolPromptResult.dispatchedStatus(action))throw new IOException("Native xqolPrompt effect unqualified; never replay");
    }
    private void requireXqolPromptCustody(AckReceived actual,NativeRequestChronology custody)throws IOException {
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)||originalRequestChronology(actual.requestId()).filter(custody::equals).isEmpty())throw new IOException("XqolPrompt crossed original Game/session/custody");
        custody.verify(actual);
    }
    private void requireXqolPromptOriginal(XqolPromptReceived actual,Instant until)throws IOException {
        Objects.requireNonNull(until);if(actual==null||actual.issuer!=this||actual!=latestXqolPrompt||actual.actionAttempted)throw new IOException("Original private xqolPrompt query unavailable or consumed");
        requireXqolPromptScope(actual.before,until);Instant now=chronologyClock.instant();
        if(until.isAfter(actual.validUntil)||!now.isBefore(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("XqolPrompt query escaped original Core/deadline/chronology");
        requireXqolPromptCustody(actual.original,actual.custody);
        var frame=CurrentXqolPromptResult.decodeOutcome(actual.original);requireXqolPromptFrame(frame,CurrentXqolPrompt.Action.QUERY_PROMPT,actual.before);
        if(!frame.equals(actual.frame)||frame.status()!=CurrentXqolPromptResult.Status.AVAILABLE)throw new IOException("Actual xqolPrompt query frame changed");
        if(!Arrays.equals(actual.original.outbound().orElseThrow().originalPacket(),xqolPromptPacket(actual.original.requestId(),CurrentXqolPrompt.Action.QUERY_PROMPT,actual.before,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),actual.validUntil)))throw new IOException("Original xqolPrompt query body/deadline changed");
    }
    public synchronized XqolPromptPrepared prepareCurrentXqolPromptAction(XqolPromptReceived query,CurrentXqolPrompt.Action action)throws IOException {
        Objects.requireNonNull(query);Objects.requireNonNull(action);if(action==CurrentXqolPrompt.Action.QUERY_PROMPT)throw new IOException("A query cannot prepare an effect");
        if(query.issuer==this&&query.prepared!=null){if(query.prepared.action!=action)throw new IOException("Original prompt query already prepared the other action");return query.prepared;}
        requireXqolPromptOriginal(query,query.validUntil);
        if(!hello.capabilities().contains(action.capability()))throw new IOException("Actual fixed known-instance reply capability absent");
        var selected=query.frame.source().orElseThrow();
        int actualInstanceId=selected.event().orElseThrow(()->new IOException("Actual current known prompt absent")).instanceId();
        if(!selected.admits(action))throw new IOException("Desired actual xqolPrompt source does not admit the single reviewed reply");
        String id="xqolPrompt-ack-"+UUID.randomUUID().toString().replace("-","");
        return query.prepared=new XqolPromptPrepared(this,query,action,actualInstanceId,selected,id,xqolPromptPacket(id,action,query.before,query.frame.providerGeneration(),query.frame.querySequence(),Optional.of(actualInstanceId),query.validUntil));
    }
    public synchronized DispatchOutcome submitCurrentXqolPromptAction(XqolPromptPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);if(original.issuer!=this||original.query.prepared!=original)return zero(original.id,"Foreign xqolPrompt reply preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original xqolPrompt call has no reusable write authority");original.called=true;DispatchOutcome outcome=null;
        try {
            var query=original.query;requireXqolPromptOriginal(query,original.deadline());
            if(!hello.capabilities().contains(original.action.capability())||!original.selected.admits(original.action)||!query.frame.source().orElseThrow().equals(original.selected)||original.selected.event().filter(e->e.instanceId()==original.instanceId).isEmpty())throw new IOException("Actual original fixed reply no longer admissible");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            if(!Arrays.equals(original.packet.value(),xqolPromptPacket(original.id,original.action,query.before,query.frame.providerGeneration(),query.frame.querySequence(),Optional.of(original.instanceId),original.deadline())))throw new IOException("Original reply packet/body drift");
            outcome=dispatch(original.id,original.packet.value(),original.deadline(),()->{requireBackgroundAtCoreWrite();try{requireXqolPromptOriginal(query,original.deadline());}catch(IOException invalid){throw new UncheckedIOException(invalid);}query.actionAttempted=true;query.before.controlAttempted=true;heldSnapshotInvalidated=true;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return original.outcome=unknown;}
            if(outcome instanceof AckReceived ack){
                var frame=CurrentXqolPromptResult.decodeOutcome(ack);requireXqolPromptFrame(frame,original.action,query.before);
                if(!frame.providerGeneration().equals(query.frame.providerGeneration())||!frame.querySequence().equals(query.frame.querySequence())||frame.instanceId().filter(n->n==original.instanceId).isEmpty())throw new IOException("Reply ACK changed original private lease");
                var custody=originalRequestChronology(original.id).orElseThrow(()->new IOException("Actual reply custody absent"));requireXqolPromptCustody(ack,custody);
                if(custody.writeEntered().order().compareTo(query.custody.responseReceived().order())<=0||custody.responseReceived().observedAt().isAfter(original.deadline())||custody.responseReceived().observedAt().isAfter(chronologyClock.instant()))throw new IOException("Reply ACK escaped original query chronology/deadline");
                if(frame.successful()&&!frame.source().equals(query.frame.source()))throw new IOException("Reply before-source differs from original private query");
                original.latestFrame=frame;
            }
            return original.outcome=outcome;
        }catch(IOException|RuntimeException invalid){return original.outcome=xqolPromptFailure(original.id,outcome,invalid);}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(original.id,"XqolPrompt reply interrupted after original write; never replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;}
    }
    private DispatchOutcome xqolPromptFailure(String id,DispatchOutcome outcome,Exception invalid) {
        if(!sentRequestIds.contains(id))return zero(id,reason(invalid));
        if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
        unresolvedCoreControl=new Unknown(id,"XqolPrompt original source/custody unqualified after write; no replay: "+reason(invalid),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());return unresolvedCoreControl;
    }


    public sealed interface FullscreenRead permits FullscreenReceived,FullscreenUnavailable { DispatchOutcome original(); }
    public static final class FullscreenReceived implements FullscreenRead {
        private final NativeGameTransport issuer;private final CoreReceived before;private final CurrentFullscreenEventResult frame;
        private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private boolean actionAttempted;private FullscreenPrepared prepared;
        private FullscreenReceived(NativeGameTransport issuer,CoreReceived before,CurrentFullscreenEventResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.before=before;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentFullscreenEventResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant until)throws IOException{Objects.requireNonNull(actual).requireFullscreenOriginal(this,until);}
    }
    public record FullscreenUnavailable(DispatchOutcome original,String reason)implements FullscreenRead {public FullscreenUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    public static final class FullscreenPrepared {
        private final NativeGameTransport issuer;private final FullscreenReceived query;private final String id;private final NativeWire.Bytes packet;
        private final int instanceId;private final CurrentFullscreenEventSource selected;
        private boolean called;private DispatchOutcome outcome;private CurrentFullscreenEventResult latestFrame;
        private FullscreenPrepared(NativeGameTransport issuer,FullscreenReceived query,int instanceId,CurrentFullscreenEventSource selected,String id,byte[] packet){this.issuer=issuer;this.query=query;this.instanceId=instanceId;this.selected=selected;this.id=id;this.packet=new NativeWire.Bytes(packet);}
        public String requestId(){return id;}public int instanceId(){return instanceId;}public CurrentFullscreenEventSource selected(){return selected;}public NativeWire.Bytes originalPacket(){return packet;}public Instant deadline(){return query.validUntil;}
        public Optional<CurrentFullscreenEventResult> latestFrame(){return Optional.ofNullable(latestFrame);}
    }
    private FullscreenReceived latestFullscreen;
    private byte[] fullscreenPacket(String id,CurrentFullscreenEvent.Action action,CoreReceived before,BigInteger provider,BigInteger query,Optional<Integer> instanceId,Instant until)throws IOException {
        if(!(before.frame instanceof CoreFrame.Partial core))throw new IOException("Exact current fullscreen Core required");
        var request=CurrentFullscreenEvent.request(core,action,provider,query,instanceId);var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
        fields.put("core_control_deadline_unix_ms",until.toEpochMilli());return NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
    }
    private void requireFullscreenScope(CoreReceived before,Instant until)throws IOException {
        Objects.requireNonNull(before);requireCoreOriginal(before,until);
        if(applicationExitAttempted||before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
            throw new IOException("Actual unused Core and resolved owner scope required for fullscreen observation/reply");
        if(!(before.frame instanceof CoreFrame.Partial core)||core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)throw new IOException("Exact current267 Core required");
        CurrentLetter.requirePrefix(core.prefix());
    }
    public synchronized FullscreenRead readCurrentFullscreenEvent(CoreReceived before,Instant deadline)throws InterruptedException {
        String id="fullscreen-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            requireFullscreenScope(before,deadline);
            if(!hello.capabilities().contains(CurrentFullscreenEvent.Action.QUERY_FULLSCREEN.capability()))throw new IOException("Actual current fullscreen query capability absent");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            Instant until=readDeadline(deadline);byte[] packet=fullscreenPacket(id,CurrentFullscreenEvent.Action.QUERY_FULLSCREEN,before,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),until);
            outcome=retainReadOutcome(dispatchRead(id,packet,until,()->{requireBackgroundAtCoreWrite();try{requireFullscreenScope(before,until);}catch(IOException invalid){throw new UncheckedIOException(invalid);}latestFullscreen=null;}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new FullscreenUnavailable(outcome,"Actual fullscreen query has no qualified ACK");}
            var frame=CurrentFullscreenEventResult.decodeOutcome(ack);requireFullscreenFrame(frame,CurrentFullscreenEvent.Action.QUERY_FULLSCREEN,before);
            if(frame.effectAttempted()||frame.nativeReturned()||frame.claimSequence().signum()!=0)throw new IOException("Readonly fullscreen query unexpectedly attempted an effect/claim");
            if(frame.status()!=CurrentFullscreenEventResult.Status.AVAILABLE)return new FullscreenUnavailable(ack,frame.unavailableReason().orElseThrow());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual fullscreen query custody absent"));
            var received=new FullscreenReceived(this,before,frame,ack,custody,until);latestFullscreen=received;
            requireFullscreenOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){latestFullscreen=null;return new FullscreenUnavailable(fullscreenFailure(id,outcome,invalid),reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();latestFullscreen=null;
            unresolvedCoreControl=new Unknown(id,"Actual fullscreen query interrupted after write; preserve original, block effects",retainedOutbound(id),Optional.empty());return new FullscreenUnavailable(unresolvedCoreControl,"Original fullscreen query interrupted");}
    }
    private void requireFullscreenFrame(CurrentFullscreenEventResult frame,CurrentFullscreenEvent.Action action,CoreReceived before)throws IOException {
        if(frame.action()!=action||frame.status()==CurrentFullscreenEventResult.Status.INDETERMINATE||!frame.cleanupKnown())throw new IOException("Actual fullscreen action/cleanup uncertain");
        if(frame.factsBefore().isPresent()&&!frame.factsBefore().orElseThrow().equals(((CoreFrame.Partial)before.frame).prefix()))throw new IOException("Actual fullscreen Core differs from original source");
        if(frame.owner().isPresent()&&!frame.owner().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Actual fullscreen owner crossed connection");
        if(frame.effectAttempted()&&frame.status()!=CurrentFullscreenEventResult.Status.ACK_DISPATCHED)throw new IOException("Native fullscreen effect unqualified; never replay");
    }
    private void requireFullscreenCustody(AckReceived actual,NativeRequestChronology custody)throws IOException {
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)||originalRequestChronology(actual.requestId()).filter(custody::equals).isEmpty())throw new IOException("Fullscreen crossed original Game/session/custody");
        custody.verify(actual);
    }
    private void requireFullscreenOriginal(FullscreenReceived actual,Instant until)throws IOException {
        Objects.requireNonNull(until);if(actual==null||actual.issuer!=this||actual!=latestFullscreen||actual.actionAttempted)throw new IOException("Original private fullscreen query unavailable or consumed");
        requireFullscreenScope(actual.before,until);Instant now=chronologyClock.instant();
        if(until.isAfter(actual.validUntil)||!now.isBefore(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("Fullscreen query escaped original Core/deadline/chronology");
        requireFullscreenCustody(actual.original,actual.custody);
        var frame=CurrentFullscreenEventResult.decodeOutcome(actual.original);requireFullscreenFrame(frame,CurrentFullscreenEvent.Action.QUERY_FULLSCREEN,actual.before);
        if(!frame.equals(actual.frame)||frame.status()!=CurrentFullscreenEventResult.Status.AVAILABLE)throw new IOException("Actual fullscreen query frame changed");
        if(!Arrays.equals(actual.original.outbound().orElseThrow().originalPacket(),fullscreenPacket(actual.original.requestId(),CurrentFullscreenEvent.Action.QUERY_FULLSCREEN,actual.before,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),actual.validUntil)))throw new IOException("Original fullscreen query body/deadline changed");
    }
    public synchronized FullscreenPrepared prepareCurrentFullscreenAcknowledgement(FullscreenReceived query)throws IOException {
        Objects.requireNonNull(query);
        if(query.issuer==this&&query.prepared!=null)return query.prepared;
        requireFullscreenOriginal(query,query.validUntil);
        if(!hello.capabilities().contains(CurrentFullscreenEvent.Action.ACKNOWLEDGE_KNOWN.capability()))throw new IOException("Actual fixed known-instance reply capability absent");
        var selected=query.frame.source().orElseThrow();
        int actualInstanceId=selected.instanceId().orElseThrow(()->new IOException("Actual current fullscreen instance absent"));
        if(!selected.knownAckAdmissible())throw new IOException("Desired actual fullscreen source does not admit the single reviewed reply");
        String id="fullscreen-ack-"+UUID.randomUUID().toString().replace("-","");
        return query.prepared=new FullscreenPrepared(this,query,actualInstanceId,selected,id,fullscreenPacket(id,CurrentFullscreenEvent.Action.ACKNOWLEDGE_KNOWN,query.before,query.frame.providerGeneration(),query.frame.querySequence(),Optional.of(actualInstanceId),query.validUntil));
    }
    public synchronized DispatchOutcome submitCurrentFullscreenAcknowledgement(FullscreenPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);if(original.issuer!=this||original.query.prepared!=original)return zero(original.id,"Foreign fullscreen reply preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original fullscreen call has no reusable write authority");original.called=true;DispatchOutcome outcome=null;
        try {
            var query=original.query;requireFullscreenOriginal(query,original.deadline());
            if(!hello.capabilities().contains(CurrentFullscreenEvent.Action.ACKNOWLEDGE_KNOWN.capability())||!original.selected.knownAckAdmissible()||!query.frame.source().orElseThrow().equals(original.selected)||original.selected.instanceId().filter(n->n==original.instanceId).isEmpty())throw new IOException("Actual original fixed reply no longer admissible");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            if(!Arrays.equals(original.packet.value(),fullscreenPacket(original.id,CurrentFullscreenEvent.Action.ACKNOWLEDGE_KNOWN,query.before,query.frame.providerGeneration(),query.frame.querySequence(),Optional.of(original.instanceId),original.deadline())))throw new IOException("Original reply packet/body drift");
            outcome=dispatch(original.id,original.packet.value(),original.deadline(),()->{requireBackgroundAtCoreWrite();try{requireFullscreenOriginal(query,original.deadline());}catch(IOException invalid){throw new UncheckedIOException(invalid);}query.actionAttempted=true;query.before.controlAttempted=true;heldSnapshotInvalidated=true;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return original.outcome=unknown;}
            if(outcome instanceof AckReceived ack){
                var frame=CurrentFullscreenEventResult.decodeOutcome(ack);requireFullscreenFrame(frame,CurrentFullscreenEvent.Action.ACKNOWLEDGE_KNOWN,query.before);
                if(!frame.providerGeneration().equals(query.frame.providerGeneration())||!frame.querySequence().equals(query.frame.querySequence())||frame.instanceId().filter(n->n==original.instanceId).isEmpty())throw new IOException("Reply ACK changed original private lease");
                var custody=originalRequestChronology(original.id).orElseThrow(()->new IOException("Actual reply custody absent"));requireFullscreenCustody(ack,custody);
                if(custody.writeEntered().order().compareTo(query.custody.responseReceived().order())<=0||custody.responseReceived().observedAt().isAfter(original.deadline())||custody.responseReceived().observedAt().isAfter(chronologyClock.instant()))throw new IOException("Reply ACK escaped original query chronology/deadline");
                if(frame.status()==CurrentFullscreenEventResult.Status.ACK_DISPATCHED&&!frame.source().equals(query.frame.source()))throw new IOException("Reply before-source differs from original private query");
                original.latestFrame=frame;
            }
            return original.outcome=outcome;
        }catch(IOException|RuntimeException invalid){return original.outcome=fullscreenFailure(original.id,outcome,invalid);}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(original.id,"Fullscreen reply interrupted after original write; never replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;}
    }
    private DispatchOutcome fullscreenFailure(String id,DispatchOutcome outcome,Exception invalid) {
        if(!sentRequestIds.contains(id))return zero(id,reason(invalid));
        if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
        unresolvedCoreControl=new Unknown(id,"Fullscreen original source/custody unqualified after write; no replay: "+reason(invalid),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());return unresolvedCoreControl;
    }


    public sealed interface LetterSetRead permits LetterSetReceived,LetterSetUnavailable { DispatchOutcome original(); }
    public static final class LetterSetReceived implements LetterSetRead {
        private final NativeGameTransport issuer;private final CoreReceived before;private final CurrentLetterSetResult frame;
        private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private boolean actionAttempted;private LetterSetPrepared prepared;
        private LetterSetReceived(NativeGameTransport issuer,CoreReceived before,CurrentLetterSetResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.before=before;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentLetterSetResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant until)throws IOException{Objects.requireNonNull(actual).requireLetterSetOriginal(this,until);}
    }
    public record LetterSetUnavailable(DispatchOutcome original,String reason)implements LetterSetRead {public LetterSetUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    public static final class LetterSetPrepared {
        private final NativeGameTransport issuer;private final LetterSetReceived query;private final String id;private final NativeWire.Bytes packet;
        private final int instanceId;private final CurrentLetterSource selected;
        private boolean called;private DispatchOutcome outcome;private CurrentLetterSetResult latestFrame;
        private LetterSetPrepared(NativeGameTransport issuer,LetterSetReceived query,int instanceId,CurrentLetterSource selected,String id,byte[] packet){this.issuer=issuer;this.query=query;this.instanceId=instanceId;this.selected=selected;this.id=id;this.packet=new NativeWire.Bytes(packet);}
        public String requestId(){return id;}public int instanceId(){return instanceId;}public CurrentLetterSource selected(){return selected;}public NativeWire.Bytes originalPacket(){return packet;}public Instant deadline(){return query.validUntil;}
        public Optional<CurrentLetterSetResult> latestFrame(){return Optional.ofNullable(latestFrame);}
    }
    private LetterSetReceived latestLetterSet;
    private byte[] letterSetPacket(String id,CurrentLetterSet.Action action,CoreReceived before,BigInteger provider,BigInteger query,Optional<Integer> instanceId,Instant until)throws IOException {
        if(!(before.frame instanceof CoreFrame.Partial core))throw new IOException("Exact current letter Core required");
        var request=CurrentLetterSet.request(core,action,provider,query,instanceId);var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
        fields.put("core_control_deadline_unix_ms",until.toEpochMilli());return NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
    }
    private void requireLetterSetScope(CoreReceived before,Instant until)throws IOException {
        Objects.requireNonNull(before);requireCoreOriginal(before,until);
        if(applicationExitAttempted||before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
            throw new IOException("Actual unused Core and resolved owner scope required for letter observation/reply");
        if(!(before.frame instanceof CoreFrame.Partial core)||core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)throw new IOException("Exact current267 Core required");
        CurrentLetter.requirePrefix(core.prefix());
    }
    public synchronized LetterSetRead readCurrentLetterSet(CoreReceived before,Instant deadline)throws InterruptedException {
        String id="letter-set-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            requireLetterSetScope(before,deadline);
            if(!hello.capabilities().contains(CurrentLetterSet.Action.QUERY_LETTERS.capability()))throw new IOException("Actual current letter query capability absent");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            Instant until=readDeadline(deadline);byte[] packet=letterSetPacket(id,CurrentLetterSet.Action.QUERY_LETTERS,before,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),until);
            outcome=retainReadOutcome(dispatchRead(id,packet,until,()->{requireBackgroundAtCoreWrite();try{requireLetterSetScope(before,until);}catch(IOException invalid){throw new UncheckedIOException(invalid);}latestLetterSet=null;latestLetter=null;}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new LetterSetUnavailable(outcome,"Actual letter query has no qualified ACK");}
            var frame=CurrentLetterSetResult.decodeOutcome(ack);requireLetterSetFrame(frame,CurrentLetterSet.Action.QUERY_LETTERS,before);
            if(frame.effectAttempted()||frame.nativeReturned()||frame.claimSequence().signum()!=0)throw new IOException("Readonly letter query unexpectedly attempted an effect/claim");
            if(frame.status()!=CurrentLetterSetResult.Status.AVAILABLE)return new LetterSetUnavailable(ack,frame.unavailableReason().orElseThrow());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual letter query custody absent"));
            var received=new LetterSetReceived(this,before,frame,ack,custody,until);latestLetterSet=received;
            requireLetterSetOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){latestLetterSet=null;return new LetterSetUnavailable(letterSetFailure(id,outcome,invalid),reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();latestLetterSet=null;
            unresolvedCoreControl=new Unknown(id,"Actual letter query interrupted after write; preserve original, block effects",retainedOutbound(id),Optional.empty());return new LetterSetUnavailable(unresolvedCoreControl,"Original letter query interrupted");}
    }
    private void requireLetterSetFrame(CurrentLetterSetResult frame,CurrentLetterSet.Action action,CoreReceived before)throws IOException {
        if(frame.action()!=action||frame.status()==CurrentLetterSetResult.Status.INDETERMINATE||!frame.cleanupKnown())throw new IOException("Actual letter action/cleanup uncertain");
        if(frame.factsBefore().isPresent()&&!frame.factsBefore().orElseThrow().equals(((CoreFrame.Partial)before.frame).prefix()))throw new IOException("Actual letter Core differs from original source");
        if(frame.owner().isPresent()&&!frame.owner().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Actual letter owner crossed connection");
        if(frame.effectAttempted()&&frame.status()!=CurrentLetterSetResult.Status.REPLY_DISPATCHED)throw new IOException("Native letter effect unqualified; never replay");
    }
    private void requireLetterSetCustody(AckReceived actual,NativeRequestChronology custody)throws IOException {
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)||originalRequestChronology(actual.requestId()).filter(custody::equals).isEmpty())throw new IOException("Letter crossed original Game/session/custody");
        custody.verify(actual);
    }
    private void requireLetterSetOriginal(LetterSetReceived actual,Instant until)throws IOException {
        Objects.requireNonNull(until);if(actual==null||actual.issuer!=this||actual!=latestLetterSet||actual.actionAttempted)throw new IOException("Original private letter query unavailable or consumed");
        requireLetterSetScope(actual.before,until);Instant now=chronologyClock.instant();
        if(until.isAfter(actual.validUntil)||!now.isBefore(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("Letter query escaped original Core/deadline/chronology");
        requireLetterSetCustody(actual.original,actual.custody);
        var frame=CurrentLetterSetResult.decodeOutcome(actual.original);requireLetterSetFrame(frame,CurrentLetterSet.Action.QUERY_LETTERS,actual.before);
        if(!frame.equals(actual.frame)||frame.status()!=CurrentLetterSetResult.Status.AVAILABLE)throw new IOException("Actual letter query frame changed");
        if(!Arrays.equals(actual.original.outbound().orElseThrow().originalPacket(),letterSetPacket(actual.original.requestId(),CurrentLetterSet.Action.QUERY_LETTERS,actual.before,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),actual.validUntil)))throw new IOException("Original letter query body/deadline changed");
    }
    public synchronized LetterSetPrepared prepareCurrentLetterInstanceReply(LetterSetReceived query,int actualInstanceId)throws IOException {
        Objects.requireNonNull(query);
        if(query.issuer==this&&query.prepared!=null){if(query.prepared.instanceId!=actualInstanceId)throw new IOException("Original complete census already prepared a different actual instance");return query.prepared;}
        requireLetterSetOriginal(query,query.validUntil);
        if(!hello.capabilities().contains(CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE.capability()))throw new IOException("Actual fixed known-instance reply capability absent");
        var selected=query.frame.source().orElseThrow().exactInstance(actualInstanceId);
        if(!selected.knownReplyAdmissible())throw new IOException("Desired actual census row does not admit the single reviewed reply");
        String id="letter-set-reply-"+UUID.randomUUID().toString().replace("-","");
        return query.prepared=new LetterSetPrepared(this,query,actualInstanceId,selected,id,letterSetPacket(id,CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE,query.before,query.frame.providerGeneration(),query.frame.querySequence(),Optional.of(actualInstanceId),query.validUntil));
    }
    public synchronized DispatchOutcome submitCurrentLetterInstanceReply(LetterSetPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);if(original.issuer!=this||original.query.prepared!=original)return zero(original.id,"Foreign letter reply preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original letter call has no reusable write authority");original.called=true;DispatchOutcome outcome=null;
        try {
            var query=original.query;requireLetterSetOriginal(query,original.deadline());
            if(!hello.capabilities().contains(CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE.capability())||!original.selected.knownReplyAdmissible()||!query.frame.source().orElseThrow().exactInstance(original.instanceId).equals(original.selected))throw new IOException("Actual original fixed reply no longer admissible");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            if(!Arrays.equals(original.packet.value(),letterSetPacket(original.id,CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE,query.before,query.frame.providerGeneration(),query.frame.querySequence(),Optional.of(original.instanceId),original.deadline())))throw new IOException("Original reply packet/body drift");
            outcome=dispatch(original.id,original.packet.value(),original.deadline(),()->{requireBackgroundAtCoreWrite();try{requireLetterSetOriginal(query,original.deadline());}catch(IOException invalid){throw new UncheckedIOException(invalid);}query.actionAttempted=true;query.before.controlAttempted=true;heldSnapshotInvalidated=true;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return original.outcome=unknown;}
            if(outcome instanceof AckReceived ack){
                var frame=CurrentLetterSetResult.decodeOutcome(ack);requireLetterSetFrame(frame,CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE,query.before);
                if(!frame.providerGeneration().equals(query.frame.providerGeneration())||!frame.querySequence().equals(query.frame.querySequence())||frame.instanceId().filter(n->n==original.instanceId).isEmpty())throw new IOException("Reply ACK changed original private lease");
                var custody=originalRequestChronology(original.id).orElseThrow(()->new IOException("Actual reply custody absent"));requireLetterSetCustody(ack,custody);
                if(custody.writeEntered().order().compareTo(query.custody.responseReceived().order())<=0||custody.responseReceived().observedAt().isAfter(original.deadline())||custody.responseReceived().observedAt().isAfter(chronologyClock.instant()))throw new IOException("Reply ACK escaped original query chronology/deadline");
                if(frame.status()==CurrentLetterSetResult.Status.REPLY_DISPATCHED&&!frame.source().equals(query.frame.source()))throw new IOException("Reply before-source differs from original private query");
                original.latestFrame=frame;
            }
            return original.outcome=outcome;
        }catch(IOException|RuntimeException invalid){return original.outcome=letterSetFailure(original.id,outcome,invalid);}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(original.id,"Letter reply interrupted after original write; never replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;}
    }
    private DispatchOutcome letterSetFailure(String id,DispatchOutcome outcome,Exception invalid) {
        if(!sentRequestIds.contains(id))return zero(id,reason(invalid));
        if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
        unresolvedCoreControl=new Unknown(id,"Letter original source/custody unqualified after write; no replay: "+reason(invalid),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());return unresolvedCoreControl;
    }


    public sealed interface LetterRead permits LetterReceived,LetterUnavailable { DispatchOutcome original(); }
    public static final class LetterReceived implements LetterRead {
        private final NativeGameTransport issuer;private final CoreReceived before;private final CurrentLetterResult frame;
        private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private boolean actionAttempted;private LetterPrepared prepared;
        private LetterReceived(NativeGameTransport issuer,CoreReceived before,CurrentLetterResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.before=before;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentLetterResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant until)throws IOException{Objects.requireNonNull(actual).requireLetterOriginal(this,until);}
    }
    public record LetterUnavailable(DispatchOutcome original,String reason)implements LetterRead {public LetterUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    public static final class LetterPrepared {
        private final NativeGameTransport issuer;private final LetterReceived query;private final String id;private final NativeWire.Bytes packet;
        private boolean called;private DispatchOutcome outcome;private CurrentLetterResult latestFrame;
        private LetterPrepared(NativeGameTransport issuer,LetterReceived query,String id,byte[] packet){this.issuer=issuer;this.query=query;this.id=id;this.packet=new NativeWire.Bytes(packet);}
        public String requestId(){return id;}public NativeWire.Bytes originalPacket(){return packet;}public Instant deadline(){return query.validUntil;}
        public Optional<CurrentLetterResult> latestFrame(){return Optional.ofNullable(latestFrame);}
    }
    private LetterReceived latestLetter;
    private byte[] letterPacket(String id,CurrentLetter.Action action,CoreReceived before,BigInteger provider,BigInteger query,Instant until)throws IOException {
        if(!(before.frame instanceof CoreFrame.Partial core))throw new IOException("Exact current letter Core required");
        var request=CurrentLetter.request(core,action,provider,query);var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
        fields.put("core_control_deadline_unix_ms",until.toEpochMilli());return NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
    }
    private void requireLetterScope(CoreReceived before,Instant until)throws IOException {
        Objects.requireNonNull(before);requireCoreOriginal(before,until);
        if(applicationExitAttempted||before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
            throw new IOException("Actual unused Core and resolved owner scope required for letter observation/reply");
        if(!(before.frame instanceof CoreFrame.Partial core)||core.build()!=ExactCk3Build.CK3_121003_STEAM_26785313)throw new IOException("Exact current267 Core required");
        CurrentLetter.requirePrefix(core.prefix());
    }
    public synchronized LetterRead readCurrentLetter(CoreReceived before,Instant deadline)throws InterruptedException {
        String id="letter-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            requireLetterScope(before,deadline);
            if(!hello.capabilities().contains(CurrentLetter.Action.QUERY_LETTER.capability()))throw new IOException("Actual current letter query capability absent");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            Instant until=readDeadline(deadline);byte[] packet=letterPacket(id,CurrentLetter.Action.QUERY_LETTER,before,BigInteger.ZERO,BigInteger.ZERO,until);
            outcome=retainReadOutcome(dispatchRead(id,packet,until,()->{requireBackgroundAtCoreWrite();try{requireLetterScope(before,until);}catch(IOException invalid){throw new UncheckedIOException(invalid);}latestLetter=null;}));
            if(!(outcome instanceof AckReceived ack)){if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;return new LetterUnavailable(outcome,"Actual letter query has no qualified ACK");}
            var frame=CurrentLetterResult.decodeOutcome(ack);requireLetterFrame(frame,CurrentLetter.Action.QUERY_LETTER,before);
            if(frame.effectAttempted()||frame.nativeReturned()||frame.claimSequence().signum()!=0)throw new IOException("Readonly letter query unexpectedly attempted an effect/claim");
            if(frame.status()!=CurrentLetterResult.Status.AVAILABLE)return new LetterUnavailable(ack,frame.unavailableReason().orElseThrow());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual letter query custody absent"));
            var received=new LetterReceived(this,before,frame,ack,custody,until);latestLetter=received;
            requireLetterOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid){latestLetter=null;return new LetterUnavailable(letterFailure(id,outcome,invalid),reason(invalid));}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();latestLetter=null;
            unresolvedCoreControl=new Unknown(id,"Actual letter query interrupted after write; preserve original, block effects",retainedOutbound(id),Optional.empty());return new LetterUnavailable(unresolvedCoreControl,"Original letter query interrupted");}
    }
    private void requireLetterFrame(CurrentLetterResult frame,CurrentLetter.Action action,CoreReceived before)throws IOException {
        if(frame.action()!=action||frame.status()==CurrentLetterResult.Status.INDETERMINATE||!frame.cleanupKnown())throw new IOException("Actual letter action/cleanup uncertain");
        if(frame.factsBefore().isPresent()&&!frame.factsBefore().orElseThrow().equals(((CoreFrame.Partial)before.frame).prefix()))throw new IOException("Actual letter Core differs from original source");
        if(frame.owner().isPresent()&&!frame.owner().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Actual letter owner crossed connection");
        if(frame.effectAttempted()&&frame.status()!=CurrentLetterResult.Status.REPLY_DISPATCHED)throw new IOException("Native letter effect unqualified; never replay");
    }
    private void requireLetterCustody(AckReceived actual,NativeRequestChronology custody)throws IOException {
        if(!custody.session().equals(session())||!custody.custodyEpoch().equals(custodyEpoch)||originalRequestChronology(actual.requestId()).filter(custody::equals).isEmpty())throw new IOException("Letter crossed original Game/session/custody");
        custody.verify(actual);
    }
    private void requireLetterOriginal(LetterReceived actual,Instant until)throws IOException {
        Objects.requireNonNull(until);if(actual==null||actual.issuer!=this||actual!=latestLetter||actual.actionAttempted)throw new IOException("Original private letter query unavailable or consumed");
        requireLetterScope(actual.before,until);Instant now=chronologyClock.instant();
        if(until.isAfter(actual.validUntil)||!now.isBefore(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("Letter query escaped original Core/deadline/chronology");
        requireLetterCustody(actual.original,actual.custody);
        var frame=CurrentLetterResult.decodeOutcome(actual.original);requireLetterFrame(frame,CurrentLetter.Action.QUERY_LETTER,actual.before);
        if(!frame.equals(actual.frame)||frame.status()!=CurrentLetterResult.Status.AVAILABLE)throw new IOException("Actual letter query frame changed");
        if(!Arrays.equals(actual.original.outbound().orElseThrow().originalPacket(),letterPacket(actual.original.requestId(),CurrentLetter.Action.QUERY_LETTER,actual.before,BigInteger.ZERO,BigInteger.ZERO,actual.validUntil)))throw new IOException("Original letter query body/deadline changed");
    }
    public synchronized LetterPrepared prepareCurrentLetterReply(LetterReceived query)throws IOException {
        Objects.requireNonNull(query);
        if(query.issuer==this&&query.prepared!=null)return query.prepared;
        requireLetterOriginal(query,query.validUntil);
        if(!hello.capabilities().contains(CurrentLetter.Action.REPLY_KNOWN.capability()))throw new IOException("Actual fixed known-letter reply capability absent");
        if(!query.frame.source().orElseThrow().knownReplyAdmissible())throw new IOException("Actual source does not permit the single reviewed reply");
        String id="letter-reply-"+UUID.randomUUID().toString().replace("-","");
        return query.prepared=new LetterPrepared(this,query,id,letterPacket(id,CurrentLetter.Action.REPLY_KNOWN,query.before,query.frame.providerGeneration(),query.frame.querySequence(),query.validUntil));
    }
    public synchronized DispatchOutcome submitCurrentLetterReply(LetterPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);if(original.issuer!=this||original.query.prepared!=original)return zero(original.id,"Foreign letter reply preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original letter call has no reusable write authority");original.called=true;DispatchOutcome outcome=null;
        try {
            var query=original.query;requireLetterOriginal(query,original.deadline());
            if(!hello.capabilities().contains(CurrentLetter.Action.REPLY_KNOWN.capability())||!query.frame.source().orElseThrow().knownReplyAdmissible())throw new IOException("Actual original fixed reply no longer admissible");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            if(!Arrays.equals(original.packet.value(),letterPacket(original.id,CurrentLetter.Action.REPLY_KNOWN,query.before,query.frame.providerGeneration(),query.frame.querySequence(),original.deadline())))throw new IOException("Original reply packet/body drift");
            outcome=dispatch(original.id,original.packet.value(),original.deadline(),()->{requireBackgroundAtCoreWrite();try{requireLetterOriginal(query,original.deadline());}catch(IOException invalid){throw new UncheckedIOException(invalid);}query.actionAttempted=true;query.before.controlAttempted=true;heldSnapshotInvalidated=true;});
            if(outcome instanceof Unknown unknown){unresolvedCoreControl=unknown;return original.outcome=unknown;}
            if(outcome instanceof AckReceived ack){
                var frame=CurrentLetterResult.decodeOutcome(ack);requireLetterFrame(frame,CurrentLetter.Action.REPLY_KNOWN,query.before);
                if(!frame.providerGeneration().equals(query.frame.providerGeneration())||!frame.querySequence().equals(query.frame.querySequence()))throw new IOException("Reply ACK changed original private lease");
                var custody=originalRequestChronology(original.id).orElseThrow(()->new IOException("Actual reply custody absent"));requireLetterCustody(ack,custody);
                if(custody.writeEntered().order().compareTo(query.custody.responseReceived().order())<=0||custody.responseReceived().observedAt().isAfter(original.deadline())||custody.responseReceived().observedAt().isAfter(chronologyClock.instant()))throw new IOException("Reply ACK escaped original query chronology/deadline");
                if(frame.status()==CurrentLetterResult.Status.REPLY_DISPATCHED&&!frame.source().equals(query.frame.source()))throw new IOException("Reply before-source differs from original private query");
                original.latestFrame=frame;
            }
            return original.outcome=outcome;
        }catch(IOException|RuntimeException invalid){return original.outcome=letterFailure(original.id,outcome,invalid);}
        catch(InterruptedException interrupted){if(!sentRequestIds.contains(original.id))throw interrupted;Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(original.id,"Letter reply interrupted after original write; never replay",original.packet.value(),Optional.empty());return original.outcome=unresolvedCoreControl;}
    }
    private DispatchOutcome letterFailure(String id,DispatchOutcome outcome,Exception invalid) {
        if(!sentRequestIds.contains(id))return zero(id,reason(invalid));
        if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
        unresolvedCoreControl=new Unknown(id,"Letter original source/custody unqualified after write; no replay: "+reason(invalid),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());return unresolvedCoreControl;
    }

    public sealed interface DjcTargetQueryRead permits DjcTargetQueryReceived,DjcTargetQueryUnavailable { DispatchOutcome original(); }
    public static final class DjcTargetQueryReceived implements DjcTargetQueryRead {
        private final NativeGameTransport issuer;private final CoreReceived before;private final NativeCharacterId target;
        private final CurrentDjcTargetWarQueryResult frame;private final AckReceived original;private final NativeRequestChronology custody;private final Instant validUntil;
        private DjcTargetQueryReceived(NativeGameTransport issuer,CoreReceived before,NativeCharacterId target,CurrentDjcTargetWarQueryResult frame,AckReceived original,NativeRequestChronology custody,Instant until){this.issuer=issuer;this.before=before;this.target=target;this.frame=frame;this.original=original;this.custody=custody;validUntil=until;}
        public CurrentDjcTargetWarQueryResult frame(){return frame;}@Override public AckReceived original(){return original;}public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport actual,Instant until)throws IOException{Objects.requireNonNull(actual).requireDjcTargetQueryOriginal(this,until);}
    }
    public record DjcTargetQueryUnavailable(DispatchOutcome original,String reason)implements DjcTargetQueryRead {public DjcTargetQueryUnavailable{Objects.requireNonNull(original);StrictJson.text(reason);}}
    private DjcTargetQueryReceived latestDjcTargetQuery;
    public synchronized DjcTargetQueryRead readCurrentDjcTargetWars(CoreReceived before,NativeCharacterId target,Instant deadline)throws InterruptedException {
        String id="djc-target-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;Instant until=deadline;
        try {
            Objects.requireNonNull(before);Objects.requireNonNull(target);Objects.requireNonNull(deadline);requireCoreOriginal(before,deadline);
            if(applicationExitAttempted||before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("Readonly DJC target query requires an actual unused Core without unresolved effects");
            if(!(before.frame instanceof CoreFrame.Partial core))throw new IOException("Actual current Core required for target query");
            var request=CurrentDjcTargetWarQuery.request(core,target);
            if(!hello.capabilities().contains(CurrentDjcTargetWarQuery.CAPABILITY))throw new IOException("Actual current DJC target query capability absent");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            until=readDeadline(deadline);final Instant queryUntil=until;
            var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));fields.put("core_control_deadline_unix_ms",until.toEpochMilli());
            byte[] packet=NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
            outcome=retainReadOutcome(dispatchRead(id,packet,until,()->{
                requireBackgroundAtCoreWrite();try{requireCoreOriginal(before,queryUntil);}catch(IOException invalid){throw new UncheckedIOException(invalid);}
                if(before.controlAttempted||applicationExitAttempted)throw new IllegalStateException("Original query Core consumed before write");
                latestDjcTargetQuery=null;
            }));
            if(!(outcome instanceof AckReceived ack)) {
                if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;
                return new DjcTargetQueryUnavailable(outcome,"Actual DJC readonly query has no qualified ACK");
            }
            var frame=CurrentDjcTargetWarQueryResult.decodeOutcome(ack);
            if(frame.status()==CurrentDjcTargetWarQueryResult.Status.INDETERMINATE||!frame.scratchCleanupKnown())throw new IOException("Native DJC scratch cleanup indeterminate; preserve original and block effects");
            if(frame.coreBefore().isPresent()&&!frame.coreBefore().orElseThrow().equals(core.prefix()))throw new IOException("Actual DJC Core differs from original source");
            if(frame.ownerWitness().isPresent()&&!frame.ownerWitness().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("Actual DJC owner crossed connection generation");
            if(frame.target().isPresent()&&!frame.target().orElseThrow().equals(target))throw new IOException("Actual DJC target differs from original query");
            if(!frame.available())return new DjcTargetQueryUnavailable(ack,frame.unavailableReason().orElseThrow());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("Actual target-query custody absent"));
            var received=new DjcTargetQueryReceived(this,before,target,frame,ack,custody,until);latestDjcTargetQuery=received;
            requireDjcTargetQueryOriginal(received,until);return received;
        }catch(IOException|RuntimeException invalid) {
            latestDjcTargetQuery=null;
            if(sentRequestIds.contains(id)) {
                if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
                unresolvedCoreControl=new Unknown(id,"Current DJC query source/custody unqualified after write; never replay effects: "+reason(invalid),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());
                return new DjcTargetQueryUnavailable(unresolvedCoreControl,reason(invalid));
            }
            return new DjcTargetQueryUnavailable(zero(id,reason(invalid)),reason(invalid));
        }catch(InterruptedException interrupted) {
            if(!sentRequestIds.contains(id))throw interrupted;Thread.currentThread().interrupt();latestDjcTargetQuery=null;
            unresolvedCoreControl=new Unknown(id,"Original DJC readonly query interrupted after write; preserve original, block effects",retainedOutbound(id),Optional.empty());
            return new DjcTargetQueryUnavailable(unresolvedCoreControl,"Original target query interrupted");
        }
    }
    private void requireDjcTargetQueryOriginal(DjcTargetQueryReceived actual,Instant until)throws IOException {
        Objects.requireNonNull(until);
        if(actual.issuer!=this||actual!=latestDjcTargetQuery||applicationExitAttempted||actual.before.controlAttempted||unresolvedCoreControl!=null||unresolvedFullClockControl!=null)
            throw new IOException("Original same-receiver DJC readonly query unavailable");
        requireCoreOriginal(actual.before,until);Instant now=chronologyClock.instant();
        if(until.isAfter(actual.validUntil)||!now.isBefore(actual.validUntil)||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)||actual.custody.writeEntered().order().compareTo(actual.before.custody.responseReceived().order())<=0)
            throw new IOException("DJC target query escaped original Core/deadline/chronology");
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)||originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isEmpty())
            throw new IOException("DJC target query crossed original Game/session/custody");
        actual.custody.verify(actual.original);
        if(!CurrentDjcTargetWarQueryResult.decodeOutcome(actual.original).equals(actual.frame)||!actual.frame.available()
                ||!actual.frame.coreBefore().orElseThrow().equals(((CoreFrame.Partial)actual.before.frame).prefix())||!actual.frame.target().orElseThrow().equals(actual.target)
                ||!actual.frame.ownerWitness().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))throw new IOException("DJC target query differs from original Core/target/native witness");
        var request=CurrentDjcTargetWarQuery.request((CoreFrame.Partial)actual.before.frame,actual.target);
        var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));fields.put("core_control_deadline_unix_ms",actual.validUntil.toEpochMilli());
        if(!Arrays.equals(actual.original.outbound().orElseThrow().originalPacket(),NativeWire.execute(actual.original.requestId(),request.step(),BigInteger.ZERO,StrictJson.canonical(fields))))
            throw new IOException("Original DJC query body/target/deadline changed");
    }

    /** One original fixed observer request; exported fields are archival DATA only. */
    public static final class AubObserverPrepared {
        private final NativeGameTransport issuer;private final CoreReceived before;
        private final String id;private final Instant deadline;private final NativeWire.Bytes packet;
        private boolean called;private DispatchOutcome outcome;
        private AubObserverPrepared(NativeGameTransport issuer,CoreReceived before,String id,Instant deadline,byte[] packet){
            this.issuer=issuer;this.before=before;this.id=id;this.deadline=deadline;this.packet=new NativeWire.Bytes(packet);
        }
        public String requestId(){return id;}public Instant deadline(){return deadline;}
        public NativeWire.Bytes originalPacket(){return packet;}
        public int sourceDateRaw(){return ((CoreFrame.Partial)before.frame).prefix().dateRaw();}
    }
    private AubObserverPrepared preparedAubObserver;
    /** Fixed observer only; no caller-selected console text, file path, contents or SHA. */
    public synchronized AubObserverPrepared prepareCurrentAubObserverFixture(CoreReceived before,Instant deadline)throws IOException {
        Objects.requireNonNull(before);Objects.requireNonNull(deadline);requireCoreOriginal(before,deadline);
        if(unresolvedCoreControl!=null||unresolvedFullClockControl!=null)throw new IOException("Unresolved original control forbids the fixed observer fixture");
        if(activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null||applicationExitAttempted||before.controlAttempted)
            throw new IOException("Fixed observer requires an unused actual Core outside business/recovery/exit scopes");
        if(!(before.frame instanceof CoreFrame.Partial partial))throw new IOException("Actual current partial Core required for the fixed observer");
        NativeRequest request=CurrentAubObserverFixture.request(partial);
        if(!hello.capabilities().contains(CurrentAubObserverFixture.CAPABILITY))throw new IOException("Current fixed observer capability not advertised");
        if(preparedAubObserver!=null) {
            if(preparedAubObserver.before==before&&preparedAubObserver.deadline.equals(deadline)&&!preparedAubObserver.called)return preparedAubObserver;
            throw new IOException("One original fixed observer preparation only; no replacement id or repeat");
        }
        if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
        long until=deadline.toEpochMilli();if(until<=0||until>before.validUntil.toEpochMilli())throw new IOException("Fixed observer cannot extend the original Core deadline");
        ObjectNode fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));fields.put("core_control_deadline_unix_ms",until);
        String id="aub-observer-"+UUID.randomUUID().toString().replace("-","");
        preparedAubObserver=new AubObserverPrepared(this,before,id,deadline,NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields)));
        return preparedAubObserver;
    }
    /** A single bounded fixture callback. A native dispatch is not nine markers, business or physical SAVE. */
    public synchronized DispatchOutcome submitCurrentAubObserverFixture(AubObserverPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);
        if(original.issuer!=this||original!=preparedAubObserver)return zero(original.id,"Foreign or superseded fixed observer preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original fixed observer has no reusable write authority");
        original.called=true;
        if(unresolvedCoreControl!=null)return original.outcome=unresolvedCoreControl;
        if(unresolvedFullClockControl!=null)return original.outcome=unresolvedFullClockControl;
        try {
            requireCoreOriginal(original.before,original.deadline);
            if(original.before.controlAttempted||applicationExitAttempted||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("Original fixed observer Core/scope already consumed");
            DispatchOutcome outcome=dispatch(original.id,original.packet.value(),original.deadline,()->{
                requireBackgroundAtCoreWrite();
                if(original.before.controlAttempted)throw new IllegalStateException("Original fixed observer Core claim consumed");
                original.before.controlAttempted=true;
            });
            if(outcome instanceof AckReceived ack) {
                try {
                    var result=CurrentAubObserverFixtureResult.decodeOutcome(ack);
                    if(result.ownerWitness().isPresent()&&!result.ownerWitness().orElseThrow().connectionGeneration().equals(hello.connectionGeneration()))
                        throw new IOException("Fixed observer owner belongs to another connection generation");
                    if(result.dispatched()&&!result.coreBefore().orElseThrow().equals(((CoreFrame.Partial)original.before.frame).prefix()))
                        throw new IOException("Fixed observer dispatched under another original Core");
                    if(result.status()==CurrentAubObserverFixtureResult.Status.INDETERMINATE||result.effectAttempted()&&!result.dispatched())
                        throw new IOException("Native fixed observer effect remains unqualified/indeterminate; never replay");
                }catch(IOException|RuntimeException invalid) {
                    indeterminateCoreAcknowledgement=ack;
                    unresolvedCoreControl=new Unknown(original.id,"Current fixed observer ACK unqualified; never replay: "+reason(invalid),original.packet.value(),Optional.of(ack.originalFrame()));
                    return original.outcome=unresolvedCoreControl;
                }
            }
            if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;
            return original.outcome=outcome;
        }catch(IOException|RuntimeException failure) {
            if(sentRequestIds.contains(original.id)) {
                unresolvedCoreControl=new Unknown(original.id,"Fixed observer write entered without qualified terminal; never replay: "+reason(failure),original.packet.value(),Optional.empty());
                return original.outcome=unresolvedCoreControl;
            }
            return original.outcome=zero(original.id,reason(failure));
        }catch(InterruptedException interrupted) {
            if(!sentRequestIds.contains(original.id))throw interrupted;
            Thread.currentThread().interrupt();
            unresolvedCoreControl=new Unknown(original.id,"Fixed observer interrupted after original write entry; never replay",original.packet.value(),Optional.empty());
            return original.outcome=unresolvedCoreControl;
        }
    }

    /** Issuer-bound original checkpoint request. Public fields are archival DATA, never reconstructed write authority. */
    public static final class CoreCheckpointPrepared {
        private final NativeGameTransport issuer;
        private final CoreReceived before;
        private final String id;
        private final Instant deadline;
        private final NativeWire.Bytes packet;
        private boolean called,knownTerminal;
        private DispatchOutcome outcome;
        private CoreCheckpointPrepared(NativeGameTransport issuer,CoreReceived before,String id,Instant deadline,byte[] packet){
            this.issuer=issuer;this.before=before;this.id=id;this.deadline=deadline;this.packet=new NativeWire.Bytes(packet);
        }
        public String requestId(){return id;}
        public Instant deadline(){return deadline;}
        public NativeWire.Bytes originalPacket(){return packet;}
        public int sourceDateRaw(){return ((CoreFrame.Partial)before.frame).prefix().dateRaw();}
    }
    private CoreCheckpointPrepared preparedCoreCheckpoint;
    /** Prepare once so the existing caller can archive the exact id/body/deadline before network write. */
    public synchronized CoreCheckpointPrepared prepareCurrentCoreCheckpoint(CoreReceived before,Instant deadline)throws IOException {
        Objects.requireNonNull(before);Objects.requireNonNull(deadline);requireCoreOriginal(before,deadline);
        if(unresolvedCoreControl!=null||unresolvedFullClockControl!=null)throw new IOException("Unresolved original control forbids a new checkpoint");
        if(activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null||applicationExitAttempted||before.controlAttempted)
            throw new IOException("Checkpoint requires an unused actual Core outside business/recovery/exit scopes");
        if(!(before.frame instanceof CoreFrame.Partial partial))throw new IOException("Actual partial Core required for checkpoint");
        NativeRequest request=CurrentCoreCheckpointSave.request(partial);
        if(!hello.capabilities().contains(CurrentCoreCheckpointSave.CAPABILITY))throw new IOException("Current narrow checkpoint capability not advertised");
        if(preparedCoreCheckpoint!=null) {
            var previous=preparedCoreCheckpoint;
            if(previous.before==before&&previous.deadline.equals(deadline)&&!previous.called)return previous;
            if(!previous.knownTerminal)throw new IOException("Original checkpoint preparation/write remains unresolved; no replacement id");
            var old=((CoreFrame.Partial)previous.before.frame).prefix();var now=partial.prefix();
            if(now.dateRaw()<=old.dateRaw()||now.localPlayerId()!=old.localPlayerId()||now.playedCharacterId()!=old.playedCharacterId())
                throw new IOException("New checkpoint requires strictly newer date from the same actual player/actor");
        }
        if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
        long until=deadline.toEpochMilli();if(until<=0||until>before.validUntil.toEpochMilli())throw new IOException("Checkpoint cannot extend original Core deadline");
        ObjectNode fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));fields.put("core_control_deadline_unix_ms",until);
        String id="core-save-"+UUID.randomUUID().toString().replace("-","");
        preparedCoreCheckpoint=new CoreCheckpointPrepared(this,before,id,deadline,NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields)));
        return preparedCoreCheckpoint;
    }
    /** One call/claim only. Native submitted is not physical-file confirmation. */
    public synchronized DispatchOutcome submitCurrentCoreCheckpoint(CoreCheckpointPrepared original)throws InterruptedException {
        Objects.requireNonNull(original);
        if(original.issuer!=this||original!=preparedCoreCheckpoint)return zero(original.id,"Foreign or superseded checkpoint preparation");
        if(original.called)return original.outcome!=null?original.outcome:zero(original.id,"Original checkpoint call has no reusable write authority");
        original.called=true;
        if(unresolvedCoreControl!=null)return original.outcome=unresolvedCoreControl;
        if(unresolvedFullClockControl!=null)return original.outcome=unresolvedFullClockControl;
        try {
            requireCoreOriginal(original.before,original.deadline);
            if(original.before.controlAttempted||applicationExitAttempted||activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("Original checkpoint Core/scope already consumed");
            DispatchOutcome outcome=dispatch(original.id,original.packet.value(),original.deadline,()->{
                requireBackgroundAtCoreWrite();
                if(original.before.controlAttempted)throw new IllegalStateException("Original checkpoint Core claim consumed");
                original.before.controlAttempted=true;
            });
            if(outcome instanceof AckReceived ack) {
                try {
                    var result=CurrentCoreCheckpointSaveResult.decodeOutcome(ack);
                    if(result.submission().isPresent()&&result.submission().orElseThrow().dateRaw()!=original.sourceDateRaw())
                        throw new IOException("Checkpoint result changed the original Core date");
                    if(result.status()==CurrentCoreCheckpointSaveResult.Status.INDETERMINATE)
                        throw new IOException("Native checkpoint indeterminate; original remains UNKNOWN");
                    original.knownTerminal=true;
                }catch(IOException|RuntimeException invalid){
                    indeterminateCoreAcknowledgement=ack;
                    unresolvedCoreControl=new Unknown(original.id,"Current checkpoint ACK unqualified/indeterminate; never replay: "+reason(invalid),original.packet.value(),Optional.of(ack.originalFrame()));
                    return original.outcome=unresolvedCoreControl;
                }
            }
            if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;
            return original.outcome=outcome;
        }catch(IOException|RuntimeException failure){
            if(sentRequestIds.contains(original.id)) {
                unresolvedCoreControl=new Unknown(original.id,"Checkpoint write entered without qualified terminal; never replay: "+reason(failure),original.packet.value(),Optional.empty());
                return original.outcome=unresolvedCoreControl;
            }
            return original.outcome=zero(original.id,reason(failure));
        }catch(InterruptedException interrupted){
            if(!sentRequestIds.contains(original.id))throw interrupted;
            Thread.currentThread().interrupt();
            unresolvedCoreControl=new Unknown(original.id,"Checkpoint interrupted after original write entry; never replay",original.packet.value(),Optional.empty());
            return original.outcome=unresolvedCoreControl;
        }
    }
    private boolean applicationExitAttempted;
    /** The private original Core permits one background application-exit request, never an exit receipt. */
    public synchronized DispatchOutcome submitCoreNormalExit(CoreReceived before,Instant deadline)throws InterruptedException {
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;
        if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        String id="core-exit-"+UUID.randomUUID().toString().replace("-","");
        try {
            Objects.requireNonNull(before);Objects.requireNonNull(deadline);requireCoreOriginal(before,deadline);
            if(activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("application exit cannot borrow a business mailbox or recovery scope");
            if(applicationExitAttempted||before.controlAttempted)throw new IOException("application exit or this original Core already entered a write");
            if(!(before.frame instanceof CoreFrame.Partial partial))throw new IOException("actual available partial Core required for application exit");
            NativeRequest request=CoreApplicationExit.request(partial);
            if(!hello.capabilities().contains(CoreApplicationExit.CAPABILITY))throw new IOException("actual application exit capability is unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            ObjectNode fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
            long until=deadline.toEpochMilli();
            if(until<=0||until>before.validUntil.toEpochMilli())throw new IOException("application exit cannot extend its original absolute query deadline");
            fields.put("core_control_deadline_unix_ms",until);
            byte[] packet=NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
            DispatchOutcome outcome=dispatchLifecycle(id,packet,deadline,()->{
                requireBackgroundAtCoreWrite();
                if(applicationExitAttempted||before.controlAttempted)throw new IllegalStateException("original application exit claim is consumed");
                before.controlAttempted=true;applicationExitAttempted=true;
            });
            return retainCoreControlOutcome(outcome);
        } catch(IOException|RuntimeException failure) {
            if(sentRequestIds.contains(id)) {
                unresolvedCoreControl=new Unknown(id,"application exit failed after actual write entry; never replay: "+reason(failure),retainedOutbound(id),Optional.empty());
                return unresolvedCoreControl;
            }
            return zero(id,reason(failure));
        }
    }
    /**
     * A separate fixed core-only control path. It does not create a full-observation SubmissionPermit,
     * a business receipt, a confirmed SAVE, or an observed engine effect. UNKNOWN keeps its original ID.
     */
    public synchronized DispatchOutcome submitCoreClockControl(CoreReceived before,CoreClockControl.Step step,
            Instant deadline)throws InterruptedException {
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;
        if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        String id="core-control-"+UUID.randomUUID().toString().replace("-","");
        try {
            requireWorldActionMode();
            Objects.requireNonNull(before);Objects.requireNonNull(step);Objects.requireNonNull(deadline);
            requireCoreOriginal(before,deadline);
            if(applicationExitAttempted)throw new IOException("application exit already entered a write in this held transport");
            if(activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)
                throw new IOException("standalone core control cannot borrow a business mailbox or recovery scope");
            if(before.controlAttempted)throw new IOException("this original core receipt already entered a control write");
            if(!(before.frame instanceof CoreFrame.Partial partial))throw new IOException("actual available partial core required for core control");
            var prefix=partial.prefix();
            if(!prefix.mapReady()||!prefix.hasPlayedCharacter()||!prefix.playedCharacterAlive())
                throw new IOException("core control requires the actual living played character and ready map");
            if(step==CoreClockControl.Step.SAVE_CHECKPOINT&&!prefix.paused())
                throw new IOException("core SAVE submission requires an actual paused core prefix");
            NativeRequest request=step==CoreClockControl.Step.SAVE_CHECKPOINT
                    && partial.build()==ExactCk3Build.CK3_1210_STEAM_26757580
                    ?CoreClockControl.requestMappedSave61(requireMappedSave61(),partial):CoreClockControl.request(step,partial);
            if(!hello.capabilities().contains(step.requiredCapability()))throw new IOException("actual core control capability is unavailable");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            ObjectNode fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
            long until=deadline.toEpochMilli();
            if(until<=0||until>before.validUntil.toEpochMilli())throw new IOException("core control cannot extend its original absolute query deadline");
            fields.put("core_control_deadline_unix_ms",until);
            byte[] packet=NativeWire.execute(id,request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
            DispatchOutcome outcome=dispatch(id,packet,deadline,()->{
                requireBackgroundAtCoreWrite();
                if(hotfixSave(request))try{requireMappedSave61();}catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                if(before.controlAttempted)throw new IllegalStateException("original core receipt is already consumed");
                before.controlAttempted=true;
            });
            return retainCoreControlOutcome(outcome);
        } catch(IOException|RuntimeException failure) {
            if(sentRequestIds.contains(id)) {
                unresolvedCoreControl=new Unknown(id,"core control failed after actual write entry; never replay: "+reason(failure),retainedOutbound(id),Optional.empty());
                return unresolvedCoreControl;
            }
            return zero(id,reason(failure));
        }
    }
    private void retainDateEvaluationFailure(org.xar.ck3.control.reconciliation.LateOutcome.Status status,AckReceived original) {
        if((status.triggerFlags()&(1L<<15))!=0&&failedDateEvaluation==null)failedDateEvaluation=original;
    }
    private void requireDateEvaluationAvailable() {
        if(failedDateEvaluation!=null)throw new IllegalStateException("Date evaluation_failure observed in original request "
                +failedDateEvaluation.requestId()+"; preserve its result and withhold clock writes");
    }
    private void requireBackgroundAtCoreWrite() {
        requireDateEvaluationAvailable();
        try {endpoint.verifyCoreControlWindowPolicy();}
        catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
    }
    private DispatchOutcome retainCoreControlOutcome(DispatchOutcome outcome) {
        if(outcome instanceof AckReceived ack&&ack.originalResultToken().isPresent()) {
            try {
                var result=NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));
                if(textEquals(result,"queue_status","indeterminate")||textEquals(result,"dispatch_status","indeterminate")) {
                    indeterminateCoreAcknowledgement=ack;
                    unresolvedCoreControl=new Unknown(ack.requestId(),"Native core result is indeterminate; retain the original only, never replay",
                            ack.outbound().orElseThrow().originalPacket(),Optional.of(ack.originalFrame()));
                    return unresolvedCoreControl;
                }
            } catch(IOException|RuntimeException malformed) {
                // An unrecognized ACK remains original DATA; it grants neither effect nor a confirmed SAVE/exit.
            }
        }
        if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;
        return outcome;
    }
    /** Freeze this query's actual deadline; a later consumer cannot give an old ACK a new window. */
    public synchronized CoreRead readCoreFrameReceived(Instant deadline)throws InterruptedException {
        Instant until=readDeadline(Objects.requireNonNull(deadline));
        DispatchOutcome original=readCoreFrame(until);
        try {
            CoreFrame frame=CoreFramePublicCodec.decodeOutcome(original);
            AckReceived ack=(AckReceived)original;
            NativeRequestChronology custody=originalRequestChronology(ack.requestId())
                    .orElseThrow(()->new IOException("actual core ACK custody unavailable"));
            var received=new CoreReceived(this,frame,ack,custody,until);
            requireCoreOriginal(received,until);return received;
        } catch(IOException|RuntimeException invalid) {return new CoreReadUnavailable(original,reason(invalid));}
    }
    private void requireCoreOriginal(CoreReceived actual,Instant operationDeadline)throws IOException {
        Objects.requireNonNull(operationDeadline);
        if(actual.issuer!=this||hello==null||closed||terminalFailure!=null)
            throw new IOException("core receipt requires its identical live held receiver");
        Instant now=chronologyClock.instant();
        if(!now.isBefore(actual.validUntil)||!now.isBefore(operationDeadline)||operationDeadline.isAfter(actual.validUntil)
                ||actual.custody.responseReceived().observedAt().isAfter(now)
                ||actual.custody.responseReceived().observedAt().isAfter(actual.validUntil)
                ||actual.custody.writeEntered().observedAt().isBefore(helloObservedAt))
            throw new IOException("core receipt escaped its original finite query window or HELLO chronology");
        verifyHeld(operationDeadline);
        if(!actual.custody.session().equals(session())||!actual.custody.custodyEpoch().equals(custodyEpoch)
                ||!originalRequestChronology(actual.original.requestId()).filter(actual.custody::equals).isPresent())
            throw new IOException("core receipt crossed its original Game/session/connection/custody");
        actual.custody.verify(actual.original);
        CoreFrame decoded=CoreFramePublicCodec.decodeOutcome(actual.original);
        ObjectNode rawHello=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
        String version=NativeWire.text(rawHello.get("expected_ck3_version"));
        if(!decoded.equals(actual.frame)||!decoded.build().matches(version,hello.gameSha256())
                ||!hello.adapterId().equals(decoded.build().coreFrameAdapterId()))
            throw new IOException("core result belongs to another exact executable or original received frame");
    }
    /** The fixed standalone partial-prefix read. It cannot carry a caller-selected step or mutation. */
    @Override public synchronized DispatchOutcome readCoreFrame(Instant deadline) throws InterruptedException {
        String id = "core-frame-" + UUID.randomUUID().toString().replace("-", "");
        try {
            awaitHello(deadline); verifyEndpoint();
            ObjectNode original = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(), 4, hello.packet().value().length)));
            String version=NativeWire.text(original.get("expected_ck3_version"));
            boolean exactFour=ExactCk3Build.CK3_12004.matches(version,hello.gameSha256())
                    &&hello.adapterId().equals("ck3-1.20.0.4-msvc-x64");
            boolean exactFlorin=ExactCk3Build.florinCoreFrameBuild(version,hello.gameSha256(),hello.adapterId())
                    .filter(build->hello.adapterId().equals(build.coreFrameAdapterId())).isPresent();
            if (!hello.capabilities().contains("game.query.core-frame.v1")||!(exactFour||exactFlorin))
                throw new IOException("standalone core prefix requires the original ready exact core build and advertised capability");
            if (sentRequestIds.size() >= maximumSubmissions) throw new IOException("Native request identity retention limit reached");
            return retainReadOutcome(dispatchRead(id, NativeWire.execute(id, "query-core-frame-v1", BigInteger.ZERO, new byte[] {'{', '}'}), readDeadline(deadline), () -> { }));
        } catch (IOException | RuntimeException failure) { return retainReadOutcome(zero(id, reason(failure))); }
    }
    /** Independently published READ for an exact supported full-state producer. No unresolved original is resubmitted. */
    @Override public synchronized NativeFreshSnapshotPort.Result readFreshFullState(Instant deadline)throws InterruptedException {
        if(armyIdentity126Source!=null)return new NativeFreshSnapshotPort.Unavailable(
                zero("identity126-default-read-"+UUID.randomUUID().toString().replace("-",""),"explicit identity-only source cannot issue an ordinary Full/clock receipt"),
                "explicit identity-only source cannot issue an ordinary Full/clock receipt");
        return readFreshFullStateInternal(deadline,false);
    }
    public synchronized ArmyIdentityRead readFreshArmyIdentity126(Instant deadline)throws InterruptedException {
        return armyIdentityResult(readFreshFullStateInternal(deadline,true));
    }
    private ArmyIdentityRead armyIdentityResult(NativeFreshSnapshotPort.Result result) {
        if(result instanceof NativeFreshSnapshotPort.Unavailable absent)return new ArmyIdentityUnavailable(absent,absent.reason());
        try {
            var actual=(NativeFreshSnapshotPort.Received)result;var source=requireArmyIdentity126Source(true);
            var normalized=DriverObservationAssembler.canonicalNativeState(actual.originalFrame(),armyObservationMode());
            return new ArmyIdentityReceived(actual,source,normalized.semantic());
        }catch(IOException|RuntimeException invalid){return new ArmyIdentityUnavailable(result,reason(invalid));}
    }
    private NativeFreshSnapshotPort.Result readFreshFullStateInternal(Instant deadline,boolean identityOnly126)throws InterruptedException {
        if(pendingFreshSnapshot!=null)return freshUnavailable(pendingFreshSnapshot,"original fresh READ remains unresolved; collect its original outcome without resubmission");
        String id="fresh-state-"+UUID.randomUUID().toString().replace("-","");
        try {
            if(identityOnly126)requireArmyIdentity126Source(false);
            awaitHello(deadline);verifyEndpoint();
            ObjectNode original=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
            String version=NativeWire.text(original.get("expected_ck3_version"));
            boolean exactSix=hello.adapterId().equals("ck3-1.19.0.6-msvc-x64")
                    &&hello.gameSha256().equalsIgnoreCase("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86")
                    &&version.equals("1.19.0.6");
            boolean exactFour=hello.adapterId().equals("ck3-1.20.0.4-msvc-x64")
                    &&hello.gameSha256().equalsIgnoreCase("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                    &&version.equals("1.20.0.4");
            var florinProfile=ExactCk3Build.florinCoreFullBuild(version,hello.gameSha256(),hello.adapterId());
            boolean exactFlorin=florinProfile.isPresent();
            if(!hello.capabilities().contains(NativeFreshSnapshotPort.CAPABILITY)||!hello.capabilities().contains("game.state.snapshot")||!(exactSix||exactFour||exactFlorin))
                throw new IOException("fresh full-state READ requires an exact supported HELLO and both independent full-state capabilities");
            if(identityOnly126) {
                if(florinProfile.orElse(null)!=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111)
                    throw new IOException("identity126 requires its exact current Full profile");
                requireArmyIdentity126Source(true);
            }else if(exactFlorin)requireCurrentFull111Source(florinProfile.orElseThrow());
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            byte[] request=NativeWire.execute(id,NativeFreshSnapshotPort.STEP,BigInteger.ZERO,new byte[]{'{','}'});
            var capture=new FreshSnapshotCapture(id);pendingFreshSnapshot=capture;
            return finishFreshRead(capture,retainReadOutcome(dispatchRead(id,request,readDeadline(deadline),()->{})));
        } catch(IOException|RuntimeException failure) {
            if(sentRequestIds.contains(id)) {
                if(pendingFreshSnapshot==null)pendingFreshSnapshot=new FreshSnapshotCapture(id);
                if(pendingFreshSnapshot.outcome==null)pendingFreshSnapshot.outcome=new Unknown(id,
                        "fresh READ failed after actual write entry; never replay: "+reason(failure),retainedOutbound(id),Optional.empty());
                return freshUnavailable(pendingFreshSnapshot,reason(failure));
            }
            pendingFreshSnapshot=null;return new NativeFreshSnapshotPort.Unavailable(retainReadOutcome(zero(id,reason(failure))),reason(failure));
        } catch(InterruptedException interrupted) {
            if(!sentRequestIds.contains(id))pendingFreshSnapshot=null;
            throw interrupted;
        }
    }
    @Override public synchronized NativeFreshSnapshotPort.Result collectFreshFullState(String originalRequestId,Instant deadline)throws IOException,InterruptedException {
        if(armyIdentity126Source!=null)throw new IOException("identity126 requires its explicit original read collector");
        return collectFreshFullStateInternal(originalRequestId,deadline);
    }
    public synchronized ArmyIdentityRead collectFreshArmyIdentity126(String originalRequestId,Instant deadline)throws IOException,InterruptedException {
        requireArmyIdentity126Source(true);
        return armyIdentityResult(collectFreshFullStateInternal(originalRequestId,deadline));
    }
    private NativeFreshSnapshotPort.Result collectFreshFullStateInternal(String originalRequestId,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(originalRequestId);var capture=pendingFreshSnapshot;
        if(capture==null||!capture.requestId.equals(originalRequestId))throw new IOException("no identical original fresh READ is held for collection");
        if(capture.outcome instanceof AckReceived)return finishFreshRead(capture,capture.outcome);
        Optional<AckReceived> original=collectOriginalOutcome(originalRequestId,deadline);
        return original.isPresent()?finishFreshRead(capture,retainReadOutcome(original.orElseThrow()))
                :freshUnavailable(capture,"original fresh READ has no received ACK yet; no resubmission");
    }
    private NativeFreshSnapshotPort.Result finishFreshRead(FreshSnapshotCapture capture,DispatchOutcome outcome) {
        capture.outcome=Objects.requireNonNull(outcome);
        if(outcome instanceof Unknown)return freshUnavailable(capture,"original fresh READ outcome is UNKNOWN; never replay");
        if(outcome instanceof RejectedBeforeDispatch||outcome instanceof AckReceived ack&&!ack.nativeOk()) {
            pendingFreshSnapshot=null;return freshUnavailable(capture,freshRejectionDiagnostic(outcome));
        }
        if(capture.invalid!=null)return freshUnavailable(capture,capture.invalid);
        if(capture.frame==null||capture.received==null)return freshUnavailable(capture,"positive ACK has no independently received matching original state packet");
        try {
            var received=new NativeFreshSnapshotPort.Received((AckReceived)outcome,capture.frame,capture.received);
            pendingFreshSnapshot=null;
            heldSnapshotInvalidated = false;
            return received;
        } catch(IOException|RuntimeException failure){return freshUnavailable(capture,reason(failure));}
    }
    /** Diagnostic only: the original outcome and every acceptance/pending predicate remain unchanged. */
    private static String freshRejectionDiagnostic(DispatchOutcome actual) {
        final int limit=512;
        var message=new StringBuilder(limit);
        boolean beforeWrite=actual instanceof RejectedBeforeDispatch;
        message.append(beforeWrite?"original fresh READ rejected before write; request_id=":
                "original fresh READ received negative Native ACK; request_id=");
        appendFreshDiagnostic(message,actual.requestId(),Math.min(limit,message.length()+128));
        message.append(beforeWrite?"; reason=":"; error=");
        if(actual instanceof RejectedBeforeDispatch rejected) {
            appendFreshDiagnostic(message,rejected.proof().reason(),limit);
        } else if(actual instanceof AckReceived ack) {
            try {
                var decoded=NativeWire.decode(ack.originalPacket());
                if(decoded instanceof NativeWire.CommandResult original && !original.nativeOk()
                        && original.requestId().equals(ack.requestId())
                        && Arrays.equals(original.payload().value(),ack.originalFrame().bytes())) {
                    if(original.error().presence()==NativeWire.Presence.ABSENT)message.append("<absent>");
                    else appendFreshDiagnostic(message,new String(original.error().token().orElseThrow().value(),
                            java.nio.charset.StandardCharsets.UTF_8),limit);
                } else message.append("<original ACK fields differ>");
            } catch(IOException|RuntimeException malformed) {
                appendFreshDiagnostic(message,"<original error unavailable: "+malformed.getClass().getSimpleName()+">",limit);
            }
        }
        return message.toString();
    }
    private static void appendFreshDiagnostic(StringBuilder output,String value,int limit) {
        for(int index=0;index<value.length() && output.length()<limit;) {
            char next=value.charAt(index++);
            if(Character.isHighSurrogate(next)) {
                if(index<value.length() && Character.isLowSurrogate(value.charAt(index))) {
                    if(output.length()+2>limit)break;
                    output.append(next).append(value.charAt(index++));
                } else output.append('\uFFFD');
            } else output.append(Character.isLowSurrogate(next)?'\uFFFD':next);
        }
    }
    private NativeFreshSnapshotPort.Unavailable freshUnavailable(FreshSnapshotCapture capture,String reason) {
        DispatchOutcome original=capture.outcome;
        if(original==null)original=new Unknown(capture.requestId,"actual fresh READ is still held; never replay",retainedOutbound(capture.requestId),Optional.empty());
        return new NativeFreshSnapshotPort.Unavailable(original,reason,Optional.ofNullable(capture.frame),Optional.ofNullable(capture.received));
    }
    private void captureFreshSnapshot(NativeWire.Snapshot received,ObservedFrame actual,NativeRequestChronology.Event event)throws IOException {
        var capture=pendingFreshSnapshot;if(capture==null)return;
        ObjectNode raw=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(received.packet().value(),4,received.packet().byteLength())));
        var marker=raw.get("read_request_id");if(marker==null)return;
        if(!marker.isTextual()){capture.invalid="fresh state request marker has the wrong JSON type";return;}
        if(!capture.requestId.equals(marker.textValue()))return;
        if(capture.frame!=null){capture.invalid="multiple original state packets claim one fresh READ";return;}
        capture.frame=actual;capture.received=event;
        var written=writtenRequests.get(capture.requestId);
        if(written==null||written.completed().isEmpty()||!written.session().equals(actual.session())
                ||event.order().compareTo(written.completed().orElseThrow().order())<=0)
            capture.invalid="fresh state did not follow this actual original request write";
    }
    public sealed interface FrontendMenuRead permits FrontendMenuReceived,FrontendMenuUnavailable {
        DispatchOutcome original();
    }
    public record FrontendMenuUnavailable(DispatchOutcome original,String reason) implements FrontendMenuRead {
        public FrontendMenuUnavailable {Objects.requireNonNull(original);Objects.requireNonNull(reason);}
    }
    /** Receiver-owned occurrence, never constructed from configuration, a Core or a caller menu boolean. */
    public static final class FrontendMenuReceived implements FrontendMenuRead {
        private final NativeGameTransport issuer;
        private final FrontendMenuFrameV1 frame;
        private final AckReceived original;
        private final NativeRequestChronology custody;
        private final FrontendMenuFrameV1PublicCodec.Request request;
        private final Instant validUntil;
        private FrontendMenuPrepared prepared;
        private boolean writeAttempted;
        private FrontendMenuReceived(NativeGameTransport issuer,FrontendMenuFrameV1 frame,AckReceived original,
                NativeRequestChronology custody,FrontendMenuFrameV1PublicCodec.Request request) {
            this.issuer=issuer;this.frame=frame;this.original=original;this.custody=custody;this.request=request;this.validUntil=request.deadline();
        }
        public FrontendMenuFrameV1 frame(){return frame;}
        @Override public AckReceived original(){return original;}
        public Instant validUntil(){return validUntil;}
        public void requireOriginal(NativeGameTransport receiver)throws IOException {receiver.requireFrontendMenuOriginal(this);}
    }
    public static final class FrontendMenuPrepared {
        private final NativeGameTransport issuer;
        private final FrontendMenuReceived menu;
        private final FrontendMenuFrameV1PublicCodec.Request request;
        private final String requestId;
        private final NativeWire.Bytes originalPacket;
        private DispatchOutcome outcome;
        private boolean writeAttempted;
        private FrontendMenuPrepared(NativeGameTransport issuer,FrontendMenuReceived menu,
                FrontendMenuFrameV1PublicCodec.Request request,String requestId,byte[] packet) {
            this.issuer=issuer;this.menu=menu;this.request=request;this.requestId=requestId;this.originalPacket=new NativeWire.Bytes(packet);
        }
        public String requestId(){return requestId;}
        public FrontendMenuFrameV1.Action action(){return request.action();}
        public Instant deadline(){return request.deadline();}
        public NativeWire.Bytes originalPacket(){return originalPacket;}
    }
    /** A current no-world source is obtained directly on the permitted frontend owner, without fabricating CoreReceived. */
    public synchronized FrontendMenuRead readCurrentFrontendMenu(Instant deadline)throws InterruptedException {
        String id="frontend-current-query-"+UUID.randomUUID().toString().replace("-","");DispatchOutcome outcome=null;
        try {
            Instant until=readDeadline(Objects.requireNonNull(deadline));requireCurrentFrontendHello(FrontendMenuFrameV1.Action.QUERY_MENU,until);
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            var request=FrontendMenuFrameV1PublicCodec.query(until);
            outcome=retainReadOutcome(dispatchRead(id,NativeWire.execute(id,request.action().step(),BigInteger.ZERO,FrontendMenuFrameV1PublicCodec.additionalFields(request).bytes()),request.deadline(),()->{}));
            if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;
            if(!(outcome instanceof AckReceived ack))return new FrontendMenuUnavailable(outcome,"original current frontend query has no actual ACK");
            var frame=FrontendMenuFrameV1PublicCodec.decodeOutcome(ack);
            if(frame.status()==FrontendMenuFrameV1.Status.INDETERMINATE){indeterminateCoreAcknowledgement=ack;unresolvedCoreControl=new Unknown(id,"current frontend query remains indeterminate; new effects blocked",retainedOutbound(id),Optional.of(ack.originalFrame()));return new FrontendMenuUnavailable(unresolvedCoreControl,"original indeterminate current frontend query");}
            if(frame.action()!=FrontendMenuFrameV1.Action.QUERY_MENU||frame.status()!=FrontendMenuFrameV1.Status.AVAILABLE)
                return new FrontendMenuUnavailable(ack,"actual current frontend source unavailable: "+frame.status().wire());
            var custody=originalRequestChronology(id).orElseThrow(()->new IOException("actual menu query chronology missing"));
            var received=new FrontendMenuReceived(this,frame,ack,custody,request);requireFrontendMenuOriginal(received);return received;
        }catch(InterruptedException interrupted) {
            if(!sentRequestIds.contains(id))throw interrupted;
            Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(id,"current menu query interrupted after write; new effects blocked",retainedOutbound(id),Optional.empty());
            return new FrontendMenuUnavailable(unresolvedCoreControl,"original current menu query interrupted after actual write");
        }catch(IOException|RuntimeException failure) {
            if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
            if(sentRequestIds.contains(id)) {
                unresolvedCoreControl=new Unknown(id,"current menu query source/custody validation failed after write; new effects blocked: "+reason(failure),retainedOutbound(id),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());
                return new FrontendMenuUnavailable(unresolvedCoreControl,reason(failure));
            }
            return new FrontendMenuUnavailable(outcome==null?zero(id,reason(failure)):outcome,reason(failure));
        }
    }
    /** Prepare a fixed action from one identical receiver occurrence, retaining its exact encoded deadline. */
    public synchronized FrontendMenuPrepared prepareCurrentFrontendMenuAction(FrontendMenuReceived menu,FrontendMenuFrameV1.Action action)throws IOException,InterruptedException {
        Objects.requireNonNull(menu);Objects.requireNonNull(action);requireFrontendMenuOriginal(menu);
        if(action.readOnly())throw new IOException("current frontend effects require one fixed non-query action");
        if(unresolvedCoreControl!=null||unresolvedFullClockControl!=null)throw new IOException("original unresolved action blocks current frontend effects");
        if(applicationExitAttempted)throw new IOException("application exit already entered its original write");
        if(menu.prepared!=null){if(menu.prepared.request.action()!=action)throw new IOException("original menu occurrence already prepared for another fixed action");return menu.prepared;}
        if(menu.writeAttempted)throw new IOException("original menu occurrence is consumed");
        requireCurrentFrontendHello(action,menu.validUntil);
        var source=menu.frame.source().orElseThrow();
        if(action==FrontendMenuFrameV1.Action.OPEN_BOOKMARKS&&source.route()!=FrontendMenuFrameV1.Route.MAIN_MENU)throw new IOException("fixed open-bookmarks requires actual main menu");
        if((action==FrontendMenuFrameV1.Action.SELECT_1066_BOOKMARK||action==FrontendMenuFrameV1.Action.SELECT_ROBERT_1066)&&source.route()!=FrontendMenuFrameV1.Route.BOOKMARKS)throw new IOException("fixed bookmark selection requires actual bookmarks source");
        if(action==FrontendMenuFrameV1.Action.START_ROBERT_1066&&!source.startAdmissible())throw new IOException("actual fixed Robert start source is not admissible");
        if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
        var request=FrontendMenuFrameV1PublicCodec.action(action,menu.request,new FrontendMenuFrameV1PublicCodec.Lease(menu.frame.providerGeneration(),menu.frame.querySequence()));
        String id="frontend-current-effect-"+UUID.randomUUID().toString().replace("-","");
        menu.prepared=new FrontendMenuPrepared(this,menu,request,id,NativeWire.execute(id,action.step(),BigInteger.ZERO,FrontendMenuFrameV1PublicCodec.additionalFields(request).bytes()));return menu.prepared;
    }
    /** One transfer only. Callback acknowledgement never becomes natural process exit or loaded-world evidence. */
    public synchronized DispatchOutcome submitCurrentFrontendMenuAction(FrontendMenuPrepared prepared)throws IOException,InterruptedException {
        Objects.requireNonNull(prepared);if(prepared.issuer!=this||prepared.menu.issuer!=this)throw new IOException("prepared menu action belongs to another actual receiver");
        if(prepared.outcome!=null)return prepared.outcome;
        if(unresolvedCoreControl!=null)return unresolvedCoreControl;if(unresolvedFullClockControl!=null)return unresolvedFullClockControl;
        if(prepared.writeAttempted){unresolvedCoreControl=new Unknown(prepared.requestId,"original menu write entered without a terminal; never replay",prepared.originalPacket.value(),Optional.empty());prepared.outcome=unresolvedCoreControl;return prepared.outcome;}
        DispatchOutcome outcome=null;
        try {
            requireFrontendMenuOriginal(prepared.menu);requireCurrentFrontendHello(prepared.request.action(),prepared.deadline());
            if(prepared.menu.prepared!=prepared||prepared.menu.writeAttempted||applicationExitAttempted)throw new IOException("original menu claim consumed or changed");
            outcome=dispatch(prepared.requestId,prepared.originalPacket.value(),prepared.deadline(),()->{
                requireBackgroundAtCoreWrite();
                try{requireFrontendMenuOriginal(prepared.menu);}catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                if(prepared.writeAttempted||prepared.menu.writeAttempted)throw new IllegalStateException("original menu claim is consumed");
                prepared.writeAttempted=true;prepared.menu.writeAttempted=true;
                if(prepared.request.action()==FrontendMenuFrameV1.Action.QUIT_MENU)applicationExitAttempted=true;
            });
            if(outcome instanceof AckReceived ack) {
                var frame=FrontendMenuFrameV1PublicCodec.decodeOutcome(ack);
                if(frame.status()==FrontendMenuFrameV1.Status.INDETERMINATE||!frame.nativeOk()&&frame.effectAttempted()){indeterminateCoreAcknowledgement=ack;unresolvedCoreControl=new Unknown(ack.requestId(),"Native current menu effect is indeterminate; never replay across actions",prepared.originalPacket.value(),Optional.of(ack.originalFrame()));outcome=unresolvedCoreControl;}
                else if(!ack.custody().orElseThrow().session().equals(prepared.menu.custody.session()))throw new IOException("frontend effect crossed original menu session");
            }
            if(outcome instanceof Unknown unknown)unresolvedCoreControl=unknown;
            prepared.outcome=outcome;return outcome;
        }catch(InterruptedException interrupted) {
            if(!sentRequestIds.contains(prepared.requestId))throw interrupted;
            Thread.currentThread().interrupt();unresolvedCoreControl=new Unknown(prepared.requestId,"current menu effect interrupted after write; never replay",prepared.originalPacket.value(),Optional.empty());prepared.outcome=unresolvedCoreControl;return prepared.outcome;
        }catch(IOException|RuntimeException failure) {
            if(sentRequestIds.contains(prepared.requestId)) {
                if(outcome instanceof AckReceived ack)indeterminateCoreAcknowledgement=ack;
                unresolvedCoreControl=new Unknown(prepared.requestId,"current menu effect uncertain after original write; never replay: "+reason(failure),prepared.originalPacket.value(),outcome instanceof AckReceived ack?Optional.of(ack.originalFrame()):Optional.empty());prepared.outcome=unresolvedCoreControl;
            }else prepared.outcome=zero(prepared.requestId,reason(failure));
            return prepared.outcome;
        }
    }
    private void requireCurrentFrontendHello(FrontendMenuFrameV1.Action action,Instant deadline)throws IOException,InterruptedException {
        awaitHello(deadline);verifyEndpoint();
        var original=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
        if(!FrontendMenuFrameV1.BUILD.matches(NativeWire.text(original.get("expected_ck3_version")),hello.gameSha256())
                ||!hello.adapterId().equals(FrontendMenuFrameV1.BUILD.coreFrameAdapterId())||!hello.capabilities().contains(action.capability()))
            throw new IOException("current no-world menu requires exact current267 HELLO and its actual fixed capability: "+action.capability());
        if(activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null)throw new IOException("current menu cannot borrow a World business mailbox or recovery scope");
    }
    private void requireFrontendMenuOriginal(FrontendMenuReceived menu)throws IOException {
        if(menu.issuer!=this||hello==null||closed||terminalFailure!=null)throw new IOException("menu occurrence requires its identical live receiver");
        Instant now=chronologyClock.instant();
        if(!now.isBefore(menu.validUntil)||menu.custody.responseReceived().observedAt().isAfter(now)||menu.custody.responseReceived().observedAt().isAfter(menu.validUntil)
                ||menu.custody.writeEntered().observedAt().isBefore(helloObservedAt))throw new IOException("menu occurrence escaped its original query/HELLO chronology");
        verifyHeld(menu.validUntil);
        if(!menu.custody.session().equals(session())||!menu.custody.custodyEpoch().equals(custodyEpoch)
                ||!originalRequestChronology(menu.original.requestId()).filter(menu.custody::equals).isPresent())throw new IOException("menu occurrence crossed its original Game/session/custody");
        menu.custody.verify(menu.original);var decoded=FrontendMenuFrameV1PublicCodec.decodeOutcome(menu.original);
        if(!decoded.equals(menu.frame)||decoded.action()!=FrontendMenuFrameV1.Action.QUERY_MENU||decoded.status()!=FrontendMenuFrameV1.Status.AVAILABLE
                ||!FrontendMenuFrameV1PublicCodec.decodeRequestPacket(menu.original.outbound().orElseThrow().originalPacket()).equals(menu.request))throw new IOException("menu occurrence or original request source drift");
        var raw=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
        if(!FrontendMenuFrameV1.BUILD.matches(NativeWire.text(raw.get("expected_ck3_version")),hello.gameSha256())||!hello.adapterId().equals(FrontendMenuFrameV1.BUILD.coreFrameAdapterId()))throw new IOException("menu occurrence belongs to another exact HELLO source");
    }

    /**
     * One fixed read-only bootstrap query. A successful packet still requires the Root frontend
     * source verifier and route decoder before it can become a FrontendIdentity.
     */
    @Override public synchronized DispatchOutcome readFrontendRoute(Instant deadline) throws InterruptedException {
        String id = "frontend-route-" + UUID.randomUUID().toString().replace("-", "");
        try {
            awaitHello(deadline); verifyEndpoint();
            ObjectNode original = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(), 4, hello.packet().value().length)));
            if (!hello.capabilities().contains("game.command.query-frontend-gui-route-v1")
                    || !hello.adapterId().equals("ck3-1.20.0.4-msvc-x64")
                    || !hello.gameSha256().equalsIgnoreCase("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                    || !NativeWire.text(original.get("expected_ck3_version")).equals("1.20.0.4"))
                throw new IOException("frontend route bootstrap requires exact .4 hello and the original advertised read capability");
            if (sentRequestIds.size() >= maximumSubmissions) throw new IOException("Native request identity retention limit reached");
            return retainReadOutcome(dispatchRead(id, NativeWire.execute(id, "query-frontend-gui-route-v1", BigInteger.ZERO,
                    new byte[] {'{', '}'}), deadline, () -> { }));
        } catch (IOException | RuntimeException failure) { return retainReadOutcome(zero(id, reason(failure))); }
    }
    /**
     * Fixed ordinary Robert menu operations on this already owned Game and pipe.
     * An ACK is transport evidence only; callers must decode fresh route/model/map observations.
     * A mutation retains its original request at write entry and is never dispatched twice.
     */
    public synchronized DispatchOutcome frontendBootstrap(Primitive step, Instant deadline)
            throws IOException, InterruptedException {
        Objects.requireNonNull(step); Objects.requireNonNull(deadline);
        boolean mutation = switch (step) {
            case ROUTE, BOOKMARK_MODEL -> false;
            case NEW_GAME, SELECT_1066_BOOKMARK, SELECT_1066, START_BOOKMARK -> true;
            default -> throw new IllegalArgumentException("not an ordinary Robert frontend bootstrap operation");
        };
        FrontendBootstrapAttempt prior = frontendBootstrapAttempts.get(step);
        if (mutation && prior != null) {
            DispatchOutcome original = prior.outcome().orElseGet(() -> unfinishedFrontendBootstrap(prior));
            if (original instanceof Unknown && originalOutboundPacket(prior.requestId()).isPresent()) {
                try {
                    Optional<AckReceived> collected = collectOriginalOutcome(prior.requestId(), deadline);
                    if (collected.isPresent()) original = collected.orElseThrow();
                } catch (IOException failure) {
                    original = frontendBootstrapFailure(prior, failure);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    original = frontendBootstrapFailure(prior, interrupted);
                }
            }
            frontendBootstrapAttempts.put(step, new FrontendBootstrapAttempt(
                    prior.requestId(), prior.packet(), Optional.of(original)));
            return original;
        }
        awaitHello(deadline); verifyEndpoint();
        if (!hello.capabilities().contains(step.capability()))
            throw new IOException("actual Native HELLO lacks frontend operation: " + step.capability());
        if (sentRequestIds.size() >= maximumSubmissions)
            throw new IOException("Native request identity retention limit reached");
        NativeRequest request = step.emptyRequest();
        String id = "frontend-bootstrap-" + UUID.randomUUID().toString().replace("-", "");
        FrontendBootstrapAttempt attempt = new FrontendBootstrapAttempt(id,
                new NativeWire.Bytes(NativeWire.execute(id, request.step(), BigInteger.ZERO,
                        request.additionalFields().bytes())), Optional.empty());
        final DispatchOutcome result;
        try {
            result = Objects.requireNonNull(dispatch(id, attempt.packet().value(), deadline, () -> {
                if (mutation) frontendBootstrapAttempts.put(step, attempt);
            }), "original frontend dispatch returned no terminal");
        } catch (InterruptedException interrupted) {
            if (!sentRequestIds.contains(id)) throw interrupted;
            Thread.currentThread().interrupt();
            DispatchOutcome unknown = frontendBootstrapFailure(attempt, interrupted);
            if (mutation) frontendBootstrapAttempts.put(step, new FrontendBootstrapAttempt(
                    id, attempt.packet(), Optional.of(unknown)));
            return mutation ? unknown : retainReadOutcome(unknown);
        } catch (RuntimeException failure) {
            if (!sentRequestIds.contains(id)) throw failure;
            DispatchOutcome unknown = frontendBootstrapFailure(attempt, failure);
            if (mutation) frontendBootstrapAttempts.put(step, new FrontendBootstrapAttempt(
                    id, attempt.packet(), Optional.of(unknown)));
            return mutation ? unknown : retainReadOutcome(unknown);
        }
        if (mutation && frontendBootstrapAttempts.containsKey(step))
            frontendBootstrapAttempts.put(step, new FrontendBootstrapAttempt(id, attempt.packet(), Optional.of(result)));
        return mutation ? result : retainReadOutcome(result);
    }
    private DispatchOutcome unfinishedFrontendBootstrap(FrontendBootstrapAttempt original) {
        if (!sentRequestIds.contains(original.requestId()))
            return zero(original.requestId(), "original frontend attempt ended before native write entry; no automatic retry");
        return new Unknown(original.requestId(), "original frontend write entered without a retained terminal; collect only, never replay",
                original.packet().value(), Optional.empty());
    }
    private DispatchOutcome frontendBootstrapFailure(FrontendBootstrapAttempt original, Exception failure) {
        WrittenRequest written = writtenRequests.get(original.requestId());
        NativeActionPort.FailureStage stage = written != null && written.completed().isPresent()
                ? NativeActionPort.FailureStage.RESPONSE_WAIT : NativeActionPort.FailureStage.WRITE;
        return new Unknown(original.requestId(), "original frontend request remains UNKNOWN; never replay: " + reason(failure),
                original.packet().value(), Optional.empty(), Optional.of(dispatchFailure(failure, stage,
                        failure instanceof InterruptedException ? NativeActionPort.FailureKind.INTERRUPTED
                                : failure instanceof IOException ? NativeActionPort.FailureKind.IO_FAILURE
                                : NativeActionPort.FailureKind.RUNTIME_FAILURE)));
    }
    public synchronized ObservedFrame observe(Instant deadline, java.time.Duration maximumAge) throws InterruptedException {
        Objects.requireNonNull(maximumAge, "maximumAge");
        if (maximumAge.isNegative() || maximumAge.isZero()) throw new IllegalArgumentException("maximumAge must be positive");
        if (!heldSnapshotInvalidated) {
            ObservedFrame actual;
            var retained = acceptedSnapshotFrame;
            if (retained == null || snapshotUndelivered) actual = observe(deadline);
            else {
                try {
                    open(deadline);
                    awaitHello(readDeadline(deadline));
                    actual = retained;
                } catch (IOException failure) {
                    throw new UncheckedIOException("Native observation unavailable; no Python fallback: " + observationFailure(failure), failure);
                }
            }
            if (actual.observedAt().plus(maximumAge).isAfter(Instant.now())) return actual;
        }
        var fresh = readFreshFullState(deadline);
        if (fresh instanceof NativeFreshSnapshotPort.Received) return ((NativeFreshSnapshotPort.Received) fresh).originalFrame();
        throw new UncheckedIOException(new IOException("actual stale snapshot refresh unavailable: " + fresh));
    }

    /** Only frames actually received in this held session can become observations. */
    @Override public synchronized ObservedFrame observe(Instant deadline) throws InterruptedException {
        if(armyIdentity126Source!=null)throw new UncheckedIOException(new IOException("identity126 is an explicit readonly result, not an ordinary Driver/action observation"));
        try {
            open(deadline);
            Instant effectiveDeadline = readDeadline(deadline);
            awaitHello(effectiveDeadline);
            if (!hello.capabilities().contains("game.state.snapshot")) throw new IOException("Native DLL did not advertise game.state.snapshot");
            if (!snapshotUndelivered) {
                for (int frames = 0; frames < maximumFramesPerOperation && !snapshotUndelivered; frames++) read(effectiveDeadline);
            }
            if (!snapshotUndelivered || snapshot == null) throw new IOException("Native state snapshot frame budget exhausted");
            verifyEndpoint(); snapshotUndelivered = false;
            return Objects.requireNonNull(acceptedSnapshotFrame,"actual accepted snapshot occurrence unavailable");
        } catch (IOException failure) { throw new UncheckedIOException("Native observation unavailable; no Python fallback: " + observationFailure(failure), failure); }
    }

    @Override public synchronized ObservedFrame currentSnapshot(Instant captureUntil) throws IOException {
        open(captureUntil); verifyEndpoint();
        if (java.time.Duration.between(Instant.now(), captureUntil).compareTo(java.time.Duration.ofDays(1)) > 0)
            throw new IOException("bounded original snapshot capture deadline required");
        ObservedFrame actual = latestObservedSnapshot().orElseThrow(
                () -> new IOException("actual held accepted original snapshot unavailable"));
        verifyEndpoint(); open(captureUntil);
        return actual;
    }
    @Override public synchronized NativeSnapshotWaitPort.WaitResult waitForSnapshot(Instant waitUntil, Instant captureUntil)
            throws IOException, InterruptedException {
        Objects.requireNonNull(waitUntil); Objects.requireNonNull(captureUntil);
        if (!waitUntil.isBefore(captureUntil)) throw new IOException("snapshot wait deadline must precede its original capture deadline");
        Instant actualNow = Instant.now();
        if (waitUntil.isBefore(actualNow.minus(java.time.Duration.ofDays(1)))
                || java.time.Duration.between(actualNow, captureUntil).compareTo(java.time.Duration.ofDays(1)) > 0)
            throw new IOException("bounded original snapshot wait and capture deadlines required");
        open(captureUntil); verifyEndpoint();
        if (hello == null) throw new IOException("typed snapshot WAIT requires the actual held HELLO; it cannot connect or adopt");
        if (snapshotUndelivered && snapshot != null) {
            snapshotUndelivered = false;
            return new NativeSnapshotWaitPort.Received(latestObservedSnapshot().orElseThrow());
        }
        for (int frames = 0; frames < maximumFramesPerOperation; frames++) {
            NativePacketPort.WaitResult result;
            try { result = endpoint.readPacketUntil(waitUntil, captureUntil); }
            catch (NativePipeEndpoint.TransferFailure failure) {
                retainActualDisconnection(failure);
                byte[] partial = failure.retainedBytes();
                if (partial.length > 0) {
                    lastOriginalPacket = partial;
                    terminalFailure = "typed snapshot WAIT failed with a partial original Native packet";
                }
                throw failure;
            }
            catch (NativePacketPort.ReadInterrupted interrupted) {
                byte[] partial = interrupted.originalPartialPacket();
                if (partial.length > 0) {
                    lastOriginalPacket = partial;
                    terminalFailure = "typed snapshot WAIT interrupted with a partial original Native packet";
                }
                throw interrupted;
            }
            catch (IOException failure) {retainActualDisconnection(failure);throw failure;}
            if (result == null) throw new IOException("actual Native provider returned no typed snapshot wait result");
            if (result instanceof NativePacketPort.Elapsed elapsed) {
                if (!elapsed.waitUntil().equals(waitUntil)) throw new IOException("typed packet deadline differs from this original wait");
                open(captureUntil); verifyEndpoint();
                ObservedFrame retained = latestObservedSnapshot().orElseThrow(
                        () -> new IOException("wait elapsed without any actual accepted original snapshot"));
                return new NativeSnapshotWaitPort.Elapsed(retained);
            }
            ingestOriginalPacket(((NativePacketPort.Packet) result).originalPacket());
            open(captureUntil); verifyEndpoint();
            if (snapshotUndelivered && snapshot != null) {
                snapshotUndelivered = false;
                return new NativeSnapshotWaitPort.Received(latestObservedSnapshot().orElseThrow());
            }
        }
        throw new IOException("typed snapshot WAIT packet budget exhausted without an accepted original or zero-prefix deadline");
    }
    // The new prepared role never reuses legacy SubmissionPermit/CommandOrigin admission.
    private final Set<String> preparedCleanupObservedNonces=new HashSet<>();
    private final Set<String> preparedCleanupWriteNonces=new HashSet<>();
    private PreparedCleanupLateCapture preparedCleanupLateCapture;
    private record PreparedCleanupLateCapture(PreparedCleanupObservationPermit observation,
            PreparedCleanupEvidence.LateBinding binding) { }
    private record PreparedCleanupDispatch(DispatchOutcome original,Optional<Throwable> originalFailure) { }

    @Override public synchronized PreparedCleanupEvidence.LateBinding observePreparedCleanupLate(
            PreparedCleanupObservationPermit permit)throws IOException,InterruptedException {
        Objects.requireNonNull(permit);var originals=new ArrayList<DispatchOutcome>();
        try {
            if(permit.consumed()||preparedCleanupObservedNonces.contains(permit.preparation().preparationNonce()))
                throw new IOException("prepared cleanup observation already attempted; retain original DATA without replay");
            if(preparedCleanupLateCapture!=null)throw new IOException("another original prepared late binding is still held");
            requirePreparedCleanupCapacity(permit.preparation());open(permit.deadline());awaitHello(permit.deadline());verifyEndpoint();
            var permission=preparedCleanupPermission(permit.preparation().command().operation());
            permission.verifyPreparedObservation(config,hello,permit);
            latestReadEvidence=null;
            requirePreparedCleanupCapacity(permit.preparation());requirePreparedCleanupHello();requireLivingPausedMap();
            Instant readUntil=preparedCleanupReadDeadline(permit.deadline());
            String nonce=permit.preparation().preparationNonce();
            var status=preparedCleanupStatus("prepared-status-"+nonce+"-late",readUntil,originals,()->{
                permit.consumeOnce();if(!preparedCleanupObservedNonces.add(nonce))throw new IllegalStateException("prepared observation nonce already used");
            });
            var fresh=preparedCleanupFresh("prepared-fresh-"+nonce+"-late",readUntil,originals);
            NativeFreshSnapshotPort.verifyAfterOriginal(status.acknowledgement(),fresh.acknowledgement(),fresh.originalFrame(),fresh.snapshotReceived());
            Instant now=chronologyClock.instant();
            Instant expiry=preparedCleanupMin(permit.deadline(),preparedCleanupMin(
                    status.acknowledgement().custody().orElseThrow().responseReceived().observedAt().plus(Duration.ofMinutes(2)),
                    fresh.originalFrame().observedAt().plus(Duration.ofMinutes(2))));
            var binding=PreparedCleanupEvidence.bindLate(permit.preparation(),status,fresh.acknowledgement(),fresh.originalFrame(),
                    fresh.snapshotReceived(),now,expiry,now);
            requirePreparedCleanupActualFrame(binding,now);
            preparedCleanupLateCapture=new PreparedCleanupLateCapture(permit,binding);return binding;
        } catch(Throwable failure) {
            if(failure instanceof InterruptedException)Thread.currentThread().interrupt();
            throw new NativeActionPort.PreparedCleanupObservationFailure("prepared cleanup late observation failed; no world submission from this entry",originals,failure);
        }
    }
    private NativePrivateActionPermission preparedCleanupPermission(org.xar.ck3.control.application.action.OperationKey operation)throws IOException {
        return privateActions.stream().filter(value->value.operation().equals(operation)).findFirst()
                .orElseThrow(()->new IOException("prepared cleanup has no actual installed Root qualification"));
    }
    private void preparedCleanupCapacity(int remaining)throws IOException {
        if(pendingFreshSnapshot!=null)throw new IOException("original fresh READ is unresolved; collect its same ID instead of preparing cleanup");
        if(activeMailbox!=null||activeCouncilRecovery!=null||activeRecoveredSeatMailbox!=null||mailboxPoison!=null)
            throw new IOException("prepared cleanup cannot cross another actual Native producer scope");
        if(remaining<1||maximumSubmissions-sentRequestIds.size()<remaining)
            throw new IOException("prepared cleanup lacks its complete fixed READ/write identity budget");
        if(preparedCleanupObservedNonces.size()>=maximumSubmissions||preparedCleanupWriteNonces.size()>=maximumSubmissions)
            throw new IOException("prepared cleanup nonce retention bound exhausted");
    }
    private void requirePreparedCleanupHello()throws IOException {
        if(hello==null||snapshot==null||acceptedSnapshotFrame==null)throw new IOException("prepared cleanup needs the original HELLO and accepted raw snapshot");
        if(!hello.capabilities().containsAll(Set.of(ClockStatusRead.STATUS_CAP,ClockStatusRead.CANCEL_CAP,
                NativeFreshSnapshotPort.CAPABILITY,"game.state.snapshot")))throw new IOException("prepared cleanup original HELLO lacks required fixed capabilities");
        var original=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
        String version=NativeWire.text(original.get("expected_ck3_version"));
        if(!PreparedCleanupEvidence.supportsCancellationHello(
                hello.adapterId(),version,hello.gameSha256()))
            throw new IOException("prepared cleanup lacks an exact qualified full-state READ profile");
    }
    private Instant preparedCleanupReadDeadline(Instant upper) {
        return preparedCleanupMin(upper,preparedCleanupMin(readDeadline(upper),chronologyClock.instant().plus(Duration.ofMinutes(2))));
    }
    private static Instant preparedCleanupMin(Instant a,Instant b){return a.isBefore(b)?a:b;}

    @Override public synchronized void requirePreparedCleanupCapacity(PreparedCleanupEvidence.Prepared prepared)throws IOException {
        Objects.requireNonNull(prepared);preparedCleanupCapacity(6);
        if(preparedCleanupLateCapture!=null)throw new IOException("an original prepared late binding is already held");
        if(!lateResults.isEmpty()||retainedResultBytes!=0)throw new IOException("prepared cleanup requires original outstanding ACK custody to be consumed first");
        requirePreparedCleanupBytes(prepared,6);
    }
    private void requirePreparedCleanupBytes(PreparedCleanupEvidence.Prepared prepared,int remaining)throws IOException {
        String nonce=prepared.preparationNonce();long bytes=0;
        if(remaining==6) {
            bytes+=NativeWire.execute("prepared-status-"+nonce+"-late",ClockStatusRead.STEP,NativeWire.UINT64_MAX,new byte[]{'{','}'}).length;
            bytes+=NativeWire.execute("prepared-fresh-"+nonce+"-late",NativeFreshSnapshotPort.STEP,BigInteger.ZERO,new byte[]{'{','}'}).length;
        } else if(remaining!=4)throw new IOException("prepared cleanup fixed capacity role differs");
        bytes+=NativeWire.execute(prepared.nativeRequestId(),prepared.nativePrepared().step(),NativeWire.UINT64_MAX,prepared.nativePrepared().additionalFields().bytes()).length;
        for(String suffix:List.of("idle1","idle2"))bytes+=NativeWire.execute("prepared-status-"+nonce+"-"+suffix,ClockStatusRead.STEP,NativeWire.UINT64_MAX,new byte[]{'{','}'}).length;
        bytes+=NativeWire.execute("prepared-fresh-"+nonce+"-post",NativeFreshSnapshotPort.STEP,BigInteger.ZERO,new byte[]{'{','}'}).length;
        if(retainedOutboundBytes+bytes>NativeWire.MAXIMUM_FRAME_BYTES+4L)throw new IOException("prepared cleanup full fixed request chain exceeds the retained original outbound budget");
    }
    private PreparedCleanupEvidence.StatusSample preparedCleanupStatus(String id,Instant deadline,List<DispatchOutcome> originals,Runnable consume)throws IOException,InterruptedException {
        open(deadline);verifyEndpoint();requirePreparedCleanupHello();
        if(sentRequestIds.contains(id)||sentRequestIds.size()>=maximumSubmissions)throw new IOException("original prepared Status identity already attempted or exhausted");
        var original=dispatchPreparedCleanup(id,NativeWire.execute(id,ClockStatusRead.STEP,snapshot.revision(),new byte[]{'{','}'}),deadline,consume,null);
        originals.add(original.original());
        if(original.originalFailure().isPresent())throw preparedCleanupReadFailure("original prepared Status transfer failed",original.originalFailure().orElseThrow());
        if(!(original.original() instanceof AckReceived ack)||!ack.nativeOk())throw new IOException("original prepared Status has no successful native ACK; raw outcome retained");
        return new PreparedCleanupEvidence.StatusSample(ack,deadline);
    }
    private NativeFreshSnapshotPort.Received preparedCleanupFresh(String id,Instant deadline,List<DispatchOutcome> originals)throws IOException,InterruptedException {
        if(pendingFreshSnapshot!=null)throw new IOException("original fresh READ unresolved; no second prepared fresh read");
        open(deadline);verifyEndpoint();requirePreparedCleanupHello();
        if(sentRequestIds.contains(id)||sentRequestIds.size()>=maximumSubmissions)throw new IOException("original prepared fresh identity already attempted or exhausted");
        var capture=new FreshSnapshotCapture(id);pendingFreshSnapshot=capture;
        var dispatch=dispatchPreparedCleanup(id,NativeWire.execute(id,NativeFreshSnapshotPort.STEP,BigInteger.ZERO,new byte[]{'{','}'}),deadline,()->{},null);
        originals.add(dispatch.original());capture.outcome=dispatch.original();
        if(dispatch.original() instanceof RejectedBeforeDispatch||dispatch.original() instanceof AckReceived negative&&!negative.nativeOk())pendingFreshSnapshot=null;
        if(dispatch.originalFailure().isPresent())throw preparedCleanupReadFailure("original prepared fresh transfer failed",dispatch.originalFailure().orElseThrow());
        if(!(dispatch.original() instanceof AckReceived ack)||!ack.nativeOk())throw new IOException("original prepared fresh READ has no successful native ACK; collect its same ID only");
        if(capture.invalid!=null)throw new IOException("prepared fresh state rejected: "+capture.invalid);
        if(capture.frame==null||capture.received==null)throw new IOException("prepared fresh ACK has no matching independently received original state");
        var result=new NativeFreshSnapshotPort.Received(ack,capture.frame,capture.received);
        pendingFreshSnapshot=null;heldSnapshotInvalidated=false;return result;
    }
    private static IOException preparedCleanupReadFailure(String message,Throwable original) {
        if(original instanceof InterruptedException)Thread.currentThread().interrupt();return new IOException(message,original);
    }

    @Override public synchronized PreparedCleanupNativeOutcome submitPreparedCleanup(PreparedCleanupPermit permit,NativeRequest request,Instant deadline)throws InterruptedException {
        Objects.requireNonNull(permit);Objects.requireNonNull(request);Objects.requireNonNull(deadline);
        String id=permit.requestId();var observations=new ArrayList<DispatchOutcome>();DispatchOutcome original=null;boolean dispatchEntered=false;
        try {
            if(permit.consumed()||preparedCleanupWriteNonces.contains(permit.nonce())||sentRequestIds.contains(id))
                throw new PreparedCleanupPriorAttempt("prepared cleanup nonce/request already attempted; same-ID collection only");
            var held=preparedCleanupLateCapture;
            if(held==null||held.binding()!=permit.binding()||held.observation().preparationSequence()!=permit.preparationSequence()
                    ||!held.observation().preparation().reference().equals(permit.preparation().reference()))
                throw new IOException("prepared cleanup permit lacks this SDK's actual one-shot late binding");
            preparedCleanupCapacity(4);requirePreparedCleanupBytes(permit.preparation(),4);
            open(deadline);verifyEndpoint();requirePreparedCleanupHello();
            if(!request.equals(permit.preparedRequest()))throw new IOException("prepared cleanup request changed its durable preparation");
            NativeStepDiscriminator.requireRequest(permit.command().operation(),Kind.ACTION,request);
            var permission=preparedCleanupPermission(permit.command().operation());permission.verifyPreparedWrite(config,hello,permit,request);
            // All actual Root callbacks have now ended; recheck mutable endpoint/snapshot facts and finite local budgets.
            preparedCleanupCapacity(4);requirePreparedCleanupBytes(permit.preparation(),4);verifyEndpoint();
            permit.requireFresh();requirePreparedCleanupActualChild(permit);requirePreparedCleanupActualFrame(permit.binding(),chronologyClock.instant());
            Instant actualDeadline=preparedCleanupMin(deadline,permit.writeDeadline());
            byte[] packet=NativeWire.execute(id,request.step(),permit.actualExpectedRevision(),request.additionalFields().bytes());
            if(!preparedCleanupWriteNonces.add(permit.nonce()))throw new PreparedCleanupPriorAttempt("prepared cleanup nonce already entered its one attempt");
            dispatchEntered=true;
            var write=dispatchPreparedCleanup(id,packet,actualDeadline,permit::consumeOnce,permit);
            original=write.original();
            if(write.originalFailure().isPresent())return preparedCleanupFailure(permit,original,observations,write.originalFailure().orElseThrow());
            if(!(original instanceof AckReceived ack)||!ack.nativeOk())
                return preparedCleanupFailure(permit,original,observations,new IOException("prepared cleanup has no positive cancellation ACK; original outcome retained"));
            PreparedCleanupEvidence.acknowledgedCancellation(
                    permit.command().source().exactBuild(),ack,request.step());
            Instant captureDeadline=preparedCleanupMin(deadline,ack.custody().orElseThrow().responseReceived().observedAt().plus(Duration.ofMinutes(2)));
            var idle1=preparedCleanupStatus("prepared-status-"+permit.nonce()+"-idle1",preparedCleanupReadDeadline(captureDeadline),observations,()->{});
            var idle2=preparedCleanupStatus("prepared-status-"+permit.nonce()+"-idle2",preparedCleanupReadDeadline(captureDeadline),observations,()->{});
            var fresh=preparedCleanupFresh("prepared-fresh-"+permit.nonce()+"-post",preparedCleanupReadDeadline(captureDeadline),observations);
            NativeFreshSnapshotPort.verifyAfterOriginal(idle2.acknowledgement(),fresh.acknowledgement(),fresh.originalFrame(),fresh.snapshotReceived());
            var captured=new PreparedCleanupEvidence.PostAckCaptured(permit.binding(),ack,idle1,idle2,fresh.acknowledgement(),fresh.originalFrame(),fresh.snapshotReceived(),captureDeadline);
            PreparedCleanupEvidence.requirePostAckCaptured(captured);
            return new PreparedCleanupNativeOutcome(permit.nonce(),original,Optional.of(captured),Optional.empty(),Optional.empty());
        } catch(Throwable failure) {
            if(failure instanceof InterruptedException)Thread.currentThread().interrupt();
            if(original==null)original=failure instanceof PreparedCleanupPriorAttempt||dispatchEntered
                    ?new Unknown(id,preparedCleanupReason(failure),retainedOutbound(id),Optional.empty(),Optional.of(dispatchFailure(failure,NativeActionPort.FailureStage.WRITE,NativeActionPort.FailureKind.RUNTIME_FAILURE)))
                    :zero(id,preparedCleanupReason(failure));
            return preparedCleanupFailure(permit,original,observations,failure);
        } finally {preparedCleanupLateCapture=null;}
    }
    private static final class PreparedCleanupPriorAttempt extends IOException {
        private static final long serialVersionUID=1L;
        private PreparedCleanupPriorAttempt(String message){super(message);}
    }

    /** Only current in-memory SDK facts; no clock, endpoint, source, archive or writer callback here. */
    private void requirePreparedCleanupActualFrame(PreparedCleanupEvidence.LateBinding binding,Instant actualNow)throws IOException {
        if(actualNow.isBefore(binding.boundAt())||!actualNow.isBefore(binding.writeDeadline())||!actualNow.isBefore(binding.prepared().deadline()))
            throw new IOException("prepared cleanup actual late freshness/operation deadline expired or regressed");
        Instant expiry=preparedCleanupMin(binding.prepared().deadline(),preparedCleanupMin(
                binding.status().acknowledgement().custody().orElseThrow().responseReceived().observedAt().plus(Duration.ofMinutes(2)),
                binding.writeFrame().observedAt().plus(Duration.ofMinutes(2))));
        if(!binding.writeDeadline().equals(expiry))throw new IOException("prepared cleanup actual expiry tuple changed");
        if(closed||terminalFailure!=null||!stateConnected||hello==null||snapshot==null||acceptedSnapshotFrame==null||heldSnapshotInvalidated)
            throw new IOException("prepared cleanup current actual endpoint/snapshot is unavailable or invalidated");
        var expected=binding.writeFrame();
        if(!session().equals(expected.session())||!custodyEpoch.equals(binding.freshSnapshotAck().custody().orElseThrow().custodyEpoch())
                ||!snapshot.snapshotId().equals(expected.snapshotId())||!snapshot.revision().equals(expected.nativeRevision())
                ||!snapshotObservedAt.equals(expected.observedAt())||!Arrays.equals(snapshot.packet().value(),expected.originalPacket())
                ||!Arrays.equals(acceptedSnapshotFrame.originalPacket(),expected.originalPacket()))
            throw new IOException("prepared cleanup late frame is not this endpoint's actual unchanged accepted packet");
        if(originalRequestChronology(binding.status().acknowledgement().requestId()).filter(binding.status().acknowledgement().custody().orElseThrow()::equals).isEmpty()
                ||originalRequestChronology(binding.freshSnapshotAck().requestId()).filter(binding.freshSnapshotAck().custody().orElseThrow()::equals).isEmpty())
            throw new IOException("prepared cleanup late READ custody was not received by this actual SDK");
    }
    private PreparedCleanupNativeOutcome preparedCleanupFailure(PreparedCleanupPermit permit,DispatchOutcome original,
            List<DispatchOutcome> observations,Throwable failure) {
        if(failure instanceof InterruptedException)Thread.currentThread().interrupt();
        Optional<PreparedCleanupEvidence.FailureData> data=Optional.empty();
        try {data=Optional.of(new PreparedCleanupEvidence.FailureData(permit.preparation(),Optional.of(permit.binding()),original,
                observations,chronologyClock.instant(),List.of()));}
        catch(Throwable metadataFailure){if(metadataFailure!=failure)failure.addSuppressed(metadataFailure);}
        return new PreparedCleanupNativeOutcome(permit.nonce(),original,Optional.empty(),data,Optional.of(failure));
    }
    private static Set<String> preparedCleanupKeys(ObjectNode value) {var keys=new HashSet<String>();value.fieldNames().forEachRemaining(keys::add);return keys;}
    private static String preparedCleanupReason(Throwable failure) {return failure.getClass().getName()+": "+Objects.toString(failure.getMessage(),"unavailable");}

    /** Dedicated new-role transfer preserves the entire original Throwable. Legacy dispatchOriginal stays byte-for-byte unchanged. */
    private PreparedCleanupDispatch dispatchPreparedCleanup(String id,byte[] packet,Instant deadline,Runnable consume,
            PreparedCleanupPermit control)throws InterruptedException {
        boolean enteredWrite=false,writeReturned=false;
        try {
            var payload=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet,4,packet.length)));
            requireDispatchScope(NativeWire.text(payload.get("step")),false,id);
            if(originalOutboundPackets.containsKey(id)||retainedOutboundBytes+packet.length>NativeWire.MAXIMUM_FRAME_BYTES+4L)
                throw new IOException("prepared original outbound is duplicate or its unchanged byte budget is exhausted");
            verifyEndpoint();open(deadline);
            NativeRequestChronology.PacketIdentity originalRequest=packetIdentity(packet);
            consume.run();
            // The actual chronology clock is the last callback. All following checks are pure until endpoint.writePacket.
            NativeRequestChronology.Event entered=chronologyEvent();
            if(!entered.observedAt().isBefore(deadline))throw new IOException("prepared actual write deadline expired after final callbacks");
            if(control!=null){requirePreparedCleanupActualChild(control);requirePreparedCleanupActualFrame(control.binding(),entered.observedAt());}
            sentRequestIds.add(id);originalOutboundPackets.put(id,new NativeWire.Bytes(packet));retainedOutboundBytes+=packet.length;
            writtenRequests.put(id,new WrittenRequest(session(),originalRequest,entered,Optional.empty()));
            if(control!=null){latestReadEvidence=null;heldSnapshotInvalidated=true;}
            enteredWrite=true;endpoint.writePacket(packet,deadline);writeReturned=true;
            NativeRequestChronology.Event completed=chronologyEvent();writtenRequests.put(id,new WrittenRequest(session(),originalRequest,entered,Optional.of(completed)));
            for(int count=0;count<maximumFramesPerOperation;count++) {
                var frame=read(deadline);
                if(frame.isPresent()&&frame.orElseThrow() instanceof NativeWire.CommandResult result&&result.requestId().equals(id)) {
                    var ack=new AckReceived(id,result.nativeOk(),result.result().token().map(value->new RawJson(value.value())),new RawJson(result.payload().value()),
                            result.packet().value(),Optional.of(new NativeActionPort.OutboundPacket(id,packet)),originalRequestChronology(id));
                    removeRetained(result);return new PreparedCleanupDispatch(ack,Optional.empty());
                }
            }
            var failure=new IOException("prepared original command_result frame budget exhausted; same-ID collection only");
            return new PreparedCleanupDispatch(new Unknown(id,failure.getMessage(),packet,Optional.empty(),Optional.of(new NativeActionPort.FailureCause(
                    NativeActionPort.FailureKind.FRAME_BUDGET_EXHAUSTED,NativeActionPort.FailureStage.RESPONSE_WAIT,
                    Optional.empty(),Optional.empty(),Optional.empty()))),Optional.of(failure));
        } catch(NativePipeEndpoint.TransferFailure failure) {
            preparedCleanupRetainDisconnection(failure);
            if(!enteredWrite)return new PreparedCleanupDispatch(zero(id,preparedCleanupReason(failure)),Optional.of(failure));
            if(enteredWrite&&!writeReturned&&!failure.writeAttempted()&&failure.writtenBytes()==0&&Arrays.equals(failure.retainedBytes(),packet)) {
                NativeWire.Bytes removed=originalOutboundPackets.remove(id);if(removed!=null)retainedOutboundBytes-=removed.value().length;writtenRequests.remove(id);
                return new PreparedCleanupDispatch(zero(id,failure.getMessage()),Optional.of(failure));
            }
            return new PreparedCleanupDispatch(new Unknown(id,preparedCleanupReason(failure),packet,Optional.empty(),Optional.of(dispatchFailure(failure,
                    writeReturned?NativeActionPort.FailureStage.RESPONSE_WAIT:NativeActionPort.FailureStage.WRITE,NativeActionPort.FailureKind.TRANSFER_IO))),Optional.of(failure));
        } catch(Throwable failure) {
            preparedCleanupRetainDisconnection(failure);if(failure instanceof InterruptedException)Thread.currentThread().interrupt();
            DispatchOutcome result=enteredWrite?new Unknown(id,preparedCleanupReason(failure),packet,Optional.empty(),Optional.of(dispatchFailure(failure,
                    writeReturned?NativeActionPort.FailureStage.RESPONSE_WAIT:NativeActionPort.FailureStage.WRITE,
                    failure instanceof InterruptedException?NativeActionPort.FailureKind.INTERRUPTED:failure instanceof IOException?NativeActionPort.FailureKind.IO_FAILURE:NativeActionPort.FailureKind.RUNTIME_FAILURE)))
                    :zero(id,preparedCleanupReason(failure));
            return new PreparedCleanupDispatch(result,Optional.of(failure));
        }
    }

    private void requirePreparedCleanupActualChild(PreparedCleanupPermit permit)throws IOException {
        var actual=org.xar.ck3.control.application.action.ActionCommandScope.current().orElseThrow(()->new IOException("prepared cleanup write lacks the actual child command scope"));
        if(!actual.equals(permit.command()))
            throw new IOException("prepared cleanup write changed its current complete child command/body");
    }
    private void preparedCleanupRetainDisconnection(Throwable original) {
        try {retainActualDisconnection(original);}catch(Throwable diagnosticFailure){if(diagnosticFailure!=original)original.addSuppressed(diagnosticFailure);}
    }

    @Override public synchronized DispatchOutcome submit(SubmissionPermit permit, NativeRequest request, Instant deadline) throws InterruptedException {
        Objects.requireNonNull(permit); Objects.requireNonNull(request);
        String id = permit.requestId();
        try {
            requireWorldActionMode();
            if (permit.origin() instanceof CommandOrigin.Reconciliation || permit.origin() instanceof CommandOrigin.PhysicalStatusOnly)
                throw new IOException("read-only reconciliation or physical status origin can never submit a world primitive");
            if (permit.consumed() || sentRequestIds.contains(id)) {
                return recordMailboxOutcome(new Unknown(id, "original permit/request was already attempted; reconcile the actual retained original without replay", retainedOutbound(id), Optional.empty()));
            }
            open(deadline); verifyEndpoint();
            if (hello == null) throw new IOException("actual Native hello is required before dispatch");
            if (!request.equals(permit.preparedRequest())) throw new IOException("primitive differs from the coordinator's durable prepared request");
            boolean fullClock=fullClockPrepared(request);
            if(hotfixSave(request))requireMappedSave61();
            if(current112Save(request))requireMappedSave112();
            boolean dateArm=request.additionalFields().objectFieldNames().contains("date_sentinel_arm");
            // A current executable with legacy empty fields cannot escape the actual Full source gate.
            // SHA selects only this rejection/check branch, never a profile or dispatch permission.
            boolean currentClockSource=false;
            if(ExactCk3Build.CK3_121003_STEAM_26785313.executableSha256().equalsIgnoreCase(hello.gameSha256())) {
                var requestedOperation=new org.xar.ck3.control.application.action.OperationKey(request.step());
                currentClockSource=FullSnapshotClockControl.supports(requestedOperation)||AdvancePrimitives.supports(requestedOperation);
            }
            final boolean requiresClockSource=fullClock||dateArm||currentClockSource;
            if(requiresClockSource){
                requireFlorinFullClockSource();
                if(unresolvedFullClockControl!=null||unresolvedCoreControl!=null)
                    throw new IOException("an original clock outcome is unresolved; reconcile it without a new write");
            }
            NativeStepDiscriminator.requireRequest(permit.guard().operation(), Kind.ACTION, request);
            if (permit.origin() instanceof CommandOrigin.LifecycleTerminal
                    && (!request.step().equals("continue-death-succession-modal-v1") || request.requiredCapability().isPresent()))
                throw new IOException("lifecycle terminal permits only the exact source-qualified private death-modal continuation");
            if (!config.sessionId().equals(permit.sessionId()) || !permit.guard().sessionId().equals(permit.sessionId())
                    || !hello.connectionGeneration().equals(permit.guard().connectionGeneration())) throw new IOException("coordinator permit belongs to a different held Native session");
            if (!Instant.now().isBefore(permit.guard().validUntil())) throw new IOException("coordinator's native guard expired before pipe write");
            if (!permit.origin().acceptsGuard(permit.guard().origin())) throw new IOException("submission origin differs from its actual guard");
            requireIdentity(permit.guard().origin());
            requireRawEvidence(permit.guard());
            requireCurrent112SpeedForPermit(permit,request,deadline);
            if (request.requiredCapability().isPresent()) {
                String requiredCapability = request.requiredCapability().orElseThrow();
                if (!hello.capabilities().contains(requiredCapability)) throw new IOException("original hello lacks required capability: " + requiredCapability);
            } else {
                NativePrivateActionPermission permission = privateActions.stream().filter(value -> value.operation().equals(permit.guard().operation())).findFirst()
                        .orElseThrow(() -> new IOException("private world primitive is not installed by the composition root"));
                permission.verify(config, hello, permit.guard(), request);
            }
            if (sentRequestIds.contains(id)) throw new IOException("original Native request id already attempted; replay forbidden");
            if (sentRequestIds.size() >= maximumSubmissions) throw new IOException("Native request identity retention limit reached");
            byte[] packet = NativeWire.execute(id, request.step(), permit.expectedRevision(), request.additionalFields().bytes());
            // Every check above is before the irreversible boundary. No application request is sent by observe/hello.
            latestReadEvidence = null;
            Instant actualDeadline = AdvancePrimitives.supports(permit.guard().operation()) ? readDeadline(deadline) : deadline;
            var activeCommand=org.xar.ck3.control.application.action.ActionCommandScope.current();
            if(activeCommand.isPresent()&&activeCommand.orElseThrow().actionId().equals(permit.actionId())
                    &&org.xar.ck3.control.application.action.ActionCodec.bodySha256(activeCommand.orElseThrow()).equals(permit.bodySha256())
                    &&org.xar.ck3.control.application.action.ActionChildPlanningScope.isPostResumePauseCancellationObservation(activeCommand.orElseThrow())
                    &&permit.guard().validUntil().isBefore(actualDeadline))
                actualDeadline=permit.guard().validUntil();
            // For this exact new cleanup only, the actual endpoint deadline stays inside both
            // freshness expiries even when the original beforeFirstWrite callbacks consume time.
            DispatchOutcome original = dispatch(id, packet, actualDeadline, () -> {
                if(requiresClockSource)requireBackgroundAtCoreWrite();
                if(hotfixSave(request))try{requireMappedSave61();}catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                if(current112Save(request))try{requireMappedSave112();}catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                try{requireCurrent112SpeedForPermit(permit,request,deadline);}catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
                permit.consumeOnce();
                heldSnapshotInvalidated = true;
            });
            if (COUNCIL_ASSIGN.equals(request.step()) && request.requiredCapability().isEmpty()
                    && original instanceof AckReceived ack && isCouncilPending(ack)) {
                // Actual canonical SUBMITTING permit and private source permission were checked above.
                activeMailbox.assignment = new CouncilAssignment(permit.actionId(), permit.bodySha256(), id, permit.guard(), request);
            }
            return dateArm?retainDateArmOutcome(original,request.step()):fullClock?retainFullClockOutcome(original,request):original;
        } catch (IOException | RuntimeException failure) { return zero(id, reason(failure)); }
    }
    /** Registered collector reads use this same endpoint and one exact request ID, without a world-action intent. */
    @Override public synchronized DispatchOutcome read(ReadPermit permit, NativeRequest request, Instant deadline) throws InterruptedException {
        Objects.requireNonNull(permit); Objects.requireNonNull(request); String id = permit.requestId();
        try {
            if (activeRecoveredSeatMailbox != null) activeRecoveredSeatMailbox.current();
            if (permit.consumed() || sentRequestIds.contains(id))
                return retainReadOutcome(recordMailboxOutcome(new Unknown(id, "original read request already attempted; allocate a new guarded read instead of replaying it", retainedOutbound(id), Optional.empty())));
            open(deadline); verifyEndpoint();
            if (hello == null) throw new IOException("actual Native hello required for a registered read");
            ReadContract<?> contract = permit.contract();
            if (!request.equals(permit.preparedRequest())
                    || !request.requiredCapability().equals(contract.requiredCapability())) throw new IOException("read request differs from its exact registered contract");
            NativeStepDiscriminator.requireRequest(contract.operation(), Kind.READ, request);
            if (!config.sessionId().equals(permit.sessionId()) || !permit.guard().sessionId().equals(permit.sessionId())
                    || !hello.connectionGeneration().equals(permit.guard().connectionGeneration())) throw new IOException("read permit belongs to another Native session");
            if (!Instant.now().isBefore(permit.guard().validUntil())) throw new IOException("planning read guard expired");
            if (!permit.origin().acceptsGuard(permit.guard().origin())) throw new IOException("read origin differs from its actual guard");
            requireIdentity(permit.guard().origin()); requireRawEvidence(permit.guard());
            ReadContract.GuardMode actualMode = switch (permit.origin()) {
                case CommandOrigin.Gameplay ignored -> ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP;
                case CommandOrigin.Frontend ignored -> ReadContract.GuardMode.FRONTEND_SESSION;
                case CommandOrigin.LifecycleTerminal ignored -> ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION;
                case CommandOrigin.Reconciliation ignored -> ReadContract.GuardMode.RECONCILIATION_OBSERVATION;
                case CommandOrigin.PhysicalStatusOnly ignored -> ReadContract.GuardMode.STATUS_ONLY;
            };
            if (actualMode != contract.guardMode() || permit.readGuard().guardMode() != contract.guardMode())
                throw new IOException("registered read crossed its origin guard mode");
            if (actualMode == ReadContract.GuardMode.STATUS_ONLY) {
                PhysicalStatusIdentity.requireProfile(contract);
                if (!request.step().equals(PhysicalStatusIdentity.OPERATION)
                        || !request.requiredCapability().equals(Optional.of(PhysicalStatusIdentity.CAPABILITY))
                        || !NativeWire.object(NativeWire.parse(request.additionalFields().bytes())).isEmpty())
                    throw new IOException("physical status permits only its fixed advertised native read with empty fields");
            }
            if (actualMode == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP) {
                requireLivingPausedMap();
                if (!permit.readGuard().paused() || !permit.readGuard().mapReady() || !permit.readGuard().playerAlive())
                    throw new IOException("read guard lacks a living paused map");
            }
            if (actualMode == ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                    && (contract.wireProfile() == ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS
                        || COUNCIL_MAILBOX_STEPS.contains(contract.operation().value())))
                throw new IOException("reconciliation observation cannot borrow any Council mailbox continuation or mutation");
            if (contract.advertisedRequired() && !hello.capabilities().contains(contract.requiredCapability().orElseThrow())) throw new IOException("actual hello lacks registered advertised read capability");
            // Private permission is granted only by the root-installed ReadContract/ReadPermit, never a query-name prefix.
            if (!contract.advertisedRequired() && (contract.permissionMode() != ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                    || contract.permissionKey().isEmpty() || contract.sourceRef().bytes() < 1)) throw new IOException("private read lacks a source-qualified registered permission");
            if (sentRequestIds.size() >= maximumSubmissions) throw new IOException("Native request identity retention limit reached");
            byte[] packet = switch (contract.wireProfile()) {
                case G2_PRIVATE_QUERY -> NativeWire.executePrivateQuery(id, request.step(), permit.expectedRevision(), request.additionalFields().bytes());
                case EXECUTE_STEP -> NativeWire.execute(id, request.step(), permit.expectedRevision(), request.additionalFields().bytes());
                case SNAPSHOT_REVISION_ONLY -> NativeWire.executeSnapshotRevisionOnly(id, request.step(), permit.expectedRevision(), request.additionalFields().bytes());
                case COUNCIL_MAILBOX_STATUS -> NativeWire.executeCouncilMailboxStatus(id, request.step(), request.additionalFields().bytes());
            };
            RecoveredSeatMailbox seat = activeRecoveredSeatMailbox;
            if (seat != null) seat.authorize(permit, request, deadline);
            try {
                if(activeMailbox!=null)activeMailbox.actualReads.put(id,permit);
                return retainReadOutcome(dispatchRead(id, packet, readDeadline(deadline), permit::consumeOnce));
            } finally { if (seat != null) seat.admitted = null; }
        } catch (IOException | RuntimeException failure) { return retainReadOutcome(zero(id, reason(failure))); }
    }
    /** One actual newly ISSUED read-only RPC; historical assignment/ACK data never become live write custody. */
    public synchronized DispatchOutcome continueRecoveredCouncil(CouncilContinuationPermit issued, NativeRequest prepared,
            Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(issued); Objects.requireNonNull(prepared); Objects.requireNonNull(deadline);
        if (activeCouncilRecovery != null || activeMailbox != null)
            throw new IOException("recovered Council RPC cannot nest or enter an ordinary mailbox");
        if (mailboxPoison != null) throw new IOException(mailboxPoison);
        open(deadline); verifyEndpoint();
        var original = issued.recoveryOriginal().orElseThrow(() -> new IOException("actual private recovered original is required"));
        original.requireCurrent();
        var command = original.command(); var attempt = original.attempt(); var ack = original.originalAck();
        if (!issued.originalActionId().equals(command.actionId())
                || !issued.originalBodySha256().equals(ActionCodec.bodySha256(command))
                || !issued.originalAttemptRequestId().equals(attempt.requestId()))
            throw new IOException("recovered Council permit differs from its exact canonical original command/attempt");
        org.xar.ck3.control.nativebridge.capabilities.governance.CouncilContinuationPolicy
                .requireOriginalPending(command, attempt, ack);
        if (issued.stage() != Stage.HELPER_STATUS && issued.stage() != Stage.RECEIPT_QUERY && issued.stage() != Stage.RECEIPT_STATUS)
            throw new IOException("recovered Council RPC is outside its fixed read-only stages");
        if (!prepared.equals(issued.preparedRequest()) || prepared.requiredCapability().isPresent()
                || !prepared.step().equals(issued.stage().step())
                || !NativeWire.object(NativeWire.parse(prepared.additionalFields().bytes())).isEmpty())
            throw new IOException("recovered Council RPC differs from its exact ISSUED stage and empty arguments");
        requireRecoveredGuard(issued, original);
        String id = issued.requestId();
        if (issued.consumed() || sentRequestIds.contains(id)) {
            if (terminalFailure == null) terminalFailure = "recovered Council request was already attempted; collect that exact original only";
            latestReadEvidence = null;
            return new Unknown(id, terminalFailure, retainedOutbound(id), Optional.empty());
        }
        if (sentRequestIds.size() >= maximumSubmissions) throw new IOException("Native request identity retention limit reached");
        byte[] packet = issued.stage() == Stage.RECEIPT_QUERY
                ? NativeWire.execute(id, COUNCIL_RECEIPT, issued.guard().origin().expectedRevision(), prepared.additionalFields().bytes())
                : NativeWire.executeCouncilMailboxStatus(id, COUNCIL_STATUS, prepared.additionalFields().bytes());
        var role = new CouncilRecoveryRole(issued, original, deadline);
        activeCouncilRecovery = role;
        try {
            role.binding(); latestReadEvidence = null;
            // This private call alone bypasses ordinary mailbox admission. All other producer writes remain fenced.
            requireWorldActionMode();
            DispatchOutcome outcome = dispatchOriginal(id, packet, readDeadline(deadline), role::consumeAtWrite);
            if (outcome instanceof Unknown && terminalFailure == null)
                terminalFailure = "actual recovered Council RPC is UNKNOWN; no new producer or replay is authorized";
            return outcome;
        } finally {
            role.released = true; activeCouncilRecovery = null;
        }
    }
    private void requireRecoveredGuard(CouncilContinuationPermit issued,
            CouncilContinuationCoordinator.RecoveryOriginal original) throws IOException {
        GuardEvidence fresh = issued.guard(); GuardEvidence before = original.attempt().guard();
        var command = original.command(); Instant now = Instant.now();
        if (hello == null || !config.sessionId().equals(issued.sessionId())
                || !fresh.sessionId().equals(issued.sessionId()) || !before.sessionId().equals(fresh.sessionId())
                || !command.sessionId().equals(fresh.sessionId())
                || !hello.connectionGeneration().equals(fresh.connectionGeneration())
                || !fresh.authorityId().equals(before.authorityId()) || !fresh.operation().equals(before.operation())
                || !fresh.operation().equals(command.operation())
                || !fresh.source().sourceRef().equals(before.source().sourceRef())
                || !fresh.source().exactBuild().equals(before.source().exactBuild())
                || !fresh.source().equals(command.source())
                || !sameCouncilLife(before.origin(), fresh.origin())
                || !now.isBefore(fresh.validUntil()) || fresh.observedAt().isAfter(now))
            throw new IOException("recovered Council RPC crossed its actual current session/guard or historical source/Game/actor binding");
        // The old connection and custody epoch remain historical DATA; only the current HELLO must match the new guard.
        if (fresh.origin().expectedRevision().compareTo(before.origin().expectedRevision()) < 0
                || (issued.stage() == Stage.RECEIPT_QUERY
                    && fresh.origin().expectedRevision().compareTo(before.origin().expectedRevision()) <= 0))
            throw new IOException("recovered Council RPC lacks its required actual current native revision");
        requireIdentity(fresh.origin()); requireRawEvidence(fresh); requireLivingPausedMap();
    }

    /** Only a live original-writer continuation permit can poll or inspect this held Council mutation. */
    public synchronized DispatchOutcome continueCouncil(CouncilContinuationPermit permit, NativeRequest exactRequest,
            Instant deadline) throws InterruptedException {
        Objects.requireNonNull(permit); Objects.requireNonNull(exactRequest); String id = permit.requestId();
        try {
            if (permit.recoveryOriginal().isPresent()) throw new IOException("recovered Council permit requires its exact private RPC lane");
            if (permit.consumed() || sentRequestIds.contains(id))
                return recordMailboxOutcome(new Unknown(id, "original continuation already attempted; collect that exact original only", retainedOutbound(id), Optional.empty()));
            open(deadline); verifyEndpoint();
            if (hello == null || activeMailbox == null) throw new IOException("Council continuation requires its actual held hello and mailbox scope");
            activeMailbox.current();
            if (activeMailbox.unknownSeen) throw new IOException("UNKNOWN mailbox continuation cannot allocate another request");
            if (activeMailbox.helperRejectedBeforeSubmit)
                throw new IOException("known non-invoked helper rejection has no pending ACK or receipt to continue");
            CouncilAssignment original = activeMailbox.assignment;
            if (original == null || !activeMailbox.attempted.contains(original.requestId())
                    || !original.requestId().equals(permit.originalAttemptRequestId())
                    || !original.actionId().equals(permit.originalActionId()) || !original.bodySha256().equals(permit.originalBodySha256()))
                throw new IOException("continuation is not the actual pending private assignment in this held mailbox");
            GuardEvidence fresh = permit.guard();
            if (!config.sessionId().equals(permit.sessionId()) || !fresh.sessionId().equals(permit.sessionId())
                    || !hello.connectionGeneration().equals(fresh.connectionGeneration())
                    || !original.guard().connectionGeneration().equals(fresh.connectionGeneration())
                    || !fresh.authorityId().equals(original.guard().authorityId()) || !fresh.operation().equals(original.guard().operation())
                    || !fresh.source().sourceRef().equals(original.guard().source().sourceRef())
                    || !fresh.source().exactBuild().equals(original.guard().source().exactBuild()))
                throw new IOException("continuation crossed the original session, Root authority or source binding");
            if (!Instant.now().isBefore(fresh.validUntil()) || fresh.observedAt().isAfter(Instant.now())
                    || !sameCouncilLife(original.guard().origin(), fresh.origin()))
                throw new IOException("continuation requires a fresh guard for the same actual actor and episode");
            requireIdentity(fresh.origin()); requireRawEvidence(fresh); requireLivingPausedMap();
            if (!exactRequest.equals(permit.preparedRequest()) || exactRequest.requiredCapability().isPresent()
                    || !exactRequest.step().equals(permit.stage().step())
                    || !NativeWire.object(NativeWire.parse(exactRequest.additionalFields().bytes())).isEmpty())
                throw new IOException("continuation differs from its durable exact Council stage and empty arguments");
            if (sentRequestIds.size() >= maximumSubmissions) throw new IOException("Native request identity retention limit reached");
            byte[] packet;
            if (permit.stage() == Stage.RECEIPT_QUERY) {
                if (!activeMailbox.helperCompleted || activeMailbox.receiptPending || activeMailbox.receiptCompleted
                        || fresh.origin().expectedRevision().compareTo(original.guard().origin().expectedRevision()) <= 0)
                    throw new IOException("receipt query needs the consumed actual helper result and a newer actual native frame");
                packet = NativeWire.execute(id, COUNCIL_RECEIPT, fresh.origin().expectedRevision(), exactRequest.additionalFields().bytes());
            } else {
                if (permit.stage() == Stage.HELPER_STATUS ? activeMailbox.helperCompleted : !activeMailbox.receiptPending)
                    throw new IOException("status stage differs from this original mailbox continuation phase");
                packet = NativeWire.executeCouncilMailboxStatus(id, COUNCIL_STATUS, exactRequest.additionalFields().bytes());
            }
            latestReadEvidence = null;
            DispatchOutcome outcome = dispatch(id, packet, deadline, permit::consumeOnce, true);
            if (outcome instanceof AckReceived ack && ack.nativeOk()) {
                if (permit.stage() == Stage.HELPER_STATUS && terminalStep(ack, "assign-councillor-v1")) {
                    activeMailbox.helperCompleted = true;
                    activeMailbox.helperRejectedBeforeSubmit = nonInvokedCouncilRejection(ack, original);
                    if (unresolvedCouncilHelper(ack)) activeMailbox.unknownSeen = true;
                }
                if (permit.stage() == Stage.RECEIPT_QUERY) {
                    if (isCouncilPending(ack)) activeMailbox.receiptPending = true;
                    else if (terminalStep(ack, "query-assign-councillor-receipt-v1")) activeMailbox.receiptCompleted = true;
                }
                if (permit.stage() == Stage.RECEIPT_STATUS && terminalStep(ack, "query-assign-councillor-receipt-v1")) {
                    activeMailbox.receiptPending = false; activeMailbox.receiptCompleted = true;
                }
            }
            return outcome;
        } catch (IOException | RuntimeException failure) { return zero(id, reason(failure)); }
    }
    private static boolean sameCouncilLife(CommandOrigin original, CommandOrigin fresh) {
        if (!(original instanceof CommandOrigin.Gameplay before) || !(fresh instanceof CommandOrigin.Gameplay after)) return false;
        return before.machineId().equals(after.machineId()) && before.game().equals(after.game())
                && before.before().frame().episodeRunId().equals(after.before().frame().episodeRunId())
                && before.before().frame().identity().player().equals(after.before().frame().identity().player());
    }
    private static boolean isCouncilPending(AckReceived ack) {
        if (!ack.nativeOk() || ack.originalResultToken().isEmpty()) return false;
        try {
            var value = NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));
            return value.has("private_council_transport") && value.get("private_council_transport").isBoolean()
                    && value.get("private_council_transport").booleanValue() && value.has("advertised")
                    && value.get("advertised").isBoolean() && !value.get("advertised").booleanValue()
                    && value.has("status") && value.get("status").isTextual() && value.get("status").textValue().equals("pending");
        } catch (IOException malformed) { return false; }
    }
    private static boolean terminalStep(AckReceived ack, String expectedStep) {
        if (isCouncilTransportStatus(ack) || ack.originalResultToken().isEmpty()) return false;
        try {
            var value = NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));
            return value.has("step") && value.get("step").isTextual() && value.get("step").textValue().equals(expectedStep)
                    && value.has("schema") && value.get("schema").isTextual()
                    && value.get("schema").textValue().equals("xar.ck3.council-application-main/v1")
                    && value.has("accepted") && value.get("accepted").isBoolean() && value.get("accepted").booleanValue();
        } catch (IOException malformed) { return false; }
    }
    /** Protocol phase only. The installed Council decoder separately validates the entire 18-field business payload. */
    private static boolean unresolvedCouncilHelper(AckReceived ack) {
        if (ack.originalResultToken().isEmpty()) return false;
        try {
            var outer = NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));
            var inner = NativeWire.object(outer.get("council_assign_councillor_ack"));
            return textEquals(inner, "native_reason_key", "action_executor_exception")
                    || textEquals(inner, "native_reason_key", "pending_assignment_unresolved");
        } catch (IOException | RuntimeException malformed) { return false; }
    }
    /** Protocol phase only. The installed Council decoder separately validates the entire 18-field business payload. */
    private static boolean nonInvokedCouncilRejection(AckReceived ack, CouncilAssignment assignment) {
        if (!ack.nativeOk() || !terminalStep(ack, "assign-councillor-v1")) return false;
        try {
            var outer = NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));
            var inner = NativeWire.object(outer.get("council_assign_councillor_ack"));
            var sent = NativeWire.object(NativeWire.parse(assignment.originalRequest().additionalFields().bytes()));
            var failure = inner.get("failure"); var reason = inner.get("native_reason_key");
            var candidate = inner.get("candidate_character_id"); var sentCandidate = sent.get("candidate_character_id");
            return textEquals(outer, "status", "rejected_before_submit") && integerEquals(outer, "snapshot_revision", 0)
                    && textEquals(inner, "status", "rejected_before_submit")
                    && textEquals(inner, "action_request_id", assignment.requestId())
                    && textEquals(inner, "pre_snapshot_id", "") && textEquals(inner, "route", "none")
                    && failure != null && failure.isTextual() && !failure.textValue().isEmpty() && !failure.textValue().equals("none")
                    && reason != null && reason.isTextual() && !reason.textValue().equals("action_executor_exception")
                    && !reason.textValue().equals("pending_assignment_unresolved")
                    && integerEquals(inner, "pre_public_revision", 0) && integerEquals(inner, "pre_native_revision", 0)
                    && integerEquals(inner, "pre_date_raw", 0) && integerEquals(inner, "owner_character_id", -1)
                    && integerEquals(inner, "active_task_id", -1) && integerEquals(inner, "previous_incumbent_character_id", -1)
                    && falseBoolean(inner, "had_incumbent") && falseBoolean(inner, "native_helper_invoked")
                    && falseBoolean(inner, "queue_acceptance_observed") && falseBoolean(inner, "verification_pending")
                    && candidate != null && candidate.isIntegralNumber() && sentCandidate != null && sentCandidate.isIntegralNumber()
                    && candidate.bigIntegerValue().equals(sentCandidate.bigIntegerValue())
                    // The private mutation wire carries candidate only. Position equality belongs to the
                    // installed Council decoder's original gates/preflight evidence, never a new wire field.
                    && inner.get("position_key") != null && inner.get("position_key").isTextual()
                    && !inner.get("position_key").textValue().isEmpty();
        } catch (IOException | RuntimeException malformed) { return false; }
    }
    private static boolean textEquals(ObjectNode object, String name, String expected) {
        var value = object.get(name); return value != null && value.isTextual() && value.textValue().equals(expected);
    }
    private static boolean integerEquals(ObjectNode object, String name, long expected) {
        var value = object.get(name); return value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(BigInteger.valueOf(expected));
    }
    private static boolean falseBoolean(ObjectNode object, String name) {
        var value = object.get(name); return value != null && value.isBoolean() && !value.booleanValue();
    }
    private Instant readDeadline(Instant callerDeadline) {
        if (configuredReadTimeout.isEmpty()) return callerDeadline;
        Instant configured = chronologyClock.instant().plus(configuredReadTimeout.get());
        return callerDeadline.isBefore(configured) ? callerDeadline : configured;
    }
    private DispatchOutcome retainReadOutcome(DispatchOutcome outcome) {
        latestReadEvidence = null;
        if (outcome instanceof AckReceived ack && ack.nativeOk()) {
            byte[] packet = ack.originalPacket();
            try { latestReadEvidence = new ReceivedReadEvidence(packet.length, sha256(packet)); }
            catch (IOException unavailable) {
                latestReadEvidence = null;
                terminalFailure = "cannot retain exact original read evidence: " + reason(unavailable);
            }
        }
        // An evidence-custody failure after an ACK cannot become a zero-dispatch result.
        return outcome;
    }
    private DispatchOutcome dispatch(String id, byte[] packet, Instant deadline, Runnable consumePermit) throws InterruptedException {
        return dispatch(id, packet, deadline, consumePermit, false);
    }
    private DispatchOutcome dispatch(String id, byte[] packet, Instant deadline, Runnable consumePermit, boolean continuation) throws InterruptedException {
        return dispatchChecked(id,packet,deadline,consumePermit,continuation,false);
    }
    private DispatchOutcome dispatchRead(String id,byte[] packet,Instant deadline,Runnable consumePermit)throws InterruptedException{
        return dispatchChecked(id,packet,deadline,consumePermit,false,true);
    }
    /** Exit/status/cancel retain their original independent finite authorization; mode creates no new ticket. */
    private DispatchOutcome dispatchLifecycle(String id,byte[] packet,Instant deadline,Runnable consumePermit)throws InterruptedException{
        return dispatchChecked(id,packet,deadline,consumePermit,false,true);
    }
    private DispatchOutcome dispatchChecked(String id,byte[] packet,Instant deadline,Runnable consumePermit,
            boolean continuation,boolean independentlyReadonlyOrLifecycle)throws InterruptedException{
        try {
            if(!independentlyReadonlyOrLifecycle)requireWorldActionMode();
            var payload = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length)));
            requireDispatchScope(NativeWire.text(payload.get("step")), continuation, id);
        } catch (IOException failure) { return zero(id, reason(failure)); }
        return recordMailboxOutcome(dispatchOriginal(id, packet, deadline, consumePermit));
    }
    private DispatchOutcome dispatchOriginal(String id, byte[] packet, Instant deadline, Runnable consumePermit) throws InterruptedException {
        boolean enteredWrite = false;
        boolean writeReturned = false;
        try {
            if (originalOutboundPackets.containsKey(id) || retainedOutboundBytes + packet.length > NativeWire.MAXIMUM_FRAME_BYTES + 4L)
                throw new IOException("original outbound custody is duplicate or its finite byte budget is exhausted before write");
            try { consumePermit.run(); }
            catch (RuntimeException consumedElsewhere) {
                byte[] original = retainedOutbound(id);
                return original.length == 0 ? zero(id, "authority rejected consumption before any write: " + reason(consumedElsewhere))
                        : new Unknown(id, "submission authority already attempted; reconcile actual retained original", original, Optional.empty());
            }
            NativeRequestChronology.PacketIdentity originalRequest = packetIdentity(packet);
            NativeRequestChronology.Event entered = chronologyEvent();
            sentRequestIds.add(id);
            originalOutboundPackets.put(id, new NativeWire.Bytes(packet)); retainedOutboundBytes += packet.length;
            writtenRequests.put(id, new WrittenRequest(session(), originalRequest, entered, Optional.empty()));
            enteredWrite = true; endpoint.writePacket(packet, deadline);
            writeReturned = true;
            NativeRequestChronology.Event completed = chronologyEvent();
            writtenRequests.put(id, new WrittenRequest(session(), originalRequest, entered, Optional.of(completed)));
            for (int frames = 0; frames < maximumFramesPerOperation; frames++) {
                Optional<NativeWire.Frame> frame = read(deadline);
                if (frame.isPresent() && frame.orElseThrow() instanceof NativeWire.CommandResult result && result.requestId().equals(id)) {
                    removeRetained(result);
                    Optional<RawJson> token = result.result().token().map(value -> new RawJson(value.value()));
                    return new AckReceived(id, result.nativeOk(), token, new RawJson(result.payload().value()), result.packet().value(),
                            Optional.of(new NativeActionPort.OutboundPacket(id, packet)), originalRequestChronology(id));
                }
            }
            return new Unknown(id, "Native command_result frame budget exhausted; original request is never replayed", packet, Optional.empty(),
                    Optional.of(new NativeActionPort.FailureCause(NativeActionPort.FailureKind.FRAME_BUDGET_EXHAUSTED,
                            NativeActionPort.FailureStage.RESPONSE_WAIT,Optional.empty(),Optional.empty(),Optional.empty())));
        } catch (NativePipeEndpoint.TransferFailure failure) {
            retainActualDisconnection(failure);
            // readPacket also uses TransferFailure(false, 0). Its response bytes cannot prove that
            // the preceding write never happened, even when their length or contents match it.
            if (enteredWrite && !writeReturned && !failure.writeAttempted() && failure.writtenBytes() == 0
                    && Arrays.equals(failure.retainedBytes(), packet)) {
                NativeWire.Bytes removed = originalOutboundPackets.remove(id);
                if (removed != null) retainedOutboundBytes -= removed.value().length;
                writtenRequests.remove(id);
                return zero(id, failure.getMessage());
            }
            return new Unknown(id, reason(failure), packet, Optional.empty(),Optional.of(dispatchFailure(failure,
                    writeReturned?NativeActionPort.FailureStage.RESPONSE_WAIT:NativeActionPort.FailureStage.WRITE,
                    NativeActionPort.FailureKind.TRANSFER_IO)));
        } catch (IOException | RuntimeException failure) {
            retainActualDisconnection(failure);
            return enteredWrite ? new Unknown(id, reason(failure), packet, Optional.empty(),Optional.of(dispatchFailure(failure,
                    writeReturned?NativeActionPort.FailureStage.RESPONSE_WAIT:NativeActionPort.FailureStage.WRITE,
                    failure instanceof IOException?NativeActionPort.FailureKind.IO_FAILURE:NativeActionPort.FailureKind.RUNTIME_FAILURE))) : zero(id, reason(failure));
        } catch (InterruptedException interrupted) {
            // Preserve UNKNOWN after a possible write, even when the caller's thread is cancelled.
            if (enteredWrite) { Thread.currentThread().interrupt(); return new Unknown(id, "Native submission interrupted after entering write; never replay", packet, Optional.empty(),
                    Optional.of(dispatchFailure(interrupted,writeReturned?NativeActionPort.FailureStage.RESPONSE_WAIT:NativeActionPort.FailureStage.WRITE,
                            NativeActionPort.FailureKind.INTERRUPTED))); }
            throw interrupted;
        }
    }
    private static NativeActionPort.FailureCause dispatchFailure(Throwable original,NativeActionPort.FailureStage stage,
            NativeActionPort.FailureKind fallback) {
        Optional<NativeActionPort.DeadlineObservation> deadline=Optional.empty();
        if(original instanceof NativePacketPort.DeadlineExpired expired)deadline=Optional.of(expired.observation());
        else if(original instanceof NativePipeEndpoint.TransferFailure transfer&&transfer.getCause() instanceof NativePacketPort.DeadlineExpired expired)
            deadline=Optional.of(expired.observation());
        return new NativeActionPort.FailureCause(deadline.isPresent()?NativeActionPort.FailureKind.DEADLINE_EXPIRED:fallback,stage,
                Optional.of(NativeActionPort.OriginalException.from(original)),
                Optional.ofNullable(original.getCause()).map(NativeActionPort.OriginalException::from),deadline);
    }
    private byte[] retainedOutbound(String requestId) {
        NativeWire.Bytes actual = originalOutboundPackets.get(requestId); return actual == null ? new byte[0] : actual.value();
    }
    private NativeRequestChronology.Event chronologyEvent() throws IOException {
        Instant actual;
        try { actual = Objects.requireNonNull(chronologyClock.instant()); }
        catch (RuntimeException unavailable) {
            terminalFailure = "actual Native chronology clock unavailable: " + reason(unavailable);
            throw new IOException(terminalFailure, unavailable);
        }
        BigInteger next = chronologyOrder.add(BigInteger.ONE);
        if (next.compareTo(NativeWire.UINT64_MAX) > 0 || lastChronologyAt != null && actual.isBefore(lastChronologyAt)) {
            terminalFailure = "actual Native event order exhausted or UTC regressed: actual=" + actual + ", previous=" + lastChronologyAt;
            throw new IOException(terminalFailure);
        }
        var event = new NativeRequestChronology.Event(next, actual);
        chronologyOrder = next; lastChronologyAt = actual;
        return event;
    }
    private static NativeRequestChronology.PacketIdentity packetIdentity(byte[] original) throws IOException {
        return new NativeRequestChronology.PacketIdentity(original.length, sha256(original));
    }
    /** Original packet-bound chronology, without I/O or a new observation timestamp. Incomplete writes grant none. */
    public synchronized Optional<NativeRequestChronology> originalRequestChronology(String requestId) {
        Objects.requireNonNull(requestId);
        WrittenRequest written = writtenRequests.get(requestId);
        ReceivedResponse received = originalResponses.get(requestId);
        if (written == null || written.completed().isEmpty() || received == null) return Optional.empty();
        return Optional.of(new NativeRequestChronology(written.session(), custodyEpoch, requestId, written.packet(), received.packet(),
                written.entered(), written.completed().orElseThrow(), received.received()));
    }
    /** Immutable original bytes actually handed to the held endpoint; never regenerates a request. */
    public synchronized Optional<NativeActionPort.OutboundPacket> originalOutboundPacket(String requestId) {
        Objects.requireNonNull(requestId); NativeWire.Bytes original = originalOutboundPackets.get(requestId);
        return original == null ? Optional.empty() : Optional.of(new NativeActionPort.OutboundPacket(requestId, original.value()));
    }
    /** Original result with the same retained actual write bytes; no dispatch or new request identity. */
    public synchronized Optional<AckReceived> collectOriginalOutcome(String requestId, Instant deadline) throws IOException, InterruptedException {
        NativeActionPort.OutboundPacket outbound = originalOutboundPacket(requestId)
                .orElseThrow(() -> new IOException("actual original outbound bytes are unavailable; no reconstruction allowed"));
        Optional<NativeWire.CommandResult> original = collectOriginalResult(requestId, deadline);
        return original.map(result -> new AckReceived(requestId, result.nativeOk(),
                result.result().token().map(value -> new RawJson(value.value())), new RawJson(result.payload().value()),
                result.packet().value(), Optional.of(outbound), originalRequestChronology(requestId)));
    }
    /** Pure exact-ID pop of an already received original. No endpoint call, deadline, new identity or resend. */
    @Override public synchronized Optional<AckReceived> pollOriginalOutcome(String attemptedRequestId) throws IOException {
        Objects.requireNonNull(attemptedRequestId);
        if (!sentRequestIds.contains(attemptedRequestId)) throw new IOException("only an original attempted request can be polled");
        NativeActionPort.OutboundPacket outbound = originalOutboundPacket(attemptedRequestId)
                .orElseThrow(() -> new IOException("actual original outbound bytes unavailable; no reconstruction allowed"));
        for (NativeWire.CommandResult result : lateResults) {
            if (!result.requestId().equals(attemptedRequestId)) continue;
            AckReceived original = new AckReceived(attemptedRequestId, result.nativeOk(),
                    result.result().token().map(value -> new RawJson(value.value())), new RawJson(result.payload().value()),
                    result.packet().value(), Optional.of(outbound), originalRequestChronology(attemptedRequestId));
            removeRetained(result);
            return Optional.of(original);
        }
        return Optional.empty();
    }
    /** Original late ACKs are delivered for reconciliation; this method never resubmits an action. */
    public synchronized List<NativeWire.CommandResult> drainLateResults() {
        List<NativeWire.CommandResult> result = List.copyOf(lateResults); lateResults.clear(); retainedResultBytes = 0; return result;
    }
    /** Includes malformed UTF-8/JSON frames verbatim; terminal decode failures prevent overwriting this evidence. */
    public synchronized byte[] lastOriginalPacket() { return lastOriginalPacket.clone(); }
    public synchronized Optional<NativeWire.CommandResult> collectOriginalResult(String requestId, Instant deadline) throws IOException, InterruptedException {
        open(deadline);
        if (!sentRequestIds.contains(requestId)) throw new IOException("only an original attempted request can be reconciled");
        for (NativeWire.CommandResult retained : lateResults) if (retained.requestId().equals(requestId)) { removeRetained(retained); return Optional.of(retained); }
        for (int frames = 0; frames < maximumFramesPerOperation; frames++) {
            Optional<NativeWire.Frame> frame = read(deadline);
            if (frame.isPresent() && frame.orElseThrow() instanceof NativeWire.CommandResult result && result.requestId().equals(requestId)) { removeRetained(result); return Optional.of(result); }
        }
        return Optional.empty();
    }
    /** Empty means one actual rejected snapshot was consumed. Every caller keeps its original finite packet budget. */
    private Optional<NativeWire.Frame> read(Instant deadline) throws IOException, InterruptedException {
        open(deadline); verifyEndpoint();
        final byte[] original;
        try { original = endpoint.readPacket(deadline); }
        catch (NativePipeEndpoint.TransferFailure failure) {
            retainActualDisconnection(failure);
            byte[] partial = failure.retainedBytes();
            if (partial.length > 0) {
                lastOriginalPacket = partial;
                terminalFailure = "ordinary Native read failed with a partial original packet";
            }
            throw failure;
        }
        catch (NativePacketPort.ReadInterrupted interrupted) {
            byte[] partial = interrupted.originalPartialPacket();
            if (partial.length > 0) {
                lastOriginalPacket = partial;
                terminalFailure = "ordinary Native read interrupted with a partial original packet";
            }
            throw interrupted;
        }
        catch (IOException failure) {retainActualDisconnection(failure);throw failure;}
        return ingestOriginalPacket(original);
    }
    /** The new raw semantic marker is accepted only with its actual held exact-build HELLO. */
    private void requireFullSnapshotBuild(NativeWire.Snapshot received)throws IOException {
        ObjectNode raw=NativeWire.object(NativeWire.parse(received.state().value()));
        ObjectNode originalHello=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
        var expectedVersion=originalHello.get("expected_ck3_version");
        if(expectedVersion!=null&&!expectedVersion.isTextual())throw new IOException("optional HELLO version must be text when present");
        var profile=expectedVersion==null?Optional.<ExactCk3Build>empty()
                :ExactCk3Build.florinCoreFullBuild(NativeWire.text(expectedVersion),hello.gameSha256(),hello.adapterId());
        boolean florin=profile.filter(build->hello.adapterId().equals(build.coreFullAdapterId())).isPresent();
        var actor=raw.get("played_character");
        if(florin) {
            StrictJson.require(hello.capabilities().contains(NativeFreshSnapshotPort.CAPABILITY)
                    &&hello.capabilities().contains("game.state.snapshot"),"Florin full state requires both advertised full-state capabilities");
            requireFlorinFullTuple(raw,"ck3_1210_full_state_v1",profile.orElseThrow());
            if(actor!=null&&!actor.isNull())requireFlorinFullTuple(NativeWire.object(actor),"ck3_1210_played_character_v1",profile.orElseThrow());
            if(profile.orElseThrow()==ExactCk3Build.CK3_121003_STEAM_26785313_FULL111) {
                StrictJson.require(raw.has("active_event")&&raw.path("active_event").isNull(),
                        "Full111 initial Full requires an explicit null active_event");
                if(armyIdentity126Source!=null) {
                    requireArmyIdentity126Source(true);
                    StrictJson.require(raw.path("active_wars").isArray()&&raw.path("active_wars").isEmpty(),
                            "identity126 requires its explicitly observed empty War scope");
                    org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies.normalize(raw,armyObservationMode());
                }else {
                    for(String field:List.of("active_wars","player_armies"))
                        StrictJson.require(raw.path(field).isArray()&&raw.path(field).isEmpty(),
                                "Full111 initial Full requires an explicit empty "+field);
                    requireCurrentFull111Source(profile.orElseThrow());
                }
            }
            if(profile.orElseThrow()==ExactCk3Build.CK3_1210_STEAM_26757580) {
                StrictJson.require(raw.has("active_event")&&raw.path("active_event").isNull(),
                        "hotfix initial Full profile requires an explicit null active_event");
                StrictJson.require(raw.path("active_wars").isArray()&&raw.path("active_wars").isEmpty(),
                        "hotfix Full profile requires explicit empty active_wars");
                var armies=raw.get("player_armies");
                StrictJson.require(armies!=null&&armies.isArray(),"hotfix Full requires explicit owned-army array");
                if(!armies.isEmpty()){
                    requireArmyReadonlySource();
                    org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies.normalize(raw);
                }
            }
        } else {
            StrictJson.require(!raw.path("schema").asText().equals("ck3_1210_full_state_v1")
                    &&(actor==null||!actor.path("schema").asText().equals("ck3_1210_played_character_v1")),
                    "Florin full-state semantics cannot borrow a legacy HELLO");
        }
    }
    private static void requireFlorinFullTuple(ObjectNode value,String schema,ExactCk3Build expected)throws IOException {
        StrictJson.require(schema.equals(NativeWire.text(value.get("schema")))
                &&expected.matches(NativeWire.text(value.get("game_version")),NativeWire.text(value.get("executable_sha256")))
                &&expected.coreFullAdapterId().equals(NativeWire.text(value.get("adapter_id")))
                &&expected.coreFullBackend().equals(NativeWire.text(value.get("backend"))),
                "Florin full-state schema/executable/adapter/backend tuple mismatch");
    }
    /** Sole decoder/accounting path for both ordinary reception and typed WAIT. */
    private Optional<NativeWire.Frame> ingestOriginalPacket(byte[] original) throws IOException {
        if(hello==null&&initialHelloCustody!=null) {
            HelloPacketCustody custody=initialHelloCustody;initialHelloCustody=null;
            lastOriginalPacket=original.clone();
            try{custody.retain(original.clone());}
            catch(IOException failure){terminalFailure="Original hello custody failed: "+failure.getMessage();throw failure;}
        }
        NativeRequestChronology.Event receivedAt;
        try { receivedAt = chronologyEvent(); }
        catch (IOException invalidTime) { lastOriginalPacket = original.clone(); throw invalidTime; }
        lastOriginalPacket = original.clone();
        NativeWire.Frame frame;
        try { frame = NativeWire.decode(original); }
        catch (IOException failure) {
            boolean snapshotEnvelope=false;
            if(hello!=null)try { snapshotEnvelope=NativeTransportDiagnostics.snapshotObject(original).isPresent(); }
            catch(IOException | IllegalArgumentException malformedEnvelope) { /* Malformed JSON/protocol is not an admitted semantic snapshot. */ }
            if (snapshotEnvelope) { verifyEndpoint(); rejectSnapshot(receivedSnapshot(original,receivedAt.observedAt()),failure); return Optional.empty(); }
            terminalFailure = failure.getMessage(); throw failure;
        }
        verifyEndpoint();
        if (frame instanceof NativeWire.Hello incoming) {
            if (hello != null) { terminalFailure = "a second Native hello invalidates the held session; no automatic reconnect"; throw new IOException(terminalFailure); }
            if (incoming.pid() != config.game().pid() || !incoming.bridgeVersion().equals(config.expectedBridgeVersion())
                    || !incoming.gameSha256().equalsIgnoreCase(config.expectedGameSha256()) || !incoming.adapterId().equals(config.expectedAdapterId())
                    || !incoming.buildMatch() || !incoming.adapterStatus().equals("ready")) { terminalFailure = "actual Native hello differs from exact Game/bridge binding"; throw new IOException(terminalFailure); }
            hello = incoming; helloObservedAt = receivedAt.observedAt();
            statePublicRevision=statePublicRevision.add(BigInteger.ONE);stateConnected=true;
            latestStateRevision=new StateRevision(session(),receivedAt,statePublicRevision,StateRevisionKind.HELLO,Optional.empty());
        } else {
            if (hello == null) { terminalFailure = "Native frame arrived before original hello"; throw new IOException(terminalFailure); }
            if (frame instanceof NativeWire.Snapshot received) {
                NativeTransportDiagnostics.ReceivedSnapshot candidate=receivedSnapshot(original,receivedAt.observedAt());
                // Reuse the sole current native collection parser. No second normalizer or guessed counter is introduced.
                ObservedFrame actual = new ObservedFrame(session(),received.snapshotId(),received.revision(),new RawJson(received.state().value()),received.packet().value(),receivedAt.observedAt());
                final OpportunityJson.Obj semantic;
                try { requireFullSnapshotBuild(received); }
                catch(IOException|IllegalArgumentException invalidIdentity) { rejectSnapshot(candidate,invalidIdentity); return Optional.empty(); }
                try {
                    semantic=DriverObservationAssembler.canonicalNativeState(actual,armyObservationMode()).semantic();
                    // The Driver consumes this exact integer; a rejected date never mints a receiver occurrence.
                    OpportunityJson.integer(semantic.get("date_raw"),"date_raw");
                }
                catch (IllegalArgumentException | ArithmeticException invalidSemantic) { rejectSnapshot(candidate,invalidSemantic); return Optional.empty(); }
                if (snapshot != null && received.revision().compareTo(snapshot.revision()) < 0) { terminalFailure = "Native revision regressed in one connection"; throw new IOException(terminalFailure); }
                captureFreshSnapshot(received,actual,receivedAt);
                retainAcceptedSnapshotRevision(actual,receivedAt,semantic);
                snapshot = received; acceptedSnapshotFrame=actual; snapshotObservedAt = receivedAt.observedAt(); snapshotUndelivered = true;
            } else if (frame instanceof NativeWire.CommandResult result) retain(result, receivedAt);
            else if (frame instanceof NativeWire.Notice notice) {
                ReceivedNotice received = new ReceivedNotice(notice, receivedAt.observedAt());
                switch (notice.kind()) {
                    case HEARTBEAT -> latestHeartbeat = received;
                    case PONG -> {latestPong = received;retainHandshakePong(received,receivedAt);}
                    case ERROR -> latestError = received;
                    case SNAPSHOT_PUBLISH_DIAGNOSTIC -> { snapshotPublishDiagnosticCount = nextDiagnosticCount(snapshotPublishDiagnosticCount); latestSnapshotDiagnostic = received; }
                }
            }
        }
        return Optional.of(frame);
    }
    private NativeTransportDiagnostics.ReceivedSnapshot receivedSnapshot(byte[] original,Instant observedAt) throws IOException {
        receivedSnapshotCount=nextDiagnosticCount(receivedSnapshotCount);
        var actual=new NativeTransportDiagnostics.ReceivedSnapshot(session(),receivedSnapshotCount,new NativeWire.Bytes(original),observedAt);
        lastReceivedSnapshot=actual;return actual;
    }
    private BigInteger nextDiagnosticCount(BigInteger actual) throws IOException {
        BigInteger next = actual.add(BigInteger.ONE);
        if (next.compareTo(NativeWire.UINT64_MAX) > 0) { diagnosticAccountingAvailable=false; throw new IOException("actual diagnostic uint64 counter exhausted; no wrapping or rounded output"); }
        return next;
    }
    private void rejectSnapshot(NativeTransportDiagnostics.ReceivedSnapshot actual, Exception failure) throws IOException {
        String errorType=failure.getClass().getSimpleName();if(errorType.isEmpty())errorType=failure.getClass().getName();
        var rejected = new NativeTransportDiagnostics.RejectedSnapshot(actual,errorType,
                failure.getMessage()==null?failure.toString():failure.getMessage());
        BigInteger next=nextDiagnosticCount(rejectedSnapshotCount);lastRejectedSnapshot=rejected;rejectedSnapshotCount=next;
    }
    private void retain(NativeWire.CommandResult result, NativeRequestChronology.Event receivedAt) throws IOException {
        if (sentRequestIds.contains(result.requestId())) {
            NativeRequestChronology.PacketIdentity identity = packetIdentity(result.packet().value());
            ReceivedResponse existing = originalResponses.get(result.requestId());
            if (existing != null && !existing.packet().equals(identity)) {
                terminalFailure = "conflicting original response packets for a retained Native request";
                throw new IOException(terminalFailure);
            }
            if (existing == null) originalResponses.put(result.requestId(), new ReceivedResponse(identity, receivedAt));
        }
        for (NativeWire.CommandResult existing : lateResults) {
            if (existing.requestId().equals(result.requestId())) {
                if (!Arrays.equals(existing.packet().value(), result.packet().value())) { terminalFailure = "conflicting original results for one Native request id"; throw new IOException(terminalFailure); }
                return;
            }
        }
        int bytes = result.packet().byteLength();
        if (lateResults.size() >= maximumFramesPerOperation || (long) retainedResultBytes + bytes > NativeWire.MAXIMUM_FRAME_BYTES + 4L) {
            terminalFailure = "undrained original Native result custody budget exhausted"; throw new IOException(terminalFailure);
        }
        lateResults.add(result); retainedResultBytes += bytes;
    }
    private void removeRetained(NativeWire.CommandResult result) {
        if (lateResults.remove(result)) retainedResultBytes -= result.packet().byteLength();
    }
    private void requireIdentity(CommandOrigin origin) throws IOException {
        if (!origin.machineId().equals(config.machineId()) || !origin.game().equals(config.game()))
            throw new IOException("origin differs from actual held Game identity");
        if (origin instanceof CommandOrigin.Gameplay gameplay) { requireGameplayIdentity(gameplay.before()); return; }
        if (origin instanceof CommandOrigin.LifecycleTerminal terminal) { requireTerminalIdentity(terminal.identity()); return; }
        if (origin instanceof CommandOrigin.Reconciliation reconciliation) { requireReconciliationIdentity(reconciliation.identity()); return; }
        if (origin instanceof CommandOrigin.PhysicalStatusOnly physical) { requirePhysicalStatusIdentity(physical.identity()); return; }
        var frontend = origin.requireFrontend();
        if (!frontend.frontendSessionId().equals(config.sessionId())
                || !frontend.connectionGeneration().equals(hello.connectionGeneration()))
            throw new IOException("frontend origin differs from actual held Native session");
        if (frontend.frame() instanceof FrontendFrame.Menu) {
            if (origin.expectedRevision().signum() != 0) throw new IOException("frontend menu requires revision zero");
            return;
        }
        FrontendFrame.Snapshot frame = (FrontendFrame.Snapshot) frontend.frame();
        if (snapshot == null || !frame.snapshotId().equals(snapshot.snapshotId())
                || !frame.nativeRevision().equals(snapshot.revision()))
            throw new IOException("frontend snapshot identity differs from actual held Native frame");
        ObjectNode state = NativeWire.object(NativeWire.parse(snapshot.state().value()));
        if (!BigInteger.valueOf(frame.dateRaw()).equals(NativeWire.integer(state.get("date_raw"), BigInteger.ZERO, null)))
            throw new IOException("frontend date differs from actual Native snapshot");
    }
    private void requireGameplayIdentity(ObservationIdentity before) throws IOException {
        if (snapshot == null) throw new IOException("gameplay origin requires an actual state snapshot");
        if (!before.machineId().equals(config.machineId()) || !before.game().equals(config.game())
                || !before.frame().snapshotId().equals(snapshot.snapshotId()) || !before.frame().identity().nativeRevision().equals(snapshot.revision()))
            throw new IOException("coordinator before identity differs from actual held Native frame");
        ObjectNode state = NativeWire.object(NativeWire.parse(snapshot.state().value()));
        BigInteger date = NativeWire.integer(state.get("date_raw"), BigInteger.ZERO, null);
        ObjectNode player = NativeWire.object(state.get("played_character"));
        BigInteger playerId = NativeCharacterId.fromJson(player.get("character_id")).asBigInteger();
        if (!before.frame().identity().dateRaw().equals(date) || !before.frame().identity().player().equals(playerId))
            throw new IOException("coordinator player/date differs from raw Native state token");
    }
    private void requireTerminalIdentity(LifecycleIdentity identity) throws IOException {
        if (snapshot == null || !identity.sessionId().equals(config.sessionId())
                || !identity.connectionGeneration().equals(hello.connectionGeneration())
                || !identity.frame().snapshotId().equals(snapshot.snapshotId()) || !identity.frame().nativeRevision().equals(snapshot.revision()))
            throw new IOException("lifecycle identity differs from the actual held terminal snapshot/session");
        ObjectNode state = NativeWire.object(NativeWire.parse(snapshot.state().value()));
        BigInteger date = NativeWire.integer(state.get("date_raw"), BigInteger.valueOf(Long.MIN_VALUE), BigInteger.valueOf(Long.MAX_VALUE));
        var paused = state.get("paused"); var mapReady = state.get("map_ready");
        if (!identity.frame().dateRaw().equals(date) || paused == null || !paused.isBoolean() || mapReady == null || !mapReady.isBoolean()
                || paused.booleanValue() != identity.frame().paused() || mapReady.booleanValue() != identity.frame().mapReady())
            throw new IOException("lifecycle date/paused/map fields differ from actual original Native state");
        var player = state.get("played_character"); LifecycleIdentity.CurrentPlayer actual;
        if (player == null) actual = new LifecycleIdentity.Missing();
        else if (player.isNull()) actual = new LifecycleIdentity.Null();
        else {
            ObjectNode character = NativeWire.object(player); var alive = character.get("alive");
            if (alive == null || !alive.isBoolean()) throw new IOException("actual terminal player requires an exact alive boolean");
            actual = new LifecycleIdentity.Character(NativeCharacterId.fromJson(character.get("character_id")).asBigInteger(), alive.booleanValue());
        }
        if (!actual.equals(identity.currentPlayer()))
            throw new IOException("lifecycle current player was inferred from the old episode subject instead of the original Native token");
    }
    private void requireReconciliationIdentity(ReconciliationIdentity identity) throws IOException {
        if (!identity.sessionId().equals(config.sessionId()) || !identity.connectionGeneration().equals(hello.connectionGeneration()))
            throw new IOException("reconciliation identity differs from the actual held Native session");
        // This checks only actual snapshot/player/date identity; ordinary living/paused/map readiness is not conferred.
        requireGameplayIdentity(identity.factual());
    }
    /** Checks original raw transport facts only. No Driver, actor, episode or ordinary readiness is inferred. */
    private void requirePhysicalStatusIdentity(PhysicalStatusIdentity identity) throws IOException {
        if (snapshot == null || !identity.transport().equals(session())
                || !identity.snapshotId().equals(snapshot.snapshotId()) || !identity.nativeRevision().equals(snapshot.revision())
                || !identity.observedAt().equals(snapshotObservedAt))
            throw new IOException("physical status identity differs from the actual retained native snapshot/session");
        requireOriginalBytes(identity.nativeEvidence(), snapshot.packet().value());
        requireOriginalBytes(identity.helloEvidence(), hello.packet().value());
        if (latestHeartbeat == null) throw new IOException("physical status requires an actual received heartbeat");
        requireOriginalBytes(identity.heartbeatEvidence(), latestHeartbeat.original().packet().value());
    }
    private static void requireOriginalBytes(org.xar.ck3.control.contracts.ExactRef expected, byte[] actual) throws IOException {
        if (expected.bytes() != actual.length || !expected.sha256().equals(sha256(actual)))
            throw new IOException("physical status source does not bind the actual received original packet");
    }
    private void requireLivingPausedMap() throws IOException {
        ObjectNode state = NativeWire.object(NativeWire.parse(snapshot.state().value()));
        ObjectNode player = NativeWire.object(state.get("played_character"));
        for (var entry : List.of(state.get("paused"), state.get("map_ready"), player.get("alive"))) {
            if (entry == null || !entry.isBoolean() || !entry.booleanValue()) throw new IOException("read requires actual native paused/map_ready/player_alive true");
        }
    }
    private void requireRawEvidence(GuardEvidence evidence) throws IOException {
        byte[] capabilities = hello.packet().value();
        if (evidence.capabilityEvidence().bytes() != capabilities.length
                || !evidence.capabilityEvidence().sha256().equals(sha256(capabilities)))
            throw new IOException("coordinator capability evidence does not bind the original hello packet");
        boolean snapshotMatch = snapshot != null && evidence.nativeEvidence().bytes() == snapshot.packet().value().length
                && evidence.nativeEvidence().sha256().equals(sha256(snapshot.packet().value()));
        if (evidence.origin() instanceof CommandOrigin.Gameplay || evidence.origin() instanceof CommandOrigin.LifecycleTerminal
                || evidence.origin() instanceof CommandOrigin.Reconciliation || evidence.origin() instanceof CommandOrigin.PhysicalStatusOnly) {
            if (!snapshotMatch) throw new IOException("gameplay/lifecycle/reconciliation evidence does not bind the actual original snapshot");
            return;
        }
        boolean readMatch = latestReadEvidence != null && evidence.nativeEvidence().bytes() == latestReadEvidence.bytes()
                && evidence.nativeEvidence().sha256().equals(latestReadEvidence.sha256());
        boolean menu = evidence.origin().requireFrontend().frame() instanceof FrontendFrame.Menu;
        if (menu ? !readMatch : !(readMatch || snapshotMatch))
            throw new IOException("frontend evidence is not an actual retained read result or matching snapshot; hello grants no frontend identity");
    }
    private static String sha256(byte[] bytes) throws IOException {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException unavailable) { throw new IOException("SHA256 unavailable", unavailable); }
    }
    private TransportSession session() {
        return new TransportSession(config.machineId(), config.game(), hello.connectionGeneration(), config.sessionId());
    }
    private void verifyEndpoint() throws IOException {
        try {endpoint.verify();}
        catch(IOException failure) {retainActualDisconnection(failure);throw failure;}
    }
    private void retainActualDisconnection(Throwable original) {
        if(hello==null||!stateConnected)return;
        NativePacketPort.Disconnection observed=endpoint.originalDisconnection().orElse(null);
        if(observed==null&&original instanceof NativePacketPort.ConnectionLost lost)observed=lost.original();
        if(observed==null&&original instanceof NativePipeEndpoint.TransferFailure transfer
                &&transfer.getCause() instanceof NativePacketPort.ConnectionLost lost)observed=lost.original();
        if(observed==null)return;
        try {
            var event=chronologyEvent();BigInteger next=statePublicRevision.add(BigInteger.ONE);
            if(next.compareTo(NativeWire.UINT64_MAX)>0)throw new IOException("actual disconnected public revision exhausted uint64");
            latestStateRevision=new StateRevision(session(),event,next,StateRevisionKind.DISCONNECTED,Optional.of(observed));
            statePublicRevision=next;stateConnected=false;
            if(terminalFailure==null)terminalFailure="actual Native pipe disconnected: "+observed.operation()+" Win32="+observed.win32Code();
        } catch(IOException invalidChronology) {
            stateRevisionAvailable=false;stateConnected=false;
            terminalFailure="actual Native disconnect revision chronology unavailable";
            if(original!=null)original.addSuppressed(invalidChronology);
        }
    }
    private void open(Instant deadline) throws IOException {
        if(activeMailbox!=null&&activeMailbox.deferredReadDiagnostic!=null)throw new IOException("deferred optional READ scope must return before further transport operations");
        if (terminalFailure != null) throw new IOException("original Native connection is terminal: " + terminalFailure);
        if (closed || deadline == null || !Instant.now().isBefore(deadline)) {
            Instant actualNow = Instant.now();
            throw new IOException("held Native transport closed or caller deadline expired: closed=" + closed + ", deadline=" + deadline + ", actualNow=" + actualNow);
        }
    }
    private static RejectedBeforeDispatch zero(String requestId, String reason) {
        return new RejectedBeforeDispatch(requestId, new ZeroDispatchProof(ZeroDispatchStage.BEFORE_WRITE, 0, reason, Optional.empty()));
    }
    private static String observationFailure(IOException failure) {
        String detail = reason(failure);
        return detail.substring(0, Math.min(512, detail.length()));
    }
    private static String reason(Exception failure) { return failure.getClass().getSimpleName() + ": " + Objects.toString(failure.getMessage(), "unavailable"); }
    @Override public synchronized void close() throws IOException {
        closed=true;
        try {endpoint.close();} finally {ownerCanonicalObj=null;derivedJsonNode=null;
            retainActualDisconnection(null);
            if(hello!=null&&stateConnected) {
                stateRevisionAvailable=false;
                terminalFailure="Native close has no qualified actual disconnection observation";
            }
        }
    }
}
