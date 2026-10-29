package org.xar.ck3.control.wave2.events.unhandledevent;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ArrayValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.NullValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.Value;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.ActiveEvent;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.AfterAssessment;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.AfterObservation;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.Context;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.FrameBinding;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.NativeSelection;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.Option;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.Plan;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.Request;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.Selection;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.Snapshot;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.Ticket;

/** Exact new wrappers and declared legacy/native projections, with immutable retained diagnostic JSON. */
public final class UnhandledEventCodec {
    public static final String PLAN_SCHEMA = "xar.ck3.unhandled-event-plan-input/v1";
    public static final String AFTER_SCHEMA = "xar.ck3.unhandled-event-after-input/v1";
    private static final List<String> WINDOW_FIELDS = List.of("schema", "schema_version", "status", "unavailable_reason", "window_match_count",
        "event_definition_key", "calculated_event_id", "runtime_stats_ordinal", "current_event_instance_id", "snapshot_revision", "date_raw",
        "root_scope", "saved_scopes", "readiness", "options", "provenance");
    private UnhandledEventCodec() { }
    public record AfterInput(Ticket ticket, AfterObservation observation) { }

    public static Request decodePlan(byte[] raw) {
        ObjectValue root = exact(RetainedJson.parse(raw), Set.of("schema", "snapshot", "event_context", "event_summary", "registry_decision", "action_steps"));
        StrictJson.require(PLAN_SCHEMA.equals(RetainedJson.string(root.get("schema"))), "unhandled plan schema");
        ObjectValue snapshot = objectOrNull(root.get("snapshot"));
        ObjectValue context = objectOrNull(root.get("event_context"));
        List<String> steps = new ArrayList<>();
        Value rawSteps = root.get("action_steps");
        if (!(rawSteps instanceof NullValue)) {
            StrictJson.require(rawSteps instanceof ArrayValue, "action steps array or null");
            for (Value step : ((ArrayValue) rawSteps).values()) {
                String text = RetainedJson.string(step); StrictJson.require(text != null, "action step string required"); steps.add(text);
            }
        }
        return new Request(snapshot(snapshot), context(context), RetainedJson.object(root.get("event_summary")), root.get("registry_decision"), steps);
    }
    public static AfterInput decodeAfter(byte[] raw) {
        ObjectValue root = exact(RetainedJson.parse(raw), Set.of("schema", "ticket", "outcome"));
        StrictJson.require(AFTER_SCHEMA.equals(RetainedJson.string(root.get("schema"))), "unhandled after schema");
        ObjectValue ticket = objectOrNull(root.get("ticket"));
        ObjectValue outcome = objectOrNull(root.get("outcome"));
        ObjectValue result = outcome == null ? null : objectOrNull(outcome.get("result"));
        ObjectValue selection = result == null ? null : objectOrNull(result.get("event_selection"));
        StrictJson.require(selection == null || selection.contains("new_event_instance_id"),
                "native event selection must retain explicit new_event_instance_id, including null");
        Ticket identity = ticket == null ? null : new Ticket(integer(ticket, "current_event_instance_id"), integer(ticket, "selected_native_option_index"));
        NativeSelection selected = selection == null ? null : new NativeSelection(text(selection, "status"), bool(selection, "postcondition_verified"),
            integer(selection, "old_event_instance_id"), integer(selection, "new_event_instance_id"), integer(selection, "selected_native_option_index"));
        return new AfterInput(identity, result == null ? null : new AfterObservation(bool(result, "accepted"), selected));
    }
    public static byte[] encodeRequest(Request request) {
        Value snapshot = request.snapshot() == null ? RetainedJson.NULL : request.snapshot().originalSnapshot();
        List<Value> steps = request.actionSteps().stream().map(RetainedJson::value).toList();
        return RetainedJson.encode(object(field("schema", text(PLAN_SCHEMA)), field("snapshot", snapshot),
            field("event_context", request.context() == null ? RetainedJson.NULL : request.context().retainedWindowContext()),
            field("event_summary", request.eventSummary()), field("registry_decision", request.registryDecision()), field("action_steps", new ArrayValue(steps))));
    }
    public static byte[] encode(Optional<Plan> plan) { return RetainedJson.encode(plan.isPresent() ? legacyPlan(plan.orElseThrow()) : RetainedJson.NULL); }
    public static byte[] encodeAfter(Optional<AfterAssessment> assessment) {
        if (assessment.isEmpty()) return RetainedJson.encode(RetainedJson.NULL);
        AfterAssessment value = assessment.orElseThrow();
        return RetainedJson.encode(object(field("command_acknowledged", bool(value.commandAcknowledged())),
            field("event_instance_advanced_verified", bool(value.eventInstanceAdvancedVerified())), field("replay_allowed", bool(false))));
    }
    public static ObjectValue legacyPlan(Plan plan) {
        Selection selected = plan.selection();
        Value eventKey = RetainedJson.value(plan.eventDefinitionKey());
        Value nativeIndex = RetainedJson.value(selected.nativeOptionIndex());
        Value number = RetainedJson.value(selected.optionNumber());
        Value rendered = RetainedJson.value(selected.renderedIndex());
        ObjectValue summary = plan.originalEventSummary().with("selected_option_number", number).with("selected_native_option_index", nativeIndex)
            .with("selected_rendered_index", rendered).with("semantic_optimal", bool(false));
        List<Value> excluded = selected.excludedDisabledRenderedIndices().stream().map(RetainedJson::value).toList();
        ObjectValue selection = object(field("rendered_index", rendered), field("native_option_index", nativeIndex), field("option_number", number),
            field("resolved_name", RetainedJson.value(selected.resolvedName())), field("enabled", RetainedJson.value(selected.enabled())),
            field("selected_step", RetainedJson.value(selected.selectedStep())),
            field("selection_order", text(plan.displayPolicy().wire())), field("excluded_disabled_rendered_indices", new ArrayValue(excluded)));
        ObjectValue capture = object(field("schema", text(UnhandledEventFallback.SCHEMA)),
            field("policy", text(plan.displayPolicy() == UnhandledEventFallback.DisplayPolicy.EXPLICIT_REQUESTED
                ? "public-explicit-option-capture-before-submit" : "user-authorized-capture-then-first-rendered-option")), field("event_definition_key", eventKey),
            field("current_event_instance_id", RetainedJson.value(plan.eventInstanceId())), field("binding", binding(plan.binding())),
            field("snapshot_option_count", RetainedJson.value(plan.snapshotOptionCount())), field("window_context", plan.windowContext()),
            field("original_registry_decision", plan.originalRegistryDecision()), field("selection", selection),
            field("semantic_optimal", bool(false)), field("native_ai_equivalent", bool(false)), field("offline_followup_required", bool(true)));
        ObjectValue decision = object(field("status", text("user_authorized_fallback")), field("event_definition_key", eventKey),
            field("selected_native_option_index", nativeIndex), field("selected_option_number", number), field("selected_rendered_index", rendered), field("semantic_optimal", bool(false)));
        String phase = switch (plan.phase()) {
            case FIRST_RENDERED_OPTION -> "active_event_unhandled_first_rendered_option";
            case FIRST_RENDERED_DISABLED -> "active_event_unhandled_first_rendered_disabled";
            case FIRST_RENDERED_UNSUPPORTED -> "active_event_unhandled_first_rendered_unsupported";
        };
        if (plan.displayPolicy() == UnhandledEventFallback.DisplayPolicy.EXPLICIT_REQUESTED)
            phase = plan.selectedStep() == null ? "active_event_public_explicit_unavailable" : "active_event_public_explicit_option";
        return object(field("policy", text("one-life-turn-v1")), field("phase", text(phase)), field("selected_step", RetainedJson.value(plan.selectedStep())),
            field("reason", text(plan.reason())), field("active_event", summary), field("event_decision", decision), field("unhandled_event_fallback", capture));
    }
    private static Snapshot snapshot(ObjectValue source) {
        if (source == null) return null;
        ObjectValue actor = objectOrNull(source.get("played_character"));
        ObjectValue diagnostics = objectOrNull(source.get("diagnostics"));
        BigInteger connection = integer(source, "connection_generation");
        BigInteger pid = integer(source, "bridge_pid");
        if (connection == null) connection = integer(diagnostics, "connection_generation");
        if (pid == null) pid = integer(diagnostics, "bridge_pid");
        FrameBinding binding = new FrameBinding(text(source, "snapshot_id"), integer(source, "revision"), integer(source, "native_revision"),
            integer(source, "date_raw"), text(source, "episode_run_id"), connection, pid, bool(source, "paused"), bool(source, "map_ready"), integer(actor, "character_id"));
        // dict.get(active_event, current_event) falls back only when active_event is absent, never for explicit null.
        ObjectValue active = objectOrNull(source.contains("active_event") ? source.get("active_event") : source.get("current_event"));
        return new Snapshot(binding, active == null ? null : new ActiveEvent(integer(active, "instance_id"), integer(active, "option_count")), source);
    }
    private static Context context(ObjectValue source) {
        if (source == null) return null;
        for (String field : List.of("schema_version", "window_match_count", "calculated_event_id", "runtime_stats_ordinal")) integer(source, field);
        Value rawOptions = source.get("options");
        List<Option> options = null;
        if (rawOptions != null && !(rawOptions instanceof NullValue)) {
            StrictJson.require(rawOptions instanceof ArrayValue, "native options array or null"); options = new ArrayList<>();
            for (Value row : ((ArrayValue) rawOptions).values()) {
                ObjectValue option = row instanceof ObjectValue object ? object : null;
                options.add(new Option(integer(option, "rendered_index"), integer(option, "native_option_index"), bool(option, "shown"), bool(option, "enabled"), text(option, "resolved_name")));
            }
        }
        return new Context(integer(source, "current_event_instance_id"), integer(source, "snapshot_revision"), integer(source, "date_raw"),
            text(source, "event_definition_key"), options, source.project(WINDOW_FIELDS));
    }
    private static ObjectValue binding(FrameBinding frame) {
        return object(field("snapshot_id", RetainedJson.value(frame.snapshotId())), field("revision", RetainedJson.value(frame.revision())),
            field("native_revision", RetainedJson.value(frame.nativeRevision())), field("date_raw", RetainedJson.value(frame.dateRaw())),
            field("episode_run_id", RetainedJson.value(frame.episodeRunId())), field("connection_generation", RetainedJson.value(frame.connectionGeneration())),
            field("bridge_pid", RetainedJson.value(frame.bridgePid())), field("paused", RetainedJson.value(frame.paused())),
            field("map_ready", RetainedJson.value(frame.mapReady())), field("actor_character_id", RetainedJson.value(frame.actorCharacterId())));
    }
    private static ObjectValue objectOrNull(Value value) {
        if (value == null || value instanceof NullValue) return null; return RetainedJson.object(value);
    }
    private static BigInteger integer(ObjectValue object, String name) { return object == null ? null : RetainedJson.integer(object.get(name)); }
    private static String text(ObjectValue object, String name) { return object == null ? null : RetainedJson.string(object.get(name)); }
    private static Boolean bool(ObjectValue object, String name) { return object == null ? null : RetainedJson.bool(object.get(name)); }
    private static Value bool(boolean value) { return new RetainedJson.BooleanValue(value); }
    private static Value text(String value) { return new RetainedJson.StringValue(value); }
    private record Field(String name, Value value) { }
    private static Field field(String name, Value value) { return new Field(name, value); }
    private static ObjectValue object(Field... fields) {
        LinkedHashMap<String, Value> values = new LinkedHashMap<>(); for (Field field : fields) values.put(field.name(), field.value()); return new ObjectValue(values);
    }
    private static ObjectValue exact(Value value, Set<String> fields) {
        ObjectValue object = RetainedJson.object(value); StrictJson.require(object.fields().keySet().equals(fields), "exact required wrapper fields"); return object;
    }
}
