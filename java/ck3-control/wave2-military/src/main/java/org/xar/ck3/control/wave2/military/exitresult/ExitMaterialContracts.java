package org.xar.ck3.control.wave2.military.exitresult;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Availability;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.ClaimRow;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.ClaimState;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Frame;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.NativeClaims;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.NativeTruce;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.TitleRow;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.TruceStatus;

/** Complete real normalizer closure for this composer, with dynamic JSON confined here. */
final class ExitMaterialContracts {
    private static final Set<String> CLAIM_FIELDS = Set.of("title_id", "present", "state", "strong", "implicit");
    private static final Set<String> TRUCE_FIELDS = Set.of("schema_version", "backend_id", "ck3_build", "executable_sha256",
            "status", "snapshot_revision", "current_date_raw", "owner_character_id", "toward_character_id", "native_has_truce",
            "actual_expiry_observable", "expiry_date_raw", "same_frame_stable", "readiness", "temporal_semantics", "unavailable_reason");
    private static final String[] TIERS = {"", "barony", "county", "duchy", "kingdom", "empire", "hegemony"};
    private static final String[] TIER_PREFIXES = {"", "b_", "c_", "d_", "k_", "e_", "h_"};
    private ExitMaterialContracts() { }

    static int integer(JsonNode value, int minimum) {
        require(value != null && value.isIntegralNumber() && value.bigIntegerValue().compareTo(BigInteger.valueOf(minimum)) >= 0
                && value.bigIntegerValue().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "full integer identity unavailable");
        return value.intValue();
    }
    static BigInteger integer64(JsonNode value, boolean positive) {
        require(value != null && value.isIntegralNumber() && value.bigIntegerValue().compareTo(positive ? BigInteger.ONE : BigInteger.ZERO) >= 0
                && value.bigIntegerValue().compareTo(StrictJson.UINT64_MAX) <= 0, "full integer identity unavailable");
        return value.bigIntegerValue();
    }
    static boolean actualTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    static boolean absent(JsonNode value) { return value == null || value.isNull(); }
    static boolean textEquals(JsonNode value, String expected) { return value != null && value.isTextual() && value.textValue().equals(expected); }
    static String nullableText(JsonNode value) { return absent(value) ? null : StrictJson.text(value); }
    static boolean sameInteger(JsonNode value, BigInteger expected) {
        return value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(expected);
    }
    static boolean sameInteger(JsonNode value, int expected) { return sameInteger(value, BigInteger.valueOf(expected)); }
    static boolean exactBool(JsonNode value, String message) {
        require(value != null && value.isBoolean(), message);
        return value.booleanValue();
    }
    static ObjectNode object(JsonNode value, String message) {
        require(value instanceof ObjectNode, message);
        return (ObjectNode) value;
    }
    static List<Integer> titleIds(JsonNode value) {
        require(value != null && value.isArray() && value.size() >= 1 && value.size() <= 4096,
                "title_ids must contain 1..4096 ordered TitleIDs");
        List<Integer> ids = new ArrayList<>();
        for (JsonNode id : value) {
            require(id.isIntegralNumber() && id.bigIntegerValue().signum() >= 0
                    && id.bigIntegerValue().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                    "TitleID must be a full non-negative int32 ID");
            ids.add(id.intValue());
        }
        require(new HashSet<>(ids).size() == ids.size(), "title_ids must not contain duplicates");
        return List.copyOf(ids);
    }
    static String claimsStep(List<Integer> ids) {
        require(!ids.isEmpty() && ids.size() <= 4096, "title_ids must contain 1..4096 ordered TitleIDs");
        return "query-player-claims-v1-" + String.join(",", ids.stream().map(String::valueOf).toList());
    }
    static BigInteger queryEnvelope(JsonNode value, Frame frame, String step) {
        require(value != null && value.isObject() && textEquals(value.get("step"), step)
                && actualTrue(value.get("accepted")) && actualTrue(value.get("read_only"))
                && textEquals(value.get("backend_id"), "native-headless"), "typed read-only envelope unavailable");
        BigInteger sequence = integer64(value.get("query_sequence"), true);
        require(textEquals(value.get("queried_snapshot_id"), frame.snapshotId())
                && sameInteger(value.get("queried_revision"), frame.revision())
                && sameInteger(value.get("queried_native_revision"), frame.nativeRevision()), "typed query differs from post frame");
        return sequence;
    }

    static NativeClaims claims(JsonNode result, Frame post, List<Integer> ids) {
        BigInteger sequence = queryEnvelope(result, post, claimsStep(ids));
        JsonNode value = result.get("player_claims");
        require(value != null && value.isObject() && textEquals(value.get("schema"), "xar.ck3.player-claims.v1")
                && sameInteger(value.get("schema_version"), 1), "player claims uses an unsupported schema");
        require(textEquals(value.get("game_version"), "1.20.0.4") && currentSha(value.get("executable_sha256")),
                "player claims lacks exact actual4 build provenance");
        require(sameInteger(value.get("snapshot_revision"), post.nativeRevision()), "player claims differs from native snapshot revision");
        require(sameInteger(value.get("date_raw"), post.dateRaw()), "player claims differs from paused date");
        require(claimId(value.get("actor_character_id"), "actor_character_id") == post.actorCharacterId(),
                "player claims actor differs from current played character");
        require(titleIds(value.get("title_ids")).equals(ids), "player claims differs from ordered requested TitleIDs");
        boolean available = exactBool(value.get("available"), "player claims status disagrees with availability");
        require(textEquals(value.get("status"), available ? "available" : "unavailable"), "player claims status disagrees with availability");
        if (!available) {
            require(nonemptyString(value.get("unavailable_reason")) && absent(value.get("claims")),
                    "unavailable player claims must preserve unknown rows and a reason");
            return new NativeClaims(Availability.UNAVAILABLE, null, sequence, value.get("unavailable_reason").textValue());
        }
        require(absent(value.get("unavailable_reason")), "available player claims must not carry failure reason");
        JsonNode rows = value.get("claims");
        require(rows != null && rows.isArray() && rows.size() == ids.size(),
                "player claim rows must correspond one-to-one to ordered TitleIDs");
        List<ClaimRow> output = new ArrayList<>();
        for (int index = 0; index < ids.size(); index++) {
            ObjectNode row = object(rows.get(index), "player claim row fields are malformed");
            require(keys(row).equals(CLAIM_FIELDS), "player claim row fields are malformed");
            require(claimId(row.get("title_id"), "claim TitleID") == ids.get(index) && row.get("present").isBoolean(),
                    "player claim row identity/presence is malformed");
            boolean present = row.get("present").booleanValue();
            if (!present) {
                require(textEquals(row.get("state"), "absent") && absent(row.get("strong")) && absent(row.get("implicit")),
                        "absent player claim must preserve absent optional flags");
                output.add(new ClaimRow(ids.get(index), false, ClaimState.ABSENT, null, null));
            } else {
                boolean strong = exactBool(row.get("strong"), "present player claim requires native boolean flags");
                boolean implicit = exactBool(row.get("implicit"), "present player claim requires native boolean flags");
                ClaimState state = strong ? (implicit ? ClaimState.STRONG_IMPLICIT : ClaimState.STRONG_EXPLICIT)
                        : (implicit ? ClaimState.WEAK_IMPLICIT : ClaimState.WEAK_EXPLICIT);
                require(textEquals(row.get("state"), state.wire()), "player claim state disagrees with native flags");
                output.add(new ClaimRow(ids.get(index), true, state, strong, implicit));
            }
        }
        return new NativeClaims(Availability.AVAILABLE, output, sequence, null);
    }

    static TitleRow title(JsonNode result, Frame post, List<Integer> frozenIds, Set<Integer> seen) {
        JsonNode value = result != null && result.isObject() ? result.get("title_holder") : null;
        JsonNode id = value != null && value.isObject() ? value.get("title_id") : null;
        require(id != null && id.isIntegralNumber() && id.canConvertToInt() && frozenIds.contains(id.intValue())
                && !seen.contains(id.intValue()), "title result is not a unique frozen target");
        int titleId = id.intValue();
        queryEnvelope(result, post, "query-title-holder-v1-" + titleId);
        object(value, "title holder must be an object");
        require(textEquals(value.get("schema"), "xar.ck3.title-holder.v1") && sameInteger(value.get("schema_version"), 1),
                "title holder uses an unsupported schema");
        boolean available = exactBool(value.get("available"), "title holder status disagrees with availability");
        require(textEquals(value.get("status"), available ? "available" : "unavailable"), "title holder status disagrees with availability");
        require(sameInteger(value.get("snapshot_revision"), post.nativeRevision()), "title holder differs from the native snapshot revision");
        require(sameInteger(value.get("date_raw"), post.dateRaw()), "title holder differs from the paused date");
        require(holderId(value.get("title_id"), "title_id") == titleId, "title holder differs from the requested TitleID");
        require(holderId(value.get("actor_character_id"), "actor_character_id") == post.actorCharacterId(),
                "title holder actor differs from the played character");
        require(isString(value.get("game_version")) && isString(value.get("executable_sha256")), "title holder lacks native build provenance");
        Integer holder = null;
        Integer immediate = null;
        Integer top = null;
        Boolean inRealm = null;
        int tier = 0;
        if (available) {
            require(absent(value.get("unavailable_reason")), "available title holder must not carry a failure reason");
            JsonNode rawTier = value.get("title_tier_raw");
            require(rawTier != null && rawTier.isIntegralNumber() && rawTier.canConvertToInt()
                    && rawTier.intValue() >= 1 && rawTier.intValue() <= 6
                    && textEquals(value.get("title_tier_key"), TIERS[rawTier.intValue()]), "title holder native tier pair is inconsistent");
            tier = rawTier.intValue();
            boolean isPlayer = exactBool(value.get("holder_is_player"), "title holder holder_is_player must be observable");
            inRealm = exactBool(value.get("holder_in_player_realm"), "title holder holder_in_player_realm must be observable");
            if (absent(value.get("holder_character_id"))) {
                require(!isPlayer && !inRealm && absent(value.get("holder_immediate_liege_character_id"))
                        && absent(value.get("holder_top_liege_character_id")), "unheld title must preserve legal holder and liege absence");
            } else {
                holder = holderId(value.get("holder_character_id"), "holder_character_id");
                immediate = absent(value.get("holder_immediate_liege_character_id")) ? null
                        : holderId(value.get("holder_immediate_liege_character_id"), "holder_immediate_liege_character_id");
                top = holderId(value.get("holder_top_liege_character_id"), "holder_top_liege_character_id");
                require(isPlayer == (holder == post.actorCharacterId()), "title holder player identity is inconsistent");
                require(!isPlayer || inRealm, "player-held title must be in the player realm");
            }
        } else {
            require(nonemptyString(value.get("unavailable_reason")), "unavailable title holder requires an explicit reason");
            for (String field : List.of("title_tier_raw", "title_tier_key", "holder_character_id", "holder_is_player",
                    "holder_in_player_realm", "holder_immediate_liege_character_id", "holder_top_liege_character_id")) {
                require(absent(value.get(field)), "unavailable title holder must preserve unknown fields as null");
            }
        }
        List<String> keyFields = List.of("title_key", "title_key_available", "title_key_status", "title_key_unavailable_reason");
        if (textEquals(value.get("game_version"), "1.20.0.4") || keyFields.stream().anyMatch(value::has)) {
            require(keyFields.stream().allMatch(value::has), "title holder lacks the complete title-key observation");
            boolean keyAvailable = exactBool(value.get("title_key_available"), "title key status disagrees with availability");
            require(textEquals(value.get("title_key_status"), keyAvailable ? "available" : "unavailable"), "title key status disagrees with availability");
            if (keyAvailable) {
                String key = isString(value.get("title_key")) ? value.get("title_key").textValue() : "";
                require(available && absent(value.get("title_key_unavailable_reason")) && key.length() >= 3 && key.length() <= 1024
                        && key.matches("[bcdkeh]_[a-z0-9][a-z0-9_]*") && key.startsWith(TIER_PREFIXES[tier]),
                        "available title key lacks an exact canonical tier/key pair");
            } else {
                require(absent(value.get("title_key")) && nonemptyString(value.get("title_key_unavailable_reason")),
                        "unavailable title key requires null key and explicit reason");
            }
        }
        require(textEquals(value.get("game_version"), "1.20.0.4") && currentSha(value.get("executable_sha256")),
                "title result lacks current4 provenance");
        seen.add(titleId);
        return new TitleRow(titleId, available ? Availability.AVAILABLE : Availability.UNAVAILABLE, holder, immediate, top,
                inRealm, nullableText(value.get("unavailable_reason")));
    }

    static NativeTruce truce(JsonNode result, Frame post, int opponent) {
        BigInteger sequence = queryEnvelope(result, post, "query-raiktor-actual-truce-expiry-v1-" + opponent);
        require(opponent > 0, "toward_character_id must be a positive full signed CharacterID");
        require(sameInteger(result.get("snapshot_revision"), post.nativeRevision()), "player truce-expiry differs from the native snapshot revision");
        require(sameInteger(result.get("date_raw"), post.dateRaw()), "player truce-expiry differs from the paused date");
        ObjectNode value = object(result.get("raiktor_actual_truce_expiry"), "player truce-expiry requires every agreed DTO field");
        require(keys(value).equals(TRUCE_FIELDS), "player truce-expiry requires every agreed DTO field");
        require(sameInteger(value.get("schema_version"), 1)
                && textEquals(value.get("backend_id"), "ck3-1.20.0.4-native-player-truce-expiry-v1")
                && textEquals(value.get("ck3_build"), "1.20.0.4") && currentSha(value.get("executable_sha256")),
                "player truce-expiry lacks exact actual4 provenance");
        for (String field : List.of("snapshot_revision", "current_date_raw", "owner_character_id", "toward_character_id")) {
            BigInteger expected = switch (field) {
                case "snapshot_revision" -> post.nativeRevision();
                case "current_date_raw" -> BigInteger.valueOf(post.dateRaw());
                case "owner_character_id" -> BigInteger.valueOf(post.actorCharacterId());
                case "toward_character_id" -> BigInteger.valueOf(opponent);
                default -> throw new IllegalStateException("fixed truce identity field");
            };
            require(sameInteger(value.get(field), expected), "player truce-expiry " + field + " differs from the current query");
        }
        boolean hasTruce = exactBool(value.get("native_has_truce"), "player truce-expiry native_has_truce must be boolean");
        boolean observable = exactBool(value.get("actual_expiry_observable"), "player truce-expiry actual_expiry_observable must be boolean");
        boolean stable = exactBool(value.get("same_frame_stable"), "player truce-expiry same_frame_stable must be boolean");
        boolean ready = exactBool(value.get("readiness"), "player truce-expiry readiness must be boolean");
        require(textEquals(value.get("temporal_semantics"), "post_application_persisted_relation_state"), "player truce-expiry temporal semantics changed");
        if (textEquals(value.get("status"), "available")) {
            JsonNode expiry = value.get("expiry_date_raw");
            require(hasTruce && observable && stable && ready && expiry != null && expiry.isIntegralNumber()
                    && expiry.bigIntegerValue().compareTo(BigInteger.valueOf(post.dateRaw())) > 0
                    && expiry.bigIntegerValue().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0
                    && absent(value.get("unavailable_reason")), "available player truce-expiry observation is incomplete");
            return new NativeTruce(TruceStatus.AVAILABLE, post.actorCharacterId(), opponent, expiry.intValue(), null, sequence);
        }
        require(textEquals(value.get("status"), "no_truce"), "successful player truce-expiry transport cannot carry an unknown state");
        require(!hasTruce && !observable && absent(value.get("expiry_date_raw")) && stable && !ready
                && textEquals(value.get("unavailable_reason"), "native_has_truce_false"), "no-truce observation is malformed");
        return new NativeTruce(TruceStatus.NO_TRUCE, post.actorCharacterId(), opponent, null, "native_has_truce_false", sequence);
    }
    static boolean currentSha(JsonNode value) {
        return isString(value) && value.textValue().toUpperCase(Locale.ROOT).equals(OrdinaryWarExitObservation.EXE_SHA256);
    }
    private static int claimId(JsonNode value, String name) {
        require(value != null && value.isIntegralNumber() && value.bigIntegerValue().signum() >= 0
                && value.bigIntegerValue().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                name + " must be a full non-negative int32 ID");
        return value.intValue();
    }
    private static int holderId(JsonNode value, String name) { return claimId(value, name); }
    private static boolean isString(JsonNode value) { return value != null && value.isTextual(); }
    private static boolean nonemptyString(JsonNode value) { return isString(value) && !value.textValue().isEmpty(); }
    private static Set<String> keys(ObjectNode value) {
        Set<String> fields = new HashSet<>();
        value.fieldNames().forEachRemaining(fields::add);
        return fields;
    }
}
