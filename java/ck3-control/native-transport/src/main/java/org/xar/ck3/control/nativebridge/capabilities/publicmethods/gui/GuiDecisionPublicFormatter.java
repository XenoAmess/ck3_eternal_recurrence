package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Pure public presentation of five original decision methods; it creates no submission or observation. */
public final class GuiDecisionPublicFormatter {
    private GuiDecisionPublicFormatter() { }

    public static boolean supports(Method method) {
        return method != null && switch (method) {
            case OPEN_DECISIONS, QUERY_DECISION, SELECT_DECISION, CONFIRM_ITEM, CONFIRM_OUTCOME -> true;
            default -> false;
        };
    }

    public static RawJson read(Request request, ReadReply reply, Optional<GuiModels.Context> actualGameContext) {
        Objects.requireNonNull(request); Objects.requireNonNull(reply); Objects.requireNonNull(actualGameContext);
        require(request.method() == Method.QUERY_DECISION,
                "decision formatter requires its exact READ branch");
        GuiModels.Context context = actualGameContext.orElseThrow(() -> new IllegalArgumentException("actual gameplay context required"));
        PlanningReadReceipt receipt = reply.receipt();
        require(receipt.request().origin() instanceof CommandOrigin.Gameplay, "actual gameplay READ original required");
        requireContext(context, receipt.request().before(), receipt.request().source(), receipt.request().sessionId());
        requireRevision(request, context);
        requireBeforeSource(reply.beforeSnapshot(), context);
        require(receipt.before().binding().connectionGeneration().equals(context.connectionGeneration())
                && receipt.after().binding().connectionGeneration().equals(context.connectionGeneration()), "READ connection changed");
        ObjectNode arguments = fields(receipt.request().arguments());
        requireMetadata(arguments, context);
        require(receipt.request().operation().value().equals("query-ingame-decision-item-v1"), "foreign READ operation");
        requireSelector(request, arguments);
        RawJson token = receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("actual READ original absent"));
        ObjectNode result = PublicDataJson.object(token);
        equal(result, "schema", "ck3-ingame-decision-item-v1");
        result = GuiPublicMetadata.decisionFrame(result, context, reply.beforeSnapshot().orElseThrow());
        ObjectNode canonical = result.putObject("canonical_gui_read").put("schema", "xar.java.gui-canonical-read-reference/v1");
        canonical.set("original_receipt", reply.originalReference().toJson());
        parsedReturn(result, reply.parsedReturnReference());
        return GuiCodec.encodePublicOriginal(PublicDataJson.encodePreservingDecimals(result, token));
    }

    public static RawJson action(Request request, ActionReply reply, GuiModels.Context actualGameContext,
            Optional<RawJson> actualLaterObservation, Optional<RawJson> actualSnapshotAfter) {
        Objects.requireNonNull(request); Objects.requireNonNull(reply); Objects.requireNonNull(actualGameContext);
        Objects.requireNonNull(actualLaterObservation); Objects.requireNonNull(actualSnapshotAfter);
        require(supports(request.method()) && request.method().mutation(), "decision formatter requires its exact ACTION branch");
        ActionReceipt receipt = reply.receipt(); ActionCommand command = receipt.command();
        require(command.origin() instanceof CommandOrigin.Gameplay, "actual gameplay ACTION original required");
        requireContext(actualGameContext, command.before(), command.source(), command.sessionId());
        requireRevision(request, actualGameContext);
        requireBeforeSource(reply.beforeSnapshot(), actualGameContext);
        require(command.operation().value().equals(operation(request.method())), "foreign decision ACTION operation");
        ObjectNode commandFields = fields(command.arguments());
        requireMetadata(commandFields, actualGameContext); requireSelector(request, commandFields);
        requireOriginal(reply.archivedReceipt(), reply.originalReference());
        Optional<NativeActionPort.AckReceived> acknowledgement = receipt.ack();
        Optional<RawJson> token = acknowledgement.flatMap(NativeActionPort.AckReceived::originalResultToken);
        ObjectNode result = token.map(PublicDataJson::object).orElseGet(() -> StrictJson.object().put("schema", "xar.ck3.gui-action-result/v1"));
        boolean applied = receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED;
        if (applied) {
            require(receipt.state() instanceof ActionState.Settled settled
                    && settled.settlement() instanceof ActionState.ControlApplied, "actual independent GUI ControlApplied required");
            require(acknowledgement.isPresent() && acknowledgement.orElseThrow().nativeOk() && token.isPresent(), "successful original ACK required");
            RawJson later = actualLaterObservation.orElseThrow(() -> new IllegalArgumentException("actual complete public later observation required"));
            ObjectNode observed = PublicDataJson.object(later);
            requireLaterRole(request, observed);
            equal(result, "schema", request.method() == Method.OPEN_DECISIONS ? "ck3-ingame-decisions-open-v1"
                    : request.method() == Method.CONFIRM_OUTCOME ? "ck3-ingame-decision-outcome-confirm-v1" : "ck3-ingame-decision-item-action-v1");
            result = GuiPublicMetadata.decisionFrame(result, actualGameContext, reply.beforeSnapshot().orElseThrow());
            result.put("postcondition_verified", true).put("verification_pending", false).put("status", successStatus(request));
            result.set(request.method() == Method.OPEN_DECISIONS ? "later_decisions_tree" : "later_actual_observation", observed);
            result.set("native_ack", PublicDataJson.object(token.orElseThrow()));
            result.put("action_request_id", acknowledgement.orElseThrow().requestId());
            if (request.method() == Method.CONFIRM_OUTCOME) {
                RawJson snapshot = actualSnapshotAfter.orElseThrow(() -> new IllegalArgumentException("actual complete public outcome snapshot required"));
                ObjectNode after = PublicDataJson.object(snapshot); requireAfterSnapshot(after, actualGameContext, reply.beforeSnapshot().orElseThrow());
                result.set("snapshot_after", after);
                result.put("verification_scope", "receiver_dispatch_and_declared_ui_outcome")
                        .put("business_effects_verified", false).put("full_product_acceptance_credit", false)
                        .put("front_event_verified", false).put("event_option_selection_authorized", false);
            } else require(actualSnapshotAfter.isEmpty(), "only the original outcome method publishes snapshot_after");
        } else {
            require(actualLaterObservation.isEmpty() && actualSnapshotAfter.isEmpty(), "unsettled/rejected action cannot publish success observations");
            // In particular preserve the original ACK's same-call flags and status on UNKNOWN.
        }
        result.remove("action_claim_path");
        result.put("legacy_claim_path_available", false);
        ObjectNode canonical = result.putObject("canonical_gui_action")
                .put("schema", "xar.java.gui-canonical-action-reference/v1")
                .put("outcome", receipt.outcome().name().toLowerCase(Locale.ROOT))
                .put("action_id", command.actionId()).put("ack_received", acknowledgement.isPresent());
        canonical.set("original_receipt", reply.originalReference().toJson());
        if (acknowledgement.isPresent()) canonical.put("native_request_id", acknowledgement.orElseThrow().requestId());
        parsedReturn(result, reply.parsedReturnReference());
        // The original canonical receipt is the explicit Java replacement for Python's FS claim.
        return GuiCodec.encodePublicOriginal(token.isPresent()
                ? PublicDataJson.encodePreservingDecimals(result, token.orElseThrow()) : PublicDataJson.encode(result));
    }

    private static String operation(Method method) {
        return switch (method) {
            case OPEN_DECISIONS -> "activate-ingame-decisions-v1";
            case SELECT_DECISION -> "select-ingame-decision-item-v1";
            case CONFIRM_ITEM -> "confirm-ingame-decision-item-v1";
            case CONFIRM_OUTCOME -> "confirm-ingame-decision-outcome-v1";
            default -> throw new IllegalArgumentException("not a decision action");
        };
    }
    private static String successStatus(Request request) {
        return switch (request.method()) {
            case OPEN_DECISIONS -> "verified_visible";
            case SELECT_DECISION -> "verified_selected_detail";
            case CONFIRM_ITEM -> "verified_inner_modal_visible";
            case CONFIRM_OUTCOME -> ((ConfirmOutcome) request.arguments()).outcome() == GuiModels.Outcome.EVENT_WINDOW
                    ? "observed_current_event_window" : "observed_decision_detail_closed";
            default -> throw new IllegalArgumentException("not a decision action");
        };
    }
    private static ObjectNode fields(OpportunityJson.Obj arguments) { return (ObjectNode) OpportunityJson.toNode(arguments); }
    private static void requireMetadata(ObjectNode actual, GuiModels.Context context) {
        equal(actual, "_gui_build", context.build().name());
        JsonNode generation = actual.get("_gui_generation");
        require(generation != null && generation.isIntegralNumber()
                && generation.bigIntegerValue().equals(context.connectionGeneration()), "original GUI connection metadata changed");
    }
    private static void requireLaterRole(Request request, ObjectNode later) {
        if (request.method() == Method.SELECT_DECISION) {
            equal(later, "schema", "ck3-ingame-decision-item-v1");
            equal(later, "decision_key", ((Decision) request.arguments()).key().value());
        } else if (request.method() == Method.CONFIRM_OUTCOME
                && ((ConfirmOutcome) request.arguments()).outcome() == GuiModels.Outcome.EVENT_WINDOW) {
            require(later.path("current_event_window_context").isObject()
                    && later.path("current_event_window_context_ready").isBoolean()
                    && later.get("current_event_window_context_ready").booleanValue(), "actual public event context required");
        } else {
            equal(later, "schema", "ck3-native-gui-window-tree-inspection-v1");
            String kind = request.method() == Method.OPEN_DECISIONS ? "decisions"
                    : request.method() == Method.CONFIRM_ITEM ? "vivhite_courtier" : "decision_detail";
            equal(later, "window_kind", kind);
            require(later.path("widgets").isArray() && later.path("root_available").isBoolean()
                    && later.path("truncated").isBoolean(), "actual complete public census required");
        }
    }
    private static void requireAfterSnapshot(ObjectNode after, GuiModels.Context before, RawJson actualBeforeSource) {
        require(after.path("snapshot_id").isTextual() && !after.get("snapshot_id").textValue().isBlank(), "actual public snapshot id required");
        boolean campaign = before.before().observationVersion() == DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION;
        if (campaign) {
            require(after.has("xar_java_snapshot_projection"), "actual profile4 after snapshot representation required");
            PublicSnapshotCodec.decode(PublicDataJson.encodeFullMaterial(after));
        } else require(!after.has("xar_java_snapshot_projection"), "ordinary decision context cannot consume profile4 after snapshot");
        JsonNode expectedEpisode = GuiPublicMetadata.episodeRunId(before, actualBeforeSource);
        JsonNode afterEpisode = after.get("episode_run_id");
        require(expectedEpisode.equals(afterEpisode == null ? com.fasterxml.jackson.databind.node.NullNode.instance : afterEpisode),
                "after snapshot changed its original public episode value");
        require(unsigned(after.get("revision")).compareTo(before.before().frame().revision()) >= 0
                && unsigned(after.get("native_revision")).compareTo(before.before().frame().identity().nativeRevision()) >= 0, "after snapshot revisions regressed");
        JsonNode date = after.get("date_raw"), actor = after.path("played_character").get("character_id");
        require(date != null && date.isIntegralNumber() && date.bigIntegerValue().compareTo(before.before().frame().identity().dateRaw()) >= 0,
                "after snapshot date regressed or changed type");
        require(actor != null && actor.isIntegralNumber() && actor.bigIntegerValue().equals(before.before().frame().identity().player()), "after snapshot actor changed");
    }
    private static java.math.BigInteger unsigned(JsonNode token) {
        if (token != null && token.isIntegralNumber()) {
            java.math.BigInteger value = token.bigIntegerValue();
            require(value.signum() >= 0 && value.bitLength() <= 64, "actual original unsigned identity outside uint64");
            return value;
        }
        return PublicUnsigned64.parse(token, PublicUnsigned64.Minimum.ZERO, PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);
    }
    private static void parsedReturn(ObjectNode result, Optional<RawJson> original) {
        Objects.requireNonNull(original);
        original.ifPresent(value -> {
            GuiPublicMetadata.requireParsedReturnReference(value);
            ObjectNode reference = PublicDataJson.object(value);
            result.set("native_ui_raw_return_receipt", reference);
        });
    }
    private static void requireBeforeSource(Optional<RawJson> original, GuiModels.Context context) {
        RawJson source = original.orElseThrow(() -> new IllegalArgumentException("actual original public before source required"));
        // The common metadata validator checks the retained snapshot identity and diagnostics bundle.
        // Its derived query metadata is not published by the original decision wrappers.
        GuiPublicMetadata.queryFrame(StrictJson.object(), context, source);
    }
    private static void requireSelector(Request request, ObjectNode actual) {
        if (request.arguments() instanceof Decision decision) equal(actual, "decision_key", decision.key().value());
        else if (request.arguments() instanceof ConfirmItem confirm) {
            equal(actual, "decision_key", confirm.key().value()); equal(actual, "expected_window_kind", confirm.window().wire());
        } else if (request.arguments() instanceof ConfirmOutcome confirm) {
            equal(actual, "decision_key", confirm.key().value()); equal(actual, "expected_outcome", confirm.outcome().wire());
            // Empty text is the exact Native closed-outcome representation, not a null alias.
            equal(actual, "expected_event_definition_key", optional(confirm.eventDefinition()).orElse(""));
        }
    }
    private static void equal(ObjectNode actual, String field, String expected) {
        JsonNode value = actual.get(field); require(value != null && value.isTextual() && value.textValue().equals(expected), "decision selector changed: " + field);
    }
    private static void requireRevision(Request request, GuiModels.Context context) {
        if (request.expectedRevision() instanceof PublicUnsigned64.Value value)
            require(value.value().equals(context.before().frame().revision()), "requested public before revision changed");
    }
    private static void requireContext(GuiModels.Context actual,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,
            org.xar.ck3.control.g2.common.G2Source source, String session) {
        require(actual.before().equals(before) && actual.source().equals(source) && actual.sessionId().equals(session), "foreign original before context");
    }
    private static void requireOriginal(byte[] bytes, ExactRef reference) {
        require(bytes.length > 0 && reference.bytes() == bytes.length, "canonical action original length changed");
        try {
            String digest = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));
            require(reference.sha256().equals(digest), "canonical action original digest changed");
        } catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
