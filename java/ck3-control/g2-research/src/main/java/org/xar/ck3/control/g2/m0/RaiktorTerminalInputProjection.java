package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Set;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.warpolicy.WarSide;

/** Actual formal-exit input producer; atomic native options are validated by the unique shared normalizer. */
public final class RaiktorTerminalInputProjection {
    private RaiktorTerminalInputProjection() { }

    /** Source-bound replay caller adapter; selects the actual unique war and never invents a terminal score. */
    public static byte[] executeFromSnapshot(byte[] raw) {
        require(raw != null && raw.length <= StrictJson.EXPLICIT_MAX_BYTES, "explicit1MiB snapshot terminal request required");
        ObjectNode request = StrictJson.object(RaiktorExitObservationCodec.parseWire(raw),
                Set.of("snapshot", "war_id", "opponent_character_id", "options_query", "white_peace_projection"));
        ObjectNode snapshot = object(request.get("snapshot"));
        int warId = (int) StrictJson.integer(request.get("war_id"), 1, Integer.MAX_VALUE);
        JsonNode wars = snapshot.get("active_wars"); require(wars != null && wars.isArray(), "current active war observation unavailable");
        List<ObjectNode> matches = new ArrayList<>();
        for (JsonNode row : wars) {
            if (row instanceof ObjectNode war && war.has("war_id") && war.get("war_id").isIntegralNumber()
                    && war.get("war_id").bigIntegerValue().equals(BigInteger.valueOf(warId))) { matches.add(war); }
        }
        require(matches.size() == 1, "current source war identity absent or ambiguous");
        ObjectNode selectedWar = matches.getFirst();
        require(StrictJson.text(selectedWar.get("player_side")).equals("attacker")
                && bool(selectedWar.get("player_is_primary_war_leader"))
                && exactIntegerEqual(selectedWar.get("primary_opponent_character_id"), request.get("opponent_character_id")),
                "replay terminal war is not the observed primary attacker/opponent");
        ObjectNode projection = object(request.get("white_peace_projection"));
        ObjectNode frame = object(object(projection.get("white_peace_observation")).get("frame"));
        RaiktorRecommendationInputCodec.decodeFrame(frame);
        ObjectNode diagnostics = object(snapshot.get("diagnostics"));
        require(bool(snapshot.get("paused")) && equal(snapshot.get("snapshot_id"), frame.get("snapshot_id"))
                && exactIntegerEqual(snapshot.get("revision"), frame.get("snapshot_revision"))
                && exactIntegerEqual(snapshot.get("native_revision"), frame.get("native_revision"))
                && exactIntegerEqual(snapshot.get("date_raw"), frame.get("date_raw"))
                && equal(snapshot.get("episode_run_id"), frame.get("episode_id"))
                && exactIntegerEqual(diagnostics.get("bridge_pid"), frame.get("ck3_pid")), "replay terminal snapshot crossed projection frame");
        String connection = StrictJson.text(frame.get("connection_id"));
        require(connection.matches("connection-generation:[0-9]+")
                && integer(diagnostics.get("connection_generation")).equals(new BigInteger(connection.substring("connection-generation:".length()))),
                "replay terminal connection generation drifted");
        ObjectNode played = object(snapshot.get("played_character"));
        require(exactIntegerEqual(played.get("character_id"), frame.get("primary_attacker_character_id")), "replay terminal actor drifted");
        ObjectNode query = object(request.get("options_query"));
        require(equal(query.get("queried_snapshot_id"), frame.get("snapshot_id"))
                && exactIntegerEqual(query.get("queried_revision"), frame.get("snapshot_revision"))
                && exactIntegerEqual(query.get("queried_native_revision"), frame.get("native_revision"))
                && exactIntegerEqual(query.get("queried_connection_generation"), diagnostics.get("connection_generation"))
                && equal(query.get("queried_episode_run_id"), frame.get("episode_id")), "replay terminal native options crossed frame");
        // Project only the fields read by the original pure terminal producer after validating full source binding.
        ObjectNode payload = StrictJson.object();
        ObjectNode warInput = payload.putObject("war"); warInput.set("player_relative_war_score", selectedWar.get("player_relative_war_score"));
        if (selectedWar.has("war_duration_days")) { warInput.set("war_duration_days", selectedWar.get("war_duration_days")); }
        payload.set("war_id", request.get("war_id")); payload.set("opponent_character_id", request.get("opponent_character_id"));
        payload.putObject("options_query").set("war_termination_options", query.get("war_termination_options"));
        payload.putObject("white_peace_projection").putObject("white_peace_observation").set("frame", frame);
        return execute(RaiktorExitObservationCodec.encodeWire(payload));
    }

    public static byte[] executeSnapshotOperation(byte[] raw) {
        require(raw != null && raw.length <= StrictJson.EXPLICIT_MAX_BYTES, "explicit1MiB snapshot terminal request required");
        ObjectNode request = StrictJson.object(RaiktorExitObservationCodec.parseWire(raw),
                Set.of("operation", "snapshot", "war_id", "opponent_character_id", "options_query", "white_peace_projection"));
        require(StrictJson.text(request.get("operation")).equals("project-terminal-control-from-snapshot"), "terminal snapshot operation differs");
        ObjectNode payload = request.deepCopy(); payload.remove("operation");
        return executeFromSnapshot(RaiktorExitObservationCodec.encodeWire(payload));
    }

    public static byte[] execute(byte[] raw) {
        require(raw != null && raw.length <= StrictJson.INPUT_MAX_BYTES, "bounded terminal request required");
        ObjectNode request = StrictJson.object(RaiktorExitObservationCodec.parseWire(raw), Set.of("war", "war_id", "opponent_character_id", "options_query", "white_peace_projection"));
        int warId = (int) StrictJson.integer(request.get("war_id"), 1, Integer.MAX_VALUE);
        int opponent = (int) StrictJson.integer(request.get("opponent_character_id"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        require(opponent != -1, "opponent full-generation identity unavailable");
        ObjectNode query = object(request.get("options_query"));
        var options = NativeTerminationOptions.normalizeNativePacket(query.get("war_termination_options"), warId);
        ObjectNode normalized = options.normalized();
        ObjectNode war = object(request.get("war"));
        BigInteger score = integer(war.get("player_relative_war_score"));
        require(options.side() == WarSide.ATTACKER && options.primary()
                && bool(normalized.get("absolute_war_scores_observable"))
                && score.equals(BigInteger.valueOf(options.relativeScore()))
                && score.equals(integer(normalized.get("attacker_war_score")))
                && score.negate().equals(integer(normalized.get("defender_war_score"))),
                "same-frame Raiktor terminal-control scores incomplete or drifted");
        BigInteger duration = integer(normalized.get("war_duration_days"));
        require(duration.signum() >= 0, "same-frame Raiktor war duration unavailable");
        if (war.has("war_duration_days") && !war.get("war_duration_days").isNull()) {
            require(duration.equals(integer(war.get("war_duration_days"))), "same-frame Raiktor war duration drifted");
        }
        ObjectNode projection = object(request.get("white_peace_projection"));
        ObjectNode observation = object(projection.get("white_peace_observation"));
        M0Frame frame = RaiktorRecommendationInputCodec.decodeFrame(observation.get("frame"));
        require(frame.warId() == warId && frame.primaryDefenderCharacterId() == opponent, "terminal-control frame unavailable");
        ObjectNode result = StrictJson.object(); result.put("schema_version", 2);
        result.put("contract", "raiktor-opponent-terminal-control-v2"); result.put("status", "complete");
        result.set("frame", observation.get("frame").deepCopy()); result.put("player_side", "attacker");
        result.put("player_is_primary_war_leader", true); result.put("player_relative_war_score", score);
        result.put("absolute_war_scores_observable", true); result.put("attacker_war_score", score);
        result.put("defender_war_score", score.negate()); result.put("war_duration_days", duration);
        result.put("opponent_terminal_control", score.compareTo(BigInteger.valueOf(-100)) <= 0);
        result.put("source_options_query_sha256", hash(normalized));
        ObjectNode producer = result.putObject("producer"); producer.put("producer_id", "raiktor-formal-exit-terminal-control-v1");
        producer.put("production_live_input", true);
        return StrictJson.canonical(result);
    }

    public static byte[] executeOperation(byte[] raw) {
        require(raw != null && raw.length <= StrictJson.INPUT_MAX_BYTES, "bounded terminal request required");
        ObjectNode request = StrictJson.object(RaiktorExitObservationCodec.parseWire(raw), Set.of("operation", "war", "war_id", "opponent_character_id", "options_query", "white_peace_projection"));
        require(StrictJson.text(request.get("operation")).equals("project-terminal-control"), "terminal projection operation differs");
        ObjectNode payload = request.deepCopy(); payload.remove("operation"); return execute(RaiktorExitObservationCodec.encodeWire(payload));
    }
    private static String hash(JsonNode value) {
        byte[] raw = RaiktorExitObservationCodec.encodeWire(value);
        return RetainedJson.pythonCanonical(RetainedJson.parse(raw),
                new RetainedJson.CanonicalBudget(StrictJson.EXPLICIT_MAX_BYTES, 100_000, 128))
                .sha256().toUpperCase(Locale.ROOT);
    }
    private static ObjectNode object(JsonNode n) { require(n instanceof ObjectNode, "explicit JSON object required"); return (ObjectNode) n; }
    private static boolean equal(JsonNode left, JsonNode right) { return left != null && right != null && left.equals(right); }
    private static boolean exactIntegerEqual(JsonNode left, JsonNode right) { return integer(left).equals(integer(right)); }
    private static BigInteger integer(JsonNode n) { require(n != null && n.isIntegralNumber(), "exact integer required"); return n.bigIntegerValue(); }
    private static boolean bool(JsonNode n) { require(n != null && n.isBoolean(), "exact boolean required"); return n.booleanValue(); }
}
