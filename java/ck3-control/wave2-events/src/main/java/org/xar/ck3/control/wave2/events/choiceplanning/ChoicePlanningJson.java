package org.xar.ck3.control.wave2.events.choiceplanning;

import static org.xar.ck3.control.wave2.events.choiceplanning.ChoicePlanningModel.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceCodec;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Decision;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.IntegerIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeChoice;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeWindow;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.TextIdentity;

/** One bounded strict wrapper; legacy SDK snapshots/history are declared projections with retained evidence. */
public final class ChoicePlanningJson {
    public static final String SCHEMA = "xar.java-mandatory-choice-planning-request/v1";
    private static final int MAX_BYTES = 65_536;
    private static final String EVENT_QUERY = "query-current-event-window-context-v1";
    private static final BigInteger UINT64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private ChoicePlanningJson() { }

    public static PlanningInput decode(byte[] raw) {
        ObjectNode row = exactObject(parse(raw), Set.of("schema", "snapshot", "commands", "action_steps", "bridge_capabilities"));
        require(SCHEMA.equals(text(row.get("schema"))), "planning schema");
        Optional<Snapshot> snapshot = row.get("snapshot").isNull() ? Optional.empty() : Optional.of(snapshot(object(row.get("snapshot"))));
        JsonNode commands = row.get("commands"); require(commands.isArray() && commands.size() <= 256, "bounded command history required");
        List<HistoryRow> history = new ArrayList<>();
        for (JsonNode command : commands) { history.add(history(command)); }
        return new PlanningInput(snapshot, history, strings(row.get("action_steps")), strings(row.get("bridge_capabilities")));
    }

    public static byte[] plan(byte[] raw) { return plan(raw, new MandatoryChoicePlanner()); }

    /** Calls the concrete typed consumer port; the port cannot submit a game action. */
    public static byte[] plan(byte[] raw, ChoicePlanningPort consumer) {
        java.util.Objects.requireNonNull(consumer);
        return encode(consumer.plan(decode(raw)));
    }

    public static byte[] encode(PlanningResult result) {
        if (result instanceof NoCandidate) { return "null".getBytes(StandardCharsets.UTF_8); }
        Proposal plan = (Proposal) result;
        ObjectNode out = JSON.createObjectNode(); out.put("policy", "native-mandatory-choice-v1");
        out.put("phase", plan.phase().wire()); out.put("reason", plan.reason());
        if (plan.selectedStep().isPresent()) { out.put("selected_step", plan.selectedStep().orElseThrow().wire()); }
        else { out.putNull("selected_step"); }
        plan.hint().ifPresent(hint -> out.set("top_exclusive_modal_choice_hint", read(hint.original())));
        switch (plan.phase()) {
            case MECHANISM_UNAVAILABLE -> {
                out.put("required_public_step", PublicStep.QUERY.wire());
                out.put("required_typed_method", "select_mandatory_choice_v1");
                out.put("required_capability", MandatoryChoicePlanner.QUERY_CAPABILITY);
            }
            case QUERY_FAILED -> {
                ObjectNode observation = out.putObject("query_observation"); observation.put("status", "failed_read");
                observation.set("row", read(plan.failedRead().orElseThrow().original()));
            }
            case QUERY_MALFORMED -> out.set("query_observation", read(plan.query().orElseThrow().original()));
            case PENDING_VERIFICATION -> {
                out.set("pending_token_result", read(plan.pending().orElseThrow().commandResult()));
                out.set("current_query_observation", read(plan.query().orElseThrow().original()));
            }
            case SELECTOR_UNAVAILABLE -> out.set("mandatory_choice_decision", selector(plan.selection().orElseThrow()));
            case FIRST_ENABLED -> encodeSelection(out, plan);
            case FRAME_UNAVAILABLE, QUERY -> { }
        }
        return bytes(out);
    }

    private static void encodeSelection(ObjectNode out, Proposal plan) {
        Decision selection = plan.selection().orElseThrow();
        NativeQuery query = plan.query().orElseThrow(); NativeWindow window = query.window().orElseThrow();
        NativeChoice choice = selection.selectedChoice().orElseThrow();
        ObjectNode capture = out.putObject("unknown_mandatory_choice_v1");
        capture.put("schema", "xar.unknown-mandatory-choice-incident/v1");
        capture.set("native_window", read(window.original())); capture.set("frame_binding", read(window.frame().original()));
        capture.put("blocking_proof_verified", true); capture.put("catalogue_complete", true);
        capture.set("native_query_receipt", read(query.original())); capture.set("selector_decision", selector(selection));
        ObjectNode chosen = capture.putObject("selection"); chosen.put("selected_step", PublicStep.SELECT.wire());
        chosen.set("choice_id", identityNode(choice.identity()));
        chosen.put("action_token", choice.actionToken().value()); chosen.put("query_id", window.queryId().value());
        chosen.set("window_instance_id", identityNode(window.windowInstanceId().value()));
        if (choice.nativeIndex().hasValue()) { chosen.put("native_index", choice.nativeIndex().value()); }
        else { chosen.putNull("native_index"); }
        JsonNode bounds = read(choice.original()).get("bounds");
        chosen.set("bounds", bounds == null ? JSON.getNodeFactory().nullNode() : bounds);
        capture.putNull("known_ui_recovery_source"); capture.put("semantic_optimal", false); capture.put("material_effects_verified", false);
        capture.put("typed_event_unavailable_same_root_fallback", plan.typedEventFallback());
        capture.set("typed_event_unavailable_context", plan.typedEventContext().map(ChoicePlanningJson::read)
                .orElseGet(() -> JSON.getNodeFactory().nullNode()));
        out.putNull("known_ui_recovery_source"); out.set("mandatory_choice_decision", selector(selection));
    }

    private static Snapshot snapshot(ObjectNode row) {
        boolean event = row.path("active_event").isObject();
        Optional<BigInteger> eventId = event ? optionalInteger(row.path("active_event").get("instance_id")) : Optional.empty();
        Optional<FrameBinding> frame = Optional.empty();
        if (row.path("played_character").isObject() && row.path("diagnostics").isObject()) {
            ObjectNode projected = JSON.createObjectNode();
            projected.set("game_pid", valueOrNull(row.path("diagnostics").get("bridge_pid")));
            projected.set("connection_generation", valueOrNull(row.path("diagnostics").get("connection_generation")));
            projected.set("actor_character_id", valueOrNull(row.path("played_character").get("character_id")));
            for (String name : Set.of("revision", "native_revision", "date_raw", "episode_run_id", "snapshot_id")) {
                projected.set(name, valueOrNull(row.get(name)));
            }
            try { frame = Optional.of(MandatoryChoiceCodec.decodeFrame(bytes(projected))); }
            catch (IllegalArgumentException error) { frame = Optional.empty(); }
        }
        Optional<NativeHint> hint = Optional.empty();
        if (row.path("top_exclusive_modal_choice_hint").isObject()) {
            ObjectNode raw = object(row.get("top_exclusive_modal_choice_hint"));
            HintStatus status = "present".equals(textOrEmpty(raw.get("status"))) ? HintStatus.PRESENT : HintStatus.OTHER;
            hint = Optional.of(new NativeHint(status, textOrEmpty(raw.get("source")),
                    trueBoolean(raw.get("owner_verified")), optionalInteger(raw.get("max_observation_age_ms")).orElse(BigInteger.valueOf(-1)),
                    optionalText(raw.get("opaque_root_id")), document(raw)));
        }
        return new Snapshot(frame, eventId, event, row.path("pending_character_interaction").isObject(), hint);
    }

    private static HistoryRow history(JsonNode raw) {
        if (!raw.isObject()) { return new HistoryRow(false, false, Optional.empty(), Optional.empty(), Optional.empty(), document(raw)); }
        ObjectNode row = object(raw);
        String command = textOrEmpty(row.get("command"));
        JsonNode result = row.get("result");
        JsonNode auto = result != null && result.isObject() ? result.get("auto_turn") : null;
        String effectiveCommand = "auto-turn".equals(command) && auto != null && auto.isObject()
                ? textOrEmpty(auto.get("selected_step")) : command;
        JsonNode queryResult = result;
        if ("auto-turn".equals(command) && auto != null && auto.isObject() && auto.path("result").isObject()) { queryResult = auto.get("result"); }
        boolean ok = trueBoolean(row.get("ok"));
        boolean queryCommand = PublicStep.QUERY.wire().equals(effectiveCommand);
        Optional<NativeQuery> query = queryCommand && queryResult != null && queryResult.isObject()
                ? Optional.of(query(object(queryResult))) : Optional.empty();
        JsonNode selectionRoot = "auto-turn".equals(command) ? auto : result;
        Optional<SubmittedSelection> submitted = selection(selectionRoot);
        JsonNode eventResult = queryResult;
        if (result != null && result.isObject() && Set.of("assault_action", "route_preview", "war_action", "war_progress_before", "war_progress_after")
                .stream().anyMatch(name -> result.path(name).isObject())) { eventResult = result; }
        Optional<EventRead> eventRead = EVENT_QUERY.equals(effectiveCommand) && eventResult != null && eventResult.isObject()
                ? eventRead(object(eventResult)) : Optional.empty();
        return new HistoryRow(queryCommand, ok, query, submitted, eventRead, document(raw));
    }

    private static NativeQuery query(ObjectNode row) {
        Optional<NativeWindow> window = Optional.empty();
        JsonNode dto = row.get("mandatory_choice");
        if (dto != null && dto.isObject() && "xar.native-mandatory-choice-window/v1".equals(dto.path("schema").textValue())) {
            try { window = Optional.of(MandatoryChoiceCodec.decode(bytes(dto))); }
            catch (IllegalArgumentException error) { window = Optional.empty(); }
        }
        Optional<RootRelation> relation = dto != null && dto.path("typed_window_relation").isObject()
                ? relation(object(dto.get("typed_window_relation"))) : Optional.empty();
        return new NativeQuery(stamp(row), trueBoolean(row.get("accepted")), PublicStep.QUERY.wire().equals(textOrEmpty(row.get("step"))),
                window, relation, document(row));
    }

    private static Optional<RootRelation> relation(ObjectNode row) {
        try {
            RelationStatus status = switch (text(row.get("status"))) {
                case "independent_top_modal" -> RelationStatus.INDEPENDENT_TOP_MODAL;
                case "same_typed_root" -> RelationStatus.SAME_TYPED_ROOT;
                default -> RelationStatus.OTHER;
            };
            return Optional.of(new RootRelation(status, bool(row.get("owner_verified")), text(row.get("source")),
                    optionalText(row.get("typed_domain")), optionalInteger(row.get("typed_window_instance_id")),
                    optionalText(row.get("top_opaque_root_id")), optionalText(row.get("typed_opaque_root_id"))));
        } catch (IllegalArgumentException error) { return Optional.empty(); }
    }
    private static Optional<SubmittedSelection> selection(JsonNode row) {
        if (row == null || !row.isObject() || !PublicStep.SELECT.wire().equals(textOrEmpty(row.get("selected_step")))) { return Optional.empty(); }
        JsonNode capture = row.path("plan").path("unknown_mandatory_choice_v1");
        JsonNode frame = capture.path("frame_binding"); JsonNode window = capture.path("native_window");
        if (!frame.isObject()) { return Optional.empty(); }
        SubmissionBinding binding;
        try {
            binding = new SubmissionBinding(unsigned(frame.get("game_pid"), true),
                    unsigned(frame.get("actor_character_id"), true), text(frame.get("episode_run_id")));
        } catch (IllegalArgumentException error) { return Optional.empty(); }
        // Once an original submission has a bindable identity, malformed result fields cannot erase that claim.
        SelectionStatus status = "pending".equals(textOrEmpty(row.get("status"))) ? SelectionStatus.PENDING : SelectionStatus.OTHER;
        return Optional.of(new SubmittedSelection(binding, status,
                optionalIdentity(window.get("window_id")), optionalIdentity(window.get("window_instance_id")), document(valueOrNull(row.get("result")))));
    }
    private static Optional<EventRead> eventRead(ObjectNode row) {
        try {
            if (!EVENT_QUERY.equals(text(row.get("step"))) || !trueBoolean(row.get("accepted")) || !row.path("current_event_window_context").isObject()) { return Optional.empty(); }
            ObjectNode context = object(row.get("current_event_window_context"));
            String status = text(context.get("status")); if (!status.equals(text(row.get("status")))) { return Optional.empty(); }
            QueryStamp stamp = stamp(row).orElseThrow(() -> new IllegalArgumentException("event query frame required"));
            BigInteger eventId = positive32(row.get("current_event_instance_id"));
            BigInteger date = signed32(row.get("date_raw")); BigInteger nativeRevision = unsigned(row.get("snapshot_revision"), true);
            require(eventId.equals(positive32(context.get("current_event_instance_id")))
                    && date.equals(signed32(context.get("date_raw"))) && nativeRevision.equals(unsigned(context.get("snapshot_revision"), true)), "event context binding");
            if ("unavailable".equals(status)) {
                if (!UnavailableEventContextProjection.valid(context, eventId, date, nativeRevision)) { return Optional.empty(); }
                return Optional.of(new EventRead(stamp, eventId, nativeRevision, date, EventContextKind.VALID_UNAVAILABLE, Optional.of(document(context))));
            }
            if ("available".equals(status)) {
                // Available semantic normalization belongs to the existing typed route; never borrow its buttons here.
                return Optional.of(new EventRead(stamp, eventId, nativeRevision, date, EventContextKind.RETAIN_TYPED_PRIORITY, Optional.empty()));
            }
            return Optional.empty();
        } catch (IllegalArgumentException error) { return Optional.empty(); }
    }
    private static Optional<QueryStamp> stamp(ObjectNode row) {
        Optional<String> snapshotId = optionalText(row.get("queried_snapshot_id"));
        Optional<BigInteger> revision = optionalInteger(row.get("queried_revision"));
        Optional<BigInteger> nativeRevision = optionalInteger(row.get("queried_native_revision"));
        return snapshotId.isPresent() && revision.isPresent() && nativeRevision.isPresent()
                ? Optional.of(new QueryStamp(snapshotId.orElseThrow(), revision.orElseThrow(), nativeRevision.orElseThrow())) : Optional.empty();
    }
    private static Set<String> strings(JsonNode node) {
        require(node != null && node.isArray() && node.size() <= 4096, "bounded string list required");
        Set<String> result = new HashSet<>(); for (JsonNode value : node) { result.add(text(value)); } return Set.copyOf(result);
    }
    private static Optional<ChoiceIdentity> optionalIdentity(JsonNode node) {
        if (node == null || node.isNull()) { return Optional.empty(); }
        return Optional.of(node.isTextual() ? new TextIdentity(text(node)) : new IntegerIdentity(integer(node)));
    }
    private static JsonNode identityNode(ChoiceIdentity identity) {
        return identity instanceof TextIdentity value ? JSON.getNodeFactory().textNode(value.value())
                : JSON.getNodeFactory().numberNode(((IntegerIdentity) identity).value());
    }
    private static Optional<BigInteger> optionalInteger(JsonNode node) { return node == null || node.isNull() ? Optional.empty() : Optional.of(integer(node)); }
    private static Optional<String> optionalText(JsonNode node) { return node == null || node.isNull() ? Optional.empty() : Optional.of(text(node)); }
    private static String textOrEmpty(JsonNode node) { return node == null || node.isNull() ? "" : textAllowEmpty(node); }
    static String text(JsonNode node) { String value = textAllowEmpty(node); require(!value.isEmpty(), "nonempty string required"); return value; }
    private static String textAllowEmpty(JsonNode node) {
        require(node != null && node.isTextual(), "string token required"); String value = node.textValue();
        if (!value.isEmpty()) { StrictJson.text(value); } return value;
    }
    static BigInteger integer(JsonNode node) {
        require(node != null && node.isIntegralNumber(), "integer token required; no bool/float/string"); return node.bigIntegerValue();
    }
    static BigInteger unsigned(JsonNode node, boolean positive) {
        BigInteger value = integer(node); require(value.compareTo(positive ? BigInteger.ONE : BigInteger.ZERO) >= 0 && value.compareTo(UINT64_MAX) <= 0, "uint64 range"); return value;
    }
    static BigInteger signed32(JsonNode node) {
        BigInteger value = integer(node); require(value.compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "signed32 range"); return value;
    }
    static BigInteger positive32(JsonNode node) { BigInteger value = signed32(node); require(value.signum() > 0, "positive event instance"); return value; }
    static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "boolean token required"); return node.booleanValue(); }
    private static boolean trueBoolean(JsonNode node) { return node != null && !node.isNull() && bool(node); }
    private static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "JSON object required"); return (ObjectNode) node; }
    static ObjectNode exactObject(JsonNode node, Set<String> expected) {
        ObjectNode row = object(node); Set<String> actual = new HashSet<>(); row.fieldNames().forEachRemaining(actual::add);
        require(expected.equals(actual), "exact wrapper/leaf fields required"); return row;
    }
    private static JsonNode parse(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded UTF-8 planning request required");
        try {
            String value = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode node = JSON.readTree(value); require(node != null, "JSON value required");
            validateJsonDomain(node, 0); return node;
        } catch (IOException error) { throw new IllegalArgumentException("invalid UTF-8/duplicate/trailing planning JSON", error); }
    }
    private static JsonNode read(EvidenceDocument document) { return parse(document.json().getBytes(StandardCharsets.UTF_8)); }
    private static void validateJsonDomain(JsonNode node, int depth) {
        require(depth <= 64, "bounded planning JSON nesting");
        if (node.isTextual() && !node.textValue().isEmpty()) { StrictJson.text(node.textValue()); }
        if (node.isFloatingPointNumber()) { require(Double.isFinite(node.doubleValue()), "finite JSON geometry number required"); }
        if (node.isObject()) { node.fieldNames().forEachRemaining(name -> { if (!name.isEmpty()) { StrictJson.text(name); } }); }
        if (node.isContainerNode()) { node.forEach(child -> validateJsonDomain(child, depth + 1)); }
    }
    private static JsonNode valueOrNull(JsonNode value) { return value == null ? JSON.getNodeFactory().nullNode() : value; }
    private static EvidenceDocument document(JsonNode node) { return new EvidenceDocument(new String(bytes(node), StandardCharsets.UTF_8)); }
    private static JsonNode selector(Decision decision) { return parse(MandatoryChoiceCodec.encodeDecision(decision)); }
    private static byte[] bytes(JsonNode value) {
        try { byte[] raw = JSON.writeValueAsBytes(value); require(raw.length <= MAX_BYTES, "planning receipt byte budget"); return raw; }
        catch (IOException error) { throw new IllegalArgumentException("JSON serialization failed", error); }
    }
    static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
