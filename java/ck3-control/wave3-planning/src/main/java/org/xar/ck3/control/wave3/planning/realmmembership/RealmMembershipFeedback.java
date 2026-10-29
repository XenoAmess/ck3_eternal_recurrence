package org.xar.ck3.control.wave3.planning.realmmembership;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.io.IOException;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsCodec;
import org.xar.ck3.control.wave2.finance.factionalerts.NativeBuildIdentityCodec;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmObservation;
import org.xar.ck3.control.wave2.planning.realmcompare.SubrealmCounties;
import org.xar.ck3.control.wave2.planning.scoreinputs.ScoreInputFrame;
import org.xar.ck3.control.wave2.planning.scoreinputs.ScoreInputFrameAssessment;
import org.xar.ck3.control.wave2.planning.scoreinputs.UnknownScoreMetric;

/** Whole existing-query feedback producer. It never performs an observation, retry, SAVE or action. */
public final class RealmMembershipFeedback {
    public static final int MAX_BYTES = 1_048_576;
    public static final String SCHEMA = "xar.ck3.realm-membership-feedback/v1";
    private static final ObjectMapper WRITER = new ObjectMapper();
    private RealmMembershipFeedback() { }

    public sealed interface Result permits VerifiedFeedback, Unavailable { byte[] wireJson(); }

    /** Only the complete source factory below can create this value; it is not native transport qualification. */
    public static final class VerifiedFeedback implements Result {
        private final RealmObservation observation; private final RealmDifference difference; private final byte[] wire;
        private VerifiedFeedback(RealmObservation observation, RealmDifference difference, byte[] wire) {
            this.observation = observation; this.difference = difference; this.wire = wire.clone();
        }
        public RealmObservation observation() { return observation; }
        public RealmDifference difference() { return difference; }
        /** Normalized feedback, never original native packet bytes. */
        @Override public byte[] wireJson() { return wire.clone(); }
        public int realmCountyCount() { return observation.component().countyTitleIds().size(); }
    }
    public static final class Unavailable implements Result {
        private final String reason; private final byte[] wire;
        private Unavailable(String reason) { this.reason = reason; this.wire = encodeFeedback(unavailableWire(reason)); }
        public String reason() { return reason; }
        @Override public byte[] wireJson() { return wire.clone(); }
    }

    /** Typed transport request; only the exact raw boundary can construct it. */
    public static final class Request {
        private final ObjectNode snapshot;
        private final JsonNode factionResult;
        private final JsonNode source;
        private final JsonNode previous;
        private Request(ObjectNode snapshot, JsonNode factionResult, JsonNode source, JsonNode previous) {
            this.snapshot = snapshot.deepCopy(); this.factionResult = factionResult.deepCopy();
            this.source = source.deepCopy(); this.previous = previous.deepCopy();
        }
    }

    /** Exact wrapper; the three optional legacy arguments preserve None/missing equivalence. */
    public static Request decodeRequest(byte[] rawRequest) {
        JsonNode parsed = StrictJson.parse(rawRequest, MAX_BYTES);
        StrictJson.require(parsed instanceof ObjectNode, "realm feedback request object required"); ObjectNode request = (ObjectNode) parsed;
        Set<String> allowed = Set.of("snapshot", "source_frame", "faction_result", "previous");
        StrictJson.require(request.has("snapshot"), "original snapshot required");
        request.fieldNames().forEachRemaining(field -> StrictJson.require(allowed.contains(field), "unknown realm feedback request field"));
        StrictJson.require(request.get("snapshot") instanceof ObjectNode, "original snapshot object required");
        return new Request((ObjectNode) request.get("snapshot"), orNull(request.get("faction_result")),
                orNull(request.get("source_frame")), orNull(request.get("previous")));
    }
    public static Result projectRequest(Request request) {
        StrictJson.require(request != null, "typed complete realm feedback request required");
        return project(request.snapshot, request.factionResult, request.source, request.previous);
    }
    public static Result project(byte[] rawRequest) { return projectRequest(decodeRequest(rawRequest)); }

    /** Boundary-only nodes are immediately assessed and converted to the shared immutable observation. */
    private static Result project(ObjectNode snapshot, JsonNode factionResult, JsonNode source, JsonNode previous) {
        if (factionResult.isNull()) return new Unavailable("existing_faction_DTO_not_obtained");
        ScoreInputFrameAssessment assessment = ScoreInputFrameAssessment.assess(snapshot, source);
        if (assessment instanceof ScoreInputFrameAssessment.Rejected rejected) return new Unavailable(rejected.reason());
        try {
            ScoreInputFrame frame = ((ScoreInputFrameAssessment.Matched) assessment).source();
            ObjectNode sourceFrame = (ObjectNode) source;
            if (frame.revision().signum() < 0 || frame.actorCharacterId().signum() < 1
                    || frame.snapshotId().isEmpty() || frame.episodeRunId().isEmpty()) throw refusal("current_source_frame_incomplete");
            if (!(factionResult instanceof ObjectNode result)) throw refusal("faction_result_missing");
            JsonNode binding = result.get("binding"); boolean mappingBinding = binding instanceof ObjectNode;
            if (binding != null && !binding.isNull() && !mappingBinding) throw refusal("faction_result_binding_invalid");
            if (mappingBinding) {
                for (String field : new String[] {"snapshot_id", "revision", "native_revision", "date_raw"}) {
                    if (!same((ObjectNode) binding, field, sourceFrame.get(field))) throw refusal("faction_result_binding_changed");
                }
                if (!same((ObjectNode) binding, "expected_revision", sourceFrame.get("revision"))) throw refusal("faction_result_expected_revision_changed");
            } else {
                if (!text(result.get("step"), FactionAlertModel.STEP) || !actualTrue(result.get("accepted"))
                        || !same(result, "snapshot_revision", sourceFrame.get("native_revision"))) throw refusal("faction_original_queried_frame_changed");
                for (String field : new String[] {"snapshot_id", "revision", "native_revision"}) {
                    if (!same(result, "queried_" + field, sourceFrame.get(field))) throw refusal("faction_original_queried_frame_changed");
                }
            }
            JsonNode sequenceNode = result.get("query_sequence");
            if (sequenceNode == null || !sequenceNode.isIntegralNumber() || sequenceNode.bigIntegerValue().signum() < 1) throw refusal("faction_original_query_sequence_unavailable");
            BigInteger sequence = StrictJson.integer(sequenceNode, BigInteger.ONE, StrictJson.UINT64_MAX);
            FactionAlertModel.Build build = NativeBuildIdentityCodec.fromSemanticSnapshot(snapshot);
            JsonNode rawAlert = result.get("player_faction_alerts");
            if (rawAlert == null) throw refusal("player faction alerts must contain exactly the v1 fields");
            // Reuse the original component's already migrated source validator for its public failure contract.
            if (rawAlert instanceof ObjectNode alert && alert.has(SubrealmCounties.COMPONENT)) {
                JsonNode alertActor = alert.get("player_character_id");
                if (alertActor != null && alertActor.isIntegralNumber() && alertActor.bigIntegerValue().signum() > 0
                        && alertActor.bigIntegerValue().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0) {
                    try {
                        SubrealmCounties.parse(alert.get(SubrealmCounties.COMPONENT), alertActor.intValue(), frame.nativeRevision(), frame.dateRaw());
                    } catch (IllegalArgumentException error) {
                        throw refusal(error.getMessage() == null ? "realm_membership_feedback_invalid" : error.getMessage());
                    }
                }
            }
            FactionAlertsCodec.Normalized normalized = FactionAlertsCodec.normalize(StrictJson.canonical(rawAlert, MAX_BYTES),
                    new FactionAlertModel.ExpectedFrame(frame.dateRaw(), frame.nativeRevision(), Optional.of(build)));
            JsonNode normalizedAlert = StrictJson.parse(normalized.json(), MAX_BYTES);
            if (binding == null || binding.isNull()) {
                if (!same(result, "status", normalizedAlert.get("status"))
                        || !same(result, "player_faction_alerts_ready", normalizedAlert.path("readiness").get("alert_ready"))) {
                    throw refusal("faction_original_envelope_disagrees");
                }
            }
            if (!(normalized.frame() instanceof FactionAlertModel.Available available)
                    || available.subrealmCounties().isEmpty()
                    || !(available.subrealmCounties().orElseThrow() instanceof FactionAlertModel.CompleteCounties)) {
                throw refusal("complete_subrealm_county_component_unavailable");
            }
            JsonNode component = normalizedAlert.get(SubrealmCounties.COMPONENT);
            if (!component.get("actor_character_id").bigIntegerValue().equals(frame.actorCharacterId())) throw refusal("subrealm_county_owner_changed");
            ObjectNode observationWire = StrictJson.object(); observationWire.put("schema", RealmObservation.SCHEMA);
            observationWire.put("status", "available"); observationWire.put("scope", SubrealmCounties.SCOPE);
            observationWire.set("component", component.deepCopy()); observationWire.set("source_frame", sourceFrame.deepCopy());
            observationWire.put("query_sequence", sequence); observationWire.set("provenance", normalizedAlert.get("provenance").deepCopy());
            RealmObservation observation = RealmObservation.parse(observationWire);
            RealmDifference difference = RealmDifference.compareObservation(previous, observation);
            ObjectNode output = base(); output.put("status", "available"); output.set("observation", observationWire);
            output.set("difference", difference.toJson()); output.putNull("unavailable_reason");
            ObjectNode metric = StrictJson.object(); metric.put("value", Integer.toString(observation.component().countyTitleIds().size()));
            metric.put("unit", "county"); metric.put("availability", "observed"); metric.put("scope", SubrealmCounties.SCOPE);
            metric.put("source_ref", "existing_player_faction_alerts"); metric.put("locator", SubrealmCounties.COMPONENT);
            ObjectNode metrics = StrictJson.object(); metrics.set("realm_county_count", metric); output.set("raw_metrics", metrics);
            return new VerifiedFeedback(observation, difference, encodeFeedback(output));
        } catch (ContractViolationException | ProjectionDomainRejection error) {
            return new Unavailable(truncate(error.getMessage() == null ? "realm_membership_feedback_invalid" : error.getMessage()));
        }
    }
    private static ObjectNode unavailableWire(String reason) {
        ObjectNode root = base(); root.put("status", "unavailable"); root.put("unavailable_reason", reason);
        ObjectNode metrics = StrictJson.object(); metrics.set("realm_county_count", new UnknownScoreMetric(UnknownScoreMetric.nameFromWire("realm_county_count"), reason).toJson());
        root.set("raw_metrics", metrics); return root;
    }
    private static ObjectNode base() {
        ObjectNode root = StrictJson.object(); root.put("schema", SCHEMA); root.putNull("observation"); root.putNull("difference");
        root.put("new_RPC_calls", 0); root.put("new_SAVE_exports", 0); root.put("same_native_capture_with_MET", false); root.putNull("native_capture_epoch"); return root;
    }
    private static boolean same(ObjectNode object, String field, JsonNode expected) {
        JsonNode value = object.get(field); return value != null && expected != null && value.equals(expected);
    }
    private static boolean text(JsonNode node, String value) { return node != null && node.isTextual() && node.textValue().equals(value); }
    private static boolean actualTrue(JsonNode node) { return node != null && node.isBoolean() && node.booleanValue(); }
    private static JsonNode orNull(JsonNode node) { return node == null ? NullNode.instance : node; }
    private static String truncate(String value) {
        int end = value.offsetByCodePoints(0, Math.min(256, value.codePointCount(0, value.length()))); return value.substring(0, end);
    }
    private static ProjectionDomainRejection refusal(String reason) { return new ProjectionDomainRejection(reason); }
    /** SDK frame extensions retain their JSON number domain; integer-only map canonicalization is not applied to them. */
    private static byte[] encodeFeedback(JsonNode node) {
        try {
            byte[] json = WRITER.writeValueAsBytes(stable(node));
            StrictJson.require(json.length <= MAX_BYTES, "realm feedback JSON byte budget"); return json;
        } catch (IOException error) { throw new IllegalStateException("realm feedback encoding failed", error); }
    }
    private static JsonNode stable(JsonNode node) {
        if (node.isObject()) {
            ObjectNode result = StrictJson.object(); TreeSet<String> names = new TreeSet<>(); node.fieldNames().forEachRemaining(names::add);
            for (String name : names) result.set(name, stable(node.get(name))); return result;
        }
        if (node.isArray()) { ArrayNode result = WRITER.createArrayNode(); for (JsonNode value : node) result.add(stable(value)); return result; }
        if (node.isFloatingPointNumber() && node.decimalValue().scale() == 0) return new DecimalNode(node.decimalValue().setScale(1));
        return node;
    }
}

