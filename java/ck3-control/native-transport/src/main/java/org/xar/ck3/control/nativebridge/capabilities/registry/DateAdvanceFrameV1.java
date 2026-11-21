package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;

/** Current one-day boundary DATA. A terminal boundary never manufactures a fresh Core or physical SAVE. */
public record DateAdvanceFrameV1(Step step,Status status,String operationId,boolean accepted,boolean claimFound,
        boolean ownerBeforeVerified,boolean armAttempted,boolean resumeAttempted,boolean resumeSubmitted,
        boolean exactDayConfirmed,boolean shutdownSafe,boolean armed,boolean accessCleanupUnknown,long failureFlags,
        Optional<BigInteger> claimSequence,Optional<BigInteger> generation,Optional<CoreFrame.Prefix> coreBefore,
        Optional<GuiRootIndexFrame.OwnerWitness> ownerWitness,Optional<Sentinel> sentinel) {
    public static final String REQUEST_SCHEMA="ck3.current_date_advance_request.v1",SCHEMA="ck3.current_date_advance.v1",
            CAPABILITY="game.command.current-date-one-day.v1";
    public static final int MAXIMUM_BYTES=16384;
    private static final Set<String> FIELDS=Set.of("schema","game_version","executable_sha256","adapter_id","backend","step","status","operation_id",
            "accepted","claim_found","owner_before_verified","arm_attempted","resume_attempted","resume_submitted","exact_day_confirmed","shutdown_safe","armed","access_cleanup_unknown",
            "complete_snapshot","physical_save_confirmed","failure_flags","claim_sequence","generation","core_before","core_after","owner_witness","sentinel");
    public enum Step {
        ADVANCE("advance-date-one-day-v1"),QUERY("query-date-one-day-v1");
        private final String wire;Step(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Step wire(String value){for(var item:values())if(item.wire.equals(value))return item;throw new IllegalArgumentException("two exact current date steps required");}
    }
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_CORE_PREFIX("stale_core_prefix"),SOURCE_CHANGED("source_changed"),CLAIM_CONSUMED("claim_consumed"),
        CAPACITY_EXHAUSTED("capacity_exhausted"),SUBMITTED("submitted"),RUNNING("running"),COMPLETED("completed"),REJECTED("rejected"),INDETERMINATE("indeterminate");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Status wire(String value){for(var item:values())if(item.wire.equals(value))return item;throw new IllegalArgumentException("current date status required");}
    }
    public enum State {
        UNAVAILABLE("unavailable"),IDLE("idle"),ARMED("armed"),TRIGGERED("triggered"),FAILED("failed");
        private final String wire;State(String wire){this.wire=wire;}public String wire(){return wire;}
        public static State wire(String value){for(var item:values())if(item.wire.equals(value))return item;throw new IllegalArgumentException("current date sentinel state required");}
    }
    public enum Mode {
        TERMINAL_OR_SENTINEL("terminal_or_sentinel"),UNAVAILABLE("unavailable");
        private final String wire;Mode(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Mode wire(String value){for(var item:values())if(item.wire.equals(value))return item;throw new IllegalArgumentException("current date sentinel mode required");}
    }
    public record Sentinel(State state,Optional<BigInteger> generation,Mode mode,long armyCount,long combatCount,
            int startingDateRaw,int targetDateRaw,int lastObservedDateRaw,int triggerDateRaw,int speed,
            long completedDailyTicks,long triggerFlags,int signedDateDeltaFromTargetRaw,int overshootDays,
            boolean pauseWrapperCalled,boolean pauseObserved,boolean combatTerminalObserved,boolean abnormal) {
        public Sentinel{Objects.requireNonNull(state);Objects.requireNonNull(generation);Objects.requireNonNull(mode);generation.ifPresent(GuiControlsFrameV2::positive64);uint32(armyCount);uint32(combatCount);uint32(completedDailyTicks);uint32(triggerFlags);}
    }
    public DateAdvanceFrameV1 {
        Objects.requireNonNull(step);Objects.requireNonNull(status);safeId(operationId);uint32(failureFlags);
        Objects.requireNonNull(claimSequence);Objects.requireNonNull(generation);Objects.requireNonNull(coreBefore);Objects.requireNonNull(ownerWitness);Objects.requireNonNull(sentinel);
        claimSequence.ifPresent(GuiControlsFrameV2::positive64);generation.ifPresent(GuiControlsFrameV2::positive64);
        RegistryJson.require(coreBefore.isPresent()==ownerBeforeVerified&&ownerWitness.isPresent()==ownerBeforeVerified,"atomic original before-Core and owner witness required");
        coreBefore.ifPresent(DateAdvanceFrameV1::requireExpectedCore);
        RegistryJson.require(sentinel.isPresent()==(claimFound&&generation.isPresent()),"original claim/generation controls sentinel presence");
        RegistryJson.require(!resumeSubmitted||resumeAttempted,"submitted resume requires its original attempt");
        boolean source=claimFound&&claimSequence.isPresent()&&generation.isPresent()&&ownerBeforeVerified&&armAttempted&&resumeAttempted&&resumeSubmitted;
        boolean submitted=source&&sentinel.filter(s->s.generation().equals(generation)&&s.state()==State.ARMED&&s.mode()==Mode.TERMINAL_OR_SENTINEL&&s.armyCount()==0&&s.combatCount()==0&&s.startingDateRaw()==coreBefore.orElseThrow().dateRaw()&&s.targetDateRaw()==coreBefore.orElseThrow().dateRaw()+24&&s.speed()==coreBefore.orElseThrow().speed()).isPresent();
        RegistryJson.require(accepted==(step==Step.ADVANCE&&status==Status.SUBMITTED&&submitted),"coherent original action acceptance only; query cannot authorize another action");
        if(status==Status.SUBMITTED&&step==Step.ADVANCE)RegistryJson.require(accepted,"incoherent action submitted cannot be promoted");
        if(status==Status.COMPLETED||exactDayConfirmed){
            RegistryJson.require(status==Status.COMPLETED&&exactDayConfirmed&&source&&shutdownSafe&&!armed&&!accessCleanupUnknown&&failureFlags==0,"exact date terminal needs original safe disarmed cleanup and zero failure");
            var s=sentinel.orElseThrow();var before=coreBefore.orElseThrow();int target=before.dateRaw()+24;
            RegistryJson.require(s.generation().equals(generation)&&s.state()==State.TRIGGERED&&s.mode()==Mode.TERMINAL_OR_SENTINEL&&s.armyCount()==0&&s.combatCount()==0
                    &&s.startingDateRaw()==before.dateRaw()&&s.targetDateRaw()==target&&s.lastObservedDateRaw()==target&&s.triggerDateRaw()==target&&s.speed()==before.speed()
                    &&s.completedDailyTicks()==1&&s.triggerFlags()==1&&s.signedDateDeltaFromTargetRaw()==0&&s.overshootDays()==0
                    &&s.pauseWrapperCalled()&&s.pauseObserved()&&!s.combatTerminalObserved()&&!s.abnormal(),"only actual original-generation exact+24 postday pause boundary can complete");
        }
    }
    public boolean nativeOk(){return step==Step.QUERY?claimFound:accepted;}
    static String safeId(String value){RegistryJson.require(value!=null&&value.matches("[A-Za-z0-9_.-]{1,96}"),"safe1..96 ASCII operation/request identity required");return value;}
    static void requireExpectedCore(CoreFrame.Prefix p){Objects.requireNonNull(p);RegistryJson.require(p.dateRaw()>0&&p.dateRaw()<=Integer.MAX_VALUE-24&&p.speed()>=1&&p.speed()<=5&&p.paused()&&p.localPlayerId()>=0&&p.mapReady()&&p.hasPlayedCharacter()&&p.playedCharacterId()!=-1&&p.playedCharacterAlive(),"current paused living map Core and bounded one-day date required");}
    private static long uint32(long value){RegistryJson.require(value>=0&&value<=0xffff_ffffL,"uint32 range required");return value;}
    private static BigInteger positive64(com.fasterxml.jackson.databind.JsonNode value){String token=RegistryJson.text(value);RegistryJson.require(token.matches("[1-9][0-9]{0,19}"),"canonical positive uint64 string required");var result=new BigInteger(token);GuiControlsFrameV2.positive64(result);return result;}
    private static Optional<BigInteger> optional64(com.fasterxml.jackson.databind.JsonNode value){return value.isNull()?Optional.empty():Optional.of(positive64(value));}
    private static long u32(com.fasterxml.jackson.databind.JsonNode value){return RegistryJson.integer(value,BigInteger.ZERO,BigInteger.valueOf(0xffff_ffffL)).longValueExact();}
    static CoreFrame.Prefix prefix(com.fasterxml.jackson.databind.JsonNode value){var p=RegistryJson.object(value);RegistryJson.keys(p,Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));return new CoreFrame.Prefix(RegistryJson.int32(p.get("date_raw")),RegistryJson.int32(p.get("speed")),RegistryJson.bool(p.get("paused")),RegistryJson.int32(p.get("local_player_id")),RegistryJson.bool(p.get("map_ready")),RegistryJson.bool(p.get("has_played_character")),RegistryJson.int32(p.get("played_character_id")),RegistryJson.bool(p.get("played_character_alive")));}
    public static DateAdvanceFrameV1 decode(RawJson raw){
        RegistryJson.require(raw.bytes().length<=MAXIMUM_BYTES,"bounded current date result required");var row=RegistryJson.object(raw);RegistryJson.keys(row,FIELDS);var build=GuiControlsFrameV2.BUILD;
        RegistryJson.require(SCHEMA.equals(RegistryJson.text(row.get("schema")))&&build.matches(RegistryJson.text(row.get("game_version")),RegistryJson.text(row.get("executable_sha256")))&&build.coreFrameAdapterId().equals(RegistryJson.text(row.get("adapter_id")))&&GuiControlsFrameV2.BACKEND.equals(RegistryJson.text(row.get("backend"))),"exact current date tuple required");
        RegistryJson.require(!RegistryJson.bool(row.get("complete_snapshot"))&&!RegistryJson.bool(row.get("physical_save_confirmed"))&&row.get("core_after").isNull(),"boundary DATA cannot manufacture a new Core or Full/physical SAVE");
        Optional<GuiRootIndexFrame.OwnerWitness> owner=Optional.empty();
        if(!row.get("owner_witness").isNull()){var w=RegistryJson.object(row.get("owner_witness"));RegistryJson.keys(w,Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));owner=Optional.of(new GuiRootIndexFrame.OwnerWitness(positive64(w.get("connection_generation")),positive64(w.get("ticket_sequence")),positive64(w.get("pump_epoch")),RegistryJson.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
        Optional<Sentinel> sentinel=Optional.empty();if(!row.get("sentinel").isNull()){
            var s=RegistryJson.object(row.get("sentinel"));RegistryJson.keys(s,Set.of("state","generation","mode","army_count","combat_count","starting_date_raw","target_date_raw","last_observed_date_raw","trigger_date_raw","speed","completed_daily_ticks","trigger_flags","signed_date_delta_from_target_raw","overshoot_days","pause_wrapper_called","pause_observed","combat_terminal_observed","abnormal"));
            sentinel=Optional.of(new Sentinel(State.wire(RegistryJson.text(s.get("state"))),optional64(s.get("generation")),Mode.wire(RegistryJson.text(s.get("mode"))),u32(s.get("army_count")),u32(s.get("combat_count")),RegistryJson.int32(s.get("starting_date_raw")),RegistryJson.int32(s.get("target_date_raw")),RegistryJson.int32(s.get("last_observed_date_raw")),RegistryJson.int32(s.get("trigger_date_raw")),RegistryJson.int32(s.get("speed")),u32(s.get("completed_daily_ticks")),u32(s.get("trigger_flags")),RegistryJson.int32(s.get("signed_date_delta_from_target_raw")),RegistryJson.int32(s.get("overshoot_days")),RegistryJson.bool(s.get("pause_wrapper_called")),RegistryJson.bool(s.get("pause_observed")),RegistryJson.bool(s.get("combat_terminal_observed")),RegistryJson.bool(s.get("abnormal"))));
        }
        return new DateAdvanceFrameV1(Step.wire(RegistryJson.text(row.get("step"))),Status.wire(RegistryJson.text(row.get("status"))),RegistryJson.text(row.get("operation_id")),RegistryJson.bool(row.get("accepted")),RegistryJson.bool(row.get("claim_found")),RegistryJson.bool(row.get("owner_before_verified")),RegistryJson.bool(row.get("arm_attempted")),RegistryJson.bool(row.get("resume_attempted")),RegistryJson.bool(row.get("resume_submitted")),RegistryJson.bool(row.get("exact_day_confirmed")),RegistryJson.bool(row.get("shutdown_safe")),RegistryJson.bool(row.get("armed")),RegistryJson.bool(row.get("access_cleanup_unknown")),u32(row.get("failure_flags")),optional64(row.get("claim_sequence")),optional64(row.get("generation")),row.get("core_before").isNull()?Optional.empty():Optional.of(prefix(row.get("core_before"))),owner,sentinel);
    }
}
