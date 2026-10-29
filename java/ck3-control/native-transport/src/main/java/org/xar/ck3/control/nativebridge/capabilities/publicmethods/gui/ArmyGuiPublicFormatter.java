package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Pure presentation of the ten original Army/window wrappers. No reads, dispatches or effects. */
public final class ArmyGuiPublicFormatter {
    private ArmyGuiPublicFormatter() { }

    public static boolean supports(Method method) {
        return method != null && switch (method) {
            case OPEN_CHARACTER, SELECT_ARMY, HOVER_ARMY, LEAVE_ARMY, QUERY_ARMY,
                    OPEN_COMBAT, FIT_COMBAT, OPEN_KNIGHTS, QUERY_WINDOW, HOVER_KNIGHTS -> true;
            default -> false;
        };
    }

    public static RawJson read(Request request, ReadReply reply, Optional<GuiModels.Context> actualGameContext) {
        Objects.requireNonNull(request); Objects.requireNonNull(reply); Objects.requireNonNull(actualGameContext);
        require(supports(request.method()) && !request.method().mutation(), "exact Army/window READ method required");
        GuiModels.Context context = actualGameContext.orElseThrow(() -> new IllegalArgumentException("actual gameplay context required"));
        PlanningReadReceipt receipt = reply.receipt();
        require(receipt.request().origin() instanceof CommandOrigin.Gameplay, "original gameplay READ required");
        requireContext(context, receipt.request().before(), receipt.request().source(), receipt.request().sessionId());
        requireRevision(request, context);
        require(receipt.request().operation().value().equals("query-ingame-ui-window-v1"), "foreign Army/window READ operation");
        require(receipt.before().binding().connectionGeneration().equals(context.connectionGeneration())
                && receipt.after().binding().connectionGeneration().equals(context.connectionGeneration()), "Army/window READ connection changed");
        requireArguments(request, fields(receipt.request().arguments()), context);
        require(receipt.original().nativeOk(), "native rejected Army/window READ has no successful public return");
        RawJson token = receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("actual Army/window READ token absent"));
        ObjectNode result = original(request, token, context);
        result = withBefore(result, context, reply.beforeSnapshot());
        ObjectNode canonical = result.putObject("canonical_gui_read").put("schema", "xar.java.gui-canonical-read-reference/v1");
        canonical.set("original_receipt", reply.originalReference().toJson());
        parsedReturn(result, reply.parsedReturnReference());
        return GuiCodec.encodePublicOriginal(PublicDataJson.encodePreservingDecimals(result, token));
    }

    public static RawJson action(Request request, ActionReply reply, GuiModels.Context actualGameContext,
            Optional<RawJson> actualLaterObservation, Optional<RawJson> actualSnapshotAfter) {
        Objects.requireNonNull(request); Objects.requireNonNull(reply); Objects.requireNonNull(actualGameContext);
        Objects.requireNonNull(actualLaterObservation); Objects.requireNonNull(actualSnapshotAfter);
        require(supports(request.method()) && request.method().mutation(), "exact Army/window ACTION method required");
        // These ten Python wrappers return the original same-call UI result. A later canonical
        // ControlApplied belongs to the canonical receipt and must not rewrite its ACK flags.
        require(actualLaterObservation.isEmpty() && actualSnapshotAfter.isEmpty(), "Army/window wrapper publishes no later/after result");
        ActionReceipt receipt = reply.receipt(); ActionCommand command = receipt.command();
        require(command.origin() instanceof CommandOrigin.Gameplay, "original gameplay ACTION required");
        requireContext(actualGameContext, command.before(), command.source(), command.sessionId());
        requireRevision(request, actualGameContext);
        require(command.operation().value().equals("navigate-ingame-ui-v1"), "foreign Army/window ACTION operation");
        requireArguments(request, fields(command.arguments()), actualGameContext);
        requireOriginal(reply.archivedReceipt(), reply.originalReference());
        Optional<NativeActionPort.AckReceived> acknowledgement = receipt.ack();
        if (acknowledgement.isPresent() && !acknowledgement.orElseThrow().nativeOk())
            throw GuiActionFailure.fromRejectedAck(receipt);
        Optional<RawJson> token = acknowledgement.flatMap(NativeActionPort.AckReceived::originalResultToken);
        ObjectNode result;
        if (acknowledgement.isPresent() && acknowledgement.orElseThrow().nativeOk()) {
            require(token.isPresent(), "successful Army/window ACK token absent");
            result = withBefore(original(request, token.orElseThrow(), actualGameContext), actualGameContext, reply.beforeSnapshot());
            parsedReturn(result, reply.parsedReturnReference());
        } else {
            // This is explicitly a canonical unresolved result, never a native UI success.
            require(receipt.outcome() != ActionReceipt.Outcome.APPLIED_CONFIRMED, "confirmed Army/window action lacks native success");
            result = StrictJson.object().put("schema", "xar.ck3.gui-action-result/v1");
            parsedReturn(result, reply.parsedReturnReference());
        }
        ObjectNode canonical = result.putObject("canonical_gui_action")
                .put("schema", "xar.java.gui-canonical-action-reference/v1")
                .put("outcome", receipt.outcome().name().toLowerCase(Locale.ROOT))
                .put("action_id", command.actionId()).put("ack_received", acknowledgement.isPresent());
        canonical.set("original_receipt", reply.originalReference().toJson());
        if (acknowledgement.isPresent()) canonical.put("native_request_id", acknowledgement.orElseThrow().requestId());
        return GuiCodec.encodePublicOriginal(token.isPresent()
                ? PublicDataJson.encodePreservingDecimals(result, token.orElseThrow()) : PublicDataJson.encode(result));
    }

    private record Selector(String kind, String operation, BigInteger subject,
            Optional<GuiModels.TooltipKind> tooltip, Optional<GuiModels.ReceiptId> receipt) { }

    private static Selector selector(Request request) {
        return switch (request.method()) {
            case OPEN_CHARACTER -> subject(request, "character", "open_character");
            case SELECT_ARMY -> subject(request, "army", "select_army");
            case OPEN_COMBAT -> subject(request, "combat", "open_combat");
            case FIT_COMBAT -> subject(request, "combat", "fit_combat_window");
            case OPEN_KNIGHTS -> new Selector("knights", "open_knights", BigInteger.ZERO, Optional.empty(), Optional.empty());
            case HOVER_KNIGHTS -> {
                KnightHover value = (KnightHover) request.arguments();
                yield new Selector("combat", "hover_" + value.side().wire() + "_knights", value.combat().value(), Optional.empty(), Optional.empty());
            }
            case HOVER_ARMY, LEAVE_ARMY, QUERY_ARMY -> {
                ArmyTooltip value = (ArmyTooltip) request.arguments();
                String operation = request.method() == Method.HOVER_ARMY ? "hover_army_tooltip"
                        : request.method() == Method.LEAVE_ARMY ? "leave_army_tooltip" : "query";
                yield new Selector("army", operation, value.army().value(), Optional.of(value.kind()), optional(value.receipt()));
            }
            case QUERY_WINDOW -> {
                String kind = ((WindowQuery) request.arguments()).kind();
                require(!kind.equals("inventory"), "inventory retains its own installed original reader");
                yield new Selector(kind, "query", BigInteger.ZERO, Optional.empty(), Optional.empty());
            }
            default -> throw new IllegalArgumentException("not an Army/window wrapper");
        };
    }
    private static Selector subject(Request request, String kind, String operation) {
        return new Selector(kind, operation, ((Subject) request.arguments()).value().value(), Optional.empty(), Optional.empty());
    }
    private static void requireArguments(Request request, ObjectNode actual, GuiModels.Context context) {
        Selector expected = selector(request);
        equal(actual, "_gui_build", context.build().name());
        integer(actual, "_gui_generation", context.connectionGeneration());
        equal(actual, "window_kind", expected.kind()); integer(actual, "subject_id", expected.subject());
        if (request.method().mutation()) equal(actual, "operation", expected.operation());
        else require(!actual.has("operation"), "query must not contain a navigation operation");
        if (expected.tooltip().isPresent()) equal(actual, "army_tooltip_kind", expected.tooltip().orElseThrow().wire());
        else require(!actual.has("army_tooltip_kind"), "unsolicited Army tooltip selector");
        if (expected.receipt().isPresent()) equal(actual, "army_tooltip_receipt", expected.receipt().orElseThrow().value());
        else require(!actual.has("army_tooltip_receipt"), "unsolicited Army tooltip receipt");
    }
    private static ObjectNode original(Request request, RawJson token, GuiModels.Context context) {
        ObjectNode result = PublicDataJson.object(token); Selector expected = selector(request);
        equal(result, "schema", "ck3-ingame-ui-window-v1"); equal(result, "window_kind", expected.kind());
        integer(result, "requested_subject_id", expected.subject());
        integer(result, "native_revision", context.before().frame().identity().nativeRevision());
        integer(result, "date_raw", context.before().frame().identity().dateRaw());
        integer(result, "played_character_id", context.before().frame().identity().player());
        // The existing registered producer/decoder owns full native validation; this formatter
        // additionally prevents cross-role projection without guessing optional domain fields.
        require(result.path("verification_pending").isBoolean() && result.path("dispatch_invoked").isBoolean()
                && result.path("status").isTextual(), "actual original UI status/flags required");
        result.put("backend_id", "native-headless");
        return result;
    }
    private static ObjectNode withBefore(ObjectNode result, GuiModels.Context context, Optional<RawJson> before) {
        return GuiPublicMetadata.queryFrame(result, context, before.orElseThrow(
                () -> new IllegalArgumentException("actual original public before snapshot and Driver diagnostics required")));
    }
    private static void parsedReturn(ObjectNode result, Optional<RawJson> reference) {
        reference.ifPresent(value -> {
            GuiPublicMetadata.requireParsedReturnReference(value);
            result.set("native_ui_raw_return_receipt", PublicDataJson.object(value));
        });
    }
    private static ObjectNode fields(OpportunityJson.Obj arguments) { return (ObjectNode) OpportunityJson.toNode(arguments); }
    private static void requireContext(GuiModels.Context actual, ObservationIdentity before, G2Source source, String session) {
        require(actual.before().equals(before) && actual.source().equals(source) && actual.sessionId().equals(session), "Army/window original before context changed");
    }
    private static void requireRevision(Request request, GuiModels.Context context) {
        require(request.expectedRevision() instanceof PublicUnsigned64.Value value
                && value.value().equals(context.before().frame().revision()), "Army/window public expected revision changed");
    }
    private static void requireOriginal(byte[] bytes, ExactRef reference) {
        require(bytes.length > 0 && reference.bytes() == bytes.length, "canonical Army/window original length changed");
        try {
            String digest = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));
            require(reference.sha256().equals(digest), "canonical Army/window original digest changed");
        } catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    private static void equal(ObjectNode node, String field, String expected) {
        JsonNode value = node.get(field);
        require(value != null && value.isTextual() && value.textValue().equals(expected), "Army/window selector changed: " + field);
    }
    private static void integer(ObjectNode node, String field, BigInteger expected) {
        JsonNode value = node.get(field);
        require(value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(expected), "Army/window integer changed: " + field);
    }
}
