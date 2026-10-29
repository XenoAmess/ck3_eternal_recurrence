package org.xar.ck3.control.wave2.military.holyhirecontract;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.holyreinf.HolyReinforcement.Context;
import org.xar.ck3.control.wave2.military.holyreinf.HolyReinforcement.Frame;
import org.xar.ck3.control.wave2.military.holyreinf.HolyReinforcement.Snapshot;
import org.xar.ck3.control.wave2.military.holyreinf.HolyReinforcementCodec;
import static org.xar.ck3.control.wave2.military.projection.HolyInputValidation.require;
import org.xar.ck3.control.wave2.military.projection.HolyInputValidation;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import static org.xar.ck3.control.wave2.military.holyhirecontract.HolyHireContract.*;

/** Strict pure adapters for the existing owner. No transport send, capability grant, retry or game operation. */
public final class HolyHireCodec {
    public static final String REQUEST_SCHEMA = "xar.ck3.holy-hire-request-input.v1";
    public static final String ACK_SCHEMA = "xar.ck3.holy-hire-ack-input.v1";
    public static final String QUERY_SCHEMA = "xar.ck3.holy-context-query-input.v1";
    private static final int BUDGET = 131_072;
    private static final long INVALID_REF = 0xffff_ffffL;
    private static final String SHA3 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
    private static final String SHA4 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private HolyHireCodec() { }

    public static Request request(byte[] input) {
        ObjectNode root = envelope(input, REQUEST_SCHEMA, Set.of("schema", "holy_order_id", "expected_revision"));
        return request(root.get("holy_order_id"), root.get("expected_revision"));
    }
    private static Request request(JsonNode id, JsonNode revision) {
        return new Request(HolyInputValidation.integer(id, 0, INVALID_REF - 1), integer(revision));
    }
    public static byte[] acknowledge(byte[] input) { return StrictJson.canonical(acknowledgeNode(input), BUDGET); }
    public static ObjectNode acknowledgeNode(byte[] input) {
        ObjectNode root = envelope(input, ACK_SCHEMA, Set.of("schema", "snapshot", "expected_holy_order_id", "expected_revision", "ack", "bind_submission_frame"));
        JsonNode rawSnapshot = root.get("snapshot"); Snapshot snapshot = HolyReinforcementCodec.snapshot(rawSnapshot);
        Request request = request(root.get("expected_holy_order_id"), root.get("expected_revision"));
        ObjectNode raw = object(root.get("ack")); require("hire-holy-order-v1".equals(text(raw.get("step"))), "native holy-order hire ACK malformed");
        String version = version(raw), expectedSchema = version.equals("1.20.0.3") ? "ck3_12003_holy_order_hire_action_v1" : "ck3_12004_holy_order_hire_action_v1";
        require(!version.equals("1.20.0.4") || (version.equals(snapshot.version()) && sha(raw).equals(snapshot.sha())), "native holy-order hire ACK differs from submission build");
        ObjectNode action = object(raw.get("holy_order_hire")); require(expectedSchema.equals(text(action.get("schema"))), "native holy-order hire action schema malformed");
        Status status;
        JsonNode rawStatus = action.get("status");
        require(rawStatus != null && rawStatus.isTextual(), "native holy-order hire action status malformed");
        try { status = Status.valueOf(rawStatus.textValue().toUpperCase(Locale.ROOT)); }
        catch (IllegalArgumentException enumRefusal) { throw new ProjectionDomainRejection("native holy-order hire action status malformed"); }
        Long employer = null;
        if (!nullish(action.get("prior_employer_character_id"))) { employer = HolyInputValidation.integer(action.get("prior_employer_character_id"), 0, INVALID_REF - 1); }
        JsonNode prior = action.get("prior_context"); boolean priorCapture = false;
        if (prior instanceof ObjectNode && !nullish(prior.get("capture_epoch"))) {
            BigInteger epoch = integer(prior.get("capture_epoch"));
            if (epoch.signum() > 0) { HolyReinforcementCodec.context(prior, snapshot); priorCapture = true; }
        }
        Frame ackFrame = new Frame(null, null, integer(raw.get("snapshot_revision")), integer(raw.get("date_raw")), null);
        Frame actionFrame = new Frame(null, null, integer(action.get("snapshot_revision")), integer(action.get("date_raw")), null);
        Action typed = new Action(status, actionFrame, HolyInputValidation.integer(action.get("holy_order_id"), 0, INVALID_REF),
                referenceOrNull(action.get("actor_character_id")), bool(action.get("holy_order_resolved")),
                bool(action.get("native_command_validation_observable")), optionalBool(action.get("native_command_valid")),
                bool(action.get("command_submitted")), bool(action.get("verification_pending")), bool(action.get("after_state_observed")),
                employer, nullableText(action.get("unavailable_reason")), priorCapture);
        HolyHireContract.validate(new Acknowledgement(version, integer(raw.get("command_sequence")), ackFrame,
                bool(raw.get("read_only")), bool(raw.get("accepted")), text(raw.get("status")),
                (int) HolyInputValidation.integer(action.get("native_hire_mode"), Integer.MIN_VALUE, Integer.MAX_VALUE), typed), snapshot.frame(), request);
        ObjectNode out = raw.deepCopy(); boolean bind = bool(root.get("bind_submission_frame"));
        if (bind) {
            require(Boolean.TRUE.equals(snapshot.paused()) && Boolean.TRUE.equals(snapshot.mapReady()) && Boolean.TRUE.equals(snapshot.actorAlive()), "holy-order hire requires a living paused player");
            require(request.expectedRevision().equals(snapshot.frame().revision()), "holy-order hire source revision is stale");
            put(out, "submitted_snapshot_id", snapshot.frame().snapshotId()); put(out, "submitted_revision", snapshot.frame().revision());
            put(out, "submitted_native_revision", snapshot.frame().nativeRevision());
        }
        return out;
    }

    /** Converts one already-received packet with the exact before/after binding used by the existing read helper. */
    public static byte[] query(byte[] input) { return StrictJson.canonical(queryNode(input), BUDGET); }
    public static ObjectNode queryNode(byte[] input) {
        ObjectNode root = envelope(input, QUERY_SCHEMA, Set.of("schema", "before_snapshot", "after_snapshot", "expected_revision", "request_id", "packet"));
        ObjectNode beforeRaw = object(root.get("before_snapshot")), afterRaw = object(root.get("after_snapshot"));
        Snapshot before = HolyReinforcementCodec.snapshot(beforeRaw), after = HolyReinforcementCodec.snapshot(afterRaw);
        BigInteger expected = integer(root.get("expected_revision"));
        require(expected.signum() > 0 && expected.equals(before.frame().revision()) && before.frame().nativeRevision() != null
                && before.frame().nativeRevision().signum() > 0 && Boolean.TRUE.equals(before.paused()) && Boolean.TRUE.equals(before.mapReady())
                && Boolean.TRUE.equals(before.actorAlive()), "private native observation requires a living paused player");
        require(before.frame().equals(after.frame()) && Objects.equals(before.paused(), after.paused())
                && Objects.equals(before.mapReady(), after.mapReady()) && Objects.equals(before.actorAlive(), after.actorAlive()), "private native observation crossed its paused frame");
        for (String field : List.of("active_event", "pending_character_interaction", "one_life_terminal_reason")) {
            require(Objects.equals(nullAsMissing(beforeRaw.get(field)), nullAsMissing(afterRaw.get(field))), "private native observation crossed its paused scope");
        }
        ObjectNode packet = object(root.get("packet"));
        require("command_result".equals(text(packet.get("type"))) && integer(packet.get("protocol_version")).equals(BigInteger.ONE)
                && text(packet.get("request_id")).equals(text(root.get("request_id"))) && bool(packet.get("ok")), "private native observation returned RED");
        ObjectNode result = object(packet.get("result"));
        require("query-player-holy-order-context-v1".equals(text(result.get("step"))) && bool(result.get("accepted"))
                && bool(result.get("private_build")) && bool(result.get("read_only")) && !bool(result.get("advertised")), "private native observation envelope malformed");
        String version = version(result); require(version.equals(before.version()) && sha(result).equals(before.sha()), "native holy-order envelope differs from queried build");
        JsonNode rawContext = result.get("player_holy_order_context"); Context context = HolyReinforcementCodec.context(rawContext, before);
        QueryEnvelope query = new QueryEnvelope(version, text(result.get("backend_id")), text(result.get("domain_key")), text(result.get("status")),
                integer(result.get("snapshot_revision")), integer(result.get("date_raw")));
        HolyHireContract.validateQuery(query, before.frame(), context.available());
        ObjectNode out = object(rawContext).deepCopy(); out.put("exact_ck3_build", version).put("exe_sha256", sha(result));
        put(out, "queried_snapshot_id", before.frame().snapshotId()); put(out, "queried_revision", before.frame().revision());
        put(out, "queried_native_revision", before.frame().nativeRevision());
        out.set("snapshot_revision", result.get("snapshot_revision").deepCopy()); out.set("query_date_raw", result.get("date_raw").deepCopy());
        out.put("backend_id", query.backendId()).put("domain_key", "player_holy_order_context_v1").put("status", query.status())
                .put("read_only", true).put("advertised", false);
        return out;
    }
    private static ObjectNode envelope(byte[] input, String schema, Set<String> fields) {
        ObjectNode out = HolyInputValidation.parseObject(input, BUDGET, fields); require(schema.equals(text(out.get("schema"))), "wrong holy-hire schema"); return out;
    }
    private static ObjectNode object(JsonNode value) { require(value instanceof ObjectNode, "JSON object required"); return (ObjectNode) value; }
    private static BigInteger integer(JsonNode value) { require(value != null && value.isIntegralNumber(), "exact JSON integer required"); return value.bigIntegerValue(); }
    private static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "actual JSON boolean required"); return value.booleanValue(); }
    private static Boolean optionalBool(JsonNode value) { return nullish(value) ? null : bool(value); }
    private static String text(JsonNode value) { require(value != null && value.isTextual(), "actual JSON text required"); return value.textValue(); }
    private static String nullableText(JsonNode value) { return nullish(value) ? null : text(value); }
    private static boolean nullish(JsonNode value) { return value == null || value.isNull(); }
    private static JsonNode nullAsMissing(JsonNode value) { return nullish(value) ? null : value; }
    private static Long referenceOrNull(JsonNode value) { return nullish(value) ? null : HolyInputValidation.integer(value, 0, INVALID_REF); }
    private static String sha(ObjectNode value) { return text(value.get("executable_sha256")).toUpperCase(Locale.ROOT); }
    private static String version(ObjectNode value) {
        String version = text(value.get("game_version")), sha = sha(value);
        require(version.equals("1.20.0.3") && sha.equals(SHA3) || version.equals("1.20.0.4") && sha.equals(SHA4), "native source does not match frozen exact build"); return version;
    }
    private static void put(ObjectNode out, String field, String value) { if (value == null) { out.putNull(field); } else { out.put(field, value); } }
    private static void put(ObjectNode out, String field, BigInteger value) { if (value == null) { out.putNull(field); } else { out.put(field, value); } }
}
