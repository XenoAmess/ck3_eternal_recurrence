package org.xar.ck3.control.warbudget;

import static org.xar.ck3.control.warbudget.BudgetJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure translations of existing source-bound observations; no IO or invented political qualification. */
final class BudgetObservations {
    static final String PROFILE = "refused-liege-demand-primary-rebel-political-survival-v1";
    static final String POLITICAL_POLICY = "political-survival-conditional-count-reversal-spend-down-v1";
    static final String DEFENCE_POLICY = "major-defence-conditional-count-reversal-spend-down-v1";
    private static final String EXE = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private BudgetObservations() { }
    static ObjectNode sourceContract() {
        return obj().put("common/casus_belli_types/00_civil_war.txt", "a9f5d844413bd7acfd4d4b1611877ac34e78eb293f309c0e7a41f27aca3a0047")
            .put("common/scripted_effects/00_war_effects.txt", "f811d12ccb11f3aae2f61b234e930e20880be9b7c065bb9f4557400bd711722b")
            .put("common/opinion_modifiers/00_war_opinions.txt", "750864482d2d6c5d268424a1e03cba24301dedf853722d7fc12cb6f9fbcc68dc");
    }
    static boolean politicalQualified(JsonNode value) {
        if (!(value instanceof ObjectNode row) || !text(get(row, "status"), "available")
            || !text(get(row, "profile"), PROFILE) || !equal(get(row, "source_contract"), sourceContract())
            || !text(get(row, "player_role"), "primary_rebel_attacker") || !text(get(row, "game_version"), "1.20.0.4")
            || !no(get(row, "actual_penalty_verified")) || !no(get(row, "automatic_title_transfer_verified"))) { return false; }
        for (String key : List.of("war_id", "connection_generation", "query_sequence", "defender_character_id")) {
            if (!positive(get(row, key))) { return false; }
        }
        if (!(text(get(row, "observed_liege_relation"), "immediate_liege_character_id")
            || text(get(row, "observed_liege_relation"), "top_liege_character_id"))) { return false; }
        JsonNode cb = get(row, "active_casus_belli_identity"); JsonNode binding = get(row, "source_frame");
        if (!text(get(cb, "canonical_key"), "refused_liege_demand_war") || !positive(get(cb, "database_index"))) { return false; }
        try { return equal(frame(binding), binding); } catch (IllegalArgumentException error) { return false; }
    }
    static ObjectNode currentRoot(ObjectNode snapshot, JsonNode root) {
        JsonNode actor = get(get(snapshot, "played_character"), "character_id");
        return positive(actor) && positive(get(snapshot, "native_revision")) && exact(get(snapshot, "date_raw"))
            && root instanceof ObjectNode object && text(get(root, "status"), "available")
            && equal(get(root, "player_character_id"), actor) && equal(get(root, "snapshot_revision"), get(snapshot, "native_revision"))
            && equal(get(root, "date_raw"), get(snapshot, "date_raw")) ? object : obj();
    }
    static ObjectNode political(ObjectNode snapshot, ObjectNode war, JsonNode root) {
        ObjectNode observed;
        try { observed = frame(snapshot); } catch (IllegalArgumentException error) { return unavailable("current_frame_identity_unavailable"); }
        JsonNode actor = observed.get("played_character_id");
        JsonNode connection = get(get(snapshot, "diagnostics"), "connection_generation");
        if (!yes(get(snapshot, "paused")) || !positive(connection) || !yes(get(get(snapshot, "played_character"), "alive"))
            || !text(get(war, "player_side"), "attacker") || !yes(get(war, "player_is_primary_war_leader"))
            || !positive(get(war, "war_id")) || !exact(get(war, "player_relative_war_score"))) {
            return unavailable("current_primary_rebel_attacker_identity_unavailable");
        }
        var matches = rows(get(snapshot, "active_wars")).stream().filter(row -> equal(get(row, "war_id"), get(war, "war_id"))).toList();
        if (matches.size() != 1 || !matches.getFirst().equals(war)) { return unavailable("unique_current_active_war_unavailable"); }
        if (!(root instanceof ObjectNode) || !text(get(root, "status"), "available")
            || !positive(get(root, "player_character_id")) || !equal(get(root, "player_character_id"), actor)
            || !yes(get(root, "player_character_alive")) || !positive(get(root, "snapshot_revision"))
            || !equal(get(root, "snapshot_revision"), observed.get("native_revision"))
            || !exact(get(root, "date_raw")) || !equal(get(root, "date_raw"), observed.get("date_raw")) || !no(get(root, "independent"))) {
            return unavailable("same_frame_living_vassal_root_unavailable");
        }
        JsonNode provenance = get(root, "provenance");
        if (!text(get(provenance, "game_version"), "1.20.0.4") || !text(get(provenance, "executable_sha256"), EXE)
            || !text(get(provenance, "backend_id"), "ck3-1.20.0.4-native-campaign-root-context-v1")
            || !yes(get(get(root, "readiness"), "lieges_ready"))) { return unavailable("reviewed_exact_build_or_native_lieges_unavailable"); }
        JsonNode opponent = get(war, "primary_opponent_character_id"); String relation = null;
        for (String key : List.of("immediate_liege_character_id", "top_liege_character_id")) {
            if (positive(opponent) && !equal(opponent, actor) && positive(get(root, key)) && equal(get(root, key), opponent)) { relation = key; break; }
        }
        if (relation == null) { return unavailable("defender_not_observed_in_current_player_liege_chain"); }
        var queries = rows(get(snapshot, "war_termination_options")).stream().filter(row -> equal(get(row, "war_id"), get(war, "war_id"))).toList();
        if (queries.size() != 1) { return unavailable("unique_same_frame_cb_query_unavailable"); }
        ObjectNode query = queries.getFirst();
        boolean binding = text(get(query, "source"), "native") && positive(get(query, "query_sequence"))
            && positive(get(query, "queried_revision")) && positive(get(query, "queried_native_revision"))
            && positive(get(query, "queried_connection_generation"))
            && equal(get(query, "queried_snapshot_id"), observed.get("snapshot_id"))
            && equal(get(query, "queried_revision"), observed.get("revision"))
            && equal(get(query, "queried_native_revision"), observed.get("native_revision"))
            && equal(get(query, "episode_run_id"), observed.get("episode_run_id"))
            && equal(get(query, "queried_connection_generation"), connection)
            && text(get(query, "player_side"), "attacker") && yes(get(query, "player_is_primary_war_leader"))
            && exact(get(query, "player_relative_war_score")) && equal(get(query, "player_relative_war_score"), get(war, "player_relative_war_score"))
            && yes(get(query, "active_casus_belli_present"));
        if (!binding) { return unavailable("cb_query_not_bound_to_current_primary_attacker_frame"); }
        JsonNode cb = get(query, "active_casus_belli_identity");
        if (!text(get(cb, "canonical_key"), "refused_liege_demand_war") || !positive(get(cb, "database_index"))
            || !text(get(get(get(query, "options"), "surrender"), "outcome"), "attacker_defeat")) {
            return unavailable("reviewed_refused_demand_cb_or_attacker_defeat_identity_unavailable");
        }
        ObjectNode result = obj().put("status", "available").put("profile", PROFILE).put("player_role", "primary_rebel_attacker");
        result.set("war_id", war.get("war_id")); result.set("source_frame", observed); result.set("connection_generation", connection);
        result.set("query_sequence", query.get("query_sequence")); result.set("active_casus_belli_identity", cb.deepCopy());
        result.set("defender_character_id", opponent); result.put("observed_liege_relation", relation).put("game_version", "1.20.0.4");
        result.set("source_contract", sourceContract());
        result.putArray("exposure").add("conditional_imprisonment").add("liege_revoke_imprison_banish_execute_reasons");
        return result.put("actual_penalty_verified", false).put("automatic_title_transfer_verified", false)
            .put("reason", "source_reviewed_rebel_defeat_political_exposure_with_current_native_cb_and_liege_roles");
    }
    private static ObjectNode unavailable(String reason) { return obj().put("status", "unavailable").put("profile", PROFILE).put("reason", reason); }

    static ObjectNode finance(ObjectNode snapshot, JsonNode rootValue, JsonNode priceValue, JsonNode contractMonthsValue,
            BigInteger floor, int window, BigInteger other) {
        input(window >= 1 && window <= 18 && other.signum() >= 0, "declared allocation window/commitments invalid");
        ObjectNode root = maybe(rootValue);
        JsonNode gross = get(root, "player_monthly_gold_income"), maxRow = get(root, "player_max_monthly_gold_maintenance_v1");
        JsonNode maximum = text(get(maxRow, "status"), "available") ? get(maxRow, "value") : null;
        JsonNode money = get(snapshot, "played_character_gold"); JsonNode actor = get(get(snapshot, "played_character"), "character_id");
        if (!positive(actor) || !positive(get(snapshot, "native_revision")) || !exact(get(snapshot, "date_raw"))
            || !text(get(root, "status"), "available") || !equal(get(root, "player_character_id"), actor)
            || !equal(get(root, "snapshot_revision"), get(snapshot, "native_revision")) || !equal(get(root, "date_raw"), get(snapshot, "date_raw"))
            || !amount(gross) || !amount(maximum) || number(maximum, "raw").signum() < 0 || !amount(money)
            || !nonnegative(priceValue) || !positive(contractMonthsValue)) {
            return obj().put("status", "unavailable").put("reason", "same_frame_contract_treasury_income_or_maximum_maintenance_missing").put("retains_military_allocation", false);
        }
        BigInteger price = integer(priceValue), months = integer(contractMonthsValue).min(BigInteger.valueOf(window));
        BigInteger maintenance = number(maximum, "raw"), allocation = maintenance.multiply(months);
        BigInteger reserve = floor.max(allocation).add(other), treasury = number(money, "raw"), after = treasury.subtract(price);
        ObjectNode result = obj().put("status", "available").put("scale", 100000).put("contract_gold_raw", price);
        ObjectNode source = result.putObject("source_frame"); source.set("actor_character_id", actor); source.set("native_revision", snapshot.get("native_revision")); source.set("date_raw", snapshot.get("date_raw"));
        result.set("contract_months", contractMonthsValue);
        result.put("contract_payment_model", "native current one-time contract quote; no invented monthly company fee")
            .put("observed_treasury_raw", treasury).put("gold_after_contract_raw", after).put("gross_monthly_income_raw", number(gross, "raw"))
            .put("maximum_monthly_military_maintenance_raw", maintenance).put("gross_less_maximum_military_raw", number(gross, "raw").subtract(maintenance))
            .put("gross_less_maximum_military_is_net_income", false).put("maintenance_allocation_months", months)
            .put("maintenance_allocation_raw", allocation).put("required_gold_reserve_raw", reserve).put("reserve_floor_includes_military_allocation", true);
        if (other.signum() != 0) { result.put("other_reserved_gold_raw", other); }
        result.put("retains_military_allocation", after.compareTo(reserve) >= 0);
        ObjectNode runway = result.putObject("cash_only_maximum_military_runway");
        runway.put("numerator_gold_raw", after.max(ZERO)).put("denominator_gold_per_month_raw", maintenance);
        if (maintenance.signum() == 0) { runway.putNull("whole_months"); } else { runway.put("whole_months", after.max(ZERO).divide(maintenance)); }
        return result.put("future_gross_income_credited_raw", 0).put("complete_monthly_net_observed", false).put("future_cost_upper_bound", false)
            .put("scope", "constant current maximum military-rate allocation; nonmilitary expenses and new conditions excluded");
    }
    private static boolean amount(JsonNode row) { return row instanceof ObjectNode && exact(get(row, "raw")) && exact(get(row, "scale")) && number(row, "scale").equals(BigInteger.valueOf(100000)); }
}
