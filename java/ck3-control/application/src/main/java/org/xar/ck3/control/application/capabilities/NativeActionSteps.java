package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.application.capabilities.CapabilityJson.*;
import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

/**
 * Exact snapshot expansion of native_driver._action_steps. This is a candidate
 * projection, never installation or dispatch authority. DynamicCapabilities
 * performs the separate exact installed-operation intersection.
 */
public final class NativeActionSteps {
    public static final String PREFIX = "game.command.";
    public static final String MOVE = PREFIX + "move-army-N-to-N";
    public static final String PREVIEW = PREFIX + "preview-move-army-N-to-N";
    public static final String HORIZON = PREFIX + "query-route-contact-horizon-v1-N";
    public static final String OCCUPATION = PREFIX + "query-war-occupation-targets-v1-N";
    public static final String ASSAULT_STATE = "game.state.war-objective-assault";
    private static final Set<String> PAUSED_WINDOWS = Set.of("query-war-declared-overview-v1","close-war-declared-overview-v1","query-war-results-window-v1","close-war-results-window-v1");
    private static final Set<String> PENDING = Set.of("accept-pending-character-interaction","reject-pending-character-interaction","acknowledge-pending-character-interaction");
    private static final Set<String> PAUSED_FIXED = Set.of("query-army-strengths-v1","query-campaign-root-context-v1","query-steward-develop-county-candidates-v1","query-player-faction-alerts-v1","query-loaded-feature-manifest-v1");
    private static final Set<String> EXPLICIT_ONLY = Set.of(
            "initiate-character-interaction-ordinary-v1","hire-mercenary-v1","hire-holy-order-v1",
            "assign-army-commander-v1-army-N-to-character-N","center-map-on-landed-title-v1","set-played-character-v1-N","probe-coat-of-arms-source-v1",
            "query-projected-contact-scope-v1-N","query-battle-transition-v1-N","query-battle-terminal-transition-v1",
            "query-zhongguo-case-snapshot-v1","query-zhongguo-ai-owned-case-snapshot-v1","query-zhongguo-result-case-snapshot-v1",
            "query-zhongguo-b2-pip-snapshot-v1","query-zhongguo-promotion-compensation-postcondition-v1","query-zhongguo-compensation-af5-snapshot-v1",
            "query-zhongguo-workforce-owner-snapshot-v1","query-zhongguo-workforce-collective-snapshot-v1","query-zhongguo-workforce-normal-exit-snapshot-v1",
            "query-zhongguo-incident-snapshot-v1","query-zhongguo-scoreboard-state-v1",
            "query-combat-simulation-inputs-v2-N","query-combat-simulation-inputs-v3-N","query-combat-phase-event-trace-v1-N",
            "query-war-entry-assessments-v1-N","query-province-local-siege-v1-N","query-war-occupation-targets-v1-N",
            "query-title-own-laws-v1-ID","query-player-claims-v1-IDS","query-title-holder-v1-N",
            "query-defender-de-jure-exit-terms-v1-N","query-raiktor-actual-truce-expiry-v1-N","query-raiktor-war-bound-loss-cleanup-v1-N",
            "surrender-war-N","offer-white-peace-N");
    private static final List<String> EXPLICIT_PREFIXES = List.of(
            "query-title-own-laws-v1-","query-player-claims-v1-","query-combat-simulation-inputs-v2-","query-combat-simulation-inputs-v3-",
            "query-battle-control-snapshot-v1-","query-battle-transition-v1-","query-battle-terminal-transition-v1-","query-battle-reinforcement-assignment-v1-",
            "query-campaign-root-context-v1","query-council-composition-candidates-v1","query-steward-develop-county-candidates-v1",
            "query-zhongguo-case-snapshot-v1","query-loaded-feature-manifest-v1","query-pending-character-interaction-context-v1",
            "query-war-termination-options-","query-war-prisoner-release-pairs-v1-","query-outbound-war-white-peace-status-v1-",
            "query-war-termination-terms-v1-","query-defender-de-jure-exit-terms-v1-","query-raiktor-actual-truce-expiry-v1-",
            "query-war-termination-exit-terms-v2-","surrender-war-","offer-white-peace-");
    private NativeActionSteps() { }

    public record Input(Set<String> bridgeCapabilities, Obj semantic, List<Obj> marriageChoices, Set<Integer> occupationTargets) {
        public Input {
            bridgeCapabilities = Set.copyOf(bridgeCapabilities); java.util.Objects.requireNonNull(semantic);
            marriageChoices = List.copyOf(marriageChoices); occupationTargets = Set.copyOf(occupationTargets);
            for (String capability : bridgeCapabilities) require(capability != null && !capability.isBlank(),"nonempty capability string required");
            for (Integer target : occupationTargets) require(target != null && target > 0,"positive observed occupation target required");
            for (String key : List.of("paused","active_event","pending_character_interaction","active_wars","player_armies")) present(semantic,key);
            bool(semantic.get("paused"),"paused");
            for (String key : List.of("active_event","pending_character_interaction"))
                require(semantic.get(key) == Nil.INSTANCE || semantic.get(key) instanceof Obj,"explicit nullable object required: " + key);
            for (Obj army : requiredRows(semantic,"player_armies")) validateArmy(army);
            for (Obj war : requiredRows(semantic,"active_wars")) {
                validateIntegerIfPresent(war,"war_id"); validateIntegerIfPresent(war,"player_relative_war_score");
                if (war.get("enemy_armies") instanceof Arr) for (Obj army : requiredRows(war,"enemy_armies")) validateArmy(army);
            }
        }
    }

    public static Set<String> candidates(Input input) {
        Set<String> caps = input.bridgeCapabilities(); Obj snapshot = input.semantic(); boolean paused = yes(snapshot,"paused");
        Obj event = obj(snapshot.get("active_event")).orElse(null), pending = obj(snapshot.get("pending_character_interaction")).orElse(null);
        Set<String> steps = new TreeSet<>(), expand = new LinkedHashSet<>(), pendingSteps = new LinkedHashSet<>();
        for (String capability : caps) {
            if ("game.state.native-mandatory-choice-window-v1".equals(capability)) { steps.add("query-mandatory-choice-v1"); steps.add("select-mandatory-choice-v1"); continue; }
            if ("game.query.council-composition-candidates-v1".equals(capability)) { if (paused) steps.add("query-council-composition-candidates-v1"); continue; }
            if ("game.action.assign-councillor-v1".equals(capability)) { if (paused) steps.add("assign-councillor-v1"); continue; }
            if (!capability.startsWith(PREFIX)) continue;
            String step = capability.substring(PREFIX.length());
            if (PAUSED_WINDOWS.contains(step) || PAUSED_FIXED.contains(step)) { if (paused) steps.add(step); continue; }
            if (EXPLICIT_ONLY.contains(step)) continue;
            if (PENDING.contains(step)) { pendingSteps.add(step); continue; }
            switch (step) {
                case "select-event-option-N", "halt-army-N", "move-army-N-to-N", "preview-move-army-N-to-N", "query-route-contact-horizon-v1-N",
                     "query-actual-contact-scope-v1-N", "query-army-commander-candidates-v1-for-army-N", "query-battle-control-snapshot-v1-N",
                     "query-battle-reinforcement-assignment-v1-N", "query-pending-character-interaction-context-v1", "query-current-event-window-context-v1",
                     "disband-army-N", "split-army-half-N", "merge-armies-N-with-N", "start-assault-N", "stop-assault-N", "enforce-demands-N",
                     "query-war-termination-options-N", "query-war-prisoner-release-pairs-v1-N", "query-outbound-war-white-peace-status-v1-N",
                     "query-war-termination-terms-v1-N", "declare-war-N", "arrange-marriage-N", "raise-troops-default" -> expand.add(step);
                default -> {
                    // WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED is false in the original current producer.
                    if (step.startsWith("split-army-half-") || step.startsWith("merge-armies-") || step.startsWith("start-assault-") || step.startsWith("stop-assault-")) continue;
                    if (EXPLICIT_PREFIXES.stream().anyMatch(step::startsWith)) continue;
                    if (!step.isEmpty()) steps.add(step);
                }
            }
        }
        if (expand.contains("select-event-option-N") && event != null && event.get("option_count") instanceof IntegerValue count && count.value().signum() > 0) {
            require(count.value().compareTo(BigInteger.valueOf(65536)) <= 0,"bounded actual displayed option count required");
            for (int i = 1; i <= count.value().intValueExact(); i++) steps.add("select-event-option-" + i);
        }
        if (pending != null && no(pending,"auto_accept_notification")) {
            for (String step : pendingSteps) if (!"acknowledge-pending-character-interaction".equals(step)) steps.add(step);
        } else if (pending != null && paused && yes(pending,"auto_accept_notification") && pendingSteps.contains("acknowledge-pending-character-interaction")) {
            steps.add("acknowledge-pending-character-interaction");
        }
        List<Obj> wars = requiredRows(snapshot,"active_wars"), armies = requiredRows(snapshot,"player_armies");
        List<Obj> controlled = armies.stream().filter(a -> yes(a,"controllable")).toList();
        if (expand.contains("raise-troops-default") && !wars.isEmpty()) steps.add("raise-troops-default");
        for (Obj war : wars) {
            Value warId = war.get("war_id");
            if (expand.contains("enforce-demands-N") && warId instanceof IntegerValue id && id.value().signum() >= 0
                    && (!caps.contains("game.state.war-primary-opponent") || yes(war,"player_is_primary_war_leader")
                    && number(war.get("player_relative_war_score")).filter(v -> v.compareTo(BigInteger.valueOf(100)) >= 0).isPresent())) steps.add("enforce-demands-" + id.value());
            if (paused && int32Id(warId)) {
                for (String prefix : List.of("query-war-termination-options-","query-war-prisoner-release-pairs-v1-","query-war-termination-terms-v1-"))
                    if (expand.contains(prefix + "N")) steps.add(prefix + integer(warId,"war_id"));
                if (yes(war,"player_is_primary_war_leader") && expand.contains("query-outbound-war-white-peace-status-v1-N")) steps.add("query-outbound-war-white-peace-status-v1-" + integer(warId,"war_id"));
            }
        }
        if (paused && pending != null && expand.contains("query-pending-character-interaction-context-v1") && validPendingId(pending.get("instance_id"))) steps.add("query-pending-character-interaction-context-v1");
        if (paused && event != null && expand.contains("query-current-event-window-context-v1") && int32Id(event.get("instance_id"))) steps.add("query-current-event-window-context-v1");
        for (Obj army : controlled) {
            Value id = army.get("army_id");
            if (!(id instanceof IntegerValue nativeId)) continue;
            if (expand.contains("disband-army-N") && nativeId.value().signum() >= 0) steps.add("disband-army-" + nativeId.value());
            if (!unitId(id)) continue;
            if (expand.contains("split-army-half-N")) steps.add("split-army-half-" + nativeId.value());
            if (paused) {
                if (expand.contains("query-actual-contact-scope-v1-N") && int32Id(army.get("current_province_id")) && !retreating(army))
                    steps.add("query-actual-contact-scope-v1-" + nativeId.value() + "-at-" + integerAt(army,"current_province_id"));
                if (expand.contains("query-army-commander-candidates-v1-for-army-N")) steps.add("query-army-commander-candidates-v1-for-army-" + nativeId.value());
                if (expand.contains("query-battle-control-snapshot-v1-N") && combat(army)) steps.add("query-battle-control-snapshot-v1-" + nativeId.value());
                if (expand.contains("halt-army-N") && named(army,"route_read_status","complete_nonempty")
                        && army.get("route_province_ids") instanceof Arr route && !route.items().isEmpty() && !combatOrRetreat(army)) steps.add("halt-army-" + nativeId.value());
            }
        }
        if (paused && expand.contains("query-battle-reinforcement-assignment-v1-N"))
            for (Obj army : armies) if (unitId(army.get("army_id"))) steps.add("query-battle-reinforcement-assignment-v1-" + integerAt(army,"army_id"));
        if (expand.contains("declare-war-N")) for (Obj choice : rows(snapshot.get("declarable_wars"))) addChoice(steps,choice,"declaration_id","declare-war-","[0-9]+-[0-9]+-(-1|[0-9]+)");
        if (expand.contains("arrange-marriage-N")) for (Obj choice : input.marriageChoices()) addChoice(steps,choice,"choice_id","arrange-marriage-","[0-9]+-[0-9]+");
        if (expand.contains("merge-armies-N-with-N")) {
            List<Obj> merge = controlled.stream().filter(a -> unitId(a.get("army_id")) && int32Id(a.get("current_province_id")) && !combatOrRetreat(a)).toList();
            for (Obj destination : merge) for (Obj source : merge)
                if (!eq(destination,"army_id",source.get("army_id")) && eq(destination,"current_province_id",source.get("current_province_id")))
                    steps.add("merge-armies-" + integerAt(destination,"army_id") + "-with-" + integerAt(source,"army_id"));
        }
        if (caps.contains(ASSAULT_STATE)) for (Obj war : wars) addAssaults(steps,rows(war.get("objective_province_states")),expand.contains("start-assault-N") && expand.contains("stop-assault-N"),expand.contains("stop-assault-N"));
        boolean move = expand.contains("move-army-N-to-N"), preview = expand.contains("preview-move-army-N-to-N"), horizon = expand.contains("query-route-contact-horizon-v1-N");
        if ((move || preview || horizon) && !wars.isEmpty()) movement(steps,caps,wars,controlled,input.occupationTargets(),paused,move,preview,horizon);
        return java.util.Collections.unmodifiableSet(steps);
    }

    public static void addAssaults(Set<String> steps, List<Obj> states, boolean start, boolean stop) {
        for (Obj state : states) {
            Obj siege = obj(state.get("active_siege")).orElse(null);
            if (!yes(state,"siege_observable") || siege == null || !yes(siege,"assault_observable") || !positive(siege.get("siege_id")) || !yes(siege,"player_army_besieging")) continue;
            if (start && no(siege,"assault_in_progress") && yes(siege,"can_start_assault")) steps.add("start-assault-" + integerAt(siege,"siege_id"));
            if (stop && yes(siege,"assault_in_progress") && yes(siege,"can_stop_assault")) steps.add("stop-assault-" + integerAt(siege,"siege_id"));
        }
    }
    private static void movement(Set<String> steps,Set<String> caps,List<Obj> wars,List<Obj> controlled,Set<Integer> occupation,
            boolean paused,boolean move,boolean preview,boolean horizon) {
        List<Obj> enemies = enemies(wars);
        // A retained historical occupation row does not grant its native query capability.
        Set<Integer> targets = new TreeSet<>(caps.contains(OCCUPATION) ? occupation : Set.of()), threats = new TreeSet<>(), friendlyRetreatSeeds = new TreeSet<>();
        for (Obj enemy : enemies) addProvince(targets,enemy.get("current_province_id"));
        for (Obj army : controlled) {
            addProvince(targets,army.get("current_province_id")); addProvince(targets,army.get("move_target_province_id"));
            if (army.get("route_province_ids") instanceof Arr route && !route.items().isEmpty()) addProvince(targets,route.items().getLast());
        }
        for (Obj war : wars) {
            if (caps.contains("game.state.war-primary-opponent")) addProvince(targets,war.get("enemy_primary_default_raise_province_id"));
            if (caps.contains("game.state.war-objectives") && war.get("war_objective_province_ids") instanceof Arr objectives) for (Value id : objectives.items()) addProvince(targets,id);
        }
        List<Integer> hostiles = new ArrayList<>();
        for (Obj enemy : enemies) {
            if (retreating(enemy)) continue;
            if (unitId(enemy.get("army_id"))) hostiles.add(integerAt(enemy,"army_id").intValueExact());
            addProvince(threats,enemy.get("current_province_id")); addProvince(threats,enemy.get("move_target_province_id"));
            if (enemy.get("route_province_ids") instanceof Arr route) for (Value id : route.items()) addProvince(threats,id);
        }
        hostiles = hostiles.stream().distinct().sorted().toList(); targets.addAll(threats);
        for (Obj army : controlled) if (int32Id(army.get("current_province_id")) && stationary(army) && !combatOrRetreat(army)) friendlyRetreatSeeds.add(idAt(army,"current_province_id"));
        friendlyRetreatSeeds.removeAll(threats);
        for (Obj army : controlled) {
            if (!unitId(army.get("army_id"))) continue;
            int armyId = integerAt(army,"army_id").intValueExact();
            Integer current = int32Id(army.get("current_province_id")) ? idAt(army,"current_province_id") : null;
            Arr route = army.get("route_province_ids") instanceof Arr a ? a : null;
            if (paused && preview && combat(army) && current != null) for (int target : friendlyRetreatSeeds) if (target != current) steps.add(preview(armyId,target));
            boolean clearRoute = current != null && route != null && !route.items().isEmpty();
            boolean hold = current != null && route != null && route.items().isEmpty() && army.members().containsKey("move_target_province_id")
                    && nil(army,"move_target_province_id") && stationary(army) && !combatOrRetreat(army);
            boolean boundedHostiles = !hostiles.isEmpty() && hostiles.size() <= 64;
            if (horizon && paused && hold && boundedHostiles) steps.add(horizon(armyId,current,hostiles));
            Set<Integer> armyTargets = new TreeSet<>(targets);
            if (clearRoute || horizon && hold && threats.contains(current)) armyTargets.add(current);
            for (int target : armyTargets) {
                boolean same = current != null && current == target, sameClear = same && clearRoute, sameHold = same && hold;
                if (same && !sameClear && !(horizon && sameHold)) continue;
                if (move && !sameClear && !eq(army,"move_target_province_id",new IntegerValue(BigInteger.valueOf(target)))) steps.add(move(armyId,target));
                if (preview && !sameHold) steps.add(preview(armyId,target));
                if (horizon && paused && boundedHostiles) steps.add(horizon(armyId,target,hostiles));
            }
        }
    }
    public static List<Obj> enemies(List<Obj> wars) {
        Map<BigInteger,Obj> unique = new LinkedHashMap<>();
        for (Obj war : wars) for (Obj enemy : rows(war.get("enemy_armies")))
            if (enemy.get("army_id") instanceof IntegerValue id) unique.putIfAbsent(id.value(),enemy);
        return List.copyOf(unique.values());
    }
    public static boolean combat(Obj army) { return yes(army,"in_combat") || "combat".equals(lower(army,"army_state")) || eq(army,"army_state_code",new IntegerValue(BigInteger.TWO)); }
    public static boolean retreating(Obj army) { return yes(army,"retreating") || "retreating".equals(lower(army,"army_state")) || eq(army,"army_state_code",new IntegerValue(BigInteger.valueOf(6))); }
    public static boolean combatOrRetreat(Obj army) { return combat(army) || retreating(army); }
    public static boolean stationary(Obj army) {
        String state = lower(army,"army_state");
        return state != null ? Set.of("regular","sieging").contains(state) : eq(army,"army_state_code",new IntegerValue(BigInteger.ONE)) || eq(army,"army_state_code",new IntegerValue(BigInteger.valueOf(3)));
    }
    public static String move(int army,int target) { return "move-army-" + army + "-to-" + target; }
    public static String preview(int army,int target) { return "preview-move-army-" + army + "-to-" + target; }
    public static String horizon(int army,int target,List<Integer> hostiles) {
        require(army >= 0 && target > 0 && !hostiles.isEmpty() && hostiles.size() <= 64,"bounded factual horizon scope required");
        return "query-route-contact-horizon-v1-" + army + "-to-" + target + "-h-" + hostiles.size() + "-" + String.join("-",hostiles.stream().map(String::valueOf).toList());
    }
    private static void addProvince(Set<Integer> targets,Value raw) { if (int32Id(raw)) targets.add(integer(raw,"province").intValueExact()); }
    private static void addChoice(Set<String> steps,Obj row,String key,String prefix,String pattern) {
        String id = textOrNull(row,key); if (id == null) return; require(id.matches(pattern),"malformed native choice identity: " + key); steps.add(prefix + id);
    }
    private static boolean validPendingId(Value value) {
        return value instanceof IntegerValue i && i.value().compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0
                && i.value().compareTo(INT32_MAX) <= 0 && !BigInteger.valueOf(-1).equals(i.value());
    }
    private static void validateArmy(Obj army) {
        for (String field : List.of("army_id","current_province_id","move_target_province_id","army_state_code")) validateIntegerIfPresent(army,field);
        if (army.get("route_province_ids") instanceof Arr route) for (Value id : route.items()) require(id instanceof IntegerValue,"route identity must be an integer");
    }
    private static void validateIntegerIfPresent(Obj row,String field) {
        if (row.members().containsKey(field) && row.get(field) != Nil.INSTANCE) require(row.get(field) instanceof IntegerValue,"integer field required: " + field);
    }
}
