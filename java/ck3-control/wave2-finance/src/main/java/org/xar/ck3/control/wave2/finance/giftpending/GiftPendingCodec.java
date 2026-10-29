package org.xar.ck3.control.wave2.finance.giftpending;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ack;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.AppliedReceipt;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Baseline;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.BeginRequest;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ObjectEvidence;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingStatus;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ReceiptStatus;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ResolvedOutcome;

/** Exact persisted v1 fields; existing native ACK/receipt/observation objects are declared projections. */
public final class GiftPendingCodec {
    public static final int MAX_BYTES = 65_536;
    private static final Set<String> LEDGER_FIELDS = Set.of("schema", "format_version", "pending", "resolved_request_outcomes");
    private static final Set<String> PENDING_FIELDS = Set.of("request_id", "episode_run_id", "source_faction_id",
            "source_round_id", "source_bridge_pid", "source_bridge_creation_date", "recipient_character_id",
            "pre_snapshot_revision", "pre_native_snapshot_revision", "pre_date_raw", "pre_player_character_id",
            "pre_player_gold_raw", "pre_recipient_opinion_of_player", "pre_gift_opinion_present",
            "pre_source_faction_power_raw", "pre_source_faction_discontent_raw", "pre_source_faction_member_character_ids",
            "pre_source_faction_targeting_player", "gold_cost_raw", "opinion_delta", "minimum_gold_reserve_raw",
            "checkpoint_sha256_before_submit", "status", "ack");
    private GiftPendingCodec() { }

    public static Ledger decodeLedger(byte[] raw) {
        StrictJson.require(raw != null && raw.length <= MAX_BYTES, "bounded faction gift ledger required");
        // The actual legacy reader uses utf-8-sig. Accept its optional BOM only at this file boundary.
        byte[] json = raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf
                ? java.util.Arrays.copyOfRange(raw, 3, raw.length) : raw;
        return ledger(StrictJson.parse(json, MAX_BYTES));
    }
    static Ledger ledger(JsonNode value) {
        ObjectNode node = StrictJson.object(value, LEDGER_FIELDS);
        StrictJson.require(GiftPendingModel.SCHEMA.equals(text(node, "schema")), "faction gift pending ledger shape is unknown");
        StrictJson.require(integer(node, "format_version").equals(BigInteger.ONE), "format_version must be exact integer one");
        JsonNode resolved = object(node.get("resolved_request_outcomes")); Map<String, ResolvedOutcome> outcomes = new HashMap<>();
        resolved.properties().forEach(entry -> outcomes.put(StrictJson.text(entry.getKey()), outcome(StrictJson.text(entry.getValue()))));
        JsonNode pending = node.get("pending");
        return new Ledger(pending.isNull() ? Optional.empty() : Optional.of(pending(pending)), outcomes);
    }
    static PendingAction pending(JsonNode value) {
        ObjectNode node = StrictJson.object(value, PENDING_FIELDS);
        requireBoolean(node, "pre_gift_opinion_present", false); requireBoolean(node, "pre_source_faction_targeting_player", true);
        Baseline pre = new Baseline(integer(node, "source_faction_id"), integer(node, "recipient_character_id"),
                integer(node, "pre_snapshot_revision"), integer(node, "pre_native_snapshot_revision"), integer(node, "pre_date_raw"),
                integer(node, "pre_player_character_id"), integer(node, "pre_player_gold_raw"),
                integer(node, "pre_recipient_opinion_of_player"), integer(node, "pre_source_faction_power_raw"),
                integer(node, "pre_source_faction_discontent_raw"), integers(node.get("pre_source_faction_member_character_ids")),
                integer(node, "gold_cost_raw"), integer(node, "opinion_delta"));
        JsonNode ack = node.get("ack");
        return new PendingAction(text(node, "request_id"), text(node, "episode_run_id"), text(node, "source_round_id"),
                new ProcessIdentity(integer(node, "source_bridge_pid"), text(node, "source_bridge_creation_date")), pre,
                integer(node, "minimum_gold_reserve_raw"), text(node, "checkpoint_sha256_before_submit"), status(text(node, "status")),
                ack.isNull() ? Optional.empty() : Optional.of(evidence(ack)));
    }
    /** Wrapper owned by this leaf; the native observation remains an extensible projection. */
    public static BeginRequest decodeBegin(byte[] raw) {
        JsonNode node = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("request_id", "episode_run_id", "source_round_id",
                "source_bridge_pid", "source_bridge_creation_date", "observation", "minimum_gold_reserve_raw", "checkpoint_sha256_before_submit"));
        JsonNode observation = object(node.get("observation")); JsonNode preview = object(observation.get("gift_preview"));
        requireBoolean(observation, "gift_opinion_present", false); requireBoolean(observation, "source_faction_targeting_player", true);
        return new BeginRequest(text(node, "request_id"), text(node, "episode_run_id"), text(node, "source_round_id"),
                new ProcessIdentity(integer(node, "source_bridge_pid"), text(node, "source_bridge_creation_date")),
                new Baseline(integer(observation, "queried_source_faction_id"), integer(observation, "recipient_character_id"),
                        integer(observation, "snapshot_revision"), integer(observation, "native_snapshot_revision"),
                        integer(observation, "observed_date_raw"), integer(observation, "player_character_id"),
                        integer(observation, "player_gold_raw"), integer(observation, "recipient_opinion_of_player"),
                        integer(observation, "source_faction_power_raw"), integer(observation, "source_faction_discontent_raw"),
                        integers(observation.get("source_faction_member_character_ids")), integer(preview, "gold_cost_raw"), integer(preview, "opinion_delta")),
                integer(node, "minimum_gold_reserve_raw"), text(node, "checkpoint_sha256_before_submit"));
    }
    public static Ack decodeAck(byte[] raw) {
        JsonNode node = object(StrictJson.parse(raw, MAX_BYTES));
        if (node.has("schema_version")) {
            StrictJson.require(integer(node, "schema_version").equals(BigInteger.ONE), "ACK schema must be exact integer one");
        }
        StrictJson.require("submitted_verification_pending".equals(text(node, "status")), "pending submission ACK status required");
        requireBoolean(node, "verification_pending", true);
        return new Ack(text(node, "request_id"), integer(node, "source_faction_id"), integer(node, "recipient_character_id"), evidence(node));
    }
    public static AppliedReceipt decodeReceipt(byte[] raw) {
        JsonNode node = object(StrictJson.parse(raw, MAX_BYTES));
        StrictJson.require(integer(node, "schema_version").equals(BigInteger.ONE), "receipt schema must be exact integer one");
        requireBoolean(node, "postcondition_verified", true); requireBoolean(node, "mitigation_applied", true);
        requireBoolean(node, "post_gift_opinion_present", true);
        ReceiptStatus status = switch (text(node, "status")) {
            case "mitigated" -> ReceiptStatus.MITIGATED;
            case "left" -> ReceiptStatus.LEFT;
            default -> throw new IllegalArgumentException("receipt status does not prove application");
        };
        return new AppliedReceipt(text(node, "request_id"), status, integer(node, "source_faction_id"),
                integer(node, "recipient_character_id"), integer(node, "player_character_id"), integer(node, "post_snapshot_revision"),
                integer(node, "post_native_snapshot_revision"), integer(node, "post_observed_date_raw"), integer(node, "post_player_gold_raw"),
                integer(node, "post_gift_opinion_modifier_value"), evidence(node));
    }
    public static byte[] encodeLedger(Ledger ledger) { return json(encodeLedgerNode(ledger)); }
    /** Shared boundary serializer for the actual receipt/cold route's extensible object projection. */
    public static byte[] encodeObjectProjection(JsonNode projection) { object(projection); return json(projection); }
    static ObjectNode encodeLedgerNode(Ledger ledger) {
        ObjectNode node = StrictJson.object(); node.put("schema", GiftPendingModel.SCHEMA); node.put("format_version", 1);
        if (ledger.pending().isPresent()) { node.set("pending", encodePending(ledger.pending().orElseThrow())); }
        else { node.putNull("pending"); }
        ObjectNode resolved = node.putObject("resolved_request_outcomes");
        ledger.resolvedRequestOutcomes().forEach((request, outcome) -> resolved.put(request, outcome.wire())); return node;
    }
    static ObjectNode encodePending(PendingAction pending) {
        Baseline pre = pending.baseline(); ObjectNode node = StrictJson.object();
        node.put("request_id", pending.requestId()); node.put("episode_run_id", pending.episodeRunId());
        node.put("source_round_id", pending.sourceRoundId()); node.put("source_bridge_pid", pending.sourceProcess().pid());
        node.put("source_bridge_creation_date", pending.sourceProcess().creationDate()); node.put("source_faction_id", pre.sourceFactionId());
        node.put("recipient_character_id", pre.recipientCharacterId()); node.put("pre_snapshot_revision", pre.snapshotRevision());
        node.put("pre_native_snapshot_revision", pre.nativeSnapshotRevision()); node.put("pre_date_raw", pre.dateRaw());
        node.put("pre_player_character_id", pre.playerCharacterId()); node.put("pre_player_gold_raw", pre.playerGoldRaw());
        node.put("pre_recipient_opinion_of_player", pre.recipientOpinionOfPlayer()); node.put("pre_gift_opinion_present", false);
        node.put("pre_source_faction_power_raw", pre.sourceFactionPowerRaw()); node.put("pre_source_faction_discontent_raw", pre.sourceFactionDiscontentRaw());
        var members = node.putArray("pre_source_faction_member_character_ids"); pre.sourceFactionMemberCharacterIds().forEach(members::add);
        node.put("pre_source_faction_targeting_player", true); node.put("gold_cost_raw", pre.goldCostRaw()); node.put("opinion_delta", pre.opinionDelta());
        node.put("minimum_gold_reserve_raw", pending.minimumGoldReserveRaw()); node.put("checkpoint_sha256_before_submit", pending.checkpointSha256BeforeSubmit());
        node.put("status", pending.status().wire());
        if (pending.ack().isPresent()) { node.set("ack", StrictJson.parse(pending.ack().orElseThrow().json().getBytes(StandardCharsets.UTF_8))); }
        else { node.putNull("ack"); } return node;
    }
    static ObjectEvidence evidence(JsonNode node) { object(node); return new ObjectEvidence(new String(json(node), StandardCharsets.UTF_8)); }
    static JsonNode object(JsonNode node) { StrictJson.require(node != null && node.isObject(), "JSON object projection required"); return node; }
    static BigInteger integer(JsonNode node, String field) { return integer(node.get(field)); }
    static BigInteger integer(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber(), "exact JSON integer required; no boolean, float or string"); return node.bigIntegerValue();
    }
    static String text(JsonNode node, String field) { return StrictJson.text(node.get(field)); }
    static boolean bool(JsonNode node, String field) {
        JsonNode value = node.get(field); StrictJson.require(value != null && value.isBoolean(), "JSON boolean required: " + field); return value.booleanValue();
    }
    static void requireBoolean(JsonNode node, String field, boolean expected) { StrictJson.require(bool(node, field) == expected, "boolean fact mismatch: " + field); }
    static List<BigInteger> integers(JsonNode node) {
        StrictJson.require(node != null && node.isArray(), "integer list required"); List<BigInteger> values = new ArrayList<>();
        for (JsonNode entry : node) { values.add(integer(entry)); } return List.copyOf(values);
    }
    private static PendingStatus status(String wire) {
        for (PendingStatus status : PendingStatus.values()) { if (status.wire().equals(wire)) { return status; } }
        throw new IllegalArgumentException("unknown faction gift pending status");
    }
    private static ResolvedOutcome outcome(String wire) {
        for (ResolvedOutcome outcome : ResolvedOutcome.values()) { if (outcome.wire().equals(wire)) { return outcome; } }
        throw new IllegalArgumentException("unknown resolved faction gift outcome");
    }
    /** Leaf-only JSON-domain serializer: opaque extension floats remain floats, never integer tokens. */
    static byte[] json(JsonNode node) {
        StringBuilder output = new StringBuilder(); append(node, output); byte[] raw = output.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(raw.length <= MAX_BYTES, "bounded faction gift JSON required"); return raw;
    }
    private static void append(JsonNode node, StringBuilder output) {
        if (node.isObject()) {
            output.append('{'); TreeSet<String> fields = new TreeSet<>(); node.fieldNames().forEachRemaining(fields::add); boolean first = true;
            for (String field : fields) {
                if (!first) { output.append(','); } first = false; output.append(new String(StrictJson.canonical(new com.fasterxml.jackson.databind.node.TextNode(field)), StandardCharsets.UTF_8));
                output.append(':'); append(node.get(field), output);
            } output.append('}');
        } else if (node.isArray()) {
            output.append('['); boolean first = true; for (JsonNode item : node) { if (!first) { output.append(','); } first = false; append(item, output); } output.append(']');
        } else if (node.isFloatingPointNumber()) {
            String number = node.decimalValue().toString(); output.append(number);
            if (number.indexOf('.') < 0 && number.indexOf('E') < 0 && number.indexOf('e') < 0) { output.append(".0"); }
        } else { output.append(new String(StrictJson.canonical(node), StandardCharsets.UTF_8)); }
    }
}
