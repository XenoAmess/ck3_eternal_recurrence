package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.contracts.semantic.FlorinWarIdentityData.*;

/** Frozen War-only Native result codec. Public decoded DATA never attests a live receiver, full Snapshot or action role. */
public final class FlorinWarIdentityCodec {
    public static final String STEP = "query-active-wars-identity-v1";
    public static final String CAPABILITY = "game.query.active-wars-identity.v1";
    public static final String ADAPTER = "ck3-1.21.0-msvc-x64";
    public static final String BACKEND = "ck3-1.21.0-native-headless-main-thread";
    public static final String RICH_REASON = RICH_UNAVAILABLE_REASON;
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;
    private static final Set<String> ROOT = Set.of("step", "schema", "game_version", "executable_sha256", "adapter_id", "backend",
            "status", "complete_snapshot", "application_main_observed", "identity_available", "same_frame_ready", "score_complete",
            "full_snapshot_available", "complete_active_wars_qualified", "core_frame", "active_wars", "war_slots_scanned",
            "active_war_rows", "ended_war_rows", "participant_records", "native_score_calls_attempted", "unavailable_reason");
    private static final Set<String> CORE = Set.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "status",
            "complete_snapshot", "core_available", "application_main_observed", "unavailable_reason", "excluded_snapshot_families",
            "date_raw", "speed", "paused", "local_player_id", "map_ready", "has_played_character", "played_character_id", "played_character_alive");
    private static final Set<String> ROW = Set.of("war_id", "actual_player_character_id", "player_side", "primary_attacker_character_id",
            "primary_defender_character_id", "primary_opponent_character_id", "player_is_primary_war_leader", "attacker_participant_ids",
            "defender_participant_ids", "native_attacker_score_raw", "player_relative_war_score", "score_unavailable_reason", "rich");
    private static final List<String> CORE_VALUES = List.of("date_raw", "speed", "paused", "local_player_id", "map_ready",
            "has_played_character", "played_character_id", "played_character_alive");
    private static final List<String> COUNTS = List.of("war_slots_scanned", "active_war_rows", "ended_war_rows", "participant_records");
    private FlorinWarIdentityCodec() { }

    public static Observation decode(byte[] original) { return read(StrictJson.parse(original)); }

    public static Observation read(JsonNode original) {
        ObjectNode root = object(original); keys(root, ROOT); requireSource(root, SCHEMA);
        need(STEP.equals(text(root.get("step"))), "War identity step differs");
        need(!bool(root.get("complete_snapshot")) && !bool(root.get("full_snapshot_available"))
                && !bool(root.get("complete_active_wars_qualified")), "War identity must remain partial DATA");
        Core core = core(root.get("core_frame"));
        boolean applicationMain = bool(root.get("application_main_observed"));
        boolean identity = bool(root.get("identity_available")), sameFrame = bool(root.get("same_frame_ready"));
        boolean scores = bool(root.get("score_complete"));
        int calls = i32(root.get("native_score_calls_attempted"));
        if (!identity) {
            need("unavailable".equals(text(root.get("status"))) && !sameFrame && !scores && root.get("active_wars").isNull(),
                    "unavailable War identity cannot retain values or an empty collection");
            for (String key : COUNTS) need(root.get(key).isNull(), "unavailable War scan count must remain null: " + key);
            return new Unavailable(core, applicationMain, calls, text(root.get("unavailable_reason")));
        }
        need("partial".equals(text(root.get("status"))) && applicationMain && sameFrame && root.get("unavailable_reason").isNull()
                && core instanceof AvailableCore, "available War identity requires its observed Core and same-frame partial status");
        JsonNode rows = root.get("active_wars"); array(rows, MAX_OWNED_WARS);
        List<Identity> wars = new ArrayList<>();
        for (JsonNode raw : rows) wars.add(identity(raw));
        return new Partial((AvailableCore) core, wars, scores,
                new ScanMetrics(i32(root.get("war_slots_scanned")), i32(root.get("active_war_rows")),
                        i32(root.get("ended_war_rows")), i32(root.get("participant_records"))), calls);
    }

    private static Identity identity(JsonNode raw) {
        ObjectNode row = object(raw); keys(row, ROW);
        Side side = switch (text(row.get("player_side"))) {
            case "attacker" -> Side.ATTACKER;
            case "defender" -> Side.DEFENDER;
            default -> throw new IllegalArgumentException("closed War side token required");
        };
        OptionalInt attackerScore = optionalI32(row.get("native_attacker_score_raw"));
        OptionalInt relative = optionalI32(row.get("player_relative_war_score"));
        Score score;
        if (relative.isPresent()) {
            need(attackerScore.isPresent() && row.get("score_unavailable_reason").isNull(), "observed relative score requires raw score and null reason");
            score = new AvailableScore(attackerScore.orElseThrow(), relative.orElseThrow());
        } else score = new UnavailableScore(attackerScore, text(row.get("score_unavailable_reason")));
        ObjectNode rich = object(row.get("rich"));
        keys(rich, java.util.Arrays.stream(RichField.values()).map(FlorinWarIdentityCodec::wire).collect(java.util.stream.Collectors.toSet()));
        List<UnavailableField> gaps = new ArrayList<>();
        for (RichField field : RichField.values()) {
            ObjectNode gap = object(rich.get(wire(field))); keys(gap, Set.of("status", "unavailable_reason"));
            need("unavailable".equals(text(gap.get("status"))) && RICH_REASON.equals(text(gap.get("unavailable_reason"))),
                    "unobserved rich War field cannot be relabelled or replaced by a default");
            gaps.add(new UnavailableField(field, RICH_REASON));
        }
        return new Identity(new WarFullId(i32(row.get("war_id"))), character(row.get("actual_player_character_id")), side,
                character(row.get("primary_attacker_character_id")), character(row.get("primary_defender_character_id")),
                character(row.get("primary_opponent_character_id")), bool(row.get("player_is_primary_war_leader")),
                characters(row.get("attacker_participant_ids")), characters(row.get("defender_participant_ids")), score, gaps);
    }

    private static Core core(JsonNode original) {
        ObjectNode row = object(original); keys(row, CORE); requireSource(row, "ck3_1210_core_frame_v1");
        need(!bool(row.get("complete_snapshot")), "War Core cannot become a complete Snapshot");
        JsonNode excluded = row.get("excluded_snapshot_families"); array(excluded, 4);
        List<String> families = new ArrayList<>(); for (JsonNode value : excluded) families.add(text(value));
        need(families.equals(List.of("treasury", "domain", "military", "campaign")), "War Core excluded families differ");
        boolean available = bool(row.get("core_available")), observed = bool(row.get("application_main_observed"));
        if (!available) {
            need("unavailable".equals(text(row.get("status"))), "War Core unavailable status differs");
            for (String key : CORE_VALUES) need(row.get(key).isNull(), "unavailable War Core values must remain null");
            return new UnavailableCore(observed, text(row.get("unavailable_reason")));
        }
        need("partial".equals(text(row.get("status"))) && observed && row.get("unavailable_reason").isNull(), "observed War Core status differs");
        return new AvailableCore(new Prefix(i32(row.get("date_raw")), i32(row.get("speed")), bool(row.get("paused")),
                i32(row.get("local_player_id")), bool(row.get("map_ready")), bool(row.get("has_played_character")),
                i32(row.get("played_character_id")), bool(row.get("played_character_alive"))));
    }

    /** Canonical serialization preserves unavailable/null values, ordered participants and the separate signed ID domains. */
    public static ObjectNode encode(Observation data) {
        java.util.Objects.requireNonNull(data); ObjectNode row = JSON.objectNode(); putSource(row, SCHEMA);
        row.put("step", STEP).put("status", data instanceof Partial ? "partial" : "unavailable")
                .put("complete_snapshot", false).put("application_main_observed", data.applicationMainObserved())
                .put("identity_available", data instanceof Partial).put("same_frame_ready", data instanceof Partial)
                .put("full_snapshot_available", false).put("complete_active_wars_qualified", false)
                .put("native_score_calls_attempted", data.nativeScoreCallsAttempted());
        row.set("core_frame", encodeCore(data.coreFrame()));
        if (data instanceof Partial partial) {
            row.put("score_complete", partial.scoreComplete()).putNull("unavailable_reason");
            ScanMetrics counts = partial.metrics();
            row.put("war_slots_scanned", counts.warSlotsScanned()).put("active_war_rows", counts.activeWarRows())
                    .put("ended_war_rows", counts.endedWarRows()).put("participant_records", counts.participantRecords());
            var wars = row.putArray("active_wars");
            for (Identity identity : partial.activeWars()) wars.add(encodeIdentity(identity));
        } else {
            row.put("score_complete", false).putNull("active_wars").put("unavailable_reason", ((Unavailable) data).reason());
            for (String key : COUNTS) row.putNull(key);
        }
        need(read(row).equals(data), "War DATA encoding crossed its validated typed contract"); return row;
    }

    private static ObjectNode encodeIdentity(Identity data) {
        ObjectNode row = JSON.objectNode().put("war_id", data.warId().value())
                .put("actual_player_character_id", data.actualPlayerCharacterId().value())
                .put("player_side", data.playerSide() == Side.ATTACKER ? "attacker" : "defender")
                .put("primary_attacker_character_id", data.primaryAttackerCharacterId().value())
                .put("primary_defender_character_id", data.primaryDefenderCharacterId().value())
                .put("primary_opponent_character_id", data.primaryOpponentCharacterId().value())
                .put("player_is_primary_war_leader", data.playerIsPrimaryWarLeader());
        var attack = row.putArray("attacker_participant_ids"); data.attackerParticipantIds().forEach(id -> attack.add(id.value()));
        var defend = row.putArray("defender_participant_ids"); data.defenderParticipantIds().forEach(id -> defend.add(id.value()));
        if (data.score() instanceof AvailableScore score) {
            row.put("native_attacker_score_raw", score.nativeAttackerRaw()).put("player_relative_war_score", score.playerRelative())
                    .putNull("score_unavailable_reason");
        } else {
            UnavailableScore score = (UnavailableScore) data.score();
            if (score.nativeAttackerRaw().isPresent()) row.put("native_attacker_score_raw", score.nativeAttackerRaw().getAsInt());
            else row.putNull("native_attacker_score_raw");
            row.putNull("player_relative_war_score").put("score_unavailable_reason", score.reason());
        }
        ObjectNode rich = row.putObject("rich");
        for (UnavailableField field : data.richFields()) rich.putObject(wire(field.field()))
                .put("status", "unavailable").put("unavailable_reason", field.reason());
        return row;
    }

    private static ObjectNode encodeCore(Core core) {
        ObjectNode row = JSON.objectNode(); putSource(row, "ck3_1210_core_frame_v1");
        row.put("complete_snapshot", false); var excluded = row.putArray("excluded_snapshot_families");
        List.of("treasury", "domain", "military", "campaign").forEach(excluded::add);
        if (core instanceof AvailableCore actual) {
            Prefix p = actual.prefix();
            row.put("status", "partial").put("core_available", true).put("application_main_observed", true).putNull("unavailable_reason")
                    .put("date_raw", p.dateRaw()).put("speed", p.speed()).put("paused", p.paused()).put("local_player_id", p.localPlayerId())
                    .put("map_ready", p.mapReady()).put("has_played_character", p.hasPlayedCharacter())
                    .put("played_character_id", p.playedCharacterId()).put("played_character_alive", p.playedCharacterAlive());
        } else {
            UnavailableCore missing = (UnavailableCore) core;
            row.put("status", "unavailable").put("core_available", false).put("application_main_observed", missing.applicationMainObserved())
                    .put("unavailable_reason", missing.reason());
            for (String key : CORE_VALUES) row.putNull(key);
        }
        return row;
    }

    private static List<NativeCharacterId> characters(JsonNode rows) {
        array(rows, MAX_SIDE); List<NativeCharacterId> values = new ArrayList<>();
        for (JsonNode id : rows) values.add(character(id)); return List.copyOf(values);
    }
    private static NativeCharacterId character(JsonNode value) { return NativeCharacterId.fromJson(value); }
    private static OptionalInt optionalI32(JsonNode value) {
        need(value != null, "explicit nullable signed32 score required");
        return value.isNull() ? OptionalInt.empty() : OptionalInt.of(i32(value));
    }
    private static int i32(JsonNode value) {
        return StrictJson.integer(value, BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();
    }
    private static void array(JsonNode value, int limit) { need(value != null && value.isArray() && value.size() <= limit, "bounded explicit War array required"); }
    private static String text(JsonNode value) { return StrictJson.text(value); }
    private static boolean bool(JsonNode value) { need(value != null && value.isBoolean(), "exact War boolean token required"); return value.booleanValue(); }
    private static ObjectNode object(JsonNode value) { need(value instanceof ObjectNode, "War DATA object required"); return (ObjectNode) value; }
    private static void keys(ObjectNode row, Set<String> expected) {
        var actual = new HashSet<String>(); row.fieldNames().forEachRemaining(actual::add);
        need(actual.equals(expected), "exact War DATA fields required");
    }
    private static String wire(RichField field) { return field.name().toLowerCase(Locale.ROOT); }
    private static void putSource(ObjectNode row, String schema) {
        row.put("schema", schema).put("game_version", ExactCk3Build.CK3_1210.version())
                .put("executable_sha256", ExactCk3Build.CK3_1210.executableSha256().toUpperCase(Locale.ROOT))
                .put("adapter_id", ADAPTER).put("backend", BACKEND);
    }
    private static void requireSource(JsonNode value, String schema) {
        ObjectNode row = object(value);
        need(schema.equals(text(row.get("schema"))) && ExactCk3Build.CK3_1210.matches(text(row.get("game_version")), text(row.get("executable_sha256")))
                && ADAPTER.equals(text(row.get("adapter_id"))) && BACKEND.equals(text(row.get("backend"))), "exact Florin War source tuple required");
    }
    private static void need(boolean condition, String message) { StrictJson.require(condition, message); }
}
