package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Pure original battle_retained_geometry producer and its six current-context diagnostics. No query, refresh or forecast authority. */
public final class BattlePublicDiagnostics {
    private static final String EXACT_SHA = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6";
    private static final List<String> STAGES = List.of("attacker_adjacency", "defender_adjacency", "holding_defender");
    private static final List<String> SCOPES = List.of("combat_side_aggregate", "selected_character_aggregate");
    private record Frame(int combat, Field<Integer> province, UInt64 revision, long date) {
        private ObjectNode into(ObjectNode n) { n.put("combat_id", combat); if (province instanceof Present<Integer> value) n.put("province_id", value.value()); else n.putNull("province_id"); return n.put("snapshot_revision", revision.value()).put("observed_date_raw", date); }
    }
    private record Eligibility(ObjectNode value, List<Optional<Long>> totals, List<Optional<String>> reasons) {
        private Eligibility { totals = List.copyOf(totals); reasons = List.copyOf(reasons); }
    }
    private BattlePublicDiagnostics() { }

    /** The same complete original domain normalizer validates every optional Native leaf before any derived field is produced. */
    public static Obj project(ArmyBattleReadValue.Kind kind, Obj normalized, ArmyPublicSnapshot captured) {
        if (kind == ArmyBattleReadValue.Kind.TERMINAL) return new Obj(java.util.Map.of());
        ObjectNode raw = object(OpportunityJson.toNode(normalized));
        int subject = i32(get(raw, kind == ArmyBattleReadValue.Kind.CONTROL ? "subject_public_cunit_id" : "combat_id"));
        Obj strict = kind == ArmyBattleReadValue.Kind.CONTROL
                ? BattleResponseCodec.normalizeControl(normalized, subject, captured.context().nativeRevision(), captured.context().dateRaw().longValueExact())
                : BattleResponseCodec.normalizeTransition(normalized, subject, captured.context().nativeRevision(), captured.context().dateRaw().longValueExact());
        ObjectNode frame = object(OpportunityJson.toNode(strict)), output = empty();
        if (!frame.has("actual_geography_v1")) return freeze(output);
        ObjectNode hello = captured.hello(); JsonNode geographyToken = frame.get("actual_geography_v1");
        ObjectNode geography = geographyToken.isNull() ? null : object(geographyToken);
        boolean exact = hello.path("game_version").asText("").equals("1.20.0.3")
                && hello.path("executable_sha256").isTextual() && hello.path("executable_sha256").textValue().equalsIgnoreCase(EXACT_SHA);
        boolean control = text(get(frame, "contract_stage")).equals("production_exact_ongoing_combat");
        boolean transition = text(get(frame, "contract_stage")).equals("production_exact_combat_lifecycle");
        boolean actual = frame.path("status").asText("").equals("available") && (control || transition);
        Frame sourceFrame = new Frame(i32(get(frame, "combat_id")), nullable(frame, "province_id", ArmyJson::i32), u64(get(frame, "snapshot_revision")), i64(get(frame, "observed_date_raw")));
        ObjectNode source = sourceFrame.into(empty());
        ArmyPublicSnapshot.copyNullable(source, "game_version", hello.get("game_version")); ArmyPublicSnapshot.copyNullable(source, "executable_sha256", hello.get("executable_sha256"));
        source.put("query", control ? "battle_control_snapshot_v1" : "battle_transition_v1");
        List<String> missing = new ArrayList<>(); if (!exact) missing.add("exact_1_20_0_3_build_binding"); if (!actual) missing.add("available_actual_combat_frame");
        ArrayNode sides = empty().arrayNode();
        if (actual) for (int index = 0; index < 2; index++) {
            String role = index == 0 ? "attacker" : "defender"; ObjectNode side = empty().put("side_index", index).put("role", role).put("source", "actual_combat_side_stored_order");
            if (control) {
                ObjectNode originalSide = object(get(frame, role)); ArrayNode ids = empty().arrayNode();
                for (JsonNode army : rows(get(originalSide, "ordered_armies"))) ids.add(i32(get(object(army), "public_cunit_id")));
                side.set("public_cunit_ids_in_stored_order", ids); side.set("primary_participant_character_id", get(originalSide, "primary_participant_character_id").deepCopy()); side.put("primary_source", "actual_combat_side_70");
            } else side.set("public_cunit_ids_in_stored_order", get(frame, role + "_public_cunit_ids_in_stored_order").deepCopy());
            sides.add(side);
        }
        JsonNode terrain = null, kindToken = null, holding = null; Integer retainedKind = null;
        if (geography == null) missing.add("actual_geography_v1");
        else {
            terrain = get(geography, "terrain"); kindToken = get(geography, "constructor_adjacency_kind_raw"); holding = get(geography, "holding_defender");
            if (!text(get(object(terrain), "status")).equals("available")) missing.add("actual_terrain");
            if (kindToken.isNull()) missing.add("retained_constructor_adjacency_kind");
            else { retainedKind = i32(kindToken); if (retainedKind < 0 || retainedKind > 3) missing.add("supported_retained_constructor_kind_0_to_3"); }
            if (holding.isNull()) missing.add("retained_holding_defender");
        }
        String crossing = retainedKind != null && retainedKind >= 0 && retainedKind <= 3 ? List.of("none", "strait", "river", "large_river").get(retainedKind) : null;
        JsonNode effects = leaf(geography, "constructor_rule_effects_v1"), context = leaf(geography, "current_rule_context_v1");
        boolean contextQualified = exact && actual && crossing != null && holding != null && !holding.isNull();
        boolean effectsReady = contextQualified && effects != null && !effects.isNull() && text(get(object(effects), "status")).equals("available");
        ObjectNode plan = null;
        if (contextQualified) {
            plan = empty(); plan.set("attacker_adjacency", empty().put("side_index", 0).put("rules_pointer_offset", 0xF70 + 8 * retainedKind));
            plan.set("defender_adjacency", empty().put("side_index", 1).put("rules_pointer_offset", 0xFA0 + 8 * retainedKind));
            plan.set("holding_defender", empty().put("side_index", 1).put("rules_pointer_offset", 0xF10).put("enabled", bool(holding)).put("predicate_source", "retained_combat_6FE"));
            plan.put("effect_values_observed", effectsReady).put("commander_exclusion_and_scale_inputs_observed", false);
        }
        ObjectNode diagnostic = empty().put("schema_version", 1).put("status", missing.isEmpty() ? "available" : "unavailable").put("retained_geometry_ready", missing.isEmpty())
                .put("geometry_mode", "actual_current_combat_retained_constructor_inputs");
        diagnostic.set("source", source.deepCopy()); diagnostic.set("actual_sides_in_stored_order", sides);
        copy(diagnostic, "terrain", terrain); copy(diagnostic, "constructor_adjacency_kind_raw", kindToken); textOrNull(diagnostic, "crossing_kind", crossing);
        diagnostic.put("adjacency_source", "retained_combat_6F8"); copy(diagnostic, "holding_defender", holding); diagnostic.put("holding_source", "retained_combat_6FE");
        copy(diagnostic, "constructor_rule_plan", plan); copy(diagnostic, "current_loaded_rule_effects", effects); diagnostic.put("loaded_selected_rule_effects_ready", effectsReady)
                .put("loaded_effect_source", "current_frame_phase_effect_database_8FC3E0").put("loaded_effect_selection_scope", "retained_rule_slots_before_commander_exclusion_and_holding_scale");
        copy(diagnostic, "current_rule_context", context); diagnostic.put("current_rule_context_frame_qualified", contextQualified);
        var gaps = diagnostic.putArray("missing_inputs"); missing.forEach(gaps::add); diagnostic.put("complete_constructor_ready", false).put("future_contact_preview", false);
        var history = diagnostic.putArray("unobserved_historical_inputs"); List.of("original_initiator_identity_and_role", "original_attacker_entry_province", "initial_participant_contexts_and_roster", "initial_loaded_effect_and_scale_operands").forEach(history::add);
        if (present(context)) copy(diagnostic, "current_rule_contributions_v1", contextQualified ? ruleContributions(sourceFrame, bool(holding), present(effects) ? object(effects) : null, object(context)) : null);
        output.set("retained_constructor_geometry_v1", diagnostic);
        boolean qualified = exact && actual;
        JsonNode stored = leaf(geography, "stored_advantage_sources_v1"), dynamic = leaf(geography, "current_dynamic_advantage_v1"), components = leaf(geography, "current_dynamic_components_v1"), own = leaf(geography, "current_own_nested_modifier_v1");
        if (present(stored)) {
            ObjectNode d = wrapper(source, qualified, "stored_inputs", stored); copy(d, "current_sources", qualified ? stored(sourceFrame, object(stored)) : null); output.set("stored_advantage_sources_v1", d);
            ObjectNode e = wrapper(source, qualified, "stored_inputs", stored); copy(e, "current_eligibility", qualified ? eligibility(sourceFrame, object(stored)).value() : null); output.set("opposite_effect_eligibility_v1", e);
        }
        if (present(dynamic)) { ObjectNode d = wrapper(source, qualified, "current_inputs", dynamic); copy(d, "current_advantage", qualified ? dynamic(sourceFrame, object(dynamic)) : null); output.set("current_dynamic_advantage_v1", d); }
        if (present(components)) { ObjectNode d = wrapper(source, qualified, "current_inputs", components); copy(d, "direct_inputs", dynamic); copy(d, "current_components", qualified ? components(sourceFrame, object(components), dynamic) : null); output.set("current_dynamic_components_v1", d); }
        if (present(own)) { ObjectNode d = wrapper(source, qualified, "own_inputs", own); copy(d, "stored_inputs", stored); copy(d, "current_nested_contributions", qualified ? own(sourceFrame, object(own), stored) : null); output.set("current_own_nested_modifier_v1", d); }
        return freeze(output);
    }

    private static ObjectNode ruleContributions(Frame frame, boolean holdingDefender, ObjectNode loaded, ObjectNode context) {
        ObjectNode holding = object(get(context, "holding_multiplier")), commander = object(get(context, "commander_exclusion"));
        Long multiplier = text(get(holding, "status")).equals("available") ? i64(get(holding, "province_multiplier_raw")) + (bool(get(holding, "province_has_holding")) ? i64(get(holding, "holding_modifier_raw")) : 0) : null;
        ObjectNode result = frame.into(base("actual_current_context_retained_rule_contributions")); boolOrNull(result, "selected_attacker_used_native_fallback", get(commander, "used_native_fallback"));
        result.set("selected_attacker_character_id_raw", get(commander, "selected_character_id_raw").deepCopy()); longOrNull(result, "current_holding_multiplier_raw", multiplier);
        ArrayNode output = result.putArray("rows"); boolean allReady = true;
        for (int index = 0; index < 3; index++) {
            String stage = STAGES.get(index); int side = index == 0 ? 0 : 1; ObjectNode effect = null;
            if (loaded != null) for (JsonNode e : rows(get(loaded, "rows"))) if (text(get(object(e), "stage")).equals(stage)) effect = object(e);
            boolean ready = true; Boolean selected = null, applied = null; Long scale = null, contribution = null; String missing = null;
            if (index == 2 && !holdingDefender) { selected = false; applied = false; contribution = 0L; }
            else if (index == 2 && multiplier == null) { ready = false; missing = "current_holding_multiplier"; }
            else if (index == 2 && multiplier <= 0) { selected = true; applied = false; scale = multiplier; contribution = 0L; }
            else if (effect == null || text(get(effect, "status")).equals("unavailable")) { ready = false; missing = "current_loaded_" + stage + "_effect"; }
            else if (text(get(effect, "status")).equals("not_selected")) { selected = false; applied = false; contribution = 0L; }
            else if (index == 1 && !text(get(commander, "status")).equals("available")) { selected = true; ready = false; missing = "current_selected_attacker_commander_flag_1A4"; }
            else { selected = true; applied = index != 1 || !bool(get(commander, "defender_adjacency_excluded")); scale = index == 2 ? multiplier : 100000L;
                long amount = applied ? BattleRecipientArithmetic.uncachedFixedMultiplyQ64(i64(get(effect, "advantage_points")) * 100000, scale) : 0; contribution = side == 0 ? amount : -amount; }
            ObjectNode row = empty().put("stage", stage).put("side_index", side).put("ready", ready); boxedBool(row, "selected", selected); boxedBool(row, "applied", applied);
            copy(row, "effect_key", effect == null ? null : get(effect, "key")); copy(row, "effect_advantage_points", effect == null ? null : get(effect, "advantage_points"));
            longOrNull(row, "multiplier_raw", scale); longOrNull(row, "signed_contribution_raw", contribution); textOrNull(row, "missing_input", missing); output.add(row); allReady &= ready;
        }
        return result.put("ready", allReady).put("complete_advantage_ready", false).put("historical_constructor_append_observed", false);
    }

    private static ObjectNode stored(Frame frame, ObjectNode stored) {
        ObjectNode result = frame.into(base("actual_current_combat_stored_advantage_sources")); copyFields(result, stored, "base_advantage_raw", "resolved_advantage_raw");
        ArrayNode output = result.putArray("sides"); boolean ready = true;
        for (JsonNode s : rows(get(stored, "sides"))) {
            ObjectNode side = object(s); int index = i32(get(side, "side_index")); JsonNode original = get(side, "rows"); ObjectNode target = empty().put("side_index", index).put("ready", !original.isNull()); copy(target, "unavailable_reason", get(side, "unavailable_reason"));
            if (original.isNull()) { target.putNull("rows"); ready = false; } else { ArrayNode values = target.putArray("rows"); int ordinal = 0;
                for (JsonNode r : rows(original)) { ObjectNode row = object(r), item = empty().put("native_ordinal", ordinal++); copyFields(item, row, "effect_key", "key_unavailable_reason"); long amount = i64(get(row, "contribution_raw")); item.put("retained_contribution_raw", amount).put("signed_contribution_raw", index == 0 ? amount : -amount); values.add(item); } }
            output.add(target);
        }
        return result.put("ready", ready).put("stored_values_ready", true).put("amount_source", "actual_stored_effect_ledger_row_8").put("base_source", "actual_stored_combat_6C8")
                .put("resolved_source", "actual_stored_combat_710_at_last_native_resolve").put("complete_advantage_ready", false).put("base_reconstructed_from_rows", false).put("historical_constructor_stage_observed", false).put("future_contact_preview", false);
    }

    private static ObjectNode dynamic(Frame frame, ObjectNode current) {
        ObjectNode result = frame.into(base("actual_current_combat_direct_dynamic_advantage")); copyFields(result, current, "base_advantage_raw", "stored_resolved_advantage_raw");
        ArrayNode output = result.putArray("sides"); List<Optional<Long>> totals = new ArrayList<>();
        for (JsonNode s : rows(get(current, "sides"))) { ObjectNode side = object(s); int index = i32(get(side, "side_index")); Long total = nullableLong(get(side, "side_dynamic_total_raw")); totals.add(Optional.ofNullable(total)); ObjectNode d = empty().put("side_index", index).put("role", index == 0 ? "attacker" : "defender").put("ready", total != null); copyFields(d, side, "current_roll_points", "selected_character_id_raw", "side_dynamic_total_raw", "unavailable_reason"); output.add(d); }
        boolean ready = totals.stream().allMatch(Optional::isPresent); Long currentValue = ready ? i64(get(current, "base_advantage_raw")) + totals.get(0).orElseThrow() - totals.get(1).orElseThrow() : null; long stored = i64(get(current, "stored_resolved_advantage_raw"));
        longOrNull(result, "current_getter_resolution_raw", currentValue); boxedBool(result, "matches_stored_resolved", currentValue == null ? null : currentValue == stored); longOrNull(result, "current_minus_stored_raw", currentValue == null ? null : currentValue - stored);
        return result.put("ready", ready).put("stored_values_ready", true).put("side_total_source", "actual_combat_258A470_null_explanation_sink").put("roll_source", "actual_stored_combat_6D0_6D4")
                .put("selected_character_source", "actual_stored_combat_94_3DC_native_generation_or_fallback").put("aggregate_source", "actual_cached_combat_side_110").put("base_source", "actual_stored_combat_6C8")
                .put("stored_resolved_source", "actual_stored_combat_710_at_last_native_resolve").put("native_state_refreshed", false).put("historical_constructor_stage_observed", false).put("future_contact_preview", false).put("complete_forecast_ready", false);
    }

    private static ObjectNode components(Frame frame, ObjectNode current, JsonNode direct) {
        ObjectNode result = frame.into(base("actual_current_combat_native_dynamic_components")); ArrayNode output = result.putArray("sides"); boolean all = true; int ordinal = 0;
        for (JsonNode s : rows(get(current, "sides"))) {
            ObjectNode side = object(s), selection = object(get(side, "selection")), relation = object(get(side, "relation")), commander = object(get(side, "commander")), aggregate = object(get(side, "side_aggregate"));
            int index = i32(get(side, "side_index")); Long c = nullableLong(get(commander, "total_raw")), a = nullableLong(get(aggregate, "total_raw")); boolean ready = c != null && a != null;
            Long observed = present(direct) ? nullableLong(get(object(rows(get(object(direct), "sides")).get(ordinal)), "side_dynamic_total_raw")) : null;
            Long total = ready ? i64(get(side, "current_roll_points")) * 100000 + c + a : null; ObjectNode row = empty().put("side_index", index).put("role", index == 0 ? "attacker" : "defender").put("ready", ready);
            copyFields(row, side, "current_roll_points", "selected_character_id_raw"); ObjectNode selected = empty().put("ready", !get(selection, "resolved_character_id_raw").isNull()); copyFields(selected, selection, "resolved_character_id_raw", "used_native_fallback", "unavailable_reason"); row.set("selection", selected);
            row.set("relation", component(relation, "kind_raw")); row.set("commander", component(commander, "total_raw")); row.set("side_aggregate", component(aggregate, "total_raw"));
            longOrNull(row, "side_total_from_components_raw", total); longOrNull(row, "observed_direct_total_raw", observed); boxedBool(row, "matches_observed_direct_total", total != null && observed != null ? total.equals(observed) : null);
            longOrNull(row, "components_minus_direct_raw", total != null && observed != null ? total - observed : null); output.add(row); all &= ready; ordinal++;
        }
        return result.put("ready", all).put("relation_source", "actual_combat_2589810").put("selected_source", "actual_combat_94_3DC_generation_5C67568_fallback_5C67570")
                .put("commander_source", "actual_selected_character_2589E10_null_explanation").put("side_aggregate_source", "actual_combat_side_110_25899C0_null_explanation")
                .put("commander_includes_selected_character_relation_aggregate", true).put("fine_source_rows_ready", false).put("nested_opposite_19F_eligibility_published", false).put("native_state_refreshed", false).put("future_contact_preview", false).put("complete_forecast_ready", false);
    }
    private static ObjectNode component(ObjectNode original, String valueField) { ObjectNode result = empty().put("ready", !get(original, valueField).isNull()); copy(result, "raw", get(original, valueField)); copy(result, "unavailable_reason", get(original, "unavailable_reason")); return result; }

    private static Eligibility eligibility(Frame frame, ObjectNode stored) {
        ObjectNode result = frame.into(base("actual_current_opposite_effect_eligibility")); ArrayNode output = result.putArray("sides"); List<JsonNode> sides = rows(get(stored, "sides"));
        List<Optional<Long>> totals = new ArrayList<>(); List<Optional<String>> reasons = new ArrayList<>(); boolean all = true;
        for (int index = 0; index < 2; index++) {
            ObjectNode opposite = object(sides.get(1 - index)); JsonNode original = get(opposite, "rows"); boolean sumReady = !original.isNull(), membership = sumReady; long sum = 0; ArrayNode values = null, eligibleIndices = null;
            if (!original.isNull()) { values = empty().arrayNode(); eligibleIndices = empty().arrayNode(); int ordinal = 0;
                for (JsonNode r : rows(original)) { ObjectNode row = object(r); JsonNode flags = leaf(row, "effect_flags_v1"); Long first = present(flags) ? nullableLong(get(object(flags), "flag88_raw")) : null, second = present(flags) ? nullableLong(get(object(flags), "flag89_raw")) : null;
                    boolean observed = first != null && second != null; Boolean eligible = observed ? first != 0 || second != 0 : null; long retained = i64(get(row, "contribution_raw")); Long contribution;
                    if (Boolean.TRUE.equals(eligible)) contribution = retained; else if (Boolean.FALSE.equals(eligible) || retained == 0) contribution = 0L; else contribution = null;
                    membership &= observed; if (contribution == null) sumReady = false; else sum += contribution;
                    ObjectNode item = empty().put("native_ledger_index", ordinal).put("retained_contribution_raw", retained); copy(item, "effect_key", get(row, "effect_key")); longOrNull(item, "flag88_raw", first); longOrNull(item, "flag89_raw", second); boxedBool(item, "eligible", eligible); longOrNull(item, "eligible_contribution_raw", contribution);
                    copy(item, "flags_unavailable_reason", present(flags) ? get(object(flags), "unavailable_reason") : empty().textNode("stored_effect_flags_v1_not_published")); if (Boolean.TRUE.equals(eligible)) eligibleIndices.add(ordinal); values.add(item); ordinal++;
                }
            }
            String reason = original.isNull() ? nullableText(get(opposite, "unavailable_reason")) : sumReady ? null : "opposite_nonzero_retained_amount_flags_unavailable";
            ObjectNode side = empty().put("side_index", index).put("opposite_side_index", i32(get(opposite, "side_index"))).put("ready", sumReady).put("membership_ready", membership);
            copy(side, "ordered_opposite_rows", values); copy(side, "eligible_native_ledger_indices", eligibleIndices); longOrNull(side, "eligible_contribution_sum_raw", sumReady ? sum : null); textOrNull(side, "unavailable_reason", reason); output.add(side);
            totals.add(sumReady ? Optional.of(sum) : Optional.empty()); reasons.add(Optional.ofNullable(reason)); all &= sumReady;
        }
        result.put("ready", all).put("membership_source", "current_loaded_effect_raw_88_OR_89_nonzero").put("amount_source", "actual_retained_16B_row_8").put("nested_19F_contribution_ready", false)
                .put("own_19F_operand_observed", false).put("current_effect_points_used_as_amount", false).put("constructor_clamp_reconstructed", false).put("future_contact_preview", false).put("complete_forecast_ready", false);
        return new Eligibility(result, totals, reasons);
    }

    private static ObjectNode own(Frame frame, ObjectNode own, JsonNode stored) {
        Eligibility eligibility = present(stored) ? eligibility(frame, object(stored)) : null; ObjectNode result = frame.into(base("actual_current_own_nested_modifier")); result.put("modifier_id", 415);
        ArrayNode output = result.putArray("sides"); boolean all = true;
        for (JsonNode s : rows(get(own, "sides"))) {
            ObjectNode original = object(s), selection = object(get(original, "selection")); int index = i32(get(original, "side_index")); ObjectNode side = empty().put("side_index", index).put("opposite_side_index", 1 - index);
            copyFields(side, original, "selected_character_id_raw"); copyFields(side, selection, "resolved_character_id_raw", "used_native_fallback"); copy(side, "selection_unavailable_reason", get(selection, "unavailable_reason"));
            for (String scope : SCOPES) {
                ObjectNode raw = object(get(original, scope)); Long amount = nullableLong(get(raw, "amount_raw")), total = eligibility == null ? null : eligibility.totals().get(index).orElse(null);
                boolean zero = amount != null && amount == 0, ready = amount != null && (zero || total != null); Long contribution = ready ? zero ? 0L : BattleRecipientArithmetic.uncachedFixedMultiplyQ64(-amount, total) : null;
                String reason = amount == null ? nullableText(get(raw, "unavailable_reason")) : ready ? null : eligibility == null ? "current_opposite_retained_rows_not_published" : eligibility.reasons().get(index).orElse(null);
                ObjectNode outputScope = empty().put("ready", ready).put("own_aggregate_source", scope.equals("combat_side_aggregate") ? "actual_Combat_side_plus_110" : "actual_native_resolved_selected_Character_28C3AE0")
                        .put("zero_shortcircuit", zero).put("opposite_sum_required", amount != null && !zero);
                longOrNull(outputScope, "own_modifier_19F_raw", amount); longOrNull(outputScope, "eligible_opposite_retained_sum_raw", total); longOrNull(outputScope, "nested_contribution_raw", contribution); textOrNull(outputScope, "unavailable_reason", reason); side.set(scope, outputScope); all &= ready;
            }
            output.add(side);
        }
        copy(result, "opposite_eligibility", eligibility == null ? null : eligibility.value());
        return result.put("ready", all).put("own_amount_source", "2303700_cached_sparse_aggregate_plus_68").put("product_source", "25895A0_wrap_negation_and_2C4D680_MAX_Q")
                .put("current_effect_points_used_as_amount", false).put("constructor_clamp_reconstructed", false).put("future_contact_preview", false).put("complete_forecast_ready", false);
    }
    private static ObjectNode wrapper(ObjectNode source, boolean qualified, String field, JsonNode original) { ObjectNode n = empty().put("schema_version", 1).put("current_frame_qualified", qualified); n.set("source", source.deepCopy()); n.set(field, original.deepCopy()); return n; }
    private static ObjectNode base(String mode) { return empty().put("schema_version", 1).put("mode", mode).put("scale", 100000); }
    private static JsonNode leaf(ObjectNode parent, String key) { return parent == null ? null : parent.get(key); }
    private static boolean present(JsonNode value) { return value != null && !value.isNull(); }
    private static List<JsonNode> rows(JsonNode value) { require(value != null && value.isArray(), "validated diagnostic array required"); List<JsonNode> result = new ArrayList<>(); value.forEach(result::add); return List.copyOf(result); }
    private static Long nullableLong(JsonNode value) { return value.isNull() ? null : i64(value); }
    private static String nullableText(JsonNode value) { return value.isNull() ? null : text(value); }
    private static void copy(ObjectNode target, String field, JsonNode value) { ArmyPublicSnapshot.copyNullable(target, field, value); }
    private static void copyFields(ObjectNode target, ObjectNode source, String... fields) { for (String field : fields) target.set(field, get(source, field).deepCopy()); }
    private static void textOrNull(ObjectNode n, String field, String value) { if (value == null) n.putNull(field); else n.put(field, value); }
    private static void longOrNull(ObjectNode n, String field, Long value) { if (value == null) n.putNull(field); else n.put(field, value); }
    private static void boxedBool(ObjectNode n, String field, Boolean value) { if (value == null) n.putNull(field); else n.put(field, value); }
    private static void boolOrNull(ObjectNode n, String field, JsonNode value) { copy(n, field, value); if (!value.isNull()) bool(value); }
    private static Obj freeze(ObjectNode value) { return DriverJson.object(bytes(value), DriverJson.MAX_NATIVE_BYTES); }
}
