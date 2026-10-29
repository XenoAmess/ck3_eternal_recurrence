package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** The actual native Create submission DTO. It contains no created-regiment or payment result. */
public final class NativeRegularMaaSubmission {
    private NativeRegularMaaSubmission() { }
    public static final String STEP="maa-regular-personal-create-private-v1";
    public static final String MATERIAL_GAP="regular MAA request/action-to-created-owned-persistent-Regi and applied ten-resource-charge poststate is unavailable; existing native final quotation and queued_pending do not verify creation/payment";
    public enum Status {
        UNAVAILABLE("unavailable"),REJECTED("rejected"),QUEUED_PENDING("queued_pending");
        private final String wire;
        Status(String wire) { this.wire=wire; }
        public String wire() { return wire; }
        static Status decode(String value) {
            for(Status status:values())if(status.wire.equals(value))return status;
            throw new IllegalArgumentException("unknown actual regular MAA submission status");
        }
    }
    /** Single six-field contract used by the actual primitive, fixed private permission and retained-result decoder. */
    public static void validateRequest(NativeRequest request) {
        Objects.requireNonNull(request);
        StrictJson.require(request.step().equals(STEP)&&request.requiredCapability().isEmpty(),"exact original non-advertised regular MAA primitive required");
        var fields=StrictJson.object(StrictJson.parse(request.additionalFields().bytes()),Set.of("expected_snapshot_revision","expected_public_revision",
                "expected_date_raw","expected_player_character_id","type_index","action_id"));
        StrictJson.integer(fields.get("expected_snapshot_revision"),BigInteger.ONE,StrictJson.UINT64_MAX);
        StrictJson.integer(fields.get("expected_public_revision"),BigInteger.ONE,StrictJson.UINT64_MAX);
        StrictJson.integer(fields.get("expected_date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE);
        StrictJson.integer(fields.get("expected_player_character_id"),29829,29829);
        StrictJson.integer(fields.get("type_index"),0,Integer.MAX_VALUE);
        String action=StrictJson.text(fields.get("action_id"));
        StrictJson.require(action.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=63,"native MAA action_id exceeds original UTF-8 byte bound");
    }
    public record Envelope(String requestId,String actionId,String gameVersion,String executableSha256,
            BigInteger captureEpoch,Submission submission,RawJson originalResult) {
        public Envelope {
            StrictJson.text(requestId);StrictJson.text(actionId);Objects.requireNonNull(gameVersion);Objects.requireNonNull(executableSha256);
            StrictJson.require(captureEpoch!=null&&captureEpoch.signum()>0&&captureEpoch.compareTo(StrictJson.UINT64_MAX)<=0,"original positive uint64 capture epoch required");
            Objects.requireNonNull(submission);Objects.requireNonNull(originalResult);
            StrictJson.require(actionId.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=63,"original caller action exceeds native UTF-8 bound");
        }
        /** The same supported scope as the original Python public producer. This is not independent material. */
        public ObjectNode pythonProjection() {
            boolean queued=submission.status()==Status.QUEUED_PENDING;
            var out=StrictJson.object().put("schema","xar.ck3.regular-maa-create-private-action.v1")
                    .put("exact_ck3_build",gameVersion).put("exe_sha256",executableSha256).put("status",submission.status().wire())
                    .put("reason",submission.reason()).put("request_id",requestId).put("action_id",actionId)
                    .put("player_character_id",submission.ownerCharacterId()).put("type_index",submission.typeIndex())
                    .put("submitted",queued).put("verification_pending",queued).put("material_result",false)
                    .put("created_observed",false).put("payment_observed",false).put("capture_epoch",captureEpoch)
                    .put("automatic_retry",false).put("advertised",false);
            out.set("native_submission",submission.toJson());return out;
        }
    }
    /** One canonical native result decoder shared by live effects, public results and pure cold replay. No Native I/O. */
    public static Envelope original(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(command);Objects.requireNonNull(attempt);Objects.requireNonNull(ack);Objects.requireNonNull(archive);
        StrictJson.require(command.operation().value().equals(STEP)&&ack.nativeOk()&&ack.outbound().isPresent()&&ack.originalResultToken().isPresent()
                &&ack.requestId().equals(attempt.requestId())&&ack.equals(archive.load(archive.referenceOf(ack))),"canonical successful original MAA dispatch required");
        var custody=ack.custody().orElseThrow(()->new IllegalArgumentException("MAA original endpoint custody unavailable"));custody.verify(ack,attempt.guard());
        StrictJson.require(!custody.writeEntered().observedAt().isBefore(attempt.submittedAt()),"MAA write predates canonical submission");
        validateRequest(attempt.preparedRequest());
        StrictJson.require(attempt.guard().observed().equals(command.before())&&attempt.guard().source().equals(command.source())
                &&attempt.guard().sessionId().equals(command.sessionId())&&attempt.guard().operation().equals(command.operation()),"MAA original guard differs from canonical command source");
        var expected=EffectJson.object(EffectJson.parse(attempt.preparedRequest().additionalFields())).deepCopy();
        StrictJson.require(!expected.has("type")&&!expected.has("protocol_version")&&!expected.has("request_id")&&!expected.has("step")&&!expected.has("expected_revision"),"MAA prepared fields collide with transport envelope");
        expected.put("type","execute_step").put("protocol_version",1).put("request_id",attempt.requestId()).put("step",STEP).put("expected_revision",command.before().frame().identity().nativeRevision());
        StrictJson.require(Arrays.equals(StrictJson.canonical(expected,StrictJson.EXPLICIT_MAX_BYTES),StrictJson.canonical(packet(ack.outbound().orElseThrow().originalPacket()),StrictJson.EXPLICIT_MAX_BYTES))&&attempt.preparedRequest().step().equals(STEP),"original MAA outbound differs from canonical prepared request");
        var frame=StrictJson.object(packet(ack.originalPacket()),Set.of("type","protocol_version","request_id","ok","result"));
        StrictJson.require(StrictJson.text(frame.get("type")).equals("command_result")&&StrictJson.text(frame.get("request_id")).equals(attempt.requestId()),"MAA native request mismatch");
        StrictJson.integer(frame.get("protocol_version"),1,1);StrictJson.trueValue(frame.get("ok"));
        StrictJson.require(frame.equals(EffectJson.parse(ack.originalFrame()))&&frame.get("result").equals(EffectJson.parse(ack.originalResultToken().orElseThrow())),"MAA packet/frame/result token mismatch");
        var result=StrictJson.object(frame.get("result"),Set.of("step","accepted","private_build","advertised","backend_id","game_version","executable_sha256","read_only","status","snapshot_revision","public_revision","date_raw","capture_epoch","action_id","submission"));
        StrictJson.require(StrictJson.text(result.get("step")).equals(STEP)&&StrictJson.text(result.get("backend_id")).equals("native-headless"),"MAA native route mismatch");
        StrictJson.trueValue(result.get("accepted"));StrictJson.trueValue(result.get("private_build"));
        StrictJson.require(result.get("advertised").isBoolean()&&!result.get("advertised").booleanValue()&&result.get("read_only").isBoolean()&&!result.get("read_only").booleanValue(),"MAA native mutation flags mismatch");
        String build=StrictJson.text(result.get("game_version")),sha=StrictJson.text(result.get("executable_sha256"));
        StrictJson.require(build.equals("1.20.0.3")&&sha.equals("94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6")
                ||build.equals("1.20.0.4")&&sha.equals("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"),"MAA native build pair mismatch");
        StrictJson.require(StrictJson.integer(result.get("snapshot_revision"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(command.before().frame().identity().nativeRevision())
                &&StrictJson.integer(result.get("public_revision"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(command.before().frame().revision())
                &&BigInteger.valueOf(StrictJson.integer(result.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)).equals(command.before().frame().identity().dateRaw()),"MAA original native/public/date frame mismatch");
        StrictJson.require(command.before().frame().identity().player().equals(BigInteger.valueOf(29829)),"actual native regular MAA Create provider only supports Robert29829");
        var selected=ArmyOrdinaryActionArguments.decode(command.arguments());
        StrictJson.require(selected.kind()==ArmyOrdinaryActionArguments.Kind.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1,"MAA original command kind mismatch");
        var arguments=EffectJson.object(EffectJson.parse(selected.publicArguments()));String action=StrictJson.text(arguments.get("action_id"));
        StrictJson.require(StrictJson.text(result.get("action_id")).equals(action),"MAA original caller action identity mismatch");
        var prepared=EffectJson.object(EffectJson.parse(attempt.preparedRequest().additionalFields()));
        StrictJson.require(StrictJson.integer(prepared.get("expected_snapshot_revision"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(command.before().frame().identity().nativeRevision())
                &&StrictJson.integer(prepared.get("expected_public_revision"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(command.before().frame().revision())
                &&BigInteger.valueOf(StrictJson.integer(prepared.get("expected_date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)).equals(command.before().frame().identity().dateRaw())
                &&StrictJson.text(prepared.get("action_id")).equals(action)&&prepared.get("type_index").equals(arguments.get("type_index")),"MAA original native request crossed selected action/type/frame");
        var value=decode(new RawJson(StrictJson.canonical(result.get("submission"))),command.before().frame().identity().player().intValueExact(),(int)StrictJson.integer(arguments.get("type_index"),0,Integer.MAX_VALUE));
        StrictJson.require(StrictJson.text(result.get("status")).equals(value.status().wire()),"MAA outer and inner native statuses differ");
        return new Envelope(attempt.requestId(),action,build,sha,StrictJson.integer(result.get("capture_epoch"),BigInteger.ONE,StrictJson.UINT64_MAX),value,ack.originalResultToken().orElseThrow());
    }
    private static ObjectNode packet(byte[] packet) {
        StrictJson.require(packet.length>4&&ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==packet.length-4,"exact original MAA native framing required");
        return EffectJson.object(StrictJson.parse(Arrays.copyOfRange(packet,4,packet.length)));
    }
    public record Submission(Status status,String reason,int ownerCharacterId,int typeIndex,
            Optional<Boolean> nativeCanCreate,Optional<Boolean> nativeSubmitAccepted,Optional<Boolean> commandPointerConsumed) {
        public Submission {
            Objects.requireNonNull(status);Objects.requireNonNull(reason);Objects.requireNonNull(nativeCanCreate);
            Objects.requireNonNull(nativeSubmitAccepted);Objects.requireNonNull(commandPointerConsumed);
            if(!reason.isEmpty())StrictJson.text(reason);
            StrictJson.require(ownerCharacterId!=-1&&typeIndex>=0,"original native MAA owner/type required");
            StrictJson.require(nativeSubmitAccepted.isPresent()==commandPointerConsumed.isPresent(),"native submit and ownership observations are atomic");
            StrictJson.require(nativeSubmitAccepted.isEmpty()||nativeCanCreate.equals(Optional.of(true)),"native submit requires its observed true validator");
            switch(status) {
                case QUEUED_PENDING -> StrictJson.require(nativeCanCreate.equals(Optional.of(true))
                        &&nativeSubmitAccepted.equals(Optional.of(true))&&commandPointerConsumed.equals(Optional.of(true))
                        &&Set.of("","native_stack_cleanup_unavailable").contains(reason),"queued MAA requires true native ownership transfer; cleanup warning does not undo submission");
                case REJECTED -> StrictJson.require(
                        reason.equals("native_denied")&&nativeCanCreate.equals(Optional.of(false))&&nativeSubmitAccepted.isEmpty()
                        ||reason.equals("native_queue_rejected")&&nativeCanCreate.equals(Optional.of(true))
                        &&nativeSubmitAccepted.equals(Optional.of(false))&&commandPointerConsumed.equals(Optional.of(true)),
                        "regular MAA rejected state differs from the actual validator/queue branches");
                case UNAVAILABLE -> StrictJson.require(!reason.isEmpty(),"native unavailable MAA retains its actual diagnostic and possible submission ambiguity");
            }
        }
        /** Diagnostic only. No submission DTO can grant an Applied result or automatic retry. */
        public String pendingReason() { return "native regular MAA "+status.wire()+" ("+reason+"); "+MATERIAL_GAP+"; retain original attempt without replay"; }
        public ObjectNode toJson() {
            var row=StrictJson.object().put("schema_version",1).put("status",status.wire()).put("reason",reason)
                    .put("command_class","CCreateMAARegimentCommand").put("owner_character_id",ownerCharacterId).put("type_index",typeIndex);
            put(row,"native_can_create",nativeCanCreate);put(row,"native_submit_accepted",nativeSubmitAccepted);
            put(row,"command_pointer_consumed",commandPointerConsumed);return row;
        }
    }
    public static Submission decode(RawJson original,int actualOwner,int actualTypeIndex) {
        var row=StrictJson.object(StrictJson.parse(original.bytes()),Set.of("schema_version","status","reason","command_class",
                "owner_character_id","type_index","native_can_create","native_submit_accepted","command_pointer_consumed"));
        StrictJson.integer(row.get("schema_version"),1,1);
        StrictJson.require(StrictJson.text(row.get("command_class")).equals("CCreateMAARegimentCommand"),"actual regular MAA native command class required");
        int owner=(int)StrictJson.integer(row.get("owner_character_id"),Integer.MIN_VALUE,Integer.MAX_VALUE);
        int type=(int)StrictJson.integer(row.get("type_index"),0,Integer.MAX_VALUE);
        StrictJson.require(owner==actualOwner&&type==actualTypeIndex,"regular MAA submission crossed its original owner/type");
        return new Submission(Status.decode(StrictJson.text(row.get("status"))),reason(row.get("reason")),owner,type,
                nullableBoolean(row.get("native_can_create")),nullableBoolean(row.get("native_submit_accepted")),nullableBoolean(row.get("command_pointer_consumed")));
    }
    private static Optional<Boolean> nullableBoolean(JsonNode value) {
        StrictJson.require(value!=null&&(value.isNull()||value.isBoolean()),"native MAA nullable boolean must be explicit bool or null");
        return value.isNull()?Optional.empty():Optional.of(value.booleanValue());
    }
    private static String reason(JsonNode value) {
        StrictJson.require(value!=null&&value.isTextual(),"native MAA reason must be an explicit string");
        String text=value.textValue();return text.isEmpty()?text:StrictJson.text(text);
    }
    private static void put(ObjectNode row,String key,Optional<Boolean> value) {
        if(value.isPresent())row.put(key,value.orElseThrow());else row.putNull(key);
    }
}
