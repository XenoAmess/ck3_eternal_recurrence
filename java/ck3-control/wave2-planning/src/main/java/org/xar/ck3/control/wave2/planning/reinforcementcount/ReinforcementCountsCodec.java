package org.xar.ck3.control.wave2.planning.reinforcementcount;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.StrictJson;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.xar.ck3.control.wave2.planning.reinforcementcount.ReinforcementCounts.*;

/** Exact request envelopes with bounded projections of existing army/cache containers. */
public final class ReinforcementCountsCodec {
    public static final String COUNT_SCHEMA = "xar.reinforcement-count.request.v1";
    public static final String STAGING_SCHEMA = "xar.reinforcement-staging.request.v1";
    private ReinforcementCountsCodec() { }

    public static CountInput decodeCount(byte[] raw) {
        ObjectNode request = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "rows", "snapshot", "role", "war_id"));
        StrictJson.require(COUNT_SCHEMA.equals(StrictJson.text(request.get("schema"))), "unknown count request schema");
        JsonNode snapshot = request.get("snapshot");
        StrictJson.require(snapshot.isObject(), "snapshot must be an object");
        JsonNode rows = request.get("rows");
        StrictJson.require(rows.isArray(), "explicit count row collection required");
        List<Army> armies = new ArrayList<>();
        for (JsonNode row : rows) {
            StrictJson.require(row.isObject(), "count row must be an object");
            armies.add(new Army(integer(row.get("army_id")), integer(row.get("soldiers"))));
        }
        String status = snapshot.path("army_strengths_status").textValue();
        CacheStatus cache = "available".equals(status) ? CacheStatus.AVAILABLE : "partial".equals(status) ? CacheStatus.PARTIAL : CacheStatus.OTHER;
        List<Strength> strengths = new ArrayList<>();
        JsonNode sourceRows = snapshot.path("army_strengths");
        if (sourceRows.isArray()) {
            for (JsonNode row : sourceRows) {
                if (!row.isObject()) { continue; }
                JsonNode role = row.get("scope_role");
                strengths.add(new Strength(integer(row.get("army_id")), role != null && role.isTextual() ? role.textValue() : "",
                        integerRows(row.get("war_ids"), true), "available".equals(row.path("status").textValue()),
                        integer(row.get("current_soldiers"))));
            }
        }
        return new CountInput(armies, StrictJson.text(snapshot.get("snapshot_id")), requiredInteger(snapshot.get("revision")),
                cache, text(snapshot.get("army_strengths_queried_snapshot_id")), integer(snapshot.get("army_strengths_queried_revision")),
                strengths, StrictJson.text(request.get("role")), integer(request.get("war_id")));
    }

    public static StagingInput decodeStaging(byte[] raw) {
        ObjectNode request = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "row", "province"));
        StrictJson.require(STAGING_SCHEMA.equals(StrictJson.text(request.get("schema"))), "unknown staging request schema");
        JsonNode row = request.get("row");
        StrictJson.require(row.isObject(), "staging row must be an object");
        JsonNode route = row.get("route_province_ids");
        return new StagingInput(truth(row.get("controllable")), integer(row.get("current_province_id")),
                truth(row.get("move_target_observable")), integer(row.get("move_target_province_id")),
                "complete_empty".equals(row.path("route_read_status").textValue()), integer(row.get("route_source_count")),
                "regular".equals(row.path("army_state").textValue()),
                route == null || route.isNull() ? Optional.empty() : Optional.of(integerRows(route, false)),
                truth(row.get("in_combat")), truth(row.get("retreating")), requiredInteger(request.get("province")));
    }

    public static byte[] encodeCount(Optional<BigInteger> result) {
        ObjectNode node = StrictJson.object();
        if (result.isPresent()) {
            StrictJson.require(result.orElseThrow().signum() >= 0, "count cannot be negative");
            node.put("count", result.orElseThrow());
        }
        else { node.putNull("count"); }
        return StrictJson.canonical(node);
    }
    public static Optional<BigInteger> decodeCountResult(byte[] raw) {
        ObjectNode node = StrictJson.object(StrictJson.parse(raw), Set.of("count"));
        Optional<BigInteger> count = integer(node.get("count"));
        count.ifPresent(value -> StrictJson.require(value.signum() >= 0, "count cannot be negative"));
        return count;
    }
    private static Optional<BigInteger> integer(JsonNode value) {
        if (value == null || value.isNull()) { return Optional.empty(); }
        StrictJson.require(value.isIntegralNumber(), "exact integer token required; no bool/float/string");
        return Optional.of(value.bigIntegerValue());
    }
    private static BigInteger requiredInteger(JsonNode value) {
        return integer(value).orElseThrow(() -> new IllegalArgumentException("required integer missing or null"));
    }
    private static Optional<String> text(JsonNode value) {
        if (value == null || value.isNull()) { return Optional.empty(); }
        return Optional.of(StrictJson.text(value));
    }
    private static List<BigInteger> integerRows(JsonNode value, boolean missingAsEmpty) {
        if (value == null && missingAsEmpty) { return List.of(); }
        StrictJson.require(value != null && value.isArray(), "integer collection required");
        List<BigInteger> values = new ArrayList<>();
        for (JsonNode item : value) { values.add(requiredInteger(item)); }
        return List.copyOf(values);
    }
    private static Truth truth(JsonNode value) {
        if (value == null || value.isNull()) { return Truth.UNKNOWN; }
        StrictJson.require(value.isBoolean(), "boolean branch required; no numeric coercion");
        return value.booleanValue() ? Truth.TRUE : Truth.FALSE;
    }
}
