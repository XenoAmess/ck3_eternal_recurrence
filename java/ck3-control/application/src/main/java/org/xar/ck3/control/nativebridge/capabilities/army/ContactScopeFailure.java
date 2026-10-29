package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.contracts.StrictJson;

/** Original fault DATA for the two existing Contact queries. No retry, current read or lease is minted. */
public final class ContactScopeFailure extends RuntimeException {
    private static final long serialVersionUID = 1L;
    public enum Kind {
        BRIDGE_UNAVAILABLE, PRE_SUBMISSION_REVISION_MISMATCH, NATIVE_COMMAND_REJECTED, UNCLASSIFIED_NATIVE
    }
    // Runtime query/evidence are retained in-process, not Java object serialization.
    private final transient ContactScopeObservation.Query query;
    private final Kind kind;
    private final transient Optional<PlanningReadResult.Unavailable<ContactScopeObservation>> unavailable;
    private final String sourceReason;

    private ContactScopeFailure(ContactScopeObservation.Query query, Kind kind, String message,
            Optional<PlanningReadResult.Unavailable<ContactScopeObservation>> unavailable, Throwable cause) {
        super(Objects.requireNonNull(message), cause);
        this.query = Objects.requireNonNull(query);
        this.kind = Objects.requireNonNull(kind);
        this.unavailable = Objects.requireNonNull(unavailable);
        this.sourceReason = unavailable.map(PlanningReadResult.Unavailable::reason).orElse(message);
    }

    public ContactScopeObservation.Query query() { return query; }
    public Kind kind() { return kind; }
    public String sourceReason() { return sourceReason; }
    public Optional<PlanningReadResult.Unavailable<ContactScopeObservation>> unavailable() { return unavailable; }
    public Optional<NativeActionPort.DispatchOutcome> original() { return unavailable.flatMap(PlanningReadResult.Unavailable::original); }

    /** Actual pre-read public revision check, with the original per-query exception message. */
    public static void requireExpectedRevision(ContactScopeObservation.Query query, BigInteger expected, BigInteger current) {
        Objects.requireNonNull(query); Objects.requireNonNull(expected); Objects.requireNonNull(current);
        StrictJson.require(expected.signum() >= 0 && expected.compareTo(StrictJson.UINT64_MAX) <= 0
                && current.signum() >= 0 && current.compareTo(StrictJson.UINT64_MAX) <= 0,
                "actual Contact public revisions must be uint64");
        if (!expected.equals(current)) {
            String message = query instanceof ContactScopeObservation.Projected
                    ? "projected-contact source revision is stale"
                    : "native gameplay revision mismatch: expected " + expected + ", current " + current;
            throw new ContactScopeFailure(query, Kind.PRE_SUBMISSION_REVISION_MISMATCH, message, Optional.empty(), null);
        }
    }

    /** Preserve the actual current-Root/observation IOException as the exception cause. */
    public static ContactScopeFailure fromIo(ContactScopeObservation.Query query, IOException original) {
        Objects.requireNonNull(original);
        String message = original.getMessage() == null ? original.toString() : original.getMessage();
        return new ContactScopeFailure(query, Kind.BRIDGE_UNAVAILABLE, message, Optional.empty(), original);
    }

    /** An unavailable result never becomes a normal public Contact response or a newly issued READ. */
    public static ContactScopeFailure from(ContactScopeObservation.Query query,
            PlanningReadResult.Unavailable<ContactScopeObservation> result) {
        Objects.requireNonNull(query); Objects.requireNonNull(result);
        Optional<NativeActionPort.DispatchOutcome> actual = result.original();
        if (actual.orElse(null) instanceof NativeActionPort.AckReceived ack) {
            Optional<String> refusal = originalRefusal(query, ack);
            if (refusal.isPresent()) return new ContactScopeFailure(query, Kind.NATIVE_COMMAND_REJECTED,
                    refusal.orElseThrow(), Optional.of(result), null);
        }
        if (actual.orElse(null) instanceof NativeActionPort.Unknown unknown
                && unknown.failureCause().filter(cause -> cause.kind() == NativeActionPort.FailureKind.DEADLINE_EXPIRED
                        && cause.stage() == NativeActionPort.FailureStage.RESPONSE_WAIT && cause.deadline().isPresent()).isPresent()
                && originalRequest(query, unknown.requestId(), unknown.originalRequestPacket())) {
            return new ContactScopeFailure(query, Kind.BRIDGE_UNAVAILABLE,
                    "native command_result timed out for gameplay step " + query.step(), Optional.of(result), null);
        }
        // Historical/unclassified Unknown and frame/IO/interruption causes cannot prove the original timeout branch.
        String message = actual.orElse(null) instanceof NativeActionPort.Unknown unknown ? unknown.reason()
                : actual.orElse(null) instanceof NativeActionPort.RejectedBeforeDispatch rejected ? rejected.proof().reason()
                : result.reason();
        return new ContactScopeFailure(query, Kind.UNCLASSIFIED_NATIVE, message, Optional.of(result), null);
    }

    private static Optional<String> originalRefusal(ContactScopeObservation.Query query, NativeActionPort.AckReceived ack) {
        if (ack.nativeOk() || ack.outbound().isEmpty()) return Optional.empty();
        try {
            ObjectNode top = packet(ack.originalPacket());
            if (!Arrays.equals(ack.originalFrame().bytes(), Arrays.copyOfRange(ack.originalPacket(), 4, ack.originalPacket().length))
                    || !originalRequest(query, ack.requestId(), ack.outbound().orElseThrow().originalPacket())
                    || !text(top, "type", "command_result") || !integerOne(top.get("protocol_version"))
                    || !text(top, "request_id", ack.requestId()) || !top.path("ok").isBoolean() || top.path("ok").booleanValue()
                    || top.path("typed_query_failure_v1").isObject()) return Optional.empty();
            JsonNode error = top.get("error");
            return Optional.of("native gameplay step failed: " + (error != null && error.isTextual() ? error.textValue() : "unknown error"));
        } catch (IllegalArgumentException malformed) { return Optional.empty(); }
    }
    private static boolean originalRequest(ContactScopeObservation.Query query, String requestId, byte[] actualPacket) {
        try {
            ObjectNode request = packet(actualPacket);
            if (!text(request, "type", "execute_step") || !integerOne(request.get("protocol_version"))
                    || !text(request, "request_id", requestId) || !text(request, "step", query.step())) return false;
            StrictJson.integer(request.get("expected_revision"), BigInteger.ONE, StrictJson.UINT64_MAX);
            return true;
        } catch (IllegalArgumentException malformed) { return false; }
    }
    private static ObjectNode packet(byte[] packet) {
        StrictJson.require(packet.length > Integer.BYTES
                && ByteBuffer.wrap(packet).order(ByteOrder.LITTLE_ENDIAN).getInt() == packet.length - Integer.BYTES,
                "actual complete native packet required");
        JsonNode value = StrictJson.parse(Arrays.copyOfRange(packet, 4, packet.length), StrictJson.EXPLICIT_MAX_BYTES);
        StrictJson.require(value instanceof ObjectNode, "actual native packet object required");
        return (ObjectNode) value;
    }
    private static boolean text(ObjectNode node, String name, String expected) {
        return node.path(name).isTextual() && expected.equals(node.path(name).textValue());
    }
    private static boolean integerOne(JsonNode value) { return value != null && value.isIntegralNumber() && BigInteger.ONE.equals(value.bigIntegerValue()); }
}
