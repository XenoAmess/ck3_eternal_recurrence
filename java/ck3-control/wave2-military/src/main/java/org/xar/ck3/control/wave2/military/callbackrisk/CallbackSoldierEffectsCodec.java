package org.xar.ck3.control.wave2.military.callbackrisk;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceCodec;

/** Narrow budget replacement at the JSON boundary; no unrelated manager graph is copied or traversed. */
public final class CallbackSoldierEffectsCodec {
    public static final String SERVICE_FIELD = "current_callback_soldier_effects_v1";
    private CallbackSoldierEffectsCodec() {}

    public static CallbackSoldierEffects.Input decodeRow(JsonNode row, CallbackSupplyRisk.Result risk) {
        StrictJson.require(row.isObject(), "army row must be object");
        StrictJson.require(Objects.equals(i32(row, "army_id"), risk.input().armyId())
                && Objects.equals(i32(row, "native_carmy_id"), risk.input().nativeCarmyId()), "callback budget subject differs from same-query army");
        return decodeValues(row, CallbackSoldierEffects.SupplyBudget.from(risk));
    }

    /** Closed external value boundary; the supplied budget is consumed without recomputing risk. */
    public static CallbackSoldierEffects.Input decodeExternal(byte[] raw) {
        ObjectNode payload = StrictJson.object(StrictJson.parse(raw, CallbackSupplyRiskCodec.MAX_BYTES),
                java.util.Set.of("army", "callback_risk"));
        JsonNode row = payload.get("army"), risk = payload.get("callback_risk");
        allowed(row, java.util.Set.of("status", "army_id", "native_carmy_id", "current_soldiers",
                "loss_application_inputs_v1", "regiment_strengths", "regiment_replenishment_records_v1"));
        i32(row, "army_id"); i32(row, "native_carmy_id");
        JsonNode status = row.get("status");
        StrictJson.require(status == null || status.isNull() || status.isTextual(), "army status must be text or null");
        allowed(risk, java.util.Set.of("conditional_supply_budget_ready", "conditional_supply_budget_soldiers",
                "conditional_post_stock_ready", "conditional_post_stock_raw"));
        return decodeValues(row, new CallbackSoldierEffects.SupplyBudget(
                flag(risk, "conditional_supply_budget_ready"), i32(risk, "conditional_supply_budget_soldiers"),
                flag(risk, "conditional_post_stock_ready"), i64(risk, "conditional_post_stock_raw")));
    }

    private static CallbackSoldierEffects.Input decodeValues(JsonNode row, CallbackSoldierEffects.SupplyBudget budget) {
        JsonNode losses = row.get("loss_application_inputs_v1");
        boolean present = losses != null && !losses.isNull();
        StrictJson.require(!present || losses.isObject(), "loss inputs must be object or null");
        boolean ready = budget.ready() && budget.soldiers() != null;
        return new CallbackSoldierEffects.Input(budget, i32(row, "current_soldiers"), present,
                present ? i32(losses, "current_supply_loss_budget") : null,
                present ? i32(losses, "siege_loss_budget") : null, present ? i32(losses, "raid_loss_budget") : null,
                ready && present ? LossSequenceCodec.decodeArmyProjectionWithSupplyBudget(row, budget.soldiers()) : null);
    }

    /** Both actual Service routes consume this same pair, passing the exact same computed risk to effects. */
    public static byte[] projectServiceFields(byte[] rawQuery) {
        JsonNode query = StrictJson.parse(rawQuery, CallbackSupplyRiskCodec.MAX_BYTES);
        StrictJson.require(query.isObject() && query.path("army_strengths").isArray(), "query army_strengths array required");
        ObjectNode result = StrictJson.object();
        var risks = result.putArray(CallbackSupplyRiskCodec.SERVICE_FIELD);
        var effects = result.putArray(SERVICE_FIELD);
        for (JsonNode row : query.get("army_strengths")) {
            var risk = CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decodeRow(row));
            var effect = CallbackSoldierEffects.project(decodeRow(row, risk));
            var riskEntry = risks.addObject(); riskEntry.put("army_id", risk.input().armyId()); riskEntry.set("projection", CallbackSupplyRiskCodec.encode(risk));
            var effectEntry = effects.addObject(); effectEntry.put("army_id", risk.input().armyId()); effectEntry.set("projection", encode(effect));
        }
        return StrictJson.canonical(result, CallbackSupplyRiskCodec.MAX_BYTES);
    }

    public static ObjectNode encode(CallbackSoldierEffects.Result value) {
        var input = value.input(); var budget = input.budget();
        ObjectNode node = StrictJson.object();
        node.put("schema_version", 1); node.put("source", "same_input_conditional_current_callback_soldier_effects");
        node.put("source_contract_game_version", "1.20.0.4");
        node.put("source_contract_scope", "associated_DATA_current_stores_and_raised_current_maximum");
        var sources = node.putObject("source_entries");
        sources.put("caller", "24E3410"); sources.put("writer", "2634190"); sources.put("record_selector", "260DB50");
        sources.put("current_setter", "2657E80"); sources.put("raised_refresh", "2633320"); sources.put("residual_allocator", "2A957E0");
        node.put("arithmetic_implementation_lineage", "existing_1.20.0.3_four_pass_core");
        node.put("input_basis", "one_captured_current_context_before_one_supply_callback_entry");
        node.put("predicate_basis", "fixed_captured_supply_eligibility_writer_admission_and_refresh_context");
        node.put("intermediate_state_basis", "derived_DATA_aliases_and_target_cached_current_maximum");
        node.put("status", value.status().name().toLowerCase(Locale.ROOT)); node.put("ready", value.ready());
        node.put("conditional_soldier_effects_ready", value.ready()); node.put("conditional_supply_budget_ready", budget.ready());
        node.put("conditional_supply_budget_soldiers", budget.soldiers());
        node.put("conditional_post_stock_ready", budget.postStockReady()); node.put("conditional_post_stock_raw", budget.postStockRaw());
        node.put("observed_current_supply_budget_soldiers", input.observedSupplyBudget());
        node.put("observed_siege_budget_soldiers", input.observedSiegeBudget()); node.put("observed_raid_budget_soldiers", input.observedRaidBudget());
        node.put("observed_current_soldiers", input.observedCurrentSoldiers());
        if (value.sequence() == null) {
            node.putNull("conditional_loss_sequence_v1");
            node.putArray("missing_inputs").add(value.missingReason().name().toLowerCase(Locale.ROOT));
        } else {
            ObjectNode sequence = LossSequenceCodec.sequenceNode(value.sequence());
            node.set("conditional_loss_sequence_v1", sequence); node.set("missing_inputs", sequence.get("missing_inputs").deepCopy());
        }
        for (String field : List.of("actual_callback_observed", "actual_loss", "earlier_stage_outputs_reconstructed",
                "future_callback_selection_ready", "full_daily_supply_transition_ready", "full_monthly_ready")) node.put(field, false);
        node.putNull("actual_post_stage_current");
        return node;
    }
    private static void allowed(JsonNode node, java.util.Set<String> fields) {
        StrictJson.require(node != null && node.isObject(), "declared external callback object required");
        node.fieldNames().forEachRemaining(field -> StrictJson.require(fields.contains(field), "unknown external callback field: " + field));
    }
    private static boolean flag(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value == null || value.isNull()) return false;
        StrictJson.require(value.isBoolean(), field + " must be boolean or null");
        return value.booleanValue();
    }
    private static Long i64(JsonNode node, String field) {
        JsonNode value = node.get(field); return value == null || value.isNull() ? null
                : StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE);
    }
    private static Integer i32(JsonNode node, String field) {
        JsonNode value = node.get(field); return value == null || value.isNull() ? null
                : (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE);
    }
}
