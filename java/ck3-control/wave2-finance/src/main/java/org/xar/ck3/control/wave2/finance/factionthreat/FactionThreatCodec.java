package org.xar.ck3.control.wave2.finance.factionthreat;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.xar.ck3.control.wave2.finance.factionthreat.FactionThreatObserver.*;

/** Strict token checks for decision fields, declared projection of extensible SDK containers. */
public final class FactionThreatCodec {
    public static final int MAX_BYTES = 1_048_576;
    public static final int MAX_HISTORY = 256;
    public static final int MAX_ROWS = 256;
    private static final BigInteger UINT32_MAX = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    private static final BigInteger UINT64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final Set<String> ENVELOPE = Set.of("snapshot", "history", "candidate", "expected_revision");
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64)
                    .maxNumberLength(128).maxStringLength(65_536).build()).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);

    private FactionThreatCodec() { }

    public static Request decodeRequest(byte[] bytes) {
        JsonNode root = parse(bytes);
        object(root, "request");
        if (root.size() != ENVELOPE.size()) throw invalid("request fields");
        for (String field : ENVELOPE) if (!root.has(field)) throw invalid("missing " + field);
        JsonNode candidate = root.get("candidate");
        if (!candidate.isObject() || !textIs(candidate.get("status"), "selected")
                || !candidate.path("choice").isObject()) return new NoSelectedGift();
        JsonNode choice = candidate.get("choice");
        SelectedGift gift = new SelectedGift(positive(choice.get("source_faction_id"), UINT32_MAX, "source_faction_id"),
                positive(choice.get("recipient_character_id"), UINT32_MAX, "recipient_character_id"));
        JsonNode snapshot = root.get("snapshot");
        object(snapshot, "snapshot");
        JsonNode actor = snapshot.get("played_character");
        object(actor, "played_character");
        Frame frame = new Frame(positive(snapshot.get("native_revision"), UINT64_MAX, "native_revision"),
                signedDate(snapshot.get("date_raw")), positive(actor.get("character_id"), UINT32_MAX, "character_id"));
        BigInteger expected = positive(root.get("expected_revision"), UINT64_MAX, "expected_revision");
        JsonNode history = root.get("history");
        if (!history.isArray() || history.size() > MAX_HISTORY) throw invalid("history must be a bounded array");
        List<Alert> alerts = new ArrayList<>();
        for (JsonNode row : history) {
            object(row, "history row");
            if (textIs(row.get("command"), STEP) && truth(row.get("ok"), "history.ok") == Truth.TRUE
                    && row.path("result").isObject()) alerts.add(projectResult(row.get("result")));
        }
        return new SelectedGiftRequest(frame, gift, alerts, expected);
    }

    public static Alert decodeExistingObserverResult(byte[] bytes) { return projectResult(parse(bytes)); }

    public static byte[] encode(Response response) {
        ObjectNode root = JSON.createObjectNode();
        root.put("status", response instanceof Observed ? "observed" : "unavailable");
        root.put("dangerous_response_ready", false);
        root.put("exact_ultimatum_timing_ready", false);
        if (response instanceof Unavailable unavailable) {
            root.put("reason", unavailable.reason().wire());
            unavailable.observerError().ifPresent(error -> root.put("observer_error", error));
        } else {
            Observed observed = (Observed) response;
            root.put("observer_step", STEP);
            root.put("same_frame_history_reused", observed.origin() == HistoryOrigin.REUSED);
            root.put("source_faction_id", observed.gift().sourceFactionId());
            root.put("recipient_character_id", observed.gift().recipientCharacterId());
            root.put("snapshot_revision", observed.frame().nativeRevision());
            root.put("date_raw", observed.frame().dateRaw());
            root.put("player_character_id", observed.frame().playerCharacterId());
            root.put("dangerous_response_ready", observed.dangerousResponseReady());
            root.set("native_row", parse(observed.nativeRow().originalJson()));
            root.put("faction_departure_or_threat_resolution", "not_inferred");
        }
        return encodeTree(root);
    }

    private static Alert projectResult(JsonNode result) {
        JsonNode raw = result.isObject() ? result.get("player_faction_alerts") : null;
        if (raw == null || !raw.isObject()) return emptyAlert();
        Optional<Frame> frame = frame(raw);
        JsonNode readiness = raw.get("readiness");
        Readiness ready = readiness != null && readiness.isObject()
                ? new Readiness(truth(readiness.get("targeting_rows_ready"), "targeting_rows_ready"),
                truth(readiness.get("stock_dangerous_predicate_ready"), "stock_dangerous_predicate_ready"),
                truth(readiness.get("same_frame_ready"), "same_frame_ready"))
                : new Readiness(Truth.UNKNOWN, Truth.UNKNOWN, Truth.UNKNOWN);
        JsonNode rows = raw.get("targeting_factions");
        if (rows == null || !rows.isArray()) return new Alert(frame, textIs(raw.get("status"), "available"), ready, false, List.of());
        if (rows.size() > MAX_ROWS) throw invalid("targeting rows limit");
        List<NativeFactionRow> projected = new ArrayList<>();
        for (JsonNode row : rows) {
            if (!row.isObject()) continue; // Matches the original mapping-only candidate filter.
            Optional<BigInteger> faction = optionalPositive(row.get("faction_id"), UINT32_MAX, "faction_id");
            Optional<BigInteger> target = optionalPositive(row.get("target_character_id"), UINT32_MAX, "target_character_id");
            Optional<BigInteger> leader = optionalPositive(row.get("leader_character_id"), UINT32_MAX, "leader_character_id");
            List<BigInteger> members = new ArrayList<>();
            JsonNode memberNodes = row.get("character_member_ids");
            if (memberNodes != null) {
                if (!memberNodes.isArray() || memberNodes.size() > MAX_ROWS) throw invalid("character_member_ids must be an array");
                for (JsonNode member : memberNodes) members.add(positive(member, UINT32_MAX, "member identity"));
            }
            projected.add(new NativeFactionRow(faction, target, leader, members,
                    truth(row.get("dangerous_by_stock_rule"), "dangerous_by_stock_rule"),
                    truth(row.get("faction_at_war"), "faction_at_war"), encodeTree(row)));
        }
        return new Alert(frame, textIs(raw.get("status"), "available"), ready, true, projected);
    }

    private static Optional<Frame> frame(JsonNode raw) {
        Optional<BigInteger> revision = optionalPositive(raw.get("snapshot_revision"), UINT64_MAX, "snapshot_revision");
        Optional<BigInteger> player = optionalPositive(raw.get("player_character_id"), UINT32_MAX, "player_character_id");
        JsonNode date = raw.get("date_raw");
        if (revision.isEmpty() || player.isEmpty() || date == null || date.isNull()) return Optional.empty();
        return Optional.of(new Frame(revision.get(), signedDate(date), player.get()));
    }

    private static Alert emptyAlert() {
        return new Alert(Optional.empty(), false,
                new Readiness(Truth.UNKNOWN, Truth.UNKNOWN, Truth.UNKNOWN), false, List.of());
    }

    private static Truth truth(JsonNode node, String field) {
        if (node == null || node.isNull()) return Truth.UNKNOWN;
        if (!node.isBoolean()) throw invalid(field + " must be boolean or null");
        return node.booleanValue() ? Truth.TRUE : Truth.FALSE;
    }

    private static Optional<BigInteger> optionalPositive(JsonNode value, BigInteger maximum, String field) {
        return value == null || value.isNull() ? Optional.empty() : Optional.of(positive(value, maximum, field));
    }

    private static BigInteger positive(JsonNode value, BigInteger maximum, String field) {
        if (value == null || !value.isIntegralNumber()) throw invalid(field + " must be an integer token");
        BigInteger integer = value.bigIntegerValue();
        if (integer.signum() <= 0 || integer.compareTo(maximum) > 0) throw invalid(field + " outside domain");
        return integer;
    }

    private static int signedDate(JsonNode node) {
        if (node == null || !node.isIntegralNumber() || !node.canConvertToInt()) throw invalid("date_raw must be int32");
        return node.intValue();
    }

    private static boolean textIs(JsonNode node, String expected) {
        return node != null && node.isTextual() && expected.equals(node.textValue());
    }

    private static void object(JsonNode node, String field) {
        if (node == null || !node.isObject()) throw invalid(field + " must be an object");
    }

    private static JsonNode parse(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_BYTES) throw invalid("JSON byte limit");
        try {
            String utf8 = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode node = JSON.readTree(utf8);
            if (node == null) throw invalid("empty JSON");
            return node;
        } catch (IOException failure) { throw new IllegalArgumentException("invalid faction threat JSON", failure); }
    }

    private static byte[] encodeTree(JsonNode node) {
        try {
            byte[] result = JSON.writeValueAsBytes(preserveFloatDomain(node));
            if (result.length > MAX_BYTES) throw invalid("encoded JSON byte limit");
            return result;
        }
        catch (IOException failure) { throw new IllegalStateException("JSON encoding failed", failure); }
    }

    /** Preserve opaque decimal precision and floating token identity across downstream validation. */
    private static JsonNode preserveFloatDomain(JsonNode node) {
        if (node.isObject()) {
            ObjectNode copy = JSON.createObjectNode();
            node.properties().forEach(entry -> copy.set(entry.getKey(), preserveFloatDomain(entry.getValue())));
            return copy;
        }
        if (node.isArray()) {
            ArrayNode copy = JSON.createArrayNode();
            node.forEach(value -> copy.add(preserveFloatDomain(value)));
            return copy;
        }
        if (node.isFloatingPointNumber()) {
            var decimal = node.decimalValue();
            return DecimalNode.valueOf(decimal.scale() == 0 ? decimal.setScale(1) : decimal);
        }
        return node;
    }

    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}
