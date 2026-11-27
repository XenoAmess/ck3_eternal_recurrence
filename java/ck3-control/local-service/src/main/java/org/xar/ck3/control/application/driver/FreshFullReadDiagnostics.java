package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import java.io.IOException;
import java.util.Optional;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Diagnostics from an original, already-bound negative Full READ response. */
public record FreshFullReadDiagnostics(String stage, Optional<Callback> callback) {
    public static final int MAXIMUM_PAYLOAD_BYTES = 4096;

    public record Callback(String stage, String reason) { }

    public static Optional<FreshFullReadDiagnostics> decode(byte[] payload) {
        try {
            return decode(NativeWire.parse(payload));
        } catch (IOException | IllegalArgumentException ignored) {
            return Optional.empty();
        }
    }

    public static Optional<FreshFullReadDiagnostics> decode(JsonNode payload) {
        var diagnostic = payload.path("fresh_full_state_diagnostic");
        var stage = diagnostic.path("stage").textValue();
        if (!"xar.native.fresh-full-state-diagnostic/v1".equals(diagnostic.path("schema").textValue())
                || !BooleanNode.FALSE.equals(diagnostic.path("fresh_available"))
                || stage == null || !stage.matches("[a-z][a-z_]{0,63}")) {
            return Optional.empty();
        }
        Optional<Callback> callback = "raw_read_unavailable".equals(stage) ? decodeCallback(diagnostic) : Optional.empty();
        return Optional.of(new FreshFullReadDiagnostics(stage, callback));
    }

    private static Optional<Callback> decodeCallback(JsonNode diagnostic) {
        var callback = diagnostic.path("callback_cause81");
        var sequence = diagnostic.path("query_sequence").textValue();
        if (!"xar.native.fresh-full-callback-cause/v1".equals(callback.path("schema").textValue())
                || sequence == null || !sequence.matches("[1-9][0-9]{0,19}")
                || !sequence.equals(callback.path("ticket_sequence").textValue())
                || !BooleanNode.TRUE.equals(callback.path("callback_entered"))
                || !BooleanNode.TRUE.equals(callback.path("exact_florin_reader"))
                || !BooleanNode.TRUE.equals(callback.path("raw_read_returned"))
                || !BooleanNode.FALSE.equals(callback.path("raw_read_available"))
                || !BooleanNode.FALSE.equals(callback.path("result_available"))) {
            return Optional.empty();
        }
        var stage = callback.path("full_stage").textValue();
        var reason = callback.path("full_reason").textValue();
        if (stage == null || !stage.matches("[a-z][a-z_]{0,63}")
                || reason == null || !reason.matches("[a-zA-Z][a-zA-Z0-9_]{0,255}")) {
            return Optional.empty();
        }
        return Optional.of(new Callback(stage, reason));
    }
}
