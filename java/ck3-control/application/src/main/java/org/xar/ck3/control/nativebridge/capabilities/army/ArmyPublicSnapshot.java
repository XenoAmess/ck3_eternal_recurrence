package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** The actual semantic frame used by an original public query; absent/nullable hello fields remain nullable. */
public record ArmyPublicSnapshot(Context context, Obj semantic) {
    public ArmyPublicSnapshot {
        Objects.requireNonNull(context); Objects.requireNonNull(semantic);
        ObjectNode snapshot = object(OpportunityJson.toNode(semantic));
        equal(get(snapshot, "snapshot_id"), context.before().frame().snapshotId());
        equal(get(snapshot, "revision"), context.before().frame().revision());
        equal(get(snapshot, "native_revision"), context.nativeRevision()); equal(get(snapshot, "date_raw"), context.dateRaw());
        yes(get(snapshot, "paused"));
    }
    public ObjectNode hello() {
        JsonNode diagnostics = object(OpportunityJson.toNode(semantic)).get("diagnostics");
        JsonNode hello = diagnostics != null && diagnostics.isObject() ? diagnostics.get("hello") : null;
        return hello != null && hello.isObject() ? ((ObjectNode) hello).deepCopy() : empty();
    }
    public ObjectNode source() {
        ObjectNode snapshot = object(OpportunityJson.toNode(semantic)), hello = hello(), result = empty();
        copyNullable(result, "game_version", hello.get("game_version")); copyNullable(result, "executable_sha256", hello.get("executable_sha256"));
        for (String field : java.util.List.of("snapshot_id", "revision", "native_revision", "date_raw", "backend_id")) copyNullable(result, field, snapshot.get(field));
        return result.put("paused", true);
    }
    static void copyNullable(ObjectNode target, String field, JsonNode value) { target.set(field, value == null ? empty().nullNode() : value.deepCopy()); }
}
