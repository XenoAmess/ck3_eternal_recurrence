package org.xar.ck3.control.wave2.development.constructionintent;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Data-only adapters for the existing service selected-receipt and planner consumed-receipt hooks.
 * The caller still owns ledger/process/frame qualification. No method grants transition eligibility.
 */
public final class ConstructionIntentConsumers {
    private static final ObjectMapper OUTPUT = new ObjectMapper();
    private ConstructionIntentConsumers() { }

    /** Original bytes and their hash remain available; enriched JSON is explicitly a projection. */
    public record EnrichedJson(byte[] originalUtf8, String originalSha256, byte[] enrichedUtf8) {
        public EnrichedJson {
            originalUtf8 = Objects.requireNonNull(originalUtf8).clone();
            Objects.requireNonNull(originalSha256);
            StrictJson.require(originalSha256.equals(sha256(originalUtf8)), "original construction JSON digest differs");
            enrichedUtf8 = Objects.requireNonNull(enrichedUtf8).clone();
        }
        @Override public byte[] originalUtf8() { return originalUtf8.clone(); }
        @Override public byte[] enrichedUtf8() { return enrichedUtf8.clone(); }
        public boolean projectionNotOriginal() { return true; }
    }

    /** bridge/service.py selected receipt hook, after the original read-only query has returned. */
    public static EnrichedJson selectedReceipt(byte[] originalPlanUtf8, byte[] originalResultUtf8) {
        ObjectNode plan = ConstructionIntentJson.object(StrictJson.parse(originalPlanUtf8));
        ObjectNode result = ConstructionIntentJson.object(StrictJson.parse(originalResultUtf8));
        String step = ConstructionIntentJson.nullableText(plan.get("selected_step"));
        StrictJson.require(ConstructionIntentContinuity.RECEIPT_STEP.equals(step),
                "selected receipt hook requires the original receipt step");
        StrictJson.require(plan.hasNonNull("construction_pending_action"), "selected receipt lacks original pending");
        var projection = ConstructionIntentContinuity.projectSelected(step,
                ConstructionIntentJson.identity(plan.get("construction_pending_action")),
                ConstructionIntentJson.result(result),
                ConstructionIntentJson.nullableText(plan.get("construction_deferred_selected_step")));
        ObjectNode enriched = result.deepCopy();
        enriched.set("construction_selected_intent", ConstructionIntentJson.tree(projection));
        return enriched(originalResultUtf8, enriched);
    }

    /**
     * Both construction_formal_consumer planner hooks and the ordinary service display hook.
     * Pass the receipt actually selected by the old planner, after its original guards have run.
     */
    public static EnrichedJson consumedReceipt(byte[] originalPlanUtf8, byte[] originalReceiptUtf8) {
        ObjectNode plan = ConstructionIntentJson.object(StrictJson.parse(originalPlanUtf8));
        ObjectNode receipt = ConstructionIntentJson.object(StrictJson.parse(originalReceiptUtf8));
        ObjectNode enriched = plan.deepCopy();
        enriched.set("construction_receipt_consumed", receipt.deepCopy());
        enriched.set("construction_consumed_intent", ConstructionIntentJson.tree(
                ConstructionIntentContinuity.projectConsumed(ConstructionIntentJson.result(receipt))));
        return enriched(originalPlanUtf8, enriched);
    }

    /** The cold-readback classifier's intent-only invariant; its native/frame/source checks stay separate. */
    public static void requireColdReadbackIntent(byte[] intentUtf8, byte[] pendingUtf8, String selectedStep) {
        StrictJson.require(ConstructionIntentContinuity.RECEIPT_STEP.equals(selectedStep), "cold intent step mismatch");
        ObjectNode intent = ConstructionIntentJson.object(StrictJson.parse(intentUtf8));
        ObjectNode pending = ConstructionIntentJson.object(StrictJson.parse(pendingUtf8));
        var identity = ConstructionIntentJson.identity(pending);
        StrictJson.require(identity.actionRequestId() != null && identity.episodeRunId() != null
                && identity.actorCharacterId() != null && identity.candidate().complete(),
                "cold intent requires complete original identity");
        var expectedResult = new ConstructionIntentContinuity.ProducerResult(identity, "applied",
                ConstructionIntentContinuity.Evidence.TRUE, ConstructionIntentContinuity.Evidence.UNKNOWN,
                ConstructionIntentContinuity.Evidence.UNKNOWN, null, true);
        ObjectNode expected = ConstructionIntentJson.tree(ConstructionIntentContinuity.projectSelected(
                selectedStep, identity, expectedResult, null));
        for (String field : new String[]{"schema", "source_role", "selected_step", "original_action",
                "observed_action", "action_identity_matches", "actor_identity_matches", "candidate_identity_matches",
                "selected_query_performed_new_submission", "observed_material_candidate", "intent_outcome"}) {
            StrictJson.require(Objects.equals(expected.get(field), intent.get(field)),
                    "cold readback intent differs: " + field);
        }
    }

    private static EnrichedJson enriched(byte[] original, ObjectNode value) {
        try {
            byte[] raw = OUTPUT.writeValueAsBytes(value);
            StrictJson.require(raw.length <= ConstructionIntentJson.MAX_INPUT_BYTES,
                    "enriched construction projection exceeds byte budget");
            return new EnrichedJson(original, sha256(original), raw);
        } catch (JsonProcessingException error) {
            throw new ContractViolationException("cannot serialize construction projection", error);
        }
    }

    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 unavailable", error); }
    }
}
