package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Bounded original SDK token retention. Domain codecs still validate every owned field. */
public final class HolySdkJson {
    public static final int LIMIT = 131_072;
    private static final JsonFactory FACTORY = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    private HolySdkJson() { }
    private record Span(int begin, int end) { }
    public static final class Source {
        private final byte[] raw;
        private final JsonNode tree;
        private final Map<String, Span> spans = new LinkedHashMap<>();
        public Source(byte[] value) {
            raw = ProjectionJson.object(value, LIMIT).bytes(); tree = StrictJson.parse(raw, LIMIT);
            try (JsonParser parser = FACTORY.createParser(raw)) { parser.nextToken(); collect(parser, "", spans); }
            catch (IOException error) { throw new IllegalArgumentException("SDK JSON token source invalid", error); }
        }
        public byte[] bytes() { return raw.clone(); }
        public JsonNode tree() { return tree.deepCopy(); }
        public Source select(String pointer) { return new Source(token(pointer)); }
        public byte[] token(String pointer) {
            Span span = spans.get(pointer);
            if (span == null) { throw new IllegalArgumentException("actual source token missing: " + pointer); }
            return java.util.Arrays.copyOfRange(raw, span.begin(), span.end());
        }
        public byte[] merge(JsonNode result, String origin, Map<String, String> aliases) {
            ByteArrayOutputStream out = new ByteArrayOutputStream(); emit(result, "", origin, aliases, out);
            return ProjectionJson.value(out.toByteArray(), LIMIT).bytes();
        }
        private void emit(JsonNode value, String outputPath, String origin, Map<String, String> aliases, ByteArrayOutputStream out) {
            String actualOrigin = aliases.getOrDefault(outputPath, origin); JsonNode original = tree.at(actualOrigin);
            if (!original.isMissingNode() && value.equals(original)) { put(out, token(actualOrigin)); return; }
            if (value.isObject()) {
                put(out, ascii("{")); boolean first = true;
                for (var field : value.properties()) {
                    if (!first) { put(out, ascii(",")); } first = false;
                    put(out, StrictJson.canonical(com.fasterxml.jackson.databind.node.TextNode.valueOf(field.getKey())));
                    put(out, ascii(":")); String suffix = "/" + escape(field.getKey());
                    emit(field.getValue(), outputPath + suffix, actualOrigin + suffix, aliases, out);
                }
                put(out, ascii("}"));
            } else if (value.isArray()) {
                put(out, ascii("["));
                for (int i = 0; i < value.size(); i++) {
                    if (i > 0) { put(out, ascii(",")); }
                    emit(value.get(i), outputPath + "/" + i, actualOrigin + "/" + i, aliases, out);
                }
                put(out, ascii("]"));
            } else if (value.isFloatingPointNumber()) {
                // Relocated observers require an explicit original pointer; equality cannot recover a lost -0.0 sign.
                throw new IllegalArgumentException("result float has no declared original SDK pointer");
            } else { put(out, StrictJson.canonical(value, LIMIT)); }
        }
    }
    private static void collect(JsonParser parser, String pointer, Map<String, Span> spans) throws IOException {
        int begin = Math.toIntExact(parser.currentTokenLocation().getByteOffset()); JsonToken token = parser.currentToken();
        if (token == JsonToken.START_OBJECT) {
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String name = parser.currentName(); parser.nextToken(); collect(parser, pointer + "/" + escape(name), spans);
            }
        } else if (token == JsonToken.START_ARRAY) {
            int index = 0;
            while (parser.nextToken() != JsonToken.END_ARRAY) { collect(parser, pointer + "/" + index++, spans); }
        }
        parser.finishToken();
        spans.put(pointer, new Span(begin, Math.toIntExact(parser.currentLocation().getByteOffset())));
    }
    private static String escape(String key) { return key.replace("~", "~0").replace("/", "~1"); }
    private static byte[] ascii(String value) { return value.getBytes(StandardCharsets.US_ASCII); }
    private static void put(ByteArrayOutputStream output, byte[] value) {
        StrictJson.require(output.size() + value.length <= LIMIT, "bounded SDK result bytes required");
        output.writeBytes(value);
    }
}
