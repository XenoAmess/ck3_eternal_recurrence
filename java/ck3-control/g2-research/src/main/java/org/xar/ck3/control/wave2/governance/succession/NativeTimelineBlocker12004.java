package org.xar.ck3.control.wave2.governance.succession;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.Session;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;

/** Decodes the original existing native timeline/Close frames. Does not query, submit, publish or qualify a source. */
public final class NativeTimelineBlocker12004 {
    public static final String QUERY_STEP = "query-current-timeline-blocker-context-v1";
    public static final String CLOSE_STEP = "continue-death-succession-modal-v1";
    public static final int MAX_BYTES = 1_048_576;
    private static final Set<String> ENVELOPE = Set.of("type", "protocol_version", "request_id", "ok", "result");
    private static final Set<String> RESULT = Set.of("step", "accepted", "status", "query_sequence", "observation_revision",
            "snapshot_revision", "current_timeline_blocker_context", "private_build", "read_only", "advertised", "backend_id");
    private static final Set<String> ACK = Set.of("step", "accepted", "status", "snapshot_revision", "date_raw",
            "played_character_id", "action_observation_revision", "identity_verified", "can_continue_verified",
            "paused_by_succession_verified", "has_open_succession_verified", "controller_vtable_verified",
            "controller_open_verified", "close_invocations", "material_result_verified", "private_build", "advertised", "backend_id");
    private static final Set<String> CONTEXT = Set.of("schema", "schema_version", "status", "snapshot_revision", "date_raw",
            "identity", "blocks_simulation", "has_open_succession", "can_continue", "evidence_source", "unavailable_reason");

    public enum Status { AVAILABLE, UNAVAILABLE }
    public enum Identity { NONE, DEATH_SUCCESSION_MODAL, GAME_OVER_MODAL, SUCCESSION_SELECT_DESTINY_MODAL }
    public sealed interface TypedBoolean permits Known, Unknown { }
    public record Known(boolean value) implements TypedBoolean { }
    public record Unknown(String reason) implements TypedBoolean { public Unknown { textBounded(reason); } }
    public record Evidence(String kind, String path, String rootName, String decisiveWidgetName) {
        public Evidence {
            Objects.requireNonNull(kind); Objects.requireNonNull(path); Objects.requireNonNull(rootName); Objects.requireNonNull(decisiveWidgetName);
        }
    }
    public record Context(Status status, BigInteger nativeRevision, int dateRaw, Identity identity,
            TypedBoolean blocksSimulation, TypedBoolean hasOpenSuccession, TypedBoolean canContinue,
            Evidence evidence, Optional<String> unavailableReason) {
        public Context {
            Objects.requireNonNull(status); positive(nativeRevision); Objects.requireNonNull(identity);
            Objects.requireNonNull(blocksSimulation); Objects.requireNonNull(hasOpenSuccession); Objects.requireNonNull(canContinue);
            Objects.requireNonNull(evidence); Objects.requireNonNull(unavailableReason); unavailableReason.ifPresent(NativeTimelineBlocker12004::textBounded);
            if (status == Status.UNAVAILABLE) {
                StrictJson.require(identity == Identity.NONE && unavailableReason.isPresent()
                        && blocksSimulation instanceof Unknown && hasOpenSuccession instanceof Unknown && canContinue instanceof Unknown
                        && evidence.equals(new Evidence("", "", "", "")), "unavailable timeline cannot carry actionable/evidence facts");
            } else {
                StrictJson.require(unavailableReason.isEmpty() && blocksSimulation instanceof Known && hasOpenSuccession instanceof Known,
                        "available timeline requires independently observed native predicates");
                StrictJson.require(evidence.kind().equals("exact-build-stock-gui-plus-native-widget-state")
                        && evidence.path().equals("game/gui/window_succession_event.gui"), "original exact-build GUI evidence source required");
                textBounded(evidence.rootName()); textBounded(evidence.decisiveWidgetName());
                StrictJson.require(identity == Identity.NONE ? canContinue instanceof Unknown : canContinue instanceof Known,
                        "no surface has unknown can_continue; recognized surface requires a typed boolean");
            }
        }
        public boolean supportedCloseObserved() {
            return status == Status.AVAILABLE && identity == Identity.DEATH_SUCCESSION_MODAL
                    && known(blocksSimulation, true) && known(hasOpenSuccession, true) && known(canContinue, true);
        }
        public boolean clearedObserved() {
            return status == Status.AVAILABLE && identity == Identity.NONE
                    && known(blocksSimulation, false) && known(hasOpenSuccession, false);
        }
    }
    /** Opaque event/interaction objects stay in the exact JSON type domain; absence is not repaired to null. */
    public record Scene(String activeEventJson, String pendingInteractionJson, Optional<String> terminalReason) {
        public Scene {
            activeEventJson = surface(activeEventJson); pendingInteractionJson = surface(pendingInteractionJson);
            Objects.requireNonNull(terminalReason); terminalReason.ifPresent(NativeTimelineBlocker12004::textBounded);
        }
        public static Scene fromSnapshot(JsonNode actualSnapshot) {
            JsonNode event = field(actualSnapshot, "active_event"), pending = field(actualSnapshot, "pending_character_interaction");
            JsonNode terminal = field(actualSnapshot, "one_life_terminal_reason");
            return new Scene(new String(StrictJson.canonical(event, MAX_BYTES), StandardCharsets.UTF_8),
                    new String(StrictJson.canonical(pending, MAX_BYTES), StandardCharsets.UTF_8),
                    terminal.isNull() ? Optional.empty() : Optional.of(StrictJson.text(terminal)));
        }
    }
    /** Root supplies the same original snapshot's frame and scene. A copy is not loaded-DLL/source-epoch qualification. */
    public record BoundFrame(Session session, Frame frame, Scene scene) {
        public BoundFrame {
            Objects.requireNonNull(session); Objects.requireNonNull(frame); Objects.requireNonNull(scene);
            StrictJson.require(session.executable().sha256().equals(NativePlayerHeirObservation12004.EXE_SHA256), "exact .4 source required");
            // The actual existing native query and Close producer accepts only a positive played actor.
            StrictJson.require(frame.actorCharacterId() > 0, "actual native timeline positive actor boundary required");
        }
    }
    public static final class Query {
        private final BoundFrame binding;
        private final String requestId;
        private final BigInteger sequence, observationRevision;
        private final Context context;
        private final ExactRef original;
        private Query(BoundFrame binding, String requestId, BigInteger sequence, BigInteger observationRevision, Context context, ExactRef original) {
            this.binding = binding; this.requestId = requestId; this.sequence = sequence;
            this.observationRevision = observationRevision; this.context = context; this.original = original;
        }
        public BoundFrame binding() { return binding; }
        public String requestId() { return requestId; }
        public BigInteger sequence() { return sequence; }
        public BigInteger observationRevision() { return observationRevision; }
        public Context context() { return context; }
        public ExactRef original() { return original; }
    }
    public record SubmissionAck(BigInteger actionObservationRevision) { public SubmissionAck { positive(actionObservationRevision); } }
    public enum CloseState { SUBMITTED_PENDING, SUBMISSION_UNKNOWN }
    /** An outer reclaim RED remains UNKNOWN even when it retains an authentic inner submission ACK. */
    public static final class Close {
        private final BoundFrame binding;
        private final String requestId;
        private final CloseState state;
        private final Optional<SubmissionAck> ack;
        private final Optional<String> failure, retainedAckValidationFailure;
        private final ExactRef original;
        private Close(BoundFrame binding, String requestId, CloseState state, Optional<SubmissionAck> ack,
                Optional<String> failure, Optional<String> retainedAckValidationFailure, ExactRef original) {
            this.binding = binding; this.requestId = requestId; this.state = state; this.ack = ack;
            this.failure = failure; this.retainedAckValidationFailure = retainedAckValidationFailure; this.original = original;
        }
        public BoundFrame binding() { return binding; }
        public String requestId() { return requestId; }
        public CloseState state() { return state; }
        public Optional<SubmissionAck> ack() { return ack; }
        public Optional<String> failure() { return failure; }
        public Optional<String> retainedAckValidationFailure() { return retainedAckValidationFailure; }
        public ExactRef original() { return original; }
        public boolean replayAuthorized() { return false; }
    }
    public enum ClearanceState { FRAME_CHANGED, INITIAL_CLOSE_NOT_OBSERVED, SUBMISSION_UNKNOWN,
        OBSERVATION_REGRESSED, POST_QUERY_NOT_NEWER, MODAL_OR_PREDICATES_UNCLEARED, CLEARED_OBSERVED }
    public record Clearance(ClearanceState state, Query initial, Close close, Query subsequent) {
        public Clearance { Objects.requireNonNull(state); Objects.requireNonNull(initial); Objects.requireNonNull(close); Objects.requireNonNull(subsequent); }
        public boolean naturalDeathProven() { return false; }
        public boolean savedContinuationProven() { return false; }
        public boolean submissionAuthorized() { return false; }
    }
    private NativeTimelineBlocker12004() { }

    /** Original native command_result only; SDK-added projection fields are not accepted as an original frame. */
    public static Query parseQuery(byte[] original, ExactRef reference, BoundFrame binding, String expectedRequestId) {
        Objects.requireNonNull(binding); exact(original, reference); textBounded(expectedRequestId);
        ObjectNode envelope = StrictJson.object(StrictJson.parse(original, MAX_BYTES), ENVELOPE);
        envelopeIdentity(envelope, expectedRequestId); truth(envelope, "ok", true);
        ObjectNode result = StrictJson.object(field(envelope, "result"), RESULT);
        StrictJson.require(QUERY_STEP.equals(text(result, "step")), "original query step required");
        truth(result, "accepted", true); truth(result, "private_build", true); truth(result, "read_only", true); truth(result, "advertised", false);
        StrictJson.require("native-headless".equals(text(result, "backend_id")), "original backend required");
        StrictJson.require(uint(result, "snapshot_revision").equals(binding.frame().nativeRevision()), "query/native frame drift");
        Context context = parseContext(field(result, "current_timeline_blocker_context"), binding.frame());
        StrictJson.require(text(result, "status").equals(statusName(context.status())), "query envelope/context status disagree");
        return new Query(binding, expectedRequestId, uint(result, "query_sequence"), uint(result, "observation_revision"), context, reference);
    }

    /** Retains every original RED as unknown; generic failure text cannot certify that no native action ran. */
    public static Close parseClose(byte[] original, ExactRef reference, BoundFrame binding, String expectedRequestId) {
        Objects.requireNonNull(binding); exact(original, reference); textBounded(expectedRequestId);
        JsonNode raw = StrictJson.parse(original, MAX_BYTES);
        envelopeIdentity(raw, expectedRequestId);
        if (bool(raw, "ok")) {
            ObjectNode envelope = StrictJson.object(raw, ENVELOPE);
            SubmissionAck ack = parseAck(field(envelope, "result"), binding.frame());
            return new Close(binding, expectedRequestId, CloseState.SUBMITTED_PENDING, Optional.of(ack), Optional.empty(), Optional.empty(), reference);
        }
        StrictJson.require(raw.isObject(), "original RED envelope required");
        boolean diagnostic = raw.has("death_succession_close_failure_v1");
        StrictJson.object(raw, diagnostic
                ? Set.of("type", "protocol_version", "request_id", "ok", "error", "death_succession_close_failure_v1")
                : Set.of("type", "protocol_version", "request_id", "ok", "error"));
        String failure = text(raw, "error");
        Optional<SubmissionAck> retained = Optional.empty(); Optional<String> invalid = Optional.empty();
        if (diagnostic) {
            try {
                ObjectNode detail = StrictJson.object(field(raw, "death_succession_close_failure_v1"), Set.of("stage", "status",
                        "material_result_verified", "business_material_verified", "reclaim_result_enum", "submitted_ack_frame_exact_json"));
                StrictJson.require("reclaim".equals(text(detail, "stage")) && "submitted_unconfirmed".equals(text(detail, "status")), "original reclaim diagnostic required");
                truth(detail, "material_result_verified", false); truth(detail, "business_material_verified", false);
                StrictJson.integer(field(detail, "reclaim_result_enum"), 0, Integer.MAX_VALUE);
                JsonNode inner = StrictJson.parse(text(detail, "submitted_ack_frame_exact_json").getBytes(StandardCharsets.UTF_8), MAX_BYTES);
                ObjectNode ackEnvelope = StrictJson.object(inner, ENVELOPE);
                envelopeIdentity(ackEnvelope, expectedRequestId); truth(ackEnvelope, "ok", true);
                retained = Optional.of(parseAck(field(ackEnvelope, "result"), binding.frame()));
            } catch (IllegalArgumentException rejected) {
                String reason = rejected.getMessage() == null ? "retained ACK rejected" : rejected.getMessage();
                invalid = Optional.of(reason.substring(0, Math.min(reason.length(), 512)));
            }
        }
        return new Close(binding, expectedRequestId, CloseState.SUBMISSION_UNKNOWN, retained, Optional.of(failure), invalid, reference);
    }

    /** Reports only a later independently decoded GUI/predicate observation, never a death/episode/SAVE authority. */
    public static Clearance compareClearance(Query initial, Close close, Query later) {
        Objects.requireNonNull(initial); Objects.requireNonNull(close); Objects.requireNonNull(later);
        ClearanceState state;
        if (!sameContinuation(initial.binding(), close.binding()) || !sameContinuation(close.binding(), later.binding())) state = ClearanceState.FRAME_CHANGED;
        else if (!initial.context().supportedCloseObserved()) state = ClearanceState.INITIAL_CLOSE_NOT_OBSERVED;
        else if (close.state() != CloseState.SUBMITTED_PENDING || close.ack().isEmpty()) state = ClearanceState.SUBMISSION_UNKNOWN;
        else if (close.ack().orElseThrow().actionObservationRevision().compareTo(initial.observationRevision()) < 0) state = ClearanceState.OBSERVATION_REGRESSED;
        else if (later.observationRevision().compareTo(close.ack().orElseThrow().actionObservationRevision()) <= 0
                || later.sequence().compareTo(initial.sequence()) <= 0
                || initial.requestId().equals(later.requestId()) || initial.original().equals(later.original())) state = ClearanceState.POST_QUERY_NOT_NEWER;
        else if (!later.context().clearedObserved()) state = ClearanceState.MODAL_OR_PREDICATES_UNCLEARED;
        else state = ClearanceState.CLEARED_OBSERVED;
        return new Clearance(state, initial, close, later);
    }
    /** Each real query/Close keeps its own frame; paused identity and scene stay fixed while counters may advance independently. */
    public static boolean sameContinuation(BoundFrame before, BoundFrame after) {
        Objects.requireNonNull(before); Objects.requireNonNull(after); Frame a=before.frame(),b=after.frame();
        return before.session().equals(after.session()) && before.scene().equals(after.scene())
                && a.dateRaw()==b.dateRaw() && a.actorCharacterId()==b.actorCharacterId() && a.localPlayerId()==b.localPlayerId()
                && b.publicRevision().compareTo(a.publicRevision())>=0 && b.nativeRevision().compareTo(a.nativeRevision())>=0;
    }

    public static Context parseContext(JsonNode raw, Frame frame) {
        Objects.requireNonNull(frame); ObjectNode value = StrictJson.object(raw, CONTEXT);
        StrictJson.require("current-timeline-blocker-context-v1".equals(text(value, "schema")), "original timeline schema required");
        StrictJson.integer(field(value, "schema_version"), 1, 1);
        Status status = switch (text(value, "status")) { case "available" -> Status.AVAILABLE; case "unavailable" -> Status.UNAVAILABLE;
            default -> throw new IllegalArgumentException("unknown timeline status"); };
        BigInteger revision = uint(value, "snapshot_revision"); int date = signed(value, "date_raw");
        StrictJson.require(revision.equals(frame.nativeRevision()) && date == frame.dateRaw(), "original timeline frame binding changed");
        Identity identity = switch (text(value, "identity")) { case "none" -> Identity.NONE; case "death_succession_modal" -> Identity.DEATH_SUCCESSION_MODAL;
            case "game_over_modal" -> Identity.GAME_OVER_MODAL; case "succession_select_destiny_modal" -> Identity.SUCCESSION_SELECT_DESTINY_MODAL;
            default -> throw new IllegalArgumentException("unknown timeline identity"); };
        ObjectNode source = StrictJson.object(field(value, "evidence_source"), Set.of("kind", "path", "root_name", "decisive_widget_name"));
        Evidence evidence = new Evidence(string(source, "kind"), string(source, "path"), string(source, "root_name"), string(source, "decisive_widget_name"));
        return new Context(status, revision, date, identity, typed(field(value, "blocks_simulation")), typed(field(value, "has_open_succession")),
                typed(field(value, "can_continue")), evidence, optionalReason(value, "unavailable_reason"));
    }

    public static byte[] encodeContext(Context value) {
        Objects.requireNonNull(value); ObjectNode out = StrictJson.object();
        out.put("schema", "current-timeline-blocker-context-v1").put("schema_version", 1).put("status", statusName(value.status()))
                .put("snapshot_revision", value.nativeRevision()).put("date_raw", value.dateRaw()).put("identity", identityName(value.identity()));
        out.set("blocks_simulation", typedNode(value.blocksSimulation())); out.set("has_open_succession", typedNode(value.hasOpenSuccession()));
        out.set("can_continue", typedNode(value.canContinue())); Evidence e = value.evidence();
        out.putObject("evidence_source").put("kind", e.kind()).put("path", e.path()).put("root_name", e.rootName()).put("decisive_widget_name", e.decisiveWidgetName());
        if (value.unavailableReason().isEmpty()) out.putNull("unavailable_reason"); else out.put("unavailable_reason", value.unavailableReason().orElseThrow());
        return StrictJson.canonical(out, MAX_BYTES);
    }

    private static SubmissionAck parseAck(JsonNode raw, Frame frame) {
        ObjectNode value = StrictJson.object(raw, ACK);
        StrictJson.require(CLOSE_STEP.equals(text(value, "step")) && "submitted".equals(text(value, "status")), "original pending Close ACK required");
        for (String key : Set.of("accepted", "identity_verified", "can_continue_verified", "paused_by_succession_verified",
                "has_open_succession_verified", "controller_vtable_verified", "controller_open_verified", "private_build")) truth(value, key, true);
        truth(value, "material_result_verified", false); truth(value, "advertised", false);
        StrictJson.require("native-headless".equals(text(value, "backend_id")), "original Close backend required");
        StrictJson.require(uint(value, "snapshot_revision").equals(frame.nativeRevision()) && signed(value, "date_raw") == frame.dateRaw()
                && signed(value, "played_character_id") == frame.actorCharacterId(), "Close source frame drift");
        StrictJson.integer(field(value, "close_invocations"), 1, 1);
        return new SubmissionAck(uint(value, "action_observation_revision"));
    }
    private static TypedBoolean typed(JsonNode raw) {
        ObjectNode field = StrictJson.object(raw, Set.of("status", "value", "unavailable_reason"));
        return switch (text(field, "status")) {
            case "available" -> { StrictJson.require(field(field, "unavailable_reason").isNull(), "known predicate reason must be null"); yield new Known(bool(field, "value")); }
            case "unavailable" -> { StrictJson.require(field(field, "value").isNull(), "unknown predicate value must be null"); yield new Unknown(text(field, "unavailable_reason")); }
            default -> throw new IllegalArgumentException("unknown predicate status");
        };
    }
    private static ObjectNode typedNode(TypedBoolean value) {
        ObjectNode out = StrictJson.object();
        if (value instanceof Known known) { out.put("status", "available").put("value", known.value()).putNull("unavailable_reason"); }
        else { out.put("status", "unavailable").putNull("value").put("unavailable_reason", ((Unknown) value).reason()); }
        return out;
    }
    private static void envelopeIdentity(JsonNode envelope, String expectedId) {
        StrictJson.require("command_result".equals(text(envelope, "type")) && expectedId.equals(text(envelope, "request_id")), "original command/request binding required");
        StrictJson.integer(field(envelope, "protocol_version"), 1, 1);
    }
    private static void exact(byte[] original, ExactRef reference) {
        Objects.requireNonNull(original); Objects.requireNonNull(reference);
        StrictJson.require(original.length > 0 && original.length <= MAX_BYTES && original.length == reference.bytes()
                && reference.sha256().equals(G2RetainedNativeSourceProvider.sha256(original)), "original native packet bytes/SHA differ");
    }
    private static JsonNode field(JsonNode value, String key) { StrictJson.require(value != null && value.isObject() && value.has(key), "missing required field: " + key); return value.get(key); }
    private static String string(JsonNode value, String key) { JsonNode node = field(value, key); StrictJson.require(node.isTextual(), "exact string required: " + key); return node.textValue(); }
    private static String text(JsonNode value, String key) { String result = string(value, key); textBounded(result); return result; }
    private static void textBounded(String value) { StrictJson.text(value); StrictJson.require(value.length() <= MAX_BYTES, "bounded native text required"); }
    private static boolean bool(JsonNode value, String key) { JsonNode node = field(value, key); StrictJson.require(node.isBoolean(), "exact boolean required: " + key); return node.booleanValue(); }
    private static void truth(JsonNode value, String key, boolean expected) { StrictJson.require(bool(value, key) == expected, "native flag drift: " + key); }
    private static int signed(JsonNode value, String key) { return (int) StrictJson.integer(field(value, key), Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static BigInteger uint(JsonNode value, String key) { return StrictJson.integer(field(value, key), BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static void positive(BigInteger value) { StrictJson.require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 required"); }
    private static Optional<String> optionalReason(JsonNode value, String key) { return field(value, key).isNull() ? Optional.empty() : Optional.of(text(value, key)); }
    private static boolean known(TypedBoolean value, boolean expected) { return value instanceof Known known && known.value() == expected; }
    private static String statusName(Status status) { return status == Status.AVAILABLE ? "available" : "unavailable"; }
    private static String surface(String raw) {
        Objects.requireNonNull(raw); JsonNode value = StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8), MAX_BYTES);
        StrictJson.require(value.isNull() || value.isObject(), "original event/interaction object or explicit null required");
        return new String(StrictJson.canonical(value, MAX_BYTES), StandardCharsets.UTF_8);
    }
    private static String identityName(Identity identity) { return switch (identity) { case NONE -> "none"; case DEATH_SUCCESSION_MODAL -> "death_succession_modal"; case GAME_OVER_MODAL -> "game_over_modal"; case SUCCESSION_SELECT_DESTINY_MODAL -> "succession_select_destiny_modal"; }; }
}
