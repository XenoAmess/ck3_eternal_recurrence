package org.xar.ck3.control.wave2.planning.playerrisk;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Context;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Known;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Stress;

/** The two current consumer seams, retaining plan priority and the later native decision guards. */
public final class PlayerRiskConsumers {
    private static final String ROOT_QUERY = "query-campaign-root-context-v1";
    private PlayerRiskConsumers() { }
    public enum JournallerStressGate { SAME_FRAME_STRESS_UNAVAILABLE, BELOW_URGENT_STRESS_THRESHOLD, CONTINUE_NATIVE_GUARDS }

    /** Service's actual reverse-history selection, including auto-turn executor wrappers. */
    public static Context fromCurrentHistory(byte[] request) {
        JsonNode input = StrictJson.parse(request);
        StrictJson.object(input, java.util.Set.of("snapshot", "history"));
        JsonNode snapshot = input.get("snapshot"), history = input.get("history");
        StrictJson.require(snapshot != null && snapshot.isObject() && history != null && history.isArray(), "current snapshot and history array required");
        JsonNode selected = null;
        for (int index = history.size() - 1; index >= 0; index--) {
            JsonNode row = history.get(index);
            if (!row.isObject() || !isTrue(row.get("ok")) || !ROOT_QUERY.equals(effectiveCommand(row))) { continue; }
            JsonNode result = effectiveResult(row);
            if (sameFrameRoot(result, snapshot)) { selected = result; break; }
        }
        return PlayerRiskCodec.projectObserved(snapshot, selected);
    }

    public static ObjectNode attachToPlan(JsonNode originalPlan, Context context) {
        StrictJson.require(originalPlan instanceof ObjectNode, "original plan object required");
        ObjectNode detached = ((ObjectNode) originalPlan).deepCopy();
        detached.set("player_risk_context", PlayerRiskCodec.encode(context));
        return detached;
    }

    /** CONTINUE means only the existing stress check passed, never that a decision/action is qualified. */
    public static JournallerStressGate journallerStressGate(Context context) {
        if (!(context.stress() instanceof Known<Stress> known)) { return JournallerStressGate.SAME_FRAME_STRESS_UNAVAILABLE; }
        return known.value().points() < 100 ? JournallerStressGate.BELOW_URGENT_STRESS_THRESHOLD : JournallerStressGate.CONTINUE_NATIVE_GUARDS;
    }

    private static String effectiveCommand(JsonNode row) {
        JsonNode command = row.get("command");
        if (!isText(command, "auto-turn")) { return command != null && command.isTextual() ? command.textValue() : null; }
        JsonNode result = row.get("result"), automatic = result != null && result.isObject() ? result.get("auto_turn") : null;
        JsonNode selected = automatic != null && automatic.isObject() ? automatic.get("selected_step") : null;
        return selected != null && selected.isTextual() ? selected.textValue() : null;
    }
    private static JsonNode effectiveResult(JsonNode row) {
        JsonNode result = row.get("result");
        if (result == null || !result.isObject()) { return null; }
        if (!isText(row.get("command"), "auto-turn")) { return result; }
        for (String name : java.util.List.of("assault_action", "route_preview", "war_action", "war_progress_before", "war_progress_after")) {
            JsonNode factual = result.get(name); if (factual != null && factual.isObject()) { return result; }
        }
        JsonNode automatic = result.get("auto_turn"), nested = automatic != null && automatic.isObject() ? automatic.get("result") : null;
        return nested != null && nested.isObject() ? nested : result;
    }
    private static boolean sameFrameRoot(JsonNode result, JsonNode snapshot) {
        if (result == null || !result.isObject() || !isText(result.get("status"), "available")) { return false; }
        JsonNode root = result.get("campaign_root_context"), played = snapshot.get("played_character");
        if (root == null || !root.isObject() || !isText(root.get("status"), "available")) { return false; }
        if (played == null || !played.isObject()) { return false; }
        for (String key : java.util.List.of("snapshot_id", "revision", "native_revision")) {
            if (!equal(result.get("queried_" + key), snapshot.get(key))) { return false; }
        }
        JsonNode sequence = result.get("query_sequence");
        return equal(root.get("snapshot_revision"), snapshot.get("native_revision"))
                && equal(root.get("date_raw"), snapshot.get("date_raw"))
                && equal(root.get("player_character_id"), played.get("character_id"))
                && sequence != null && sequence.isIntegralNumber() && sequence.bigIntegerValue().signum() > 0;
    }
    private static boolean equal(JsonNode left, JsonNode right) { return left != null && right != null && left.equals(right); }
    private static boolean isText(JsonNode value, String text) { return value != null && value.isTextual() && value.textValue().equals(text); }
    private static boolean isTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
}
