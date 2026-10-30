package org.xar.ck3.control.planning.opportunity;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Immutable JSON domain for opaque, owner-defined proposal evidence; never arbitrary Java objects. */
public final class OpportunityJson {
    private OpportunityJson() { }
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build());
    public sealed interface Value permits Obj, Arr, Text, IntegerValue, DecimalValue, Bool, Nil { }
    public record Obj(Map<String, Value> members) implements Value {
        public Obj { members = Collections.unmodifiableMap(new LinkedHashMap<>(members)); }
        public Value get(String key) { return members.get(key); }
        public Obj with(String key, Value value) {
            Map<String, Value> copy = new LinkedHashMap<>(members); copy.put(key, value); return new Obj(copy);
        }
    }
    public record Arr(List<Value> items) implements Value { public Arr { items = List.copyOf(items); } }
    public record Text(String value) implements Value { }
    public record IntegerValue(BigInteger value) implements Value { }
    public record DecimalValue(String token) implements Value {
        public DecimalValue { DecimalTokenNode.requireToken(token); }
    }
    public record Bool(boolean value) implements Value { }
    public enum Nil implements Value { INSTANCE }

    public static Value parse(byte[] bytes) {
        require(bytes != null && bytes.length <= 131072, "request exceeds 128 KiB");
        return fromMaterialNode(FullJsonTree.parse(bytes,131072),0);
    }
    public static Value parseComplete(byte[] bytes, int maximumBytes) {
        return fromMaterialNode(FullJsonTree.parse(bytes, maximumBytes), 0);
    }
    private static Value fromMaterialNode(JsonNode node,int depth) {
        require(depth<=32,"JSON nesting exceeds 32");
        if(node.isObject()) {Map<String,Value> fields=new LinkedHashMap<>();node.properties().forEach(e->fields.put(e.getKey(),fromMaterialNode(e.getValue(),depth+1)));return new Obj(fields);}
        if(node.isArray()) {List<Value> items=new ArrayList<>();node.forEach(item->items.add(fromMaterialNode(item,depth+1)));return new Arr(items);}
        if(node.isTextual())return new Text(node.textValue());
        if(node.isIntegralNumber())return new IntegerValue(node.bigIntegerValue());
        if(node instanceof DecimalTokenNode token)return new DecimalValue(token.originalToken());
        if(node.isBoolean())return new Bool(node.booleanValue());
        require(node.isNull(),"unsupported JSON material node");return Nil.INSTANCE;
    }

    public static byte[] encode(Value value) {
        try {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            try (JsonGenerator generator = MAPPER.createGenerator(output)) { write(generator, value, 0); }
            return output.toByteArray();
        } catch (IOException e) { throw new IllegalArgumentException("JSON encoding failed", e); }
    }
    private static void write(JsonGenerator output, Value value, int depth) throws IOException {
        require(depth <= 32, "JSON nesting exceeds 32");
        if (value instanceof Obj object) {
            output.writeStartObject();
            for (var field : object.members().entrySet()) {
                output.writeFieldName(field.getKey()); write(output, field.getValue(), depth + 1);
            }
            output.writeEndObject();
        } else if (value instanceof Arr array) {
            output.writeStartArray(); for (Value item : array.items()) write(output, item, depth + 1); output.writeEndArray();
        } else if (value instanceof Text text) output.writeString(text.value());
        else if (value instanceof IntegerValue integer) output.writeNumber(integer.value());
        else if (value instanceof DecimalValue decimal) output.writeRawValue(decimal.token());
        else if (value instanceof Bool bool) output.writeBoolean(bool.value());
        else if (value == Nil.INSTANCE) output.writeNull();
        else throw new IllegalArgumentException("null Java value is not JSON null");
    }

    /** Tree and wire projections retain the same original floating token, including signed zero. */
    public static JsonNode toNode(Value value) {
        if (value instanceof Obj obj) {
            ObjectNode result = MAPPER.createObjectNode();
            obj.members().forEach((key, item) -> result.set(key, toNode(item))); return result;
        }
        if (value instanceof Arr arr) {
            var result = MAPPER.createArrayNode(); arr.items().forEach(item -> result.add(toNode(item))); return result;
        }
        if (value instanceof Text text) return MAPPER.getNodeFactory().textNode(text.value());
        if (value instanceof IntegerValue integer) return MAPPER.getNodeFactory().numberNode(integer.value());
        if (value instanceof DecimalValue decimal) return new DecimalTokenNode(decimal.token());
        if (value instanceof Bool bool) return MAPPER.getNodeFactory().booleanNode(bool.value());
        if (value == Nil.INSTANCE) return MAPPER.getNodeFactory().nullNode();
        throw new IllegalArgumentException("null Java value is not JSON null");
    }
    public static Obj object(Value value, String name) {
        require(value instanceof Obj, name + " must be an object"); return (Obj) value;
    }
    public static List<Value> array(Value value, String name) {
        require(value instanceof Arr, name + " must be an array"); return ((Arr) value).items();
    }
    public static String text(Value value, String name) {
        require(value instanceof Text && !((Text) value).value().isEmpty(), name + " must be nonempty text");
        return ((Text) value).value();
    }
    public static BigInteger integer(Value value, String name) {
        require(value instanceof IntegerValue, name + " must be an integer token"); return ((IntegerValue) value).value();
    }
    public static BigInteger nonnegative(Value value, String name) {
        BigInteger result = integer(value, name); require(result.signum() >= 0, name + " must be nonnegative"); return result;
    }
    public static boolean bool(Value value, String name) {
        require(value instanceof Bool, name + " must be a boolean"); return ((Bool) value).value();
    }
    public static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
