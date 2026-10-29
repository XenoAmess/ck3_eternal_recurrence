package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** The public option number is native index + 1; rendered position is never used as its identity. */
public final class EventOptionPublicCodec {
    public static final int MAXIMUM_REQUEST_BYTES = 16384;
    private static final Set<String> FIELDS = Set.of("option_number", "event_instance_id", "expected_revision");
    private EventOptionPublicCodec() { }
    public enum Presence { MISSING, NULL, VALUE }
    public record Field<T>(Presence presence, T value) {
        public Field { Objects.requireNonNull(presence); require((presence == Presence.VALUE) == (value != null), "public event optional field presence/value differs"); }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, null); }
        public static <T> Field<T> nullValue() { return new Field<>(Presence.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.VALUE, Objects.requireNonNull(value)); }
    }
    public record Request(EventActionPreparation.OptionNumber optionNumber, Field<Integer> eventInstanceId,
            Field<BigInteger> expectedRevision) {
        public Request {
            Objects.requireNonNull(optionNumber); Objects.requireNonNull(eventInstanceId); Objects.requireNonNull(expectedRevision);
            if (eventInstanceId.presence() == Presence.VALUE) require(eventInstanceId.value() > 0, "event_instance_id must be a positive full int32");
            if (expectedRevision.presence() == Presence.VALUE) require(expectedRevision.value().signum() >= 0 && expectedRevision.value().bitLength() <= 64, "public expected_revision must be uint64");
        }
    }
    public static Request decode(PublicBindings.Arguments arguments) {
        require(arguments instanceof PublicBindings.Value, "select_event_option requires present object arguments");
        ObjectNode n = object(StrictJson.parse(((PublicBindings.Value) arguments).original().bytes(), MAXIMUM_REQUEST_BYTES));
        require(n.has("option_number"), "select_event_option requires option_number");
        n.fieldNames().forEachRemaining(name -> require(FIELDS.contains(name), "unknown select_event_option field: " + name));
        int number = (int) StrictJson.integer(n.get("option_number"), 1, 999999999);
        Field<Integer> instance = !n.has("event_instance_id") ? Field.missing() : n.get("event_instance_id").isNull() ? Field.nullValue()
                : Field.of((int) StrictJson.integer(n.get("event_instance_id"), 1, Integer.MAX_VALUE));
        Field<BigInteger> revision = !n.has("expected_revision") ? Field.missing() : n.get("expected_revision").isNull() ? Field.nullValue()
                : Field.of(decimal(n.get("expected_revision")));
        return new Request(new EventActionPreparation.OptionNumber(number), instance, revision);
    }
    public static RawJson encodeRequest(Request request) {
        Objects.requireNonNull(request); ObjectNode n = StrictJson.object().put("option_number", request.optionNumber().value());
        switch (request.eventInstanceId().presence()) { case MISSING -> { } case NULL -> n.putNull("event_instance_id"); case VALUE -> n.put("event_instance_id", request.eventInstanceId().value()); }
        switch (request.expectedRevision().presence()) { case MISSING -> { } case NULL -> n.putNull("expected_revision"); case VALUE -> n.put("expected_revision", request.expectedRevision().value().toString()); }
        return new RawJson(StrictJson.canonical(n, MAXIMUM_REQUEST_BYTES));
    }
    public static BigInteger decimal(JsonNode value) {
        require(value != null && value.isTextual(), "public expected_revision requires canonical uint64 decimal string");
        String token = value.textValue(); require(token.length() <= 20 && token.matches("0|[1-9][0-9]*"), "public expected_revision is not canonical uint64 decimal");
        BigInteger parsed = new BigInteger(token); require(parsed.bitLength() <= 64, "public expected_revision exceeds uint64"); return parsed;
    }
    private static ObjectNode object(JsonNode value) { require(value != null && value.isObject(), "select_event_option argument object required"); return (ObjectNode) value; }
    private static void require(boolean valid, String reason) { StrictJson.require(valid, reason); }
}
