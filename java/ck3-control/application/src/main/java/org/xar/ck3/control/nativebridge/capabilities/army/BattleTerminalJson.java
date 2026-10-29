package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Narrow native JSON boundary. Widths remain native; no JS numeric conversion occurs here. */
final class BattleTerminalJson {
    private BattleTerminalJson() { }
    static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    static boolean nil(JsonNode value) { return value == null || value.isNull(); }
    static void require(boolean value, String field) { StrictJson.require(value, field); }
    static ObjectNode object(JsonNode value, String field, String... fields) {
        require(value != null && value.isObject(), field + ": object required");
        return StrictJson.object(value, Set.of(fields));
    }
    static ObjectNode extended(JsonNode value, String field, Set<String> required, Set<String> optional) {
        require(value != null && value.isObject(), field + ": object required");
        Set<String> fields = new HashSet<>(required);
        for (String name : optional) if (value.has(name)) fields.add(name);
        return StrictJson.object(value, fields);
    }
    static ArrayNode array(JsonNode value, String field) {
        require(value != null && value.isArray(), field + ": array required");
        return (ArrayNode) value;
    }
    static String text(JsonNode value, String field) {
        require(value != null && value.isTextual(), field + ": string required");
        return value.textValue();
    }
    static boolean bool(JsonNode value, String field) {
        require(value != null && value.isBoolean(), field + ": Boolean required");
        return value.booleanValue();
    }
    static Boolean optionalBool(JsonNode value, String field) { return nil(value) ? null : bool(value, field); }
    static BigInteger integer(JsonNode value, String field, BigInteger min, BigInteger max) {
        require(value != null && value.isIntegralNumber(), field + ": exact integer required");
        BigInteger actual = value.bigIntegerValue();
        require(actual.compareTo(min) >= 0 && actual.compareTo(max) <= 0, field + ": integer range");
        return actual;
    }
    static long integer(JsonNode value, String field, long min, long max) {
        return integer(value, field, BigInteger.valueOf(min), BigInteger.valueOf(max)).longValueExact();
    }
    static Integer i32(JsonNode value, String field) {
        return nil(value) ? null : Math.toIntExact(integer(value, field, Integer.MIN_VALUE, Integer.MAX_VALUE));
    }
    static Long i64(JsonNode value, String field) {
        return nil(value) ? null : integer(value, field, Long.MIN_VALUE, Long.MAX_VALUE);
    }
    static BigInteger u64(JsonNode value, String field) { return nil(value) ? null : integer(value, field, BigInteger.ZERO, U64); }
    static Integer positive(JsonNode value, String field) { return Math.toIntExact(integer(value, field, 1, Integer.MAX_VALUE)); }
    static Long optionalInteger(JsonNode value, String field, long min, long max) {
        return nil(value) ? null : integer(value, field, min, max);
    }
    static boolean allPresent(ObjectNode value, String... fields) {
        for (String field : fields) if (nil(value.get(field))) return false;
        return true;
    }
    static void numbers(JsonNode value, String field, long min, long max, boolean nullableEntries) {
        ArrayNode rows = array(value, field);
        for (int index = 0; index < rows.size(); index++) {
            if (nullableEntries && rows.get(index).isNull()) continue;
            integer(rows.get(index), field + "[" + index + "]", min, max);
        }
    }
    static boolean fixedI32(JsonNode value, String field, int size) {
        ArrayNode rows = array(value, field); require(rows.size() == size, field + ": native extent");
        boolean complete = true;
        for (int index = 0; index < size; index++) complete &= i32(rows.get(index), field + "[" + index + "]") != null;
        return complete;
    }
    static void reason(JsonNode value, String field, boolean ready) {
        if (ready) require(nil(value), field + ": ready reason must be null");
        else require(!text(value, field).isEmpty(), field + ": unavailable reason required");
    }
    static void availability(ObjectNode row, String field, String readyKey, String reasonKey, boolean complete) {
        String status = text(row.get("status"), field + ".status");
        require(Set.of("available", "partial", "unavailable").contains(status), field + ": availability status");
        boolean ready = bool(row.get(readyKey), field + "." + readyKey);
        require(ready == status.equals("available") && ready == complete, field + ": completeness disagrees");
        reason(row.get(reasonKey), field + "." + reasonKey, ready);
    }
    record PropertyBlock(ObjectNode wire, boolean complete) { }
    /** This native property shape uses count, unlike source census keys_count/values_count. */
    static PropertyBlock properties(JsonNode value, String field) {
        if (nil(value)) return new PropertyBlock(null, false);
        ObjectNode row = object(value, field, "count", "keys_u16", "values_q64");
        Integer count = i32(row.get("count"), field + ".count");
        for (String key : new String[] {"keys_u16", "values_q64"}) {
            JsonNode vector = row.get(key);
            if (!nil(vector)) {
                numbers(vector, field + "." + key, key.equals("keys_u16") ? 0 : Long.MIN_VALUE,
                        key.equals("keys_u16") ? 65535 : Long.MAX_VALUE, false);
                if (count != null) require(vector.size() == Math.max(0, count), field + ": native property extent");
            }
        }
        return new PropertyBlock(row, count != null && !nil(row.get("keys_u16")) && !nil(row.get("values_q64")));
    }
}
