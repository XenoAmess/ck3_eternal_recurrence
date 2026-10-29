package org.xar.ck3.control.wave2.governance.focusscope;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScope.*;

/** Strict new envelopes plus declared projections of extensible native query/snapshot containers. */
public final class EducationFocusScopeCodec {
    public static final String SCHEMA = "xar.java.education-focus-scope.v1";
    private static final Set<String> FRAME_KEYS = Set.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id",
            "paused", "map_ready", "player_character_id", "actor_alive");
    private static final Set<String> SOURCE_KEYS = Set.of("snapshot_id", "episode_run_id", "native_revision", "date_raw", "controller_full_id", "paused");
    private static final Set<String> CONTEXT_KEYS = Set.of("snapshot_id", "episode_run_id", "native_revision", "date_raw", "controller_full_id", "paused",
            "public_revision", "exact_ck3_build", "exe_sha256");
    private EducationFocusScopeCodec() { }
    public sealed interface Request permits QualifyRequest, ProjectRequest, CombineRequest, FormalRequest, OpeningRequest { }
    public record QualifyRequest(Query query, Frame frame, BigInteger expectedRevision) implements Request { }
    public record ProjectRequest(SemanticSnapshot snapshot) implements Request { public ProjectRequest { Objects.requireNonNull(snapshot); } }
    public record CombineRequest(StateQuery state, Frame before, Frame after, Query query, BigInteger expectedRevision) implements Request { }
    public record FormalRequest(RetainedCombined evidence, FormalScope scope) implements Request { }
    public record OpeningRequest(OpeningInput input) implements Request { }

    public sealed interface Result permits FrameResult, QualificationResult, CombinedResult { }
    public record FrameResult(Frame frame) implements Result { public FrameResult { Objects.requireNonNull(frame); } }
    public record QualificationResult(Qualification qualification) implements Result { public QualificationResult { Objects.requireNonNull(qualification); } }
    public record CombinedResult(CombinedDecision combined) implements Result { public CombinedResult { Objects.requireNonNull(combined); } }

    public static Request decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "operation", "input"));
        StrictJson.require(SCHEMA.equals(text(root.get("schema"))), "education focus scope schema mismatch");
        ObjectNode input = object(root.get("input"));
        return switch (text(root.get("operation"))) {
            case "qualify" -> {
                StrictJson.object(input, Set.of("query", "frame", "expected_revision"));
                yield new QualifyRequest(nullable(input.get("query"), EducationFocusScopeCodec::query),
                        nullable(input.get("frame"), EducationFocusScopeCodec::frame), nullableInteger(input.get("expected_revision")));
            }
            case "project" -> {
                StrictJson.object(input, Set.of("snapshot")); yield new ProjectRequest(snapshot(input.get("snapshot")));
            }
            case "combine" -> {
                StrictJson.object(input, Set.of("state", "before", "after", "query", "expected_revision"));
                yield new CombineRequest(nullable(input.get("state"), EducationFocusScopeCodec::state), nullable(input.get("before"), EducationFocusScopeCodec::frame),
                        nullable(input.get("after"), EducationFocusScopeCodec::frame), nullable(input.get("query"), EducationFocusScopeCodec::query),
                        nullableInteger(input.get("expected_revision")));
            }
            case "formal" -> {
                StrictJson.object(input, Set.of("combined", "scope"));
                yield new FormalRequest(nullable(input.get("combined"), EducationFocusScopeCodec::retained), nullable(input.get("scope"), EducationFocusScopeCodec::scope));
            }
            case "opening" -> {
                StrictJson.object(input, Set.of("combined", "before", "after", "expected_revision", "formal", "pending_action"));
                yield new OpeningRequest(new OpeningInput(nullable(input.get("combined"), EducationFocusScopeCodec::retained),
                        nullable(input.get("before"), EducationFocusScopeCodec::frame), nullable(input.get("after"), EducationFocusScopeCodec::frame),
                        nullableInteger(input.get("expected_revision")), nullable(input.get("formal"), EducationFocusScopeCodec::state),
                        nullable(input.get("pending_action"), value -> {
                            ObjectNode pending = object(value); return new PendingAction(optionalText(pending, "action_request_id"), optionalText(pending, "status"));
                        })));
            }
            default -> throw new ContractViolationException("unknown education focus scope operation");
        };
    }

    public static byte[] evaluate(byte[] raw) { return encodeResult(execute(decode(raw))); }
    /** Domain execution is separate from transport decode and serialization. */
    public static Result execute(Request request) {
        Objects.requireNonNull(request);
        return switch (request) {
            case QualifyRequest qualify -> new QualificationResult(EducationFocusScope.qualify(qualify.query(), qualify.frame(), qualify.expectedRevision()));
            case ProjectRequest project -> new FrameResult(EducationFocusScope.project(project.snapshot()));
            case CombineRequest combine -> new CombinedResult(EducationFocusScope.combine(combine.state(), combine.before(), combine.after(), combine.query(), combine.expectedRevision()));
            case FormalRequest formal -> new QualificationResult(EducationFocusScope.consumeFormal(formal.evidence(), formal.scope()));
            case OpeningRequest opening -> new QualificationResult(EducationFocusScope.consumeOpening(opening.input()));
        };
    }
    public static byte[] encodeResult(Result result) {
        Objects.requireNonNull(result);
        JsonNode output = switch (result) {
            case FrameResult frame -> frameNode(frame.frame());
            case QualificationResult qualification -> qualificationNode(qualification.qualification());
            case CombinedResult combined -> combinedNode(combined.combined());
        };
        return StrictJson.canonical(output);
    }
    public static byte[] encode(Request request) {
        ObjectNode root = StrictJson.object().put("schema", SCHEMA); ObjectNode input = root.putObject("input");
        switch (request) {
            case QualifyRequest qualify -> {
                root.put("operation", "qualify"); input.set("query", node(qualify.query(), EducationFocusScopeCodec::queryNode));
                input.set("frame", node(qualify.frame(), EducationFocusScopeCodec::frameNode)); input.set("expected_revision", integerNode(qualify.expectedRevision()));
            }
            case ProjectRequest project -> { root.put("operation", "project"); input.set("snapshot", snapshotNode(project.snapshot())); }
            case CombineRequest combine -> {
                root.put("operation", "combine"); input.set("state", node(combine.state(), EducationFocusScopeCodec::stateNode));
                input.set("before", node(combine.before(), EducationFocusScopeCodec::frameNode)); input.set("after", node(combine.after(), EducationFocusScopeCodec::frameNode));
                input.set("query", node(combine.query(), EducationFocusScopeCodec::queryNode)); input.set("expected_revision", integerNode(combine.expectedRevision()));
            }
            case FormalRequest formal -> { root.put("operation", "formal"); input.set("combined", node(formal.evidence(), EducationFocusScopeCodec::retainedNode));
                input.set("scope", node(formal.scope(), value -> StrictJson.object().put("status", value.status()).put("snapshot_revision", value.snapshotRevision()).put("player_character_id", value.playerCharacterId()))); }
            case OpeningRequest opening -> {
                root.put("operation", "opening"); OpeningInput value = opening.input();
                input.set("combined", node(value.combined(), EducationFocusScopeCodec::retainedNode)); input.set("before", node(value.before(), EducationFocusScopeCodec::frameNode));
                input.set("after", node(value.after(), EducationFocusScopeCodec::frameNode)); input.set("expected_revision", integerNode(value.expectedRevision()));
                input.set("formal", node(value.formal(), EducationFocusScopeCodec::stateNode));
                input.set("pending_action", node(value.pendingAction(), pending -> StrictJson.object().put("action_request_id", pending.actionRequestId()).put("status", pending.status())));
            }
        }
        return StrictJson.canonical(root);
    }

    public static Frame frame(JsonNode raw) {
        ObjectNode row = StrictJson.object(raw, FRAME_KEYS);
        return new Frame(nullableText(row.get("snapshot_id")), nullableInteger(row.get("revision")), nullableInteger(row.get("native_revision")),
                nullableInteger(row.get("date_raw")), nullableText(row.get("episode_run_id")), nullableBoolean(row.get("paused")),
                nullableBoolean(row.get("map_ready")), nullableInteger(row.get("player_character_id")), nullableBoolean(row.get("actor_alive")));
    }
    private static SemanticSnapshot snapshot(JsonNode raw) {
        ObjectNode row = object(raw); // Declared legacy SDK projection: unrelated native fields stay in original custody.
        PlayedCharacter played = nullable(row.get("played_character"), value -> { ObjectNode actor = object(value);
            return new PlayedCharacter(nullableInteger(actor.get("character_id")), nullableBoolean(actor.get("alive"))); });
        return new SemanticSnapshot(optionalText(row, "snapshot_id"), nullableInteger(row.get("revision")), nullableInteger(row.get("native_revision")),
                nullableInteger(row.get("date_raw")), optionalText(row, "episode_run_id"), nullableBoolean(row.get("paused")), nullableBoolean(row.get("map_ready")), played);
    }
    private static Query query(JsonNode raw) {
        ObjectNode row = object(raw); // native_legal and target-definition unavailability are deliberately not qualification inputs.
        return new Query(optionalText(row, "schema"), optionalText(row, "kind"), optionalText(row, "status"), nullableInteger(row.get("child_full_id")),
                optionalText(row, "target_key"), nullableInteger(row.get("source_public_revision")), nullable(row.get("source_frame"), EducationFocusScopeCodec::sourceFrame),
                nullable(row.get("source_context"), value -> { ObjectNode context = StrictJson.object(value, CONTEXT_KEYS);
                    return new SourceContext(sourceFrameProjection(context), nullableInteger(context.get("public_revision")), nullableText(context.get("exact_ck3_build")), nullableText(context.get("exe_sha256"))); }),
                optionalText(row, "request_id"), nullable(row.get("current_focus"), value -> {
                    ObjectNode focus = object(value);
                    StrictJson.require(focus.has("available") && focus.has("unavailable_reason") && focus.has("presence") && focus.has("key"), "current-focus consumed fields required");
                    return new CurrentFocus(nullableBoolean(focus.get("available")), nullableText(focus.get("unavailable_reason")), nullableText(focus.get("presence")), nullableText(focus.get("key")));
                }));
    }
    private static NativeSourceFrame sourceFrame(JsonNode raw) { return sourceFrameProjection(StrictJson.object(raw, SOURCE_KEYS)); }
    private static NativeSourceFrame sourceFrameProjection(ObjectNode row) {
        return new NativeSourceFrame(nullableText(row.get("snapshot_id")), nullableText(row.get("episode_run_id")), nullableInteger(row.get("native_revision")),
                nullableInteger(row.get("date_raw")), nullableInteger(row.get("controller_full_id")), nullableBoolean(row.get("paused")));
    }
    private static StateQuery state(JsonNode raw) { ObjectNode row = object(raw); return new StateQuery(optionalText(row, "status"), optionalText(row, "native_error")); }
    private static FormalScope scope(JsonNode raw) { ObjectNode row = object(raw); return new FormalScope(optionalText(row, "status"), nullableInteger(row.get("snapshot_revision")), nullableInteger(row.get("player_character_id"))); }
    private static RetainedCombined retained(JsonNode raw) {
        ObjectNode row = object(raw);
        return new RetainedCombined(optionalText(row, "status"), nullable(row.get("state"), EducationFocusScopeCodec::state),
                nullable(row.get("education_focus_source_frame"), EducationFocusScopeCodec::frame), nullable(row.get("education_focus_scope"), EducationFocusScopeCodec::fact),
                nullable(row.get("education_focus_query"), EducationFocusScopeCodec::query));
    }
    private static CurrentEducationFact fact(JsonNode raw) {
        ObjectNode row = StrictJson.object(raw, Set.of("status", "current_focus_key", "source_frame", "source_review", "age_observed", "lifestyle_action_legal"));
        StrictJson.require(EducationFocusScope.FACT_STATUS.equals(text(row.get("status"))) && Boolean.FALSE.equals(nullableBoolean(row.get("age_observed")))
                && row.get("lifestyle_action_legal").isNull(), "fact cannot claim age observation or action legality");
        FocusKey key = FocusKey.observed(text(row.get("current_focus_key"))).orElseThrow(() -> new ContractViolationException("unknown education focus fact"));
        ObjectNode review = StrictJson.object(row.get("source_review"), Set.of("definition_path", "definition_sha256", "definition_type", "reader", "reader_sha256"));
        return new CurrentEducationFact(key, frame(row.get("source_frame")), new SourceReview(text(review.get("definition_path")), text(review.get("definition_sha256")),
                text(review.get("definition_type")), text(review.get("reader")), text(review.get("reader_sha256"))));
    }

    public static JsonNode qualificationNode(Qualification qualification) {
        return qualification instanceof Qualified observed ? factNode(observed.fact()) : StrictJson.object().nullNode();
    }
    public static ObjectNode factNode(CurrentEducationFact fact) {
        ObjectNode row = StrictJson.object().put("status", EducationFocusScope.FACT_STATUS).put("current_focus_key", fact.currentFocus().wire())
                .put("age_observed", false).putNull("lifestyle_action_legal"); row.set("source_frame", frameNode(fact.sourceFrame()));
        SourceReview review = fact.sourceReview(); row.set("source_review", StrictJson.object().put("definition_path", review.definitionPath()).put("definition_sha256", review.definitionSha256())
                .put("definition_type", review.definitionType()).put("reader", review.reader()).put("reader_sha256", review.readerSha256())); return row;
    }
    public static ObjectNode frameNode(Frame value) {
        return StrictJson.object().put("snapshot_id", value.snapshotId()).put("revision", value.revision()).put("native_revision", value.nativeRevision())
                .put("date_raw", value.dateRaw()).put("episode_run_id", value.episodeRunId()).put("paused", value.paused()).put("map_ready", value.mapReady())
                .put("player_character_id", value.playerCharacterId()).put("actor_alive", value.actorAlive());
    }
    private static ObjectNode combinedNode(CombinedDecision combined) {
        ObjectNode row = StrictJson.object().put("status", combined.status().wire());
        combined.fact().ifPresent(value -> { row.set("education_focus_source_frame", frameNode(value.sourceFrame())); row.set("education_focus_scope", factNode(value)); }); return row;
    }
    private static ObjectNode sourceFrameNode(NativeSourceFrame value) {
        return StrictJson.object().put("snapshot_id", value.snapshotId()).put("episode_run_id", value.episodeRunId()).put("native_revision", value.nativeRevision())
                .put("date_raw", value.dateRaw()).put("controller_full_id", value.controllerFullId()).put("paused", value.paused());
    }
    private static ObjectNode queryNode(Query query) {
        ObjectNode row = StrictJson.object().put("schema", query.schema()).put("kind", query.kind()).put("status", query.status()).put("child_full_id", query.childFullId())
                .put("target_key", query.targetKey()).put("source_public_revision", query.sourcePublicRevision()).put("request_id", query.requestId());
        row.set("source_frame", node(query.sourceFrame(), EducationFocusScopeCodec::sourceFrameNode));
        row.set("source_context", node(query.sourceContext(), context -> sourceFrameNode(context.frame()).put("public_revision", context.publicRevision())
                .put("exact_ck3_build", context.exactBuild()).put("exe_sha256", context.executableSha256())));
        row.set("current_focus", node(query.currentFocus(), focus -> StrictJson.object().put("available", focus.available()).put("unavailable_reason", focus.unavailableReason())
                .put("presence", focus.presence()).put("key", focus.key()))); return row;
    }
    private static ObjectNode snapshotNode(SemanticSnapshot snapshot) {
        ObjectNode row = StrictJson.object().put("snapshot_id", snapshot.snapshotId()).put("revision", snapshot.revision()).put("native_revision", snapshot.nativeRevision())
                .put("date_raw", snapshot.dateRaw()).put("episode_run_id", snapshot.episodeRunId()).put("paused", snapshot.paused()).put("map_ready", snapshot.mapReady());
        row.set("played_character", node(snapshot.playedCharacter(), actor -> StrictJson.object().put("character_id", actor.characterId()).put("alive", actor.alive()))); return row;
    }
    private static ObjectNode stateNode(StateQuery value) { return StrictJson.object().put("status", value.status()).put("native_error", value.nativeError()); }
    private static ObjectNode retainedNode(RetainedCombined value) {
        ObjectNode row = StrictJson.object().put("status", value.status()); row.set("state", node(value.state(), EducationFocusScopeCodec::stateNode));
        row.set("education_focus_source_frame", node(value.sourceFrame(), EducationFocusScopeCodec::frameNode));
        row.set("education_focus_scope", node(value.retainedFact(), EducationFocusScopeCodec::factNode)); row.set("education_focus_query", node(value.educationQuery(), EducationFocusScopeCodec::queryNode)); return row;
    }
    private static ObjectNode object(JsonNode node) { StrictJson.require(node instanceof ObjectNode, "JSON object required"); return (ObjectNode) node; }
    private static String text(JsonNode node) { StrictJson.require(node != null && node.isTextual(), "actual string token required"); String value = node.textValue(); if (!value.isEmpty()) { StrictJson.text(value); } return value; }
    private static String nullableText(JsonNode node) { return node == null || node.isNull() ? null : text(node); }
    private static String optionalText(ObjectNode row, String key) { return nullableText(row.get(key)); }
    private static BigInteger nullableInteger(JsonNode node) {
        if (node == null || node.isNull()) { return null; }
        StrictJson.require(node.isIntegralNumber(), "actual integer token required, no bool/float/string coercion"); return node.bigIntegerValue();
    }
    private static Boolean nullableBoolean(JsonNode node) {
        if (node == null || node.isNull()) { return null; }
        StrictJson.require(node.isBoolean(), "actual boolean token required"); return node.booleanValue();
    }
    private static <T> T nullable(JsonNode node, Function<JsonNode, T> parse) { return node == null || node.isNull() ? null : parse.apply(node); }
    private static <T> JsonNode node(T value, Function<T, JsonNode> encode) { return value == null ? StrictJson.object().nullNode() : encode.apply(value); }
    private static JsonNode integerNode(BigInteger value) { return value == null ? StrictJson.object().nullNode() : StrictJson.object().numberNode(value); }
}
