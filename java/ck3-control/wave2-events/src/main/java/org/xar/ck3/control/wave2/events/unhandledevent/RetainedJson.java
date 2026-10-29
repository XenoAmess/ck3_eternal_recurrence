package org.xar.ck3.control.wave2.events.unhandledevent;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Immutable diagnostic JSON domain. Business identities are separately decoded as exact integers. */
public final class RetainedJson {
    private static final JsonFactory JSON = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    private RetainedJson() { }
    public sealed interface Value permits NullValue, BooleanValue, StringValue, IntegerValue, FloatingValue, ArrayValue, ObjectValue { }
    public record NullValue() implements Value { }
    public record BooleanValue(boolean value) implements Value { }
    public record StringValue(String value) implements Value {
        public StringValue { unicode(value); }
    }
    public record IntegerValue(BigInteger value) implements Value {
        public IntegerValue { Objects.requireNonNull(value, "integer"); }
    }
    /** Only opaque pre-existing diagnostic floats use the old Python binary64 JSON domain. */
    public record FloatingValue(double value) implements Value {
        public FloatingValue { StrictJson.require(Double.isFinite(value), "finite diagnostic float required"); }
    }
    public record ArrayValue(List<Value> values) implements Value {
        public ArrayValue { values = List.copyOf(values); }
    }
    public record ObjectValue(Map<String, Value> fields) implements Value {
        public ObjectValue {
            LinkedHashMap<String, Value> copy = new LinkedHashMap<>();
            fields.forEach((name, value) -> { unicode(name); copy.put(name, Objects.requireNonNull(value)); });
            fields = Collections.unmodifiableMap(copy);
        }
        public Value get(String name) { return fields.get(name); }
        public Value getOrNull(String name) { return fields.getOrDefault(name, NULL); }
        public boolean contains(String name) { return fields.containsKey(name); }
        public ObjectValue with(String name, Value value) {
            LinkedHashMap<String, Value> copy = new LinkedHashMap<>(fields); copy.put(name, value); return new ObjectValue(copy);
        }
        public ObjectValue project(List<String> names) {
            LinkedHashMap<String, Value> copy = new LinkedHashMap<>(); names.forEach(name -> copy.put(name, getOrNull(name))); return new ObjectValue(copy);
        }
    }
    public static final NullValue NULL = new NullValue();
    /** Explicit resource lease for callers retaining a complete large diagnostic source. */
    public record ParseBudget(long maximumInputBytes, long maximumVisitedValues, int maximumDepth) {
        public ParseBudget {
            StrictJson.require(maximumInputBytes > 0 && maximumVisitedValues > 0 && maximumDepth >= 0,
                    "positive retained parse resource budget required");
        }
    }
    public static Value parse(byte[] raw) {
        return parseBounded(raw, StrictJson.EXPLICIT_MAX_BYTES);
    }
    private static Value parseBounded(byte[] raw, int maximum) {
        return parse(raw, new ParseBudget(maximum, Long.MAX_VALUE, 128));
    }
    public static Value parse(byte[] raw, ParseBudget budget) {
        Objects.requireNonNull(budget, "retained parse budget");
        StrictJson.require(raw != null && raw.length > 0 && raw.length <= budget.maximumInputBytes(), "bounded retained JSON");
        try {
            var decoder = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT);
            try (JsonParser parser = JSON.createParser(new java.io.InputStreamReader(new java.io.ByteArrayInputStream(raw), decoder))) {
                JsonToken first = parser.nextToken(); StrictJson.require(first != null, "JSON value required");
                Value value = read(parser, first, 0, new ParseLease(budget)); StrictJson.require(parser.nextToken() == null, "trailing JSON"); return value;
            }
        } catch (IOException error) { throw new ContractViolationException("invalid retained JSON", error); }
    }
    private static final class ParseLease {
        private final ParseBudget budget;
        private long visited;
        private ParseLease(ParseBudget budget) { this.budget = budget; }
        private void visit(int depth) {
            StrictJson.require(depth <= budget.maximumDepth(), "retained JSON depth");
            StrictJson.require(visited < budget.maximumVisitedValues(), "retained parse resource lease exhausted");
            visited++;
        }
    }
    public static byte[] encode(Value value) {
        return encodeBounded(value, StrictJson.EXPLICIT_MAX_BYTES);
    }
    static byte[] encodeOfflineMetadata(Value value) { return encodeBounded(value, 2_097_152); }
    private static byte[] encodeBounded(Value value, int maximum) {
        Objects.requireNonNull(value, "value");
        try {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            try (JsonGenerator generator = JSON.createGenerator(bytes)) { write(generator, value); }
            StrictJson.require(bytes.size() <= maximum, "bounded retained JSON output"); return bytes.toByteArray();
        } catch (IOException error) { throw new IllegalStateException("retained JSON serialization failed", error); }
    }
    public static ObjectValue object(Value value) {
        StrictJson.require(value instanceof ObjectValue, "JSON object required"); return (ObjectValue) value;
    }
    public static String string(Value value) {
        if (value == null || value instanceof NullValue) return null;
        StrictJson.require(value instanceof StringValue, "string token required"); return ((StringValue) value).value();
    }
    public static BigInteger integer(Value value) {
        if (value == null || value instanceof NullValue) return null;
        StrictJson.require(value instanceof IntegerValue, "integer token required; no boolean/float/string"); return ((IntegerValue) value).value();
    }
    public static Boolean bool(Value value) {
        if (value == null || value instanceof NullValue) return null;
        StrictJson.require(value instanceof BooleanValue, "boolean token required"); return ((BooleanValue) value).value();
    }
    public static Value value(String value) { return value == null ? NULL : new StringValue(value); }
    public static Value value(BigInteger value) { return value == null ? NULL : new IntegerValue(value); }
    public static Value value(Boolean value) { return value == null ? NULL : new BooleanValue(value); }

    private static Value read(JsonParser parser, JsonToken token, int depth, ParseLease lease) throws IOException {
        lease.visit(depth);
        return switch (token) {
            case VALUE_NULL -> NULL;
            case VALUE_TRUE -> new BooleanValue(true);
            case VALUE_FALSE -> new BooleanValue(false);
            case VALUE_STRING -> new StringValue(parser.getText());
            case VALUE_NUMBER_INT -> new IntegerValue(parser.getBigIntegerValue());
            case VALUE_NUMBER_FLOAT -> new FloatingValue(parser.getDoubleValue());
            case START_ARRAY -> {
                List<Value> values = new ArrayList<>(); JsonToken next;
                while ((next = parser.nextToken()) != JsonToken.END_ARRAY) { StrictJson.require(next != null, "unterminated JSON array"); values.add(read(parser, next, depth + 1, lease)); }
                yield new ArrayValue(values);
            }
            case START_OBJECT -> {
                LinkedHashMap<String, Value> values = new LinkedHashMap<>(); JsonToken next;
                while ((next = parser.nextToken()) != JsonToken.END_OBJECT) {
                    StrictJson.require(next == JsonToken.FIELD_NAME, "object field required"); String name = parser.currentName();
                    JsonToken child = parser.nextToken(); StrictJson.require(child != null, "field value required"); values.put(name, read(parser, child, depth + 1, lease));
                }
                yield new ObjectValue(values);
            }
            default -> throw new ContractViolationException("unsupported JSON token");
        };
    }
    private static void write(JsonGenerator generator, Value value) throws IOException {
        switch (value) {
            case NullValue ignored -> generator.writeNull();
            case BooleanValue bool -> generator.writeBoolean(bool.value());
            case StringValue text -> generator.writeString(text.value());
            case IntegerValue integer -> generator.writeNumber(integer.value());
            case FloatingValue floating -> generator.writeNumber(floating.value());
            case ArrayValue array -> { generator.writeStartArray(); for (Value item : array.values()) write(generator, item); generator.writeEndArray(); }
            case ObjectValue object -> { generator.writeStartObject(); for (Map.Entry<String, Value> field : object.fields().entrySet()) { generator.writeFieldName(field.getKey()); write(generator, field.getValue()); } generator.writeEndObject(); }
        }
    }
    /** Explicit resource lease for the Python diagnostic lane; no business-domain byte cap is introduced. */
    public record CanonicalBudget(long maximumOutputBytes, long maximumVisitedValues, int maximumDepth) {
        public CanonicalBudget {
            StrictJson.require(maximumOutputBytes > 0 && maximumOutputBytes <= Integer.MAX_VALUE - 8L
                    && maximumVisitedValues > 0 && maximumDepth >= 0, "finite canonical resource budget required");
        }
    }
    /** Only the shared canonical producer can create a body/digest pair. */
    public static final class CanonicalForm {
        private final byte[] bytes;
        private final String sha256;
        private CanonicalForm(byte[] bytes) {
            this.bytes = bytes;
            try { this.sha256 = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)); }
            catch (java.security.NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
        }
        public byte[] bytes() { return bytes.clone(); }
        public String sha256() { return sha256; }
        public int size() { return bytes.length; }
    }
    /**
     * Python json.dumps(ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).
     * Default retained parse/encode and all old business parsers are unchanged. Opaque floats retain
     * their finite binary64 and negative-zero domain; object keys sort by Unicode scalar value.
     */
    public static CanonicalForm pythonCanonical(Value value, CanonicalBudget budget) {
        Objects.requireNonNull(value); Objects.requireNonNull(budget);
        PythonCanonicalWriter writer = new PythonCanonicalWriter(budget); writer.value(value, 0);
        return new CanonicalForm(writer.bytes.toByteArray());
    }
    private static final class PythonCanonicalWriter {
        private static final char[] HEX = "0123456789abcdef".toCharArray();
        private final CanonicalBudget budget;
        private final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        private final java.util.IdentityHashMap<Value,Boolean> active = new java.util.IdentityHashMap<>();
        private long visited;
        private PythonCanonicalWriter(CanonicalBudget budget) { this.budget = budget; }
        private void value(Value value, int depth) {
            StrictJson.require(depth <= budget.maximumDepth() && ++visited <= budget.maximumVisitedValues(), "canonical resource lease exhausted");
            boolean container = value instanceof ArrayValue || value instanceof ObjectValue;
            if (container) StrictJson.require(active.put(value, Boolean.TRUE) == null, "cyclic object is outside JSON canonical domain");
            switch (value) {
                case NullValue ignored -> raw("null");
                case BooleanValue bool -> raw(bool.value() ? "true" : "false");
                case StringValue text -> string(text.value());
                case IntegerValue integer -> {
                    long lowerDecimalDigits = Math.max(1L, ((Math.max(1, integer.value().bitLength()) - 1L) * 1233L) / 4096L);
                    StrictJson.require(lowerDecimalDigits <= budget.maximumOutputBytes() - bytes.size(), "canonical integer resource lease exhausted");
                    raw(integer.value().toString());
                }
                case FloatingValue floating -> raw(pythonDouble(floating.value()));
                case ArrayValue array -> {
                    raw("["); boolean first = true;
                    for (Value item : array.values()) { if (!first) raw(","); first = false; value(item, depth + 1); }
                    raw("]");
                }
                case ObjectValue object -> {
                    List<String> names = new ArrayList<>(object.fields().keySet()); names.sort(RetainedJson::compareCodePoints);
                    raw("{"); boolean first = true;
                    for (String name : names) {
                        if (!first) raw(","); first = false; string(name); raw(":"); value(object.get(name), depth + 1);
                    }
                    raw("}");
                }
            }
            if (container) active.remove(value);
        }
        private void string(String value) {
            raw("\""); StringBuilder pending = new StringBuilder();
            for (int offset = 0; offset < value.length();) {
                int codePoint = value.codePointAt(offset); offset += Character.charCount(codePoint);
                String escaped = switch (codePoint) {
                    case '"' -> "\\\"";
                    case '\\' -> "\\\\";
                    case '\b' -> "\\b";
                    case '\f' -> "\\f";
                    case '\n' -> "\\n";
                    case '\r' -> "\\r";
                    case '\t' -> "\\t";
                    default -> codePoint < 32 ? "\\u00" + HEX[(codePoint >>> 4) & 15] + HEX[codePoint & 15] : null;
                };
                if (escaped != null) {
                    if (!pending.isEmpty()) { raw(pending.toString()); pending.setLength(0); }
                    raw(escaped);
                } else {
                    pending.appendCodePoint(codePoint);
                    if (pending.length() >= 4096) { raw(pending.toString()); pending.setLength(0); }
                }
            }
            if (!pending.isEmpty()) raw(pending.toString()); raw("\"");
        }
        private void raw(String value) {
            byte[] utf8 = value.getBytes(StandardCharsets.UTF_8);
            StrictJson.require((long) bytes.size() + utf8.length <= budget.maximumOutputBytes(), "canonical output resource lease exhausted");
            bytes.writeBytes(utf8);
        }
    }
    private static int compareCodePoints(String left, String right) {
        int first = 0, second = 0;
        while (first < left.length() && second < right.length()) {
            int a = left.codePointAt(first), b = right.codePointAt(second);
            if (a != b) return Integer.compare(a, b);
            first += Character.charCount(a); second += Character.charCount(b);
        }
        return Integer.compare(left.length() - first, right.length() - second);
    }
    /** Closest shortest decimal that round-trips to the actual binary64; Java's display spelling is not used as Python repr. */
    private static String pythonDouble(double value) {
        StrictJson.require(Double.isFinite(value), "finite Python JSON float required");
        if (value == 0.0) return Double.doubleToRawLongBits(value) == Long.MIN_VALUE ? "-0.0" : "0.0";
        boolean negative = value < 0;
        double positive = Math.abs(value);
        java.math.BigDecimal exact = new java.math.BigDecimal(positive);
        java.math.BigDecimal chosen = null;
        for (int precision = 1; precision <= 17 && chosen == null; precision++) {
            java.math.BigDecimal closest = null, distance = null;
            for (java.math.RoundingMode rounding : List.of(java.math.RoundingMode.FLOOR, java.math.RoundingMode.CEILING)) {
                java.math.BigDecimal candidate = exact.round(new java.math.MathContext(precision, rounding)).stripTrailingZeros();
                if (Double.doubleToRawLongBits(Double.parseDouble(candidate.toString())) != Double.doubleToRawLongBits(positive)) continue;
                java.math.BigDecimal delta = exact.subtract(candidate).abs();
                int comparison = distance == null ? -1 : delta.compareTo(distance);
                if (closest == null || comparison < 0 || comparison == 0 && !candidate.unscaledValue().testBit(0)) {
                    closest = candidate; distance = delta;
                }
            }
            chosen = closest;
        }
        if (chosen == null) throw new IllegalStateException("finite binary64 shortest decimal not found");
        String digits = chosen.unscaledValue().abs().toString();
        int exponent = digits.length() - 1 - chosen.scale(); String number;
        if (exponent >= -4 && exponent < 16) {
            number = chosen.toPlainString(); if (chosen.scale() <= 0) number += ".0";
        } else {
            String mantissa = digits.length() == 1 ? digits : digits.charAt(0) + "." + digits.substring(1);
            int magnitude = Math.abs(exponent);
            number = mantissa + "e" + (exponent < 0 ? "-" : "+") + (magnitude < 10 ? "0" : "") + magnitude;
        }
        return negative ? "-" + number : number;
    }
    private static void unicode(String value) {
        Objects.requireNonNull(value, "JSON string");
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) { StrictJson.require(index + 1 < value.length() && Character.isLowSurrogate(value.charAt(index + 1)), "unpaired Unicode surrogate"); index++; }
            else StrictJson.require(!Character.isLowSurrogate(current), "unpaired Unicode surrogate");
        }
    }
}
