package org.xar.ck3.control.warbudget;

import static org.xar.ck3.control.warbudget.BudgetJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** The original complete war-spending-priority producer. It grants no procurement or army action. */
public final class OrdinaryWarPriority {
    private static final com.fasterxml.jackson.databind.ObjectMapper JSON = new com.fasterxml.jackson.databind.ObjectMapper();
    private OrdinaryWarPriority() { }
    public record Input(byte[] snapshot, byte[] nullableCampaignRoot) {
        public Input {
            snapshot = Objects.requireNonNull(snapshot).clone();
            nullableCampaignRoot = Objects.requireNonNull(nullableCampaignRoot).clone();
            record(StrictJson.parse(snapshot, StrictJson.EXPLICIT_MAX_BYTES));
            JsonNode root = StrictJson.parse(nullableCampaignRoot, StrictJson.EXPLICIT_MAX_BYTES);
            input(root.isNull() || root.isObject(), "nullable current campaign root required");
        }
        @Override public byte[] snapshot() { return snapshot.clone(); }
        @Override public byte[] nullableCampaignRoot() { return nullableCampaignRoot.clone(); }
    }
    public static final class Observation {
        private final ObjectNode originalSnapshot;
        private final ObjectNode priority;
        private Observation(ObjectNode snapshot, ObjectNode priority) {
            this.originalSnapshot = snapshot.deepCopy(); this.priority = priority.deepCopy();
        }
        public byte[] toJson() { return encode(priority); }
        public byte[] sourceSnapshot() { return encode(originalSnapshot); }
        public boolean deferredOptionalConstruction() { return yes(priority.get("defer_new_economic_construction")); }
        public boolean actionAuthority() { return false; }
        public java.util.Optional<BigInteger> countCurrentMembers(List<Integer> unitIds, java.util.Optional<BigInteger> enemyWar) {
            return countCurrentFullMembers(unitIds.stream().map(BigInteger::valueOf).toList(), enemyWar);
        }

        /** Full public CUnit identity, including zero and unsigned 32-bit values; shared original strength cache arithmetic. */
        public java.util.Optional<BigInteger> countCurrentFullMembers(List<BigInteger> unitIds, java.util.Optional<BigInteger> enemyWar) {
            Objects.requireNonNull(enemyWar); unitIds = List.copyOf(unitIds);
            if (new HashSet<>(unitIds).size() != unitIds.size()) return java.util.Optional.empty();
            List<ObjectNode> universe;
            if (enemyWar.isPresent()) {
                List<ObjectNode> war = rows(get(originalSnapshot, "active_wars")).stream()
                        .filter(w -> exact(get(w, "war_id")) && integer(get(w, "war_id")).equals(enemyWar.orElseThrow())).toList();
                if (war.size() != 1 || !get(war.getFirst(), "enemy_armies").isArray()) return java.util.Optional.empty();
                universe = rows(get(war.getFirst(), "enemy_armies"));
            } else {
                if (!get(originalSnapshot, "player_armies").isArray()) return java.util.Optional.empty();
                universe = rows(get(originalSnapshot, "player_armies"));
            }
            List<ObjectNode> selected = new ArrayList<>();
            for (BigInteger id : unitIds) {
                List<ObjectNode> matches = universe.stream().filter(a -> exact(get(a, "army_id"))
                        && integer(get(a, "army_id")).equals(id)).toList();
                if (matches.size() != 1) return java.util.Optional.empty();
                selected.add(matches.getFirst());
            }
            return java.util.Optional.ofNullable(count(selected, originalSnapshot,
                    enemyWar.isPresent() ? "active_war_enemy" : "player",
                    enemyWar.<JsonNode>map(com.fasterxml.jackson.databind.node.BigIntegerNode::valueOf).orElse(null)));
        }

        ObjectNode value() { return priority.deepCopy(); }
        ObjectNode snapshot() { return originalSnapshot.deepCopy(); }
    }

    public record FinanceRequest(Input observations, java.util.Optional<BigInteger> price,
            java.util.Optional<BigInteger> contractMonths, BigInteger goldFloor, int reservationMonths,
            BigInteger otherCommitments) {
        public FinanceRequest {
            Objects.requireNonNull(observations); Objects.requireNonNull(price); Objects.requireNonNull(contractMonths);
            Objects.requireNonNull(goldFloor); Objects.requireNonNull(otherCommitments);
            input(goldFloor.signum() >= 0 && reservationMonths >= 1 && reservationMonths <= 18 && otherCommitments.signum() >= 0,
                    "nonnegative original finance policy parameters required");
        }
    }
    /** The existing shared finance arithmetic, with no copied reserve formula or policy alteration. */
    public static byte[] finance(FinanceRequest request) {
        ObjectNode snapshot = record(StrictJson.parse(request.observations().snapshot(), StrictJson.EXPLICIT_MAX_BYTES));
        JsonNode root = StrictJson.parse(request.observations().nullableCampaignRoot(), StrictJson.EXPLICIT_MAX_BYTES);
        JsonNode price = request.price().<JsonNode>map(com.fasterxml.jackson.databind.node.BigIntegerNode::valueOf)
                .orElse(com.fasterxml.jackson.databind.node.NullNode.instance);
        JsonNode months = request.contractMonths().<JsonNode>map(com.fasterxml.jackson.databind.node.BigIntegerNode::valueOf)
                .orElse(com.fasterxml.jackson.databind.node.NullNode.instance);
        return encode(BudgetObservations.finance(snapshot, root, price, months, request.goldFloor(),
                request.reservationMonths(), request.otherCommitments()));
    }


    public static Observation observe(Input input) {
        ObjectNode snapshot = record(StrictJson.parse(input.snapshot(), StrictJson.EXPLICIT_MAX_BYTES));
        JsonNode suppliedRoot = StrictJson.parse(input.nullableCampaignRoot(), StrictJson.EXPLICIT_MAX_BYTES);
        List<ObjectNode> own = rows(get(snapshot, "player_armies")), active = rows(get(snapshot, "active_wars"));
        BigInteger ownCount = get(snapshot, "player_armies").isArray() ? count(own, snapshot, "player", null) : null;
        boolean retreating = !own.isEmpty() && own.stream().allMatch(a -> yes(get(a, "retreating")));
        List<ObjectNode> primary = active.stream().filter(w -> yes(get(w, "player_is_primary_war_leader"))).toList();
        List<ObjectNode> hostile = primary.stream().flatMap(w -> rows(get(w, "enemy_armies")).stream()).toList();
        boolean complete = primary.stream().allMatch(w -> get(w, "enemy_armies").isArray());
        BigInteger enemyUnion = complete && !primary.isEmpty() ? count(hostile, snapshot, "active_war_enemy", null) : null;
        ObjectNode root = BudgetObservations.currentRoot(snapshot, suppliedRoot);
        JsonNode primaryTitle = get(get(root, "primary_title"), "title_id");
        Set<BigInteger> held = new HashSet<>();
        for (ObjectNode row : rows(get(root, "held_title_partition"))) {
            JsonNode id = get(get(row, "title"), "title_id"); if (exact(id)) held.add(integer(id));
        }
        List<ObjectNode> wars = new ArrayList<>();
        for (ObjectNode war : active) {
            ObjectNode political = BudgetObservations.political(snapshot, war, root);
            boolean nonleading = nonleading(snapshot, war);
            JsonNode score = get(war, "player_relative_war_score");
            boolean main = yes(get(war, "player_is_primary_war_leader"));
            List<BigInteger> targets = ids(get(war, "targeted_title_ids"), false);
            boolean exposed = main && text(get(war, "player_side"), "defender") && !targets.isEmpty();
            List<JsonNode> sieges = rows(get(war, "enemy_armies")).stream()
                    .filter(a -> text(get(a, "army_state"), "sieging") && yes(get(a, "siege_province_in_player_subrealm")))
                    .map(a -> get(a, "army_id")).toList();
            List<ObjectNode> objectives = rows(get(war, "objective_province_states"));
            JsonNode opponent = get(war, "primary_opponent_character_id");
            List<JsonNode> occupations = objectives.stream().filter(s -> yes(get(s, "occupation_observable"))
                    && yes(get(s, "is_occupied")) && positive(opponent)
                    && equal(get(s, "occupying_character_id"), opponent)).map(s -> get(s, "province_id")).toList();
            BigInteger enemy = get(war, "enemy_armies").isArray()
                    ? count(rows(get(war, "enemy_armies")), snapshot, "active_war_enemy", get(war, "war_id")) : null;
            boolean deficit = ownCount != null && enemy != null && ownCount.compareTo(enemy) < 0;
            boolean losing = exact(score) && integer(score).signum() < 0;
            List<String> reasons = new ArrayList<>();
            if (main && losing && BudgetObservations.politicalQualified(political)) reasons.add("losing_primary_rebel_war_exposes_political_survival");
            if (main && losing && exposed) reasons.add("losing_primary_defence_exposes_target_titles");
            if (main && text(get(war, "player_side"), "defender") && deficit
                    && allObjects(get(snapshot, "player_armies")) && allObjects(get(war, "enemy_armies")))
                reasons.add("primary_defence_observed_raised_force_outnumbered");
            if (main && losing && deficit) reasons.add("losing_own_war_and_observed_raised_force_outnumbered");
            if (main && losing && primary.size() > 1 && ownCount != null && enemyUnion != null && ownCount.compareTo(enemyUnion) < 0)
                reasons.add("losing_own_war_and_shared_raised_force_below_unique_primary_hostiles");
            if (main && !sieges.isEmpty()) reasons.add("observed_hostile_siege_in_player_subrealm");
            if (nonleading) reasons.add("qualified_nonleading_defence_stationary_hostile_siege_in_player_realm");
            if (main && retreating) reasons.add("entire_observed_own_raised_force_currently_retreating");
            if (main && text(get(war, "player_side"), "defender") && !occupations.isEmpty())
                reasons.add("observed_primary_opponent_occupation_of_defensive_objective");
            if (main && exact(score) && integer(score).compareTo(BigInteger.valueOf(-100)) <= 0)
                reasons.add("score_defeat_threshold_reached_war_still_observed_active");
            ObjectNode w = obj(); w.set("war_id", get(war, "war_id")); w.put("primary_player_war", main);
            w.set("player_side", get(war, "player_side")); w.set("player_relative_war_score", score);
            w.set("political_survival_stakes_v1", political); putIds(w, "possible_defensive_target_title_ids", exposed ? targets : List.of());
            ObjectNode stakes = w.putObject("target_stakes_v1"); stakes.put("current_root_available", !root.isEmpty());
            if (exact(primaryTitle)) stakes.put("primary_title_targeted", targets.contains(integer(primaryTitle))); else stakes.putNull("primary_title_targeted");
            if (!root.isEmpty()) putIds(stakes, "directly_held_target_title_ids", held.stream().filter(targets::contains).sorted().toList());
            else stakes.putNull("directly_held_target_title_ids");
            stakes.put("source", "same-native-frame root title identities; CB defeat transfer remains unverified");
            w.put("major_direct_title_targeted", rows(get(root, "held_title_partition")).stream().anyMatch(t ->
                    exact(get(get(t, "title"), "title_id")) && targets.contains(integer(get(get(t, "title"), "title_id")))
                    && exact(get(get(t, "title"), "tier_raw")) && integer(get(get(t, "title"), "tier_raw")).compareTo(BigInteger.valueOf(3)) >= 0));
            w.put("defeat_title_transfer_verified", false); w.put("active_war_observed", true); w.put("war_resolution_verified", false);
            w.put("new_procurement_suppressed_by_score_policy", exact(score) && integer(score).compareTo(BigInteger.valueOf(-100)) <= 0);
            putNodes(w, "observed_hostile_siege_in_player_subrealm_army_ids", sieges);
            putNodes(w, "observed_primary_opponent_objective_occupation_province_ids", occupations);
            w.put("objective_control_projection_available", !objectives.isEmpty());
            w.put("all_observed_own_raised_armies_currently_retreating", retreating);
            nullable(w, "observed_player_raised_soldiers", ownCount); nullable(w, "observed_enemy_raised_soldiers", enemy);
            if (ownCount == null || enemy == null) w.putNull("raised_force_deficit"); else w.put("raised_force_deficit", deficit);
            w.set("existing_operational_strength_balance_v1", operational(snapshot, get(war, "war_id")));
            putStrings(w, "protect_cash_reasons", reasons);
            ObjectNode n = w.putObject("nonleading_realm_siege_cash_protection_v1");
            n.put("qualified_current_scope", nonleading); n.put("procurement_scope_extended", nonleading);
            putStrings(n, "reasons", nonleading ? List.of("qualified_nonleading_defence_stationary_hostile_siege_in_player_realm") : List.of());
            n.put("arrival_before_loss_verified", false); n.put("defeat_title_transfer_verified", false);
            wars.add(w);
        }
        List<ObjectNode> protectedWars = wars.stream().filter(w -> !rowsOrValues(get(w, "protect_cash_reasons")).isEmpty()).sorted(
                Comparator.comparing((ObjectNode w) -> !yes(get(get(w, "target_stakes_v1"), "primary_title_targeted")))
                .thenComparing(w -> rowsOrValues(get(get(w, "target_stakes_v1"), "directly_held_target_title_ids")).isEmpty())
                .thenComparing(w -> rowsOrValues(get(w, "possible_defensive_target_title_ids")).isEmpty())
                .thenComparing(w -> exact(get(w, "player_relative_war_score")) ? integer(get(w, "player_relative_war_score")) : BigInteger.ZERO)
                .thenComparing(w -> exact(get(w, "war_id")) ? integer(get(w, "war_id")) : BigInteger.valueOf(-1))).toList();
        ObjectNode out = obj().put("schema", "xar.war-spending-priority.v1").put("read_only", true);
        out.put("defer_new_economic_construction", wars.stream().anyMatch(w -> !rowsOrValues(get(w, "protect_cash_reasons")).isEmpty()));
        out.put("nonleading_realm_siege_construction_deferred_v1", wars.stream().anyMatch(w -> yes(get(get(w, "nonleading_realm_siege_cash_protection_v1"), "qualified_current_scope"))));
        ArrayNode outWars = out.putArray("wars"); wars.forEach(outWars::add);
        out.put("count_scope", "observed raised armies; no unraised reserves or promised allies");
        putNodes(out, "cash_protection_priority_war_ids", protectedWars.stream().map(w -> get(w, "war_id")).toList());
        out.put("cash_priority_does_not_assign_armies", true);
        ObjectNode union = out.putObject("primary_war_hostile_union_v1");
        putNodes(union, "war_ids", primary.stream().map(w -> get(w, "war_id")).toList());
        putIds(union, "unique_army_ids", hostile.stream().map(a -> get(a, "army_id")).filter(BudgetJson::exact).map(BudgetJson::integer).distinct().sorted().toList());
        nullable(union, "observed_current_soldiers", enemyUnion); nullable(union, "shared_player_raised_soldiers", ownCount);
        if (ownCount == null || enemyUnion == null) union.putNull("shared_force_deficit"); else union.put("shared_force_deficit", ownCount.compareTo(enemyUnion) < 0);
        union.put("future_or_unraised_reinforcements_bounded", false); out.putNull("war_win_probability");
        return new Observation(snapshot, out);
    }

    static BigInteger count(List<ObjectNode> armies, ObjectNode snapshot, String role, JsonNode warId) {
        boolean current = (text(get(snapshot, "army_strengths_status"), "available") || text(get(snapshot, "army_strengths_status"), "partial"))
                && equal(get(snapshot, "army_strengths_queried_snapshot_id"), get(snapshot, "snapshot_id"))
                && equal(get(snapshot, "army_strengths_queried_revision"), get(snapshot, "revision"));
        List<ObjectNode> strengths = current ? rows(get(snapshot, "army_strengths")) : List.of();
        java.util.Map<BigInteger, BigInteger> counts = new HashMap<>();
        for (ObjectNode army : armies) {
            JsonNode id = get(army, "army_id"), value = get(army, "soldiers");
            List<ObjectNode> matched = strengths.stream().filter(s -> equal(get(s, "army_id"), id)
                    && text(get(s, "scope_role"), role) && (warId == null || rowsOrValues(get(s, "war_ids")).contains(warId))).toList();
            if (matched.size() == 1 && text(get(matched.getFirst(), "status"), "available")) value = get(matched.getFirst(), "current_soldiers");
            if (!exact(id) || !nonnegative(value)) return null;
            BigInteger prior = counts.putIfAbsent(integer(id), integer(value));
            if (prior != null && !prior.equals(integer(value))) return null;
        }
        return counts.values().stream().reduce(BigInteger.ZERO, BigInteger::add);
    }
    static boolean nonleading(ObjectNode s, ObjectNode w) {
        JsonNode actor = get(get(s, "played_character"), "character_id"), nativeRev = get(s, "native_revision");
        JsonNode diag = get(s, "diagnostics"), played = get(s, "played_character"), score = get(w, "player_relative_war_score");
        boolean frame = text(get(s, "source"), "injected-dll-named-pipe") && positive(nativeRev)
                && text(get(s, "snapshot_id"), "native:" + nativeRev.asText()) && nonnegative(get(s, "revision"))
                && exact(get(s, "date_raw")) && get(s, "episode_run_id").isTextual() && !get(s, "episode_run_id").textValue().isEmpty()
                && yes(get(s, "paused")) && yes(get(s, "map_ready")) && get(s, "active_event").isNull()
                && get(s, "pending_character_interaction").isNull() && text(get(played, "source"), "native")
                && positive(actor) && yes(get(played, "alive")) && yes(get(diag, "connected"))
                && positive(get(diag, "bridge_pid")) && nonnegative(get(diag, "connection_generation"));
        if (!frame || !text(get(w, "source"), "native") || !positive(get(w, "war_id"))
                || !text(get(w, "player_side"), "defender") || !no(get(w, "player_is_primary_war_leader"))
                || !exact(score) || integer(score).compareTo(BigInteger.valueOf(-100)) <= 0 || integer(score).compareTo(BigInteger.valueOf(100)) >= 0)
            return false;
        return rows(get(w, "enemy_armies")).stream().anyMatch(e -> text(get(e, "source"), "native")
                && positive(get(e, "army_id")) && positive(get(e, "owner_character_id")) && !equal(get(e, "owner_character_id"), actor)
                && no(get(e, "controllable")) && text(get(e, "army_state"), "sieging")
                && exact(get(e, "army_state_code")) && integer(get(e, "army_state_code")).equals(BigInteger.valueOf(3))
                && no(get(e, "in_combat")) && no(get(e, "retreating")) && positive(get(e, "current_province_id"))
                && yes(get(e, "siege_province_in_player_subrealm")) && e.has("move_target_province_id")
                && get(e, "move_target_province_id").isNull() && get(e, "route_province_ids").isArray()
                && get(e, "route_province_ids").isEmpty() && text(get(e, "route_read_status"), "complete_empty"));
    }
    private static JsonNode operational(ObjectNode snapshot, JsonNode warId) {
        // Exact cached row summary is optional and never supplies win probability.
        if (!positive(warId) || !yes(get(snapshot, "paused"))
                || !(text(get(snapshot, "army_strengths_status"), "available") || text(get(snapshot, "army_strengths_status"), "partial"))
                || !equal(get(snapshot, "army_strengths_queried_snapshot_id"), get(snapshot, "snapshot_id"))
                || !equal(get(snapshot, "army_strengths_queried_revision"), get(snapshot, "revision"))) return com.fasterxml.jackson.databind.node.NullNode.instance;
        List<ObjectNode> all = rows(get(snapshot, "army_strengths")).stream().filter(a -> rowsOrValues(get(a, "war_ids")).contains(warId)).toList();
        if (all.isEmpty() || all.stream().anyMatch(a -> !text(get(a, "status"), "available") || !nonnegative(get(a, "army_id"))
                || integer(get(a, "army_id")).compareTo(BigInteger.valueOf(0xFFFF_FFFEL)) > 0)) return com.fasterxml.jackson.databind.node.NullNode.instance;
        List<ObjectNode> friendly = all.stream().filter(a -> text(get(a, "scope_role"), "player") || text(get(a, "scope_role"), "active_war_ally")).toList();
        List<ObjectNode> enemy = all.stream().filter(a -> text(get(a, "scope_role"), "active_war_enemy")).toList();
        if (friendly.isEmpty() || enemy.isEmpty()) return com.fasterxml.jackson.databind.node.NullNode.instance;
        for (ObjectNode row : all) for (String key : List.of("current_soldiers", "maximum_soldiers", "ai_base_power_raw"))
            if (!exact(get(row, key))) return com.fasterxml.jackson.databind.node.NullNode.instance;
        ObjectNode out = obj().put("status", "available"); out.set("war_id", warId);
        putIds(out, "friendly_army_ids", friendly.stream().map(a -> number(a, "army_id")).sorted().toList());
        putIds(out, "enemy_army_ids", enemy.stream().map(a -> number(a, "army_id")).sorted().toList());
        BigInteger fc = sum(friendly, "current_soldiers"), ec = sum(enemy, "current_soldiers"), fp = sum(friendly, "ai_base_power_raw"), ep = sum(enemy, "ai_base_power_raw");
        out.put("friendly_current_soldiers", fc); out.put("enemy_current_soldiers", ec);
        out.put("friendly_maximum_soldiers", sum(friendly, "maximum_soldiers"));
        out.put("enemy_maximum_soldiers", sum(enemy, "maximum_soldiers"));
        out.put("friendly_ai_base_power_raw", fp); out.put("enemy_ai_base_power_raw", ep);
        out.put("hostile_operational_overmatch", ec.multiply(BigInteger.valueOf(4)).compareTo(fc.multiply(BigInteger.valueOf(5))) > 0
                || ep.multiply(BigInteger.valueOf(4)).compareTo(fp.multiply(BigInteger.valueOf(5))) > 0);
        out.put("interpretation", "operational_routing_risk_not_battle_win_odds");
        return out;
    }
    private static byte[] encode(ObjectNode value) {
        try { return JSON.writeValueAsBytes(value); }
        catch (java.io.IOException failure) { throw new IllegalStateException("priority encoding failed", failure); }
    }
    private static BigInteger sum(List<ObjectNode> rows, String key) { return rows.stream().map(r -> number(r, key)).reduce(BigInteger.ZERO, BigInteger::add); }
    static List<JsonNode> rowsOrValues(JsonNode value) { if (!value.isArray()) return List.of(); List<JsonNode> out = new ArrayList<>(); value.forEach(out::add); return out; }
    static List<BigInteger> ids(JsonNode value, boolean positive) { return rowsOrValues(value).stream().filter(v -> positive ? positive(v) : nonnegative(v)).map(BudgetJson::integer).toList(); }
    static void nullable(ObjectNode out, String key, BigInteger value) { if (value == null) out.putNull(key); else out.put(key, value); }
    static void putNodes(ObjectNode out, String key, List<JsonNode> values) { ArrayNode array = out.putArray(key); values.forEach(array::add); }
    static void putIds(ObjectNode out, String key, List<BigInteger> values) { ArrayNode array = out.putArray(key); values.forEach(array::add); }
    static void putStrings(ObjectNode out, String key, List<String> values) { ArrayNode array = out.putArray(key); values.forEach(array::add); }
    private static boolean allObjects(JsonNode value) { return value.isArray() && rowsOrValues(value).stream().allMatch(JsonNode::isObject); }
}
