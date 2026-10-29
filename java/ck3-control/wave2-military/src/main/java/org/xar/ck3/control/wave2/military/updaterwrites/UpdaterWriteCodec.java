package org.xar.ck3.control.wave2.military.updaterwrites;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Locale;

/** The extensible normalized Army row is projected; its native source-next family is closed. */
public final class UpdaterWriteCodec {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String CONDITION = "one source updater invocation for this CURRENT captured receiver at source-derived next passedDate, all non-date gate values unchanged after earlier Unit stages";
    private UpdaterWriteCodec() {}

    public static UpdaterInput decode(byte[] bytes) { return decode(SourceNextFrameCodec.parse(bytes)); }
    public static UpdaterInput decode(JsonNode row) {
        requireObject(row, "normalized Army row");
        String status = SourceNextFrameCodec.text(row, "status", true);
        Integer army = SourceNextFrameCodec.integer32(row, "army_id");
        Integer carmy = SourceNextFrameCodec.integer32(row, "native_carmy_id");
        JsonNode inputs = optionalObject(row.get("monthly_loss_budget_inputs_v1"));
        JsonNode clock = optionalObject(row.get("army_update_clock_v1"));
        JsonNode caller = optionalObject(row.get("monthly_caller_effect_inputs_v1"));
        return new UpdaterInput("available".equals(status), army, carmy,
                new UpdaterInput.GateInputs(SourceNextFrameCodec.integer32(inputs, "unit_native_170_raw"),
                        nullableBoolean(inputs, "native_unit_in_combat"), nullableBoolean(inputs, "native_unit_gathering"),
                        SourceNextFrameCodec.integer32(inputs, "army_gathering_count_raw")),
                new UpdaterInput.ClockInputs(SourceNextFrameCodec.integer32(clock, "current_date_raw"),
                        SourceNextFrameCodec.integer32(clock, "last_supply_update_date_raw"),
                        SourceNextFrameCodec.integer32(clock, "grace_anchor_date_raw"),
                        SourceNextFrameCodec.integer32(clock, "loaded_grace_days"),
                        SourceNextFrameCodec.integer64(clock, "last_supply_update_date_storage_raw64"),
                        SourceNextFrameCodec.integer64(clock, "grace_anchor_date_storage_raw64")),
                new UpdaterInput.CallerInputs(SourceNextFrameCodec.integer64(caller, "army_byte_22_raw"),
                        SourceNextFrameCodec.integer64(caller, "current_date_storage_raw64")),
                SourceNextFrameCodec.decode(row.get("source_derived_next_daily_supply_frame_inputs_v1"), army, carmy));
    }

    public static ObjectNode encode(UpdaterProjection value) {
        ObjectNode node = JSON.createObjectNode();
        node.put("schema_version", 1); node.put("source", "same_input_conditional_source_derived_next_updater_writes");
        node.put("status", value.status().name().toLowerCase(Locale.ROOT)); node.put("ready", value.ready());
        ArrayNode missing = node.putArray("missing_inputs"); value.missingInputs().forEach(missing::add);
        SourceNextFrameCodec.nullable(node, "army_id", value.armyId()); SourceNextFrameCodec.nullable(node, "native_carmy_id", value.nativeCarmyId());
        node.put("condition", CONDITION); node.put("callback_entry_is_conditional", true);
        node.set("source_next_date", SourceNextFrameCodec.encode(value.sourceNextDate()));
        SourceNextFrameCodec.nullable(node, "observed_current_army_byte_22_raw", value.observedArmyByte22());
        node.put("observed_current_army_byte_22_ready", value.observedArmyByte22Ready());
        SourceNextFrameCodec.nullable(node, "observed_current_last_supply_update_date_storage_raw64", value.observedLastSupplyUpdateStorage());
        SourceNextFrameCodec.nullable(node, "observed_current_last_supply_update_date_raw_i32", value.observedLastSupplyUpdateLow());
        SourceNextFrameCodec.nullable(node, "observed_current_caller_date_storage_raw64", value.observedCallerStorage());
        node.put("observed_current_update_date_comparison_ready", value.updateComparisonReady());
        nullableBoolean(node, "observed_current_update_date_matches_current_clock", value.updateMatchesCurrentClock());
        nullableBoolean(node, "observed_current_clock_matches_source_seed", value.currentClockMatchesSourceSeed());
        SourceNextFrameCodec.nullable(node, "observed_current_grace_elapsed_days", value.observedGraceElapsedDays());
        node.set("next_admission", encodeAdmission(value.nextAdmission()));
        ArrayNode writes = node.putArray("conditional_writes");
        for (ConditionalWrite write : value.conditionalWrites()) writes.add(encodeWrite(write));
        ObjectNode anchor = node.putObject("conditional_grace_anchor_190");
        anchor.put("would_write", false); anchor.put("ready", value.graceAnchor().ready());
        SourceNextFrameCodec.nullable(anchor, "observed_value", value.graceAnchor().observedValue());
        SourceNextFrameCodec.nullable(anchor, "conditional_value", value.graceAnchor().observedValue());
        SourceNextFrameCodec.nullable(anchor, "observed_low32", value.graceAnchor().observedLow32());
        SourceNextFrameCodec.nullable(anchor, "conditional_low32", value.graceAnchor().observedLow32());
        anchor.put("actual_write_observed", false);
        node.put("source_next_full_date_ready", value.sourceNextFullDateReady());
        for (String field : new String[]{"earlier_stage_effects_reconstructed", "actual_future_date_stage_observed",
                "actual_future_callback_observed", "actual_future_writes_observed", "future_stock_or_strength_ready",
                "full_daily_supply_transition_ready", "full_monthly_ready"}) node.put(field, false);
        return node;
    }

    public static ObjectNode encodeAdmission(UpdaterAdmission value) {
        ObjectNode node = JSON.createObjectNode(); node.put("ready", value.ready());
        nullableBoolean(node, "admitted", value.admitted()); node.put("rejection", value.rejection());
        ArrayNode witnesses = node.putArray("witnesses");
        for (UpdaterAdmission.Witness witness : value.witnesses()) {
            ObjectNode entry = witnesses.addObject();
            switch (witness) {
                case UpdaterAdmission.IntegerGateWitness integer -> {
                    entry.put("input", integer.field().wire()); SourceNextFrameCodec.nullable(entry, "value", integer.value());
                    nullableBoolean(entry, "passed", integer.passed());
                }
                case UpdaterAdmission.BooleanGateWitness bool -> {
                    entry.put("input", bool.field().wire()); nullableBoolean(entry, "value", bool.value());
                    nullableBoolean(entry, "passed", bool.passed());
                }
                case UpdaterAdmission.GraceWitness grace -> {
                    entry.put("input", "native_grace_strict_greater"); entry.put("passed_date_raw_i32", grace.passedDateRawI32());
                    entry.put("grace_anchor_date_raw_i32", grace.graceAnchorDateRawI32()); entry.put("elapsed_date_raw_i32", grace.elapsedDateRawI32());
                    entry.put("elapsed_days", grace.elapsedDays()); entry.put("loaded_grace_days", grace.loadedGraceDays()); entry.put("passed", grace.passed());
                }
            }
        }
        ArrayNode missing = node.putArray("missing_inputs"); value.missingInputs().forEach(missing::add);
        return node;
    }

    private static ObjectNode encodeWrite(ConditionalWrite value) {
        ObjectNode node = JSON.createObjectNode();
        switch (value) {
            case ConditionalWrite.Byte22Write write -> {
                node.put("order", 0); node.put("member", "CArmy+0x22"); node.put("stage", "before_admission");
                node.put("write_ready", write.writeReady()); nullableBoolean(node, "would_write", write.wouldWrite());
                SourceNextFrameCodec.nullable(node, "observed_value", write.observedValue());
                SourceNextFrameCodec.nullable(node, "conditional_value", write.conditionalValue());
            }
            case ConditionalWrite.Date188Write write -> {
                node.put("order", 1); node.put("member", "CArmy+0x188"); node.put("stage", "after_admission_before_rate");
                node.put("write_ready", write.writeReady()); node.put("write_predicate_ready", write.writePredicateReady());
                nullableBoolean(node, "would_write", write.wouldWrite()); node.put("after_value_ready", write.afterValueReady());
                SourceNextFrameCodec.nullable(node, "observed_value", write.observedValue());
                SourceNextFrameCodec.nullable(node, "conditional_value", write.conditionalValue());
                node.put("value_origin", write.valueOrigin() == null ? null : write.valueOrigin().name().toLowerCase(Locale.ROOT));
            }
        }
        node.put("actual_write_observed", false);
        return node;
    }

    private static JsonNode optionalObject(JsonNode node) {
        if (node == null || node.isNull()) return JSON.createObjectNode();
        requireObject(node, "declared normalized family"); return node;
    }
    private static void requireObject(JsonNode node, String name) {
        if (node == null || !node.isObject()) throw new IllegalArgumentException(name + " must be object");
    }
    private static Boolean nullableBoolean(JsonNode node, String field) {
        JsonNode value = node.get(field);
        return value == null || value.isNull() ? null : SourceNextFrameCodec.bool(node, field);
    }
    private static void nullableBoolean(ObjectNode node, String field, Boolean value) {
        if (value == null) node.putNull(field); else node.put(field, value.booleanValue());
    }
}
