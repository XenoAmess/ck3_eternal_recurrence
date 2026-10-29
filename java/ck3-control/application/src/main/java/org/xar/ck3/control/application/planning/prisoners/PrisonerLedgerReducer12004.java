package org.xar.ck3.control.application.planning.prisoners;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;

/** Pure existing-body reduction. The sole writer's verifier must first prove canonical action membership and replay its actual originals. */
public final class PrisonerLedgerReducer12004 {
    private PrisonerLedgerReducer12004() { }
    public static void validate(PrisonerPlanningPorts.Family family, JsonNode body) {
        Objects.requireNonNull(family);
        if(PrisonerEpisodeLedger12004.isV2(family,body)) {
            PrisonerEpisodeLedger12004.decode(family,new RawJson(StrictJson.canonical(body,1_048_576)));return;
        }
        StrictJson.require(body != null && body.isObject() && body.has("pending") && (body.get("pending").isNull() || body.get("pending").isObject()), "explicit original pending field required");
        Set<String> fields = new java.util.HashSet<>(Set.of("pending")); if (body.has("resolved")) fields.add("resolved");
        if (family == PrisonerPlanningPorts.Family.RANSOM) {
            fields.add("schema"); StrictJson.require("xar.ck3.prisoner-ransom-formal.v1".equals(StrictJson.text(body.get("schema"))), "exact ransom domain schema required");
            StrictJson.require(body.has("resolved"), "ransom resolved field is mandatory");
        }
        StrictJson.object(body, fields);
        if (body.has("resolved")) StrictJson.require(body.get("resolved").isNull() || body.get("resolved").isObject(), "resolved must be explicit object/null");
        if (!body.get("pending").isNull()) PrisonerPendingIdentity12004.decode(family, new RawJson(StrictJson.canonical(body.get("pending"))));
    }
    /** The caller replays the actual selected read and preparation under the original writer lock before this pure reduction. */
    public static RawJson prepare(PrisonerPlanningPorts.Family family, RawJson actualPreviousBody,
            ActionCommand command, PrisonerActionBinding12004.SelectedRead selected) {
        JsonNode previous = StrictJson.parse(actualPreviousBody.bytes(), 1_048_576); validate(family, previous);
        if(PrisonerEpisodeLedger12004.isV2(family,previous))PrisonerEpisodeLedger12004.decode(family,actualPreviousBody).epoch().owner()
                .require(command.before(),command.source(),command.sessionId());
        StrictJson.require(previous.get("pending").isNull(), "existing pending cannot be overwritten by a new command");
        OperationKey expected = family == PrisonerPlanningPorts.Family.RELEASE ? PrisonerOrdinaryPolicy12004.RELEASE : PrisonerOrdinaryPolicy12004.RANSOM;
        StrictJson.require(command.operation().equals(expected) && PrisonerActionBinding12004.selectedFrameMatches(command,selected.receipt())
                && selected.receipt().request().source().equals(command.source())
                && selected.receipt().request().sessionId().equals(command.sessionId()), "pending producer requires its actual selected command/read pair");
        JsonNode args = StrictJson.parse(OpportunityJson.encode(command.arguments()), ActionCommand.MAX_ARGUMENT_BYTES);
        ObjectNode pending = StrictJson.object().put("stage", "submission_unresolved").put("action_id", command.actionId())
                .put("player_character_id", command.before().frame().identity().player())
                .put("prisoner_character_id", PrisonerActionBinding12004.id(args.get("prisoner_character_id")))
                .put("pre_native_revision", command.before().frame().identity().nativeRevision())
                .put("pre_public_revision", command.before().frame().revision())
                .put("pre_date_raw", command.before().frame().identity().dateRaw()).put("material_result", false);
        if (family == PrisonerPlanningPorts.Family.RELEASE) {
            pending.set("release_query_sequence", args.get("release_query_sequence"));
            pending.set("release_option_mask_bits", args.get("release_option_mask_bits"));
            var keys = pending.putArray("release_option_keys");
            if (selected.intent().options() instanceof PrisonerOptionIntent.Negotiated negotiated)
                negotiated.options().forEach(option -> keys.add(option.key()));
            JsonNode row = StrictJson.parse(selected.normalized().bytes(), 1_048_576).path("player_prisoner_collection").path("prisoners").get(selected.ordinal());
            StrictJson.require(row != null && row.isObject() && PrisonerActionBinding12004.id(row.get("prisoner_character_id"))
                    == PrisonerActionBinding12004.id(args.get("prisoner_character_id")), "selected pending target differs");
            JsonNode preview = row.get(selected.intent().options() instanceof PrisonerOptionIntent.Negotiated ? "negotiated_release_preview" : "unconditional_release_preview");
            StrictJson.require(preview != null && preview.isObject(), "actual release preview is absent");
            pending.set("costs", preview.get("costs")); pending.set("acceptance", preview.get("acceptance"));
        } else for (String key : java.util.List.of("payer_character_id", "selected_option", "amount_is_acceptance_time_quote", "quoted_gold_raw", "pre_player_gold_raw"))
            pending.set(key, args.get(key));
        PrisonerPendingIdentity12004.decode(family, new RawJson(StrictJson.canonical(pending)));
        ObjectNode next = ((ObjectNode) previous).deepCopy(); next.set("pending", pending);
        validate(family, next); return new RawJson(StrictJson.canonical(next, 1_048_576));
    }
    public static RawJson resolve(PrisonerPlanningPorts.Family family, RawJson actualPreviousBody,
            ActionReceipt actualCanonicalReceipt, RawJson independentlyReplayedMaterial) {
        Objects.requireNonNull(actualCanonicalReceipt); Objects.requireNonNull(independentlyReplayedMaterial);
        JsonNode previous = StrictJson.parse(actualPreviousBody.bytes(), 1_048_576); validate(family, previous);
        if(PrisonerEpisodeLedger12004.isV2(family,previous))PrisonerEpisodeLedger12004.decode(family,actualPreviousBody).epoch().owner()
                .require(actualCanonicalReceipt.command().before(),actualCanonicalReceipt.command().source(),actualCanonicalReceipt.command().sessionId());
        StrictJson.require(!previous.get("pending").isNull(), "clear domain cannot be resolved a second time");
        var pending = PrisonerPendingIdentity12004.decode(family, new RawJson(StrictJson.canonical(previous.get("pending"))));
        StrictJson.require(pending.matches(actualCanonicalReceipt), "terminal receipt differs from full original pending identity");
        if(actualCanonicalReceipt.state() instanceof ActionState.RejectedBeforeDispatch){
            StrictJson.require(pending.actionId().filter(actualCanonicalReceipt.command().actionId()::equals).isPresent()&&pending.requestId().isEmpty(),
                    "zero-write rejection can resolve only its modern pre-submission pending, never a legacy submitted ACK");
            RawJson expected=zeroMaterial(actualCanonicalReceipt);
            StrictJson.require(StrictJson.parse(expected.bytes()).equals(StrictJson.parse(independentlyReplayedMaterial.bytes())),"canonical zero-write material differs");
            ObjectNode resolved=(ObjectNode)StrictJson.parse(expected.bytes());ObjectNode sourcePending=((ObjectNode)previous.get("pending")).deepCopy();sourcePending.remove("last_receipt");resolved.set("source_pending",sourcePending);
            ObjectNode next=((ObjectNode)previous).deepCopy();next.putNull("pending");next.set("resolved",resolved);validate(family,next);return new RawJson(StrictJson.canonical(next,1_048_576));
        }
        StrictJson.require(actualCanonicalReceipt.state() instanceof ActionState.Settled, "UNKNOWN/ACK/intent cannot clear pending");
        var settled = (ActionState.Settled) actualCanonicalReceipt.state();
        JsonNode material = StrictJson.parse(independentlyReplayedMaterial.bytes(), 1_048_576);
        StrictJson.require(material instanceof ObjectNode, "actual independently replayed terminal material required");
        String status = StrictJson.text(material.get("status"));
        if (settled.settlement() instanceof ActionState.Applied applied) {
            StrictJson.require(applied.observation().observerSchema().equals(PrisonerActionBinding12004.SCHEMA)
                    && status.equals("applied") && bool(material.get("material_result")) && bool(material.get("postcondition_verified")), "success domain material differs from canonical observed effect");
        } else if (settled.settlement() instanceof ActionState.NonAppliedTerminal negative) {
            StrictJson.require(family == PrisonerPlanningPorts.Family.RELEASE, "release terminal kind cannot settle ransom material");
            var terminal = negative.observation(); terminal.validate(actualCanonicalReceipt.command(), settled.attempt());
            StrictJson.require(terminal.disposition().targetId().longValueExact() == pending.target(), "negative terminal target differs");
            if (terminal.disposition() instanceof ActionTerminalObservation.PrisonerTransferred transferred) {
                StrictJson.require(status.equals("transferred") && transferred.currentJailerId().longValueExact() != pending.actor(), "actual transfer is not original actor custody");
            } else StrictJson.require(terminal.disposition() instanceof ActionTerminalObservation.PrisonerTargetDead && status.equals("dead"), "actual death terminal differs");
            StrictJson.require(!bool(material.get("material_result")) && !bool(material.get("postcondition_verified"))
                    && !bool(material.get("release_causation_observed")) && !bool(material.get("command_costs_verified")), "negative terminal cannot grant release, fees or causation");
        } else if (settled.settlement() instanceof ActionState.Rejected rejected) {
            StrictJson.require(rejected.requestId().equals(settled.attempt().requestId()) && status.equals("rejected")
                    && !bool(material.get("material_result")), "actual native rejection material differs");
        } else throw new IllegalArgumentException("unrelated canonical settlement cannot clear prisoner pending");
        ObjectNode resolved = ((ObjectNode) material).deepCopy();
        ObjectNode sourcePending = ((ObjectNode) previous.get("pending")).deepCopy(); sourcePending.remove("last_receipt");
        resolved.set("source_pending", sourcePending); resolved.put("action_id", actualCanonicalReceipt.command().actionId())
                .put("action_body_sha256", actualCanonicalReceipt.bodySha256()).put("request_id", settled.attempt().requestId());
        ObjectNode next = ((ObjectNode) previous).deepCopy(); next.putNull("pending"); next.set("resolved", resolved);
        validate(family, next); return new RawJson(StrictJson.canonical(next, 1_048_576));
    }
    /** Pure projection only. A live import must first reopen/validate this exact receipt through the original same-writer journal. */
    public static RawJson zeroMaterial(ActionReceipt receipt){
        StrictJson.require(receipt.state() instanceof ActionState.RejectedBeforeDispatch,"actual canonical zero-dispatch state required");
        var state=(ActionState.RejectedBeforeDispatch)receipt.state();var dispatch=state.dispatch();
        StrictJson.require(dispatch.requestId().equals(state.attempt().requestId())&&dispatch.proof().stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                &&dispatch.proof().requestBytesWritten()==0,"exact zero native bytes before write required");
        var value=StrictJson.object().put("schema","xar.java.prisoner-zero-dispatch/v1").put("status","rejected_before_dispatch")
                .put("action_id",receipt.command().actionId()).put("action_body_sha256",receipt.bodySha256()).put("request_id",dispatch.requestId())
                .put("material_result",false).put("postcondition_verified",false).put("payment_observed",false).put("freedom_observed",false)
                .put("relationship_effect_verified",false).put("game_advanced",false).put("request_bytes_written",0).put("reason",dispatch.proof().reason());
        return new RawJson(StrictJson.canonical(value));
    }
    private static boolean bool(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "actual terminal boolean required"); return value.booleanValue(); }
}
