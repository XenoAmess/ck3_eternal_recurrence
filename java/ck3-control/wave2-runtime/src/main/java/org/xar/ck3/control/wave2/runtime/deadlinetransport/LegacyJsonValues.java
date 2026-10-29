package org.xar.ck3.control.wave2.runtime.deadlinetransport;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;
import org.xar.ck3.control.contracts.StrictJson;

/** Value-domain writer for opaque legacy extensions, preserving JSON integer versus decimal types. */
final class LegacyJsonValues {
    private LegacyJsonValues() { }

    static String text(JsonNode value) {
        StringBuilder output = new StringBuilder();
        append(value, output, 0);
        String result = output.toString();
        require(result.getBytes(StandardCharsets.UTF_8).length <= StrictJson.INPUT_MAX_BYTES,
                "bounded legacy JSON required");
        return result;
    }

    static byte[] encode(JsonNode value) { return text(value).getBytes(StandardCharsets.UTF_8); }

    private static void append(JsonNode value, StringBuilder output, int depth) {
        require(value != null && depth <= 128 && output.length() <= StrictJson.INPUT_MAX_BYTES,
                "bounded existing JSON value required");
        if (value.isObject()) {
            output.append('{');
            Iterator<String> fields = value.fieldNames();
            boolean first = true;
            while (fields.hasNext()) {
                String field = fields.next();
                if (!first) { output.append(','); }
                first = false;
                quote(field, output); output.append(':');
                append(value.get(field), output, depth + 1);
            }
            output.append('}');
        } else if (value.isArray()) {
            output.append('[');
            boolean first = true;
            for (JsonNode entry : value) {
                if (!first) { output.append(','); }
                first = false;
                append(entry, output, depth + 1);
            }
            output.append(']');
        } else if (value.isTextual()) {
            quote(value.textValue(), output);
        } else if (value.isIntegralNumber()) {
            output.append(value.bigIntegerValue());
        } else if (value.isFloatingPointNumber()) {
            require(!(value.isDouble() || value.isFloat()) || Double.isFinite(value.doubleValue()),
                    "finite JSON decimal required");
            String decimal = value.decimalValue().toString();
            output.append(decimal);
            if (decimal.indexOf('.') < 0 && decimal.indexOf('E') < 0 && decimal.indexOf('e') < 0) {
                output.append(".0");
            }
        } else if (value.isBoolean()) {
            output.append(value.booleanValue() ? "true" : "false");
        } else {
            require(value.isNull(), "existing JSON value required; no missing node");
            output.append("null");
        }
    }

    private static void quote(String value, StringBuilder output) {
        if (!value.isEmpty()) { StrictJson.text(value); }
        output.append(TextNode.valueOf(value));
    }
}
