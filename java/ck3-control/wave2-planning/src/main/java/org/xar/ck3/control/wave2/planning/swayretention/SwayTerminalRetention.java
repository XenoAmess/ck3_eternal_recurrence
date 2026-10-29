package org.xar.ck3.control.wave2.planning.swayretention;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.core.JsonGenerator;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Arrays;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure historical-cause retention; it never attributes the fresh read or rearms consumption. */
public final class SwayTerminalRetention {
    private static final String BUILD = "1.20.0.4";
    private static final String SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String COMPLETE = "authored_sway_complete_100_source";
    private static final ObjectMapper WRITER = new ObjectMapper();
    private SwayTerminalRetention() { }

    public enum Selection { CURRENT_OBSERVATION, HISTORICAL_TERMINAL }

    /** Immutable opaque JSON-domain snapshot. Unknown history fields are carried unchanged. */
    public static final class Snapshot {
        private final byte[] raw;
        private Snapshot(JsonNode value) {
            require(value != null && value.isObject(), "terminal snapshot must be an object");
            try {
                ByteArrayOutputStream output = new ByteArrayOutputStream();
                try (JsonGenerator generator = WRITER.getFactory().createGenerator(output)) { token(value, generator); }
                raw = output.toByteArray();
            }
            catch (IOException error) { throw new ContractViolationException("terminal snapshot serialization failed", error); }
            require(raw.length <= StrictJson.INPUT_MAX_BYTES, "terminal snapshot exceeds finite byte budget");
        }
        public byte[] toJson() { return raw.clone(); }
        @Override public boolean equals(Object other) { return other instanceof Snapshot snapshot && Arrays.equals(raw, snapshot.raw); }
        @Override public int hashCode() { return Arrays.hashCode(raw); }
    }

    public record Result(Selection selection, Snapshot snapshot) {
        public Result { Objects.requireNonNull(selection); Objects.requireNonNull(snapshot); }
        public boolean consumptionRearmed() { return false; }
        public boolean freshReadCauseAttributed() { return false; }
        public boolean submissionAuthorized() { return false; }
    }

    private record Identity(String actionId, long actor, long target, long instance, int generation, String build, String sha) {
        private Identity {
            StrictJson.text(actionId); StrictJson.text(build); StrictJson.text(sha);
            require(actor > 0 && actor <= 0xffff_ffffL && target > 0 && target <= 0xffff_ffffL && actor != target,
                    "full actor/target identity required");
            require(instance >= 0 && instance < 0xffff_ffffL && generation == instance >> 24,
                    "full instance generation differs");
        }
    }
    private record HistoricalProof(Identity identity) { }
    private record CurrentRetainedEnd(Identity identity) { }

    /** Exact outer contract; extensible old history/native objects use consumed-field projections. */
    public static Result evaluate(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("previous", "observation"));
        JsonNode observation = input.get("observation");
        Snapshot current = new Snapshot(observation);
        Optional<HistoricalProof> previous = historical(input.get("previous"));
        Optional<CurrentRetainedEnd> present = current(observation);
        if (previous.isPresent() && present.isPresent()
                && previous.orElseThrow().identity.equals(present.orElseThrow().identity)) {
            return new Result(Selection.HISTORICAL_TERMINAL, new Snapshot(input.get("previous")));
        }
        return new Result(Selection.CURRENT_OBSERVATION, current);
    }

    /** Original producer JSON result, without adding or replacing history fields. */
    public static byte[] compose(byte[] raw) { return evaluate(raw).snapshot.toJson(); }

    private static Optional<HistoricalProof> historical(JsonNode previous) {
        try {
            object(previous); flag(previous.get("instance_terminal_outcome_observed"), true);
            flag(previous.get("terminal_cause_observed"), true);
            Identity original = identity(previous);
            eq(previous.get("terminal_cause"), COMPLETE);
            JsonNode cause = previous.get("causal_observation"); object(cause);
            require(identity(cause).equals(original), "historical causal identity differs");
            eq(cause.get("schema"), "xar.ck3.sway-end-causal-observation.12004.v1");
            eq(cause.get("cause_key"), COMPLETE);
            flag(cause.get("terminal_cause_observed"), true);
            flag(cause.get("native_terminal_transition_observed"), true);
            require(StrictJson.integer(cause.get("native_status_raw"), 1, 1) == 1, "historical cause status differs");
            return Optional.of(new HistoricalProof(original));
        } catch (ContractViolationException unavailable) { return Optional.empty(); }
    }

    private static Optional<CurrentRetainedEnd> current(JsonNode observation) {
        try {
            object(observation); flag(observation.get("instance_terminal_outcome_observed"), true);
            flag(observation.get("terminal_cause_observed"), false);
            Identity identity = identity(observation);
            require(identity.build.equals(BUILD) && identity.sha.toUpperCase(Locale.ROOT).equals(SHA), "exact current build differs");
            JsonNode nativeObservation = observation.get("native_observation"); object(nativeObservation);
            eq(nativeObservation.get("schema"), "xar.ck3.sway_completion.v1");
            flag(nativeObservation.get("available"), true);
            // The native object has no action ID. Join every remaining identity
            // field exactly, including SHA spelling, before retaining history.
            require(id(nativeObservation.get("actor_character_id")) == identity.actor
                    && id(nativeObservation.get("target_character_id")) == identity.target
                    && StrictJson.integer(nativeObservation.get("scheme_instance_id"), 0, 0xffff_fffeL) == identity.instance
                    && StrictJson.integer(nativeObservation.get("scheme_instance_generation"), 0, 255) == identity.generation,
                    "native retained instance differs");
            eq(nativeObservation.get("exact_ck3_build"), identity.build); eq(nativeObservation.get("exe_sha256"), identity.sha);
            for (String field : Set.of("instance_source_observed", "instance_present", "exact_instance_join_ready",
                    "native_status_observed", "native_terminal_state_observed")) { flag(nativeObservation.get(field), true); }
            flag(nativeObservation.get("storage_slot_reused"), false);
            require(StrictJson.integer(nativeObservation.get("native_status_raw"), 1, 1) == 1, "native retained status differs");
            long owner = StrictJson.integer(nativeObservation.get("native_owner_raw"), 0, 0xffff_ffffL);
            require(owner == identity.actor || owner == 0xffff_ffffL, "native owner is neither original nor purged sentinel");
            return Optional.of(new CurrentRetainedEnd(identity));
        } catch (ContractViolationException unavailable) { return Optional.empty(); }
    }

    private static Identity identity(JsonNode row) {
        return new Identity(StrictJson.text(row.get("action_id")), id(row.get("actor_character_id")), id(row.get("target_character_id")),
                StrictJson.integer(row.get("scheme_instance_id"), 0, 0xffff_fffeL),
                Math.toIntExact(StrictJson.integer(row.get("scheme_instance_generation"), 0, 255)),
                StrictJson.text(row.get("exact_ck3_build")), StrictJson.text(row.get("exe_sha256")));
    }
    private static void token(JsonNode value, JsonGenerator generator) throws IOException {
        if (value.isObject()) {
            generator.writeStartObject();
            for (var field : value.properties()) {
                if (!field.getKey().isEmpty()) { StrictJson.text(field.getKey()); }
                generator.writeFieldName(field.getKey()); token(field.getValue(), generator);
            }
            generator.writeEndObject();
        } else if (value.isArray()) {
            generator.writeStartArray(); for (JsonNode item : value) { token(item, generator); } generator.writeEndArray();
        } else if (value.isFloatingPointNumber()) {
            String raw = value.decimalValue().toString();
            if (!raw.contains(".") && !raw.contains("E") && !raw.contains("e")) { raw += ".0"; }
            generator.writeNumber(raw);
        } else {
            if (value.isTextual() && !value.textValue().isEmpty()) { StrictJson.text(value.textValue()); }
            generator.writeTree(value);
        }
    }
    private static long id(JsonNode node) { return StrictJson.integer(node, 1, 0xffff_ffffL); }
    private static void object(JsonNode node) { require(node != null && node.isObject(), "actual object required"); }
    private static void flag(JsonNode node, boolean value) {
        require(node != null && node.isBoolean() && node.booleanValue() == value, "actual source boolean differs");
    }
    private static void eq(JsonNode node, String value) { require(node != null && node.isTextual() && value.equals(node.textValue()), "source text differs"); }
    private static void require(boolean value, String reason) { StrictJson.require(value, reason); }
}
