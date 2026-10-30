package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** One strict original public Sway argument/result codec; native numeric packets are never rewritten. */
public final class SwayPublicCodec {
    public record JournalRequest(SwayObservationReads.Kind kind,BigInteger expectedRevision,long targetCharacterId,
            long schemeInstanceId,BigInteger afterSequence) {
        public JournalRequest {
            Objects.requireNonNull(kind);require(kind==SwayObservationReads.Kind.EXECUTION||kind==SwayObservationReads.Kind.TERMINATION,"selected original public journal required");
            SwayNativeWire.u64(expectedRevision,1);SwayNativeWire.u64(afterSequence,0);if(kind==SwayObservationReads.Kind.TERMINATION)NativeCharacterId.of(targetCharacterId);else SwayNativeWire.currentCharacter(targetCharacterId);
            SwayNativeWire.instance(schemeInstanceId,(int)(schemeInstanceId>>24));
        }
    }
    public record DirectRequest(SwayObservationReads.Kind kind,BigInteger expectedRevision,long targetCharacterId,java.util.OptionalLong schemeInstanceId) {
        public DirectRequest {Objects.requireNonNull(kind);Objects.requireNonNull(schemeInstanceId);SwayNativeWire.u64(expectedRevision,1);NativeCharacterId.of(targetCharacterId);
            require(kind==SwayObservationReads.Kind.COMPLETION&&schemeInstanceId.isPresent()||kind==SwayObservationReads.Kind.OPINION&&schemeInstanceId.isEmpty(),"completion and opinion have distinct original public fields");schemeInstanceId.ifPresent(value->SwayNativeWire.instance(value,(int)(value>>24)));}
    }
    public static DirectRequest decodeDirect(SwayObservationReads.Kind kind,RawJson arguments) {
        require(kind==SwayObservationReads.Kind.COMPLETION||kind==SwayObservationReads.Kind.OPINION,"only original completion/opinion direct read");
        var row=StrictJson.object(StrictJson.parse(arguments.bytes(),65536),kind==SwayObservationReads.Kind.COMPLETION?Set.of("expected_revision","target_character_id","scheme_instance_id"):Set.of("expected_revision","target_character_id"));
        long target = NativeCharacterId.fromJson(row.get("target_character_id")).value();
        return new DirectRequest(kind,publicUInt64(row.get("expected_revision"),1),target,kind==SwayObservationReads.Kind.COMPLETION?java.util.OptionalLong.of(StrictJson.integer(row.get("scheme_instance_id"),0,0xffff_fffeL)):java.util.OptionalLong.empty());
    }
    public static RawJson encodeDirectRequest(DirectRequest request) {
        var row=StrictJson.object();row.put("expected_revision",request.expectedRevision().toString());row.put("target_character_id",request.targetCharacterId());request.schemeInstanceId().ifPresent(value->row.put("scheme_instance_id",value));return raw(row);
    }
    public record InvalidationRequest(BigInteger expectedRevision,long targetCharacterId,long schemeInstanceId,BigInteger afterSequence) {
        public InvalidationRequest {SwayNativeWire.u64(expectedRevision,1);SwayNativeWire.currentCharacter(targetCharacterId);SwayNativeWire.instance(schemeInstanceId,(int)(schemeInstanceId>>24));SwayNativeWire.u64(afterSequence,0);}
    }
    public static InvalidationRequest decodeInvalidation(RawJson original) {
        var node=StrictJson.parse(original.bytes(),65536);require(node.isObject(),"original selected notification arguments must be an object");
        var row=StrictJson.object(node,node.has("after_sequence")?Set.of("expected_revision","target_character_id","scheme_instance_id","after_sequence"):Set.of("expected_revision","target_character_id","scheme_instance_id"));
        return new InvalidationRequest(publicUInt64(row.get("expected_revision"),1),StrictJson.integer(row.get("target_character_id"),1,Integer.MAX_VALUE),
                StrictJson.integer(row.get("scheme_instance_id"),0,0xffff_fffeL),row.has("after_sequence")?publicUInt64(row.get("after_sequence"),0):BigInteger.ZERO);
    }
    public static RawJson encodeInvalidationRequest(InvalidationRequest request) {
        var row=StrictJson.object();row.put("expected_revision",request.expectedRevision().toString());row.put("target_character_id",request.targetCharacterId());row.put("scheme_instance_id",request.schemeInstanceId());row.put("after_sequence",request.afterSequence().toString());return raw(row);
    }
    public static RawJson publicNormalized(SwayObservationReads.InvalidationPlane value) {
        var row=StrictJson.parse(value.normalized().bytes(),SwayNativeWire.MAX);decimalize(row);return new RawJson(StrictJson.canonical(row,SwayNativeWire.MAX));
    }
    private static final Set<String> WIDE=Set.of("after_sequence","earliest_sequence","latest_sequence","sequence","snapshot_revision","source_snapshot_revision","queried_revision","queried_native_revision",
            "capture_epoch","container_generation","pre_capture_epoch","post_capture_epoch","post_container_generation","observer_session_identity","toast_invocation_id","branch_source_sequence","original_invocation_id","parent_toast_invocation_id","end_original_invocation_id","payload");
    private SwayPublicCodec() { }
    public static SwaySelectedFinish.Request decodeFinish(RawJson arguments) {
        var row=StrictJson.object(StrictJson.parse(arguments.bytes(),65536),Set.of("expected_revision","target_character_id","scheme_instance_id","scheme_instance_generation"));
        return new SwaySelectedFinish.Request(publicUInt64(row.get("expected_revision"),1),StrictJson.integer(row.get("target_character_id"),1,Integer.MAX_VALUE),
                StrictJson.integer(row.get("scheme_instance_id"),0,0xffff_fffeL),Math.toIntExact(StrictJson.integer(row.get("scheme_instance_generation"),0,255)));
    }
    public static JournalRequest decodeJournal(SwayObservationReads.Kind kind,RawJson arguments) {
        var node=StrictJson.parse(arguments.bytes(),65536);require(node.isObject(),"public journal arguments must be an object");
        var fields=node.has("after_sequence")?Set.of("expected_revision","target_character_id","scheme_instance_id","after_sequence"):Set.of("expected_revision","target_character_id","scheme_instance_id");
        var row=StrictJson.object(node,fields);
        return new JournalRequest(kind,publicUInt64(row.get("expected_revision"),1),kind==SwayObservationReads.Kind.TERMINATION?NativeCharacterId.fromJson(row.get("target_character_id")).value():StrictJson.integer(row.get("target_character_id"),1,Integer.MAX_VALUE),
                StrictJson.integer(row.get("scheme_instance_id"),0,0xffff_fffeL),row.has("after_sequence")?publicUInt64(row.get("after_sequence"),0):BigInteger.ZERO);
    }
    public static RawJson encodeFinishRequest(SwaySelectedFinish.Request request) {
        var row=StrictJson.object();row.put("expected_revision",request.expectedRevision().toString());row.put("target_character_id",request.targetCharacterId());
        row.put("scheme_instance_id",request.schemeInstanceId());row.put("scheme_instance_generation",request.schemeInstanceGeneration());return raw(row);
    }
    public static RawJson encodeJournalRequest(JournalRequest request) {
        var row=StrictJson.object();row.put("expected_revision",request.expectedRevision().toString());row.put("target_character_id",request.targetCharacterId());
        row.put("scheme_instance_id",request.schemeInstanceId());row.put("after_sequence",request.afterSequence().toString());return raw(row);
    }
    /** Original numeric interfaces retain safe integer inputs; full-width public values use canonical decimal strings. */
    public static BigInteger publicUInt64(JsonNode value,long minimum) {
        final BigInteger actual;
        if(value!=null&&value.isTextual())actual=new BigInteger(new CrossJsDecimalUInt64(value.textValue()).decimal());
        else actual=StrictJson.integer(value,BigInteger.valueOf(minimum),BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER));
        SwayNativeWire.u64(actual,minimum);return actual;
    }
    public static RawJson publicNormalized(SwayObservationReads.Plane value) {
        var row=StrictJson.parse(value.normalized().bytes(),SwayNativeWire.MAX);decimalize(row);return new RawJson(StrictJson.canonical(row,SwayNativeWire.MAX));
    }
    public static RawJson publicNormalized(SwayObservationReads.JournalPlane value) {
        var row=StrictJson.parse(value.normalized().bytes(),SwayNativeWire.MAX);decimalize(row);return new RawJson(StrictJson.canonical(row,SwayNativeWire.MAX));
    }
    public static RawJson publicNormalized(SwayObservationReads.JournalBatch value) {
        var row=(ObjectNode)StrictJson.parse(value.primary().normalized().bytes(),SwayNativeWire.MAX);
        var termination=value.primary().kind()==SwayObservationReads.Kind.TERMINATION?value.primary():value.independentPeer();
        var end=StrictJson.parse(termination.normalized().bytes(),SwayNativeWire.MAX);
        if(end.has("common_native_end"))row.set("common_native_end",end.get("common_native_end"));
        value.originalComposition().ifPresent(raw->{
            var composition=StrictJson.parse(raw.bytes(),SwayNativeWire.MAX);row.set("sway_terminal_sources_12004",composition);
            row.set("sway_end_causal_observation_12004",composition.get("causal_observation"));row.set("sway_end_cause_observed_12004",composition.get("terminal_cause_observed"));
        });
        decimalize(row);return new RawJson(StrictJson.canonical(row,SwayNativeWire.MAX));
    }
    public static RawJson publicNormalized(SwayObservationReads.DirectBatch value) {
        var row=(ObjectNode)StrictJson.parse(value.primary().normalized().bytes(),SwayNativeWire.MAX);value.originalComposition().ifPresent(raw->row.set("sway_terminal_sources_12004",StrictJson.parse(raw.bytes(),SwayNativeWire.MAX)));
        decimalize(row);return new RawJson(StrictJson.canonical(row,SwayNativeWire.MAX));
    }
    public static RawJson retained(SwaySelectedFinish.Retained value) {
        var row=StrictJson.object();row.put("status",value.reason().name().toLowerCase(java.util.Locale.ROOT));row.put("detail",value.detail());row.put("postcondition_verified",false);
        var evidence=row.putArray("evidence");value.evidence().forEach(ref->evidence.add(ref.toJson()));return raw(row);
    }
    /** Presentation consumes the actual canonical result; a formatter never grants terminal or material benefit. */
    public static RawJson finishResult(ActionReceipt receipt,boolean reconciliation) {
        require(receipt.command().operation().value().equals(SwayNativeWire.STOP),"Finish presentation requires its actual selected Stop result");
        require(!receipt.eligibleAdvance(),"selected Stop cannot claim an eligible game advance");
        var row=StrictJson.object();row.put("status",receipt.outcome().name().toLowerCase(java.util.Locale.ROOT));row.put("action_id",receipt.command().actionId());
        row.put("body_sha256",receipt.bodySha256());row.put("reconciliation",reconciliation);row.put("postcondition_verified",receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED);
        row.put("eligible_advance",false);row.put("new_saved_game_days",0);row.put("state",receipt.state().getClass().getSimpleName());return raw(row);
    }
    private static void decimalize(JsonNode value) {
        if(value.isObject()) {
            var row=(ObjectNode)value;
            var names=new java.util.ArrayList<String>();row.fieldNames().forEachRemaining(names::add);
            for(String field:names) {
                JsonNode item=row.get(field);
                if(WIDE.contains(field)&&!item.isNull())row.put(field,StrictJson.integer(item,BigInteger.ZERO,StrictJson.UINT64_MAX).toString());
                else if(field.equals("native_success_chance_raw")&&!item.isNull())row.put(field,StrictJson.integer(item,BigInteger.ONE.shiftLeft(63).negate(),BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE)).toString());
                else decimalize(item);
            }
        } else if(value.isArray()) for(JsonNode item:value)decimalize(item);
        else if(value.isIntegralNumber())require(value.bigIntegerValue().abs().compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,"unclassified unsafe public integer must not cross JavaScript Number");
        else if(value.isFloatingPointNumber())throw new IllegalArgumentException("public Sway result contains an untyped floating-point value");
    }
    private static RawJson raw(ObjectNode value){return new RawJson(StrictJson.canonical(value,SwayNativeWire.MAX));}
}
