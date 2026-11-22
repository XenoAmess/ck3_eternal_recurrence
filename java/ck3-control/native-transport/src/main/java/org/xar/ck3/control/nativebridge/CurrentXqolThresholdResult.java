package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
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

/** Exact new XQOL threshold DATA; a void callback proves no closed prompt, new date or SAVE. */
public record CurrentXqolThresholdResult(CurrentXqolThreshold.Action action,Status status,boolean effectAttempted,boolean nativeReturned,
        boolean cleanupKnown,BigInteger providerGeneration,BigInteger querySequence,BigInteger claimSequence,
        Optional<CoreFrame.Prefix> factsBefore,Optional<CurrentLetterResult.OwnerWitness> owner,Optional<CurrentXqolThresholdSource> source,
        Optional<String> unavailableReason,Optional<Integer> instanceId) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_SOURCE("stale_source"),CLAIM_CONSUMED("claim_consumed"),
        AVAILABLE("available"),THRESHOLD_ROUTE_DISPATCHED("threshold_route_dispatched"),INDETERMINATE("indeterminate");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        static Status parse(String value)throws IOException {for(var status:values())if(status.wire.equals(value))return status;throw new IOException("Unknown current XQOL threshold status");}
    }
    public CurrentXqolThresholdResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);CurrentLetter.unsigned(providerGeneration,false);
        CurrentLetter.unsigned(querySequence,false);CurrentLetter.unsigned(claimSequence,false);
        Objects.requireNonNull(factsBefore);Objects.requireNonNull(owner);Objects.requireNonNull(source);Objects.requireNonNull(unavailableReason);Objects.requireNonNull(instanceId);
        if(action==CurrentXqolThreshold.Action.QUERY_THRESHOLD)StrictJson.require(claimSequence.signum()==0&&!effectAttempted&&!nativeReturned,"Threshold query never takes an effect claim or enters a callback");
        else StrictJson.require(providerGeneration.signum()>0&&querySequence.signum()>0,"Every parsed fixed acknowledgement retains its original positive private lease");
        StrictJson.require(!nativeReturned||effectAttempted,"A returned prompt callback requires its actual effect attempt");
        StrictJson.require(action==CurrentXqolThreshold.Action.QUERY_THRESHOLD?instanceId.isEmpty():instanceId.filter(n->n>0).isPresent(),"Threshold result actual-instance role differs");
        StrictJson.require(factsBefore.isPresent()==owner.isPresent(),"Actual Core/owner nullable roles differ");
        factsBefore.ifPresent(CurrentLetter::requirePrefix);
        if(source.isPresent()) {
            StrictJson.require(factsBefore.isPresent()&&cleanupKnown,"Actual full census requires observed Core/owner/cleanup");
            var actual=source.orElseThrow();
            if(actual.prompt().event().isPresent())StrictJson.require(actual.prompt().event().orElseThrow().recipientCharacterId()==factsBefore.orElseThrow().playedCharacterId(),"Known prompt recipient differs from original actual player");
        }
        if(status==Status.AVAILABLE)StrictJson.require(action==CurrentXqolThreshold.Action.QUERY_THRESHOLD&&source.isPresent()&&providerGeneration.signum()>0
                &&querySequence.signum()>0&&!effectAttempted&&!nativeReturned&&claimSequence.signum()==0&&unavailableReason.isEmpty(),"Available complete XQOL threshold query coherence differs");
        else if(status==Status.THRESHOLD_ROUTE_DISPATCHED) {
            StrictJson.require(action!=CurrentXqolThreshold.Action.QUERY_THRESHOLD&&status==dispatchedStatus(action)&&source.isPresent()&&providerGeneration.signum()>0
                    &&querySequence.signum()>0&&claimSequence.signum()>0&&effectAttempted&&nativeReturned&&unavailableReason.isEmpty(),"Void actual-instance reply coherence differs");
            var actual=source.orElseThrow();StrictJson.require(actual.setAdmissible()&&actual.prompt().event().map(e->e.instanceId()).equals(instanceId),"Original actual prompt source does not admit the fixed same-instance acknowledgement");
        } else {
            StrictJson.require(unavailableReason.filter(s->!s.isEmpty()).isPresent(),"Original XQOL threshold refusal reason required");
            if(status!=Status.INDETERMINATE)StrictJson.require(!effectAttempted&&!nativeReturned,"Known prompt refusal must retain zero effect/callback flags even if a once claim was spent");
        }
    }
    public boolean successful(){return status==Status.AVAILABLE||status==Status.THRESHOLD_ROUTE_DISPATCHED;}
    public static Status dispatchedStatus(CurrentXqolThreshold.Action action){if(action!=CurrentXqolThreshold.Action.SET_THRESHOLD)throw new IllegalArgumentException("Query has no dispatch status");return Status.THRESHOLD_ROUTE_DISPATCHED;}
    public static CurrentXqolThresholdResult decode(RawJson raw)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","backend","adapter_id","action","status","source_available","effect_attempted","native_returned","native_handled","cleanup_known","provider_generation","query_sequence","claim_sequence","facts_before","owner","source","addresses_redacted","threshold_applied","event_closed","conversion_applied","new_date_observed","physical_save_confirmed","unavailable_reason","instance_id"));
            var b=ExactCk3Build.CK3_121003_STEAM_26785313;require(r,"schema",CurrentXqolThreshold.RESULT_SCHEMA);require(r,"game_version",b.version());
            require(r,"executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT));require(r,"adapter_id",b.coreFrameAdapterId());require(r,"backend",CurrentXqolThreshold.BACKEND);
            if(!bool(r,"addresses_redacted")||bool(r,"native_handled")||bool(r,"threshold_applied")||bool(r,"event_closed")||bool(r,"conversion_applied")||bool(r,"new_date_observed")||bool(r,"physical_save_confirmed"))throw new IOException("Threshold DATA cannot claim native handling/closed/date/SAVE");
            Optional<CoreFrame.Prefix> core=Optional.empty();Optional<CurrentLetterResult.OwnerWitness> owner=Optional.empty();Optional<CurrentXqolThresholdSource> source=Optional.empty();
            if(!r.get("facts_before").isNull()){var p=StrictJson.object(r.get("facts_before"),Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));core=Optional.of(new CoreFrame.Prefix(i32(p.get("date_raw")),i32(p.get("speed")),bool(p,"paused"),i32(p.get("local_player_id")),bool(p,"map_ready"),bool(p,"has_played_character"),i32(p.get("played_character_id")),bool(p,"played_character_alive")));}
            if(!r.get("owner").isNull()){var w=StrictJson.object(r.get("owner"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));owner=Optional.of(new CurrentLetterResult.OwnerWitness(decimal(w,"connection_generation"),decimal(w,"ticket_sequence"),decimal(w,"pump_epoch"),NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
            if(!r.get("source").isNull())source=Optional.of(CurrentXqolThresholdSource.decode(r.get("source")));
            if(bool(r,"source_available")!=source.isPresent())throw new IOException("Threshold source availability/null mismatch");
            return new CurrentXqolThresholdResult(CurrentXqolThreshold.Action.parse(NativeWire.text(r.get("action"))),Status.parse(NativeWire.text(r.get("status"))),bool(r,"effect_attempted"),bool(r,"native_returned"),bool(r,"cleanup_known"),decimal(r,"provider_generation"),decimal(r,"query_sequence"),decimal(r,"claim_sequence"),core,owner,source,r.get("unavailable_reason").isNull()?Optional.empty():Optional.of(NativeWire.text(r.get("unavailable_reason"))),r.get("instance_id").isNull()?Optional.empty():Optional.of(i32(r.get("instance_id"))));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact current XQOL threshold DATA",invalid);}
    }
    public static CurrentXqolThresholdResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var e=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));
            require(e,"type","command_result");require(e,"request_id",original.requestId());NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(bool(e,"ok")!=original.nativeOk())throw new IOException("Original XQOL threshold envelope ok mismatch");
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original XQOL threshold result token absent"));
            if(!NativeWire.parse(token.bytes()).equals(e.get("result")))throw new IOException("Threshold result differs from original envelope");
            var result=decode(new RawJson(token.bytes()));if(result.successful()!=original.nativeOk())throw new IOException("Native ok differs from coherent actual-source/void-dispatch result");return result;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid actual XQOL threshold acknowledgement",invalid);}
    }
    public RawJson encode() {
        var b=ExactCk3Build.CK3_121003_STEAM_26785313;
        var r=StrictJson.object().put("schema",CurrentXqolThreshold.RESULT_SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT))
                .put("backend",CurrentXqolThreshold.BACKEND).put("adapter_id",b.coreFrameAdapterId()).put("action",action.wire()).put("status",status.wire())
                .put("source_available",source.isPresent()).put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("native_handled",false).put("cleanup_known",cleanupKnown)
                .put("provider_generation",providerGeneration.toString()).put("query_sequence",querySequence.toString()).put("claim_sequence",claimSequence.toString());
        if(factsBefore.isPresent()){var p=factsBefore.orElseThrow();r.putObject("facts_before").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());var w=owner.orElseThrow();r.putObject("owner").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());}
        else{r.putNull("facts_before");r.putNull("owner");}
        if(source.isPresent())r.set("source",source.orElseThrow().encode());else r.putNull("source");
        if(instanceId.isPresent())r.put("instance_id",instanceId.orElseThrow());else r.putNull("instance_id");
        r.put("addresses_redacted",true).put("threshold_applied",false).put("event_closed",false).put("conversion_applied",false).put("new_date_observed",false).put("physical_save_confirmed",false);
        if(unavailableReason.isPresent())r.put("unavailable_reason",unavailableReason.orElseThrow());else r.putNull("unavailable_reason");return new RawJson(StrictJson.canonical(r));
    }
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static boolean bool(ObjectNode r,String k)throws IOException {var n=r.get(k);if(n==null||!n.isBoolean())throw new IOException("Actual XQOL threshold bool required: "+k);return n.booleanValue();}
    private static BigInteger decimal(ObjectNode r,String k)throws IOException {String s=NativeWire.text(r.get(k));if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical uint64 string required: "+k);var n=new BigInteger(s);CurrentLetter.unsigned(n,false);return n;}
    private static void require(ObjectNode r,String k,String expected)throws IOException {if(!NativeWire.text(r.get(k)).equals(expected))throw new IOException("Exact current XQOL threshold identity mismatch: "+k);}
}
