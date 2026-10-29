package org.xar.ck3.control.application.routecontact;

import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.Objects;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy;

/** Narrow runtime boundary for the original semantic snapshot and exact route query result. */
public final class RouteContactCodec {
    private RouteContactCodec() { }
    private static final Set<String> HORIZON = Set.of("status", "date_raw", "snapshot_revision", "subject_army_id", "target_province_id",
            "hostile_army_ids", "subject_route", "hostile_routes", "horizon_start_date_raw", "horizon_end_date_raw", "one_day_contact_free", "conflicts");
    private static final Set<String> TIMED = Set.of("timeline_observable", "army_id", "current_province_id", "effective_origin_province_id", "route_province_ids", "arrival_date_raws");
    public static Frame frame(AdvanceObservationPort.Frame original) {
        Objects.requireNonNull(original);
        return frame(original.identity(), original.source(), original.sessionId(), original.semantic());
    }
    /** Detached capability decoding shares the actual frame parser without inventing native evidence or a query identity. */
    public static Frame frame(ObservationIdentity identity, G2Source source, String sessionId, Obj value) {
        Objects.requireNonNull(identity); Objects.requireNonNull(source); StrictJson.text(sessionId); Objects.requireNonNull(value);
        StrictJson.require(identity.machineId().equals(source.machineId())
                && identity.frame().snapshotId().equals(text(value.get("snapshot_id"), "snapshot_id"))
                && identity.frame().revision().equals(integer(value.get("revision"), "revision"))
                && identity.frame().identity().nativeRevision().equals(integer(value.get("native_revision"), "native_revision"))
                && identity.frame().identity().dateRaw().equals(integer(value.get("date_raw"), "date_raw"))
                && identity.frame().episodeRunId().equals(text(value.get("episode_run_id"), "episode_run_id"))
                && identity.frame().identity().player().equals(integer(object(value.get("played_character"), "played_character").get("character_id"), "character_id")),
                "detached route semantic frame differs from its original observation identity");
        Obj diagnostics = object(value.get("diagnostics"), "diagnostics");
        Owner owner = new Owner(identity.machineId(), identity.game(), sessionId,
                positive64(diagnostics.get("connection_generation"), "connection_generation"), pid(diagnostics.get("bridge_pid")),
                text(value.get("episode_run_id"), "episode_run_id"), NativeCharacterId.of(integer(value.get("episode_character_id"), "episode_character_id")).value(),
                nonnegative(value.get("local_player_id"), "local_player_id").intValueExact());
        List<Army> own = array(value.get("player_armies"), "player_armies").stream().map(item -> army(object(item, "player_army"))).toList();
        List<Integer> warIds = new ArrayList<>(); LinkedHashMap<Integer, Army> hostile = new LinkedHashMap<>();
        for (Value item : array(value.get("active_wars"), "active_wars")) {
            Obj war = object(item, "war"); warIds.add(positive(war.get("war_id"), "war_id"));
            for (Value row : array(war.get("enemy_armies"), "enemy_armies")) {
                Army parsed = army(object(row, "enemy_army")); Army prior = hostile.putIfAbsent(parsed.armyId(), parsed);
                StrictJson.require(prior == null || prior.equals(parsed), "same hostile ID has conflicting native rows");
            }
        }
        return new Frame(owner, text(value.get("snapshot_id"), "snapshot_id"), nonnegative(value.get("revision"), "revision"),
                positive64(value.get("native_revision"), "native_revision"), integer(value.get("date_raw"), "date_raw").intValueExact(),
                bool(value.get("map_ready"), "map_ready"), bool(value.get("paused"), "paused"), integer(value.get("speed"), "speed").intValueExact(),
                optionalBool(value, "one_life_terminal", false), optionalBool(value, "played_character_alive", true),
                required(value, "active_event"), required(value, "pending_character_interaction"), modal(value), warIds, own, List.copyOf(hostile.values()));
    }
    /** The outer query-source fields are validated separately from the inner native uint64 revision. */
    public static RouteQuery query(String step, boolean ok, Frame queriedFrame, Obj result) {
        RouteContactSteps.Request scope = RouteContactSteps.query(step);
        StrictJson.require(text(result.get("queried_snapshot_id"), "queried_snapshot_id").equals(queriedFrame.snapshotId())
                && integer(result.get("queried_revision"), "queried_revision").equals(queriedFrame.revision())
                && integer(result.get("queried_native_revision"), "queried_native_revision").equals(queriedFrame.nativeRevision())
                && integer(result.get("queried_connection_generation"), "queried_connection_generation").equals(queriedFrame.owner().connectionGeneration())
                && text(result.get("queried_episode_run_id"), "queried_episode_run_id").equals(queriedFrame.owner().episodeRunId()), "outer route query source differs");
        Obj horizon = object(result.get("route_contact_horizon"), "route_contact_horizon"); keys(horizon, HORIZON);
        StrictJson.require(text(horizon.get("status"), "status").equals("available"), "route horizon unavailable");
        int date = integer(horizon.get("date_raw"), "date_raw").intValueExact(); BigInteger revision = positive64(horizon.get("snapshot_revision"), "snapshot_revision");
        List<Integer> ids = ids(horizon.get("hostile_army_ids"));
        int subject = unit(integer(horizon.get("subject_army_id"), "subject_army_id").intValueExact());
        int target = positive(horizon.get("target_province_id"), "target_province_id");
        StrictJson.require(date == queriedFrame.dateRaw() && revision.equals(queriedFrame.nativeRevision()) && subject == scope.subjectId()
                && target == scope.targetId() && ids.equals(scope.hostiles()) && ids.equals(queriedFrame.hostileIds())
                && integer(horizon.get("horizon_start_date_raw"), "horizon_start_date_raw").intValueExact() == date
                && integer(horizon.get("horizon_end_date_raw"), "horizon_end_date_raw").intValueExact() == Math.addExact(date, 24), "inner horizon scope/date differs");
        Obj subjectObject = object(horizon.get("subject_route"), "subject_route"); RouteWindowPolicy.Route subjectRoute = timed(subjectObject, date);
        List<RouteWindowPolicy.Route> hostileRoutes = array(horizon.get("hostile_routes"), "hostile_routes").stream().map(item -> timed(object(item, "hostile_route"), date)).toList();
        List<Integer> hostileOrigins = array(horizon.get("hostile_routes"), "hostile_routes").stream()
                .map(item -> positive(object(item, "hostile_route").get("effective_origin_province_id"), "effective_origin_province_id")).toList();
        StrictJson.require(subjectRoute.provinceIds().isEmpty() ? subjectRoute.currentProvinceId() == target : subjectRoute.provinceIds().getLast() == target, "route misses exact target");
        List<RouteWindowPolicy.Conflict> conflicts = array(horizon.get("conflicts"), "conflicts").stream().map(item -> conflict(object(item, "conflict"))).toList();
        StrictJson.require(bool(horizon.get("one_day_contact_free"), "one_day_contact_free") == conflicts.isEmpty(), "native predicate differs from conflicts");
        return new RouteQuery(step, ok, queriedFrame.owner(), queriedFrame.snapshotId(), queriedFrame.revision(), revision, date, subject, target, ids,
                subjectRoute, hostileRoutes, positive(subjectObject.get("effective_origin_province_id"), "effective_origin_province_id"), hostileOrigins, conflicts);
    }
    private static Army army(Obj value) {
        int current = positive(value.get("current_province_id"), "current_province_id");
        List<Integer> route = array(value.get("route_province_ids"), "route_province_ids").stream().map(item -> positive(item, "route_province_id")).toList();
        if (!route.isEmpty() && route.getFirst() == current) route = route.subList(1, route.size());
        Optional<Integer> target = nullableInteger(required(value, "move_target_province_id"), "move_target_province_id"); target.ifPresent(RouteContactModel::province);
        Optional<String> state = optionalText(value, "army_state"); Optional<Integer> code = value.get("army_state_code") == null || value.get("army_state_code") == Nil.INSTANCE
                ? Optional.empty() : Optional.of(nonnegative(value.get("army_state_code"), "army_state_code").intValueExact());
        boolean combat = optionalBool(value, "in_combat", false) || state.map(item -> item.equalsIgnoreCase("combat")).orElse(false) || code.equals(Optional.of(2));
        boolean retreat = optionalBool(value, "retreating", false) || state.map(item -> item.equalsIgnoreCase("retreating")).orElse(false) || code.equals(Optional.of(6));
        return new Army(unit(integer(value.get("army_id"), "army_id").intValueExact()), optionalBool(value, "controllable", false), current, target, route, state, code, combat, retreat);
    }
    private static RouteWindowPolicy.Route timed(Obj value, int date) {
        keys(value, TIMED); StrictJson.require(bool(value.get("timeline_observable"), "timeline_observable"), "complete native timeline required");
        int current = positive(value.get("current_province_id"), "current_province_id"); int origin = positive(value.get("effective_origin_province_id"), "effective_origin_province_id");
        List<Integer> provinces = array(value.get("route_province_ids"), "route_province_ids").stream().map(item -> positive(item, "route_province_id")).toList();
        List<Integer> arrivals = array(value.get("arrival_date_raws"), "arrival_date_raws").stream().map(item -> integer(item, "arrival_date_raw").intValueExact()).toList();
        StrictJson.require(provinces.isEmpty() ? origin == current : origin == current || origin == provinces.getFirst(), "effective native origin differs");
        StrictJson.require(arrivals.stream().allMatch(valueDate -> valueDate >= date), "arrival before source date");
        return new RouteWindowPolicy.Route(unit(integer(value.get("army_id"), "army_id").intValueExact()), current, provinces, arrivals);
    }
    private static RouteWindowPolicy.Conflict conflict(Obj value) {
        String kind = text(value.get("kind"), "kind"); int id = unit(integer(value.get("hostile_army_id"), "hostile_army_id").intValueExact());
        int start = integer(value.get("overlap_start_date_raw"), "overlap_start_date_raw").intValueExact(); int end = integer(value.get("overlap_end_date_raw"), "overlap_end_date_raw").intValueExact();
        if (kind.equals("same_province")) {
            keys(value, Set.of("kind", "hostile_army_id", "province_id", "overlap_start_date_raw", "overlap_end_date_raw"));
            return new RouteWindowPolicy.SameProvince(id, positive(value.get("province_id"), "province_id"), start, end);
        }
        StrictJson.require(kind.equals("opposing_edge"), "unknown native conflict kind");
        keys(value, Set.of("kind", "hostile_army_id", "subject_from_province_id", "subject_to_province_id", "hostile_from_province_id", "hostile_to_province_id", "overlap_start_date_raw", "overlap_end_date_raw"));
        return new RouteWindowPolicy.OpposingEdge(id, positive(value.get("subject_from_province_id"), "subject_from_province_id"),
                positive(value.get("subject_to_province_id"), "subject_to_province_id"), positive(value.get("hostile_from_province_id"), "hostile_from_province_id"),
                positive(value.get("hostile_to_province_id"), "hostile_to_province_id"), start, end);
    }
    private static Value modal(Obj value) {
        Value item = value.get("top_exclusive_modal_choice_hint");
        if (item == null || item == Nil.INSTANCE) return Nil.INSTANCE;
        Obj hint = object(item, "top_exclusive_modal_choice_hint"); return hint.get("status") instanceof Text status && status.value().equals("present") ? hint : Nil.INSTANCE;
    }
    public static List<Integer> ids(Value value) { return canonicalUnits(array(value, "army_ids").stream().map(item -> unit(integer(item, "army_id").intValueExact())).toList(), 1, 64); }
    private static Optional<Integer> nullableInteger(Value value, String key) { return value == Nil.INSTANCE ? Optional.empty() : Optional.of(integer(value, key).intValueExact()); }
    private static Optional<String> optionalText(Obj value, String key) { return value.get(key) == null || value.get(key) == Nil.INSTANCE ? Optional.empty() : Optional.of(text(value.get(key), key)); }
    private static boolean optionalBool(Obj value, String key, boolean fallback) { return value.get(key) == null || value.get(key) == Nil.INSTANCE ? fallback : bool(value.get(key), key); }
    private static int positive(Value value, String key) { return province(integer(value, key).intValueExact()); }
    private static BigInteger positive64(Value value, String key) { BigInteger result = integer(value, key); StrictJson.require(result.signum() > 0 && result.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 required: " + key); return result; }
    private static long pid(Value value) { long result = integer(value, "bridge_pid").longValueExact(); StrictJson.require(result > 0 && result <= 4_294_967_295L, "native uint32 PID required"); return result; }
    private static Value required(Obj value, String key) { StrictJson.require(value.members().containsKey(key), "missing is not null: " + key); return value.get(key); }
    private static void keys(Obj value, Set<String> expected) { StrictJson.require(value.members().keySet().equals(expected), "native route contract fields differ"); }
}
