package org.xar.ck3.control.wave3.governance.focusread;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.EnumSet;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.Field;
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScope.NativeSourceFrame;
import org.xar.ck3.control.wave3.governance.focusread.FocusReadPolicy.*;

/** Runtime validation precedes typed construction; unknown progress JSON is opaque and immutable. */
public final class FocusReadCodec {
    public static final String SCHEMA = "xar.java.focus-read.v1";
    public static final int MAX_BYTES = 65_536;
    private static final int RESPONSE_MAX_BYTES = 32_768;
    private static final ObjectMapper OUTPUT = new ObjectMapper();
    private static final JsonMapper ORIGINAL = JsonMapper.builder()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private FocusReadCodec() { }
    public sealed interface Request permits ParseRequest, CompleteQueryRequest, ResearchRequest { Input input(); }
    public record ParseRequest(Input input) implements Request { public ParseRequest { Objects.requireNonNull(input); } }
    public record ResearchRequest(Input input) implements Request { public ResearchRequest { Objects.requireNonNull(input); } }
    public record PostRead(BigInteger startingPublicRevision, BigInteger endingPublicRevision, Boolean endingMapReady) {
        public PostRead { StrictJson.require(startingPublicRevision != null && startingPublicRevision.signum() > 0, "completed query needs its original positive public revision"); }
    }
    public record CompleteQueryRequest(Input input, PostRead after) implements Request {
        public CompleteQueryRequest { Objects.requireNonNull(input); Objects.requireNonNull(after); }
    }
    public static Request decode(byte[] raw) {
        JsonNode node = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("schema", "operation", "target", "expected_request_id",
                "source_frame", "independent_after_frame", "response_json", "post_read"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(node.get("schema"))), "fixed focus read schema required");
        Target target = switch (StrictJson.text(node.get("target"))) {
            case "wealth" -> Target.WEALTH; case "martial" -> Target.MARTIAL;
            default -> throw new ContractViolationException("only the two actual fixed-focus parser consumers are supported");
        };
        String original = StrictJson.text(node.get("response_json"));
        Input input = new Input(target, textOrNull(node.get("expected_request_id")), frame(node.get("source_frame")),
                frame(node.get("independent_after_frame")), response(original.getBytes(StandardCharsets.UTF_8)));
        return switch (StrictJson.text(node.get("operation"))) {
            case "parse" -> { StrictJson.require(node.get("post_read").isNull(), "parse requires explicit null post_read"); yield new ParseRequest(input); }
            case "research_after_parser" -> { StrictJson.require(node.get("post_read").isNull(), "research projection requires null post_read"); yield new ResearchRequest(input); }
            case "complete_query" -> {
                JsonNode post = StrictJson.object(node.get("post_read"), Set.of("starting_public_revision", "ending_public_revision", "ending_map_ready"));
                yield new CompleteQueryRequest(input, new PostRead(integerOrNull(post.get("starting_public_revision")),
                        integerOrNull(post.get("ending_public_revision")), boolOrNull(post.get("ending_map_ready"))));
            }
            default -> throw new ContractViolationException("unknown fixed focus operation");
        };
    }
    private static NativeSourceFrame frame(JsonNode node) {
        StrictJson.require(node != null && node.isObject(), "declared frame projection required");
        return new NativeSourceFrame(textOrNull(node.get("snapshot_id")), textOrNull(node.get("episode_run_id")),
                integerOrNull(node.get("native_revision")), integerOrNull(node.get("date_raw")), integerOrNull(node.get("played_character_id")), boolOrNull(node.get("paused")));
    }
    public static ResponseEvidence response(byte[] raw) {
        StrictJson.parse(raw, RESPONSE_MAX_BYTES);
        JsonNode node;
        try { node = ORIGINAL.readTree(raw); }
        catch (IOException error) { throw new ContractViolationException("invalid original focus response", error); }
        validateOriginal(node, 0); Response value = null;
        if (node.isObject()) {
            JsonNode result = node.get("result");
            value = new Response(textOrNull(node.get("type")), integerOrNull(node.get("protocol_version")), textOrNull(node.get("request_id")),
                    boolOrNull(node.get("ok")), result != null && result.isObject() ? result(result) : null);
        }
        return new ResponseEvidence(new RawJson(raw), value);
    }
    private static void validateOriginal(JsonNode node, int depth) {
        StrictJson.require(depth <= 128, "bounded native response nesting required");
        if (node.isTextual()) { if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); } }
        else if (node.isObject()) {
            node.fieldNames().forEachRemaining(key -> { if (!key.isEmpty()) { StrictJson.text(key); } });
            node.elements().forEachRemaining(value -> validateOriginal(value, depth + 1));
        } else if (node.isArray()) { node.forEach(value -> validateOriginal(value, depth + 1)); }
        else { StrictJson.require(node.isNull() || node.isBoolean() || node.isIntegralNumber() || node.isFloatingPointNumber(), "original JSON value required"); }
    }
    private static NativeResult result(JsonNode node) {
        return new NativeResult(textOrNull(node.get("step")), boolOrNull(node.get("private_build")), boolOrNull(node.get("advertised")),
                boolOrNull(node.get("read_only")), boolOrNull(node.get("policy_scoped")), textOrNull(node.get("snapshot_id")),
                textOrNull(node.get("episode_run_id")), textOrNull(node.get("target_key")), textOrNull(node.get("status")),
                field(node, "native_legal", FocusReadCodec::bool), integerOrNull(node.get("scanned_database_rows")),
                textOrNull(node.get("target_lifestyle_key")), field(node, "target_lifestyle_progress", FocusReadCodec::progress));
    }
    private static ProgressSource progress(JsonNode node) {
        StrictJson.require(node.isObject(), "target progress must be an object or unavailable/null field");
        Set<ProgressNumber> invalid = EnumSet.noneOf(ProgressNumber.class);
        for (ProgressNumber number : ProgressNumber.values()) {
            JsonNode value = node.get(number.wire());
            if (value != null && !value.isNull() && !value.isIntegralNumber()) { invalid.add(number); }
        }
        if (!invalid.isEmpty()) {
            return new InvalidProgress(textOrNull(node.get("presence")), textOrNull(node.get("source")),
                    textOrNull(node.get("reason")), invalid, new RawJson(write(node, RESPONSE_MAX_BYTES)));
        }
        return new Progress(textOrNull(node.get("presence")), textOrNull(node.get("source")), textOrNull(node.get("reason")),
                field(node, "xp_total_raw", FocusReadCodec::integer), field(node, "xp_within_level_raw", FocusReadCodec::integer),
                field(node, "xp_per_level", FocusReadCodec::integer), field(node, "unspent_perk_points", FocusReadCodec::integer),
                field(node, "used_perk_points", FocusReadCodec::integer), new RawJson(write(node, RESPONSE_MAX_BYTES)));
    }
    private static <T> Field<T> field(JsonNode node, String key, Function<JsonNode, T> parser) {
        JsonNode value = node.get(key); return value == null ? Field.missing() : value.isNull() ? Field.nullValue() : Field.of(parser.apply(value));
    }
    private static String textOrNull(JsonNode node) {
        if (node == null || node.isNull()) { return null; }
        StrictJson.require(node.isTextual(), "actual JSON string required"); String value = node.textValue();
        if (!value.isEmpty()) { StrictJson.text(value); } return value;
    }
    private static BigInteger integerOrNull(JsonNode node) { return node == null || node.isNull() ? null : integer(node); }
    private static BigInteger integer(JsonNode node) {
        StrictJson.require(node.isIntegralNumber(), "actual integer token required, bool/float/string rejected"); return node.bigIntegerValue();
    }
    private static Boolean boolOrNull(JsonNode node) { return node == null || node.isNull() ? null : bool(node); }
    private static Boolean bool(JsonNode node) { StrictJson.require(node.isBoolean(), "actual JSON boolean required"); return node.booleanValue(); }
    public static byte[] encode(Request request) {
        ObjectNode node = StrictJson.object(); Input input = request.input(); node.put("schema", SCHEMA);
        node.put("operation", request instanceof CompleteQueryRequest ? "complete_query" : request instanceof ResearchRequest ? "research_after_parser" : "parse");
        node.put("target", input.target().name().toLowerCase(java.util.Locale.ROOT)); node.put("expected_request_id", input.expectedRequestId());
        node.set("source_frame", frameNode(input.sourceFrame(), true)); node.set("independent_after_frame", frameNode(input.independentAfterFrame(), true));
        node.put("response_json", new String(input.response().original().bytes(), StandardCharsets.UTF_8));
        if (request instanceof CompleteQueryRequest complete) {
            ObjectNode post = StrictJson.object(); post.put("starting_public_revision", complete.after().startingPublicRevision());
            post.put("ending_public_revision", complete.after().endingPublicRevision());
            if (complete.after().endingMapReady() == null) { post.putNull("ending_map_ready"); } else { post.put("ending_map_ready", complete.after().endingMapReady()); }
            node.set("post_read", post);
        } else { node.putNull("post_read"); }
        return StrictJson.canonical(node, MAX_BYTES);
    }
    public sealed interface Evaluation permits ParsedEvaluation, CompletedEvaluation, ResearchEvaluation { }
    public record ParsedEvaluation(Outcome outcome) implements Evaluation {
        public ParsedEvaluation { Objects.requireNonNull(outcome); }
    }
    public record CompletedEvaluation(Outcome outcome, Target target, String requestId) implements Evaluation {
        public CompletedEvaluation { Objects.requireNonNull(outcome); Objects.requireNonNull(target); }
    }
    public record ResearchEvaluation(ResearchView view) implements Evaluation {
        public ResearchEvaluation { Objects.requireNonNull(view); }
    }
    /** The shared host decodes first; only typed policy execution occurs in project. */
    public static Evaluation project(Request request) {
        Objects.requireNonNull(request); Outcome outcome = FocusReadPolicy.parse(request.input());
        if (request instanceof ResearchRequest) {
            Response response = request.input().response().response();
            String nativeStatus = response == null || response.result() == null ? null : response.result().status();
            return new ResearchEvaluation(FocusReadPolicy.researchAfterParser(outcome, nativeStatus));
        }
        if (request instanceof CompleteQueryRequest complete) {
            outcome = FocusReadPolicy.finishQuery(outcome, complete.after().startingPublicRevision(),
                    complete.after().endingPublicRevision(), complete.after().endingMapReady());
            return new CompletedEvaluation(outcome, request.input().target(), request.input().expectedRequestId());
        }
        return new ParsedEvaluation(outcome);
    }
    public static byte[] encode(Evaluation evaluation) {
        return switch (evaluation) {
            case ParsedEvaluation parsed -> encode(parsed.outcome());
            case ResearchEvaluation research -> encodeResearch(research.view());
            case CompletedEvaluation complete -> {
                ObjectNode node = outcomeNode(complete.outcome());
                if (!(complete.outcome() instanceof Red red && red.issue() == Issue.PAUSED_FOCUS_PUBLIC_FRAME_DRIFT)) {
                    node.put("step", complete.target().step()); node.put("request_id", complete.requestId());
                }
                yield write(node, MAX_BYTES);
            }
        };
    }
    public static byte[] evaluate(byte[] raw) { return encode(project(decode(raw))); }
    public static byte[] encode(Outcome outcome) { return write(outcomeNode(outcome), MAX_BYTES); }
    public static byte[] encodeResearch(ResearchView view) {
        ObjectNode node = StrictJson.object(); node.put("status", view.status().name().toLowerCase(java.util.Locale.ROOT));
        node.put("native_status", view.nativeStatus());
        if (view.basis() != null) { node.put("basis", view.basis()); }
        if (view.issue() != null) { node.put("issue", view.issue().wire()); }
        if (view.progress() != null) { node.set("target_lifestyle_progress", StrictJson.parse(view.progress().bytes(), RESPONSE_MAX_BYTES)); }
        return write(node, MAX_BYTES);
    }
    public static ObjectNode outcomeNode(Outcome outcome) {
        ObjectNode node = StrictJson.object();
        switch (outcome) {
            case Red red -> { node.put("status", "red"); node.put("issue", red.issue().wire()); if (red.nativeStatus() != null) { node.put("native_status", red.nativeStatus()); } }
            case ProgressUnavailable unavailable -> {
                node.put("status", "target_progress_unavailable"); node.put("native_legal", unavailable.nativeLegal());
                node.put("target_key", unavailable.target().key()); node.put("target_lifestyle_key", unavailable.target().lifestyle());
            }
            case Observed observed -> {
                node.put("status", "observed"); node.put("native_legal", observed.nativeLegal());
                node.put("target_key", observed.target().key()); node.put("target_lifestyle_key", observed.target().lifestyle());
                node.set("target_lifestyle_progress", StrictJson.parse(observed.originalProgress().bytes(), RESPONSE_MAX_BYTES));
                node.set("source_frame", frameNode(observed.sourceFrame(), false));
            }
        }
        return node;
    }
    private static ObjectNode frameNode(NativeSourceFrame frame, boolean paused) {
        ObjectNode node = StrictJson.object(); node.put("snapshot_id", frame.snapshotId()); node.put("native_revision", frame.nativeRevision());
        node.put("date_raw", frame.dateRaw()); node.put("played_character_id", frame.controllerFullId()); node.put("episode_run_id", frame.episodeRunId());
        if (paused) { if (frame.paused() == null) { node.putNull("paused"); } else { node.put("paused", frame.paused()); } }
        return node;
    }
    private static byte[] write(JsonNode node, int maximum) {
        // Only the declared opaque original progress object can contain decimal JSON numbers.
        try { byte[] raw = OUTPUT.writeValueAsBytes(node); StrictJson.require(raw.length <= maximum, "fixed focus output byte budget"); return raw; }
        catch (IOException error) { throw new ContractViolationException("unable to encode retained progress JSON", error); }
    }
}
