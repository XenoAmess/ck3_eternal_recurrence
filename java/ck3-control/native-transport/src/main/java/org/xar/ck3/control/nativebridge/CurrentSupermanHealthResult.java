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

/** Exact current health DATA; raw typed values never claim rendered UI, changed health or a saved result. */
public record CurrentSupermanHealthResult(CurrentSupermanHealth.Action action,Status status,boolean effectAttempted,boolean nativeReturned,
        boolean cleanupKnown,BigInteger providerGeneration,BigInteger querySequence,BigInteger claimSequence,
        Optional<CoreFrame.Prefix> factsBefore,Optional<CurrentLetterResult.OwnerWitness> owner,Optional<CurrentSupermanHealthSource> source,
        Optional<String> unavailableReason,CurrentSupermanHealth.Phase phase) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_SOURCE("stale_source"),CLAIM_CONSUMED("claim_consumed"),
        AVAILABLE("available"),KNOWN_CHOICE_DISPATCHED("known_choice_dispatched"),INDETERMINATE("indeterminate");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        static Status parse(String value)throws IOException {for(var status:values())if(status.wire.equals(value))return status;throw new IOException("Unknown current Superman health status");}
    }
    public CurrentSupermanHealthResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);CurrentLetter.unsigned(providerGeneration,false);
        CurrentLetter.unsigned(querySequence,false);CurrentLetter.unsigned(claimSequence,false);
        Objects.requireNonNull(factsBefore);Objects.requireNonNull(owner);Objects.requireNonNull(source);Objects.requireNonNull(unavailableReason);Objects.requireNonNull(phase);
        if(action==CurrentSupermanHealth.Action.QUERY_HEALTH)StrictJson.require(claimSequence.signum()==0&&!effectAttempted&&!nativeReturned,"Superman health query never takes an effect claim or enters a callback");
        else StrictJson.require(providerGeneration.signum()>0&&querySequence.signum()>0,"Every parsed fixed acknowledgement retains its original positive private lease");
        StrictJson.require(!nativeReturned||effectAttempted,"A returned prompt callback requires its actual effect attempt");
        StrictJson.require(factsBefore.isPresent()==owner.isPresent(),"Actual Core/owner nullable roles differ");
        factsBefore.ifPresent(CurrentLetter::requirePrefix);
        if(source.isPresent()) {
            StrictJson.require(factsBefore.isPresent()&&cleanupKnown,"Actual full census requires observed Core/owner/cleanup");
            var actual=source.orElseThrow();
            StrictJson.require(actual.phase()==phase,"Superman health source product/setting differs from original result");
            StrictJson.require(actual.characters().get(0).characterId()==factsBefore.orElseThrow().playedCharacterId(),"First actual receiver must be the original Core actor");
            if(actual.eventFound())StrictJson.require(actual.recipientCharacterId().orElseThrow()==factsBefore.orElseThrow().playedCharacterId(),"Actual fixed event recipient differs from original Core");
        }
        if(status==Status.AVAILABLE)StrictJson.require(action==CurrentSupermanHealth.Action.QUERY_HEALTH&&source.isPresent()&&providerGeneration.signum()>0
                &&querySequence.signum()>0&&!effectAttempted&&!nativeReturned&&claimSequence.signum()==0&&unavailableReason.isEmpty(),"Available complete Superman health query coherence differs");
        else if(status==Status.KNOWN_CHOICE_DISPATCHED) {
            StrictJson.require(action!=CurrentSupermanHealth.Action.QUERY_HEALTH&&status==dispatchedStatus(action)&&source.isPresent()&&providerGeneration.signum()>0
                    &&querySequence.signum()>0&&claimSequence.signum()>0&&effectAttempted&&nativeReturned&&unavailableReason.isEmpty(),"Void actual-instance reply coherence differs");
            var actual=source.orElseThrow();StrictJson.require(actual.nativeChoiceAdmissible(),"Original actual prompt source does not admit the fixed same-instance acknowledgement");
        } else {
            StrictJson.require(unavailableReason.filter(s->!s.isEmpty()).isPresent(),"Original Superman health refusal reason required");
            if(status!=Status.INDETERMINATE)StrictJson.require(!effectAttempted&&!nativeReturned,"Known prompt refusal must retain zero effect/callback flags even if a once claim was spent");
        }
    }
    public boolean successful(){return status==Status.AVAILABLE||status==Status.KNOWN_CHOICE_DISPATCHED;}
    public static Status dispatchedStatus(CurrentSupermanHealth.Action action){if(action!=CurrentSupermanHealth.Action.CHOOSE_KNOWN)throw new IllegalArgumentException("Query has no dispatch status");return Status.KNOWN_CHOICE_DISPATCHED;}
    public static CurrentSupermanHealthResult decode(RawJson raw)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","backend","adapter_id","action","status","source_available","effect_attempted","native_returned","native_handled","cleanup_known","provider_generation","query_sequence","claim_sequence","facts_before","owner","source","addresses_redacted","event_closed","health_changed","trait_UI_rendered","new_date_observed","physical_save_confirmed","unavailable_reason","phase"));
            var b=ExactCk3Build.CK3_121003_STEAM_26785313;require(r,"schema",CurrentSupermanHealth.RESULT_SCHEMA);require(r,"game_version",b.version());
            require(r,"executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT));require(r,"adapter_id",b.coreFrameAdapterId());require(r,"backend",CurrentSupermanHealth.BACKEND);
            if(!bool(r,"addresses_redacted")||bool(r,"native_handled")||bool(r,"event_closed")||bool(r,"health_changed")||bool(r,"trait_UI_rendered")||bool(r,"new_date_observed")||bool(r,"physical_save_confirmed"))throw new IOException("Superman health DATA cannot claim native handling/closed/date/SAVE");
            Optional<CoreFrame.Prefix> core=Optional.empty();Optional<CurrentLetterResult.OwnerWitness> owner=Optional.empty();Optional<CurrentSupermanHealthSource> source=Optional.empty();
            if(!r.get("facts_before").isNull()){var p=StrictJson.object(r.get("facts_before"),Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));core=Optional.of(new CoreFrame.Prefix(i32(p.get("date_raw")),i32(p.get("speed")),bool(p,"paused"),i32(p.get("local_player_id")),bool(p,"map_ready"),bool(p,"has_played_character"),i32(p.get("played_character_id")),bool(p,"played_character_alive")));}
            if(!r.get("owner").isNull()){var w=StrictJson.object(r.get("owner"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));owner=Optional.of(new CurrentLetterResult.OwnerWitness(decimal(w,"connection_generation"),decimal(w,"ticket_sequence"),decimal(w,"pump_epoch"),NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
            if(!r.get("source").isNull())source=Optional.of(CurrentSupermanHealthSource.decode(r.get("source")));
            if(bool(r,"source_available")!=source.isPresent())throw new IOException("Superman health source availability/null mismatch");
            return new CurrentSupermanHealthResult(CurrentSupermanHealth.Action.parse(NativeWire.text(r.get("action"))),Status.parse(NativeWire.text(r.get("status"))),bool(r,"effect_attempted"),bool(r,"native_returned"),bool(r,"cleanup_known"),decimal(r,"provider_generation"),decimal(r,"query_sequence"),decimal(r,"claim_sequence"),core,owner,source,r.get("unavailable_reason").isNull()?Optional.empty():Optional.of(NativeWire.text(r.get("unavailable_reason"))),CurrentSupermanHealth.Phase.parse(NativeWire.text(r.get("phase"))));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact current Superman health DATA",invalid);}
    }
    public static CurrentSupermanHealthResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var e=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));
            require(e,"type","command_result");require(e,"request_id",original.requestId());NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(bool(e,"ok")!=original.nativeOk())throw new IOException("Original Superman health envelope ok mismatch");
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original Superman health result token absent"));
            if(!NativeWire.parse(token.bytes()).equals(e.get("result")))throw new IOException("Superman health result differs from original envelope");
            var result=decode(new RawJson(token.bytes()));if(result.successful()!=original.nativeOk())throw new IOException("Native ok differs from coherent actual-source/void-dispatch result");return result;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid actual Superman health acknowledgement",invalid);}
    }
    public RawJson encode() {
        var b=ExactCk3Build.CK3_121003_STEAM_26785313;
        var r=StrictJson.object().put("schema",CurrentSupermanHealth.RESULT_SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT))
                .put("backend",CurrentSupermanHealth.BACKEND).put("adapter_id",b.coreFrameAdapterId()).put("action",action.wire()).put("status",status.wire())
                .put("source_available",source.isPresent()).put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("native_handled",false).put("cleanup_known",cleanupKnown)
                .put("provider_generation",providerGeneration.toString()).put("query_sequence",querySequence.toString()).put("claim_sequence",claimSequence.toString());
        if(factsBefore.isPresent()){var p=factsBefore.orElseThrow();r.putObject("facts_before").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());var w=owner.orElseThrow();r.putObject("owner").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());}
        else{r.putNull("facts_before");r.putNull("owner");}
        if(source.isPresent())r.set("source",source.orElseThrow().encode());else r.putNull("source");
        r.put("phase",phase.wire());
        r.put("addresses_redacted",true).put("event_closed",false).put("health_changed",false).put("trait_UI_rendered",false).put("new_date_observed",false).put("physical_save_confirmed",false);
        if(unavailableReason.isPresent())r.put("unavailable_reason",unavailableReason.orElseThrow());else r.putNull("unavailable_reason");return new RawJson(StrictJson.canonical(r));
    }
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static boolean bool(ObjectNode r,String k)throws IOException {var n=r.get(k);if(n==null||!n.isBoolean())throw new IOException("Actual Superman health bool required: "+k);return n.booleanValue();}
    private static BigInteger decimal(ObjectNode r,String k)throws IOException {String s=NativeWire.text(r.get(k));if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical uint64 string required: "+k);var n=new BigInteger(s);CurrentLetter.unsigned(n,false);return n;}
    private static void require(ObjectNode r,String k,String expected)throws IOException {if(!NativeWire.text(r.get(k)).equals(expected))throw new IOException("Exact current Superman health identity mismatch: "+k);}
}
