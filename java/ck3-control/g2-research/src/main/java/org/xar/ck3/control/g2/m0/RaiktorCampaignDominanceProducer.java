package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m0.RaiktorRawJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual three-snapshot, two-query strategic-power producer; never an outcome forecast. */
public final class RaiktorCampaignDominanceProducer {
    public static final String OPERATION = "produce-campaign-dominance";
    private static final List<String> POWER = List.of("actor_power_base_raw", "actor_network_contribution_raw",
            "actor_power_total_raw", "target_power_base_raw", "target_network_contribution_raw",
            "target_pre_adjustment_total_raw", "target_adjustment_delta_raw", "target_power_total_raw",
            "actual_power_ratio_raw");
    private RaiktorCampaignDominanceProducer() { }

    public static JsonNode produce(JsonNode before, JsonNode first, JsonNode between, JsonNode second,
            JsonNode after, int warId, int opponentId) {
        ObjectNode input = StrictJson.object(); input.set("before", before); input.set("first", first);
        input.set("between", between); input.set("second", second); input.set("after", after);
        return produce(before, first, between, second, after, warId, opponentId, hash(input));
    }

    /** Explicit artifact binding is the existing Python provider contract, not a generated observation. */
    public static JsonNode produce(JsonNode before, JsonNode first, JsonNode between, JsonNode second,
            JsonNode after, int warId, int opponentId, String sourceArtifactSha256) {
        require(sourceArtifactSha256 != null && sourceArtifactSha256.matches("[0-9A-F]{64}"), "source artifact SHA required");
        require(warId != -1 && opponentId != -1, "invalid full-generation war or opponent ID");
        ObjectNode a = frame(before, warId, opponentId);
        require(a.equals(frame(between, warId, opponentId)) && a.equals(frame(after, warId, opponentId)),
                "snapshot frame changed across the two queries");
        Sample firstSample = sample(first, a, opponentId);
        Sample secondSample = sample(second, a, opponentId);
        require((long) secondSample.sequence() == (long) firstSample.sequence() + 1,
                "strategic-power query sequence is not consecutive");
        require(firstSample.power().equals(secondSample.power()),
                "strategic-power payload changed across the two queries");
        ObjectNode power = firstSample.power();
        BigInteger actor = integer(power.get("actor_power_total_raw"), "actor power");
        BigInteger target = integer(power.get("target_power_total_raw"), "target power");
        power.put("relation", target.compareTo(actor) > 0 ? "opponent_stronger"
                : target.compareTo(actor) < 0 ? "actor_stronger" : "equal");
        power.put("target_minus_actor_raw", target.subtract(actor));
        ObjectNode certificate = StrictJson.object(); certificate.put("schema_version", 2);
        certificate.put("contract", "raiktor-campaign-dominance-certificate-v2");
        certificate.put("status", "complete"); certificate.set("frame", a); certificate.set("power", power);
        ObjectNode evidence = certificate.putObject("evidence");
        evidence.put("first_query_sequence", firstSample.sequence()); evidence.put("second_query_sequence", secondSample.sequence());
        evidence.put("double_sample_stable", true); evidence.put("source_artifact_sha256", sourceArtifactSha256);
        ObjectNode payload = firstSample.power(); payload.remove(List.of("relation", "target_minus_actor_raw"));
        evidence.put("query_payload_sha256", hash(payload));
        ObjectNode producer = certificate.putObject("producer");
        producer.put("producer_id", "raiktor-active-war-power-dominance-provider-v1");
        producer.put("producer_version", "1.0.0"); producer.put("production_live_input", true);
        ObjectNode boundaries = certificate.putObject("boundaries"); boundaries.put("measured_strategic_power_ready", true);
        boundaries.put("campaign_outcome_forecast_ready", false); boundaries.put("exit_utility_ready", false);
        boundaries.putNull("recommended_outcome"); boundaries.put("action_ready", false); boundaries.putNull("action_literal");
        ObjectNode result = StrictJson.object();
        result.put("schema", "xar.ck3.raiktor_campaign_dominance_provider.v1");
        result.put("provider", "raiktor-active-war-power-dominance-provider-v1"); result.put("status", "available");
        result.put("certificate_available", true); result.set("campaign_dominance_certificate", certificate);
        result.putArray("blockers");
        strings(result, "boundaries", List.of("factual_power_relation_only", "not_a_campaign_outcome_probability",
                "not_an_exit_utility_evaluation", "does_not_recommend_or_submit_an_action"));
        return result;
    }

    /** Recheck persisted certificates before any consumer or cross-process replay may use them. */
    public static ObjectNode normalizeCertificate(JsonNode value) {
        ObjectNode certificate = exact(value, Set.of("schema_version", "contract", "status", "frame", "power",
                "evidence", "producer", "boundaries"), "dominance certificate").deepCopy();
        int version = Math.toIntExact(number(certificate.get("schema_version"), 2, 3, "certificate version"));
        require(text(certificate.get("contract"), "certificate contract").equals(version == 2
                ? "raiktor-campaign-dominance-certificate-v2" : "raiktor-campaign-dominance-checkpoint-replay-certificate-v3")
                && text(certificate.get("status"), "certificate status").equals("complete"), "certificate identity drifted");
        ObjectNode frame = certificateFrame(certificate.get("frame"));
        java.util.HashSet<String> powerFields = new java.util.HashSet<>(POWER);
        powerFields.addAll(Set.of("fixed_point_scale", "relation", "target_minus_actor_raw"));
        ObjectNode power = exact(certificate.get("power"), Set.copyOf(powerFields), "certificate power");
        for (String key : POWER) number(power.get(key), Long.MIN_VALUE, Long.MAX_VALUE, key);
        long actor = positive64(power.get("actor_power_total_raw"), "actor power");
        long target = positive64(power.get("target_power_total_raw"), "target power");
        int scale = positive32(power.get("fixed_point_scale"), "power scale");
        require(integer(power.get("actual_power_ratio_raw"), "ratio").equals(BigInteger.valueOf(target)
                .multiply(BigInteger.valueOf(scale)).divide(BigInteger.valueOf(actor))), "certificate ratio drifted");
        require(text(power.get("relation"), "relation").equals(target > actor ? "opponent_stronger"
                : target < actor ? "actor_stronger" : "equal") && integer(power.get("target_minus_actor_raw"), "margin")
                .equals(BigInteger.valueOf(target).subtract(BigInteger.valueOf(actor))), "certificate relation drifted");
        java.util.HashSet<String> evidenceFields = new java.util.HashSet<>(Set.of("first_query_sequence", "second_query_sequence",
                "double_sample_stable", "source_artifact_sha256", "query_payload_sha256"));
        if (version == 3) evidenceFields.addAll(Set.of("source_certificate_sha256", "checkpoint_sha256", "driver_state_sha256",
                "source_runtime_frame", "checkpoint_state_equivalent"));
        ObjectNode evidence = exact(certificate.get("evidence"), Set.copyOf(evidenceFields), "certificate evidence");
        long first = positive32(evidence.get("first_query_sequence"), "first sequence");
        require(positive32(evidence.get("second_query_sequence"), "second sequence") == first + 1
                && bool(evidence.get("double_sample_stable"), "double sample"), "certificate sample sequence drifted");
        sha(evidence.get("source_artifact_sha256"), "source artifact");
        ObjectNode payload = power.deepCopy(); payload.remove(List.of("relation", "target_minus_actor_raw"));
        require(sha(evidence.get("query_payload_sha256"), "payload SHA").equals(hash(payload)), "certificate payload hash drifted");
        ObjectNode producer = exact(certificate.get("producer"), Set.of("producer_id", "producer_version", "production_live_input"), "producer");
        require(text(producer.get("producer_id"), "producer ID").equals(version == 2
                ? "raiktor-active-war-power-dominance-provider-v1" : "raiktor-checkpoint-power-dominance-replay-provider-v1")
                && text(producer.get("producer_version"), "producer version").equals("1.0.0")
                && bool(producer.get("production_live_input"), "production live input"), "certificate producer drifted");
        ObjectNode expectedBoundaries = StrictJson.object(); expectedBoundaries.put("measured_strategic_power_ready", true);
        expectedBoundaries.put("campaign_outcome_forecast_ready", false); expectedBoundaries.put("exit_utility_ready", false);
        expectedBoundaries.putNull("recommended_outcome"); expectedBoundaries.put("action_ready", false); expectedBoundaries.putNull("action_literal");
        if (version == 3) {
            for (String key : List.of("source_certificate_sha256", "checkpoint_sha256", "driver_state_sha256")) sha(evidence.get(key), key);
            require(bool(evidence.get("checkpoint_state_equivalent"), "checkpoint state equivalence"), "checkpoint equivalence required");
            ObjectNode source = certificateFrame(evidence.get("source_runtime_frame"));
            requireDistinctProcessSameState(source, frame);
            expectedBoundaries.put("same_runtime_frame_ready", false); expectedBoundaries.put("immutable_checkpoint_state_replay", true);
        }
        require(same(certificate.get("boundaries"), expectedBoundaries), "certificate authority boundary drifted");
        return certificate;
    }

    public static ObjectNode replay(JsonNode sourceValue, JsonNode targetValue, String sourceCheckpointSha,
            String targetCheckpointSha, String sourceDriverSha, String targetDriverSha) {
        ObjectNode source = normalizeCertificate(sourceValue);
        require(number(source.get("schema_version"), 2, 3, "source version") == 2, "replay source must be direct");
        for (String value : List.of(sourceCheckpointSha, targetCheckpointSha, sourceDriverSha, targetDriverSha))
            require(value.matches("[0-9A-F]{64}"), "checkpoint and driver SHA required");
        require(sourceCheckpointSha.equals(targetCheckpointSha) && sourceDriverSha.equals(targetDriverSha), "immutable input identity drifted");
        ObjectNode target = certificateFrame(targetValue); ObjectNode oldFrame = certificateFrame(source.get("frame"));
        requireDistinctProcessSameState(oldFrame, target);
        ObjectNode certificate = source.deepCopy(); certificate.put("schema_version", 3);
        certificate.put("contract", "raiktor-campaign-dominance-checkpoint-replay-certificate-v3"); certificate.set("frame", target);
        ObjectNode evidence = object(certificate.get("evidence"), "replay evidence");
        evidence.put("source_certificate_sha256", hash(source)); evidence.put("checkpoint_sha256", sourceCheckpointSha);
        evidence.put("driver_state_sha256", sourceDriverSha); evidence.set("source_runtime_frame", oldFrame); evidence.put("checkpoint_state_equivalent", true);
        object(certificate.get("producer"), "replay producer").put("producer_id", "raiktor-checkpoint-power-dominance-replay-provider-v1");
        ObjectNode boundaries = object(certificate.get("boundaries"), "replay boundaries");
        boundaries.put("same_runtime_frame_ready", false); boundaries.put("immutable_checkpoint_state_replay", true);
        ObjectNode result = StrictJson.object(); result.put("schema", "xar.ck3.raiktor_checkpoint_dominance_replay_provider.v1");
        result.put("provider", "raiktor-checkpoint-power-dominance-replay-provider-v1"); result.put("status", "available");
        result.put("certificate_available", true); result.set("campaign_dominance_certificate", normalizeCertificate(certificate)); result.putArray("blockers");
        strings(result, "boundaries", List.of("same_immutable_checkpoint_and_driver_state_only", "source_and_target_runtime_processes_remain_distinct",
                "factual_power_relation_only", "does_not_recommend_or_submit_an_action")); return result;
    }

    private static ObjectNode certificateFrame(JsonNode value) {
        ObjectNode frame = exact(value, Set.of("snapshot_id", "snapshot_revision", "native_revision", "date_raw", "connection_generation",
                "ck3_pid", "episode_run_id", "paused", "war_id", "actor_character_id", "opponent_character_id"), "power frame").deepCopy();
        text(frame.get("snapshot_id"), "snapshot ID"); text(frame.get("episode_run_id"), "episode ID"); i32(frame.get("date_raw"), "date");
        for (String key : List.of("snapshot_revision", "native_revision")) positive64(frame.get(key), key);
        for (String key : List.of("connection_generation", "ck3_pid")) positive32(frame.get(key), key);
        for (String key : List.of("war_id", "actor_character_id", "opponent_character_id")) fullId(frame.get(key), key);
        require(bool(frame.get("paused"), "paused"), "power certificate must be paused"); return frame;
    }

    private static void requireDistinctProcessSameState(ObjectNode source, ObjectNode target) {
        require(!same(source.get("ck3_pid"), target.get("ck3_pid")), "checkpoint replay requires distinct runtime processes");
        ObjectNode left = source.deepCopy(); left.remove("ck3_pid"); ObjectNode right = target.deepCopy(); right.remove("ck3_pid");
        require(same(left, right), "checkpoint gameplay state identity drifted");
    }

    private static ObjectNode frame(JsonNode raw, int warId, int opponentId) {
        ObjectNode snapshot = structured(raw, "snapshot");
        ObjectNode diagnostics = object(snapshot.get("diagnostics"), "snapshot.diagnostics");
        ObjectNode played = object(snapshot.get("played_character"), "played_character");
        int actor = fullId(played.get("character_id"), "played_character_id");
        List<ObjectNode> matches = new ArrayList<>();
        for (JsonNode value : array(snapshot.get("active_wars"), "active_wars")) {
            if (value instanceof ObjectNode war && war.get("war_id") != null && war.get("war_id").isIntegralNumber()
                    && integer(war.get("war_id"), "war_id").equals(BigInteger.valueOf(warId))) matches.add(war);
        }
        require(matches.size() == 1, "active war identity is not unique");
        ObjectNode war = matches.getFirst();
        require(text(war.get("player_side"), "player_side").equals("attacker")
                && bool(war.get("player_is_primary_war_leader"), "primary war leader")
                && fullId(war.get("primary_opponent_character_id"), "primary opponent") == opponentId,
                "active war opponent binding drifted");
        require(bool(snapshot.get("paused"), "paused") && bool(snapshot.get("map_ready"), "map_ready"),
                "snapshot must be a paused ready map");
        ObjectNode frame = StrictJson.object();
        frame.put("snapshot_id", text(snapshot.get("snapshot_id"), "snapshot_id"));
        frame.put("snapshot_revision", positive64(snapshot.get("revision"), "revision"));
        frame.put("native_revision", positive64(snapshot.get("native_revision"), "native_revision"));
        frame.put("date_raw", i32(snapshot.get("date_raw"), "date_raw"));
        frame.put("connection_generation", positive32(diagnostics.get("connection_generation"), "connection_generation"));
        frame.put("ck3_pid", positive32(diagnostics.get("bridge_pid"), "bridge_pid"));
        frame.put("episode_run_id", text(snapshot.get("episode_run_id"), "episode_run_id")); frame.put("paused", true);
        frame.put("war_id", warId); frame.put("actor_character_id", actor); frame.put("opponent_character_id", opponentId);
        return frame;
    }

    private static Sample sample(JsonNode raw, ObjectNode frame, int opponent) {
        ObjectNode query = structured(raw, "query");
        int sequence = positive32(query.get("query_sequence"), "query_sequence");
        require(bool(query.get("accepted"), "accepted") && text(query.get("status"), "status").equals("available")
                && same(query.get("queried_snapshot_id"), frame.get("snapshot_id"))
                && same(query.get("queried_revision"), frame.get("snapshot_revision"))
                && same(query.get("queried_native_revision"), frame.get("native_revision")),
                "strategic-power query frame binding drifted");
        var scopes = JsonNodeFactory.instance.arrayNode(); var scope = scopes.addObject(); scope.put("target_character_id", opponent);
        scope.putArray("sources").add("active_war_primary_opponent");
        require(same(scopes, query.get("target_scopes")), "strategic-power target scope drifted");
        ObjectNode observation = object(query.get("war_entry_assessments"), "assessment");
        ObjectNode readiness = object(observation.get("readiness"), "assessment.readiness");
        ObjectNode provenance = object(observation.get("provenance"), "assessment.provenance");
        var rows = array(observation.get("assessments"), "assessment rows");
        var targets = JsonNodeFactory.instance.arrayNode().add(opponent);
        require(text(observation.get("status"), "assessment status").equals("available")
                && same(observation.get("snapshot_revision"), frame.get("native_revision"))
                && same(observation.get("date_raw"), frame.get("date_raw"))
                && same(observation.get("actor_character_id"), frame.get("actor_character_id"))
                && same(targets, observation.get("requested_target_character_ids")) && rows.size() == 1
                && bool(readiness.get("ready"), "readiness.ready"), "strategic-power observation is incomplete");
        for (JsonNode value : readiness) require(bool(value, "readiness"), "strategic-power observation is incomplete");
        ObjectNode row = object(rows.get(0), "assessment row");
        require(fullId(row.get("target_character_id"), "target ID") == opponent
                && fullId(row.get("effective_target_character_id"), "effective target ID") == opponent,
                "strategic-power assessment target drifted");
        ObjectNode power = StrictJson.object();
        for (String key : POWER) power.put(key, number(row.get(key), Long.MIN_VALUE, Long.MAX_VALUE, key));
        int scale = positive32(provenance.get("fixed_point_scale"), "fixed_point_scale"); power.put("fixed_point_scale", scale);
        long actor = positive64(power.get("actor_power_total_raw"), "actor power");
        long target = positive64(power.get("target_power_total_raw"), "target power");
        require(integer(power.get("actual_power_ratio_raw"), "ratio").equals(
                BigInteger.valueOf(target).multiply(BigInteger.valueOf(scale)).divide(BigInteger.valueOf(actor))),
                "strategic-power ratio is inconsistent");
        return new Sample(sequence, power);
    }

    private static ObjectNode structured(JsonNode raw, String name) {
        ObjectNode row = object(raw, name);
        JsonNode nested = row.get("structured_content");
        return nested == null || nested.isNull() ? row : object(nested, name + ".structured_content");
    }
    private record Sample(int sequence, ObjectNode rawPower) {
        private Sample { rawPower = rawPower.deepCopy(); }
        ObjectNode power() { return rawPower.deepCopy(); }
    }
}
