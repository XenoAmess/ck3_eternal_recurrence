package org.xar.ck3.control.g2.m0.lossexposure;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m0.lossexposure.WarLossExposureBaseline.Available;
import org.xar.ck3.control.g2.m0.lossexposure.WarLossExposureBaseline.Observation;
import org.xar.ck3.control.g2.m0.lossexposure.WarLossExposureBaseline.Side;
import org.xar.ck3.control.g2.m0.lossexposure.WarLossExposureBaseline.SourceFrame;
import org.xar.ck3.control.g2.m0.lossexposure.WarLossExposureBaseline.Target;
import org.xar.ck3.control.g2.m0.lossexposure.WarLossExposureBaseline.Unavailable;
import org.xar.ck3.control.g2.m0.lossexposure.WarLossExposureBaseline.UnavailableReason;

/** Strict native wire boundary. Creates no action, utility, resolved loss, or live qualification. */
public final class WarLossExposureBaselineCodec {
    private static final Set<String> ROOT_FIELDS = Set.of("schema", "backend_id", "game_version", "executable_sha256",
            "status", "reason", "source_frame", "war_id", "player_side", "player_is_primary_war_leader",
            "targeted_title_ids", "targets", "settlement_effect_status", "settlement_effect_reason");
    private static final Set<String> FRAME_FIELDS = Set.of("snapshot_revision", "date_raw", "actor_character_id");
    private static final Set<String> TARGET_FIELDS = Set.of("title_id", "title_tier_raw", "title_tier_key",
            "holder_character_id", "holder_is_player", "holder_in_player_realm",
            "holder_immediate_liege_character_id", "holder_top_liege_character_id");
    private static final int MAX_BYTES = 1_048_576;

    private WarLossExposureBaselineCodec() { }

    public static Observation decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), ROOT_FIELDS);
        equalText(root.get("schema"), WarLossExposureBaseline.SCHEMA);
        equalText(root.get("backend_id"), WarLossExposureBaseline.BACKEND);
        equalText(root.get("game_version"), WarLossExposureBaseline.GAME_VERSION);
        equalText(root.get("executable_sha256"), WarLossExposureBaseline.EXECUTABLE_SHA256);
        equalText(root.get("settlement_effect_status"), "unavailable");
        equalText(root.get("settlement_effect_reason"), WarLossExposureBaseline.SETTLEMENT_REASON);
        Optional<SourceFrame> frame = root.get("source_frame").isNull()
                ? Optional.empty() : Optional.of(frame(root.get("source_frame")));
        Optional<Integer> war = nullableId(root.get("war_id"));
        String status = StrictJson.text(root.get("status"));
        if (status.equals("unavailable")) {
            for (String key : List.of("player_side", "player_is_primary_war_leader", "targeted_title_ids", "targets")) {
                require(root.get(key).isNull(), "unavailable material must be explicit null: " + key);
            }
            return new Unavailable(enumValue(UnavailableReason.class, root.get("reason")), frame, war);
        }
        require(status.equals("available"), "unknown native availability status");
        require(root.get("reason").isNull() && frame.isPresent() && war.isPresent(),
                "available native identity and null reason required");
        JsonNode idsNode = root.get("targeted_title_ids");
        JsonNode targetsNode = root.get("targets");
        require(idsNode.isArray() && targetsNode.isArray() && idsNode.size() <= 4096,
                "bounded complete target arrays required");
        List<Integer> ids = new ArrayList<>();
        for (JsonNode value : idsNode) { ids.add((int) StrictJson.integer(value, 0, Integer.MAX_VALUE)); }
        List<Target> targets = new ArrayList<>();
        for (JsonNode value : targetsNode) {
            ObjectNode row = StrictJson.object(value, TARGET_FIELDS);
            targets.add(new Target((int) StrictJson.integer(row.get("title_id"), 0, Integer.MAX_VALUE),
                    (int) StrictJson.integer(row.get("title_tier_raw"), 1, 6), StrictJson.text(row.get("title_tier_key")),
                    nullableId(row.get("holder_character_id")), bool(row.get("holder_is_player")),
                    bool(row.get("holder_in_player_realm")), nullableId(row.get("holder_immediate_liege_character_id")),
                    nullableId(row.get("holder_top_liege_character_id"))));
        }
        return new Available(frame.orElseThrow(), war.orElseThrow(), enumValue(Side.class, root.get("player_side")),
                bool(root.get("player_is_primary_war_leader")), ids, targets);
    }

    public static byte[] encode(Observation observation) {
        Objects.requireNonNull(observation, "observation");
        ObjectNode root = StrictJson.object();
        root.put("schema", WarLossExposureBaseline.SCHEMA);
        root.put("backend_id", WarLossExposureBaseline.BACKEND);
        root.put("game_version", WarLossExposureBaseline.GAME_VERSION);
        root.put("executable_sha256", WarLossExposureBaseline.EXECUTABLE_SHA256);
        root.put("settlement_effect_status", "unavailable");
        root.put("settlement_effect_reason", WarLossExposureBaseline.SETTLEMENT_REASON);
        switch (observation) {
            case Available available -> {
                root.put("status", "available"); root.putNull("reason");
                root.set("source_frame", frame(available.sourceFrame()));
                root.put("war_id", available.warId());
                root.put("player_side", wire(available.playerSide()));
                root.put("player_is_primary_war_leader", available.playerIsPrimaryWarLeader());
                var ids = root.putArray("targeted_title_ids"); available.targetedTitleIds().forEach(ids::add);
                var rows = root.putArray("targets");
                for (Target target : available.targets()) {
                    ObjectNode row = StrictJson.object();
                    row.put("title_id", target.titleId()); row.put("title_tier_raw", target.titleTierRaw());
                    row.put("title_tier_key", target.titleTierKey());
                    nullableId(row, "holder_character_id", target.holderCharacterId());
                    row.put("holder_is_player", target.holderIsPlayer());
                    row.put("holder_in_player_realm", target.holderInPlayerRealm());
                    nullableId(row, "holder_immediate_liege_character_id", target.holderImmediateLiegeCharacterId());
                    nullableId(row, "holder_top_liege_character_id", target.holderTopLiegeCharacterId()); rows.add(row);
                }
            }
            case Unavailable unavailable -> {
                root.put("status", "unavailable"); root.put("reason", wire(unavailable.reason()));
                if (unavailable.sourceFrame().isPresent()) {
                    root.set("source_frame", frame(unavailable.sourceFrame().orElseThrow()));
                } else { root.putNull("source_frame"); }
                nullableId(root, "war_id", unavailable.warId());
                for (String key : List.of("player_side", "player_is_primary_war_leader", "targeted_title_ids", "targets")) {
                    root.putNull(key);
                }
            }
        }
        return StrictJson.canonical(root, MAX_BYTES);
    }

    private static SourceFrame frame(JsonNode value) {
        ObjectNode root = StrictJson.object(value, FRAME_FIELDS);
        String revision = StrictJson.text(root.get("snapshot_revision"));
        require(revision.matches("[1-9][0-9]{0,19}"), "canonical positive uint64 decimal string required");
        return new SourceFrame(new BigInteger(revision), int32(root.get("date_raw")), id(root.get("actor_character_id")));
    }

    private static ObjectNode frame(SourceFrame value) {
        ObjectNode result = StrictJson.object(); result.put("snapshot_revision", value.snapshotRevision().toString());
        result.put("date_raw", value.dateRaw()); result.put("actor_character_id", value.actorCharacterId()); return result;
    }

    private static Optional<Integer> nullableId(JsonNode value) {
        require(value != null, "explicit nullable ID required");
        return value.isNull() ? Optional.empty() : Optional.of(id(value));
    }

    private static void nullableId(ObjectNode root, String key, Optional<Integer> value) {
        if (value.isPresent()) { root.put(key, value.orElseThrow()); } else { root.putNull(key); }
    }

    private static int id(JsonNode value) { int result = int32(value); require(result != -1, "native invalid ID sentinel"); return result; }
    private static int int32(JsonNode value) { return (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "exact JSON boolean required"); return value.booleanValue(); }
    private static void equalText(JsonNode value, String expected) { require(StrictJson.text(value).equals(expected), "native source identity or boundary differs"); }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static <T extends Enum<T>> T enumValue(Class<T> type, JsonNode value) {
        String key = StrictJson.text(value);
        for (T entry : type.getEnumConstants()) { if (wire(entry).equals(key)) { return entry; } }
        throw new IllegalArgumentException("unrecognized native " + type.getSimpleName());
    }
}
