package org.xar.ck3.control.wave2.events.eventoutcome;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Decision;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.EffectProfile;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Evaluation;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Expectation;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.ExpectationStatus;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Metric;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Observation;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.ObservationPair;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.PlanInput;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Relation;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Resource;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Selection;

/** Strict scalar fields within explicitly extensible legacy decision/native containers. */
public final class ScalarOutcomeCodec {
    private static final String PLAN_SCHEMA = "xar.ck3.scalar-event-outcome-plan-input/v1";
    private ScalarOutcomeCodec() { }

    public static PlanInput decodePlanInput(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "decision", "played_character",
            "played_character_gold", "played_character_prestige", "snapshot_id", "revision"));
        StrictJson.require(PLAN_SCHEMA.equals(text(root, "schema")), "scalar plan input schema");
        JsonNode decisionNode = nullableObject(root.get("decision"));
        JsonNode character = nullableObject(root.get("played_character"));
        return new PlanInput(decision(decisionNode), integer(character, "character_id"), integer(character, "stress_points"),
            resource(nullableObject(root.get("played_character_gold"))), resource(nullableObject(root.get("played_character_prestige"))),
            text(root, "snapshot_id"), integer(root, "revision"));
    }

    public static byte[] encodePlanInput(PlanInput input) {
        ObjectNode root = StrictJson.object().put("schema", PLAN_SCHEMA);
        Decision decision = input.decision();
        if (decision == null) root.putNull("decision");
        else {
            ObjectNode row = root.putObject("decision");
            row.put("status", decision.status()).put("event_definition_key", decision.eventDefinitionKey()).put("ck3_build", decision.ck3Build())
                .put("selected_option_number", decision.selectedOptionNumber()).put("selected_native_option_index", decision.selectedNativeOptionIndex());
            if (decision.profile() == null) row.putNull("choice_effect_profile");
            else {
                EffectProfile profile = decision.profile();
                ObjectNode effect = row.putObject("choice_effect_profile");
                effect.put("schema", profile.schema()).put("schema_version", profile.schemaVersion())
                    .put("selected_native_option_index", profile.selectedNativeOptionIndex());
                effect.putObject("observable_postcondition").put("metric", profile.metric())
                    .put("expected_relation", profile.expectedRelation()).put("material_change_required_for_evidence", profile.materialChangeRequired());
            }
        }
        root.putObject("played_character").put("character_id", input.characterId()).put("stress_points", input.stressPoints());
        resourceNode(root, "played_character_gold", input.gold());
        resourceNode(root, "played_character_prestige", input.prestige());
        root.put("snapshot_id", input.snapshotId()).put("revision", input.revision());
        return StrictJson.canonical(root);
    }

    public static Expectation decodeExpectation(byte[] raw) {
        JsonNode root = nullableObject(StrictJson.parse(raw));
        StrictJson.require(root != null && ScalarEventOutcome.SCHEMA.equals(text(root, "schema"))
            && BigInteger.ONE.equals(integer(root, "schema_version")), "scalar expectation schema");
        StrictJson.require(Boolean.TRUE.equals(bool(root, "material_change_required_for_evidence")), "material requirement");
        String status = text(root, "status");
        StrictJson.require("ready".equals(status) || "unavailable".equals(status), "expectation status");
        StrictJson.require(root.has("unavailable_reason"), "expectation reason must be present, explicit null is distinct from missing");
        return new Expectation(requiredText(root, "event_definition_key"), integer(root, "selected_option_number"),
            requiredInteger(root, "selected_native_option_index"), Metric.fromWire(requiredText(root, "metric")),
            Relation.fromWire(requiredText(root, "expected_relation")), "ready".equals(status) ? ExpectationStatus.READY : ExpectationStatus.UNAVAILABLE,
            text(root, "starting_snapshot_id"), integer(root, "starting_revision"), integer(root, "character_id"),
            integer(root, "starting_value"), text(root, "unavailable_reason"));
    }

    public static Selection decodeSelection(byte[] raw) {
        JsonNode node = nullableObject(StrictJson.parse(raw));
        if (node == null) return null;
        return new Selection(bool(node, "postcondition_verified"), text(node, "starting_snapshot_id"), integer(node, "starting_revision"),
            text(node, "ending_snapshot_id"), integer(node, "ending_revision"),
            observations(node, Metric.STRESS), observations(node, Metric.GOLD), observations(node, Metric.PRESTIGE));
    }

    public static byte[] encode(Expectation expectation) { return StrictJson.canonical(expectationNode(expectation)); }
    public static byte[] encode(Optional<Expectation> expectation) {
        return expectation.isPresent() ? encode(expectation.orElseThrow()) : new byte[] {'n', 'u', 'l', 'l'};
    }
    public static byte[] encode(Evaluation evaluation) {
        ObjectNode node = baseNode(evaluation.expectation());
        String status = switch (evaluation.status()) {
            case UNAVAILABLE -> "unavailable"; case FAILED -> "failed";
            case VERIFIED_CHANGE -> "verified_change"; case VERIFIED_NO_CHANGE -> "verified_no_change";
        };
        node.put("status", status).put("relation_satisfied", evaluation.relationSatisfied())
            .put("material_change_observed", evaluation.materialChangeObserved()).put("ending_value", evaluation.endingValue())
            .put("delta", evaluation.delta()).put("unavailable_reason", evaluation.unavailableReason());
        return StrictJson.canonical(node);
    }
    public static byte[] encodeSelection(Selection selection) {
        if (selection == null) return new byte[] {'n', 'u', 'l', 'l'};
        ObjectNode root = StrictJson.object().put("postcondition_verified", selection.postconditionVerified())
            .put("starting_snapshot_id", selection.startingSnapshotId()).put("starting_revision", selection.startingRevision())
            .put("ending_snapshot_id", selection.endingSnapshotId()).put("ending_revision", selection.endingRevision());
        observationsNode(root, Metric.STRESS, selection.stress());
        observationsNode(root, Metric.GOLD, selection.gold());
        observationsNode(root, Metric.PRESTIGE, selection.prestige());
        return StrictJson.canonical(root);
    }

    private static Decision decision(JsonNode node) {
        if (node == null) return null;
        JsonNode rawProfile = nullableObject(node.get("choice_effect_profile"));
        EffectProfile profile = null;
        if (rawProfile != null) {
            JsonNode specification = nullableObject(rawProfile.get("observable_postcondition"));
            profile = new EffectProfile(text(rawProfile, "schema"), integer(rawProfile, "schema_version"),
                integer(rawProfile, "selected_native_option_index"), text(specification, "metric"),
                text(specification, "expected_relation"), bool(specification, "material_change_required_for_evidence"));
        }
        return new Decision(text(node, "status"), text(node, "event_definition_key"), text(node, "ck3_build"),
            integer(node, "selected_option_number"), integer(node, "selected_native_option_index"), profile);
    }
    private static Resource resource(JsonNode node) {
        return node == null ? null : new Resource(integer(node, "raw"), integer(node, "scale"));
    }
    private static ObservationPair observations(JsonNode node, Metric metric) {
        return new ObservationPair(observation(node.get("starting_played_character_" + metric.noun()), metric),
            observation(node.get("ending_played_character_" + metric.noun()), metric));
    }
    private static Observation observation(JsonNode node, Metric metric) {
        node = nullableObject(node);
        return node == null ? null : new Observation(text(node, "status"), integer(node, "character_id"), integer(node, metric.valueField()), integer(node, "scale"));
    }
    private static void observationsNode(ObjectNode root, Metric metric, ObservationPair pair) {
        if (pair == null) return;
        observationNode(root, "starting_played_character_" + metric.noun(), metric, pair.before());
        observationNode(root, "ending_played_character_" + metric.noun(), metric, pair.after());
    }
    private static void observationNode(ObjectNode root, String field, Metric metric, Observation observation) {
        if (observation == null) { root.putNull(field); return; }
        root.putObject(field).put("status", observation.status()).put("character_id", observation.characterId())
            .put(metric.valueField(), observation.value()).put("scale", observation.scale());
    }
    private static void resourceNode(ObjectNode root, String name, Resource resource) {
        if (resource == null) root.putNull(name);
        else root.putObject(name).put("raw", resource.raw()).put("scale", resource.scale());
    }
    private static ObjectNode expectationNode(Expectation expectation) {
        return baseNode(expectation).put("status", expectation.status() == ExpectationStatus.READY ? "ready" : "unavailable")
            .put("unavailable_reason", expectation.unavailableReason());
    }
    private static ObjectNode baseNode(Expectation expectation) {
        return StrictJson.object().put("schema", ScalarEventOutcome.SCHEMA).put("schema_version", 1)
            .put("event_definition_key", expectation.eventDefinitionKey()).put("selected_option_number", expectation.selectedOptionNumber())
            .put("selected_native_option_index", expectation.selectedNativeOptionIndex()).put("metric", expectation.metric().wire())
            .put("expected_relation", expectation.relation().wire()).put("material_change_required_for_evidence", true)
            .put("starting_snapshot_id", expectation.startingSnapshotId()).put("starting_revision", expectation.startingRevision())
            .put("character_id", expectation.characterId()).put("starting_value", expectation.startingValue());
    }
    private static JsonNode nullableObject(JsonNode node) {
        if (node == null || node.isNull()) return null;
        StrictJson.require(node.isObject(), "object or explicit null required");
        return node;
    }
    private static String text(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        if (value == null || value.isNull()) return null;
        StrictJson.require(value.isTextual(), "string token required: " + field);
        String result = value.textValue();
        if (!result.isEmpty()) StrictJson.text(result);
        return result;
    }
    private static String requiredText(JsonNode node, String field) {
        String value = text(node, field);
        StrictJson.require(value != null && !value.isEmpty(), "required text: " + field);
        return value;
    }
    private static BigInteger integer(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        if (value == null || value.isNull()) return null;
        StrictJson.require(value.isIntegralNumber(), "integer token required, no bool/float/string: " + field);
        return value.bigIntegerValue();
    }
    private static BigInteger requiredInteger(JsonNode node, String field) {
        BigInteger value = integer(node, field);
        StrictJson.require(value != null, "required integer: " + field);
        return value;
    }
    private static Boolean bool(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        if (value == null || value.isNull()) return null;
        StrictJson.require(value.isBoolean(), "boolean token required: " + field);
        return value.booleanValue();
    }
}
