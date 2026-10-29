package org.xar.ck3.control.wave3.governance.crownfinalterms;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown.RawObservation;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown.TurnTick;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTerms.*;

/** Strict token validation and complete existing private query value boundary. */
public final class CrownFinalTermsCodec {
    public static final String PAYLOAD_SCHEMA = "xar.java-crown-final-terms-payload/v1";
    public static final String PREPARE_SCHEMA = "xar.java-crown-final-terms-prepare/v1";
    public static final String CONSUME_SCHEMA = "xar.java-crown-final-terms-consume/v1";
    private static final String COOLDOWN = "crown_authority_cooldown";
    private static final String TICK = "crown_authority_cooldown_turn_tick";
    private static final Set<String> PAYLOAD_FIELDS = Set.of("schema", "snapshot_revision", "date_raw", "actor_character_id", "cost_scale", "cost_slots", "groups");
    private static final Set<String> ROW_FIELDS = Set.of("law_key", "active", "final_status", "final_can_enact", "native_reason", "cost_raw");
    private CrownFinalTermsCodec() { }

    public static byte[] normalize(byte[] body) { return encode(decode(body)); }

    public static Payload decode(byte[] body) {
        ObjectNode request = StrictJson.object(StrictJson.parse(body), Set.of("schema", "expected_revision", "date_raw", "actor_character_id", "exact_ck3_build", "payload"));
        require(PAYLOAD_SCHEMA.equals(StrictJson.text(request.get("schema"))), "law payload request schema differs");
        return payload(request.get("payload"), integer(request.get("expected_revision")), integer(request.get("date_raw")),
                integer(request.get("actor_character_id")), buildVersion(StrictJson.text(request.get("exact_ck3_build"))));
    }

    public record PrepareRequest(boolean queryEnabled, BigInteger expectedRevision, String requestId, SourceFrame before) { }
    public record ResponseValidation(String requestId, BigInteger expectedRevision) { }

    public static PrepareRequest decodePrepare(byte[] body) {
        ObjectNode request = StrictJson.object(StrictJson.parse(body), Set.of("schema", "query_enabled", "expected_revision", "request_id", "before_snapshot"));
        require(PREPARE_SCHEMA.equals(StrictJson.text(request.get("schema"))), "law prepare schema differs");
        return new PrepareRequest(bool(request.get("query_enabled")), integer(request.get("expected_revision")),
                StrictJson.text(request.get("request_id")), frame(object(request.get("before_snapshot"))));
    }
    public static NativeRequest projectPrepare(PrepareRequest request) {
        return CrownFinalTerms.prepare(request.queryEnabled(), request.expectedRevision(), request.requestId(), request.before());
    }
    public static byte[] encode(NativeRequest request) {
        ObjectNode result = StrictJson.object(); result.put("type", "execute_step"); result.put("protocol_version", 1);
        result.put("request_id", request.requestId()); result.put("step", CrownFinalTerms.STEP); result.put("expected_revision", request.expectedNativeRevision());
        return StrictJson.canonical(result);
    }
    public static byte[] prepare(byte[] body) { return encode(projectPrepare(decodePrepare(body))); }

    public static byte[] consume(byte[] body) { return encode(decodeReadback(body)); }

    public static ResponseValidation decodeResponseValidation(byte[] body) {
        ObjectNode request = StrictJson.object(StrictJson.parse(body), Set.of("schema", "expected_revision", "request_id", "before_snapshot", "command_result"));
        require("xar.java-crown-final-terms-validate-response/v1".equals(StrictJson.text(request.get("schema"))), "law response validation schema differs");
        ValidatedResponse response = response(request);
        return new ResponseValidation(response.requestId(), response.expected());
    }
    public static byte[] encode(ResponseValidation value) {
        return StrictJson.canonical(StrictJson.object().put("schema", "xar.java-crown-final-terms-response-validated/v1")
                .put("status", "validated").put("request_id", value.requestId()).put("expected_revision", value.expectedRevision()));
    }
    public static byte[] validateResponse(byte[] body) { return encode(decodeResponseValidation(body)); }

    private record ValidatedResponse(Payload payload, SourceFrame before, ObjectNode beforeNode,
            BigInteger expected, String requestId) { }

    private static ValidatedResponse response(ObjectNode request) {
        BigInteger expected = integer(request.get("expected_revision")); String requestId = StrictJson.text(request.get("request_id"));
        ObjectNode beforeNode = object(request.get("before_snapshot")); SourceFrame before = frame(beforeNode);
        CrownFinalTerms.prepare(true, expected, requestId, before);
        JsonNode command = request.get("command_result");
        require(command.isObject() && "command_result".equals(optionalText(command.get("type")))
                && BigInteger.ONE.equals(optionalInteger(command.get("protocol_version"))) && requestId.equals(optionalText(command.get("request_id"))),
                "private realm-law command_result unavailable");
        if (!actualTrue(command.get("ok"))) {
            JsonNode error = command.get("error");
            throw new IllegalArgumentException("private realm-law native RED: " + (error == null ? "unknown" : error.isTextual() ? error.textValue() : error.toString()));
        }
        ObjectNode envelope = object(command.get("result"));
        Set<String> fields = new HashSet<>(Set.of("step", "accepted", "status", "private_build", "read_only", "advertised", "realm_law_final_terms", "backend_id"));
        if (envelope.has("snapshot_revision") && before.build() != Build.LEGACY_11906) { fields.add("snapshot_revision"); }
        StrictJson.object(envelope, fields);
        require(!envelope.has("snapshot_revision") || before.nativeRevision().equals(integer(envelope.get("snapshot_revision"))), "private realm-law native payload malformed");
        require(CrownFinalTerms.STEP.equals(optionalText(envelope.get("step"))) && actualTrue(envelope.get("accepted"))
                && "available".equals(optionalText(envelope.get("status"))) && actualTrue(envelope.get("private_build"))
                && actualTrue(envelope.get("read_only")) && actualFalse(envelope.get("advertised"))
                && "native-headless".equals(optionalText(envelope.get("backend_id"))), "private realm-law native payload malformed");
        Payload payload = payload(envelope.get("realm_law_final_terms"), before.nativeRevision(), before.dateRaw(), before.actorCharacterId(), before.build());
        return new ValidatedResponse(payload, before, beforeNode, expected, requestId);
    }

    public static Readback decodeReadback(byte[] body) {
        ObjectNode request = StrictJson.object(StrictJson.parse(body), Set.of("schema", "expected_revision", "request_id", "before_snapshot", "after_snapshot", "command_result"));
        require(CONSUME_SCHEMA.equals(StrictJson.text(request.get("schema"))), "law consume schema differs");
        ValidatedResponse response = response(request); SourceFrame before = response.before();
        ObjectNode after = object(request.get("after_snapshot")); validateActor(after.get("played_character"));
        require(actualTrue(after.get("paused")) && actualTrue(after.get("map_ready"))
                && Objects.equals(before.dateRaw(), optionalInteger(after.get("date_raw")))
                && sameJson(response.beforeNode().get("played_character"), after.get("played_character")), "private realm-law read crossed the paused actor/date frame");
        return new Readback(response.payload(), before.build(), before.snapshotId(), response.expected(), before.nativeRevision(), optionalText(after.get("snapshot_id")));
    }

    private static Payload payload(JsonNode value, BigInteger revision, BigInteger date, BigInteger actor, Build build) {
        ObjectNode row = object(value); Set<String> fields = new HashSet<>(PAYLOAD_FIELDS);
        if (row.has(COOLDOWN)) { fields.add(COOLDOWN); }
        if (row.has(TICK)) { fields.add(TICK); }
        StrictJson.object(row, fields);
        require(CrownFinalTerms.SCHEMA.equals(StrictJson.text(row.get("schema"))) && revision.equals(integer(row.get("snapshot_revision")))
                && date.equals(integer(row.get("date_raw"))) && actor.equals(integer(row.get("actor_character_id")))
                && BigInteger.valueOf(100000).equals(integer(row.get("cost_scale"))), "law payload source frame or cost scale differs");
        JsonNode slots = row.get("cost_slots"); require(slots.isArray() && slots.size() == CrownFinalTerms.SLOTS.size(), "law cost slots differ");
        for (int index = 0; index < slots.size(); index++) { require(CrownFinalTerms.SLOTS.get(index).equals(StrictJson.text(slots.get(index))), "law cost slot order differs"); }
        JsonNode groups = row.get("groups"); require(groups.isArray() && groups.size() == 2, "both ordered law groups required");
        List<Group> parsed = new ArrayList<>();
        for (int index = 0; index < groups.size(); index++) { parsed.add(group(groups.get(index), index == 0 ? GroupKey.CROWN_AUTHORITY : GroupKey.SUCCESSION_ORDER_LAWS, build)); }
        RawObservation cooldown = null; TurnTick turnTick = null;
        if (row.has(COOLDOWN) || row.has(TICK)) { require(build == Build.CK3_12004, "native cooldown fields require exact 1.20.0.4"); }
        if (row.has(TICK)) { turnTick = tick(row.get(TICK)); CrownCooldown.validateTurnTick(turnTick); }
        if (row.has(COOLDOWN)) { cooldown = cooldown(row.get(COOLDOWN)); CrownCooldown.interpret(cooldown, date, turnTick); }
        return new Payload(revision, date, actor, parsed, cooldown, turnTick);
    }

    private static Group group(JsonNode value, GroupKey expected, Build build) {
        ObjectNode row = StrictJson.object(value, Set.of("group_key", "active_law_key", "candidates"));
        require(wire(expected).equals(StrictJson.text(row.get("group_key"))), "law group order differs");
        JsonNode candidates = row.get("candidates"); require(candidates.isArray() && candidates.size() >= 1 && candidates.size() <= 8, "law candidate count differs");
        boolean profiles = build.profileRows() && expected == GroupKey.SUCCESSION_ORDER_LAWS;
        Set<String> fields = new HashSet<>(ROW_FIELDS); if (profiles) { fields.add("succession_profile_status"); fields.add("succession_profile"); }
        List<Candidate> parsed = new ArrayList<>(); Set<String> keys = new HashSet<>(); String active = null;
        for (JsonNode node : candidates) {
            ObjectNode candidate = StrictJson.object(node, fields); String key = StrictJson.text(candidate.get("law_key")); require(keys.add(key), "duplicate law candidate key");
            boolean isActive = bool(candidate.get("active")); FinalStatus status = enumeration(candidate.get("final_status"), FinalStatus.class);
            boolean enact = bool(candidate.get("final_can_enact")); require(enact == (status == FinalStatus.CAN_ENACT), "final status and native legal verdict differ");
            String reason = string(candidate.get("native_reason")); require(reason.codePointCount(0, reason.length()) <= 4096, "native law reason exceeds bound");
            JsonNode rawCosts = candidate.get("cost_raw"); require(rawCosts.isArray() && rawCosts.size() == 10, "ten complete native law cost slots required");
            List<Long> costs = new ArrayList<>(); for (JsonNode cost : rawCosts) { costs.add(StrictJson.integer(cost, Long.MIN_VALUE, Long.MAX_VALUE)); }
            ProfileStatus profileStatus = profiles ? enumeration(candidate.get("succession_profile_status"), ProfileStatus.class) : null;
            SuccessionProfile profile = null;
            if (profiles && profileStatus == ProfileStatus.AVAILABLE) { profile = profile(candidate.get("succession_profile")); }
            else if (profiles) { require(candidate.get("succession_profile").isNull(), "nonavailable succession profile must be null"); }
            if (isActive) { require(active == null && status == FinalStatus.ALREADY_ACTIVE, "active law count or verdict differs"); active = key; }
            parsed.add(new Candidate(key, isActive, status, enact, reason, costs, profileStatus, profile));
        }
        require(Objects.equals(active, optionalText(row.get("active_law_key"))), "active law key differs");
        return new Group(expected, active, parsed);
    }

    private static SuccessionProfile profile(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("order", "traversal", "rank", "division", "primary_heir_minimum_share_raw", "primary_heir_minimum_share_scale", "create_primary_tier_titles"));
        require(BigInteger.valueOf(100000).equals(integer(row.get("primary_heir_minimum_share_scale"))), "succession share scale differs");
        return new SuccessionProfile(optionalEnum(row.get("order"), Order.class), optionalEnum(row.get("traversal"), Traversal.class),
                optionalEnum(row.get("rank"), Rank.class), optionalEnum(row.get("division"), Division.class),
                StrictJson.integer(row.get("primary_heir_minimum_share_raw"), Long.MIN_VALUE, Long.MAX_VALUE), bool(row.get("create_primary_tier_titles")));
    }

    private static RawObservation cooldown(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("read_available", "present", "timed", "expiry_raw", "current_clock_raw", "remaining_raw", "retry_date_raw", "expiry_type", "remaining_unit"));
        return new RawObservation(bool(row.get("read_available")), nullableBool(row.get("present")), nullableBool(row.get("timed")), nullableI32(row.get("expiry_raw")),
                nullableI32(row.get("current_clock_raw")), nullableI32(row.get("remaining_raw")), optionalInteger(row.get("retry_date_raw")), StrictJson.text(row.get("expiry_type")), StrictJson.text(row.get("remaining_unit")));
    }

    private static TurnTick tick(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("source", "read_available", "manager_match_count", "manager_contains_context", "scalar_tail_allows_tick", "context_tick_eligible", "unavailable_reason"));
        return new TurnTick(bool(row.get("read_available")), optionalInteger(row.get("manager_match_count")), nullableBool(row.get("manager_contains_context")),
                nullableBool(row.get("scalar_tail_allows_tick")), nullableBool(row.get("context_tick_eligible")), optionalText(row.get("unavailable_reason")), StrictJson.text(row.get("source")));
    }

    private static SourceFrame frame(ObjectNode value) {
        JsonNode actor = value.get("played_character"); validateActor(actor);
        return new SourceFrame(optionalInteger(value.get("revision")), optionalInteger(value.get("native_revision")), optionalInteger(value.get("date_raw")),
                actor != null && actor.isObject() ? optionalInteger(actor.get("character_id")) : null,
                actualTrue(value.get("paused")), actualTrue(value.get("map_ready")), actor != null && actor.isObject() && actualTrue(actor.get("alive")), optionalText(value.get("snapshot_id")), build(value));
    }

    private static Build build(ObjectNode snapshot) {
        JsonNode diagnostics = snapshot.get("diagnostics"); JsonNode hello = diagnostics != null && diagnostics.isObject() ? diagnostics.get("hello") : null;
        // Existing archived 1.19 contracts predate hello projection. This branch
        // can never label an input 1.20 or qualify its native runtime.
        if (hello == null || !hello.isObject()) { return Build.LEGACY_11906; }
        JsonNode version = hello.has("expected_ck3_version") ? hello.get("expected_ck3_version") : hello.get("game_version");
        JsonNode sha = hello.has("expected_ck3_sha256") ? hello.get("expected_ck3_sha256") : hello.get("executable_sha256");
        String actualVersion = optionalText(version); String actualSha = optionalText(sha);
        for (Build build : Build.values()) { if (build.version().equals(actualVersion) && actualSha != null && build.sha256().equals(actualSha.toUpperCase(Locale.ROOT))) { return build; } }
        throw new IllegalArgumentException("private nonwar source lacks a frozen exact native build");
    }

    private static Build buildVersion(String version) {
        for (Build build : Build.values()) { if (build.version().equals(version)) { return build; } }
        throw new IllegalArgumentException("unknown native law value-contract version");
    }

    public static byte[] encode(Payload value) {
        ObjectNode row = StrictJson.object(); row.put("schema", CrownFinalTerms.SCHEMA); row.put("snapshot_revision", value.snapshotRevision());
        row.put("date_raw", value.dateRaw()); row.put("actor_character_id", value.actorCharacterId()); row.put("cost_scale", 100000);
        var slots = row.putArray("cost_slots"); CrownFinalTerms.SLOTS.forEach(slots::add); var groups = row.putArray("groups");
        for (Group group : value.groups()) {
            ObjectNode item = groups.addObject(); item.put("group_key", wire(group.key())); putNullable(item, "active_law_key", group.activeLawKey()); var candidates = item.putArray("candidates");
            for (Candidate candidate : group.candidates()) {
                ObjectNode record = candidates.addObject(); record.put("law_key", candidate.lawKey()); record.put("active", candidate.active()); record.put("final_status", wire(candidate.finalStatus()));
                record.put("final_can_enact", candidate.finalCanEnact()); record.put("native_reason", candidate.nativeReason()); var costs = record.putArray("cost_raw"); candidate.costRaw().forEach(cost -> costs.add(cost.longValue()));
                if (candidate.profileStatus() != null) { record.put("succession_profile_status", wire(candidate.profileStatus())); if (candidate.profile() == null) { record.putNull("succession_profile"); } else { record.set("succession_profile", encodeProfile(candidate.profile())); } }
            }
        }
        if (value.cooldown() != null) { row.set(COOLDOWN, encodeCooldown(value.cooldown())); }
        if (value.turnTick() != null) { row.set(TICK, encodeTick(value.turnTick())); }
        return StrictJson.canonical(row);
    }

    public static byte[] encode(Readback value) {
        ObjectNode row = object(StrictJson.parse(encode(value.payload()))); row.put("exact_ck3_build", value.build().version());
        if (value.build() != Build.LEGACY_11906) { row.put("exe_sha256", value.build().sha256()); }
        putNullable(row, "queried_snapshot_id", value.queriedSnapshotId()); row.put("queried_revision", value.queriedRevision());
        row.put("queried_native_revision", value.queriedNativeRevision()); putNullable(row, "post_snapshot_id", value.postSnapshotId()); return StrictJson.canonical(row);
    }

    private static ObjectNode encodeProfile(SuccessionProfile value) {
        ObjectNode row = StrictJson.object(); putNullable(row, "order", value.order() == null ? null : wire(value.order())); putNullable(row, "traversal", value.traversal() == null ? null : wire(value.traversal()));
        putNullable(row, "rank", value.rank() == null ? null : wire(value.rank())); putNullable(row, "division", value.division() == null ? null : wire(value.division()));
        row.put("primary_heir_minimum_share_raw", value.primaryHeirMinimumShareRaw()); row.put("primary_heir_minimum_share_scale", 100000); row.put("create_primary_tier_titles", value.createPrimaryTierTitles()); return row;
    }

    private static ObjectNode encodeCooldown(RawObservation value) {
        ObjectNode row = StrictJson.object(); row.put("read_available", value.readAvailable()); nullable(row, "present", value.present()); nullable(row, "timed", value.timed());
        nullable(row, "expiry_raw", value.expiryRaw()); nullable(row, "current_clock_raw", value.currentClockRaw()); nullable(row, "remaining_raw", value.remainingRaw());
        if (value.retryDateRaw() == null) { row.putNull("retry_date_raw"); } else { row.put("retry_date_raw", value.retryDateRaw()); }
        row.put("expiry_type", value.expiryType()); row.put("remaining_unit", value.remainingUnit()); return row;
    }

    private static ObjectNode encodeTick(TurnTick value) {
        ObjectNode row = StrictJson.object(); row.put("source", value.source()); row.put("read_available", value.readAvailable());
        if (value.managerMatchCount() == null) { row.putNull("manager_match_count"); } else { row.put("manager_match_count", value.managerMatchCount()); }
        nullable(row, "manager_contains_context", value.managerContainsContext()); nullable(row, "scalar_tail_allows_tick", value.scalarTailAllowsTick());
        nullable(row, "context_tick_eligible", value.contextTickEligible()); putNullable(row, "unavailable_reason", value.unavailableReason()); return row;
    }

    private static boolean sameJson(JsonNode left, JsonNode right) {
        if (left == null || right == null) { return left == right; }
        if (left.isNumber() && right.isNumber()) { return left.decimalValue().compareTo(right.decimalValue()) == 0; }
        if (left.isObject() && right.isObject()) { if (left.size() != right.size()) { return false; } for (var entry : ((ObjectNode) left).properties()) { if (!right.has(entry.getKey()) || !sameJson(entry.getValue(), right.get(entry.getKey()))) { return false; } } return true; }
        if (left.isArray() && right.isArray()) { if (left.size() != right.size()) { return false; } for (int index = 0; index < left.size(); index++) { if (!sameJson(left.get(index), right.get(index))) { return false; } } return true; }
        return left.equals(right);
    }
    private static void validateActor(JsonNode value) { if (value == null || !value.isObject()) { return; } if (value.has("character_id")) { optionalInteger(value.get("character_id")); } if (value.hasNonNull("alive")) { bool(value.get("alive")); } }
    private static ObjectNode object(JsonNode value) { require(value != null && value.isObject(), "JSON object required"); return (ObjectNode) value; }
    private static BigInteger integer(JsonNode value) { require(value != null && value.isIntegralNumber(), "actual integer token required"); return value.bigIntegerValue(); }
    private static BigInteger optionalInteger(JsonNode value) { return value == null || value.isNull() ? null : integer(value); }
    private static Integer nullableI32(JsonNode value) { return value.isNull() ? null : Math.toIntExact(StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE)); }
    private static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "actual boolean token required"); return value.booleanValue(); }
    private static Boolean nullableBool(JsonNode value) { return value.isNull() ? null : bool(value); }
    private static boolean actualTrue(JsonNode value) { return value != null && !value.isNull() && bool(value); }
    private static boolean actualFalse(JsonNode value) { return value != null && !value.isNull() && !bool(value); }
    private static String string(JsonNode value) { require(value != null && value.isTextual(), "actual string token required"); return value.textValue().isEmpty() ? "" : StrictJson.text(value); }
    private static String optionalText(JsonNode value) { return value == null || value.isNull() ? null : string(value); }
    private static <E extends Enum<E>> E enumeration(JsonNode value, Class<E> type) {
        String text = StrictJson.text(value); E result = Enum.valueOf(type, text.toUpperCase(Locale.ROOT)); require(wire(result).equals(text), "exact lowercase native enum required"); return result;
    }
    private static <E extends Enum<E>> E optionalEnum(JsonNode value, Class<E> type) { return value.isNull() ? null : enumeration(value, type); }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static void putNullable(ObjectNode row, String key, String value) { if (value == null) { row.putNull(key); } else { row.put(key, value); } }
    private static void nullable(ObjectNode row, String key, Boolean value) { if (value == null) { row.putNull(key); } else { row.put(key, value.booleanValue()); } }
    private static void nullable(ObjectNode row, String key, Integer value) { if (value == null) { row.putNull(key); } else { row.put(key, value.intValue()); } }
    private static void require(boolean condition, String message) { CrownFinalTerms.require(condition, message); }
}
