package org.xar.ck3.control.wave2.planning.scoretarget;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** One boundary for the active saved-war consumer stage and its exact metric rows. */
public final class RebellionMetricCodec {
    public static final String CONTROL_UNKNOWN_REASON = "存在本方防守战争，需核对CB及战前县集合后才能闭合治理集合G";
    private RebellionMetricCodec() { }

    public static SavedWarScan decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("player", "unknown_key_fields",
                "war_containers", "war_layout_unknown", "source_ref"));
        JsonNode count = row.get("unknown_key_fields");
        StrictJson.require(count.isIntegralNumber() && count.bigIntegerValue().signum() >= 0, "unknown-key count must be exact nonnegative integer");
        JsonNode layout = row.get("war_layout_unknown");
        StrictJson.require(layout.isBoolean(), "actual layout Boolean required");
        JsonNode paths = row.get("war_containers");
        StrictJson.require(paths.isArray(), "war containers must be actual path arrays");
        List<List<String>> containers = new ArrayList<>();
        for (JsonNode path : paths) {
            StrictJson.require(path.isArray(), "container path array required");
            List<String> tokens = new ArrayList<>();
            for (JsonNode token : path) { tokens.add(StrictJson.text(token)); }
            containers.add(List.copyOf(tokens));
        }
        // Keep actual float token kinds and unrelated SDK extensions; no tree re-encoding.
        PlayerWarInput player = PlayerWarDefenceCodec.input(row.get("player"));
        return new SavedWarScan(player, count.bigIntegerValue(), containers, layout.booleanValue(), StrictJson.text(row.get("source_ref")));
    }

    public static byte[] evaluate(byte[] raw) { return encode(RebellionMetricAdapter.project(decode(raw))); }

    public static byte[] encode(RebellionMetricDelta delta) {
        ObjectNode result = StrictJson.object(); ObjectNode scope;
        if (delta.scope() instanceof RebellionMetricDelta.ListedScope listed) {
            scope = PlayerWarDefenceCodec.audit(listed.result());
        } else if (delta.scope() instanceof RebellionMetricDelta.WorldScope world) {
            scope = StrictJson.object(); scope.put("method", "independent_complete_world_war_roster");
            scope.put("known", true); scope.put("own_defence", world.ownDefence());
            scope.put("reason", "ALL_WORLD_CB_DEFENDERS_VERIFIED");
        } else { throw new IllegalArgumentException("saved war scope required"); }
        scope.put("source_ref", delta.scope().sourceRef()); result.set("player_war_scope", scope);
        if (delta.update() instanceof RebellionMetricDelta.ObservedNoRebellion observed) {
            ObjectNode update = StrictJson.object(); update.put("metric", "rebel_share");
            update.set("observation", observation("0", observed.sourceRef(), observed.locator(), null));
            result.set("metric_update", update);
        } else if (delta.update() instanceof RebellionMetricDelta.UnknownControl unknown) {
            ObjectNode update = StrictJson.object(); update.put("metric", "control_average");
            update.set("observation", observation(null, unknown.sourceRef(), null, CONTROL_UNKNOWN_REASON));
            result.set("metric_update", update);
        } else { result.putNull("metric_update"); }
        return StrictJson.canonical(result);
    }

    private static ObjectNode observation(String value, String source, String locator, String reason) {
        ObjectNode row = StrictJson.object();
        if (value == null) { row.putNull("value"); } else { row.put("value", value); }
        row.put("unit", "fraction"); row.put("availability", value == null ? "unknown" : "observed");
        row.put("scope", "saved_current_player_realm"); row.put("source_ref", source);
        if (locator == null) { row.putNull("locator"); } else { row.put("locator", locator); }
        if (reason == null) { row.putNull("unavailable_reason"); } else { row.put("unavailable_reason", reason); }
        return row;
    }
}
