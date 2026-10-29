package org.xar.ck3.control.wave3.military.holyobservation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract.Choice;
import org.xar.ck3.control.wave2.military.holycost.HolyCostJsonAdapter;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation;

/** The existing ordinary-plan annotation policy. It never changes the selected action or sends a declaration. */
public final class HolyDefenderObservation {
    public static final String ANNOTATION = "ordinary_holy_war_candidate_observation";
    public static final String CHILD = "player_holy_war_defender_join_inputs";
    private static final List<String> ROLES = List.of("context_actor_character_id", "context_recipient_character_id",
            "context_additional_role_character_id", "context_claimant_character_id", "recipient_uses_native_fallback",
            "additional_role_uses_native_fallback", "claimant_uses_native_fallback");
    private static final List<String> CHILD_FIELDS = List.of("primary_attacker_character_id", "primary_defender_character_id",
            "primary_defender_faith_available", "primary_defender_faith_unavailable_reason", "primary_defender_rite_id",
            "primary_defender_faith_id", "cb_flags_raw", "defender_faith_can_join", "native_joiner_set_observed",
            "joiner_count", "joiners", "raw_scale", "unit", "is_final_join_score");
    private HolyDefenderObservation() { }

    public enum Status {
        FRAME_NOT_READY, NATIVE_CATALOGUE_UNAVAILABLE, NO_CURRENT_ORDINARY_HOLY_WAR_CANDIDATE,
        QUERY_UNAVAILABLE, QUERY_FAILED, DEFENDER_INPUTS_NOT_RETURNED, NATIVE_DEFENDER_SET_UNAVAILABLE,
        NO_EXTRA_NATIVE_DEFENDERS_OBSERVED, EXTRA_NATIVE_DEFENDERS_OBSERVED;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public sealed interface Preparation permits Unchanged, Annotated, Query { }
    public record Unchanged() implements Preparation { }
    public record Annotated(Status status, String reason, Candidate candidate) implements Preparation {
        public Annotated { Objects.requireNonNull(status); }
    }
    public record Candidate(int sourceOrdinal, Choice choice) {
        public Candidate { StrictJson.require(sourceOrdinal >= 0 && choice != null, "current canonical candidate required"); }
    }
    public record Query(BigInteger expectedRevision, Candidate candidate) implements Preparation {
        public Query { Objects.requireNonNull(expectedRevision); Objects.requireNonNull(candidate); }
    }
    public record Observation(HolyCostObservation owner, HolyDefenderInputs child, Status status) {
        public Observation { Objects.requireNonNull(owner); Objects.requireNonNull(status); }
    }

    public static Preparation prepare(JsonNode planned, JsonNode snapshot, boolean permission, boolean queryAvailable) {
        if (!permission || planned == null || !planned.isObject() || !planned.path("plan").isObject()) { return new Unchanged(); }
        JsonNode actor = snapshot.path("played_character");
        JsonNode revision = planned.get("revision"), nativeRevision = snapshot.get("native_revision");
        if (!trueFlag(snapshot.get("paused")) || !trueFlag(snapshot.get("map_ready"))
                || !nullOrMissing(snapshot.get("active_event")) || !nullOrMissing(snapshot.get("pending_character_interaction"))
                || !actor.isObject() || !trueFlag(actor.get("alive")) || !positiveInteger(revision)
                || !positiveInteger(snapshot.get("revision")) || !revision.bigIntegerValue().equals(snapshot.get("revision").bigIntegerValue())
                || !positiveInteger(nativeRevision)) { return new Annotated(Status.FRAME_NOT_READY, null, null); }
        List<Choice> rows;
        try { rows = DeclarationContract.normalize(snapshot.get("declarable_wars")); }
        catch (ProjectionDomainRejection refusal) { return new Annotated(Status.NATIVE_CATALOGUE_UNAVAILABLE, refusal.getMessage(), null); }
        Candidate selected = null;
        for (int ordinal = 0; ordinal < rows.size(); ordinal++) {
            if (HolyCostJsonAdapter.ORDINARY_HOLY_WAR_KEYS.contains(rows.get(ordinal).casusBelliKey())) {
                selected = new Candidate(ordinal, rows.get(ordinal)); break;
            }
        }
        if (selected == null) { return new Annotated(Status.NO_CURRENT_ORDINARY_HOLY_WAR_CANDIDATE, null, null); }
        return queryAvailable ? new Query(revision.bigIntegerValue(), selected) : new Annotated(Status.QUERY_UNAVAILABLE, null, selected);
    }

    /** Validate the actual normalized owner, optional child and snapshot together before producing an internal observation. */
    public static Observation observe(JsonNode normalizedQuery, JsonNode snapshot) {
        ObjectNode core = HolyCostJsonAdapter.projectCore(normalizedQuery);
        String declaration = StrictJson.text(core.get("declaration_id"));
        HolyCostObservation owner = HolyCostJsonAdapter.normalize(core, snapshot, declaration, core.get("selected_declaration"));
        JsonNode rawChild = normalizedQuery.get(CHILD);
        HolyDefenderInputs child = rawChild == null || rawChild.isNull() ? null : HolyDefenderInputsCodec.normalize(rawChild, owner, snapshot);
        Status status = child == null ? Status.DEFENDER_INPUTS_NOT_RETURNED : !child.nativeJoinerSetObserved()
                ? Status.NATIVE_DEFENDER_SET_UNAVAILABLE : child.joinerCount() == 0
                ? Status.NO_EXTRA_NATIVE_DEFENDERS_OBSERVED : Status.EXTRA_NATIVE_DEFENDERS_OBSERVED;
        return new Observation(owner, child, status);
    }

    public static ObjectNode annotation(JsonNode snapshot, Status status) {
        ObjectNode output = StrictJson.object().put("status", status.wire()).put("read_only", true);
        ObjectNode frame = output.putObject("source_frame");
        for (String field : List.of("snapshot_id", "revision", "native_revision", "date_raw")) { copy(frame, field, snapshot.get(field)); }
        copy(frame, "played_character_id", snapshot.path("played_character").get("character_id"));
        JsonNode wars = snapshot.get("active_wars");
        output.put("decision", truthy(wars) ? "continue_current_war" : "observation_only");
        output.put("automatic_declaration_enabled", false); return output;
    }

    public static ObjectNode project(Observation observed, JsonNode normalizedQuery, JsonNode snapshot) {
        ObjectNode result = annotation(snapshot, observed.status());
        for (String field : List.of("declaration_id", "selected_declaration", "final_can_send", "cb_cost",
                "generic_interaction_cost_raw", "total_declaration_cost_raw", "total_cost_ready", "query_status")) {
            copy(result, field, normalizedQuery.get(field));
        }
        copy(result, "declaration_context_available", normalizedQuery.get("available"));
        copy(result, "declaration_context_unavailable_reason", normalizedQuery.get("unavailable_reason"));
        copy(result, "query_backend_id", normalizedQuery.get("backend_id"));
        ObjectNode roles = result.putObject("native_roles");
        for (String field : ROLES) { copy(roles, field, normalizedQuery.get(field)); }
        copy(result, "cb_cost_available", normalizedQuery.path("cb_cost").get("available"));
        JsonNode child = observed.child() == null ? null : HolyDefenderInputsCodec.encode(observed.child());
        copy(result, CHILD, child); copy(result, "defender_inputs_available", child == null ? null : child.get("available"));
        copy(result, "defender_inputs_unavailable_reason", child == null ? null : child.get("unavailable_reason"));
        for (String field : CHILD_FIELDS) { copy(result, field, child == null ? null : child.get(field)); }
        return result;
    }

    public static ObjectNode fold(JsonNode planned, JsonNode snapshot, Preparation prepared, JsonNode normalizedQuery,
            Observation observation, String queryError) {
        if (prepared instanceof Unchanged) { return (ObjectNode) planned.deepCopy(); }
        ObjectNode annotation;
        if (prepared instanceof Annotated result) {
            annotation = annotation(snapshot, result.status());
            if (result.reason() != null) { annotation.put("reason", result.reason()); }
            candidate(annotation, result.candidate());
        } else if (prepared instanceof Query query) {
            if (queryError != null) {
                annotation = annotation(snapshot, Status.QUERY_FAILED); candidate(annotation, query.candidate()); annotation.put("reason", queryError);
            } else {
                Objects.requireNonNull(observation, "validated current observation required");
                annotation = project(observation, normalizedQuery, snapshot); annotation.put("source_ordinal", query.candidate().sourceOrdinal());
            }
        } else { throw new IllegalArgumentException("unknown typed preparation"); }
        ObjectNode output = (ObjectNode) planned.deepCopy(); ((ObjectNode) output.get("plan")).set(ANNOTATION, annotation); return output;
    }

    private static void candidate(ObjectNode output, Candidate candidate) {
        if (candidate != null) {
            output.put("source_ordinal", candidate.sourceOrdinal()).put("declaration_id", candidate.choice().declarationId());
            ObjectNode selected = DeclarationContract.encodeChoice(candidate.choice());
            selected.remove("declaration_id"); selected.remove("source"); output.set("selected_declaration", selected);
        }
    }
    private static void copy(ObjectNode output, String field, JsonNode value) { output.set(field, value == null ? output.nullNode() : value.deepCopy()); }
    private static boolean trueFlag(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static boolean positiveInteger(JsonNode value) { return value != null && value.isIntegralNumber() && value.bigIntegerValue().signum() > 0; }
    private static boolean nullOrMissing(JsonNode value) { return value == null || value.isNull(); }
    private static boolean truthy(JsonNode value) {
        if (value == null || value.isNull()) { return false; }
        if (value.isContainerNode()) { return !value.isEmpty(); }
        if (value.isBoolean()) { return value.booleanValue(); }
        if (value.isNumber()) { return value.decimalValue().signum() != 0; }
        return !value.isTextual() || !value.textValue().isEmpty();
    }
}
