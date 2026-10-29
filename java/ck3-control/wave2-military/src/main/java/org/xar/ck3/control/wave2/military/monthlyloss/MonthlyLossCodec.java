package org.xar.ck3.control.wave2.military.monthlyloss;

import static org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Runtime validation precedes immutable models; SDK outer objects use declared projection. */
public final class MonthlyLossCodec {
    public static final int MAX_BYTES = 65_536;
    private static final Set<String> FAMILY_FIELDS = Set.of("status", "ready", "unavailable_reason", "scale",
            "unit_native_170_raw", "army_gathering_count_raw", "native_unit_in_combat", "native_unit_gathering",
            "native_fleet_supply_loss_suppressed", "commander_valid", "loaded_supply_state_levels",
            "loaded_supply_state_fractions_raw", "commander_supply_modifier_id", "commander_supply_modifier_raw");
    private MonthlyLossCodec() {}

    public static Input decode(byte[] raw) { return decodeArmyProjection(StrictJson.parse(raw, MAX_BYTES)); }

    public static Input decodeArmyProjection(JsonNode node) {
        object(node, "army strength row");
        JsonNode status = node.get("status");
        boolean available = status != null && status.isTextual() && status.textValue().equals("available");
        BudgetInputs family = decodeFamilyNullable(node.get("monthly_loss_budget_inputs_v1"));
        AdmissionInputs admission = family == null ? new AdmissionInputs(null, null, null, null, null) : family.admission();
        SupplyInputs supply = family == null ? new SupplyInputs(null, null, null, null) : family.supply();
        JsonNode losses = optionalObject(node.get("loss_application_inputs_v1"), "loss_application_inputs_v1");
        JsonNode clock = optionalObject(node.get("army_update_clock_v1"), "army_update_clock_v1");
        return new Input(available, admission, supply, decodeLossProjection(losses),
                new ClockInputs(i32(clock, "current_date_raw"), i32(clock, "grace_anchor_date_raw"), i32(clock, "loaded_grace_days")),
                i64(node, "current_supply_raw"), i64(node, "current_supply_change_monthly_raw"), i64(node, "current_supply_capacity_raw"));
    }

    /** Current callback getter projection permits the original partially published Mapping operands. */
    public static Input decodeSupplyEntryProjection(JsonNode node) {
        object(node, "army strength row");
        JsonNode status = node.get("status");
        StrictJson.require(status == null || status.isNull() || status.isTextual(), "army status must be text");
        JsonNode family = optionalObject(node.get("monthly_loss_budget_inputs_v1"), "monthly_loss_budget_inputs_v1");
        JsonNode clock = optionalObject(node.get("army_update_clock_v1"), "army_update_clock_v1");
        return new Input(status != null && status.isTextual() && status.textValue().equals("available"),
                new AdmissionInputs(i32(family, "unit_native_170_raw"), predicate(family, "native_unit_in_combat"),
                        predicate(family, "native_unit_gathering"), i32(family, "army_gathering_count_raw"),
                        predicate(family, "native_fleet_supply_loss_suppressed")), decodeSupplyProjection(family),
                decodeLossProjection(node.get("loss_application_inputs_v1")),
                new ClockInputs(i32(clock, "current_date_raw"), i32(clock, "grace_anchor_date_raw"), i32(clock, "loaded_grace_days")),
                i64(node, "current_supply_raw"), i64(node, "current_supply_change_monthly_raw"), i64(node, "current_supply_capacity_raw"));
    }

    /** Missing and explicit null both mean unpublished to the original family's nullable normalizer. */
    public static BudgetInputs decodeFamilyNullable(JsonNode node) {
        if (node == null || node.isNull()) return null;
        StrictJson.object(node, FAMILY_FIELDS);
        String status = StrictJson.text(node.get("status"));
        Availability availability = switch (status) {
            case "available" -> Availability.AVAILABLE;
            case "unavailable" -> Availability.UNAVAILABLE;
            default -> throw new IllegalArgumentException("unsupported monthly loss input status");
        };
        Boolean ready = predicate(node, "ready");
        StrictJson.require(ready != null, "monthly loss ready must be bool");
        StrictJson.require(StrictJson.integer(node.get("scale"), 100_000, 100_000) == 100_000, "scale must be 100000");
        String reason = nullableText(node.get("unavailable_reason"));
        return new BudgetInputs(availability, ready, reason,
                new AdmissionInputs(i32(node, "unit_native_170_raw"), predicate(node, "native_unit_in_combat"),
                        predicate(node, "native_unit_gathering"), i32(node, "army_gathering_count_raw"),
                        predicate(node, "native_fleet_supply_loss_suppressed")),
                new SupplyInputs(integers32(node.get("loaded_supply_state_levels")),
                        integers64(node.get("loaded_supply_state_fractions_raw")), predicate(node, "commander_valid"),
                        i64(node, "commander_supply_modifier_raw")),
                nullableInteger(node.get("commander_supply_modifier_id"), 0, 65_535).map(Long::intValue).orElse(null));
    }

    public static LossInputs decodeLossProjection(JsonNode node) {
        node = optionalObject(node, "loss_application_inputs_v1");
        return new LossInputs(i32(node, "supply_eligible_soldiers"), i32(node, "current_supply_loss_budget"),
                i32(node, "whole_soldiers"), predicate(node, "siege_active"), predicate(node, "raid_active"),
                i64(node, "siege_rate_raw"), i64(node, "raid_rate_raw"));
    }

    /** Pure getter consumers use the original Mapping projection rather than native-family publication readiness. */
    public static SupplyInputs decodeSupplyProjection(JsonNode node) {
        node = optionalObject(node, "monthly_loss_budget_inputs_v1");
        JsonNode levels = node == null ? null : node.get("loaded_supply_state_levels");
        JsonNode fractions = node == null ? null : node.get("loaded_supply_state_fractions_raw");
        return new SupplyInputs(levels == null ? null : integers32(levels),
                fractions == null ? null : integers64(fractions), predicate(node, "commander_valid"),
                i64(node, "commander_supply_modifier_raw"));
    }

    public static JsonNode encodeFamilyNullable(BudgetInputs value) {
        if (value == null) return com.fasterxml.jackson.databind.node.NullNode.getInstance();
        ObjectNode node = StrictJson.object();
        node.put("status", wire(value.status())); node.put("ready", value.ready());
        nullable(node, "unavailable_reason", value.unavailableReason()); node.put("scale", MonthlyLossPolicy.SCALE);
        AdmissionInputs admission = value.admission(); SupplyInputs supply = value.supply();
        nullable(node, "unit_native_170_raw", admission.unitNative170Raw());
        nullable(node, "native_unit_in_combat", admission.nativeUnitInCombat());
        nullable(node, "native_unit_gathering", admission.nativeUnitGathering());
        nullable(node, "army_gathering_count_raw", admission.armyGatheringCountRaw());
        nullable(node, "native_fleet_supply_loss_suppressed", admission.nativeFleetSupplyLossSuppressed());
        nullable(node, "commander_valid", supply.commanderValid());
        nullable(node, "commander_supply_modifier_id", value.commanderSupplyModifierId());
        nullable(node, "commander_supply_modifier_raw", supply.commanderSupplyModifierRaw());
        if (supply.loadedSupplyStateLevels() == null) node.putNull("loaded_supply_state_levels");
        else { ArrayNode values = node.putArray("loaded_supply_state_levels"); supply.loadedSupplyStateLevels().forEach(values::add); }
        if (supply.loadedSupplyStateFractionsRaw() == null) node.putNull("loaded_supply_state_fractions_raw");
        else { ArrayNode values = node.putArray("loaded_supply_state_fractions_raw"); supply.loadedSupplyStateFractionsRaw().forEach(values::add); }
        return node;
    }

    /** Original producer's complete budget fields, before its separate physical-loss-sequence consumer. */
    public static ObjectNode kernelNode(Result value) {
        ObjectNode node = StrictJson.object();
        node.put("projection_kind", "conditional_post_updater_monthly_loss_budgets");
        node.put("source_contract_game_version", "1.20.0.3");
        node.put("input_basis", "one_query_current_native_inputs_conditional_caller_entry");
        node.put("status", wire(value.status())); node.put("conditional_budgets_ready", value.conditionalBudgetsReady());
        node.put("actual_loss", false); node.putNull("actual_post_stage_current"); node.put("full_monthly_applied_loss_ready", false);
        node.put("fraction_scale", MonthlyLossPolicy.SCALE); node.put("soldier_scale", 1);
        nullable(node, "current_readonly_supply_loss_budget", value.currentReadonlySupplyLossBudget());
        nullable(node, "supply_updater_admitted", value.supplyUpdaterAdmitted()); node.put("admission_ready", value.admissionReady());
        node.set("admission_witnesses", admissionWitnessesNode(value.admissionWitnesses()));
        nullable(node, "admission_rejection", value.admissionRejection());
        nullable(node, "conditional_post_supply_raw", value.conditionalPostSupplyRaw()); node.put("post_supply_ready", value.postSupplyReady());
        SupplyComponent supply = value.supplyComponent();
        nullable(node, "supply_state_index", supply.stateIndex()); nullable(node, "supply_base_fraction_raw", supply.baseFractionRaw());
        nullable(node, "supply_effective_fraction_raw", supply.effectiveFractionRaw());
        nullable(node, "supply_budget_soldiers", supply.soldiers()); node.put("supply_budget_ready", supply.ready());
        nullable(node, "siege_budget_soldiers", value.siegeBudgetSoldiers()); node.put("siege_budget_ready", value.siegeBudgetReady());
        nullable(node, "raid_budget_soldiers", value.raidBudgetSoldiers()); node.put("raid_budget_ready", value.raidBudgetReady());
        nullable(node, "combined_siege_raid_budget_soldiers", value.combinedSiegeRaidBudgetSoldiers());
        ArrayNode missing = node.putArray("missing_inputs"); value.missingInputs().forEach(missing::add);
        return node;
    }

    /** Shared witness field contract used by complete monthly budgets and the supply-only callback wrapper. */
    public static ArrayNode admissionWitnessesNode(List<AdmissionWitness> values) {
        ArrayNode witnesses = StrictJson.object().arrayNode();
        for (AdmissionWitness witness : values) {
            ObjectNode item = witnesses.addObject();
            switch (witness) {
                case GateWitness gate -> {
                    item.put("input", gate.input()); nullable(item, "passed", gate.passed());
                    switch (gate.value()) {
                        case IntegerValue integer -> item.put("value", integer.value());
                        case BooleanValue predicate -> item.put("value", predicate.value());
                        case MissingValue ignored -> item.putNull("value");
                    }
                }
                case GraceWitness grace -> {
                    item.put("input", "native_grace_strict_greater"); item.put("elapsed_date_raw", grace.elapsedDateRaw());
                    item.put("elapsed_days", grace.elapsedDays()); item.put("loaded_grace_days", grace.loadedGraceDays());
                    item.put("passed", grace.passed());
                }
            }
        }
        return witnesses;
    }

    public static byte[] projectKernel(byte[] raw) {
        return StrictJson.canonical(kernelNode(MonthlyLossPolicy.constructConditionalMonthlyLossBudgets(decode(raw))), MAX_BYTES);
    }
    public static ObjectNode supplyComponentNode(SupplyComponent value) {
        ObjectNode node = StrictJson.object();
        nullable(node, "supply_state_index", value.stateIndex()); nullable(node, "supply_base_fraction_raw", value.baseFractionRaw());
        nullable(node, "supply_effective_fraction_raw", value.effectiveFractionRaw());
        node.put("supply_budget_ready", value.ready()); nullable(node, "supply_budget_soldiers", value.soldiers());
        ArrayNode missing = node.putArray("missing_inputs"); value.missingInputs().forEach(missing::add);
        return node;
    }

    private static JsonNode object(JsonNode value, String name) {
        StrictJson.require(value != null && value.isObject(), name + " must be object"); return value;
    }
    private static JsonNode optionalObject(JsonNode value, String name) {
        return value == null || value.isNull() ? null : object(value, name);
    }
    private static String nullableText(JsonNode value) {
        return value == null || value.isNull() ? null : StrictJson.text(value);
    }
    private static java.util.Optional<Long> nullableInteger(JsonNode value, long min, long max) {
        return value == null || value.isNull() ? java.util.Optional.empty() : java.util.Optional.of(StrictJson.integer(value, min, max));
    }
    private static Long i64(JsonNode node, String key) {
        return nullableInteger(node == null ? null : node.get(key), Long.MIN_VALUE, Long.MAX_VALUE).orElse(null);
    }
    private static Integer i32(JsonNode node, String key) {
        return nullableInteger(node == null ? null : node.get(key), Integer.MIN_VALUE, Integer.MAX_VALUE).map(Long::intValue).orElse(null);
    }
    private static Boolean predicate(JsonNode node, String key) {
        JsonNode value = node == null ? null : node.get(key);
        if (value == null || value.isNull()) return null;
        StrictJson.require(value.isBoolean(), key + " must be bool or null"); return value.booleanValue();
    }
    private static List<Integer> integers32(JsonNode node) {
        if (node.isNull()) return null;
        StrictJson.require(node.isArray(), "ordered signed32 array required");
        List<Integer> values = new ArrayList<>();
        for (JsonNode value : node) values.add((int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE));
        return List.copyOf(values);
    }
    private static List<Long> integers64(JsonNode node) {
        if (node.isNull()) return null;
        StrictJson.require(node.isArray(), "ordered signed64 array required");
        List<Long> values = new ArrayList<>();
        for (JsonNode value : node) values.add(StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE));
        return List.copyOf(values);
    }
    private static void nullable(ObjectNode node, String key, Integer value) { if (value == null) node.putNull(key); else node.put(key, value.intValue()); }
    private static void nullable(ObjectNode node, String key, Long value) { if (value == null) node.putNull(key); else node.put(key, value.longValue()); }
    private static void nullable(ObjectNode node, String key, Boolean value) { if (value == null) node.putNull(key); else node.put(key, value.booleanValue()); }
    private static void nullable(ObjectNode node, String key, String value) { if (value == null) node.putNull(key); else node.put(key, value); }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
}
