package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import java.nio.charset.StandardCharsets;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;

/** Existing seed/governance extension numbers preserve floating token class; control fields validate before this emitter. */
final class ClosedAdoptionJson {
    private ClosedAdoptionJson() { }
    static byte[] encode(JsonNode value) {
        return encode(value, StrictJson.INPUT_MAX_BYTES);
    }
    static byte[] encode(JsonNode value, int maximumBytes) {
        StringBuilder text = new StringBuilder(); append(value, text);
        byte[] raw = text.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(maximumBytes > 0 && maximumBytes <= OriginalWriterTransaction.MAX_PROTOCOL_BYTES
                && raw.length <= maximumBytes, "finite existing-payload JSON wire"); return raw;
    }
    private static void append(JsonNode value, StringBuilder out) {
        StrictJson.require(value != null, "missing value cannot become null");
        if (value.isObject()) {
            // Only the existing Document envelope carries an entire JSON document as
            // text. Its dedicated decoder validates exact ref/identity, strict UTF-8,
            // the JSON object and the independent 64 KiB document cap.
            boolean document = value.size() == 3 && value.has("ref") && value.has("identity") && value.has("raw_utf8");
            if (document) { OriginalWriterTransaction.Document.decode(value); }
            out.append('{'); TreeSet<String> names = new TreeSet<>(); value.fieldNames().forEachRemaining(names::add);
            boolean first = true;
            for (String name : names) {
                if (!first) { out.append(','); } first = false;
                out.append(new String(StrictJson.canonical(com.fasterxml.jackson.databind.node.TextNode.valueOf(name)), StandardCharsets.UTF_8));
                out.append(':');
                if (document && "raw_utf8".equals(name)) { quoteDocument(value.get(name).textValue(), out); }
                else { append(value.get(name), out); }
            }
            out.append('}');
        } else if (value.isArray()) {
            out.append('['); boolean first = true;
            for (JsonNode entry : value) { if (!first) { out.append(','); } first = false; append(entry, out); }
            out.append(']');
        } else if (value.isFloatingPointNumber()) {
            String decimal = value.decimalValue().toPlainString(); out.append(decimal);
            if (decimal.indexOf('.') < 0) { out.append(".0"); }
        } else { out.append(new String(StrictJson.canonical(value), StandardCharsets.UTF_8)); }
    }
    /** The complete document was validated above; ordinary metadata strings retain StrictJson's text cap. */
    private static void quoteDocument(String value, StringBuilder out) {
        out.append('"'); String hex = "0123456789abcdef";
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            switch (current) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\b' -> out.append("\\b");
                case '\f' -> out.append("\\f");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (current < 0x20) { out.append("\\u00").append(hex.charAt(current >> 4)).append(hex.charAt(current & 15)); }
                    else { out.append(current); }
                }
            }
        }
        out.append('"');
    }
}
