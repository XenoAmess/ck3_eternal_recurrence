package org.xar.ck3.control.application.planning.family;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Narrow validated JSON boundary. Missing, null, integer and boolean remain distinct. */
final class FamilyJson {
    private FamilyJson() { }
    static Obj object(Value value) { return OpportunityJson.object(value, "family object"); }
    static Obj decode(byte[] bytes) { return object(OpportunityJson.parse(bytes)); }
    /** Full canonical domain body budget is distinct from the planner's 128 KiB message budget. */
    static Obj decodeDomain(byte[] bytes) {
        OpportunityJson.require(bytes != null && bytes.length > 0 && bytes.length <= org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES, "bounded full family domain body required");
        var factory = com.fasterxml.jackson.core.JsonFactory.builder().enable(com.fasterxml.jackson.core.StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
        try (var parser = factory.createParser(bytes)) {
            OpportunityJson.require(parser.nextToken() != null, "family domain JSON required");
            Obj value = object(read(parser, 0)); OpportunityJson.require(parser.nextToken() == null, "single family domain document required"); return value;
        } catch (java.io.IOException error) { throw new IllegalArgumentException("invalid UTF-8 or family domain JSON", error); }
    }
    private static Value read(com.fasterxml.jackson.core.JsonParser parser, int depth) throws java.io.IOException {
        OpportunityJson.require(depth <= 32, "family JSON nesting exceeds32");
        return switch (parser.currentToken()) {
            case START_OBJECT -> {
                Map<String, Value> fields = new LinkedHashMap<>();
                while (parser.nextToken() != com.fasterxml.jackson.core.JsonToken.END_OBJECT) {
                    OpportunityJson.require(parser.currentToken() == com.fasterxml.jackson.core.JsonToken.FIELD_NAME, "family field required");
                    String key = parser.currentName(); OpportunityJson.require(parser.nextToken() != null, "family field value required");
                    OpportunityJson.require(fields.put(key, read(parser, depth + 1)) == null, "duplicate family field");
                }
                yield new Obj(fields);
            }
            case START_ARRAY -> {
                List<Value> items = new ArrayList<>();
                while (parser.nextToken() != com.fasterxml.jackson.core.JsonToken.END_ARRAY) items.add(read(parser, depth + 1));
                yield new Arr(items);
            }
            case VALUE_STRING -> new Text(parser.getText());
            case VALUE_NUMBER_INT -> new IntegerValue(parser.getBigIntegerValue());
            case VALUE_NUMBER_FLOAT -> new DecimalValue(parser.getText());
            case VALUE_TRUE -> new Bool(true);
            case VALUE_FALSE -> new Bool(false);
            case VALUE_NULL -> Nil.INSTANCE;
            default -> throw new IllegalArgumentException("family JSON value required");
        };
    }
    static List<Value> array(Value value) { return OpportunityJson.array(value, "family array"); }
    static String text(Value value) { return OpportunityJson.text(value, "family text"); }
    static String string(Value value) { return value instanceof Text t ? t.value() : null; }
    static BigInteger integer(Value value) { return OpportunityJson.integer(value, "family integer"); }
    static BigInteger positive(Value value) {
        BigInteger number = integer(value);
        OpportunityJson.require(number.signum() > 0, "positive family ID required"); return number;
    }
    static boolean yes(Value value) { return value instanceof Bool b && b.value(); }
    static boolean no(Value value) { return value instanceof Bool b && !b.value(); }
    static boolean eq(Value left, Value right) { return left != null && left.equals(right); }
    static boolean oneOf(Value value, String... choices) {
        String actual = string(value); if (actual == null) return false;
        for (String choice : choices) if (choice.equals(actual)) return true; return false;
    }
    static boolean material(Obj value) { return oneOf(value.get("status"), "marriage", "betrothal"); }
    static Value nil(Value value) { return value == null ? Nil.INSTANCE : value; }
    static Obj obj(Object... pairs) {
        if (pairs.length % 2 != 0) throw new IllegalArgumentException("key/value pairs required");
        Map<String, Value> result = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) {
            if (!(pairs[i] instanceof String key) || !(pairs[i + 1] instanceof Value value))
                throw new IllegalArgumentException("typed JSON pair required");
            if (result.put(key, value) != null) throw new IllegalArgumentException("duplicate JSON pair");
        }
        return new Obj(result);
    }
    static Text t(String value) { return new Text(value); }
    static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    static Arr rows(List<? extends Value> values) { return new Arr(new ArrayList<>(values)); }
    static Obj evidence(Obj original, String key, Value value) { return original.with(key, value); }
    static boolean sameEpisode(Obj record, Obj snapshot) { return eq(record.get("episode_run_id"), snapshot.get("episode_run_id")); }
    static boolean unpartnered(Obj relation) {
        return relation.get("betrothed_character_id") == Nil.INSTANCE
                && relation.get("primary_spouse_character_id") == Nil.INSTANCE
                && relation.get("spouse_character_ids") instanceof Arr a && a.items().isEmpty();
    }
    static byte[] bytes(Value value) { return OpportunityJson.encode(value); }
}
