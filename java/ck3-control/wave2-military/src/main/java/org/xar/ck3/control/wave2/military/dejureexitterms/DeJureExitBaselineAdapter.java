package org.xar.ck3.control.wave2.military.dejureexitterms;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.Frame;

/** Existing ordinary native-driver returned-result path; intentionally no H2743 admission or native transport. */
public final class DeJureExitBaselineAdapter {
    private DeJureExitBaselineAdapter() { }

    public record DriverFrame(String snapshotId, BigInteger revision, BigInteger nativeRevision,
                              BigInteger connectionGeneration, String episodeRunId) {
        public DriverFrame {
            StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            require(revision != null && revision.signum() >= 0 && nativeRevision != null && nativeRevision.signum() > 0
                    && connectionGeneration != null && connectionGeneration.signum() >= 0, "complete exact native frame required");
        }
        public boolean samePausedNativeFrame(DriverFrame other) {
            return other != null && snapshotId.equals(other.snapshotId) && nativeRevision.equals(other.nativeRevision)
                    && connectionGeneration.equals(other.connectionGeneration) && episodeRunId.equals(other.episodeRunId);
        }
    }
    public record BoundBaseline(DeJureExitBaseline baseline, BigInteger querySequence, String backendId, DriverFrame queriedFrame) {
        public BoundBaseline {
            require(baseline != null && queriedFrame != null && querySequence != null && querySequence.signum() > 0
                    && querySequence.compareTo(StrictJson.UINT64_MAX) <= 0, "bound baseline with exact positive uint64 sequence required");
            StrictJson.text(backendId);
            require(queriedFrame.nativeRevision().equals(BigInteger.valueOf(baseline.expectedFrame().nativeRevision())), "baseline native revision differs");
        }
    }

    /** Validates real returned bytes plus before/after SDK projections; it dispatches nothing. */
    public static BoundBaseline bindReturnedBaseline(byte[] rawResult, byte[] rawBefore, byte[] rawAfter, int warId) {
        require(warId > 0, "positive signed query WarID required");
        JsonNode before = StrictJson.parse(rawBefore, DeJureExitBaselineCodec.MAX_BYTES);
        JsonNode after = StrictJson.parse(rawAfter, DeJureExitBaselineCodec.MAX_BYTES);
        DriverFrame startingFrame = frame(before), endingFrame = frame(after);
        JsonNode war = war(before, warId).orElseThrow(() -> new ContractViolationException("primary defender war absent"));
        require(startingFrame.samePausedNativeFrame(endingFrame) && war(after, warId).filter(war::equals).isPresent(), "baseline crossed native war frame");
        DeJureExitBaselineCodec.literal(war.get("player_side"), "defender"); StrictJson.trueValue(war.get("player_is_primary_war_leader"));
        Frame expected = new Frame(warId, DeJureExitBaselineCodec.nativeInt(before.get("native_revision"), true),
                DeJureExitBaselineCodec.nativeInt(before.get("date_raw"), false),
                DeJureExitBaselineCodec.nativeInt(before.path("played_character").get("character_id"), true),
                DeJureExitBaselineCodec.nativeInt(war.get("primary_opponent_character_id"), true), DeJureExitBaselineCodec.ids(war.get("targeted_title_ids")));
        ObjectNode result = StrictJson.object(StrictJson.parse(rawResult, DeJureExitBaselineCodec.MAX_BYTES),
                Set.of("step", "accepted", "status", "query_sequence", "defender_de_jure_exit_terms_v1", "backend_id"));
        DeJureExitBaselineCodec.literal(result.get("step"), DeJureExitBaselineCodec.queryStep(warId)); StrictJson.trueValue(result.get("accepted"));
        DeJureExitBaselineCodec.literal(result.get("status"), "baseline_only");
        return new BoundBaseline(DeJureExitBaselineCodec.decodeNode(result.get("defender_de_jure_exit_terms_v1"), expected),
                StrictJson.integer(result.get("query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX), StrictJson.text(result.get("backend_id")), startingFrame);
    }
    public static byte[] encodeDriverResult(BoundBaseline value) {
        require(value != null, "bound baseline required"); ObjectNode result = StrictJson.object();
        long warId = value.baseline().expectedFrame().warId(); require(warId <= Integer.MAX_VALUE, "native query WarID outside int32");
        result.put("step", DeJureExitBaselineCodec.queryStep((int) warId)); result.put("accepted", true); result.put("status", "baseline_only");
        result.put("query_sequence", value.querySequence()); result.put("backend_id", value.backendId());
        result.set("defender_de_jure_exit_terms_v1", DeJureExitBaselineCodec.projectionNode(value.baseline()));
        result.put("queried_snapshot_id", value.queriedFrame().snapshotId()); result.put("queried_revision", value.queriedFrame().revision());
        result.put("queried_native_revision", value.queriedFrame().nativeRevision());
        return StrictJson.canonical(result, DeJureExitBaselineCodec.MAX_BYTES);
    }
    private static DriverFrame frame(JsonNode root) {
        require(root != null && root.isObject(), "extensible SDK snapshot required"); StrictJson.trueValue(root.get("paused"));
        return new DriverFrame(StrictJson.text(root.get("snapshot_id")), integer(root.get("revision")), integer(root.get("native_revision")),
                integer(root.path("diagnostics").get("connection_generation")), StrictJson.text(root.get("episode_run_id")));
    }
    private static Optional<JsonNode> war(JsonNode root, int warId) {
        JsonNode rows = root.get("active_wars"); require(rows != null && rows.isArray(), "active wars required");
        for (JsonNode row : rows) {
            JsonNode id = row.get("war_id");
            if (row.isObject() && id != null && id.isIntegralNumber() && id.bigIntegerValue().equals(BigInteger.valueOf(warId))) { return Optional.of(row); }
        }
        return Optional.empty();
    }
    private static BigInteger integer(JsonNode value) {
        require(value != null && value.isIntegralNumber(), "exact SDK JSON integer required"); return value.bigIntegerValue();
    }
}
