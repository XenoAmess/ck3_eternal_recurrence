package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict Native result DATA. No variant is a physical-file or business SAVE receipt. */
public record CurrentCoreCheckpointSaveResult(Status status,boolean accepted,boolean effectAttempted,Optional<Submission> submission) {
    public enum Status {
        SUBMITTED("submitted"),REJECTED("rejected"),INDETERMINATE("indeterminate"),EXPIRED("expired"),
        STALE_CORE_PREFIX("stale_core_prefix"),REQUIRES_PAUSED_MAP_LIVING("requires_paused_map_living"),
        CLAIM_CONSUMED("claim_consumed"),SOURCE_CHANGED("source_changed"),CAPACITY_EXHAUSTED("capacity_exhausted"),UNAVAILABLE("unavailable");
        private final String wire;Status(String value){wire=value;}public String wire(){return wire;}
        static Status parse(String value)throws IOException {for(Status s:values())if(s.wire.equals(value))return s;throw new IOException("Unknown current checkpoint queue status");}
    }
    public record Submission(BigInteger sequence,int dateRaw) {
        public Submission {Objects.requireNonNull(sequence);StrictJson.require(sequence.signum()>0&&sequence.compareTo(NativeWire.UINT64_MAX)<=0,"Positive exact uint64 checkpoint sequence required");}
    }
    public CurrentCoreCheckpointSaveResult {
        Objects.requireNonNull(status);Objects.requireNonNull(submission);
        StrictJson.require(accepted==(status==Status.SUBMITTED)&&submission.isPresent()==accepted
                &&(!accepted||effectAttempted),"Coherent submitted-only data required; never incomplete success");
    }
    public static CurrentCoreCheckpointSaveResult decode(RawJson raw)throws IOException {
        try {
            ObjectNode row=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","adapter_id","backend","step",
                    "accepted","queue_status","effect_attempted","complete_snapshot","physical_save_confirmed","save_name","physical_filename"),Set.of("submission"));
            var build=ExactCk3Build.CK3_121003_STEAM_26785313;
            require(row,"schema",CurrentCoreCheckpointSave.RESULT_SCHEMA);require(row,"game_version",build.version());
            require(row,"executable_sha256",build.executableSha256().toUpperCase(Locale.ROOT));require(row,"adapter_id",build.coreFrameAdapterId());
            require(row,"backend",CurrentCoreCheckpointSave.BACKEND);require(row,"step",CurrentCoreCheckpointSave.STEP);
            require(row,"save_name",CurrentCoreCheckpointSave.SAVE_NAME);require(row,"physical_filename",CurrentCoreCheckpointSave.FILENAME);
            if(bool(row,"complete_snapshot")||bool(row,"physical_save_confirmed"))throw new IOException("Native checkpoint result cannot grant snapshot or physical SAVE");
            Status status=Status.parse(NativeWire.text(row.get("queue_status")));boolean accepted=bool(row,"accepted"),attempted=bool(row,"effect_attempted");
            Optional<Submission> submission=Optional.empty();
            if(row.has("submission")) {
                ObjectNode original=StrictJson.object(row.get("submission"),Set.of("sequence","requested_save_name","date_raw"));
                require(original,"requested_save_name",CurrentCoreCheckpointSave.SAVE_NAME);
                submission=Optional.of(new Submission(NativeWire.integer(original.get("sequence"),BigInteger.ONE,NativeWire.UINT64_MAX),
                        NativeWire.integer(original.get("date_raw"),BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact()));
            }
            return new CurrentCoreCheckpointSaveResult(status,accepted,attempted,submission);
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid current checkpoint result",invalid);}
    }
    public static CurrentCoreCheckpointSaveResult decodeOutcome(AckReceived original)throws IOException {
        try {
            ObjectNode envelope=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),
                    Set.of("type","protocol_version","request_id","ok","result"));
            require(envelope,"type","command_result");require(envelope,"request_id",original.requestId());
            NativeWire.integer(envelope.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(bool(envelope,"ok")!=original.nativeOk())throw new IOException("Original checkpoint outer ok differs");
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid original checkpoint envelope",invalid);}
        var raw=original.originalResultToken().orElseThrow(()->new IOException("Original checkpoint result token required"));
        var result=decode(new RawJson(raw.bytes()));
        if(original.nativeOk()!=result.accepted())throw new IOException("Outer Native ok differs from original submitted result");
        return result;
    }
    private static void require(ObjectNode row,String key,String expected)throws IOException {
        if(!NativeWire.text(row.get(key)).equals(expected))throw new IOException("Current checkpoint identity/name mismatch: "+key);
    }
    private static boolean bool(ObjectNode row,String key)throws IOException {
        var value=row.get(key);if(value==null||!value.isBoolean())throw new IOException("Actual checkpoint boolean required: "+key);return value.booleanValue();
    }
}
