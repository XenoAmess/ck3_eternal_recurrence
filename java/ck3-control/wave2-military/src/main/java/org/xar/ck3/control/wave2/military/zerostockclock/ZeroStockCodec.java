package org.xar.ck3.control.wave2.military.zerostockclock;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossCodec;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.BudgetInputs;
import org.xar.ck3.control.wave2.military.supplyschedule.NativeNextDailySupplyScheduleCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteCodec;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.AvailableOpportunities;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.Candidate;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.Input;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.Opportunities;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.UnavailableOpportunities;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.ZeroBudget;

/** Native families are validated by their single owner; outer SDK objects remain extensible. */
public final class ZeroStockCodec {
    private static final Set<String> COMPLETE_FAMILY_HEADER = Set.of("status", "ready", "scale", "loaded_supply_state_levels", "loaded_supply_state_fractions_raw");
    private ZeroStockCodec() { }
    public static Input decode(byte[] raw) { return decode(StrictJson.parse(raw)); }
    public static Input decode(JsonNode row) { return decode(row, false); }
    public static Input decodeForHost(JsonNode row) { return decode(row, true); }
    private static Input decode(JsonNode row, boolean host) {
        input(host, () -> { StrictJson.require(row != null && row.isObject(), "same-query zero stock row must be object"); return true; });
        JsonNode status = row.get("status");
        if (status != null && !status.isNull()) input(host, () -> StrictJson.text(status));
        JsonNode rawFamily = row.get("monthly_loss_budget_inputs_v1"); BudgetInputs complete = null;
        if (rawFamily != null && !rawFamily.isNull()) {
            input(host, () -> { StrictJson.require(rawFamily.isObject(), "monthly family must be object or null"); return true; });
            boolean header = COMPLETE_FAMILY_HEADER.stream().allMatch(rawFamily::has);
            if (header) complete = input(host, () -> MonthlyLossCodec.decodeFamilyNullable(rawFamily));
        }
        return new Input(status != null && "available".equals(status.textValue()),
                input(host, () -> ArmyUpdateClockCodec.i32(row, "army_id")), input(host, () -> ArmyUpdateClockCodec.i32(row, "native_carmy_id")),
                input(host, () -> ArmyUpdateClockCodec.i64(row, "current_supply_raw")), input(host, () -> ArmyUpdateClockCodec.i64(row, "current_supply_capacity_raw")),
                input(host, () -> ArmyUpdateClockCodec.i64(row, "current_supply_change_monthly_raw")),
                input(host, () -> ArmyUpdateClockCodec.decode(row.get("army_update_clock_v1"))), (host ? NativeNextDailySupplyScheduleCodec.fromSameQueryRowForHost(row) : NativeNextDailySupplyScheduleCodec.fromSameQueryRow(row)),
                input(host, () -> UpdaterWriteCodec.decode(row)), complete, input(host, () -> MonthlyLossCodec.decodeLossProjection(row.get("loss_application_inputs_v1"))));
    }

    public static JsonNode project(byte[] raw) { return encode(ZeroStockProjection.projectNextCallbackCandidate(decode(raw))); }
    public static ObjectNode encode(Candidate value) {
        ObjectNode out = StrictJson.object();
        out.put("source", "existing_next_pair_bucket_and_updater_gate_join_12004");
        out.put("conditional_zero_entry_capture_candidate", value.conditionalZeroEntryCaptureCandidate());
        out.put("observed_current_stock_is_exact_zero", value.observedCurrentStockIsExactZero());
        out.put("same_row_clock_seed_matches", value.sameRowClockSeedMatches());
        out.put("next_date_raw_i32", value.nextDateRawI32()); out.put("next_native_day_index_raw_i32", value.nextNativeDayIndexRawI32());
        out.put("next_selected_phase_i32", value.nextSelectedPhaseI32());
        positions(out, "conditional_original_pointer_positions", value.conditionalOriginalPointerPositions());
        out.put("conditional_callback_opportunity_count", value.conditionalCallbackOpportunityCount());
        out.set("next_admission", UpdaterWriteCodec.encodeAdmission(value.nextAdmission()));
        out.put("condition", "captured receiver, stock, bucket membership and all non-date gate inputs unchanged through earlier stages");
        out.put("repeated_occurrences_are_independent", true); out.putNull("successful_updater_count");
        for (String field : Set.of("zero_stock_at_actual_writer_observed", "physical_loss_observed", "complete_cycle_observed",
                "full_daily_supply_transition_ready", "full_monthly_ready")) out.put(field, false);
        out.set("conditional_next_zero_supply_budget_v1", encodeBudget(value.conditionalNextZeroSupplyBudget())); return out;
    }

    public static ObjectNode encodeBudget(ZeroBudget value) {
        ObjectNode out = StrictJson.object(); out.put("source", "conditional_next_post_updater_zero_supply_budget_12004");
        out.put("conditional_post_supply_raw", value.conditionalPostSupplyRaw()); out.put("post_supply_ready", value.postSupplyReady());
        out.put("supply_budget_soldiers", value.supplyBudgetSoldiers()); out.put("supply_budget_ready", value.supplyBudgetReady());
        out.put("conditional_positive_budget_capture_candidate", value.conditionalPositiveBudgetCaptureCandidate());
        out.put("first_reaches_zero_in_this_conditional_callback", value.firstReachesZeroInThisConditionalCallback());
        out.put("next_date_raw_i32", value.nextDateRawI32()); out.put("next_selected_phase_i32", value.nextSelectedPhaseI32());
        positions(out, "original_pointer_positions", value.originalPointerPositions());
        out.put("candidate_first_original_pointer_position", value.candidateFirstOriginalPointerPosition());
        ArrayNode missing = out.putArray("missing_inputs"); value.missingInputs().forEach(missing::add);
        for (String field : Set.of("actual_future_callback_observed", "physical_loss_observed", "physical_writer_execution_ready")) out.put(field, false);
        out.put("condition", "one actual source-derived next pointer occurrence; captured current receiver/rate/cap/Province-specific loss operands/eligible count unchanged after earlier stages");
        out.put("acceptance", "same actual callback token and writer-time stock0 plus complete unique physical debit>0; budget alone never passes");
        if (value.nativeAddOverflowWrapped() != null) out.put("native_ADD_overflow_wrapped", value.nativeAddOverflowWrapped());
        if (value.completeFamilyReached()) {
            out.put("current_supply_fraction_modifier_id", value.currentSupplyFractionModifierId());
            out.put("current_supply_fraction_modifier_raw", value.currentSupplyFractionModifierRaw());
        }
        var component = value.component();
        if (component != null) {
            if (component.stateIndex() != null) out.put("supply_state_index", component.stateIndex());
            if (component.baseFractionRaw() != null) out.put("supply_base_fraction_raw", component.baseFractionRaw());
            if (component.effectiveFractionRaw() != null) out.put("supply_effective_fraction_raw", component.effectiveFractionRaw());
        }
        return out;
    }

    public static ObjectNode encodeOpportunities(Opportunities value) {
        ObjectNode out = StrictJson.object(); out.put("ready", value.ready()); ArrayNode required = out.putArray("required_fields");
        switch (value) {
            case UnavailableOpportunities unavailable -> {
                unavailable.requiredFields().forEach(required::add); out.putNull("successful_bucket_occurrences");
            }
            case AvailableOpportunities available -> {
                out.put("successful_bucket_occurrences", available.successfulBucketOccurrences());
                out.put("first_successful_post_stock_raw", available.firstSuccessfulPostStockRaw());
                out.put("first_zero_same_invocation_can_apply_supply_loss", true);
                out.put("first_new_zero_writer_opportunity", available.firstNewZeroWriterOpportunity());
                out.putNull("bucket_visits"); out.putNull("actual_days");
                out.put("condition", "same captured rate/cap and successful updater at each original pointer occurrence");
                out.put("physical_loss_predicted", false);
            }
        }
        return out;
    }


    private static <T> T input(boolean host, java.util.function.Supplier<T> validator) {
        try { return validator.get(); }
        catch (IllegalArgumentException rejected) {
            if (!host || rejected instanceof org.xar.ck3.control.contracts.projection.ProjectionDomainRejection) throw rejected;
            throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection(rejected.getMessage());
        }
    }

    private static void positions(ObjectNode out, String name, java.util.List<Integer> positions) {
        if (positions == null) out.putNull(name); else { ArrayNode array = out.putArray(name); positions.forEach(array::add); }
    }
}
