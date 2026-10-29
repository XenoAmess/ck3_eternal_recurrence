package org.xar.ck3.control.military.projectedcontact;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Available;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Capture;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.CapturedRow;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryKey;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryRow;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Request;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Scope;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Selection;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Side;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Snapshot;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Transition;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.UnusableRow;

/** Strict leaf schema with explicit projections from extensible legacy containers. */
public final class ProjectedContactCodec {
    private static final Set<String> SCOPE_FIELDS = Set.of("status", "scope_kind", "snapshot_revision", "date_raw",
            "subject_army_id", "subject_native_carmy_id", "subject_owner_character_id", "subject_current_province_id",
            "target_province_id", "incoming_entry_province_id", "observed_target_public_cunit_ids",
            "observed_target_combat_ids", "transition_kind", "selected_current_combat_id",
            "selected_current_combat_array_index", "projected_subject_side", "projected_initiator_is_defender_observable",
            "projected_initiator_is_defender", "incoming_adjacency_kind_raw", "projected_attacker_army_ids",
            "projected_defender_army_ids", "contact_projection_inputs_complete");
    private static final Set<String> REQUEST_FIELDS = Set.of("subject_army_id", "target_province_id",
            "incoming_entry_province_id", "subject_current_province_id", "subject_owner_character_id");

    private ProjectedContactCodec() { }

    public record Input(Snapshot snapshot, List<QueryRow> queryRows, Request request) {
        public Input {
            Objects.requireNonNull(snapshot, "snapshot"); Objects.requireNonNull(request, "request");
            queryRows = List.copyOf(queryRows);
        }
    }

    public static Input decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("snapshot", "query_rows", "request"));
        JsonNode snapshot = objectProjection(root.get("snapshot"));
        JsonNode diagnostics = objectProjection(snapshot.get("diagnostics"));
        Capture capture = new Capture(text(snapshot, "snapshot_id"), uint(snapshot, "revision", false),
                uint(snapshot, "native_revision", true), uint(diagnostics, "connection_generation", true),
                text(snapshot, "episode_run_id"));
        Snapshot frame = new Snapshot(capture, number(snapshot, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE));
        ObjectNode request = StrictJson.object(root.get("request"), REQUEST_FIELDS);
        Request bound = new Request(new QueryKey(number(request, "subject_army_id", 0, Integer.MAX_VALUE),
                positive(request, "target_province_id"), positive(request, "incoming_entry_province_id")),
                positive(request, "subject_current_province_id"), nullableInteger(request,
                        "subject_owner_character_id", 1));
        JsonNode rows = root.get("query_rows");
        StrictJson.require(rows != null && rows.isArray() && rows.size() <= 1024, "bounded query row array required");
        List<QueryRow> result = new ArrayList<>();
        for (JsonNode row : rows) { result.add(decodeRow(row)); }
        return new Input(frame, result, bound);
    }

    public static byte[] select(byte[] raw) {
        Input input = decode(raw);
        return encode(ProjectedContactPolicy.select(input.snapshot(), input.queryRows(), input.request()));
    }

    private static QueryRow decodeRow(JsonNode value) {
        // Malformed or stale native query evidence cannot authorize contact; retain older valid history.
        try {
            JsonNode row = objectProjection(value);
            StrictJson.trueValue(row.get("ok"));
            Optional<QueryKey> key = ProjectedContactPolicy.parseStep(text(row, "step"));
            if (key.isEmpty()) { return new UnusableRow(); }
            JsonNode result = objectProjection(row.get("result"));
            Capture capture = new Capture(text(result, "queried_snapshot_id"), uint(result, "queried_revision", false),
                    uint(result, "queried_native_revision", true), uint(result, "queried_connection_generation", true),
                    text(result, "queried_episode_run_id"));
            return new CapturedRow(key.orElseThrow(), capture, decodeScope(result.get("projected_contact_scope")));
        } catch (ContractViolationException error) { return new UnusableRow(); }
    }

    public static Scope decodeScope(JsonNode value) {
        ObjectNode scope = StrictJson.object(value, SCOPE_FIELDS);
        StrictJson.require(text(scope, "status").equals("available")
                && text(scope, "scope_kind").equals(ProjectedContactPolicy.SCOPE_KIND), "available native scope required");
        StrictJson.trueValue(scope.get("contact_projection_inputs_complete"));
        boolean observable = bool(scope, "projected_initiator_is_defender_observable");
        JsonNode initiator = scope.get("projected_initiator_is_defender");
        Boolean role = initiator.isNull() ? null : bool(scope, "projected_initiator_is_defender");
        return new Scope(uint(scope, "snapshot_revision", true), number(scope, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE),
                number(scope, "subject_army_id", 0, Integer.MAX_VALUE), positive(scope, "subject_native_carmy_id"),
                positive(scope, "subject_owner_character_id"), positive(scope, "subject_current_province_id"),
                positive(scope, "target_province_id"), positive(scope, "incoming_entry_province_id"),
                ids(scope, "observed_target_public_cunit_ids", 0), componentIds(scope, "observed_target_combat_ids"),
                transition(text(scope, "transition_kind")), nullableComponent(scope, "selected_current_combat_id"),
                nullableInteger(scope, "selected_current_combat_array_index", 0), side(text(scope, "projected_subject_side")),
                observable, role, number(scope, "incoming_adjacency_kind_raw", 0, 3),
                ids(scope, "projected_attacker_army_ids", 0), ids(scope, "projected_defender_army_ids", 0));
    }

    public static byte[] encode(Selection selection) {
        ObjectNode result = StrictJson.object();
        result.put("query_step", selection.key().step());
        if (selection instanceof Available available) {
            Scope scope = available.projection();
            result.put("status", "available"); result.set("projection", encodeScope(scope));
            result.put("transition_kind", token(scope.transition())); result.put("subject_side", token(scope.subjectSide()));
            array(result, "attacker_army_ids", scope.attackerArmyIds());
            array(result, "defender_army_ids", scope.defenderArmyIds());
            result.put("incoming_attacker_geometry_ready", available.incomingAttackerGeometryReady());
            result.put("actual_arrival_observed", available.actualArrivalObserved());
            result.put("future_contact_authorized", available.futureContactAuthorized());
        } else { result.put("status", "query_required"); }
        return StrictJson.canonical(result);
    }

    public static ObjectNode encodeScope(Scope scope) {
        ObjectNode result = StrictJson.object();
        result.put("status", "available"); result.put("scope_kind", ProjectedContactPolicy.SCOPE_KIND);
        result.put("snapshot_revision", scope.snapshotRevision()); result.put("date_raw", scope.dateRaw());
        result.put("subject_army_id", scope.subjectArmyId()); result.put("subject_native_carmy_id", scope.subjectNativeCarmyId());
        result.put("subject_owner_character_id", scope.subjectOwnerCharacterId());
        result.put("subject_current_province_id", scope.subjectCurrentProvinceId());
        result.put("target_province_id", scope.targetProvinceId()); result.put("incoming_entry_province_id", scope.incomingEntryProvinceId());
        array(result, "observed_target_public_cunit_ids", scope.observedTargetPublicCunitIds());
        array(result, "observed_target_combat_ids", scope.observedTargetCombatIds());
        result.put("transition_kind", token(scope.transition()));
        nullable(result, "selected_current_combat_id", scope.selectedCurrentCombatId());
        nullable(result, "selected_current_combat_array_index", scope.selectedCurrentCombatArrayIndex());
        result.put("projected_subject_side", token(scope.subjectSide()));
        result.put("projected_initiator_is_defender_observable", scope.initiatorIsDefenderObservable());
        if (scope.initiatorIsDefender() == null) { result.putNull("projected_initiator_is_defender"); }
        else { result.put("projected_initiator_is_defender", scope.initiatorIsDefender()); }
        result.put("incoming_adjacency_kind_raw", scope.incomingAdjacencyKindRaw());
        array(result, "projected_attacker_army_ids", scope.attackerArmyIds());
        array(result, "projected_defender_army_ids", scope.defenderArmyIds());
        result.put("contact_projection_inputs_complete", true);
        return result;
    }

    private static JsonNode objectProjection(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "legacy container object required"); return value;
    }
    private static String text(JsonNode value, String key) { return StrictJson.text(value.get(key)); }
    private static int positive(JsonNode value, String key) { return number(value, key, 1, Integer.MAX_VALUE); }
    private static int number(JsonNode value, String key, int low, int high) {
        return (int) StrictJson.integer(value.get(key), low, high);
    }
    private static BigInteger uint(JsonNode value, String key, boolean positive) {
        return StrictJson.integer(value.get(key), positive ? BigInteger.ONE : BigInteger.ZERO, StrictJson.UINT64_MAX);
    }
    private static Integer nullableInteger(JsonNode value, String key, int low) {
        JsonNode field = value.get(key); StrictJson.require(field != null, "required nullable field missing: " + key);
        return field.isNull() ? null : number(value, key, low, Integer.MAX_VALUE);
    }
    private static Integer nullableComponent(JsonNode value, String key) {
        JsonNode field=value.get(key);StrictJson.require(field!=null,"required nullable field missing: "+key);
        if(field.isNull())return null;
        int result=(int)StrictJson.integer(field,Integer.MIN_VALUE,Integer.MAX_VALUE);
        StrictJson.require(result!=-1,"missing full ComponentID sentinel forbidden");return result;
    }
    private static List<Integer> componentIds(JsonNode value,String key) {
        JsonNode items=value.get(key);StrictJson.require(items!=null&&items.isArray(),"full ComponentID array required: "+key);
        List<Integer> result=new ArrayList<>();
        for(JsonNode item:items){int id=(int)StrictJson.integer(item,Integer.MIN_VALUE,Integer.MAX_VALUE);StrictJson.require(id!=-1,"missing full ComponentID sentinel forbidden");result.add(id);}
        return result;
    }
    private static boolean bool(JsonNode value, String key) {
        JsonNode field = value.get(key); StrictJson.require(field != null && field.isBoolean(), "JSON bool required: " + key);
        return field.booleanValue();
    }
    private static List<Integer> ids(JsonNode value, String key, int low) {
        JsonNode items = value.get(key); StrictJson.require(items != null && items.isArray(), "identity array required: " + key);
        List<Integer> result = new ArrayList<>();
        for (JsonNode item : items) { result.add((int) StrictJson.integer(item, low, Integer.MAX_VALUE)); }
        return result;
    }
    private static Transition transition(String value) {
        return switch (value) {
            case "none" -> Transition.NONE; case "join_existing" -> Transition.JOIN_EXISTING;
            case "create_new" -> Transition.CREATE_NEW;
            default -> throw new ContractViolationException("unknown contact transition");
        };
    }
    private static Side side(String value) {
        return switch (value) {
            case "none" -> Side.NONE; case "attacker" -> Side.ATTACKER; case "defender" -> Side.DEFENDER;
            default -> throw new ContractViolationException("unknown subject side");
        };
    }
    private static String token(Transition value) {
        return switch (value) { case NONE -> "none"; case JOIN_EXISTING -> "join_existing"; case CREATE_NEW -> "create_new"; };
    }
    private static String token(Side value) {
        return switch (value) { case NONE -> "none"; case ATTACKER -> "attacker"; case DEFENDER -> "defender"; };
    }
    private static void nullable(ObjectNode result, String key, Integer value) {
        if (value == null) { result.putNull(key); } else { result.put(key, value); }
    }
    private static void array(ObjectNode result, String key, List<Integer> values) {
        ArrayNode array = result.putArray(key); values.forEach(array::add);
    }
}
