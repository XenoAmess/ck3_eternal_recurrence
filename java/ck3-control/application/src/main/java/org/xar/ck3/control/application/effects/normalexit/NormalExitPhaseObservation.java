package org.xar.ck3.control.application.effects.normalexit;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** DATA for three observed UI phases. No constructor/codec grants native qualification, gameplay, SAVE or process-exit credit. */
public record NormalExitPhaseObservation(Phase phase,Outcome outcome,String actionId,String commandBodySha256,String originalRequestId,
        ExactRef originalDispatchRef,ExactRef preparedRequestRef,ObservationIdentity before,ObservationIdentity after,G2Source source,String sessionId,
        ExactRef beforeContextRef,PlanningReadReceipt beforeContext,ExactRef afterContextRef,PlanningReadReceipt afterContext) {
    public static final String SCHEMA="xar.java.normal-exit-phase-observation/v1";
    public enum Phase {
        PREPARE_CONFIRMATION(NativeStepDiscriminator.NormalExit.PREPARE_CONFIRMATION),
        CONTINUE_PREPARATION(NativeStepDiscriminator.NormalExit.CONTINUE_PREPARATION),
        DISABLE_EXIT_AUTOSAVE(NativeStepDiscriminator.NormalExit.DISABLE_EXIT_AUTOSAVE);
        private final NativeStepDiscriminator.NormalExit selector;
        Phase(NativeStepDiscriminator.NormalExit selector){this.selector=selector;}
        public NativeStepDiscriminator.NormalExit selector(){return selector;}
    }
    public enum Outcome { PREPARATION_REMAINING,CONFIRMATION_VISIBLE,AUTOSAVE_DISABLED }
    public NormalExitPhaseObservation {
        Objects.requireNonNull(phase);Objects.requireNonNull(outcome);StrictJson.text(actionId);StrictJson.text(originalRequestId);StrictJson.text(sessionId);
        require(commandBodySha256!=null&&commandBodySha256.matches("[0-9a-f]{64}"),"exact original normal-exit command body required");
        for(var ref:List.of(originalDispatchRef,preparedRequestRef,beforeContextRef,afterContextRef))require(ref!=null&&ref.bytes()>0,"nonempty exact phase original required");
        Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(source);Objects.requireNonNull(beforeContext);Objects.requireNonNull(afterContext);
        require(!beforeContextRef.equals(afterContextRef),"after context must be an independent actual read");
        require(phase==Phase.PREPARE_CONFIRMATION&&(outcome==Outcome.PREPARATION_REMAINING||outcome==Outcome.CONFIRMATION_VISIBLE)
                ||phase==Phase.CONTINUE_PREPARATION&&outcome==Outcome.CONFIRMATION_VISIBLE
                ||phase==Phase.DISABLE_EXIT_AUTOSAVE&&outcome==Outcome.AUTOSAVE_DISABLED,"closed phase/UI outcome pair required");
    }
    /** Structural custody only. The unique registered domain must re-decode both native queries and original ACK before settling. */
    public void validate(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
        require(command.origin() instanceof CommandOrigin.Gameplay&&command.operation().equals(phase.selector().operationKey())
                &&command.expected().observerSchema().equals(SCHEMA)&&command.actionId().equals(actionId)&&ActionCodec.bodySha256(command).equals(commandBodySha256)
                &&attempt.requestId().equals(originalRequestId)&&dispatch.requestId().equals(originalRequestId)&&command.before().equals(before)
                &&command.source().equals(source)&&command.sessionId().equals(sessionId),"phase observation changed canonical operation/attempt/before/source/session");
        require(dispatch instanceof NativeActionPort.AckReceived ack&&ack.nativeOk()&&ack.outbound().isPresent()&&ack.custody().isPresent(),"phase confirmation requires an actual successful ACK and retained write/response custody");
        var ack=(NativeActionPort.AckReceived)dispatch;ack.custody().orElseThrow().verify(ack,attempt.guard());NativeStepDiscriminator.requireRequest(command.operation(),phase.selector().kind(),attempt.preparedRequest());
        require(before.machineId().equals(after.machineId())&&before.game().equals(after.game())&&before.observationVersion()==after.observationVersion()
                &&before.frame().episodeRunId().equals(after.frame().episodeRunId())&&before.frame().identity().player().equals(after.frame().identity().player())
                &&before.frame().identity().dateRaw().equals(after.frame().identity().dateRaw())&&after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision())>=0
                &&after.frame().revision().compareTo(before.frame().revision())>=0,"UI phase cannot cross Game/player/episode/day or regress its actual frame");
        for(var pair:List.of(Map.entry(beforeContext,before),Map.entry(afterContext,after))){var read=pair.getKey();require(read.request().origin() instanceof CommandOrigin.Gameplay
                    &&read.request().before().equals(pair.getValue())&&read.request().operation().equals(NativeStepDiscriminator.NormalExit.QUERY_CONTEXT.operationKey())
                    &&read.request().source().equals(source)&&read.request().sessionId().equals(sessionId)&&read.original().nativeOk(),"phase context is not its independent same-source actual query");
            for(var guard:List.of(read.before(),read.after()))require(guard.binding().observed().equals(pair.getValue())&&guard.binding().source().equals(source)&&guard.binding().sessionId().equals(sessionId)
                    &&guard.binding().connectionGeneration().equals(attempt.guard().connectionGeneration()),"phase context changed its actual full-frame/source/held connection guard");}
        require(beforeContext.before().binding().nativeEvidence().equals(attempt.guard().nativeEvidence()),"phase baseline is not the actual submitted before packet");
        NativeRequestChronology.requireBeforeSubmission(beforeContext,attempt,ack);NativeRequestChronology.requireSampledAfter(afterContext,attempt,ack);
    }
    public void validate(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,ActionPorts.OutcomeArchive archive){validate(command,attempt,dispatch);requireArchive(archive);
        require(originalDispatchRef.equals(archive.referenceOf(dispatch))&&archive.load(originalDispatchRef).equals(dispatch)
                &&preparedRequestRef.equals(archive.requestReferenceOf(attempt.preparedRequest()))&&archive.loadRequest(preparedRequestRef).equals(attempt.preparedRequest()),"phase original dispatch/prepared request crossed the actual canonical attempt");}
    public List<ExactRef> references(){var refs=new LinkedHashSet<>(List.of(originalDispatchRef,preparedRequestRef,beforeContextRef,afterContextRef));
        for(var read:List.of(beforeContext,afterContext))for(var guard:List.of(read.before(),read.after())){refs.add(guard.binding().nativeEvidence());refs.add(guard.binding().capabilityEvidence());refs.addAll(guard.binding().supportingEvidence());}return List.copyOf(refs);}
    private void requireArchive(ActionPorts.OutcomeArchive archive){for(var pair:List.of(Map.entry(beforeContextRef,beforeContext),Map.entry(afterContextRef,afterContext)))require(archive.loadRead(pair.getKey()).equals(pair.getValue())&&archive.readReferenceOf(pair.getValue()).equals(pair.getKey()),"phase original context read changed");
        var dispatch=archive.load(originalDispatchRef);var prepared=archive.loadRequest(preparedRequestRef);require(archive.referenceOf(dispatch).equals(originalDispatchRef)&&archive.requestReferenceOf(prepared).equals(preparedRequestRef),"phase original dispatch/prepared-request archive changed");}
    public ObjectNode encode(ActionPorts.OutcomeArchive archive){requireArchive(Objects.requireNonNull(archive));var value=StrictJson.object().put("schema",SCHEMA).put("phase",phase.name()).put("outcome",outcome.name()).put("action_id",actionId)
                .put("command_body_sha256",commandBodySha256).put("original_request_id",originalRequestId).put("session_id",sessionId);
        value.set("original_dispatch_ref",originalDispatchRef.toJson());value.set("prepared_request_ref",preparedRequestRef.toJson());value.set("before",ProposalLifecycleCodec.observation(before));value.set("after",ProposalLifecycleCodec.observation(after));
        value.set("source",ProposalLifecycleCodec.source(source));value.set("before_context_ref",beforeContextRef.toJson());value.set("after_context_ref",afterContextRef.toJson());return value;}
    public static NormalExitPhaseObservation decode(JsonNode input,ActionPorts.OutcomeArchive archive){Objects.requireNonNull(archive);var value=StrictJson.object(input,Set.of("schema","phase","outcome","action_id","command_body_sha256","original_request_id","session_id","original_dispatch_ref","prepared_request_ref","before","after","source","before_context_ref","after_context_ref"));
        require(SCHEMA.equals(StrictJson.text(value.get("schema"))),"exact normal-exit phase schema required");var beforeRef=ExactRef.fromJson(value.get("before_context_ref"));var afterRef=ExactRef.fromJson(value.get("after_context_ref"));
        var result=new NormalExitPhaseObservation(Phase.valueOf(StrictJson.text(value.get("phase"))),Outcome.valueOf(StrictJson.text(value.get("outcome"))),StrictJson.text(value.get("action_id")),StrictJson.text(value.get("command_body_sha256")),StrictJson.text(value.get("original_request_id")),
                ExactRef.fromJson(value.get("original_dispatch_ref")),ExactRef.fromJson(value.get("prepared_request_ref")),ProposalLifecycleCodec.decodeObservation(value.get("before")),ProposalLifecycleCodec.decodeObservation(value.get("after")),G2Wire.source(value.get("source")),StrictJson.text(value.get("session_id")),beforeRef,archive.loadRead(beforeRef),afterRef,archive.loadRead(afterRef));result.requireArchive(archive);return result;}
}
