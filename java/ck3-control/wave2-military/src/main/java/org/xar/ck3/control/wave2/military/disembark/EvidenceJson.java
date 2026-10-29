package org.xar.ck3.control.wave2.military.disembark;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Narrow immutable JSON evidence boundary. Decimal tokens never pass through double or the map integer-only emitter. */
public final class EvidenceJson {
    public static final int MAX_BYTES = 65_536;
    private static final JsonFactory FACTORY = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    private EvidenceJson() { }

    public sealed interface Value permits ObjectValue, ArrayValue, TextValue, IntegerValue, DecimalValue, BooleanValue, NullValue { }
    public record Member(String name, Value value) {
        public Member { Objects.requireNonNull(name); Objects.requireNonNull(value); }
    }
    public record ObjectValue(List<Member> members) implements Value {
        public ObjectValue {
            members = members.stream().sorted(Comparator.comparing(Member::name)).toList();
            Set<String> keys = new HashSet<>();
            for (Member member : members) {
                if (!keys.add(member.name())) { throw new IllegalArgumentException("duplicate evidence member"); }
            }
        }
        public Optional<Value> member(String key) {
            return members.stream().filter(member -> member.name().equals(key)).map(Member::value).findFirst();
        }
        public Value required(String key) {
            return member(key).orElseThrow(() -> new IllegalArgumentException("missing field: " + key));
        }
        public void exactFields(Set<String> keys) {
            Set<String> actual = new HashSet<>(); members.forEach(member -> actual.add(member.name()));
            if (!actual.equals(keys)) { throw new IllegalArgumentException("exact fields required: " + keys); }
        }
    }
    public record ArrayValue(List<Value> values) implements Value {
        public ArrayValue { values = List.copyOf(values); }
    }
    public record TextValue(String value) implements Value { public TextValue { Objects.requireNonNull(value); } }
    public record IntegerValue(BigInteger value) implements Value { public IntegerValue { Objects.requireNonNull(value); } }
    public record DecimalValue(String token) implements Value {
        public DecimalValue {
            Objects.requireNonNull(token);
            if (!token.matches("-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+(?:[eE][+-]?[0-9]+)?|[eE][+-]?[0-9]+)")) {
                throw new IllegalArgumentException("JSON decimal token required");
            }
            new BigDecimal(token);
        }
    }
    public record BooleanValue(boolean value) implements Value { }
    public enum NullValue implements Value { INSTANCE }

    public static Value parse(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_BYTES) { throw new IllegalArgumentException("bounded nonempty JSON required"); }
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            try (JsonParser parser = FACTORY.createParser(text)) {
                if (parser.nextToken() == null) { throw new IllegalArgumentException("JSON value required"); }
                Value value = read(parser, 0);
                if (parser.nextToken() != null) { throw new IllegalArgumentException("trailing JSON content"); }
                return value;
            }
        } catch (IOException error) { throw new IllegalArgumentException("invalid/duplicate UTF-8 JSON", error); }
    }

    public static byte[] encode(Value value) {
        try {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            try (JsonGenerator generator = FACTORY.createGenerator(output)) { write(generator, value); }
            byte[] bytes = output.toByteArray();
            if (bytes.length > MAX_BYTES) { throw new IllegalArgumentException("evidence JSON exceeds byte budget"); }
            return bytes;
        } catch (IOException error) { throw new IllegalArgumentException("cannot encode evidence JSON", error); }
    }

    public static ObjectValue object(Value value) {
        if (value instanceof ObjectValue object) { return object; }
        throw new IllegalArgumentException("JSON object required");
    }
    public static ObjectValue object(Member... members) { return new ObjectValue(List.of(members)); }
    public static Member member(String key, Value value) { return new Member(key, value); }
    public static TextValue text(String text) { return new TextValue(text); }
    public static IntegerValue integer(long value) { return new IntegerValue(BigInteger.valueOf(value)); }

    private static Value read(JsonParser parser, int depth) throws IOException {
        if (depth > 64) { throw new IllegalArgumentException("evidence JSON nesting exceeds budget"); }
        JsonToken token = parser.currentToken();
        if (token == JsonToken.START_OBJECT) {
            List<Member> members = new ArrayList<>();
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                if (parser.currentToken() != JsonToken.FIELD_NAME) { throw new IllegalArgumentException("object field required"); }
                String name = parser.currentName();
                if (parser.nextToken() == null) { throw new IllegalArgumentException("object field value required"); }
                members.add(new Member(name, read(parser, depth + 1)));
            }
            return new ObjectValue(members);
        }
        if (token == JsonToken.START_ARRAY) {
            List<Value> values = new ArrayList<>();
            while (parser.nextToken() != JsonToken.END_ARRAY) { values.add(read(parser, depth + 1)); }
            return new ArrayValue(values);
        }
        if (token == JsonToken.VALUE_STRING) { return new TextValue(parser.getText()); }
        if (token == JsonToken.VALUE_NUMBER_INT) { return new IntegerValue(parser.getBigIntegerValue()); }
        if (token == JsonToken.VALUE_NUMBER_FLOAT) { return new DecimalValue(parser.getText()); }
        if (token == JsonToken.VALUE_TRUE) { return new BooleanValue(true); }
        if (token == JsonToken.VALUE_FALSE) { return new BooleanValue(false); }
        if (token == JsonToken.VALUE_NULL) { return NullValue.INSTANCE; }
        throw new IllegalArgumentException("JSON value required");
    }

    private static void write(JsonGenerator generator, Value value) throws IOException {
        switch (value) {
            case ObjectValue object -> {
                generator.writeStartObject();
                for (Member member : object.members()) { generator.writeFieldName(member.name()); write(generator, member.value()); }
                generator.writeEndObject();
            }
            case ArrayValue array -> {
                generator.writeStartArray(); for (Value entry : array.values()) { write(generator, entry); } generator.writeEndArray();
            }
            case TextValue text -> generator.writeString(text.value());
            case IntegerValue integer -> generator.writeNumber(integer.value());
            case DecimalValue decimal -> generator.writeNumber(decimal.token());
            case BooleanValue bool -> generator.writeBoolean(bool.value());
            case NullValue ignored -> generator.writeNull();
        }
    }
}
