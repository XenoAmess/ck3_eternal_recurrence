package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Production-only provenance over the original no-CombatID shell advantage contract. */
final class PhaseAdvantageModelCodec {
    private PhaseAdvantageModelCodec() { }
    static final List<String> CALL_ORDER = List.of("width", "attacker_adjacency", "defender_adjacency", "attacker_terrain", "defender_terrain", "side_context_0", "side_context_1", "supply_0", "supply_1", "holding_defender_1", "gathering_army_0", "gathering_army_1", "debt_0_owner_then_treasury", "debt_1_owner_then_treasury", "unreformed_faith_0", "unreformed_faith_1", "side_finalize_0", "side_finalize_1");
    static final List<String> SOURCE_ORDER = List.of("attacker_adjacency", "defender_adjacency", "attacker_terrain", "defender_terrain", "supply_0", "supply_1", "holding_defender_1", "gathering_army_0", "gathering_army_1", "debt_0_owner", "debt_0_treasury", "debt_1_owner", "debt_1_treasury", "unreformed_faith_0", "unreformed_faith_1");
    private static final Set<String> DEFENDER = Set.of("defender_adjacency", "defender_terrain", "supply_1", "holding_defender_1", "gathering_army_1", "debt_1_owner", "debt_1_treasury", "unreformed_faith_1");
    static ObjectNode normalize(JsonNode value) {
        ObjectNode row = object(value, "status scale scenario_policy observation_origin side_inputs constructor_call_order constructor_sources base_static_accumulator_raw resolved_dynamic unavailable_reason", "phase advantage");
        scale(row.get("scale"), "phase advantage scale");
        eq(row.get("scenario_policy"), "explicit_hypothetical_fixed_at_contact_no_reinforcements", "phase advantage scenario policy drifted");
        eq(row.get("observation_origin"), "native_exact_build_production", "phase advantage origin is not production");
        require(strings(row.get("constructor_call_order"), "constructor call order").equals(CALL_ORDER), "constructor call order drifted");
        // The available phase requires all helper inputs. A model-level unavailable is not a partial model.
        eq(row.get("status"), "available", "available phase requires full advantage model");
        require(nil(row.get("unavailable_reason")), "available advantage has a reason");
        validateSides(row.get("side_inputs"));
        BigInteger accumulator = validateSources(row.get("constructor_sources"));
        long base = i64(row.get("base_static_accumulator_raw"), "base_static_accumulator_raw");
        require(accumulator.equals(BigInteger.valueOf(base)), "base advantage disagrees with source ledger");
        validateDynamic(row.get("resolved_dynamic"), base);
        return row.deepCopy();
    }
    private static void validateSides(JsonNode value) {
        ArrayNode rows = array(value, "advantage side_inputs"); require(rows.size() == 2, "advantage requires two sides");
        for (int index = 0; index < 2; index++) {
            ObjectNode row = object(rows.get(index), "side primary_army_id ordered_army_ids supply primary_army_gathering_raw owner_character_id owner_debt_selector_raw treasury_debt_selector_raw", "advantage side");
            eq(row.get("side"), index == 0 ? "attacker" : "defender", "advantage side order changed");
            List<Integer> armies = ids(row.get("ordered_army_ids"), false, true, "ordered_army_ids");
            require(nonnegative(row.get("primary_army_id"), "primary_army_id") == armies.getFirst(), "advantage primary army changed request order");
            ObjectNode supply = object(row.get("supply"), "selected_key selected_effect_identity selected_effect_points eligible_soldiers_total eligible_soldiers_supplied eligible_soldiers_running_low eligible_soldiers_starving", "supply");
            String selected = token(supply.get("selected_key"), "selected_key", "supply_state_supplied_advantage", "supply_state_running_low_advantage", "supply_state_starving_advantage");
            long total = nonnegative64(supply.get("eligible_soldiers_total"), "eligible_soldiers_total");
            long supplied = nonnegative64(supply.get("eligible_soldiers_supplied"), "eligible_soldiers_supplied");
            long low = nonnegative64(supply.get("eligible_soldiers_running_low"), "eligible_soldiers_running_low");
            long starving = nonnegative64(supply.get("eligible_soldiers_starving"), "eligible_soldiers_starving");
            BigInteger totalN = BigInteger.valueOf(total), suppliedN = BigInteger.valueOf(supplied), lowN = BigInteger.valueOf(low);
            require(totalN.equals(suppliedN.add(lowN).add(BigInteger.valueOf(starving))), "supply counts disagree");
            String expected = total <= 0 || suppliedN.shiftLeft(1).compareTo(totalN) > 0 ? "supply_state_supplied_advantage"
                    : suppliedN.add(lowN).shiftLeft(1).compareTo(totalN) > 0 ? "supply_state_running_low_advantage" : "supply_state_starving_advantage";
            require(selected.equals(expected), "supply strict-majority selection changed");
            text(supply.get("selected_effect_identity"), "selected_effect_identity"); i32(supply.get("selected_effect_points"), "selected_effect_points");
            i32(row.get("primary_army_gathering_raw"), "primary_army_gathering_raw");
            positive(row.get("owner_character_id"), "owner_character_id"); i32(row.get("owner_debt_selector_raw"), "owner_debt_selector_raw");
            if (!nil(row.get("treasury_debt_selector_raw"))) i32(row.get("treasury_debt_selector_raw"), "treasury_debt_selector_raw");
        }
    }
    private static BigInteger validateSources(JsonNode value) {
        ArrayNode rows = array(value, "constructor_sources");
        require(rows.size() >= SOURCE_ORDER.size(), "advantage omitted a constructor stage");
        Set<String> seen = new HashSet<>(); int prior = -1, append = 0; BigInteger accumulator = BigInteger.ZERO;
        for (int index = 0; index < rows.size(); index++) {
            ObjectNode row = object(rows.get(index), "stage_order append_order stage side source_key effect_advantage_points scale_raw signed_contribution_raw accumulator_before_raw accumulator_after_raw selected applied skip_reason", "constructor source");
            require(i32(row.get("stage_order"), "stage_order") == index, "source stage_order changed");
            String stage = text(row.get("stage"), "stage"); int position = SOURCE_ORDER.indexOf(stage);
            require(position >= prior && position >= 0, "constructor stage order changed"); prior = position; seen.add(stage);
            boolean defender = DEFENDER.contains(stage); eq(row.get("side"), defender ? "defender" : "attacker", "source side changed");
            boolean selected = bool(row.get("selected"), "selected"), applied = bool(row.get("applied"), "applied");
            require(!applied || selected, "unselected source applied");
            Integer points = null;
            if (selected) { text(row.get("source_key"), "source_key"); points = i32(row.get("effect_advantage_points"), "effect_advantage_points"); }
            else require(nil(row.get("source_key")) && nil(row.get("effect_advantage_points")), "unselected source invented effect");
            long scale = i64(row.get("scale_raw"), "scale_raw");
            BigInteger expected = applied ? BigInteger.valueOf(points.longValue()).multiply(BigInteger.valueOf(scale)) : BigInteger.ZERO;
            if (defender) expected = expected.negate();
            long contribution = i64(row.get("signed_contribution_raw"), "signed_contribution_raw");
            require(expected.equals(BigInteger.valueOf(contribution)), "signed source contribution mismatch");
            require(BigInteger.valueOf(i64(row.get("accumulator_before_raw"), "accumulator_before_raw")).equals(accumulator), "source accumulator_before mismatch");
            accumulator = accumulator.add(expected).max(BigInteger.valueOf(-10_000_000)).min(BigInteger.valueOf(10_000_000));
            require(BigInteger.valueOf(i64(row.get("accumulator_after_raw"), "accumulator_after_raw")).equals(accumulator), "source per-effect clamp mismatch");
            if (applied) { require(i32(row.get("append_order"), "append_order") == append++, "append order changed"); require(nil(row.get("skip_reason")), "applied source has skip reason"); }
            else { require(nil(row.get("append_order")), "skipped source has append order"); text(row.get("skip_reason"), "skip_reason"); }
        }
        require(seen.equals(new HashSet<>(SOURCE_ORDER)), "constructor stage coverage mismatch"); return accumulator;
    }
    private static void validateDynamic(JsonNode value, long base) {
        ObjectNode row = object(value, "status helper_status context_mode roll_policy sides side_0_dynamic_raw side_1_dynamic_raw resolved_advantage_at_zero_roll_raw original_total_helper_raw original_total_helper_match", "resolved_dynamic");
        eq(row.get("status"), "available", "dynamic status unavailable"); eq(row.get("helper_status"), "original_helpers_matched", "dynamic original helpers mismatch");
        eq(row.get("context_mode"), "temporary_unregistered_local_context", "dynamic context mode changed"); eq(row.get("roll_policy"), "zero_in_query_sampled_offline", "dynamic roll policy changed");
        ArrayNode sides = array(row.get("sides"), "dynamic sides"); require(sides.size() == 2, "dynamic requires two sides");
        long[] totals = new long[2];
        for (int index = 0; index < 2; index++) {
            ObjectNode side = object(sides.get(index), "side battle_commander_character_id battle_commander_selected battle_commander_selection primary_army_gathering_raw gathering relation_kind_raw roll_points roll_raw target_conditionals_residual_raw commander_dynamic_raw side_dynamic_raw side_total_raw contribution_to_resolved_raw", "dynamic side");
            eq(side.get("side"), index == 0 ? "attacker" : "defender", "dynamic side order changed");
            boolean selected = bool(side.get("battle_commander_selected"), "battle_commander_selected");
            if (selected) positive(side.get("battle_commander_character_id"), "battle_commander_character_id");
            else require(nil(side.get("battle_commander_character_id")), "absent commander invented ID");
            eq(side.get("battle_commander_selection"), "native_0x23C8A60", "commander selection provenance changed");
            require(bool(side.get("gathering"), "gathering") == (i32(side.get("primary_army_gathering_raw"), "primary_army_gathering_raw") > 0), "gathering bool disagrees with raw");
            i32(side.get("relation_kind_raw"), "relation_kind_raw");
            require(i32(side.get("roll_points"), "roll_points") == 0 && i64(side.get("roll_raw"), "roll_raw") == 0, "precontact query rolled RNG");
            long residual = i64(side.get("target_conditionals_residual_raw"), "target_conditionals_residual_raw"), commander = i64(side.get("commander_dynamic_raw"), "commander_dynamic_raw"), dynamic = i64(side.get("side_dynamic_raw"), "side_dynamic_raw");
            require(selected || commander == 0, "absent commander contributed");
            long total = i64(side.get("side_total_raw"), "side_total_raw");
            require(BigInteger.valueOf(residual).add(BigInteger.valueOf(commander)).add(BigInteger.valueOf(dynamic)).equals(BigInteger.valueOf(total)), "dynamic component sum mismatch");
            BigInteger signed = index == 0 ? BigInteger.valueOf(total) : BigInteger.valueOf(total).negate();
            require(signed.equals(BigInteger.valueOf(i64(side.get("contribution_to_resolved_raw"), "contribution_to_resolved_raw"))), "dynamic side contribution sign changed"); totals[index] = total;
        }
        require(i64(row.get("side_0_dynamic_raw"), "side_0_dynamic_raw") == totals[0] && i64(row.get("side_1_dynamic_raw"), "side_1_dynamic_raw") == totals[1], "dynamic side totals mismatch");
        long resolved = i64(row.get("resolved_advantage_at_zero_roll_raw"), "resolved_advantage_at_zero_roll_raw");
        require(BigInteger.valueOf(base).add(BigInteger.valueOf(totals[0])).subtract(BigInteger.valueOf(totals[1])).equals(BigInteger.valueOf(resolved)), "resolved advantage sum mismatch");
        require(bool(row.get("original_total_helper_match"), "original_total_helper_match") && i64(row.get("original_total_helper_raw"), "original_total_helper_raw") == resolved, "original total helper equality mismatch");
    }
}
