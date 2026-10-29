package org.xar.ck3.control.wave2.governance.educationpreference;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Explicit aggregate host transport; the standalone leaf codecs retain their 64 KiB boundary. */
public final class EducationBatchJson {
    public static final int MAX_BYTES = 8_388_608;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    private EducationBatchJson() { }

    public static JsonNode decode(byte[] raw) {
        StrictJson.require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded education host payload required");
        try {
            JsonNode result = JSON.readTree(ProjectionJson.object(raw, MAX_BYTES).bytes());
            StrictJson.require(result != null && result.isObject(), "education host payload must be an object");
            return result;
        } catch (IOException error) { throw new IllegalArgumentException("invalid education host UTF8/JSON", error); }
    }

    public static byte[] encode(JsonNode value) {
        try {
            byte[] raw = JSON.writeValueAsBytes(value);
            StrictJson.require(raw.length > 0 && raw.length <= MAX_BYTES, "education host result exceeds aggregate budget");
            return ProjectionJson.value(raw, MAX_BYTES).bytes();
        } catch (IOException error) { throw new IllegalArgumentException("education host JSON encoding failed", error); }
    }
}
