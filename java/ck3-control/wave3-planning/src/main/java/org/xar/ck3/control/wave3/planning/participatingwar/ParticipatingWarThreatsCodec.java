package org.xar.ck3.control.wave3.planning.participatingwar;

import static org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreats.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;

/** Native SDK integer input and versioned decimal-string output are separate explicit boundaries. */
public final class ParticipatingWarThreatsCodec {
    public static final String SCHEMA = "xar.java.participating-war-threat-observation.v2";
    public static final int MAX_BYTES = 1_048_576;
    private static final Set<String> OUTPUT_FIELDS = Set.of("schema", "status", "source_frame", "reason", "source_presence",
            "participating_war_ids", "primary_war_ids", "non_primary_war_ids", "leadership_unknown_war_ids", "enemy_army_memberships",
            "unique_enemy_army_ids", "strength", "leadership_scope_complete", "non_participant_liege_scope", "action_authorized", "read_only",
            "unraised_or_future_enemy_reserves_bounded", "defeat_title_transfer_verified", "battle_win_probability");
    private static final Set<String> FRAME_FIELDS = Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id");
    private ParticipatingWarThreatsCodec() { }

    /** Consumes the actual detached SDK snapshot; unknown native extension fields remain projections. */
    public static Observation observeSnapshot(byte[] bytes) {
        JsonNode root = StrictJson.parse(bytes, MAX_BYTES); StrictJson.require(root.isObject(), "snapshot object required");
        Frame frame;
        try { frame = nativeFrame(root); }
        catch (IllegalArgumentException error) { return unavailable(null, Reason.CURRENT_FRAME_IDENTITY_UNAVAILABLE, framePresence(root)); }
        JsonNode player = root.get("played_character");
        if (!trueToken(root.get("paused")) || !trueToken(root.get("map_ready")) || player == null || !player.isObject() || !trueToken(player.get("alive")))
            return unavailable(frame, Reason.CURRENT_PAUSED_LIVING_PLAYER_REQUIRED, presence(player));
        JsonNode wars = root.get("active_wars");
        if (wars == null || !wars.isArray()) return unavailable(frame, Reason.PUBLISHED_ACTIVE_WAR_ARRAY_UNAVAILABLE, presence(wars));
        List<War> parsed = new ArrayList<>(); List<Integer> seen = new ArrayList<>();
        for (JsonNode row : wars) {
            if (!row.isObject()) return unavailable(frame, Reason.DISTINCT_NATIVE_PARTICIPATING_WAR_IDENTITY_UNAVAILABLE, presence(row));
            int id; Leadership leader;
            try {
                id = positiveWarId(row.get("war_id")); StrictJson.require(!seen.contains(id), "duplicate war");
                StrictJson.require(textEquals(row.get("source"), "native") && (textEquals(row.get("player_side"), "attacker") || textEquals(row.get("player_side"), "defender")), "native participant identity required");
                JsonNode leadership = row.get("player_is_primary_war_leader");
                if (leadership == null) leader = Leadership.MISSING;
                else if (leadership.isNull()) leader = Leadership.EXPLICIT_NULL;
                else { StrictJson.require(leadership.isBoolean(), "leadership boolean required"); leader = leadership.booleanValue() ? Leadership.PRIMARY : Leadership.NON_PRIMARY; }
            } catch (IllegalArgumentException error) { return unavailable(frame, Reason.DISTINCT_NATIVE_PARTICIPATING_WAR_IDENTITY_UNAVAILABLE, presence(row.get("war_id"))); }
            seen.add(id); JsonNode enemies = row.get("enemy_armies");
            if (enemies == null || !enemies.isArray()) return unavailable(frame, Reason.PUBLISHED_ENEMY_ARMY_ARRAY_UNAVAILABLE, presence(enemies));
            List<Army> armies = new ArrayList<>();
            for (JsonNode army : enemies) {
                try { StrictJson.require(army.isObject(), "army object required"); armies.add(new Army(armyId(army.get("army_id")), soldiers(army.get("soldiers")))); }
                catch (IllegalArgumentException error) { return unavailable(frame, Reason.PUBLISHED_ENEMY_ARMY_IDENTITY_UNAVAILABLE, presence(army.get("army_id"))); }
            }
            parsed.add(new War(id, leader, armies));
        }
        boolean currentCache = (textEquals(root.get("army_strengths_status"), "available") || textEquals(root.get("army_strengths_status"), "partial"))
                && textEquals(root.get("army_strengths_queried_snapshot_id"), frame.snapshotId())
                && integralEquals(root.get("army_strengths_queried_revision"), frame.revision());
        List<CacheRow> strengths = new ArrayList<>(); JsonNode cache = root.get("army_strengths");
        if (currentCache && cache != null && cache.isArray() && parsed.stream().anyMatch(war -> !war.enemies().isEmpty())) {
            for (JsonNode row : cache) {
                if (!row.isObject()) continue; // Existing _armies ignores non-object strength rows.
                try {
                    JsonNode identity = row.get("army_id"), role = row.get("scope_role");
                    if (!textEquals(role, "active_war_enemy")) continue;
                    if (!cacheIdentityCouldMatch(identity, parsed)) continue;
                    strengths.add(new CacheRow(armyId(identity), StrictJson.text(role), textEquals(row.get("status"), "available"), soldiers(row.get("current_soldiers"))));
                } catch (IllegalArgumentException error) { return unavailable(frame, Reason.STRENGTH_CACHE_CONTRACT_UNAVAILABLE, Presence.INVALID); }
            }
        }
        return observe(new Snapshot(frame, parsed, currentCache, strengths));
    }

    public static byte[] encode(Observation observation) {
        ObjectNode root = StrictJson.object(); root.put("schema", SCHEMA);
        root.put("non_participant_liege_scope", observation.nonParticipantLiegeScope().name()); root.put("action_authorized", false);
        root.put("read_only", true); root.put("unraised_or_future_enemy_reserves_bounded", false); root.put("defeat_title_transfer_verified", false); root.putNull("battle_win_probability");
        switch (observation) {
            case Observed value -> {
                root.put("status", "observed"); root.set("source_frame", frame(value.frame())); root.putNull("reason"); root.put("source_presence", "observed");
                ids(root, "participating_war_ids", value.participatingWarIds()); ids(root, "primary_war_ids", value.primaryWarIds());
                ids(root, "non_primary_war_ids", value.nonPrimaryWarIds()); ids(root, "leadership_unknown_war_ids", value.leadershipUnknownWarIds());
                ArrayNode rows = root.putArray("enemy_army_memberships");
                for (Membership membership : value.enemyArmyMemberships()) { ObjectNode row = StrictJson.object(); row.put("army_id", membership.armyId()); ids(row, "war_ids", membership.warIds()); rows.add(row); }
                ids(root, "unique_enemy_army_ids", value.uniqueEnemyArmyIds()); root.set("strength", strength(value.strength())); root.put("leadership_scope_complete", value.leadershipScopeComplete());
            }
            case Unavailable value -> {
                root.put("status", "unavailable"); if (value.sourceFrame().isPresent()) root.set("source_frame", frame(value.sourceFrame().orElseThrow())); else root.putNull("source_frame");
                root.put("reason", value.reason().name().toLowerCase(Locale.ROOT)); root.put("source_presence", value.sourcePresence().name().toLowerCase(Locale.ROOT));
                for (String field : List.of("participating_war_ids", "primary_war_ids", "non_primary_war_ids", "leadership_unknown_war_ids", "enemy_army_memberships", "unique_enemy_army_ids", "strength", "leadership_scope_complete")) root.putNull(field);
            }
        }
        return StrictJson.canonical(root, MAX_BYTES);
    }

    public static Observation decode(byte[] bytes) {
        ObjectNode root = StrictJson.object(StrictJson.parse(bytes, MAX_BYTES), OUTPUT_FIELDS);
        StrictJson.require(textEquals(root.get("schema"), SCHEMA) && textEquals(root.get("non_participant_liege_scope"), NonParticipantLiegeScope.UNASSESSED_NONPARTICIPANT_LIEGE_WARS.name()), "versioned participant observation required");
        StrictJson.require(root.get("action_authorized").isBoolean() && !root.get("action_authorized").booleanValue(), "fact cannot authorize actions");
        StrictJson.trueValue(root.get("read_only"));
        for (String field : List.of("unraised_or_future_enemy_reserves_bounded", "defeat_title_transfer_verified")) StrictJson.require(root.get(field).isBoolean() && !root.get(field).booleanValue(), "unobserved material consequence cannot be asserted");
        StrictJson.require(root.get("battle_win_probability").isNull(), "no observed battle probability exists");
        String status = StrictJson.text(root.get("status")); JsonNode source = root.get("source_frame");
        if (status.equals("unavailable")) {
            for (String field : List.of("participating_war_ids", "primary_war_ids", "non_primary_war_ids", "leadership_unknown_war_ids", "enemy_army_memberships", "unique_enemy_army_ids", "strength", "leadership_scope_complete")) StrictJson.require(root.get(field).isNull(), "unavailable cannot assert observed scope");
            return new Unavailable(source.isNull() ? Optional.empty() : Optional.of(wireFrame(source)), Reason.valueOf(StrictJson.text(root.get("reason")).toUpperCase(Locale.ROOT)), Presence.valueOf(StrictJson.text(root.get("source_presence")).toUpperCase(Locale.ROOT)));
        }
        StrictJson.require(status.equals("observed") && root.get("reason").isNull() && textEquals(root.get("source_presence"), "observed"), "observed status required");
        JsonNode memberships = root.get("enemy_army_memberships"); StrictJson.require(memberships.isArray(), "membership array required"); List<Membership> rows = new ArrayList<>();
        for (JsonNode raw : memberships) { ObjectNode row = StrictJson.object(raw, Set.of("army_id", "war_ids")); rows.add(new Membership(armyId(row.get("army_id")), warIds(row.get("war_ids")))); }
        Observed result = new Observed(wireFrame(source), warIds(root.get("participating_war_ids")), warIds(root.get("primary_war_ids")), warIds(root.get("non_primary_war_ids")), warIds(root.get("leadership_unknown_war_ids")), rows, decodeStrength(root.get("strength")));
        StrictJson.require(root.get("leadership_scope_complete").isBoolean() && root.get("leadership_scope_complete").booleanValue() == result.leadershipScopeComplete(), "leadership completeness differs");
        StrictJson.require(armyIds(root.get("unique_enemy_army_ids")).equals(result.uniqueEnemyArmyIds()), "army union differs from memberships"); return result;
    }


    public static final String NON_PRIMARY_RISK_SCHEMA = "xar.java.non-primary-war-risk.v1";
    private static final Set<String> RISK_FIELDS = Set.of("schema", "status", "source_frame",
            "risk_assessment_status", "non_primary_war_ids", "leadership_unknown_war_ids", "reason",
            "source_presence", "non_participant_liege_scope", "political_and_territorial_consequences_assessed",
            "unraised_reserves_bounded", "battle_win_probability", "action_authorized", "read_only");

    /** A separate read-only risk statement; the existing observation wire is unchanged. */
    public static byte[] encodeNonPrimaryRisk(NonPrimaryRisk risk) {
        ObjectNode root = StrictJson.object(); root.put("schema", NON_PRIMARY_RISK_SCHEMA);
        root.put("non_participant_liege_scope", risk.nonParticipantLiegeScope().name());
        root.put("political_and_territorial_consequences_assessed", risk.politicalAndTerritorialConsequencesAssessed());
        root.put("unraised_reserves_bounded", risk.unraisedReservesBounded());
        root.putNull("battle_win_probability"); root.put("action_authorized", risk.actionAuthorized());
        root.put("read_only", true);
        switch (risk) {
            case ObservedNonPrimaryRisk value -> {
                root.put("status", "observed"); root.set("source_frame", frame(value.frame()));
                root.put("risk_assessment_status", value.status().name().toLowerCase(Locale.ROOT));
                ids(root, "non_primary_war_ids", value.nonPrimaryWarIds());
                ids(root, "leadership_unknown_war_ids", value.leadershipUnknownWarIds());
                root.putNull("reason"); root.put("source_presence", "observed");
            }
            case UnavailableNonPrimaryRisk value -> {
                root.put("status", "unavailable");
                if (value.sourceFrame().isPresent()) root.set("source_frame", frame(value.sourceFrame().orElseThrow()));
                else root.putNull("source_frame");
                for (String field : List.of("risk_assessment_status", "non_primary_war_ids", "leadership_unknown_war_ids"))
                    root.putNull(field);
                root.put("reason", value.reason().name().toLowerCase(Locale.ROOT));
                root.put("source_presence", value.sourcePresence().name().toLowerCase(Locale.ROOT));
            }
        }
        return StrictJson.canonical(root, MAX_BYTES);
    }

    public static NonPrimaryRisk decodeNonPrimaryRisk(byte[] bytes) {
        ObjectNode root = StrictJson.object(StrictJson.parse(bytes, MAX_BYTES), RISK_FIELDS);
        StrictJson.require(textEquals(root.get("schema"), NON_PRIMARY_RISK_SCHEMA)
                && textEquals(root.get("non_participant_liege_scope"),
                    NonParticipantLiegeScope.UNASSESSED_NONPARTICIPANT_LIEGE_WARS.name()), "versioned non-primary risk required");
        StrictJson.trueValue(root.get("read_only"));
        for (String field : List.of("political_and_territorial_consequences_assessed", "unraised_reserves_bounded", "action_authorized"))
            StrictJson.require(root.get(field).isBoolean() && !root.get(field).booleanValue(),
                    "participant observation cannot assess unobserved consequences or authorize an action");
        StrictJson.require(root.get("battle_win_probability").isNull(), "raised soldiers do not establish a battle probability");
        String status = StrictJson.text(root.get("status"));
        if (status.equals("unavailable")) {
            for (String field : List.of("risk_assessment_status", "non_primary_war_ids", "leadership_unknown_war_ids"))
                StrictJson.require(root.get(field).isNull(), "unavailable risk cannot assert an empty observed scope");
            JsonNode source = root.get("source_frame");
            return new UnavailableNonPrimaryRisk(source.isNull() ? Optional.empty() : Optional.of(wireFrame(source)),
                    Reason.valueOf(StrictJson.text(root.get("reason")).toUpperCase(Locale.ROOT)),
                    Presence.valueOf(StrictJson.text(root.get("source_presence")).toUpperCase(Locale.ROOT)));
        }
        StrictJson.require(status.equals("observed") && root.get("reason").isNull()
                && textEquals(root.get("source_presence"), "observed"), "observed risk status required");
        ObservedNonPrimaryRisk result = new ObservedNonPrimaryRisk(wireFrame(root.get("source_frame")),
                warIds(root.get("non_primary_war_ids")), warIds(root.get("leadership_unknown_war_ids")));
        StrictJson.require(textEquals(root.get("risk_assessment_status"), result.status().name().toLowerCase(Locale.ROOT)),
                "risk status differs from observed non-primary and unresolved-leadership scope");
        return result;
    }

    private static Frame nativeFrame(JsonNode root) {
        return new Frame(nativeUInt(nativeActor(root), true), nativeUInt(root.get("native_revision"), true), nativeUInt(root.get("date_raw"), false), StrictJson.text(root.get("snapshot_id")), nativeUInt(root.get("revision"), true), StrictJson.text(root.get("episode_run_id")));
    }
    private static JsonNode nativeActor(JsonNode root) { JsonNode actor = root.get("played_character_id"); if (actor == null || actor.isNull()) { JsonNode player = root.get("played_character"); return player == null ? null : player.get("character_id"); } return actor; }
    private static Presence framePresence(JsonNode root) { for (JsonNode field : new JsonNode[] { nativeActor(root), root.get("native_revision"), root.get("date_raw"), root.get("snapshot_id"), root.get("revision"), root.get("episode_run_id") }) { if (field == null) return Presence.MISSING; if (field.isNull()) return Presence.EXPLICIT_NULL; } return Presence.INVALID; }
    private static ObjectNode frame(Frame value) {
        ObjectNode node = StrictJson.object(); node.put("played_character_id", decimal(value.playedCharacterId())); node.put("native_revision", decimal(value.nativeRevision()));
        node.put("date_raw", decimal(value.dateRaw())); node.put("snapshot_id", value.snapshotId()); node.put("revision", decimal(value.revision())); node.put("episode_run_id", value.episodeRunId()); return node;
    }
    private static Frame wireFrame(JsonNode value) {
        ObjectNode node = StrictJson.object(value, FRAME_FIELDS);
        return new Frame(wireUInt(node.get("played_character_id"), true), wireUInt(node.get("native_revision"), true), wireUInt(node.get("date_raw"), false), StrictJson.text(node.get("snapshot_id")), wireUInt(node.get("revision"), true), StrictJson.text(node.get("episode_run_id")));
    }
    private static BigInteger nativeUInt(JsonNode value, boolean positive) { return StrictJson.integer(value, positive ? BigInteger.ONE : BigInteger.ZERO, StrictJson.UINT64_MAX); }
    private static BigInteger wireUInt(JsonNode value, boolean positive) { BigInteger result = new BigInteger(new CrossJsDecimalUInt64(StrictJson.text(value)).decimal()); StrictJson.require(!positive || result.signum() > 0, "positive identity required"); return result; }
    private static String decimal(BigInteger value) { return new CrossJsDecimalUInt64(value.toString()).decimal(); }
    private static Soldiers soldiers(JsonNode value) { if (value == null) return new Missing(); if (value.isNull()) return new ExplicitNull(); if (!value.isIntegralNumber() || value.bigIntegerValue().signum() < 0) return new Invalid(); return new Present(value.bigIntegerValue()); }
    private static ObjectNode strength(Strength strength) {
        ObjectNode node = StrictJson.object();
        switch (strength) {
            case Known known -> { node.put("status", "known"); node.put("soldiers", known.soldiers().toString()); node.putNull("unavailable_presence"); node.putNull("conflicting_army_id"); }
            case Unknown unknown -> { node.put("status", "unknown"); node.putNull("soldiers"); node.put("unavailable_presence", unknown.firstUnavailablePresence().name().toLowerCase(Locale.ROOT)); node.putNull("conflicting_army_id"); }
            case Conflict conflict -> { node.put("status", "conflict"); node.putNull("soldiers"); node.putNull("unavailable_presence"); node.put("conflicting_army_id", conflict.armyId()); }
        }
        return node;
    }
    private static Strength decodeStrength(JsonNode value) {
        ObjectNode node = StrictJson.object(value, Set.of("status", "soldiers", "unavailable_presence", "conflicting_army_id")); String status = StrictJson.text(node.get("status"));
        return switch (status) {
            case "known" -> { StrictJson.require(node.get("unavailable_presence").isNull() && node.get("conflicting_army_id").isNull(), "known strength excludes unknown fields"); String soldiers = StrictJson.text(node.get("soldiers")); StrictJson.require(soldiers.matches("0|[1-9][0-9]*"), "canonical nonnegative soldier decimal string required"); yield new Known(new BigInteger(soldiers)); }
            case "unknown" -> { StrictJson.require(node.get("soldiers").isNull() && node.get("conflicting_army_id").isNull(), "unknown strength excludes count"); yield new Unknown(Presence.valueOf(StrictJson.text(node.get("unavailable_presence")).toUpperCase(Locale.ROOT))); }
            case "conflict" -> { StrictJson.require(node.get("soldiers").isNull() && node.get("unavailable_presence").isNull(), "conflict excludes count"); yield new Conflict(armyId(node.get("conflicting_army_id"))); }
            default -> throw new IllegalArgumentException("unknown strength status");
        };
    }
    private static Unavailable unavailable(Frame frame, Reason reason, Presence presence) { return new Unavailable(Optional.ofNullable(frame), reason, presence); }
    private static Presence presence(JsonNode value) { return value == null ? Presence.MISSING : value.isNull() ? Presence.EXPLICIT_NULL : Presence.INVALID; }
    private static int armyId(JsonNode value) { return Math.toIntExact(StrictJson.integer(value, 0, Integer.MAX_VALUE)); }
    private static int positiveWarId(JsonNode value) { return Math.toIntExact(StrictJson.integer(value, 1, Integer.MAX_VALUE)); }
    private static List<Integer> warIds(JsonNode value) { StrictJson.require(value.isArray(), "WarID array required"); List<Integer> result = new ArrayList<>(); for (JsonNode id : value) result.add(positiveWarId(id)); return List.copyOf(result); }
    private static List<Integer> armyIds(JsonNode value) { StrictJson.require(value.isArray(), "ArmyID array required"); List<Integer> result = new ArrayList<>(); for (JsonNode id : value) result.add(armyId(id)); return List.copyOf(result); }
    private static void ids(ObjectNode node, String field, List<Integer> ids) { ArrayNode result = node.putArray(field); ids.forEach(result::add); }
    private static boolean trueToken(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static boolean textEquals(JsonNode value, String expected) { return value != null && value.isTextual() && value.textValue().equals(expected); }
    private static boolean integralEquals(JsonNode value, BigInteger expected) { return value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(expected); }
    /** Ignore unconsumed rows; matching boolean/float aliases still fail armyId's strict boundary. */
    private static boolean cacheIdentityCouldMatch(JsonNode identity, List<War> wars) {
        if (identity == null) return false; BigInteger comparable;
        if (identity.isIntegralNumber()) comparable = identity.bigIntegerValue();
        else if (identity.isBoolean()) comparable = identity.booleanValue() ? BigInteger.ONE : BigInteger.ZERO;
        else if (identity.isFloatingPointNumber()) {
            try { comparable = identity.decimalValue().toBigIntegerExact(); }
            catch (ArithmeticException nonIntegral) { return false; }
        } else return false;
        return wars.stream().flatMap(war -> war.enemies().stream()).anyMatch(army -> comparable.equals(BigInteger.valueOf(army.armyId())));
    }
}
