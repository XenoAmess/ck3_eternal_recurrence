package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;

public record SavedFrame(String snapshotId, long revision, long nativeRevision, long dateRaw,
                         long actorCharacterId, String episodeRunId) {
    public SavedFrame {
        StrictJson.text(snapshotId);
        StrictJson.safe(revision, 1); StrictJson.safe(nativeRevision, 1);
        StrictJson.safe(dateRaw, 0); NativeCharacterId.of(actorCharacterId);
        StrictJson.text(episodeRunId);
        StrictJson.require(snapshotId.equals("native:" + nativeRevision), "native snapshot identity");
    }
    public static SavedFrame fromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("snapshot_id", "revision", "native_revision",
                "date_raw", "actor_character_id", "episode_run_id"));
        return new SavedFrame(StrictJson.text(row.get("snapshot_id")),
                StrictJson.integer(row.get("revision"), 1, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(row.get("native_revision"), 1, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(row.get("date_raw"), 0, StrictJson.MAX_SAFE_INTEGER),
                NativeCharacterId.fromJson(row.get("actor_character_id")).value(),
                StrictJson.text(row.get("episode_run_id")));
    }
    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object();
        row.put("snapshot_id", snapshotId); row.put("revision", revision);
        row.put("native_revision", nativeRevision); row.put("date_raw", dateRaw);
        row.put("actor_character_id", actorCharacterId); row.put("episode_run_id", episodeRunId);
        return row;
    }
}
