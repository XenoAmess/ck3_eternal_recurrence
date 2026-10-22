package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.time.DateTimeException;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeSet;

/** Exact JSON boundary. No Jackson bean coercions or JavaScript Number domain. */
public final class StrictJson {
    public static final int INPUT_MAX_BYTES = 65_536;
    public static final int OUTPUT_MAX_BYTES = 16_384;
    public static final int EXPLICIT_MAX_BYTES = 1_048_576;
    public static final long MAX_SAFE_INTEGER = 9_007_199_254_740_991L;
    public static final BigInteger UINT64_MAX = new BigInteger("18446744073709551615");
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    private StrictJson() { }

    public static JsonNode parse(byte[] raw) {
        return parse(raw, INPUT_MAX_BYTES);
    }

    /** Explicit leaf budget; the default map input limit remains unchanged. */
    public static JsonNode parse(byte[] raw, int maximumBytes) {
        require(maximumBytes > 0 && maximumBytes <= EXPLICIT_MAX_BYTES, "explicit JSON input byte budget");
        require(raw != null && raw.length > 0 && raw.length <= maximumBytes, "bounded nonempty UTF-8 JSON required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode node = MAPPER.readTree(text);
            require(node != null, "JSON value required");
            return node;
        } catch (CharacterCodingException error) {
            throw new ContractViolationException("invalid UTF-8 JSON", error);
        } catch (IOException error) {
            throw new ContractViolationException("invalid or duplicate JSON fields", error);
        }
    }

    public static ObjectNode object(JsonNode node, Set<String> fields) {
        require(node instanceof ObjectNode, "JSON object required");
        ObjectNode result = (ObjectNode) node;
        Set<String> actual = new HashSet<>();
        result.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(fields), "exact JSON fields required: " + fields);
        return result;
    }

    public static ObjectNode object() { return MAPPER.createObjectNode(); }

    public static String text(JsonNode value) {
        require(value != null && value.isTextual(), "JSON string required");
        return text(value.textValue());
    }

    public static String text(String value) {
        require(value != null && !value.isEmpty() && value.codePointCount(0, value.length()) <= 32_768,
                "nonempty bounded text required");
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) {
                require(index + 1 < value.length() && Character.isLowSurrogate(value.charAt(index + 1)),
                        "unpaired Unicode surrogate");
                index++;
            } else {
                require(!Character.isLowSurrogate(current), "unpaired Unicode surrogate");
            }
        }
        return value;
    }

    public static BigInteger integer(JsonNode value, BigInteger minimum, BigInteger maximum) {
        require(value != null && value.isIntegralNumber(), "exact JSON integer required; no boolean, float or string");
        BigInteger result = value.bigIntegerValue();
        require(result.compareTo(minimum) >= 0 && result.compareTo(maximum) <= 0, "integer outside contract range");
        return result;
    }

    public static long integer(JsonNode value, long minimum, long maximum) {
        return integer(value, BigInteger.valueOf(minimum), BigInteger.valueOf(maximum)).longValueExact();
    }

    public static long safe(long value, long minimum) {
        require(value >= minimum && value <= MAX_SAFE_INTEGER, "safe integer outside contract range");
        return value;
    }

    public static void trueValue(JsonNode value) {
        require(value != null && value.isBoolean() && value.booleanValue(), "actual JSON true required");
    }

    public static String utc(String value) {
        text(value);
        try {
            String normalized = value;
            if (normalized.matches("[0-9]{8}[^0-9].+")) {
                normalized = LocalDate.parse(normalized.substring(0, 8), DateTimeFormatter.BASIC_ISO_DATE)
                        + normalized.substring(8);
            } else if (normalized.matches("[0-9]{4}-W[0-9]{2}-[0-9].+")) {
                normalized = LocalDate.parse(normalized.substring(0, 10), DateTimeFormatter.ISO_WEEK_DATE)
                        + normalized.substring(10);
            }
            if (normalized.length() > 10 && normalized.charAt(10) == ' ') {
                normalized = normalized.substring(0, 10) + "T" + normalized.substring(11);
            }
            if (normalized.length() >= 17 && normalized.substring(11, 17).matches("[0-9]{6}")) {
                normalized = normalized.substring(0, 13) + ":" + normalized.substring(13, 15)
                        + ":" + normalized.substring(15);
            }
            require(OffsetDateTime.parse(normalized).getOffset().equals(ZoneOffset.UTC), "UTC offset zero required");
        } catch (DateTimeException error) {
            throw new ContractViolationException("ISO UTC observation time required", error);
        }
        return value;
    }

    public static void require(boolean condition, String message) {
        if (!condition) { throw new ContractViolationException(message); }
    }

    /** Python json.dumps(ensure_ascii=False, sort_keys=True, separators=(',',':')). */
    public static byte[] canonical(JsonNode value) {
        return canonical(value, INPUT_MAX_BYTES);
    }

    public static byte[] canonical(JsonNode value, int maximumBytes) {
        require(maximumBytes > 0 && maximumBytes <= EXPLICIT_MAX_BYTES, "explicit JSON output byte budget");
        StringBuilder output = new StringBuilder();
        append(value, output);
        byte[] raw = output.toString().getBytes(StandardCharsets.UTF_8);
        require(raw.length <= maximumBytes, "canonical JSON exceeds shared receipt byte budget");
        return raw;
    }

    private static void append(JsonNode value, StringBuilder output) {
        require(value != null, "missing JSON node cannot be serialized as null");
        if (value.isObject()) {
            output.append('{');
            TreeSet<String> keys = new TreeSet<>();
            value.fieldNames().forEachRemaining(keys::add);
            boolean first = true;
            for (String key : keys) {
                if (!first) { output.append(','); }
                first = false;
                quote(key, output);
                output.append(':');
                append(value.get(key), output);
            }
            output.append('}');
        } else if (value.isArray()) {
            output.append('[');
            boolean first = true;
            for (JsonNode entry : value) {
                if (!first) { output.append(','); }
                first = false;
                append(entry, output);
            }
            output.append(']');
        } else if (value.isTextual()) {
            quote(value.textValue(), output);
        } else if (value.isIntegralNumber()) {
            output.append(value.bigIntegerValue());
        } else if (value.isBoolean()) {
            output.append(value.booleanValue() ? "true" : "false");
        } else if (value.isNull()) {
            output.append("null");
        } else {
            throw new ContractViolationException("non-integer JSON number is outside this canonical contract");
        }
    }

    private static void quote(String value, StringBuilder output) {
        // Empty strings are valid JSON values; contracts decide whether they are allowed.
        if (!value.isEmpty()) { text(value); }
        output.append('"');
        String hexadecimal = "0123456789abcdef";
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            switch (current) {
                case '"' -> output.append("\\\"");
                case '\\' -> output.append("\\\\");
                case '\b' -> output.append("\\b");
                case '\f' -> output.append("\\f");
                case '\n' -> output.append("\\n");
                case '\r' -> output.append("\\r");
                case '\t' -> output.append("\\t");
                default -> {
                    if (current < 0x20) {
                        output.append("\\u00").append(hexadecimal.charAt(current >> 4))
                                .append(hexadecimal.charAt(current & 15));
                    } else { output.append(current); }
                }
            }
        }
        output.append('"');
    }
}
