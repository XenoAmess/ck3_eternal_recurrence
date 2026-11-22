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

/** Finite original Native DATA. Dispatched/handled never means closed/applied/paid/date/SAVE. */
public record CurrentLydResult(CurrentLyd.Action action,Status status,boolean effectAttempted,boolean nativeReturned,
        boolean nativeHandled,boolean cleanupKnown,BigInteger providerGeneration,BigInteger querySequence,BigInteger claimSequence,
        Optional<CurrentLyd.DecisionKey> decisionKey,Optional<CurrentLyd.PersonalKey> personalKey,Optional<CurrentLyd.EventRole> eventRole,
        Optional<Integer> instanceId,Optional<CoreFrame.Prefix> factsBefore,Optional<CurrentLetterResult.OwnerWitness> owner,
        Optional<CurrentLydSource> source,Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_SOURCE("stale_source"),CLAIM_CONSUMED("claim_consumed"),
        AVAILABLE("available"),NAVIGATION_DISPATCHED("navigation_dispatched"),SELECTION_DISPATCHED("selection_dispatched"),
        CONFIRMATION_DISPATCHED("confirmation_dispatched"),INDETERMINATE("indeterminate");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Status parse(String value)throws IOException{for(var s:values())if(s.wire.equals(value))return s;throw new IOException("Unknown exact LYD status");}
    }
    public CurrentLydResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);CurrentLetter.unsigned(providerGeneration,false);CurrentLetter.unsigned(querySequence,false);CurrentLetter.unsigned(claimSequence,false);
        Objects.requireNonNull(decisionKey);Objects.requireNonNull(personalKey);Objects.requireNonNull(eventRole);Objects.requireNonNull(instanceId);
        Objects.requireNonNull(factsBefore);Objects.requireNonNull(owner);Objects.requireNonNull(source);Objects.requireNonNull(unavailableReason);
        CurrentLyd.requireTarget(action,new CurrentLyd.Target(decisionKey,personalKey,eventRole,instanceId,""),false);
        StrictJson.require(!nativeReturned||effectAttempted,"Returned action requires actual effect attempt");
        if(nativeHandled)StrictJson.require(nativeReturned&&(action==CurrentLyd.Action.OPEN_LIST||action==CurrentLyd.Action.OPEN_PERSONAL),"Only the two actual native Toggles have handled bool DATA");
        StrictJson.require(factsBefore.isPresent()==owner.isPresent(),"Actual original Core/owner nullable roles differ");
        factsBefore.ifPresent(CurrentLetter::requirePrefix);
        if(source.isPresent())StrictJson.require(factsBefore.isPresent()&&cleanupKnown&&source.orElseThrow().kind()==action.kind(),"Whole typed Source requires original owner/Core/cleanup and matching union kind");
        if(action.isQuery())StrictJson.require(claimSequence.signum()==0&&!effectAttempted&&!nativeReturned&&!nativeHandled,"Query has no effect claim or action flags");
        else StrictJson.require(providerGeneration.signum()>0&&querySequence.signum()>0,"Parsed action ACK retains original positive private lease and targets");
        if(status==Status.AVAILABLE)StrictJson.require(action.isQuery()&&source.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0
                &&cleanupKnown&&unavailableReason.isEmpty(),"Available requires full actual LYD query source");
        else if(status==Status.NAVIGATION_DISPATCHED||status==Status.SELECTION_DISPATCHED||status==Status.CONFIRMATION_DISPATCHED) {
            StrictJson.require(!action.isQuery()&&status==dispatchedStatus(action)&&source.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0
                    &&claimSequence.signum()>0&&effectAttempted&&nativeReturned&&cleanupKnown&&unavailableReason.isEmpty(),"Dispatch requires actual once claim and immutable beforeSource");
            StrictJson.require(source.orElseThrow().admitsResult(action,decisionKey,personalKey,eventRole,instanceId,factsBefore.orElseThrow().playedCharacterId()),"Dispatched action lacks exact public Source shape admission");
        } else {
            StrictJson.require(unavailableReason.filter(s->!s.isEmpty()).isPresent(),"Actual refusal/unknown reason required");
            if(status!=Status.INDETERMINATE)StrictJson.require(!effectAttempted&&!nativeReturned&&!nativeHandled,"Known refusal has zero action flags, even if claim was spent");
        }
    }
    public boolean successful(){return status==Status.AVAILABLE||status==Status.NAVIGATION_DISPATCHED||status==Status.SELECTION_DISPATCHED||status==Status.CONFIRMATION_DISPATCHED;}
    public static Status dispatchedStatus(CurrentLyd.Action action){
        Objects.requireNonNull(action);
        return switch(action){
            case CONFIRM_DECISION,CHOOSE_KNOWN_EVENT_OPTION,CONFIRM_PERSONAL_ADD->Status.CONFIRMATION_DISPATCHED;
            case OPEN_DETAIL,SELECT_PERSONAL_CANDIDATE->Status.SELECTION_DISPATCHED;
            case OPEN_LIST,OPEN_PERSONAL,START_ADD_PERSONAL->Status.NAVIGATION_DISPATCHED;
            default->throw new IllegalArgumentException("Query has no dispatch status");
        };
    }
    public static CurrentLydResult decode(RawJson raw)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","backend","adapter_id","action","status","source_available","effect_attempted","native_returned","native_handled","cleanup_known","provider_generation","query_sequence","claim_sequence","decision_key","personal_key","event_role","instance_id","facts_before","owner","source","addresses_redacted","event_closed","personal_applied","gold_paid","piety_paid","modifiers_applied","new_date_observed","physical_save_confirmed","unavailable_reason"));
            var build=ExactCk3Build.CK3_121003_STEAM_26785313;
            require(r,"schema",CurrentLyd.RESULT_SCHEMA);require(r,"game_version",build.version());require(r,"executable_sha256",build.executableSha256().toUpperCase(Locale.ROOT));
            require(r,"backend",CurrentLyd.BACKEND);require(r,"adapter_id",build.coreFrameAdapterId());
            if(!CurrentLyd.bool(r,"addresses_redacted")||CurrentLyd.bool(r,"event_closed")||CurrentLyd.bool(r,"personal_applied")||CurrentLyd.bool(r,"gold_paid")
                    ||CurrentLyd.bool(r,"piety_paid")||CurrentLyd.bool(r,"modifiers_applied")||CurrentLyd.bool(r,"new_date_observed")||CurrentLyd.bool(r,"physical_save_confirmed"))
                throw new IOException("Native LYD dispatch cannot claim applied/paid/closed/date/SAVE");
            Optional<CoreFrame.Prefix> facts=r.get("facts_before").isNull()?Optional.empty():Optional.of(CurrentLyd.readCore(r.get("facts_before")));
            Optional<CurrentLetterResult.OwnerWitness> owner=Optional.empty();
            if(!r.get("owner").isNull()) {
                var w=StrictJson.object(r.get("owner"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));
                owner=Optional.of(new CurrentLetterResult.OwnerWitness(CurrentLyd.decimal(w,"connection_generation"),CurrentLyd.decimal(w,"ticket_sequence"),CurrentLyd.decimal(w,"pump_epoch"),
                        NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
            }
            Optional<CurrentLydSource> source=r.get("source").isNull()?Optional.empty():Optional.of(CurrentLydSource.decode(r.get("source")));
            if(CurrentLyd.bool(r,"source_available")!=source.isPresent())throw new IOException("LYD Source availability/null mismatch");
            return new CurrentLydResult(CurrentLyd.Action.parse(NativeWire.text(r.get("action"))),Status.parse(NativeWire.text(r.get("status"))),CurrentLyd.bool(r,"effect_attempted"),CurrentLyd.bool(r,"native_returned"),
                    CurrentLyd.bool(r,"native_handled"),CurrentLyd.bool(r,"cleanup_known"),CurrentLyd.decimal(r,"provider_generation"),CurrentLyd.decimal(r,"query_sequence"),CurrentLyd.decimal(r,"claim_sequence"),
                    CurrentLydSource.decision(r.get("decision_key")),CurrentLydSource.personalKey(r.get("personal_key")),CurrentLydSource.role(r.get("event_role")),CurrentLyd.integer(r.get("instance_id")),facts,owner,source,
                    r.get("unavailable_reason").isNull()?Optional.empty():Optional.of(CurrentLyd.nativeText(r.get("unavailable_reason"))));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact current LYD DATA",invalid);}
    }
    public static CurrentLydResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));
            require(r,"type","command_result");require(r,"request_id",original.requestId());NativeWire.integer(r.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(CurrentLyd.bool(r,"ok")!=original.nativeOk())throw new IOException("Original LYD envelope ok mismatch");
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original LYD result token absent"));
            if(!NativeWire.parse(token.bytes()).equals(r.get("result")))throw new IOException("LYD token differs from actual envelope");
            var result=decode(new RawJson(token.bytes()));if(result.successful()!=original.nativeOk())throw new IOException("LYD envelope ok differs from coherent source/dispatch");return result;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid original LYD ACK",invalid);}
    }
    public RawJson encode(){
        var b=ExactCk3Build.CK3_121003_STEAM_26785313;
        var r=StrictJson.object().put("schema",CurrentLyd.RESULT_SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT))
                .put("backend",CurrentLyd.BACKEND).put("adapter_id",b.coreFrameAdapterId()).put("action",action.wire()).put("status",status.wire())
                .put("source_available",source.isPresent()).put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("native_handled",nativeHandled).put("cleanup_known",cleanupKnown)
                .put("provider_generation",providerGeneration.toString()).put("query_sequence",querySequence.toString()).put("claim_sequence",claimSequence.toString());
        CurrentLyd.putText(r,"decision_key",decisionKey.map(CurrentLyd.DecisionKey::wire));CurrentLyd.putText(r,"personal_key",personalKey.map(CurrentLyd.PersonalKey::wire));
        CurrentLyd.putText(r,"event_role",eventRole.map(CurrentLyd.EventRole::wire));CurrentLyd.putInteger(r,"instance_id",instanceId);
        if(factsBefore.isPresent()){r.set("facts_before",CurrentLyd.core(factsBefore.orElseThrow()));var w=owner.orElseThrow();r.putObject("owner").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());}
        else{r.putNull("facts_before");r.putNull("owner");}
        if(source.isPresent())r.set("source",source.orElseThrow().encode());else r.putNull("source");
        r.put("addresses_redacted",true).put("event_closed",false).put("personal_applied",false).put("gold_paid",false).put("piety_paid",false).put("modifiers_applied",false).put("new_date_observed",false).put("physical_save_confirmed",false);
        CurrentLyd.putText(r,"unavailable_reason",unavailableReason);return new RawJson(StrictJson.canonical(r));
    }
    private static void require(ObjectNode r,String key,String expected)throws IOException{if(!NativeWire.text(r.get(key)).equals(expected))throw new IOException("Exact LYD identity mismatch: "+key);}
}
