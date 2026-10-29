package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.BattleControlTurnState.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;

/** Exact native typed-read failures retain a bounded hands-off watch; they never authorize retreat. */
public final class BattleReaderWatch {
    private BattleReaderWatch() { }
    public static final String SCHEMA = "xar.battle-control-readonly-unavailable.v1";
    private static final Set<String> FRAME_KEYS = Set.of("snapshot_id", "revision", "native_revision", "date_raw", "actor_character_id", "episode_run_id", "bridge_pid", "connection_generation", "paused", "map_ready");
    private record Failure(int position, Obj original, BigInteger date) { }

    public static Optional<Obj> select(Obj snapshot, List<Obj> history) {
        Optional<Obj> frame = frame(snapshot); if (frame.isEmpty()) return Optional.empty();
        for (int subject : rows(snapshot.get("player_armies")).stream().filter(row -> yes(row.get("controllable")) && yes(row.get("in_combat")))
                .map(row -> id(row.get("army_id"))).distinct().sorted().toList()) {
            Optional<Obj> scope = scope(snapshot, subject); if (scope.isEmpty()) continue;
            List<Failure> failures = new ArrayList<>();
            for (int i = 0; i < history.size(); i++) {
                Obj row = history.get(i), original = result(row);
                if (original == null || !named(original, "schema", SCHEMA) || !no(row.get("ok"))) continue;
                try {
                    validateUnavailable(original);
                    if (Objects.equals(original.get("scope_key"), scope.orElseThrow()))
                        failures.add(new Failure(i, original, n(object(original.get("source_frame"), "source_frame"), "date_raw")));
                } catch (IllegalArgumentException invalid) { /* Preserve failed receipt; it is not a validated watch. */ }
            }
            if (failures.isEmpty()) continue;
            Failure last = failures.getLast(); BigInteger now = n(frame.orElseThrow(), "date_raw");
            String queryStep = org.xar.ck3.control.planning.opportunity.OpportunityJson.text(last.original().get("step"), "step");
            if (last.date().compareTo(now) > 0 || !continuous(history, last.position(), last.date(), now, scope.orElseThrow(), queryStep)) continue;
            List<BigInteger> dates = failures.stream().map(Failure::date).distinct().sorted().toList();
            boolean cooldown = dates.size() >= 2 && dates.getLast().subtract(dates.get(dates.size() - 2)).equals(BigInteger.valueOf(24));
            if (cooldown) {
                BigInteger previous = dates.get(dates.size() - 2); Failure prior = failures.stream().filter(failure -> failure.date().equals(previous)).reduce((a, b) -> b).orElseThrow();
                cooldown = continuous(history, prior.position(), previous, now, scope.orElseThrow(), queryStep);
            }
            BigInteger until = dates.getLast().add(BigInteger.valueOf(cooldown ? 30 * 24 : 24)); if (now.compareTo(until) >= 0) continue;
            return Optional.of(obj(f("status", text("reader_unavailable_hands_off")), f("subject_army_id", number(subject)),
                    f("scope_key", scope.orElseThrow()), f("original_failure", last.original()), f("cooldown_active", new Bool(cooldown)),
                    f("next_query_date_raw", number(until)), f("observed_date_raw", number(now)),
                    f("prediction_ready", new Bool(false)), f("retreat_authorized", new Bool(false))));
        }
        return Optional.empty();
    }

    public static Obj validateUnavailable(Obj value) {
        exact(value, Set.of("schema", "step", "accepted", "status", "read_only", "business_submission", "replay_allowed", "backend_id", "battle_control_snapshot", "diagnostic_reason", "prediction_ready", "retreat_authorized", "scope_key", "source_frame", "same_frame_readback", "native_request", "native_command_result"));
        int subject = controlSubject(org.xar.ck3.control.planning.opportunity.OpportunityJson.text(value.get("step"), "step")).orElseThrow(() -> new IllegalArgumentException("invalid original query step"));
        require(named(value, "schema", SCHEMA) && no(value.get("accepted")) && named(value, "status", "unavailable")
                && yes(value.get("read_only")) && no(value.get("business_submission")) && no(value.get("replay_allowed"))
                && named(value, "backend_id", "native-headless") && value.get("battle_control_snapshot") == Nil.INSTANCE
                && named(value, "diagnostic_reason", "native_battle_control_typed_read_failed")
                && no(value.get("prediction_ready")) && no(value.get("retreat_authorized")), "unavailable receipt classification differs");
        Obj frame = object(value.get("source_frame"), "source_frame"), key = object(value.get("scope_key"), "scope_key");
        exact(frame, FRAME_KEYS); require(frame.equals(value.get("same_frame_readback")), "unavailable readback frame differs");
        for (String name : List.of("revision", "native_revision", "date_raw", "actor_character_id", "bridge_pid", "connection_generation")) require(n(frame, name).signum() > 0, "positive failure frame field required: " + name);
        require(named(frame, "snapshot_id", "native:" + n(frame, "native_revision")) && frame.get("episode_run_id") instanceof Text episode && !episode.value().isEmpty()
                && yes(frame.get("paused")) && yes(frame.get("map_ready")), "failure native frame differs");
        exact(key, Set.of("subject_army_id", "province_id", "actor_character_id", "episode_run_id", "bridge_pid", "connection_generation", "active_war_ids", "observed_combat_army_ids"));
        require(equal(key, "subject_army_id", subject) && province(key.get("province_id")) > 0, "failure subject/province differs");
        for (String name : List.of("actor_character_id", "episode_run_id", "bridge_pid", "connection_generation")) require(Objects.equals(key.get(name), frame.get(name)), "failure scope owner differs");
        List<Integer> wars = ids(key.get("active_war_ids")), participants = ids(key.get("observed_combat_army_ids"));
        require(!wars.isEmpty() && wars.stream().allMatch(war -> war > 0) && wars.equals(wars.stream().distinct().sorted().toList())
                && !participants.isEmpty() && participants.equals(participants.stream().distinct().sorted().toList()) && participants.contains(subject), "failure scope roster malformed");
        Obj request = object(value.get("native_request"), "native_request"), response = object(value.get("native_command_result"), "native_command_result");
        exact(request, Set.of("type", "protocol_version", "request_id", "step", "expected_revision"));
        exact(response, Set.of("type", "protocol_version", "request_id", "ok", "error", "typed_query_failure_v1"));
        require(named(request, "type", "execute_step") && equal(request, "protocol_version", 1) && request.get("request_id") instanceof Text rid && !rid.value().isEmpty()
                && Objects.equals(request.get("step"), value.get("step")) && Objects.equals(request.get("expected_revision"), frame.get("native_revision"))
                && named(response, "type", "command_result") && equal(response, "protocol_version", 1) && Objects.equals(request.get("request_id"), response.get("request_id"))
                && no(response.get("ok")) && named(response, "error", "application-main typed query failed or its snapshot changed"), "original native request/result mismatch");
        Obj failure = object(response.get("typed_query_failure_v1"), "typed_query_failure_v1");
        exact(failure, Set.of("executor_enter", "executor_exception", "executor_finish", "executor_typed_result", "final_equal", "final_read", "frame_stable", "query_type", "stage", "typed_result", "wait_completed", "wait_result"));
        Obj exception = object(failure.get("executor_exception"), "executor_exception"); exact(exception, Set.of("code", "image", "rva"));
        require(yes(failure.get("executor_enter")) && equal(exception, "code", 0) && named(exception, "image", "none") && exception.get("rva") == Nil.INSTANCE
                && yes(failure.get("executor_finish")) && no(failure.get("executor_typed_result")) && failure.get("final_equal") == Nil.INSTANCE && failure.get("final_read") == Nil.INSTANCE
                && yes(failure.get("frame_stable")) && named(failure, "query_type", "battle_control") && named(failure, "stage", "typed_result")
                && no(failure.get("typed_result")) && yes(failure.get("wait_completed")) && named(failure, "wait_result", "completed"), "original terminal typed failure differs");
        return value;
    }
    private static Optional<Obj> frame(Obj snapshot) {
        Obj played = child(snapshot, "played_character"), diagnostics = child(snapshot, "diagnostics");
        if (played == null || !yes(played.get("alive")) || diagnostics == null) return Optional.empty();
        try {
            Obj frame = obj(f("snapshot_id", snapshot.get("snapshot_id")), f("revision", snapshot.get("revision")), f("native_revision", snapshot.get("native_revision")),
                    f("date_raw", snapshot.get("date_raw")), f("episode_run_id", snapshot.get("episode_run_id")), f("paused", snapshot.get("paused")), f("map_ready", snapshot.get("map_ready")),
                    f("actor_character_id", played.get("character_id")), f("bridge_pid", diagnostics.get("bridge_pid")), f("connection_generation", diagnostics.get("connection_generation")));
            for (String key : List.of("revision", "native_revision", "date_raw", "actor_character_id", "bridge_pid", "connection_generation")) require(n(frame, key).signum() > 0, "positive frame required");
            require(named(frame, "snapshot_id", "native:" + n(frame, "native_revision")) && frame.get("episode_run_id") instanceof Text episode && !episode.value().isEmpty()
                    && yes(frame.get("paused")) && yes(frame.get("map_ready")) && nullish(snapshot.get("active_event"))
                    && nullish(snapshot.get("pending_character_interaction")) && no(snapshot.get("one_life_terminal")), "watch frame unavailable");
            return Optional.of(frame);
        } catch (IllegalArgumentException | NullPointerException malformed) { return Optional.empty(); }
    }
    private static Optional<Obj> scope(Obj snapshot, int subject) {
        Optional<Obj> frame = frame(snapshot); if (frame.isEmpty()) return Optional.empty();
        try {
            List<Obj> own = rows(snapshot.get("player_armies")).stream().filter(army -> equal(army, "army_id", subject)).toList();
            if (own.size() != 1 || !yes(own.getFirst().get("controllable")) || !yes(own.getFirst().get("in_combat")) || !no(own.getFirst().get("retreating"))
                    || !Objects.equals(own.getFirst().get("owner_character_id"), frame.orElseThrow().get("actor_character_id"))) return Optional.empty();
            int province = province(own.getFirst().get("current_province_id")); List<Obj> wars = rows(snapshot.get("active_wars")); if (wars.isEmpty()) return Optional.empty();
            Set<Integer> warIds = new TreeSet<>(), participants = new TreeSet<>(); participants.add(subject); List<Obj> armies = new ArrayList<>(rows(snapshot.get("player_armies")));
            for (Obj war : wars) { int id = province(war.get("war_id")); require(warIds.add(id), "duplicate WarID"); armies.addAll(rows(war.get("allied_armies"))); armies.addAll(rows(war.get("enemy_armies"))); }
            for (Obj army : armies) if (equal(army, "current_province_id", province) && yes(army.get("in_combat"))) participants.add(id(army.get("army_id")));
            return Optional.of(obj(f("subject_army_id", number(subject)), f("province_id", number(province)),
                    f("actor_character_id", frame.orElseThrow().get("actor_character_id")), f("episode_run_id", frame.orElseThrow().get("episode_run_id")),
                    f("bridge_pid", frame.orElseThrow().get("bridge_pid")), f("connection_generation", frame.orElseThrow().get("connection_generation")),
                    f("active_war_ids", numbers(List.copyOf(warIds))), f("observed_combat_army_ids", numbers(List.copyOf(participants)))));
        } catch (IllegalArgumentException | ArithmeticException malformed) { return Optional.empty(); }
    }
    private static boolean continuous(List<Obj> rows, int failurePosition, BigInteger start, BigInteger end, Obj scope, String queryStep) {
        BigInteger cursor = start;
        for (Obj row : rows.subList(failurePosition + 1, rows.size())) {
            String step = command(row); Obj result = result(row); if (queryStep.equals(step) && yes(row.get("ok"))) return false;
            if (step == null || !step.startsWith("life-advance")) continue;
            if (!yes(row.get("ok")) || !step.equals("life-advance-one-day") || result == null || !Objects.equals(new IntegerValue(cursor), result.get("starting_date_raw"))) return false;
            BigInteger ending = numberOrNull(result.get("ending_date_raw"));
            if (ending == null || !ending.equals(cursor) && !ending.equals(cursor.add(BigInteger.valueOf(24)))
                    || !progress(result.get("war_progress_before"), scope) || !progress(result.get("war_progress_after"), scope)) return false;
            cursor = ending;
        }
        return cursor.equals(end);
    }
    private static boolean progress(Value raw, Obj key) {
        if (!(raw instanceof Obj progress) || !(progress.get("wars") instanceof Arr)) return false;
        try {
            List<Integer> wars = new ArrayList<>(); Set<Integer> participants = new TreeSet<>(); boolean seen = false;
            for (Obj war : rows(progress.get("wars"))) {
                wars.add(province(war.get("war_id")));
                for (String side : List.of("player_armies", "enemy_armies")) for (Obj army : rows(war.get(side))) {
                    boolean atProvince = yes(army.get("in_combat")) && Objects.equals(army.get("current_province_id"), key.get("province_id"));
                    if (Objects.equals(army.get("army_id"), key.get("subject_army_id"))) { seen = atProvince; if (!seen) return false; }
                    if (atProvince) participants.add(id(army.get("army_id")));
                }
            }
            return seen && numbers(wars.stream().sorted().toList()).equals(key.get("active_war_ids")) && numbers(List.copyOf(participants)).equals(key.get("observed_combat_army_ids"));
        } catch (IllegalArgumentException | ArithmeticException invalid) { return false; }
    }
    private static void exact(Obj object, Set<String> keys) { require(object.members().keySet().equals(keys), "exact original failure shape required"); }
    private static boolean nullish(Value value) { return value == null || value == Nil.INSTANCE; }
    private static void require(boolean condition, String reason) { org.xar.ck3.control.contracts.StrictJson.require(condition, reason); }
}
