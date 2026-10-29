package org.xar.ck3.control.wave3.governance.crowncooldown;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown.Clock;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown.DurationLiteral;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown.RawObservation;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown.TurnTick;

/** Versioned strict codecs for source-closed native clock value operations. */
public final class CrownCooldownCodec {
    public static final String LITERAL_SCHEMA = "xar.java-crown-duration-literal/v1";
    public static final String CLOCK_SCHEMA = "xar.java-crown-cooldown-clock/v1";
    public static final String NORMALIZED_CLOCK_SCHEMA = "xar.java-crown-cooldown-normalized-clock/v1";
    private CrownCooldownCodec() { }

    public record LiteralRequest(BigInteger tokenId, int literalI32) { }
    public record ClockRequest(RawObservation observation, BigInteger dateRaw, TurnTick turnTick) { }

    public static LiteralRequest decodeLiteral(byte[] body) {
        ObjectNode row = StrictJson.object(StrictJson.parse(body), Set.of("schema", "token_id", "literal_i32"));
        StrictJson.require(LITERAL_SCHEMA.equals(StrictJson.text(row.get("schema"))), "native duration literal schema differs");
        return new LiteralRequest(integer(row.get("token_id")), i32(row.get("literal_i32")));
    }
    public static ClockRequest decodeClock(byte[] body) {
        ObjectNode row = StrictJson.object(StrictJson.parse(body), Set.of("schema", "date_raw", "raw_observation", "turn_tick_observation"));
        StrictJson.require(CLOCK_SCHEMA.equals(StrictJson.text(row.get("schema"))), "native cooldown clock schema differs");
        return new ClockRequest(decodeRawObservation(row.get("raw_observation")), integer(row.get("date_raw")),
                row.get("turn_tick_observation").isNull() ? null : decodeTurnTickObservation(row.get("turn_tick_observation")));
    }
    public static ClockRequest decodeNormalizedClock(byte[] body) {
        return decodeRawRequest(body, NORMALIZED_CLOCK_SCHEMA);
    }
    public static ClockRequest decodeRawNormalization(byte[] body) {
        return decodeRawRequest(body, "xar.java-crown-cooldown-raw-normalize/v1");
    }
    private static ClockRequest decodeRawRequest(byte[] body, String schema) {
        ObjectNode row = StrictJson.object(StrictJson.parse(body), Set.of("schema", "date_raw", "raw_observation"));
        StrictJson.require(schema.equals(StrictJson.text(row.get("schema"))), "normalized cooldown clock schema differs");
        return new ClockRequest(decodeRawObservation(row.get("raw_observation")), integer(row.get("date_raw")), null);
    }
    public static TurnTick decodeTickNormalization(byte[] body) {
        ObjectNode row = StrictJson.object(StrictJson.parse(body), Set.of("schema", "turn_tick_observation"));
        StrictJson.require("xar.java-crown-cooldown-turn-tick-normalize/v1".equals(StrictJson.text(row.get("schema"))), "turn-tick normalization schema differs");
        return decodeTurnTickObservation(row.get("turn_tick_observation"));
    }
    public static RawObservation normalizeRaw(ClockRequest request) {
        CrownCooldown.validateRaw(request.observation(), request.dateRaw());
        return request.observation();
    }
    public static TurnTick normalizeTurnTick(TurnTick observation) {
        CrownCooldown.validateTurnTick(observation); return observation;
    }
    public static byte[] scale(byte[] body) {
        LiteralRequest request = decodeLiteral(body);
        return encode(CrownCooldown.scale(request.tokenId(), request.literalI32()));
    }
    public static byte[] interpret(byte[] body) {
        ClockRequest request = decodeClock(body);
        return encode(CrownCooldown.interpret(request.observation(), request.dateRaw(), request.turnTick()));
    }
    public static byte[] interpretNormalized(byte[] body) {
        ClockRequest request = decodeNormalizedClock(body);
        return encode(CrownCooldown.interpretNormalized(request.observation(), request.dateRaw()));
    }
    public static byte[] normalizeRaw(byte[] body) { return encode(normalizeRaw(decodeRawNormalization(body))); }
    public static byte[] normalizeTurnTick(byte[] body) { return encode(normalizeTurnTick(decodeTickNormalization(body))); }

    public static byte[] encode(RawObservation value) {
        ObjectNode row = StrictJson.object(); row.put("read_available", value.readAvailable());
        nullableBoolean(row, "present", value.present()); nullableBoolean(row, "timed", value.timed());
        nullable(row, "expiry_raw", value.expiryRaw()); nullable(row, "current_clock_raw", value.currentClockRaw());
        nullable(row, "remaining_raw", value.remainingRaw());
        if (value.retryDateRaw() == null) { row.putNull("retry_date_raw"); } else { row.put("retry_date_raw", value.retryDateRaw()); }
        row.put("expiry_type", value.expiryType()); row.put("remaining_unit", value.remainingUnit());
        return StrictJson.canonical(row);
    }
    public static byte[] encode(TurnTick value) {
        ObjectNode row = StrictJson.object(); row.put("source", value.source()); row.put("read_available", value.readAvailable());
        if (value.managerMatchCount() == null) { row.putNull("manager_match_count"); } else { row.put("manager_match_count", value.managerMatchCount()); }
        nullableBoolean(row, "manager_contains_context", value.managerContainsContext());
        nullableBoolean(row, "scalar_tail_allows_tick", value.scalarTailAllowsTick());
        nullableBoolean(row, "context_tick_eligible", value.contextTickEligible());
        if (value.unavailableReason() == null) { row.putNull("unavailable_reason"); } else { row.put("unavailable_reason", value.unavailableReason()); }
        return StrictJson.canonical(row);
    }
    private static void nullableBoolean(ObjectNode row, String key, Boolean value) {
        if (value == null) { row.putNull(key); } else { row.put(key, value); }
    }

    public static byte[] encode(DurationLiteral value) {
        ObjectNode row = StrictJson.object();
        row.put("token_id", value.tokenId()); row.put("literal_i32", value.literalI32());
        row.put("accepted", value.accepted()); row.put("multiplier_i32", value.multiplierI32());
        nullable(row, "clock_steps_i32", value.clockStepsI32());
        return StrictJson.canonical(row);
    }

    public static byte[] encode(Clock value) {
        ObjectNode row = StrictJson.object(); row.put("state", value.state().wire());
        nullable(row, "current_clock_raw", value.currentClockRaw());
        nullable(row, "native_clock_deadline_raw", value.nativeClockDeadlineRaw());
        nullable(row, "remaining_native_clock_steps", value.remainingNativeClockSteps());
        if (value.queryRetryDateRaw() == null) { row.putNull("query_retry_date_raw"); }
        else { row.put("query_retry_date_raw", value.queryRetryDateRaw()); }
        ArrayNode factors = row.putArray("duration_token_factors");
        value.durationTokenFactors().forEach(factor -> factors.addArray().add(factor.tokenId()).add(factor.multiplierI32()));
        row.put("keyword_names_qualified", value.keywordNamesQualified()); row.put("calendar_deadline_ready", value.calendarDeadlineReady());
        return StrictJson.canonical(row);
    }

    public static RawObservation decodeRawObservation(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("read_available", "present", "timed", "expiry_raw", "current_clock_raw",
                "remaining_raw", "retry_date_raw", "expiry_type", "remaining_unit"));
        return new RawObservation(bool(row.get("read_available")), nullableBool(row.get("present")), nullableBool(row.get("timed")),
                nullableI32(row.get("expiry_raw")), nullableI32(row.get("current_clock_raw")), nullableI32(row.get("remaining_raw")),
                row.get("retry_date_raw").isNull() ? null : integer(row.get("retry_date_raw")),
                StrictJson.text(row.get("expiry_type")), StrictJson.text(row.get("remaining_unit")));
    }

    public static TurnTick decodeTurnTickObservation(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("source", "read_available", "manager_match_count", "manager_contains_context",
                "scalar_tail_allows_tick", "context_tick_eligible", "unavailable_reason"));
        JsonNode reason = row.get("unavailable_reason");
        if (!reason.isNull()) { StrictJson.require(reason.isTextual(), "turn-tick reason must be string or null"); }
        return new TurnTick(bool(row.get("read_available")), row.get("manager_match_count").isNull() ? null : integer(row.get("manager_match_count")),
                nullableBool(row.get("manager_contains_context")), nullableBool(row.get("scalar_tail_allows_tick")),
                nullableBool(row.get("context_tick_eligible")), reason.isNull() ? null : reason.textValue(), StrictJson.text(row.get("source")));
    }

    private static BigInteger integer(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "actual native integer token required"); return value.bigIntegerValue();
    }
    private static int i32(JsonNode value) { return Math.toIntExact(StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE)); }
    private static Integer nullableI32(JsonNode value) { return value.isNull() ? null : i32(value); }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "actual native boolean token required"); return value.booleanValue();
    }
    private static Boolean nullableBool(JsonNode value) { return value.isNull() ? null : bool(value); }
    private static void nullable(ObjectNode row, String field, Integer value) { if (value == null) { row.putNull(field); } else { row.put(field, value.intValue()); } }
}
