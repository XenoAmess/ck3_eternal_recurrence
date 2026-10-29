package org.xar.ck3.control.governance.heirpreference;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.heirpreference.HeirReproductivePreference.CandidateId;
import org.xar.ck3.control.governance.heirpreference.HeirReproductivePreference.ComparisonRow;
import org.xar.ck3.control.governance.heirpreference.HeirReproductivePreference.ObservedComparison;
import org.xar.ck3.control.governance.heirpreference.HeirReproductivePreference.PreferredChoice;

/** Strict bounded adapter; opaque SDK fields remain at this boundary only. */
public final class HeirPreferenceCodec {
    public static final int MAX_CHOICES = 5;
    public static final int MAX_ROWS = 5;
    private static final String FLOOR = "candidate_native_fertility_floor_comparison_v1";
    private static final String AGE = "candidate_native_scorer_age_branch_v1";

    private HeirPreferenceCodec() { }

    /** Input is the explicit {choices,rows} projection; output is the old producer's array. */
    public static byte[] prioritize(byte[] request) {
        ObjectNode root = StrictJson.object(StrictJson.parse(request), Set.of("choices", "rows"));
        // Validate the complete integer-only JSON domain, including unused opaque metadata.
        StrictJson.canonical(root);
        ArrayNode choices = boundedArray(root.get("choices"), MAX_CHOICES);
        ArrayNode rows = boundedArray(root.get("rows"), MAX_ROWS);
        List<CandidateId> choiceIds = new ArrayList<>(choices.size());
        List<ObjectNode> originalChoices = new ArrayList<>(choices.size());
        for (JsonNode choice : choices) {
            ObjectNode object = openObject(choice);
            choiceIds.add(candidateId(object.get("candidate_character_id")));
            originalChoices.add(object);
        }
        List<ComparisonRow> observations = new ArrayList<>(rows.size());
        Map<CandidateId, ObjectNode> originalRows = new HashMap<>();
        for (JsonNode row : rows) {
            ObjectNode object = openObject(row);
            CandidateId candidate = candidateId(object.get("candidate_character_id"));
            observations.add(new ComparisonRow(candidate, comparison(object.get(FLOOR)),
                    comparison(object.get(AGE))));
            originalRows.put(candidate, object);
        }
        ArrayNode result = JsonNodeFactory.instance.arrayNode();
        for (PreferredChoice preference : HeirReproductivePreference.prioritize(choiceIds, observations)) {
            ObjectNode choice = originalChoices.get(preference.originalOrdinal()).deepCopy();
            ObjectNode row = originalRows.get(preference.candidateId());
            ObjectNode basis = StrictJson.object();
            basis.put("source", "derived_observed_native_reproductive_comparison_preference");
            basis.put("candidate_character_id", preference.candidateId().value());
            basis.put("preference_class", preference.preferenceClass().order());
            basis.put("comparison_status", preference.preferenceClass().wireStatus());
            basis.set("floor_comparison", comparisonCopy(row, FLOOR));
            basis.set("age_comparison", preference.ageConsidered()
                    ? comparisonCopy(row, AGE) : JsonNodeFactory.instance.nullNode());
            basis.put("age_considered", preference.ageConsidered());
            choice.set(HeirReproductivePreference.BASIS, basis);
            result.add(choice);
        }
        return StrictJson.canonical(result);
    }

    private static ArrayNode boundedArray(JsonNode node, int maximum) {
        StrictJson.require(node instanceof ArrayNode, "array required");
        ArrayNode array = (ArrayNode) node;
        StrictJson.require(array.size() <= maximum, "bounded existing five-candidate projection required");
        return array;
    }

    private static ObjectNode openObject(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "SDK projection object required");
        return (ObjectNode) node;
    }

    private static CandidateId candidateId(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "exact integer candidate ID required");
        StrictJson.require(value.bigIntegerValue().signum() > 0, "positive candidate ID required");
        return new CandidateId(value.bigIntegerValue());
    }

    private static ObservedComparison comparison(JsonNode value) {
        if (value == null || value.isNull()) {
            return ObservedComparison.UNAVAILABLE;
        }
        ObjectNode object = openObject(value);
        JsonNode ready = object.get("ready");
        JsonNode passes = object.get("passes");
        nullableBoolean(ready);
        nullableBoolean(passes);
        if (ready != null && ready.isBoolean() && ready.booleanValue()
                && passes != null && passes.isBoolean()) {
            return passes.booleanValue() ? ObservedComparison.PASS : ObservedComparison.FAIL;
        }
        return ObservedComparison.UNAVAILABLE;
    }

    private static void nullableBoolean(JsonNode value) {
        StrictJson.require(value == null || value.isNull() || value.isBoolean(),
                "comparison flag must be missing, null or actual boolean");
    }

    private static JsonNode comparisonCopy(ObjectNode row, String field) {
        JsonNode value = row == null ? null : row.get(field);
        return value instanceof ObjectNode ? value.deepCopy() : JsonNodeFactory.instance.nullNode();
    }
}
