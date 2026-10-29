package org.xar.ck3.control.wave2.military.fleetsupply;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.ArmyBudget;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.ArmyRow;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.BudgetStatus;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.FleetSupplyBudget;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.FleetTick;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.StockBasis;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.TickStatus;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.LossInputs;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrameCodec;

/** Closed native family boundary. SDK row containers use a declared projection separately. */
public final class FleetSupplyCodec {
    public static final String SOURCE = "same_input_conditional_source_derived_next_fleet_supply_budget";
    public static final String CONDITION = "one direct 24E32C0 getter evaluation with source-derived next GLOBAL GameState low32 date and CURRENT captured stock/Fleet/commander/eligible-current inputs unchanged";
    private static final String COMPARISON = "signed_int32_strict_greater_than_global_date";
    private static final Set<String> FALSE_FIELDS = Set.of("earlier_stage_effects_reconstructed",
            "actual_future_date_stage_observed", "actual_future_callback_observed", "actual_future_supply_budget_observed",
            "future_supply_eligibility_ready", "future_stock_or_strength_ready", "full_daily_supply_transition_ready", "full_monthly_ready");
    private static final Set<String> BUDGET_FIELDS = Set.of("schema_version", "source", "status", "ready", "missing_inputs",
            "army_id", "native_carmy_id", "condition", "stock_basis", "post_updater_stock_used", "held_current_supply_stock_raw",
            "observed_current_native_fleet_supply_loss_suppressed", "observed_current_supply_loss_budget_soldiers",
            "source_next_global_clock", "source_next_global_date_raw_i32", "source_next_global_date_ready",
            "native_fleet_branch_applicable", "fleet_day_raw_i32", "loaded_fleet_day_sentinel_raw_i32", "fleet_date_predicate_ready",
            "conditional_native_fleet_supply_loss_suppressed", "fleet_date_comparison", "global_date_operand_used",
            "held_stock_state_index", "supply_base_fraction_raw", "supply_effective_fraction_raw", "conditional_supply_budget_ready",
            "conditional_supply_budget_soldiers", "earlier_stage_effects_reconstructed", "actual_future_date_stage_observed",
            "actual_future_callback_observed", "actual_future_supply_budget_observed", "future_supply_eligibility_ready",
            "future_stock_or_strength_ready", "full_daily_supply_transition_ready", "full_monthly_ready");
    private static final Set<String> TICK_FIELDS = Set.of(
            "source", "status", "ready", "unavailable_reason", "scale", "subject_army_id", "subject_carmy_id",
            "province_id", "current_native_date_low32", "fleet_raw_full_id", "fleet_resolved_full_id", "fleet_day_raw",
            "loaded_fleet_day_sentinel_raw", "commander_raw_full_id", "commander_resolved_full_id",
            "terrain_modifier_772_raw", "loaded_fleet_loss_raw", "commander_modifier_1a9_raw",
            "loaded_divisor_floor_raw", "loaded_max_loss_raw", "native_fleet_branch_applicable",
            "fleet_used_native_fallback", "commander_used_native_fallback", "terrain_magic_38_raw", "terrain_modifier_772_id");

    private FleetSupplyCodec() { }

    public static ArmyRow decodeRow(byte[] raw) { return decodeRow(StrictJson.parse(raw)); }

    /** Extension-bearing SDK army rows and monthly families deliberately use a declared projection. */
    public static ArmyRow decodeRow(JsonNode node) {
        ObjectNode row = objectProjection(node);
        Integer armyId = i32(row, "army_id"); Integer carmyId = i32(row, "native_carmy_id");
        ObjectNode inputs = optionalObject(row.get("monthly_loss_budget_inputs_v1"));
        ObjectNode losses = optionalObject(row.get("loss_application_inputs_v1"));
        LossInputs lossInputs = MonthlyLossCodec.decodeLossProjection(losses);
        return new ArmyRow(nullableText(row.get("status")), armyId, carmyId, i64(row, "current_supply_raw"),
                decodeTick(row.get("current_fleet_supply_tick_inputs_v1")),
                SourceNextFrameCodec.decode(row.get("source_derived_next_daily_supply_frame_inputs_v1"), armyId, carmyId),
                MonthlyLossCodec.decodeSupplyProjection(inputs), lossInputs,
                nullableBool(inputs.get("native_fleet_supply_loss_suppressed")), lossInputs.currentSupplyLossBudget());
    }

    public static ObjectNode encodeBudget(FleetSupplyBudget budget) {
        ObjectNode out = StrictJson.object();
        out.put("schema_version", 1); out.put("source", SOURCE); out.put("status", budget.status().name().toLowerCase(Locale.ROOT));
        out.put("ready", budget.ready()); out.putArray("missing_inputs").addAll(
                budget.missingInputs().stream().map(com.fasterxml.jackson.databind.node.TextNode::valueOf).toList());
        out.put("army_id", budget.armyId()); out.put("native_carmy_id", budget.nativeCarmyId()); out.put("condition", CONDITION);
        out.put("stock_basis", budget.stockBasis().wire()); out.put("post_updater_stock_used", budget.postUpdaterStockUsed());
        out.put("held_current_supply_stock_raw", budget.heldCurrentSupplyStockRaw());
        out.put("observed_current_native_fleet_supply_loss_suppressed", budget.observedCurrentNativeFleetSupplyLossSuppressed());
        out.put("observed_current_supply_loss_budget_soldiers", budget.observedCurrentSupplyLossBudgetSoldiers());
        out.set("source_next_global_clock", SourceNextFrameCodec.encode(budget.sourceNextGlobalClock()));
        out.put("source_next_global_date_raw_i32", budget.sourceNextGlobalDateRawI32());
        out.put("source_next_global_date_ready", budget.sourceNextGlobalDateReady());
        out.put("native_fleet_branch_applicable", budget.nativeFleetBranchApplicable());
        out.put("fleet_day_raw_i32", budget.fleetDayRawI32()); out.put("loaded_fleet_day_sentinel_raw_i32", budget.loadedFleetDaySentinelRawI32());
        out.put("fleet_date_predicate_ready", budget.fleetDatePredicateReady());
        out.put("conditional_native_fleet_supply_loss_suppressed", budget.conditionalNativeFleetSupplyLossSuppressed());
        out.put("fleet_date_comparison", COMPARISON); out.put("global_date_operand_used", budget.globalDateOperandUsed());
        out.put("held_stock_state_index", budget.heldStockStateIndex()); out.put("supply_base_fraction_raw", budget.supplyBaseFractionRaw());
        out.put("supply_effective_fraction_raw", budget.supplyEffectiveFractionRaw());
        out.put("conditional_supply_budget_ready", budget.conditionalSupplyBudgetReady());
        out.put("conditional_supply_budget_soldiers", budget.conditionalSupplyBudgetSoldiers());
        FALSE_FIELDS.forEach(field -> out.put(field, false)); return out;
    }

    public static FleetSupplyBudget decodeBudget(byte[] raw) { return decodeBudget(StrictJson.parse(raw)); }

    public static FleetSupplyBudget decodeBudget(JsonNode node) {
        ObjectNode value = StrictJson.object(node, BUDGET_FIELDS);
        StrictJson.integer(value.get("schema_version"), 1, 1);
        equalText(value, "source", SOURCE); equalText(value, "condition", CONDITION); equalText(value, "fleet_date_comparison", COMPARISON);
        FALSE_FIELDS.forEach(field -> StrictJson.require(!bool(value.get(field)), "conditional budget cannot claim future effects"));
        StockBasis basis = switch (StrictJson.text(value.get("stock_basis"))) {
            case "captured_current_stock_unchanged" -> StockBasis.CAPTURED_CURRENT_STOCK_UNCHANGED;
            case "conditional_post_updater_stock" -> StockBasis.CONDITIONAL_POST_UPDATER_STOCK;
            default -> throw new org.xar.ck3.control.contracts.ContractViolationException("fleet budget stock basis invalid");
        };
        BudgetStatus status = switch (StrictJson.text(value.get("status"))) {
            case "available" -> BudgetStatus.AVAILABLE;
            case "partial" -> BudgetStatus.PARTIAL;
            case "unavailable" -> BudgetStatus.UNAVAILABLE;
            default -> throw new org.xar.ck3.control.contracts.ContractViolationException("fleet budget status invalid");
        };
        boolean ready = bool(value.get("ready")); Integer date = i32(value, "source_next_global_date_raw_i32");
        StrictJson.require(bool(value.get("conditional_supply_budget_ready")) == ready, "fleet budget readiness fields differ");
        StrictJson.require(bool(value.get("source_next_global_date_ready")) == (date != null), "fleet date readiness differs");
        StrictJson.require(bool(value.get("post_updater_stock_used")) == basis.postUpdaterStockUsed(), "fleet stock basis fields differ");
        Integer army = i32(value, "army_id"); Integer carmy = i32(value, "native_carmy_id");
        return new FleetSupplyBudget(status, army, carmy, basis, i64(value, "held_current_supply_stock_raw"),
                nullableBool(value.get("observed_current_native_fleet_supply_loss_suppressed")),
                i32(value, "observed_current_supply_loss_budget_soldiers"),
                SourceNextFrameCodec.decode(value.get("source_next_global_clock"), army, carmy), date,
                nullableBool(value.get("native_fleet_branch_applicable")), i32(value, "fleet_day_raw_i32"),
                i32(value, "loaded_fleet_day_sentinel_raw_i32"), bool(value.get("fleet_date_predicate_ready")),
                nullableBool(value.get("conditional_native_fleet_supply_loss_suppressed")), bool(value.get("global_date_operand_used")),
                i32(value, "held_stock_state_index"), i64(value, "supply_base_fraction_raw"), i64(value, "supply_effective_fraction_raw"),
                ready, i32(value, "conditional_supply_budget_soldiers"), textList(value.get("missing_inputs")));
    }

    public static JsonNode encodeServiceRows(List<ArmyBudget> rows) {
        var out = StrictJson.object().putArray("rows");
        for (ArmyBudget row : rows) {
            ObjectNode entry = out.addObject(); entry.put("army_id", row.armyId()); entry.set("projection", encodeBudget(row.projection()));
        }
        return out;
    }

    private static ObjectNode objectProjection(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "SDK object required"); return (ObjectNode) value;
    }
    private static ObjectNode optionalObject(JsonNode value) {
        return value == null || value.isNull() ? StrictJson.object() : objectProjection(value);
    }
    private static List<String> textList(JsonNode value) {
        StrictJson.require(value != null && value.isArray(), "ordered JSON text array required");
        List<String> result = new ArrayList<>(); for (JsonNode item : value) result.add(StrictJson.text(item)); return List.copyOf(result);
    }
    private static void equalText(ObjectNode value, String field, String expected) {
        StrictJson.require(expected.equals(StrictJson.text(value.get(field))), "fleet budget " + field + " differs");
    }

    public static FleetTick decodeTick(byte[] raw) { return decodeTick(StrictJson.parse(raw)); }

    public static FleetTick decodeTick(JsonNode node) {
        if (node == null || node.isNull()) return null;
        ObjectNode value = StrictJson.object(node, TICK_FIELDS);
        StrictJson.require("native_current_fleet_supply_tick_inputs".equals(StrictJson.text(value.get("source"))),
                "native fleet tick source differs");
        StrictJson.require(StrictJson.integer(value.get("scale"), 100_000, 100_000) == 100_000,
                "native fleet tick scale differs");
        String statusText = StrictJson.text(value.get("status"));
        TickStatus status = switch (statusText) {
            case "available" -> TickStatus.AVAILABLE;
            case "unavailable" -> TickStatus.UNAVAILABLE;
            case "not_fleet" -> TickStatus.NOT_FLEET;
            default -> throw new org.xar.ck3.control.contracts.ContractViolationException("fleet tick status invalid");
        };
        return new FleetTick(status, bool(value.get("ready")), nullableText(value.get("unavailable_reason")),
                i32(value, "subject_army_id"), i32(value, "subject_carmy_id"), i32(value, "province_id"),
                i32(value, "current_native_date_low32"), i32(value, "fleet_raw_full_id"),
                i32(value, "fleet_resolved_full_id"), i32(value, "fleet_day_raw"),
                i32(value, "loaded_fleet_day_sentinel_raw"), i32(value, "commander_raw_full_id"),
                i32(value, "commander_resolved_full_id"), i64(value, "terrain_modifier_772_raw"),
                i64(value, "loaded_fleet_loss_raw"), i64(value, "commander_modifier_1a9_raw"),
                i64(value, "loaded_divisor_floor_raw"), i64(value, "loaded_max_loss_raw"),
                nullableBool(value.get("native_fleet_branch_applicable")), nullableBool(value.get("fleet_used_native_fallback")),
                nullableBool(value.get("commander_used_native_fallback")), unsigned(value, "terrain_magic_38_raw", 0xffff_ffffL),
                unsigned16(value, "terrain_modifier_772_id"));
    }

    public static ObjectNode encodeTick(FleetTick tick) {
        if (tick == null) throw new IllegalArgumentException("use JSON null for absent fleet tick");
        ObjectNode out = StrictJson.object();
        out.put("source", "native_current_fleet_supply_tick_inputs"); out.put("scale", 100_000);
        out.put("status", tick.status().name().toLowerCase(Locale.ROOT)); out.put("ready", tick.ready());
        out.put("unavailable_reason", tick.unavailableReason());
        out.put("subject_army_id", tick.subjectArmyId()); out.put("subject_carmy_id", tick.subjectCarmyId());
        out.put("province_id", tick.provinceId()); out.put("current_native_date_low32", tick.currentNativeDateLow32());
        out.put("fleet_raw_full_id", tick.fleetRawFullId()); out.put("fleet_resolved_full_id", tick.fleetResolvedFullId());
        out.put("fleet_day_raw", tick.fleetDayRaw()); out.put("loaded_fleet_day_sentinel_raw", tick.loadedFleetDaySentinelRaw());
        out.put("commander_raw_full_id", tick.commanderRawFullId()); out.put("commander_resolved_full_id", tick.commanderResolvedFullId());
        out.put("terrain_modifier_772_raw", tick.terrainModifier772Raw()); out.put("loaded_fleet_loss_raw", tick.loadedFleetLossRaw());
        out.put("commander_modifier_1a9_raw", tick.commanderModifier1a9Raw()); out.put("loaded_divisor_floor_raw", tick.loadedDivisorFloorRaw());
        out.put("loaded_max_loss_raw", tick.loadedMaxLossRaw()); out.put("native_fleet_branch_applicable", tick.nativeFleetBranchApplicable());
        out.put("fleet_used_native_fallback", tick.fleetUsedNativeFallback()); out.put("commander_used_native_fallback", tick.commanderUsedNativeFallback());
        out.put("terrain_magic_38_raw", tick.terrainMagic38Raw()); out.put("terrain_modifier_772_id", tick.terrainModifier772Id());
        return out;
    }

    static Integer i32(ObjectNode node, String field) {
        JsonNode value = node.get(field); return value == null || value.isNull() ? null
                : (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE);
    }
    static Long i64(ObjectNode node, String field) {
        JsonNode value = node.get(field); return value == null || value.isNull() ? null
                : StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE);
    }
    private static Long unsigned(ObjectNode node, String field, long maximum) {
        JsonNode value = node.get(field); return value.isNull() ? null : StrictJson.integer(value, 0, maximum);
    }
    private static Integer unsigned16(ObjectNode node, String field) {
        Long value = unsigned(node, field, 0xffff); return value == null ? null : value.intValue();
    }
    static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "actual JSON boolean required");
        return value.booleanValue();
    }
    static Boolean nullableBool(JsonNode value) { return value == null || value.isNull() ? null : bool(value); }
    static String nullableText(JsonNode value) { return value == null || value.isNull() ? null : StrictJson.text(value); }
}
