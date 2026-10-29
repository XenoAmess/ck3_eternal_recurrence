package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.NativeDriverObservationProducer;
import org.xar.ck3.control.application.effects.FrontendAuthority;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission.FrameMode;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * One held transport's actual frontend read sequence. This lives in local-service: the concrete
 * archive already depends on native-transport. No second protocol public-revision owner is created.
 */
public final class FrontendObservationSequence {
    @FunctionalInterface public interface SourceAuthority {
        SourceQualification verify(ContinuityStorePort.Session borrowed, NativeObservationPort.TransportSession actualSession,
                G2Source actualSource, ExactRef actualRoutePacket, NativeGameTransport.TransportDiagnostics received,
                Instant deadline) throws IOException;
    }
    private record Captured(FrontendAuthority.LeaseSnapshot lease, SourceQualification source, Optional<Pin> sourceProof) { }
    private static final int PACKET_LIMIT = NativeWire.MAXIMUM_FRAME_BYTES + 4;
    private final NativeGameTransport transport;
    private final NativeOutcomeArchive archive;
    private final G2Source source;
    private final RootExecutableBindings installed;
    private final List<FrontendRouteAdmission> admissions;
    private final Supplier<Optional<NativeDriverObservationProducer>> snapshotFacts;
    private NativeDriverObservationProducer acceptedSnapshotFacts;
    private final SourceAuthority sourceAuthority;
    private final Clock clock;
    private final Duration leaseTtl;
    private final Duration heartbeatMaxAge;
    private final int maximumOrigins;
    private final Map<BigInteger, FrontendIdentity> issued = new LinkedHashMap<>();
    private BigInteger querySequence = BigInteger.ZERO;
    private NativeObservationPort.TransportSession acceptedSession;
    private boolean callbackActive;
    private Captured activeRead;
    private ContinuityStorePort.Session activeReadSession;
    private String activeReadHead;

    public FrontendObservationSequence(NativeGameTransport sameTransport, NativeOutcomeArchive sameArchive,
            G2Source actualSource, RootExecutableBindings sameInstalled, List<FrontendRouteAdmission> routeAdmissions,
            Supplier<Optional<NativeDriverObservationProducer>> sameSnapshotFacts, SourceAuthority sameSourceAuthority, Clock clock, Duration leaseTtl,
            Duration heartbeatMaxAge, int maximumOrigins) {
        transport = Objects.requireNonNull(sameTransport); archive = Objects.requireNonNull(sameArchive);
        source = Objects.requireNonNull(actualSource); installed = Objects.requireNonNull(sameInstalled);
        admissions = List.copyOf(routeAdmissions); snapshotFacts = Objects.requireNonNull(sameSnapshotFacts);
        sourceAuthority = Objects.requireNonNull(sameSourceAuthority);
        this.clock = Objects.requireNonNull(clock); this.leaseTtl = finite(leaseTtl, Duration.ofSeconds(30));
        this.heartbeatMaxAge = finite(heartbeatMaxAge, Duration.ofMinutes(1)); this.maximumOrigins = maximumOrigins;
        StrictJson.require(installed.frozen() && maximumOrigins >= 1 && maximumOrigins <= 65_536,
                "one frozen Root registry and finite frontend origin custody required");
        StrictJson.require(admissions.size() <= 4096, "bounded explicit frontend route admission list required");
        var unique = new HashSet<OperationKey>();
        for (FrontendRouteAdmission admission : admissions)
            StrictJson.require(unique.add(admission.operation()), "duplicate frontend route admission");
    }

    /** Detached facts only. The actual guard must enter NativeFrontendAuthority.current. */
    public synchronized FrontendAuthority.LeaseSnapshot observeMenu(ContinuityStorePort.Session session,
            Instant deadline) throws IOException {
        return observe(session, FrameMode.MENU, deadline).lease();
    }

    /** Uses the same Driver public-revision producer as gameplay; absence never becomes a guessed revision. */
    public synchronized FrontendAuthority.LeaseSnapshot observeSnapshot(ContinuityStorePort.Session session,
            Instant deadline) throws IOException {
        return observe(session, FrameMode.SNAPSHOT, deadline).lease();
    }

    /** One real route/source observation covers the entire read consumer and both of its native read guards. */
    public synchronized <T> T withSourceBoundFrontendRead(ContinuityStorePort.Session session, FrameMode mode,
            Instant deadline, FrontendAuthority.CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(work); Objects.requireNonNull(mode); Objects.requireNonNull(deadline);
        if (activeRead != null) {
            boolean menu = activeRead.lease().identity().frame() instanceof FrontendFrame.Menu;
            StrictJson.require(menu ? mode == FrameMode.MENU : mode == FrameMode.SNAPSHOT,
                    "nested frontend read cannot change its actual held frame mode");
            return borrowedRead(session, activeRead.lease().identity(), deadline, work);
        }
        requireIdle(); requireSession(session);
        synchronized (transport) {
            Captured captured = observe(session, mode, deadline);
            String head = session.head().digest();
            activeRead = captured; activeReadSession = session; activeReadHead = head; callbackActive = true;
            try { return borrowedRead(session, captured.lease().identity(), deadline, work); }
            finally { activeRead = null; activeReadSession = null; activeReadHead = null; callbackActive = false; }
        }
    }

    /** Root's actual menu action facade checks this before any canonical intent or submission. */
    public synchronized void requireOutsideSourceBoundFrontendRead() {
        StrictJson.require(activeRead == null, "frontend action cannot execute inside the source-bound read scope");
    }

    /** The continuation verifier must prove the original live scope, never invoke an observation fallback. */
    public synchronized <T> T currentSourceBoundRead(ContinuityStorePort.Session session, FrontendIdentity expected,
            Instant deadline, FrontendAuthority.CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(expected); Objects.requireNonNull(deadline); Objects.requireNonNull(work);
        if (activeRead == null) throw new IOException("actual source-bound frontend read scope is not active");
        return borrowedRead(session, expected, deadline, work);
    }

    private <T> T borrowedRead(ContinuityStorePort.Session session, FrontendIdentity expected, Instant deadline,
            FrontendAuthority.CheckedWork<T> work) throws IOException {
        requireSession(session);
        StrictJson.require(activeRead != null && activeReadSession == session,
                "frontend read requires its identical actual writer scope");
        FrontendIdentity original = issued.get(expected.frame().querySequence());
        StrictJson.require(expected.equals(original) && expected.sameGuardFrame(activeRead.lease().identity()),
                "frontend read changed the actual issued process, connection or snapshot");
        requireReadCurrent(session, deadline);
        T result = work.apply(activeRead.lease());
        requireReadCurrent(session, deadline);
        return result;
    }
    private void requireReadCurrent(ContinuityStorePort.Session session, Instant deadline) throws IOException {
        StrictJson.require(activeReadSession == session && activeReadHead.equals(session.head().digest()),
                "frontend read changed its original writer head");
        StrictJson.require(clock.instant().isBefore(deadline), "frontend caller deadline expired inside the original read");
        requireCurrentTime(activeRead.lease()); transport.verifyHeld(deadline);
        activeRead.source().assertCurrent(session); if(activeRead.sourceProof().isPresent())session.verifyPin(activeRead.sourceProof().orElseThrow());
        requireCurrentTime(activeRead.lease());
    }

    synchronized <T> T current(ContinuityStorePort.Session session, FrontendIdentity expected,
            Instant deadline, FrontendAuthority.CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(expected); Objects.requireNonNull(work);
        if (activeRead != null) return borrowedRead(session, expected, deadline, work);
        requireIdle(); requireSession(session);
        FrontendIdentity original = issued.get(expected.frame().querySequence());
        StrictJson.require(expected.equals(original), "frontend identity was not produced by this held observation sequence");
        synchronized (transport) {
            var captured = observe(session, expected.frame() instanceof FrontendFrame.Menu ? FrameMode.MENU : FrameMode.SNAPSHOT, deadline);
            var actual = captured.lease();
            StrictJson.require(expected.sameGuardFrame(actual.identity()), "frontend guard changed the actual process, connection or snapshot");
            captured.source().assertCurrent(session); if(captured.sourceProof().isPresent())session.verifyPin(captured.sourceProof().orElseThrow());
            transport.verifyHeld(deadline); requireCurrentTime(actual);
            callbackActive = true;
            try {
                T result = work.apply(actual);
                requireSession(session); transport.verifyHeld(deadline); requireCurrentTime(actual);
                captured.source().assertCurrent(session); if(captured.sourceProof().isPresent())session.verifyPin(captured.sourceProof().orElseThrow());
                return result;
            } finally { callbackActive = false; }
        }
    }

    private Captured observe(ContinuityStorePort.Session session, FrameMode mode,
            Instant deadline) throws IOException {
        requireIdle(); requireSession(session); Objects.requireNonNull(mode); Objects.requireNonNull(deadline);
        StrictJson.require(issued.size() < maximumOrigins && querySequence.compareTo(StrictJson.UINT64_MAX) < 0,
                "frontend origin custody is full; do not evict identities or reset an active connection");
        StrictJson.require(clock.instant().isBefore(deadline), "frontend observation deadline expired");
        synchronized (transport) {
            NativeObservationPort.TransportSession actualSession;
            NativeActionPort.DispatchOutcome outcome;
            try {
                actualSession = transport.awaitHello(deadline); transport.verifyHeld(deadline);
                outcome = transport.readFrontendRoute(deadline);
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                var failure = new InterruptedIOException("frontend read interrupted; original request must never be replayed");
                failure.initCause(interrupted); throw failure;
            }
            if (acceptedSession == null) acceptedSession = actualSession;
            StrictJson.require(acceptedSession.equals(actualSession) && actualSession.machineId().equals(source.machineId()),
                    "frontend source or held connection changed; no implicit reconnect");
            var diagnostic = transport.diagnostics();
            StrictJson.require(diagnostic.receivedState() == NativeGameTransport.ReceivedState.HELLO_VERIFIED
                    && diagnostic.session().filter(actualSession::equals).isPresent(), "held frontend transport is unavailable");
            var hello = diagnostic.originalHello().orElseThrow(() -> new IOException("original frontend hello unavailable"));
            var heartbeat = diagnostic.latestHeartbeat().orElseThrow(() -> new IOException("actual frontend heartbeat unavailable"));
            StrictJson.require(heartbeat.original().kind() == NativeWire.NoticeKind.HEARTBEAT,
                    "actual heartbeat frame required");
            // Preserve every returned branch before deciding whether it can be an observation.
            var bound = archive.withSession(session); ExactRef outcomeRef = bound.preserve(outcome);
            StrictJson.require(outcome.equals(bound.load(outcomeRef)), "frontend route outcome archive changed");
            if (!(outcome instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk())
                throw new IOException("frontend route has no successful original query result; archived outcome=" + outcomeRef.path());
            BigInteger next = querySequence.add(BigInteger.ONE);
            var rawHello = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.original().packet().value(), 4,
                    hello.original().packet().value().length)));
            var exactBuild = FrontendRulesData.Build.require(NativeWire.text(rawHello.get("expected_ck3_version")), hello.original().gameSha256());
            var nativeSource = new FrontendRulesData.Source(new FrontendRulesData.Binding(hello.original().pid(),
                    hello.original().connectionGeneration()), exactBuild);
            var route = FrontendRulesCodec.route(ack.originalResultToken().orElseThrow(() -> new IOException("frontend route token missing")), nativeSource, next);
            StrictJson.require(route.route() != FrontendRulesData.Route.UNAVAILABLE, "actual native frontend route is unavailable");
            Instant observedAt = clock.instant();
            StrictJson.require(!observedAt.isBefore(hello.observedAt()) && !observedAt.isBefore(heartbeat.observedAt()),
                    "frontend observation clock precedes actual received originals");
            Instant validUntil = earliest(deadline, observedAt.plus(leaseTtl), heartbeat.observedAt().plus(heartbeatMaxAge));
            StrictJson.require(observedAt.isBefore(validUntil), "actual frontend heartbeat or observation lease is stale");
            ExactRef routePacket = preserveExact(session, ack.originalPacket());
            ExactRef helloPacket = preserveExact(session, hello.original().packet().value());
            ExactRef heartbeatPacket = preserveExact(session, heartbeat.original().packet().value());
            SourceQualification qualified = Objects.requireNonNull(sourceAuthority.verify(session, actualSession, source,
                    routePacket, diagnostic, deadline), "actual frontend source authority returned no qualification");
            qualified.assertCurrent(session);
            Optional<Pin> sourceProof = Optional.empty();
            if(qualified.proof().isPresent()) {
                Pin actualProof=session.capturePin(qualified.proof().orElseThrow(),16<<20);
                session.verifyPin(actualProof);sourceProof=Optional.of(actualProof);
            }
            FrontendFrame frame;
            List<ExactRef> supporting;
            if (mode == FrameMode.MENU) { frame = new FrontendFrame.Menu(next); supporting = qualified.proof().stream().toList(); }
            else {
                var actual = transport.latestObservedSnapshot().orElseThrow(() -> new IOException("actual frontend snapshot unavailable"));
                StrictJson.require(actual.session().equals(actualSession), "frontend snapshot belongs to another held session");
                var state = DriverJson.object(actual.state().bytes(), DriverJson.MAX_NATIVE_BYTES);
                StrictJson.require(nullOrMissing(state, "played_character") && nullOrMissing(state, "episode_run_id"),
                        "frontend snapshot cannot borrow an actual gameplay actor or episode");
                var producer = Objects.requireNonNull(snapshotFacts.get(), "actual context Driver lookup cannot return null")
                        .orElseThrow(() -> new IOException("the same actual Driver public-revision producer is not yet adopted"));
                producer.requireSameTransport(transport, source);
                if (acceptedSnapshotFacts == null) acceptedSnapshotFacts = producer;
                StrictJson.require(acceptedSnapshotFacts == producer, "one held frontend sequence cannot switch its actual Driver revision producer");
                var result = producer.read(actual);
                if (!(result instanceof DriverObservationFacts.Known known))
                    throw new IOException("actual frontend public-revision facts unavailable: " + ((DriverObservationFacts.Unavailable) result).reasons());
                var facts = known.facts();
                StrictJson.require(facts.source().equals(source) && facts.transport().equals(actualSession)
                        && facts.snapshotId().equals(actual.snapshotId()) && facts.nativeRevision().equals(actual.nativeRevision()),
                        "frontend public revision crossed the real source, snapshot or native session");
                ExactRef nativePacket = preserveExact(session, actual.originalPacket());
                ExactRef manifestRef = facts.semanticFactsEvidence();
                RawJson manifest = new RawJson(archive.readArtifact(session, manifestRef, RawJson.MAXIMUM_BYTES));
                ExactRef driverRef = DriverObservationEvidenceReader.currentDriverReference(manifestRef, manifest);
                RawJson driver = new RawJson(archive.readArtifact(session, driverRef, RawJson.MAXIMUM_BYTES));
                var decoded = DriverObservationEvidenceReader.decode(manifestRef, manifest, driver, actual);
                StrictJson.require(Arrays.equals(facts.driver().encode(), decoded.driver().encode())
                        && facts.driverVersion() == decoded.driverVersion() && facts.episodeEpoch() == decoded.episodeEpoch()
                        && facts.publicRevision().equals(decoded.publicRevision()) && facts.observationVersion() == decoded.observationVersion()
                        && facts.source().equals(decoded.source()) && facts.originalSemanticFields().equals(decoded.originalSemanticFields()),
                        "archived frontend public-revision facts differ from the actual shared producer");
                long date = OpportunityJson.integer(state.get("date_raw"), "date_raw").longValueExact();
                frame = new FrontendFrame.Snapshot(actual.snapshotId(), facts.publicRevision(), actual.nativeRevision(), date, next);
                supporting = java.util.stream.Stream.concat(List.of(manifestRef, driverRef, nativePacket).stream(),qualified.proof().stream()).toList();
            }
            Set<OperationKey> operations = new HashSet<>(); Set<String> caps = Set.copyOf(hello.original().capabilities());
            for (FrontendRouteAdmission admission : admissions) {
                if (admission.frameMode() != mode || !admission.routes().contains(route.route())) continue;
                var step = installed.resolve(admission.operation(), ReadContract.GuardMode.FRONTEND_SESSION).orElseThrow(() -> new IOException("frontend route admission has no actual Root callable"));
                StrictJson.require(step.guardMode() == ReadContract.GuardMode.FRONTEND_SESSION,
                        "frontend route admission crossed the actual Root guard mode");
                pin(session, admission.source()); pin(session, step.implementationSource()); pin(session, step.decoderSource());
                if (step.requiredCapability().isPresent() && !caps.contains(step.requiredCapability().orElseThrow())) continue;
                operations.add(admission.operation());
            }
            var identity = new FrontendIdentity(actualSession.machineId(), actualSession.game(), actualSession.sessionId(),
                    actualSession.connectionGeneration(), hello.original().pid(), frame, routePacket, helloPacket);
            var lease = new FrontendAuthority.LeaseSnapshot(identity, source, ack, heartbeatPacket, operations, caps,
                    observedAt, validUntil, supporting);
            requireSession(session); transport.verifyHeld(deadline); requireCurrentTime(lease);
            qualified.assertCurrent(session); if(sourceProof.isPresent())session.verifyPin(sourceProof.orElseThrow());
            requireCurrentTime(lease);
            querySequence = next; issued.put(next, identity); return new Captured(lease, qualified, sourceProof);
        }
    }

    private void requireSession(ContinuityStorePort.Session session) throws IOException {
        Objects.requireNonNull(session); archive.writer().requireSession(session);
        session.requireWriter(archive.artifactStore().originalWriterLock());
        StrictJson.require(session.head().state().machineId().equals(source.machineId()), "frontend borrowed writer machine differs");
        pin(session, source.sourceRef());
    }
    private static void pin(ContinuityStorePort.Session session, ExactRef ref) throws IOException {
        StrictJson.require(ref.bytes() > 0 && java.nio.file.Path.of(ref.path()).isAbsolute(), "actual absolute frontend source required");
        var pin = session.capturePin(ref, RawJson.MAXIMUM_BYTES); session.verifyPin(pin);
    }
    private ExactRef preserveExact(ContinuityStorePort.Session session, byte[] bytes) throws IOException {
        ExactRef ref = archive.preserveArtifact(session, bytes, PACKET_LIMIT);
        StrictJson.require(Arrays.equals(bytes, archive.readArtifact(session, ref, PACKET_LIMIT)), "frontend original packet readback changed");
        return ref;
    }
    private void requireIdle() { StrictJson.require(!callbackActive, "a live frontend authority callback cannot recursively refresh its evidence"); }
    private void requireCurrentTime(FrontendAuthority.LeaseSnapshot lease) {
        Instant now = clock.instant(); StrictJson.require(!now.isBefore(lease.observedAt()) && now.isBefore(lease.validUntil()), "frontend live callback lease expired");
    }
    private static boolean nullOrMissing(OpportunityJson.Obj row, String key) {
        return !row.members().containsKey(key) || row.get(key) == OpportunityJson.Nil.INSTANCE;
    }
    private static Duration finite(Duration actual, Duration maximum) {
        Objects.requireNonNull(actual); StrictJson.require(!actual.isZero() && !actual.isNegative() && actual.compareTo(maximum) <= 0,
                "positive finite frontend lease duration required"); return actual;
    }
    private static Instant earliest(Instant first, Instant second, Instant third) {
        Instant pair = first.isBefore(second) ? first : second; return pair.isBefore(third) ? pair : third;
    }
}
