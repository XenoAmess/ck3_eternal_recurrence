package org.xar.ck3.control.wave2.governance.betrothal;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Bounded operation envelopes. Decimal extension tokens never pass through integer-only canonical JSON. */
public final class MarriageProjectionJson {
    private static final JsonMapper JSON = JsonMapper.builder(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                    DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS,
                    DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private MarriageProjectionJson() { }

    public static JsonNode value(byte[] raw, int maximumBytes) {
        StrictJson.parse(raw, maximumBytes);
        try { return JSON.readTree(raw); }
        catch (IOException error) { throw new IllegalArgumentException("invalid marriage projection JSON", error); }
    }
    public static ObjectNode object(byte[] raw, int maximumBytes, Set<String> fields) {
        return StrictJson.object(value(raw, maximumBytes), fields);
    }
    public static byte[] bytes(JsonNode value, int maximumBytes) {
        StrictJson.require(value != null, "missing projection field cannot become null");
        try {
            byte[] result = JSON.writeValueAsBytes(value);
            StrictJson.require(result.length <= maximumBytes, "marriage projection exceeds its explicit byte budget");
            return result;
        } catch (IOException error) { throw new IllegalArgumentException("cannot encode marriage projection", error); }
    }
}
