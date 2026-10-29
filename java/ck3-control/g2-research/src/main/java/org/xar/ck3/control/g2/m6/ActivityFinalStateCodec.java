package org.xar.ck3.control.g2.m6;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.ActivityFinalState.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/**
 * One compact persistence contract, containing locators rather than native
 * packet copies. Decode requires original-source replay and the actual reducer;
 * JSON shape, fields and a constructor alone cannot restore qualified state.
 */
public final class ActivityFinalStateCodec {
    public static final String SCHEMA = "xar.java.activity-final-state/v1";
    public static final int MAX_BYTES = 131072;
    private ActivityFinalStateCodec() {}

    @FunctionalInterface public interface Replay {
        /** Root reopens the same writer's archived read and runs the installed decoder and both original guards. */
        Sample replay(Identity identity, ObservationIdentity queried, Provenance provenance);
    }

    public static byte[] encode(State state) {
        Objects.requireNonNull(state);
        ObjectNode root = StrictJson.object(); root.put("schema", SCHEMA);
        ObjectNode identity = root.putObject("identity");
        identity.put("original_action_id", state.identity().originalActionId());
        identity.put("activity_full_id", state.identity().activityFullId());
        identity.put("host_character_id", state.identity().hostCharacterId());
        identity.put("activity_type_key", state.identity().typeKey());
        root.set("origin", ProposalLifecycleCodec.observation(state.origin()));
        put(root, "latest", state.latest()); put(root, "first_final", state.firstFinal());
        return StrictJson.canonical(root, MAX_BYTES);
    }

    public static State decode(byte[] bytes, Replay originalReplay) {
        Objects.requireNonNull(originalReplay, "actual original-read replay is mandatory");
        ObjectNode root = StrictJson.object(StrictJson.parse(bytes, MAX_BYTES),
                Set.of("schema", "identity", "origin", "latest", "first_final"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))), "Activity final state schema differs");
        ObjectNode row = StrictJson.object(root.get("identity"),
                Set.of("original_action_id", "activity_full_id", "host_character_id", "activity_type_key"));
        Identity identity = new Identity(StrictJson.text(row.get("original_action_id")),
                StrictJson.integer(row.get("activity_full_id"), 0, 0xFFFF_FFFEL),
                StrictJson.integer(row.get("host_character_id"), 1, 0xFFFF_FFFEL),
                StrictJson.text(row.get("activity_type_key")));
        ObservationIdentity origin = ProposalLifecycleCodec.decodeObservation(root.get("origin"));
        Optional<Sample> latest = read(root.get("latest"), identity, originalReplay);
        Optional<Sample> first = read(root.get("first_final"), identity, originalReplay);
        StrictJson.require(first.isEmpty() || latest.isPresent(), "retained final state requires its latest observation");
        first.ifPresent(value -> StrictJson.require(value.kind() == Kind.FINAL_UNATTRIBUTED,
                "retained first final lacks its independently observed native flag"));
        State state = ActivityFinalState.empty(identity, origin);
        if (first.isPresent()) state = ActivityFinalState.observe(state, first.orElseThrow());
        if (latest.isPresent()) state = ActivityFinalState.observe(state, latest.orElseThrow());
        StrictJson.require(state.latest().equals(latest) && state.firstFinal().equals(first),
                "restored Activity summaries differ from the unique reducer's original-source replay");
        return state;
    }

    private static void put(ObjectNode root, String field, Optional<Sample> sample) {
        if (sample.isEmpty()) { root.putNull(field); return; }
        Sample value = sample.orElseThrow(); ObjectNode row = root.putObject(field);
        row.set("queried", ProposalLifecycleCodec.observation(value.queried()));
        ObjectNode proof = row.putObject("provenance");
        proof.set("original_read", value.provenance().originalRead().toJson());
        proof.set("producer_source", value.provenance().producerSource().toJson());
        proof.set("hello_source", value.provenance().helloSource().toJson());
        ObjectNode instance = row.putObject("instance");
        if (value.instance() instanceof Missing) instance.put("kind", "MISSING_EXACT_INSTANCE");
        else if (value.instance() instanceof Flags flags) {
            instance.put("kind", "FLAGS").put("completed", flags.completed()).put("invalidated", flags.invalidated());
            stamp(instance, flags.rawCompletionStamp());
        } else if (value.instance() instanceof RetainedFlags retained) {
            instance.put("kind", "RETAINED_FLAGS");
            byteValue(instance, "completed_raw", retained.completedRaw());
            byteValue(instance, "invalidated_raw", retained.invalidatedRaw());
            stamp(instance, retained.rawCompletionStamp());
            instance.put("capture_sequence", retained.captureSequence().toString());
            instance.put("captured_date_raw", retained.capturedDateRaw().toString());
        } else if (value.instance() instanceof FlagsUnavailable unknown) {
            instance.put("kind", "FLAGS_UNAVAILABLE"); stamp(instance, unknown.rawCompletionStamp());
        } else throw new IllegalArgumentException("unknown Activity instance branch");
    }

    private static Optional<Sample> read(JsonNode input, Identity identity, Replay replay) {
        StrictJson.require(input != null, "Activity sample field is required, even when null");
        if (input.isNull()) return Optional.empty();
        ObjectNode row = StrictJson.object(input, Set.of("queried", "provenance", "instance"));
        ObservationIdentity queried = ProposalLifecycleCodec.decodeObservation(row.get("queried"));
        ObjectNode proof = StrictJson.object(row.get("provenance"),
                Set.of("original_read", "producer_source", "hello_source"));
        Provenance provenance = new Provenance(ExactRef.fromJson(proof.get("original_read")),
                ExactRef.fromJson(proof.get("producer_source")), ExactRef.fromJson(proof.get("hello_source")));
        JsonNode raw = row.get("instance");
        StrictJson.require(raw != null && raw.isObject(), "Activity instance object required");
        String kind = StrictJson.text(raw.get("kind"));
        Instance instance;
        switch (kind) {
            case "MISSING_EXACT_INSTANCE" -> {
                StrictJson.object(raw, Set.of("kind")); instance = new Missing();
            }
            case "FLAGS_UNAVAILABLE" -> {
                StrictJson.object(raw, Set.of("kind", "raw_stamp"));
                instance = new FlagsUnavailable(stamp(raw.get("raw_stamp")));
            }
            case "FLAGS" -> {
                StrictJson.object(raw, Set.of("kind", "completed", "invalidated", "raw_stamp"));
                instance = new Flags(bool(raw.get("completed")), bool(raw.get("invalidated")), stamp(raw.get("raw_stamp")));
            }
            case "RETAINED_FLAGS" -> {
                StrictJson.object(raw, Set.of("kind", "completed_raw", "invalidated_raw", "raw_stamp",
                        "capture_sequence", "captured_date_raw"));
                instance = new RetainedFlags(byteValue(raw.get("completed_raw")), byteValue(raw.get("invalidated_raw")),
                        stamp(raw.get("raw_stamp")), stamp(raw.get("capture_sequence")).orElseThrow(
                                () -> new IllegalArgumentException("terminal capture sequence cannot be null")),
                        signed64(raw.get("captured_date_raw")));
            }
            default -> throw new IllegalArgumentException("unknown Activity instance kind");
        }
        Sample metadata = new Sample(identity, queried, instance, provenance);
        Sample actual = Objects.requireNonNull(replay.replay(identity, queried, provenance), "actual Activity replay sample required");
        StrictJson.require(metadata.equals(actual), "persisted Activity flags/provenance differ from their original native read");
        return Optional.of(actual);
    }

    private static void stamp(ObjectNode row, Optional<BigInteger> value) {
        if (value.isPresent()) row.put("raw_stamp", value.orElseThrow().toString());
        else row.putNull("raw_stamp");
    }
    private static Optional<BigInteger> stamp(JsonNode value) {
        StrictJson.require(value != null, "raw stamp is required and nullable");
        if (value.isNull()) return Optional.empty();
        String text = StrictJson.text(value);
        StrictJson.require(text.matches("0|[1-9][0-9]{0,19}"), "opaque uint64 stamp requires canonical decimal text");
        BigInteger number = new BigInteger(text);
        StrictJson.require(number.compareTo(StrictJson.UINT64_MAX) <= 0, "opaque stamp exceeds uint64");
        return Optional.of(number);
    }
    private static void byteValue(ObjectNode row, String key, Optional<Integer> value) {
        if (value.isPresent()) row.put(key, value.orElseThrow()); else row.putNull(key);
    }
    private static Optional<Integer> byteValue(JsonNode value) {
        StrictJson.require(value != null, "retained native byte is required and nullable");
        return value.isNull() ? Optional.empty() : Optional.of((int) StrictJson.integer(value, 0, 255));
    }
    private static BigInteger signed64(JsonNode value) {
        String text = StrictJson.text(value);
        StrictJson.require(text.matches("0|-?[1-9][0-9]{0,18}"), "canonical signed64 capture date required");
        BigInteger number = new BigInteger(text);
        StrictJson.require(number.compareTo(BigInteger.valueOf(Long.MIN_VALUE)) >= 0
                && number.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0, "capture date exceeds signed64");
        return number;
    }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "exact native flag boolean required");
        return value.booleanValue();
    }
}
