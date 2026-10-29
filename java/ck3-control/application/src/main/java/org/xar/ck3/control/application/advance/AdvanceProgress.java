package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Original event/terminal/interaction/war/threat/date break conditions. None awards saved-day credit. */
public final class AdvanceProgress {
    private AdvanceProgress() { }
    public enum Boundary { ACTIVE_EVENT, TERMINAL, INTERACTION, MODAL, WAR_PROGRESS, NEW_THREAT, HORIZON }
    public static Optional<Boundary> boundary(AdvanceObservationPort.Frame current, AdvanceObservationPort.Frame starting, AdvancePlan plan) {
        if (plan.dailyWatch().isPresent()) {
            Optional<WarDailyWatch.Boundary> watch = plan.dailyWatch().orElseThrow().boundary(current);
            if (watch.isPresent()) return switch (watch.orElseThrow()) {
                case ACTIVE_EVENT -> Optional.of(Boundary.ACTIVE_EVENT);
                case PENDING_INTERACTION -> Optional.of(Boundary.INTERACTION);
                case EXCLUSIVE_MODAL_OR_UNKNOWN -> Optional.of(Boundary.MODAL);
                default -> Optional.empty(); // The clock rejects these unsafe ownership/unavailable states.
            };
            return current.identity().frame().identity().dateRaw().compareTo(plan.targetDateRaw()) >= 0 ? Optional.of(Boundary.HORIZON) : Optional.empty();
        }
        Obj now = current.semantic(), before = starting.semantic();
        if (newModal(now, starting.identity(), Optional.of(before)).isPresent()) return Optional.of(Boundary.MODAL);
        if (now.get("active_event") instanceof Obj) return Optional.of(Boundary.ACTIVE_EVENT);
        if (now.get("one_life_terminal_reason") instanceof Text) return Optional.of(Boundary.TERMINAL);
        if (!Objects.equals(now.get("pending_character_interaction"), before.get("pending_character_interaction"))) return Optional.of(Boundary.INTERACTION);
        if (!warSignature(now).equals(warSignature(before))) return Optional.of(Boundary.WAR_PROGRESS);
        Set<Threat> threats = new HashSet<>(threats(now)); threats.removeAll(threats(before));
        if (!threats.isEmpty()) return Optional.of(Boundary.NEW_THREAT);
        return current.identity().frame().identity().dateRaw().compareTo(plan.targetDateRaw()) >= 0 ? Optional.of(Boundary.HORIZON) : Optional.empty();
    }
    public static Optional<Obj> newModal(Obj current, ObservationIdentity before, Optional<Obj> original) {
        if (current.get("active_event") instanceof Obj || current.get("pending_character_interaction") instanceof Obj
                || !(current.get("top_exclusive_modal_choice_hint") instanceof Obj hint)
                || !new Text("present").equals(hint.get("status"))
                || !new Text("application_main_pump_observed_modal_receiver").equals(hint.get("source"))
                || !AdvancePolicy.truth(hint, "owner_verified")
                || !new IntegerValue(BigInteger.valueOf(2000)).equals(hint.get("max_observation_age_ms"))
                || !(hint.get("opaque_root_id") instanceof Text root) || root.value().isEmpty()) return Optional.empty();
        if (original.isPresent()) {
            Obj first = original.orElseThrow();
            if (first.get("top_exclusive_modal_choice_hint") instanceof Obj old && new Text("present").equals(old.get("status"))
                    && Objects.equals(old.get("opaque_root_id"), root)) return Optional.empty();
            Obj firstDiag = object(first.get("diagnostics"), "starting diagnostics"), diagnostics = object(current.get("diagnostics"), "current diagnostics");
            for (String key : List.of("bridge_pid", "connection_generation")) if (!Objects.equals(firstDiag.get(key), diagnostics.get(key))) return Optional.empty();
        }
        if (!before.frame().episodeRunId().equals(text(current.get("episode_run_id"), "episode_run_id"))
                || !before.frame().identity().player().equals(integer(object(current.get("played_character"), "played_character").get("character_id"), "character_id"))
                || integer(current.get("revision"), "revision").compareTo(before.frame().revision()) <= 0
                || integer(current.get("date_raw"), "date_raw").compareTo(before.frame().identity().dateRaw()) < 0) return Optional.empty();
        return Optional.of(hint);
    }
    public record Army(BigInteger id, BigInteger province, BigInteger target, String state, BigInteger stateCode, boolean combat, boolean retreat) { }
    public record War(BigInteger id, BigInteger score, List<Army> armies) { public War { armies = List.copyOf(armies); } }
    public record Threat(BigInteger war, BigInteger playerArmy, BigInteger hostile, BigInteger province) { }
    public static List<War> warSignature(Obj frame) {
        List<War> result = new ArrayList<>();
        for (Obj war : AdvancePolicy.wars(frame)) {
            if (!(war.get("war_id") instanceof IntegerValue id) || !(war.get("player_relative_war_score") instanceof IntegerValue score)) continue;
            List<Army> armies = new ArrayList<>();
            for (Obj army : AdvancePolicy.objects(war.get("allied_armies"), "allied_armies")) {
                if (!AdvancePolicy.truth(army, "controllable") || !(army.get("army_id") instanceof IntegerValue armyId)) continue;
                armies.add(new Army(armyId.value(), numeric(army.get("current_province_id")), numeric(army.get("move_target_province_id")),
                        army.get("army_state") instanceof Text state ? state.value() : "", numeric(army.get("army_state_code")),
                        AdvancePolicy.truth(army, "in_combat"), AdvancePolicy.truth(army, "retreating")));
            }
            armies.sort(Comparator.comparing(Army::id).thenComparing(Army::province).thenComparing(Army::target)
                    .thenComparing(Army::state).thenComparing(Army::stateCode).thenComparing(Army::combat).thenComparing(Army::retreat));
            result.add(new War(id.value(), score.value(), armies));
        }
        result.sort(Comparator.comparing(War::id).thenComparing(War::score)); return List.copyOf(result);
    }
    public static Set<Threat> threats(Obj frame) {
        Set<Threat> result = new HashSet<>();
        for (Obj war : AdvancePolicy.wars(frame)) {
            if (!(war.get("war_id") instanceof IntegerValue id)) continue;
            List<Obj> stationary = AdvancePolicy.objects(war.get("allied_armies"), "allied_armies").stream().filter(army -> {
                boolean state = army.get("army_state") instanceof Text text ? Set.of("regular", "sieging").contains(text.value().toLowerCase(java.util.Locale.ROOT))
                        : new IntegerValue(BigInteger.ONE).equals(army.get("army_state_code")) || new IntegerValue(BigInteger.valueOf(3)).equals(army.get("army_state_code"));
                return AdvancePolicy.truth(army, "controllable") && army.get("army_id") instanceof IntegerValue
                        && army.get("current_province_id") instanceof IntegerValue && state
                        && !(army.get("move_target_province_id") instanceof IntegerValue)
                        && !AdvancePolicy.truth(army, "in_combat") && !AdvancePolicy.truth(army, "retreating");
            }).toList();
            for (Obj hostile : AdvancePolicy.objects(war.get("enemy_armies"), "enemy_armies")) {
                if (AdvancePolicy.truth(hostile, "retreating") || hostile.get("army_state") instanceof Text state
                        && state.value().equalsIgnoreCase("retreating") || !(hostile.get("army_id") instanceof IntegerValue hostileId)) continue;
                Set<BigInteger> provinces = new HashSet<>();
                for (String key : List.of("current_province_id", "move_target_province_id")) if (hostile.get(key) instanceof IntegerValue value) provinces.add(value.value());
                if (hostile.get("route_province_ids") instanceof Arr route) route.items().forEach(value -> { if (value instanceof IntegerValue number) provinces.add(number.value()); });
                for (Obj army : stationary) {
                    BigInteger province = integer(army.get("current_province_id"), "province");
                    if (provinces.contains(province)) result.add(new Threat(id.value(), integer(army.get("army_id"), "army_id"), hostileId.value(), province));
                }
            }
        }
        return Set.copyOf(result);
    }
    private static BigInteger numeric(Value value) { return value instanceof IntegerValue number ? number.value() : BigInteger.valueOf(-1); }
}
