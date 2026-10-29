package org.xar.ck3.control.wave2.planning.scoreinputs;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** The already-obtained planning frame identity; carries no native freshness grant. */
public record ScoreInputFrame(String snapshotId, BigInteger revision, BigInteger nativeRevision,
        int dateRaw, String episodeRunId, BigInteger actorCharacterId, long bridgePid,
        BigInteger connectionGeneration) {
    static final BigInteger UINT32_MAX = new BigInteger("4294967295");
    private static final Set<String> FIELDS = Set.of("snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "actor_character_id", "bridge_pid", "connection_generation");

    public ScoreInputFrame {
        StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
        require(inRange(revision, BigInteger.ZERO, StrictJson.UINT64_MAX)
                && inRange(nativeRevision, BigInteger.ZERO, StrictJson.UINT64_MAX), "uint64 revisions required");
        require(inRange(actorCharacterId, BigInteger.ONE, UINT32_MAX), "positive uint32 actor required");
        require(bridgePid >= 1 && bridgePid <= 4_294_967_295L, "positive uint32 bridge PID required");
        require(inRange(connectionGeneration, BigInteger.ZERO, StrictJson.UINT64_MAX), "uint64 connection generation required");
    }

    public static ScoreInputFrame fromJson(JsonNode input) {
        ObjectNode object = StrictJson.object(input, FIELDS);
        return new ScoreInputFrame(StrictJson.text(object.get("snapshot_id")),
                StrictJson.integer(object.get("revision"), BigInteger.ZERO, StrictJson.UINT64_MAX),
                StrictJson.integer(object.get("native_revision"), BigInteger.ZERO, StrictJson.UINT64_MAX),
                (int) StrictJson.integer(object.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                StrictJson.text(object.get("episode_run_id")),
                StrictJson.integer(object.get("actor_character_id"), BigInteger.ONE, UINT32_MAX),
                StrictJson.integer(object.get("bridge_pid"), 1, 4_294_967_295L),
                StrictJson.integer(object.get("connection_generation"), BigInteger.ZERO, StrictJson.UINT64_MAX));
    }

    public ObjectNode toJson() {
        ObjectNode object = StrictJson.object();
        object.put("snapshot_id", snapshotId); object.put("revision", revision); object.put("native_revision", nativeRevision);
        object.put("date_raw", dateRaw); object.put("episode_run_id", episodeRunId); object.put("actor_character_id", actorCharacterId);
        object.put("bridge_pid", bridgePid); object.put("connection_generation", connectionGeneration);
        return object;
    }

    static boolean inRange(BigInteger value, BigInteger minimum, BigInteger maximum) {
        return value != null && value.compareTo(minimum) >= 0 && value.compareTo(maximum) <= 0;
    }
}
