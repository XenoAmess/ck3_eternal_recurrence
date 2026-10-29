package org.xar.ck3.control.g2.m4;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Base64;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.m4.M4ConstructionConsumers.Evaluation;
import org.xar.ck3.control.g2.m4.M4ConstructionConsumers.Stage;

/**
 * Versioned data serialization for the original persistence owner. No method
 * opens a file, writes a ledger, evaluates a request or retries an action.
 */
public final class M4ConstructionCheckpoint {
    public static final String SCHEMA = "xar.ck3.g2.m4.construction-gate-checkpoint/v1";
    private static final Set<String> FIELDS = Set.of("schema", "stage", "request_wire_base64", "response_wire_base64");
    private static final ObjectMapper JSON = new ObjectMapper();
    private M4ConstructionCheckpoint() { }

    public static byte[] encode(Evaluation evaluation, int maximumBytes) {
        Objects.requireNonNull(evaluation);
        StrictJson.require(maximumBytes > 0 && maximumBytes <= StrictJson.EXPLICIT_MAX_BYTES,
                "explicit M4 checkpoint byte budget required");
        ObjectNode node = StrictJson.object();
        node.put("schema", SCHEMA); node.put("stage", evaluation.stage().name());
        // The common codec alone owns the transport envelope. Base64 preserves its
        // exact bytes and the original JSON integer/floating token categories.
        node.put("request_wire_base64", Base64.getEncoder().encodeToString(G2Wire.encodeRequest(evaluation.request())));
        node.put("response_wire_base64", Base64.getEncoder().encodeToString(G2Wire.encodeResponse(evaluation.response())));
        try {
            // These are bounded binary wire blobs, not ordinary 32768-character
            // domain identifiers. Their limit is the caller's whole checkpoint budget.
            byte[] raw = JSON.writeValueAsBytes(node);
            StrictJson.parse(raw, maximumBytes);
            return raw;
        } catch (IOException error) { throw new IllegalArgumentException("cannot encode M4 checkpoint", error); }
    }

    public static Evaluation decode(byte[] checkpointUtf8, int maximumBytes) {
        ObjectNode node = StrictJson.object(StrictJson.parse(checkpointUtf8, maximumBytes), FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(node.get("schema"))), "M4 checkpoint schema mismatch");
        Stage stage;
        try { stage = Stage.valueOf(StrictJson.text(node.get("stage"))); }
        catch (IllegalArgumentException error) { throw new IllegalArgumentException("M4 checkpoint stage mismatch", error); }
        byte[] request = raw(node.get("request_wire_base64"));
        byte[] response = raw(node.get("response_wire_base64"));
        return M4ConstructionConsumers.restore(stage, G2Wire.decodeRequest(request), G2Wire.decodeResponse(response));
    }

    private static byte[] raw(JsonNode value) {
        StrictJson.require(value != null && value.isTextual() && !value.textValue().isEmpty(),
                "nonempty M4 checkpoint wire blob required");
        String encoded = value.textValue();
        try {
            byte[] raw = Base64.getDecoder().decode(encoded);
            StrictJson.require(Base64.getEncoder().encodeToString(raw).equals(encoded), "canonical M4 checkpoint base64 required");
            return raw;
        } catch (IllegalArgumentException error) { throw new IllegalArgumentException("invalid M4 checkpoint wire bytes", error); }
    }
}
