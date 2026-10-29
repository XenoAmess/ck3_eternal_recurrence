package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.util.Base64;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeComposer;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence;
import org.xar.ck3.control.wave2.events.interactionreceipt.InteractionReceipt;
import org.xar.ck3.control.wave2.events.interactionreceipt.InteractionReceiptCodec;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;

/** Base64 envelopes retain exact original JSON tokens; 128KiB wire never enlarges the 64KiB original role. */
public final class InteractionHostJson {
    public static final int WIRE_MAXIMUM = 131_072;
    public static final int ORIGINAL_MAXIMUM = 65_536;
    public static final String BEFORE_SCHEMA = "xar.pending-interaction-before-input/v1";
    public static final String RECEIPT_SCHEMA = "xar.pending-interaction-receipt-input/v1";
    public static final String AFTER_SCHEMA = "xar.pending-interaction-after-input/v1";
    private InteractionHostJson() { }
    public record Original(byte[] bytes, String sha256) {
        public Original {
            require(bytes != null && bytes.length > 0 && bytes.length <= ORIGINAL_MAXIMUM && sha(bytes).equals(sha256), "bounded original source pin differs"); bytes = bytes.clone();
        }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    public record BeforeInput(Original planned, String incidentId, String capturedAtUtc) { }
    public sealed interface ReceiptRequest permits ReceiptInput, AfterBodyInput { }
    public record ReceiptInput(Original response, InteractionReceipt.Expected expected, InteractionReceipt.Origin origin,
            InteractionReceipt.ErrorInfo error) implements ReceiptRequest { }
    public record AfterBodyInput(Optional<ObjectValue> ticket, Original response, InteractionReceipt.Origin origin,
            InteractionReceipt.ErrorInfo error, String capturedAtUtc) implements ReceiptRequest { }
    public sealed interface ReceiptOutput permits AssessmentOutput, AfterBodyOutput { }
    public record AssessmentOutput(InteractionReceipt.Assessment assessment) implements ReceiptOutput { }
    public record AfterBodyOutput(Optional<ObjectValue> body) implements ReceiptOutput { }
    public static BeforeInput decodeBefore(byte[] raw) {
        ObjectValue root = exact(raw, Set.of("schema", "original_planned_base64", "original_sha256", "incident_id", "captured_at_utc"));
        require(eq(root, "schema", s(BEFORE_SCHEMA)), "interaction before schema");
        String incident = required(root, "incident_id"), time = required(root, "captured_at_utc");
        // Validate before requesting configured source files.
        new InteractionBeforeEvidence.Identity(incident, time, "portable-validation-only");
        Original planned = original(root, "original_planned_base64");
        InteractionBeforeComposer.compose(planned.bytes(), planned.sha256(), new InteractionBeforeEvidence.Identity(incident, time, "portable-validation-only"),
                new InteractionBeforeEvidence.GuiSourcePin(InteractionFallback.GUI_SOURCE, InteractionFallback.GUI_SHA256));
        return new BeforeInput(planned, incident, time);
    }
    public static InteractionBeforeEvidence.Result before(BeforeInput input, TrustedEventSourceContext trusted) {
        SourceReviewedInteractionContinuation.verifyGui(trusted);
        return InteractionBeforeComposer.compose(input.planned().bytes(), input.planned().sha256(),
                new InteractionBeforeEvidence.Identity(input.incidentId(), input.capturedAtUtc(), trusted.machineId()),
                new InteractionBeforeEvidence.GuiSourcePin(InteractionFallback.GUI_SOURCE, InteractionFallback.GUI_SHA256));
    }
    public static byte[] encodeBefore(InteractionBeforeEvidence.Result result) {
        return result instanceof InteractionBeforeEvidence.Prepared prepared ? prepared.json() : RetainedJson.encode(NULL);
    }
    public static ReceiptRequest decodeReceipt(byte[] raw) {
        require(raw != null && raw.length <= WIRE_MAXIMUM, "interaction input container byte bound exceeded");
        ObjectValue initial = RetainedJson.object(RetainedJson.parse(raw));
        if (eq(initial, "schema", s(AFTER_SCHEMA))) return decodeAfter(raw);
        ObjectValue root = exact(raw, Set.of("schema", "original_response_base64", "original_sha256", "expected", "origin", "error"));
        require(eq(root, "schema", s(RECEIPT_SCHEMA)), "interaction receipt schema");
        ObjectValue expected = o(root, "expected");
        require(expected != null && expected.fields().keySet().equals(Set.of("pending_interaction_id", "action")), "exact interaction expected source identity required");
        java.math.BigInteger id = number(expected, "pending_interaction_id");
        require(id != null && id.bitLength() <= 31 && !id.equals(java.math.BigInteger.valueOf(-1)), "signed pending interaction ID required");
        InteractionReceipt.Action action = action(required(expected, "action"));
        Original source = original(root, "original_response_base64");
        InteractionReceipt.Expected identity = new InteractionReceipt.Expected(id.intValueExact(), action); InteractionReceipt.Origin route = origin(root);
        validateResponse(source, identity, route);
        return new ReceiptInput(source, identity, route, error(root));
    }
    private static InteractionReceipt.Action action(String value) {
        return switch (value) {
            case "accept" -> InteractionReceipt.Action.ACCEPT; case "reject" -> InteractionReceipt.Action.REJECT; case "acknowledge" -> InteractionReceipt.Action.ACKNOWLEDGE;
            default -> throw new IllegalArgumentException("unsupported interaction action");
        };
    }
    private static InteractionReceipt.Origin origin(ObjectValue root) {
        return switch (required(root, "origin")) {
            case "execute_step" -> InteractionReceipt.Origin.EXECUTE_STEP; case "reply_api" -> InteractionReceipt.Origin.REPLY_API; case "acknowledge_api" -> InteractionReceipt.Origin.ACKNOWLEDGE_API;
            default -> throw new IllegalArgumentException("unsupported interaction response origin");
        };
    }
    private static InteractionReceipt.ErrorInfo error(ObjectValue root) {
        if (!(root.get("error") instanceof NullValue)) {
            ObjectValue failure = o(root, "error"); require(failure != null && failure.fields().keySet().equals(Set.of("type", "message")), "exact original failure required");
            require(failure.get("message") instanceof StringValue, "original failure message string required");
            return new InteractionReceipt.ErrorInfo(required(failure, "type"), ((StringValue) failure.get("message")).value());
        }
        return null;
    }
    private static AfterBodyInput decodeAfter(byte[] raw) {
        ObjectValue root = exact(raw, Set.of("schema", "original_response_base64", "original_sha256", "ticket", "origin", "error", "captured_at_utc"));
        require(root.get("ticket") instanceof NullValue || root.get("ticket") instanceof ObjectValue, "original interaction ticket or explicit null required");
        String time = required(root, "captured_at_utc"); org.xar.ck3.control.contracts.StrictJson.utc(time);
        AfterBodyInput input = new AfterBodyInput(Optional.ofNullable(o(root, "ticket")), original(root, "original_response_base64"), origin(root), error(root), time);
        input.ticket().ifPresent(ticket -> validateResponse(input.response(), ticketExpected(ticket), input.origin()));
        return input;
    }
    private static void validateResponse(Original source, InteractionReceipt.Expected expected, InteractionReceipt.Origin route) {
        InteractionReceiptCodec.parseResponse(source.bytes(), source.sha256());
        require(route != InteractionReceipt.Origin.REPLY_API || expected.action() != InteractionReceipt.Action.ACKNOWLEDGE, "reply API cannot encode acknowledgement");
        require(route != InteractionReceipt.Origin.ACKNOWLEDGE_API || expected.action() == InteractionReceipt.Action.ACKNOWLEDGE, "acknowledge API cannot encode acceptance/rejection");
    }
    private static InteractionReceipt.Expected ticketExpected(ObjectValue ticket) {
        String incident = required(ticket, "incident_id"); require(incident.matches("[0-9a-f]{32}"), "original interaction incident ID required");
        ObjectValue before = o(ticket, "before"); require(before != null, "original before source reference required");
        required(before, "path"); require(required(before, "sha256").matches("[0-9a-f]{64}") && positive(number(before, "bytes")), "before original SHA/bytes required");
        java.math.BigInteger pending = number(ticket, "pending_interaction_id");
        require(pending != null && pending.bitLength() <= 31, "original signed pending interaction ID required");
        return new InteractionReceipt.Expected(pending.intValueExact(), action(required(ticket, "action")));
    }
    public static InteractionReceipt.Assessment receipt(ReceiptInput input) {
        return InteractionReceipt.assess(input.expected(), input.origin(), InteractionReceiptCodec.parseResponse(input.response().bytes(), input.response().sha256()), input.error());
    }
    public static byte[] encodeReceipt(InteractionReceipt.Assessment result) { return InteractionReceiptCodec.encodeAssessment(result); }
    public static ReceiptOutput projectReceipt(ReceiptRequest input) {
        return switch (input) {
            case ReceiptInput assessment -> new AssessmentOutput(receipt(assessment));
            case AfterBodyInput after -> new AfterBodyOutput(after(after));
        };
    }
    public static byte[] encodeReceipt(ReceiptOutput output) {
        return switch (output) {
            case AssessmentOutput assessment -> encodeReceipt(assessment.assessment());
            case AfterBodyOutput after -> RetainedJson.encode(after.body().<Value>map(value -> value).orElse(NULL));
        };
    }
    private static Optional<ObjectValue> after(AfterBodyInput input) {
        if (input.ticket().isEmpty()) return Optional.empty();
        ObjectValue ticket = input.ticket().orElseThrow(); String incident = required(ticket, "incident_id");
        ObjectValue before = o(ticket, "before");
        InteractionReceipt.Assessment assessment = receipt(new ReceiptInput(input.response(), ticketExpected(ticket), input.origin(), input.error()));
        Value response = RetainedJson.parse(input.response().bytes()); ObjectValue result = o(response);
        ObjectValue error = input.error() == null ? null : obj(f("type", s(input.error().type())), f("message", s(input.error().message())));
        return Optional.of(obj(f("schema", s("xar.pending-interaction-left-reply/v1")), f("kind", s("pending_character_interaction")),
                f("incident_id", s(incident)), f("stage", s("after_response")), f("captured_at_utc", s(input.capturedAtUtc())), f("before", before),
                f("command_acknowledged", b(assessment.commandAcknowledged() == InteractionReceipt.Ack.ACKNOWLEDGED)),
                f("command_acknowledgement", s(assessment.commandAcknowledged().name().toLowerCase(Locale.ROOT))),
                f("original_pending_advanced_verified", b(assessment.legacyCaptureWouldMarkAdvanced())),
                f("original_pending_advanced_in_response", b(assessment.originalPendingAdvancedInResponse())),
                f("postcondition_scope", s("sdk-response-only")), f("durable_completion_granted", b(false)),
                f("interaction_result", v(result, "interaction_result")), f("remaining_pending_character_interaction", v(result, "remaining_pending_character_interaction")),
                f("action_receipt", result == null ? NULL : projectedReceipt(result)), f("response_assessment", RetainedJson.parse(encodeReceipt(assessment))),
                f("error", error == null ? NULL : error), f("replay_allowed", b(false)), f("material_effects_verified", b(false))));
    }
    private static ObjectValue projectedReceipt(ObjectValue result) {
        ObjectValue receipt = obj();
        for (String field : List.of("step", "accepted", "status", "request_id", "native_request_id", "snapshot_id", "revision", "paused")) receipt = receipt.with(field, v(result, field));
        return receipt;
    }

    public static byte[] encodeRegistry(InteractionRegistry.Result result) {
        ObjectValue reviewed = null; ObjectValue audit;
        if (result instanceof InteractionRegistry.Known known) {
            InteractionRegistry.VerifiedReview review = known.review(); InteractionRegistry.Audit evidence = review.audit();
            reviewed = RetainedJson.object(RetainedJson.parse(InteractionRegistryCodec.encodeEntry(review.entry())));
            audit = obj(f("status", s("offline-source-reviewed")), f("fingerprint", s(evidence.fingerprint())), f("entry_path", s(evidence.entryPath())),
                    f("entry_sha256", s(evidence.entrySha256())), f("source_sha256", s(evidence.sourceSha256())), f("gui_sha256", s(evidence.guiSha256())),
                    f("machine_id", s(evidence.machineId())), f("observed_at_utc", s(evidence.observedAtUtc())), f("material_effects_verified", b(false)));
        } else {
            InteractionRegistry.Unknown unknown = (InteractionRegistry.Unknown) result;
            List<Value> rejected = unknown.rejectedEntries().stream().map(row -> (Value) obj(f("entry", s(row.name())), f("reason", s(row.reason().name().toLowerCase(Locale.ROOT))))).toList();
            audit = obj(f("status", s("unknown")), f("reason", s(unknown.reason().name().toLowerCase(Locale.ROOT))), f("rejected_entries", new ArrayValue(rejected)));
        }
        byte[] raw = RetainedJson.encode(obj(f("schema", s("xar.interaction-registry-result/v1")), f("reviewed", reviewed == null ? NULL : reviewed), f("audit", audit)));
        require(raw.length <= WIRE_MAXIMUM, "registry output container byte bound exceeded"); return raw;
    }
    private static Original original(ObjectValue root, String field) {
        String encoded = required(root, field); byte[] raw = Base64.getDecoder().decode(encoded);
        require(Base64.getEncoder().encodeToString(raw).equals(encoded), "canonical original base64 required");
        return new Original(raw, required(root, "original_sha256"));
    }
    private static ObjectValue exact(byte[] raw, Set<String> fields) {
        require(raw != null && raw.length <= WIRE_MAXIMUM, "interaction input container byte bound exceeded");
        ObjectValue row = RetainedJson.object(RetainedJson.parse(raw)); require(row.fields().keySet().equals(fields), "exact versioned interaction wrapper required"); return row;
    }
    private static String required(ObjectValue row, String field) { String value = text(row, field); require(value != null && !value.isEmpty(), "interaction text required: " + field); return value; }
}
