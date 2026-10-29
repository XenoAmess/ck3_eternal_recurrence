package org.xar.ck3.control.wave2.finance.rawcash;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.contracts.StrictJson;

/** Central SDK projection transport. Preserves integer versus floating token categories across subtree handoffs. */
public final class SdkProjectionJson {
    private static final ObjectMapper WRITER = new ObjectMapper();
    private SdkProjectionJson() { }
    public static byte[] encode(JsonNode node) {
        return encode(node, 65_536);
    }
    /** Explicit role budget; the default SDK projection boundary remains 64 KiB. */
    public static byte[] encode(JsonNode node, int maximumBytes) {
        StrictJson.require(maximumBytes > 0 && maximumBytes <= StrictJson.EXPLICIT_MAX_BYTES,
                "explicit SDK projection byte budget");
        StrictJson.require(node != null, "missing SDK projection cannot become JSON null");
        StringBuilder output = new StringBuilder(); append(node, output);
        byte[] raw = output.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(raw.length <= maximumBytes, "SDK projection exceeds declared wire boundary"); return raw;
    }
    private static void append(JsonNode node, StringBuilder output) {
        if (node.isObject()) {
            output.append('{'); boolean first = true;
            for (var field : node.properties()) {
                if (!first) { output.append(','); } first = false;
                output.append(quoted(field.getKey())).append(':'); append(field.getValue(), output);
            }
            output.append('}');
        } else if (node.isArray()) {
            output.append('['); boolean first = true;
            for (JsonNode value : node) { if (!first) { output.append(','); } first = false; append(value, output); }
            output.append(']');
        } else if (node.isFloatingPointNumber()) {
            String token = node.decimalValue().toString(); output.append(token);
            // StrictJson's tree can strip trailing zeroes. Keeping .0 prevents 1.0 being laundered into an integer.
            if (token.indexOf('.') < 0 && token.indexOf('E') < 0 && token.indexOf('e') < 0) { output.append(".0"); }
        } else if (node.isTextual()) { output.append(quoted(node.textValue())); }
        else if (node.isIntegralNumber()) { output.append(node.bigIntegerValue()); }
        else if (node.isBoolean()) { output.append(node.booleanValue()); }
        else { StrictJson.require(node.isNull(), "SDK projection contains unsupported JSON node"); output.append("null"); }
    }
    private static String quoted(String value) {
        if (!value.isEmpty()) { StrictJson.text(value); }
        try { return WRITER.writeValueAsString(value); }
        catch (JsonProcessingException error) { throw new IllegalArgumentException("SDK projection string encoding failed", error); }
    }
}
