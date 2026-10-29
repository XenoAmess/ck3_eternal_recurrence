package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.*;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.List;

/** One checked JSON boundary. Memory integers never pass through binary floating point. */
public final class CombatJson {
    private CombatJson() { }
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    public static JsonNode parse(byte[] raw) {
        require(raw.length > 0 && raw.length <= 8 * 1024 * 1024, "bounded combat JSON required");
        try { JsonNode result = JSON.readTree(raw); require(result != null, "combat JSON value required"); return result; }
        catch (IOException error) { throw new CombatInputException("invalid combat JSON", error); }
    }
    public static ObjectNode object() { return JSON.createObjectNode(); }
    public static ArrayNode array() { return JSON.createArrayNode(); }
    static ObjectNode object(JsonNode node, String name) { require(node != null && node.isObject(), name + " must be an object"); return (ObjectNode) node; }
    static JsonNode field(JsonNode node, String key) { return node == null ? null : node.get(key); }
    static BigInteger integer(JsonNode node, String name) { require(node != null && node.isIntegralNumber(), name + " must be an integer"); return node.bigIntegerValue(); }
    static BigInteger positiveInteger(JsonNode node, String name) { BigInteger value = integer(node, name); require(positive(value), name + " must be positive"); return value; }
    private static BigInteger nonnegativeInt32(BigInteger value, String name) {
        require(value != null && value.signum() >= 0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                name + " must be a nonnegative int32 identity"); return value;
    }
    /** Canonical public_unit_contract: slot zero is a valid CUnit, never absent. */
    public static BigInteger publicCunitId(JsonNode node, String name) { return publicCunitId(integer(node, name), name); }
    public static BigInteger publicCunitId(BigInteger value, String name) { return nonnegativeInt32(value, name); }
    /** V2 owner/commander/knight CharacterID follows its nonnegative int32 producer. */
    public static BigInteger characterId(JsonNode node, String name) { return characterId(integer(node, name), name); }
    public static BigInteger characterId(BigInteger value, String name) { return nonnegativeInt32(value, name); }
    static int intValue(JsonNode node, String name) { try { return integer(node, name).intValueExact(); } catch (ArithmeticException error) { throw new CombatInputException(name + " exceeds index domain", error); } }
    static String text(JsonNode node, String name) { require(node != null && node.isTextual(), name + " must be a string"); return node.textValue(); }
    static boolean bool(JsonNode node, String name) { require(node != null && node.isBoolean(), name + " must be boolean"); return node.booleanValue(); }
    static boolean is(JsonNode node, String value) { return node != null && node.isTextual() && node.textValue().equals(value); }
    static boolean yes(JsonNode node) { return node != null && node.isBoolean() && node.booleanValue(); }
    static boolean no(JsonNode node) { return node != null && node.isBoolean() && !node.booleanValue(); }
    static boolean absentOrNull(JsonNode node) { return node == null || node.isNull(); }
    static List<JsonNode> elements(JsonNode node, String name) { require(node != null && node.isArray(), name + " must be an array"); var result = new ArrayList<JsonNode>(); node.forEach(result::add); return List.copyOf(result); }
    static List<BigInteger> ids(JsonNode node, String name) { var result = elements(node, name).stream().map(v -> publicCunitId(v, name)).toList(); require(result.size() == result.stream().distinct().count(), name + " repeats an ID"); return result; }
    static void available(JsonNode node, String name) { require(is(field(node, "status"), "available"), name + " is not available"); }
    static void scale(JsonNode node, String name) { require(integer(field(node, "scale"), name + ".scale").equals(SCALE), name + ".scale is not Q100000"); }
    static String sha256(byte[] bytes) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); } }
    public static byte[] canonical(JsonNode node) { StringBuilder result = new StringBuilder(); canonical(node, result); return result.toString().getBytes(StandardCharsets.UTF_8); }
    private static final Comparator<String> CODEPOINT_ORDER = (left, right) -> {
        int a = 0, b = 0; while (a < left.length() && b < right.length()) { int x = left.codePointAt(a), y = right.codePointAt(b); if (x != y) return Integer.compare(x, y); a += Character.charCount(x); b += Character.charCount(y); } return Integer.compare(left.length() - a, right.length() - b);
    };
    private static void canonical(JsonNode node, StringBuilder result) {
        require(node != null && !node.isMissingNode(), "missing value cannot be serialized");
        if (node.isObject()) {
            result.append('{'); var keys = new ArrayList<String>(); node.fieldNames().forEachRemaining(keys::add); keys.sort(CODEPOINT_ORDER);
            for (int i = 0; i < keys.size(); i++) { if (i > 0) result.append(','); quote(keys.get(i), result); result.append(':'); canonical(node.get(keys.get(i)), result); } result.append('}');
        } else if (node.isArray()) { result.append('['); for (int i = 0; i < node.size(); i++) { if (i > 0) result.append(','); canonical(node.get(i), result); } result.append(']'); }
        else if (node.isTextual()) quote(node.textValue(), result);
        else if (node.isIntegralNumber()) result.append(node.bigIntegerValue());
        else if (node.isFloatingPointNumber()) result.append(pythonFloat(node.doubleValue()));
        else if (node.isBoolean()) result.append(node.booleanValue()); else if (node.isNull()) result.append("null");
        else throw new CombatInputException("unsupported combat JSON prototype");
    }
    private static String pythonFloat(double value) {
        require(Double.isFinite(value), "nonfinite combat JSON number");
        if (value == 0.0) return Double.doubleToRawLongBits(value) < 0 ? "-0.0" : "0.0";
        // CPython repr selects the closest shortest decimal which round-trips.
        // Older Java Double.toString can choose a longer spelling (e.g. 1e23).
        BigDecimal exact = new BigDecimal(value), decimal = null;
        for (int precision = 1; precision <= 17; precision++) {
            BigDecimal candidate = exact.round(new MathContext(precision, RoundingMode.HALF_EVEN));
            int exponent = exact.precision() - exact.scale() - precision;
            BigDecimal unit = BigDecimal.ONE.scaleByPowerOfTen(exponent), closest = null;
            // At powers of two the round-trip interval is asymmetric. The
            // adjacent decimal can be valid even when the nearest one is not.
            for (BigDecimal alternative : List.of(candidate, candidate.subtract(unit), candidate.add(unit))) {
                if (alternative.stripTrailingZeros().precision() > precision
                        || Double.doubleToRawLongBits(Double.parseDouble(alternative.toString())) != Double.doubleToRawLongBits(value)) continue;
                int distance = closest == null ? -1 : alternative.subtract(exact).abs().compareTo(closest.subtract(exact).abs());
                if (closest == null || distance < 0 || distance == 0
                        && !alternative.scaleByPowerOfTen(-exponent).toBigIntegerExact().testBit(0)) closest = alternative;
            }
            if (closest != null) { decimal = closest.stripTrailingZeros(); break; }
        }
        require(decimal != null, "no round-trip combat number");
        double abs = Math.abs(value);
        if (abs >= .0001 && abs < 1.0e16) { String result = decimal.toPlainString(); return result.indexOf('.') < 0 ? result + ".0" : result; }
        String digits = decimal.unscaledValue().abs().toString(); int exponent = digits.length() - 1 - decimal.scale();
        return (value < 0 ? "-" : "") + digits.charAt(0) + (digits.length() > 1 ? "." + digits.substring(1) : "") + "e" + (exponent >= 0 ? "+" : "-") + String.format(java.util.Locale.ROOT, "%02d", Math.abs(exponent));
    }
    private static void quote(String value, StringBuilder target) {
        for (int i = 0; i < value.length(); i++) {
            char current = value.charAt(i);
            if (Character.isHighSurrogate(current)) {
                require(i + 1 < value.length() && Character.isLowSurrogate(value.charAt(++i)), "unpaired combat JSON surrogate");
            } else require(!Character.isLowSurrogate(current), "unpaired combat JSON surrogate");
        }
        try { target.append(JSON.writeValueAsString(value)); } catch (IOException error) { throw new IllegalStateException(error); }
    }
}
