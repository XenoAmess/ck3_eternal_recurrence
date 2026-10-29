package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** The existing continuity Python JSON domain, including finite binary64 leaves.
 * Coordinates still require integer tokens. Missing fields never become null.
 */
public final class ContinuityJson {
    public static final int DOCUMENT_MAX_BYTES = 65_536;
    public static final int TRANSPORT_MAX_BYTES = 262_144;
    /** Aggregate snapshot/event bound, including all inline domain producer metadata. */
    public static final int LEDGER_MAX_BYTES = 262_144;
    /** Explicit full domain bodies remain off-ledger and use the same JSON type/canonicalization contract. */
    public static final int DOMAIN_MAX_BYTES = 1_048_576;
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private ContinuityJson() { }

    public static ObjectNode parseObject(byte[] raw, int maximum) {
        // Reuse strict UTF-8, duplicate-key and finite input bounds at the boundary.
        StrictJson.parse(raw, maximum);
        try {
            JsonNode value = MAPPER.readTree(raw);
            ObjectNode row = object(value);
            canonical(row, maximum);
            return row;
        } catch (IOException error) {
            throw new ContractViolationException("invalid continuity JSON", error);
        }
    }

    public static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "continuity JSON object required");
        return (ObjectNode) value;
    }

    public static byte[] canonical(JsonNode value) { return canonical(value, isLedgerProfile(value) ? LEDGER_MAX_BYTES : DOCUMENT_MAX_BYTES); }

    public static byte[] canonical(JsonNode value, int maximum) {
        StrictJson.require(maximum > 0 && maximum <= DOMAIN_MAX_BYTES, "bounded continuity JSON");
        StringBuilder out = new StringBuilder();
        append(Objects.requireNonNull(value), out);
        byte[] raw = out.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(raw.length <= maximum, "continuity JSON exceeds byte budget");
        return raw;
    }

    public static boolean same(JsonNode left, JsonNode right) {
        return java.util.Arrays.equals(canonical(left, TRANSPORT_MAX_BYTES), canonical(right, TRANSPORT_MAX_BYTES));
    }

    public static String digest(JsonNode value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(canonical(value))); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    private static void append(JsonNode value, StringBuilder out) {
        if (value.isObject()) {
            List<String> keys = new ArrayList<>(); value.fieldNames().forEachRemaining(keys::add);
            keys.sort(ContinuityJson::compareCodePoints);
            out.append('{');
            for (int index = 0; index < keys.size(); index++) {
                if (index > 0) { out.append(','); }
                quote(keys.get(index), out); out.append(':'); append(value.get(keys.get(index)), out);
            }
            out.append('}');
        } else if (value.isArray()) {
            out.append('[');
            for (int index = 0; index < value.size(); index++) {
                if (index > 0) { out.append(','); } append(value.get(index), out);
            }
            out.append(']');
        } else if (value.isTextual()) { quote(value.textValue(), out); }
        else if (value.isIntegralNumber()) {
            out.append(StrictJson.integer(value, -StrictJson.MAX_SAFE_INTEGER, StrictJson.MAX_SAFE_INTEGER));
        } else if (value.isFloatingPointNumber()) {
            double number = value.doubleValue();
            StrictJson.require(Double.isFinite(number), "finite continuity JSON number");
            out.append(pythonFloat(number));
        } else if (value.isNull()) { out.append("null"); }
        else if (value.isBoolean()) { out.append(value.booleanValue()); }
        else { throw new ContractViolationException("continuity JSON type domain required"); }
    }

    private static void quote(String value, StringBuilder out) {
        out.append('"');
        String hex = "0123456789abcdef";
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
                    if (current < 0x20) {
                        out.append("\\u00").append(hex.charAt(current >> 4)).append(hex.charAt(current & 15));
                    } else if (Character.isHighSurrogate(current)) {
                        StrictJson.require(index + 1 < value.length() && Character.isLowSurrogate(value.charAt(index + 1)),
                                "unpaired continuity Unicode surrogate");
                        out.append(current).append(value.charAt(++index));
                    } else {
                        StrictJson.require(!Character.isLowSurrogate(current), "unpaired continuity Unicode surrogate");
                        out.append(current);
                    }
                }
            }
        }
        out.append('"');
    }

    /** Only aggregate ledger state/event documents use this finite profile; request/details remain bounded separately. */
    private static boolean isLedgerProfile(JsonNode value) {
        if (isLedgerState(value)) { return true; }
        if (!(value instanceof ObjectNode row) || row.size() != 7) { return false; }
        return row.has("sequence") && row.has("at_utc") && row.has("kind") && row.has("details")
                && row.has("identity") && row.has("previous_sha256") && isLedgerState(row.get("after"));
    }

    private static boolean isLedgerState(JsonNode value) {
        if (!(value instanceof ObjectNode row)) { return false; }
        JsonNode schema = row.get("schema");
        return schema != null && schema.isTextual() && (schema.textValue().equals("root.ck3.continuity-window/v1")
                || schema.textValue().equals(EpisodeWindow.STATE_SCHEMA)
                || schema.textValue().equals(FreshContinuityGenesis.STATE_SCHEMA));
    }

    private static int compareCodePoints(String left, String right) {
        int l = 0, r = 0;
        while (l < left.length() && r < right.length()) {
            int a = left.codePointAt(l), b = right.codePointAt(r);
            if (a != b) { return Integer.compare(a, b); }
            l += Character.charCount(a); r += Character.charCount(b);
        }
        return Integer.compare(left.length() - l, right.length() - r);
    }

    private static String pythonFloat(double number) {
        if (number == 0.0) { return Double.doubleToRawLongBits(number) < 0 ? "-0.0" : "0.0"; }
        BigDecimal exact = new BigDecimal(number), shortest = null;
        for (int precision = 1; precision <= 17; precision++) {
            // A power-of-two binary64 has asymmetric neighboring intervals. Check
            // both adjacent decimal candidates, then choose the closest/even one.
            for (RoundingMode mode : List.of(RoundingMode.FLOOR, RoundingMode.CEILING)) {
                BigDecimal candidate = exact.round(new MathContext(precision, mode)).stripTrailingZeros();
                if (Double.doubleToRawLongBits(Double.parseDouble(candidate.toString())) != Double.doubleToRawLongBits(number)) { continue; }
                int distance = shortest == null ? -1 : candidate.subtract(exact).abs().compareTo(shortest.subtract(exact).abs());
                if (distance < 0 || distance == 0 && !candidate.unscaledValue().testBit(0)) { shortest = candidate; }
            }
            if (shortest != null) { break; }
        }
        if (shortest == null) { throw new IllegalStateException("binary64 has no decimal round trip"); }
        int exponent = shortest.precision() - shortest.scale() - 1;
        if (exponent >= -4 && exponent < 16) {
            String plain = shortest.toPlainString();
            return plain.indexOf('.') < 0 ? plain + ".0" : plain;
        }
        String mantissa = shortest.movePointLeft(exponent).toPlainString();
        String digits = Integer.toString(Math.abs(exponent));
        return mantissa + "e" + (exponent >= 0 ? "+" : "-") + (digits.length() < 2 ? "0" : "") + digits;
    }
}
