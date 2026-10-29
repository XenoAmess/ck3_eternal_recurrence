package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Original unhandled incident bodies; durable storage and gameplay submission stay with their owners. */
public final class UnhandledEventEvidenceJson {
    public static final String BEFORE_SCHEMA = "xar.events-unhandled-before-body-input/v1";
    public static final String AFTER_SCHEMA = "xar.events-unhandled-after-body-input/v1";
    private static final String CAPTURE_SCHEMA = "xar.unhandled-event-first-rendered/v1";
    private static final List<String> RECEIPT_FIELDS = List.of("step", "accepted", "status", "query_sequence", "request_id",
            "native_request_id", "snapshot_id", "revision", "progress_status");
    private UnhandledEventEvidenceJson() { }

    public record BeforeInput(Optional<ObjectValue> planned, String incidentId, String capturedAtUtc) {
        public BeforeInput { Objects.requireNonNull(planned); requireText(incidentId); requireText(capturedAtUtc); planned.ifPresent(UnhandledEventEvidenceJson::validateBeforeShapes); }
    }
    public record AfterInput(Optional<ObjectValue> ticket, Optional<ObjectValue> outcome, Value error, String capturedAtUtc) {
        public AfterInput { Objects.requireNonNull(ticket); Objects.requireNonNull(outcome); Objects.requireNonNull(error); requireText(capturedAtUtc); ticket.ifPresent(UnhandledEventEvidenceJson::validateTicketShapes); }
    }

    public static BeforeInput decodeBefore(byte[] raw) {
        ObjectValue root = exact(parse(raw), Set.of("schema", "planned", "incident_id", "captured_at_utc"));
        require(BEFORE_SCHEMA.equals(text(root, "schema")), "unhandled before schema");
        return new BeforeInput(nullableObject(root.get("planned")), requiredText(root, "incident_id"), requiredText(root, "captured_at_utc"));
    }

    public static Optional<ObjectValue> before(BeforeInput input) {
        ObjectValue planned = input.planned().orElse(null); ObjectValue plan = o(planned, "plan");
        ObjectValue capture = o(plan, "unhandled_event_fallback");
        if (capture == null) return Optional.empty();
        ObjectValue selection = o(capture, "selection"); ObjectValue binding = o(capture, "binding");
        Value selected = v(plan, "selected_step");
        domainRequire(CAPTURE_SCHEMA.equals(text(capture, "schema")) && selection != null && binding != null,
                "unhandled event capture missing original selection/frame");
        domainRequire(selected instanceof NullValue || selected instanceof StringValue, "selected step string or null required");
        domainRequire(selected instanceof NullValue || selected.equals(v(selection, "selected_step")), "planned selection differs");
        domainRequire(selected instanceof NullValue || yes(selection, "enabled"), "disabled selection cannot be submitted");
        domainRequire(v(planned, "snapshot_id").equals(v(binding, "snapshot_id"))
                && v(planned, "revision").equals(v(binding, "revision")), "unhandled planned frame differs");
        domainRequire(number(planned, "revision") != null && number(binding, "revision") != null, "actual planned revision integer required");
        domainRequire(positive(number(capture, "current_event_instance_id")) && number(selection, "native_option_index") != null
                && number(selection, "native_option_index").signum() >= 0, "actual event/option identity integer required");
        return Optional.of(put(capture, f("incident_id", s(input.incidentId())), f("stage", s("before_submission")),
                f("captured_at_utc", s(input.capturedAtUtc())), f("dispatch_attempted", b(false))));
    }

    public static AfterInput decodeAfter(byte[] raw) {
        ObjectValue root = exact(parse(raw), Set.of("schema", "ticket", "outcome", "error", "captured_at_utc"));
        require(AFTER_SCHEMA.equals(text(root, "schema")), "unhandled after body schema");
        Value error = root.get("error");
        if (!(error instanceof NullValue)) {
            ObjectValue item = exact(error, Set.of("type", "message")); requiredText(item, "type");
            require(item.get("message") instanceof StringValue, "error message string required");
        }
        Optional<ObjectValue> ticket = nullableObject(root.get("ticket")), outcome = nullableObject(root.get("outcome"));
        // Validate the nested legacy receipt shapes at the JSON decode boundary.
        UnhandledEventCodec.decodeAfter(encode(obj(f("schema", s(UnhandledEventCodec.AFTER_SCHEMA)),
                f("ticket", ticket.<Value>map(value -> value).orElse(NULL)),
                f("outcome", outcome.<Value>map(value -> value).orElse(NULL)))));
        return new AfterInput(ticket, outcome, error, requiredText(root, "captured_at_utc"));
    }

    public static Optional<ObjectValue> after(AfterInput input) {
        if (input.ticket().isEmpty()) return Optional.empty();
        ObjectValue ticket = input.ticket().orElseThrow(); String incident = domainText(ticket, "incident_id");
        ObjectValue before = o(ticket, "before"); domainRequire(before != null, "original before reference required");
        domainText(before, "path"); String sha = domainText(before, "sha256");
        domainRequire(sha.matches("[0-9a-fA-F]{64}") && positive(number(before, "bytes")), "exact before reference required");
        ObjectValue outcome = input.outcome().orElse(null); ObjectValue result = o(outcome, "result");
        UnhandledEventCodec.AfterInput assessmentInput = UnhandledEventCodec.decodeAfter(encode(obj(
                f("schema", s(UnhandledEventCodec.AFTER_SCHEMA)), f("ticket", ticket), f("outcome", outcome == null ? NULL : outcome))));
        UnhandledEventFallback.AfterAssessment assessment = UnhandledEventFallback.assessAfter(
                assessmentInput.ticket(), assessmentInput.observation()).orElseThrow();
        return Optional.of(obj(f("schema", s(CAPTURE_SCHEMA)), f("incident_id", s(incident)), f("stage", s("after_response")),
                f("captured_at_utc", s(input.capturedAtUtc())), f("before", before),
                f("command_acknowledged", b(assessment.commandAcknowledged())),
                f("event_instance_advanced_verified", b(assessment.eventInstanceAdvancedVerified())),
                f("result_status", v(outcome, "status")), f("event_selection", v(result, "event_selection")),
                f("action_receipt", result == null ? NULL : result.project(RECEIPT_FIELDS)), f("error", input.error()), f("replay_allowed", b(false))));
    }

    public static byte[] encodeBody(Optional<ObjectValue> body) { return encode(body.<Value>map(value -> value).orElse(NULL)); }

    private static ObjectValue exact(Value value, Set<String> fields) {
        ObjectValue result = o(value); require(result != null && result.fields().keySet().equals(fields), "exact versioned unhandled body wrapper required");
        return result;
    }
    private static Optional<ObjectValue> nullableObject(Value value) {
        require(value instanceof NullValue || value instanceof ObjectValue, "object or explicit null required");
        return Optional.ofNullable(o(value));
    }
    private static String requiredText(ObjectValue object, String field) { String value = text(object, field); requireText(value); return value; }
    private static void requireText(String value) { require(value != null && !value.isEmpty(), "nonempty unhandled body text required"); }
    private static void validateBeforeShapes(ObjectValue planned) {
        ObjectValue capture = o(o(planned, "plan"), "unhandled_event_fallback");
        if (capture == null) return;
        text(capture, "schema"); number(planned, "revision"); number(o(capture, "binding"), "revision");
        number(capture, "current_event_instance_id"); number(o(capture, "selection"), "native_option_index");
    }
    private static void validateTicketShapes(ObjectValue ticket) {
        text(ticket, "incident_id"); ObjectValue before = o(ticket, "before");
        text(before, "path"); text(before, "sha256"); number(before, "bytes");
    }
    private static void domainRequire(boolean accepted, String message) {
        if (!accepted) throw new ProjectionDomainRejection(message);
    }
    private static String domainText(ObjectValue object, String key) {
        String value = text(object, key);
        domainRequire(value != null && !value.isEmpty(), "nonempty unhandled body text required");
        return value;
    }

}
