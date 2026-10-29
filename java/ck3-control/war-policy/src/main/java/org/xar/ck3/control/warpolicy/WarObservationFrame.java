package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** War observation DATA: uint64 revisions and the original signed public native character ID. */
public record WarObservationFrame(String snapshotId, BigInteger revision,
        BigInteger nativeRevision, int dateRaw, String episodeRunId,
        int playedCharacterId, long bridgePid, BigInteger connectionGeneration) {
    public WarObservationFrame {
        StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
        require(revision != null && revision.signum() > 0 && revision.compareTo(StrictJson.UINT64_MAX) <= 0,
                "revision outside positive uint64");
        require(nativeRevision != null && nativeRevision.signum() > 0
                && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "native revision outside positive uint64");
        require(connectionGeneration != null && connectionGeneration.signum() > 0
                && connectionGeneration.compareTo(StrictJson.UINT64_MAX) <= 0, "connection outside positive uint64");
        require(snapshotId.equals("native:" + nativeRevision), "snapshot/native revision mismatch");
        NativeCharacterId.of(playedCharacterId);
        require(bridgePid > 0 && bridgePid <= 4_294_967_295L, "bridge identity outside contract");
    }

    public static WarObservationFrame fromSnapshot(JsonNode raw) {
        ObjectNode snapshot = WarJson.record(raw, "snapshot");
        ObjectNode player = WarJson.record(snapshot.get("played_character"), "played_character");
        ObjectNode diagnostics = WarJson.record(snapshot.get("diagnostics"), "diagnostics");
        return new WarObservationFrame(StrictJson.text(snapshot.get("snapshot_id")),
            WarJson.positive64(snapshot.get("revision")), WarJson.positive64(snapshot.get("native_revision")),
            WarJson.signed32(snapshot.get("date_raw")), StrictJson.text(snapshot.get("episode_run_id")),
            NativeCharacterId.fromJson(player.get("character_id")).value(),
            StrictJson.integer(diagnostics.get("bridge_pid"), BigInteger.ONE, WarJson.UINT32_MAX).longValueExact(),
            WarJson.positive64(diagnostics.get("connection_generation")));
    }

    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object();
        row.put("snapshot_id", snapshotId); row.put("revision", revision);
        row.put("native_revision", nativeRevision); row.put("date_raw", dateRaw);
        row.put("episode_run_id", episodeRunId); row.put("played_character_id", playedCharacterId);
        row.put("bridge_pid", bridgePid); row.put("connection_generation", connectionGeneration);
        return row;
    }
}
