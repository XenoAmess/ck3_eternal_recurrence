package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact original operation DATA. Pending/running/dispatch are not completed RMTM business or a fresh Core. */
public record CurrentRmtmActorTransitionResult(CurrentRmtmActorTransition.Action action,String requestId,String operationId,
        Status status,boolean ok,boolean accepted,BigInteger providerGeneration,BigInteger querySequence,BigInteger claimSequence,
        BigInteger actorEpoch,int completedNaturalDays,BigInteger deadlineUnixMs,BigInteger connectionGeneration,BigInteger ticketSequence,BigInteger pumpEpoch,
        long threadId,Optional<CoreFrame.Prefix> factsBefore,Optional<CurrentRmtmActorTransitionSource> source,Optional<Progress> progress,
        boolean effectAttempted,boolean nativeReturned,boolean cleanupKnown,Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_SOURCE("stale_source"),CLAIM_CONSUMED("claim_consumed"),
        CAPACITY_EXHAUSTED("capacity_exhausted"),AVAILABLE("available"),SUBMITTED("submitted"),RUNNING("running"),
        COMPLETED_DAY("completed_day"),TRANSITION_PENDING("transition_pending"),EPOCH_CONFIRMED("epoch_confirmed"),INDETERMINATE("indeterminate");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Status parse(String value)throws IOException{
            for(var status:values())if(status.wire.equals(value))return status;throw new IOException("Unknown current RMTM transition status");
        }
        public boolean isOk(){return this==AVAILABLE||this==SUBMITTED||this==RUNNING||this==COMPLETED_DAY||this==TRANSITION_PENDING||this==EPOCH_CONFIRMED;}
    }
    public record Progress(BigInteger generation,int startingDateRaw,int targetDateRaw,int lastObservedDateRaw,
            int beforeActorId,int afterActorId,long completedDailyTicks,long failureFlags,int overshootDays,
            boolean armAttempted,boolean resumeAttempted,boolean resumeSubmitted,boolean exactDayConfirmed,
            boolean transitionPending,boolean shutdownSafe,boolean armed,boolean accessCleanupUnknown) {
        public Progress {
            CurrentRmtmActorTransition.unsigned(generation,false);
            StrictJson.require((long)startingDateRaw+24==targetDateRaw&&beforeActorId!=-1&&completedDailyTicks>=0&&completedDailyTicks<=1
                    &&failureFlags>=0&&failureFlags<=0xffff_ffffL&&overshootDays>=-1,"Actual RMTM one-day progress domain");
            if(overshootDays==-1)StrictJson.require(completedDailyTicks==0&&!exactDayConfirmed&&!transitionPending&&lastObservedDateRaw==startingDateRaw&&afterActorId==-1,
                    "Unobserved after actor remains sentinel DATA before the first actual tick");
            StrictJson.require(!resumeSubmitted||resumeAttempted,"Resume submission requires actual attempt");
            StrictJson.require(!resumeAttempted||armAttempted,"Resume attempt requires original ARM attempt");
            StrictJson.require(!armed||generation.signum()>0,"Armed operation requires generation");
            if(exactDayConfirmed)StrictJson.require(generation.signum()>0&&failureFlags==0&&overshootDays==0&&completedDailyTicks==1&&lastObservedDateRaw==targetDateRaw
                    &&afterActorId!=-1&&!armed&&shutdownSafe&&!accessCleanupUnknown&&resumeSubmitted,"Exact one day requires actual terminal tick and safe disarmed cleanup");
            if(transitionPending)StrictJson.require(exactDayConfirmed&&beforeActorId!=afterActorId,"Pending requires proven distinct actors");
        }
        static Progress decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("generation","starting_date_raw","target_date_raw","last_observed_date_raw","before_actor_id","after_actor_id","completed_daily_ticks","failure_flags","overshoot_days","arm_attempted","resume_attempted","resume_submitted","exact_day_confirmed","transition_pending","shutdown_safe","armed","access_cleanup_unknown"));
            return new Progress(CurrentRmtmActorTransition.decimal(r,"generation"),CurrentRmtmActorTransition.i32(r.get("starting_date_raw")),CurrentRmtmActorTransition.i32(r.get("target_date_raw")),
                    CurrentRmtmActorTransition.i32(r.get("last_observed_date_raw")),CurrentRmtmActorTransition.i32(r.get("before_actor_id")),CurrentRmtmActorTransition.i32(r.get("after_actor_id")),
                    CurrentRmtmActorTransition.u32(r.get("completed_daily_ticks")),CurrentRmtmActorTransition.u32(r.get("failure_flags")),CurrentRmtmActorTransition.i32(r.get("overshoot_days")),
                    CurrentRmtmActorTransition.bool(r,"arm_attempted"),CurrentRmtmActorTransition.bool(r,"resume_attempted"),CurrentRmtmActorTransition.bool(r,"resume_submitted"),
                    CurrentRmtmActorTransition.bool(r,"exact_day_confirmed"),CurrentRmtmActorTransition.bool(r,"transition_pending"),CurrentRmtmActorTransition.bool(r,"shutdown_safe"),
                    CurrentRmtmActorTransition.bool(r,"armed"),CurrentRmtmActorTransition.bool(r,"access_cleanup_unknown"));
        }
        ObjectNode encode(){return StrictJson.object().put("generation",generation.toString()).put("starting_date_raw",startingDateRaw).put("target_date_raw",targetDateRaw)
                .put("last_observed_date_raw",lastObservedDateRaw).put("before_actor_id",beforeActorId).put("after_actor_id",afterActorId)
                .put("completed_daily_ticks",completedDailyTicks).put("failure_flags",failureFlags).put("overshoot_days",overshootDays)
                .put("arm_attempted",armAttempted).put("resume_attempted",resumeAttempted).put("resume_submitted",resumeSubmitted)
                .put("exact_day_confirmed",exactDayConfirmed).put("transition_pending",transitionPending).put("shutdown_safe",shutdownSafe)
                .put("armed",armed).put("access_cleanup_unknown",accessCleanupUnknown);}
    }
    public CurrentRmtmActorTransitionResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);CurrentRmtmActorTransition.identifier(requestId);Objects.requireNonNull(operationId);
        CurrentRmtmActorTransition.unsigned(providerGeneration,false);CurrentRmtmActorTransition.unsigned(querySequence,false);CurrentRmtmActorTransition.unsigned(claimSequence,false);
        CurrentRmtmActorTransition.epoch(actorEpoch);CurrentRmtmActorTransition.requireDays(completedNaturalDays);CurrentRmtmActorTransition.unsigned(deadlineUnixMs,true);
        CurrentRmtmActorTransition.unsigned(connectionGeneration,false);CurrentRmtmActorTransition.unsigned(ticketSequence,false);CurrentRmtmActorTransition.unsigned(pumpEpoch,false);
        Objects.requireNonNull(factsBefore);Objects.requireNonNull(source);Objects.requireNonNull(progress);Objects.requireNonNull(unavailableReason);
        StrictJson.require(threadId>=0&&threadId<=0xffff_ffffL&&ok==status.isOk(),"Exact status/owner integer shape");
        if(factsBefore.isPresent()){
            CurrentRmtmActorTransition.requireCore(factsBefore.orElseThrow());
            StrictJson.require(connectionGeneration.signum()>0&&ticketSequence.signum()>0&&pumpEpoch.signum()>0&&threadId>0,"Actual Core requires all positive owner witnesses");
        }else StrictJson.require(connectionGeneration.signum()==0&&ticketSequence.signum()==0&&pumpEpoch.signum()==0&&threadId==0,"SourceNull Core requires owner zeros");
        if(source.isPresent())StrictJson.require(factsBefore.isPresent()&&cleanupKnown,"Complete RMTM Source requires actual Core and known cleanup");
        if(action==CurrentRmtmActorTransition.Action.QUERY_ROLE)StrictJson.require(operationId.isEmpty()&&!accepted&&claimSequence.signum()==0&&!effectAttempted&&!nativeReturned&&progress.isEmpty(),"Role query is readonly without ARM or progress");
        else CurrentRmtmActorTransition.identifier(operationId);
        if(action==CurrentRmtmActorTransition.Action.QUERY_OPERATION)StrictJson.require(source.isEmpty(),"Original operation read never supplies a fresh role Source");
        if(!cleanupKnown)StrictJson.require(status==Status.INDETERMINATE,"Unknown cleanup remains indeterminate");
        if(status==Status.INDETERMINATE)StrictJson.require(source.isEmpty(),"UNKNOWN remains SourceNull");
        if(status==Status.AVAILABLE){
            StrictJson.require(action==CurrentRmtmActorTransition.Action.QUERY_ROLE&&source.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0
                    &&cleanupKnown&&unavailableReason.isEmpty()&&source.orElseThrow().actorEpoch().equals(actorEpoch),"Available exact role-query coherence");
        }else if(status==Status.EPOCH_CONFIRMED){
            StrictJson.require(action==CurrentRmtmActorTransition.Action.CONFIRM_EPOCH&&source.isPresent()&&source.orElseThrow().confirmAdmissible()
                    &&source.orElseThrow().actorEpoch().signum()==0&&actorEpoch.equals(BigInteger.ONE)&&accepted&&claimSequence.signum()>0&&providerGeneration.signum()>0&&querySequence.signum()>0
                    &&!effectAttempted&&!nativeReturned&&progress.isEmpty()&&cleanupKnown&&unavailableReason.isEmpty(),"Epoch1 consumes original beforeSource0 custody, not a Game effect");
        }else if(status==Status.SUBMITTED||status==Status.RUNNING||status==Status.COMPLETED_DAY||status==Status.TRANSITION_PENDING){
            StrictJson.require((action==CurrentRmtmActorTransition.Action.ADVANCE_DAY||action==CurrentRmtmActorTransition.Action.QUERY_OPERATION)&&accepted&&claimSequence.signum()>0
                    &&providerGeneration.signum()>0&&querySequence.signum()>0&&factsBefore.isPresent()&&progress.isPresent()&&effectAttempted&&nativeReturned&&cleanupKnown&&unavailableReason.isEmpty(),
                    "Retained one-day status requires its actual original claim/progress/ARM flags");
            if(action==CurrentRmtmActorTransition.Action.ADVANCE_DAY)StrictJson.require(source.filter(CurrentRmtmActorTransitionSource::advanceAdmissible).isPresent(),"Successful advance retains immutable admitted beforeSource");
            var p=progress.orElseThrow();
            StrictJson.require(p.armAttempted()&&p.resumeAttempted()&&p.resumeSubmitted(),"Successful retained day requires actual ARM/Resume");
            if(status==Status.SUBMITTED)StrictJson.require(!p.exactDayConfirmed()&&!p.transitionPending()&&p.failureFlags()==0&&!p.accessCleanupUnknown(),"Submitted is not a completed tick");
            else if(status==Status.RUNNING)StrictJson.require(!p.transitionPending()&&p.failureFlags()==0&&!p.accessCleanupUnknown()
                    &&(!p.exactDayConfirmed()||action==CurrentRmtmActorTransition.Action.QUERY_OPERATION&&actorEpoch.signum()==0&&p.beforeActorId()==p.afterActorId()),"Running original-operation state differs");
            else{
                StrictJson.require(p.exactDayConfirmed()&&!p.armed()&&p.shutdownSafe()&&!p.accessCleanupUnknown()&&p.failureFlags()==0&&p.completedDailyTicks()==1&&p.overshootDays()==0&&p.afterActorId()!=-1,"Terminal actual one-tick proof required");
                if(status==Status.TRANSITION_PENDING)StrictJson.require(p.transitionPending()&&actorEpoch.signum()==0&&p.beforeActorId()!=p.afterActorId(),"Actual pending retains frontier0 and actual actor transition");
                else StrictJson.require(!p.transitionPending()&&p.beforeActorId()==p.afterActorId(),"Completed day retains its actual before actor");
            }
        }else if(status!=Status.INDETERMINATE)StrictJson.require(!accepted&&!effectAttempted&&!nativeReturned&&cleanupKnown,"Known missing/refused claim has no ARM; retained failures become UNKNOWN");
        if(status.isOk())StrictJson.require(unavailableReason.isEmpty(),"Success reason is empty actual text");
        else StrictJson.require(unavailableReason.filter(x->!x.isEmpty()).isPresent(),"Original refusal/UNKNOWN reason required");
        if((action==CurrentRmtmActorTransition.Action.ADVANCE_DAY||action==CurrentRmtmActorTransition.Action.QUERY_OPERATION)&&progress.isPresent()){
            var p=progress.orElseThrow();StrictJson.require(factsBefore.filter(f->f.playedCharacterId()==p.beforeActorId()&&f.dateRaw()==p.startingDateRaw()).isPresent(),"Original ARM actor/date facts remain beforeSource, not new recipient Core");
        }
        if(action==CurrentRmtmActorTransition.Action.CONFIRM_EPOCH)StrictJson.require(!effectAttempted&&!nativeReturned,"Epoch confirmation never calls ARM/Resume");
    }
    public boolean sourceAvailable(){return source.isPresent();}
    public boolean successful(){return ok;}
    public Optional<CurrentLetterResult.OwnerWitness> owner(){return factsBefore.isEmpty()?Optional.empty():Optional.of(new CurrentLetterResult.OwnerWitness(connectionGeneration,ticketSequence,pumpEpoch,threadId));}
    private static Optional<String> reasonText(JsonNode node)throws IOException {
        if(node==null||!node.isTextual())throw new IOException("RMTM transition reason must retain actual JSON string");
        if(node.textValue().isEmpty())return Optional.empty();
        return Optional.of(NativeWire.text(node)); // Known refusals still require a nonempty reason in the constructor.
    }
    private static String operationText(JsonNode node)throws IOException {
        if(node==null||!node.isTextual()||!node.textValue().matches("[A-Za-z0-9_.-]{0,96}"))throw new IOException("Bounded actual RMTM operation text required");
        return node.textValue(); // Only QUERY_ROLE may retain the empty string; the constructor checks every other action.
    }
    public static CurrentRmtmActorTransitionResult decode(RawJson raw)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","backend","action","request_id","operation_id","status","ok","accepted","source_available","unavailable_reason",
                    "provider_generation","query_sequence","claim_sequence","actor_epoch","completed_natural_days","deadline_unix_ms","connection_generation","ticket_sequence","pump_epoch","thread_id","facts_before","source","progress","effect_attempted","native_returned","cleanup_known","core_after"));
            require(r,"schema",CurrentRmtmActorTransition.RESULT_SCHEMA);require(r,"backend",CurrentRmtmActorTransition.BACKEND);
            if(!r.get("core_after").isNull())throw new IOException("RMTM result never manufactures independent after Core");
            Optional<CoreFrame.Prefix> facts=r.get("facts_before").isNull()?Optional.empty():Optional.of(CurrentRmtmActorTransition.readCore(r.get("facts_before")));
            Optional<CurrentRmtmActorTransitionSource> source=r.get("source").isNull()?Optional.empty():Optional.of(CurrentRmtmActorTransitionSource.decode(r.get("source")));
            if(CurrentRmtmActorTransition.bool(r,"source_available")!=source.isPresent())throw new IOException("RMTM Source availability/null mismatch");
            return new CurrentRmtmActorTransitionResult(CurrentRmtmActorTransition.Action.parse(NativeWire.text(r.get("action"))),NativeWire.text(r.get("request_id")),operationText(r.get("operation_id")),
                    Status.parse(NativeWire.text(r.get("status"))),CurrentRmtmActorTransition.bool(r,"ok"),CurrentRmtmActorTransition.bool(r,"accepted"),
                    CurrentRmtmActorTransition.decimal(r,"provider_generation"),CurrentRmtmActorTransition.decimal(r,"query_sequence"),CurrentRmtmActorTransition.decimal(r,"claim_sequence"),
                    CurrentRmtmActorTransition.decimal(r,"actor_epoch"),CurrentRmtmActorTransition.days(r.get("completed_natural_days")),CurrentRmtmActorTransition.deadline(r,"deadline_unix_ms"),CurrentRmtmActorTransition.decimal(r,"connection_generation"),
                    CurrentRmtmActorTransition.decimal(r,"ticket_sequence"),CurrentRmtmActorTransition.decimal(r,"pump_epoch"),CurrentRmtmActorTransition.u32(r.get("thread_id")),facts,source,
                    r.get("progress").isNull()?Optional.empty():Optional.of(Progress.decode(r.get("progress"))),CurrentRmtmActorTransition.bool(r,"effect_attempted"),
                    CurrentRmtmActorTransition.bool(r,"native_returned"),CurrentRmtmActorTransition.bool(r,"cleanup_known"),
                    reasonText(r.get("unavailable_reason")));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact RMTM transition DATA",invalid);}
    }
    public static CurrentRmtmActorTransitionResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var envelope=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));
            require(envelope,"type","command_result");require(envelope,"request_id",original.requestId());NativeWire.integer(envelope.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(CurrentRmtmActorTransition.bool(envelope,"ok")!=original.nativeOk())throw new IOException("RMTM envelope ok differs from original ACK");
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original RMTM result token absent"));
            if(!NativeWire.parse(token.bytes()).equals(envelope.get("result")))throw new IOException("RMTM result token differs from original envelope");
            var result=decode(new RawJson(token.bytes()));
            if(!result.requestId().equals(original.requestId())||result.ok()!=original.nativeOk())throw new IOException("RMTM result original ID/ok mismatch");
            return result;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid original RMTM acknowledgement",invalid);}
    }
    public RawJson encode(){
        var r=StrictJson.object().put("schema",CurrentRmtmActorTransition.RESULT_SCHEMA).put("backend",CurrentRmtmActorTransition.BACKEND).put("action",action.wire())
                .put("request_id",requestId).put("operation_id",operationId).put("status",status.wire()).put("ok",ok).put("accepted",accepted)
                .put("source_available",source.isPresent()).put("provider_generation",providerGeneration.toString()).put("query_sequence",querySequence.toString())
                .put("claim_sequence",claimSequence.toString()).put("actor_epoch",actorEpoch.toString()).put("completed_natural_days",completedNaturalDays).put("deadline_unix_ms",deadlineUnixMs)
                .put("connection_generation",connectionGeneration.toString()).put("ticket_sequence",ticketSequence.toString()).put("pump_epoch",pumpEpoch.toString()).put("thread_id",threadId)
                .put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("cleanup_known",cleanupKnown).putNull("core_after");
        if(factsBefore.isPresent())r.set("facts_before",CurrentRmtmActorTransition.core(factsBefore.orElseThrow()));else r.putNull("facts_before");
        if(source.isPresent())r.set("source",source.orElseThrow().encode());else r.putNull("source");
        if(progress.isPresent())r.set("progress",progress.orElseThrow().encode());else r.putNull("progress");
        if(unavailableReason.isPresent())r.put("unavailable_reason",unavailableReason.orElseThrow());else r.put("unavailable_reason","");
        return new RawJson(StrictJson.canonical(r));
    }
    private static void require(ObjectNode r,String key,String expected)throws IOException{
        if(!NativeWire.text(r.get(key)).equals(expected))throw new IOException("Exact RMTM identity mismatch: "+key);
    }
}
