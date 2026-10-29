package org.xar.ck3.control.wave2.military.callbackrisk;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Locale;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossCodec;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel;

/** Central declared SDK projection and serialization; pure risk models never contain JSON nodes. */
public final class CallbackSupplyRiskCodec {
    public static final int MAX_BYTES = 65_536;
    public static final String SERVICE_FIELD = "current_callback_supply_risk_v1";
    private CallbackSupplyRiskCodec() {}

    public static CallbackSupplyRisk.Input decode(byte[] raw) { return decodeRow(StrictJson.parse(raw, MAX_BYTES)); }
    public static CallbackSupplyRisk.Input decodeRow(JsonNode row) {
        StrictJson.require(row instanceof ObjectNode, "army strength row must be an object");
        Integer armyId = i32(row, "army_id"), carmyId = i32(row, "native_carmy_id");
        JsonNode clock = row.get("army_update_clock_v1");
        StrictJson.require(clock == null || clock.isNull() || clock.isObject(), "army update clock must be an object or null");
        return new CallbackSupplyRisk.Input(armyId, carmyId, MonthlyLossCodec.decodeSupplyEntryProjection(row),
                i64(row, "current_attrition_fraction_raw"), clock == null || clock.isNull() ? null
                        : i64(clock, "last_supply_update_date_storage_raw64"),
                CurrentSupplyDispatchCodec.decode(row.get("current_daily_supply_dispatch_inputs_v1"), armyId, carmyId));
    }
    public static byte[] project(byte[] raw) { return StrictJson.canonical(encode(CallbackSupplyRisk.project(decode(raw))), MAX_BYTES); }

    public static ObjectNode encode(CallbackSupplyRisk.Result value) {
        var input = value.input(); var supply = input.supply(); var entry = value.supplyEntry(); var dispatch = input.dispatch();
        ObjectNode node = StrictJson.object();
        node.put("schema_version", 1); node.put("source", "same_input_conditional_current_supply_callback_risk");
        node.put("source_contract_game_version", "1.20.0.4");
        node.put("input_basis", "captured_current_context_before_one_native_supply_callback_entry");
        node.put("status", value.status().name().toLowerCase(Locale.ROOT)); node.put("ready", value.ready());
        node.put("current_context_callback_values_ready", value.ready()); node.put("scale", 100_000);
        node.put("observed_current_supply_raw", supply.currentSupplyRaw());
        node.put("observed_current_supply_capacity_raw", supply.currentSupplyCapacityRaw());
        node.put("observed_current_supply_change_monthly_raw", supply.currentSupplyChangeMonthlyRaw());
        node.put("observed_current_attrition_fraction_raw", input.observedAttritionFractionRaw());
        node.put("observed_current_supply_loss_budget_soldiers", supply.losses().currentSupplyLossBudget());
        node.set("observed_current_stock_state", stockState(value.currentStockState()));
        node.put("observed_current_date_raw", supply.clock().currentDateRaw());
        node.put("observed_last_supply_update_date_raw64", input.lastSupplyUpdateDateStorageRaw64());
        boolean selectedReady = dispatch != null && dispatch.ready();
        node.put("observed_selected_bucket_ready", selectedReady);
        node.put("observed_selected_bucket_phase", selectedReady ? dispatch.selectedBucketPhase() : null);
        node.put("observed_subject_callback_occurrences", selectedReady ? dispatch.subjectDispatchOccurrenceCount() : null);
        if (selectedReady) {
            var indices = node.putArray("observed_subject_callback_positions");
            dispatch.subjectOccurrenceIndices().forEach(indices::add);
        } else node.putNull("observed_subject_callback_positions");
        node.put("observed_current_day_callback_selected", selectedReady ? dispatch.subjectDispatchOccurrenceCount() > 0 : null);
        node.put("admission_ready", entry.admitted() != null); node.put("conditional_callback_admitted", entry.admitted());
        node.set("admission_witnesses", MonthlyLossCodec.admissionWitnessesNode(entry.witnesses()));
        node.put("admission_rejection", entry.rejection());
        node.put("conditional_post_stock_ready", entry.postStockReady()); node.put("conditional_post_stock_raw", entry.postStockRaw());
        node.set("conditional_post_stock_state", value.postStockState() == null ? NullNode.getInstance() : stockState(value.postStockState()));
        node.put("conditional_supply_effective_fraction_raw", entry.component().effectiveFractionRaw());
        node.put("conditional_supply_budget_ready", entry.component().ready());
        node.put("conditional_supply_budget_soldiers", entry.component().soldiers());
        node.put("conditional_positive_supply_budget", value.positiveBudget());
        node.put("conditional_enters_positive_supply_base_state", value.entersPositiveBaseState());
        var missing = node.putArray("missing_inputs"); value.missingInputs().forEach(missing::add);
        for (String field : List.of("actual_callback_observed", "actual_supply_update_observed", "actual_loss",
                "earlier_stage_outputs_reconstructed", "future_callback_selection_ready", "future_date_or_day_derived",
                "full_daily_supply_transition_ready", "full_monthly_ready")) node.put(field, false);
        node.putNull("actual_post_stage_supply_raw"); node.putNull("actual_post_stage_current");
        return node;
    }
    public static JsonNode encodeServiceRows(List<CallbackSupplyRisk.ArmyRisk> rows) {
        var array = StrictJson.object().putArray("rows");
        for (var row : rows) { var item = array.addObject(); item.put("army_id", row.armyId()); item.set("projection", encode(row.projection())); }
        return array;
    }
    private static JsonNode stockState(MonthlyLossModel.StockState value) {
        ObjectNode node = StrictJson.object(); node.put("ready", value.ready()); node.put("stock_integer", value.stockInteger());
        node.put("state_index", value.stateIndex()); node.put("base_fraction_raw", value.baseFractionRaw());
        var missing = node.putArray("missing_inputs"); value.missingInputs().forEach(missing::add); return node;
    }
    private static Integer i32(JsonNode node, String field) {
        JsonNode value = node.get(field); return value == null || value.isNull() ? null
                : (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE);
    }
    private static Long i64(JsonNode node, String field) {
        JsonNode value = node.get(field); return value == null || value.isNull() ? null
                : StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE);
    }
}
