package org.xar.ck3.control.wave3.governance.lifestylehistory;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistory.*;

/** Original result objects travel as exact JSON text, keeping unknown diagnostics/float spellings untouched. */
public final class LifestyleHistoryCodec {
    public static final String SCHEMA = "xar.java.lifestyle-history.v1";
    private static final ObjectMapper RECEIPT_JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private LifestyleHistoryCodec() { }

    public static Input decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "episode_run_id", "history"));
        StrictJson.require(SCHEMA.equals(text(root.get("schema"))), "lifestyle history schema mismatch");
        JsonNode history = root.get("history"); StrictJson.require(history.isArray() && history.size() <= 512, "bounded actual history projection required");
        List<HistoryRow> rows = new ArrayList<>();
        for (JsonNode rawRow : history) {
            ObjectNode row = StrictJson.object(rawRow, Set.of("command", "ok", "result_json"));
            rows.add(new HistoryRow(nullableText(row.get("command")), nullableBoolean(row.get("ok")),
                    row.get("result_json").isNull() ? null : receipt(text(row.get("result_json")))));
        }
        return new Input(nullableText(root.get("episode_run_id")), rows);
    }
    public static byte[] encode(Input input) {
        ObjectNode root = StrictJson.object().put("schema", SCHEMA).put("episode_run_id", input.episodeRunId());
        ArrayNode rows = root.putArray("history");
        for (HistoryRow row : input.history()) {
            ObjectNode item = rows.addObject().put("command", row.command()).put("ok", row.ok());
            if (row.result() == null) { item.putNull("result_json"); }
            else { item.put("result_json", new String(row.result().originalJson().bytes(), StandardCharsets.UTF_8)); }
        }
        return StrictJson.canonical(root);
    }
    public static byte[] evaluate(byte[] input) { return encodeSelection(LifestyleHistory.select(decode(input))); }
    public static byte[] encodeSelection(Selection selection) { return StrictJson.canonical(selectionNode(selection)); }
    public static ObjectNode selectionNode(Selection selection) {
        ObjectNode root = StrictJson.object().put("episode_run_id", selection.episodeRunId()).put("status", selection.status().name().toLowerCase(java.util.Locale.ROOT));
        ArrayNode pending = root.putArray("original_pending_json");
        selection.pendingActions().forEach(value -> pending.add(new String(value.originalJson().bytes(), StandardCharsets.UTF_8)));
        ArrayNode unverified = root.putArray("unverified_receipts_json");
        selection.unverifiedReceipts().forEach(value -> unverified.add(new String(value.originalJson().bytes(), StandardCharsets.UTF_8)));
        root.put("original_pending_action_json", originalPendingActionJson(selection));
        root.set("latest_applied_receipt", selection.latestApplied().isPresent() ? appliedNode(selection.latestApplied().orElseThrow()) : root.nullNode());
        root.put("replay_authorized", false).put("native_business_qualification", false); return root;
    }
    /** Null means clear; verified pending retains byte-exact original JSON; uncertainty uses the unique typed guard. */
    private static String originalPendingActionJson(Selection selection) {
        var pending = LifestyleHistoryConsumer.pendingGuard(selection);
        if (!pending.present()) { return null; }
        if (selection.status() == Status.VERIFY_ORIGINAL_RECEIPT) {
            return new String(selection.pendingActions().getFirst().originalJson().bytes(), StandardCharsets.UTF_8);
        }
        return new String(StrictJson.canonical(StrictJson.object().put("status", pending.value().status().value())), StandardCharsets.UTF_8);
    }
    /** Legacy latest-receipt field names are retained; post_public_revision is the original native stamp. */
    public static ObjectNode appliedNode(AppliedReceipt value) {
        return StrictJson.object().put("action_request_id", value.actionRequestId()).put("target_key", value.targetKey())
                .put("post_snapshot_id", value.postSnapshotId()).put("post_public_revision", value.postPublicRevision()).put("post_date_raw", value.postDateRaw())
                .put("episode_run_id", value.episodeRunId()).put("post_target_perk_owned", value.postTargetPerkOwned())
                .put("postcondition_verified", value.postconditionVerified()).put("kind", value.kind().wire())
                .put("post_has_current_focus", value.postHasCurrentFocus()).put("post_current_focus_key", value.postCurrentFocusKey());
    }
    private static ReceiptData receipt(String sourceJson) {
        StrictJson.require(!sourceJson.isEmpty(), "nonempty original result JSON required");
        byte[] raw = sourceJson.getBytes(StandardCharsets.UTF_8); StrictJson.require(raw.length <= 32_768, "bounded original result JSON required");
        JsonNode parsed;
        try { parsed = RECEIPT_JSON.readTree(raw); }
        catch (IOException error) { throw new ContractViolationException("invalid or duplicate original result JSON", error); }
        StrictJson.require(parsed != null, "original JSON result required"); validateValue(parsed, 0);
        if (!(parsed instanceof ObjectNode row)) { return null; } // Original nonmapping history results are ignored.
        ObjectNode source = null;
        if (row.hasNonNull("source_frame")) {
            StrictJson.require(row.get("source_frame") instanceof ObjectNode, "source_frame must be an object or null"); source = (ObjectNode) row.get("source_frame");
        }
        return new ReceiptData(optionalText(row, "status"), optionalText(row, "episode_run_id"), optionalText(row, "action_request_id"),
                optionalText(row, "target_key"), optionalText(row, "kind"), integer(row.get("pre_public_revision")),
                source == null ? null : integer(source.get("native_revision")), source == null ? null : integer(source.get("date_raw")),
                source == null ? null : integer(source.get("player_character_id")), optionalText(row, "post_snapshot_id"), integer(row.get("post_public_revision")),
                integer(row.get("post_date_raw")), nullableBoolean(row.get("post_target_perk_owned")), nullableBoolean(row.get("postcondition_verified")),
                nullableBoolean(row.get("post_has_current_focus")), optionalText(row, "post_current_focus_key"), new RetainedJson(raw));
    }
    private static void validateValue(JsonNode value, int depth) {
        StrictJson.require(depth <= 128, "bounded original result nesting required");
        if (value.isTextual()) { if (!value.textValue().isEmpty()) { StrictJson.text(value.textValue()); } }
        else if (value.isObject()) {
            value.fieldNames().forEachRemaining(key -> { if (!key.isEmpty()) { StrictJson.text(key); } });
            value.elements().forEachRemaining(child -> validateValue(child, depth + 1));
        } else if (value.isArray()) { value.forEach(child -> validateValue(child, depth + 1)); }
        else { StrictJson.require(value.isNull() || value.isBoolean() || value.isIntegralNumber() || value.isFloatingPointNumber(), "JSON value required"); }
    }
    private static String text(JsonNode node) {
        StrictJson.require(node != null && node.isTextual(), "actual JSON string required");
        String text = node.textValue(); if (!text.isEmpty()) { StrictJson.text(text); } return text;
    }
    private static String nullableText(JsonNode node) { return node == null || node.isNull() ? null : text(node); }
    private static String optionalText(ObjectNode row, String field) { return nullableText(row.get(field)); }
    private static BigInteger integer(JsonNode node) {
        if (node == null || node.isNull()) { return null; }
        StrictJson.require(node.isIntegralNumber(), "actual integer identity token required, no bool/float/string coercion"); return node.bigIntegerValue();
    }
    private static Boolean nullableBoolean(JsonNode node) {
        if (node == null || node.isNull()) { return null; }
        StrictJson.require(node.isBoolean(), "actual JSON boolean required"); return node.booleanValue();
    }
}
