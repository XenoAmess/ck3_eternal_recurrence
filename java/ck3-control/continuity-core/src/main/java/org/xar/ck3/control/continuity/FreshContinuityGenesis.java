package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** A configured empty store before Game entry. No planned value is a native observation or credit. */
public final class FreshContinuityGenesis {
    public static final String REQUEST_SCHEMA="xar.java-continuity-genesis-request/v1";
    public static final String STATE_SCHEMA="xar.java-continuity-pre-entry/v1";
    public static final String FIELD="java_fresh_continuity_genesis";
    public static final int MAXIMUM_REQUEST_BYTES=4096;
    private FreshContinuityGenesis() { }

    /** The original stability-window policy is explicit and independent of campaign calendar goals. */
    public record Plan(String machineId,long plannedWindowId,long targetDays) {
        public Plan {
            StrictJson.require(machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,127}")&&!machineId.equals("unknown"),
                    "actual configured machine identity required");
            StrictJson.safe(plannedWindowId,1);StrictJson.safe(targetDays,1);
            Math.multiplyExact(targetDays,24);
        }
    }
    public static byte[] encode(Plan plan) {
        var row=StrictJson.object();row.put("schema",REQUEST_SCHEMA);row.put("machine_id",plan.machineId());
        row.put("planned_window_id",plan.plannedWindowId());row.put("target_days",plan.targetDays());
        return StrictJson.canonical(row,MAXIMUM_REQUEST_BYTES);
    }
    public static Plan decode(byte[] bytes) {
        var row=StrictJson.object(StrictJson.parse(bytes,MAXIMUM_REQUEST_BYTES),
                Set.of("schema","machine_id","planned_window_id","target_days"));
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact genesis request version required");
        return new Plan(StrictJson.text(row.get("machine_id")),
                StrictJson.integer(row.get("planned_window_id"),1,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(row.get("target_days"),1,StrictJson.MAX_SAFE_INTEGER));
    }
    /** Original request is observed and compared by the sole physical initializer before this pure projection. */
    public static ContinuityState initial(Plan plan,ExactRef actualPlanOriginal) {
        java.util.Objects.requireNonNull(plan);java.util.Objects.requireNonNull(actualPlanOriginal);
        var row=StrictJson.object();row.put("schema",STATE_SCHEMA);row.put("machine_id",plan.machineId());
        row.put("sequence",0);row.put("window_id",0);row.put("status","awaiting_initial_entry");
        row.putNull("start_date_raw");row.putNull("target_date_raw");row.put("target_days",plan.targetDays());
        row.put("last_settled_cycles",0);row.putNull("last_settled_date_raw");
        row.put("manual_repair_count",0);row.put("automatic_recovery_count",0);row.put("binding_lineage_count",0);
        row.putNull("latest_binding");
        var genesis=row.putObject(FIELD);genesis.put("schema",REQUEST_SCHEMA);
        genesis.put("planned_window_id",plan.plannedWindowId());genesis.put("target_days",plan.targetDays());
        genesis.set("original_request",actualPlanOriginal.toJson());
        return ContinuityState.fromJson(row,plan.machineId());
    }
    static void requirePreEntry(ObjectNode row) {
        StrictJson.require(STATE_SCHEMA.equals(StrictJson.text(row.get("schema")))
                &&"awaiting_initial_entry".equals(StrictJson.text(row.get("status")))
                &&StrictJson.integer(row.get("window_id"),0,0)==0
                &&StrictJson.integer(row.get("last_settled_cycles"),0,0)==0,
                "fresh store has no active window or settled credit");
        for(String key:Set.of("start_date_raw","target_date_raw","last_settled_date_raw","latest_binding"))
            StrictJson.require(row.has(key)&&row.get(key).isNull(),"fresh origin/date/binding must be explicitly absent: "+key);
        StrictJson.require(!row.has("game_binding")&&!row.has(WriterContracts.GAMEPLAY_ENTRY_FIELD)
                &&!row.has(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD),"pre-entry cannot contain Game or Entry authority");
        for(String key:Set.of("manual_repair_count","automatic_recovery_count","binding_lineage_count"))
            StrictJson.integer(row.get(key),0,0);
        var genesis=StrictJson.object(row.get(FIELD),Set.of("schema","planned_window_id","target_days","original_request"));
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(genesis.get("schema"))),"exact genesis source version required");
        Plan plan=new Plan(StrictJson.text(row.get("machine_id")),StrictJson.integer(genesis.get("planned_window_id"),1,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(genesis.get("target_days"),1,StrictJson.MAX_SAFE_INTEGER));
        StrictJson.require(StrictJson.integer(row.get("target_days"),1,StrictJson.MAX_SAFE_INTEGER)==plan.targetDays(),"genesis policy changed");
        ExactRef original=ExactRef.fromJson(genesis.get("original_request"));
        StrictJson.require(original.bytes()>0&&original.bytes()<=MAXIMUM_REQUEST_BYTES,"bounded actual genesis request required");
    }
    /** Called only by the existing closed GameplayEntry projection; its fixed authority revalidates native facts. */
    public static ObjectNode entryPredecessor(ContinuityState before,WriterContracts.Request actualEntry) {
        ObjectNode next=before.toJson();
        if(before.status()!=ContinuityState.Status.AWAITING_INITIAL_ENTRY)return next;
        requirePreEntry(next);
        var details=WriterContracts.gameplayEntryDetails(actualEntry);
        return observedEntryPredecessor(before,details);
    }
    /** Shared pure date/window projection; the observed-entry authority supplies its actual native facts. */
    static ObjectNode observedEntryPredecessor(ContinuityState before,ObjectNode details) {
        ObjectNode next=before.toJson();requirePreEntry(next);
        var frame=StrictJson.object(details.get("frame"),Set.of("snapshot_id","revision","native_revision","date_raw","player_character_id","connection_generation"));
        long date=StrictJson.integer(frame.get("date_raw"),0,Integer.MAX_VALUE);
        var genesis=StrictJson.object(next.get(FIELD),Set.of("schema","planned_window_id","target_days","original_request"));
        long days=StrictJson.integer(genesis.get("target_days"),1,StrictJson.MAX_SAFE_INTEGER);
        long target=Math.addExact(date,Math.multiplyExact(days,24));StrictJson.safe(target,0);
        next.put("schema","root.ck3.continuity-window/v1");next.put("status","running");
        next.put("window_id",StrictJson.integer(genesis.get("planned_window_id"),1,StrictJson.MAX_SAFE_INTEGER));
        next.put("start_date_raw",date);next.put("target_date_raw",target);next.put("last_settled_date_raw",date);
        next.set("game_binding",GameGeneration.fromJson(details.get("game")).toJson());
        var binding=next.putObject("latest_binding");binding.put("date_raw",date);
        binding.set("actor_character_id",frame.get("player_character_id").deepCopy());
        binding.put("episode_run_id",StrictJson.text(details.get("episode_id")));
        for(String field:Set.of("snapshot_id","revision","native_revision"))binding.set(field,frame.get(field).deepCopy());
        return next;
    }
}
