package org.xar.ck3.control.application.effects.coa;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;

/** Completion of the native clipboard/source function only. The registered domain verifier must replay every original. */
public record NativeSourceObservation(OperationKey operation,String commandBodySha256,String requestId,
        Outcome outcome,Instant observedAt,ExactRef originalDispatch,ExactRef independentClipboard,
        ExactRef afterScope,ExactRef compatibleResult,List<ExactRef> sourceOriginals) {
    public static final String SCHEMA="xar.native-coa-source-completed/v1";
    public enum Outcome {PROBE_DETECTED,PROBE_APPLIED,PROBE_NOT_DETECTED,PROBE_APPLY_FAILED,PROBE_UNAVAILABLE,EXPORTED,EXPORT_UNAVAILABLE}
    public NativeSourceObservation{
        Objects.requireNonNull(operation);StrictJson.require(Set.of("probe-coat-of-arms-source-v1","export-coat-of-arms-source-v1").contains(operation.value()),"only the original two CoA source operations have this finite completion");
        StrictJson.require(commandBodySha256!=null&&commandBodySha256.matches("[a-f0-9]{64}"),"original command digest required");
        StrictJson.require(requestId!=null&&!requestId.isBlank()&&requestId.length()<=4096,"original native request ID required");Objects.requireNonNull(outcome);Objects.requireNonNull(observedAt);
        for(ExactRef ref:List.of(originalDispatch,independentClipboard,afterScope,compatibleResult))StrictJson.require(ref.bytes()>0,"nonempty independently retained source original required");
        StrictJson.require(new LinkedHashSet<>(List.of(originalDispatch,independentClipboard,afterScope,compatibleResult)).size()==4,"dispatch, clipboard, independent binding and result are distinct originals");
        sourceOriginals=List.copyOf(sourceOriginals);StrictJson.require(!sourceOriginals.isEmpty()&&sourceOriginals.size()<=64&&new LinkedHashSet<>(sourceOriginals).size()==sourceOriginals.size(),"bounded unique actual source producers required");
        sourceOriginals.forEach(ref->StrictJson.require(ref.bytes()>0,"nonempty actual producer source required"));
        StrictJson.require(operation.value().startsWith("probe-")==outcome.name().startsWith("PROBE_"),"source outcome belongs to another operation");
    }
    public boolean visibleGameplayCredit(){return false;}
    public boolean gameDayCredit(){return false;}
    public boolean renderedTextureVerified(){return false;}
    public List<ExactRef> references(){var refs=new LinkedHashSet<ExactRef>();refs.add(originalDispatch);refs.add(independentClipboard);refs.add(afterScope);refs.add(compatibleResult);refs.addAll(sourceOriginals);return List.copyOf(refs);}
    /** Shape/identity validation never substitutes for the installed source-domain original replay. */
    public void validate(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
        StrictJson.require(command.operation().equals(operation)&&ActionCodec.bodySha256(command).equals(commandBodySha256)&&attempt.requestId().equals(requestId)
                &&dispatch.requestId().equals(requestId)&&dispatch instanceof NativeActionPort.AckReceived&&((NativeActionPort.AckReceived)dispatch).nativeOk()
                &&((NativeActionPort.AckReceived)dispatch).originalResultToken().isPresent(),"native source completion crossed its original command/attempt/returned packet");
        StrictJson.require(command.origin() instanceof CommandOrigin.Frontend||command.origin() instanceof CommandOrigin.Gameplay,"read-only or lifecycle origin cannot gain source completion");
        StrictJson.require(sourceOriginals.contains(command.source().sourceRef())&&!observedAt.isBefore(attempt.submittedAt()),"source completion lacks original source or independently later observation");
    }
    public byte[] encode(){
        ObjectNode n=JsonNodeFactory.instance.objectNode().put("schema",SCHEMA).put("operation",operation.value()).put("command_body_sha256",commandBodySha256).put("request_id",requestId).put("outcome",outcome.name()).put("observed_at",observedAt.toString()).put("visible_gameplay_credit",false).put("game_day_credit",false).put("rendered_texture_verified",false);
        n.set("original_dispatch",originalDispatch.toJson());n.set("independent_clipboard",independentClipboard.toJson());n.set("after_scope",afterScope.toJson());n.set("compatible_result",compatibleResult.toJson());var sources=n.putArray("source_originals");sourceOriginals.forEach(ref->sources.add(ref.toJson()));return FullJsonTree.encode(n,65536);
    }
    public static NativeSourceObservation decode(byte[] original){
        JsonNode parsed=FullJsonTree.parse(original,65536);StrictJson.require(parsed instanceof ObjectNode,"source observation must be object");ObjectNode n=(ObjectNode)parsed;
        Set<String> fields=Set.of("schema","operation","command_body_sha256","request_id","outcome","observed_at","visible_gameplay_credit","game_day_credit","rendered_texture_verified","original_dispatch","independent_clipboard","after_scope","compatible_result","source_originals");
        StrictJson.require(n.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toSet()).equals(fields),"source observation fields differ");StrictJson.require(SCHEMA.equals(text(n,"schema")),"source observation schema differs");
        for(String field:List.of("visible_gameplay_credit","game_day_credit","rendered_texture_verified"))StrictJson.require(n.get(field).isBoolean()&&!n.get(field).booleanValue(),"source completion cannot claim Game, day or rendered credit");
        JsonNode sources=n.get("source_originals");StrictJson.require(sources.isArray()&&sources.size()>0&&sources.size()<=64,"source original roster outside bound");var refs=new java.util.ArrayList<ExactRef>();for(JsonNode ref:sources)refs.add(ExactRef.fromJson(ref));
        return new NativeSourceObservation(new OperationKey(text(n,"operation")),text(n,"command_body_sha256"),text(n,"request_id"),Outcome.valueOf(text(n,"outcome")),Instant.parse(text(n,"observed_at")),ExactRef.fromJson(n.get("original_dispatch")),ExactRef.fromJson(n.get("independent_clipboard")),ExactRef.fromJson(n.get("after_scope")),ExactRef.fromJson(n.get("compatible_result")),refs);
    }
    private static String text(ObjectNode n,String field){JsonNode value=n.get(field);StrictJson.require(value!=null&&value.isTextual()&&!value.textValue().isBlank(),"source observation text required: "+field);return value.textValue();}
}
