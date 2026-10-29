package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** Original BridgeUnavailable query fault DATA. The LOCAL_SERVICE boundary supplies the MCP exception class. */
public final class ArmyWindowQueryFailure extends RuntimeException {
    private static final long serialVersionUID = 1L;
    private final ArmyWindowCodec.Kind window;
    // Original native evidence remains in-process; durable evidence uses the receipt archive.
    private final transient Optional<NativeActionPort.DispatchOutcome> original;
    private ArmyWindowQueryFailure(ArmyWindowCodec.Kind window, String message, Optional<NativeActionPort.DispatchOutcome> original) {
        super(Objects.requireNonNull(message)); this.window = Objects.requireNonNull(window); this.original = Objects.requireNonNull(original);
    }
    public ArmyWindowCodec.Kind window() { return window; }
    public Optional<NativeActionPort.DispatchOutcome> original() { return original; }
    public static ArmyWindowQueryFailure from(ArmyWindowCodec.Kind kind, PlanningReadResult.Unavailable<?> unavailable) {
        Objects.requireNonNull(unavailable); String message = unavailable.reason();
        if (unavailable.original().isPresent()) {
            NativeActionPort.DispatchOutcome actual = unavailable.original().orElseThrow();
            if (actual instanceof NativeActionPort.Unknown) message = timeoutMessage(kind);
            else if (actual instanceof NativeActionPort.RejectedBeforeDispatch rejected) message = rejected.proof().reason();
            else if (actual instanceof NativeActionPort.AckReceived ack && !ack.nativeOk()) {
                try { message = refusalMessage(kind, ack.originalFrame(), ack.requestId()); }
                catch (IllegalArgumentException malformed) { message = malformed.getMessage(); }
            }
        }
        return new ArmyWindowQueryFailure(kind, message, unavailable.original());
    }
    public static String timeoutMessage(ArmyWindowCodec.Kind kind) { return label(kind) + " original command_result timed out"; }
    /** Sole two-window false-TOP parser, shared with the direct CLOSE public formatter. No refusal becomes Known. */
    public static String refusalMessage(ArmyWindowCodec.Kind kind, RawJson actualTop, String requestId) {
        String name = label(kind); com.fasterxml.jackson.databind.node.ObjectNode top;
        try { top = object(parse(Objects.requireNonNull(actualTop).bytes())); }
        catch (IllegalArgumentException malformed) { throw new IllegalArgumentException(name + " command_result is missing", malformed); }
        try {
            equal(top.get("type"), "command_result"); require(i32(top.get("protocol_version")) == 1, "protocol"); equal(top.get("request_id"), requestId);
        } catch (IllegalArgumentException malformed) { throw new IllegalArgumentException(name + " actual TOP request binding differs", malformed); }
        if (!top.has("ok") || !top.get("ok").isBoolean() || top.get("ok").booleanValue())
            throw new IllegalArgumentException(name + " command_result success shape is malformed");
        if (!names(top).equals(Set.of("type","protocol_version","request_id","ok","error")) || !top.get("error").isTextual())
            throw new IllegalArgumentException(name + " refusal shape is malformed");
        return (kind == ArmyWindowCodec.Kind.OVERVIEW ? "Native war overview refused: " : "Native war results refused: ") + top.get("error").textValue();
    }
    private static String label(ArmyWindowCodec.Kind kind) { return Objects.requireNonNull(kind) == ArmyWindowCodec.Kind.OVERVIEW ? "war overview" : "war results"; }
}
