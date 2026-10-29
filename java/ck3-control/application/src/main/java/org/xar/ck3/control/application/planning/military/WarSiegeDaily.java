package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/**
 * Complete original exact-siege/one-day-assault reducers and both ordinary
 * daily boundaries. Results are observations and selections, never native ACKs.
 * The shared EarlyWarCoreInputs producer owns current source/frame custody.
 */
public final class WarSiegeDaily {
    private WarSiegeDaily() { }
    private static final BigInteger DAY = BigInteger.valueOf(24);
    private static final BigInteger STALL_DAYS = BigInteger.valueOf(7);
    private static final BigInteger UNIT_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final String POLICY = "one-life-turn-v1";

    public static List<WarCorePlanner.Leaf> factories(ExactRef source, EarlyWarCoreInputs.Collector collector) {
        Objects.requireNonNull(source); Objects.requireNonNull(collector);
        return List.of(new WarCorePlanner.Leaf(WarCorePlanner.Boundary.ASSAULT_STABILITY, source,
                        (request, previous) -> evaluate(request, previous, collector, true)),
                new WarCorePlanner.Leaf(WarCorePlanner.Boundary.ASSAULT_AND_ARMY_STATE, source,
                        (request, previous) -> evaluate(request, previous, collector, false)));
    }

    private static MilitaryPlanningDecision evaluate(PlanningRequest request, OrdinaryPolicy.Draft previous,
            EarlyWarCoreInputs.Collector collector, boolean stability) {
        EarlyWarCoreInputs.Capture captured = collector.capture(request, previous);
        if (captured instanceof EarlyWarCoreInputs.Unavailable missing)
            return new MilitaryPlanningDecision.Unavailable(missing.missing(), "exact siege daily input chain unavailable");
        var actual = ((EarlyWarCoreInputs.Available) captured).state();
        actual.requireSame(request);
        return stability ? stability(request, actual) : armyState(request, actual);
    }

    /** strategy10765..10831: this review precedes every potential time advance. */
    public static MilitaryPlanningDecision stability(PlanningRequest request, EarlyWarCoreInputs.Actual actual) {
        actual.requireSame(request);
        List<Obj> unavailable = actual.assaultReviews().stream().filter(row -> is(row, "status", "unavailable")).toList();
        if (!unavailable.isEmpty()) return hold(actual, "native_war_assault_observation_blocked",
                "observable-exact-assault-state",
                "at least one player siege has an unavailable exact assault subdomain; do not advance a potentially active assault",
                obj(f("assault_states", objects(unavailable))));
        List<Obj> active = active(actual.assaultReviews());
        Optional<Obj> unsafe = active.stream().filter(row -> !yes(row.get("one_day_safe")))
                .min(Comparator.comparingLong(row -> sortId(row.get("siege_id"))));
        if (unsafe.isEmpty()) return new MilitaryPlanningDecision.Keep(annotations(actual));
        Obj selected = unsafe.orElseThrow(); Integer siege = nativeId(selected.get("siege_id"));
        String step = siege != null && siege > 0 ? "stop-assault-" + siege : null;
        Obj details = obj(f("assault_state", selected), f("assault_states", objects(active)));
        if (step != null && yes(selected.get("can_stop_assault")) && advertised(request, step))
            return select(actual, "native_war_assault_stop", step,
                    "an active exact assault failed its daily progress, casualty, or threat review; stop it before any time advance", details);
        return hold(actual, "native_war_assault_stop_blocked", step == null ? "exact-stop-assault" : step,
                "an active assault failed its one-day safety review but no exact Stop Assault action is eligible", details);
    }

    /** strategy11369..11393 and11560..11757, after the actual merge/route fences. */
    public static MilitaryPlanningDecision armyState(PlanningRequest request, EarlyWarCoreInputs.Actual actual) {
        actual.requireSame(request);
        List<Obj> active = active(actual.assaultReviews());
        if (!active.isEmpty() && actual.unsafeArmyIds().isEmpty() && actual.threatenedStationaryArmyIds().isEmpty()) {
            Obj details = obj(f("assault_state", active.getFirst()), f("assault_states", objects(active)));
            return advance(request, actual, "native_war_assault_daily_progress",
                    "every active exact assault and every controlled route passed the current one-day review; advance exactly one day and re-observe all armies",
                    "active assaults may only advance through one-day paused-to-paused slices", details);
        }
        Army subject = actual.subject(); String state = subject.tacticalState();
        if ("gathering".equals(state)) return advance(request, actual, "native_war_gathering_progress",
                "the raised army is still gathering; advance before previewing or issuing movement",
                "the raised army must finish gathering before route preview", empty());
        Optional<Obj> exactAssault = actual.exactAssault();
        if (exactAssault.isPresent()) {
            Obj assault = exactAssault.orElseThrow(); Integer siege = nativeId(assault.get("siege_id"));
            Obj details = obj(f("assault_state", assault));
            if (is(assault, "status", "unavailable")) return hold(actual, "native_war_assault_observation_blocked",
                    "observable-exact-assault-state",
                    "the exact adapter advertises assault state but the current SiegeID is not atomically observable; do not advance an unknown potentially active assault", details);
            if (is(assault, "status", "active") && siege != null) {
                if (yes(assault.get("one_day_safe"))) return advance(request, actual, "native_war_assault_daily_progress",
                        "the same exact SiegeID remains assaulting and its current one-day progress, casualties, and enemy convergence projection are safe; advance exactly one day and re-observe",
                        "an active assault may only advance through one-day paused-to-paused slices", details);
                String stop = siege > 0 ? "stop-assault-" + siege : "exact-stop-assault";
                if (siege > 0 && yes(assault.get("can_stop_assault")) && advertised(request, stop))
                    return select(actual, "native_war_assault_stop", stop,
                            "the next assault day no longer satisfies the exact progress, casualty, or threat budget; stop it before advancing time", details);
                return hold(actual, "native_war_assault_stop_blocked", stop,
                        "the active assault failed its one-day safety review but no exact Stop Assault action is currently eligible", details);
            }
            if (is(assault, "status", "inactive") && siege != null && siege > 0
                    && yes(assault.get("walls_breached")) && yes(assault.get("can_start_assault"))
                    && yes(assault.get("one_day_safe")) && actual.startBlockingRouteArmyIds().isEmpty()
                    && actual.unsafeArmyIds().isEmpty()) {
                String start = "start-assault-" + siege;
                if (advertised(request, start)) return select(actual, "native_war_assault_start", start,
                        "the walls are breached, CK3's exact validator accepts Start Assault, and the projected next day stays inside the progress, casualty, and threat budget", details);
            }
        }
        boolean arrivedRelief = is(actual.siegeRelief(), "status", "arrived_sieging");
        boolean objective = subject.current() != null && actual.siegeObjectives().contains(subject.current());
        if (actual.exactSiege().filter(row -> is(row, "status", "progressing")).isPresent()
                && subject.target() == null && actual.stationaryThreats().isEmpty()
                && (objective || arrivedRelief) && advertised(request, "life-advance")) {
            Obj details = obj(f("siege_state", actual.exactSiege().orElseThrow()));
            if (arrivedRelief && nativeId(actual.siegeRelief().get("target_province_id")) != null)
                details = put(details, "siege_relief", actual.siegeRelief());
            return select(actual, "native_war_siege_progress", "life-advance",
                    "the exact paused state confirms a player siege; advance one observed day and read the siege again", details);
        }
        if ("sieging".equals(state) && subject.target() == null && actual.stationaryThreats().isEmpty()
                && actual.exactSiege().isEmpty()
                && (objective || arrivedRelief || actual.siegeObjectives().isEmpty() && !actual.exactOccupationFullyObservable())
                && advertised(request, "life-advance")) {
            Obj details = arrivedRelief && nativeId(actual.siegeRelief().get("target_province_id")) != null
                    ? obj(f("siege_relief", actual.siegeRelief())) : empty();
            return select(actual, "native_war_siege_progress", "life-advance", "the native army is sieging; advance the occupation", details);
        }
        if ("retreating".equals(state)) {
            BigInteger days = integer(actual.tactical().get("retreat_days"));
            if (days == null) days = BigInteger.ZERO;
            if (advertised(request, "life-advance")) return select(actual,
                    days.compareTo(BigInteger.valueOf(30)) < 0 ? "native_war_retreat_progress" : "native_war_recovery_wait",
                    "life-advance", days.compareTo(BigInteger.valueOf(30)) < 0
                            ? "the native army is retreating; wait within the 30-day deadline"
                            : "the retreat exceeded its normal deadline; keep advancing bounded intervals until CK3 releases the army",
                    obj(f("retreat_days", number(days))));
            return hold(actual, "native_war_no_safe_target", "query-safe-war-objectives",
                    "the native retreat exceeded its bounded deadline", empty());
        }
        if ("combat".equals(state)) {
            Obj details = obj(f("battle_control_frames", arrayDefault(actual.battleControl(), "evidence")),
                    f("battle_transitions", arrayDefault(actual.battleControl(), "transitions")));
            return advance(request, actual, "native_war_battle_control_progress",
                    "the active subject has an available exact battle-control frame bound to this paused revision; advance at most one day, then query and verify the same CombatID again",
                    "the exact battle-control frame is current, but this backend cannot advance its required bounded time slice", details);
        }
        return new MilitaryPlanningDecision.Keep(annotations(actual));
    }

    public static Optional<Obj> siege(PlanningRequest request, Integer war, Integer province,
            Map<Integer, Obj> states, Optional<Army> subject) {
        return siege(request.observations().snapshot(), request.observations().history(), war, province, states, subject);
    }
    public static Optional<Obj> siege(Obj snapshot, List<Obj> history, Integer war, Integer province,
            Map<Integer, Obj> states, Optional<Army> subject) {
        Objects.requireNonNull(snapshot); Objects.requireNonNull(history); Objects.requireNonNull(states); Objects.requireNonNull(subject);
        if (province == null || !yes(snapshot.get("war_objective_siege_progress_supported"))) return Optional.empty();
        Obj state = states.get(province);
        if (state == null || !yes(state.get("siege_observable"))) return Optional.empty();
        if (!(state.get("active_siege") instanceof Obj siege))
            return Optional.of(obj(f("status", text("not_active")), f("province_id", number(province))));
        Integer siegeId = nativeId(siege.get("siege_id"));
        Obj result = obj(f("status", text("progressing")), f("province_id", number(province)),
                f("siege_id", json(siegeId)), f("besieging_army_id", value(siege, "besieging_army_id")),
                f("player_army_besieging", value(siege, "player_army_besieging")),
                f("garrison_size", value(state, "garrison_size")), f("besieging_strength", value(state, "besieging_strength")),
                f("progress_fraction", value(siege, "progress_fraction")), f("current_work", value(siege, "current_work")),
                f("total_work", value(siege, "total_work")), f("remaining_work", value(siege, "remaining_work")),
                f("days_left", value(siege, "days_left")), f("current_besieging_army_selection", value(state, "current_besieging_army_selection")));
        if (!yes(siege.get("player_army_besieging"))) {
            Obj contribution = subjectContribution(state, subject);
            result = put(result, "subject_contribution", contribution);
            if (!is(contribution, "status", "eligible"))
                return Optional.of(put(result, "status", text(is(contribution, "status", "excluded")
                        ? "not_player_besieging" : "contribution_unavailable")));
        }
        BigInteger garrison = integer(state.get("garrison_size")), strength = integer(state.get("besieging_strength"));
        if (yes(snapshot.get("war_objective_garrison_supported")) && garrison != null && strength != null && strength.compareTo(garrison) < 0)
            return Optional.of(put(result, "status", text("insufficient_strength")));
        BigInteger stalled = war != null && siegeId != null ? stallDays(history, war, province, siegeId) : BigInteger.ZERO;
        result = put(result, "stall_days", number(stalled));
        if (stalled.compareTo(STALL_DAYS) >= 0) result = put(result, "status", text("stalled"));
        return Optional.of(result);
    }

    /** Shared measured native province qualification; no owner/primary-besieger inference. */
    public static Obj subjectContribution(Obj province, Optional<Army> subject) {
        Obj result = obj(f("status", text("unavailable")), f("current_besieging_army_selection", value(province, "current_besieging_army_selection")),
                f("public_unit_id", Nil.INSTANCE), f("native_carmy_id", Nil.INSTANCE), f("matches_current_selection", Nil.INSTANCE));
        if (subject.isEmpty() || !subject.orElseThrow().controllable())
            return put(result, "reason", text("selected_controllable_subject_unavailable"));
        Army army = subject.orElseThrow(); Obj raw = army.raw();
        result = put(result, "public_unit_id", value(raw, "army_id"));
        if (!Objects.equals(raw.get("current_province_id"), province.get("province_id"))
                || !nullish(raw.get("move_target_province_id")) || !new Arr(List.of()).equals(raw.get("route_province_ids")))
            return put(result, "reason", text("selected_subject_not_arrived_with_empty_route"));
        Obj siege = province.get("active_siege") instanceof Obj row ? row : null;
        if (siege == null || !(siege.get("province_unit_occurrences") instanceof Arr occurrences))
            return put(result, "reason", text("current_province_qualification_unavailable"));
        List<Obj> matches = occurrences.items().stream().filter(Obj.class::isInstance).map(Obj.class::cast)
                .filter(row -> Objects.equals(row.get("public_unit_id"), raw.get("army_id"))).toList();
        if (matches.isEmpty() || matches.stream().anyMatch(row -> !(row.get("eligible") instanceof Bool)))
            return put(result, "reason", text("selected_subject_native_qualification_unavailable"));
        result = put(result, "occurrence_indices", new Arr(matches.stream().map(row -> value(row, "occurrence_index")).toList()));
        result = put(result, "native_carmy_id", value(matches.getFirst(), "native_carmy_id"));
        result = put(result, "status", text(matches.stream().allMatch(row -> yes(row.get("eligible"))) ? "eligible" : "excluded"));
        result = put(result, "reason", text("measured_native_province_qualification"));
        if (province.get("current_besieging_army_selection") instanceof Obj selection && !nullish(selection.get("native_carmy_id")))
            result = put(result, "matches_current_selection", new Bool(Objects.equals(selection.get("native_carmy_id"), result.get("native_carmy_id"))));
        return result;
    }

    public static Optional<Obj> assault(PlanningRequest request, Integer war, Integer province,
            Map<Integer, Obj> states, List<Obj> threats, Optional<Obj> exactSiege) {
        return assault(request.observations().snapshot(), request.observations().history(), war, province, states, threats, exactSiege);
    }
    public static Optional<Obj> assault(Obj snapshot, List<Obj> history, Integer war, Integer province,
            Map<Integer, Obj> states, List<Obj> threats, Optional<Obj> exactSiege) {
        Objects.requireNonNull(snapshot); Objects.requireNonNull(history); Objects.requireNonNull(states);
        threats = List.copyOf(threats); Objects.requireNonNull(exactSiege);
        if (province == null || !yes(snapshot.get("war_objective_assault_supported"))) return Optional.empty();
        Obj state = states.get(province);
        if (state == null || !yes(state.get("siege_observable")) || !(state.get("active_siege") instanceof Obj siege)) return Optional.empty();
        Integer siegeId = nativeId(siege.get("siege_id"));
        Obj base = obj(f("province_id", number(province)), f("siege_id", json(siegeId)),
                f("assault_observable", new Bool(yes(siege.get("assault_observable")))));
        if (!yes(siege.get("assault_observable"))) return Optional.of(merge(base, obj(f("status", text("unavailable")),
                f("one_day_safe", new Bool(false)), f("one_day_rejection_reasons", strings(List.of("assault_subdomain_unobservable"))))));
        BigInteger breach = integer(siege.get("breach_level")), progress = raw(siege.get("assault_daily_progress"));
        boolean breached = BigInteger.ONE.equals(breach) || BigInteger.TWO.equals(breach);
        boolean inProgress = yes(siege.get("assault_in_progress"));
        BigInteger casualties = integer(siege.get("assault_daily_casualties"));
        BigInteger strength = integer(state.get("besieging_strength")), garrison = integer(state.get("garrison_size"));
        BigInteger projected = strength != null && casualties != null ? strength.subtract(casualties) : null;
        Optional<Obj> previous = war != null && siegeId != null ? previousDay(history, war, province, siegeId) : Optional.empty();
        List<String> rejected = new ArrayList<>();
        if (siegeId == null) rejected.add("siege_id_unavailable");
        if (!yes(siege.get("player_army_besieging"))) rejected.add("player_not_primary_besieger");
        if (!breached) rejected.add("walls_not_breached");
        if (progress == null || progress.signum() <= 0) rejected.add("daily_progress_not_positive");
        if (casualties == null) rejected.add("daily_casualties_unavailable");
        if (strength == null || garrison == null) rejected.add("one_day_strength_budget_unavailable");
        else if (projected == null || projected.signum() <= 0 || projected.compareTo(garrison) < 0) rejected.add("projected_strength_below_garrison");
        if (!threats.isEmpty()) rejected.add("enemy_convergence_observed");
        if (exactSiege.isPresent() && !is(exactSiege.orElseThrow(), "status", "progressing")) {
            Value status = exactSiege.orElseThrow().get("status");
            rejected.add("siege_" + (status instanceof Text name && !name.value().isEmpty() ? name.value() : "unavailable"));
        }
        if (previous.isPresent()) {
            Obj day = previous.orElseThrow();
            if (is(day, "status", "unknown") && day.get("reason") instanceof Text reason) rejected.add(reason.value());
            if (!BigInteger.ONE.equals(integer(day.get("elapsed_days")))) rejected.add("previous_assault_slice_not_one_day");
            BigInteger delta = integer(day.get("work_delta_raw"));
            if (delta == null || delta.signum() <= 0) rejected.add("previous_assault_day_no_work_progress");
            if (nullish(day.get("strength_loss"))) rejected.add("previous_assault_day_strength_change_unavailable");
        }
        return Optional.of(merge(base, obj(f("status", text(inProgress ? "active" : "inactive")),
                f("breach_level", json(breach)), f("walls_breached", new Bool(breached)), f("assault_in_progress", new Bool(inProgress)),
                f("can_start_assault", new Bool(yes(siege.get("can_start_assault")))), f("can_stop_assault", new Bool(yes(siege.get("can_stop_assault")))),
                f("assault_daily_progress", value(siege, "assault_daily_progress")), f("assault_daily_casualties", json(casualties)),
                f("besieging_strength", json(strength)), f("garrison_size", json(garrison)), f("projected_strength_after_one_day", json(projected)),
                f("threats", objects(threats)), f("one_day_safe", new Bool(rejected.isEmpty())), f("one_day_rejection_reasons", strings(rejected)),
                f("projection_horizon_days", number(1)), f("previous_assault_day", previous.<Value>map(row -> row).orElse(Nil.INSTANCE)))));
    }

    public static List<Obj> reviews(PlanningRequest request, List<Army> enemies) {
        return reviews(request.observations().snapshot(), request.observations().history(), wars(request), enemies);
    }
    public static List<Obj> reviews(Obj snapshot, List<Obj> history, List<Obj> activeWars, List<Army> enemies) {
        if (!yes(snapshot.get("war_objective_assault_supported"))) return List.of();
        List<Obj> reviews = new ArrayList<>();
        for (Obj war : activeWars) {
            Integer warId = nativeId(war.get("war_id")); if (warId == null) continue;
            Map<Integer, Obj> states = AssaultLifecycle.states(war);
            for (var entry : states.entrySet()) {
                Obj state = entry.getValue(); int province = entry.getKey();
                if (!yes(state.get("siege_observable")) || !(state.get("active_siege") instanceof Obj current)
                        || !yes(current.get("player_army_besieging"))) continue;
                Optional<Obj> siege = siege(snapshot, history, warId, province, states, Optional.empty());
                assault(snapshot, history, warId, province, states, WarContactObservation.stationaryThreats(province, enemies), siege)
                        .ifPresent(row -> reviews.add(put(row, "war_id", number(warId))));
            }
        }
        return reviews.stream().sorted(Comparator.comparingLong((Obj row) -> sortId(row.get("siege_id")))
                .thenComparingLong(row -> sortId(row.get("province_id")))).toList();
    }

    public static Optional<Obj> rejection(Optional<Obj> siege, Army subject, Set<Integer> siegeObjectives) {
        if (subject.current() == null || !siegeObjectives.contains(subject.current()) || siege.isEmpty()) return Optional.empty();
        Obj current = siege.orElseThrow();
        return is(current, "status", "not_player_besieging") || is(current, "status", "insufficient_strength")
                || is(current, "status", "stalled") || is(current, "status", "not_active") && "sieging".equals(subject.tacticalState())
                ? siege : Optional.empty();
    }

    /** strategy20290..20434: the newest failed slice after Start hides older success. */
    public static Optional<Obj> previousDay(List<Obj> history, int war, int province, int siege) {
        List<Obj> scoped = afterRestore(history); BigInteger started = null;
        for (AssaultLifecycle.Open open : AssaultLifecycle.open(history))
            if (open.warId() == war && open.provinceId() == province && open.siegeId() == siege)
                started = BigInteger.valueOf(open.startedIndex());
        for (int index = scoped.size() - 1; index >= 0; index--) {
            Obj row = scoped.get(index); BigInteger rowIndex = integer(row.get("index"));
            if (rowIndex == null) rowIndex = BigInteger.valueOf(index + 1L);
            if (started != null && rowIndex.compareTo(started) <= 0) break;
            if (!WarHistorySteps.isLifeAdvance(command(row))) continue;
            if (!yes(row.get("ok"))) {
                if (started != null) return Optional.of(unknown("previous_assault_slice_failed_unknown"));
                continue;
            }
            Optional<Obj> result = child(row.get("result"));
            var before = WarHistorySteps.progressSlice(result, WarHistorySteps.ProgressPhase.BEFORE, war);
            var after = WarHistorySteps.progressSlice(result, WarHistorySteps.ProgressPhase.AFTER, war);
            Optional<Obj> beforeState = WarHistorySteps.progressObjective(before.war(), province);
            Optional<Obj> beforeSiege = WarHistorySteps.progressActiveSiege(beforeState, siege);
            if (beforeSiege.isEmpty() || !yes(beforeSiege.orElseThrow().get("assault_observable"))
                    || !yes(beforeSiege.orElseThrow().get("assault_in_progress"))) {
                if (started != null) return Optional.of(unknown("previous_assault_slice_state_unavailable"));
                continue;
            }
            Optional<Obj> afterState = WarHistorySteps.progressObjective(after.war(), province);
            Optional<Obj> afterSiege = WarHistorySteps.progressActiveSiege(afterState, siege);
            BigInteger beforeWork = raw(beforeSiege.orElseThrow().get("current_work")), afterWork = afterSiege.map(row2 -> raw(row2.get("current_work"))).orElse(null);
            BigInteger beforeStrength = nonnegative(beforeState.map(row2 -> integer(row2.get("besieging_strength"))).orElse(null));
            BigInteger afterStrength = nonnegative(afterState.map(row2 -> integer(row2.get("besieging_strength"))).orElse(null));
            Integer army = publicUnit(beforeSiege.orElseThrow().get("besieging_army_id"));
            Optional<Obj> beforeArmy = army == null ? Optional.empty() : WarHistorySteps.progressArmy(before.war(), WarHistorySteps.ArmyRole.PLAYER, army);
            Optional<Obj> afterArmy = army == null ? Optional.empty() : WarHistorySteps.progressArmy(after.war(), WarHistorySteps.ArmyRole.PLAYER, army);
            BigInteger beforeSoldiers = beforeArmy.map(row2 -> integer(row2.get("soldiers"))).orElse(null), afterSoldiers = afterArmy.map(row2 -> integer(row2.get("soldiers"))).orElse(null);
            BigInteger elapsed = before.dateRaw().isPresent() && after.dateRaw().isPresent()
                    ? after.dateRaw().orElseThrow().subtract(before.dateRaw().orElseThrow()).divide(DAY).max(BigInteger.ZERO) : null;
            return Optional.of(obj(f("elapsed_days", json(elapsed)), f("work_delta_raw", json(delta(beforeWork, afterWork))),
                    f("strength_loss", json(loss(beforeStrength, afterStrength))), f("starting_besieging_strength", json(beforeStrength)),
                    f("ending_besieging_strength", json(afterStrength)), f("soldier_loss", json(loss(beforeSoldiers, afterSoldiers))),
                    f("starting_soldiers", json(beforeSoldiers)), f("ending_soldiers", json(afterSoldiers))));
        }
        return Optional.empty();
    }

    /** strategy20437..20521: observed combat/route/generation breaks a stall streak. */
    public static BigInteger stallDays(List<Obj> history, int war, int province, int siege) {
        BigInteger days = BigInteger.ZERO;
        for (Obj row : afterRestore(history)) {
            if (!WarHistorySteps.isLifeAdvance(command(row)) || !yes(row.get("ok"))) continue;
            Optional<Obj> result = child(row.get("result"));
            var before = WarHistorySteps.progressSlice(result, WarHistorySteps.ProgressPhase.BEFORE, war);
            var after = WarHistorySteps.progressSlice(result, WarHistorySteps.ProgressPhase.AFTER, war);
            if (before.dateRaw().isEmpty() || after.dateRaw().isEmpty() || after.dateRaw().orElseThrow().compareTo(before.dateRaw().orElseThrow()) < 0
                    || before.war().isEmpty() || after.war().isEmpty()) { days = BigInteger.ZERO; continue; }
            Optional<Obj> beforeSiege = WarHistorySteps.progressActiveSiege(WarHistorySteps.progressObjective(before.war(), province), siege);
            Optional<Obj> afterSiege = WarHistorySteps.progressActiveSiege(WarHistorySteps.progressObjective(after.war(), province), siege);
            if (beforeSiege.isEmpty() || afterSiege.isEmpty()) { days = BigInteger.ZERO; continue; }
            Obj b = beforeSiege.orElseThrow(), a = afterSiege.orElseThrow();
            Integer beforeId = publicUnit(b.get("besieging_army_id")), afterId = publicUnit(a.get("besieging_army_id"));
            Optional<Obj> beforeArmy = beforeId == null ? Optional.empty() : WarHistorySteps.progressArmy(before.war(), WarHistorySteps.ArmyRole.PLAYER, beforeId);
            Optional<Obj> afterArmy = afterId == null ? Optional.empty() : WarHistorySteps.progressArmy(after.war(), WarHistorySteps.ArmyRole.PLAYER, afterId);
            if (beforeId == null || !beforeId.equals(afterId) || beforeArmy.isEmpty() || afterArmy.isEmpty()
                    || !siegingAt(beforeArmy.orElseThrow(), province) || !siegingAt(afterArmy.orElseThrow(), province)) { days = BigInteger.ZERO; continue; }
            BigInteger elapsed = after.dateRaw().orElseThrow().subtract(before.dateRaw().orElseThrow()).divide(DAY).max(BigInteger.ZERO);
            boolean advanced = increased(raw(b.get("current_work")), raw(a.get("current_work")))
                    || increased(raw(b.get("progress_fraction")), raw(a.get("progress_fraction")));
            days = advanced ? BigInteger.ZERO : days.add(elapsed);
        }
        return days;
    }

    private static boolean siegingAt(Obj army, int province) {
        return "sieging".equals(MilitaryPlanInputs.army(army).tacticalState()) && BigInteger.valueOf(province).equals(integer(army.get("current_province_id")));
    }
    private static List<Obj> active(List<Obj> reviews) { return reviews.stream().filter(row -> is(row, "status", "active")).toList(); }
    private static Obj annotations(EarlyWarCoreInputs.Actual actual) {
        return obj(f("assault_states", objects(actual.assaultReviews())),
                f("exact_siege_state", actual.exactSiege().<Value>map(row -> row).orElse(Nil.INSTANCE)),
                f("exact_assault_state", actual.exactAssault().<Value>map(row -> row).orElse(Nil.INSTANCE)));
    }
    private static MilitaryPlanningDecision advance(PlanningRequest request, EarlyWarCoreInputs.Actual actual,
            String phase, String reason, String unsupported, Obj details) {
        return advertised(request, "life-advance") ? select(actual, phase, "life-advance", reason, details)
                : hold(actual, phase + "_unsupported", "life-advance", unsupported, details);
    }
    private static Obj plan(EarlyWarCoreInputs.Actual actual, String phase, String reason, Value selected, Obj details) {
        return merge(merge(annotations(actual), details), obj(f("policy", text(POLICY)), f("phase", text(phase)),
                f("reason", text(reason)), f("selected_step", selected), f("active_wars", objects(actual.warSummaries()))));
    }
    private static MilitaryPlanningDecision select(EarlyWarCoreInputs.Actual actual, String phase, String step, String reason, Obj details) {
        return new MilitaryPlanningDecision.Select(POLICY, phase, reason, new OperationKey(step), empty(),
                "life-advance".equals(step) ? OrdinaryPolicy.Purpose.DATE_ADVANCE : OrdinaryPolicy.Purpose.WORLD_ACTION,
                plan(actual, phase, reason, text(step), details));
    }
    private static MilitaryPlanningDecision hold(EarlyWarCoreInputs.Actual actual, String phase, String required, String reason, Obj details) {
        return new MilitaryPlanningDecision.Hold(POLICY, phase, reason, Optional.of(new OperationKey(required)),
                put(plan(actual, phase, reason, Nil.INSTANCE, details), "required_step", text(required)));
    }
    private static Obj unknown(String reason) {
        Obj result = obj(f("status", text("unknown")), f("reason", text(reason)));
        for (String key : List.of("elapsed_days", "work_delta_raw", "strength_loss", "starting_besieging_strength",
                "ending_besieging_strength", "soldier_loss", "starting_soldiers", "ending_soldiers")) result = put(result, key, Nil.INSTANCE);
        return result;
    }
    private static Optional<Obj> child(Value value) { return value instanceof Obj row ? Optional.of(row) : Optional.empty(); }
    private static Value value(Obj object, String key) { return nullable(object.get(key)); }
    private static Value arrayDefault(Obj object, String key) { return object.members().containsKey(key) ? value(object, key) : new Arr(List.of()); }
    private static boolean is(Obj object, String key, String expected) { return new Text(expected).equals(object.get(key)); }
    private static boolean nullish(Value value) { return value == null || value == Nil.INSTANCE; }
    private static BigInteger integer(Value value) { return value instanceof IntegerValue number ? number.value() : null; }
    private static BigInteger raw(Value value) { return value instanceof Obj object ? integer(object.get("raw")) : null; }
    private static BigInteger nonnegative(BigInteger value) { return value != null && value.signum() < 0 ? null : value; }
    private static Integer nativeId(Value value) {
        BigInteger integer = integer(value);
        return integer != null && integer.compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0 && integer.compareTo(UNIT_MAX) <= 0 ? integer.intValueExact() : null;
    }
    private static Integer publicUnit(Value value) { Integer id = nativeId(value); return id != null && id >= 0 ? id : null; }
    private static Value json(BigInteger value) { return value == null ? Nil.INSTANCE : number(value); }
    private static Value json(Integer value) { return value == null ? Nil.INSTANCE : number(value); }
    private static long sortId(Value value) { Integer id = nativeId(value); return id == null || id == 0 ? 2_147_483_648L : id; }
    private static BigInteger delta(BigInteger before, BigInteger after) { return before == null || after == null ? null : after.subtract(before); }
    private static BigInteger loss(BigInteger before, BigInteger after) { return before == null || after == null ? null : before.subtract(after).max(BigInteger.ZERO); }
    private static boolean increased(BigInteger before, BigInteger after) { return before != null && after != null && after.compareTo(before) > 0; }
}
