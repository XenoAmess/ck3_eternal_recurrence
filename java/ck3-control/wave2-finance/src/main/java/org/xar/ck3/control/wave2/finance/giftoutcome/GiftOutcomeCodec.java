package org.xar.ck3.control.wave2.finance.giftoutcome;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeModel.*;

/** Strict tokens at declared fields; existing extensible SDK objects remain evidence, not exact-key DTOs. */
public final class GiftOutcomeCodec {
    public static final int MAX_BYTES = 1_048_576;
    private static final ObjectMapper WRITER = new ObjectMapper();
    private GiftOutcomeCodec() { }

    public static Request request(byte[] json) {
        ObjectNode root = StrictJson.object(StrictJson.parse(json, MAX_BYTES), Set.of("request_id", "expected_revision"));
        return new Request(StrictJson.text(root.get("request_id")), requiredInteger(root.get("expected_revision")));
    }
    public static Snapshot snapshot(byte[] json) { return snapshot(StrictJson.parse(json, MAX_BYTES)); }
    private static Snapshot snapshot(JsonNode input) {
        ObjectNode root = requireObject(input); ObjectNode actor = projectionObject(root.get("played_character"));
        return new Snapshot(text(root, "snapshot_id"), integer(root, "revision"), integer(root, "native_revision"),
                integer(root, "date_raw"), text(root, "episode_run_id"), truth(root, "paused"), truth(root, "map_ready"),
                integer(actor, "character_id"), truth(actor, "alive"), evidence(orNull(root.get("active_event"))),
                evidence(orNull(root.get("pending_character_interaction"))));
    }
    public static Optional<HistoryEntry> historyEntry(byte[] json) {
        return historyEntry(StrictJson.parse(json, MAX_BYTES));
    }
    private static Optional<HistoryEntry> historyEntry(JsonNode input) {
        ObjectNode row = requireObject(input);
        String command = text(row, "command").orElse("");
        Truth ok = truth(row, "ok");
        if (ok != Truth.TRUE) return Optional.empty();
        ObjectNode result = projectionObject(row.get("result"));
        String selected = command;
        if (command.equals("auto-turn")) {
            ObjectNode turn = projectionObject(result.get("auto_turn"));
            selected = text(turn, "selected_step").orElse(""); result = projectionObject(turn.get("result"));
        }
        if (!selected.equals(SUBMIT_STEP) && !selected.equals(RECEIPT_STEP) && !command.equals(ALERT_STEP)) return Optional.empty();
        Optional<PendingHistory> pending = Optional.empty(); Optional<ReceiptHistory> receipt = Optional.empty();
        if (selected.equals(SUBMIT_STEP)) {
            JsonNode raw = projectionObject(result.get("pending_ledger")).get("pending");
            if (raw != null && raw.isObject() && !raw.isEmpty()) pending = Optional.of(pending((ObjectNode) raw));
        }
        if (selected.equals(RECEIPT_STEP)) {
            JsonNode raw = result.get("receipt");
            if (raw != null && raw.isObject() && !raw.isEmpty()) receipt = Optional.of(receipt((ObjectNode) raw));
        }
        Optional<Alert> alert = command.equals(ALERT_STEP) ? Optional.of(alert(result.get("player_faction_alerts"))) : Optional.empty();
        return Optional.of(new HistoryEntry(selected, ok, pending, receipt, alert));
    }
    public static List<HistoryEntry> history(byte[] json) {
        JsonNode node = StrictJson.parse(json, MAX_BYTES);
        StrictJson.require(node.isArray(), "history array required within declared packet byte budget");
        List<HistoryEntry> result = new ArrayList<>();
        for (JsonNode row : node) historyEntry(row).ifPresent(result::add);
        return List.copyOf(result);
    }
    private static PendingHistory pending(ObjectNode root) {
        return new PendingHistory(text(root, "request_id"), text(root, "episode_run_id"), integer(root, "pre_player_character_id"),
                integer(root, "source_faction_id"), integer(root, "recipient_character_id"), integer(root, "pre_date_raw"),
                integer(root, "gold_cost_raw"), integer(root, "opinion_delta"), integer(root, "pre_recipient_opinion_of_player"),
                integer(root, "pre_source_faction_power_raw"), integer(root, "pre_source_faction_discontent_raw"));
    }
    private static ReceiptHistory receipt(ObjectNode root) {
        return new ReceiptHistory(text(root, "request_id"), integer(root, "schema_version"), text(root, "status"),
                truth(root, "postcondition_verified"), truth(root, "mitigation_applied"), integer(root, "player_character_id"),
                integer(root, "source_faction_id"), integer(root, "recipient_character_id"), integer(root, "post_observed_date_raw"), evidence(root));
    }
    public static PairPacket pairResult(byte[] json) {
        ObjectNode root = requireObject(StrictJson.parse(json, MAX_BYTES)); ObjectNode nativeResult = projectionObject(root.get("native"));
        ObjectNode raw = projectionObject(nativeResult.get("observation"));
        PairObservation observation = new PairObservation(truth(raw, "available"), truth(raw, "paused"), integer(raw, "snapshot_revision"),
                integer(raw, "native_snapshot_revision"), integer(raw, "observed_date_raw"), integer(raw, "player_character_id"),
                truth(raw, "source_faction_requery_complete"), integer(raw, "queried_source_faction_id"), truth(raw, "source_faction_present"),
                truth(raw, "source_faction_metrics_available"), integer(raw, "source_faction_leader_character_id"),
                integerList(raw.get("source_faction_member_character_ids")), truth(raw, "recipient_identity_resolved"),
                integer(raw, "recipient_character_id"), truth(raw, "recipient_opinion_query_complete"), integer(raw, "recipient_opinion_of_player"),
                truth(raw, "gift_opinion_present"), evidence(raw));
        return new PairPacket(text(root, "step"), truth(root, "accepted"), text(root, "status"), integer(nativeResult, "failure_flags"), observation);
    }
    public static Alert alertResult(byte[] json) {
        return alert(projectionObject(StrictJson.parse(json, MAX_BYTES)).get("player_faction_alerts"));
    }
    private static Alert alert(JsonNode input) {
        ObjectNode root = projectionObject(input); ObjectNode readiness = projectionObject(root.get("readiness"));
        Optional<List<AlertRow>> rows = Optional.empty(); JsonNode rawRows = root.get("targeting_factions");
        if (rawRows != null && rawRows.isArray()) {
            List<AlertRow> projected = new ArrayList<>();
            for (JsonNode row : rawRows) {
                if (row.isObject()) projected.add(new AlertRow(integer((ObjectNode) row, "faction_id"), evidence(row)));
            }
            rows = Optional.of(List.copyOf(projected));
        }
        return new Alert(text(root, "status"), integer(root, "snapshot_revision"), integer(root, "date_raw"), integer(root, "player_character_id"),
                truth(readiness, "same_frame_ready"), truth(readiness, "targeting_rows_ready"), truth(readiness, "stock_dangerous_predicate_ready"), rows);
    }
    public static byte[] pairRequest(PairRequest request) {
        ObjectNode root = StrictJson.object(); root.put("step", PAIR_STEP);
        root.put("expected_revision", request.expectedRevision()); root.put("expected_date_raw", request.expectedDateRaw());
        root.put("expected_player_character_id", request.expectedPlayerId()); root.put("source_faction_id", request.sourceFactionId());
        root.put("recipient_character_id", request.recipientId()); return encode(root);
    }
    public static byte[] outcome(Outcome outcome) {
        ObjectNode root = StrictJson.object(); root.put("schema", SCHEMA); root.put("request_id", outcome.request().requestId());
        root.put("status", outcome instanceof Observed ? "observed" : "unavailable"); root.put("attributed_to_gift", false);
        put(root, "observed_date_raw", outcome.frame().dateRaw()); put(root, "snapshot_revision", outcome.frame().nativeRevision());
        putText(root, "episode_run_id", outcome.frame().episodeRunId());
        outcome.original().ifPresent(original -> root.set("original", original(original)));
        if (outcome instanceof Unavailable unavailable) {
            root.put("reason", unavailable.reason().wire()); unavailable.observerError().ifPresent(value -> root.put("observer_error", value));
        } else {
            Observed observed = (Observed) outcome; root.put("faction_outcome", observed.factionOutcome().wire());
            root.set("current_observation", decodeEvidence(observed.currentObservation().original()));
            root.set("current_alert", currentAlert(observed.currentAlert())); root.put("followup_date_advanced", observed.followupDateAdvanced());
            root.put("gift_submit_performed", observed.giftSubmitPerformed()); root.put("pending_resolution_performed", observed.pendingResolutionPerformed());
        }
        return encode(root);
    }
    private static ObjectNode original(OriginalGift gift) {
        ObjectNode root = StrictJson.object(); root.put("request_id", gift.requestId()); putText(root, "episode_run_id", gift.episodeRunId());
        root.put("player_character_id", gift.actorId()); root.put("source_faction_id", gift.sourceFactionId()); root.put("recipient_character_id", gift.recipientId());
        put(root, "action_date_raw", gift.actionDateRaw()); root.put("material_date_raw", gift.materialDateRaw()); put(root, "gold_cost_raw", gift.goldCostRaw());
        put(root, "opinion_delta", gift.opinionDelta()); put(root, "pre_recipient_opinion_of_player", gift.preRecipientOpinion());
        put(root, "pre_source_faction_power_raw", gift.preFactionPower()); put(root, "pre_source_faction_discontent_raw", gift.preFactionDiscontent());
        root.set("receipt", decodeEvidence(gift.receipt())); return root;
    }
    private static ObjectNode currentAlert(CurrentAlert alert) {
        ObjectNode root = StrictJson.object();
        if (alert instanceof AlertObserved observed) {
            root.put("status", "observed"); root.set("row", decodeEvidence(observed.row().original()));
        } else if (alert instanceof AlertAbsent) { root.put("status", "not_in_current_targeting_vector"); root.putNull("row");
        } else { root.put("status", "unavailable"); root.put("reason", ((AlertUnavailable) alert).reason()); root.putNull("row"); }
        return root;
    }
    private static void put(ObjectNode root, String field, Optional<BigInteger> value) {
        if (value.isPresent()) root.put(field, value.orElseThrow()); else root.putNull(field);
    }
    private static void putText(ObjectNode root, String field, Optional<String> value) {
        if (value.isPresent()) root.put(field, value.orElseThrow()); else root.putNull(field);
    }
    private static Optional<String> text(ObjectNode object, String field) {
        JsonNode value = object.get(field); if (value == null || value.isNull()) return Optional.empty();
        StrictJson.require(value.isTextual(), field + " requires string token");
        if (!value.textValue().isEmpty()) StrictJson.text(value.textValue());
        return Optional.of(value.textValue());
    }
    private static Optional<BigInteger> integer(ObjectNode object, String field) {
        JsonNode value = object.get(field); return value == null || value.isNull() ? Optional.empty() : Optional.of(requiredInteger(value));
    }
    private static BigInteger requiredInteger(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "integer token required; bool/float/string rejected");
        return value.bigIntegerValue();
    }
    private static Truth truth(ObjectNode object, String field) {
        JsonNode value = object.get(field); if (value == null || value.isNull()) return Truth.UNKNOWN;
        StrictJson.require(value.isBoolean(), field + " requires boolean token"); return value.booleanValue() ? Truth.TRUE : Truth.FALSE;
    }
    private static Optional<List<BigInteger>> integerList(JsonNode raw) {
        if (raw == null || !raw.isArray()) return Optional.empty();
        List<BigInteger> result = new ArrayList<>();
        for (JsonNode value : raw) result.add(requiredInteger(value)); return Optional.of(List.copyOf(result));
    }
    private static ObjectNode requireObject(JsonNode node) {
        StrictJson.require(node != null && node.isObject(), "JSON object required"); return (ObjectNode) node;
    }
    /** The old _object helper treats nonobjects as absent. This is not an authority-bearing DTO. */
    private static ObjectNode projectionObject(JsonNode node) { return node != null && node.isObject() ? (ObjectNode) node : StrictJson.object(); }
    private static JsonNode orNull(JsonNode node) { return node == null ? NullNode.instance : node; }
    private static WireValue evidence(JsonNode node) { return new WireValue(encode(node)); }
    private static JsonNode decodeEvidence(WireValue value) { return StrictJson.parse(value.json(), MAX_BYTES); }
    private static byte[] encode(JsonNode node) {
        try {
            byte[] raw = WRITER.writeValueAsBytes(normalized(node)); StrictJson.require(raw.length <= MAX_BYTES, "gift outcome byte limit"); return raw;
        } catch (JsonProcessingException error) { throw new ContractViolationException("gift outcome JSON encoding failed", error); }
    }
    /** Stable dictionary equality for _binding; preserve floating-token domain in unrelated SDK extensions. */
    private static JsonNode normalized(JsonNode node) {
        if (node.isObject()) {
            ObjectNode result = StrictJson.object(); TreeSet<String> names = new TreeSet<>(); node.fieldNames().forEachRemaining(names::add);
            for (String name : names) result.set(name, normalized(node.get(name))); return result;
        }
        if (node.isArray()) {
            ArrayNode result = WRITER.createArrayNode(); for (JsonNode value : node) result.add(normalized(value)); return result;
        }
        if (node.isFloatingPointNumber() && node.decimalValue().scale() == 0) return new DecimalNode(node.decimalValue().setScale(1));
        return node;
    }
}
