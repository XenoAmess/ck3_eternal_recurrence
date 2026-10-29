package org.xar.ck3.control.warbudget;

import static org.xar.ck3.control.warbudget.BudgetJson.*;
import static org.xar.ck3.control.warbudget.BudgetObservations.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Existing emergency budget policy translated without introducing a new spend or native action. */
public final class WarEmergencyBudget {
    private WarEmergencyBudget() { }

    public static int priorityLevel(ObjectNode war) {
        JsonNode stakes = get(war, "target_stakes_v1");
        boolean major = yes(get(stakes, "current_root_available"))
            && (yes(get(stakes, "primary_title_targeted")) || yes(get(war, "major_direct_title_targeted")));
        JsonNode score = get(war, "player_relative_war_score");
        boolean occupied = listPresent(get(war, "observed_primary_opponent_objective_occupation_province_ids"));
        boolean siege = listPresent(get(war, "observed_hostile_siege_in_player_subrealm_army_ids"));
        boolean deficit = yes(get(war, "raised_force_deficit"));
        boolean political = text(get(war, "player_side"), "attacker") && politicalQualified(get(war, "political_survival_stakes_v1"));
        if (!yes(get(war, "primary_player_war")) || !exact(score)
            || !(text(get(war, "player_side"), "defender") && major || political)) { return 0; }
        JsonNode deadline = get(war, "observed_risk_deadline_days");
        boolean imminent = siege && exact(deadline) && integer(deadline).compareTo(BigInteger.valueOf(7)) <= 0;
        if (integer(score).compareTo(BigInteger.valueOf(-75)) <= 0 && (occupied && (deficit || siege) || imminent && deficit)) { return 2; }
        if (political) { return 0; }
        return integer(score).compareTo(BigInteger.valueOf(-50)) <= 0 && (deficit || occupied || siege)
            || integer(score).compareTo(BigInteger.valueOf(-25)) <= 0 && occupied && siege ? 1 : 0;
    }

    public static ObjectNode observePolicy(ObjectNode snapshot, ObjectNode priority, JsonNode root, JsonNode spending) {
        ObjectNode normal = obj().put("level", 0).put("eligible", false).put("reason", "normal_policy_or_missing_emergency_evidence");
        ObjectNode current = currentRoot(snapshot, root);
        if (current.isEmpty() || !(spending instanceof ObjectNode) || !text(get(spending, "status"), "observed")) { return normal; }
        JsonNode binding = get(spending, "frame");
        if (!(binding instanceof ObjectNode) || !equal(get(binding, "actor_character_id"), get(get(snapshot, "played_character"), "character_id"))
            || !equal(get(binding, "native_revision"), get(snapshot, "native_revision")) || !equal(get(binding, "date_raw"), get(snapshot, "date_raw"))
            || !equal(get(binding, "snapshot_id"), get(snapshot, "snapshot_id"))) { return normal; }
        JsonNode reserved = get(get(spending, "budget"), "reserved_raw");
        if (!(reserved instanceof ObjectNode) || !nonnegative(get(reserved, "gold"))) { return normal; }
        JsonNode union = get(priority, "primary_war_hostile_union_v1");
        if (!(union instanceof ObjectNode) || !exact(get(union, "observed_current_soldiers")) || !exact(get(union, "shared_player_raised_soldiers"))) { return normal; }
        Set<BigInteger> majorIds = new HashSet<>();
        for (ObjectNode row : rows(get(current, "held_title_partition"))) {
            JsonNode title = get(row, "title");
            if (exact(get(title, "title_id")) && exact(get(title, "tier_raw")) && number(title, "tier_raw").compareTo(BigInteger.valueOf(3)) >= 0) {
                majorIds.add(number(title, "title_id"));
            }
        }
        ObjectNode chosen = null; int level = 0;
        for (ObjectNode original : rows(get(priority, "wars"))) {
            ObjectNode war = original.deepCopy(); ObjectNode live = liveWar(snapshot, get(war, "war_id"));
            war.set("political_survival_stakes_v1", political(snapshot, live, current));
            Set<JsonNode> enemies = new HashSet<>(); rows(get(live, "enemy_armies")).forEach(row -> enemies.add(get(row, "army_id")));
            var deadlines = war.putArray("observed_risk_deadlines"); BigInteger minimum = null;
            for (ObjectNode row : rows(get(live, "objective_province_states"))) {
                JsonNode siege = get(row, "active_siege"), selection = get(row, "current_besieging_army_selection");
                if (yes(get(row, "siege_observable")) && siege instanceof ObjectNode && selection instanceof ObjectNode
                    && enemies.contains(get(selection, "public_unit_id")) && nonnegative(get(siege, "days_left"))) {
                    ObjectNode deadline = obj(); deadline.set("province_id", get(row, "province_id")); deadline.set("days_left", siege.get("days_left")); deadlines.add(deadline);
                    BigInteger days = number(siege, "days_left"); minimum = minimum == null ? days : minimum.min(days);
                }
            }
            if (minimum == null) { war.putNull("observed_risk_deadline_days"); } else { war.put("observed_risk_deadline_days", minimum); }
            boolean direct = false; JsonNode targets = get(get(war, "target_stakes_v1"), "directly_held_target_title_ids");
            if (targets.isArray()) { for (JsonNode target : targets) { if (exact(target) && majorIds.contains(integer(target))) { direct = true; } } }
            war.put("major_direct_title_targeted", direct); int candidate = priorityLevel(war);
            if (candidate > level || candidate != 0 && candidate == level
                && number(war, "player_relative_war_score").compareTo(number(chosen, "player_relative_war_score")) < 0) { level = candidate; chosen = war; }
        }
        if (chosen == null) { return normal; }
        ObjectNode result = obj().put("level", level).put("eligible", true); result.set("war_id", chosen.get("war_id"));
        result.put("policy", politicalQualified(get(chosen, "political_survival_stakes_v1"))
            ? "political-survival-emergency-funding-candidate-v1" : "major-defence-emergency-funding-candidate-v1")
            .put("maintenance_window_months", level == 2 ? 3 : 6).put("fixed_gold_floor_raw", 0);
        result.set("other_reserved_gold_raw", reserved.get("gold")); result.set("source_frame", frame(snapshot));
        result.set("trigger_evidence", chosen); result.set("global_hostile_scope", union.deepCopy());
        return result.put("thresholds_are_policy_not_user_or_native_hard_limits", true).put("defeat_title_transfer_verified", false).put("war_resolution_verified", false);
    }

    public static JsonNode validSavedRevision(ObjectNode selected, JsonNode sourceFrame, ObjectNode snapshot) {
        JsonNode value = get(selected, "emergency_budget_revision_v1");
        if (!(value instanceof ObjectNode revision)) { return com.fasterxml.jackson.databind.node.NullNode.instance; }
        JsonNode binding = get(revision, "source_frame");
        if (!(binding instanceof ObjectNode) || !(sourceFrame instanceof ObjectNode) || !exact(get(snapshot, "native_revision"))
            || !equal(binding, sourceFrame) || !equal(get(binding, "episode_run_id"), get(snapshot, "episode_run_id"))
            || !equal(get(binding, "played_character_id"), get(get(snapshot, "played_character"), "character_id"))
            || !exact(get(binding, "native_revision")) || number(binding, "native_revision").compareTo(number(snapshot, "native_revision")) > 0
            || !exact(get(revision, "level")) || number(revision, "level").compareTo(BigInteger.ONE) < 0 || number(revision, "level").compareTo(BigInteger.valueOf(3)) > 0
            || !get(revision, "epoch_id").isTextual() || get(revision, "epoch_id").textValue().isEmpty()
            || !nonnegative(get(revision, "anchor_treasury_raw")) || !nonnegative(get(revision, "total_package_limit_raw"))
            || !nonnegative(get(revision, "ordinary_reserve_target_raw"))
            || number(revision, "total_package_limit_raw").compareTo(number(revision, "anchor_treasury_raw")) > 0) { return com.fasterxml.jackson.databind.node.NullNode.instance; }
        if (number(revision, "level").intValueExact() == 3) {
            JsonNode crisis = get(revision, "crisis_spend_down_v1");
            if (!(crisis instanceof ObjectNode) || !(text(get(crisis, "policy"), DEFENCE_POLICY) || text(get(crisis, "policy"), POLITICAL_POLICY))
                || !exact(get(crisis, "future_funding_credited_raw")) || number(crisis, "future_funding_credited_raw").signum() != 0
                || !no(get(crisis, "ordinary_military_allocation_retained")) || !no(get(crisis, "future_debt_occurrence_verified"))
                || !nonnegative(get(crisis, "current_treasury_raw")) || !nonnegative(get(crisis, "complete_contract_gold_raw"))
                || !nonnegative(get(crisis, "other_reserved_gold_raw")) || number(crisis, "current_treasury_raw")
                    .compareTo(number(crisis, "complete_contract_gold_raw").add(number(crisis, "other_reserved_gold_raw"))) < 0) { return com.fasterxml.jackson.databind.node.NullNode.instance; }
            if (text(get(crisis, "policy"), POLITICAL_POLICY)) {
                JsonNode proof = get(crisis, "political_survival_stakes_v1"); JsonNode politicalFrame = get(proof, "source_frame");
                if (!politicalQualified(proof) || !equal(get(politicalFrame, "episode_run_id"), get(binding, "episode_run_id"))
                    || !equal(get(politicalFrame, "played_character_id"), get(binding, "played_character_id"))
                    || number(politicalFrame, "native_revision").compareTo(number(binding, "native_revision")) > 0) { return com.fasterxml.jackson.databind.node.NullNode.instance; }
            }
        }
        return revision.deepCopy();
    }

    public static ObjectNode quote(ObjectNode snapshot, ObjectNode policy, JsonNode focusValue, ObjectNode local,
            JsonNode troopsValue, JsonNode price, JsonNode contractMonths, JsonNode root,
            ObjectNode normalFinance, ObjectNode pack) {
        ObjectNode inactive = obj().put("applied", false).put("reason", "no_qualified_emergency_marginal_value");
        ObjectNode focus = maybe(focusValue);
        if (!yes(get(policy, "eligible")) || focus.isEmpty()
            || !text(get(normalFinance, "status"), "available") || text(get(pack, "status"), "unavailable")) { return inactive; }
        input(positive(get(policy, "war_id")) && positive(get(focus, "war_id")),
            "eligible emergency quote requires positive exact war identities");
        if (!equal(get(focus, "war_id"), get(policy, "war_id"))) { return inactive; }
        boolean isLocal = text(get(local, "status"), "available");
        JsonNode ownValue = get(isLocal ? local : focus, isLocal ? "player_current_soldiers" : "observed_player_raised_soldiers");
        JsonNode enemyValue = get(isLocal ? local : focus, isLocal ? "enemy_current_soldiers" : "observed_enemy_raised_soldiers");
        if (!exact(ownValue) || !exact(enemyValue) || !positive(troopsValue)) { return inactive; }
        BigInteger own = integer(ownValue), enemy = integer(enemyValue), troops = integer(troopsValue), after = own.add(troops);
        if (enemy.compareTo(own) <= 0 || troops.multiply(BigInteger.TWO).compareTo(enemy.subtract(own)) < 0) { return inactive; }
        ObjectNode live = liveWar(snapshot, get(policy, "war_id")); ObjectNode political = political(snapshot, live, root);
        boolean politicalOk = politicalQualified(political); int level = inputInt(number(policy, "level"));
        if (text(get(live, "player_side"), "attacker") && (!politicalOk || level != 2 || !exact(get(live, "player_relative_war_score"))
            || number(live, "player_relative_war_score").compareTo(BigInteger.valueOf(-75)) > 0 || after.compareTo(enemy) <= 0)) { return inactive; }
        BigInteger other = number(policy, "other_reserved_gold_raw");
        ObjectNode finance = finance(snapshot, root, price, contractMonths, number(policy, "fixed_gold_floor_raw"),
            inputInt(number(policy, "maintenance_window_months")), other);
        if (!text(get(finance, "status"), "available")) { return inactive; }
        boolean crisis = level == 2 && yes(get(live, "player_is_primary_war_leader"))
            && (text(get(live, "player_side"), "defender") || politicalOk)
            && equal(get(live, "player_relative_war_score"), get(focus, "player_relative_war_score"))
            && no(get(finance, "retains_military_allocation")) && after.compareTo(enemy) > 0
            && number(normalFinance, "observed_treasury_raw").compareTo(integer(price).add(other)) >= 0;
        ObjectNode spendDown = obj();
        if (crisis) {
            spendDown.put("policy", politicalOk ? POLITICAL_POLICY : DEFENCE_POLICY);
            if (politicalOk) { spendDown.set("political_survival_stakes_v1", political); }
            spendDown.set("current_treasury_raw", normalFinance.get("observed_treasury_raw")); spendDown.set("complete_contract_gold_raw", price);
            spendDown.put("other_reserved_gold_raw", other).put("ordinary_military_allocation_retained", false);
            spendDown.putArray("overridden_policy_checks").add("military_cash_allocation").add("treasury_share_limit");
            spendDown.put("conditional_count_reversal_only", true).put("future_funding_credited_raw", 0).put("future_debt_occurrence_verified", false)
                .put("future_maintenance_debt_risk_accepted", true).putNull("loan_principal_or_debt_capacity").putNull("arrival_eta_days").putNull("battle_win_probability");
        }
        int effective = crisis ? 3 : level;
        BigInteger cash = crisis ? other : number(finance, "required_gold_reserve_raw");
        BigInteger committed = defaultInteger(pack, "committed_contract_quote_gold_raw", ZERO);
        ObjectNode previous = maybe(get(pack, "emergency_budget_epoch_v1"));
        boolean hasPrevious = get(pack, "emergency_budget_epoch_v1") instanceof ObjectNode;
        BigInteger anchor = defaultInteger(pack, "original_treasury_raw", number(normalFinance, "observed_treasury_raw"));
        BigInteger priorLimit = pack.has("effective_package_gold_limit_raw") ? integer(pack.get("effective_package_gold_limit_raw"))
            : defaultInteger(pack, "original_package_gold_limit_raw", ZERO);
        String epoch;
        if (hasPrevious) { epoch = inputText(previous.get("epoch_id")); }
        else if (!get(pack, "anchor_action_request_id").isNull()) {
            JsonNode identity = get(pack, "anchor_action_request_id");
            input(identity.isTextual(), "anchor action identity must be text/null/missing");
            if (!identity.textValue().isEmpty()) { epoch = identity.textValue(); }
            else { epoch = fallbackEpochFor(snapshot, policy); }
        }
        else {
            epoch = fallbackEpochFor(snapshot, policy);
        }
        int previousLevel = hasPrevious ? inputInt(defaultInteger(previous, "level", ZERO)) : 0;
        BigInteger limit; ObjectNode revision;
        if (previousLevel >= effective) {
            limit = number(previous, "total_package_limit_raw"); revision = previous.deepCopy();
            revision.set("source_frame", frame(snapshot)); revision.put("reuses_locked_level_limit", true);
        } else {
            if (previousLevel != 0 && number(snapshot, "native_revision").compareTo(number(get(previous, "source_frame"), "native_revision")) <= 0) {
                return inactive.put("reason", "higher_emergency_level_requires_new_native_observation");
            }
            limit = priorLimit.max(anchor.min(committed.add(number(finance, "observed_treasury_raw").subtract(cash).max(ZERO))));
            revision = obj().put("epoch_id", epoch).put("level", effective); revision.set("source_frame", frame(snapshot));
            revision.put("anchor_treasury_raw", anchor).put("total_package_limit_raw", limit).put("prior_total_limit_raw", priorLimit);
            revision.set("ordinary_reserve_target_raw", hasPrevious ? get(previous, "ordinary_reserve_target_raw") : normalFinance.get("required_gold_reserve_raw"));
            revision.put("committed_before_quote_raw", committed).put("newly_opened_package_gold_raw", limit.subtract(priorLimit).max(ZERO))
                .put("reuses_locked_level_limit", false); revision.set("policy_evidence", policy.deepCopy());
            if (crisis) { revision.set("crisis_spend_down_v1", spendDown.deepCopy()); }
        }
        ObjectNode result = obj().put("applied", true); result.set("finance", finance); result.set("revision", revision);
        result.put("crisis_spend_down_policy_eligible", crisis);
        if (crisis) { result.set("crisis_spend_down_v1", spendDown); }
        result.put("remaining_package_gold_raw", limit.subtract(committed).max(ZERO)).put("total_package_limit_raw", limit);
        result.putObject("conditional_counts").put("player", own).put("enemy", enemy).put("after_company_arrival", after)
            .put("deficit_closed_soldiers", troops.min(enemy.subtract(own))).put("local_native_members_available", isLocal)
            .put("scope", isLocal ? "validated local native members" : "deduplicated war armies; concentration and joint arrival unverified");
        return result.putNull("arrival_eta_days").put("arrival_estimate", "unbought company has no real CUnit route; ETA unknown")
            .put("cannot_guarantee_arrival_before_loss", true).putNull("battle_win_probability");
    }

    public static JsonNode recovery(ObjectNode snapshot, ObjectNode ledger, JsonNode root) {
        if (ledger.has("observed")) {
            input(ledger.get("observed").isArray(), "observed ledger rows must be an array; null is not empty");
            for (JsonNode row : ledger.get("observed")) { inputRecord(row); }
        }
        if (ledger.has("pending") && !ledger.get("pending").isNull()) { inputRecord(ledger.get("pending")); }
        List<ObjectNode> valid = new ArrayList<>(); List<ObjectNode> values = new ArrayList<>(rows(get(ledger, "observed")));
        if (get(ledger, "pending") instanceof ObjectNode pending) { values.add(pending); }
        for (ObjectNode row : values) {
            if (text(get(row, "status"), "native_rejected")) { continue; }
            JsonNode revision = validSavedRevision(maybe(get(get(row, "decision"), "selected_candidate")), get(row, "source_frame"), snapshot);
            if (revision instanceof ObjectNode object) { valid.add(object); }
        }
        if (valid.isEmpty()) { return com.fasterxml.jackson.databind.node.NullNode.instance; }
        ObjectNode normal = finance(snapshot, root, obj().put("x", 0).get("x"), obj().put("x", 18).get("x"), BigInteger.valueOf(20000000), 18, ZERO);
        boolean known = text(get(normal, "status"), "available");
        boolean ready = known && number(normal, "observed_treasury_raw").compareTo(number(normal, "required_gold_reserve_raw")) >= 0;
        ObjectNode result = obj().put("status", ready ? "normal_buffer_restored" : "recovering_emergency_cash_buffer").put("defer_new_economic_construction", !ready);
        result.set("normal_reserve_target_raw", get(normal, "required_gold_reserve_raw")); result.set("source_frame", frame(snapshot));
        result.put("finance_observed", known); result.set("latest_emergency_epoch_id", valid.getLast().get("epoch_id"));
        return result.put("unknown_pending_preserved", !get(ledger, "pending").isNull()).put("future_income_credited_raw", 0);
    }
    private static ObjectNode liveWar(ObjectNode snapshot, JsonNode warId) {
        return rows(get(snapshot, "active_wars")).stream().filter(row -> equal(get(row, "war_id"), warId)).findFirst().orElseGet(BudgetJson::obj);
    }
    private static String fallbackEpochFor(ObjectNode snapshot, ObjectNode policy) {
        List<BigInteger> warIds = new ArrayList<>(); JsonNode ids = get(get(policy, "global_hostile_scope"), "war_ids");
        input(ids.isArray(), "hostile war IDs required for epoch");
        ids.forEach(id -> warIds.add(integer(id))); return fallbackEpoch(frame(snapshot), warIds);
    }
}
