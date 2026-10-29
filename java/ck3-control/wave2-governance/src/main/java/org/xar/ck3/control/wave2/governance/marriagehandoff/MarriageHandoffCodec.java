package org.xar.ck3.control.wave2.governance.marriagehandoff;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import static org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffModel.*;

/** Strict entry plus declared projection of extensible historical ledger objects. */
public final class MarriageHandoffCodec {
    public static final int MAXIMUM_BYTES = 131_072;
    private static final Set<String> REQUEST_FIELDS = Set.of("schema", "state_directory_present", "handoff", "ledger");
    private static final Set<String> HANDOFF_FIELDS = Set.of("source_episode_run_id", "successor_episode_run_id", "predecessor_character_id", "successor_character_id");
    private static final Set<String> CHARACTER_FIELDS = Set.of("played_character_id", "heir_character_id", "candidate_character_id", "recipient_character_id", "predecessor_character_id", "successor_character_id");
    private static final Set<String> INTEGER_FIELDS = Set.of("schema_version", "pre_native_revision", "post_native_revision", "native_revision", "source_native_revision", "source_legality_query_sequence", "source_date_raw", "last_checked_native_revision", "source_bridge_pid", "last_checked_bridge_pid", "post_bridge_pid", "last_outbound_pending_id", "last_outbound_pending_age_days", "last_outbound_pending_ai_reply_cutoff_days", "last_checked_date_raw", "last_consumed_checkpoint_native_revision", "last_consumed_checkpoint_date_raw");
    private static final Set<String> BOOLEAN_FIELDS = Set.of("material_result", "fulfill_existing_betrothal", "cold_absent_relation_unresolved", "preproposal_realm_alliance_attempt_if_accepted", "preproposal_played_has_recipient_alliance", "cold_recovery", "cold_recovery_verified", "matrilineal_option_selected", "ck3_command_submitted");
    private static final Set<String> TEXT_FIELDS = Set.of("status", "submission_state", "source_bridge_creation_date", "last_checked_bridge_creation_date", "post_bridge_creation_date", "episode_run_id", "source_episode_run_id", "successor_episode_run_id");
    private static final Set<String> DECLARED_OBJECTS = Set.of("pending", "resolved", "source_pending", "selected_value_projection", "prior_betrothal_relationship", "alliance_result");
    private static final JsonMapper MAPPER = JsonMapper.builder(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS, DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private MarriageHandoffCodec() { }

    public static Request decodeRequest(byte[] raw) {
        ObjectNode root = StrictJson.object(parse(raw), REQUEST_FIELDS);
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(root.get("schema"))), "handoff request schema differs");
        boolean present = bool(root.get("state_directory_present"));
        Handoff handoff = handoff(StrictJson.object(root.get("handoff"), HANDOFF_FIELDS));
        JsonNode ledger = root.get("ledger");
        StrictJson.require(present ? ledger.isObject() : ledger.isNull(), "state directory and ledger presence differ");
        return new Request(present, handoff, present ? ledger(ledger) : null);
    }

    public static Ledger decodeLedger(byte[] raw) { return ledger(parse(raw)); }
    public static byte[] encodeLedger(Ledger ledger) { return bytes(ledger.source().json()); }

    public static byte[] encodeResult(Reduction reduction) {
        ObjectNode root = MAPPER.createObjectNode();
        if (reduction instanceof Archived archived) {
            root.set("ledger", node(archived.after().source()));
            root.set("receipt", receipt(archived.receipt()));
            root.put("write_required", true);
        } else if (reduction instanceof Unchanged unchanged) {
            if (unchanged.ledger() == null) { root.putNull("ledger"); }
            else { root.set("ledger", node(unchanged.ledger().source())); }
            root.putNull("receipt"); root.put("write_required", false);
        }
        return bytes(root.toString());
    }

    public static byte[] encodeReceipt(Receipt value) { return bytes(receipt(value).toString()); }

    static Ledger archive(Ledger before, Handoff handoff, boolean pending, boolean resolved) {
        ObjectNode after = node(before.source());
        ObjectNode history = MAPPER.createObjectNode();
        history.put("source", "matched_ordinary_successor_episode");
        handoffFields(history, handoff);
        history.set("pending", pending ? node(before.pending().source()) : MAPPER.getNodeFactory().nullNode());
        history.set("resolved", resolved ? node(before.resolved().source()) : MAPPER.getNodeFactory().nullNode());
        if (pending) { after.putNull("pending"); }
        if (resolved) { after.putNull("resolved"); }
        ArrayNode entries = before.historyPresent() ? (ArrayNode) after.get("episode_history") : MAPPER.createArrayNode();
        entries.add(history); after.set("episode_history", entries);
        return ledger(after);
    }

    private static Ledger ledger(JsonNode value) {
        ObjectNode root = object(value);
        validateJsonDomain(root);
        StrictJson.require(LEDGER_SCHEMA.equals(textRequired(root, "schema")), "family marriage ledger schema differs");
        StrictJson.require(root.has("pending") && root.has("resolved"), "pending and resolved are required even when null");
        FamilyRecord pending = record(root.get("pending"));
        FamilyRecord resolved = record(root.get("resolved"));
        if (root.has("episode_history")) {
            JsonNode history = root.get("episode_history");
            StrictJson.require(history.isArray(), "episode_history must be an array, not null");
            for (JsonNode entry : history) { object(entry); validateDeclared(entry); }
        }
        return new Ledger(preserve(root), pending, resolved, root.has("episode_history"));
    }

    private static FamilyRecord record(JsonNode value) {
        if (value.isNull()) { return null; }
        ObjectNode source = object(value); validateDeclared(source);
        return new FamilyRecord(preserve(source), episodeField(source));
    }

    /** Unknown SDK fields survive, while declared identity/type fields cannot exploit JSON coercion. */
    private static void validateDeclared(JsonNode value) {
        if (!value.isObject()) { return; }
        Iterator<Map.Entry<String, JsonNode>> fields = value.properties().iterator();
        while (fields.hasNext()) {
            Map.Entry<String, JsonNode> field = fields.next(); String key = field.getKey(); JsonNode item = field.getValue();
            if (!key.isEmpty()) { StrictJson.text(key); }
            if (!item.isNull()) {
                if (CHARACTER_FIELDS.contains(key)) {
                    if (item.isIntegralNumber() && item.bigIntegerValue().signum() > 0) { character(item); }
                    else { NativeCharacterId.fromJson(item); }
                }
                else if (INTEGER_FIELDS.contains(key)) { StrictJson.require(item.isIntegralNumber(), "actual integer required for " + key); }
                else if (BOOLEAN_FIELDS.contains(key)) { bool(item); }
                else if (TEXT_FIELDS.contains(key)) { StrictJson.text(item); }
            }
            if (DECLARED_OBJECTS.contains(key) && item.isObject()) { validateDeclared(item); }
            else if ("episode_history".equals(key) && item.isArray()) { for (JsonNode entry : item) { validateDeclared(entry); } }
        }
    }

    private static void validateJsonDomain(JsonNode value) {
        if (value.isTextual() && !value.textValue().isEmpty()) { StrictJson.text(value); }
        if (value.isArray()) { for (JsonNode item : value) { validateJsonDomain(item); } }
        if (value.isObject()) {
            Iterator<Map.Entry<String, JsonNode>> fields = value.properties().iterator();
            while (fields.hasNext()) {
                Map.Entry<String, JsonNode> field = fields.next();
                if (!field.getKey().isEmpty()) { StrictJson.text(field.getKey()); }
                validateJsonDomain(field.getValue());
            }
        }
    }

    private static Handoff handoff(ObjectNode row) {
        return new Handoff(textRequired(row, "source_episode_run_id"), textRequired(row, "successor_episode_run_id"),
                character(row.get("predecessor_character_id")), character(row.get("successor_character_id")));
    }
    private static CharacterId character(JsonNode value) { return new CharacterId(StrictJson.integer(value, BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact()); }
    private static ObjectNode receipt(Receipt value) {
        ObjectNode result = MAPPER.createObjectNode(); result.put("status", "predecessor_records_archived"); handoffFields(result, value.handoff());
        result.put("pending_archived", value.pendingArchived()); result.put("resolved_archived", value.resolvedArchived()); result.put("ck3_command_submitted", false); return result;
    }
    private static void handoffFields(ObjectNode row, Handoff value) {
        row.put("source_episode_run_id", value.sourceEpisodeRunId()); row.put("successor_episode_run_id", value.successorEpisodeRunId());
        row.put("predecessor_character_id", value.predecessorCharacterId().value()); row.put("successor_character_id", value.successorCharacterId().value());
    }
    private static JsonNode parse(byte[] raw) {
        StrictJson.parse(raw, MAXIMUM_BYTES);
        try { return MAPPER.readTree(raw); }
        catch (IOException error) { throw new IllegalArgumentException("strict JSON parse failed", error); }
    }
    private static ObjectNode object(JsonNode value) { StrictJson.require(value != null && value.isObject(), "JSON object required"); return (ObjectNode) value; }
    private static boolean bool(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "actual boolean token required"); return value.booleanValue(); }
    private static String textRequired(ObjectNode row, String key) { return StrictJson.text(row.get(key)); }
    private static PreservedObject preserve(ObjectNode value) { return new PreservedObject(value.toString()); }
    static void requireRecordProjection(PreservedObject source, EpisodeField episode) {
        StrictJson.require(episodeField(node(source)).equals(episode), "record episode projection differs from preserved source");
    }
    static void requireLedgerProjection(PreservedObject source, FamilyRecord pending, FamilyRecord resolved, boolean historyPresent) {
        ObjectNode row = node(source);
        StrictJson.require(LEDGER_SCHEMA.equals(textRequired(row, "schema")) && row.has("pending") && row.has("resolved"), "preserved ledger schema or fields differ");
        StrictJson.require(sameRecord(row.get("pending"), pending) && sameRecord(row.get("resolved"), resolved), "ledger projection differs from preserved records");
        StrictJson.require(row.has("episode_history") == historyPresent, "history presence projection differs");
    }
    private static boolean sameRecord(JsonNode actual, FamilyRecord expected) { return expected == null ? actual.isNull() : actual.equals(node(expected.source())); }
    private static EpisodeField episodeField(ObjectNode source) {
        JsonNode episode = source.get("episode_run_id");
        return episode == null ? new EpisodeField(Presence.MISSING, null) : episode.isNull() ? new EpisodeField(Presence.NULL, null) : new EpisodeField(Presence.VALUE, StrictJson.text(episode));
    }
    static boolean sameJson(String first, String second) { return parse(bytes(first)).equals(parse(bytes(second))); }
    static int jsonHash(String value) { return parse(bytes(value)).hashCode(); }
    private static ObjectNode node(PreservedObject value) { return object(parse(bytes(value.json()))); }
    private static byte[] bytes(String value) {
        byte[] result = value.getBytes(StandardCharsets.UTF_8);
        StrictJson.require(result.length <= MAXIMUM_BYTES, "family ledger exceeds explicit byte budget"); return result;
    }
}
