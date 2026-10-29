package org.xar.ck3.control.wave2.military.warresults;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Attempt;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Binding;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.DispatchAck;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Field;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.FieldPresence;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Observation;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.PendingClose;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Plan;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.QueryFrame;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Request;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Snapshot;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind;

/** Typed projection of an already validated SDK snapshot; not the native-source normalizer. */
public final class WarResultsCodec {
    public static final String SCHEMA = "xar.ck3.war-results-priority-input/v1";
    private static final String CHECK_DUE = "war_results_window_v1_check_due";
    private static final String NEXT_CHECK = "war_results_window_v1_next_check_date_raw";

    private WarResultsCodec() { }

    public static Request decode(byte[] bytes) {
        return decode(bytes, WindowKind.RESULTS);
    }

    public static Request decode(byte[] bytes, WindowKind kind) {
        StrictJson.require(kind != null, "explicit window kind required");
        ObjectNode root = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "snapshot", "action_steps", "bridge_capabilities"));
        StrictJson.require(kind.inputSchema().equals(text(root.get("schema"))), "unsupported window projection schema");
        JsonNode snapshot = root.get("snapshot");
        Optional<Snapshot> frame = snapshot.isNull() ? Optional.empty() : Optional.of(snapshot(snapshot, kind));
        return new Request(frame, strings(root.get("action_steps")), strings(root.get("bridge_capabilities")));
    }

    public static byte[] encodeRequest(Request request) {
        return encodeRequest(request, WindowKind.RESULTS);
    }

    public static byte[] encodeRequest(Request request, WindowKind kind) {
        StrictJson.require(kind != null, "explicit window kind required");
        ObjectNode root = StrictJson.object(); root.put("schema", kind.inputSchema());
        root.set("snapshot", request.snapshot().map(snapshot -> encodeSnapshot(snapshot, kind)).orElse(NullNode.getInstance()));
        ArrayNode steps = root.putArray("action_steps"); new TreeSet<>(request.actionSteps()).forEach(steps::add);
        ArrayNode capabilities = root.putArray("bridge_capabilities"); new TreeSet<>(request.bridgeCapabilities()).forEach(capabilities::add);
        return StrictJson.canonical(root);
    }

    public static byte[] encodePlan(Optional<Plan> plan) {
        return encodePlan(plan, WindowKind.RESULTS);
    }

    public static byte[] encodePlan(Optional<Plan> plan, WindowKind kind) {
        StrictJson.require(kind != null, "explicit window kind required");
        if (plan.isEmpty()) { return StrictJson.canonical(NullNode.getInstance()); }
        Plan value = plan.orElseThrow(); ObjectNode node = StrictJson.object();
        node.put("policy", kind.policy()); node.put("phase", kind.phase());
        node.put("status", value.status().name().toLowerCase(Locale.ROOT));
        if (value.selectedStep().isPresent()) { node.put("selected_step", WarResultsPolicy.stepText(value.selectedStep().orElseThrow(), kind)); }
        else { node.putNull("selected_step"); }
        node.put("reason", value.reason().wire(kind)); ArrayNode pending = node.putArray("pending_actions");
        WarResultsPolicy.pendingActions(value, kind).forEach(pending::add);
        ObjectNode summary = node.putObject(kind.phase());
        summary.put("presence", value.summary().presence().name().toLowerCase(Locale.ROOT));
        summary.put("close_pending", value.summary().closePending());
        summary.set("query_attempt_status", scalar(value.summary().queryAttemptStatus(), TextNode::valueOf));
        if (kind.checkDueApplies()) {
            summary.set("check_due", scalar(value.summary().checkDue(), BooleanNode::valueOf));
            summary.set("next_check_date_raw", scalar(value.summary().nextCheckDateRaw(), BigIntegerNode::valueOf));
        }
        summary.put("close_action_credit", false);
        return StrictJson.canonical(node);
    }

    /** Legacy tuple's JSON domain is an array; missing binding values project to explicit null. */
    public static byte[] encodeQueryFrame(QueryFrame frame) {
        ArrayNode values = StrictJson.object().putArray("frame");
        values.add(scalar(frame.nativeRevision(), BigIntegerNode::valueOf)); values.add(scalar(frame.dateRaw(), BigIntegerNode::valueOf));
        values.add(scalar(frame.actorId(), BigIntegerNode::valueOf)); values.add(scalar(frame.connectionGeneration(), BigIntegerNode::valueOf));
        values.add(scalar(frame.episodeRunId(), TextNode::valueOf)); values.add(scalar(frame.originalCloseRequestId(), TextNode::valueOf));
        return StrictJson.canonical(values);
    }

    private static Snapshot snapshot(JsonNode value, WindowKind kind) {
        ObjectNode node = object(value); return new Snapshot(binding(node, false), bool(node, "map_ready"), bool(node, "paused"),
                field(node, kind.publicPrefix() + "_observation", WarResultsCodec::observation),
                field(node, kind.publicPrefix() + "_query_attempt", WarResultsCodec::attempt),
                field(node, kind.publicPrefix() + "_close_pending", WarResultsCodec::pending),
                kind.checkDueApplies() ? bool(node, CHECK_DUE) : Field.missing(),
                kind.checkDueApplies() ? field(node, NEXT_CHECK, next -> StrictJson.integer(next, BigInteger.valueOf(Integer.MIN_VALUE),
                        BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.valueOf(6L * 24L)))) : Field.missing());
    }

    private static Observation observation(JsonNode value) {
        ObjectNode node = object(value);
        return new Observation(string(node, "sdk_validation_schema"), binding(node, true), bool(node, "available"),
                bool(node, "post_observed"), bool(node, "scope_unchanged"), bool(node, "post_window_present"),
                bool(node, "post_effective_visible"), bool(node, "close_retry_deferred_for_native_frame"),
                new DispatchAck(bool(node, "accepted"), bool(node, "dispatch_attempted"), bool(node, "dispatch_invoked")));
    }

    private static Attempt attempt(JsonNode value) {
        ObjectNode node = object(value); return new Attempt(string(node, "validation_schema"), binding(node, true),
                string(node, "status"), string(node, "native_request_id"));
    }

    private static PendingClose pending(JsonNode value) {
        ObjectNode node = object(value); return new PendingClose(string(node, "native_request_id"), string(node, "status"));
    }

    private static Binding binding(ObjectNode node, boolean queried) {
        if (queried) {
            return new Binding(string(node, "queried_snapshot_id"), number(node, "queried_revision", false),
                    number(node, "queried_native_revision", false), number(node, "queried_date_raw", true),
                    number(node, "queried_actor_character_id", true), number(node, "queried_connection_generation", false),
                    string(node, "queried_episode_run_id"));
        }
        JsonNode played = node.get("played_character"); JsonNode diagnostics = node.get("diagnostics");
        StrictJson.require(played == null || played.isNull() || played.isObject(), "played_character must be an object or null");
        StrictJson.require(diagnostics == null || diagnostics.isNull() || diagnostics.isObject(), "diagnostics must be an object or null");
        return new Binding(string(node, "snapshot_id"), number(node, "revision", false), number(node, "native_revision", false),
                number(node, "date_raw", true), number(played, "character_id", true), number(diagnostics, "connection_generation", false),
                string(node, "episode_run_id"));
    }

    private static JsonNode encodeSnapshot(Snapshot value, WindowKind kind) {
        ObjectNode node = StrictJson.object(); writeBinding(node, value.binding(), false);
        write(node, "map_ready", value.mapReady(), BooleanNode::valueOf); write(node, "paused", value.paused(), BooleanNode::valueOf);
        write(node, kind.publicPrefix() + "_observation", value.observation(), WarResultsCodec::encodeObservation);
        write(node, kind.publicPrefix() + "_query_attempt", value.queryAttempt(), WarResultsCodec::encodeAttempt);
        write(node, kind.publicPrefix() + "_close_pending", value.closePending(), WarResultsCodec::encodePending);
        if (kind.checkDueApplies()) {
            write(node, CHECK_DUE, value.checkDue(), BooleanNode::valueOf); write(node, NEXT_CHECK, value.nextCheckDateRaw(), BigIntegerNode::valueOf);
        }
        return node;
    }

    private static JsonNode encodeObservation(Observation value) {
        ObjectNode node = StrictJson.object(); write(node, "sdk_validation_schema", value.validationSchema(), TextNode::valueOf);
        writeBinding(node, value.binding(), true); write(node, "available", value.available(), BooleanNode::valueOf);
        write(node, "post_observed", value.postObserved(), BooleanNode::valueOf); write(node, "scope_unchanged", value.scopeUnchanged(), BooleanNode::valueOf);
        write(node, "post_window_present", value.postWindowPresent(), BooleanNode::valueOf);
        write(node, "post_effective_visible", value.postEffectiveVisible(), BooleanNode::valueOf);
        write(node, "close_retry_deferred_for_native_frame", value.retryDeferred(), BooleanNode::valueOf);
        write(node, "accepted", value.dispatchAck().accepted(), BooleanNode::valueOf);
        write(node, "dispatch_attempted", value.dispatchAck().attempted(), BooleanNode::valueOf);
        write(node, "dispatch_invoked", value.dispatchAck().invoked(), BooleanNode::valueOf); return node;
    }

    private static JsonNode encodeAttempt(Attempt value) {
        ObjectNode node = StrictJson.object(); write(node, "validation_schema", value.validationSchema(), TextNode::valueOf);
        writeBinding(node, value.binding(), true); write(node, "status", value.status(), TextNode::valueOf);
        write(node, "native_request_id", value.nativeRequestId(), TextNode::valueOf); return node;
    }

    private static JsonNode encodePending(PendingClose value) {
        ObjectNode node = StrictJson.object(); write(node, "native_request_id", value.nativeRequestId(), TextNode::valueOf);
        write(node, "status", value.status(), TextNode::valueOf); return node;
    }

    private static void writeBinding(ObjectNode node, Binding value, boolean queried) {
        String prefix = queried ? "queried_" : "";
        write(node, prefix + "snapshot_id", value.snapshotId(), TextNode::valueOf);
        write(node, prefix + "revision", value.revision(), BigIntegerNode::valueOf);
        write(node, prefix + "native_revision", value.nativeRevision(), BigIntegerNode::valueOf);
        write(node, prefix + "date_raw", value.dateRaw(), BigIntegerNode::valueOf);
        write(node, prefix + "episode_run_id", value.episodeRunId(), TextNode::valueOf);
        if (queried) {
            write(node, "queried_actor_character_id", value.actorId(), BigIntegerNode::valueOf);
            write(node, "queried_connection_generation", value.connectionGeneration(), BigIntegerNode::valueOf);
        } else {
            if (value.actorId().presence() != FieldPresence.MISSING) { write(node.putObject("played_character"), "character_id", value.actorId(), BigIntegerNode::valueOf); }
            if (value.connectionGeneration().presence() != FieldPresence.MISSING) { write(node.putObject("diagnostics"), "connection_generation", value.connectionGeneration(), BigIntegerNode::valueOf); }
        }
    }

    private static Set<String> strings(JsonNode value) {
        StrictJson.require(value != null && value.isArray() && value.size() <= 512, "bounded string array required");
        Set<String> result = new HashSet<>(); value.forEach(entry -> result.add(text(entry))); return Set.copyOf(result);
    }
    private static String text(JsonNode value) {
        StrictJson.require(value != null && value.isTextual(), "exact JSON string required");
        String text = value.textValue(); if (!text.isEmpty()) { StrictJson.text(text); } return text;
    }
    private static Field<String> string(JsonNode node, String key) { return field(node, key, WarResultsCodec::text); }
    private static Field<Boolean> bool(JsonNode node, String key) {
        return field(node, key, value -> { StrictJson.require(value.isBoolean(), "exact JSON boolean required: " + key); return value.booleanValue(); });
    }
    private static Field<BigInteger> number(JsonNode node, String key, boolean signed32) {
        return field(node, key, value -> StrictJson.integer(value, signed32 ? BigInteger.valueOf(Integer.MIN_VALUE) : BigInteger.ZERO,
                signed32 ? BigInteger.valueOf(Integer.MAX_VALUE) : StrictJson.UINT64_MAX));
    }
    private static <T> Field<T> field(JsonNode node, String key, Function<JsonNode, T> decoder) {
        if (node == null || !node.isObject() || !node.has(key)) { return Field.missing(); }
        JsonNode value = node.get(key); return value.isNull() ? Field.nullValue() : Field.of(decoder.apply(value));
    }
    private static ObjectNode object(JsonNode value) { StrictJson.require(value != null && value.isObject(), "JSON object required"); return (ObjectNode) value; }
    private static <T> JsonNode scalar(Field<T> field, Function<T, JsonNode> encoder) { return field.value().map(encoder).orElse(NullNode.getInstance()); }
    private static <T> void write(ObjectNode node, String key, Field<T> field, Function<T, JsonNode> encoder) {
        if (field.presence() != FieldPresence.MISSING) { node.set(key, scalar(field, encoder)); }
    }
}
