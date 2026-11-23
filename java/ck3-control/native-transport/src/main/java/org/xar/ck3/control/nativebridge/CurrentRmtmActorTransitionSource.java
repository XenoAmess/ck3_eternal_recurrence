package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** RMTM fixed-role DATA; neither a caller-created Source nor a shown witness grants private actor custody. */
public record CurrentRmtmActorTransitionSource(Role role, boolean definitionFound, Optional<Boolean> nativeShown,
        BigInteger actorEpoch, Optional<Integer> songActorId, Optional<Integer> successorActorId, Optional<Pending> pending,
        int completedNaturalDays, int maximumNaturalDays, int caseStartDateRaw,
        boolean caseStartCaptured, Optional<Boolean> executeTimeIdentityConfirmed,
        boolean runtimeReady, boolean predecessorResolved, boolean advanceAdmissible, boolean confirmAdmissible) {
    public enum Role {
        SONG("song"), SUCCESSOR("successor");
        private final String wire; Role(String wire) { this.wire=wire; }
        public String wire() { return wire; }
        public static Role parse(String value) throws IOException {
            for (var r:values()) if (r.wire.equals(value)) return r;
            throw new IOException("Unknown RMTM fixed role");
        }
    }
    public record Pending(String operationId, BigInteger claimSequence, BigInteger generation, BigInteger originalDeadlineUnixMs,
            int beforeActorId, int afterActorId, int startingDateRaw, int targetDateRaw, long completedDailyTicks,
            boolean exactDayConfirmed, boolean shutdownSafe, boolean cleanupKnown) {
        public Pending {
            CurrentRmtmActorTransition.identifier(operationId); CurrentRmtmActorTransition.unsigned(claimSequence,true);
            CurrentRmtmActorTransition.unsigned(generation,true); CurrentRmtmActorTransition.unsigned(originalDeadlineUnixMs,true);
            StrictJson.require(beforeActorId!=-1&&afterActorId!=-1&&beforeActorId!=afterActorId
                    &&(long)startingDateRaw+24==targetDateRaw&&completedDailyTicks==1&&exactDayConfirmed&&shutdownSafe&&cleanupKnown,
                    "Pending requires original distinct actors, exact one day and safe cleanup");
        }
        static Pending decode(JsonNode node) throws IOException {
            var r=StrictJson.object(node,Set.of("operation_id","claim_sequence","generation","original_deadline_unix_ms","before_actor_id","after_actor_id","starting_date_raw","target_date_raw","completed_daily_ticks","exact_day_confirmed","shutdown_safe","cleanup_known"));
            return new Pending(NativeWire.text(r.get("operation_id")),CurrentRmtmActorTransition.decimal(r,"claim_sequence"),CurrentRmtmActorTransition.decimal(r,"generation"),CurrentRmtmActorTransition.deadline(r,"original_deadline_unix_ms"),
                    CurrentRmtmActorTransition.i32(r.get("before_actor_id")),CurrentRmtmActorTransition.i32(r.get("after_actor_id")),CurrentRmtmActorTransition.i32(r.get("starting_date_raw")),CurrentRmtmActorTransition.i32(r.get("target_date_raw")),
                    CurrentRmtmActorTransition.u32(r.get("completed_daily_ticks")),CurrentRmtmActorTransition.bool(r,"exact_day_confirmed"),CurrentRmtmActorTransition.bool(r,"shutdown_safe"),CurrentRmtmActorTransition.bool(r,"cleanup_known"));
        }
        public ObjectNode encode() {
            return StrictJson.object().put("operation_id",operationId).put("claim_sequence",claimSequence.toString()).put("generation",generation.toString()).put("original_deadline_unix_ms",originalDeadlineUnixMs)
                    .put("before_actor_id",beforeActorId).put("after_actor_id",afterActorId).put("starting_date_raw",startingDateRaw).put("target_date_raw",targetDateRaw).put("completed_daily_ticks",completedDailyTicks)
                    .put("exact_day_confirmed",exactDayConfirmed).put("shutdown_safe",shutdownSafe).put("cleanup_known",cleanupKnown);
        }
    }
    public CurrentRmtmActorTransitionSource {
        Objects.requireNonNull(role); Objects.requireNonNull(nativeShown); Objects.requireNonNull(songActorId); Objects.requireNonNull(successorActorId); Objects.requireNonNull(pending); Objects.requireNonNull(executeTimeIdentityConfirmed);
        CurrentRmtmActorTransition.epoch(actorEpoch); CurrentRmtmActorTransition.requireDays(completedNaturalDays);
        StrictJson.require(maximumNaturalDays==14&&definitionFound==nativeShown.isPresent(),"Exact RMTM original14-day counter/witness shape");
        songActorId.ifPresent(n->StrictJson.require(n!=-1,"Actual Song actor except invalid sentinel"));
        successorActorId.ifPresent(n->StrictJson.require(n!=-1,"Actual successor actor except invalid sentinel"));
        if (pending.isPresent()) {
            var p=pending.orElseThrow();
            StrictJson.require(actorEpoch.signum()==0&&role==Role.SUCCESSOR&&songActorId.filter(n->n==p.beforeActorId()).isPresent(),"Pending retains actual before-Song proof at frontier0");
            successorActorId.ifPresent(n->StrictJson.require(n==p.afterActorId(),"Independent successor differs from pending actor"));
        }
        if (actorEpoch.signum()>0) StrictJson.require(songActorId.isPresent()&&successorActorId.isPresent()&&!songActorId.equals(successorActorId)&&role==Role.SUCCESSOR&&pending.isEmpty(),"Confirmed frontier retains distinct actors and no pending");
        if (advanceAdmissible) StrictJson.require(caseStartCaptured&&completedNaturalDays<14&&definitionFound&&nativeShown.orElse(false)&&runtimeReady&&predecessorResolved&&pending.isEmpty()&&!confirmAdmissible
                &&(actorEpoch.signum()!=0||role==Role.SONG&&songActorId.isPresent()&&successorActorId.isEmpty()),"Advance admissibility requires original native prerequisites; never infer the reverse");
        if (confirmAdmissible) StrictJson.require(caseStartCaptured&&completedNaturalDays>0&&completedNaturalDays<=14&&definitionFound&&nativeShown.orElse(false)&&runtimeReady&&predecessorResolved&&pending.isPresent()
                &&actorEpoch.signum()==0&&role==Role.SUCCESSOR&&songActorId.isPresent()&&successorActorId.isPresent()&&!advanceAdmissible,"Confirm requires actual successor and exact pending proof; D5 execute identity remains independent nullable DATA");
    }
    public static CurrentRmtmActorTransitionSource decode(JsonNode node) throws IOException {
        try {
            var r=StrictJson.object(node,Set.of("schema","role","definition_found","native_shown","actor_epoch","song_actor_id","successor_actor_id","pending","completed_natural_days","maximum_natural_days","case_start_date_raw","case_start_captured","execute_time_identity_confirmed","runtime_ready","predecessor_resolved","advance_admissible","confirm_admissible"));
            CurrentRmtmActorTransition.identity(r,"schema",CurrentRmtmActorTransition.SOURCE_SCHEMA);
            return new CurrentRmtmActorTransitionSource(Role.parse(NativeWire.text(r.get("role"))),CurrentRmtmActorTransition.bool(r,"definition_found"),r.get("native_shown").isNull()?Optional.empty():Optional.of(CurrentRmtmActorTransition.bool(r,"native_shown")),
                    CurrentRmtmActorTransition.decimal(r,"actor_epoch"),actor(r.get("song_actor_id")),actor(r.get("successor_actor_id")),r.get("pending").isNull()?Optional.empty():Optional.of(Pending.decode(r.get("pending"))),
                    CurrentRmtmActorTransition.days(r.get("completed_natural_days")),CurrentRmtmActorTransition.i32(r.get("maximum_natural_days")),CurrentRmtmActorTransition.i32(r.get("case_start_date_raw")),
                    CurrentRmtmActorTransition.bool(r,"case_start_captured"),r.get("execute_time_identity_confirmed").isNull()?Optional.empty():Optional.of(CurrentRmtmActorTransition.bool(r,"execute_time_identity_confirmed")),
                    CurrentRmtmActorTransition.bool(r,"runtime_ready"),CurrentRmtmActorTransition.bool(r,"predecessor_resolved"),CurrentRmtmActorTransition.bool(r,"advance_admissible"),CurrentRmtmActorTransition.bool(r,"confirm_admissible"));
        } catch (IllegalArgumentException|ArithmeticException invalid) { throw new IOException("Invalid RMTM fixed-role Source DATA",invalid); }
    }
    public ObjectNode encode() {
        var r=StrictJson.object().put("schema",CurrentRmtmActorTransition.SOURCE_SCHEMA).put("role",role.wire()).put("definition_found",definitionFound).put("actor_epoch",actorEpoch.toString())
                .put("completed_natural_days",completedNaturalDays).put("maximum_natural_days",maximumNaturalDays).put("case_start_date_raw",caseStartDateRaw).put("case_start_captured",caseStartCaptured).put("runtime_ready",runtimeReady)
                .put("predecessor_resolved",predecessorResolved).put("advance_admissible",advanceAdmissible).put("confirm_admissible",confirmAdmissible);
        if(executeTimeIdentityConfirmed.isPresent())r.put("execute_time_identity_confirmed",executeTimeIdentityConfirmed.orElseThrow());else r.putNull("execute_time_identity_confirmed");
        if(nativeShown.isPresent())r.put("native_shown",nativeShown.orElseThrow());else r.putNull("native_shown");
        putActor(r,"song_actor_id",songActorId);putActor(r,"successor_actor_id",successorActorId);
        if(pending.isPresent())r.set("pending",pending.orElseThrow().encode());else r.putNull("pending");return r;
    }
    private static Optional<Integer> actor(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentRmtmActorTransition.i32(n));}
    private static void putActor(ObjectNode r,String key,Optional<Integer> n){if(n.isPresent())r.put(key,n.orElseThrow());else r.putNull(key);}
}
