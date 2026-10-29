package org.xar.ck3.control.wave3.governance.marriagenotice;

import static org.xar.ck3.control.wave3.governance.marriagenotice.MarriageNoticeModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalCodec;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.ArrayValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.BooleanValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.IntegerValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.NullValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.ObjectValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.TextValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.WireValue;

/** Exact new envelopes and declared old-container projection; no loaded-source verification is claimed. */
public final class MarriageNoticeCodec {
    public static final String REVIEW_SCHEMA = "xar.ck3.marriage-notice-review-request.v1";
    public static final String CONTINUE_SCHEMA = "xar.ck3.marriage-notice-continue-request.v1";
    private MarriageNoticeCodec() { }

    public static ReviewInput decodeReview(byte[] raw) {
        ObjectNode root = StrictJson.object(BetrothalCodec.readJson(raw), Set.of("schema", "context", "historical_evidence"));
        require(REVIEW_SCHEMA.equals(text(root.get("schema"))), "marriage notice review schema");
        return new ReviewInput(context(root.get("context")), wire(root.get("historical_evidence")));
    }

    public static ContinueInput decodeContinue(byte[] raw) {
        ObjectNode root = StrictJson.object(BetrothalCodec.readJson(raw), Set.of("schema", "plan", "snapshot", "action_steps"));
        require(CONTINUE_SCHEMA.equals(text(root.get("schema"))), "marriage notice continuation schema");
        return new ContinueInput(plan(root.get("plan")), snapshot(root.get("snapshot")), strings(root.get("action_steps")));
    }

    public static Plan decodePlan(byte[] raw) { return plan(BetrothalCodec.readJson(raw)); }
    public static byte[] encodeReview(ReviewResult result) { return BetrothalCodec.encodeEvidence(reviewValue(result)); }
    public static byte[] encodeContinuation(ContinuationResult result) { return BetrothalCodec.encodeEvidence(continuationValue(result)); }
    public static byte[] encodeProjection(OrdinaryProjection projection) {
        return BetrothalCodec.encodeEvidence(new ObjectValue(Map.of("snapshot", projection.snapshot(), "action_steps", textArray(projection.actionSteps()), "scope", t("planning_only"))));
    }

    public static WireValue reviewValue(ReviewResult result) {
        if (result instanceof UnchangedEvidence unchanged) { return unchanged.evidence(); }
        ReviewedEvidence reviewed = (ReviewedEvidence) result;
        Map<String, WireValue> value = new HashMap<>(reviewed.historicalEvidence().values());
        WireValue previousSha = value.getOrDefault("source_sha256", NullValue.INSTANCE);
        value.put("source_sha256", t(MarriageNoticePolicy.SOURCE_SHA256)); value.put("source_policy", t(MarriageNoticePolicy.SOURCE_POLICY));
        value.put("build", new ObjectValue(Map.of("version", t(MarriageNoticePolicy.VERSION), "exe_sha256", t(MarriageNoticePolicy.EXECUTABLE_SHA256))));
        value.put("native_backend_id", t(MarriageNoticePolicy.BACKEND_ID));
        Map<String, WireValue> knowledge = new HashMap<>();
        knowledge.put("schema", t("xar.arrange-marriage-reject-only-source-review/v1")); knowledge.put("status", t("offline-source-reviewed")); knowledge.put("action_scope", t("existing_reject_only"));
        knowledge.put("canonical_key", t(MarriageNoticePolicy.KEY)); knowledge.put("deterministic_key_hash", new IntegerValue(MarriageNoticePolicy.KEY_HASH));
        knowledge.put("source_relative", t("common/character_interactions/00_marriage_interactions.txt")); knowledge.put("source_sha256", t(MarriageNoticePolicy.SOURCE_SHA256));
        knowledge.put("definition_sha256", t("5927c5d4e719bb04a645d47c4e79544bf3e72f76be5c60e8bd6ad5ad59b0301a"));
        knowledge.put("on_decline_sha256", t("8390846f7a5c14848079abcd079d2fca1d801214011e80da44786d4788c1ace1"));
        knowledge.put("send_option_count", new IntegerValue(BigInteger.valueOf(6))); knowledge.put("send_option_catalogue_sha256", t("c462de92849c534ab85391b020e288470de75a1b65693a313051493827ae5731"));
        knowledge.put("decline_event_source", t("events/interaction_events/marriage_interaction_events.txt")); knowledge.put("decline_event_source_sha256", t("78c367ba0b32a374e5be5d88f7660e7898ef9dbc44412049521f64a472e4dca5"));
        knowledge.put("decline_event_definition_sha256", t("6f21ff04501d9ba75caf19e1274b772749e1fd00d748fd29a610feb08029e86f")); knowledge.put("historical_source_sha256", previousSha);
        knowledge.put("loaded_definition_bytes_verified", new BooleanValue(false)); knowledge.put("accept_outcome_qualified", new BooleanValue(false)); knowledge.put("material_effects_verified", new BooleanValue(false));
        value.put("source_knowledge", new ObjectValue(knowledge)); value.put("known_decline_effects", textArray(List.of(
                "puppet_or_actor!=recipient:marriage_interaction.0011", "puppet_or_actor:if_grand_wedding_promise_pending:remove_variable", "secondary_actor:player_declined_marriage:5y")));
        return new ObjectValue(value);
    }

    public static ObjectValue continuationValue(ContinuationResult result) {
        if (result instanceof UnchangedPlan unchanged) { return unchanged.plan().original(); }
        ContinuedPlan continued = (ContinuedPlan) result;
        Map<String, WireValue> value = new HashMap<>(continued.ordinaryPlan().original().values());
        value.put("deferred_pending_interaction", continued.deferredDiagnosis().original());
        value.put("notification_continuation", new ObjectValue(Map.of("policy", t("blocked-marriage-reply-ordinary-continuation-v1"),
                "pending_interaction_id", new IntegerValue(continued.pendingInteractionId()), "interaction_submission", new BooleanValue(false),
                "observed_notification_cleared", new BooleanValue(false), "planning_projection_only", new BooleanValue(true))));
        return new ObjectValue(value);
    }

    private static SourceContext context(JsonNode node) {
        if (!(node instanceof ObjectNode object)) { return new UnknownContext(wire(node)); }
        JsonNode build = object.get("build"), definition = object.get("definition"), provenance = object.get("provenance");
        if (build != null && !build.isObject() || definition != null && !definition.isObject() || provenance != null && !provenance.isObject()) { return new UnknownContext(wire(node)); }
        return new ContextFacts(nullableText(child(build, "version")), nullableText(child(build, "exe_sha256")), nullableText(child(definition, "canonical_key")),
                nullableInteger(child(definition, "deterministic_key_hash")), nullableText(child(provenance, "backend_id")));
    }

    private static Plan plan(JsonNode node) {
        ObjectNode object = object(node); JsonNode decisionNode = object.get("decision"); Decision decision = null;
        if (decisionNode instanceof ObjectNode decisionObject) {
            String classification = nullableText(decisionObject.get("classification"));
            Classification kind = "known_marriage_special".equals(classification) ? Classification.KNOWN_MARRIAGE_SPECIAL
                    : "evidence_invalid".equals(classification) ? Classification.EVIDENCE_INVALID : Classification.OTHER;
            JsonNode definition = decisionObject.get("definition_classification");
            decision = new Decision(kind, nullableText(decisionObject.get("interaction_key")), nullableStrings(decisionObject.get("marriage_contract_gaps")),
                    definition instanceof ObjectNode def ? nullableText(def.get("definition_key")) : null, nullableInteger(decisionObject.get("pending_interaction_id")));
        }
        return new Plan((ObjectValue) wire(node), nullableText(object.get("selected_step")), nullableText(object.get("phase")), decision);
    }

    private static SnapshotView snapshot(JsonNode node) {
        if (!(node instanceof ObjectNode object)) { return new SnapshotView(wire(node), null, false, false, false); }
        JsonNode pendingNode = object.get("pending_character_interaction"), modal = object.get("top_exclusive_modal_choice_hint"); PendingInteraction pending = null;
        if (pendingNode instanceof ObjectNode pendingObject) { pending = new PendingInteraction(integer(pendingObject.get("instance_id")), nullableBoolean(pendingObject.get("auto_accept_notification"))); }
        boolean present = modal instanceof ObjectNode && "present".equals(nullableText(modal.get("status")));
        return new SnapshotView(wire(node), pending, present, nonnull(object.get("active_event")), nonnull(object.get("current_event")));
    }

    private static JsonNode child(JsonNode parent, String key) { return parent == null ? null : parent.get(key); }
    private static boolean nonnull(JsonNode node) { return node != null && !node.isNull(); }
    private static WireValue wire(JsonNode node) { return node == null ? NullValue.INSTANCE : BetrothalCodec.projectEvidence(node); }
    private static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "object required"); return (ObjectNode) node; }
    private static String text(JsonNode node) { require(node != null && node.isTextual(), "string required"); String text = node.textValue(); if (!text.isEmpty()) { StrictJson.text(text); } return text; }
    private static String nullableText(JsonNode node) { return node == null || node.isNull() ? null : text(node); }
    private static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "exact integer required; no bool/float/string"); return node.bigIntegerValue(); }
    private static BigInteger nullableInteger(JsonNode node) { return node == null || node.isNull() ? null : integer(node); }
    private static Boolean nullableBoolean(JsonNode node) { if (node == null || node.isNull()) { return null; } require(node.isBoolean(), "boolean required"); return node.booleanValue(); }
    private static List<String> strings(JsonNode node) { require(node != null && node.isArray(), "string array required"); List<String> result = new ArrayList<>(); node.forEach(value -> result.add(text(value))); return List.copyOf(result); }
    private static List<String> nullableStrings(JsonNode node) { return node == null || node.isNull() ? null : strings(node); }
    private static TextValue t(String value) { return new TextValue(value); }
    private static ArrayValue textArray(List<String> values) { return new ArrayValue(values.stream().<WireValue>map(MarriageNoticeCodec::t).toList()); }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
