package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.planning.OrdinaryHistory;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicCUnitId;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy;

/** The actual original life-advance history consumers, after the latest successful restore. */
public final class AdvanceHistory {
    public static final String IDENTITY_PENDING = "identity_pending";
    public static final String IDENTITY_DIAGNOSTIC = "active_combat_identity_subject_combat_id_invalid";
    private AdvanceHistory() { }
    public record Assault(BigInteger warId, BigInteger provinceId, BigInteger siegeId, int startedHistoryPosition) { }
    public record AssaultFailure(Assault lifecycle, String reason) { }
    public static List<Obj> afterRestore(List<Obj> history) {
        for (int i = history.size() - 1; i >= 0; i--) if (new Text("restore-checkpoint").equals(history.get(i).get("command"))
                && AdvancePolicy.truth(history.get(i), "ok")) return List.copyOf(history.subList(i + 1, history.size()));
        return List.copyOf(history);
    }
    public static List<Assault> openAssaults(List<Obj> completeHistory) {
        List<Obj> history = afterRestore(completeHistory); Map<List<BigInteger>, Assault> opened = new HashMap<>();
        for (int i = 0; i < history.size(); i++) {
            Obj row = history.get(i); if (!OrdinaryHistory.successful(row)) continue;
            Optional<Obj> result = OrdinaryHistory.effectiveCommandResult(row); if (result.isEmpty()) continue;
            Obj value = result.orElseThrow(); Value actionValue = value.get("assault_action") instanceof Obj ? value.get("assault_action") : value.get("war_action");
            if (!(actionValue instanceof Obj action) || !AdvancePolicy.positive(action.get("siege_id")) || !AdvancePolicy.positive(action.get("war_id")) || !AdvancePolicy.positive(action.get("province_id"))) continue;
            BigInteger siege = integer(action.get("siege_id"), "siege_id"), war = integer(action.get("war_id"), "war_id"), province = integer(action.get("province_id"), "province_id");
            List<BigInteger> key = List.of(war, province, siege); String step = OrdinaryHistory.effectiveCommand(row).orElse("");
            if (new Text("assault_started").equals(action.get("status")) && step.equals("start-assault-" + siege)) opened.put(key, new Assault(war, province, siege, i + 1));
            else if (new Text("assault_stopped").equals(action.get("status")) && step.equals("stop-assault-" + siege)) opened.remove(key);
        }
        return opened.values().stream().sorted(Comparator.comparingInt(Assault::startedHistoryPosition).thenComparing(Assault::warId).thenComparing(Assault::provinceId).thenComparing(Assault::siegeId)).toList();
    }
    public static List<AssaultFailure> unobservableAssaults(Obj frame, List<Obj> completeHistory, List<Assault> open) {
        Map<BigInteger, Obj> wars = new HashMap<>();
        AdvancePolicy.wars(frame).forEach(war -> { if (AdvancePolicy.positive(war.get("war_id"))) wars.put(integer(war.get("war_id"), "war_id"), war); });
        List<AssaultFailure> result = new ArrayList<>();
        for (Assault lifecycle : open) {
            Obj war = wars.get(lifecycle.warId()); if (war == null) continue;
            Obj state = siegeStates(frame, war).stream().filter(row -> new IntegerValue(lifecycle.provinceId()).equals(row.get("province_id"))).findFirst().orElse(null);
            String reason;
            if (!AdvancePolicy.truth(frame, "war_objective_assault_supported")) reason = "assault_capability_unavailable_after_start";
            else if (state == null) reason = "objective_row_unavailable_after_start";
            else if (!AdvancePolicy.truth(state, "siege_observable")) reason = "siege_unobservable_after_start";
            else if (state.get("active_siege") == Nil.INSTANCE) continue;
            else if (!(state.get("active_siege") instanceof Obj siege)) reason = "active_siege_unavailable_after_start";
            else if (!new IntegerValue(lifecycle.siegeId()).equals(siege.get("siege_id"))) {
                if (AdvancePolicy.positive(siege.get("siege_id"))) continue;
                reason = "siege_generation_unavailable_after_start";
            } else if (!AdvancePolicy.truth(siege, "assault_observable")) reason = "assault_subdomain_unobservable_after_start";
            else if (AdvancePolicy.falsehood(siege, "assault_in_progress")) continue;
            else if (AdvancePolicy.truth(siege, "assault_in_progress") && AdvancePolicy.truth(siege, "player_army_besieging")) {
                if (!latestAdvanceFailed(completeHistory, lifecycle.startedHistoryPosition())) continue;
                reason = "previous_assault_slice_failed_unknown";
            } else reason = "assault_flag_unavailable_after_start";
            result.add(new AssaultFailure(lifecycle, reason));
        }
        return List.copyOf(result);
    }
    private static boolean latestAdvanceFailed(List<Obj> completeHistory, int after) {
        List<Obj> history = afterRestore(completeHistory);
        for (int i = history.size() - 1; i >= after; i--) {
            Obj row = history.get(i); String step = OrdinaryHistory.effectiveCommand(row).orElse("");
            if (DriverSurvivingHistory.isLifeAdvanceStep(step)) return !OrdinaryHistory.successful(row);
        }
        return false;
    }
    public static boolean unresolvedWarWatch(List<Obj> history) {
        return history.stream().anyMatch(row -> row.get("result") instanceof Obj result
                && (new Text("xar.war-daily-watch-unresolved.v1").equals(result.get("schema")) || new Text(WarDailyWatchUnresolved.SCHEMA).equals(result.get("schema")))
                && AdvancePolicy.truth(result, "never_replay"));
    }
    public static AdvanceReadiness.Facts facts(AdvanceObservationPort.Frame frame, List<Obj> completeHistory,
            Set<OperationKey> actualActionSteps, Set<String> actualBridgeCapabilities, CrownRetryPolicy.State actualCrownState,
            boolean crownQueryEnabled, boolean crownPausedQueryEnabled, ExactRef originalHistoryEvidence) {
        Objects.requireNonNull(actualCrownState, "actual same-source Crown state required; absence is not an empty retry state");
        Obj semantic = enrichHoldingStates(frame.semantic(), completeHistory); List<Assault> open = openAssaults(completeHistory);
        Obj diagnostics = object(semantic.get("diagnostics"), "diagnostics");
        CrownRetryPolicy.Frame crownFrame = new CrownRetryPolicy.Frame(new CrownRetryPolicy.ContextKey(integer(diagnostics.get("bridge_pid"), "bridge_pid"),
                text(semantic.get("episode_run_id"), "episode_run_id")), true, frame.identity().frame().identity().player(), frame.identity().frame().identity().dateRaw());
        int horizon = CrownRetryPolicy.horizonDays(crownFrame, actualCrownState, BigInteger.valueOf(45), crownQueryEnabled, crownPausedQueryEnabled).intValueExact();
        return new AdvanceReadiness.Facts(frame.identity(), actualActionSteps, actualBridgeCapabilities, !open.isEmpty(),
                AdvancePolicy.truth(semantic, "paused") && !unobservableAssaults(semantic, completeHistory, open).isEmpty(),
                unresolvedWarWatch(completeHistory), horizon, originalHistoryEvidence);
    }
    /** Production path: the Crown bound has already consumed the private same-writer publication proof. */
    public static AdvanceReadiness.Facts verifiedFacts(ActionCommand parent, AdvanceObservationPort.Frame frame, List<Obj> completeHistory,
            Set<OperationKey> actualActionSteps, Set<String> actualBridgeCapabilities, int verifiedCrownMaximumDays,
            boolean warDailyWatchEnabled, ExactRef originalHistoryEvidence) {
        Obj semantic = enrichHoldingStates(frame.semantic(),completeHistory); List<Assault> open = openAssaults(completeHistory);
        boolean unresolvedAssault = !unobservableAssaults(semantic,completeHistory,open).isEmpty();
        boolean assault = !open.isEmpty() || unresolvedAssault || AdvancePolicy.assault(semantic);
        boolean exact = parent.operation().value().equals("life-advance-one-day");
        Optional<WarDailyWatch.Context> watch = WarDailyWatch.select(frame,warDailyWatchEnabled,exact,parent.operation().value(),Optional.empty(),
                actualBridgeCapabilities,actualActionSteps,assault);
        boolean readerRate = ReaderUnavailableSpeed.ready(semantic,completeHistory,exact,parent.operation().value(),Optional.empty(),
                actualBridgeCapabilities,actualActionSteps,assault);
        return new AdvanceReadiness.Facts(frame.identity(),actualActionSteps,actualBridgeCapabilities,!open.isEmpty(),
                AdvancePolicy.truth(semantic,"paused") && unresolvedAssault,unresolvedWarWatch(completeHistory),verifiedCrownMaximumDays,
                originalHistoryEvidence,watch,readerRate);
    }
    public static Obj enrichHoldingStates(Obj frame, List<Obj> completeHistory) {
        if (!AdvancePolicy.truth(frame, "paused")) return frame.with("_queried_holding_siege_states", new Arr(List.of()));
        List<Obj> history = afterRestore(completeHistory); List<Value> states = new ArrayList<>(); Set<BigInteger> seen = new HashSet<>();
        Obj played = object(frame.get("played_character"), "played_character"), diagnostic = object(frame.get("diagnostics"), "diagnostics");
        for (int i = history.size() - 1; i >= 0; i--) {
            Obj row = history.get(i); if (!(row.get("command") instanceof Text command) || !command.value().matches("query-war-occupation-targets-v1-[1-9][0-9]*")) continue;
            BigInteger warId = new BigInteger(command.value().substring("query-war-occupation-targets-v1-".length()));
            if (!seen.add(warId) || !OrdinaryHistory.successful(row) || !(row.get("result") instanceof Obj result)
                    || !(result.get("war_occupation_targets_v1") instanceof Obj value)) continue;
            List<Obj> matches = AdvancePolicy.wars(frame).stream().filter(war -> new IntegerValue(warId).equals(war.get("war_id"))).toList();
            if (!AdvancePolicy.truth(played, "alive") || matches.size() != 1 || !(matches.getFirst().get("player_side") instanceof Text side)
                    || !Set.of("attacker", "defender").contains(side.value()) || !AdvancePolicy.truth(value, "available") || !AdvancePolicy.truth(value, "collection_complete")
                    || !Objects.equals(value.get("war_id"), new IntegerValue(warId)) || !Objects.equals(value.get("actor_character_id"), played.get("character_id"))
                    || !Objects.equals(value.get("player_side"), side) || !Objects.equals(value.get("snapshot_revision"), frame.get("native_revision"))
                    || !Objects.equals(value.get("date_raw"), frame.get("date_raw"))) continue;
            boolean same = true;
            for (String key : List.of("snapshot_id", "revision", "native_revision", "episode_run_id")) if (!Objects.equals(result.get("queried_" + key), frame.get(key))) same = false;
            if (!same || !Objects.equals(result.get("queried_connection_generation"), diagnostic.get("connection_generation"))) continue;
            for (Obj holding : AdvancePolicy.objects(value.get("rows"), "occupation rows")) {
                var state = new LinkedHashMap<String, Value>(); state.put("war_id", new IntegerValue(warId));
                for (String key : List.of("province_id", "siege_observable", "active_siege")) { require(holding.members().containsKey(key), "actual holding row missing " + key); state.put(key, holding.get(key)); }
                for (String key : List.of("occupation_observable", "is_occupied", "occupying_character_id", "occupier_side")) state.put(key, holding.get(key) == null ? Nil.INSTANCE : holding.get(key));
                state.put("observation_source", new Text("war_occupation_query")); states.add(new Obj(state));
            }
        }
        return frame.with("_queried_holding_siege_states", new Arr(states));
    }
    private static List<Obj> siegeStates(Obj frame, Obj war) {
        List<Obj> result = new ArrayList<>(AdvancePolicy.objects(war.get("objective_province_states"), "objective states")); Set<Value> observed = new HashSet<>();
        result.stream().filter(state -> AdvancePolicy.truth(state, "siege_observable")).forEach(state -> observed.add(state.get("province_id")));
        for (Obj state : AdvancePolicy.objects(frame.get("_queried_holding_siege_states"), "holding states")) if (Objects.equals(state.get("war_id"), war.get("war_id")) && !observed.contains(state.get("province_id"))) result.add(state);
        return List.copyOf(result);
    }
    public static Optional<BigInteger> materializationSubject(Obj frame) {
        if (!new Text(IDENTITY_PENDING).equals(frame.get("battle_control_snapshot_v1_status"))) return Optional.empty();
        Value subject = frame.get("battle_control_snapshot_v1_subject_army_id");
        BigInteger publicId = new PublicCUnitId(integer(subject, "subject_public_cunit_id")).value();
        require(AdvancePolicy.truth(frame, "paused") && AdvancePolicy.truth(frame, "map_ready")
                && frame.get("active_event") == Nil.INSTANCE && frame.get("pending_character_interaction") == Nil.INSTANCE
                && new Text(IDENTITY_DIAGNOSTIC).equals(frame.get("battle_control_snapshot_v1_diagnostic_reason"))
                && new Text("state_changed").equals(frame.get("battle_control_snapshot_v1_native_query_status"))
                && new IntegerValue(BigInteger.valueOf(3)).equals(frame.get("battle_control_snapshot_v1_query_attempts"))
                && frame.get("battle_control_snapshot_v1") == Nil.INSTANCE, "battle identity materialization lacks the exact frozen public-combat binding");
        for (String key : List.of("snapshot_id", "revision", "native_revision")) require(Objects.equals(frame.get("battle_control_snapshot_v1_queried_" + key), frame.get(key)), "battle materialization query frame differs");
        require(AdvancePolicy.players(frame).stream().anyMatch(army -> Objects.equals(army.get("army_id"), subject)
                && AdvancePolicy.truth(army, "controllable") && AdvancePolicy.truth(army, "in_combat")), "battle materialization subject is not actual controlled combat");
        return Optional.of(publicId);
    }
    public static boolean materializationConsumed(Obj frame, List<Obj> completeHistory, BigInteger subject) {
        new PublicCUnitId(subject);
        for (Obj row : afterRestore(completeHistory)) {
            if (!OrdinaryHistory.successful(row) || !OrdinaryHistory.effectiveCommand(row).orElse("").equals("life-advance")) continue;
            Optional<Obj> effective = OrdinaryHistory.effectiveCommandResult(row);
            if (effective.isEmpty() || !(effective.orElseThrow().get("battle_identity_materialization") instanceof Obj value)) continue;
            Obj result = effective.orElseThrow();
            if (!new Bool(true).equals(result.get("paused")) || !new IntegerValue(BigInteger.ONE).equals(result.get("timeline_speed"))
                    || !new Text("exact_one_day_battle_identity_materialization").equals(result.get("timeline_policy"))) continue;
            if (!new IntegerValue(BigInteger.ONE).equals(value.get("schema_version")) || !new Text("one_day_advanced").equals(value.get("status"))
                    || !new Text("battle_identity_materialization").equals(value.get("proof_kind")) || !new Text(IDENTITY_DIAGNOSTIC).equals(value.get("diagnostic_reason"))
                    || !new IntegerValue(subject).equals(value.get("subject_public_cunit_id")) || !new Text("full_combat_id").equals(value.get("next_revision_requirement"))) continue;
            boolean matches = true;
            for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw")) if (!Objects.equals(value.get("ending_" + key), frame.get(key))) matches = false;
            if (matches && value.get("starting_date_raw") instanceof IntegerValue start && value.get("ending_date_raw") instanceof IntegerValue end
                    && end.value().equals(start.value().add(AdvancePlan.DAY)) && new IntegerValue(BigInteger.ONE).equals(value.get("elapsed_days"))
                    && value.get("starting_revision") instanceof IntegerValue sr && value.get("ending_revision") instanceof IntegerValue er && er.value().compareTo(sr.value()) > 0
                    && value.get("starting_native_revision") instanceof IntegerValue sn && value.get("ending_native_revision") instanceof IntegerValue en
                    && sn.value().signum() > 0 && en.value().compareTo(sn.value()) > 0) return true;
        }
        return false;
    }
}
