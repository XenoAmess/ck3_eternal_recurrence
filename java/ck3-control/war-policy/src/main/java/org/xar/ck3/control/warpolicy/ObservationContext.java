package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Caller-supplied actual observation identity, separate from registry research identity. */
public record ObservationContext(String machineId, String observedAtUtc,
        String snapshotSource, String snapshotSha256) {
    public ObservationContext {
        StrictJson.text(machineId); StrictJson.text(snapshotSource); StrictJson.text(snapshotSha256);
        require(observedAtUtc != null && observedAtUtc.matches(
            "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\\.[0-9]{1,6})?Z"),
            "observation UTC spelling differs from this version's oracle");
        require(snapshotSha256.matches("[0-9a-f]{64}"), "canonical observation SHA-256 required");
    }

    public static ObservationContext fromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value,
            Set.of("machine_id", "observed_at_utc", "snapshot_source", "snapshot_sha256"));
        return new ObservationContext(StrictJson.text(row.get("machine_id")),
            StrictJson.text(row.get("observed_at_utc")), StrictJson.text(row.get("snapshot_source")),
            WarJson.sha(row.get("snapshot_sha256")));
    }

    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object(); row.put("machine_id", machineId);
        row.put("observed_at_utc", observedAtUtc); row.put("snapshot_source", snapshotSource);
        row.put("snapshot_sha256", snapshotSha256); return row;
    }
}
