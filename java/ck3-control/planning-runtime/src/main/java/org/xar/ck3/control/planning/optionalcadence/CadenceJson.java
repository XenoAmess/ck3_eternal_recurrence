package org.xar.ck3.control.planning.optionalcadence;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.StrictJson;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

import static org.xar.ck3.control.planning.optionalcadence.CadenceModels.*;

/** Explicit runtime validation of the persisted producer contract; no integer coercion. */
public final class CadenceJson {
    private static final int MAX_BYTES = 65_536;
    private static final ObjectMapper MAPPER = JsonMapper.builder().build();
    private static final Set<String> ROOT_FIELDS = Set.of("schema", "episode_run_id", "domains");
    private static final Set<String> ROW_REQUIRED = Set.of("consecutive_no_action", "next_due_date_raw",
            "last_check_frame", "last_actual_action_frame");
    private static final Set<String> ROW_ALLOWED = Set.of("consecutive_no_action", "next_due_date_raw",
            "last_check_frame", "last_actual_action_frame", "native_catalogue", "technical_defer");
    private static final Set<String> TECHNICAL_FIELDS = Set.of("status", "frame", "evidence_path",
            "business_submission", "no_action_counter_incremented");

    private CadenceJson() { }

    public static State readState(byte[] bytes, String expectedEpisode) {
        nonempty(expectedEpisode, "expectedEpisode");
        JsonNode root = parse(bytes);
        object(root, "state");
        if (!SCHEMA.equals(text(required(root, "schema"), "schema"))) {
            throw invalid("unknown cadence schema");
        }
        String episode = text(required(root, "episode_run_id"), "episode_run_id");
        // The legacy producer resets another episode before inspecting its domain rows.
        if (!expectedEpisode.equals(episode)) { return State.empty(expectedEpisode); }
        exactFields(root, ROOT_FIELDS, ROOT_FIELDS, "state");
        JsonNode domains = required(root, "domains");
        Set<String> names = new HashSet<>();
        for (Domain domain : Domain.values()) { names.add(domain.wire()); }
        exactFields(domains, names, names, "domains");
        EnumMap<Domain, Row> rows = new EnumMap<>(Domain.class);
        for (Domain domain : Domain.values()) { rows.put(domain, readRow(domains.get(domain.wire()))); }
        return new State(episode, rows);
    }

    /** A full semantic snapshot is extensible. Only the four cadence-owned projection fields are read. */
    public static Optional<Frame> readFrame(byte[] snapshot) {
        JsonNode root = parse(snapshot);
        if (!root.isObject() || !root.path("paused").isBoolean() || !root.path("paused").booleanValue()
                || !root.path("episode_run_id").isTextual() || root.path("episode_run_id").textValue().isEmpty()
                || !root.path("date_raw").isIntegralNumber() || root.path("date_raw").bigIntegerValue().signum() < 0
                || !root.path("native_revision").isIntegralNumber()
                || root.path("native_revision").bigIntegerValue().signum() < 0) {
            return Optional.empty();
        }
        return Optional.of(new Frame(root.get("episode_run_id").textValue(),
                root.get("date_raw").bigIntegerValue(), root.get("native_revision").bigIntegerValue()));
    }

    public static byte[] writeState(State state) {
        ObjectNode root = MAPPER.createObjectNode();
        root.put("schema", SCHEMA);
        root.put("episode_run_id", state.episodeRunId());
        ObjectNode domains = root.putObject("domains");
        for (Domain domain : Domain.values()) { domains.set(domain.wire(), rowNode(state.row(domain))); }
        return StrictJson.canonical(root, MAX_BYTES);
    }

    public static byte[] writeDeferred(Optional<Deferred> result) {
        if (result.isEmpty()) { return "null".getBytes(StandardCharsets.UTF_8); }
        Deferred deferred = result.orElseThrow();
        ObjectNode root = MAPPER.createObjectNode();
        root.put("status", deferred.status().wire());
        root.put("consecutive_no_action", deferred.consecutiveNoAction());
        root.put("next_due_date_raw", deferred.nextDueDateRaw());
        deferred.technicalDefer().ifPresent(value -> root.set("technical_defer", technicalNode(value)));
        root.put("remaining_game_days", deferred.remainingGameDays());
        return write(root);
    }

    private static Row readRow(JsonNode node) {
        exactFields(node, ROW_REQUIRED, ROW_ALLOWED, "domain row");
        BigInteger count = integer(required(node, "consecutive_no_action"), "consecutive_no_action");
        if (count.signum() < 0 || count.compareTo(BigInteger.TWO) > 0) {
            throw invalid("consecutive_no_action must be 0..2");
        }
        Optional<BigInteger> due = nullableInteger(required(node, "next_due_date_raw"), "next_due_date_raw");
        Optional<Marker> check = nullableMarker(required(node, "last_check_frame"), "last_check_frame");
        Optional<Marker> action = nullableMarker(required(node, "last_actual_action_frame"), "last_actual_action_frame");
        Optional<String> catalogue = node.has("native_catalogue")
                ? Optional.of(text(node.get("native_catalogue"), "native_catalogue")) : Optional.empty();
        Optional<TechnicalDefer> technical = node.has("technical_defer")
                ? Optional.of(readTechnical(node.get("technical_defer"))) : Optional.empty();
        return new Row(count.intValueExact(), due, check, action, catalogue, technical);
    }

    private static TechnicalDefer readTechnical(JsonNode node) {
        exactFields(node, TECHNICAL_FIELDS, TECHNICAL_FIELDS, "technical_defer");
        if (!"read_unavailable".equals(text(node.get("status"), "technical_defer.status"))) {
            throw invalid("unknown technical_defer status");
        }
        exactFalse(node.get("business_submission"), "business_submission");
        exactFalse(node.get("no_action_counter_incremented"), "no_action_counter_incremented");
        return new TechnicalDefer(marker(node.get("frame"), "technical_defer.frame"),
                text(node.get("evidence_path"), "evidence_path"));
    }

    private static ObjectNode rowNode(Row row) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put("consecutive_no_action", row.consecutiveNoAction());
        if (row.nextDueDateRaw().isPresent()) { node.put("next_due_date_raw", row.nextDueDateRaw().orElseThrow()); }
        else { node.putNull("next_due_date_raw"); }
        putMarker(node, "last_check_frame", row.lastCheckFrame());
        putMarker(node, "last_actual_action_frame", row.lastActualActionFrame());
        row.nativeCatalogue().ifPresent(value -> node.put("native_catalogue", value));
        row.technicalDefer().ifPresent(value -> node.set("technical_defer", technicalNode(value)));
        return node;
    }

    private static ObjectNode technicalNode(TechnicalDefer technical) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put("status", "read_unavailable");
        node.set("frame", markerNode(technical.frame()));
        node.put("evidence_path", technical.evidencePath());
        node.put("business_submission", false);
        node.put("no_action_counter_incremented", false);
        return node;
    }

    private static void putMarker(ObjectNode node, String name, Optional<Marker> marker) {
        if (marker.isPresent()) { node.set(name, markerNode(marker.orElseThrow())); }
        else { node.putNull(name); }
    }
    private static ArrayNode markerNode(Marker marker) {
        return MAPPER.createArrayNode().add(marker.dateRaw()).add(marker.nativeRevision());
    }
    private static Optional<Marker> nullableMarker(JsonNode node, String name) {
        return node.isNull() ? Optional.empty() : Optional.of(marker(node, name));
    }
    private static Marker marker(JsonNode node, String name) {
        if (node == null || !node.isArray() || node.size() != 2) { throw invalid(name + " must be a pair"); }
        return new Marker(integer(node.get(0), name + ".date_raw"), integer(node.get(1), name + ".native_revision"));
    }
    private static Optional<BigInteger> nullableInteger(JsonNode node, String name) {
        return node.isNull() ? Optional.empty() : Optional.of(integer(node, name));
    }
    private static BigInteger integer(JsonNode node, String name) {
        if (node == null || !node.isIntegralNumber()) { throw invalid(name + " must be an integer token"); }
        return node.bigIntegerValue();
    }
    private static String text(JsonNode node, String name) {
        if (node == null || !node.isTextual() || node.textValue().isEmpty()) { throw invalid(name + " must be nonempty text"); }
        nonempty(node.textValue(), name);
        return node.textValue();
    }
    private static void exactFalse(JsonNode node, String name) {
        if (node == null || !node.isBoolean() || node.booleanValue()) { throw invalid(name + " must be false"); }
    }
    private static JsonNode required(JsonNode node, String name) {
        if (!node.has(name)) { throw invalid("missing " + name); }
        return node.get(name);
    }
    private static void object(JsonNode node, String name) {
        if (node == null || !node.isObject()) { throw invalid(name + " must be an object"); }
    }
    private static void exactFields(JsonNode node, Set<String> required, Set<String> allowed, String name) {
        object(node, name);
        Set<String> seen = new HashSet<>();
        node.fieldNames().forEachRemaining(seen::add);
        if (!seen.containsAll(required) || !allowed.containsAll(seen)) { throw invalid(name + " fields differ"); }
    }
    private static JsonNode parse(byte[] bytes) {
        return StrictJson.parse(bytes, MAX_BYTES);
    }
    private static byte[] write(JsonNode node) {
        try {
            byte[] bytes = MAPPER.writeValueAsBytes(node);
            if (bytes.length > MAX_BYTES) { throw invalid("cadence JSON output exceeds 65536 bytes"); }
            return bytes;
        }
        catch (JsonProcessingException error) { throw new IllegalArgumentException("cannot encode cadence JSON", error); }
    }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}
