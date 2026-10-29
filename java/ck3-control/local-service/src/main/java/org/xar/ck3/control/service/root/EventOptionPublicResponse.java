package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.events.EventSelectionPublicResult;
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Wraps the installed event producer's verified public result without re-encoding its business fields. */
public final class EventOptionPublicResponse {
    public static final String RECEIPT_SCHEMA = "xar.ck3.public-event-option-receipt/v1";
    public static final String MATERIAL_ENCODING = "xar.event-material-public64/v1";
    public static final int MAXIMUM_RESPONSE_BYTES = 8 * 1024 * 1024;
    private EventOptionPublicResponse() { }
    public static final class Payload {
        private final RawJson original;
        private Payload(RawJson original) { this.original = Objects.requireNonNull(original); }
        public RawJson original() { return original; }
    }

    /** Called after one real execution, still in Root's original writer/archive scope. */
    public static Payload capture(ActionReceipt actual, ActionPorts.OutcomeArchive sameArchive,
            Optional<RawJson> installedVerifiedMaterial) {
        Objects.requireNonNull(actual); Objects.requireNonNull(sameArchive); Objects.requireNonNull(installedVerifiedMaterial);
        ExactRef reference = sameArchive.receiptReferenceOf(actual);
        require(actual.equals(sameArchive.loadReceipt(reference)), "actual public event receipt differs from the sole writer archive");
        ActionCommand command = actual.command();
        EventActionPreparation.OptionNumber option = EventActionPreparation.option(command.operation());
        require(NativeEventPostconditionPort.EVENT_SCHEMA.equals(command.expected().observerSchema()), "actual event selection observer schema required");
        EventActionPreparation.prepare(command); // Shared exact-instance/native-index validator; this performs no dispatch.
        int instance = OpportunityJson.integer(command.arguments().get("event_instance_id"), "actual event instance").intValueExact();
        require(instance > 0, "positive actual event instance required");
        boolean applied = actual.applied().isPresent();
        require(applied == (actual.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED)
                        && applied == installedVerifiedMaterial.isPresent(),
                "event material must be the installed verifier's original Applied result only");
        ObjectNode result = installedVerifiedMaterial.map(original -> {
            EventSelectionPublicResult.parse(original); // Validate its inverse without replacing the public string representation.
            return decode(original);
        }).orElseGet(StrictJson::object);
        require(!result.has("action_receipt") && !result.has("event_material_result_available"),
                "original event business result conflicts with declared public receipt fields");
        if (applied) require(new TextNode(MATERIAL_ENCODING).equals(result.get("event_material_wire_encoding")),
                "actual event material must use the sole installed public64 encoder");
        else result.put("status", actual.outcome() == ActionReceipt.Outcome.UNRESOLVED ? "action_state_unknown" : "event_action_not_applied");
        sameOrAbsent(result, "step", new TextNode(command.operation().value()));
        sameOrAbsent(result, "event_instance_id", StrictJson.object().put("value", instance).get("value"));
        sameOrAbsent(result, "option_number", StrictJson.object().put("value", option.value()).get("value"));
        sameOrAbsent(result, "option_index", StrictJson.object().put("value", option.value() - 1).get("value"));
        result.put("event_material_result_available", applied);
        ObjectNode receipt = result.putObject("action_receipt").put("schema", RECEIPT_SCHEMA)
                .put("action_id", command.actionId()).put("command_body_sha256", actual.bodySha256())
                .put("sequence", Long.toString(actual.sequence())).put("canonical_outcome", actual.outcome().name())
                .put("settled", actual.settled()).put("ack_received", actual.ack().isPresent())
                .put("machine_id", command.before().machineId()).put("session_id", command.sessionId());
        if (actual.ack().isPresent()) receipt.put("native_ok", actual.ack().orElseThrow().nativeOk());
        else receipt.putNull("native_ok");
        if (applied) {
            var observation = actual.applied().orElseThrow().observation();
            boolean advanced = observation.observerSchema().equals(NativeEventPostconditionPort.EVENT_SCHEMA)
                    && observation.actual().stream().anyMatch(value -> value instanceof ExpectedBoolean flag
                            && flag.field().value().equals("old_instance_advanced") && flag.value());
            require(advanced, "applied event receipt lacks independent original-instance advancement");
            receipt.put("old_instance_advanced", true); receipt.set("after", frame(observation.after()));
        } else { receipt.putNull("old_instance_advanced"); receipt.putNull("after"); }
        receipt.set("before", frame(command.before())); receipt.set("original_receipt", reference.toJson());
        return parse(new RawJson(result.toString().getBytes(StandardCharsets.UTF_8)));
    }

    /** Wire validation grants no dispatch, replay, archive authenticity or effect authority. */
    public static Payload parse(RawJson original) {
        ObjectNode root = decode(Objects.requireNonNull(original));
        int option = (int) StrictJson.integer(root.get("option_number"), 1, 999999999);
        long instance = StrictJson.integer(root.get("event_instance_id"), 1, Integer.MAX_VALUE);
        require(StrictJson.integer(root.get("option_index"), 0, 999999998) == option - 1L, "public event option index/number differs");
        require(new TextNode("select-event-option-" + option).equals(root.get("step")), "public event result step differs");
        ObjectNode receipt = StrictJson.object(root.get("action_receipt"), Set.of("schema", "action_id", "command_body_sha256",
                "sequence", "canonical_outcome", "settled", "ack_received", "native_ok", "old_instance_advanced", "machine_id",
                "session_id", "before", "after", "original_receipt"));
        require(new TextNode(RECEIPT_SCHEMA).equals(receipt.get("schema")), "public event receipt schema differs");
        for (String name : Set.of("action_id", "machine_id", "session_id")) StrictJson.text(receipt.get(name));
        require(StrictJson.text(receipt.get("command_body_sha256")).matches("[0-9a-f]{64}"), "public event body SHA differs");
        BigInteger sequence = decimal(receipt.get("sequence"));
        require(sequence.signum() > 0 && sequence.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)) <= 0,
                "positive actual writer receipt sequence required");
        ActionReceipt.Outcome outcome = ActionReceipt.Outcome.valueOf(StrictJson.text(receipt.get("canonical_outcome")));
        boolean settled = bool(receipt.get("settled")), ack = bool(receipt.get("ack_received"));
        boolean available = bool(root.get("event_material_result_available"));
        require(settled == (outcome != ActionReceipt.Outcome.UNRESOLVED), "public event receipt outcome/settlement differs");
        if (ack) bool(receipt.get("native_ok")); else require(receipt.get("native_ok").isNull(), "no ACK cannot invent native_ok");
        validateFrame(object(receipt.get("before"))); ExactRef.fromJson(receipt.get("original_receipt"));
        if (outcome == ActionReceipt.Outcome.APPLIED_CONFIRMED) {
            require(available && bool(receipt.get("old_instance_advanced")), "applied public event result requires independent consumption and original material");
            validateFrame(object(receipt.get("after")));
            require(new TextNode(MATERIAL_ENCODING).equals(root.get("event_material_wire_encoding")), "public event material encoding marker differs");
            ObjectNode material = root.deepCopy(); material.remove("action_receipt"); material.remove("event_material_result_available");
            EventSelectionPublicResult.parse(new RawJson(material.toString().getBytes(StandardCharsets.UTF_8)));
            ObjectNode selection = object(root.get("event_selection"));
            require(StrictJson.integer(selection.get("old_event_instance_id"), 1, Integer.MAX_VALUE) == instance,
                    "public material names a different original event instance");
            ObjectNode before = object(receipt.get("before")), after = object(receipt.get("after"));
            require(Objects.equals(selection.get("starting_revision"), before.get("revision"))
                            && Objects.equals(selection.get("ending_revision"), after.get("revision"))
                            && Objects.equals(selection.get("starting_snapshot_id"), before.get("snapshot_id"))
                            && Objects.equals(selection.get("ending_snapshot_id"), after.get("snapshot_id"))
                            && Objects.equals(selection.get("episode_run_id"), after.get("episode_run_id")),
                    "public event material differs from its original receipt frame descriptors");
        } else {
            require(!available && receipt.get("old_instance_advanced").isNull() && receipt.get("after").isNull(),
                    "nonapplied event receipt cannot claim material, consumption or after frame");
            require(!root.has("event_material_wire_encoding"), "nonapplied result cannot claim a material encoding");
            require(new TextNode(outcome == ActionReceipt.Outcome.UNRESOLVED ? "action_state_unknown" : "event_action_not_applied")
                    .equals(root.get("status")), "nonapplied public event status differs from its canonical receipt");
        }
        safeNumbers(root); return new Payload(original);
    }
    private static ObjectNode decode(RawJson original) {
        require(original.bytes().length <= MAXIMUM_RESPONSE_BYTES, "bounded public event response required");
        return object(OpportunityJson.toNode(DriverJson.object(original.bytes(), MAXIMUM_RESPONSE_BYTES)));
    }
    private static void sameOrAbsent(ObjectNode object, String field, JsonNode expected) {
        JsonNode present = object.get(field);
        boolean equal = present != null && (expected.isIntegralNumber() && present.isIntegralNumber()
                ? expected.bigIntegerValue().equals(present.bigIntegerValue()) : expected.equals(present));
        require(!object.has(field) || equal, "original public event result differs at " + field);
        object.set(field, expected);
    }
    private static ObjectNode frame(ObservationIdentity identity) {
        var f = identity.frame();
        return StrictJson.object().put("snapshot_id", f.snapshotId()).put("episode_run_id", f.episodeRunId())
                .put("revision", f.revision().toString()).put("native_revision", f.identity().nativeRevision().toString())
                .put("date_raw", f.identity().dateRaw().toString()).put("actor_character_id", f.identity().player());
    }
    private static void validateFrame(ObjectNode frame) {
        StrictJson.object(frame, Set.of("snapshot_id", "episode_run_id", "revision", "native_revision", "date_raw", "actor_character_id"));
        StrictJson.text(frame.get("snapshot_id")); StrictJson.text(frame.get("episode_run_id")); uint64(frame.get("revision"));
        require(uint64(frame.get("native_revision")).signum() > 0, "positive public native revision required"); uint64(frame.get("date_raw"));
        StrictJson.integer(frame.get("actor_character_id"), 1, StrictJson.MAX_SAFE_INTEGER);
    }
    private static BigInteger decimal(JsonNode value) {
        require(value != null && value.isTextual(), "canonical public decimal string required"); String token = value.textValue();
        require(token.length() <= 20 && token.matches("0|[1-9][0-9]*"), "canonical bounded nonnegative public decimal required");
        return new BigInteger(token);
    }
    private static BigInteger uint64(JsonNode value) { BigInteger parsed = decimal(value); require(parsed.bitLength() <= 64, "public frame integer exceeds uint64"); return parsed; }
    private static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "exact public event boolean required"); return value.booleanValue(); }
    private static ObjectNode object(JsonNode value) { require(value != null && value.isObject(), "public event object required"); return (ObjectNode) value; }
    private static void safeNumbers(JsonNode value) {
        if (value.isIntegralNumber()) require(value.bigIntegerValue().abs().compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)) <= 0, "undeclared unsafe public event integer");
        else if (value.isContainerNode()) value.forEach(EventOptionPublicResponse::safeNumbers);
    }
    private static void require(boolean valid, String reason) { StrictJson.require(valid, reason); }
}
