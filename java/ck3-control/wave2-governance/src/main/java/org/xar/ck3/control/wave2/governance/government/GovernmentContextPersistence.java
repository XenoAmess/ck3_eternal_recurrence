package org.xar.ck3.control.wave2.governance.government;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Context;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Status;

/** Strict persisted-result codec. It does not issue source, cold or action qualification. */
final class GovernmentContextPersistence {
    private static final Set<String> FIELDS = Set.of("schema", "schema_version", "status", "query_permitted",
            "identity_observation_ready", "core_adapter_ready", "ordinary_goal_context_ready", "unavailable_reason",
            "campaign_id", "current_character_id", "snapshot_revision", "date_raw", "government_key", "adapter_family",
            "adapter_status", "government_runtime_adapter");

    private GovernmentContextPersistence() { }

    static void requireCurrentPlayerBinding(Context context, BigInteger actorCharacterId) {
        NativeCharacterId.of(actorCharacterId);
        ObjectNode result = GovernmentContextCodec.contextJson(context);
        parse(result);
        JsonNode observed = result.get("government_runtime_adapter");
        if (!observed.isNull()) {
            StrictJson.require(actorCharacterId.equals(characterId(observed.get("player_character_id"))),
                    "retained government observation belongs to another consumer player");
        }
    }

    static Context decode(byte[] raw) {
        return parse(StrictJson.parse(raw));
    }

    static Context parse(JsonNode value) {
        ObjectNode row = StrictJson.object(value, FIELDS);
        StrictJson.require(GovernmentContext.SCHEMA.equals(StrictJson.text(row.get("schema")))
                && BigInteger.ONE.equals(integer(row.get("schema_version"))), "government result schema differs");
        Status status = status(StrictJson.text(row.get("status")));
        boolean permitted = bool(row.get("query_permitted"));
        boolean identity = bool(row.get("identity_observation_ready"));
        boolean core = bool(row.get("core_adapter_ready"));
        boolean goalReady = bool(row.get("ordinary_goal_context_ready"));
        String reason = text(row.get("unavailable_reason"));
        String campaign = text(row.get("campaign_id"));
        BigInteger current = characterId(row.get("current_character_id"));
        BigInteger revision = integer(row.get("snapshot_revision"));
        BigInteger date = integer(row.get("date_raw"));
        String key = text(row.get("government_key"));
        String family = text(row.get("adapter_family"));
        String adapterStatus = text(row.get("adapter_status"));
        JsonNode observation = row.get("government_runtime_adapter");
        String wire = null;
        if (observation.isNull()) {
            StrictJson.require(!identity && !core && !goalReady && key == null && family == null && adapterStatus == null,
                    "unobserved government result cannot claim native identity");
            StrictJson.require((status == Status.INACTIVE || status == Status.NOT_QUERIED || status == Status.UNAVAILABLE)
                    && reason != null, "unobserved government result status differs");
        } else {
            StrictJson.require(permitted && campaign != null && !campaign.isEmpty() && current != null,
                    "preserved government observation requires its ordinary goal binding");
            ObjectNode observed = object(observation);
            BigInteger nativePlayer = characterId(observed.get("player_character_id"));
            ObjectNode build = object(observed.get("build"));
            // A parsed DecimalNode may render 1.0 as 1. Validate the actually
            // consumed integer token kinds before reconstructing a raw request.
            integer(observed.get("schema_version")); integer(observed.get("snapshot_revision"));
            if (!"unavailable".equals(text(observed.get("status")))) {
                integer(observed.get("date_raw"));
                ObjectNode features = object(observed.get("effective_feature_flags"));
                integer(features.get("native_count")); JsonNode items = features.get("items");
                StrictJson.require(items != null && items.isArray(), "retained native feature array required");
                for (JsonNode item : items) { integer(object(item).get("native_index")); }
            }
            // Reuse the sole native normalizer. This checks the retained DTO against
            // its result frame; it does not establish a fresh live hello or query.
            ObjectNode request = StrictJson.object();
            request.put("schema", GovernmentContextCodec.NORMALIZE_SCHEMA);
            ObjectNode snapshot = request.putObject("snapshot");
            nullableInteger(snapshot, "native_revision", revision);
            nullableInteger(snapshot, "date_raw", date);
            snapshot.putObject("played_character").set("character_id", observed.path("player_character_id"));
            ObjectNode hello = snapshot.putObject("diagnostics").putObject("hello");
            hello.set("expected_ck3_version", build.path("version"));
            hello.set("expected_ck3_sha256", build.path("exe_sha256"));
            request.set("government_observation", observed);
            JsonNode normalized = StrictJson.parse(GovernmentContextCodec.normalizeAdapter(bytes(request)));
            StrictJson.require(normalized.equals(observed), "retained government observation changed during validation");
            Status nativeStatus = status(StrictJson.text(observed.get("status")));
            ObjectNode readiness = object(observed.get("readiness"));
            boolean expectedIdentity = nativeStatus == Status.AVAILABLE && bool(readiness.get("same_frame_ready"));
            boolean expectedCore = expectedIdentity && bool(readiness.get("core_adapter_ready"));
            boolean playerMatches = Objects.equals(current, nativePlayer);
            String expectedReason = text(observed.get("unavailable_reason"));
            String nativeAdapterStatus = projectedText(observed.get("adapter"), "status");
            if (expectedIdentity && !playerMatches) { expectedReason = "ordinary_goal_current_ruler_not_matched"; }
            else if (expectedIdentity && !expectedCore) {
                expectedReason = nativeAdapterStatus == null ? "government_adapter_unavailable" : nativeAdapterStatus;
            }
            StrictJson.require(status == nativeStatus && identity == expectedIdentity && core == expectedCore
                    && goalReady == (expectedCore && playerMatches) && Objects.equals(reason, expectedReason)
                    && Objects.equals(key, projectedText(observed.get("government"), "key"))
                    && Objects.equals(family, projectedText(observed.get("adapter"), "family"))
                    && Objects.equals(adapterStatus, nativeAdapterStatus), "government result differs from its retained observation");
            wire = observed.toString();
        }
        return new Context(status, permitted, identity, core, goalReady, reason, campaign, current, revision, date,
                key, family, adapterStatus, wire);
    }

    private static Status status(String value) {
        for (Status status : Status.values()) { if (status.wire().equals(value)) { return status; } }
        throw new IllegalArgumentException("exact government result status required");
    }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "retained government object required");
        return (ObjectNode) value;
    }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "actual government boolean required");
        return value.booleanValue();
    }
    private static BigInteger integer(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isIntegralNumber(), "actual government integer required; no bool/float/string");
        return value.bigIntegerValue();
    }
    private static BigInteger characterId(JsonNode value) {
        return value == null || value.isNull() ? null : NativeCharacterId.fromJson(value).asBigInteger();
    }
    private static String text(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isTextual(), "actual government string required");
        if (!value.textValue().isEmpty()) { StrictJson.text(value); }
        return value.textValue();
    }
    private static String projectedText(JsonNode value, String field) {
        return value != null && value.isObject() ? text(value.get(field)) : null;
    }
    private static void nullableInteger(ObjectNode row, String field, BigInteger value) {
        if (value == null) { row.putNull(field); } else { row.put(field, value); }
    }
    private static byte[] bytes(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
}
