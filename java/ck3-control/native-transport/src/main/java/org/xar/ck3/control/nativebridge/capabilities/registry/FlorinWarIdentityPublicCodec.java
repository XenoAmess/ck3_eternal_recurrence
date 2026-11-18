package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.semantic.FlorinWarIdentityCodec;
import org.xar.ck3.control.contracts.semantic.FlorinWarIdentityData;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Original War-only request/result DATA. Its partial Full view cannot substitute for Driver FullSnapshot or a control receipt. */
public final class FlorinWarIdentityPublicCodec {
    private FlorinWarIdentityPublicCodec() { }
    public sealed interface ProjectedRead permits PartialFullData, UnavailableRead {
        NativeActionPort.DispatchOutcome original();
    }
    /** Core plus War identities/sides/optional scores; each unobserved rich field remains a named Unavailable value. */
    public record PartialFullData(NativeActionPort.AckReceived original, FlorinWarIdentityData.Observation warData)
            implements ProjectedRead {
        public PartialFullData {
            Objects.requireNonNull(original); Objects.requireNonNull(warData);
            try { RegistryJson.require(decodeOutcome(original).equals(warData), "partial War Full DATA differs from its exact original result"); }
            catch (IOException invalid) { throw new IllegalArgumentException("partial War Full DATA requires original query/result bytes", invalid); }
        }
        public boolean completeSnapshot() { return false; }
        public boolean completeActiveWarsQualified() { return false; }
        public FlorinWarIdentityData.Core coreFrame() { return warData.coreFrame(); }
    }
    /** ACK/UNKNOWN/zero-dispatch decoding failure retains the original outcome without making an unavailable Native result. */
    public record UnavailableRead(NativeActionPort.DispatchOutcome original, String reason) implements ProjectedRead {
        public UnavailableRead { Objects.requireNonNull(original); RegistryJson.require(reason != null && !reason.isEmpty(), "original War read failure reason required"); }
    }

    public static FlorinWarIdentityData.Observation decodePacket(RawJson original, String expectedRequestId) throws IOException {
        Objects.requireNonNull(original); Objects.requireNonNull(expectedRequestId);
        var envelope = RegistryJson.object(original);
        RegistryJson.keys(envelope, Set.of("type", "protocol_version", "request_id", "ok", "result"));
        RegistryJson.require("command_result".equals(RegistryJson.text(envelope.get("type")))
                && RegistryJson.integer(envelope.get("protocol_version"), BigInteger.ONE, BigInteger.ONE).equals(BigInteger.ONE)
                && expectedRequestId.equals(RegistryJson.text(envelope.get("request_id"))) && RegistryJson.bool(envelope.get("ok")),
                "War identity original envelope identity/status differs");
        var decoded = NativeWire.decode(NativeWire.packet(original.bytes()));
        RegistryJson.require(decoded instanceof NativeWire.CommandResult, "War identity requires its original command_result");
        var result = (NativeWire.CommandResult) decoded;
        RegistryJson.require(result.result().presence() == NativeWire.Presence.VALUE, "War identity original result missing or null");
        return FlorinWarIdentityCodec.decode(result.result().token().orElseThrow().value());
    }

    public static FlorinWarIdentityData.Observation decodeOutcome(NativeActionPort.DispatchOutcome original) throws IOException {
        Objects.requireNonNull(original);
        if (original instanceof NativeActionPort.RejectedBeforeDispatch rejected)
            throw new IOException("War identity source unavailable before dispatch: " + rejected.proof().reason());
        if (original instanceof NativeActionPort.Unknown unknown)
            throw new IOException("War identity query result unknown; original request is never replayed: " + unknown.reason());
        var ack = (NativeActionPort.AckReceived) original;
        try {
            var outbound = ack.outbound().orElseThrow(() -> new IOException("original War identity outbound missing"));
            var request = NativeWire.decodeExecuteRequest(outbound.originalPacket());
            RegistryJson.require(outbound.requestId().equals(ack.requestId()) && request.requestId().equals(ack.requestId())
                    && FlorinWarIdentityCodec.STEP.equals(request.step()) && request.expectedRevision().equals(Optional.of(BigInteger.ZERO))
                    && request.expectedSnapshotRevision().isEmpty(), "War identity request step/revision/identity differs");
            RegistryJson.keys(RegistryJson.object(new RawJson(request.normalizedAdditionalFields().value())), Set.of());
            var decoded = NativeWire.decode(ack.originalPacket());
            RegistryJson.require(decoded instanceof NativeWire.CommandResult, "original War identity ACK is not command_result");
            var result = (NativeWire.CommandResult) decoded;
            RegistryJson.require(result.requestId().equals(ack.requestId()) && result.nativeOk() == ack.nativeOk()
                    && Arrays.equals(result.payload().value(), ack.originalFrame().bytes()), "retained War identity envelope differs");
            RegistryJson.require(result.result().presence() == NativeWire.Presence.VALUE && ack.originalResultToken().isPresent()
                    && Arrays.equals(result.result().token().orElseThrow().value(), ack.originalResultToken().orElseThrow().bytes()),
                    "retained War identity result token differs");
            return decodePacket(ack.originalFrame(), ack.requestId());
        } catch (IllegalArgumentException invalid) { throw new IOException("original War identity profile/result invalid", invalid); }
    }

    /** Projection entry uses the actual independent query; positive War DATA does not require the unsupported positive rich Full path. */
    public static ProjectedRead projectPartialFull(NativeActionPort.DispatchOutcome original) {
        Objects.requireNonNull(original);
        try {
            var data = decodeOutcome(original);
            return new PartialFullData((NativeActionPort.AckReceived) original, data);
        }
        catch (IOException | RuntimeException invalid) {
            String reason = invalid.getMessage();
            return new UnavailableRead(original, reason == null || reason.isEmpty() ? invalid.getClass().getName() : reason);
        }
    }
}
