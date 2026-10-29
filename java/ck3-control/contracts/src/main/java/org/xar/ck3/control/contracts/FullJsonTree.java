package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;

/** Sole raw-token parser for complete native, semantic and Driver material; StrictJson stays a receipt lane. */
public final class FullJsonTree {
    public static final int MAXIMUM_BYTES = 64 * 1024 * 1024;
    public static final int MAXIMUM_DRIVER_BYTES = 256 * 1024 * 1024;
    private static final JsonFactory FACTORY = JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64)
                    .maxStringLength(MAXIMUM_DRIVER_BYTES).maxNumberLength(MAXIMUM_DRIVER_BYTES).build()).build();
    private static final ObjectMapper JSON = new ObjectMapper(FACTORY);
    private FullJsonTree() { }

    /** No field normalization is applied. Decimal tokens, integer tokens, missing and null stay distinct. */
    public static JsonNode parse(byte[] original, int maximumBytes) {
        requireLimit(maximumBytes);
        StrictJson.require(original != null && original.length > 0 && original.length <= maximumBytes,
                "bounded complete JSON material required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(original)).toString();
            try (JsonParser parser = FACTORY.createParser(text)) {
                StrictJson.require(parser.nextToken() != null, "complete JSON value required");
                JsonNode result = read(parser, 0);
                StrictJson.require(parser.nextToken() == null, "trailing complete JSON rejected");
                return result;
            }
        } catch (IOException failure) { throw new IllegalArgumentException("invalid complete JSON material", failure); }
    }
    private static JsonNode read(JsonParser parser, int depth) throws IOException {
        StrictJson.require(depth <= 64, "bounded complete JSON depth required");
        var factory = JsonNodeFactory.instance;
        return switch (parser.currentToken()) {
            case START_OBJECT -> {
                var result = factory.objectNode();
                while (parser.nextToken() != JsonToken.END_OBJECT) {
                    StrictJson.require(parser.currentToken() == JsonToken.FIELD_NAME, "complete JSON member required");
                    String key = parser.currentName();
                    StrictJson.require(parser.nextToken() != null, "missing complete JSON value");
                    result.set(key, read(parser, depth + 1));
                }
                yield result;
            }
            case START_ARRAY -> {
                var result = factory.arrayNode();
                while (parser.nextToken() != JsonToken.END_ARRAY) {
                    StrictJson.require(parser.currentToken() != null, "incomplete complete JSON array");
                    result.add(read(parser, depth + 1));
                }
                yield result;
            }
            case VALUE_STRING -> factory.textNode(parser.getText());
            case VALUE_NUMBER_INT -> factory.numberNode(parser.getBigIntegerValue());
            case VALUE_NUMBER_FLOAT -> new DecimalTokenNode(parser.getText());
            case VALUE_TRUE -> factory.booleanNode(true);
            case VALUE_FALSE -> factory.booleanNode(false);
            case VALUE_NULL -> factory.nullNode();
            default -> throw new IllegalArgumentException("unsupported complete JSON token");
        };
    }
    public static byte[] encode(JsonNode normalized, int maximumBytes) {
        requireLimit(maximumBytes); validate(normalized, 0);
        try {
            byte[] result = JSON.writeValueAsBytes(normalized);
            StrictJson.require(result.length <= maximumBytes, "complete JSON material exceeds its explicit lease");
            return result;
        } catch (IOException failure) { throw new IllegalArgumentException("complete JSON encoding failed", failure); }
    }
    private static void requireLimit(int maximumBytes) {
        StrictJson.require(maximumBytes > 0 && maximumBytes <= MAXIMUM_DRIVER_BYTES, "finite complete JSON material lease required");
    }
    private static void validate(JsonNode value, int depth) {
        StrictJson.require(value != null && depth <= 64 && !value.isMissingNode(), "bounded complete JSON tree required");
        if (value.isContainerNode()) { value.forEach(child -> validate(child, depth + 1)); return; }
        StrictJson.require(value.isTextual() || value.isNumber() || value.isBoolean() || value.isNull(), "unsupported complete JSON node");
        if (value.isFloatingPointNumber() && !(value instanceof DecimalTokenNode)) {
            // Derived binary64 values must be finite; original opaque tokens are never rounded to test finiteness.
            if (value.isDouble() || value.isFloat()) StrictJson.require(Double.isFinite(value.doubleValue()), "finite derived JSON float required");
        }
    }
}
