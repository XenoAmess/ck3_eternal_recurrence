package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.NativeInteractionRoles;

/**
 * Java producer for the original Raiktor white-peace observation and available
 * session validators. This is evidence normalization, never an exit permit.
 * Opaque frame/option/terms objects are detached at this JSON ingress boundary;
 * their consumers apply their own named field contracts before scoring.
 */
public final class RaiktorExitObservationCodec {
    public static final String OBSERVATION_CONTRACT = "raiktor-white-peace-terms-observation-v1";
    public static final String SESSION_BACKEND = "ck3-1.19.0.6-raiktor-six-domain-session-binding-v1";
    public static final String PROJECTION_SCHEMA = "xar.ck3.raiktor_white_peace_narrow_projection_provider.v3";
    public static final String PROJECTION_PROVIDER = "raiktor-white-peace-narrow-projection-v3";
    public static final int MAX_WIRE_BYTES = 1_048_576;
    // Python JSON objects contain finite binary floats; DoubleNode retains negative zero.
    // USE_BIG_DECIMAL_FOR_FLOATS would erase that source distinction at this boundary.
    private static final ObjectMapper WIRE = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNumberLength(4300).build()).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;
    private static final List<String> COMPLETENESS_FIELDS = List.of(
            "claim_disposition_ready", "favor_hook_ready", "final_recipient_response_ready",
            "gold_transfer_ready", "prestige_delta_ready", "prisoner_release_ready", "truce_ready");
    private static final Set<String> OBSERVATION_FIELDS = Set.of("schema_version", "contract", "status", "frame",
            "evaluated_candidate_sha256", "evaluated_surrender_terms_sha256", "producer", "completeness",
            "option", "terms", "same_frame_stable");
    private static final Set<String> PRODUCER_FIELDS = Set.of("producer_id", "producer_version",
            "source_artifact_sha256", "production_live");
    private static final Set<String> BINDING_FIELDS = Set.of("snapshot_id", "snapshot_revision", "native_revision",
            "date_raw", "connection_generation", "episode_run_id", "episode_character_id", "process_id", "war_id");
    private static final Set<String> READINESS_FIELDS = Set.of("snapshot_binding_ready", "query_receipt_binding_ready",
            "same_frame_revision_ready", "episode_owner_ready", "process_binding_ready", "aggregate_session_binding_ready");

    private RaiktorExitObservationCodec() { }

    /** One raw JSON producer boundary used by the common M0 wrapper and by the real consumer probe. */
    public static byte[] execute(byte[] raw) {
        return encodeWire(normalizeOperation(parseWire(raw)));
    }

    /** Shared M0 JSON ingress. Known integer fields are validated by their domain parser after this boundary. */
    public static JsonNode parseWire(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_WIRE_BYTES, "bounded nonempty normalization JSON required");
        require(!(raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf), "UTF-8 BOM rejected");
        for (byte value : raw) require(value != 0, "raw NUL rejected");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode request = WIRE.readTree(text);
            require(request != null, "JSON value required"); requireFinite(request);
            return request;
        } catch (IOException error) { throw new IllegalArgumentException("invalid normalization JSON", error); }
    }

    /** Shared M0 finite JSON egress, preserving integer/float kinds and negative zero in opaque objects. */
    public static byte[] encodeWire(JsonNode value) {
        require(value != null, "JSON value required"); requireFinite(value);
        try {
            byte[] result = WIRE.writeValueAsBytes(value);
            require(result.length <= MAX_WIRE_BYTES, "normalization output exceeds role budget"); return result;
        } catch (IOException error) { throw new IllegalArgumentException("normalization JSON encoding failed", error); }
    }

    private static void requireFinite(JsonNode value) {
        if (value.isFloatingPointNumber()) require(Double.isFinite(value.doubleValue()), "finite JSON numbers required");
        if (value.isContainerNode()) for (JsonNode child : value) requireFinite(child);
    }

    public enum ObservationStatus {
        COMPLETE("complete"), INCOMPLETE("incomplete");
        private final String wire;
        ObservationStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static ObservationStatus parse(JsonNode value) {
            String wire = text(value, "observation.status");
            for (ObservationStatus status : values()) if (status.wire.equals(wire)) return status;
            throw rejected("observation status must be complete or incomplete");
        }
    }

    public record Completeness(boolean claimDispositionReady, boolean favorHookReady,
            boolean finalRecipientResponseReady, boolean goldTransferReady, boolean prestigeDeltaReady,
            boolean prisonerReleaseReady, boolean truceReady) {
        public ObjectNode toJson() {
            return JSON.objectNode().put("claim_disposition_ready", claimDispositionReady)
                    .put("favor_hook_ready", favorHookReady).put("final_recipient_response_ready", finalRecipientResponseReady)
                    .put("gold_transfer_ready", goldTransferReady).put("prestige_delta_ready", prestigeDeltaReady)
                    .put("prisoner_release_ready", prisonerReleaseReady).put("truce_ready", truceReady);
        }
    }

    public record Producer(String producerId, String producerVersion, String sourceArtifactSha256, boolean productionLive) {
        public Producer { Objects.requireNonNull(producerId); Objects.requireNonNull(producerVersion); Objects.requireNonNull(sourceArtifactSha256); }
        public ObjectNode toJson() {
            return JSON.objectNode().put("producer_id", producerId).put("producer_version", producerVersion)
                    .put("source_artifact_sha256", sourceArtifactSha256).put("production_live", productionLive);
        }
    }

    public record Observation(ObservationStatus status, ObjectNode frame, String evaluatedCandidateSha256,
            String evaluatedSurrenderTermsSha256, Producer producerMetadata, Completeness completeness,
            ObjectNode option, ObjectNode terms, boolean sameFrameStable) {
        public Observation {
            Objects.requireNonNull(status); Objects.requireNonNull(completeness); Objects.requireNonNull(producerMetadata);
            frame = frame.deepCopy(); option = option.deepCopy(); terms = terms.deepCopy();
            requireDeclaredContextRoles(option);
        }
        @Override public ObjectNode frame() { return frame.deepCopy(); }
        public ObjectNode producer() { return producerMetadata.toJson(); }
        @Override public ObjectNode option() { return option.deepCopy(); }
        @Override public ObjectNode terms() { return terms.deepCopy(); }
        public ObjectNode toJson() {
            ObjectNode result = JSON.objectNode().put("schema_version", 1).put("contract", OBSERVATION_CONTRACT)
                    .put("status", status.wire());
            result.set("frame", frame()); result.put("evaluated_candidate_sha256", evaluatedCandidateSha256);
            result.put("evaluated_surrender_terms_sha256", evaluatedSurrenderTermsSha256);
            result.set("producer", producer()); result.set("completeness", completeness.toJson());
            result.set("option", option()); result.set("terms", terms()); result.put("same_frame_stable", sameFrameStable);
            return result;
        }
    }


    /** Legacy observation options stay opaque; a declared context-v1 companion keeps its shared strict contract. */
    private static void requireDeclaredContextRoles(ObjectNode option) {
        NativeInteractionRoles roles = requireDeclaredContext(option);
        JsonNode nested = option.get("same_frame_surrender");
        if (nested instanceof ObjectNode surrender) {
            NativeInteractionRoles other = requireDeclaredContext(surrender);
            NativeInteractionRoles.requireSameProfile(roles, other, other);
        } else if (!(roles instanceof NativeInteractionRoles.LegacyWithoutRoles) && option.has("same_frame_surrender")) {
            require(false, "context-v1 same-frame surrender must be an option object");
        }
    }

    private static NativeInteractionRoles requireDeclaredContext(ObjectNode option) {
        NativeInteractionRoles roles = NativeInteractionRoles.fromOption(option);
        if (roles instanceof NativeInteractionRoles.LegacyWithoutRoles) return roles;
        boolean constructed = bool(option.get("context_constructed"), "context-v1 context_constructed");
        ObjectNode response = object(option.get("recipient_response"), "context-v1 recipient response");
        String responseStatus = text(response.get("status"), "context-v1 recipient response status");
        require(Set.of("available", "unavailable").contains(responseStatus), "unknown context-v1 recipient response status");
        if (roles instanceof NativeInteractionRoles.Observed)
            require(constructed, "observed roles require a constructed context");
        if (roles instanceof NativeInteractionRoles.Unavailable) {
            exact(response, Set.of("status", "decision_status_raw", "would_accept_now"), "unavailable context recipient response");
            require("unavailable".equals(responseStatus)
                    && response.get("decision_status_raw").isNull() && response.get("would_accept_now").isNull(),
                    "unavailable roles cannot bind a final recipient answer");
        }
        return roles;
    }

    public record Projection(Observation observation, List<String> unobservedDynamicEffects,
            List<String> surrenderUnobservedDynamicEffects, boolean productionLive, ObjectNode raw) {
        public Projection {
            Objects.requireNonNull(observation);
            unobservedDynamicEffects = List.copyOf(unobservedDynamicEffects);
            surrenderUnobservedDynamicEffects = List.copyOf(surrenderUnobservedDynamicEffects);
            raw = raw.deepCopy();
        }
        @Override public ObjectNode raw() { return raw.deepCopy(); }
    }

    /** The nine expected fields of the original available-session boundary, not a new identity discovery. */
    public record ExpectedBinding(String snapshotId, BigInteger snapshotRevision, BigInteger nativeRevision,
            BigInteger dateRaw, BigInteger connectionGeneration, String episodeRunId,
            BigInteger episodeCharacterId, BigInteger processId, BigInteger warId) {
        public ExpectedBinding {
            nonblank(snapshotId, "expected_snapshot_id");
            positive(snapshotRevision, "expected_snapshot_revision"); positive(nativeRevision, "expected_native_revision");
            Objects.requireNonNull(dateRaw, "expected_date_raw");
            positive(connectionGeneration, "expected_connection_generation");
            nonblank(episodeRunId, "expected_episode_run_id");
            positive(episodeCharacterId, "expected_episode_character_id");
            positive(processId, "expected_process_id"); positive(warId, "expected_war_id");
        }
        public ObjectNode toJson() {
            return JSON.objectNode().put("snapshot_id", snapshotId).put("snapshot_revision", snapshotRevision)
                    .put("native_revision", nativeRevision).put("date_raw", dateRaw)
                    .put("connection_generation", connectionGeneration).put("episode_run_id", episodeRunId)
                    .put("episode_character_id", episodeCharacterId).put("process_id", processId).put("war_id", warId);
        }
    }

    public record Session(ExpectedBinding binding, ObjectNode aggregate, ObjectNode raw) {
        public Session { Objects.requireNonNull(binding); aggregate = aggregate.deepCopy(); raw = raw.deepCopy(); }
        @Override public ObjectNode aggregate() { return aggregate.deepCopy(); }
        @Override public ObjectNode raw() { return raw.deepCopy(); }
    }

    public static Observation normalizeObservation(JsonNode value) {
        ObjectNode item = exact(value, OBSERVATION_FIELDS, "observation");
        versionOne(item.get("schema_version"), "observation schema_version must be 1");
        require(OBSERVATION_CONTRACT.equals(text(item.get("contract"), "observation.contract")), "observation contract drifted");
        ObservationStatus status = ObservationStatus.parse(item.get("status"));
        ObjectNode frame = object(item.get("frame"), "observation.frame");
        ObjectNode producerInput = exact(item.get("producer"), PRODUCER_FIELDS, "observation.producer");
        Producer producer = new Producer(nonblank(producerInput.get("producer_id"), "observation.producer_id"),
                nonblank(producerInput.get("producer_version"), "observation.producer_version"),
                sha(producerInput.get("source_artifact_sha256"), "observation.source_artifact_sha256"),
                bool(producerInput.get("production_live"), "observation.production_live"));
        ObjectNode flags = exact(item.get("completeness"), Set.copyOf(COMPLETENESS_FIELDS), "observation.completeness");
        Completeness completeness = new Completeness(
                bool(flags.get("claim_disposition_ready"), "observation.completeness.claim_disposition_ready"),
                bool(flags.get("favor_hook_ready"), "observation.completeness.favor_hook_ready"),
                bool(flags.get("final_recipient_response_ready"), "observation.completeness.final_recipient_response_ready"),
                bool(flags.get("gold_transfer_ready"), "observation.completeness.gold_transfer_ready"),
                bool(flags.get("prestige_delta_ready"), "observation.completeness.prestige_delta_ready"),
                bool(flags.get("prisoner_release_ready"), "observation.completeness.prisoner_release_ready"),
                bool(flags.get("truce_ready"), "observation.completeness.truce_ready"));
        return new Observation(status, frame, sha(item.get("evaluated_candidate_sha256"), "observation.evaluated_candidate_sha256"),
                sha(item.get("evaluated_surrender_terms_sha256"), "observation.evaluated_surrender_terms_sha256"),
                producer, completeness, object(item.get("option"), "observation.option"),
                object(item.get("terms"), "observation.terms"), bool(item.get("same_frame_stable"), "observation.same_frame_stable"));
    }

    /** Original immediate-evaluator projection ingress, before features or utility are evaluated. */
    public static Projection normalizeProjection(JsonNode value) {
        ObjectNode item = object(value, "white-peace projection");
        require(PROJECTION_SCHEMA.equals(textOrNull(item.get("schema")))
                && PROJECTION_PROVIDER.equals(textOrNull(item.get("provider")))
                && "available".equals(textOrNull(item.get("status"))) && trueValue(item.get("observation_ready"))
                && emptyArray(item.get("blockers")), "white-peace narrow projection is unavailable");
        Observation observation = normalizeObservation(item.get("white_peace_observation"));
        require(observation.status() == ObservationStatus.COMPLETE && observation.sameFrameStable(),
                "white-peace observation is incomplete");
        return new Projection(observation, strings(item.get("unobserved_dynamic_effects"), "projection.unobserved_dynamic_effects"),
                strings(item.get("surrender_unobserved_dynamic_effects"), "projection.surrender_unobserved_dynamic_effects"),
                bool(item.get("production_live"), "white-peace production_live"), item);
    }

    public static Session normalizeSession(JsonNode value, Observation observation) {
        return normalizeSession(value, expectedFromFrame(observation.frame()));
    }

    /** Complete strict consumer of an already-bound aggregate. The six-domain bind producer remains separate. */
    public static Session normalizeSession(JsonNode value, ExpectedBinding expected) {
        Objects.requireNonNull(expected, "expected session binding");
        ObjectNode item = object(value, "Raiktor aggregate session binding");
        versionOne(item.get("schema_version"), "Raiktor aggregate session binding is unavailable");
        require(SESSION_BACKEND.equals(textOrNull(item.get("backend_id")))
                && "available".equals(textOrNull(item.get("status")))
                && (item.get("failure") == null || item.get("failure").isNull())
                && item.get("aggregate") instanceof ObjectNode, "Raiktor aggregate session binding is unavailable");
        ObjectNode binding = exact(item.get("binding"), BINDING_FIELDS, "Raiktor aggregate session binding");
        // Validate actual numeric kinds before equality; Python bool/float equality cannot grant identity.
        ExpectedBinding actual = binding(binding);
        require(actual.equals(expected), "Raiktor aggregate session binding disagrees");
        ObjectNode readiness = exact(item.get("readiness"), READINESS_FIELDS, "Raiktor aggregate session readiness");
        for (String field : READINESS_FIELDS) require(trueValue(readiness.get(field)), "Raiktor aggregate session readiness overclaims");
        return new Session(actual, (ObjectNode) item.get("aggregate"), item);
    }

    public static ExpectedBinding expectedFromFrame(JsonNode value) {
        ObjectNode frame = object(value, "white-peace frame");
        String connection = textOrNull(frame.get("connection_id"));
        String prefix = "connection-generation:";
        require(connection != null && connection.startsWith(prefix), "white-peace frame lacks connection generation");
        BigInteger generation = pythonInteger(connection.substring(prefix.length()));
        return new ExpectedBinding(nonblank(frame.get("snapshot_id"), "expected_snapshot_id"),
                positiveInteger(frame.get("snapshot_revision"), "expected_snapshot_revision"),
                positiveInteger(frame.get("native_revision"), "expected_native_revision"),
                integer(frame.get("date_raw"), "expected_date_raw"), generation,
                nonblank(frame.get("episode_id"), "expected_episode_run_id"),
                positiveInteger(frame.get("primary_attacker_character_id"), "expected_episode_character_id"),
                positiveInteger(frame.get("ck3_pid"), "expected_process_id"),
                positiveInteger(frame.get("war_id"), "expected_war_id"));
    }

    /** Wire adapter for callers of the existing nine-key keyword-only session normalizer. */
    public static ExpectedBinding expectedBinding(JsonNode value) {
        ObjectNode row = exact(value, BINDING_FIELDS, "expected session binding");
        return binding(row);
    }

    private static ExpectedBinding binding(ObjectNode row) {
        return new ExpectedBinding(nonblank(row.get("snapshot_id"), "expected_snapshot_id"),
                positiveInteger(row.get("snapshot_revision"), "expected_snapshot_revision"),
                positiveInteger(row.get("native_revision"), "expected_native_revision"),
                integer(row.get("date_raw"), "expected_date_raw"),
                positiveInteger(row.get("connection_generation"), "expected_connection_generation"),
                nonblank(row.get("episode_run_id"), "expected_episode_run_id"),
                positiveInteger(row.get("episode_character_id"), "expected_episode_character_id"),
                positiveInteger(row.get("process_id"), "expected_process_id"),
                positiveInteger(row.get("war_id"), "expected_war_id"));
    }

    /** Migration operation adapter for the same M0 wrapper; it opens no transport or state writer. */
    public static ObjectNode normalizeOperation(JsonNode value) {
        ObjectNode request = object(value, "M0 normalization request");
        String operation = text(request.get("operation"), "operation");
        return switch (operation) {
            case "normalize-white-peace-observation" -> {
                exact(request, Set.of("operation", "value"), "observation request");
                yield normalizeObservation(request.get("value")).toJson();
            }
            case "normalize-surrender-session" -> {
                exact(request, Set.of("operation", "value", "expected"), "session request");
                yield normalizeSession(request.get("value"), expectedBinding(request.get("expected"))).raw();
            }
            default -> throw rejected("unknown M0 normalization operation");
        };
    }

    private static ObjectNode object(JsonNode value, String name) {
        require(value instanceof ObjectNode, name + " must be an object");
        return (ObjectNode) value;
    }
    private static ObjectNode exact(JsonNode value, Set<String> fields, String name) {
        ObjectNode item = object(value, name);
        Set<String> actual = new HashSet<>(); item.properties().forEach(entry -> actual.add(entry.getKey()));
        require(actual.equals(fields), name + " has a malformed schema"); return item;
    }
    private static String text(JsonNode value, String name) {
        require(value != null && value.isTextual(), name + " must be a string"); return value.textValue();
    }
    private static String textOrNull(JsonNode value) { return value != null && value.isTextual() ? value.textValue() : null; }
    private static String nonblank(JsonNode value, String name) { return nonblank(text(value, name), name); }
    private static String nonblank(String value, String name) {
        require(value != null && !pythonStrip(value).isEmpty(), name + " must be a nonempty string"); return value;
    }
    private static String sha(JsonNode value, String name) {
        String text = text(value, name); require(text.matches("[0-9A-F]{64}"), name + " must be an uppercase SHA-256"); return text;
    }
    private static boolean bool(JsonNode value, String name) {
        require(value != null && value.isBoolean(), name + " must be a boolean"); return value.booleanValue();
    }
    private static boolean trueValue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static boolean emptyArray(JsonNode value) { return value != null && value.isArray() && value.isEmpty(); }
    private static BigInteger integer(JsonNode value, String name) {
        require(value != null && value.isIntegralNumber(), name + " must be an integer"); return value.bigIntegerValue();
    }
    private static BigInteger positiveInteger(JsonNode value, String name) { return positive(integer(value, name), name); }
    private static BigInteger positive(BigInteger value, String name) {
        require(value != null && value.signum() > 0, name + " must be positive"); return value;
    }
    private static void versionOne(JsonNode value, String reason) {
        require(value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(BigInteger.ONE), reason);
    }
    private static List<String> strings(JsonNode value, String name) {
        require(value != null && value.isArray(), name + " must be a list");
        List<String> result = new ArrayList<>(); Set<String> seen = new HashSet<>();
        for (JsonNode entry : value) {
            String text = nonblank(entry, name + "[]");
            require(seen.add(text), name + " contains duplicates"); result.add(text);
        }
        return List.copyOf(result);
    }
    // Python int(str) accepts a sign, decimal Unicode digits and single digit separators.
    // Preserve that source contract; generation positivity is checked by ExpectedBinding.
    private static BigInteger pythonInteger(String value) {
        String stripped = pythonStrip(value);
        StringBuilder digits = new StringBuilder(); boolean previousDigit = false;
        int index = 0;
        if (!stripped.isEmpty() && (stripped.charAt(0) == '+' || stripped.charAt(0) == '-')) {
            digits.append(stripped.charAt(0)); index++;
        }
        for (; index < stripped.length();) {
            int point = stripped.codePointAt(index); index += Character.charCount(point);
            if (point == '_') {
                require(previousDigit && index < stripped.length() && Character.digit(stripped.codePointAt(index), 10) >= 0,
                        "white-peace connection generation is malformed");
                previousDigit = false; continue;
            }
            int digit = Character.digit(point, 10);
            require(digit >= 0 && Character.getType(point) == Character.DECIMAL_DIGIT_NUMBER,
                    "white-peace connection generation is malformed");
            digits.append((char) ('0' + digit)); previousDigit = true;
        }
        require(previousDigit, "white-peace connection generation is malformed");
        return new BigInteger(digits.toString());
    }
    private static String pythonStrip(String value) {
        int start = 0, end = value.length();
        while (start < end && pythonWhitespace(value.codePointAt(start))) start += Character.charCount(value.codePointAt(start));
        while (end > start && pythonWhitespace(value.codePointBefore(end))) end -= Character.charCount(value.codePointBefore(end));
        return value.substring(start, end);
    }
    private static boolean pythonWhitespace(int point) {
        return point >= 9 && point <= 13 || point >= 28 && point <= 32 || point == 0x85 || point == 0xA0
                || point == 0x1680 || point >= 0x2000 && point <= 0x200A || point == 0x2028 || point == 0x2029
                || point == 0x202F || point == 0x205F || point == 0x3000;
    }
    private static void require(boolean condition, String reason) { if (!condition) throw rejected(reason); }
    private static IllegalArgumentException rejected(String reason) { return new IllegalArgumentException(reason); }
}

