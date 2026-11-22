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

/** Exact original operation DATA. Pending/running/dispatch are not completed TED business or a fresh Core. */
public record CurrentTedActorTransitionResult(CurrentTedActorTransition.Action action,String requestId,String operationId,
        Status status,boolean ok,boolean accepted,BigInteger providerGeneration,BigInteger querySequence,BigInteger claimSequence,
        BigInteger actorEpoch,long deadlineUnixMs,BigInteger connectionGeneration,BigInteger ticketSequence,BigInteger pumpEpoch,
        long threadId,Optional<CoreFrame.Prefix> factsBefore,Optional<CurrentTedActorTransitionSource> source,Optional<Progress> progress,
        boolean effectAttempted,boolean nativeReturned,boolean cleanupKnown,Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_SOURCE("stale_source"),CLAIM_CONSUMED("claim_consumed"),
        CAPACITY_EXHAUSTED("capacity_exhausted"),AVAILABLE("available"),SUBMITTED("submitted"),RUNNING("running"),
        COMPLETED_DAY("completed_day"),TRANSITION_PENDING("transition_pending"),EPOCH_CONFIRMED("epoch_confirmed"),INDETERMINATE("indeterminate");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Status parse(String value)throws IOException{
            for(var status:values())if(status.wire.equals(value))return status;throw new IOException("Unknown current TED transition status");
        }
        public boolean isOk(){return this==AVAILABLE||this==SUBMITTED||this==RUNNING||this==COMPLETED_DAY||this==TRANSITION_PENDING||this==EPOCH_CONFIRMED;}
    }
    public record Progress(BigInteger generation,int startingDateRaw,int targetDateRaw,int lastObservedDateRaw,
            int beforeActorId,int afterActorId,long completedDailyTicks,long failureFlags,int overshootDays,
            boolean armAttempted,boolean resumeAttempted,boolean resumeSubmitted,boolean exactDayConfirmed,
            boolean transitionPending,boolean shutdownSafe,boolean armed,boolean accessCleanupUnknown) {
        public Progress {
            CurrentTedActorTransition.unsigned(generation,false);
            StrictJson.require(completedDailyTicks>=0&&completedDailyTicks<=0xffff_ffffL&&failureFlags>=0&&failureFlags<=0xffff_ffffL,"Actual uint32 progress counters required");
            StrictJson.require(!resumeSubmitted||resumeAttempted,"Submitted resume requires actual attempt");
            if(exactDayConfirmed||transitionPending)StrictJson.require(generation.signum()>0&&beforeActorId!=-1&&afterActorId!=-1
                    &&(long)startingDateRaw+24==targetDateRaw&&lastObservedDateRaw==targetDateRaw&&completedDailyTicks==1&&failureFlags==0&&overshootDays==0
                    &&armAttempted&&resumeAttempted&&resumeSubmitted&&exactDayConfirmed&&shutdownSafe&&!armed&&!accessCleanupUnknown,
                    "Exact TED day requires actual actor samples, one daily tick and disarmed safe cleanup");
            if(transitionPending)StrictJson.require(beforeActorId!=afterActorId,"Pending transition requires two different actual actors");
            // Until an actual snapshot exists, before/after=-1 remain unknown DATA, never a fabricated identity.
        }
        static Progress decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("generation","starting_date_raw","target_date_raw","last_observed_date_raw","before_actor_id","after_actor_id","completed_daily_ticks","failure_flags","overshoot_days","arm_attempted","resume_attempted","resume_submitted","exact_day_confirmed","transition_pending","shutdown_safe","armed","access_cleanup_unknown"));
            return new Progress(CurrentTedActorTransition.decimal(r,"generation"),CurrentTedActorTransition.i32(r.get("starting_date_raw")),CurrentTedActorTransition.i32(r.get("target_date_raw")),
                    CurrentTedActorTransition.i32(r.get("last_observed_date_raw")),CurrentTedActorTransition.i32(r.get("before_actor_id")),CurrentTedActorTransition.i32(r.get("after_actor_id")),
                    CurrentTedActorTransition.u32(r.get("completed_daily_ticks")),CurrentTedActorTransition.u32(r.get("failure_flags")),CurrentTedActorTransition.i32(r.get("overshoot_days")),
                    CurrentTedActorTransition.bool(r,"arm_attempted"),CurrentTedActorTransition.bool(r,"resume_attempted"),CurrentTedActorTransition.bool(r,"resume_submitted"),
                    CurrentTedActorTransition.bool(r,"exact_day_confirmed"),CurrentTedActorTransition.bool(r,"transition_pending"),CurrentTedActorTransition.bool(r,"shutdown_safe"),
                    CurrentTedActorTransition.bool(r,"armed"),CurrentTedActorTransition.bool(r,"access_cleanup_unknown"));
        }
        ObjectNode encode(){return StrictJson.object().put("generation",generation.toString()).put("starting_date_raw",startingDateRaw).put("target_date_raw",targetDateRaw)
                .put("last_observed_date_raw",lastObservedDateRaw).put("before_actor_id",beforeActorId).put("after_actor_id",afterActorId)
                .put("completed_daily_ticks",completedDailyTicks).put("failure_flags",failureFlags).put("overshoot_days",overshootDays)
                .put("arm_attempted",armAttempted).put("resume_attempted",resumeAttempted).put("resume_submitted",resumeSubmitted)
                .put("exact_day_confirmed",exactDayConfirmed).put("transition_pending",transitionPending).put("shutdown_safe",shutdownSafe)
                .put("armed",armed).put("access_cleanup_unknown",accessCleanupUnknown);}
    }
    public CurrentTedActorTransitionResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);CurrentTedActorTransition.identifier(requestId);Objects.requireNonNull(operationId);
        CurrentTedActorTransition.unsigned(providerGeneration,false);CurrentTedActorTransition.unsigned(querySequence,false);
        CurrentTedActorTransition.unsigned(claimSequence,false);CurrentTedActorTransition.epoch(actorEpoch);
        CurrentTedActorTransition.unsigned(connectionGeneration,false);CurrentTedActorTransition.unsigned(ticketSequence,false);CurrentTedActorTransition.unsigned(pumpEpoch,false);
        Objects.requireNonNull(factsBefore);Objects.requireNonNull(source);Objects.requireNonNull(progress);Objects.requireNonNull(unavailableReason);
        StrictJson.require(deadlineUnixMs>0&&threadId>=0&&threadId<=0xffff_ffffL,"Parsed original positive deadline and uint32 thread required");
        StrictJson.require(ok==status.isOk(),"TED ok must match exact status, without treating it as business completion");
        StrictJson.require(!nativeReturned||effectAttempted,"Native returned requires actual effect attempt");
        if(factsBefore.isPresent()) {
            CurrentTedActorTransition.requireCore(factsBefore.orElseThrow());
            StrictJson.require(connectionGeneration.signum()>0&&ticketSequence.signum()>0&&pumpEpoch.signum()>0&&threadId>0,"Observed original Core requires all positive owner scalars");
        } else StrictJson.require(connectionGeneration.signum()==0&&ticketSequence.signum()==0&&pumpEpoch.signum()==0&&threadId==0,"Absent original Core requires zero owner scalars");
        if(source.isPresent())StrictJson.require(factsBefore.isPresent()&&cleanupKnown,"Complete Source requires observed owner/Core and known cleanup");
        if(status.isOk()&&(action==CurrentTedActorTransition.Action.ADVANCE_DAY||action==CurrentTedActorTransition.Action.CONFIRM_EPOCH))
            StrictJson.require(source.isPresent(),"Successful action must echo its immutable consumed beforeSource");
        if((action==CurrentTedActorTransition.Action.ADVANCE_DAY||action==CurrentTedActorTransition.Action.QUERY_OPERATION)
                &&progress.isPresent()&&progress.orElseThrow().beforeActorId()!=-1) {
            var p=progress.orElseThrow();
            StrictJson.require(factsBefore.filter(core->core.playedCharacterId()==p.beforeActorId()&&core.dateRaw()==p.startingDateRaw()).isPresent(),
                    "Captured ARM before actor/date must match original checked request Core, not a fresh after Core");
        }
        if(action==CurrentTedActorTransition.Action.QUERY_ROLE) {
            StrictJson.require(operationId.isEmpty()&&claimSequence.signum()==0&&!accepted&&!effectAttempted&&!nativeReturned&&progress.isEmpty(),"Role query never ARM/Resume/claims/progress");
            if(source.isPresent()) {
                var s=source.orElseThrow();var p=factsBefore.orElseThrow();
                StrictJson.require(s.actorEpoch().equals(actorEpoch),"Role query epoch differs from actual source frontier");
                if(s.nativeShown().orElse(false))StrictJson.require((s.role()==CurrentTedActorTransitionSource.Role.SONG?s.songActorId():s.recipientActorId())
                        .filter(id->id==p.playedCharacterId()).isPresent(),"Positive role Source must match independent current Core actor");
            }
        } else {
            CurrentTedActorTransition.identifier(operationId);
            StrictJson.require(providerGeneration.signum()>0&&querySequence.signum()>0,"Parsed operation retains original positive private lease");
        }
        if(action==CurrentTedActorTransition.Action.QUERY_OPERATION)StrictJson.require(source.isEmpty(),"Operation status never supplies a new role source/lease");
        if(status==Status.AVAILABLE)StrictJson.require(action==CurrentTedActorTransition.Action.QUERY_ROLE&&source.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0
                &&cleanupKnown&&unavailableReason.isEmpty(),"Available requires complete actual role query");
        else if(status==Status.EPOCH_CONFIRMED)StrictJson.require(action==CurrentTedActorTransition.Action.CONFIRM_EPOCH&&accepted&&claimSequence.signum()>0
                &&factsBefore.isPresent()&&actorEpoch.equals(BigInteger.ONE)&&!effectAttempted&&!nativeReturned&&cleanupKnown&&unavailableReason.isEmpty(),
                "Epoch confirmation consumes custody once without a Game action");
        else if(status==Status.SUBMITTED||status==Status.RUNNING||status==Status.TRANSITION_PENDING||status==Status.COMPLETED_DAY) {
            StrictJson.require((action==CurrentTedActorTransition.Action.ADVANCE_DAY||action==CurrentTedActorTransition.Action.QUERY_OPERATION)
                    &&accepted&&claimSequence.signum()>0&&factsBefore.isPresent()&&progress.isPresent()&&unavailableReason.isEmpty(),"Date status requires actual retained claim/progress");
            if(status==Status.TRANSITION_PENDING)StrictJson.require(actorEpoch.signum()==0&&progress.orElseThrow().transitionPending()
                    &&progress.orElseThrow().exactDayConfirmed()&&effectAttempted&&nativeReturned&&cleanupKnown,"Pending is only an exact original opt-in day, not an epoch update");
            if(status==Status.COMPLETED_DAY)StrictJson.require(progress.orElseThrow().exactDayConfirmed()&&!progress.orElseThrow().transitionPending()
                    &&progress.orElseThrow().beforeActorId()==progress.orElseThrow().afterActorId()&&cleanupKnown,
                    "Completed day requires actual same-actor result; Main independently requires D1 pending/confirm before D2");
        } else {
            StrictJson.require(unavailableReason.filter(reason->!reason.isEmpty()).isPresent(),"Actual TED refusal/unknown reason required");
            // query_operation exposes ORIGINAL ARM/Resume flags even when the status read is unavailable.
            if(status!=Status.INDETERMINATE&&action!=CurrentTedActorTransition.Action.QUERY_OPERATION)
                StrictJson.require(!effectAttempted&&!nativeReturned,"Known early refusal cannot invent a Game effect");
        }
        if(action==CurrentTedActorTransition.Action.CONFIRM_EPOCH)StrictJson.require(!effectAttempted&&!nativeReturned,"Epoch confirmation never calls Game/ARM/Resume");
    }
    private static Optional<String> reasonText(JsonNode node)throws IOException {
        if(node!=null&&(node.isNull()||node.isTextual()&&node.textValue().isEmpty()))return Optional.empty();
        return Optional.of(NativeWire.text(node)); // Known refusals still require a nonempty reason in the constructor.
    }
    private static String operationText(JsonNode node)throws IOException {
        if(node==null||!node.isTextual()||!node.textValue().matches("[A-Za-z0-9_.-]{0,96}"))throw new IOException("Bounded actual TED operation text required");
        return node.textValue(); // Only QUERY_ROLE may retain the empty string; the constructor checks every other action.
    }
    public static CurrentTedActorTransitionResult decode(RawJson raw)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","backend","action","request_id","operation_id","status","ok","accepted","source_available","unavailable_reason",
                    "provider_generation","query_sequence","claim_sequence","actor_epoch","deadline_unix_ms","connection_generation","ticket_sequence","pump_epoch","thread_id","facts_before","source","progress","effect_attempted","native_returned","cleanup_known","core_after"));
            require(r,"schema",CurrentTedActorTransition.RESULT_SCHEMA);require(r,"backend",CurrentTedActorTransition.BACKEND);
            if(!r.get("core_after").isNull())throw new IOException("TED result never manufactures independent after Core");
            Optional<CoreFrame.Prefix> facts=r.get("facts_before").isNull()?Optional.empty():Optional.of(CurrentTedActorTransition.readCore(r.get("facts_before")));
            Optional<CurrentTedActorTransitionSource> source=r.get("source").isNull()?Optional.empty():Optional.of(CurrentTedActorTransitionSource.decode(r.get("source")));
            if(CurrentTedActorTransition.bool(r,"source_available")!=source.isPresent())throw new IOException("TED Source availability/null mismatch");
            return new CurrentTedActorTransitionResult(CurrentTedActorTransition.Action.parse(NativeWire.text(r.get("action"))),NativeWire.text(r.get("request_id")),operationText(r.get("operation_id")),
                    Status.parse(NativeWire.text(r.get("status"))),CurrentTedActorTransition.bool(r,"ok"),CurrentTedActorTransition.bool(r,"accepted"),
                    CurrentTedActorTransition.decimal(r,"provider_generation"),CurrentTedActorTransition.decimal(r,"query_sequence"),CurrentTedActorTransition.decimal(r,"claim_sequence"),
                    CurrentTedActorTransition.decimal(r,"actor_epoch"),CurrentTedActorTransition.deadline(r,"deadline_unix_ms"),CurrentTedActorTransition.decimal(r,"connection_generation"),
                    CurrentTedActorTransition.decimal(r,"ticket_sequence"),CurrentTedActorTransition.decimal(r,"pump_epoch"),CurrentTedActorTransition.u32(r.get("thread_id")),facts,source,
                    r.get("progress").isNull()?Optional.empty():Optional.of(Progress.decode(r.get("progress"))),CurrentTedActorTransition.bool(r,"effect_attempted"),
                    CurrentTedActorTransition.bool(r,"native_returned"),CurrentTedActorTransition.bool(r,"cleanup_known"),
                    reasonText(r.get("unavailable_reason")));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact TED transition DATA",invalid);}
    }
    public static CurrentTedActorTransitionResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var envelope=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));
            require(envelope,"type","command_result");require(envelope,"request_id",original.requestId());NativeWire.integer(envelope.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(CurrentTedActorTransition.bool(envelope,"ok")!=original.nativeOk())throw new IOException("TED envelope ok differs from original ACK");
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original TED result token absent"));
            if(!NativeWire.parse(token.bytes()).equals(envelope.get("result")))throw new IOException("TED result token differs from original envelope");
            var result=decode(new RawJson(token.bytes()));
            if(!result.requestId().equals(original.requestId())||result.ok()!=original.nativeOk())throw new IOException("TED result original ID/ok mismatch");
            return result;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid original TED acknowledgement",invalid);}
    }
    public RawJson encode(){
        var r=StrictJson.object().put("schema",CurrentTedActorTransition.RESULT_SCHEMA).put("backend",CurrentTedActorTransition.BACKEND).put("action",action.wire())
                .put("request_id",requestId).put("operation_id",operationId).put("status",status.wire()).put("ok",ok).put("accepted",accepted)
                .put("source_available",source.isPresent()).put("provider_generation",providerGeneration.toString()).put("query_sequence",querySequence.toString())
                .put("claim_sequence",claimSequence.toString()).put("actor_epoch",actorEpoch.toString()).put("deadline_unix_ms",deadlineUnixMs)
                .put("connection_generation",connectionGeneration.toString()).put("ticket_sequence",ticketSequence.toString()).put("pump_epoch",pumpEpoch.toString()).put("thread_id",threadId)
                .put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("cleanup_known",cleanupKnown).putNull("core_after");
        if(factsBefore.isPresent())r.set("facts_before",CurrentTedActorTransition.core(factsBefore.orElseThrow()));else r.putNull("facts_before");
        if(source.isPresent())r.set("source",source.orElseThrow().encode());else r.putNull("source");
        if(progress.isPresent())r.set("progress",progress.orElseThrow().encode());else r.putNull("progress");
        if(unavailableReason.isPresent())r.put("unavailable_reason",unavailableReason.orElseThrow());else r.putNull("unavailable_reason");
        return new RawJson(StrictJson.canonical(r));
    }
    private static void require(ObjectNode r,String key,String expected)throws IOException{
        if(!NativeWire.text(r.get(key)).equals(expected))throw new IOException("Exact TED identity mismatch: "+key);
    }
}
