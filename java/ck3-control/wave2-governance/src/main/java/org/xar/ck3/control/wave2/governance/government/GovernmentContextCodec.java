package org.xar.ck3.control.wave2.governance.government;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Context;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.GoalIdentity;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Observation;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Request;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Snapshot;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Status;

/** Strict wrapper plus declared projections of extensible existing SDK objects. */
public final class GovernmentContextCodec {
    public static final String REQUEST_SCHEMA = "xar.java-government-context-request/v1";
    public static final String NORMALIZE_SCHEMA = "xar.java-government-adapter-normalize-request/v1";
    private static final Map<String, String> BUILDS = Map.of(
            "1.19.0.6", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            "1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
            "1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
            "1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
    private GovernmentContextCodec() { }

    public static Request decodeRequest(byte[] body) {
        ObjectNode root = StrictJson.object(StrictJson.parse(body), Set.of("schema", "snapshot", "government_observation", "query_permitted"));
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(root.get("schema"))), "government context request schema differs");
        boolean permitted = bool(root.get("query_permitted"));
        Snapshot snapshot = snapshot(object(root.get("snapshot")), true);
        JsonNode rawObservation = root.get("government_observation");
        boolean present = !rawObservation.isNull();
        Observation observed = null;
        String error = null;
        // Existing early branches neither normalize nor consume the supplied profile.
        if (present && permitted && GovernmentContext.ORDINARY_LIFECYCLE.equals(snapshot.lifecycle())
                && snapshot.goalObject() && snapshot.goalValidationError() == null) {
            try { observed = observation(rawObservation, snapshot); }
            catch (SourceRejected rejected) { error = rejected.getMessage(); }
        }
        return new Request(snapshot, permitted, observed, error, present);
    }

    public static Context decodeAndBuild(byte[] body) { return GovernmentContext.build(decodeRequest(body)); }
    public static byte[] compose(byte[] body) { return encode(decodeAndBuild(body)); }

    /** Restore the strict typed result; this grants no fresh native or runtime qualification. */
    public static Context decodeContext(byte[] body) { return GovernmentContextPersistence.decode(body); }

    /** Preserve numeric token kinds when an enclosing contract has already parsed the JSON. */
    public static Context parseContext(JsonNode value) { return GovernmentContextPersistence.parse(value); }

    /** Bind a retained native observation to its actual consumer player, without issuing a new query. */
    public static void requireCurrentPlayerBinding(Context context, BigInteger actorCharacterId) {
        GovernmentContextPersistence.requireCurrentPlayerBinding(context, actorCharacterId);
    }

    /** Direct reusable normalizer port used by the existing private query adapter. */
    public static Observation decodeNormalizedAdapter(byte[] body) {
        ObjectNode root = StrictJson.object(StrictJson.parse(body), Set.of("schema", "snapshot", "government_observation"));
        StrictJson.require(NORMALIZE_SCHEMA.equals(StrictJson.text(root.get("schema"))), "government adapter normalization schema differs");
        Snapshot snapshot = snapshot(object(root.get("snapshot")), false);
        return observation(root.get("government_observation"), snapshot);
    }
    public static byte[] encodeAdapter(Observation observation) {
        return observation.preservedWire().getBytes(StandardCharsets.UTF_8);
    }
    public static byte[] normalizeAdapter(byte[] body) { return encodeAdapter(decodeNormalizedAdapter(body)); }

    /** Source validation for a combined projection caller, with serialization outside the rejection boundary. */
    public static byte[] normalizeAdapterProjection(byte[] body) {
        Observation normalized;
        try { normalized = decodeNormalizedAdapter(body); }
        catch (SourceRejected | ContractViolationException rejected) {
            throw new ProjectionDomainRejection(rejected.getMessage());
        }
        return encodeAdapter(normalized);
    }

    public static byte[] encode(Context context) {
        ObjectNode result = contextJson(context);
        // Extensible native payloads may contain decimal-valued metadata. They are
        // retained as JSON values, never interpreted as integer identities.
        byte[] encoded = result.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(encoded.length <= StrictJson.INPUT_MAX_BYTES, "government result exceeds byte budget");
        return encoded;
    }

    static ObjectNode contextJson(Context context) {
        StrictJson.require(context != null, "typed government context required");
        if (context.currentCharacterId() != null) { NativeCharacterId.of(context.currentCharacterId()); }
        ObjectNode result = StrictJson.object();
        result.put("schema", GovernmentContext.SCHEMA); result.put("schema_version", 1);
        result.put("status", context.status().wire()); result.put("query_permitted", context.queryPermitted());
        result.put("identity_observation_ready", context.identityObservationReady());
        result.put("core_adapter_ready", context.coreAdapterReady());
        result.put("ordinary_goal_context_ready", context.ordinaryGoalContextReady());
        text(result, "unavailable_reason", context.unavailableReason()); text(result, "campaign_id", context.campaignId());
        number(result, "current_character_id", context.currentCharacterId()); number(result, "snapshot_revision", context.snapshotRevision());
        number(result, "date_raw", context.dateRaw()); text(result, "government_key", context.governmentKey());
        text(result, "adapter_family", context.adapterFamily()); text(result, "adapter_status", context.adapterStatus());
        if (context.governmentRuntimeAdapterWire() == null) { result.putNull("government_runtime_adapter"); }
        else { result.set("government_runtime_adapter", StrictJson.parse(context.governmentRuntimeAdapterWire().getBytes(StandardCharsets.UTF_8))); }
        return result;
    }

    private static Snapshot snapshot(ObjectNode row, boolean contextGoal) {
        BigInteger revision = optionalInteger(row.get("native_revision"));
        BigInteger date = optionalInteger(row.get("date_raw"));
        JsonNode actor = row.get("played_character");
        BigInteger player = actor != null && actor.isObject() ? optionalCharacterId(actor.get("character_id")) : null;
        JsonNode lifecycleRow = contextGoal ? row.get("succession_lifecycle") : null;
        String lifecycle = lifecycleRow != null && lifecycleRow.isObject() ? optionalText(lifecycleRow.get("lifecycle")) : null;
        JsonNode goal = contextGoal ? row.get("campaign_goal") : null;
        boolean goalObject = goal != null && goal.isObject();
        GoalIdentity identity = goalObject ? new GoalIdentity(optionalText(goal.get("campaign_id")), optionalCharacterId(goal.get("current_character_id"))) : null;
        String goalError = goalObject ? goalError(goal) : null;
        JsonNode diagnostics = row.get("diagnostics");
        JsonNode hello = diagnostics != null && diagnostics.isObject() ? diagnostics.get("hello") : null;
        String version = "1.19.0.6";
        String sha = BUILDS.get(version);
        String buildError = null;
        if (hello != null && hello.isObject()) {
            version = optionalText(hello.has("expected_ck3_version") ? hello.get("expected_ck3_version") : hello.get("game_version"));
            sha = optionalText(hello.has("expected_ck3_sha256") ? hello.get("expected_ck3_sha256") : hello.get("executable_sha256"));
            if (!knownBuild(version, sha)) { buildError = "private nonwar source lacks a frozen exact native build"; }
        }
        return new Snapshot(revision, date, player, lifecycle, identity, goalObject, goalError, version, sha, buildError);
    }

    private static String goalError(JsonNode goal) {
        BigInteger format = optionalInteger(goal.get("format_version"));
        String key = optionalText(goal.get("goal_key"));
        String campaign = optionalText(goal.get("campaign_id"));
        if (!BigInteger.ONE.equals(format) || !"dynasty_continuity".equals(key) || campaign == null || campaign.isEmpty()) {
            return "ordinary campaign goal is malformed";
        }
        for (String field : new String[] {"origin_character_id", "current_character_id"}) {
            if (optionalCharacterId(goal.get(field)) == null) { return "ordinary campaign goal " + field + " is malformed"; }
        }
        JsonNode progress = goal.get("progress");
        if (progress == null || !progress.isObject()) { return "ordinary campaign goal progress is malformed"; }
        BigInteger count = optionalInteger(progress.get("reconciled_successions"));
        JsonNode last = progress.get("last_succession");
        if (count == null || count.signum() < 0 || last != null && !last.isNull() && !last.isObject()) {
            return "ordinary campaign goal progress is malformed";
        }
        boolean hasLast = last != null && !last.isNull();
        if ((count.signum() == 0) == hasLast) { return "ordinary campaign goal progress is malformed"; }
        if (!hasLast && !Objects.equals(optionalCharacterId(goal.get("origin_character_id")),
                optionalCharacterId(goal.get("current_character_id")))) {
            return "ordinary campaign goal origin_character_id is malformed";
        }
        return null;
    }

    private static Observation observation(JsonNode value, Snapshot snapshot) {
        if (!value.isObject() || !"government-runtime-adapter-v1".equals(optionalText(value.get("schema")))
                || !BigInteger.ONE.equals(optionalInteger(value.get("schema_version")))) {
            throw rejected("government runtime adapter schema is unavailable");
        }
        JsonNode build = value.get("build");
        if (build == null || !build.isObject()) { throw rejected("government runtime adapter lacks build identity"); }
        String version = optionalText(build.get("version"));
        String sha = optionalText(build.get("exe_sha256"));
        if (!knownBuild(version, sha)) { throw rejected("native source does not match a frozen exact build"); }
        if (snapshot.nativeBuildError() != null) { throw rejected(snapshot.nativeBuildError()); }
        if (!Objects.equals(version, snapshot.nativeBuildVersion()) || !sha.equalsIgnoreCase(snapshot.nativeBuildSha256())) {
            throw rejected("government runtime adapter belongs to another native build");
        }
        JsonNode provenance = value.get("provenance");
        if (provenance == null || !provenance.isObject()
                || !("ck3-" + version + "-private-government-runtime-adapter-v1").equals(optionalText(provenance.get("backend_id")))
                || !("ck3-" + version + "-native-campaign-root-context-v1").equals(optionalText(provenance.get("campaign_backend_id")))
                || !("ck3-" + version + "-native-loaded-feature-manifest-v1").equals(optionalText(provenance.get("feature_backend_id")))) {
            throw rejected("government runtime adapter lacks its native source identities");
        }
        String statusText = optionalText(value.get("status"));
        JsonNode readiness = value.get("readiness");
        if (!Set.of("available", "not_present", "unavailable").contains(statusText == null ? "" : statusText)
                || readiness == null || !readiness.isObject()) { throw rejected("government runtime adapter status is malformed"); }
        if (!hasBoolean(readiness, "same_frame_ready") || !hasBoolean(readiness, "core_adapter_ready")) {
            throw rejected("government runtime adapter readiness is malformed");
        }
        boolean same = bool(readiness.get("same_frame_ready"));
        boolean core = bool(readiness.get("core_adapter_ready"));
        if (!Objects.equals(optionalInteger(value.get("snapshot_revision")), snapshot.nativeRevision())) {
            throw rejected("government runtime adapter revision differs from the query frame");
        }
        Status status = Status.observation(statusText);
        String reason = optionalText(value.get("unavailable_reason"));
        BigInteger nativePlayer = optionalCharacterId(value.get("player_character_id"));
        if (status == Status.UNAVAILABLE) {
            if (reason == null || same || core) { throw rejected("government runtime adapter lost its unavailable result"); }
            return new Observation(status, false, false, reason, projectedText(value.get("government"), "key"),
                    projectedText(value.get("adapter"), "family"), projectedText(value.get("adapter"), "status"), value.toString());
        }
        if (snapshot.playerCharacterId() == null || !Objects.equals(nativePlayer, snapshot.playerCharacterId())
                || !Objects.equals(optionalInteger(value.get("date_raw")), snapshot.dateRaw()) || !same) {
            throw rejected("government runtime adapter does not match the paused player frame");
        }
        JsonNode government = value.get("government");
        JsonNode features = value.get("effective_feature_flags");
        JsonNode adapter = value.get("adapter");
        if (government == null || !government.isObject() || optionalText(government.get("key")) == null
                || !isArray(government.get("flags")) || features == null || !features.isObject()
                || !isArray(features.get("items")) || adapter == null || !adapter.isObject()
                || optionalText(adapter.get("status")) == null || !hasBoolean(adapter, "requirements_met")) {
            throw rejected("government runtime adapter observation is malformed");
        }
        JsonNode rows = features.get("items");
        if (rows.size() != 44 || !BigInteger.valueOf(44).equals(optionalInteger(features.get("native_count")))) {
            throw rejected("government runtime adapter feature count is malformed");
        }
        Set<String> keys = new HashSet<>();
        for (int index = 0; index < rows.size(); index++) {
            JsonNode item = rows.get(index);
            if (!item.isObject()) { throw rejected("government runtime adapter feature identity is malformed"); }
            String key = optionalText(item.get("key"));
            if (!BigInteger.valueOf(index).equals(optionalInteger(item.get("native_index"))) || key == null || key.isEmpty()
                    || !keys.add(key) || !hasBoolean(item, "enabled")) {
                throw rejected("government runtime adapter feature identity is malformed");
            }
        }
        boolean expectedCore = status == Status.AVAILABLE && "core_supported".equals(optionalText(adapter.get("status")))
                && bool(adapter.get("requirements_met"));
        if (core != expectedCore) { throw rejected("government runtime adapter disagrees with its native core verdict"); }
        return new Observation(status, same, core, reason, optionalText(government.get("key")),
                optionalText(adapter.get("family")), optionalText(adapter.get("status")), value.toString());
    }

    private static String projectedText(JsonNode row, String key) { return row != null && row.isObject() ? optionalText(row.get(key)) : null; }
    private static boolean isArray(JsonNode row) { return row != null && row.isArray(); }
    private static boolean hasBoolean(JsonNode row, String field) {
        JsonNode value = row.get(field);
        if (value == null || value.isNull()) { return false; }
        bool(value); return true;
    }
    private static boolean knownBuild(String version, String sha) {
        return version != null && sha != null && BUILDS.containsKey(version) && BUILDS.get(version).equalsIgnoreCase(sha);
    }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "JSON object required"); return (ObjectNode) value;
    }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "actual boolean token required"); return value.booleanValue();
    }
    private static BigInteger optionalInteger(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isIntegralNumber(), "actual integer token required; bool/float/string rejected"); return value.bigIntegerValue();
    }
    private static BigInteger optionalCharacterId(JsonNode value) {
        return value == null || value.isNull() ? null : NativeCharacterId.fromJson(value).asBigInteger();
    }
    private static String optionalText(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isTextual(), "actual string token required");
        if (!value.textValue().isEmpty()) { StrictJson.text(value); }
        return value.textValue();
    }
    private static void text(ObjectNode row, String name, String value) { if (value == null) { row.putNull(name); } else { row.put(name, value); } }
    private static void number(ObjectNode row, String name, BigInteger value) { if (value == null) { row.putNull(name); } else { row.put(name, value); } }
    private static SourceRejected rejected(String reason) { return new SourceRejected(reason); }
    private static final class SourceRejected extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        SourceRejected(String reason) { super(reason); }
    }
}
