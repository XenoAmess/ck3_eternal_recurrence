package org.xar.ck3.control.governance.council;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.governance.council.CouncilModels.*;

/** Runtime boundary shared by native readers and ordinary governance consumers. */
public final class CouncilCodec {
    private CouncilCodec() { }
    public static final Set<String> PAYLOAD_FIELDS = Set.of("snapshot", "owner_character_id", "position",
            "candidate_collection_complete", "candidates", "readiness");
    private static final Set<String> READY = Set.of("identity_ready", "candidate_collection_ready", "incumbent_ready",
            "incumbent_main_skill_ready", "candidate_legality_ready", "main_skill_ready", "action_route_ready", "same_frame_ready", "ready");
    private static final Set<String> TAX = Set.of("status", "unavailable_reason", "active_task_id", "owner_character_id",
            "incumbent_character_id", "task_key", "frozen", "modifier_id", "keyword_id", "observed_keyword_key", "value");

    public static Candidates decode(byte[] bytes, Frame frame, Position role) {
        return decodeNode(StrictJson.object(StrictJson.parse(bytes), PAYLOAD_FIELDS), frame, role);
    }
    public static byte[] encode(Candidates value) { return Objects.requireNonNull(value).original().bytes(); }
    /** Native metadata is checked before projecting the sole normalized six-field contract. */
    public static Candidates decodeNative(byte[] bytes, Frame frame, Position role, String expectedVersion, String expectedSha256) {
        Set<String> fields = new HashSet<>(PAYLOAD_FIELDS);
        fields.addAll(Set.of("schema", "schema_version", "capability", "exact_build", "status", "unavailable_reason", "source_unavailable_reason"));
        ObjectNode nativePayload = StrictJson.object(StrictJson.parse(bytes), fields);
        StrictJson.require(text(nativePayload, "schema").equals("xar.ck3.council-composition-candidates/v1")
                && number(nativePayload, "schema_version", 1, 1) == 1
                && text(nativePayload, "capability").equals("game.query.council-composition-candidates-v1")
                && text(nativePayload, "status").equals("available"), "native Council metadata/status mismatch");
        nullValue(nativePayload.get("unavailable_reason")); nullValue(nativePayload.get("source_unavailable_reason"));
        ObjectNode exact = StrictJson.object(nativePayload.get("exact_build"), Set.of("game_version", "executable_sha256"));
        requireBuild(text(exact, "game_version"), text(exact, "executable_sha256"));
        requireBuild(expectedVersion, expectedSha256);
        StrictJson.require(text(exact, "game_version").equals(expectedVersion)
                && text(exact, "executable_sha256").equalsIgnoreCase(expectedSha256), "council connected exact-build drift");
        ObjectNode payload = StrictJson.object();
        for (String key : PAYLOAD_FIELDS) payload.set(key, nativePayload.get(key));
        return decodeNode(payload, frame, role);
    }
    public static Tax validateTax(byte[] bytes, int ownerId, OptionalInt incumbentId) {
        return tax(StrictJson.object(StrictJson.parse(bytes), TAX), ownerId, incumbentId);
    }
    public static void requireBuild(String version, String sha256) {
        String expected = switch (StrictJson.text(version)) {
            case "1.19.0.6" -> "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
            case "1.20.0.2" -> "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
            case "1.20.0.3" -> "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
            case "1.20.0.4" -> "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
            default -> throw new IllegalArgumentException("unknown exact CK3 build");
        };
        StrictJson.require(expected.equalsIgnoreCase(sha256), "CK3 version/executable SHA pair mismatch");
    }
    private static Candidates decodeNode(ObjectNode payload, Frame frame, Position role) {
        Objects.requireNonNull(frame); Objects.requireNonNull(role);
        ObjectNode observed = StrictJson.object(payload.get("snapshot"), Set.of("snapshot_id", "public_revision", "native_revision", "date_raw", "paused"));
        StrictJson.require(text(observed, "snapshot_id").equals(frame.snapshotId())
                && u64(observed.get("public_revision"), true).equals(frame.publicRevision())
                && u64(observed.get("native_revision"), true).equals(frame.nativeRevision())
                && number(observed, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE) == frame.dateRaw()
                && bool(observed.get("paused")), "council requested paused frame mismatch");
        StrictJson.require(id(payload.get("owner_character_id")) == frame.ownerId(), "council owner mismatch");
        ObjectNode position = object(payload.get("position"));
        Set<String> required = Set.of("position_key", "incumbent_character_id", "incumbent_main_skill", "vacant", "action_route");
        Set<String> actual = new HashSet<>(); position.fieldNames().forEachRemaining(actual::add);
        StrictJson.require(actual.containsAll(required), "council position fields missing");
        actual.removeAll(required);
        StrictJson.require(Set.of("current_task_owner_domain_tax_mult_v1").containsAll(actual), "unknown council position fields");
        StrictJson.require(text(position, "position_key").equals(role.key()), "council position mismatch");
        OptionalInt incumbent = nullableId(position.get("incumbent_character_id"));
        JsonNode incumbentSkillRaw = position.get("incumbent_main_skill");
        OptionalInt incumbentSkill = isNull(incumbentSkillRaw) ? OptionalInt.empty() : OptionalInt.of(skill(incumbentSkillRaw, role));
        boolean vacant = bool(position.get("vacant"));
        StrictJson.require(vacant == incumbent.isEmpty() && vacant == incumbentSkill.isEmpty(), "vacancy/identity/skill mismatch");
        ActionRoute route = route(position.get("action_route"));
        Optional<Tax> tax = position.has("current_task_owner_domain_tax_mult_v1")
                ? Optional.of(tax(StrictJson.object(position.get("current_task_owner_domain_tax_mult_v1"), TAX), frame.ownerId(), incumbent)) : Optional.empty();
        Seat seat = new Seat(role, incumbent, incumbentSkill, route, tax);
        StrictJson.trueValue(payload.get("candidate_collection_complete"));
        JsonNode rows = payload.get("candidates"); StrictJson.require(rows != null && rows.isArray(), "candidate list required");
        List<Candidate> candidates = new ArrayList<>();
        for (JsonNode value : rows) {
            ObjectNode row = StrictJson.object(value, Set.of("character_id", "native_collection_ordinal", "eligible", "eligibility_reason", "main_skill", "action_route"));
            StrictJson.trueValue(row.get("eligible"));
            StrictJson.require(text(row, "eligibility_reason").equals("native_candidate_provider_accepted"), "candidate provider did not accept row");
            candidates.add(new Candidate(id(row.get("character_id")), number(row, "native_collection_ordinal", 0, 0xffff_ffffL),
                    skill(row.get("main_skill"), role), route(row.get("action_route"))));
        }
        ObjectNode ready = StrictJson.object(payload.get("readiness"), READY);
        READY.forEach(key -> StrictJson.trueValue(ready.get(key)));
        return new Candidates(frame, seat, candidates, new JsonBody(StrictJson.canonical(payload)));
    }
    private static Tax tax(ObjectNode value, int ownerId, OptionalInt incumbentId) {
        StrictJson.require(id(value.get("owner_character_id")) == ownerId
                && nullableId(value.get("incumbent_character_id")).equals(incumbentId), "tax selected owner/incumbent mismatch");
        TaskContext context = new TaskContext((int) number(value, "active_task_id", Integer.MIN_VALUE, Integer.MAX_VALUE), ownerId,
                incumbentId, nullableText(value.get("task_key")), nullableBool(value.get("frozen")),
                (int) number(value, "modifier_id", 0, 65535), (int) number(value, "keyword_id", 0, Integer.MAX_VALUE),
                nullableText(value.get("observed_keyword_key")));
        return switch (text(value, "status")) {
            case "available" -> {
                nullValue(value.get("unavailable_reason"));
                yield new AvailableTax(context, fixed(value.get("value")));
            }
            case "unavailable" -> {
                nullValue(value.get("value"));
                yield new UnavailableTax(context, StrictJson.text(value.get("unavailable_reason")));
            }
            default -> throw new IllegalArgumentException("tax availability state invalid");
        };
    }
    public static Fixed fixed(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("raw", "scale"));
        StrictJson.require(number(row, "scale", Fixed.SCALE, Fixed.SCALE) == Fixed.SCALE, "native fixed scale mismatch");
        return new Fixed(number(row, "raw", Long.MIN_VALUE, Long.MAX_VALUE));
    }
    private static int skill(JsonNode value, Position role) {
        ObjectNode row = StrictJson.object(value, Set.of("key", "value"));
        StrictJson.require(text(row, "key").equals(role.skill()), "council main skill key mismatch");
        return (int) number(row, "value", 0, Integer.MAX_VALUE);
    }
    private static ActionRoute route(JsonNode value) {
        return switch (StrictJson.text(value)) { case "assign" -> ActionRoute.ASSIGN; case "replace" -> ActionRoute.REPLACE;
            default -> throw new IllegalArgumentException("invalid council action route"); };
    }
    public static ObjectNode object(JsonNode value) { StrictJson.require(value instanceof ObjectNode, "JSON object required"); return (ObjectNode) value; }
    public static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    public static long number(ObjectNode row, String field, long minimum, long maximum) { return StrictJson.integer(row.get(field), minimum, maximum); }
    public static BigInteger u64(JsonNode value, boolean positive) { return StrictJson.integer(value, positive ? BigInteger.ONE : BigInteger.ZERO, StrictJson.UINT64_MAX); }
    public static boolean bool(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "exact JSON boolean required"); return value.booleanValue(); }
    public static boolean isNull(JsonNode value) { StrictJson.require(value != null, "missing is distinct from null"); return value.isNull(); }
    public static void nullValue(JsonNode value) { StrictJson.require(isNull(value), "explicit JSON null required"); }
    public static int id(JsonNode value) { int result = (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); characterId(result); return result; }
    private static OptionalInt nullableId(JsonNode value) { return isNull(value) ? OptionalInt.empty() : OptionalInt.of(id(value)); }
    private static Optional<String> nullableText(JsonNode value) { return isNull(value) ? Optional.empty() : Optional.of(StrictJson.text(value)); }
    private static Optional<Boolean> nullableBool(JsonNode value) { return isNull(value) ? Optional.empty() : Optional.of(bool(value)); }
}
