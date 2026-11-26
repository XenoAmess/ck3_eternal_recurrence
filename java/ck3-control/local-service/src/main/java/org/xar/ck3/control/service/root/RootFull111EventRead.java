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
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111EventObservation;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111EventRead;
import org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.semantic.NativeFull111OrdinaryEvent;
import org.xar.ck3.control.nativebridge.CurrentLyd;
import org.xar.ck3.control.nativebridge.CurrentLydResult;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Optional Full111 foreground evidence for the ordinary diagnostic. */
final class RootFull111EventRead implements Full111EventRead {
    private static final BigInteger MIN_INT = BigInteger.valueOf(Integer.MIN_VALUE);
    private static final BigInteger MAX_INT = BigInteger.valueOf(Integer.MAX_VALUE);
    private final RootRuntimeContext context;
    private final NativeGameTransport transport;

    RootFull111EventRead(RootRuntimeContext context, NativeGameTransport transport) {
        this.context = Objects.requireNonNull(context);
        this.transport = Objects.requireNonNull(transport);
    }

    @Override public Optional<Full111EventObservation> observe(PlanningRequest actual, NativeFull111OrdinaryEvent foreground) {
        var caps = actual.observations().bridgeCapabilities();
        if (!caps.contains(CoreFrame.CAPABILITY) || !caps.contains(CurrentLyd.Action.QUERY_EVENTS.capability()))
            return Optional.empty();
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
        if (!actual.source().equals(frame.source()) || !actual.sessionId().equals(frame.sessionId())
                || !actual.observations().snapshot().equals(frame.semantic())
                || !lease.bridgeCapabilities().contains(CoreFrame.CAPABILITY)
                || !lease.bridgeCapabilities().contains(CurrentLyd.Action.QUERY_EVENTS.capability()))
            return Optional.empty();
        var originals = lease.semantic();
        var full = context.collector().activeOriginalNativeFrame(same, lease);
        var raw = NativeWire.object(NativeWire.parse(full.state().bytes()));
        var bound = originals.originalNativePacket();
        byte[] rawPacket = full.originalPacket();
        if (!originals.frame().equals(frame.identity()) || !bound.equals(frame.originalEvidence())
                || bound.bytes() != rawPacket.length
                || !bound.sha256().equals(ActionCodec.sha256(rawPacket))
                || !NativeFull111OrdinaryEvent.read(raw).filter(foreground::equals).isPresent())
            return Optional.empty();
        Instant deadline = earlier(actual.deadline(), lease.validUntil());
        var accepted = transport.acceptedSnapshotRevision(full);
        accepted.requireOriginal(transport.currentSnapshot(deadline));

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
            if (!(transport.readFull111OrdinaryEvents(core, deadline) instanceof AckReceived ack) || !ack.nativeOk())
                return Optional.empty();
            accepted.requireOriginal(transport.currentSnapshot(deadline));
            var key = foregroundDefinition(core.original(), partial.prefix(), ack, foreground);
            if (key.isEmpty()) return Optional.empty();

            var archive = context.archive().withSession(same);
            return Optional.of(new Full111EventObservation(foreground.instanceId(), key.orElseThrow(),
                    bound, originals.semantic(), archive.preserve(core.original()), archive.preserve(ack)));
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return Optional.empty();
        }
    }

    /** Join only the real returned read evidence. A complete runtime queue or an option binding is never inferred here. */
    static Optional<String> foregroundDefinition(AckReceived core, CoreFrame.Prefix expected, AckReceived lyd,
            NativeFull111OrdinaryEvent foreground) throws IOException {
        var basis = core.custody().orElseThrow(() -> new IOException("Original Full111 Core read custody is missing"));
        var receipt = lyd.custody().orElseThrow(() -> new IOException("Original Full111 event read custody is missing"));
        basis.verify(core);
        receipt.verify(lyd);
        if (!basis.session().equals(receipt.session()) || !basis.custodyEpoch().equals(receipt.custodyEpoch())
                || receipt.writeEntered().order().compareTo(basis.responseReceived().order()) <= 0)
            return Optional.empty();
        var result = CurrentLydResult.decodeFull111OrdinaryEvents(lyd);
        if (!result.successful() || !result.factsBefore().filter(expected::equals).isPresent()
                || !result.owner().orElseThrow().connectionGeneration().equals(basis.session().connectionGeneration()))
            return Optional.empty();
        return result.source().orElseThrow().events().orElseThrow().events().stream()
                .filter(row -> row.instanceId() == foreground.instanceId()
                        && row.authoredOptionCount() == foreground.authoredOptionCount()
                        && row.namedRootBound() && row.windowVisible())
                .map(row -> row.definitionKey()).findFirst();
    }

    private static CoreFrame.Prefix prefix(JsonNode raw) throws IOException {
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
