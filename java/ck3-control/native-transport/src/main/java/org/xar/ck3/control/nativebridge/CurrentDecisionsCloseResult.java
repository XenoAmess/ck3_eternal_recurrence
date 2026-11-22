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

/** Preserves the native bool return. Even a dispatched close never proves panels_closed. */
public record CurrentDecisionsCloseResult(CurrentDecisionsClose.Action action,Status status,boolean effectAttempted,boolean nativeReturned,
        boolean nativeHandled,boolean cleanupKnown,BigInteger providerGeneration,BigInteger querySequence,BigInteger claimSequence,
        Optional<CoreFrame.Prefix> factsBefore,Optional<CurrentLetterResult.OwnerWitness> owner,
        Optional<CurrentCuratedDecisionsSource> source,boolean closeAdmissible,Optional<String> unavailableReason){
    public enum Status{
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_SOURCE("stale_source"),CLAIM_CONSUMED("claim_consumed"),AVAILABLE("available"),CLOSE_DISPATCHED("close_dispatched"),INDETERMINATE("indeterminate");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        static Status parse(String value)throws IOException{for(var item:values())if(item.wire.equals(value))return item;throw new IOException("Unknown decisions-close result status");}
    }
    public CurrentDecisionsCloseResult{
        Objects.requireNonNull(action);Objects.requireNonNull(status);CurrentLetter.unsigned(providerGeneration,false);CurrentLetter.unsigned(querySequence,false);CurrentLetter.unsigned(claimSequence,false);
        Objects.requireNonNull(factsBefore);Objects.requireNonNull(owner);Objects.requireNonNull(source);Objects.requireNonNull(unavailableReason);
        StrictJson.require(!nativeReturned||effectAttempted,"Native return needs actual effect entry");StrictJson.require(!nativeHandled||nativeReturned,"Native bool handling requires its actual return");
        if(action==CurrentDecisionsClose.Action.QUERY_CLOSE)StrictJson.require(!effectAttempted&&!nativeReturned&&!nativeHandled&&claimSequence.signum()==0,"Readonly close query never takes an effect claim");
        else StrictJson.require(providerGeneration.signum()>0&&querySequence.signum()>0,"Every parsed close refusal retains its original positive private lease");
        StrictJson.require(factsBefore.isPresent()==owner.isPresent(),"Actual Core/owner nullable roles differ");factsBefore.ifPresent(CurrentLetter::requirePrefix);
        if(source.isPresent())StrictJson.require(factsBefore.isPresent()&&cleanupKnown,"Actual complete close source needs Core/owner/cleanup");
        if(closeAdmissible){
            var s=source.orElseThrow(()->new IllegalArgumentException("Close admission has no actual source"));
            StrictJson.require(s.listFound()&&s.listVisible()&&s.listEnabled()&&s.detailFound()&&!s.detailVisible()&&s.completeModelCensus()&&!s.blockedByVisibleModal(),"Close admission contradicts actual list/detail/model/modal facts");
        }
        if(status==Status.AVAILABLE)StrictJson.require(action==CurrentDecisionsClose.Action.QUERY_CLOSE&&source.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0&&unavailableReason.isEmpty(),"Available close query needs actual source and positive private lease");
        else if(status==Status.CLOSE_DISPATCHED)StrictJson.require(action==CurrentDecisionsClose.Action.CLOSE_LIST&&closeAdmissible&&source.isPresent()&&effectAttempted&&nativeReturned&&claimSequence.signum()>0&&unavailableReason.isEmpty(),"Dispatched close needs its original admissible source and real call/claim");
        else{
            StrictJson.require(unavailableReason.filter(s->!s.isEmpty()).isPresent(),"Original close refusal reason required");
            if(status!=Status.INDETERMINATE)StrictJson.require(!effectAttempted&&!nativeReturned&&!nativeHandled,"Known close refusal keeps zero effect even if claim spent");
        }
    }
    public boolean successful(){return status==Status.AVAILABLE||status==Status.CLOSE_DISPATCHED;}
    public static CurrentDecisionsCloseResult decode(RawJson raw)throws IOException{
        try{
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","status","source_available","effect_attempted","native_returned","native_handled","cleanup_known","provider_generation","query_sequence","claim_sequence","facts_before","owner","source","close_admissible","addresses_redacted","panels_closed","new_date_observed","physical_save_confirmed","unavailable_reason"));
            var b=ExactCk3Build.CK3_121003_STEAM_26785313;require(r,"schema",CurrentDecisionsClose.RESULT_SCHEMA);require(r,"game_version",b.version());require(r,"executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT));require(r,"adapter_id",b.coreFrameAdapterId());require(r,"backend",CurrentDecisionsClose.BACKEND);
            if(!bool(r,"addresses_redacted")||bool(r,"panels_closed")||bool(r,"new_date_observed")||bool(r,"physical_save_confirmed"))throw new IOException("Fixed close DATA cannot prove closed panels/date/SAVE");
            Optional<CoreFrame.Prefix> core=Optional.empty();Optional<CurrentLetterResult.OwnerWitness> owner=Optional.empty();Optional<CurrentCuratedDecisionsSource> source=Optional.empty();
            if(!r.get("facts_before").isNull()){var p=StrictJson.object(r.get("facts_before"),Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));core=Optional.of(new CoreFrame.Prefix(i32(p.get("date_raw")),i32(p.get("speed")),bool(p,"paused"),i32(p.get("local_player_id")),bool(p,"map_ready"),bool(p,"has_played_character"),i32(p.get("played_character_id")),bool(p,"played_character_alive")));}
            if(!r.get("owner").isNull()){var p=StrictJson.object(r.get("owner"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));owner=Optional.of(new CurrentLetterResult.OwnerWitness(decimal(p,"connection_generation"),decimal(p,"ticket_sequence"),decimal(p,"pump_epoch"),NativeWire.integer(p.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
            if(!r.get("source").isNull())source=Optional.of(CurrentCuratedDecisionsSource.decode(r.get("source")));
            if(bool(r,"source_available")!=source.isPresent())throw new IOException("Close source availability/null mismatch");
            return new CurrentDecisionsCloseResult(CurrentDecisionsClose.Action.parse(NativeWire.text(r.get("action"))),Status.parse(NativeWire.text(r.get("status"))),bool(r,"effect_attempted"),bool(r,"native_returned"),bool(r,"native_handled"),bool(r,"cleanup_known"),decimal(r,"provider_generation"),decimal(r,"query_sequence"),decimal(r,"claim_sequence"),core,owner,source,bool(r,"close_admissible"),r.get("unavailable_reason").isNull()?Optional.empty():Optional.of(NativeWire.text(r.get("unavailable_reason"))));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact current decisions-close DATA",invalid);}
    }
    public static CurrentDecisionsCloseResult decodeOutcome(AckReceived original)throws IOException{
        try{
            var e=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));require(e,"type","command_result");require(e,"request_id",original.requestId());NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(bool(e,"ok")!=original.nativeOk())throw new IOException("Original close envelope ok mismatch");var token=original.originalResultToken().orElseThrow(()->new IOException("Original close result token absent"));
            if(!NativeWire.parse(token.bytes()).equals(e.get("result")))throw new IOException("Close token differs from original envelope");var frame=decode(new RawJson(token.bytes()));if(frame.successful()!=original.nativeOk())throw new IOException("Native ok differs from close-source/call coherence");return frame;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid actual decisions-close ACK",invalid);}
    }
    public RawJson encode(){
        var b=ExactCk3Build.CK3_121003_STEAM_26785313;var r=StrictJson.object().put("schema",CurrentDecisionsClose.RESULT_SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT)).put("adapter_id",b.coreFrameAdapterId()).put("backend",CurrentDecisionsClose.BACKEND)
                .put("action",action.wire()).put("status",status.wire()).put("source_available",source.isPresent()).put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("native_handled",nativeHandled).put("cleanup_known",cleanupKnown)
                .put("provider_generation",providerGeneration.toString()).put("query_sequence",querySequence.toString()).put("claim_sequence",claimSequence.toString()).put("close_admissible",closeAdmissible).put("addresses_redacted",true).put("panels_closed",false).put("new_date_observed",false).put("physical_save_confirmed",false);
        if(factsBefore.isPresent()){var p=factsBefore.orElseThrow();r.putObject("facts_before").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());var o=owner.orElseThrow();r.putObject("owner").put("connection_generation",o.connectionGeneration().toString()).put("ticket_sequence",o.ticketSequence().toString()).put("pump_epoch",o.pumpEpoch().toString()).put("thread_id",o.threadId());}
        else{r.putNull("facts_before");r.putNull("owner");}
        if(source.isPresent())r.set("source",source.orElseThrow().encode());else r.putNull("source");if(unavailableReason.isPresent())r.put("unavailable_reason",unavailableReason.orElseThrow());else r.putNull("unavailable_reason");return new RawJson(StrictJson.canonical(r));
    }
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static boolean bool(ObjectNode r,String key)throws IOException{var n=r.get(key);if(n==null||!n.isBoolean())throw new IOException("Actual close bool required: "+key);return n.booleanValue();}
    private static BigInteger decimal(ObjectNode r,String key)throws IOException{String s=NativeWire.text(r.get(key));if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical uint64 string required: "+key);var n=new BigInteger(s);CurrentLetter.unsigned(n,false);return n;}
    private static void require(ObjectNode r,String key,String expected)throws IOException{if(!NativeWire.text(r.get(key)).equals(expected))throw new IOException("Exact decisions-close identity mismatch: "+key);}
}
