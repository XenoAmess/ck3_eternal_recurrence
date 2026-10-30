package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Original three Driver argument families. An opaque public quote never grants native or action authority. */
public final class SwayDriverCodec {
    private SwayDriverCodec() { }
    public record TargetRequest(BigInteger expectedRevision,long targetCharacterId) {
        public TargetRequest {SwayNativeWire.u64(expectedRevision,1);SwayNativeWire.actionCharacter(targetCharacterId);}
    }
    public record ReceiptRequest(BigInteger expectedRevision,long targetCharacterId,String actionId,BigInteger preCaptureEpoch) {
        public ReceiptRequest {SwayNativeWire.u64(expectedRevision,1);SwayNativeWire.actionCharacter(targetCharacterId);SwayNativeWire.action(actionId,false);SwayNativeWire.u64(preCaptureEpoch,1);}
    }
    /** The complete original public bytes remain available for an exact producer recomputation at the archive boundary. */
    public record Quote(BigInteger expectedRevision,long targetCharacterId,ExactRef originalRead,RawJson presentation) {
        public Quote {SwayNativeWire.u64(expectedRevision,1);SwayNativeWire.actionCharacter(targetCharacterId);Objects.requireNonNull(originalRead);Objects.requireNonNull(presentation);require(originalRead.bytes()>0,"nonempty original target receipt required");}
    }
    public record StartRequest(Quote readback,String actionId) {
        public StartRequest {Objects.requireNonNull(readback);SwayNativeWire.action(actionId,false);}
    }
    private static final Set<String> QUOTE_FIELDS=Set.of("schema","snapshot_revision","capture_epoch","container_generation","date_raw","actor_character_id","target_character_id","target_opinion_of_actor","active_scheme_count","matching_sway_active","native_complete_can_send","native_legal_now","native_failure_classification","active_sway_instances","exact_ck3_build","exe_sha256","queried_snapshot_id","queried_revision","queried_native_revision","post_snapshot_id","java_original_target_read");
    public static TargetRequest decodeTarget(RawJson arguments) {
        var row=StrictJson.object(StrictJson.parse(arguments.bytes(),65536),Set.of("expected_revision","target_character_id"));
        return new TargetRequest(SwayPublicCodec.publicUInt64(row.get("expected_revision"),1),id(row.get("target_character_id")));
    }
    public static ReceiptRequest decodeReceipt(RawJson arguments) {
        var row=StrictJson.object(StrictJson.parse(arguments.bytes(),65536),Set.of("target_character_id","action_id","expected_revision","pre_capture_epoch"));
        return new ReceiptRequest(SwayPublicCodec.publicUInt64(row.get("expected_revision"),1),id(row.get("target_character_id")),StrictJson.text(row.get("action_id")),SwayPublicCodec.publicUInt64(row.get("pre_capture_epoch"),1));
    }
    public static StartRequest decodeStart(RawJson arguments) {
        var row=StrictJson.object(StrictJson.parse(arguments.bytes(),SwayNativeWire.MAX),Set.of("readback","action_id"));
        var quote=StrictJson.object(row.get("readback"),QUOTE_FIELDS);
        require(StrictJson.text(quote.get("schema")).equals("active-scheme-sway-private-read-v1"),"original target public schema required");
        require(StrictJson.text(quote.get("exact_ck3_build")).equals(SwayNativeWire.BUILD)&&StrictJson.text(quote.get("exe_sha256")).equalsIgnoreCase(SwayNativeWire.EXE),"current native target build pair required");
        for(String name:Set.of("snapshot_revision","capture_epoch","container_generation","queried_revision","queried_native_revision"))SwayPublicCodec.publicUInt64(quote.get(name),1);
        id(quote.get("actor_character_id"));id(quote.get("target_character_id"));
        StrictJson.integer(quote.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE);StrictJson.integer(quote.get("target_opinion_of_actor"),-100,100);StrictJson.integer(quote.get("active_scheme_count"),0,32);
        for(String name:Set.of("matching_sway_active","native_complete_can_send","native_legal_now"))SwayNativeWire.bool(quote,name);
        StrictJson.text(quote.get("queried_snapshot_id"));StrictJson.text(quote.get("post_snapshot_id"));
        var failure=quote.get("native_failure_classification");require(failure!=null&&failure.isTextual()&&Set.of("","native_complete_validator_rejected").contains(failure.textValue()),"exact native target failure class required");
        require(quote.get("active_sway_instances").isArray()&&quote.get("active_sway_instances").size()<=32,"bounded original instances required");
        for(var value:quote.get("active_sway_instances")) {
            var instance=StrictJson.object(value,Set.of("scheme_instance_id","scheme_instance_generation","target_character_id","progress","progress_goal","is_exposed","is_frozen"));
            new SwayNativeWire.Instance(StrictJson.integer(instance.get("scheme_instance_id"),0,0xffff_fffeL),(int)StrictJson.integer(instance.get("scheme_instance_generation"),0,255),id(instance.get("target_character_id")),(int)StrictJson.integer(instance.get("progress"),0,Integer.MAX_VALUE),(int)StrictJson.integer(instance.get("progress_goal"),1,Integer.MAX_VALUE),SwayNativeWire.bool(instance,"is_exposed"),SwayNativeWire.bool(instance,"is_frozen"));
        }
        return new StartRequest(new Quote(SwayPublicCodec.publicUInt64(quote.get("queried_revision"),1),id(quote.get("target_character_id")),ExactRef.fromJson(quote.get("java_original_target_read")),raw(quote)),StrictJson.text(row.get("action_id")));
    }
    public static RawJson encode(TargetRequest request) {var row=StrictJson.object();row.put("expected_revision",request.expectedRevision().toString());row.put("target_character_id",request.targetCharacterId());return raw(row);}
    public static RawJson encode(ReceiptRequest request) {var row=StrictJson.object();row.put("expected_revision",request.expectedRevision().toString());row.put("target_character_id",request.targetCharacterId());row.put("action_id",request.actionId());row.put("pre_capture_epoch",request.preCaptureEpoch().toString());return raw(row);}
    public static RawJson encode(StartRequest request) {var row=StrictJson.object();row.set("readback",StrictJson.parse(request.readback().presentation().bytes(),SwayNativeWire.MAX));row.put("action_id",request.actionId());return raw(row);}
    public static RawJson quote(PlanningReadReceipt read,SwayNativeWire.TargetRead value,ExactRef original) {
        require(read.request().before().equals(value.binding().before())&&read.request().sessionId().equals(value.binding().sessionId()),"public target presentation requires its actual guarded receipt");
        var row=(ObjectNode)StrictJson.parse(value.body().bytes(),SwayNativeWire.MAX);provenance(row,value.binding());
        row.put("queried_snapshot_id",read.request().before().frame().snapshotId());row.put("queried_revision",read.request().before().frame().revision().toString());
        row.put("queried_native_revision",value.binding().revision().toString());row.put("post_snapshot_id",read.after().binding().observed().frame().snapshotId());row.set("java_original_target_read",original.toJson());
        return presentation(row);
    }
    public static RawJson receipt(PlanningReadReceipt read,SwayNativeWire.AppliedReceipt value,ExactRef original) {
        var row=(ObjectNode)StrictJson.parse(value.body().bytes(),SwayNativeWire.MAX);provenance(row,value.binding());
        var source=row.putObject("_receipt_source_frame_v1");source.put("schema","xar.ck3.sway-receipt-source-frame.v1");
        source.set("before",sourceFrame(read.before().binding()));source.set("after",sourceFrame(read.after().binding()));row.set("java_original_receipt_read",original.toJson());return presentation(row);
    }
    public static RawJson startResult(ActionReceipt actual,ActionPorts.OutcomeArchive originals) {
        var command=actual.command();require(command.operation().value().startsWith(SwayNativeWire.START),"actual Start result required");
        var arguments=SwayNativeBindings.args(command.arguments(),Set.of("schema","target_character_id","original_target_read"));SwayNativeBindings.startAdmission(arguments);
        long target=SwayNativeWire.actionCharacter(arguments,"target_character_id");var original=originals.loadRead(ExactRef.fromJson(arguments.get("original_target_read")));
        var quote=SwayNativeWire.target(original.original().originalFrame().bytes(),original.requestId(),SwayNativeBindings.bind(original,new OperationKey(SwayNativeWire.TARGET+target)),target);
        ObjectNode row;
        var acknowledgement=ack(actual,quote);
        if(acknowledgement.isPresent())row=(ObjectNode)StrictJson.parse(acknowledgement.orElseThrow().body().bytes(),SwayNativeWire.MAX);
        else {row=StrictJson.object();row.put("schema","active-scheme-sway-formal-private-v1");row.put("stage",actual.state() instanceof ActionState.RejectedBeforeDispatch?"rejected_before_dispatch":"submission_unresolved");row.put("action_id",command.actionId());row.put("receipt_pending",!(actual.state() instanceof ActionState.RejectedBeforeDispatch));}
        if(actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED)require(actual.applied().filter(applied->applied.observation().observerSchema().equals(SwayActionLifecycle.START_OBSERVER)).isPresent(),"Start presentation requires its actual independent Sway effect; control or scheduler settlement cannot substitute");
        require(!actual.eligibleAdvance(),"public native Start cannot grant game advancement");
        provenance(row,quote.binding());row.put("canonical_outcome",actual.outcome().name().toLowerCase(java.util.Locale.ROOT));row.put("canonical_postcondition_verified",actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED);row.put("canonical_body_sha256",actual.bodySha256());row.put("eligible_advance",false);return presentation(row);
    }
    public static java.util.Optional<SwayNativeWire.StartAck> ack(ActionReceipt actual,SwayNativeWire.TargetRead quote) {
        return actual.ack().map(ack->SwayNativeWire.startAck(ack.originalFrame().bytes(),ack.requestId(),actual.command().actionId(),quote));
    }
    public static RawJson retained(String status,String detail,String actionId,java.util.List<ExactRef> evidence) {
        var row=StrictJson.object();row.put("status",status);row.put("detail",detail);row.put("action_id",actionId);row.put("postcondition_verified",false);var refs=row.putArray("evidence");evidence.forEach(ref->refs.add(ref.toJson()));return raw(row);
    }
    private static ObjectNode sourceFrame(GuardEvidence guard) {
        var row=StrictJson.object();var frame=guard.observed().frame();row.put("snapshot_id",frame.snapshotId());row.put("revision",frame.revision().toString());row.put("native_revision",frame.identity().nativeRevision().toString());row.put("date_raw",frame.identity().dateRaw());row.put("episode_run_id",frame.episodeRunId());row.put("actor_character_id",frame.identity().player());row.put("connection_generation",guard.connectionGeneration().toString());return row;
    }
    private static void provenance(ObjectNode row,SwayNativeWire.Binding binding){row.put("exact_ck3_build",binding.exactBuild());row.put("exe_sha256",binding.exeSha256());}
    private static RawJson presentation(ObjectNode row) {
        for(String name:Set.of("snapshot_revision","capture_epoch","container_generation","pre_capture_epoch","pre_container_generation","post_capture_epoch","post_container_generation"))if(row.has(name))row.put(name,StrictJson.integer(row.get(name),BigInteger.ONE,StrictJson.UINT64_MAX).toString());
        return raw(row);
    }
    private static long id(JsonNode value){return org.xar.ck3.control.contracts.NativeCharacterId.fromJson(value).value();}
    private static RawJson raw(ObjectNode value){return new RawJson(StrictJson.canonical(value,SwayNativeWire.MAX));}
}
