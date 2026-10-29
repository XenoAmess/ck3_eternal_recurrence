package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m0.RaiktorRawJson.*;

/** Original source-generation/current/cleanup plus stable persisted-truce composer; pure, with historical EXE scope explicit. */
public final class RaiktorExitPostwarEvidence {
    public static final String SCHEMA = "xar.ck3.raiktor_three_way_exit_postwar_evidence_provider.v1";
    public static final String PROVIDER = "raiktor-three-way-exit-postwar-evidence-provider-v1";
    private RaiktorExitPostwarEvidence() { }
    public record SourceBinding(ObjectNode authorization, String route, ObjectNode frame, ObjectNode expectations,
            RaiktorWarBoundEvidenceCodec.Frame activeFrame, ObjectNode source, ObjectNode active) {
        public SourceBinding {
            authorization = authorization.deepCopy(); frame = frame.deepCopy(); expectations = expectations.deepCopy(); source = source.deepCopy(); active = active.deepCopy();
        }
        @Override public ObjectNode authorization() { return authorization.deepCopy(); }
        @Override public ObjectNode frame() { return frame.deepCopy(); }
        @Override public ObjectNode expectations() { return expectations.deepCopy(); }
        @Override public ObjectNode source() { return source.deepCopy(); }
        @Override public ObjectNode active() { return active.deepCopy(); }
    }
    public static SourceBinding bindSource(JsonNode actionGate, JsonNode sourceCapture, String captureSha256, JsonNode activeWarBound) {
        ObjectNode authorization = RaiktorExitPostcondition.normalizeAuthorization(actionGate);
        String route = text(object(authorization.get("action"), "authorization action").get("semantic_action"), "route");
        require(Set.of("white_peace", "surrender").contains(route), "source binding requires termination authorization");
        ObjectNode frame = object(authorization.get("frame"), "authorization frame");
        ObjectNode expected = object(object(authorization.get("postcondition_plan"), "postcondition plan").get("expectations"), "frozen expectations");
        int war = positive32(expected.get("war_id"), "expected war"), attacker = positive32(expected.get("played_character_id"), "expected attacker"), defender = positive32(expected.get("opponent_character_id"), "expected defender");
        var activeFrame = new RaiktorWarBoundEvidenceCodec.Frame(war, attacker, defender, uint64(frame.get("snapshot_revision")), uint64(frame.get("native_revision")), i32(frame.get("date_raw"), "active date"));
        ObjectNode source = RaiktorWarBoundEvidenceCodec.normalizeCapture(sourceCapture, captureSha256);
        ObjectNode active = RaiktorWarBoundEvidenceCodec.normalizeGeneric(activeWarBound, activeFrame);
        require(RaiktorWarBoundEvidenceCodec.sourceIdentity(source).sameRegiments(RaiktorWarBoundEvidenceCodec.observationIdentity(active)),
                "active generations differ from exact source capture; army containers alone are not origin evidence");
        return new SourceBinding(authorization, route, frame, expected, activeFrame, source, active);
    }
    public static ObjectNode provide(JsonNode actionGate, JsonNode sourceCapture, String captureSha256, JsonNode activeWarBound,
            JsonNode postSnapshot, JsonNode cleanupResult, JsonNode truceResults) {
        SourceBinding binding = bindSource(actionGate, sourceCapture, captureSha256, activeWarBound);
        ObjectNode authorization = binding.authorization(), frame = binding.frame(), expected = binding.expectations();
        var activeFrame = binding.activeFrame(); ObjectNode source = binding.source(), active = binding.active();
        var sourceSet = RaiktorWarBoundEvidenceCodec.sourceIdentity(source); var activeSet = RaiktorWarBoundEvidenceCodec.observationIdentity(active);
        ObjectNode post = RaiktorExitPostcondition.snapshot(postSnapshot, "postwar snapshot");
        require(integer(post.get("revision"), "post public revision").compareTo(activeFrame.publicRevision()) > 0
                && integer(post.get("native_revision"), "post native revision").compareTo(activeFrame.nativeRevision()) > 0
                && integer(post.get("date_raw"), "post date").compareTo(BigInteger.valueOf(activeFrame.dateRaw())) >= 0
                && bool(post.get("paused"), "post paused") && RaiktorExitPostcondition.absent(post.get("active_event"))
                && !RaiktorExitPostcondition.warPresent(post, expected.get("war_id")) && RaiktorExitPostcondition.sameHot(post, frame), "postwar successor/session binding failed");
        ObjectNode cleanup = RaiktorWarBoundEvidenceCodec.normalizeCleanup(cleanupResult, activeFrame, uint64(post.get("revision")), uint64(post.get("native_revision")), i32(post.get("date_raw"), "post date"));
        ObjectNode cleaned = object(cleanup.get("observation"), "cleanup observation");
        require(RaiktorWarBoundEvidenceCodec.observationIdentity(cleaned).equals(activeSet), "cleanup full generations differ from frozen active set");
        ObjectNode truceExpected = object(expected.get("truce"), "truce expectations");
        BigInteger expectedDays = integer(truceExpected.get("evaluated_days"), "expected truce days"); require(expectedDays.signum() >= 0, "expected truce days negative");
        var reads = array(truceResults, "truce double reads"); require(reads.size() == 2, "exactly two persisted truce reads required");
        ObjectNode first = normalizeLegacyTruce(reads.get(0), activeFrame.defender(), uint64(post.get("native_revision")));
        ObjectNode second = normalizeLegacyTruce(reads.get(1), activeFrame.defender(), uint64(post.get("native_revision")));
        BigInteger firstSequence = positive(reads.get(0).get("query_sequence"), "first truce sequence"), secondSequence = positive(reads.get(1).get("query_sequence"), "second truce sequence");
        require(same(first, second) && secondSequence.equals(firstSequence.add(BigInteger.ONE)), "persisted truce reads must be stable and consecutive");
        boolean truceReady = text(first.get("status"), "persisted truce status").equals("available") && bool(first.get("readiness"), "persisted truce readiness")
                && same(first.get("owner_character_id"), truceExpected.get("owner_character_id")) && same(first.get("toward_character_id"), truceExpected.get("toward_character_id"))
                && same(first.get("current_date_raw"), post.get("date_raw")) && first.get("expiry_date_raw").isIntegralNumber()
                && first.get("expiry_date_raw").bigIntegerValue().equals(integer(post.get("date_raw"), "post date").add(expectedDays.multiply(BigInteger.valueOf(24))));
        Map<String,Boolean> checks = new LinkedHashMap<>();
        checks.put("source_generations_bound", sourceSet.sameRegiments(activeSet)); checks.put("old_war_absent", true);
        checks.put("source_specific_cleanup_destroyed", text(object(cleaned.get("cleanup"), "cleanup status").get("status"), "cleanup status").equals("destroyed"));
        checks.put("directional_persisted_truce_stable", truceReady);
        List<String> blockers = checks.entrySet().stream().filter(e -> !e.getValue()).map(Map.Entry::getKey).toList(); ObjectNode evidence = null;
        if (blockers.isEmpty()) {
            evidence = StrictJson.object().put("schema", RaiktorExitPostcondition.POSTWAR_SCHEMA).put("war_id", activeFrame.warId());
            evidence.set("authorization_sha256", authorization.get("authorization_sha256")); evidence.set("post_snapshot_id", post.get("snapshot_id"));
            ObjectNode loss = evidence.putObject("source_specific_loss").put("war_id", activeFrame.warId()).put("status", "destroyed")
                    .put("source_specific_attribution_ready", true).put("frozen_generation_count", activeSet.persistent().size()).put("post_termination_soldiers", 0);
            loss.set("source_set_sha256", source.get("source_set_sha256"));
            ObjectNode lossEvidence = StrictJson.object(); lossEvidence.set("source", source); lossEvidence.set("active", active); lossEvidence.set("cleanup", cleanup); loss.put("evidence_sha256", hash(lossEvidence));
            ObjectNode truce = evidence.putObject("truce").put("source", "persisted_native_truce_row").put("formula_derived", false).put("evaluated_days", expectedDays);
            truce.set("from_character_id", first.get("owner_character_id")); truce.set("to_character_id", first.get("toward_character_id"));
            truce.set("queried_at_date_raw", first.get("current_date_raw")); truce.set("expiry_date_raw", first.get("expiry_date_raw"));
            ObjectNode truceEvidence = StrictJson.object(); truceEvidence.set("first", reads.get(0)); truceEvidence.set("second", reads.get(1)); truce.put("evidence_sha256", hash(truceEvidence));
        }
        ObjectNode result = StrictJson.object().put("schema", SCHEMA).put("provider", PROVIDER).put("status", evidence == null ? "red" : "available").put("evidence_ready", evidence != null);
        if (evidence == null) result.putNull("postwar_evidence"); else result.set("postwar_evidence", evidence);
        ObjectNode checkJson = result.putObject("checks"); checks.forEach(checkJson::put); strings(result, "blockers", blockers);
        strings(result, "boundaries", List.of("source_capture_is_read_only_origin_evidence", "war_and_regiment_generations_must_match_the_source_capture",
                "active_army_containers_are_cleanup_context_not_source_identity", "command_acknowledgement_is_not_consumed_as_postwar_state",
                "this_provider_performs_no_ck3_or_filesystem_operation")); return result;
    }
    /** Original historical six-field persisted truce packet. Current .4's distinct typed codec is not aliased into this old receipt. */
    public static ObjectNode normalizeLegacyTruce(JsonNode raw, int defender, BigInteger nativeRevision) {
        require(defender > 0 && nativeRevision != null && nativeRevision.signum() > 0 && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "positive legacy truce target and native revision required");
        ObjectNode result = object(raw, "persisted truce result");
        Set<String> fields = new java.util.HashSet<>(Set.of("step", "accepted", "query_sequence", "snapshot_revision", "raiktor_actual_truce_expiry", "backend_id"));
        if (result.has("actual_truce_expiry_proof")) fields.add("actual_truce_expiry_proof"); exact(result, fields, "truce wire fields");
        require(text(result.get("step"), "truce step").equals("query-raiktor-actual-truce-expiry-v1-" + defender)
                && bool(result.get("accepted"), "truce accepted") && integer(result.get("snapshot_revision"), "truce outer revision").equals(nativeRevision), "truce original transport binding differs");
        positive(result.get("query_sequence"), "truce sequence");
        ObjectNode value = exact(result.get("raiktor_actual_truce_expiry"), Set.of("schema_version", "backend_id", "status", "snapshot_revision", "current_date_raw",
                "owner_character_id", "toward_character_id", "native_has_truce", "actual_expiry_observable", "expiry_date_raw", "same_frame_stable", "readiness",
                "temporal_semantics", "unavailable_reason"), "legacy actual truce payload");
        number(value.get("schema_version"), 1, 1, "truce version");
        require(text(value.get("backend_id"), "truce payload backend").equals("ck3-1.19.0.6-native-raiktor-actual-truce-expiry-v1")
                && integer(value.get("snapshot_revision"), "truce revision").equals(nativeRevision) && integer(value.get("toward_character_id"), "truce target").equals(BigInteger.valueOf(defender))
                && text(value.get("temporal_semantics"), "truce temporal semantics").equals("post_application_persisted_relation_state"), "legacy truce source differs");
        integer(value.get("current_date_raw"), "truce date"); integer(value.get("owner_character_id"), "truce owner");
        for (String name : List.of("native_has_truce", "actual_expiry_observable", "same_frame_stable", "readiness")) bool(value.get(name), name);
        String status = text(value.get("status"), "truce status");
        if (status.equals("available")) {
            require(bool(value.get("native_has_truce"), "has truce") && bool(value.get("actual_expiry_observable"), "actual expiry")
                    && bool(value.get("same_frame_stable"), "stable") && bool(value.get("readiness"), "ready")
                    && integer(value.get("expiry_date_raw"), "expiry").compareTo(integer(value.get("current_date_raw"), "truce date")) > 0
                    && value.get("unavailable_reason").isNull(), "available persisted truce incomplete");
        } else require(status.equals("no_truce") && !bool(value.get("native_has_truce"), "has truce") && !bool(value.get("actual_expiry_observable"), "actual expiry")
                && value.get("expiry_date_raw").isNull() && bool(value.get("same_frame_stable"), "stable") && !bool(value.get("readiness"), "ready")
                && text(value.get("unavailable_reason"), "truce absence reason").equals("native_has_truce_false"), "negative persisted truce observation differs");
        if (result.has("actual_truce_expiry_proof") && !result.get("actual_truce_expiry_proof").isNull()) require(same(result.get("actual_truce_expiry_proof"), value), "driver truce proof differs from native wire");
        return value.deepCopy();
    }
    private static BigInteger uint64(JsonNode value) { return StrictJson.integer(value, BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static BigInteger positive(JsonNode value, String name) { BigInteger n = integer(value, name); require(n.signum() > 0, name + " must be positive"); return n; }
}

