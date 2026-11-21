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
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Strict fixed-fixture result DATA. A dispatched callback never grants marker, business or SAVE success. */
public record CurrentAubObserverFixtureResult(Status status,boolean effectAttempted,boolean nativeReturned,
        boolean nativeAccepted,boolean cleanupKnown,BigInteger claimSequence,Optional<String> inboxSha256,
        boolean fileVerified,boolean fileVerifiedAfter,Optional<CoreFrame.Prefix> coreBefore,
        Optional<OwnerWitness> ownerWitness,Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_CORE("stale_core"),CLAIM_CONSUMED("claim_consumed"),
        SOURCE_CHANGED("source_changed"),DISPATCHED("dispatched"),INDETERMINATE("indeterminate");
        private final String wire;Status(String value){wire=value;}public String wire(){return wire;}
        static Status parse(String value)throws IOException {for(var s:values())if(s.wire.equals(value))return s;throw new IOException("Unknown fixed observer status");}
    }
    public record OwnerWitness(BigInteger connectionGeneration,BigInteger ticketSequence,BigInteger pumpEpoch,long threadId) {
        public OwnerWitness {positive(connectionGeneration);positive(ticketSequence);positive(pumpEpoch);
            StrictJson.require(threadId>0&&threadId<=0xffff_ffffL,"Actual positive uint32 owner thread required");}
    }
    public CurrentAubObserverFixtureResult {
        Objects.requireNonNull(status);Objects.requireNonNull(claimSequence);Objects.requireNonNull(inboxSha256);
        Objects.requireNonNull(coreBefore);Objects.requireNonNull(ownerWitness);Objects.requireNonNull(unavailableReason);
        StrictJson.require(claimSequence.signum()>=0&&claimSequence.compareTo(NativeWire.UINT64_MAX)<=0,"Exact unsigned claim sequence required");
        inboxSha256.ifPresent(s->StrictJson.require(s.matches("[0-9a-f]{64}"),"Exact lowercase SHA256 required"));
        coreBefore.ifPresent(CurrentAubObserverFixture::requirePrefix);
        StrictJson.require(coreBefore.isPresent()==ownerWitness.isPresent(),"Core and actual owner witness must be present or null together");
        if(status==Status.DISPATCHED)StrictJson.require(effectAttempted&&nativeReturned&&nativeAccepted&&cleanupKnown
                &&claimSequence.signum()>0&&fileVerified&&fileVerifiedAfter&&inboxSha256.isPresent()
                &&coreBefore.isPresent()&&unavailableReason.isEmpty(),"Incomplete native dispatch cannot be success");
        else StrictJson.require(unavailableReason.filter(s->!s.isEmpty()).isPresent(),"Actual refusal/unknown reason required");
    }
    public boolean dispatched(){return status==Status.DISPATCHED;}
    public static CurrentAubObserverFixtureResult decode(RawJson raw)throws IOException {
        try {
            ObjectNode row=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","adapter_id","backend","step",
                    "status","effect_attempted","native_returned","native_accepted","cleanup_known","claim_sequence","inbox_filename","inbox_sha256",
                    "file_verified","file_verified_after","core_before","owner_witness","addresses_redacted","observer_markers_confirmed",
                    "business_pass_confirmed","production_actions_confirmed","physical_save_confirmed","unavailable_reason"));
            var build=ExactCk3Build.CK3_121003_STEAM_26785313;
            require(row,"schema",CurrentAubObserverFixture.RESULT_SCHEMA);require(row,"game_version",build.version());
            require(row,"executable_sha256",build.executableSha256().toUpperCase(Locale.ROOT));require(row,"adapter_id",build.coreFrameAdapterId());
            require(row,"backend",CurrentAubObserverFixture.BACKEND);require(row,"step",CurrentAubObserverFixture.STEP);require(row,"inbox_filename",CurrentAubObserverFixture.FILENAME);
            if(!bool(row,"addresses_redacted")||bool(row,"observer_markers_confirmed")||bool(row,"business_pass_confirmed")
                    ||bool(row,"production_actions_confirmed")||bool(row,"physical_save_confirmed"))throw new IOException("Fixed fixture result cannot grant marker/business/production/SAVE confirmation");
            Optional<CoreFrame.Prefix> core=Optional.empty();Optional<OwnerWitness> owner=Optional.empty();
            if(!row.get("core_before").isNull()) {
                var c=StrictJson.object(row.get("core_before"),Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));
                core=Optional.of(new CoreFrame.Prefix(i32(c,"date_raw"),i32(c,"speed"),bool(c,"paused"),i32(c,"local_player_id"),bool(c,"map_ready"),bool(c,"has_played_character"),i32(c,"played_character_id"),bool(c,"played_character_alive")));
            }
            if(!row.get("owner_witness").isNull()) {
                var w=StrictJson.object(row.get("owner_witness"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));
                owner=Optional.of(new OwnerWitness(decimal(w,"connection_generation",true),decimal(w,"ticket_sequence",true),decimal(w,"pump_epoch",true),NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
            }
            Optional<String> hash=row.get("inbox_sha256").isNull()?Optional.empty():Optional.of(NativeWire.text(row.get("inbox_sha256")));
            Optional<String> reason=row.get("unavailable_reason").isNull()?Optional.empty():Optional.of(NativeWire.text(row.get("unavailable_reason")));
            return new CurrentAubObserverFixtureResult(Status.parse(NativeWire.text(row.get("status"))),bool(row,"effect_attempted"),bool(row,"native_returned"),bool(row,"native_accepted"),bool(row,"cleanup_known"),decimal(row,"claim_sequence",false),hash,bool(row,"file_verified"),bool(row,"file_verified_after"),core,owner,reason);
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid actual fixed observer result",invalid);}
    }
    public static CurrentAubObserverFixtureResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var e=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));
            require(e,"type","command_result");require(e,"request_id",original.requestId());NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(bool(e,"ok")!=original.nativeOk())throw new IOException("Actual fixed observer envelope ok mismatch");
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid actual fixed observer envelope",invalid);}
        var token=original.originalResultToken().orElseThrow(()->new IOException("Original fixed observer result token required"));
        var result=decode(new RawJson(token.bytes()));
        if(result.dispatched()!=original.nativeOk())throw new IOException("Actual fixed observer outer ok differs from dispatched status");
        return result;
    }
    private static void positive(BigInteger n){Objects.requireNonNull(n);StrictJson.require(n.signum()>0&&n.compareTo(NativeWire.UINT64_MAX)<=0,"Positive exact uint64 witness required");}
    private static BigInteger decimal(ObjectNode row,String key,boolean positive)throws IOException {
        String s=NativeWire.text(row.get(key));if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical unsigned decimal string required: "+key);
        BigInteger n=new BigInteger(s);if(n.compareTo(NativeWire.UINT64_MAX)>0||(positive&&n.signum()==0))throw new IOException("Witness/claim outside exact uint64 range: "+key);return n;
    }
    private static int i32(ObjectNode row,String key)throws IOException{return NativeWire.integer(row.get(key),BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static void require(ObjectNode row,String key,String expected)throws IOException {if(!NativeWire.text(row.get(key)).equals(expected))throw new IOException("Fixed observer identity/name mismatch: "+key);}
    private static boolean bool(ObjectNode row,String key)throws IOException {var v=row.get(key);if(v==null||!v.isBoolean())throw new IOException("Actual boolean required: "+key);return v.booleanValue();}
}
