package org.xar.ck3.control.wave2.military.actualcontact;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel.Binding;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel.Query;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel.Scope;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel.ScopeKind;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel.Side;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel.Transition;

/** Strict native-shaped contract. Decode does not confer native provenance. */
public final class ActualContactCodec {
    private static final Set<String> SCOPE_KEYS = Set.of("schema_version", "contract_stage", "status", "scope_kind",
            "snapshot_revision", "date_raw", "subject_army_id", "subject_native_carmy_id", "subject_owner_character_id",
            "target_province_id", "province_unit_army_ids", "province_combat_ids", "stored_order_policy", "transition_kind",
            "selected_combat_id", "selected_combat_array_index", "join_side", "defender_seed_character_id", "initiator_is_defender",
            "adjacency_kind_raw", "loser_excluded_native_carmy_ids", "opponent_army_ids", "attacker_army_ids", "defender_army_ids",
            "actual_contact_scope_ready", "combat_v3_participant_scope_ready");
    private ActualContactCodec() { }

    private sealed interface QueryInput permits BuildQuery, ParseQuery { }
    private record BuildQuery(Query query) implements QueryInput { }
    private record ParseQuery(String step) implements QueryInput { }

    public static void validateQueryRequest(byte[] raw) { decodeQueryInput(raw); }

    private static QueryInput decodeQueryInput(byte[] raw) {
        JsonNode input = StrictJson.parse(raw); String operation = StrictJson.text(input.get("operation"));
        if (operation.equals("build_query")) {
            StrictJson.object(input, Set.of("operation", "subject_army_id", "target_province_id"));
            return new BuildQuery(new Query(number(input, "subject_army_id", 0, Integer.MAX_VALUE),
                    number(input, "target_province_id", 1, Integer.MAX_VALUE)));
        } else if (operation.equals("parse_query")) {
            StrictJson.object(input, Set.of("operation", "step")); JsonNode value = input.get("step");
            return new ParseQuery(value.isTextual() ? value.textValue() : null);
        } else { throw new ContractViolationException("unknown actual contact query operation"); }
    }

    public static byte[] query(byte[] raw) {
        QueryInput input = decodeQueryInput(raw); ObjectNode output = StrictJson.object();
        if (input instanceof BuildQuery build) { output.put("step", build.query().step()); }
        else if (input instanceof ParseQuery parse) {
            Optional<Query> parsed = ActualContactModel.parseStep(parse.step());
            if (parsed.isPresent()) { var tuple = output.putArray("parsed"); tuple.add(parsed.orElseThrow().subjectArmyId()); tuple.add(parsed.orElseThrow().targetProvinceId()); }
            else { output.putNull("parsed"); }
        }
        return StrictJson.canonical(output);
    }

    private record BoundScope(Scope scope, Binding binding) { }

    /** Only this explicit host binding refusal uses the host domain marker. */
    public static void validateScopeRequest(byte[] raw) {
        BoundScope input = decodeBoundScope(raw);
        if (!input.scope().matches(input.binding())) { throw new ProjectionDomainRejection("actual contact source binding disagrees"); }
    }

    public static byte[] normalize(byte[] raw) {
        BoundScope input = decodeBoundScope(raw);
        StrictJson.require(input.scope().matches(input.binding()), "actual contact source binding disagrees");
        return StrictJson.canonical(encodeScope(input.scope()));
    }

    private static BoundScope decodeBoundScope(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("scope", "expected"));
        ObjectNode expected = StrictJson.object(root.get("expected"), Set.of("subject_army_id", "target_province_id", "date_raw", "snapshot_revision"));
        Binding binding = new Binding(new Query(number(expected, "subject_army_id", 0, Integer.MAX_VALUE),
                number(expected, "target_province_id", 1, Integer.MAX_VALUE)), number(expected, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE),
                StrictJson.integer(expected.get("snapshot_revision"), BigInteger.ONE, StrictJson.UINT64_MAX));
        Scope scope = decodeScope(root.get("scope"));
        return new BoundScope(scope, binding);
    }

    public static Scope decodeScope(JsonNode value) {
        ObjectNode scope = StrictJson.object(value, SCOPE_KEYS);
        // Explicit user-required type fix: Python equality previously accepted true and 1.0 as version 1.
        StrictJson.integer(scope.get("schema_version"), 1, 1);
        StrictJson.require(text(scope, "contract_stage").equals("production_exact_current_province")
                && text(scope, "status").equals("available") && text(scope, "stored_order_policy").equals("numeric_full_id"),
                "current Province contact contract unavailable");
        StrictJson.trueValue(scope.get("actual_contact_scope_ready"));
        return new Scope(kind(text(scope, "scope_kind")), StrictJson.integer(scope.get("snapshot_revision"), BigInteger.ONE, StrictJson.UINT64_MAX),
                number(scope, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE), number(scope, "subject_army_id", 0, Integer.MAX_VALUE),
                number(scope, "subject_native_carmy_id", 1, Integer.MAX_VALUE), number(scope, "subject_owner_character_id", 1, Integer.MAX_VALUE),
                number(scope, "target_province_id", 1, Integer.MAX_VALUE), ids(scope, "province_unit_army_ids", 0), ids(scope, "province_combat_ids", 1),
                transition(text(scope, "transition_kind")), nullable(scope, "selected_combat_id", 1), nullable(scope, "selected_combat_array_index", 0),
                side(scope.get("join_side")), nullable(scope, "defender_seed_character_id", 1), bool(scope, "initiator_is_defender"),
                number(scope, "adjacency_kind_raw", Integer.MIN_VALUE, Integer.MAX_VALUE), ids(scope, "loser_excluded_native_carmy_ids", 1),
                ids(scope, "opponent_army_ids", 0), ids(scope, "attacker_army_ids", 0), ids(scope, "defender_army_ids", 0),
                bool(scope, "combat_v3_participant_scope_ready"));
    }

    public static ObjectNode encodeScope(Scope scope) {
        ObjectNode result = StrictJson.object(); result.put("schema_version", 1);
        result.put("contract_stage", "production_exact_current_province"); result.put("status", "available");
        result.put("scope_kind", scope.scopeKind() == ScopeKind.PRE_CONTACT_PREDICTION ? "pre_contact_prediction" : "post_contact_observation");
        result.put("snapshot_revision", scope.snapshotRevision()); result.put("date_raw", scope.dateRaw());
        result.put("subject_army_id", scope.subjectArmyId()); result.put("subject_native_carmy_id", scope.subjectNativeCarmyId());
        result.put("subject_owner_character_id", scope.subjectOwnerCharacterId()); result.put("target_province_id", scope.targetProvinceId());
        array(result, "province_unit_army_ids", scope.provinceUnitArmyIds()); array(result, "province_combat_ids", scope.provinceCombatIds());
        result.put("stored_order_policy", "numeric_full_id"); result.put("transition_kind", token(scope.transition()));
        nullable(result, "selected_combat_id", scope.selectedCombatId()); nullable(result, "selected_combat_array_index", scope.selectedCombatArrayIndex());
        if (scope.joinSide() == null) { result.putNull("join_side"); }
        else { result.put("join_side", scope.joinSide() == Side.ATTACKER ? "attacker" : "defender"); }
        nullable(result, "defender_seed_character_id", scope.defenderSeedCharacterId()); result.put("initiator_is_defender", scope.initiatorIsDefender());
        result.put("adjacency_kind_raw", scope.adjacencyKindRaw()); array(result, "loser_excluded_native_carmy_ids", scope.loserExcludedNativeCarmyIds());
        array(result, "opponent_army_ids", scope.opponentArmyIds()); array(result, "attacker_army_ids", scope.attackerArmyIds());
        array(result, "defender_army_ids", scope.defenderArmyIds()); result.put("actual_contact_scope_ready", true);
        result.put("combat_v3_participant_scope_ready", scope.combatV3ParticipantScopeReady()); return result;
    }

    private static int number(JsonNode value, String field, int minimum, int maximum) { return (int) StrictJson.integer(value.get(field), minimum, maximum); }
    private static String text(JsonNode value, String field) { return StrictJson.text(value.get(field)); }
    private static boolean bool(JsonNode value, String field) {
        JsonNode node = value.get(field); StrictJson.require(node != null && node.isBoolean(), "JSON boolean required: " + field); return node.booleanValue();
    }
    private static Integer nullable(JsonNode value, String field, int minimum) {
        JsonNode node = value.get(field); StrictJson.require(node != null, "required nullable field missing: " + field);
        return node.isNull() ? null : number(value, field, minimum, Integer.MAX_VALUE);
    }
    private static List<Integer> ids(JsonNode value, String field, int minimum) {
        JsonNode nodes = value.get(field); StrictJson.require(nodes != null && nodes.isArray(), "native ID array required: " + field);
        List<Integer> result = new ArrayList<>(); for (JsonNode node : nodes) { result.add((int) StrictJson.integer(node, minimum, Integer.MAX_VALUE)); }
        return result;
    }
    private static ScopeKind kind(String value) {
        return switch (value) { case "pre_contact_prediction" -> ScopeKind.PRE_CONTACT_PREDICTION;
            case "post_contact_observation" -> ScopeKind.POST_CONTACT_OBSERVATION;
            default -> throw new ContractViolationException("unknown actual contact scope kind"); };
    }
    private static Transition transition(String value) {
        return switch (value) { case "none" -> Transition.NONE; case "join_existing" -> Transition.JOIN_EXISTING;
            case "create_new" -> Transition.CREATE_NEW; case "in_combat" -> Transition.IN_COMBAT;
            default -> throw new ContractViolationException("unknown actual contact transition"); };
    }
    private static Side side(JsonNode value) {
        StrictJson.require(value != null, "required nullable join_side missing"); if (value.isNull()) { return null; }
        return switch (StrictJson.text(value)) { case "attacker" -> Side.ATTACKER; case "defender" -> Side.DEFENDER;
            default -> throw new ContractViolationException("unknown join side"); };
    }
    private static String token(Transition value) {
        return switch (value) { case NONE -> "none"; case JOIN_EXISTING -> "join_existing"; case CREATE_NEW -> "create_new"; case IN_COMBAT -> "in_combat"; };
    }
    private static void array(ObjectNode output, String field, List<Integer> values) { var array = output.putArray(field); values.forEach(array::add); }
    private static void nullable(ObjectNode output, String field, Integer value) { if (value == null) { output.putNull(field); } else { output.put(field, value); } }
}
