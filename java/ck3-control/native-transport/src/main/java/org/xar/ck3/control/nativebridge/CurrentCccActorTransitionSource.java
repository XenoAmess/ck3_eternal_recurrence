package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** CCC fixed-role DATA; neither a caller-created Source nor a shown witness grants private actor custody. */
public record CurrentCccActorTransitionSource(Role role, boolean definitionFound, Optional<Boolean> nativeShown,
        BigInteger actorEpoch, Optional<Integer> songActorId, Optional<Integer> officialActorId, Optional<Pending> pending,
        int completedNaturalDays, int maximumNaturalDays, int caseStartDateRaw,
        boolean runtimeReady, boolean predecessorResolved, boolean advanceAdmissible, boolean confirmAdmissible) {
    public enum Role {
        SONG("song"), OFFICIAL("official");
        private final String wire; Role(String wire) { this.wire=wire; }
        public String wire() { return wire; }
        public static Role parse(String value) throws IOException {
            for (var r:values()) if (r.wire.equals(value)) return r;
            throw new IOException("Unknown CCC fixed role");
        }
    }
    public record Pending(String operationId, BigInteger claimSequence, BigInteger generation, BigInteger originalDeadlineUnixMs,
            int beforeActorId, int afterActorId, int startingDateRaw, int targetDateRaw, long completedDailyTicks,
            boolean exactDayConfirmed, boolean shutdownSafe, boolean cleanupKnown) {
        public Pending {
            CurrentCccActorTransition.identifier(operationId); CurrentCccActorTransition.unsigned(claimSequence,true);
            CurrentCccActorTransition.unsigned(generation,true); CurrentCccActorTransition.unsigned(originalDeadlineUnixMs,true);
            StrictJson.require(beforeActorId!=-1&&afterActorId!=-1&&beforeActorId!=afterActorId
                    &&(long)startingDateRaw+24==targetDateRaw&&completedDailyTicks==1&&exactDayConfirmed&&shutdownSafe&&cleanupKnown,
                    "Pending requires original distinct actors, exact one day and safe cleanup");
        }
        static Pending decode(JsonNode node) throws IOException {
            var r=StrictJson.object(node,Set.of("operation_id","claim_sequence","generation","original_deadline_unix_ms","before_actor_id","after_actor_id","starting_date_raw","target_date_raw","completed_daily_ticks","exact_day_confirmed","shutdown_safe","cleanup_known"));
            return new Pending(NativeWire.text(r.get("operation_id")),CurrentCccActorTransition.decimal(r,"claim_sequence"),CurrentCccActorTransition.decimal(r,"generation"),CurrentCccActorTransition.deadline(r,"original_deadline_unix_ms"),
                    CurrentCccActorTransition.i32(r.get("before_actor_id")),CurrentCccActorTransition.i32(r.get("after_actor_id")),CurrentCccActorTransition.i32(r.get("starting_date_raw")),CurrentCccActorTransition.i32(r.get("target_date_raw")),
                    CurrentCccActorTransition.u32(r.get("completed_daily_ticks")),CurrentCccActorTransition.bool(r,"exact_day_confirmed"),CurrentCccActorTransition.bool(r,"shutdown_safe"),CurrentCccActorTransition.bool(r,"cleanup_known"));
        }
        public ObjectNode encode() {
            return StrictJson.object().put("operation_id",operationId).put("claim_sequence",claimSequence.toString()).put("generation",generation.toString()).put("original_deadline_unix_ms",originalDeadlineUnixMs)
                    .put("before_actor_id",beforeActorId).put("after_actor_id",afterActorId).put("starting_date_raw",startingDateRaw).put("target_date_raw",targetDateRaw).put("completed_daily_ticks",completedDailyTicks)
                    .put("exact_day_confirmed",exactDayConfirmed).put("shutdown_safe",shutdownSafe).put("cleanup_known",cleanupKnown);
        }
    }
    public CurrentCccActorTransitionSource {
        Objects.requireNonNull(role); Objects.requireNonNull(nativeShown); Objects.requireNonNull(songActorId); Objects.requireNonNull(officialActorId); Objects.requireNonNull(pending);
        CurrentCccActorTransition.epoch(actorEpoch); CurrentCccActorTransition.requireDays(completedNaturalDays);
        StrictJson.require(maximumNaturalDays==13&&caseStartDateRaw>=0&&definitionFound==nativeShown.isPresent(),"Exact CCC original13-day counter/witness shape");
        songActorId.ifPresent(n->StrictJson.require(n!=-1,"Actual Song actor except invalid sentinel"));
        officialActorId.ifPresent(n->StrictJson.require(n!=-1,"Actual official actor except invalid sentinel"));
        if (pending.isPresent()) {
            var p=pending.orElseThrow();
            StrictJson.require(actorEpoch.signum()==0&&role==Role.OFFICIAL&&songActorId.filter(n->n==p.beforeActorId()).isPresent(),"Pending retains actual before-Song proof at frontier0");
            officialActorId.ifPresent(n->StrictJson.require(n==p.afterActorId(),"Independent official differs from pending actor"));
        }
        if (actorEpoch.signum()>0) StrictJson.require(songActorId.isPresent()&&officialActorId.isPresent()&&!songActorId.equals(officialActorId)&&role==Role.OFFICIAL&&pending.isEmpty(),"Confirmed frontier retains distinct actors and no pending");
        if (advanceAdmissible) StrictJson.require(caseStartDateRaw>0&&completedNaturalDays<13&&definitionFound&&nativeShown.orElse(false)&&runtimeReady&&predecessorResolved&&pending.isEmpty()&&!confirmAdmissible
                &&(actorEpoch.signum()!=0||role==Role.SONG&&songActorId.isPresent()&&officialActorId.isEmpty()),"Advance admissibility requires original native prerequisites; never infer the reverse");
        if (confirmAdmissible) StrictJson.require(caseStartDateRaw>0&&completedNaturalDays==1&&definitionFound&&nativeShown.orElse(false)&&runtimeReady&&predecessorResolved&&pending.isPresent()
                &&actorEpoch.signum()==0&&role==Role.OFFICIAL&&songActorId.isPresent()&&officialActorId.isPresent()&&!advanceAdmissible,"Confirm requires independent official and exact pending proof");
    }
    public static CurrentCccActorTransitionSource decode(JsonNode node) throws IOException {
        try {
            var r=StrictJson.object(node,Set.of("schema","role","definition_found","native_shown","actor_epoch","song_actor_id","official_actor_id","pending","completed_natural_days","maximum_natural_days","case_start_date_raw","runtime_ready","predecessor_resolved","advance_admissible","confirm_admissible"));
            CurrentCccActorTransition.identity(r,"schema",CurrentCccActorTransition.SOURCE_SCHEMA);
            return new CurrentCccActorTransitionSource(Role.parse(NativeWire.text(r.get("role"))),CurrentCccActorTransition.bool(r,"definition_found"),r.get("native_shown").isNull()?Optional.empty():Optional.of(CurrentCccActorTransition.bool(r,"native_shown")),
                    CurrentCccActorTransition.decimal(r,"actor_epoch"),actor(r.get("song_actor_id")),actor(r.get("official_actor_id")),r.get("pending").isNull()?Optional.empty():Optional.of(Pending.decode(r.get("pending"))),
                    CurrentCccActorTransition.days(r.get("completed_natural_days")),CurrentCccActorTransition.i32(r.get("maximum_natural_days")),CurrentCccActorTransition.i32(r.get("case_start_date_raw")),
                    CurrentCccActorTransition.bool(r,"runtime_ready"),CurrentCccActorTransition.bool(r,"predecessor_resolved"),CurrentCccActorTransition.bool(r,"advance_admissible"),CurrentCccActorTransition.bool(r,"confirm_admissible"));
        } catch (IllegalArgumentException|ArithmeticException invalid) { throw new IOException("Invalid CCC fixed-role Source DATA",invalid); }
    }
    public ObjectNode encode() {
        var r=StrictJson.object().put("schema",CurrentCccActorTransition.SOURCE_SCHEMA).put("role",role.wire()).put("definition_found",definitionFound).put("actor_epoch",actorEpoch.toString())
                .put("completed_natural_days",completedNaturalDays).put("maximum_natural_days",maximumNaturalDays).put("case_start_date_raw",caseStartDateRaw).put("runtime_ready",runtimeReady)
                .put("predecessor_resolved",predecessorResolved).put("advance_admissible",advanceAdmissible).put("confirm_admissible",confirmAdmissible);
        if(nativeShown.isPresent())r.put("native_shown",nativeShown.orElseThrow());else r.putNull("native_shown");
        putActor(r,"song_actor_id",songActorId);putActor(r,"official_actor_id",officialActorId);
        if(pending.isPresent())r.set("pending",pending.orElseThrow().encode());else r.putNull("pending");return r;
    }
    private static Optional<Integer> actor(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentCccActorTransition.i32(n));}
    private static void putActor(ObjectNode r,String key,Optional<Integer> n){if(n.isPresent())r.put(key,n.orElseThrow());else r.putNull(key);}
}
