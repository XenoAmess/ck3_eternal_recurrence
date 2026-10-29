package org.xar.ck3.control.g2.planning;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import java.math.BigInteger;
import java.io.IOException;
import java.nio.CharBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.finance.jointbudget.JointBudgetCodec;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import static org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Domain payload codec. Common G2 wrapper frame/source are validated and mapped once by the host adapter. */
public final class ProposalLifecycleCodec {
    public static final String REQUEST_SCHEMA = "xar.g2-proposal-lifecycle-request/v1";
    public static final String RESULT_SCHEMA = "xar.g2-proposal-lifecycle-result/v1";
    public static final String FACT_SCHEMA = "xar.java-action-external-fact/v2";
    public static final int MAX_BYTES = 262_144;
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    private ProposalLifecycleCodec() { }

    public static Input decode(byte[] raw, G2Source source) {
        StrictJson.require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded lifecycle payload required");
        ProjectionJson.object(raw, MAX_BYTES); // Validate every string, including escaped surrogate pairs, without a hidden per-text cap.
        ObjectNode root;
        try { root = StrictJson.object(JSON.readTree(raw), Set.of("schema", "observation", "joint_budget_request", "intents", "external_facts")); }
        catch (IOException failure) { throw new IllegalArgumentException("invalid lifecycle JSON", failure); }
        StrictJson.require(REQUEST_SCHEMA.equals(text(root, "schema")), "exact proposal lifecycle schema required");
        JointBudgetSelector.Input evaluation = JointBudgetCodec.decode(encodeJson(root.get("joint_budget_request"), StrictJson.INPUT_MAX_BYTES));
        var frame = switch (evaluation) {
            case JointBudgetSelector.AssessedInput value -> value.intake().frame();
            case JointBudgetSelector.MissingAssessments value -> value.intake().frame();
        };
        ObjectNode observation = StrictJson.object(root.get("observation"), Set.of("game", "observation_version"));
        var generation = GameGeneration.fromJson(observation.get("game"));
        ObservationIdentity observed = new ObservationIdentity(source.machineId(), generation, frame,
                StrictJson.integer(observation.get("observation_version"), 1, StrictJson.MAX_SAFE_INTEGER));
        List<CandidateIntent> intents = new ArrayList<>();
        for (JsonNode value : array(root.get("intents"))) {
            ObjectNode row = StrictJson.object(value, Set.of("action_id", "candidate_id", "expected"));
            ObjectNode expected = StrictJson.object(row.get("expected"), Set.of("version", "observer_schema", "values"));
            intents.add(new CandidateIntent(text(row, "action_id"), text(row, "candidate_id"), new ExpectedPostcondition(
                    Math.toIntExact(StrictJson.integer(expected.get("version"), 1, 1)), observed, source, text(expected, "observer_schema"), values(expected.get("values")))));
        }
        List<ExternalFact> facts = new ArrayList<>();
        for (JsonNode value : array(root.get("external_facts"))) {
            facts.add(decodeFact(value));
        }
        return new Input(observed, source, evaluation, intents, facts);
    }
    public static Plan evaluate(byte[] payload, G2Source source) {
        return evaluate(decode(payload, source));
    }
    public static Plan evaluate(Input input) { return ProposalLifecycle.plan(input, ProposalLifecycleCodec::bodyDigest); }
    public static byte[] evaluateG2Payload(byte[] payload, G2Source source) {
        Input input = decode(payload, source);
        RequestBodyEncoding encoding = new RequestBodyEncoding();
        Plan plan = ProposalLifecycle.plan(input, encoding::digest);
        return encode(plan, encoding::verifiedBody);
    }
    public static byte[] encode(Plan value) {
        return encode(value, action -> verifiedBody(action, encodeBody(action.body())));
    }
    @FunctionalInterface private interface ProposedBodyEncoding { ObjectNode encode(ProposedAction action); }
    private static byte[] encode(Plan value, ProposedBodyEncoding proposedBodyEncoding) {
        ObjectNode row = StrictJson.object(); row.put("schema", RESULT_SCHEMA); row.set("evaluation", StrictJson.parse(JointBudgetCodec.encode(value.evaluation())));
        row.put("formal_action_ready", false); row.put("resource_reservation_performed", false); row.put("intent_durable", false);
        row.putNull("proposal"); row.putNull("deferred_reason"); row.putNull("body_conflict"); row.putArray("blocking_facts");
        switch (value) {
            case Proposed proposed -> {
                row.put("status", "PROPOSED"); ObjectNode action = row.putObject("proposal"); action.set("body", proposedBodyEncoding.encode(proposed.action())); action.put("body_sha256", proposed.action().bodySha256()); action.put("dispatch_allowed", false);
            }
            case Deferred deferred -> {
                row.put("status", "DEFERRED"); row.put("deferred_reason", deferred.reason().name()); ArrayNode facts = (ArrayNode) row.get("blocking_facts"); deferred.blockingFacts().forEach(fact -> facts.add(fact(fact)));
            }
            case Conflict conflict -> {
                row.put("status", "BODY_CONFLICT"); ObjectNode detail = row.putObject("body_conflict"); detail.put("action_id", conflict.actionId()); detail.put("prior_body_sha256", conflict.priorBodySha256()); detail.put("proposed_body_sha256", conflict.proposedBodySha256());
            }
        }
        return encodeJson(row, MAX_BYTES);
    }
    public static String bodyDigest(ProposedBody value) { return encodeBody(value).digest(); }

    /** Private, request-local JSON; neither this tree nor its reuse scope escapes the producer. */
    private record EncodedBody(ProposedBody original, ObjectNode json, String digest) { }
    private static EncodedBody encodeBody(ProposedBody value) {
        ObjectNode json = body(value);
        return new EncodedBody(value, json, sha256(encodeJson(json, MAX_BYTES)));
    }
    private static ObjectNode verifiedBody(ProposedAction action, EncodedBody encoded) {
        StrictJson.require(encoded.digest().equals(action.bodySha256()), "proposal body SHA differs from its complete canonical body");
        return encoded.json();
    }
    /**
     * The exact immutable ProposedBody retains observation, source, candidate and expected post-state.
     * Each public producer invocation creates a new scope, so facts, actions and later requests always
     * run the full planner again. This reuses only its canonical body while encoding that same result.
     */
    private static final class RequestBodyEncoding {
        private EncodedBody encoded;
        private EncodedBody canonical(ProposedBody value) {
            if (encoded == null || encoded.original() != value) encoded = encodeBody(value);
            return encoded;
        }
        private String digest(ProposedBody value) { return canonical(value).digest(); }
        private ObjectNode verifiedBody(ProposedAction action) {
            return ProposalLifecycleCodec.verifiedBody(action, canonical(action.body()));
        }
    }
    /** Sorted-key compact UTF-8 for this explicit role. Jackson renders JSON; ProjectionJson validates complete strings and bytes. */
    public static byte[] encodePayload(ObjectNode value) { return encodeJson(value, MAX_BYTES); }
    /** Named callers must provide their own envelope cap; existing lifecycle defaults stay unchanged. */
    public static byte[] encodePayload(ObjectNode value, int maximumBytes) {
        StrictJson.require(maximumBytes > 0 && maximumBytes <= ProjectionJson.MAX_BYTES, "explicit lifecycle-derived payload role cap required");
        return encodeJson(value, maximumBytes);
    }
    public static ObjectNode decodePayload(byte[] raw, int maximumBytes) {
        ProjectionJson.object(raw, maximumBytes);
        try {
            JsonNode parsed = JSON.readTree(raw); StrictJson.require(parsed instanceof ObjectNode, "lifecycle-derived payload object required");
            return (ObjectNode) parsed;
        } catch (IOException failure) { throw new IllegalArgumentException("lifecycle-derived payload decoding failed", failure); }
    }
    public static ObjectNode body(ProposedBody value) {
        ObjectNode row = StrictJson.object(); row.put("action_id", value.actionId()); row.set("observed", observation(value.observed())); row.set("source", source(value.source()));
        JointBudgetSelector.Result one = new JointBudgetSelector.Result(JointBudgetSelector.Status.SELECTED, value.observed().frame().identity(), 0, List.of(value.candidate()), value.candidate().candidateId());
        // Reuse the original selector's sole result encoder; do not copy its evaluated-row field contract.
        row.set("evaluated_candidate", StrictJson.parse(JointBudgetCodec.encode(one))); row.set("expected", expected(value.expected())); return row;
    }
    public static ObjectNode observation(ObservationIdentity value) {
        ObjectNode row = StrictJson.object(); row.put("machine_id", value.machineId()); row.set("game", value.game().toJson()); row.put("observation_version", value.observationVersion());
        var frame = value.frame(); ObjectNode current = row.putObject("frame"); current.put("played_character_id", frame.identity().player().toString()); current.put("native_revision", frame.identity().nativeRevision().toString());
        current.put("date_raw", frame.identity().dateRaw().toString()); current.put("snapshot_id", frame.snapshotId()); current.put("revision", new org.xar.ck3.control.contracts.PublicRevision(frame.revision()).canonical()); current.put("episode_run_id", frame.episodeRunId()); return row;
    }
    public static ObservationIdentity decodeObservation(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("machine_id", "game", "observation_version", "frame"));
        ObjectNode frame = StrictJson.object(row.get("frame"), Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id"));
        var identity = new JointBudgetSelector.Frame(signedCharacterDecimal(frame, "played_character_id"), decimalUInt64(frame, "native_revision", true), decimalUInt64(frame, "date_raw", false));
        var full = new JointBudgetSelector.ProposalFrame(identity, text(frame, "snapshot_id"), org.xar.ck3.control.contracts.PublicRevision.decimal(text(frame, "revision")).value(), text(frame, "episode_run_id"));
        return new ObservationIdentity(text(row, "machine_id"), GameGeneration.fromJson(row.get("game")), full,
                StrictJson.integer(row.get("observation_version"), 1, StrictJson.MAX_SAFE_INTEGER));
    }
    public static ObjectNode source(G2Source value) {
        JsonNode encoded = StrictJson.parse(G2Wire.sourceBytes(value));
        if (encoded instanceof ObjectNode object) return object;
        throw new IllegalArgumentException("shared G2 source encoder must return an object");
    }
    public static ObjectNode expected(ExpectedPostcondition value) {
        ObjectNode row = StrictJson.object(); row.put("version", value.version()); row.set("before", observation(value.before())); row.set("source", source(value.source())); row.put("observer_schema", value.observerSchema());
        ArrayNode values = row.putArray("values"); value.values().forEach(item -> values.add(value(item))); return row;
    }
    public static ArrayNode encodeValues(List<ExpectedValue> expected) {
        ArrayNode values = StrictJson.object().putArray("values"); List.copyOf(expected).forEach(item -> values.add(value(item))); return values;
    }
    private static ObjectNode value(ExpectedValue expected) {
        ObjectNode row = StrictJson.object(); row.put("field", expected.field().value());
        switch (expected) {
            case ExpectedBoolean typed -> { row.put("kind", "BOOLEAN"); row.put("value", typed.value()); }
            case ExpectedInteger typed -> { row.put("kind", "INTEGER"); row.put("value", typed.value()); }
            case ExpectedText typed -> { row.put("kind", "TEXT"); row.put("value", typed.value()); }
            case ExpectedNull ignored -> { row.put("kind", "NULL"); row.putNull("value"); }
            case ExpectedAbsent ignored -> row.put("kind", "ABSENT");
        }
        return row;
    }
    public static List<ExpectedValue> values(JsonNode node) {
        List<ExpectedValue> values = new ArrayList<>();
        for (JsonNode value : array(node)) {
            if (!(value instanceof ObjectNode row)) throw new IllegalArgumentException("expected value object required");
            String kind = text(row, "kind");
            StrictJson.object(row, kind.equals("ABSENT") ? Set.of("field", "kind") : Set.of("field", "kind", "value")); FieldKey field = new FieldKey(text(row, "field"));
            values.add(switch (kind) {
                case "BOOLEAN" -> { StrictJson.require(row.get("value").isBoolean(), "actual boolean required"); yield new ExpectedBoolean(field, row.get("value").booleanValue()); }
                case "INTEGER" -> { StrictJson.require(row.get("value").isIntegralNumber(), "actual integer required"); yield new ExpectedInteger(field, row.get("value").bigIntegerValue()); }
                case "TEXT" -> { StrictJson.require(row.get("value").isTextual(), "actual text required"); yield new ExpectedText(field, row.get("value").textValue()); }
                case "NULL" -> { StrictJson.require(row.get("value").isNull(), "explicit null required"); yield new ExpectedNull(field); }
                case "ABSENT" -> new ExpectedAbsent(field);
                default -> throw new IllegalArgumentException("unsupported expected value kind");
            });
        }
        return List.copyOf(values);
    }
    public static ObjectNode fact(ExternalFact value) {
        ObjectNode row = StrictJson.object(); row.put("schema", FACT_SCHEMA); row.put("action_id", value.actionId()); row.put("body_sha256", value.bodySha256()); row.set("origin", observation(value.origin())); row.put("state", value.state().name()); row.put("scope", value.scope().name()); row.put("domain", value.domain().name());
        row.set("claims", claims(value.affectedClaims())); row.set("original_evidence_ref", value.originalEvidenceRef().toJson()); return row;
    }
    public static ExternalFact decodeFact(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("schema", "action_id", "body_sha256", "origin", "state", "scope", "domain", "claims", "original_evidence_ref"));
        StrictJson.require(FACT_SCHEMA.equals(text(row, "schema")), "exact current external fact v2 schema required");
        return decodeFactFields(row);
    }
    /** Strict historical reader for the original unversioned v1 shape; it cannot represent a confirmed send. */
    public static ExternalFact decodeHistoricalFactV1(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("action_id", "body_sha256", "origin", "state", "scope", "domain", "claims", "original_evidence_ref"));
        ExternalFact fact = decodeFactFields(row);
        StrictJson.require(fact.state() != ExternalState.SEND_CONFIRMED, "historical external fact v1 cannot represent SEND_CONFIRMED");
        return fact;
    }
    private static ExternalFact decodeFactFields(ObjectNode row) {
        return new ExternalFact(text(row, "action_id"), text(row, "body_sha256"), decodeObservation(row.get("origin")), externalState(text(row, "state")), UnknownScope.valueOf(text(row, "scope")),
                Domain.valueOf(text(row, "domain")), claims(row.get("claims")), ExactRef.fromJson(row.get("original_evidence_ref")));
    }
    private static ExternalState externalState(String value) {
        return switch (value) {
            case "UNKNOWN" -> ExternalState.UNKNOWN;
            case "ACK_RECEIVED" -> ExternalState.ACK_RECEIVED;
            case "APPLIED_CONFIRMED" -> ExternalState.APPLIED_CONFIRMED;
            case "SEND_CONFIRMED" -> ExternalState.SEND_CONFIRMED;
            case "REJECTED_CONFIRMED" -> ExternalState.REJECTED_CONFIRMED;
            case "TERMINAL_WITHOUT_EFFECT" -> ExternalState.TERMINAL_WITHOUT_EFFECT;
            default -> throw new IllegalArgumentException("unsupported exact external action state");
        };
    }
    private static ObjectNode claims(Claims value) {
        ObjectNode row = StrictJson.object(); numeric(row.putArray("army_ids"), value.armyIds()); numeric(row.putArray("ally_character_ids"), value.allyCharacterIds()); numeric(row.putArray("character_ids"), value.characterIds());
        ArrayNode keys = row.putArray("commitment_keys"); value.commitmentKeys().stream().sorted(JointBudgetSelector::comparePythonText).forEach(keys::add); return row;
    }
    private static Claims claims(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("army_ids", "ally_character_ids", "character_ids", "commitment_keys")); Set<String> keys = new HashSet<>();
        for (JsonNode key : array(row.get("commitment_keys"))) StrictJson.require(keys.add(StrictJson.text(key)), "duplicate resource key");
        return new Claims(numbers(row.get("army_ids"), false), numbers(row.get("ally_character_ids"), true), numbers(row.get("character_ids"), true), keys);
    }
    private static Set<BigInteger> numbers(JsonNode node, boolean positive) {
        Set<BigInteger> values = new HashSet<>(); for (JsonNode value : array(node)) {
            StrictJson.require(value.isIntegralNumber() && value.bigIntegerValue().signum() >= (positive ? 1 : 0), "exact resource integer required"); StrictJson.require(values.add(value.bigIntegerValue()), "duplicate resource integer");
        } return values;
    }
    private static void numeric(ArrayNode target, Set<BigInteger> values) { values.stream().sorted().forEach(target::add); }
    private static byte[] encodeJson(JsonNode value, int maximumBytes) {
        try {
            // Jackson's byte generator escapes supplementary characters as twelve ASCII bytes. The character generator retains the pair;
            // strict UTF-8 encoding then keeps its actual four-byte representation without replacing malformed UTF-16.
            var encoded = StandardCharsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
                    .encode(CharBuffer.wrap(JSON.writeValueAsString(ordered(value))));
            byte[] raw = new byte[encoded.remaining()]; encoded.get(raw);
            return ProjectionJson.value(raw, maximumBytes).bytes();
        }
        catch (IOException failure) { throw new IllegalArgumentException("lifecycle JSON encoding failed", failure); }
    }
    private static JsonNode ordered(JsonNode value) {
        StrictJson.require(value != null, "missing node is not explicit JSON null");
        if (value.isObject()) {
            ObjectNode result = StrictJson.object(); Set<String> names = new TreeSet<>(); value.fieldNames().forEachRemaining(names::add);
            names.forEach(name -> result.set(name, ordered(value.get(name)))); return result;
        }
        if (value.isArray()) { ArrayNode result = JSON.createArrayNode(); value.forEach(item -> result.add(ordered(item))); return result; }
        if (value.isDouble() || value.isFloat()) StrictJson.require(Double.isFinite(value.doubleValue()), "non-finite values are not JSON numbers");
        // readTree may strip BigDecimal trailing zeroes. Preserve the floating token domain when forwarding the unchanged legacy budget boundary.
        if (value.isBigDecimal() && value.decimalValue().scale() <= 0) return DecimalNode.valueOf(value.decimalValue().setScale(1));
        StrictJson.require(value.isTextual() || value.isNumber() || value.isBoolean() || value.isNull(), "JSON data node required"); return value;
    }
    /** This persistent observation field has always been canonical decimal text; native/request IDs remain JSON integers. */
    private static BigInteger signedCharacterDecimal(ObjectNode row, String field) {
        String raw = text(row, field);
        StrictJson.require(raw.matches("0|-?[1-9][0-9]{0,9}"), "canonical signed-i32 character decimal text required");
        return org.xar.ck3.control.contracts.NativeCharacterId.of(new BigInteger(raw)).asBigInteger();
    }
    private static BigInteger decimalUInt64(ObjectNode row, String field, boolean positive) {
        BigInteger value = new BigInteger(new CrossJsDecimalUInt64(text(row, field)).decimal());
        StrictJson.require(!positive || value.signum() > 0, "positive decimal identity required"); return value;
    }
    private static ArrayNode array(JsonNode value) { StrictJson.require(value instanceof ArrayNode, "exact array required"); return (ArrayNode) value; }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static String sha256(byte[] raw) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
}
