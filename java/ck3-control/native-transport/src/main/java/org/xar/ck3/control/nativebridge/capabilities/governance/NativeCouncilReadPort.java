package org.xar.ck3.control.nativebridge.capabilities.governance;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.governance.CouncilSelection;
import org.xar.ck3.control.application.planning.governance.CouncilTechnicalReadFailure;
import org.xar.ck3.control.application.planning.governance.GovernanceCouncilSupplier;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Council mailbox read closure under the original writer Session, then the one native transport monitor. */
public final class NativeCouncilReadPort implements GovernanceCouncilSupplier.CouncilReadPort {
    /** Pure original-read decoding inputs. They grant no Session, mailbox or submit authority. */
    public record ReplayConfiguration(PrivateCouncilReads definitions, int maximumStatusPolls, String connectedVersion, String connectedSha256) {
        public ReplayConfiguration {
            Objects.requireNonNull(definitions);
            StrictJson.require(maximumStatusPolls > 0 && maximumStatusPolls <= 3000, "bounded original Council status group required");
            CouncilCodec.requireBuild(connectedVersion, connectedSha256);
        }
    }
    @FunctionalInterface public interface SessionWork<T> {
        T run(ContinuityStorePort.Session borrowed) throws IOException, InterruptedException;
    }
    /** Root supplies an already held original session; this adapter never opens a writer lock or constructs a Session. */
    public interface SessionAccess {
        <T> T withSession(PlanningRequest request, SessionWork<T> work) throws IOException, InterruptedException;
    }
    private final PlanningReadPort reads;
    private final GovernanceNativeReads publicReads;
    private final PrivateCouncilReads privateReads;
    private final NativeGameTransport transport;
    private final SessionAccess sessions;
    private final Path originalWriterLock;
    private final ActionPorts.OutcomeArchive archive;
    private final Clock clock;
    private final int maximumStatusPolls;
    private final String connectedVersion;
    private final String connectedSha256;
    private final ReplayConfiguration replayConfiguration;
    public NativeCouncilReadPort(PlanningReadPort reads, GovernanceNativeReads publicReads, PrivateCouncilReads privateReads,
            NativeGameTransport transport, SessionAccess sessions, Path originalWriterLock, ActionPorts.OutcomeArchive archive,
            Clock clock, int maximumStatusPolls, String connectedVersion, String connectedSha256) {
        this.reads = Objects.requireNonNull(reads); this.publicReads = Objects.requireNonNull(publicReads); this.privateReads = Objects.requireNonNull(privateReads);
        this.transport = Objects.requireNonNull(transport); this.sessions = Objects.requireNonNull(sessions); this.originalWriterLock = Objects.requireNonNull(originalWriterLock);
        this.archive = Objects.requireNonNull(archive); this.clock = Objects.requireNonNull(clock);
        StrictJson.require(originalWriterLock.isAbsolute() && maximumStatusPolls > 0 && maximumStatusPolls <= 3000, "Council requires original absolute writer lock and bounded status polls");
        this.maximumStatusPolls = maximumStatusPolls; CouncilCodec.requireBuild(connectedVersion, connectedSha256);
        this.connectedVersion = connectedVersion; this.connectedSha256 = connectedSha256;
        this.replayConfiguration = new ReplayConfiguration(privateReads, maximumStatusPolls, connectedVersion, connectedSha256);
    }
    @Override public Read<CouncilSelection.Query> readPrivate(PlanningRequest request, CouncilSelection.Position position) {
        Objects.requireNonNull(request); Objects.requireNonNull(position);
        try {
            return sessions.withSession(request, borrowed -> {
                borrowed.requireWriter(originalWriterLock);
                try {
                    return transport.withMailbox(request.deadline(), scope -> privateHeld(borrowed, request, position, scope));
                } finally { borrowed.requireWriter(originalWriterLock); }
            });
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt(); return new Unavailable<>("Council mailbox interrupted; original operation is never replayed");
        } catch (IOException | RuntimeException failure) {
            return new Unavailable<>(bounded(failure));
        }
    }
    private Read<CouncilSelection.Query> privateHeld(ContinuityStorePort.Session borrowed, PlanningRequest request,
            CouncilSelection.Position role, NativeGameTransport.MailboxScope scope) throws IOException, InterruptedException {
        List<ExactRef> originals = new ArrayList<>(); var originalReads = new ArrayList<PlanningReadReceipt>();
        var firstRequest = query(request, privateReads.gates(), new Obj(Map.of()).with("position_key", new Text(role.key())));
        PlanningReadRequest currentRequest = firstRequest;
        PlanningReadResult<CouncilPrivateCodec.Reply> current = reads.read(borrowed, privateReads.gates(), currentRequest);
        boolean pendingObserved = false;
        for (int polls = 0; ; polls++) {
            if (current instanceof PlanningReadResult.Unavailable<CouncilPrivateCodec.Reply> unavailable) {
                boolean completed = false;
                if (unavailable.original().isPresent()) {
                    NativeActionPort.DispatchOutcome original = unavailable.original().orElseThrow();
                    archive.inSession(borrowed, bound -> bound.preserve(original));
                    // A negative initial command_result has not queued a mailbox operation. A later failure is unresolved.
                    if (!pendingObserved && original instanceof NativeActionPort.AckReceived ack && !ack.nativeOk()) {
                        scope.complete(original); completed = true;
                    }
                }
                var failedRequest = currentRequest;
                Optional<CouncilTechnicalReadFailure> technical = archive.inSession(borrowed, bound -> CouncilTechnicalReadFailures.observe(
                        unavailable, failedRequest, firstRequest, role, originalReads, replayConfiguration, bound));
                if (technical.isPresent() && !completed) {
                    var bound = archive.withSession(borrowed);
                    scope.deferReadOnly(unavailable.observedFailure().orElseThrow(),
                            CouncilTechnicalReadFailures.failedReadReference(technical.orElseThrow().diagnostic(), bound), bound);
                }
                return new Unavailable<>("Council mailbox unavailable: " + unavailable.reason(), technical);
            }
            var known = (PlanningReadResult.Known<CouncilPrivateCodec.Reply>) current;
            originals.add(known.originalReceipt());
            originalReads.add(known.receipt());
            if (known.value() instanceof CouncilPrivateCodec.Terminal terminal) {
                GovernanceReadChronology.requireOrderedReads(originalReads);
                var nativeFrame = PrivateCouncilReads.nativeFrame(firstRequest);
                CouncilPrivateCodec.requireTerminalBinding(terminal, CouncilPrivateCodec.GATES, nativeFrame);
                // This exact ACK has already been archived by PlanningReadCoordinator. No fabricated query/status join.
                scope.complete(known.receipt().original());
                var normalized = CouncilPrivateCodec.normalize(terminal, CouncilPrivateCodec.GATES, nativeFrame,
                        GovernanceNativeReads.frame(firstRequest), CouncilModels.Position.exact(role.key()), connectedVersion, connectedSha256);
                return new Known<>(CouncilSelection.decode(request, role, object(parse(normalized.bytes()), "normalized actual Council query")), originals);
            }
            pendingObserved = true;
            if (polls >= maximumStatusPolls || !clock.instant().isBefore(request.deadline()))
                throw new IOException("Council mailbox terminal result unconfirmed; pending operation is never requeued");
            pauseBeforeStatus(request);
            currentRequest = query(request, privateReads.status(), new Obj(Map.of()));
            current = reads.read(borrowed, privateReads.status(), currentRequest);
        }
    }
    @Override public Read<CouncilSelection.Query> readCore(PlanningRequest request) {
        Objects.requireNonNull(request);
        try {
            return sessions.withSession(request, borrowed -> {
                borrowed.requireWriter(originalWriterLock);
                try {
                    PlanningReadResult<CouncilModels.Candidates> result = reads.read(borrowed, publicReads.council(), query(request, publicReads.council(), new Obj(Map.of())));
                    if (result instanceof PlanningReadResult.Known<CouncilModels.Candidates> known) {
                        GovernanceReadChronology.requireOrderedReads(List.of(known.receipt()));
                        return new Known<>(CouncilSelection.fromComposition(request, known.value()), List.of(known.originalReceipt()));
                    }
                    var unavailable = (PlanningReadResult.Unavailable<CouncilModels.Candidates>) result;
                    unavailable.original().ifPresent(original -> archive.inSession(borrowed, bound -> bound.preserve(original)));
                    return new Unavailable<CouncilSelection.Query>("public Council read unavailable: " + unavailable.reason());
                } finally { borrowed.requireWriter(originalWriterLock); }
            });
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt(); return new Unavailable<>("public Council read interrupted");
        } catch (IOException | RuntimeException failure) { return new Unavailable<>(bounded(failure)); }
    }
    /** Pure archived failure replay using this installed port's exact decoding configuration; no Session or native I/O. */
    public CouncilTechnicalReadFailure replayTechnicalReadFailure(ExactRef diagnostic, ActionPorts.OutcomeArchive bound) {
        return CouncilTechnicalReadFailures.replay(diagnostic, replayConfiguration, bound);
    }
    /** Pure replay of one already archived read closure; never opens the mailbox or issues a request. */
    public CouncilSelection.Query replayPrivate(List<PlanningReadReceipt> originalReads,CouncilSelection.Position role) {
        return replayPrivateOriginals(originalReads,role,replayConfiguration);
    }
    /** The identical production replay body, callable before any live Game/transport is installed. */
    public static CouncilSelection.Query replayPrivateOriginals(List<PlanningReadReceipt> originalReads,CouncilSelection.Position role,
            ReplayConfiguration configuration) {
        Objects.requireNonNull(role);Objects.requireNonNull(configuration);
        var privateReads=configuration.definitions();
        originalReads=List.copyOf(originalReads);StrictJson.require(!originalReads.isEmpty()&&originalReads.size()<=configuration.maximumStatusPolls()+1,"complete bounded original Council read chain required");
        GovernanceReadChronology.requireOrderedReads(originalReads);
        var first=originalReads.getFirst();var expected=first.request();CouncilPrivateCodec.Terminal terminal=null;
        StrictJson.require(expected.arguments().equals(new Obj(Map.of()).with("position_key",new Text(role.key()))),"original Council role or query fields differ from following receipt consumption");
        for(int index=0;index<originalReads.size();index++) {
            var read=originalReads.get(index);ReadContract<CouncilPrivateCodec.Reply> contract=index==0?privateReads.gates():privateReads.status();
            StrictJson.require(read.contractId().equals(contract.contractId())&&read.request().operation().equals(contract.operation())
                    &&read.request().before().equals(expected.before())&&read.request().source().equals(expected.source())&&read.request().sessionId().equals(expected.sessionId())
                    &&(index==0||read.request().arguments().equals(new Obj(Map.of()))),"original Council query/status closure crossed its contract/frame/source/session");
            var decoded=contract.decode(read);
            if(decoded instanceof CouncilPrivateCodec.Terminal observed) {StrictJson.require(index==originalReads.size()-1,"Council chain dispatch continued after terminal result");terminal=observed;}
            else StrictJson.require(index<originalReads.size()-1,"Council final status still pending");
        }
        StrictJson.require(terminal!=null,"Council native terminal result missing");
        var nativeFrame=PrivateCouncilReads.nativeFrame(expected);
        var normalized=CouncilPrivateCodec.normalize(terminal,CouncilPrivateCodec.GATES,nativeFrame,GovernanceNativeReads.frame(expected),
                CouncilModels.Position.exact(role.key()),configuration.connectedVersion(),configuration.connectedSha256());
        return CouncilSelection.decodeObserved(expected.before(),role,object(parse(normalized.bytes()),"original normalized Council read"));
    }
    private static PlanningReadRequest query(PlanningRequest request, ReadContract<?> contract, OpportunityJson.Obj arguments) {
        return new PlanningReadRequest(request.before(), request.source(), request.sessionId(), contract.operation(), arguments, request.deadline());
    }
    private void pauseBeforeStatus(PlanningRequest request) throws IOException, InterruptedException {
        Duration remaining = Duration.between(clock.instant(), request.deadline());
        if (remaining.isNegative() || remaining.isZero()) throw new IOException("Council mailbox deadline passed before STATUS");
        long nanos = Math.min(10_000_000L, remaining.toNanos());
        Thread.sleep(nanos / 1_000_000L, (int) (nanos % 1_000_000L));
    }
    private static String bounded(Throwable failure) {
        String message = failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage());
        return message.length() <= 2048 ? message : message.substring(0, 2048);
    }
}
