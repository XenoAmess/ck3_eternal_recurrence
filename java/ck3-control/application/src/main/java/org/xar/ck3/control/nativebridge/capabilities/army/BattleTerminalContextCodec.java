package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleTerminalJson.*;

/** Original terminal title census, branch, provider-prefix and stored-array observations. */
final class BattleTerminalContextCodec {
    private BattleTerminalContextCodec() { }
    static JsonNode branch(JsonNode value, String field) {
        if (nil(value)) return NullNode.instance;
        ObjectNode row = extended(value, field, Set.of("status", "ready", "character_id", "flag14", "selected_index", "selected_property_block",
                "group_counts", "group_property_blocks", "unavailable_reason"), Set.of("census_inputs"));
        Integer actor = positive(row.get("character_id"), field + ".character_id");
        Boolean flag = optionalBool(row.get("flag14"), field + ".flag14");
        Integer selected = i32(row.get("selected_index"), field + ".selected_index");
        boolean property = properties(row.get("selected_property_block"), field + ".selected_property_block").complete();
        ArrayNode counts = array(row.get("group_counts"), field + ".group_counts");
        ArrayNode blocks = array(row.get("group_property_blocks"), field + ".group_property_blocks");
        require(counts.size() == 7 && blocks.size() == 7, field + ": seven native groups required");
        boolean complete = flag != null && (Boolean.FALSE.equals(flag) || selected != null && property);
        for (int index = 0; index < 7; index++) {
            Integer count = i32(counts.get(index), field + ".group_counts[" + index + "]");
            boolean block = properties(blocks.get(index), field + ".group_property_blocks[" + index + "]").complete();
            complete &= count != null && (count <= 0 || block);
        }
        availability(row, field, "ready", "unavailable_reason", complete);
        ObjectNode result = row.deepCopy();
        if (row.has("census_inputs")) {
            JsonNode census = census(row.get("census_inputs"), field + ".census_inputs");
            if (!nil(census)) require(census.get("character_id").intValue() == actor, field + ": census receiver differs");
            result.set("census_inputs", census);
        }
        return result;
    }
    static JsonNode census(JsonNode value, String field) {
        if (nil(value)) return NullNode.instance;
        ObjectNode row = object(value, field, "status", "ready", "character_id", "scratch_present", "model_present", "model_owner_present",
                "model_owner_full_character_id_raw_i32", "model_owner_matches_character", "model_magic_raw_u32", "header_source",
                "title_count_raw_i32", "title_occurrences", "unavailable_reason");
        positive(row.get("character_id"), field + ".character_id");
        boolean scratch = bool(row.get("scratch_present"), field + ".scratch_present");
        Boolean model = optionalBool(row.get("model_present"), field + ".model_present");
        Boolean owner = optionalBool(row.get("model_owner_present"), field + ".model_owner_present");
        Boolean matches = optionalBool(row.get("model_owner_matches_character"), field + ".model_owner_matches_character");
        Integer ownerId = i32(row.get("model_owner_full_character_id_raw_i32"), field + ".model_owner_full_character_id_raw_i32");
        Long magic = optionalInteger(row.get("model_magic_raw_u32"), field + ".model_magic_raw_u32", 0, 0xffff_ffffL);
        Integer count = i32(row.get("title_count_raw_i32"), field + ".title_count_raw_i32");
        require(Set.of("landed", "static").contains(text(row.get("header_source"), field)), field + ": header source");
        boolean complete = count != null && count >= 0;
        if (scratch) {
            complete &= model != null;
            if (Boolean.TRUE.equals(model)) {
                complete &= owner != null && matches != null;
                if (Boolean.TRUE.equals(owner)) complete &= ownerId != null;
                if (Boolean.TRUE.equals(matches)) complete &= magic != null;
            }
        }
        JsonNode rawRows = row.get("title_occurrences");
        if (nil(rawRows)) complete = false;
        else {
            ArrayNode rows = array(rawRows, field + ".title_occurrences");
            if (count != null) require(rows.size() == Math.max(0, count), field + ": title occurrence count");
            for (int index = 0; index < rows.size(); index++) {
                String name = field + ".title_occurrences[" + index + "]";
                ObjectNode current = object(rows.get(index), name, "native_row_index", "requested_full_title_id_raw_i32", "resolution",
                        "resolved_full_title_id_raw_i32", "qualifier_1d8_raw_u8", "qualifier_130_raw_u8", "qualifier_12c_raw_i32", "government_bit14", "template_tier_raw_i32");
                integer(current.get("native_row_index"), name + ".native_row_index", index, index);
                integer(current.get("requested_full_title_id_raw_i32"), name + ".requested_full_title_id_raw_i32", Integer.MIN_VALUE, Integer.MAX_VALUE);
                Integer resolved = i32(current.get("resolved_full_title_id_raw_i32"), name + ".resolved_full_title_id_raw_i32");
                Long q1 = optionalInteger(current.get("qualifier_1d8_raw_u8"), name + ".qualifier_1d8_raw_u8", 0, 255);
                Long q2 = optionalInteger(current.get("qualifier_130_raw_u8"), name + ".qualifier_130_raw_u8", 0, 255);
                Integer q3 = i32(current.get("qualifier_12c_raw_i32"), name + ".qualifier_12c_raw_i32");
                Boolean government = optionalBool(current.get("government_bit14"), name + ".government_bit14");
                Integer tier = i32(current.get("template_tier_raw_i32"), name + ".template_tier_raw_i32");
                String resolution = text(current.get("resolution"), name + ".resolution");
                require(Set.of("matched", "fallback", "unavailable").contains(resolution), name + ": resolution");
                boolean rowComplete = !resolution.equals("unavailable") && resolved != null;
                boolean demanded = rowComplete;
                if (demanded) { rowComplete &= q1 != null; demanded = q1 != null && q1 == 0; }
                if (demanded) { rowComplete &= q2 != null; demanded = q2 != null && q2 == 0; }
                if (demanded) { rowComplete &= q3 != null; demanded = q3 != null && q3 == -1; }
                if (demanded) { rowComplete &= government != null; if (Boolean.TRUE.equals(government)) rowComplete &= tier != null; }
                complete &= rowComplete;
            }
        }
        availability(row, field, "ready", "unavailable_reason", complete);
        return row.deepCopy();
    }
    static JsonNode prior(JsonNode value, String field) {
        if (nil(value)) return NullNode.instance;
        ObjectNode row = object(value, field, "available", "reason", "character_full_id", "base_property_block", "common_property_blocks", "selector", "selected_property_blocks");
        positive(row.get("character_full_id"), field + ".character_full_id");
        boolean base = provider(row.get("base_property_block"), field + ".base_property_block");
        boolean common = providers(row.get("common_property_blocks"), field + ".common_property_blocks");
        boolean selected = providers(row.get("selected_property_blocks"), field + ".selected_property_blocks");
        ObjectNode selector = object(row.get("selector"), field + ".selector", "available", "uses_18f8_source", "selected_header_offset");
        boolean selectorAvailable = bool(selector.get("available"), field + ".selector.available");
        Boolean uses = optionalBool(selector.get("uses_18f8_source"), field + ".selector.uses_18f8_source");
        Integer offset = i32(selector.get("selected_header_offset"), field + ".selector.selected_header_offset");
        if (selectorAvailable) require(uses != null && offset != null && offset == (uses ? 0x18f8 : 0x19a0), field + ": selector/header differs");
        else require(uses == null && offset == null, field + ": unavailable selector selected a header");
        boolean available = bool(row.get("available"), field + ".available");
        require(available == (base && common && selectorAvailable && selected), field + ": prefix completeness differs");
        reason(row.get("reason"), field + ".reason", available);
        return row.deepCopy();
    }
    private static boolean provider(JsonNode value, String field) {
        if (nil(value)) return false;
        ObjectNode row = object(value, field, "rows");
        ArrayNode rows = array(row.get("rows"), field + ".rows");
        for (int index = 0; index < rows.size(); index++) {
            String name = field + ".rows[" + index + "]";
            ObjectNode current = object(rows.get(index), name, "key", "value_raw");
            integer(current.get("key"), name + ".key", 0, 65535);
            integer(current.get("value_raw"), name + ".value_raw", Long.MIN_VALUE, Long.MAX_VALUE);
        }
        return true;
    }
    private static boolean providers(JsonNode value, String field) {
        if (nil(value)) return false;
        ArrayNode rows = array(value, field); boolean complete = true;
        for (int index = 0; index < rows.size(); index++) complete &= provider(rows.get(index), field + "[" + index + "]");
        return complete;
    }
    static JsonNode stored(JsonNode value, String field) {
        if (nil(value)) return NullNode.instance;
        ObjectNode row = object(value, field, "available", "reason", "character_full_id", "scratch_present", "scratch_address", "model_present", "model_address", "context_address",
                "owner_address", "owner_character_full_id", "bound_to_requested_character", "pending_raw", "owned_count_raw", "weighted", "key_array", "value_array", "reset_input");
        positive(row.get("character_full_id"), field + ".character_full_id");
        boolean available = bool(row.get("available"), field + ".available");
        reason(row.get("reason"), field + ".reason", available);
        for (String key : new String[] {"scratch_present", "model_present", "bound_to_requested_character"}) optionalBool(row.get(key), field + "." + key);
        for (String key : new String[] {"scratch_address", "model_address", "context_address", "owner_address"}) u64(row.get(key), field + "." + key);
        for (String key : new String[] {"owner_character_full_id", "owned_count_raw"}) i32(row.get(key), field + "." + key);
        optionalInteger(row.get("pending_raw"), field + ".pending_raw", 0, 255);
        storedArray(row.get("weighted"), field + ".weighted", StoredKind.WEIGHTED);
        storedArray(row.get("key_array"), field + ".key_array", StoredKind.KEY);
        storedArray(row.get("value_array"), field + ".value_array", StoredKind.VALUE);
        ObjectNode reset = object(row.get("reset_input"), field + ".reset_input", "weighted_count_nonzero");
        optionalBool(reset.get("weighted_count_nonzero"), field + ".reset_input.weighted_count_nonzero");
        return row.deepCopy();
    }
    private enum StoredKind { WEIGHTED, KEY, VALUE }
    private static void storedArray(JsonNode value, String field, StoredKind kind) {
        if (nil(value)) return;
        ObjectNode row = object(value, field, "data_address", "capacity_raw", "count", "items");
        u64(row.get("data_address"), field + ".data_address");
        optionalInteger(row.get("capacity_raw"), field + ".capacity_raw", 0, 0xffff_ffffL);
        Integer count = i32(row.get("count"), field + ".count");
        if (nil(row.get("items"))) return;
        ArrayNode rows = array(row.get("items"), field + ".items");
        require(count != null && count >= 0 && rows.size() == count, field + ": active stored count differs");
        for (int index = 0; index < rows.size(); index++) {
            String name = field + ".items[" + index + "]";
            if (kind != StoredKind.WEIGHTED) {
                integer(rows.get(index), name, kind == StoredKind.KEY ? 0 : Long.MIN_VALUE, kind == StoredKind.KEY ? 65535 : Long.MAX_VALUE);
                continue;
            }
            ObjectNode current = object(rows.get(index), name, "native_index", "weight_raw", "property_block");
            integer(current.get("native_index"), name + ".native_index", index, index);
            i64(current.get("weight_raw"), name + ".weight_raw");
            if (!nil(current.get("property_block"))) {
                ObjectNode block = object(current.get("property_block"), name + ".property_block", "key_array", "value_array");
                storedArray(block.get("key_array"), name + ".property_block.key_array", StoredKind.KEY);
                storedArray(block.get("value_array"), name + ".property_block.value_array", StoredKind.VALUE);
            }
        }
    }
}
