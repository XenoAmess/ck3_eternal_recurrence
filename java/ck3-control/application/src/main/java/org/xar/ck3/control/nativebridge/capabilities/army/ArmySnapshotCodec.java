package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyResponses.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Full original service war_state slice, shared with the actual Driver and cold consumers. No partial row projection. */
public final class ArmySnapshotCodec {
    private ArmySnapshotCodec() { }
    public static WarState state(byte[] rawSemantic, String snapshotId, BigInteger publicRevision, BigInteger nativeRevision) {
        ObjectNode n = parse(rawSemantic), player = object(get(n, "played_character"));
        require(snapshotId != null && !snapshotId.isEmpty(), "actual snapshot identity required");
        new UInt64(publicRevision); UInt64.positive(nativeRevision);
        if (n.has("snapshot_id")) equal(n.get("snapshot_id"), snapshotId);
        if (n.has("revision")) equal(n.get("revision"), publicRevision);
        if (n.has("native_revision")) equal(n.get("native_revision"), nativeRevision);
        var wars = NativeActiveWarsCodec.normalize(n.get("active_wars"));
        var armies = ArmyStateProjection.playerArmiesFromState(wars, n.get("player_armies"));
        WarStateStatus status = !wars.isEmpty() ? WarStateStatus.ACTIVE : !armies.isEmpty() ? WarStateStatus.POSTWAR_ARMIES : WarStateStatus.IDLE;
        ObjectNode result = empty().put("status", status.name().toLowerCase(java.util.Locale.ROOT));
        result.set("active_wars", NativeActiveWarsCodec.encode(wars)); result.set("player_armies", NativeArmiesCodec.encode(armies));
        for (String key : List.of("war_termination_options", "war_termination_terms", "war_termination_exit_terms", "army_strengths")) result.set(key, retainedArray(n, key));
        // These are retained Driver wire slots, not new strength-domain authority. Their producer/consumer owns its strict contract.
        result.set("army_strengths_status", n.get("army_strengths_status"));
        result.set("army_strengths_query_sequence", n.get("army_strengths_query_sequence"));
        result.put("snapshot_id", snapshotId).put("revision", publicRevision);
        result.set("backend_id", n.get("backend_id"));
        return new WarState(status, snapshotId, publicRevision, nativeRevision, integer(get(n, "date_raw")), integer(get(player, "character_id")),
                wars, armies, DriverJson.object(bytes(result), DriverJson.MAX_NATIVE_BYTES));
    }
    public static RawJson encode(WarState value) { return new RawJson(OpportunityJson.encode(value.normalized())); }
    private static JsonNode retainedArray(ObjectNode source, String name) {
        JsonNode value = source.get(name);
        return value != null && value.isArray() ? value.deepCopy() : empty().putArray("items");
    }
}

