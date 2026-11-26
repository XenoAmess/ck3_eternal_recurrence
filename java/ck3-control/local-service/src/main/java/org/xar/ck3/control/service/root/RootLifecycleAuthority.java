package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.application.readiness.RootNativeCapabilities;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One real physical snapshot serves public facts, terminal reads and explicitly qualified reconciliation. */
public final class RootLifecycleAuthority {
    @FunctionalInterface public interface SourcePort {
        SourceQualification verify(ContinuityStorePort.Session session, NativeObservationPort.TransportSession actualSession,
                G2Source actualSource, ExactRef actualOriginPacket, NativeGameTransport.TransportDiagnostics received,
                Instant deadline) throws IOException;
    }
    @FunctionalInterface public interface CheckedWork<T> { T apply(Lease actual) throws IOException; }
    @FunctionalInterface public interface SnapshotWork<T> { T apply(SnapshotLease actual) throws IOException; }
    @FunctionalInterface private interface FreshSnapshotRead {
        NativeFreshSnapshotPort.Result read(Instant deadline) throws IOException, InterruptedException;
    }
    @FunctionalInterface public interface ActualDriverAuthority {
        /** Root resolves its actually adopted Driver at use time; no pre-adoption repository or substitute is legal. */
        DriverStateAssembler resolve(ContinuityStorePort.Session borrowed) throws IOException;
    }

    /** Verified negative READ DATA only: never a snapshot, physical lease or reconciliation issuer. */
    public static final class NegativeFreshRead extends IOException {
        @java.io.Serial private static final long serialVersionUID = 1L;
        private final byte[] sourceBytes;
        private final String machine, game, session, requestId, acknowledgementPath, acknowledgementSha, outboundPath, outboundSha;
        private final long acknowledgementBytes, outboundBytes;
        private NegativeFreshRead(G2Source source, NativeObservationPort.TransportSession owner, String requestId,
                ExactRef acknowledgement, ExactRef outbound) {
            super("actual fresh read unavailable: kind=ACK/native_ok=false; request_id=" + requestId
                    + "; dispatch_ref=" + acknowledgement + "; frame_ref=absent; reason=original fresh READ received negative Native ACK; request_id="
                    + requestId + "; error=\"fresh_full_state_native_read_unavailable\"");
            sourceBytes=org.xar.ck3.control.contracts.StrictJson.canonical(
                    org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.source(source));
            machine=owner.machineId();game=owner.game().toString();session=owner.sessionId();this.requestId=requestId;
            acknowledgementPath=acknowledgement.path();acknowledgementBytes=acknowledgement.bytes();acknowledgementSha=acknowledgement.sha256();
            outboundPath=outbound.path();outboundBytes=outbound.bytes();outboundSha=outbound.sha256();
        }
        public boolean matches(ActionCommand original) {
            return machine.equals(original.origin().machineId()) && game.equals(original.origin().game().toString())
                    && session.equals(original.sessionId()) && Arrays.equals(sourceBytes,
                    org.xar.ck3.control.contracts.StrictJson.canonical(org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.source(original.source())));
        }
        public String requestId() { return requestId; }
        public ExactRef acknowledgement() { return new ExactRef(acknowledgementPath,acknowledgementBytes,acknowledgementSha); }
        public ExactRef outbound() { return new ExactRef(outboundPath,outboundBytes,outboundSha); }
    }

    /** Pure packet/custody validation; an Unavailable/ACK DTO by itself grants no live observation authority. */
    static Optional<NativeActionPort.AckReceived> verifiedNegativeFreshRead(NativeFreshSnapshotPort.Result result,
            NativeObservationPort.TransportSession actualOwner) throws IOException {
        if (!(result instanceof NativeFreshSnapshotPort.Unavailable unavailable)
                || !(unavailable.dispatch() instanceof NativeActionPort.AckReceived ack) || ack.nativeOk()
                || unavailable.originalFrame().isPresent() || unavailable.snapshotReceived().isPresent()) return Optional.empty();
        var custody=ack.custody().orElseThrow(()->new IOException("negative fresh READ lacks actual chronology"));
        custody.verify(ack);
        require(custody.session().equals(actualOwner),"negative fresh READ crossed the actual held Native owner");
        var outbound=ack.outbound().orElseThrow(()->new IOException("negative fresh READ lacks its original outbound"));
        byte[] outboundBytes=outbound.originalPacket();
        require(outboundBytes.length>=5 && java.nio.ByteBuffer.wrap(outboundBytes,0,4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt()==outboundBytes.length-4,
                "negative fresh READ outbound framing changed");
        var request=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(outboundBytes,4,outboundBytes.length)));
        require(request.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toSet())
                .equals(Set.of("type","protocol_version","request_id","step","expected_revision")),"negative fresh READ outbound fields changed");
        require("execute_step".equals(NativeWire.text(request.get("type")))
                && java.math.BigInteger.ONE.equals(NativeWire.integer(request.get("protocol_version"),java.math.BigInteger.ONE,java.math.BigInteger.ONE))
                && NativeFreshSnapshotPort.STEP.equals(NativeWire.text(request.get("step")))
                && ack.requestId().equals(NativeWire.text(request.get("request_id")))
                && java.math.BigInteger.ZERO.equals(NativeWire.integer(request.get("expected_revision"),java.math.BigInteger.ZERO,java.math.BigInteger.ZERO)),
                "negative fresh READ differs from its fixed original query");
        var decoded=NativeWire.decode(ack.originalPacket());
        require(decoded instanceof NativeWire.CommandResult,"negative fresh READ is not an original command result");
        var response=(NativeWire.CommandResult)decoded;
        require(!response.nativeOk() && ack.requestId().equals(response.requestId())
                && Arrays.equals(response.payload().value(),ack.originalFrame().bytes())
                && response.result().token().isPresent()==ack.originalResultToken().isPresent()
                && (response.result().token().isEmpty() || Arrays.equals(response.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes())),
                "negative fresh READ ACK fields differ from the actual framed packet");
        var wire=NativeWire.object(NativeWire.parse(response.payload().value()));
        var fields=wire.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toSet());
        require(fields.equals(Set.of("type","protocol_version","request_id","ok","error"))
                || fields.equals(Set.of("type","protocol_version","request_id","ok","error","result")),"negative fresh READ response fields changed");
        if (!"fresh_full_state_native_read_unavailable".equals(NativeWire.text(wire.get("error")))) return Optional.empty();
        require(!wire.has("result") || wire.get("result").isNull(),"negative fresh READ unexpectedly returned successful material");
        return Optional.of(ack);
    }

    /** Its private constructor and active writer scope distinguish source qualification from copied snapshot data. */
    public static final class SnapshotLease {
        private final RootLifecycleAuthority owner;
        private final DriverObservationAssembler.FullSnapshot full;
        private final Known known;
        private final DriverObservationFacts facts;
        private final Optional<DriverObservationAssembler.Complete> ordinary;
        private final Optional<LifecycleIdentity> terminal;
        private final Optional<LifecycleObservationPort.Snapshot> terminalSnapshot;
        private final Optional<ExactRef> terminalSemantic;
        private final Optional<NativeFreshSnapshotPort.Received> freshSnapshot;
        private final ExactRef hello,heartbeat,driver,semantic;
        private final SourceQualification sources;
        private final Instant until;
        private final Set<String> capabilities;
        private final Supplier<DriverStateSnapshot> canonicalProjection;
        private SnapshotLease(RootLifecycleAuthority owner,DriverObservationAssembler.FullSnapshot full,Known known,
                DriverObservationFacts facts,Optional<DriverObservationAssembler.Complete> ordinary,Optional<LifecycleIdentity> terminal,
                Optional<LifecycleObservationPort.Snapshot> terminalSnapshot,Optional<ExactRef> terminalSemantic,
                Optional<NativeFreshSnapshotPort.Received> freshSnapshot,
                ExactRef hello,ExactRef heartbeat,ExactRef driver,ExactRef semantic,SourceQualification sources,
                Instant until,Set<String> capabilities,Supplier<DriverStateSnapshot> canonicalProjection) {
            this.owner=owner;this.full=full;this.known=known;this.facts=facts;this.ordinary=ordinary;this.terminal=terminal;
            this.terminalSnapshot=terminalSnapshot;this.terminalSemantic=terminalSemantic;this.freshSnapshot=freshSnapshot;this.hello=hello;this.heartbeat=heartbeat;
            this.driver=driver;this.semantic=semantic;this.sources=sources;this.until=until;
            this.capabilities=Set.copyOf(capabilities);this.canonicalProjection=canonicalProjection;
        }
        public Optional<NativeFreshSnapshotPort.Received> freshSnapshot() { return freshSnapshot; }
        public DriverObservationAssembler.FullSnapshot fullSnapshot() { return full; }
        public Known factsKnown() { return known; }
        public DriverObservationFacts freshFacts() { return facts; }
        /** Complete is actual joined data. This optional does not grant ordinary readiness, action or SAVE authority. */
        public Optional<DriverObservationAssembler.Complete> ordinary() { return ordinary; }
        public Optional<LifecycleIdentity> terminalIdentity() { return terminal; }
        public ExactRef originalHello() { return hello; }
        public ExactRef originalHeartbeat() { return heartbeat; }
        public ExactRef originalDriver() { return driver; }
        public ExactRef originalSemantic() { return semantic; }
        public SourceQualification sourceQualification() { return sources; }
        public Instant validUntil() { return until; }
        public Set<String> bridgeCapabilities() { return capabilities; }
        public void assertCurrent(ContinuityStorePort.Session borrowed) throws IOException {
            Scope scope=owner.active.get();require(scope!=null&&scope.snapshot()==this,"detached physical snapshot has no live source authority");
            owner.assertScope(scope,borrowed,scope.deadline());
        }
    }

    /** Only withObserved can create this narrower canonical terminal admission inside the shared physical scope. */
    public static final class Lease {
        private final SnapshotLease physical;
        private Lease(SnapshotLease physical) { this.physical=physical; }
        public LifecycleIdentity identity() { return physical.terminal.orElseThrow(); }
        public LifecycleObservationPort.Snapshot snapshot() { return physical.terminalSnapshot.orElseThrow(); }
        public DriverObservationFacts freshFacts() { return physical.freshFacts(); }
        public ExactRef originalHello() { return physical.originalHello(); }
        public ExactRef originalHeartbeat() { return physical.originalHeartbeat(); }
        public ExactRef originalSemantic() { return physical.terminalSemantic.orElseThrow(); }
        public SourceQualification sourceQualification() { return physical.sourceQualification(); }
        public Instant validUntil() { return physical.validUntil(); }
        public Set<String> bridgeCapabilities() { return physical.bridgeCapabilities(); }
        public void assertCurrent(ContinuityStorePort.Session borrowed) throws IOException { physical.assertCurrent(borrowed); }
    }
    private record Scope(ContinuityStorePort.Session session,SnapshotLease snapshot,String head,Instant deadline,Instant heartbeatObservedAt) { }
    @FunctionalInterface interface PreparedReadWork<T> { T run() throws IOException,InterruptedException; }
    private static final class OriginalArmReadPreparation {
        private final ActionReceipt parent,child;
        private final String head;
        private final Instant deadline;
        private ContinuityStorePort.Session session;
        private OriginalArmReadPreparation(ActionReceipt parent,ActionReceipt child,String head,Instant deadline) {
            this.parent=parent;this.child=child;this.head=head;this.deadline=deadline;
        }
    }
    private final ThreadLocal<OriginalArmReadPreparation> originalArmPreparation=new ThreadLocal<>();
    private final ThreadLocal<Boolean> zeroCancellationPreparation=new ThreadLocal<>();
    private static final int MAX_ORIGINAL=WriterContracts.MAX_PIN_BYTES;
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private final NativeGameTransport transport;
    private final ActualDriverAuthority driver;
    private final DriverObservationAssembler assembler;
    private final G2Source source;
    private final SourcePort sources;
    private final Clock clock;
    private final Duration freshness;
    private final NativeSemanticEvidenceVerifier semantics;
    private final ThreadLocal<Scope> active=new ThreadLocal<>();
    public RootLifecycleAuthority(ContinuityWriter sameWriter,NativeOutcomeArchive sameArchive,NativeGameTransport sameTransport,
            DriverStateAssembler sameDriver,DriverObservationAssembler sameAssembler,G2Source actualSource,
            SourcePort actualSources,Clock clock,Duration freshness) {
        this(sameWriter,sameArchive,sameTransport,borrowed->{sameWriter.requireSession(borrowed);return Objects.requireNonNull(sameDriver);},
                sameAssembler,actualSource,actualSources,clock,freshness);
    }
    /** Constructed before catalog freeze; every actual read resolves the one adopted runtime Driver or explicitly refuses. */
    public RootLifecycleAuthority(ContinuityWriter sameWriter,NativeOutcomeArchive sameArchive,NativeGameTransport sameTransport,
            ActualDriverAuthority actualAdoptedDriver,DriverObservationAssembler sameAssembler,G2Source actualSource,
            SourcePort actualSources,Clock clock,Duration freshness) {
        writer=Objects.requireNonNull(sameWriter);archive=Objects.requireNonNull(sameArchive);transport=Objects.requireNonNull(sameTransport);
        driver=Objects.requireNonNull(actualAdoptedDriver);assembler=Objects.requireNonNull(sameAssembler);source=Objects.requireNonNull(actualSource);
        sources=Objects.requireNonNull(actualSources);this.clock=Objects.requireNonNull(clock);this.freshness=Objects.requireNonNull(freshness);
        semantics=new NativeSemanticEvidenceVerifier((borrowed,ref,maximum)->archive.readArtifact(borrowed,ref,maximum));
        require(archive.writer()==writer,"physical snapshot must share the sole writer/archive");
        require(!freshness.isNegative()&&!freshness.isZero()&&freshness.compareTo(Duration.ofMinutes(1))<=0,"finite physical snapshot freshness required");
    }

    /** Package-owned Root call only. The actual Core private DATA identity is checked before this entry. */
    <T>T withOriginalArmReadPreparation(org.xar.ck3.control.application.session.ContinuityBatchJournal.UnresolvedSameGameData data,
            Instant callerDeadline,PreparedReadWork<T> work)throws IOException,InterruptedException {
        Objects.requireNonNull(data);Objects.requireNonNull(callerDeadline);Objects.requireNonNull(work);
        require(originalArmPreparation.get()==null&&active.get()==null,"original ARM preparation cannot nest an observation or preparation");
        Instant now=clock.instant(),local=now.plus(Duration.ofMinutes(10));
        Instant until=callerDeadline.isBefore(local)?callerDeadline:local;
        require(now.isBefore(until),"original ARM read preparation caller deadline expired");
        // Complete actual canonical membership is authenticated before the parent Coordinator mints its old 120s window.
        OriginalArmReadPreparation prepared=writer.locked(same->{
            requireSession(same);var head=same.head();var bound=archive.withSession(same);
            require(data.unresolvedActions().size()==1&&data.retainedHistory().isPresent(),"original ARM preparation requires its actual retained single root");
            ActionReceipt parent=data.unresolvedActions().getFirst();
            var canonical=ContinuityActionJournal.receipts(head.state(),bound);
            require(org.xar.ck3.control.application.session.ContinuityBatchJournal.readOnlyLifeRecoveryRoot(canonical).filter(parent::equals).isPresent()
                    &&parent.state() instanceof ActionState.CompositeUnknown,"original ARM preparation lost its canonical Life root");
            var execution=((ActionState.CompositeUnknown)parent.state()).execution();
            require(execution.children().size()==1,"original ARM preparation permits its sole original ARM child only");
            var binding=execution.children().getFirst();
            ActionReceipt child=canonical.stream().filter(value->value.command().actionId().equals(binding.actionId())).findFirst().orElseThrow();
            ActionReceipt retained=data.retainedHistory().orElseThrow().settledActions().stream()
                    .filter(value->value.command().actionId().equals(binding.actionId())).findFirst().orElseThrow();
            var plan=org.xar.ck3.control.application.advance.AdvancePlan.decode(parent.command());
            require(child.equals(retained)&&child.bodySha256().equals(binding.bodySha256())
                    &&child.command().operation().value().equals(plan.armStep())&&RootReconciliationAuthority.isPositiveAckClockArm(child)
                    &&child.command().source().equals(source)&&child.command().sessionId().equals(data.capturedController().owner().sessionId())
                    &&child.command().origin().game().equals(data.capturedController().owner().game()),
                    "original ARM preparation changed its actual ACK/Attempt/body/source/Game/sole prefix");
            require(head.digest().equals(same.head().digest())&&clock.instant().isBefore(until),
                    "original ARM preparation changed its writer or exhausted its one caller envelope");
            return new OriginalArmReadPreparation(parent,child,head.digest(),until);
        });
        originalArmPreparation.set(prepared);
        try{return work.run();}finally{originalArmPreparation.remove();}
    }
    /** A separate preparation role for an already terminal zero-write cancellation.
     * It authenticates the complete retained prefix before the coordinator starts its short new token window.
     * Core has already checked private DATA identity; this scope grants no READ, Ready, dispatch or write bypass. */
    <T>T withZeroCancellationReadPreparation(
            org.xar.ck3.control.application.session.ContinuityBatchJournal.UnresolvedSameGameData data,
            Instant callerDeadline,PreparedReadWork<T> work)throws IOException,InterruptedException {
        Objects.requireNonNull(data);Objects.requireNonNull(callerDeadline);Objects.requireNonNull(work);
        require(originalArmPreparation.get()==null&&zeroCancellationPreparation.get()==null&&active.get()==null,
                "zero cancellation preparation cannot nest an observation or another preparation");
        Instant now=clock.instant(),local=now.plus(Duration.ofMinutes(10));
        Instant until=callerDeadline.isBefore(local)?callerDeadline:local;
        require(now.isBefore(until),"zero cancellation preparation caller deadline expired");
        writer.locked(same->{
            requireSession(same);var head=same.head();var bound=archive.withSession(same);
            require(data.unresolvedActions().size()==1&&data.retainedHistory().isPresent()
                            &&head.state().sequence()==data.canonicalSequence()
                            &&head.digest().equals(data.canonicalHeadDigest()),
                    "zero cancellation preparation changed its actual retained DATA/head");
            var parent=data.unresolvedActions().getFirst();
            var canonical=ContinuityActionJournal.receipts(head.state(),bound);
            require(org.xar.ck3.control.application.session.ContinuityBatchJournal.readOnlyLifeRecoveryRoot(canonical)
                            .filter(parent::equals).isPresent()&&parent.state() instanceof ActionState.CompositeUnknown,
                    "zero cancellation preparation lost its canonical original Life root");
            var execution=((ActionState.CompositeUnknown)parent.state()).execution();
            var children=execution.children().stream().map(binding->{
                var child=canonical.stream().filter(value->value.command().actionId().equals(binding.actionId())).findFirst().orElseThrow();
                require(child.bodySha256().equals(binding.bodySha256())
                                &&data.retainedHistory().orElseThrow().settledActions().contains(child)
                                &&child.equals(bound.loadReceipt(bound.receiptReferenceOf(child))),
                        "zero cancellation preparation replaced a complete retained child original");
                return child;
            }).toList();
            org.xar.ck3.control.application.advance.LifeAdvanceComposite.requireZeroWriteInitializationCancellationOriginal(children.getLast(),bound);
            org.xar.ck3.control.application.advance.LifeAdvanceComposite.requireArmedInitializationWithZeroCancellationPrefix(
                    parent.command(),execution,children);
            require(parent.command().source().equals(source)
                            &&parent.command().sessionId().equals(data.capturedController().owner().sessionId())
                            &&parent.command().before().game().equals(data.capturedController().owner().game())
                            &&head.digest().equals(same.head().digest())&&clock.instant().isBefore(until),
                    "zero cancellation preparation crossed its actual source/Game/session or finite envelope");
            return null;
        });
        zeroCancellationPreparation.set(Boolean.TRUE);
        try{return work.run();}finally{zeroCancellationPreparation.remove();}
    }
    /** This optional deadline is available only inside the actual Root's canonical original ARM call. */
    Optional<Instant> originalArmReadPreparationDeadline(ContinuityStorePort.Session same,ActionReceipt original)throws IOException {
        OriginalArmReadPreparation prepared=originalArmPreparation.get();
        if(prepared==null||!prepared.child.equals(original))return Optional.empty();
        requireSession(same);
        if(prepared.session==null)prepared.session=same;
        require(prepared.session==same&&active.get()==null&&prepared.head.equals(same.head().digest())
                &&clock.instant().isBefore(prepared.deadline),"original ARM preparation escaped its actual writer/head/thread/caller envelope");
        return Optional.of(prepared.deadline);
    }

    /** No planning input, capability projection, onObserved domain hook, publication or second Native observe. */
    public <T>T withSnapshot(ContinuityStorePort.Session borrowed,Instant callerDeadline,SnapshotWork<T> work) throws IOException {
        return withSnapshot(borrowed,callerDeadline,Optional.empty(),work,freshness);
    }
    /** Only original UNKNOWN reconciliation gets a longer read-only physical lease. */
    public <T>T withReconciliationSnapshot(ContinuityStorePort.Session borrowed,Instant callerDeadline,SnapshotWork<T> work)throws IOException {
        return withSnapshot(borrowed,callerDeadline,Optional.empty(),work,Duration.ofMinutes(2));
    }
    /** Fresh SAVE reconciliation: actual independent read, never replay. */
    public <T>T withReconciliationSnapshot(ContinuityStorePort.Session borrowed,Instant callerDeadline,boolean freshRead,SnapshotWork<T> work)throws IOException {
        return withSnapshot(borrowed,callerDeadline,Optional.empty(),work,Duration.ofMinutes(2),
                freshRead ? Optional.of(transport::readFreshFullState) : Optional.empty());
    }

    <T> T withFull111EventReconciliationSnapshot(ContinuityStorePort.Session same, Instant deadline, ActionState.Attempt attempt,
            NativeActionPort.AckReceived selected, SnapshotWork<T> work) throws IOException {
        return withSnapshot(same, deadline, Optional.empty(), work, Duration.ofMinutes(2),
                Optional.of(limit -> transport.readFreshFullStateAfterFull111Selection(attempt, selected, limit)));
    }

    /** Pure custody check against the same receiver that will perform the physical read. */
    boolean canConfirmFull111EventSelection(ActionState.Attempt attempt,NativeActionPort.AckReceived selected) {
        return transport.canConfirmFull111EventSelection(attempt,selected);
    }
    /**
     * Qualifies the exact original already accepted by the same transport's bounded wait. This branch
     * neither samples nor reads Native again, and DATA equality alone never bypasses the original full qualifier.
     */
    public <T>T withReceivedSnapshot(ContinuityStorePort.Session borrowed,Instant callerDeadline,
            NativeObservationPort.ObservedFrame exactFromWait,SnapshotWork<T> work)throws IOException {
        Objects.requireNonNull(exactFromWait);Objects.requireNonNull(work);
        Instant deadline=deadline(callerDeadline);
        return withSnapshot(borrowed,deadline,Optional.of(exactFromWait),physical->{
            requireSameReceived(exactFromWait,physical.fullSnapshot().actual());
            requireSameReceived(exactFromWait,transport.currentSnapshot(deadline));
            T result=work.apply(physical);
            requireSameReceived(exactFromWait,transport.currentSnapshot(deadline));
            return result;
        },freshness);
    }
    private <T>T withSnapshot(ContinuityStorePort.Session borrowed,Instant callerDeadline,
            Optional<NativeObservationPort.ObservedFrame> received,SnapshotWork<T> work,Duration effectiveFreshness)throws IOException {
        return withSnapshot(borrowed,callerDeadline,received,work,effectiveFreshness,Optional.empty());
    }
    private <T>T withSnapshot(ContinuityStorePort.Session borrowed,Instant callerDeadline,
            Optional<NativeObservationPort.ObservedFrame> received,SnapshotWork<T> work,Duration effectiveFreshness,
            Optional<FreshSnapshotRead> freshReader)throws IOException {
        Objects.requireNonNull(work);Objects.requireNonNull(effectiveFreshness);
        require(!effectiveFreshness.isZero()&&!effectiveFreshness.isNegative()
                &&effectiveFreshness.compareTo(Duration.ofMinutes(2))<=0,"bounded physical observation window required");
        boolean freshRead = freshReader.isPresent();
        Instant deadline=deadline(callerDeadline,effectiveFreshness);Scope existing=active.get();
        if(existing!=null){
            if(freshRead) throw new IOException("fresh reconciliation read cannot borrow an existing physical scope");
            if(received.isPresent())requireSameReceived(received.orElseThrow(),existing.snapshot().fullSnapshot().actual());
            return borrowed(existing,borrowed,deadline,work);
        }
        requireSession(borrowed);String head=borrowed.head().digest();
        DriverStateAssembler actualDriver=Objects.requireNonNull(driver.resolve(borrowed),"actual adopted Driver authority is unavailable");
        OriginalArmReadPreparation prepared=originalArmPreparation.get();
        final long[] readPhases;
        if(freshRead&&prepared!=null&&prepared.session==borrowed) {
            long started=System.nanoTime();readPhases=new long[]{started,started};
        }else readPhases=null;
        synchronized(transport) {
            final NativeObservationPort.ObservedFrame actual;
            final Optional<NativeFreshSnapshotPort.Received> freshResult;
            if(received.isPresent()) {
                actual=received.orElseThrow();requireSameReceived(actual,transport.currentSnapshot(deadline));
                freshResult=Optional.empty();
            }else if(freshRead) {
                NativeFreshSnapshotPort.Result readResult;
                try { transport.awaitHello(deadline);transport.verifyHeld(deadline);readResult=freshReader.orElseThrow().read(deadline); }
                catch(InterruptedException failure){Thread.currentThread().interrupt();var interrupted=new InterruptedIOException("actual fresh reconciliation read interrupted");interrupted.initCause(failure);throw interrupted;}
                if(readResult instanceof NativeFreshSnapshotPort.Unavailable unavailable) {
                    var outcome=unavailable.dispatch();
                    if(outcome instanceof NativeActionPort.Unknown unknown) {
                        try { readResult=transport.collectFreshFullState(unknown.requestId(),deadline); }
                        catch(InterruptedException failure){Thread.currentThread().interrupt();var interrupted=new InterruptedIOException("actual fresh reconciliation collection interrupted");interrupted.initCause(failure);throw interrupted;}
                    }
                }
                if(!(readResult instanceof NativeFreshSnapshotPort.Received)) {
                    var diagnostics=transport.diagnostics();
                    require(diagnostics.receivedState()==NativeGameTransport.ReceivedState.HELLO_VERIFIED
                            && diagnostics.terminalFailure().isEmpty(),"negative fresh READ lost its actual held transport");
                    var actualOwner=diagnostics.session().orElseThrow(()->new IOException("negative fresh READ has no actual held owner"));
                    require(actualOwner.machineId().equals(source.machineId()),"negative fresh READ crossed the installed source machine");
                    var negative=verifiedNegativeFreshRead(readResult,actualOwner);
                    if(negative.isPresent()) {
                        requireSession(borrowed);require(borrowed.head().digest().equals(head),"negative fresh READ changed its original writer head");
                        var acknowledgement=negative.orElseThrow();
                        var ackRef=archive.withSession(borrowed).preserve(acknowledgement);
                        var outboundRef=preserve(borrowed,acknowledgement.outbound().orElseThrow().originalPacket(),MAX_ORIGINAL);
                        throw new NegativeFreshRead(source,actualOwner,acknowledgement.requestId(),ackRef,outboundRef);
                    }
                    throw new IOException("actual fresh reconciliation read unavailable or failed closed");
                }
                var receivedResult=(NativeFreshSnapshotPort.Received)readResult;
                actual=receivedResult.originalFrame();
                requireSameReceived(actual,transport.currentSnapshot(deadline));
                freshResult=Optional.of(receivedResult);
            }else {
                try { transport.awaitHello(deadline);transport.verifyHeld(deadline);actual=transport.observe(deadline,effectiveFreshness); }
                catch(InterruptedException failure){Thread.currentThread().interrupt();var interrupted=new InterruptedIOException("actual physical snapshot interrupted");interrupted.initCause(failure);throw interrupted;}
                catch(UncheckedIOException failure){throw failure.getCause();}
                freshResult=Optional.empty();
            }
            require(actual.session().machineId().equals(source.machineId()),"actual physical Native source machine differs");
            reportArmReadPhase(readPhases,"read_complete",actual,null);
            ExactRef packet=preserve(borrowed,actual.originalPacket(),MAX_ORIGINAL);
            return actualDriver.withFrozenRawObservation(actual,borrowed,frozen->{
                var facts=frozen.facts();var known=frozen.state();
                require(facts.source().equals(source),"physical original Driver source differs from the installed source");
                return assembler.withCapturedProjection(actual,facts,packet,full->()->{
                reportArmReadPhase(readPhases,"full_projected",actual,packet);
                var diagnostics=transport.diagnostics();
                require(diagnostics.receivedState()==NativeGameTransport.ReceivedState.HELLO_VERIFIED&&diagnostics.terminalFailure().isEmpty()
                        &&diagnostics.session().filter(actual.session()::equals).isPresent(),"actual held physical transport is unavailable");
                var hello=diagnostics.originalHello().orElseThrow(()->new IOException("actual original hello absent"));
                var heartbeat=diagnostics.latestHeartbeat().orElseThrow(()->new IOException("actual original heartbeat absent"));
                Instant now=clock.instant();
                require(!actual.observedAt().isAfter(now)&&actual.observedAt().plus(effectiveFreshness).isAfter(now)
                        &&!hello.observedAt().isAfter(actual.observedAt())&&!heartbeat.observedAt().isBefore(hello.observedAt())
                        &&!heartbeat.observedAt().isAfter(now)&&heartbeat.observedAt().plus(effectiveFreshness).isAfter(now),"physical snapshot or original heartbeat is stale/future/pre-hello");
                require(heartbeat.original().kind()==NativeWire.NoticeKind.HEARTBEAT&&hello.original().pid()==actual.session().game().pid()
                        &&hello.original().connectionGeneration().equals(actual.session().connectionGeneration())
                        &&hello.original().capabilities().contains("game.state.snapshot"),"physical hello does not bind actual Game/generation/snapshot support");
                var helloBody=RootNativeCapabilities.framedObject(hello.original().packet().value());
                require(OpportunityJson.bool(helloBody.get("ck3_build_match"),"ck3_build_match")
                        &&"ready".equals(OpportunityJson.text(helloBody.get("game_adapter_status"),"game_adapter_status")),"physical exact-build Native adapter unavailable");
                ExactRef helloRef=preserve(borrowed,hello.original().packet().value(),1<<20);
                ExactRef heartbeatRef=preserve(borrowed,heartbeat.original().packet().value(),1<<20);
                SourceQualification qualified=Objects.requireNonNull(sources.verify(borrowed,actual.session(),source,packet,diagnostics,deadline));
                qualified.assertCurrent(borrowed);
                RawJson manifest=RawJson.fullMaterial(archive.readArtifact(borrowed,facts.semanticFactsEvidence(),MAX_ORIGINAL));
                ExactRef originalDriver=DriverObservationEvidenceReader.currentDriverReference(facts.semanticFactsEvidence(),manifest);
                RawJson driverBytes=RawJson.fullMaterial(archive.readArtifact(borrowed,originalDriver,MAX_ORIGINAL));
                var decoded=DriverObservationEvidenceReader.decode(facts.semanticFactsEvidence(),manifest,driverBytes,actual);
                require(Arrays.equals(decoded.driver().encode(),known.driver().encode())&&decoded.driverVersion()==known.stamp().driverVersion()
                        &&decoded.episodeEpoch()==known.stamp().episodeEpoch()&&decoded.publicRevision().equals(facts.publicRevision())
                        &&decoded.observationVersion()==facts.observationVersion()&&decoded.source().equals(source)
                        &&decoded.originalSemanticFields().equals(facts.originalSemanticFields()),"physical manifest/full Driver producer roundtrip differs");
                reportArmReadPhase(readPhases,"manifest_driver_verified",actual,packet);
                Optional<DriverObservationAssembler.Complete> ordinary=Optional.empty();
                Optional<LifecycleIdentity> terminal=Optional.empty();
                Optional<LifecycleObservationPort.Snapshot> terminalSnapshot=Optional.empty();
                Optional<ExactRef> terminalSemantic=Optional.empty();
                var player=LifecycleOriginFactory.currentPlayer(DriverJson.object(actual.state().bytes(),DriverJson.MAX_NATIVE_BYTES));
                boolean living=player instanceof LifecycleIdentity.Character current
                        &&current.alive()&&current.characterId().equals(known.driver().session().actorId());
                if(living) {
                    var joined=assembler.assembleCapturedProjection(full,actual,facts,packet);
                    require(joined instanceof DriverObservationAssembler.Complete,"actual living physical snapshot is not a complete data join: "+joined);
                    ordinary=Optional.of((DriverObservationAssembler.Complete)joined);
                } else {
                    var projected=LifecycleOriginFactory.project(full,helloRef,originalDriver,qualified.proof());
                    require(projected instanceof LifecycleOriginFactory.Projected,"actual current-player phase is neither same living subject nor a source-bound terminal projection: "+projected);
                    var phase=(LifecycleOriginFactory.Projected)projected;
                    terminal=Optional.of(phase.identity());
                    terminalSnapshot=Optional.of(new LifecycleObservationPort.Snapshot(actual,source,phase.semantic(),known,packet));
                    terminalSemantic=Optional.of(preserve(borrowed,DriverJson.encode(phase.semantic()),MAX_ORIGINAL));
                }
                reportArmReadPhase(readPhases,living?"living_assembled":"terminal_projected",actual,packet);
                ExactRef semantic=preserve(borrowed,DriverJson.encode(full.semantic()),MAX_ORIGINAL);
                reportArmReadPhase(readPhases,"semantic_archived",actual,packet);
                Instant until=earliest(deadline,actual.observedAt().plus(effectiveFreshness),heartbeat.observedAt().plus(effectiveFreshness));
                var captured=new SnapshotLease(this,full,known,facts,ordinary,terminal,terminalSnapshot,terminalSemantic,freshResult,helloRef,heartbeatRef,
                        originalDriver,semantic,qualified,until,Set.copyOf(hello.original().capabilities()),frozen::projection);
                Scope scope=new Scope(borrowed,captured,head,deadline,heartbeat.observedAt());
                require(active.get()==null,"physical callback cannot replace another frozen observation");active.set(scope);
                try {
                    reportArmReadPhase(readPhases,"scope_enter_attempt",actual,packet);
                    return borrowed(scope,borrowed,deadline,work);
                }finally{active.remove();}
                });
            });
        }
    }

    /** Resolve only, using this actual Life definition's loader; no projection, observation, permission or Game I/O. */
    static void requireCapturedProjectionLinkage() {
        org.xar.ck3.control.application.action.ReconciliationPendingBinding.requireCanonicalHistoryBatchLinkage();
        RootDerivedChildAuthority.requireFreshBatchLinkage();
        try {
            var lookup=java.lang.invoke.MethodHandles.lookup();
            lookup.findVirtual(DriverObservationAssembler.class,"withCapturedProjection",java.lang.invoke.MethodType.methodType(
                    Object.class,NativeObservationPort.ObservedFrame.class,org.xar.ck3.control.application.driver.DriverObservationFacts.class,
                    ExactRef.class,java.util.function.Function.class));
            lookup.findVirtual(DriverObservationAssembler.class,"assembleCapturedProjection",java.lang.invoke.MethodType.methodType(
                    DriverObservationAssembler.Result.class,DriverObservationAssembler.FullSnapshot.class,NativeObservationPort.ObservedFrame.class,
                    org.xar.ck3.control.application.driver.DriverObservationFacts.class,ExactRef.class));
        }catch(NoSuchMethodException|IllegalAccessException cause){
            throw new LinkageError("actual captured projection JDK method linkage unavailable",cause);
        }
        try {
            ClassLoader life=RootLifecycleAuthority.class.getClassLoader(),projection=DriverObservationAssembler.class.getClassLoader();
            System.getLogger(RootLifecycleAuthority.class.getName()).log(System.Logger.Level.INFO,
                    "CAPTURED_PROJECTION_LINKAGE resolved life_loader="+(life==null?"bootstrap":life.getClass().getName()+"@"+Integer.toHexString(System.identityHashCode(life)))
                    +" assembler_loader="+(projection==null?"bootstrap":projection.getClass().getName()+"@"+Integer.toHexString(System.identityHashCode(projection))));
        }catch(RuntimeException|Error diagnosticUnavailable){ /* Optional output cannot replace successful resolution. */ }
    }

    /** Bounded natural diagnostics for this actual Root-owned ARM READ only; never a qualifier or a new observation. */
    private void reportArmReadPhase(long[] phases,String stage,NativeObservationPort.ObservedFrame actual,ExactRef packet) {
        if(phases==null)return;
        try {
            long now=System.nanoTime(),previous=phases[1];phases[1]=now;
            System.getLogger(RootLifecycleAuthority.class.getName()).log(System.Logger.Level.INFO,
                    "ARM_FRESH_PHASE stage="+stage+" elapsed_ns="+Math.max(0L,now-phases[0])+" stage_ns="+Math.max(0L,now-previous)
                    +" checked_at="+clock.instant()+" observed_at="+actual.observedAt()
                    +" native_packet_ref_sha256="+(packet==null?"not_yet_archived":packet.sha256()));
        }catch(RuntimeException|Error diagnosticUnavailable) { /* Only optional output is contained; all work/guards remain outside. */ }
    }

    /** The same physical producer seals and independently replays four SEM originals, without ordinary eligibility or domain hooks. */
    public SessionPorts.SemanticEvidence semantic(ContinuityStorePort.Session borrowed,SessionPorts.SessionIdentity owner,
            Instant callerDeadline)throws IOException{
        Objects.requireNonNull(owner);
        return withSnapshot(borrowed,callerDeadline,physical->semantic(borrowed,owner,physical));
    }
    /** Seals the same held physical lease; another owner, session, thread or detached lease cannot recapture or mint SEM. */
    public SessionPorts.SemanticEvidence semantic(ContinuityStorePort.Session borrowed,SessionPorts.SessionIdentity owner,
            SnapshotLease physical)throws IOException{
            Objects.requireNonNull(owner);Objects.requireNonNull(physical);physical.assertCurrent(borrowed);
            require(physical.owner==this&&active.get()!=null&&active.get().snapshot()==physical,
                    "SEM must borrow this authority's exact active original physical snapshot");
            var actual=physical.fullSnapshot().actual().session();
            require(owner.machineId().equals(actual.machineId())&&owner.game().equals(actual.game())
                    &&owner.sessionId().equals(actual.sessionId()),"physical SEM belongs to another actual owned session");
            var frame=physical.ordinary().orElseThrow(()->new IOException("actual living actor/Driver data is unavailable for ordinary SEM"));
            ExactRef stamp=preserve(borrowed,NativeDriverStamp.encode(frame,physical.factsKnown()),16<<10);
            var evidence=new SessionPorts.SemanticEvidence(frame.identity(),physical.originalSemantic(),
                    physical.fullSnapshot().originalEvidence(),stamp,physical.originalDriver(),frame.observedAt());
            semantics.verify(borrowed,owner,evidence);physical.assertCurrent(borrowed);return evidence;
    }

    /** Canonical terminal admission remains stronger than a public physical snapshot. */
    public <T>T withObserved(ContinuityStorePort.Session borrowed,Instant callerDeadline,CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(work);
        return withSnapshot(borrowed,callerDeadline,physical->{
            require(physical.terminalIdentity().isPresent(),"actual same living subject is not a terminal lifecycle origin");
            physical.assertCurrent(borrowed);
            require(physical.canonicalProjection.get() instanceof DriverStateSnapshot.Complete,
                    "original complete canonical Driver or same active terminal action is unresolved; physical data alone grants no terminal admission");
            Lease terminal=new Lease(physical);
            T result=work.apply(terminal);terminal.assertCurrent(borrowed);return result;
        });
    }

    public <T>T current(ContinuityStorePort.Session borrowed,LifecycleIdentity expected,Instant callerDeadline,CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(expected);Objects.requireNonNull(work);Instant deadline=deadline(callerDeadline);Scope scope=active.get();
        if(scope!=null)require(scope.snapshot().terminalIdentity().filter(expected::sameGuardFrame).isPresent(),"nested terminal query must retain the exact outer original frame");
        return withObserved(borrowed,deadline,actual->{
            require(expected.sameSession(actual.identity()),"terminal guard crossed the actual old episode/subject or physical session");
            return work.apply(actual);
        });
    }
    /** A domain writer must reject an enclosing observation before preview/commit, rather than detect its changed Head afterwards. */
    public void requireOutsideObservationScope(ContinuityStorePort.Session borrowed)throws IOException{
        requireSession(borrowed);
        require(active.get()==null,"domain publication must leave the actual physical observation scope before preview or commit");
        Objects.requireNonNull(driver.resolve(borrowed),"actual adopted Driver authority is unavailable").requireOutsideObservationScope(borrowed);
    }
    private <T>T borrowed(Scope scope,ContinuityStorePort.Session borrowed,Instant deadline,SnapshotWork<T> work)throws IOException{
        assertScope(scope,borrowed,deadline);T value=work.apply(scope.snapshot());assertScope(scope,borrowed,deadline);return value;
    }
    private void assertScope(Scope scope,ContinuityStorePort.Session borrowed,Instant deadline)throws IOException{
        requireSession(borrowed);require(scope.session()==borrowed&&active.get()==scope,"physical read escaped the original borrowed writer/frozen callback");
        require(scope.head().equals(borrowed.head().digest()),"writer changed inside observation-only physical scope");
        Instant now=clock.instant();require(!now.isBefore(scope.snapshot().fullSnapshot().actual().observedAt())&&now.isBefore(scope.snapshot().validUntil())
                &&now.isBefore(scope.deadline())&&now.isBefore(deadline),"actual physical lease/caller deadline expired: checked_at="+now
                +", snapshot_valid_until="+scope.snapshot().validUntil()+", scope_deadline="+scope.deadline()+", caller_deadline="+deadline
                +", observed_at="+scope.snapshot().fullSnapshot().actual().observedAt()+", heartbeat_observed_at="+scope.heartbeatObservedAt());
        transport.verifyHeld(deadline);
    }
    private void requireSession(ContinuityStorePort.Session borrowed)throws IOException{
        writer.requireSession(borrowed);borrowed.requireWriter(archive.artifactStore().originalWriterLock());
        require(borrowed.head().state().machineId().equals(source.machineId()),"physical writer/source machine differs");
    }
    private Instant deadline(Instant supplied){return deadline(supplied,freshness);}
    private Instant deadline(Instant supplied,Duration window){Objects.requireNonNull(supplied);Instant local=clock.instant().plus(window);Instant result=supplied.isBefore(local)?supplied:local;require(clock.instant().isBefore(result),"physical caller deadline expired before Native I/O");return result;}
    private ExactRef preserve(ContinuityStorePort.Session borrowed,byte[] actual,int limit)throws IOException{
        require(actual.length>0&&actual.length<=limit,"complete physical original exceeds its finite lane");
        return archive.preserveArtifact(borrowed,actual,limit);
    }
    private static Instant earliest(Instant first,Instant second,Instant third){Instant result=first.isBefore(second)?first:second;return result.isBefore(third)?result:third;}
    private void requireSameReceived(NativeObservationPort.ObservedFrame expected,NativeObservationPort.ObservedFrame current)throws IOException{
        require(expected.session().equals(current.session())&&expected.snapshotId().equals(current.snapshotId())
                &&expected.nativeRevision().equals(current.nativeRevision())&&expected.observedAt().equals(current.observedAt())
                &&expected.state().equals(current.state())&&Arrays.equals(expected.originalPacket(),current.originalPacket()),
                "received physical snapshot differs from the actual held original accepted by this transport");
        // Equal DATA cannot identify a received occurrence: A/B/A can share all values and a fixed clock.
        // Only the sole transport producer can bind expected to its actual accepted frame, and its
        // retained historical token must still identify the actual current frame at every use.
        transport.acceptedSnapshotRevision(expected).requireOriginal(current);
    }
}
