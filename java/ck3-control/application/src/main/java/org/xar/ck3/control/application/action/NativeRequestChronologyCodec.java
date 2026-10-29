package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Sole durable representation of actual endpoint chronology. No legacy aliases or synthetic upgrades. */
public final class NativeRequestChronologyCodec {
    public static final String SCHEMA = "xar.java.native-request-chronology/v1";
    private static final Set<String> FIELDS = Set.of("schema", "session", "custody_epoch", "request_id", "original_request", "original_response",
            "write_entered", "write_completed", "response_received");
    private NativeRequestChronologyCodec() { }
    public static ObjectNode encode(NativeRequestChronology value) {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA); row.set("session", session(value.session())); row.put("custody_epoch", value.custodyEpoch().toString());
        row.put("request_id", value.requestId()); row.set("original_request", packet(value.originalRequest()));
        row.set("original_response", packet(value.originalResponse())); row.set("write_entered", event(value.writeEntered()));
        row.set("write_completed", event(value.writeCompleted())); row.set("response_received", event(value.responseReceived())); return row;
    }
    public static NativeRequestChronology decode(JsonNode value) {
        ObjectNode row = StrictJson.object(value, FIELDS);
        StrictJson.require(StrictJson.text(row.get("schema")).equals(SCHEMA), "native request chronology schema mismatch");
        return new NativeRequestChronology(session(row.get("session")), epoch(row.get("custody_epoch")), StrictJson.text(row.get("request_id")),
                packet(row.get("original_request")), packet(row.get("original_response")), event(row.get("write_entered")),
                event(row.get("write_completed")), event(row.get("response_received")));
    }
    private static ObjectNode session(NativeObservationPort.TransportSession value) {
        ObjectNode row = StrictJson.object(); row.put("machine_id", value.machineId()); row.set("game", value.game().toJson());
        row.put("connection_generation", value.connectionGeneration().toString()); row.put("session_id", value.sessionId()); return row;
    }
    private static NativeObservationPort.TransportSession session(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("machine_id", "game", "connection_generation", "session_id"));
        return new NativeObservationPort.TransportSession(StrictJson.text(row.get("machine_id")), GameGeneration.fromJson(row.get("game")),
                positive(row.get("connection_generation")), StrictJson.text(row.get("session_id")));
    }
    private static ObjectNode packet(NativeRequestChronology.PacketIdentity value) {
        ObjectNode row = StrictJson.object(); row.put("bytes", value.bytes()); row.put("sha256", value.sha256()); return row;
    }
    private static NativeRequestChronology.PacketIdentity packet(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("bytes", "sha256"));
        return new NativeRequestChronology.PacketIdentity(StrictJson.integer(row.get("bytes"), 1, RawJson.MAXIMUM_BYTES + 4L), StrictJson.text(row.get("sha256")));
    }
    private static ObjectNode event(NativeRequestChronology.Event value) {
        ObjectNode row = StrictJson.object(); row.put("order", value.order().toString()); row.put("observed_at", value.observedAt().toString()); return row;
    }
    private static NativeRequestChronology.Event event(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("order", "observed_at")); String encoded = StrictJson.text(row.get("observed_at"));
        Instant observed;
        try { observed = Instant.parse(encoded); }
        catch (DateTimeParseException malformed) { throw new IllegalArgumentException("canonical actual endpoint UTC instant required", malformed); }
        StrictJson.require(observed.toString().equals(encoded), "canonical actual endpoint UTC instant required");
        return new NativeRequestChronology.Event(positive(row.get("order")), observed);
    }
    private static UUID epoch(JsonNode value) {
        String encoded = StrictJson.text(value); UUID decoded = UUID.fromString(encoded);
        StrictJson.require(decoded.toString().equals(encoded), "canonical actual transport custody epoch required"); return decoded;
    }
    private static BigInteger positive(JsonNode value) {
        String encoded = StrictJson.text(value);
        StrictJson.require(encoded.matches("[1-9][0-9]{0,19}"), "canonical positive decimal u64 string required");
        BigInteger result = new BigInteger(encoded);
        StrictJson.require(result.compareTo(StrictJson.UINT64_MAX) <= 0, "decimal u64 chronology carrier out of range"); return result;
    }
}
