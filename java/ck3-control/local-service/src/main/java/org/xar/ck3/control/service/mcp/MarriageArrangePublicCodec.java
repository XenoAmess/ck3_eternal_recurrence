package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.effects.family.FamilySendObservation;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** The original public choice and revision contract; presentation never upgrades ACK or UNKNOWN to a send. */
public final class MarriageArrangePublicCodec {
    private MarriageArrangePublicCodec() { }
    public record Request(String choiceId,MarriageChoicesPublicCodec.Request revision) {
        public Request {
            StrictJson.require(choiceId!=null&&choiceId.matches("[0-9]+-[0-9]+"),"arrange-marriage choice_id is malformed");
            Objects.requireNonNull(revision);
        }
        public String step(){return "arrange-marriage-"+choiceId;}
    }
    public record Reply(ActionReceipt canonical,boolean reconciliation) {
        public Reply {
            Objects.requireNonNull(canonical);var intent=RulerMarriageIntent.fromJson(canonical.command().arguments());
            StrictJson.require(canonical.command().operation().value().equals(intent.step()),"public marriage receipt differs from its exact original intent");
            StrictJson.require(canonical.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED&&!canonical.visibleGameplay()&&!canonical.eligibleAdvance(),
                    "public marriage send cannot borrow a generic Applied or game-advance result");
            if(canonical.outcome()==ActionReceipt.Outcome.SEND_CONFIRMED) {
                StrictJson.require(canonical.state() instanceof ActionState.Settled,"public marriage requires its primitive original send settlement");
                var settled=(ActionState.Settled)canonical.state();
                StrictJson.require(settled.settlement() instanceof ActionState.FamilySendConfirmed
                        &&((ActionState.FamilySendConfirmed)settled.settlement()).observation().profile()==FamilySendObservation.Profile.MARRIAGE,
                        "public marriage send requires the same canonical marriage profile");
            }
        }
    }
    public static Request decode(PublicBindings.Arguments arguments) {
        StrictJson.require(arguments instanceof PublicBindings.Value,"named choice_id arguments must be a present object");
        var row=McpJson.object(McpJson.parse(((PublicBindings.Value)arguments).original().bytes()));
        McpJson.fields(row,Set.of("choice_id","expected_revision"),Set.of("choice_id"));
        String choice=StrictJson.text(row.get("choice_id"));ObjectNode revision=StrictJson.object();
        if(row.has("expected_revision"))revision.set("expected_revision",row.get("expected_revision"));
        return new Request(choice,MarriageChoicesPublicCodec.decode(new PublicBindings.Value(raw(revision))));
    }
    public static RawJson encodeRequest(Request request) {
        Objects.requireNonNull(request);var row=McpJson.object(McpJson.parse(MarriageChoicesPublicCodec.encodeRequest(request.revision()).bytes()));
        row.put("choice_id",request.choiceId());return raw(row);
    }
    public static RawJson encode(Reply reply) {
        Objects.requireNonNull(reply);var receipt=reply.canonical();var intent=RulerMarriageIntent.fromJson(receipt.command().arguments());
        boolean sent=receipt.outcome()==ActionReceipt.Outcome.SEND_CONFIRMED;
        String status=switch(receipt.outcome()) {
            case SEND_CONFIRMED -> "proposal_submitted";
            case UNRESOLVED -> "unknown";
            case REJECTED_CONFIRMED -> "rejected";
            case REJECTED_BEFORE_DISPATCH -> "rejected_before_dispatch";
            case TERMINAL_WITHOUT_EFFECT -> "terminal_without_effect";
            case APPLIED_CONFIRMED -> throw new IllegalArgumentException("a generic Applied is not a public marriage send result");
        };
        ObjectNode row=StrictJson.object().put("step",intent.step()).put("status",receipt.outcome().name().toLowerCase(Locale.ROOT))
                .put("action_id",receipt.command().actionId()).put("reconciliation",reply.reconciliation())
                .put("send_confirmed",sent).put("relationship_confirmed",false).put("eligible_advance",false);
        var ack=receipt.ack();
        if(ack.isPresent()) {
            var original=ack.orElseThrow();row.put("native_request_id",original.requestId()).put("native_ack_ok",original.nativeOk());
            JsonNode accepted=null;
            if(original.nativeOk()&&original.originalResultToken().isPresent()) {
                var nativeResult=McpJson.object(McpJson.parse(original.originalResultToken().orElseThrow().bytes()));accepted=nativeResult.get("accepted");
                StrictJson.require(accepted==null||accepted.isNull()||accepted.isBoolean(),"original native accepted field changed type");
            }
            if(accepted==null)row.putNull("accepted");else row.set("accepted",accepted);
        } else {row.putNull("native_request_id");row.putNull("native_ack_ok");row.putNull("accepted");}
        row.putObject("marriage_choice").put("choice_id",intent.choiceId()).put("played_character_id",intent.actorId())
                .put("candidate_character_id",intent.candidateId()).put("source","native");
        var action=row.putObject("marriage_action").put("status",status).put("choice_id",intent.choiceId())
                .put("played_character_id",intent.actorId()).put("candidate_character_id",intent.candidateId());
        var attempt=ActionTransitions.attempt(receipt.state());
        if(sent&&attempt.isPresent())action.put("submitted_date_raw",attempt.orElseThrow().guard().observed().frame().identity().dateRaw());
        else action.putNull("submitted_date_raw");
        McpJson.publicNumbers(row);return raw(row);
    }
    private static RawJson raw(JsonNode row){return new RawJson(McpJson.utf8(row.toString()));}
}
