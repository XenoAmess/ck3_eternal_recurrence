package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.checkpoint.DriverRollbackFailurePublication;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverCapabilityStateProducer;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSemanticReadState;
import org.xar.ck3.control.application.history.DriverHistoryProjection;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure replay of the actual physical cold binding. This value never performs stage, commit or adoption. */
public final class RootRestoreMaterialProjection {
    private RootRestoreMaterialProjection() { }
    public record Input(String requestId, GameGeneration previous, NativeObservationPort.TransportSession replacement,
            String actualPipe, String snapshotId, BigInteger nativeRevision, DriverStateSnapshot.Complete saved, DriverStateSnapshot.Complete abandoned,
            Obj actualNativeState, Obj actualLifecycleControl, ExactRef lifecycleSource, ExactRef nativeSource,
            Optional<Obj> abandonedSnapshot) {
        public Input {
            StrictJson.text(requestId); Objects.requireNonNull(previous); Objects.requireNonNull(replacement); StrictJson.text(actualPipe);
            StrictJson.text(snapshotId); Objects.requireNonNull(nativeRevision); StrictJson.require(nativeRevision.signum()>=0,"actual native revision required");
            Objects.requireNonNull(saved); Objects.requireNonNull(abandoned); Objects.requireNonNull(actualNativeState);
            Objects.requireNonNull(actualLifecycleControl); Objects.requireNonNull(lifecycleSource); Objects.requireNonNull(nativeSource);
            Objects.requireNonNull(abandonedSnapshot);
        }
    }
    public record Reduced(DriverStateSnapshot.Complete provisional, Obj completedRow, Obj restoredSemantic) {
        public Reduced { Objects.requireNonNull(provisional); Objects.requireNonNull(completedRow); Objects.requireNonNull(restoredSemantic); }
    }
    public static Reduced reduce(Input input) {
        Objects.requireNonNull(input); var saved=input.saved(); var abandoned=input.abandoned(); var raw=input.actualNativeState();
        StrictJson.require(input.previous().pid()==abandoned.session().bridgePid()
                &&!input.previous().equals(input.replacement().game())&&input.previous().pid()!=input.replacement().game().pid()
                &&saved.session().actorId().equals(abandoned.session().actorId())
                &&saved.session().episodeRunId().equals(abandoned.session().episodeRunId()),"physical cold binding crossed the original Game/actor/episode");
        Obj checkpoint=slot(saved.lastCheckpoint(),"saved checkpoint"), priorCheckpoint=slot(abandoned.lastCheckpoint(),"abandoned checkpoint");
        StrictJson.require(checkpoint.equals(priorCheckpoint),"abandoned Driver does not retain the exact physical saved checkpoint");
        var checkpointIdentity=DriverHistoryProjection.checkpointIdentity(checkpoint).orElseThrow(()->new IllegalArgumentException("actual saved checkpoint identity missing"));
        Obj player=OpportunityJson.object(raw.get("played_character"),"actual replacement player");
        StrictJson.require(OpportunityJson.bool(raw.get("map_ready"),"map_ready")&&OpportunityJson.bool(raw.get("paused"),"paused")
                &&OpportunityJson.bool(player.get("alive"),"alive")
                &&OpportunityJson.integer(player.get("character_id"),"actual player").equals(saved.session().actorId())
                &&OpportunityJson.integer(raw.get("date_raw"),"actual date").equals(checkpointIdentity.dateRaw())
                &&OpportunityJson.integer(checkpoint.get("episode_character_id"),"checkpoint actor").equals(saved.session().actorId())
                &&OpportunityJson.text(checkpoint.get("episode_run_id"),"checkpoint episode").equals(saved.session().episodeRunId()),
                "actual replacement paused living map does not match saved actor/date/episode");
        requireLifecycle(input);
        List<Obj> savedRows=DriverSurvivingHistory.rows(saved), oldRows=DriverSurvivingHistory.rows(abandoned);
        var savedAnchor=DriverHistoryProjection.checkpointHistoryIndex(checkpoint,savedRows);
        StrictJson.require(savedAnchor.isPresent()&&savedAnchor.getAsInt()==savedRows.size()&&oldRows.size()>=savedRows.size(),"actual saved complete prefix unavailable");
        for(int index=0;index<savedRows.size();index++)StrictJson.require(savedRows.get(index).equals(oldRows.get(index)),"saved unknown/failed history prefix changed");
        var projection=DriverHistoryProjection.retain(checkpoint,oldRows);
        StrictJson.require(projection instanceof DriverHistoryProjection.Available,"actual cold history projection unavailable");
        List<Obj> history=new ArrayList<>(((DriverHistoryProjection.Available)projection).rows());
        Obj lifecycle=new Obj(java.util.Map.of("request_id",new Text(input.requestId()),"previous_pid",integer(input.previous().pid()),
                "pid",integer(input.replacement().game().pid()),"connection_generation",new IntegerValue(input.replacement().connectionGeneration()),
                "original_lifecycle_source",reference(input.lifecycleSource())));
        var resultFields=new LinkedHashMap<String,Value>(); resultFields.put("step",new Text("restore-checkpoint"));
        resultFields.put("accepted",new Bool(true));resultFields.put("status",new Text("restored"));resultFields.put("backend_id",new Text("native-headless"));
        resultFields.put("source",new Text("native-session-cold-start"));resultFields.put("checkpoint",checkpoint);
        resultFields.put("restored_date_raw",raw.get("date_raw"));resultFields.put("map_ready",raw.get("map_ready"));resultFields.put("paused",raw.get("paused"));
        resultFields.put("lifecycle",lifecycle); resultFields.put("original_native_packet",reference(input.nativeSource()));
        resultFields.put("snapshot_id",new Text(input.snapshotId()));resultFields.put("native_revision",new IntegerValue(input.nativeRevision()));
        Obj cold=row(history.size()+1,new Obj(resultFields));history.add(cold);
        var session=new DriverStateSnapshot.Session(input.actualPipe(),input.replacement().game().pid(),saved.session().actorId(),saved.session().episodeRunId());
        var entries=history.stream().map(value->new DriverStateSnapshot.HistoryEntry(OpportunityJson.integer(value.get("index"),"history index").longValueExact(),
                new DriverStateSnapshot.Value(OpportunityJson.encode(value)))).toList();
        var initial=new DriverStateSnapshot.Complete(session,entries,saved.lastCheckpoint(),abandoned.rollbackWarFailure(),new DriverStateSnapshot.NullValue(),
                new DriverStateSnapshot.NullValue(),saved.successionLifecycle(),saved.campaignGoal(),abandoned.rollbackWarFailures());
        Obj restored=semantic(raw,session,input.replacement());
        // Execute the genuine discarded-branch domain reducer before the Root can stage anything.
        var reduced=DriverRollbackFailurePublication.project(initial,abandoned,restored,input.abandonedSnapshot(),64);
        var completeResult=new LinkedHashMap<>(resultFields);completeResult.put("source",new Text("native-session-lifecycle-queue"));
        input.abandonedSnapshot().map(value->value.get("date_raw")).ifPresent(value->completeResult.put("starting_date_raw",value));
        // No public revision is invented before the unique staged protocol producer observes this Game.
        return new Reduced(reduced,row(history.size(),new Obj(completeResult)),restored);
    }
    /** Actual cold auxiliary reduction over replayed saved producer data; no caller-supplied empty cache substitutes. */
    public static Obj reduceAuxiliary(Obj verifiedActualSavedAuxiliary,Obj actualNativeState) {
        Objects.requireNonNull(verifiedActualSavedAuxiliary);Objects.requireNonNull(actualNativeState);
        var fields=new LinkedHashMap<>(verifiedActualSavedAuxiliary.members());
        // Transport/native facts are supplied afresh by the same staged producer, rather than borrowing old diagnostics.
        actualNativeState.members().keySet().forEach(fields::remove);fields.remove("diagnostics");
        fields.put("arrange_marriage_choices",new Arr(List.of()));fields.put("arrange_marriage_query_sequence",Nil.INSTANCE);
        fields.put("active_combat_retreat_token",Nil.INSTANCE);fields.put("succession_reconciliation",Nil.INSTANCE);
        fields.remove("capability_succession_source");
        for(String key:List.of("campaign_root_context_query","episode_seed","episode_transition","independent_battle_speed_readiness",
                "capability_read_sources","episode_transition_error"))StrictJson.require(fields.containsKey(key),"actual saved private cache missing: "+key);
        StrictJson.require(fields.get("episode_transition")==Nil.INSTANCE,"unresolved original episode transition cannot be erased by restore");
        fields.put("driver_state_restored",new Bool(true));fields.put("driver_state_error",Nil.INSTANCE);
        fields.put("restore_kind",new Text("cold_checkpoint"));fields.put("episode_binding_state",new Text("active_resumed"));fields.put("cold_candidate_rejection",Nil.INSTANCE);
        if(fields.containsKey("rollback_war_failures_migration_required")) {
            OpportunityJson.bool(fields.get("rollback_war_failures_migration_required"),"rollback migration marker");
            fields.put("rollback_war_failures_migration_required",new Bool(false));
        }
        return DriverSemanticReadState.clearForCold(DriverCapabilityStateProducer.afterEpisodeCacheClear(new Obj(fields)));
    }
    private static void requireLifecycle(Input input) {
        Obj control=input.actualLifecycleControl();
        StrictJson.require(text(control.get("schema"),"xar.java-game-replacement/v1")
                &&text(control.get("parentLifecycleIntentId"),input.requestId())
                &&text(control.get("phase"),"NATIVE_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED")
                &&OpportunityJson.integer(control.get("oldPid"),"original lifecycle PID").equals(BigInteger.valueOf(input.previous().pid()))
                &&text(control.get("oldBirthDecimal"),input.previous().creationFiletime().value().toString()),"actual lifecycle original parent/generation source differs");
    }
    private static Obj semantic(Obj raw,DriverStateSnapshot.Session driver,NativeObservationPort.TransportSession actual) {
        var fields=new LinkedHashMap<>(raw.members());
        Value oldEpisode=fields.get("episode_run_id");StrictJson.require(oldEpisode==null||text(oldEpisode,driver.episodeRunId()),"native episode field conflicts with saved binding");
        fields.put("episode_run_id",new Text(driver.episodeRunId()));
        var diagnostics=raw.get("diagnostics") instanceof Obj original?new LinkedHashMap<>(original.members()):new LinkedHashMap<String,Value>();
        Value oldPid=diagnostics.put("bridge_pid",integer(actual.game().pid()));
        StrictJson.require(oldPid==null||oldPid.equals(integer(actual.game().pid())),"native diagnostics belongs to another actual Game");
        Value oldConnection=diagnostics.put("connection_generation",new IntegerValue(actual.connectionGeneration()));
        StrictJson.require(oldConnection==null||oldConnection.equals(new IntegerValue(actual.connectionGeneration())),"native diagnostics belongs to another actual connection");
        fields.put("diagnostics",new Obj(diagnostics));return new Obj(fields);
    }
    private static Obj row(long index,Obj result) { return new Obj(java.util.Map.of("index",integer(index),"command",new Text("restore-checkpoint"),"ok",new Bool(true),"result",result)); }
    private static Obj slot(DriverStateSnapshot.Slot slot,String context) {
        StrictJson.require(slot instanceof DriverStateSnapshot.Value,context+" must be present");
        return DriverJson.object(((DriverStateSnapshot.Value)slot).json(),DriverJson.MAX_NATIVE_BYTES);
    }
    private static Obj reference(ExactRef ref) { return org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.reference(ref); }
    private static IntegerValue integer(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static boolean text(Value value,String expected) { return value instanceof Text word&&word.value().equals(expected); }
}
