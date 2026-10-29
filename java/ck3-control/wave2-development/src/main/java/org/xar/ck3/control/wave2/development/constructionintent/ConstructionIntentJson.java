package org.xar.ck3.control.wave2.development.constructionintent;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.ConstructionInputValidation;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.CandidateIds;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.ConsumedProjection;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.Evidence;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.Identity;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.ProducerResult;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.ResultFields;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.SelectedProjection;

/** Strict new wrapper, declared projection of extensible legacy producer containers. */
public final class ConstructionIntentJson {
    public static final String REQUEST_SCHEMA = "xar.ck3.construction-intent-java-request/v1";
    public static final int MAX_INPUT_BYTES = 65_536;
    private ConstructionIntentJson() { }

    public static byte[] project(byte[] raw) {
        ObjectNode request = object(StrictJson.parse(raw, MAX_INPUT_BYTES));
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(request.get("schema"))), "request schema mismatch");
        String operation = StrictJson.text(request.get("operation"));
        if ("selected".equals(operation)) {
            ConstructionInputValidation.read(() -> StrictJson.object(request, Set.of("schema", "operation", "selected_step", "pending_action",
                    "typed_result", "deferred_selected_step")));
            return encode(ConstructionIntentContinuity.projectSelected(nullableText(request.get("selected_step")),
                    identity(request.get("pending_action")), result(request.get("typed_result")),
                    nullableText(request.get("deferred_selected_step"))));
        }
        StrictJson.require("consumed".equals(operation), "unknown construction intent operation");
        StrictJson.object(request, Set.of("schema", "operation", "receipt"));
        return encode(ConstructionIntentContinuity.projectConsumed(result(request.get("receipt"))));
    }

    public static Identity identity(JsonNode raw) {
        ObjectNode row = nullableObject(raw);
        if (row == null) { return Identity.unknown(); }
        CandidateIds candidate = candidate(row.get("candidate"));
        return new Identity(nullableText(row.get("action_request_id")), nullableText(row.get("episode_run_id")),
                nullableInteger(row.get("actor_character_id")),
                candidate == null ? CandidateIds.unknown() : candidate);
    }

    public static ProducerResult result(JsonNode raw) {
        ObjectNode row = nullableObject(raw);
        if (row == null) {
            return new ProducerResult(Identity.unknown(), null, Evidence.UNKNOWN, Evidence.UNKNOWN,
                    Evidence.UNKNOWN, null, false);
        }
        return new ProducerResult(identity(row), nullableText(row.get("status")),
                evidence(row.get("postcondition_verified")), evidence(row.get("requested_postcondition_verified")),
                evidence(row.get("material_postcondition_verified")), candidate(row.get("observed_material_tuple")),
                row.get("candidate") != null && !row.get("candidate").isNull());
    }

    public static byte[] encode(SelectedProjection projection) { return StrictJson.canonical(tree(projection)); }
    public static byte[] encode(ConsumedProjection projection) { return StrictJson.canonical(tree(projection)); }

    public static ObjectNode tree(SelectedProjection projection) {
        ObjectNode out = StrictJson.object();
        out.put("schema", ConstructionIntentContinuity.SCHEMA);
        out.put("source_role", projection.sourceRole().wire());
        out.put("selected_step", projection.selectedStep());
        out.put("deferred_selected_step", projection.deferredSelectedStep());
        out.set("original_action", identityTree(projection.originalAction()));
        out.set("observed_action", identityTree(projection.observedAction()));
        put(out, "action_identity_matches", projection.actionIdentityMatches());
        put(out, "actor_identity_matches", projection.actorIdentityMatches());
        put(out, "candidate_identity_matches", projection.candidateIdentityMatches());
        put(out, "selected_query_performed_new_submission", projection.selectedQueryPerformedNewSubmission());
        fields(out, projection.result());
        return out;
    }

    public static ObjectNode tree(ConsumedProjection projection) {
        ObjectNode out = StrictJson.object();
        out.put("schema", ConstructionIntentContinuity.SCHEMA);
        out.put("source_role", ConstructionIntentContinuity.SourceRole.PREVIOUS_CONSTRUCTION_RECEIPT.wire());
        out.set("original_action", identityTree(projection.originalAction()));
        out.putNull("selected_query_performed_new_submission");
        fields(out, projection.result());
        return out;
    }

    private static void fields(ObjectNode out, ResultFields fields) {
        out.put("producer_status", fields.producerStatus());
        put(out, "producer_postcondition_verified", fields.producerPostconditionVerified());
        put(out, "producer_requested_postcondition_verified", fields.producerRequestedPostconditionVerified());
        put(out, "producer_material_postcondition_verified", fields.producerMaterialPostconditionVerified());
        put(out, "requested_construction_verified", fields.requestedConstructionVerified());
        put(out, "material_construction_verified", fields.materialConstructionVerified());
        put(out, "restoration_verified", fields.restorationVerified());
        if (fields.observedMaterialCandidate() == null) { out.putNull("observed_material_candidate"); }
        else { out.set("observed_material_candidate", candidateTree(fields.observedMaterialCandidate())); }
        out.put("intent_outcome", fields.intentOutcome().wire());
    }

    private static ObjectNode identityTree(Identity identity) {
        ObjectNode out = StrictJson.object();
        out.put("action_request_id", identity.actionRequestId());
        out.put("episode_run_id", identity.episodeRunId());
        out.put("actor_character_id", identity.actorCharacterId());
        out.set("candidate", candidateTree(identity.candidate()));
        return out;
    }

    private static ObjectNode candidateTree(CandidateIds candidate) {
        ObjectNode out = StrictJson.object();
        out.put("barony_title_id", candidate.baronyTitleId());
        out.put("province_id", candidate.provinceId());
        out.put("building_type_id", candidate.buildingTypeId());
        out.put("slot_index", candidate.slotIndex());
        return out;
    }

    private static CandidateIds candidate(JsonNode value) {
        ObjectNode row = nullableObject(value);
        return row == null ? null : new CandidateIds(nullableInteger(row.get("barony_title_id")),
                nullableInteger(row.get("province_id")), nullableInteger(row.get("building_type_id")),
                nullableInteger(row.get("slot_index")));
    }

    private static BigInteger nullableInteger(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        ConstructionInputValidation.check(() -> StrictJson.require(value.isIntegralNumber(), "exact construction identity integer required"));
        return value.bigIntegerValue();
    }

    static String nullableText(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isTextual(), "construction text must be string or null");
        return value.textValue().isEmpty() ? null : StrictJson.text(value);
    }

    private static Evidence evidence(JsonNode value) {
        if (value == null || value.isNull()) { return Evidence.UNKNOWN; }
        StrictJson.require(value.isBoolean(), "construction evidence must be boolean or null");
        return Evidence.of(value.booleanValue());
    }

    static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "construction object required");
        return (ObjectNode) value;
    }

    private static ObjectNode nullableObject(JsonNode value) {
        return value == null || value.isNull() ? null : object(value);
    }

    private static void put(ObjectNode out, String key, Evidence evidence) {
        Boolean value = evidence.nullableBoolean();
        if (value == null) { out.putNull(key); } else { out.put(key, value.booleanValue()); }
    }
}
