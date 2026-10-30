package org.xar.ck3.control.finance.factiongift;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.NativeFactionId;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

import static org.xar.ck3.control.finance.factiongift.FactionGiftChoice.MembershipRole;
import static org.xar.ck3.control.finance.factiongift.FactionGiftChoice.Reason;

/** Exact pure decision leaf. Dynamic JSON is confined to this validated boundary. */
public final class FactionGiftPolicy {
    public static final int MAX_INPUT_BYTES = 131_072;
    public static final int MAX_OBSERVATIONS = 256;
    private static final BigInteger SCALE = BigInteger.valueOf(100_000);
    private static final Set<String> INPUT_FIELDS = Set.of(
            "observations", "complete_native_enumeration", "minimum_gold_reserve_raw");
    private static final Set<String> OBSERVATION_FIELDS = Set.of(
            "available", "paused", "snapshot_revision", "native_snapshot_revision",
            "observed_date_raw", "date_raw", "player_resources_query_complete",
            "player_character_id", "player_gold_raw", "player_gold_scale",
            "source_faction_requery_complete", "queried_source_faction_id",
            "source_faction_present", "source_faction_target_character_id",
            "source_faction_targeting_player", "source_faction_at_war",
            "source_faction_leader_character_id", "source_faction_member_character_ids",
            "source_faction_metrics_available", "source_faction_power_raw",
            "source_faction_discontent_raw", "source_faction_metric_scale",
            "recipient_identity_resolved", "recipient_character_id", "recipient_alive",
            "recipient_is_ai", "recipient_is_direct_landed_vassal",
            "recipient_opinion_query_complete", "recipient_opinion_of_player",
            "gift_opinion_present", "gift_opinion_modifier_value", "gift_preview");
    private static final Set<String> PREVIEW_FIELDS = Set.of("available", "definition_key",
            "definition_stable_hash", "interaction_legal", "auto_accept", "gold_cost_raw",
            "gold_scale", "opinion_delta");
    private static final List<String> CHOICE_ORDER = List.of("status", "reason", "source_faction_id",
            "recipient_character_id", "membership_role", "snapshot_revision",
            "native_snapshot_revision", "date_raw", "player_character_id",
            "definition_stable_hash", "gold_cost_raw", "opinion_delta");
    private static final Set<String> CHOICE_FIELDS = Set.copyOf(CHOICE_ORDER);
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(32)
                    .maxNumberLength(4300).maxStringLength(16_384).build()).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    private FactionGiftPolicy() { }

    /** The numeric wire is Python-only; JavaScript callers must not round-trip it via Number. */
    public static FactionGiftChoice choose(byte[] request) {
        JsonNode root = parse(request);
        requireObject(root, "request");
        allowedFields(root, INPUT_FIELDS, "request");
        for (String field : INPUT_FIELDS) {
            if (!root.has(field)) throw invalid("request missing " + field);
        }
        BigInteger reserve = integer(root.get("minimum_gold_reserve_raw"), false);
        if (reserve == null || reserve.signum() < 0 || !isTrue(root.get("complete_native_enumeration"))) {
            return declined(Reason.ENUMERATION_OR_RESERVE_UNPROVEN);
        }
        JsonNode observations = root.get("observations");
        if (!observations.isArray()) throw invalid("observations must be an array");
        if (observations.size() > MAX_OBSERVATIONS) throw invalid("observations exceed limit");
        if (observations.isEmpty()) return declined(Reason.COMPLETE_NATIVE_EMPTY);
        Frame frame = null;
        Candidate best = null;
        int legalCount = 0;
        for (JsonNode observation : observations) {
            if (!observation.isObject()) return declined(Reason.MALFORMED_NATIVE_OBSERVATION);
            allowedFields(observation, OBSERVATION_FIELDS, "observation");
            if (observation.has("date_raw") && integer(observation.get("date_raw"), false) == null) {
                throw invalid("date_raw metadata must be an integer");
            }
            JsonNode modifier = observation.get("gift_opinion_modifier_value");
            if (modifier != null && !modifier.isNull() && integer(modifier, false) == null) {
                throw invalid("gift_opinion_modifier_value metadata must be null or an integer");
            }
            for (String field : Set.of("available", "paused", "player_resources_query_complete",
                    "source_faction_requery_complete", "recipient_identity_resolved",
                    "recipient_opinion_query_complete", "source_faction_metrics_available")) {
                if (!isTrue(observation.get(field))) return declined(Reason.NATIVE_OBSERVATION_INCOMPLETE);
            }
            BigInteger revision = integer(observation.get("snapshot_revision"), true);
            BigInteger nativeRevision = integer(observation.get("native_snapshot_revision"), true);
            BigInteger date = integer(observation.get("observed_date_raw"), false);
            BigInteger player = privateCharacter(observation.get("player_character_id"));
            BigInteger gold = integer(observation.get("player_gold_raw"), false);
            BigInteger sourceId = privateFaction(observation.get("queried_source_faction_id"));
            BigInteger recipient = privateCharacter(observation.get("recipient_character_id"));
            BigInteger target = privateCharacter(observation.get("source_faction_target_character_id"));
            if (revision == null || nativeRevision == null || date == null || player == null
                    || gold == null || sourceId == null || recipient == null || target == null
                    || !SCALE.equals(integer(observation.get("player_gold_scale"), false))
                    || integer(observation.get("source_faction_power_raw"), false) == null
                    || integer(observation.get("source_faction_discontent_raw"), false) == null
                    || !SCALE.equals(integer(observation.get("source_faction_metric_scale"), false))) {
                return declined(Reason.NATIVE_IDENTITY_OR_METRIC_UNAVAILABLE);
            }
            Frame current = new Frame(revision, nativeRevision, date, player, gold);
            if (frame == null) frame = current;
            else if (!current.equals(frame)) return declined(Reason.CANDIDATE_FRAME_DRIFT);

            JsonNode members = observation.get("source_faction_member_character_ids");
            JsonNode leaderNode = observation.get("source_faction_leader_character_id");
            BigInteger leader = privateCharacter(leaderNode);
            if (members == null || !members.isArray()
                    || (leaderNode != null && !leaderNode.isNull() && leader == null)) {
                return declined(Reason.FACTION_MEMBERSHIP_UNAVAILABLE);
            }
            Set<BigInteger> memberIds = new HashSet<>();
            for (JsonNode memberNode : members) {
                BigInteger member = privateCharacter(memberNode);
                if (member == null || !memberIds.add(member)) {
                    return declined(Reason.FACTION_MEMBERSHIP_UNAVAILABLE);
                }
            }
            for (String field : Set.of("source_faction_present", "source_faction_targeting_player",
                    "source_faction_at_war", "recipient_alive", "recipient_is_ai",
                    "recipient_is_direct_landed_vassal", "gift_opinion_present")) {
                if (!isBoolean(observation.get(field))) {
                    return declined(Reason.FACTION_OR_RECIPIENT_STATE_UNAVAILABLE);
                }
            }
            BigInteger opinion = integer(observation.get("recipient_opinion_of_player"), false);
            if (opinion == null) return declined(Reason.FACTION_OR_RECIPIENT_STATE_UNAVAILABLE);
            JsonNode preview = observation.get("gift_preview");
            if (preview == null || !preview.isObject()) return declined(Reason.GIFT_PREVIEW_UNAVAILABLE);
            allowedFields(preview, PREVIEW_FIELDS, "gift_preview");
            for (String field : Set.of("available", "interaction_legal", "auto_accept")) {
                if (!isBoolean(preview.get(field))) return declined(Reason.GIFT_LEGALITY_UNAVAILABLE);
            }
            BigInteger definitionHash = integer(preview.get("definition_stable_hash"), true);
            JsonNode definitionKey = preview.get("definition_key");
            if (definitionKey == null || !definitionKey.isTextual()
                    || !"gift_interaction".equals(definitionKey.textValue())
                    || definitionHash == null || !isTrue(preview.get("available"))) {
                return declined(Reason.GIFT_DEFINITION_UNAVAILABLE);
            }
            // Native known denial is terminal before cost/effect availability is required.
            if (!isTrue(preview.get("interaction_legal")) || !isTrue(preview.get("auto_accept"))) continue;
            BigInteger cost = integer(preview.get("gold_cost_raw"), true);
            BigInteger delta = integer(preview.get("opinion_delta"), true);
            if (cost == null || delta == null || !SCALE.equals(integer(preview.get("gold_scale"), false))) {
                return declined(Reason.GIFT_VALUE_UNAVAILABLE);
            }
            MembershipRole role = recipient.equals(leader) ? MembershipRole.LEADER
                    : memberIds.contains(recipient) ? MembershipRole.CHARACTER_MEMBER : null;
            if (!isTrue(observation.get("source_faction_present"))
                    || !isTrue(observation.get("source_faction_targeting_player"))
                    || !target.equals(player) || isTrue(observation.get("source_faction_at_war"))
                    || role == null || !isTrue(observation.get("recipient_alive"))
                    || !isTrue(observation.get("recipient_is_ai"))
                    || !isTrue(observation.get("recipient_is_direct_landed_vassal"))
                    || isTrue(observation.get("gift_opinion_present"))) continue;
            legalCount++;
            if (gold.subtract(cost).compareTo(reserve) < 0) continue;
            Candidate candidate = new Candidate(current, sourceId, recipient, role, definitionHash,
                    cost, delta, opinion);
            if (best == null || candidate.compareTo(best) < 0) best = candidate;
        }
        if (best == null) return declined(legalCount > 0
                ? Reason.GOLD_RESERVE_NOT_SATISFIED : Reason.COMPLETE_NATIVE_NO_LEGAL_MEMBER);
        return best.choice();
    }

    /** Exact field names and explicit nulls match dataclasses.asdict of the old producer. */
    public static byte[] encode(FactionGiftChoice choice) {
        Objects.requireNonNull(choice, "choice");
        ObjectNode result = JSON.createObjectNode();
        result.put("status", choice.status().wire());
        result.put("reason", choice.reason().wire());
        for (String field : CHOICE_ORDER) {
            if (!field.equals("status") && !field.equals("reason")) result.putNull(field);
        }
        if (choice instanceof FactionGiftChoice.Selected selected) {
            result.put("source_faction_id", selected.sourceFactionId());
            result.put("recipient_character_id", selected.recipientCharacterId());
            result.put("membership_role", selected.membershipRole().wire());
            result.put("snapshot_revision", selected.snapshotRevision());
            result.put("native_snapshot_revision", selected.nativeSnapshotRevision());
            result.put("date_raw", selected.dateRaw());
            result.put("player_character_id", selected.playerCharacterId());
            result.put("definition_stable_hash", selected.definitionStableHash());
            result.put("gold_cost_raw", selected.goldCostRaw());
            result.put("opinion_delta", selected.opinionDelta());
        }
        try { return JSON.writeValueAsBytes(result); }
        catch (IOException failure) { throw new IllegalStateException("choice encoding failed", failure); }
    }

    /** Validates persisted choice JSON without accepting status aliases or default zeroes. */
    public static FactionGiftChoice decodeChoice(byte[] bytes) {
        JsonNode value = parse(bytes);
        requireObject(value, "choice");
        allowedFields(value, CHOICE_FIELDS, "choice");
        for (String field : CHOICE_FIELDS) if (!value.has(field)) throw invalid("choice missing " + field);
        String reasonWire = text(value.get("reason"));
        Reason reason = null;
        for (Reason candidate : Reason.values()) if (candidate.wire().equals(reasonWire)) reason = candidate;
        if (reason == null || !reason.status().wire().equals(text(value.get("status")))) {
            throw invalid("inconsistent choice status/reason");
        }
        if (reason != Reason.SELECTED) {
            for (String field : CHOICE_FIELDS) {
                if (!field.equals("status") && !field.equals("reason") && !value.get(field).isNull()) {
                    throw invalid("declined choice has action fields");
                }
            }
            return declined(reason);
        }
        MembershipRole role = null;
        for (MembershipRole candidate : MembershipRole.values()) {
            if (candidate.wire().equals(text(value.get("membership_role")))) role = candidate;
        }
        if (role == null) throw invalid("invalid membership role");
        BigInteger date = integer(value.get("date_raw"), false);
        if (date == null) throw invalid("invalid date_raw");
        return new FactionGiftChoice.Selected(NativeFactionId.fromJson(value.get("source_faction_id")).asBigInteger(),
                requiredCharacter(value, "recipient_character_id"), role,
                requiredPositive(value, "snapshot_revision"), requiredPositive(value, "native_snapshot_revision"),
                date, requiredCharacter(value, "player_character_id"),
                requiredPositive(value, "definition_stable_hash"), requiredPositive(value, "gold_cost_raw"),
                requiredPositive(value, "opinion_delta"));
    }

    private record Frame(BigInteger revision, BigInteger nativeRevision, BigInteger date,
                         BigInteger player, BigInteger gold) { }

    private record Candidate(Frame frame, BigInteger source, BigInteger recipient,
                             MembershipRole role, BigInteger definitionHash,
                             BigInteger cost, BigInteger delta, BigInteger opinion) implements Comparable<Candidate> {
        @Override public int compareTo(Candidate other) {
            int order = cost.multiply(other.delta).compareTo(other.cost.multiply(delta));
            if (order == 0) order = Integer.compare(role.ordinal(), other.role.ordinal());
            if (order == 0) order = opinion.compareTo(other.opinion);
            if (order == 0) order = source.compareTo(other.source);
            if (order == 0) order = recipient.compareTo(other.recipient);
            return order;
        }
        FactionGiftChoice.Selected choice() {
            return new FactionGiftChoice.Selected(source, recipient, role, frame.revision,
                    frame.nativeRevision, frame.date, frame.player, definitionHash, cost, delta);
        }
    }

    private static JsonNode parse(byte[] bytes) {
        Objects.requireNonNull(bytes, "bytes");
        if (bytes.length == 0 || bytes.length > MAX_INPUT_BYTES) throw invalid("JSON byte limit");
        try {
            String utf8 = StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode result = JSON.readTree(utf8);
            if (result == null) throw invalid("empty JSON");
            return result;
        } catch (IOException failure) { throw new IllegalArgumentException("invalid faction gift JSON", failure); }
    }

    private static BigInteger character(JsonNode value) {
        try { return NativeCharacterId.fromJson(value).asBigInteger(); }
        catch (IllegalArgumentException invalid) { return null; }
    }

    private static BigInteger privateCharacter(JsonNode value) {
        if (value == null || !value.isIntegralNumber()) return null;
        try { return NativeCharacterId.fromRawUInt32(value.bigIntegerValue()).asBigInteger(); }
        catch (IllegalArgumentException invalid) { return null; }
    }
    private static BigInteger privateFaction(JsonNode value) {
        if (value == null || !value.isIntegralNumber()) return null;
        try { return NativeFactionId.fromRawUInt32(value.bigIntegerValue()).asBigInteger(); }
        catch (IllegalArgumentException invalid) { return null; }
    }

    private static BigInteger requiredCharacter(JsonNode value, String field) {
        BigInteger result = character(value.get(field));
        if (result == null) throw invalid("invalid " + field);
        return result;
    }

    private static BigInteger integer(JsonNode value, boolean positive) {
        if (value == null || !value.isIntegralNumber()) return null;
        BigInteger result = value.bigIntegerValue();
        return positive && result.signum() <= 0 ? null : result;
    }

    private static BigInteger requiredPositive(JsonNode value, String field) {
        BigInteger result = integer(value.get(field), true);
        if (result == null) throw invalid("invalid " + field);
        return result;
    }

    private static boolean isTrue(JsonNode value) { return isBoolean(value) && value.booleanValue(); }
    private static boolean isBoolean(JsonNode value) { return value != null && value.isBoolean(); }
    private static String text(JsonNode value) { return value != null && value.isTextual() ? value.textValue() : null; }
    private static FactionGiftChoice.Declined declined(Reason reason) { return new FactionGiftChoice.Declined(reason); }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }

    private static void requireObject(JsonNode value, String label) {
        if (!value.isObject()) throw invalid(label + " must be an object");
    }

    private static void allowedFields(JsonNode value, Set<String> allowed, String label) {
        for (var property : value.properties()) {
            String field = property.getKey();
            if (!allowed.contains(field)) throw invalid(label + " unknown field: " + field);
        }
    }
}
