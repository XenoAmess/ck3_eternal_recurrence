package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleTerminalJson.*;

/** Original terminal raw numeric, auxiliary scratch and nine cache-byte input normalizers. */
final class BattleTerminalNumericCodec {
    private BattleTerminalNumericCodec() { }
    static JsonNode normalize(JsonNode value, String field) {
        if (nil(value)) return NullNode.instance;
        ObjectNode row = extended(value, field, Set.of("status", "raw_numeric_inputs_ready", "character_id", "scratch_present",
                "context_source", "base_points", "caps", "prowess_adjustment", "category_counts", "scratch_factor_numerator",
                "scratch_factor_denominator", "context", "unavailable_reason"), Set.of("auxiliary_scratch_inputs", "nine_cache_byte_inputs"));
        positive(row.get("character_id"), field + ".character_id");
        Boolean scratch = optionalBool(row.get("scratch_present"), field + ".scratch_present");
        boolean numbersComplete = fixedI32(row.get("base_points"), field + ".base_points", 6);
        numbersComplete &= fixedI32(row.get("caps"), field + ".caps", 6);
        numbersComplete &= fixedI32(row.get("category_counts"), field + ".category_counts", 4);
        for (String key : new String[] {"prowess_adjustment", "scratch_factor_numerator", "scratch_factor_denominator"})
            numbersComplete &= i32(row.get(key), field + "." + key) != null;
        String source = text(row.get("context_source"), field + ".context_source");
        require(Set.of("model_inline", "fallback_static", "not_required_no_scratch", "unavailable").contains(source), field + ": context source");
        boolean contextComplete = context(row.get("context"), field + ".context");
        boolean complete = Boolean.FALSE.equals(scratch) || Boolean.TRUE.equals(scratch) && contextComplete && numbersComplete;
        availability(row, field, "raw_numeric_inputs_ready", "unavailable_reason", complete);
        ObjectNode result = row.deepCopy();
        if (row.has("auxiliary_scratch_inputs")) result.set("auxiliary_scratch_inputs", auxiliary(row.get("auxiliary_scratch_inputs"), field + ".auxiliary_scratch_inputs", scratch));
        if (row.has("nine_cache_byte_inputs")) result.set("nine_cache_byte_inputs", nine(row.get("nine_cache_byte_inputs"), field + ".nine_cache_byte_inputs", scratch));
        return result;
    }
    private static boolean context(JsonNode value, String field) {
        if (nil(value)) return false;
        ObjectNode row = object(value, field, "aggregate_properties", "weighted_count", "weighted_rows");
        boolean aggregate = properties(row.get("aggregate_properties"), field + ".aggregate_properties").complete();
        Integer count = i32(row.get("weighted_count"), field + ".weighted_count");
        boolean complete = !nil(row.get("weighted_rows"));
        if (complete) {
            ArrayNode rows = array(row.get("weighted_rows"), field + ".weighted_rows");
            if (count != null) require(rows.size() == Math.max(0, count), field + ": weighted extent");
            for (int index = 0; index < rows.size(); index++) {
                String name = field + ".weighted_rows[" + index + "]";
                ObjectNode current = object(rows.get(index), name, "native_index", "properties", "weight_q64");
                integer(current.get("native_index"), name + ".native_index", index, index);
                complete &= i64(current.get("weight_q64"), name + ".weight_q64") != null;
                complete &= properties(current.get("properties"), name + ".properties").complete();
            }
        }
        return aggregate && count != null && complete;
    }
    private static JsonNode auxiliary(JsonNode value, String field, Boolean scratch) {
        if (nil(value)) return NullNode.instance;
        ObjectNode row = object(value, field, "status", "ready", "base430_q64", "base438_q64", "selector_flag_raw", "selector_metric_raw",
                "selected_low_threshold_raw", "selected_high_threshold_raw", "prepared430_q64", "prepared438_q64", "copied430_q64",
                "copied438_q64", "ready440_raw", "unavailable_reason");
        for (String key : new String[] {"base430_q64", "base438_q64", "prepared430_q64", "prepared438_q64", "copied430_q64", "copied438_q64"}) i64(row.get(key), field + "." + key);
        for (String key : new String[] {"selector_flag_raw", "ready440_raw"}) optionalInteger(row.get(key), field + "." + key, 0, 255);
        Long metric = optionalInteger(row.get("selector_metric_raw"), field + ".selector_metric_raw", Short.MIN_VALUE, Short.MAX_VALUE);
        Integer low = i32(row.get("selected_low_threshold_raw"), field + ".selected_low_threshold_raw");
        Integer high = i32(row.get("selected_high_threshold_raw"), field + ".selected_high_threshold_raw");
        boolean present = allPresent(row, "base430_q64", "base438_q64", "selector_flag_raw", "selector_metric_raw", "selected_low_threshold_raw",
                "prepared430_q64", "prepared438_q64", "copied430_q64", "copied438_q64", "ready440_raw");
        boolean complete = Boolean.FALSE.equals(scratch) || Boolean.TRUE.equals(scratch) && present && (metric < low || high != null);
        availability(row, field, "ready", "unavailable_reason", complete);
        return row.deepCopy();
    }
    private static JsonNode nine(JsonNode value, String field, Boolean scratch) {
        if (nil(value)) return NullNode.instance;
        ObjectNode row = object(value, field, "status", "ready", "model_present", "aggregate_properties", "carrier278_present", "carrier278_magic_raw",
                "linked20_present", "used_native_definition_fallback", "selected_definition_present", "selected_definition_magic_raw",
                "selected_definition_keys_u16", "current_cache_present", "current_cache_bytes", "unavailable_reason");
        for (String key : new String[] {"model_present", "carrier278_present", "linked20_present", "used_native_definition_fallback", "selected_definition_present", "current_cache_present"}) optionalBool(row.get(key), field + "." + key);
        Long first = optionalInteger(row.get("carrier278_magic_raw"), field + ".carrier278_magic_raw", 0, 0xffff_ffffL);
        Long second = optionalInteger(row.get("selected_definition_magic_raw"), field + ".selected_definition_magic_raw", 0, 0xffff_ffffL);
        for (String key : new String[] {"selected_definition_keys_u16", "current_cache_bytes"}) if (!nil(row.get(key))) {
            require(array(row.get(key), field + "." + key).size() == 9, field + ": nine native occurrences required");
            numbers(row.get(key), field + "." + key, key.equals("current_cache_bytes") ? -128 : 0, key.equals("current_cache_bytes") ? 127 : 65535, false);
        }
        boolean propertyComplete = properties(row.get("aggregate_properties"), field + ".aggregate_properties").complete();
        Boolean linked = optionalBool(row.get("linked20_present"), field + ".linked20_present");
        Boolean fallback = optionalBool(row.get("used_native_definition_fallback"), field + ".used_native_definition_fallback");
        boolean optionalComplete = Boolean.TRUE.equals(optionalBool(row.get("carrier278_present"), field)) && first != null
                && (first != 0x41495374L || linked != null && java.util.Objects.equals(fallback, Boolean.FALSE.equals(linked))
                && Boolean.TRUE.equals(optionalBool(row.get("selected_definition_present"), field)) && second != null
                && (second != 0x4744624fL || !nil(row.get("selected_definition_keys_u16"))));
        boolean complete = Boolean.FALSE.equals(scratch) || Boolean.TRUE.equals(scratch)
                && Boolean.TRUE.equals(optionalBool(row.get("model_present"), field)) && propertyComplete && optionalComplete;
        availability(row, field, "ready", "unavailable_reason", complete);
        return row.deepCopy();
    }
}
