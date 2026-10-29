package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.SuccessorUiQueueModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Narrow, exact new wrapper around extensible original App/SDK containers. No query, file or action IO. */
public final class SuccessorUiQueueCodec {
    public static final String SCHEMA = "xar.java-successor-ui-queue/v1";
    public static final String RESULT_SCHEMA = "xar.java-successor-ui-queue-result/v1";
    private static final List<String> PROOF = List.of("status", "predecessor_character_id", "successor_character_id",
            "source_episode_run_id", "episode_run_id", "same_campaign_frame", "ck3_command_submitted",
            "process_restarted", "succession_lifecycle", "reconciliation");
    private static final List<String> SOURCE = List.of("snapshot_id", "revision", "native_revision", "date_raw", "bridge_pid", "connection_generation");
    private SuccessorUiQueueCodec() { }

    public static byte[] apply(byte[] body) { return encode(evaluate(body)); }
    public static Result evaluate(byte[] body) { return SuccessorUiQueueModel.evaluate(decode(body)); }

    public static Input decode(byte[] body) {
        JsonNode request = SuccessionCodec.parse(ProjectionJson.object(body, ProjectionJson.MAX_BYTES).bytes());
        SuccessionCodec.exact(request, Set.of("schema", "operation", "transition", "app_response", "independent_snapshot"));
        require(SCHEMA.equals(text(request, "schema")) && "consume_resume".equals(text(request, "operation")), "exact UI Queue operation required");
        JsonNode transition = object(field(request, "transition"));
        require("verified".equals(text(transition, "status")), "original verified handoff evidence required");
        require(bool(transition, "same_campaign_frame") && !bool(transition, "ck3_command_submitted")
                && !bool(transition, "process_restarted"), "original same-Game handoff evidence required");
        JsonNode app = object(field(request, "app_response"));
        JsonNode retained = field(app, "transition");
        if (!retained.isNull()) {
            object(retained);
            for (String name : PROOF) require(field(retained, name).equals(field(transition, name)), "App changed original handoff proof: " + name);
            for (String name : List.of("predecessor_binding", "successor_episode_binding")) {
                for (String key : SOURCE) require(field(field(retained, name), key).equals(field(field(transition, name), key)), "App changed original handoff source: " + key);
            }
        }
        LivingFrame claimed = snapshot(field(app, "snapshot"));
        LivingFrame independent = snapshot(field(request, "independent_snapshot"));
        String episode = text(transition, "episode_run_id");
        BigInteger successor = NativeCharacterId.fromJson(field(transition, "successor_character_id")).asBigInteger();
        JsonNode independentWire = field(request, "independent_snapshot");
        require(field(independentWire, "succession_lifecycle").equals(field(transition, "succession_lifecycle")), "Queue post lifecycle changed");
        JsonNode goal = object(field(independentWire, "campaign_goal"));
        require(NativeCharacterId.fromJson(field(goal, "current_character_id")).asBigInteger().equals(successor), "Queue post goal changed successor");
        JsonNode retainedGoal = object(field(transition, "campaign_goal_after"));
        require(integer(goal, "format_version").equals(BigInteger.ONE)
                && integer(retainedGoal, "format_version").equals(BigInteger.ONE)
                && "dynasty_continuity".equals(text(goal, "goal_key")), "original continuity goal required");
        for (String key : List.of("goal_key", "campaign_id", "origin_character_id", "current_character_id")) {
            require(field(goal, key).equals(field(retainedGoal, key)), "Queue post changed retained campaign goal: " + key);
        }
        require(integer(field(goal, "progress"), "reconciled_successions").equals(
                integer(field(retainedGoal, "progress"), "reconciled_successions")), "Queue post changed retained succession count");
        if (retained != null && !retained.isNull()) {
            require(field(field(app, "snapshot"), "campaign_goal").equals(field(independentWire, "campaign_goal")), "App and Queue goal differ");
        }
        JsonNode cold = app.get("cold_resume_binding");
        boolean reconnect = cold != null && !cold.isNull() && bool(object(cold), "connection_rebound");
        SourceFrame originalSource = source(field(transition, "successor_episode_binding"));
        SourceFrame predecessorSource = source(field(transition, "predecessor_binding"));
        require(originalSource.bridgePid().equals(predecessorSource.bridgePid())
                && originalSource.connectionGeneration().equals(predecessorSource.connectionGeneration()), "original handoff process/connection changed");
        JsonNode post = field(request, "independent_snapshot");
        boolean decision = objectOrNull(post, "active_event") || objectOrNull(post, "pending_character_interaction");
        return new Input(Status.fromWire(text(app, "status")), bool(app, "pending"), claimed, independent,
                episode, successor, originalSource, decision, reconnect);
    }

    public static byte[] encode(Result result) {
        ObjectNode out = SuccessionCodec.objectNode();
        out.put("schema", RESULT_SCHEMA);
        if (result instanceof Observed observed) {
            out.put("status", observed.status().wire()).put("pending", observed.pending())
                    .put("player_decision_pending", observed.playerDecisionPending()).putNull("unavailable_reason");
        } else {
            Unavailable unavailable = (Unavailable) result;
            out.put("status", "unavailable").putNull("pending").putNull("player_decision_pending")
                    .put("unavailable_reason", unavailable.reason().name());
        }
        ObjectNode frame = out.putObject("frame");
        LivingFrame living = result.frame(); SourceFrame source = living.source();
        frame.put("snapshot_id", source.snapshotId()).put("revision", source.revision()).put("native_revision", source.nativeRevision())
                .put("date_raw", source.dateRaw()).put("bridge_pid", source.bridgePid()).put("connection_generation", source.connectionGeneration())
                .put("episode_run_id", living.episodeRunId()).put("successor_character_id", living.successorCharacterId());
        out.put("submission_authorized", false).put("action_replay_authorized", false).put("queries_performed", 0)
                .put("ordinary_cycle_credit", 0).put("new_natural_succession_credit", 0)
                .put("original_app_queue_verification_required", true);
        return SuccessionCodec.encode(out);
    }

    public static Result decodeResult(byte[] body) {
        JsonNode row = SuccessionCodec.parse(ProjectionJson.object(body, ProjectionJson.MAX_BYTES).bytes());
        SuccessionCodec.exact(row, Set.of("schema", "status", "pending", "player_decision_pending", "unavailable_reason", "frame",
                "submission_authorized", "action_replay_authorized", "queries_performed", "ordinary_cycle_credit",
                "new_natural_succession_credit", "original_app_queue_verification_required"));
        require(RESULT_SCHEMA.equals(text(row, "schema")) && !bool(row, "submission_authorized")
                && !bool(row, "action_replay_authorized") && bool(row, "original_app_queue_verification_required")
                && integer(row, "queries_performed").signum() == 0 && integer(row, "ordinary_cycle_credit").signum() == 0
                && integer(row, "new_natural_succession_credit").signum() == 0, "read-only UI result flags required");
        JsonNode frame = field(row, "frame");
        SuccessionCodec.exact(frame, Set.of("snapshot_id", "revision", "native_revision", "date_raw", "bridge_pid",
                "connection_generation", "episode_run_id", "successor_character_id"));
        LivingFrame living = new LivingFrame(source(frame), text(frame, "episode_run_id"), NativeCharacterId.fromJson(field(frame, "successor_character_id")).asBigInteger());
        if ("unavailable".equals(text(row, "status"))) {
            require(field(row, "pending").isNull() && field(row, "player_decision_pending").isNull(), "unavailable is not a pending or clear observation");
            return new Unavailable(UnavailableReason.valueOf(text(row, "unavailable_reason")), living);
        }
        require(field(row, "unavailable_reason").isNull(), "observed UI result cannot carry unavailable reason");
        Status status = Status.fromWire(text(row, "status")); boolean pending = bool(row, "pending");
        boolean decision = bool(row, "player_decision_pending");
        require(status == Status.CLEAR ? !pending && !decision : pending, "inconsistent observed UI result");
        return new Observed(status, pending, living, decision);
    }

    private static LivingFrame snapshot(JsonNode node) {
        object(node); JsonNode played = object(field(node, "played_character"));
        require(bool(node, "paused") && bool(node, "map_ready") && bool(played, "alive")
                && !bool(node, "one_life_terminal") && field(node, "one_life_terminal_reason").isNull(), "stable paused living successor required");
        BigInteger id = NativeCharacterId.fromJson(field(node, "episode_character_id")).asBigInteger();
        require(id.equals(NativeCharacterId.fromJson(field(played, "character_id")).asBigInteger()), "played and episode successor differ");
        JsonNode diagnostics = object(field(node, "diagnostics"));
        SourceFrame source = new SourceFrame(text(node, "snapshot_id"), integer(node, "revision"), integer(node, "native_revision"),
                integer(node, "date_raw"), integer(diagnostics, "bridge_pid"), integer(diagnostics, "connection_generation"));
        return new LivingFrame(source, text(node, "episode_run_id"), id);
    }
    private static SourceFrame source(JsonNode node) {
        return new SourceFrame(text(node, "snapshot_id"), integer(node, "revision"), integer(node, "native_revision"),
                integer(node, "date_raw"), integer(node, "bridge_pid"), integer(node, "connection_generation"));
    }
    private static boolean objectOrNull(JsonNode node, String key) { JsonNode value = field(node, key); require(value.isObject() || value.isNull(), "original optional UI object required"); return value.isObject(); }
    private static JsonNode object(JsonNode node) { require(node != null && node.isObject(), "original UI object required"); return node; }
    private static JsonNode field(JsonNode node, String key) { object(node); JsonNode value = node.get(key); require(value != null, "missing UI field: " + key); return value; }
    private static String text(JsonNode node, String key) { JsonNode value = field(node, key); require(value.isTextual() && !value.textValue().isEmpty(), "nonempty UI text required: " + key); return value.textValue(); }
    private static BigInteger integer(JsonNode node, String key) { JsonNode value = field(node, key); require(value.isIntegralNumber(), "exact original UI integer token required: " + key); return value.bigIntegerValue(); }
    private static boolean bool(JsonNode node, String key) { JsonNode value = field(node, key); require(value.isBoolean(), "exact original UI boolean required: " + key); return value.booleanValue(); }
}
