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
import org.xar.ck3.control.contracts.semantic.NativeSemanticFingerprint;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.application.action.PhysicalStatusIdentity;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.PlanningReadFailure;
import org.xar.ck3.control.application.action.PlanningReadFailureCodec;
import org.xar.ck3.control.application.action.CommandOrigin;
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
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.ReconciliationIdentity;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.SubmissionPermit;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverJson;
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
    private OpportunityJson.Obj lastAcceptedSemantic;
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
        if(!NativeSemanticFingerprint.equivalent(DriverJson.toNode(semantic),
                lastAcceptedSemantic==null?null:DriverJson.toNode(lastAcceptedSemantic)))next=next.add(BigInteger.ONE);
        if(next.compareTo(NativeWire.UINT64_MAX)>0)throw new IOException("actual received public revision exhausted uint64");
        var token=new AcceptedSnapshotRevision(actual,received,next);
        if(acceptedSnapshotRevisions.size()>=Math.max(4096,maximumFramesPerOperation))
            acceptedSnapshotRevisions.remove(acceptedSnapshotRevisions.keySet().iterator().next());
        acceptedSnapshotRevisions.put(received.order(),token);latestAcceptedSnapshotRevision=token;
        statePublicRevision=next;lastAcceptedSemantic=semantic;
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
        /** Leaves only this original optional READ prefix, after a real current after guard and original archive check. */
        public void deferReadOnly(PlanningReadFailure live, ExactRef sharedFailureDiagnostic,
                ActionPorts.OutcomeArchive boundArchive) throws IOException {
            synchronized(NativeGameTransport.this) {
                current();Objects.requireNonNull(live);Objects.requireNonNull(sharedFailureDiagnostic);Objects.requireNonNull(boundArchive);
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
        Objects.requireNonNull(work); open(deadline);
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
    private void requireDispatchScope(String step, boolean continuation) throws IOException {
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
    /** The one original standalone partial-prefix read. It cannot carry a caller-selected step or mutation. */
    @Override public synchronized DispatchOutcome readCoreFrame(Instant deadline) throws InterruptedException {
        String id = "core-frame-" + UUID.randomUUID().toString().replace("-", "");
        try {
            awaitHello(deadline); verifyEndpoint();
            ObjectNode original = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(), 4, hello.packet().value().length)));
            if (!hello.capabilities().contains("game.query.core-frame.v1")
                    || !hello.adapterId().equals("ck3-1.20.0.4-msvc-x64")
                    || !hello.gameSha256().equalsIgnoreCase("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                    || !NativeWire.text(original.get("expected_ck3_version")).equals("1.20.0.4"))
                throw new IOException("standalone core prefix requires the original ready exact .4 hello and advertised core-frame capability");
            if (sentRequestIds.size() >= maximumSubmissions) throw new IOException("Native request identity retention limit reached");
            return retainReadOutcome(dispatch(id, NativeWire.execute(id, "query-core-frame-v1", BigInteger.ZERO, new byte[] {'{', '}'}), deadline, () -> { }));
        } catch (IOException | RuntimeException failure) { return retainReadOutcome(zero(id, reason(failure))); }
    }
    /** Independently published READ for either exact .6 or .4 producer. No unresolved original is resubmitted. */
    @Override public synchronized NativeFreshSnapshotPort.Result readFreshFullState(Instant deadline)throws InterruptedException {
        if(pendingFreshSnapshot!=null)return freshUnavailable(pendingFreshSnapshot,"original fresh READ remains unresolved; collect its original outcome without resubmission");
        String id="fresh-state-"+UUID.randomUUID().toString().replace("-","");
        try {
            awaitHello(deadline);verifyEndpoint();
            ObjectNode original=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(),4,hello.packet().value().length)));
            String version=NativeWire.text(original.get("expected_ck3_version"));
            boolean exactSix=hello.adapterId().equals("ck3-1.19.0.6-msvc-x64")
                    &&hello.gameSha256().equalsIgnoreCase("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86")
                    &&version.equals("1.19.0.6");
            boolean exactFour=hello.adapterId().equals("ck3-1.20.0.4-msvc-x64")
                    &&hello.gameSha256().equalsIgnoreCase("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                    &&version.equals("1.20.0.4");
            if(!hello.capabilities().contains(NativeFreshSnapshotPort.CAPABILITY)||!hello.capabilities().contains("game.state.snapshot")||!(exactSix||exactFour))
                throw new IOException("fresh full-state READ requires an exact .6 or .4 HELLO and its independent read capability");
            if(sentRequestIds.size()>=maximumSubmissions)throw new IOException("Native request identity retention limit reached");
            byte[] request=NativeWire.execute(id,NativeFreshSnapshotPort.STEP,BigInteger.ZERO,new byte[]{'{','}'});
            var capture=new FreshSnapshotCapture(id);pendingFreshSnapshot=capture;
            return finishFreshRead(capture,retainReadOutcome(dispatch(id,request,deadline,()->{})));
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
            pendingFreshSnapshot=null;return freshUnavailable(capture,"original fresh READ was rejected without an accepted independent state proof");
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
    private NativeFreshSnapshotPort.Unavailable freshUnavailable(FreshSnapshotCapture capture,String reason) {
        DispatchOutcome original=capture.outcome;
        if(original==null)original=new Unknown(capture.requestId,"actual fresh READ is still held; never replay",retainedOutbound(capture.requestId),Optional.empty());
        return new NativeFreshSnapshotPort.Unavailable(original,reason,Optional.ofNullable(capture.frame),Optional.ofNullable(capture.received));
    }
    private void captureFreshSnapshot(NativeWire.Snapshot received,ObservedFrame actual,NativeRequestChronology.Event event)throws IOException {
        var capture=pendingFreshSnapshot;if(capture==null)return;
        ObjectNode raw=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(received.packet().value(),4,received.packet().value().length)));
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
            return retainReadOutcome(dispatch(id, NativeWire.execute(id, "query-frontend-gui-route-v1", BigInteger.ZERO,
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
                    awaitHello(deadline);
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
        try {
            awaitHello(deadline);
            if (!hello.capabilities().contains("game.state.snapshot")) throw new IOException("Native DLL did not advertise game.state.snapshot");
            if (!snapshotUndelivered) {
                for (int frames = 0; frames < maximumFramesPerOperation && !snapshotUndelivered; frames++) read(deadline);
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
    @Override public synchronized DispatchOutcome submit(SubmissionPermit permit, NativeRequest request, Instant deadline) throws InterruptedException {
        Objects.requireNonNull(permit); Objects.requireNonNull(request);
        String id = permit.requestId();
        try {
            if (permit.origin() instanceof CommandOrigin.Reconciliation || permit.origin() instanceof CommandOrigin.PhysicalStatusOnly)
                throw new IOException("read-only reconciliation or physical status origin can never submit a world primitive");
            if (permit.consumed() || sentRequestIds.contains(id)) {
                return recordMailboxOutcome(new Unknown(id, "original permit/request was already attempted; reconcile the actual retained original without replay", retainedOutbound(id), Optional.empty()));
            }
            open(deadline); verifyEndpoint();
            if (hello == null) throw new IOException("actual Native hello is required before dispatch");
            if (!request.equals(permit.preparedRequest())) throw new IOException("primitive differs from the coordinator's durable prepared request");
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
            DispatchOutcome original = dispatch(id, packet, deadline, () -> {
                permit.consumeOnce();
                heldSnapshotInvalidated = true;
            });
            if (COUNCIL_ASSIGN.equals(request.step()) && request.requiredCapability().isEmpty()
                    && original instanceof AckReceived ack && isCouncilPending(ack)) {
                // Actual canonical SUBMITTING permit and private source permission were checked above.
                activeMailbox.assignment = new CouncilAssignment(permit.actionId(), permit.bodySha256(), id, permit.guard(), request);
            }
            return original;
        } catch (IOException | RuntimeException failure) { return zero(id, reason(failure)); }
    }
    /** Registered collector reads use this same endpoint and one exact request ID, without a world-action intent. */
    @Override public synchronized DispatchOutcome read(ReadPermit permit, NativeRequest request, Instant deadline) throws InterruptedException {
        Objects.requireNonNull(permit); Objects.requireNonNull(request); String id = permit.requestId();
        try {
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
            if(activeMailbox!=null)activeMailbox.actualReads.put(id,permit);
            return retainReadOutcome(dispatch(id, packet, readDeadline(deadline), permit::consumeOnce));
        } catch (IOException | RuntimeException failure) { return retainReadOutcome(zero(id, reason(failure))); }
    }
    /** Only a live original-writer continuation permit can poll or inspect this held Council mutation. */
    public synchronized DispatchOutcome continueCouncil(CouncilContinuationPermit permit, NativeRequest exactRequest,
            Instant deadline) throws InterruptedException {
        Objects.requireNonNull(permit); Objects.requireNonNull(exactRequest); String id = permit.requestId();
        try {
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
        try {
            var payload = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length)));
            requireDispatchScope(NativeWire.text(payload.get("step")), continuation);
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
    /** Sole decoder/accounting path for both ordinary reception and typed WAIT. */
    private Optional<NativeWire.Frame> ingestOriginalPacket(byte[] original) throws IOException {
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
                try {
                    semantic=DriverObservationAssembler.canonicalNativeState(actual).semantic();
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
        int bytes = result.packet().value().length;
        if (lateResults.size() >= maximumFramesPerOperation || (long) retainedResultBytes + bytes > NativeWire.MAXIMUM_FRAME_BYTES + 4L) {
            terminalFailure = "undrained original Native result custody budget exhausted"; throw new IOException(terminalFailure);
        }
        lateResults.add(result); retainedResultBytes += bytes;
    }
    private void removeRetained(NativeWire.CommandResult result) {
        if (lateResults.remove(result)) retainedResultBytes -= result.packet().value().length;
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
        if (closed || deadline == null || !Instant.now().isBefore(deadline)) throw new IOException("held Native transport closed or caller deadline expired");
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
        try {endpoint.close();} finally {
            retainActualDisconnection(null);
            if(hello!=null&&stateConnected) {
                stateRevisionAvailable=false;
                terminalFailure="Native close has no qualified actual disconnection observation";
            }
        }
    }
}

