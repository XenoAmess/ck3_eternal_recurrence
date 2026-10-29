package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiWhiteOriginals;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiPresentationResult;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;

/** Original eight public wrappers over actual archived data; no observation or submission here. */
public final class GuiFaithWhitePublicFormatter {
    private static final Set<Method> FAITH = Set.of(Method.OPEN_FAITH, Method.PRESENT,
            Method.QUERY_PRESENT, Method.QUERY_PRESENT_TOOLTIP);
    private static final Set<Method> WHITE = Set.of(Method.WHITE_AGE, Method.WHITE_NUMERIC,
            Method.WHITE_BUSINESS, Method.WHITE_TEXT);
    public record WhiteEvidence(GuiWhiteOriginals.Before before, Optional<ActionState.ControlApplied> after) {
        public WhiteEvidence { Objects.requireNonNull(before); Objects.requireNonNull(after); }
    }
    private GuiFaithWhitePublicFormatter() { }
    public static boolean supports(Method method) { return FAITH.contains(method) || WHITE.contains(method); }
    public static boolean white(Method method) { return WHITE.contains(method); }

    public static RawJson read(Request request, ReadReply reply, GuiModels.Context context, RawJson actualBeforeSource) {
        require(supports(request.method()) && !request.submitsAction(), "owned actual Faith/White READ required");
        var receipt = reply.receipt();
        require(receipt.request().before().equals(context.before()) && receipt.request().source().equals(context.source())
                && receipt.request().sessionId().equals(context.sessionId()), "Faith/White READ crossed actual before source");
        RawJson token = receipt.original().originalResultToken().orElseThrow();
        ObjectNode out = PublicDataJson.object(token);
        if (FAITH.contains(request.method())) {
            require(receipt.request().operation().value().equals("query-ingame-ui-window-v1"), "original Faith READ operation required");
            requireFaithRequest(request, context, (ObjectNode)OpportunityJson.toNode(receipt.request().arguments()), false);
            requireFaithDto(request,context,out,(ObjectNode)OpportunityJson.toNode(receipt.request().arguments()),false);
            out = GuiPublicMetadata.queryFrame(out, context, actualBeforeSource);
            if (!out.has("backend_id")) out.put("backend_id", "native-headless");
            parsedReturn(out, reply.parsedReturnReference());
        } else {
            require(receipt.request().operation().value().equals(request.method() == Method.WHITE_BUSINESS
                    ? "query-white-player-business-variables-v1" : "query-white-rendered-text-v1"), "exact original White READ required");
            out = whiteRead(receipt, context, actualBeforeSource, request.method() == Method.WHITE_BUSINESS);
        }
        return GuiCodec.encodePublicOriginal(PublicDataJson.encodePreservingFullMaterial(out, token));
    }

    /** Actual Root reopens the four originals before calling this pure formatter. */
    public static RawJson action(Request request, ActionReply reply, GuiModels.Context context, RawJson actualBeforeSource,
            Optional<WhiteEvidence> whiteEvidence) {
        require(supports(request.method()) && request.submitsAction(), "owned actual Faith/White ACTION required");
        var receipt = reply.receipt(); var command = receipt.command();
        require(command.before().equals(context.before()) && command.source().equals(context.source())
                && command.sessionId().equals(context.sessionId()), "Faith/White action crossed actual before source");
        if (FAITH.contains(request.method())) {
            require(whiteEvidence.isEmpty(), "Faith wrapper cannot consume White evidence");
            require(command.operation().value().equals("navigate-ingame-ui-v1"), "original Faith navigation operation required");
            requireFaithRequest(request, context, GuiService.argumentFields(command), true);
            if(receipt.ack().isEmpty())return GuiCodec.encode(reply);
            var acknowledgement = receipt.ack().orElseThrow(() -> new IllegalArgumentException("actual Faith ACK absent"));
            if (!acknowledgement.nativeOk()) throw GuiActionFailure.fromRejectedAck(receipt);
            RawJson token = acknowledgement.originalResultToken().orElseThrow();
            requireFaithDto(request,context,PublicDataJson.object(token),GuiService.argumentFields(command),true);
            ObjectNode out = GuiPublicMetadata.queryFrame(PublicDataJson.object(token), context, actualBeforeSource);
            if (!out.has("backend_id")) out.put("backend_id", "native-headless");
            // Same-call native UI status and flags retain their original meaning, as in the Army wrapper.
            parsedReturn(out, reply.parsedReturnReference()); canonical(out, reply);
            return GuiCodec.encodePublicOriginal(PublicDataJson.encodePreservingFullMaterial(out, token));
        }
        requireWhiteRequest(request, context, command);
        WhiteEvidence originals = whiteEvidence.orElseThrow(() -> new IllegalArgumentException("actual archived White originals required"));
        if (receipt.outcome() != ActionReceipt.Outcome.APPLIED_CONFIRMED) {
            require(originals.after().isEmpty(), "unresolved White action cannot publish business success");
            return GuiCodec.encode(reply);
        }
        require(receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied,
                "actual durable White double-READ settlement required");
        var control = originals.after().orElseThrow();
        require(control.equals(((ActionState.Settled) receipt.state()).settlement()) && control.supportingReads().size() == 1,
                "White public evidence differs from the actual durable settlement");
        var ack = receipt.ack().orElseThrow(); RawJson token = ack.originalResultToken().orElseThrow();
        ObjectNode fields = GuiService.argumentFields(command), out = PublicDataJson.object(token);
        GuiWhiteOriginals.requireAck(out, context, fields, command.operation().value());
        ObjectNode beforeBusiness = whiteRead(originals.before().business(), context, actualBeforeSource, true);
        ObjectNode beforeText = whiteRead(originals.before().text(), context, actualBeforeSource, false);
        ObjectNode laterBusiness = whiteRead(control.read(), context, actualBeforeSource, true);
        ObjectNode laterText = whiteRead(control.supportingReads().getFirst(), context, actualBeforeSource, false);
        out = GuiPublicMetadata.decisionFrame(out, context, actualBeforeSource);
        out.put("postcondition_verified", true).put("independent_business_after_verified", true)
                .put("independent_rendered_text_after_verified", true).put("full_gui_acceptance_credit", false)
                .put("intent_id", StrictJson.text(fields.get("_gui_intent_id")));
        out.set("before_business", beforeBusiness); out.set("before_rendered_text", beforeText);
        out.set("later_actual_business", laterBusiness); out.set("later_actual_rendered_text", laterText);
        if (request.method() == Method.WHITE_NUMERIC) {
            String price = GuiModels.TextName.PRICE.wire();
            out.put("actual_price_before_after_bound", true).put("price_formula_verified", false)
                    .put("actual_price_before", StrictJson.text(beforeText.path("fields").path(price).get("text_utf8")))
                    .put("actual_price_after", StrictJson.text(laterText.path("fields").path(price).get("text_utf8")));
        }
        out.put("legacy_claim_path_available", false); canonical(out, reply);
        return GuiCodec.encodePublicOriginal(PublicDataJson.encodePreservingFullMaterial(out, token));
    }

    private static ObjectNode whiteRead(PlanningReadReceipt receipt, GuiModels.Context context,
            RawJson actualBeforeSource, boolean business) {
        require(context.build() == GuiModels.Build.CROZIER3, "original fixed White wrappers require exact .3 build");
        require(receipt.request().operation().value().equals(business
                ? "query-white-player-business-variables-v1" : "query-white-rendered-text-v1"), "White archived READ roles were swapped");
        require(receipt.request().before().equals(context.before()) && receipt.request().source().equals(context.source())
                && receipt.request().sessionId().equals(context.sessionId()), "White archived READ crossed actual before source");
        ObjectNode out = PublicDataJson.object(receipt.original().originalResultToken().orElseThrow());
        out = GuiPublicMetadata.readFrame(out, context, actualBeforeSource);
        out.put(business ? "gui_acceptance_credit" : "full_gui_acceptance_credit", false);
        return out;
    }
    private static void requireWhiteRequest(Request request, GuiModels.Context context, ActionCommand command) {
        ObjectNode fields=GuiService.argumentFields(command);
        require(command.actionId().equals(GuiService.actionId(request,context)),"White original intent/episode identity changed");
        if(request.arguments() instanceof WhiteAge age){
            require(command.operation().value().equals("click-white-control-v1")
                    &&StrictJson.text(fields.get("control")).equals("age_plus_1")
                    &&fields.get("expected_before_age").isIntegralNumber()
                    &&fields.get("expected_before_age").bigIntegerValue().equals(java.math.BigInteger.valueOf(age.before()))
                    &&StrictJson.text(fields.get("_gui_intent_id")).equals(age.intentId()),"White original age request changed");
        }else{
            WhiteNumeric numeric=(WhiteNumeric)request.arguments();
            require(command.operation().value().equals("click-white-numeric-control-v1")
                    &&StrictJson.text(fields.get("control")).equals(numeric.control().wire())
                    &&fields.get("expected_before_value").isIntegralNumber()
                    &&fields.get("expected_before_value").bigIntegerValue().equals(java.math.BigInteger.valueOf(numeric.before()))
                    &&StrictJson.text(fields.get("expected_before_price_text")).equals(numeric.price())
                    &&StrictJson.text(fields.get("_gui_intent_id")).equals(numeric.intentId()),"White original numeric request changed");
        }
    }
    private static void requireFaithRequest(Request request, GuiModels.Context context, ObjectNode actual, boolean action) {
        if(request.expectedRevision() instanceof org.xar.ck3.control.contracts.PublicUnsigned64.Value revision)
            require(revision.value().equals(context.before().frame().revision()),"original Faith public revision changed");
        ObjectNode expected = GuiService.metadata(context);
        if(request.method()==Method.OPEN_FAITH){
            require(action,"Faith opening is an actual navigation action");
            expected.put("window_kind","faith").put("subject_id",((Subject)request.arguments()).value().value())
                    .put("operation","open_faith").put("_gui_verify","visible");
        }else{
            GuiModels.Presentation presentation=((Presentation)request.arguments()).nativeRequest(request.method());
            expected.put("window_kind",presentation.kind().wire()).put("subject_id",presentation.subject().value());
            presentation.target().ifPresent(value->expected.put("presentation_target",value));
            presentation.index().ifPresent(value->expected.put("presentation_index",value));
            presentation.tab().ifPresent(value->expected.put("presentation_tab",value));
            presentation.receipt().ifPresent(value->expected.put("presentation_receipt",value.value()));
            if(action)expected.put("operation",presentation.operation()).put("_gui_verify",
                    presentation.operation().equals("select_presentation_tab")?"tab":"presentation");
        }
        require(expected.equals(actual),"Faith formatter received a different actual selector/request");
    }
    private static void requireFaithDto(Request request,GuiModels.Context context,ObjectNode actual,ObjectNode fields,boolean action){
        GuiModels.WindowKind kind=GuiModels.WindowKind.parse(StrictJson.text(fields.get("window_kind")));
        GuiModels.Subject subject=new GuiModels.Subject(StrictJson.integer(fields.get("subject_id"),java.math.BigInteger.ZERO,java.math.BigInteger.ONE.shiftLeft(32).subtract(java.math.BigInteger.TWO)));
        GuiPresentationResult.validate(actual,context,action?StrictJson.text(fields.get("operation")):"query",kind,subject,fields);
    }
    private static void parsedReturn(ObjectNode out, Optional<RawJson> original) {
        original.ifPresent(value -> { GuiPublicMetadata.requireParsedReturnReference(value);
            out.set("native_ui_raw_return_receipt", PublicDataJson.object(value)); });
    }
    private static void canonical(ObjectNode out, ActionReply reply) {
        var receipt = reply.receipt();
        out.putObject("canonical_gui_action").put("schema", "xar.java.gui-canonical-action-reference/v1")
                .put("outcome", receipt.outcome().name().toLowerCase(Locale.ROOT))
                .put("action_id", receipt.command().actionId()).put("ack_received", receipt.ack().isPresent())
                .set("original_receipt", reply.originalReference().toJson());
    }
    private static void require(boolean ok, String reason) { if (!ok) throw new IllegalArgumentException(reason); }
}
