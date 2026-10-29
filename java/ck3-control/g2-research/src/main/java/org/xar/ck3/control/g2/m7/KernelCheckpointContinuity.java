package org.xar.ck3.control.g2.m7;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Goal;

/** Exact kernel identity DATA. Neither decoding nor comparison grants Native/cold/action authority. */
public final class KernelCheckpointContinuity {
    public static final String SCHEMA = "xar.g2.m7.kernel-observation/v1";
    private KernelCheckpointContinuity() { }

    public record Observation(String machineId, java.util.Optional<String> sourceEpoch, GameIdentity game, java.util.Optional<ExactRef> executable,
            String snapshotId, BigInteger revision, BigInteger nativeRevision, String episodeRunId, long actorCharacterId,
            long dateRaw, Goal goal, String governmentKey, String adapterFamily) implements CheckpointContinuity.Frame {
        public Observation {
            java.util.Objects.requireNonNull(sourceEpoch); java.util.Objects.requireNonNull(executable);
            StrictJson.text(machineId); Objects.requireNonNull(game);
            StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            if (sourceEpoch.isPresent()) {
                String epoch = sourceEpoch.get();
                StrictJson.require(epoch.matches("[0-9a-f]{64}"), "supplied source epoch must be exact hex");
            }
            if (executable.isPresent()) {
                ExactRef exe = executable.get();
                StrictJson.require(exe.bytes() > 0, "supplied executable reference must be nonempty");
            }
            StrictJson.require(revision != null && revision.signum() >= 0 && revision.compareTo(StrictJson.UINT64_MAX) <= 0
                    && nativeRevision != null && nativeRevision.signum() > 0 && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0,
                    "exact uint64 kernel public/native revisions required");
            StrictJson.safe(dateRaw, 0);
            NativeCharacterId.of(actorCharacterId);
            Objects.requireNonNull(goal);
            StrictJson.require(goal.currentCharacterId() == actorCharacterId, "actual goal belongs to this current ruler");
            StrictJson.require((governmentKey == null) == (adapterFamily == null), "government key/family absent together");
            if (governmentKey != null) { StrictJson.text(governmentKey); StrictJson.text(adapterFamily); }
        }
        /** Exact lossless construction for existing bounded observations; accessors retain the full uint64 domain. */
        public Observation(String machineId, String sourceEpoch, GameIdentity game, ExactRef executable, String snapshotId,
                BigInteger revision, BigInteger nativeRevision, String episodeRunId, long actorCharacterId, long dateRaw,
                Goal goal, String governmentKey, String adapterFamily) {
            this(machineId, java.util.Optional.of(sourceEpoch), game, java.util.Optional.of(executable), snapshotId, revision, nativeRevision,
                    episodeRunId, actorCharacterId, dateRaw, goal, governmentKey, adapterFamily);
        }
        public Observation(String machineId, String sourceEpoch, GameIdentity game, ExactRef executable, String snapshotId,
                long revision, long nativeRevision, String episodeRunId, long actorCharacterId, long dateRaw,
                Goal goal, String governmentKey, String adapterFamily) {
            this(machineId, java.util.Optional.of(sourceEpoch), game, java.util.Optional.of(executable), snapshotId, BigInteger.valueOf(revision), BigInteger.valueOf(nativeRevision),
                    episodeRunId, actorCharacterId, dateRaw, goal, governmentKey, adapterFamily);
        }
        public Observation(String machineId, java.util.Optional<String> sourceEpoch, GameIdentity game, java.util.Optional<ExactRef> executable, String snapshotId,
                long revision, long nativeRevision, String episodeRunId, long actorCharacterId, long dateRaw,
                Goal goal, String governmentKey, String adapterFamily) {
            this(machineId, sourceEpoch, game, executable, snapshotId, BigInteger.valueOf(revision), BigInteger.valueOf(nativeRevision),
                    episodeRunId, actorCharacterId, dateRaw, goal, governmentKey, adapterFamily);
        }
    }

    public static CheckpointContinuity.Comparison compare(Observation before, Observation after) {
        Objects.requireNonNull(before); Objects.requireNonNull(after);
        return CheckpointContinuity.compareFrames(before, after, sameGameIdentity(before, after),
                !before.game().creationFiletime().equals(after.game().creationFiletime()));
    }

    public static boolean sameGameIdentity(Observation first, Observation second) {
        Objects.requireNonNull(first); Objects.requireNonNull(second);
        if (!first.game().equals(second.game())) return false;
        if (first.executable().isPresent() && second.executable().isPresent()) {
            ExactRef e1 = first.executable().get();
            ExactRef e2 = second.executable().get();
            return image(e1.path()).equals(image(e2.path()))
                    && e1.bytes() == e2.bytes()
                    && e1.sha256().equals(e2.sha256());
        }
        return true;
    }

    public static byte[] encodeObservation(Observation value) { return StrictJson.canonical(toJson(value), StrictJson.EXPLICIT_MAX_BYTES); }
    public static Observation decodeObservation(byte[] raw) { return fromJson(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES)); }
    public static Observation fromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("schema", "machine_id", "game_identity",
                "snapshot_id", "revision", "native_revision", "episode_run_id", "actor_character_id", "date_raw",
                "campaign_goal", "government_key", "adapter_family"), Set.of("source_epoch"));
        StrictJson.require(SCHEMA.equals(text(row,"schema")), "kernel observation schema required");
        ObjectNode game = StrictJson.object(row.get("game_identity"), Set.of("pid", "creation_filetime"), Set.of("executable_ref"));
        java.util.Optional<String> epoch = row.has("source_epoch") && !row.get("source_epoch").isNull() ? java.util.Optional.of(text(row,"source_epoch")) : java.util.Optional.empty();
        java.util.Optional<ExactRef> exe = game.has("executable_ref") && !game.get("executable_ref").isNull() ? java.util.Optional.of(ExactRef.fromJson(game.get("executable_ref"))) : java.util.Optional.empty();
        return new Observation(text(row,"machine_id"), epoch,
                new GameIdentity(StrictJson.integer(game.get("pid"),1,0xffff_ffffL),text(game,"creation_filetime")),
                exe,text(row,"snapshot_id"),
                StrictJson.integer(row.get("revision"),BigInteger.ZERO,StrictJson.UINT64_MAX),
                StrictJson.integer(row.get("native_revision"),BigInteger.ONE,StrictJson.UINT64_MAX),text(row,"episode_run_id"),NativeCharacterId.fromJson(row.get("actor_character_id")).value(),
                integer(row,"date_raw",0),GoalCodec.parseGoal(row.get("campaign_goal")),
                nullable(row.get("government_key")),nullable(row.get("adapter_family")));
    }
    public static ObjectNode toJson(Observation value) {
        Objects.requireNonNull(value); ObjectNode row = StrictJson.object(); row.put("schema",SCHEMA);
        row.put("machine_id",value.machineId());
        if (value.sourceEpoch().isPresent()) row.put("source_epoch", value.sourceEpoch().get()); else row.putNull("source_epoch");
        ObjectNode game=row.putObject("game_identity"); game.put("pid",value.game().pid());
        game.put("creation_filetime",value.game().creationFiletime());
        if (value.executable().isPresent()) game.set("executable_ref", value.executable().get().toJson()); else game.putNull("executable_ref");
        row.put("snapshot_id",value.snapshotId()); row.put("revision",value.revision()); row.put("native_revision",value.nativeRevision());
        row.put("episode_run_id",value.episodeRunId()); row.put("actor_character_id",value.actorCharacterId()); row.put("date_raw",value.dateRaw());
        row.set("campaign_goal",GoalCodec.goalJson(value.goal()));
        if(value.governmentKey()==null) { row.putNull("government_key"); row.putNull("adapter_family"); }
        else { row.put("government_key",value.governmentKey()); row.put("adapter_family",value.adapterFamily()); }
        return row;
    }
    private static String image(String value) { return value.replace('\\','/').toLowerCase(java.util.Locale.ROOT); }
    private static String text(ObjectNode row,String key) { return StrictJson.text(row.get(key)); }
    private static long integer(ObjectNode row,String key,long minimum) { return StrictJson.integer(row.get(key),minimum,StrictJson.MAX_SAFE_INTEGER); }
    private static String nullable(JsonNode value) {
        StrictJson.require(value!=null,"explicit nullable field required"); return value.isNull()?null:StrictJson.text(value);
    }
}
