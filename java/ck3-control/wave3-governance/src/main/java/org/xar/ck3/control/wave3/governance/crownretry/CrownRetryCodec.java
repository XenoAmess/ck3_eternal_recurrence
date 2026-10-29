package org.xar.ck3.control.wave3.governance.crownretry;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy.ContextKey;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy.Frame;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy.Hint;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy.State;

/** Strict wire boundary around the existing Crown retry cache projection. */
public final class CrownRetryCodec {
    public static final String MATCH_SCHEMA = "xar.java-crown-future-retry-match/v1";
    public static final String HORIZON_SCHEMA = "xar.java-crown-retry-horizon/v1";
    private CrownRetryCodec() { }

    public record MatchRequest(Frame frame, State state, String lawKey) { }
    public record HorizonRequest(Frame frame, State state, BigInteger requestedDays, boolean queryEnabled, boolean pausedQueryEnabled) { }

    public static MatchRequest decodeMatch(byte[] body) {
        ObjectNode row = StrictJson.object(StrictJson.parse(body), Set.of("schema", "bridge_pid", "snapshot", "state", "law_key"));
        StrictJson.require(MATCH_SCHEMA.equals(StrictJson.text(row.get("schema"))), "Crown retry match schema differs");
        State state = state(row.get("state"));
        return state == null ? new MatchRequest(null, null, null) : new MatchRequest(frame(row), state, text(row.get("law_key")));
    }
    public static HorizonRequest decodeHorizon(byte[] body) {
        ObjectNode row = StrictJson.object(StrictJson.parse(body), Set.of("schema", "bridge_pid", "snapshot", "state", "horizon_days", "query_enabled", "paused_query_enabled"));
        StrictJson.require(HORIZON_SCHEMA.equals(StrictJson.text(row.get("schema"))), "Crown retry horizon schema differs");
        BigInteger requested = integer(row.get("horizon_days"));
        StrictJson.require(requested.signum() > 0, "positive horizon days required");
        boolean enabled = bool(row.get("query_enabled")), pausedEnabled = bool(row.get("paused_query_enabled"));
        if (!enabled || !pausedEnabled || row.get("state").isNull()) {
            return new HorizonRequest(null, null, requested, enabled, pausedEnabled);
        }
        return new HorizonRequest(frame(row), state(row.get("state")), requested, enabled, pausedEnabled);
    }
    public static Optional<Hint> projectMatch(MatchRequest request) {
        return request.state() == null ? Optional.empty()
                : CrownRetryPolicy.matchingFutureRetry(request.frame(), request.state(), request.lawKey());
    }
    public static BigInteger projectHorizon(HorizonRequest request) {
        return CrownRetryPolicy.horizonDays(request.frame(), request.state(), request.requestedDays(),
                request.queryEnabled(), request.pausedQueryEnabled());
    }
    public static byte[] encodeMatch(Optional<Hint> matched) {
        return matched.isEmpty() ? "null".getBytes(StandardCharsets.UTF_8) : matched.orElseThrow().originalWire().getBytes(StandardCharsets.UTF_8);
    }
    public static byte[] encodeHorizon(BigInteger days) { return StrictJson.canonical(BigIntegerNode.valueOf(days)); }
    public static byte[] match(byte[] body) { return encodeMatch(projectMatch(decodeMatch(body))); }
    public static byte[] horizon(byte[] body) { return encodeHorizon(projectHorizon(decodeHorizon(body))); }

    private static Frame frame(ObjectNode request) {
        ObjectNode snapshot = object(request.get("snapshot"));
        JsonNode actor = snapshot.get("played_character");
        boolean actorObject = actor != null && actor.isObject();
        return new Frame(new ContextKey(nullableInteger(request.get("bridge_pid")), text(snapshot.get("episode_run_id"))), actorObject,
                actorObject ? nullableInteger(actor.get("character_id")) : null, nullableInteger(snapshot.get("date_raw")));
    }

    private static State state(JsonNode value) {
        if (value.isNull()) { return null; }
        ObjectNode row = object(value);
        JsonNode pending = row.get("pending");
        boolean pendingPresent = pending != null && !pending.isNull();
        if (pendingPresent) { return new State(true, null); }
        JsonNode retry = row.get("retry");
        if (retry == null || !retry.isObject()) { return new State(pendingPresent, null); }
        JsonNode source = retry.get("source_context");
        ContextKey context = null;
        if (source != null && source.isObject()) {
            Set<String> fields = new HashSet<>(); source.fieldNames().forEachRemaining(fields::add);
            if (fields.equals(Set.of("bridge_pid", "episode_run_id"))) {
                context = new ContextKey(nullableInteger(source.get("bridge_pid")), text(source.get("episode_run_id")));
            }
        }
        if (context == null) { return new State(false, new Hint(null, null, null, null, retry.toString())); }
        // Unknown source-context fields are a true mismatch, as in the original
        // whole-dict comparison. They are never discarded to gain a match.
        return new State(pendingPresent, new Hint(context, nullableInteger(retry.get("actor_character_id")),
                nullableInteger(retry.get("retry_date_raw")), text(retry.get("law_key")), retry.toString()));
    }

    private static ObjectNode object(JsonNode value) { StrictJson.require(value != null && value.isObject(), "JSON object required"); return (ObjectNode) value; }
    private static BigInteger integer(JsonNode value) { StrictJson.require(value != null && value.isIntegralNumber(), "actual integer token required"); return value.bigIntegerValue(); }
    private static BigInteger nullableInteger(JsonNode value) { return value == null || value.isNull() ? null : integer(value); }
    private static boolean bool(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "actual boolean token required"); return value.booleanValue(); }
    private static String text(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isTextual(), "actual string token required");
        return value.textValue().isEmpty() ? "" : StrictJson.text(value);
    }
}
