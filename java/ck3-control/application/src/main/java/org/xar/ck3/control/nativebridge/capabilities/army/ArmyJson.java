package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** The only JSON boundary in this group. No bean coercion, Number round trip, aliases, or mutable JSON in domain records. */
final class ArmyJson {
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(RawJson.MAXIMUM_BYTES).maxNumberLength(4300).maxNestingDepth(1000).build()).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private ArmyJson() { }
    static ObjectNode parse(byte[] input) {
        return object(parseValue(input, RawJson.MAXIMUM_BYTES));
    }
    /** One native-token boundary also serves array and scalar family projections within an explicit full-frame budget. */
    static JsonNode parseValue(byte[] input, int maximumBytes) {
        require(maximumBytes > 0 && maximumBytes <= RawJson.MAXIMUM_BYTES, "bounded native JSON byte budget required");
        require(input != null && input.length > 0 && input.length <= maximumBytes, "native JSON exceeds its requested byte budget");
        RawJson original = new RawJson(input);
        try {
            JsonNode result = MAPPER.readTree(original.bytes());
            require(result != null, "present native JSON value required"); return result;
        } catch (IOException error) { throw new IllegalArgumentException("invalid original native JSON", error); }
    }
    static byte[] bytes(JsonNode node) { try { return new RawJson(MAPPER.writeValueAsBytes(node)).bytes(); } catch (IOException error) { throw new IllegalArgumentException("native encoding failed", error); } }
    static ObjectNode empty() { return MAPPER.createObjectNode(); }
    static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "exact object required"); return (ObjectNode) node; }
    static ObjectNode closed(JsonNode node, String... fields) { ObjectNode result = object(node); require(names(result).equals(Set.of(fields)), "wrong, missing or invented native fields: " + names(result)); return result; }
    static Set<String> names(ObjectNode node) { Set<String> fields = new HashSet<>(); node.fieldNames().forEachRemaining(fields::add); return Set.copyOf(fields); }
    static void required(ObjectNode node, String... fields) { for (String name : fields) require(node.has(name), "missing required native field: " + name); }
    static JsonNode get(ObjectNode node, String field) { require(node.has(field), "missing native field: " + field); return node.get(field); }
    static String text(JsonNode node) { require(node != null && node.isTextual(), "exact string token required"); return node.textValue(); }
    static String nonempty(JsonNode node) { String value = text(node); require(!value.isEmpty(), "nonempty text required"); return value; }
    static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "exact boolean token required"); return node.booleanValue(); }
    static void yes(JsonNode node) { require(bool(node), "actual native true required"); }
    static void no(JsonNode node) { require(!bool(node), "actual native false required"); }
    static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "integer token required; bool/float/string forbidden"); return node.bigIntegerValue(); }
    static BigInteger range(JsonNode node, BigInteger minimum, BigInteger maximum) { BigInteger value = integer(node); require(value.compareTo(minimum) >= 0 && value.compareTo(maximum) <= 0, "integer outside native contract"); return value; }
    static int i32(JsonNode node) { return range(node, BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact(); }
    static long i64(JsonNode node) { return range(node, BigInteger.valueOf(Long.MIN_VALUE), BigInteger.valueOf(Long.MAX_VALUE)).longValueExact(); }
    static int nonnegative(JsonNode node) { int value = i32(node); require(value >= 0, "nonnegative int32 required"); return value; }
    static PublicUnitId unit(JsonNode node) { return new PublicUnitId(nonnegative(node)); }
    static PositiveId id(JsonNode node) { return new PositiveId(i32(node)); }
    static FullId full(JsonNode node) { return new FullId(i32(node)); }
    static UInt64 u64(JsonNode node) { return new UInt64(integer(node)); }
    static UInt64 positive(JsonNode node) { return UInt64.positive(integer(node)); }
    static HireId hire(JsonNode node) { return new HireId(range(node, BigInteger.ZERO, new BigInteger("4294967294")).longValueExact()); }
    static <T> Field<T> field(ObjectNode node, String name, Function<JsonNode,T> decode) { return !node.has(name) ? new Missing<>() : node.get(name).isNull() ? new NullValue<>() : new Present<>(decode.apply(node.get(name))); }
    static <T> Field<T> nullable(ObjectNode node, String name, Function<JsonNode,T> decode) { get(node, name); return field(node, name, decode); }
    static <T> List<T> array(JsonNode node, Function<JsonNode,T> decode) { require(node != null && node.isArray(), "array required"); List<T> result = new ArrayList<>(); for (JsonNode item : node) result.add(decode.apply(item)); return List.copyOf(result); }
    static List<PublicUnitId> units(JsonNode node) { return distinct(array(node, ArmyJson::unit), 0, 65536, "CUnit array"); }
    static void equal(JsonNode node, String value) { require(text(node).equals(value), "native literal mismatch: " + value); }
    static void equal(JsonNode node, BigInteger value) { require(integer(node).equals(value), "native frame/identity mismatch"); }
    static Availability availability(JsonNode node) { return switch (text(node)) { case "available" -> Availability.AVAILABLE; case "partial" -> Availability.PARTIAL; case "unavailable" -> Availability.UNAVAILABLE; case "absent" -> Availability.ABSENT; default -> throw new IllegalArgumentException("unknown native availability"); }; }
}
