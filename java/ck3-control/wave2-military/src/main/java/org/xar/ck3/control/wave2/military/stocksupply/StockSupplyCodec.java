package org.xar.ck3.control.wave2.military.stocksupply;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrameCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteCodec;

/** Declared projection from an extensible same-query SDK row; JSON stays at this boundary. */
public final class StockSupplyCodec {
    public static final int MAX_BYTES = 65_536;
    public static final String SERVICE_FIELD = "source_derived_next_stock_supply_budget_v1";
    public static final String RATE_SERVICE_FIELD = "same_input_conditional_next_admitted_day_fleet_rate_v1";
    public static final String CONDITION = "one source-ordered Fleet supply callback for this CURRENT captured receiver at "
            + "source-derived next passedDate and the same next GLOBAL GameState low32 date, "
            + "with captured capacity and all non-date rate/budget inputs unchanged after earlier Unit stages";
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64).maxNumberLength(40).build()).build());
    private StockSupplyCodec() {}

    public static StockSupplyProjection.Input decode(byte[] bytes) { return decodeRow(read(bytes)); }
    public static StockSupplyProjection.Input decodeRow(JsonNode row) {
        if (row == null || !row.isObject()) throw new IllegalArgumentException("same-query strength must be an object");
        return new StockSupplyProjection.Input(FleetSupplyCodec.decodeRow(row), UpdaterWriteCodec.decode(row),
                nullableLong(row, "current_supply_change_monthly_raw"), nullableLong(row, "current_supply_capacity_raw"));
    }
    public static byte[] project(byte[] bytes) { return bytes(encode(StockSupplyProjection.project(decode(bytes)))); }
    public static NextFleetRate.Input decodeRate(byte[] bytes) { return decodeRateRow(read(bytes)); }
    public static NextFleetRate.Input decodeRateRow(JsonNode row) {
        if (row == null || !row.isObject()) throw new IllegalArgumentException("same-query strength must be an object");
        JsonNode status = row.get("status");
        return new NextFleetRate.Input(status != null && status.isTextual() && "available".equals(status.textValue()),
                nullableInt(row, "army_id"), nullableInt(row, "native_carmy_id"),
                nullableLong(row, "current_supply_change_monthly_raw"),
                FleetSupplyCodec.decodeTick(row.get("current_fleet_supply_tick_inputs_v1")));
    }
    public static byte[] projectRate(byte[] bytes) { return bytes(encodeRate(NextFleetRate.project(decodeRate(bytes)))); }

    /** The sole original Service consumer publishes one wrapper for every original strength row. */
    public static byte[] projectServiceField(byte[] queryBytes) {
        JsonNode query = read(queryBytes);
        if (!query.isObject() || !query.path("army_strengths").isArray()) {
            throw new IllegalArgumentException("query army_strengths array required");
        }
        ObjectNode result = JSON.createObjectNode();
        var entries = result.putArray(SERVICE_FIELD);
        for (JsonNode row : query.get("army_strengths")) {
            var projected = StockSupplyProjection.project(decodeRow(row));
            ObjectNode entry = entries.addObject();
            nullable(entry, "army_id", projected.input().row().armyId());
            entry.set("projection", encode(projected));
        }
        return bytes(result);
    }

    public static byte[] projectRateServiceField(byte[] queryBytes) {
        JsonNode query = read(queryBytes);
        if (!query.isObject() || !query.path("army_strengths").isArray()) {
            throw new IllegalArgumentException("query army_strengths array required");
        }
        ObjectNode result = JSON.createObjectNode();
        var entries = result.putArray(RATE_SERVICE_FIELD);
        for (JsonNode row : query.get("army_strengths")) {
            NextFleetRate.Input input = decodeRateRow(row);
            ObjectNode entry = entries.addObject();
            nullable(entry, "army_id", input.armyId());
            entry.set("projection", encodeRate(NextFleetRate.project(input)));
        }
        return bytes(result);
    }

    public static ObjectNode encode(StockSupplyProjection.Result value) {
        ObjectNode result = JSON.createObjectNode();
        var row = value.input().row();
        result.put("schema_version", 1);
        result.put("source", "same_input_conditional_source_derived_next_stock_supply_budget");
        result.put("status", wire(value.status())); result.put("ready", value.ready());
        strings(result, "missing_inputs", value.missingInputs());
        nullable(result, "army_id", row.armyId()); nullable(result, "native_carmy_id", row.nativeCarmyId());
        result.put("condition", CONDITION); result.put("callback_entry_is_conditional", true);
        nullable(result, "observed_current_stock_raw", row.currentSupplyRaw());
        nullable(result, "observed_current_rate_raw", value.input().observedRate());
        nullable(result, "observed_current_capacity_raw", value.input().capturedCapacity());
        nullable(result, "observed_current_native_fleet_supply_loss_suppressed", row.observedSuppressed());
        nullable(result, "observed_current_budget_soldiers", row.observedBudget());
        result.set("source_next_date", value.updater().sourceNextDate() == null ? JSON.nullNode()
                : SourceNextFrameCodec.encode(value.updater().sourceNextDate()));
        JsonNode writes = UpdaterWriteCodec.encode(value.updater());
        result.set("next_admission", writes.get("next_admission"));
        result.set("conditional_pre_rate_writes", writes.get("conditional_writes"));
        result.put("ordered_pre_rate_writes_ready", value.updater().ready());
        result.set("conditional_rate", rateStage(value.rate()));
        result.set("conditional_post_updater_stock", stockStage(value.stock()));
        result.set("conditional_budget_getter", budgetStage(value.budget()));
        for (String field : List.of("earlier_stage_effects_reconstructed", "actual_future_date_stage_observed",
                "actual_future_callback_observed", "actual_future_stock_observed", "actual_future_supply_budget_observed",
                "actual_physical_loss_observed", "future_stock_or_strength_ready", "full_daily_supply_transition_ready",
                "full_monthly_ready")) result.put(field, false);
        return result;
    }

    public static ObjectNode encodeRate(NextFleetRate.Result value) {
        ObjectNode result = JSON.createObjectNode();
        result.put("source", "conditional_same_context_next_admitted_day_fleet_rate");
        result.put("status", wire(value.status())); result.put("conditional_fleet_rate_ready", value.ready());
        nullable(result, "current_native_date_low32", value.currentDateLow32());
        nullable(result, "conditional_next_date_low32", value.nextDateLow32());
        if (value.raw() == null) result.putNull("conditional_full_fleet_rate_raw");
        else result.put("conditional_full_fleet_rate_raw", value.raw());
        nullable(result, "fleet_date_admitted", value.fleetDateAdmitted());
        nullable(result, "branch", value.branch() == null ? null : wire(value.branch()));
        nullable(result, "division_path", value.divisionPath() == null ? null : wire(value.divisionPath()));
        nullable(result, "commander_divisor_raw", value.commanderDivisor());
        nullable(result, "current_observed_total_rate_raw", value.observedTotalRate());
        result.put("scale", 100_000);
        for (String field : List.of("actual_next_callback_ready", "actual_after", "actual_post_stage_observed",
                "full_daily_supply_transition_ready", "full_monthly_ready")) result.put(field, false);
        strings(result, "fixed_context", List.of("same Fleet association", "same Province/terrain",
                "same commander/fallback", "same loaded slots/modifier context"));
        strings(result, "missing_inputs", value.missingInputs());
        return result;
    }
    private static ObjectNode rateStage(StockSupplyProjection.RateStage value) {
        ObjectNode result = JSON.createObjectNode();
        nullable(result, "would_evaluate", value.wouldEvaluate()); result.put("ready", value.ready());
        if (value.raw() == null) result.putNull("raw"); else result.put("raw", value.raw());
        nullable(result, "basis", value.basis() == null ? null : wire(value.basis()));
        result.put("native_day_index_used", false); result.put("fixed_divisor_is_calendar_day_index", false);
        nullable(result, "source_next_pair_matches_rate_helper", value.sourcePairMatches());
        result.set("existing_fleet_rate_projection", value.existingRate() == null ? JSON.nullNode() : encodeRate(value.existingRate()));
        strings(result, "missing_inputs", value.missingInputs()); return result;
    }
    private static ObjectNode stockStage(StockSupplyProjection.StockStage value) {
        ObjectNode result = JSON.createObjectNode();
        result.put("ready", value.ready()); nullable(result, "raw", value.raw());
        nullable(result, "signed64_add_raw", value.signed64Add());
        nullable(result, "clamp_branch", value.clampBranch() == null ? null : wire(value.clampBranch()));
        result.put("capacity_basis", "captured_current_capacity_unchanged");
        result.put("actual_future_capacity_observed", false); strings(result, "missing_inputs", value.missingInputs());
        return result;
    }
    private static ObjectNode budgetStage(StockSupplyProjection.BudgetStage value) {
        ObjectNode result = JSON.createObjectNode();
        nullable(result, "would_call", value.wouldCall()); result.put("call_predicate_ready", value.callPredicateReady());
        nullable(result, "global_date_raw_i32", value.globalDate()); result.put("fleet_date_predicate_ready", value.fleetDatePredicateReady());
        nullable(result, "suppression", value.suppression());
        result.put("stock_basis", value.getterRejected() ? "getter_not_called_rejected_updater" : "conditional_post_updater_stock");
        nullable(result, "stock_raw", value.stockRaw()); nullable(result, "state_index", value.stateIndex());
        nullable(result, "base_fraction_raw", value.baseFraction()); nullable(result, "effective_fraction_raw", value.effectiveFraction());
        result.put("ready", value.ready()); nullable(result, "soldiers", value.soldiers());
        strings(result, "missing_inputs", value.missingInputs()); return result;
    }
    private static JsonNode read(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_BYTES) throw new IllegalArgumentException("stock supply byte budget exceeded or empty");
        try {
            StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
            try (JsonParser parser = JSON.createParser(bytes)) {
                JsonNode value = JSON.readTree(parser);
                if (value == null || parser.nextToken() != null) throw new IllegalArgumentException("exactly one JSON value required");
                return value;
            }
        } catch (IOException failure) { throw new IllegalArgumentException("invalid stock supply UTF-8/JSON", failure); }
    }
    private static Long nullableLong(JsonNode object, String field) {
        JsonNode value = object.get(field);
        if (value == null || value.isNull()) return null;
        if (!value.isIntegralNumber() || !value.canConvertToLong()) throw new IllegalArgumentException(field + " must be signed int64 or null");
        return value.longValue();
    }
    private static Integer nullableInt(JsonNode object, String field) {
        Long value = nullableLong(object, field);
        if (value == null) return null;
        if (value < Integer.MIN_VALUE || value > Integer.MAX_VALUE) throw new IllegalArgumentException(field + " must be signed int32 or null");
        return value.intValue();
    }
    private static void strings(ObjectNode node, String field, List<String> values) {
        var array = node.putArray(field); values.forEach(array::add);
    }
    private static void nullable(ObjectNode node, String field, Number value) {
        if (value == null) node.putNull(field); else node.put(field, value.longValue());
    }
    private static void nullable(ObjectNode node, String field, Boolean value) {
        if (value == null) node.putNull(field); else node.put(field, value.booleanValue());
    }
    private static void nullable(ObjectNode node, String field, String value) {
        if (value == null) node.putNull(field); else node.put(field, value);
    }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static byte[] bytes(JsonNode value) {
        try { return JSON.writeValueAsBytes(value); }
        catch (IOException failure) { throw new IllegalArgumentException("cannot encode stock supply", failure); }
    }
}
