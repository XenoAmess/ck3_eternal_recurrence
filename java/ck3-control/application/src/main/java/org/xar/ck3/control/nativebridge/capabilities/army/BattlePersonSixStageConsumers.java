package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.wave2.military.combatwire.PersonSixStageCaptureCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleTerminalJson.*;

/** Original capture consumers. They emit owned input observations and never perform or replay native writes. */
public final class BattlePersonSixStageConsumers {
    private static final String FIELD = BattlePersonSixStageCaptureCodec.CAPTURE_FIELD;
    private BattlePersonSixStageConsumers() { }
    private record Joined(long characterId, ObjectNode capture) { }
    private record Classified(Joined joined, ObjectNode stage, int mode) { }
    private static Joined join(JsonNode section) {
        require(section != null && section.isObject(), "Required native input unavailable: " + FIELD);
        long character = integer(section.get("character_id"), "current_person_state.character_id", 0, 0xffff_ffffL);
        JsonNode normalized = PersonSixStageCaptureCodec.normalize(section.get(FIELD));
        require(normalized instanceof ObjectNode, "Required native input unavailable: " + FIELD);
        require(!nil(normalized.get("character_id")) && normalized.get("character_id").longValue() == character,
                "Required native input unavailable: full CharacterID join");
        return new Joined(character, (ObjectNode) normalized);
    }
    private static int index(long index) { require(index >= 0 && index < 6, "Required native input unavailable: physical stage"); return (int) index; }
    private static boolean yes(JsonNode row, String key) { return row.has(key) && row.get(key).isBoolean() && row.get(key).booleanValue(); }
    private static ObjectNode objectField(ObjectNode row, String key) {
        JsonNode value = row.get(key); require(value instanceof ObjectNode, "Required native input unavailable: " + key); return (ObjectNode) value;
    }
    private static void copy(ObjectNode from, ObjectNode to, String fields) {
        for (String field : fields.split(" ")) { require(from.has(field), "missing normalized source field " + field); to.set(field, from.get(field).deepCopy()); }
    }
    public static ArrayNode emitRequests(JsonNode section) {
        Joined joined = join(section); require(yes(joined.capture(), "ready"), "Required native input unavailable: six-stage capture");
        ArrayNode result = ArmyJson.empty().arrayNode();
        for (JsonNode stage : joined.capture().get("stages")) for (JsonNode request : stageRequests(joined, (ObjectNode) stage)) result.add(request);
        return result;
    }
    public static ArrayNode emitOccurrenceRequests(JsonNode section, long nativeIndex) {
        Joined joined = join(section); return stageRequests(joined, (ObjectNode) joined.capture().get("stages").get(index(nativeIndex)));
    }
    private static ArrayNode stageRequests(Joined joined, ObjectNode stage) {
        ObjectNode leaf = joined.capture();
        require(yes(leaf, "capture_complete") && yes(stage, "observed") && yes(stage.get("first_pc"), "ready") && yes(stage.get("second_pc"), "ready"),
                "Required native input unavailable: six-stage occurrence");
        ArrayNode requests = ArmyJson.empty().arrayNode(); int stageIndex = stage.get("index").intValue();
        String[] kinds = {"first", "second"};
        for (int slot = 0; slot < 2; slot++) {
            String kind = kinds[slot]; if (!yes(stage, kind + "_append_observed")) continue;
            ObjectNode pc = objectField(stage, kind + "_pc"), properties = objectField(pc, "properties");
            ObjectNode request = requests.addObject();
            request.put("source_family", "captured_six_attribute_stages"); request.put("source_ordinal", 2 * stageIndex + slot);
            request.put("stage_index", stageIndex); request.put("append_kind", kind); request.put("native_append_observed", true);
            request.put("historical_capture", true); request.put("character_id", joined.characterId());
            copy(leaf, request, "capture_sequence capture_date_raw capture_thread_id query_thread_id character_identity context_identity source_return_rva");
            request.set("raw_count_i32", stage.get("raw_count_i32").deepCopy()); request.set("source_pc_identity", pc.get("identity").deepCopy());
            request.set("weight_q100000", pc.get("weight_q100000").deepCopy());
            ObjectNode block = request.putObject("property_block"); block.set("keys_count", pc.get("count_i32").deepCopy());
            copy(properties, block, "keys_u16 values_q64"); request.put("actual_model_write_performed", false); request.put("full_helper_ready", false);
        }
        return requests;
    }
    public static ObjectNode emitPreSixAggregate(JsonNode section) {
        Joined joined = join(section); ObjectNode leaf = joined.capture();
        require(yes(leaf, "aggregate_postimage_inputs_ready") && leaf.has("pre_six_aggregate"), "Required native input unavailable: actual pre-six aggregate baseline");
        ObjectNode aggregate = objectField(leaf, "pre_six_aggregate"), pc = objectField(aggregate, "pc");
        ObjectNode result = ArmyJson.empty(); result.put("character_id", joined.characterId());
        copy(leaf, result, "capture_sequence capture_date_raw capture_thread_id context_identity");
        result.set("source_pc_identity", pc.get("identity").deepCopy());
        ObjectNode block = result.putObject("property_block"); block.set("keys_count", pc.get("count_i32").deepCopy());
        copy(objectField(pc, "properties"), block, "keys_u16 values_q64");
        result.put("historical_capture", true); result.set("source_stage", aggregate.get("source_stage").deepCopy());
        result.put("actual_model_write_performed", false); result.put("full_helper_ready", false); return result;
    }
    public static ObjectNode emitPreparationModel(JsonNode section) {
        Joined joined = join(section); ObjectNode leaf = joined.capture();
        require(leaf.has("preparation_model") && yes(leaf.get("preparation_model"), "ready"), "Required native input unavailable: preparation Model");
        ObjectNode model = objectField(leaf, "preparation_model"), result = ArmyJson.empty(); result.put("character_id", joined.characterId());
        copy(leaf, result, "capture_sequence capture_date_raw capture_thread_id context_identity");
        copy(model, result, "model_identity owner_character_identity owner_character_id owner_matches_capture context_offset owner_offset source_stage");
        result.put("historical_capture", true); result.put("actual_model_write_performed", false); result.put("full_helper_ready", false); return result;
    }
    private static ObjectNode provenance(Joined joined) {
        ObjectNode result = ArmyJson.empty(); result.put("character_id", joined.characterId());
        copy(joined.capture(), result, "character_identity context_identity capture_sequence capture_date_raw capture_thread_id");
        result.put("source_stage", "before_each_original_count"); result.put("historical_capture", true);
        result.put("actual_model_write_performed", false); result.put("full_helper_ready", false); return result;
    }
    public static ObjectNode emitBasePoints(JsonNode section) {
        Joined joined = join(section); ObjectNode base = objectField(joined.capture(), "base_point_inputs");
        require(yes(base, "ready"), "Required native input unavailable: base points");
        ObjectNode result = provenance(joined); copy(base, result, "character_offset stride_bytes values_i32"); return result;
    }
    public static ObjectNode emitBasePoint(JsonNode section, long nativeIndex) {
        Joined joined = join(section); int index = index(nativeIndex); ObjectNode base = objectField(joined.capture(), "base_point_inputs");
        require(base.get("observed").get(index).booleanValue(), "Required native input unavailable: base_point_unobserved");
        JsonNode value = base.get("values_i32").get(index); require(!nil(value), "Required native input unavailable: base_point_unread");
        ObjectNode result = provenance(joined); result.put("stage_index", index);
        result.put("source_offset_bytes", base.get("character_offset").longValue() + base.get("stride_bytes").longValue() * index);
        result.set("value_i32", value.deepCopy()); return result;
    }
    public static ObjectNode emitPietyCategory(JsonNode section, long nativeIndex) {
        Joined joined = join(section); int index = index(nativeIndex); ObjectNode inputs = objectField(joined.capture(), "piety_category_inputs");
        ObjectNode stage = (ObjectNode) inputs.get("stages").get(index); require(yes(stage, "ready"), "Required native input unavailable: piety category");
        ObjectNode result = provenance(joined); result.put("stage_index", index);
        result.set("property_key_u16", stage.get("property_key_u16").deepCopy()); result.set("category_multiplier_i32", stage.get("category_i32").deepCopy());
        copy(stage, result, "extension_identity score_q64 cap_i32 threshold_count_i32 thresholds_used_q64"); return result;
    }
    private static Classified classified(JsonNode section, long nativeIndex, int mode) {
        require(mode == 1 || mode == 2, "Required native input unavailable: classified piety mode");
        Joined joined = join(section); int index = index(nativeIndex); ObjectNode inputs = objectField(joined.capture(), "classified_piety_inputs");
        return new Classified(joined, (ObjectNode) inputs.get("stages").get(index), mode);
    }
    private static ObjectNode classifiedProvenance(Classified value) {
        ObjectNode result = provenance(value.joined()); result.set("stage_index", value.stage().get("index").deepCopy());
        result.put("mode", value.mode()); copy(value.stage(), result, "property_key_u16 row_array_identity");
        result.put("classified_reader_rva", 0x2438980); result.put("key_lookup_rva", 0x23036e0);
        result.put("source_evaluated", true); result.put("native_mode_call_observed", false); return result;
    }
    private static ObjectNode scaledRow(ObjectNode row, int mode) {
        require(yes(row, "ready"), "Required native input unavailable: classified row");
        // This source divides the signed maximum in its decomposed branch, unlike the cached minimum kernel.
        long scaled = BattleRecipientArithmetic.uncachedFixedMultiplyQ64(row.get("raw_value_q64").longValue(), row.get("scale_q64").longValue());
        boolean included = mode == 1 ? scaled > 0 : scaled < 0;
        ObjectNode result = row.deepCopy(); result.put("scaled_value_q64", scaled); result.put("included", included);
        result.put("value_q64", included ? scaled : 0); return result;
    }
    public static ObjectNode emitClassifiedPietyRow(JsonNode section, long nativeIndex, long rowIndex, int mode) {
        Classified value = classified(section, nativeIndex, mode); JsonNode rows = value.stage().get("rows");
        require(yes(value.stage(), "observed") && rowIndex >= 0 && rowIndex < rows.size(), "Required native input unavailable: classified piety row");
        ObjectNode result = classifiedProvenance(value); result.setAll(scaledRow((ObjectNode) rows.get((int) rowIndex), mode)); return result;
    }
    public static ObjectNode emitClassifiedPietyValue(JsonNode section, long nativeIndex, int mode) {
        Classified value = classified(section, nativeIndex, mode); ObjectNode stage = value.stage();
        require(yes(stage, "ready"), "Required native input unavailable: classified piety");
        long total = 0; ArrayNode included = ArmyJson.empty().arrayNode();
        for (JsonNode row : stage.get("rows")) {
            ObjectNode term = scaledRow((ObjectNode) row, mode);
            if (yes(term, "included")) { included.add(term.get("native_index").deepCopy()); total += term.get("value_q64").longValue(); }
        }
        JsonNode piety = value.joined().capture().get("piety_category_inputs");
        JsonNode categoryStage = piety == null ? null : piety.get("stages").get(stage.get("index").intValue());
        boolean categoryReady = categoryStage != null && yes(categoryStage, "ready");
        ObjectNode result = classifiedProvenance(value); result.set("row_count_i32", stage.get("row_count_i32").deepCopy());
        result.put("value_q64", total); result.set("included_native_indexes", included); result.put("direct_term_ready", categoryReady);
        if (categoryReady) {
            int category = categoryStage.get("category_i32").intValue(); result.put("category_multiplier_i32", category);
            // Signed64 multiply wrap, signed trunc0 division, then low32, exactly as the original IMUL/SAR/SHR divide.
            result.put("direct_term_i32", (int) ((category * total) / 100000L)); result.putNull("direct_term_reason");
        } else {
            result.putNull("category_multiplier_i32"); result.putNull("direct_term_i32");
            if (categoryStage == null) result.put("direct_term_reason", "piety_category_unobserved");
            else result.set("direct_term_reason", categoryStage.get("reason").deepCopy());
        }
        return result;
    }
}
