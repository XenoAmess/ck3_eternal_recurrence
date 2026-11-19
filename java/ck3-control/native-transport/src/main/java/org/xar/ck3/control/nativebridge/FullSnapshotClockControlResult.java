package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.application.advance.AdvancePrimitives;

/** Full-clock ACK DATA only. Even REJECTED_BEFORE_QUEUE is an actual ACK after a request write, never NoDispatch or retry authority. */
public final class FullSnapshotClockControlResult {
    public static final String SCHEMA="ck3_1210_full_clock_control_result_v1";
    public static final String CAPABILITY="game.command.full-snapshot-clock-control.v1";
    public static final String SAVE_NAME="xar_checkpoint";
    public static final Set<String> STEPS=Set.of("pause-map","resume-map","set-speed-1","set-speed-2","set-speed-3","set-speed-4","set-speed-5","save-checkpoint");
    private static final Set<String> BASE=Set.of("schema","game_version","executable_sha256","adapter_id","backend","step",
            "accepted","queue_status","effect_attempted","full_snapshot_before_verified","complete_snapshot","physical_save_confirmed");
    private static final Set<String> ZERO_QUEUE=Set.of("unavailable","expired","stale_core_prefix","stale_full_snapshot","requires_map","requires_paused","rejected");
    private static final Set<String> STATUSES=Set.of("unavailable","expired","stale_core_prefix","stale_full_snapshot","requires_map","requires_paused",
            "already_satisfied","rejected","submitted","indeterminate");
    public enum Disposition { SUBMITTED,REJECTED_BEFORE_QUEUE,UNKNOWN }
    public record Submission(BigInteger sequence,String requestedSaveName,int dateRaw,String status,String saveName) {
        public Submission {
            Objects.requireNonNull(sequence);Objects.requireNonNull(requestedSaveName);Objects.requireNonNull(status);Objects.requireNonNull(saveName);
        }
    }
    public record Assessment(Disposition disposition,String step,String queueStatus,boolean effectAttempted,
            boolean fullBeforeVerified,Optional<Submission> submission) {
        public Assessment {
            Objects.requireNonNull(disposition);Objects.requireNonNull(step);Objects.requireNonNull(queueStatus);Objects.requireNonNull(submission);
        }
    }
    private FullSnapshotClockControlResult(){ }

    /** Packet/metadata correlation only; a caller must independently retain the actual issuer, source, session and original control claim. */
    public static Assessment decode(NativeActionPort.AckReceived original,String expectedStep)throws IOException {
        require(expectedStep!=null&&STEPS.contains(expectedStep),"one exact fixed full-clock step required");
        return decodeCommon(original,expectedStep,false);
    }
    /** Negative Date ARM DATA only; success still uses the legacy sentinel result codec. */
    public static Assessment decodeDateArmRejection(NativeActionPort.AckReceived original,String expectedStep)throws IOException {
        dateArmSpec(expectedStep);
        return decodeCommon(original,expectedStep,true);
    }
    static AdvancePrimitives.ArmSpec dateArmSpec(String step)throws IOException {
        require(step!=null,"exact Date ARM step required");
        try {
            var arm=AdvancePrimitives.armSpec(step);
            require(step.equals("research-arm-tactical-daily-sentinel-v1-"+arm.startingDateRaw()+"-to-"+arm.targetDateRaw()
                    +"-speed-"+arm.speed()+"-mode-terminal-a-0"),"exact terminal-a-0 Date ARM step required");
            return arm;
        }catch(IllegalArgumentException invalid){throw new IOException("invalid Date ARM step",invalid);}
    }
    static NativeWire.CommandResult correlatedAck(NativeActionPort.AckReceived original,String expectedStep)throws IOException {
        Objects.requireNonNull(original);
        try {
            var outbound=original.outbound().orElseThrow(()->new IOException("full-clock original outbound missing"));
            var custody=original.custody().orElseThrow(()->new IOException("full-clock original request chronology missing"));
            custody.verify(original);
            var request=NativeWire.decodeExecuteRequest(outbound.originalPacket());
            require(outbound.requestId().equals(original.requestId())&&request.requestId().equals(original.requestId())
                    &&expectedStep.equals(request.step()),"full-clock outbound request identity or step differs");
            require(custody.requestId().equals(request.requestId()),"full-clock request chronology identity differs");
            var decoded=NativeWire.decode(original.originalPacket());
            require(decoded instanceof NativeWire.CommandResult,"full-clock original response must be command_result");
            var result=(NativeWire.CommandResult)decoded;
            require(result.requestId().equals(original.requestId())&&result.nativeOk()==original.nativeOk()
                    &&Arrays.equals(result.payload().value(),original.originalFrame().bytes()),"full-clock retained ACK differs from its original packet");
            require(result.result().presence()==NativeWire.Presence.VALUE&&original.originalResultToken().isPresent()
                    &&Arrays.equals(result.result().token().orElseThrow().value(),original.originalResultToken().orElseThrow().bytes()),
                    "full-clock retained result token differs from its original packet");
            return result;
        }catch(IllegalArgumentException invalid){throw new IOException("original ACK correlation is invalid",invalid);}
    }
    private static Assessment decodeCommon(NativeActionPort.AckReceived original,String expectedStep,boolean dateArm)throws IOException {
        try {
            var result=correlatedAck(original,expectedStep);
            var envelope=NativeWire.object(NativeWire.parse(result.payload().value()));
            var row=NativeWire.object(NativeWire.parse(result.result().token().orElseThrow().value()));
            var profile=ExactCk3Build.florinCoreFullBuild(text(row,"game_version"),text(row,"executable_sha256"));
            require(SCHEMA.equals(text(row,"schema"))&&profile.isPresent()
                    &&profile.orElseThrow().coreFullAdapterId().equals(text(row,"adapter_id"))
                    &&"ck3-1.21.0-native-headless-main-thread".equals(text(row,"backend")),"full-clock exact source tuple or schema differs");
            String step=text(row,"step"),status=text(row,"queue_status");
            require(expectedStep.equals(step)&&(dateArm||STEPS.contains(step)),"full-clock result step differs from the original fixed request");
            require(STATUSES.contains(status),"unknown full-clock queue status");
            boolean accepted=bool(row,"accepted"),attempted=bool(row,"effect_attempted"),before=bool(row,"full_snapshot_before_verified");
            require(!bool(row,"complete_snapshot")&&!bool(row,"physical_save_confirmed"),"full-clock ACK cannot claim a complete snapshot or physical SAVE confirmation");
            if(dateArm)require(!accepted&&!original.nativeOk(),"Date ARM negative codec cannot accept a full-clock success");
            require(accepted==original.nativeOk(),"full-clock nativeOk and accepted fields disagree");
            require(accepted==(status.equals("submitted")||status.equals("already_satisfied")),"full-clock acceptance contradicts the native status vocabulary");
            Set<String> fields=new HashSet<>(BASE);
            if(step.equals("save-checkpoint"))fields.add("save_name");
            if(step.equals("save-checkpoint")&&status.equals("submitted")){fields.add("status");fields.add("submission");}
            keys(row,fields);
            if(step.equals("save-checkpoint"))require(SAVE_NAME.equals(text(row,"save_name")),"full-clock SAVE basename differs from the fixed native target");

            // Native emits the explicit error only for a negative result which did not enter an effect, excluding indeterminate.
            boolean zeroError=!accepted&&!attempted&&!status.equals("indeterminate");
            keys(envelope,zeroError?Set.of("type","protocol_version","request_id","ok","result","error")
                    :Set.of("type","protocol_version","request_id","ok","result"));
            if(zeroError)require(ZERO_QUEUE.contains(status)&&("full_clock_"+status).equals(text(envelope,"error")),
                    "full-clock before-queue status/error pair differs");

            Optional<Submission> submission=Optional.empty();
            if(step.equals("save-checkpoint")&&status.equals("submitted")){
                require("submitted".equals(text(row,"status")),"full-clock SAVE submission status differs");
                var saved=NativeWire.object(row.get("submission"));keys(saved,Set.of("sequence","requested_save_name","date_raw"));
                BigInteger sequence=NativeWire.integer(saved.get("sequence"),BigInteger.ONE,NativeWire.UINT64_MAX);
                String requested=text(saved,"requested_save_name");require(SAVE_NAME.equals(requested),"full-clock requested SAVE basename differs");
                int date=NativeWire.integer(saved.get("date_raw"),BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();
                submission=Optional.of(new Submission(sequence,requested,date,text(row,"status"),text(row,"save_name")));
            }
            if(status.equals("indeterminate")||(!accepted&&attempted))
                return new Assessment(Disposition.UNKNOWN,step,status,attempted,before,submission);
            if(status.equals("submitted")){
                require(original.nativeOk()&&accepted&&attempted&&before,"submitted full-clock ACK lacks actual effect entry or full-before verification");
                return new Assessment(Disposition.SUBMITTED,step,status,true,true,submission);
            }
            if(zeroError)return new Assessment(Disposition.REJECTED_BEFORE_QUEUE,step,status,false,before,submission);
            // already_satisfied is not submission or a negative before-queue proof, and is never a synthesized Noop/retry license.
            return new Assessment(Disposition.UNKNOWN,step,status,attempted,before,submission);
        }catch(IllegalArgumentException invalid){throw new IOException("full-clock original ACK profile or correlation is invalid",invalid);}
    }
    private static String text(ObjectNode row,String field)throws IOException{return NativeWire.text(row.get(field));}
    private static boolean bool(ObjectNode row,String field)throws IOException {
        JsonNode value=row.get(field);require(value!=null&&value.isBoolean(),"exact full-clock boolean required: "+field);return value.booleanValue();
    }
    private static void keys(ObjectNode row,Set<String> expected)throws IOException {
        Set<String> actual=new HashSet<>();row.fieldNames().forEachRemaining(actual::add);require(actual.equals(expected),"closed full-clock object fields differ");
    }
    private static void require(boolean condition,String reason)throws IOException {if(!condition)throw new IOException(reason);}
}
