package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.OrdinaryPolicy.Draft;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetCodec;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactCodec;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.warbudget.OrdinaryWarPriority;
import org.xar.ck3.control.warbudget.WarEmergencyBudget;

/** Original strategic-reserve chooser over current native quotes. No fake ETA, credit, payment or submit authority. */
public final class OrdinaryMercenaryChoice {
    private static final BigInteger ZERO = BigInteger.ZERO;
    private static final BigInteger FLOOR = BigInteger.valueOf(20_000_000);
    private static final int OUTPUT_MAX_BYTES = 4_194_304;
    private OrdinaryMercenaryChoice() { }
    public static final class Assessment {
        private final Obj original;
        private final Optional<NativeMercenaryMarket.Company> selected;
        private Assessment(Obj original, Optional<NativeMercenaryMarket.Company> selected) { this.original = original; this.selected = selected; }
        public Obj original() { return original; }
        public Optional<NativeMercenaryMarket.Company> selected() { return selected; }
        public boolean actionSubmissionQualified() { return false; }
        public BigInteger fundingCreditRaw() { return ZERO; }
    }
    public static Assessment assess(PlanningRequest request, Draft previous, OrdinaryWarPriority.Observation observedPriority,
            NativeMercenaryMarket.Observation market, Optional<Obj> currentRoot,
            FinanceStatePort.Ledger procurement, FeastBudgetPolicy.Observed spending) {
        require(procurement.document().domain() == FinanceStatePort.Domain.MERCENARY, "actual mercenary body required");
        require(object(parse(observedPriority.sourceSnapshot()), "priority original").equals(request.observations().snapshot())
                && market.packet().receipt().request().before().equals(request.before()), "chooser sources crossed current frame");
        ObjectNode snapshot = node(request.observations().snapshot()), priority = node(object(parse(observedPriority.toJson()), "priority"));
        JsonNode root = currentRoot.<JsonNode>map(OrdinaryMercenaryChoice::node).orElse(com.fasterxml.jackson.databind.node.NullNode.instance);
        ObjectNode spendingNode = obj(StrictJson.parse(FeastBudgetCodec.encode(spending)));
        ObjectNode emergencyPolicy = WarEmergencyBudget.observePolicy(snapshot, priority, root, spendingNode);
        List<ObjectNode> wars = recoverable(priority);
        if (yes(get(emergencyPolicy, "eligible"))) wars.sort(Comparator.comparing(w -> !equal(get(w, "war_id"), get(emergencyPolicy, "war_id"))));
        else wars.removeIf(w -> numberOr(w, "player_relative_war_score", ZERO).compareTo(BigInteger.valueOf(-100)) <= 0);
        ObjectNode focus = wars.isEmpty() ? null : wars.getFirst();
        ObjectNode strategic = strategicNeed(focus);
        ObjectNode packageBudget = packageBudget(snapshot, priority, node(procurement.original()), focus);
        ObjectNode local = local(request, previous, observedPriority, focus);
        JsonNode money = get(snapshot, "played_character_gold");
        BigInteger treasury = exact(get(money, "raw")) && equal(get(money, "scale"), num(100000)) ? integer(get(money, "raw")) : null;
        List<ObjectNode> candidates = new ArrayList<>();
        List<NativeMercenaryMarket.Company> companies = market.companies();
        for (NativeMercenaryMarket.Company company : companies) {
            Optional<List<BigInteger>> vector = company.terms().costs();
            boolean fullCosts = company.terms().available() && vector.isPresent()
                    && vector.orElseThrow().size() == 10 && vector.orElseThrow().stream().allMatch(n -> n.signum() >= 0);
            BigInteger price = fullCosts ? vector.orElseThrow().getFirst() : null;
            BigInteger troops = company.currentSoldiers().orElse(null), spawn = company.spawnProvince().orElse(null);
            ObjectNode finance = obj(StrictJson.parse(OrdinaryWarPriority.finance(new OrdinaryWarPriority.FinanceRequest(
                    new OrdinaryWarPriority.Input(observedPriority.sourceSnapshot(), currentRoot.map(OrdinaryMercenaryChoice::wire).orElse(new byte[]{'n','u','l','l'})),
                    Optional.ofNullable(price), company.terms().durationMonths(), FLOOR, 18, ZERO))));
            ObjectNode emergency = WarEmergencyBudget.quote(snapshot, emergencyPolicy,
                    focus == null ? com.fasterxml.jackson.databind.node.NullNode.instance : focus, local,
                    troops == null ? com.fasterxml.jackson.databind.node.NullNode.instance : num(troops),
                    price == null ? com.fasterxml.jackson.databind.node.NullNode.instance : num(price),
                    company.terms().durationMonths().<JsonNode>map(OrdinaryMercenaryChoice::num).orElse(com.fasterxml.jackson.databind.node.NullNode.instance),
                    root, finance, packageBudget);
            ObjectNode candidatePackage = packageBudget.deepCopy();
            if (yes(get(emergency, "applied"))) {
                finance = obj(get(emergency, "finance"));
                candidatePackage.put("status", "available");
                candidatePackage.set("emergency_budget_epoch_v1", get(emergency, "revision"));
                candidatePackage.set("effective_package_gold_limit_raw", get(emergency, "total_package_limit_raw"));
                candidatePackage.set("remaining_package_gold_raw", get(emergency, "remaining_package_gold_raw"));
            }
            List<String> reasons = new ArrayList<>();
            if (!market.available()) reasons.add("native_current_actor_date_company_collection_unavailable");
            if (!company.hireReady() || !fullCosts) reasons.add("native_composition_or_complete_hire_terms_not_ready");
            if (company.terms().canHire() != NativeMercenaryMarket.Truth.TRUE || company.terms().canAfford() != NativeMercenaryMarket.Truth.TRUE)
                reasons.add("native_hire_or_affordability_rejected");
            if (company.employer().isPresent()) reasons.add("company_already_employed");
            if (!yes(get(finance, "retains_military_allocation")) && !yes(get(emergency, "crisis_spend_down_policy_eligible")))
                reasons.add("same_frame_contract_and_military_cash_allocation_not_ready_or_not_retained");
            if (troops == null || troops.signum() <= 0) reasons.add("positive_current_company_strength_unavailable");
            if (spawn == null || !company.positionReady() || company.attemptedInWar() != NativeMercenaryMarket.Truth.TRUE)
                reasons.add("native_active_war_spawn_unavailable");
            if (focus == null) reasons.add("no_current_recoverable_own_war_need");
            List<BigInteger> spawnHostiles = rows(get(snapshot, "active_wars")).stream().flatMap(w -> rows(get(w, "enemy_armies")).stream())
                    .filter(a -> spawn != null && equal(get(a, "current_province_id"), num(spawn)) && exact(get(a, "army_id")))
                    .map(a -> integer(get(a, "army_id"))).distinct().sorted().toList();
            if (!spawnHostiles.isEmpty()) reasons.add("currently_observed_hostile_army_at_predicted_spawn");
            List<Integer> stagingIds = rows(get(snapshot, "player_armies")).stream().filter(a -> stationary(a, spawn))
                    .map(a -> integer(get(a, "army_id")).intValueExact()).distinct().sorted().toList();
            BigInteger staging = stagingIds.isEmpty() ? null : observedPriority.countCurrentMembers(stagingIds, Optional.empty()).orElse(null);
            BigInteger ownCount = optionalInteger(get(local, "player_current_soldiers")), enemyCount = optionalInteger(get(local, "enemy_current_soldiers"));
            BigInteger combined = ownCount != null && troops != null ? ownCount.add(troops) : null;
            boolean flip = ownCount != null && enemyCount != null && combined != null
                    && ownCount.compareTo(enemyCount) < 0 && enemyCount.compareTo(combined) < 0;
            BigInteger reference = ownCount != null && ownCount.signum() > 0 ? ownCount : optionalInteger(get(focus, "observed_player_raised_soldiers"));
            if (reference == null || reference.signum() <= 0) reference = optionalInteger(get(focus, "observed_enemy_raised_soldiers"));
            BigInteger minimum = reference != null && reference.signum() > 0 ? reference.add(BigInteger.valueOf(3)).divide(BigInteger.valueOf(4)) : null;
            if (!flip && !yes(get(strategic, "worth_strategic_reserve"))) reasons.add("no_concrete_stakes_or_current_deterioration_worth_strategic_spend");
            if (!flip && (minimum == null || troops == null || troops.compareTo(minimum) < 0))
                reasons.add("strategic_marginal_headcount_below_policy_quarter_or_unknown");
            int divisor = flip || yes(get(strategic, "critical_primary_title")) ? 2 : 3;
            BigInteger ordinaryLimit = treasury != null && treasury.signum() >= 0 ? treasury.divide(BigInteger.valueOf(divisor)) : null;
            BigInteger limit = yes(get(emergency, "applied")) ? optionalInteger(get(emergency, "remaining_package_gold_raw")) : ordinaryLimit;
            if (limit == null || price == null || price.compareTo(limit) > 0) reasons.add("contract_exceeds_declared_cash_opportunity_cost_limit");
            if (text(get(candidatePackage, "status"), "unavailable")) reasons.add("same_purpose_original_procurement_package_budget_unavailable");
            else if (text(get(candidatePackage, "status"), "available") && (price == null
                    || price.compareTo(integer(get(candidatePackage, "remaining_package_gold_raw"))) > 0))
                reasons.add("contract_exceeds_remaining_same_purpose_package_budget");
            ObjectNode row = objectNode(); row.put("company_id", company.id()); nullable(row, "gold_cost_raw", price);
            if (fullCosts) array(row, "quoted_resource_costs_raw", vector.orElseThrow()); else row.putNull("quoted_resource_costs_raw");
            nullable(row, "gold_after_hire_raw", treasury != null && price != null ? treasury.subtract(price) : null);
            nullable(row, "company_current_soldiers", troops); nullable(row, "friendly_staging_soldiers", staging);
            nullable(row, "reinforced_staging_soldiers", staging != null && troops != null ? staging.add(troops) : null);
            nullable(row, "predicted_auto_raise_province_id", spawn);
            array(row, "staging_army_ids", stagingIds.stream().map(BigInteger::valueOf).toList());
            row.put("spawn_requires_preexisting_friendly_army", false); array(row, "observed_hostile_at_predicted_spawn_army_ids", spawnHostiles);
            row.put("purpose", flip ? "conditional_local_deficit_reinforcement" : "strategic_reserve_for_threatened_own_war");
            array(row, "purpose_war_ids", focus == null ? List.of() : List.of(integer(get(focus, "war_id"))));
            row.set("strategic_need", strategic.deepCopy()); nullable(row, "marginal_reference_observed_soldiers", reference);
            nullable(row, "strategic_minimum_marginal_soldiers", minimum); nullable(row, "cash_opportunity_cost_limit_raw", limit);
            row.put("cash_opportunity_cost_fraction", yes(get(emergency, "applied")) ? "locked_emergency_epoch" : "1/" + divisor);
            row.set("procurement_package_budget_v1", candidatePackage);
            if (yes(get(emergency, "applied"))) {
                row.set("emergency_budget_revision_v1", get(emergency, "revision"));
                row.set("emergency_marginal_value_v1", get(emergency, "conditional_counts"));
                nullable(row, "ordinary_cash_opportunity_cost_limit_raw", ordinaryLimit);
                ObjectNode risk = row.putObject("emergency_arrival_risk_v1");
                for (String key : List.of("arrival_eta_days", "arrival_estimate", "cannot_guarantee_arrival_before_loss", "battle_win_probability")) risk.set(key, get(emergency, key));
            }
            if (yes(get(emergency, "crisis_spend_down_policy_eligible"))) row.set("crisis_spend_down_v1", get(emergency, "crisis_spend_down_v1"));
            array(row, "numerical_balance_reversed_war_ids", flip && focus != null ? List.of(integer(get(focus, "war_id"))) : List.of());
            nullable(row, "conditional_local_player_soldiers_after_arrival", combined); row.set("local_comparison", local);
            row.put("comparison_condition", "company arrives and remains available; arrival and effective combat strength unverified");
            row.put("multiple_primary_wars_share_force", values(get(get(priority, "primary_war_hostile_union_v1"), "war_ids")).size() > 1);
            row.set("comparison_enemy_current_soldiers", get(get(priority, "primary_war_hostile_union_v1"), "observed_current_soldiers"));
            row.put("global_enemy_count_is_purchase_reversal_threshold", false).putNull("arrival_eta_days");
            row.put("arrival_risk_accepted_for_strategic_purpose", reasons.isEmpty()).put("guaranteed_emergency_rescue", false).putNull("battle_win_probability");
            row.set("finance", finance); strings(row, "rejection_reasons", reasons); candidates.add(row);
        }
        List<ObjectNode> eligible = candidates.stream().filter(r -> values(get(r, "rejection_reasons")).isEmpty()).toList();
        List<ObjectNode> flips = eligible.stream().filter(r -> !values(get(r, "numerical_balance_reversed_war_ids")).isEmpty()).toList();
        List<ObjectNode> emergency = eligible.stream().filter(r -> r.has("emergency_budget_revision_v1")).toList();
        List<ObjectNode> emergencyFlips = emergency.stream().filter(r -> integer(get(get(r, "emergency_marginal_value_v1"), "after_company_arrival"))
                .compareTo(integer(get(get(r, "emergency_marginal_value_v1"), "enemy"))) > 0).toList();
        Comparator<ObjectNode> cheapest = Comparator.comparing((ObjectNode r) -> integer(get(r, "gold_cost_raw")))
                .thenComparing(r -> integer(get(r, "company_current_soldiers")).negate()).thenComparing(r -> integer(get(r, "company_id")));
        ObjectNode chosen;
        if (!flips.isEmpty()) chosen = flips.stream().min(cheapest).orElseThrow();
        else if (!emergencyFlips.isEmpty()) chosen = emergencyFlips.stream().min(cheapest).orElseThrow();
        else if (!emergency.isEmpty()) chosen = emergency.stream().min((a,b) -> ratio(a,b,
                integer(get(get(a, "emergency_marginal_value_v1"), "deficit_closed_soldiers")),
                integer(get(get(b, "emergency_marginal_value_v1"), "deficit_closed_soldiers")), false)).orElseThrow();
        else chosen = eligible.stream().min((a,b) -> ratio(a,b, integer(get(a, "company_current_soldiers")),
                integer(get(b, "company_current_soldiers")), true)).orElse(null);
        ObjectNode out = objectNode().put("schema", "xar.mercenary-reinforcement-tradeoff.v1").put("policy_revision", "strategic-reserve-v1");
        out.set("actor_character_id", get(get(snapshot, "played_character"), "character_id")); out.set("war_spending_priority", priority);
        var all = out.putArray("candidates"); candidates.forEach(all::add);
        out.set("selected_company_id", chosen == null ? com.fasterxml.jackson.databind.node.NullNode.instance : get(chosen, "company_id"));
        out.set("selected_candidate", chosen == null ? com.fasterxml.jackson.databind.node.NullNode.instance : chosen);
        out.put("minimum_gold_reserve_raw", FLOOR).put("recommendation", chosen == null ? "continue_existing_war_action" : "hire_local_reinforcement");
        out.put("selection_comparison", "highest-stakes protected war; cheapest conditional local count flip, otherwise soldiers per quoted gold; lower cost then full CompanyID");
        out.put("emergency_selection_comparison", "qualified emergency conditional count reversal first, otherwise deficit closure per gold; no arrival or win probability");
        ObjectNode thresholds = out.putObject("policy_thresholds"); thresholds.put("strategic_defensive_exposure_score_at_most", -25)
                .put("strategic_minimum_marginal_headcount_fraction", "1/4 of observed relevant current force")
                .put("ordinary_strategic_treasury_spend_cap_fraction", "1/3")
                .put("primary_title_or_conditional_local_flip_treasury_spend_cap_fraction", "1/2")
                .put("native_rules_or_calibrated_win_probability", false);
        out.put("arrival_model", "native predicted auto-raise province; no pre-hire CUnit route; ETA unknown accepted as strategic risk");
        out.putNull("arrival_eta_days").putNull("battle_win_probability").put("postcondition_verified", false);
        strings(out, "model_limits", List.of("current headcount is not combat power", "no rescue credit for a current battle or siege deadline",
                "no pre-hire route or guaranteed arrival time", "current military allocation is not a future cost bound",
                "reserve efficiency is not a calibrated utility or win probability", "native spawn selector does not publish every safety branch"));
        BigInteger selectedId = chosen == null ? null : integer(get(chosen, "company_id"));
        Optional<NativeMercenaryMarket.Company> selected = selectedId == null ? Optional.empty()
                : companies.stream().filter(c -> c.id().equals(selectedId)).findFirst();
        return new Assessment(DriverJson.object(wire(out), OUTPUT_MAX_BYTES), selected);
    }

    private static List<ObjectNode> recoverable(ObjectNode priority) {
        List<BigInteger> order = values(get(priority, "cash_protection_priority_war_ids")).stream().filter(OrdinaryMercenaryChoice::exact).map(OrdinaryMercenaryChoice::integer).toList();
        List<ObjectNode> result = new ArrayList<>(rows(get(priority, "wars")).stream().filter(w -> !values(get(w, "protect_cash_reasons")).isEmpty()
                && exact(get(w, "war_id")) && exact(get(w, "player_relative_war_score"))
                && (integer(get(w, "player_relative_war_score")).compareTo(BigInteger.valueOf(-100)) > 0 || WarEmergencyBudget.priorityLevel(w) > 0)).toList());
        result.sort(Comparator.comparingInt(w -> { int i=order.indexOf(integer(get(w, "war_id"))); return i<0 ? order.size() : i; })); return result;
    }
    private static ObjectNode strategicNeed(ObjectNode war) {
        ObjectNode result = objectNode(); List<String> reasons = new ArrayList<>();
        boolean losing = exact(get(war, "player_relative_war_score")) && integer(get(war, "player_relative_war_score")).signum() < 0;
        boolean defensive = text(get(war, "player_side"), "defender");
        boolean primary = defensive && losing && yes(get(get(war, "target_stakes_v1"), "primary_title_targeted"));
        if (losing && values(get(war, "protect_cash_reasons")).stream().anyMatch(v -> text(v, "losing_primary_rebel_war_exposes_political_survival")))
            reasons.add("losing_primary_rebel_war_has_source_reviewed_political_survival_stakes");
        if (primary) reasons.add("losing_defence_targets_current_primary_title");
        if (defensive && losing && !values(get(get(war, "target_stakes_v1"), "directly_held_target_title_ids")).isEmpty()) reasons.add("losing_defence_targets_current_directly_held_title");
        if (!values(get(war, "possible_defensive_target_title_ids")).isEmpty() && exact(get(war, "player_relative_war_score"))
                && integer(get(war, "player_relative_war_score")).compareTo(BigInteger.valueOf(-25)) <= 0) reasons.add("defensive_title_exposure_and_policy_score_at_most_minus25");
        if (losing && !values(get(war, "observed_primary_opponent_objective_occupation_province_ids")).isEmpty()) reasons.add("losing_defence_with_observed_objective_occupation");
        if (losing && !values(get(war, "observed_hostile_siege_in_player_subrealm_army_ids")).isEmpty()) reasons.add("losing_own_war_with_observed_player_subrealm_hostile_siege");
        result.put("worth_strategic_reserve", !reasons.isEmpty()).put("critical_primary_title", primary); strings(result, "reasons", reasons); return result;
    }
    public static boolean modelNeed(OrdinaryWarPriority.Observation priority) {
        return recoverable(obj(StrictJson.parse(priority.toJson()))).stream().anyMatch(w -> yes(get(strategicNeed(w), "worth_strategic_reserve")) || yes(get(w, "raised_force_deficit")));
    }
    private static ObjectNode local(PlanningRequest request, Draft previous, OrdinaryWarPriority.Observation priority, ObjectNode focus) {
        ObjectNode missing = objectNode().put("status", "unavailable").put("reason", "no_valid_current_target_contact_query");
        missing.putArray("allocated_player_army_ids"); missing.putArray("local_hostile_army_ids");
        missing.putNull("player_current_soldiers").putNull("enemy_current_soldiers").putNull("arrival_eta_days").put("company_arrival_verified", false);
        if (!(previous.detail().get("projected_contact_scope") instanceof Obj projection) || focus == null) return missing;
        try {
            BigInteger subject = OpportunityInteger(projection.get("subject_army_id"));
            List<Obj> own = org.xar.ck3.control.planning.opportunity.OpportunityJson.array(request.observations().snapshot().get("player_armies"), "current own armies").stream().filter(v -> v instanceof Obj).map(v -> (Obj)v)
                    .filter(a -> new IntegerValue(subject).equals(a.get("army_id")) && new Bool(true).equals(a.get("controllable"))
                            && new IntegerValue(request.before().frame().identity().player()).equals(a.get("owner_character_id"))).toList();
            if (own.size() != 1) return missing;
            Obj inputRequest = new Obj(java.util.Map.of("subject_army_id", projection.get("subject_army_id"), "target_province_id", projection.get("target_province_id"),
                    "incoming_entry_province_id", projection.get("incoming_entry_province_id"), "subject_current_province_id", own.getFirst().get("current_province_id"),
                    "subject_owner_character_id", new IntegerValue(request.before().frame().identity().player())));
            List<Value> history = request.observations().history().stream().map(row -> (Value)row.with("step",
                    row.get("command") != null ? row.get("command") : row.get("step") != null ? row.get("step") : Nil.INSTANCE)).toList();
            var decoded = ProjectedContactCodec.decode(encode(new Obj(java.util.Map.of("snapshot", request.observations().snapshot(),
                    "query_rows", new Arr(history), "request", inputRequest))));
            var selection = ProjectedContactPolicy.select(decoded.snapshot(), decoded.queryRows(), decoded.request());
            if (!(selection instanceof ProjectedContactPolicy.Available current) || current.projection().transition() == ProjectedContactPolicy.Transition.NONE) return missing;
            var scope = current.projection();
            List<Integer> friendly = scope.subjectSide() == ProjectedContactPolicy.Side.ATTACKER ? scope.attackerArmyIds() : scope.defenderArmyIds();
            List<Integer> hostile = scope.subjectSide() == ProjectedContactPolicy.Side.ATTACKER ? scope.defenderArmyIds() : scope.attackerArmyIds();
            Optional<BigInteger> player = priority.countCurrentMembers(friendly, Optional.empty());
            Optional<BigInteger> enemy = priority.countCurrentMembers(hostile, Optional.of(integer(get(focus, "war_id"))));
            if (player.isEmpty() || enemy.isEmpty()) return missing.put("reason", "target_membership_not_complete_for_selected_war");
            ObjectNode result = objectNode().put("status", "available"); result.set("war_id", get(focus, "war_id")); result.put("target_province_id", scope.targetProvinceId());
            array(result, "allocated_player_army_ids", friendly.stream().map(BigInteger::valueOf).toList());
            array(result, "local_hostile_army_ids", hostile.stream().map(BigInteger::valueOf).toList());
            result.put("player_current_soldiers", player.orElseThrow()).put("enemy_current_soldiers", enemy.orElseThrow());
            result.put("source", "same-frame native ordered projected-contact members; current target state only");
            ObjectNode frame = result.putObject("source_frame"); for (String k : List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id")) frame.set(k, get(node(request.observations().snapshot()),k));
            result.put("company_arrival_verified", false).putNull("arrival_eta_days").put("other_hostile_armies_excluded_from_local_comparison_only", true)
                    .put("future_contact_authorized", false).putNull("battle_win_probability"); return result;
        } catch (IllegalArgumentException | ArithmeticException invalid) { return missing; }
    }
    private static boolean stationary(ObjectNode row, BigInteger province) {
        if (province == null || !exact(get(row,"army_id"))) return false;
        boolean route = yes(get(row,"move_target_observable")) && get(row,"move_target_province_id").isNull()
                || text(get(row,"route_read_status"),"complete_empty") && equal(get(row,"route_source_count"),num(0)) && text(get(row,"army_state"),"regular")
                || text(get(row,"army_state"),"regular") && get(row,"move_target_province_id").isNull() && get(row,"route_province_ids").isArray() && get(row,"route_province_ids").isEmpty();
        return yes(get(row,"controllable")) && equal(get(row,"current_province_id"),num(province)) && route && no(get(row,"in_combat"))
                && no(get(row,"retreating")) && get(row,"route_province_ids").isArray() && get(row,"route_province_ids").isEmpty();
    }
    private static int ratio(ObjectNode a,ObjectNode b,BigInteger numeratorA,BigInteger numeratorB,boolean freeFirst) {
        BigInteger pa=integer(get(a,"gold_cost_raw")),pb=integer(get(b,"gold_cost_raw"));
        if (freeFirst && (pa.signum()==0)!=(pb.signum()==0)) return pa.signum()==0?-1:1;
        int c=numeratorB.multiply(pa.max(BigInteger.ONE)).compareTo(numeratorA.multiply(pb.max(BigInteger.ONE)));
        if(c==0)c=pa.compareTo(pb); if(c==0)c=integer(get(a,"company_id")).compareTo(integer(get(b,"company_id"))); return c;
    }

    private static ObjectNode packageBudget(ObjectNode snapshot,ObjectNode priority,ObjectNode ledger,ObjectNode focus) {
        if (!get(ledger,"pending").isNull()) return unavailable("unresolved_mercenary_commitment");
        Set<BigInteger> connected=new HashSet<>(),purposes=new HashSet<>();
        if(focus!=null)purposes.add(integer(get(focus,"war_id"))); connected.addAll(purposes);
        for(ObjectNode w:rows(get(snapshot,"active_wars")))if(yes(get(w,"player_is_primary_war_leader"))&&exact(get(w,"war_id")))connected.add(integer(get(w,"war_id")));
        for(ObjectNode w:rows(get(priority,"wars")))if(yes(get(get(w,"nonleading_realm_siege_cash_protection_v1"),"qualified_current_scope"))&&exact(get(w,"war_id")))connected.add(integer(get(w,"war_id")));
        record Prior(ObjectNode receipt,ObjectNode selected,Set<BigInteger> scope) { }
        List<Prior> records=new ArrayList<>(); JsonNode actor=get(get(snapshot,"played_character"),"character_id");
        boolean nativeFrame=text(get(snapshot,"source"),"injected-dll-named-pipe")&&positive(get(snapshot,"native_revision"))
                &&text(get(snapshot,"snapshot_id"),"native:"+get(snapshot,"native_revision").asText())&&yes(get(snapshot,"paused"))&&yes(get(snapshot,"map_ready"))
                &&text(get(get(snapshot,"played_character"),"source"),"native")&&yes(get(get(snapshot,"played_character"),"alive"))
                &&yes(get(get(snapshot,"diagnostics"),"connected"))&&positive(get(get(snapshot,"diagnostics"),"bridge_pid"))
                &&nonnegative(get(get(snapshot,"diagnostics"),"connection_generation"))&&get(snapshot,"active_event").isNull()&&get(snapshot,"pending_character_interaction").isNull();
        Set<BigInteger> activeNonleading=new HashSet<>();
        if(nativeFrame)for(ObjectNode w:rows(get(snapshot,"active_wars")))if(text(get(w,"source"),"native")&&text(get(w,"player_side"),"defender")
                &&no(get(w,"player_is_primary_war_leader"))&&positive(get(w,"war_id")))activeNonleading.add(integer(get(w,"war_id")));
        for(ObjectNode receipt:rows(get(ledger,"observed"))) {
            if(!text(get(receipt,"status"),"employment_observed"))continue;
            JsonNode source=get(receipt,"source_frame"); if(!equal(get(source,"episode_run_id"),get(snapshot,"episode_run_id"))||!equal(get(source,"played_character_id"),actor))continue;
            ObjectNode decision=objOrEmpty(get(receipt,"decision")),selected=objOrEmpty(get(decision,"selected_candidate"));
            Set<BigInteger> scope=ids(get(selected,selected.has("purpose_war_ids")?"purpose_war_ids":"numerical_balance_reversed_war_ids"));
            Set<BigInteger> priorPurpose=new HashSet<>(scope); scope.addAll(ids(get(get(get(decision,"war_spending_priority"),"primary_war_hostile_union_v1"),"war_ids")));
            Set<BigInteger> qualified=new HashSet<>();
            for(ObjectNode w:rows(get(get(decision,"war_spending_priority"),"wars"))) {
                JsonNode proof=get(w,"nonleading_realm_siege_cash_protection_v1");
                if(no(get(w,"primary_player_war"))&&text(get(w,"player_side"),"defender")&&exact(get(w,"war_id"))
                        &&yes(get(proof,"qualified_current_scope"))&&yes(get(proof,"procurement_scope_extended"))
                        &&values(get(proof,"reasons")).equals(List.of(com.fasterxml.jackson.databind.node.TextNode.valueOf("qualified_nonleading_defence_stationary_hostile_siege_in_player_realm")))
                        &&values(get(w,"protect_cash_reasons")).stream().anyMatch(v->text(v,"qualified_nonleading_defence_stationary_hostile_siege_in_player_realm")))qualified.add(integer(get(w,"war_id")));
            }
            Set<BigInteger> retained=new HashSet<>(priorPurpose);retained.retainAll(activeNonleading);
            boolean frame=positive(get(source,"native_revision"))&&text(get(source,"snapshot_id"),"native:"+get(source,"native_revision").asText())
                    &&exact(get(source,"date_raw"))&&integer(get(source,"date_raw")).compareTo(integer(get(snapshot,"date_raw")))<=0;
            if(!retained.isEmpty()&&(!frame||!qualified.containsAll(retained)))return unavailable("active_nonleading_prior_contract_scope_unqualified");
            connected.addAll(retained);records.add(new Prior(receipt,selected,scope));
        }
        boolean changed=true;while(changed){changed=false;for(Prior r:records)if(r.scope().stream().anyMatch(connected::contains)&&!connected.containsAll(r.scope())){connected.addAll(r.scope());changed=true;}}
        List<Prior> receipts=records.stream().filter(r->r.scope().stream().anyMatch(connected::contains)).toList();
        if(receipts.isEmpty())return objectNode().put("status","no_prior_package").putNull("remaining_package_gold_raw");
        Set<String> seen=new HashSet<>();
        for(Prior r:receipts){JsonNode id=get(r.receipt(),"action_request_id");if(!id.isTextual()||id.textValue().isEmpty()||!seen.add(id.textValue()))return unavailable("same_purpose_contract_claim_identity_missing_or_duplicated");}
        Prior first=receipts.getFirst();JsonNode finance=get(first.selected(),"finance");
        BigInteger treasury=optionalNonnegative(get(finance,"observed_treasury_raw")),reserve=optionalNonnegative(get(finance,"required_gold_reserve_raw")),
                cap=optionalNonnegative(get(first.selected(),"cash_opportunity_cost_limit_raw"));
        if(treasury==null||reserve==null||cap==null||receipts.stream().anyMatch(r->!nonnegative(get(r.selected(),"gold_cost_raw"))))
            return unavailable("same_purpose_original_package_budget_or_committed_quote_missing");
        BigInteger envelope=cap.min(treasury.subtract(reserve)).max(ZERO),committed=receipts.stream().map(r->integer(get(r.selected(),"gold_cost_raw"))).reduce(ZERO,BigInteger::add);
        List<JsonNode> revisions=new ArrayList<>();
        for(Prior r:receipts){JsonNode revision=WarEmergencyBudget.validSavedRevision(r.selected(),get(r.receipt(),"source_frame"),snapshot);
            if(r.selected().has("emergency_budget_revision_v1")&&revision.isNull())return unavailable("same_package_emergency_revision_binding_unavailable");if(!revision.isNull())revisions.add(revision);}
        JsonNode epoch=revisions.stream().max(Comparator.comparing(r->integer(get(r,"level")))).orElse(null);
        BigInteger effective=epoch==null?envelope:envelope.max(integer(get(epoch,"total_package_limit_raw")));
        ObjectNode out=objectNode().put("status","available");out.set("anchor_action_request_id",get(first.receipt(),"action_request_id"));out.set("anchor_source_frame",get(first.receipt(),"source_frame"));
        array(out,"purpose_war_ids",purposes.stream().sorted().toList());array(out,"shared_active_war_package_scope_ids",connected.stream().sorted().toList());
        out.put("original_treasury_raw",treasury).put("original_required_reserve_raw",reserve).put("original_treasury_share_cap_raw",cap).put("original_package_gold_limit_raw",envelope)
                .put("committed_contract_quote_gold_raw",committed).put("remaining_package_gold_raw",effective.subtract(committed).max(ZERO));
        if(epoch!=null){out.set("emergency_budget_epoch_v1",epoch);out.put("effective_package_gold_limit_raw",effective);}
        var claims=out.putArray("committed_action_request_ids");receipts.forEach(r->claims.add(get(r.receipt(),"action_request_id")));
        out.put("payment_attribution_verified",false).put("future_income_credited_raw",0).put("current_cash_and_military_reserve_must_also_pass",true);return out;
    }
    private static ObjectNode unavailable(String reason){return objectNode().put("status","unavailable").put("reason",reason).putNull("remaining_package_gold_raw");}
    private static BigInteger OpportunityInteger(Value value){return org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(value,"source integer");}
    private static ObjectNode node(Obj value){return (ObjectNode)toNode(value);}
    private static ObjectNode objectNode(){return StrictJson.object();}
    private static ObjectNode obj(JsonNode value){require(value instanceof ObjectNode,"JSON object required");return (ObjectNode)value;}
    private static ObjectNode objOrEmpty(JsonNode value){return value instanceof ObjectNode row?row:objectNode();}
    private static JsonNode get(JsonNode value,String key){return value!=null&&value.isObject()&&value.has(key)?value.get(key):com.fasterxml.jackson.databind.node.NullNode.instance;}
    private static boolean exact(JsonNode value){return value!=null&&value.isIntegralNumber();}
    private static BigInteger integer(JsonNode value){require(exact(value),"exact finance integer required");return value.bigIntegerValue();}
    private static boolean positive(JsonNode value){return exact(value)&&integer(value).signum()>0;}
    private static boolean nonnegative(JsonNode value){return exact(value)&&integer(value).signum()>=0;}
    private static boolean yes(JsonNode value){return value!=null&&value.isBoolean()&&value.booleanValue();}
    private static boolean no(JsonNode value){return value!=null&&value.isBoolean()&&!value.booleanValue();}
    private static boolean text(JsonNode value,String text){return value!=null&&value.isTextual()&&value.textValue().equals(text);}
    private static boolean equal(JsonNode a,JsonNode b){return a!=null&&b!=null&&a.getNodeType()==b.getNodeType()&&a.equals(b);}
    private static BigInteger optionalInteger(JsonNode value){return exact(value)?integer(value):null;}
    private static BigInteger optionalNonnegative(JsonNode value){return nonnegative(value)?integer(value):null;}
    private static BigInteger numberOr(JsonNode value,String key,BigInteger fallback){return exact(get(value,key))?integer(get(value,key)):fallback;}
    private static List<JsonNode> values(JsonNode value){List<JsonNode> out=new ArrayList<>();if(value!=null&&value.isArray())value.forEach(out::add);return out;}
    private static List<ObjectNode> rows(JsonNode value){return values(value).stream().filter(JsonNode::isObject).map(v->(ObjectNode)v).toList();}
    private static Set<BigInteger> ids(JsonNode value){Set<BigInteger> ids=new HashSet<>();values(value).stream().filter(OrdinaryMercenaryChoice::exact).map(OrdinaryMercenaryChoice::integer).forEach(ids::add);return ids;}
    private static JsonNode num(long value){return com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(BigInteger.valueOf(value));}
    private static JsonNode num(BigInteger value){return com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(value);}
    private static void nullable(ObjectNode out,String key,BigInteger value){if(value==null)out.putNull(key);else out.put(key,value);}
    private static void array(ObjectNode out,String key,List<BigInteger> values){var a=out.putArray(key);values.forEach(a::add);}
    private static void strings(ObjectNode out,String key,List<String> values){var a=out.putArray(key);values.forEach(a::add);}
    private static byte[] wire(Obj value){return encode(value);}
    private static byte[] wire(ObjectNode value){
        byte[] raw=DriverJson.encodeNode(value);
        require(raw.length<=OUTPUT_MAX_BYTES,"chooser output exceeds 4 MiB");
        return raw;
    }
}

