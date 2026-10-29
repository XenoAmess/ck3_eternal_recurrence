package org.xar.ck3.control.service.mcp;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/** Original Service planning/camera DATA projections over the already frozen semantic observation.
 * No observation, writer, action qualification, public-width conversion or native access occurs here.
 */
public final class OriginalPlanningFrameProjection {
    private OriginalPlanningFrameProjection() { }
    private static final List<String> ARMY_FIELDS = List.of("army_id", "current_province_id",
            "in_combat", "controllable", "army_state", "siege_days_left", "retreating",
            "move_target_province_id", "route_province_ids");
    private static final Set<String> ACTIVE_STATES = Set.of("moving", "siege", "sieging", "gathering");

    public static Obj sourceFrame(PlanningRequest actual) {
        return sourceFrame(Objects.requireNonNull(actual).observations().snapshot());
    }

    /** Already observed raw or Ready semantic DATA. Caller retains actual source/current custody. */
    public static Obj sourceFrame(Obj actualSnapshot) {
        Obj snapshot = Objects.requireNonNull(actualSnapshot);
        Value actor = child(snapshot.get("played_character"), "character_id");
        Value generation = child(snapshot.get("diagnostics"), "connection_generation");
        var fields = new LinkedHashMap<String, Value>();
        fields.put("schema", new Text("xar.ck3.planning-source-frame/v1"));
        // Intentional shared native-ID repair: signed int32 except -1 replaces Python actor>0.
        // This complete DATA status grants no private-character or action permission.
        boolean complete = nonempty(snapshot.get("snapshot_id"))
                && nonnegative(snapshot.get("revision")) && positive(snapshot.get("native_revision"))
                && snapshot.get("date_raw") instanceof IntegerValue && nativeActor(actor)
                && nonempty(snapshot.get("episode_run_id")) && nonnegative(generation);
        fields.put("status", new Text(complete ? "complete" : "partial"));
        fields.put("snapshot_id", get(snapshot, "snapshot_id"));
        fields.put("revision", get(snapshot, "revision"));
        fields.put("native_revision", get(snapshot, "native_revision"));
        fields.put("date_raw", get(snapshot, "date_raw"));
        fields.put("actor_character_id", actor);
        fields.put("episode_run_id", get(snapshot, "episode_run_id"));
        fields.put("connection_generation", generation);
        fields.put("bridge_pid", child(snapshot.get("diagnostics"), "bridge_pid"));
        return new Obj(fields);
    }

    public static Obj cameraInput(PlanningRequest actual) {
        return cameraInput(Objects.requireNonNull(actual).observations().snapshot());
    }

    /** Same original projection for raw terminal semantic DATA; no actor or PlanningRequest is created. */
    public static Obj cameraInput(Obj actualSnapshot) {
        Obj snapshot = Objects.requireNonNull(actualSnapshot);
        var wars = new ArrayList<Value>();
        for (Obj war : objectRows(snapshot.get("active_wars"), "active_wars")) {
            var armies = new ArrayList<Value>();
            for (Obj army : objectRows(war.get("allied_armies"), "allied_armies")) {
                var fields = new LinkedHashMap<String, Value>();
                for (String key : ARMY_FIELDS) {
                    Value value = get(army, key);
                    fields.put(key, key.equals("route_province_ids")
                            ? value instanceof Arr array ? new Arr(array.items()) : Nil.INSTANCE : value);
                }
                armies.add(new Obj(fields));
            }
            var states = new ArrayList<Value>();
            for (Obj row : objectRows(war.get("objective_province_states"), "objective_province_states")) {
                var fields = new LinkedHashMap<String, Value>();
                fields.put("province_id", get(row, "province_id"));
                fields.put("active_siege", get(row, "active_siege"));
                states.add(new Obj(fields));
            }
            var fields = new LinkedHashMap<String, Value>();
            fields.put("war_id", get(war, "war_id"));
            fields.put("allied_armies", new Arr(armies));
            fields.put("objective_province_states", new Arr(states));
            fields.put("war_objective_province_ids", new Arr(iterable(war.get("war_objective_province_ids"),
                    "war_objective_province_ids")));
            wars.add(new Obj(fields));
        }
        boolean hasArmies = objectRows(snapshot.get("player_armies"), "player_armies").stream().anyMatch(army ->
                isTrue(army.get("in_combat")) || isTrue(army.get("retreating"))
                || positive(army.get("move_target_province_id"))
                || activeState(army.get("army_state")));
        Obj diagnostics = truthyObject(snapshot.get("diagnostics"), "diagnostics");
        Obj hello = truthyObject(diagnostics.get("hello"), "diagnostics.hello");
        var build = new LinkedHashMap<String, Value>();
        build.put("game_version", fallback(hello, "expected_ck3_version", "game_version"));
        build.put("executable_sha256", fallback(hello, "expected_ck3_sha256", "executable_sha256"));
        var fields = new LinkedHashMap<String, Value>();
        fields.put("source_frame", sourceFrame(snapshot));
        fields.put("active_wars", new Arr(wars));
        fields.put("map_ready", get(snapshot, "map_ready"));
        fields.put("has_active_event", new Bool(present(snapshot.get("active_event"))));
        fields.put("has_pending_interaction", new Bool(present(snapshot.get("pending_character_interaction"))));
        fields.put("mandatory_choice", new Bool(snapshot.get("top_exclusive_modal_choice_hint") instanceof Obj hint
                && new Text("present").equals(hint.get("status"))));
        fields.put("has_player_armies", new Bool(hasArmies));
        fields.put("source_build", new Obj(build));
        return new Obj(fields);
    }

    /** Caller supplies only its already observed, same-frame campaign-root result.
     * This projection does not look up history or certify the supplied root's provenance. */
    public static Obj ordinarySwayInput(PlanningRequest actual, Value actualRootResult) {
        return ordinarySwayInput(Objects.requireNonNull(actual).observations().snapshot(), actualRootResult);
    }

    /** Caller supplies the unchanged actual snapshot and its already observed same-frame root result. */
    public static Obj ordinarySwayInput(Obj actualSnapshot, Value actualRootResult) {
        Obj snapshot = Objects.requireNonNull(actualSnapshot);
        var frame = new LinkedHashMap<String, Value>();
        for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw", "paused",
                "map_ready", "episode_run_id", "episode_character_id", "one_life_terminal_reason"))
            frame.put(key, get(snapshot, key));
        Value played = snapshot.get("played_character");
        frame.put("played_character", played instanceof Obj p ? new Obj(p.members()) : Nil.INSTANCE);
        Value context = snapshot.get("active_context");
        if (!(context instanceof Obj) && snapshot.members().containsKey("active_event")
                && snapshot.members().containsKey("pending_character_interaction")) {
            var fallback = new LinkedHashMap<String, Value>();
            fallback.put("active_event", get(snapshot, "active_event"));
            fallback.put("pending_character_interaction", get(snapshot, "pending_character_interaction"));
            context = new Obj(fallback);
        }
        frame.put("active_context", context instanceof Obj c ? new Obj(c.members()) : Nil.INSTANCE);
        Value root = child(actualRootResult, "campaign_root_context");
        Value compact = Nil.INSTANCE;
        if (root instanceof Obj observedRoot) {
            var fields = new LinkedHashMap<String, Value>();
            for (String key : List.of("status", "player_character_id", "player_character_alive",
                    "snapshot_revision", "date_raw")) fields.put(key, get(observedRoot, key));
            Value ids = observedRoot.get("direct_landed_vassal_character_ids");
            fields.put("direct_landed_vassal_character_ids", ids instanceof Arr a ? new Arr(a.items()) : Nil.INSTANCE);
            compact = new Obj(fields);
        }
        var output = new LinkedHashMap<String, Value>();
        output.put("snapshot", new Obj(frame)); output.put("root", compact);
        return new Obj(output);
    }

    private static Value get(Obj object, String field) {
        Value value = object.get(field); return value == null ? Nil.INSTANCE : value;
    }
    private static Value child(Value value, String field) {
        return value instanceof Obj object ? get(object, field) : Nil.INSTANCE;
    }
    private static Value fallback(Obj object, String primary, String secondary) {
        return object.members().containsKey(primary) ? get(object, primary) : get(object, secondary);
    }
    private static boolean nonempty(Value value) { return value instanceof Text t && !t.value().isEmpty(); }
    private static boolean positive(Value value) { return value instanceof IntegerValue n && n.value().signum() > 0; }
    private static boolean nonnegative(Value value) { return value instanceof IntegerValue n && n.value().signum() >= 0; }
    private static boolean activeState(Value value) {
        if (value instanceof Arr || value instanceof Obj)
            throw new IllegalArgumentException("army_state must be hashable as in the original JSON projection");
        return value instanceof Text text && ACTIVE_STATES.contains(text.value());
    }
    private static boolean isTrue(Value value) { return value instanceof Bool b && b.value(); }
    private static boolean present(Value value) { return value != null && value != Nil.INSTANCE; }
    private static boolean nativeActor(Value value) {
        if (!(value instanceof IntegerValue integer)) return false;
        try { NativeCharacterId.of(integer.value()); return true; }
        catch (IllegalArgumentException absentOrOverflow) { return false; }
    }

    /** Python JSON truthiness and list(iterable or []) without a double conversion. */
    private static boolean truthy(Value value) {
        if (!present(value)) return false;
        if (value instanceof Bool b) return b.value();
        if (value instanceof IntegerValue n) return n.value().signum() != 0;
        if (value instanceof OpportunityJson.DecimalValue n) return new java.math.BigDecimal(n.token()).signum() != 0;
        if (value instanceof Text t) return !t.value().isEmpty();
        if (value instanceof Arr a) return !a.items().isEmpty();
        return value instanceof Obj o && !o.members().isEmpty();
    }
    private static Obj truthyObject(Value value, String field) {
        if (!truthy(value)) return new Obj(java.util.Map.of());
        return OpportunityJson.object(value, field);
    }
    private static List<Value> iterable(Value value, String field) {
        if (!truthy(value)) return List.of();
        if (value instanceof Arr a) return a.items();
        if (value instanceof Obj o) return o.members().keySet().stream().map(name -> (Value) new Text(name)).toList();
        if (value instanceof Text t) return t.value().codePoints()
                .mapToObj(point -> (Value) new Text(new String(Character.toChars(point)))).toList();
        throw new IllegalArgumentException(field + " must be iterable");
    }
    private static List<Obj> objectRows(Value value, String field) {
        return iterable(value, field).stream().filter(Obj.class::isInstance).map(Obj.class::cast).toList();
    }
}
