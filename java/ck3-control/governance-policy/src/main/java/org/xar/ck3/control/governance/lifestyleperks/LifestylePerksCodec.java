package org.xar.ck3.control.governance.lifestyleperks;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel.*;

/** Strict new wrapper around an explicitly consumed projection of extensible legacy snapshots. */
public final class LifestylePerksCodec {
    public static final String INPUT_SCHEMA = "xar.java.all-lifestyle-perk-input.v1";
    private static final Set<String> BINDING_KEYS = Set.of("expected_snapshot_id", "expected_episode_run_id",
            "expected_public_revision", "expected_native_revision", "expected_proof_epoch", "expected_date_raw",
            "expected_player_character_id");
    private LifestylePerksCodec() { }

    public static Input decode(byte[] raw) {
        JsonNode root = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "snapshot", "binding", "owned"));
        StrictJson.require(StrictJson.text(root.get("schema")).equals(INPUT_SCHEMA), "lifestyle perk input schema");
        JsonNode snapshot = object(root.get("snapshot"));
        JsonNode bindingNode = StrictJson.object(root.get("binding"), BINDING_KEYS);
        ExpectedBinding binding = new ExpectedBinding(text(bindingNode, "expected_snapshot_id"),
                text(bindingNode, "expected_episode_run_id"), integer(bindingNode, "expected_public_revision"),
                integer(bindingNode, "expected_native_revision"), integer(bindingNode, "expected_proof_epoch"),
                integer(bindingNode, "expected_date_raw"), integer(bindingNode, "expected_player_character_id"));
        FrameIdentity snapshotFrame = frame(snapshot);
        StrictJson.require(integer(snapshot, "public_revision").equals(binding.expectedPublicRevision()), "public revision binding mismatch");
        StrictJson.require(integer(snapshot, "proof_epoch").equals(binding.expectedProofEpoch()), "proof epoch binding mismatch");
        JsonNode progress = object(snapshot.get("all_lifestyle_progress_v3"));
        Completeness completeness = switch (text(progress, "status")) {
            case "complete" -> Completeness.COMPLETE;
            case "partial" -> Completeness.PARTIAL;
            default -> throw new IllegalArgumentException("complete or partial progress required");
        };
        JsonNode rawRows = array(progress.get("rows"));
        List<ProgressRow> rows = new ArrayList<>();
        for (JsonNode rawRow : rawRows) {
            JsonNode row = object(rawRow);
            Lifestyle lifestyle = Lifestyle.fromWire(text(row, "lifestyle_key"));
            rows.add(switch (text(row, "status")) {
                case "available" -> new AvailableProgress(lifestyle, integer(row, "xp_total_raw"),
                        integer(row, "xp_within_level_raw"), integer(row, "xp_per_level"),
                        integer(row, "unspent_perk_points"), integer(row, "used_perk_points"));
                case "unavailable" -> new UnavailableProgress(lifestyle, text(row, "unavailable_reason"));
                default -> throw new IllegalArgumentException("available or unavailable progress row required");
            });
        }
        JsonNode candidatesNode = object(snapshot.get("legal_perk_candidates"));
        String candidateStatus = text(candidatesNode, "status");
        CandidateObservation candidates;
        if (candidateStatus.equals("available")) {
            List<Candidate> items = new ArrayList<>();
            for (JsonNode row : array(candidatesNode.get("items"))) {
                object(row); items.add(new Candidate(text(row, "key"), text(row, "lifestyle_key")));
            }
            candidates = new LegalCandidates(text(candidatesNode, "scope"), items);
        } else { candidates = new UnavailableCandidates(candidateStatus); }
        List<String> owned = new ArrayList<>();
        for (JsonNode key : array(root.get("owned"))) { owned.add(StrictJson.text(key)); }
        return new Input(snapshotFrame, new ProgressObservation(frame(progress), completeness, rows), candidates, binding, owned);
    }

    /** Canonical projection encoding; never labels reconstructed bytes as the original native response. */
    public static byte[] encodeInput(Input input) {
        ObjectNode root = StrictJson.object(); root.put("schema", INPUT_SCHEMA);
        ObjectNode snapshot = root.putObject("snapshot"); writeFrame(snapshot, input.snapshotFrame());
        snapshot.put("public_revision", input.binding().expectedPublicRevision());
        snapshot.put("proof_epoch", input.binding().expectedProofEpoch());
        ObjectNode progress = snapshot.putObject("all_lifestyle_progress_v3");
        writeFrame(progress, input.progress().frame()); progress.put("status", input.progress().completeness().wire());
        ArrayNode rows = progress.putArray("rows");
        for (ProgressRow row : input.progress().rows()) {
            ObjectNode item = rows.addObject(); item.put("lifestyle_key", row.lifestyle().wire());
            if (row instanceof AvailableProgress available) {
                item.put("status", "available"); item.put("xp_total_raw", available.xpTotalRaw());
                item.put("xp_within_level_raw", available.xpWithinLevelRaw()); item.put("xp_per_level", available.xpPerLevel());
                item.put("unspent_perk_points", available.unspentPerkPoints()); item.put("used_perk_points", available.usedPerkPoints());
                item.putNull("unavailable_reason");
            } else if (row instanceof UnavailableProgress unavailable) {
                item.put("status", "unavailable"); item.put("unavailable_reason", unavailable.reason());
                for (String field : List.of("xp_total_raw", "xp_within_level_raw", "xp_per_level", "unspent_perk_points", "used_perk_points")) {
                    item.putNull(field);
                }
            }
        }
        ObjectNode candidateNode = snapshot.putObject("legal_perk_candidates");
        if (input.candidates() instanceof LegalCandidates legal) {
            candidateNode.put("status", "available"); candidateNode.put("scope", legal.scope());
            ArrayNode items = candidateNode.putArray("items");
            for (Candidate candidate : legal.items()) {
                ObjectNode row = items.addObject(); row.put("key", candidate.key()); row.put("lifestyle_key", candidate.lifestyleKey());
            }
        } else if (input.candidates() instanceof UnavailableCandidates unavailable) {
            candidateNode.put("status", unavailable.sourceStatus());
        }
        root.set("binding", binding(input.binding()));
        ArrayNode owned = root.putArray("owned"); input.owned().forEach(owned::add);
        return StrictJson.canonical(root);
    }

    public static byte[] encodeDecision(Decision decision) {
        return StrictJson.canonical(decisionNode(decision));
    }

    /** Serialization-only node for the outer legacy consumer's policy-id/default-action envelope. */
    public static ObjectNode decisionNode(Decision decision) {
        ObjectNode node = StrictJson.object(); node.put("status", decision.status().wire());
        switch (decision) {
            case ObservationUnavailable unavailable -> {
                node.put("reason", unavailable.reason().wire());
                unavailable.unavailableLifestyles().ifPresent(values -> {
                    ArrayNode keys = node.putArray("unavailable_lifestyles"); values.forEach(key -> keys.add(key.wire()));
                });
            }
            case CandidatesUnavailable unavailable -> unavailable.reason().ifPresent(reason -> node.put("reason", reason.wire()));
            case NoLegalMinimum minimum -> {
                node.put("reason", minimum.reason().wire());
                ObjectNode points = node.putObject("observed_positive_points");
                minimum.observedPositivePoints().forEach((key, value) -> points.put(key.wire(), value));
            }
            case Recommendation recommendation -> {
                Action action = recommendation.action(); ObjectNode selected = node.putObject("selected_action");
                selected.put("kind", action.kind()); selected.put("target_key", action.targetKey());
                selected.put("target_lifestyle_key", action.targetLifestyle().wire());
                selected.set("expected", binding(action.expected())); selected.put("reason", action.reason().wire());
                node.put("progress_status", recommendation.progressStatus().wire());
                node.put("observed_target_points", recommendation.observedTargetPoints());
            }
        }
        return node;
    }

    private static FrameIdentity frame(JsonNode object) {
        return new FrameIdentity(text(object, "snapshot_id"), integer(object, "native_revision"),
                integer(object, "date_raw"), integer(object, "player_character_id"), text(object, "episode_run_id"));
    }
    private static void writeFrame(ObjectNode node, FrameIdentity frame) {
        node.put("snapshot_id", frame.snapshotId()); node.put("native_revision", frame.nativeRevision());
        node.put("date_raw", frame.dateRaw()); node.put("player_character_id", frame.playerCharacterId()); node.put("episode_run_id", frame.episodeRunId());
    }
    private static ObjectNode binding(ExpectedBinding binding) {
        ObjectNode node = StrictJson.object(); node.put("expected_snapshot_id", binding.expectedSnapshotId());
        node.put("expected_episode_run_id", binding.expectedEpisodeRunId()); node.put("expected_public_revision", binding.expectedPublicRevision());
        node.put("expected_native_revision", binding.expectedNativeRevision()); node.put("expected_proof_epoch", binding.expectedProofEpoch());
        node.put("expected_date_raw", binding.expectedDateRaw()); node.put("expected_player_character_id", binding.expectedPlayerCharacterId());
        return node;
    }
    private static JsonNode object(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "required legacy projection object"); return value;
    }
    private static JsonNode array(JsonNode value) {
        StrictJson.require(value != null && value.isArray(), "required JSON array"); return value;
    }
    private static String text(JsonNode object, String key) { return StrictJson.text(object.get(key)); }
    private static BigInteger integer(JsonNode object, String key) {
        JsonNode value = object.get(key);
        StrictJson.require(value != null && value.isIntegralNumber(), "exact integer token required: " + key);
        return value.bigIntegerValue();
    }
}
