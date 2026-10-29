package org.xar.ck3.control.g2.m7;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.time.DateTimeException;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.format.ResolverStyle;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Goal;

/** Pure identity/intent comparison. The original binder alone owns actual cold lineage tokens. */
public final class CheckpointContinuity {
    private static final Pattern DMTF = Pattern.compile("([0-9]{14})\\.([0-9]{6})([+-])([0-9]{3})");
    private static final Pattern ISO = Pattern.compile("([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})\\.([0-9]{7})Z");
    private static final DateTimeFormatter DMTF_DATE = DateTimeFormatter.ofPattern("uuuuMMddHHmmss", Locale.ROOT)
            .withResolverStyle(ResolverStyle.STRICT);
    private static final DateTimeFormatter ISO_DATE = DateTimeFormatter.ofPattern("uuuu-MM-dd'T'HH:mm:ss", Locale.ROOT)
            .withResolverStyle(ResolverStyle.STRICT);
    private CheckpointContinuity() { }

    /** Raw creation_date and image remain exactly as observed; comparison parses without rounding. */
    public record GameIdentity(long pid, String creationDate, String executable) {
        public GameIdentity {
            StrictJson.require(pid > 0 && pid <= 0xffff_ffffL, "actual uint32 process PID required");
            StrictJson.text(creationDate); StrictJson.text(executable);
            StrictJson.require(!executable.isBlank(), "actual process image required");
            creationUtc(creationDate);
        }
    }
    public record Observation(String machineId, String sourceEpoch, GameIdentity game, String snapshotId,
            long revision, long nativeRevision, String episodeRunId, long actorCharacterId, long dateRaw,
            Goal goal, String governmentKey, String adapterFamily) implements Frame {
        public Observation {
            StrictJson.text(machineId); StrictJson.text(sourceEpoch); Objects.requireNonNull(game);
            StrictJson.require(sourceEpoch.matches("[0-9a-f]{64}"), "exact original source epoch required");
            StrictJson.text(snapshotId); StrictJson.safe(revision, 0); StrictJson.safe(nativeRevision, 0);
            StrictJson.text(episodeRunId); NativeCharacterId.of(actorCharacterId); StrictJson.safe(dateRaw, 0);
            Objects.requireNonNull(goal);
            StrictJson.require(goal.currentCharacterId() == actorCharacterId, "observed goal binds current episode actor");
            StrictJson.require((governmentKey == null) == (adapterFamily == null), "government key/family missing together");
            if (governmentKey != null) { StrictJson.text(governmentKey); StrictJson.text(adapterFamily); }
        }
    }
    public record Comparison(boolean sameGoal, boolean sameCampaignOrigin, boolean sameRulerEpisode,
            boolean sameMachine, boolean sameGameIdentity, boolean replacementBirthKnown,
            boolean governmentObservationComparable, boolean governmentKeyChanged, boolean adapterFamilyChanged) {
        public boolean grantsColdAuthority() { return false; }
        public boolean actionReplayAuthorized() { return false; }
    }

    /** Internal shared intent fields; these values never confer source or action authority. */
    interface Frame {
        String machineId(); OrdinaryCampaignGoal.Goal goal(); long actorCharacterId();
        String episodeRunId(); String governmentKey(); String adapterFamily();
    }
    public static Comparison compare(Observation before, Observation after) {
        Objects.requireNonNull(before); Objects.requireNonNull(after);
        return compareFrames(before, after, sameGameIdentity(before.game(), after.game()),
                !creationUtc(before.game().creationDate()).equals(creationUtc(after.game().creationDate())));
    }
    static Comparison compareFrames(Frame before, Frame after, boolean sameGame, boolean replacementBirth) {
        boolean machine = known(before.machineId()) && known(after.machineId()) && before.machineId().equals(after.machineId());
        boolean comparable = before.governmentKey() != null && after.governmentKey() != null;
        return new Comparison(before.goal().equals(after.goal()),
                before.goal().campaignId().equals(after.goal().campaignId())
                        && before.goal().originCharacterId() == after.goal().originCharacterId(),
                before.actorCharacterId() == after.actorCharacterId() && before.episodeRunId().equals(after.episodeRunId()),
                machine, machine && sameGame, machine && replacementBirth,
                comparable, comparable && !before.governmentKey().equals(after.governmentKey()),
                comparable && !before.adapterFamily().equals(after.adapterFamily()));
    }
    public static boolean sameGameIdentity(GameIdentity first, GameIdentity second) {
        Objects.requireNonNull(first); Objects.requireNonNull(second);
        return first.pid() == second.pid() && image(first.executable()).equals(image(second.executable()))
                && creationUtc(first.creationDate()).equals(creationUtc(second.creationDate()));
    }
    public static Instant creationUtc(String value) {
        try { return parseCreationUtc(value); }
        catch (DateTimeException error) { throw new ContractViolationException("invalid original process creation time", error); }
    }
    private static Instant parseCreationUtc(String value) {
        StrictJson.text(value); String text = value.strip(); Matcher dmtf = DMTF.matcher(text);
        if (dmtf.matches()) {
            int minutes = Integer.parseInt(dmtf.group(4));
            StrictJson.require(minutes <= 14 * 60, "DMTF process offset outside supported range");
            if (dmtf.group(3).equals("-")) { minutes = -minutes; }
            return boundedUtc(LocalDateTime.parse(dmtf.group(1), DMTF_DATE).withNano(Integer.parseInt(dmtf.group(2)) * 1_000),
                    ZoneOffset.ofTotalSeconds(minutes * 60));
        }
        Matcher iso = ISO.matcher(text);
        StrictJson.require(iso.matches() && iso.group(2).charAt(6) == '0',
                "known exact DMTF or microsecond-representable seven-digit ISO process birth required");
        return boundedUtc(LocalDateTime.parse(iso.group(1), ISO_DATE).withNano(Integer.parseInt(iso.group(2).substring(0, 6)) * 1_000),
                ZoneOffset.UTC);
    }
    private static Instant boundedUtc(LocalDateTime local, ZoneOffset offset) {
        StrictJson.require(local.getYear() >= 1 && local.getYear() <= 9999, "original process-time calendar range required");
        Instant result = local.toInstant(offset); int utcYear = result.atOffset(ZoneOffset.UTC).getYear();
        StrictJson.require(utcYear >= 1 && utcYear <= 9999, "UTC process instant stays inside original datetime range");
        return result;
    }
    public static byte[] encodeObservation(Observation observation) {
        return StrictJson.canonical(observationJson(observation), StrictJson.EXPLICIT_MAX_BYTES);
    }
    public static Observation decodeObservation(byte[] raw) { return parseObservation(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES)); }
    public static Observation parseObservation(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("machine_id", "source_epoch",
                "game_identity", "snapshot_id", "revision", "native_revision", "episode_run_id", "actor_character_id", "date_raw",
                "campaign_goal", "government_key", "adapter_family"));
        ObjectNode game = StrictJson.object(row.get("game_identity"), Set.of("pid", "creation_date", "executable"));
        return new Observation(text(row, "machine_id"), text(row, "source_epoch"), new GameIdentity(
                integer(game, "pid", 1), text(game, "creation_date"), text(game, "executable")), text(row, "snapshot_id"),
                integer(row, "revision", 0), integer(row, "native_revision", 0), text(row, "episode_run_id"),
                NativeCharacterId.fromJson(row.get("actor_character_id")).value(), integer(row, "date_raw", 0), GoalCodec.parseGoal(row.get("campaign_goal")),
                nullableText(row.get("government_key")), nullableText(row.get("adapter_family")));
    }
    public static byte[] encodeComparison(Comparison comparison) {
        ObjectNode row = StrictJson.object(); row.put("same_goal", comparison.sameGoal());
        row.put("same_campaign_origin", comparison.sameCampaignOrigin()); row.put("same_ruler_episode", comparison.sameRulerEpisode());
        row.put("same_machine", comparison.sameMachine()); row.put("same_game_identity", comparison.sameGameIdentity());
        row.put("replacement_birth_known", comparison.replacementBirthKnown());
        row.put("government_observation_comparable", comparison.governmentObservationComparable());
        row.put("government_key_changed", comparison.governmentKeyChanged()); row.put("adapter_family_changed", comparison.adapterFamilyChanged());
        row.put("cold_authority_granted", false); row.put("action_replay_authorized", false);
        return StrictJson.canonical(row);
    }
    private static ObjectNode observationJson(Observation value) {
        ObjectNode row = StrictJson.object(); row.put("machine_id", value.machineId()); row.put("source_epoch", value.sourceEpoch());
        ObjectNode game = row.putObject("game_identity"); game.put("pid", value.game().pid());
        game.put("creation_date", value.game().creationDate()); game.put("executable", value.game().executable());
        row.put("snapshot_id", value.snapshotId()); row.put("revision", value.revision()); row.put("native_revision", value.nativeRevision());
        row.put("episode_run_id", value.episodeRunId()); row.put("actor_character_id", value.actorCharacterId()); row.put("date_raw", value.dateRaw());
        row.set("campaign_goal", GoalCodec.goalJson(value.goal()));
        if (value.governmentKey() == null) { row.putNull("government_key"); row.putNull("adapter_family"); }
        else { row.put("government_key", value.governmentKey()); row.put("adapter_family", value.adapterFamily()); }
        return row;
    }
    private static String nullableText(JsonNode value) { return value.isNull() ? null : StrictJson.text(value); }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static long integer(ObjectNode row, String field, long minimum) { return StrictJson.integer(row.get(field), minimum, StrictJson.MAX_SAFE_INTEGER); }
    private static boolean known(String value) { return !Set.of("unknown", "none", "null").contains(value.strip().toLowerCase(Locale.ROOT)); }
    private static String image(String value) { return value.replace('\\', '/').toLowerCase(Locale.ROOT); }
}
