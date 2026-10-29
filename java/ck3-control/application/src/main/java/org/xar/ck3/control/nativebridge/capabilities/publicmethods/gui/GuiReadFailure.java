package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.contracts.StrictJson;

/** Original failed read DATA. This exception grants no read lineage, retry or action authority. */
public final class GuiReadFailure extends RuntimeException {
    private static final long serialVersionUID = 1L;

    public enum Kind {
        NO_ORIGINAL, REJECTED_BEFORE_DISPATCH, NATIVE_REFUSAL, ACK_UNUSABLE, UNKNOWN
    }

    // In-process domain evidence is consumed directly; Java serialization is not its persistence contract.
    private final transient PlanningReadResult.Unavailable<?> unavailable;
    private final Kind kind;

    private GuiReadFailure(PlanningReadResult.Unavailable<?> unavailable, Kind kind, String message) {
        super(Objects.requireNonNull(message));
        this.unavailable = Objects.requireNonNull(unavailable);
        this.kind = Objects.requireNonNull(kind);
    }

    public PlanningReadResult.Unavailable<?> unavailable() { return unavailable; }
    public Optional<NativeActionPort.DispatchOutcome> original() { return unavailable.original(); }
    public Kind kind() { return kind; }
    public String sourceReason() { return unavailable.reason(); }

    /** Retain the identical original outcome; Unknown is never inferred to mean timeout. */
    public static GuiReadFailure from(PlanningReadResult.Unavailable<?> result) {
        Objects.requireNonNull(result);
        if (result.original().isEmpty()) return new GuiReadFailure(result, Kind.NO_ORIGINAL, result.reason());
        NativeActionPort.DispatchOutcome actual = result.original().orElseThrow();
        if (actual instanceof NativeActionPort.Unknown unknown)
            return new GuiReadFailure(result, Kind.UNKNOWN, unknown.reason());
        if (actual instanceof NativeActionPort.RejectedBeforeDispatch rejected)
            return new GuiReadFailure(result, Kind.REJECTED_BEFORE_DISPATCH, rejected.proof().reason());
        NativeActionPort.AckReceived ack = (NativeActionPort.AckReceived) actual;
        Optional<String> refusal = refusalMessage(ack);
        return refusal.map(message -> new GuiReadFailure(result, Kind.NATIVE_REFUSAL, message))
                .orElseGet(() -> new GuiReadFailure(result, Kind.ACK_UNUSABLE, result.reason()));
    }

    /** The original common primitive rejection profile, only from a bound original false TOP.
     * Structured typed-query failures need their own domain profile and retain the original reason here. */
    static Optional<String> refusalMessage(NativeActionPort.AckReceived ack) {
        if (ack.nativeOk()) return Optional.empty();
        byte[] body = ack.originalFrame().bytes();
        byte[] packet = ack.originalPacket();
        if (packet.length != body.length + Integer.BYTES
                || ByteBuffer.wrap(packet).order(ByteOrder.LITTLE_ENDIAN).getInt() != body.length
                || !Arrays.equals(body, Arrays.copyOfRange(packet, Integer.BYTES, packet.length)))
            return Optional.empty();
        try {
            JsonNode parsed = StrictJson.parse(body, StrictJson.EXPLICIT_MAX_BYTES);
            if (!(parsed instanceof ObjectNode top)
                    || !top.path("type").isTextual() || !"command_result".equals(top.path("type").textValue())
                    || !top.path("protocol_version").isIntegralNumber() || !top.path("protocol_version").bigIntegerValue().equals(java.math.BigInteger.ONE)
                    || !top.path("request_id").isTextual() || !ack.requestId().equals(top.path("request_id").textValue())
                    || !top.path("ok").isBoolean() || top.path("ok").booleanValue()
                    || top.path("typed_query_failure_v1").isObject()) return Optional.empty();
            JsonNode error = top.get("error");
            String actualError = error != null && error.isTextual() ? error.textValue() : "unknown error";
            return Optional.of("native gameplay step failed: " + actualError);
        } catch (IllegalArgumentException malformed) {
            return Optional.empty();
        }
    }
}
