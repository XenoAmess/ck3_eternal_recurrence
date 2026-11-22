package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact twelve-field Source DATA. An after-recipient Source never substitutes for retained before-Song proof. */
public record CurrentTedActorTransitionSource(Role role,boolean definitionFound,Optional<Boolean> nativeShown,
        BigInteger actorEpoch,Optional<Integer> songActorId,Optional<Integer> recipientActorId,Optional<Pending> pending,
        boolean runtimeReady,boolean predecessorResolved,boolean advanceAdmissible,boolean confirmAdmissible) {
    public enum Role {
        SONG("song"),RECIPIENT("recipient");
        private final String wire;Role(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Role parse(String value)throws IOException{
            for(var role:values())if(role.wire.equals(value))return role;throw new IOException("Unknown actual TED actor role");
        }
    }
    public record Pending(String operationId,BigInteger claimSequence,BigInteger generation,long originalDeadlineUnixMs,
            int beforeActorId,int afterActorId,int startingDateRaw,int targetDateRaw,long completedDailyTicks,
            boolean exactDayConfirmed,boolean shutdownSafe,boolean cleanupKnown) {
        public Pending {
            CurrentTedActorTransition.identifier(operationId);CurrentTedActorTransition.unsigned(claimSequence,true);
            CurrentTedActorTransition.unsigned(generation,true);
            StrictJson.require(originalDeadlineUnixMs>0&&beforeActorId!=-1&&afterActorId!=-1&&beforeActorId!=afterActorId,
                    "Pending retains original deadline and two different actual signed32 actor IDs");
            StrictJson.require((long)startingDateRaw+24==targetDateRaw&&completedDailyTicks==1&&exactDayConfirmed&&shutdownSafe&&cleanupKnown,
                    "Pending requires exact24 raw ticks, one actual daily tick and safe cleanup");
        }
        static Pending decode(JsonNode node)throws IOException {
            var p=StrictJson.object(node,Set.of("operation_id","claim_sequence","generation","original_deadline_unix_ms","before_actor_id","after_actor_id","starting_date_raw","target_date_raw","completed_daily_ticks","exact_day_confirmed","shutdown_safe","cleanup_known"));
            return new Pending(NativeWire.text(p.get("operation_id")),CurrentTedActorTransition.decimal(p,"claim_sequence"),CurrentTedActorTransition.decimal(p,"generation"),
                    CurrentTedActorTransition.deadline(p,"original_deadline_unix_ms"),CurrentTedActorTransition.i32(p.get("before_actor_id")),CurrentTedActorTransition.i32(p.get("after_actor_id")),
                    CurrentTedActorTransition.i32(p.get("starting_date_raw")),CurrentTedActorTransition.i32(p.get("target_date_raw")),CurrentTedActorTransition.u32(p.get("completed_daily_ticks")),
                    CurrentTedActorTransition.bool(p,"exact_day_confirmed"),CurrentTedActorTransition.bool(p,"shutdown_safe"),CurrentTedActorTransition.bool(p,"cleanup_known"));
        }
        ObjectNode encode(){return StrictJson.object().put("operation_id",operationId).put("claim_sequence",claimSequence.toString()).put("generation",generation.toString())
                .put("original_deadline_unix_ms",originalDeadlineUnixMs).put("before_actor_id",beforeActorId).put("after_actor_id",afterActorId)
                .put("starting_date_raw",startingDateRaw).put("target_date_raw",targetDateRaw).put("completed_daily_ticks",completedDailyTicks)
                .put("exact_day_confirmed",exactDayConfirmed).put("shutdown_safe",shutdownSafe).put("cleanup_known",cleanupKnown);}
    }
    public CurrentTedActorTransitionSource {
        Objects.requireNonNull(role);Objects.requireNonNull(nativeShown);Objects.requireNonNull(songActorId);
        Objects.requireNonNull(recipientActorId);Objects.requireNonNull(pending);CurrentTedActorTransition.epoch(actorEpoch);
        StrictJson.require(definitionFound==nativeShown.isPresent(),"NativeShown is null exactly when actual fixed definition is missing");
        songActorId.ifPresent(id->StrictJson.require(id!=-1,"Actual Song ID cannot be the invalid sentinel"));
        recipientActorId.ifPresent(id->StrictJson.require(id!=-1,"Actual recipient ID cannot be the invalid sentinel"));
        if(recipientActorId.isPresent())StrictJson.require(songActorId.isPresent()&&!recipientActorId.equals(songActorId),"Recipient requires retained distinct Song identity");
        if(role==Role.SONG)StrictJson.require(actorEpoch.signum()==0&&pending.isEmpty(),"Song role belongs only to initial frontier");
        if(actorEpoch.signum()>0)StrictJson.require(role==Role.RECIPIENT&&songActorId.isPresent()&&recipientActorId.isPresent()&&pending.isEmpty(),"Confirmed epoch retains both actors and no pending");
        if(pending.isPresent()) {
            var p=pending.orElseThrow();
            StrictJson.require(actorEpoch.signum()==0&&role==Role.RECIPIENT&&songActorId.filter(id->id==p.beforeActorId()).isPresent(),"Pending binds retained before-Song frontier0");
            recipientActorId.ifPresent(id->StrictJson.require(id==p.afterActorId(),"Recipient differs from actual pending after sample"));
        }
        StrictJson.require(!advanceAdmissible||!confirmAdmissible,"Advance and epoch confirmation are mutually exclusive");
        if(advanceAdmissible)StrictJson.require(definitionFound&&nativeShown.orElse(false)&&runtimeReady&&predecessorResolved&&pending.isEmpty()
                &&actorEpoch.compareTo(BigInteger.ONE)<=0&&(actorEpoch.signum()==0?role==Role.SONG&&songActorId.isPresent():role==Role.RECIPIENT&&recipientActorId.isPresent()),
                "Advance permission requires actual fixed role, custody and permitted frontier; no reverse implication");
        if(confirmAdmissible)StrictJson.require(definitionFound&&nativeShown.orElse(false)&&runtimeReady&&predecessorResolved&&actorEpoch.signum()==0
                &&role==Role.RECIPIENT&&pending.isPresent()&&recipientActorId.isPresent(),"Confirmation requires actual independent recipient witness and retained pending; no reverse implication");
        if(actorEpoch.equals(BigInteger.TWO))StrictJson.require(!advanceAdmissible&&!confirmAdmissible,"Epoch2 is data-only");
    }
    static CurrentTedActorTransitionSource decode(JsonNode node)throws IOException {
        var r=StrictJson.object(node,Set.of("schema","role","definition_found","native_shown","actor_epoch","song_actor_id","recipient_actor_id","pending","runtime_ready","predecessor_resolved","advance_admissible","confirm_admissible"));
        if(!NativeWire.text(r.get("schema")).equals(CurrentTedActorTransition.SOURCE_SCHEMA))throw new IOException("Exact TED Source schema required");
        Optional<Boolean> shown=Optional.empty();if(!r.get("native_shown").isNull())shown=Optional.of(CurrentTedActorTransition.bool(r,"native_shown"));
        return new CurrentTedActorTransitionSource(Role.parse(NativeWire.text(r.get("role"))),CurrentTedActorTransition.bool(r,"definition_found"),shown,
                CurrentTedActorTransition.decimal(r,"actor_epoch"),actor(r.get("song_actor_id")),actor(r.get("recipient_actor_id")),
                r.get("pending").isNull()?Optional.empty():Optional.of(Pending.decode(r.get("pending"))),CurrentTedActorTransition.bool(r,"runtime_ready"),
                CurrentTedActorTransition.bool(r,"predecessor_resolved"),CurrentTedActorTransition.bool(r,"advance_admissible"),CurrentTedActorTransition.bool(r,"confirm_admissible"));
    }
    ObjectNode encode(){
        var r=StrictJson.object().put("schema",CurrentTedActorTransition.SOURCE_SCHEMA).put("role",role.wire()).put("definition_found",definitionFound)
                .put("actor_epoch",actorEpoch.toString()).put("runtime_ready",runtimeReady).put("predecessor_resolved",predecessorResolved)
                .put("advance_admissible",advanceAdmissible).put("confirm_admissible",confirmAdmissible);
        if(nativeShown.isPresent())r.put("native_shown",nativeShown.orElseThrow().booleanValue());else r.putNull("native_shown");
        putActor(r,"song_actor_id",songActorId);putActor(r,"recipient_actor_id",recipientActorId);
        if(pending.isPresent())r.set("pending",pending.orElseThrow().encode());else r.putNull("pending");return r;
    }
    private static Optional<Integer> actor(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentTedActorTransition.i32(n));}
    private static void putActor(ObjectNode r,String key,Optional<Integer> value){if(value.isPresent())r.put(key,value.orElseThrow().intValue());else r.putNull(key);}
}
