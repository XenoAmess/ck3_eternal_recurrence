package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.NativeActionPort.DispatchOutcome;
import org.xar.ck3.control.application.action.NativeActionPort.RejectedBeforeDispatch;
import org.xar.ck3.control.application.action.NativeActionPort.Unknown;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111EventObservation;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111EventRead;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111RenderedOption;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111RendererObservation;
import org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.semantic.NativeFull111OrdinaryEvent;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.CurrentFull111EventRenderer;
import org.xar.ck3.control.nativebridge.CurrentLyd;
import org.xar.ck3.control.nativebridge.CurrentLydResult;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeGameTransport.AcceptedSnapshotRevision;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Optional Full111 foreground evidence for the ordinary diagnostic. */
final class RootFull111EventRead implements Full111EventRead {
    private static final BigInteger MIN_INT = BigInteger.valueOf(Integer.MIN_VALUE);
    private static final BigInteger MAX_INT = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final System.Logger LOG = System.getLogger(RootFull111EventRead.class.getName());
    private final RootRuntimeContext context;
    private String lastRendererRefusal;
    private final NativeGameTransport transport;
    private final HeldReadMemo reads = new HeldReadMemo();

    RootFull111EventRead(RootRuntimeContext context, NativeGameTransport transport) {
        this.context = Objects.requireNonNull(context);
        this.transport = Objects.requireNonNull(transport);
    }

    void release(ExactRef originalRenderer) { reads.release(originalRenderer); }

    @Override public Optional<Full111EventObservation> observe(PlanningRequest actual, NativeFull111OrdinaryEvent foreground) {
        var caps = actual.observations().bridgeCapabilities();
        if (!caps.contains(CoreFrame.CAPABILITY) || !(caps.contains(CurrentFull111EventRenderer.CAPABILITY)
                || caps.contains(CurrentLyd.Action.QUERY_EVENTS.capability()))) return Optional.empty();
        try {
            Session same = context.borrowedSession();
            context.writer().requireSession(same);
            return context.collector().borrowCurrent(same, actual.before(), actual.deadline(),
                    lease -> read(same, actual, lease, foreground));
        } catch (IOException | UncheckedIOException | ContractViolationException unavailable) {
            return Optional.empty();
        }
    }

    private Optional<Full111EventObservation> read(Session same, PlanningRequest actual, LeaseSnapshot lease,
            NativeFull111OrdinaryEvent foreground) throws IOException {
        var frame = lease.frame();
        var caps = lease.bridgeCapabilities();
        boolean canRender = caps.contains(CurrentFull111EventRenderer.CAPABILITY);
        boolean canReadLyd = caps.contains(CurrentLyd.Action.QUERY_EVENTS.capability());
        if (!actual.source().equals(frame.source()) || !actual.sessionId().equals(frame.sessionId())
                || !actual.observations().snapshot().equals(frame.semantic())
                || !caps.contains(CoreFrame.CAPABILITY) || !(canRender || canReadLyd))
            return Optional.empty();
        var originals = lease.semantic();
        var full = context.collector().activeOriginalNativeFrame(same, lease);
        var bound = originals.originalNativePacket();
        if (!originals.frame().equals(frame.identity()) || !bound.equals(frame.originalEvidence()))
            return Optional.empty();
        Instant deadline = earlier(actual.deadline(), lease.validUntil());
        var accepted = transport.acceptedSnapshotRevision(full);
        accepted.requireOriginal(transport.currentSnapshot(deadline));
        Instant now = context.clock().instant();
        if (!now.isBefore(deadline)) return Optional.empty();
        var subject = new ReadSubject(accepted, frame.identity(), frame.source(), bound, originals.semantic(), foreground);
        EventReadAttempt original = () -> query(same, full, subject, canRender, canReadLyd, deadline);
        if (!canRender) {
            recordRendererRefusal(subject, "actual HELLO does not advertise the Full111 renderer", Optional.empty());
            return reads.observe(subject, now, original);
        }
        return reads.observe(subject, now, original, base -> {
            var basis = base.rendererBasis().orElseThrow();
            return renderer(same, subject, basis.core(), basis.lyd(), Optional.of(base.evidence().definitionKey()), deadline)
                    .map(RenderedEvent::observation);
        });
    }

    private Optional<VerifiedRead> query(Session same, ObservedFrame full, ReadSubject subject, boolean canRender,
            boolean canReadLyd, Instant deadline) throws IOException {
        var raw = NativeWire.object(NativeWire.parse(full.state().bytes()));
        byte[] packet = full.originalPacket();
        if (subject.full().bytes() != packet.length || !subject.full().sha256().equals(ActionCodec.sha256(packet))
                || NativeFull111OrdinaryEvent.read(raw).filter(subject.foreground()::equals).isEmpty())
            return Optional.empty();
        var accepted = subject.occurrence();

        try {
            if (!(transport.readCoreFrameReceived(deadline) instanceof NativeGameTransport.CoreReceived core)
                    || !(core.frame() instanceof CoreFrame.Partial partial)
                    || !partial.prefix().equals(prefix(raw)))
                return Optional.empty();
            var coreCustody = core.original().custody().orElseThrow(() -> new IOException("Original Full111 Core read custody is missing"));
            if (!accepted.session().equals(coreCustody.session())
                    || coreCustody.writeEntered().order().compareTo(accepted.received().order()) <= 0)
                return Optional.empty();
            accepted.requireOriginal(transport.currentSnapshot(deadline));
            var archive = context.archive().withSession(same);
            if (canRender) {
                var direct = renderer(same, subject, core, core.original(), Optional.empty(), deadline);
                if (direct.isPresent()) {
                    var observed = direct.orElseThrow();
                    var evidence = new Full111EventObservation(subject.foreground().instanceId(), observed.definitionKey(),
                            subject.full(), subject.semantic(), archive.preserve(core.original()),
                            Optional.empty(), Optional.of(observed.observation()));
                    return Optional.of(new VerifiedRead(core.validUntil(), evidence));
                }
            }
            if (!canReadLyd || Thread.currentThread().isInterrupted()) return Optional.empty();
            if (!(transport.readFull111OrdinaryEvents(core, deadline) instanceof AckReceived ack) || !ack.nativeOk())
                return Optional.empty();
            accepted.requireOriginal(transport.currentSnapshot(deadline));
            var key = foregroundDefinition(core.original(), partial.prefix(), ack, subject.foreground());
            if (key.isEmpty()) return Optional.empty();

            var evidence = new Full111EventObservation(subject.foreground().instanceId(), key.orElseThrow(),
                    subject.full(), subject.semantic(), archive.preserve(core.original()), archive.preserve(ack));
            var renderBasis = canRender ? Optional.of(new RendererBasis(core, ack)) : Optional.<RendererBasis>empty();
            return Optional.of(new VerifiedRead(core.validUntil(), evidence, renderBasis));
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return Optional.empty();
        }
    }

    private record RenderedEvent(String definitionKey, Full111RendererObservation observation) { }

    private Optional<RenderedEvent> renderer(Session same, ReadSubject subject, NativeGameTransport.CoreReceived core,
            AckReceived previous, Optional<String> definitionKey, Instant deadline) throws IOException {
        Instant until = earlier(deadline, core.validUntil());
        if (!context.clock().instant().isBefore(until)) return Optional.empty();
        subject.occurrence().requireOriginal(transport.currentSnapshot(until));

        DispatchOutcome outcome;
        try {
            outcome = transport.readFull111EventRenderer(core, subject.foreground().instanceId(), until);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return Optional.empty();
        }
        if (!(outcome instanceof AckReceived ack)) {
            var reason = switch (outcome) {
                case RejectedBeforeDispatch zero -> zero.proof().stage() + ": " + zero.proof().reason();
                case Unknown unknown -> unknown.reason();
                case AckReceived ignored -> throw new IllegalStateException("Renderer ACK already handled");
            };
            recordRendererRefusal(subject, reason, Optional.empty());
            return Optional.empty();
        }
        try {
            if (!ack.nativeOk()) {
                var reference = context.archive().withSession(same).preserve(ack);
                var result = CurrentFull111EventRenderer.decodeOutcome(ack);
                recordRendererRefusal(subject, result.status() + ": " + result.unavailableReason().orElseThrow(),
                        Optional.of(reference));
                return Optional.empty();
            }
            // A result cannot authorize selection after another accepted frame.
            subject.occurrence().requireOriginal(transport.currentSnapshot(deadline));
            var expected = ((CoreFrame.Partial) core.frame()).prefix();
            var observed = foregroundRenderer(previous, expected, ack, subject.foreground(), definitionKey);
            if (observed.isEmpty()) {
                recordRendererRefusal(subject, "Renderer ACK does not match the held Core, owner, or foreground", Optional.empty());
                return Optional.empty();
            }
            lastRendererRefusal = null;
            var options = observed.orElseThrow().options().stream().map(RootFull111EventRead::displayedOption).toList();
            var original = context.archive().withSession(same).preserve(ack);
            return Optional.of(new RenderedEvent(observed.orElseThrow().definitionKey(), new Full111RendererObservation(original, options)));
        } catch (IOException | UncheckedIOException | ContractViolationException unavailable) {
            recordRendererRefusal(subject, unavailable.getMessage(), Optional.empty());
            return Optional.empty();
        }
    }

    private void recordRendererRefusal(ReadSubject subject, String reason, Optional<ExactRef> reference) {
        String fingerprint = subject.foreground().instanceId() + ": " + reason;
        if (fingerprint.equals(lastRendererRefusal)) return;
        lastRendererRefusal = fingerprint;
        LOG.log(System.Logger.Level.WARNING, "Full111 event renderer unavailable for game {0}, instance {1}, snapshot {2}: {3}. Original ACK: {4}",
                subject.before().game().pid(), subject.foreground().instanceId(), subject.before().frame().snapshotId(),
                reason, reference.map(ExactRef::path).orElse("absent"));
    }

    static Full111RenderedOption displayedOption(CurrentFull111EventRenderer.Option option) {
        return new Full111RenderedOption(option.authoredOptionIndex(), option.nativeCanSelect(), option.widgetVisible(),
                option.widgetEnabled(), Optional.of(option.text()));
    }

    static Optional<CurrentFull111EventRenderer.Source> foregroundRenderer(AckReceived previous, CoreFrame.Prefix expected,
            AckReceived ack, NativeFull111OrdinaryEvent foreground, Optional<String> definitionKey) throws IOException {
        if (!sameSessionAfter(previous, ack)) return Optional.empty();
        var result = CurrentFull111EventRenderer.decodeOutcome(ack);
        if (result.status() != CurrentFull111EventRenderer.Status.AVAILABLE
                || result.factsBefore().filter(expected::equals).isEmpty()
                || !result.owner().orElseThrow().connectionGeneration().equals(previous.custody().orElseThrow().session().connectionGeneration()))
            return Optional.empty();
        return result.source().filter(source -> source.instanceId() == foreground.instanceId()
                && source.authoredOptionCount() == foreground.authoredOptionCount()
                && definitionKey.filter(key -> !source.definitionKey().equals(key)).isEmpty());
    }

    record ReadSubject(AcceptedSnapshotRevision occurrence, ObservationIdentity before, G2Source source,
            ExactRef full, ExactRef semantic, NativeFull111OrdinaryEvent foreground) { }
    record RendererBasis(NativeGameTransport.CoreReceived core, AckReceived lyd) { }
    record VerifiedRead(Instant validUntil, Full111EventObservation evidence, Optional<RendererBasis> rendererBasis) {
        VerifiedRead(Instant validUntil, Full111EventObservation evidence) {
            this(validUntil, evidence, Optional.empty());
        }
    }
    @FunctionalInterface interface EventReadAttempt {
        Optional<VerifiedRead> read() throws IOException;
    }
    @FunctionalInterface interface RendererReadAttempt {
        Optional<Full111RendererObservation> read(VerifiedRead basis) throws IOException;
    }

    /** Accessed under the one Root writer. Both readings stay bound to the same accepted occurrence. */
    static final class HeldReadMemo {
        private record Entry(ReadSubject subject, VerifiedRead observed) { }
        private Entry retained;

        void release(ExactRef originalRenderer) {
            if (retained != null && retained.observed().evidence().renderer().map(Full111RendererObservation::originalRead)
                    .filter(originalRenderer::equals).isPresent()) retained = null;
        }

        Optional<Full111EventObservation> observe(ReadSubject actual, Instant now, EventReadAttempt attempt)
                throws IOException {
            return observe(actual, now, attempt, unused -> Optional.empty());
        }
        Optional<Full111EventObservation> observe(ReadSubject actual, Instant now, EventReadAttempt attempt,
                RendererReadAttempt renderer) throws IOException {
            if (retained == null || !retained.subject().equals(actual) || !now.isBefore(retained.observed().validUntil())) {
                retained = null;
                var sampled = attempt.read();
                sampled.ifPresent(read -> retained = new Entry(actual, read));
                return sampled.map(VerifiedRead::evidence);
            }
            var read = retained.observed();
            if (read.rendererBasis().isPresent() && read.evidence().renderer().isEmpty()) {
                renderer.read(read).ifPresent(actualRenderer -> retained = new Entry(actual,
                        new VerifiedRead(read.validUntil(), read.evidence().withRenderer(actualRenderer))));
            }
            return Optional.of(retained.observed().evidence());
        }
    }

    /** Join only the real returned read evidence. A complete runtime queue or an option binding is never inferred here. */
    static Optional<String> foregroundDefinition(AckReceived core, CoreFrame.Prefix expected, AckReceived lyd,
            NativeFull111OrdinaryEvent foreground) throws IOException {
        if (!sameSessionAfter(core, lyd)) return Optional.empty();
        var result = CurrentLydResult.decodeFull111OrdinaryEvents(lyd);
        if (!result.successful() || !result.factsBefore().filter(expected::equals).isPresent()
                || !result.owner().orElseThrow().connectionGeneration().equals(core.custody().orElseThrow().session().connectionGeneration()))
            return Optional.empty();
        return result.source().orElseThrow().events().orElseThrow().events().stream()
                .filter(row -> row.instanceId() == foreground.instanceId()
                        && row.authoredOptionCount() == foreground.authoredOptionCount()
                        && row.namedRootBound() && row.windowVisible())
                .map(row -> row.definitionKey()).findFirst();
    }

    private static boolean sameSessionAfter(AckReceived first, AckReceived next) throws IOException {
        var basis = first.custody().orElseThrow(() -> new IOException("Original Full111 basis read custody is missing"));
        var receipt = next.custody().orElseThrow(() -> new IOException("Original Full111 event read custody is missing"));
        basis.verify(first);
        receipt.verify(next);
        return basis.session().equals(receipt.session()) && basis.custodyEpoch().equals(receipt.custodyEpoch())
                && receipt.writeEntered().order().compareTo(basis.responseReceived().order()) > 0;
    }

    static CoreFrame.Prefix prefix(JsonNode raw) throws IOException {
        var player = raw.path("played_character");
        return new CoreFrame.Prefix(readInt(raw, "date_raw"), readInt(raw, "speed"), readBool(raw, "paused"),
                readInt(raw, "local_player_id"), readBool(raw, "map_ready"), true,
                readInt(player, "character_id"), readBool(player, "alive"));
    }

    private static int readInt(JsonNode body, String name) throws IOException {
        return NativeWire.integer(body.path(name), MIN_INT, MAX_INT).intValueExact();
    }

    private static boolean readBool(JsonNode body, String name) throws IOException {
        var value = body.path(name);
        if (!value.isBoolean()) throw new IOException("Full111 field must be a boolean: " + name);
        return value.booleanValue();
    }

    private static Instant earlier(Instant first, Instant second) { return first.isBefore(second) ? first : second; }
}
