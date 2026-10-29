package org.xar.ck3.control.wave2.planning.realmcompare;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

/** Narrow JSON tool entry. Runtime consumers may supply already-parsed typed DTOs. */
public final class RealmDifferenceCodec {
    // Two independently bounded 16,384-county components must fit together.
    // This is a separate collection profile, not the map's 64 KiB receipt ABI.
    public static final int MAX_BYTES = 512 * 1024;
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private RealmDifferenceCodec() { }

    /** Boundary-only immutable JSON values preserve all legacy unavailable branches and opaque extensions. */
    public record Request(JsonNode previous, JsonNode observation) {
        public Request {
            StrictJson.require(previous != null && observation != null, "explicit previous/observation JSON values required");
            previous = previous.deepCopy(); observation = observation.deepCopy();
        }
        @Override public JsonNode previous() { return previous.deepCopy(); }
        @Override public JsonNode observation() { return observation.deepCopy(); }
    }
    public static Request decodeRequest(byte[] input) {
        ObjectNode object = StrictJson.object(parse(input), Set.of("previous", "observation"));
        return new Request(object.get("previous"), object.get("observation"));
    }
    public static RealmDifference projectRequest(Request request) {
        StrictJson.require(request != null, "typed difference request required");
        return RealmDifference.compare(request.previous(), request.observation());
    }
    public static RealmDifference decodeAndCompare(byte[] input) { return projectRequest(decodeRequest(input)); }
    public static byte[] evaluate(byte[] input) { return encode(decodeAndCompare(input)); }
    public static byte[] encode(RealmDifference result) {
        StrictJson.require(result != null, "typed difference required");
        ObjectNode object = result.toJson();
        validateValues(object, 0);
        byte[] raw = SdkProjectionJson.encode(object, MAX_BYTES);
        parse(raw);
        return raw;
    }
    public static JsonNode parsedResult(RealmDifference result) { return parse(encode(result)); }

    private static JsonNode parse(byte[] raw) {
        StrictJson.require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded realm collection JSON required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode node = MAPPER.readTree(text);
            StrictJson.require(node != null, "realm collection JSON value required");
            return node;
        } catch (IOException error) {
            throw new ContractViolationException("invalid UTF-8 or duplicate realm collection JSON", error);
        }
    }

    private static void validateValues(JsonNode node, int depth) {
        StrictJson.require(node != null && depth <= 256, "bounded JSON value depth required");
        if (node.isObject()) {
            node.properties().forEach(entry -> {
                if (!entry.getKey().isEmpty()) { StrictJson.text(entry.getKey()); }
                validateValues(entry.getValue(), depth + 1);
            });
        } else if (node.isArray()) { node.forEach(entry -> validateValues(entry, depth + 1)); }
        else if (node.isTextual()) { if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); } }
        else if (node.isFloatingPointNumber()) {
            StrictJson.require(node.isBigDecimal() || Double.isFinite(node.doubleValue()), "finite JSON decimals required");
        } else { StrictJson.require(node.isIntegralNumber() || node.isBoolean() || node.isNull(), "ordinary JSON value required"); }
    }
}

