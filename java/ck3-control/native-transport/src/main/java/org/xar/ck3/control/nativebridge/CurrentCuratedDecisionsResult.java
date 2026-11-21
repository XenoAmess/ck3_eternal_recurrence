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

/** Exact finite current decision result; a native dispatch proves no applied decision, date or SAVE. */
public record CurrentCuratedDecisionsResult(CurrentCuratedDecisions.Action action,Status status,boolean effectAttempted,boolean nativeReturned,boolean nativeHandled,
        boolean cleanupKnown,BigInteger providerGeneration,BigInteger querySequence,BigInteger claimSequence,
        Optional<CoreFrame.Prefix> factsBefore,Optional<CurrentLetterResult.OwnerWitness> owner,Optional<CurrentCuratedDecisionsSource> source,
        Optional<String> unavailableReason,Optional<CurrentCuratedDecisions.DecisionKey> decisionKey) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_SOURCE("stale_source"),CLAIM_CONSUMED("claim_consumed"),AVAILABLE("available"),
        NAVIGATION_DISPATCHED("navigation_dispatched"),SELECTION_DISPATCHED("selection_dispatched"),CONFIRMATION_DISPATCHED("confirmation_dispatched"),INDETERMINATE("indeterminate");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        static Status parse(String value)throws IOException{for(var s:values())if(s.wire.equals(value))return s;throw new IOException("Unknown current curated-decision status");}
    }
    public CurrentCuratedDecisionsResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);CurrentLetter.unsigned(providerGeneration,false);CurrentLetter.unsigned(querySequence,false);CurrentLetter.unsigned(claimSequence,false);
        Objects.requireNonNull(factsBefore);Objects.requireNonNull(owner);Objects.requireNonNull(source);Objects.requireNonNull(unavailableReason);Objects.requireNonNull(decisionKey);
        StrictJson.require((action==CurrentCuratedDecisions.Action.QUERY||action==CurrentCuratedDecisions.Action.OPEN_LIST)?decisionKey.isEmpty():decisionKey.isPresent(),"Curated action/key role differs");
        if(action==CurrentCuratedDecisions.Action.QUERY)StrictJson.require(claimSequence.signum()==0&&!effectAttempted&&!nativeReturned&&!nativeHandled,"Query cannot claim an effect");
        else StrictJson.require(providerGeneration.signum()>0&&querySequence.signum()>0,"Parsed effect retains its positive private lease");
        StrictJson.require(!nativeReturned||effectAttempted,"Returned callback requires attempted effect");
        StrictJson.require(!nativeHandled||(action==CurrentCuratedDecisions.Action.OPEN_LIST&&nativeReturned),"Only native list opening returns a handling bool");
        StrictJson.require(factsBefore.isPresent()==owner.isPresent(),"Actual Core/owner nullable roles differ");factsBefore.ifPresent(CurrentLetter::requirePrefix);
        if(source.isPresent())StrictJson.require(factsBefore.isPresent()&&cleanupKnown,"Actual source needs observed Core/owner and known cleanup");
        boolean success=status==Status.AVAILABLE||status==Status.NAVIGATION_DISPATCHED||status==Status.SELECTION_DISPATCHED||status==Status.CONFIRMATION_DISPATCHED;
        if(success){StrictJson.require(source.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0&&unavailableReason.isEmpty(),"Successful result lacks actual private source");
            if(action==CurrentCuratedDecisions.Action.QUERY)StrictJson.require(status==Status.AVAILABLE,"Query status differs");
            else StrictJson.require(status==dispatchedStatus(action)&&effectAttempted&&nativeReturned&&claimSequence.signum()>0&&source.orElseThrow().admits(action,decisionKey),"Dispatch lacks original actual admission");}
        else{StrictJson.require(unavailableReason.filter(s->!s.isEmpty()).isPresent(),"Original refusal reason required");if(status!=Status.INDETERMINATE)StrictJson.require(!effectAttempted&&!nativeReturned&&!nativeHandled,"Known rejection must retain zero effect even with a spent once claim");}
    }
    public static Status dispatchedStatus(CurrentCuratedDecisions.Action action){return switch(action){case OPEN_LIST->Status.NAVIGATION_DISPATCHED;case OPEN_DETAIL->Status.SELECTION_DISPATCHED;case CONFIRM->Status.CONFIRMATION_DISPATCHED;case QUERY->throw new IllegalArgumentException("Query is readonly");};}
    public boolean successful(){return status==Status.AVAILABLE||status==Status.NAVIGATION_DISPATCHED||status==Status.SELECTION_DISPATCHED||status==Status.CONFIRMATION_DISPATCHED;}
    public static CurrentCuratedDecisionsResult decode(RawJson raw)throws IOException {
        try{var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","backend","adapter_id","action","status","source_available","effect_attempted","native_returned","native_handled","cleanup_known","provider_generation","query_sequence","claim_sequence","decision_key","facts_before","owner","source","addresses_redacted","decision_applied","new_date_observed","physical_save_confirmed","unavailable_reason"));
            var b=ExactCk3Build.CK3_121003_STEAM_26785313;require(r,"schema",CurrentCuratedDecisions.RESULT_SCHEMA);require(r,"game_version",b.version());require(r,"executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT));require(r,"adapter_id",b.coreFrameAdapterId());require(r,"backend",CurrentCuratedDecisions.BACKEND);
            if(!bool(r,"addresses_redacted")||bool(r,"decision_applied")||bool(r,"new_date_observed")||bool(r,"physical_save_confirmed"))throw new IOException("Curated dispatch cannot claim applied/date/SAVE");
            Optional<CoreFrame.Prefix> core=Optional.empty();Optional<CurrentLetterResult.OwnerWitness> owner=Optional.empty();Optional<CurrentCuratedDecisionsSource> source=Optional.empty();
            if(!r.get("facts_before").isNull()){var p=StrictJson.object(r.get("facts_before"),Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));core=Optional.of(new CoreFrame.Prefix(i32(p.get("date_raw")),i32(p.get("speed")),bool(p,"paused"),i32(p.get("local_player_id")),bool(p,"map_ready"),bool(p,"has_played_character"),i32(p.get("played_character_id")),bool(p,"played_character_alive")));}
            if(!r.get("owner").isNull()){var w=StrictJson.object(r.get("owner"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));owner=Optional.of(new CurrentLetterResult.OwnerWitness(decimal(w,"connection_generation"),decimal(w,"ticket_sequence"),decimal(w,"pump_epoch"),NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
            if(!r.get("source").isNull())source=Optional.of(CurrentCuratedDecisionsSource.decode(r.get("source")));if(bool(r,"source_available")!=source.isPresent())throw new IOException("Source availability/null role differs");
            return new CurrentCuratedDecisionsResult(CurrentCuratedDecisions.Action.parse(NativeWire.text(r.get("action"))),Status.parse(NativeWire.text(r.get("status"))),bool(r,"effect_attempted"),bool(r,"native_returned"),bool(r,"native_handled"),bool(r,"cleanup_known"),decimal(r,"provider_generation"),decimal(r,"query_sequence"),decimal(r,"claim_sequence"),core,owner,source,r.get("unavailable_reason").isNull()?Optional.empty():Optional.of(NativeWire.text(r.get("unavailable_reason"))),r.get("decision_key").isNull()?Optional.empty():Optional.of(CurrentCuratedDecisions.DecisionKey.parse(NativeWire.text(r.get("decision_key")))));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact current curated-decision DATA",invalid);}
    }
    public static CurrentCuratedDecisionsResult decodeOutcome(AckReceived original)throws IOException {
        try{var e=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));require(e,"type","command_result");require(e,"request_id",original.requestId());NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(bool(e,"ok")!=original.nativeOk())throw new IOException("Original envelope ok differs");var token=original.originalResultToken().orElseThrow(()->new IOException("Original result token absent"));if(!NativeWire.parse(token.bytes()).equals(e.get("result")))throw new IOException("Result token differs from original envelope");
            var result=decode(new RawJson(token.bytes()));if(result.successful()!=original.nativeOk())throw new IOException("Envelope ok differs from coherent actual source/dispatch");return result;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid actual curated-decision ACK",invalid);}
    }
    public RawJson encode(){var b=ExactCk3Build.CK3_121003_STEAM_26785313;var r=StrictJson.object().put("schema",CurrentCuratedDecisions.RESULT_SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT)).put("backend",CurrentCuratedDecisions.BACKEND).put("adapter_id",b.coreFrameAdapterId()).put("action",action.wire()).put("status",status.wire()).put("source_available",source.isPresent()).put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("native_handled",nativeHandled).put("cleanup_known",cleanupKnown).put("provider_generation",providerGeneration.toString()).put("query_sequence",querySequence.toString()).put("claim_sequence",claimSequence.toString());
        if(decisionKey.isPresent())r.put("decision_key",decisionKey.orElseThrow().wire());else r.putNull("decision_key");
        if(factsBefore.isPresent()){var p=factsBefore.orElseThrow();r.putObject("facts_before").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());var w=owner.orElseThrow();r.putObject("owner").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());}else{r.putNull("facts_before");r.putNull("owner");}
        if(source.isPresent())r.set("source",source.orElseThrow().encode());else r.putNull("source");r.put("addresses_redacted",true).put("decision_applied",false).put("new_date_observed",false).put("physical_save_confirmed",false);if(unavailableReason.isPresent())r.put("unavailable_reason",unavailableReason.orElseThrow());else r.putNull("unavailable_reason");return new RawJson(StrictJson.canonical(r));}
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static boolean bool(ObjectNode r,String k)throws IOException{var n=r.get(k);if(n==null||!n.isBoolean())throw new IOException("Actual boolean required: "+k);return n.booleanValue();}
    private static BigInteger decimal(ObjectNode r,String k)throws IOException{String s=NativeWire.text(r.get(k));if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical uint64 string required: "+k);var n=new BigInteger(s);CurrentLetter.unsigned(n,false);return n;}
    private static void require(ObjectNode r,String k,String expected)throws IOException{if(!NativeWire.text(r.get(k)).equals(expected))throw new IOException("Exact curated identity mismatch: "+k);}
}
