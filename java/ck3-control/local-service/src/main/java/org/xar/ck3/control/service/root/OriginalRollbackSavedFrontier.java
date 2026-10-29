package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;

/** Reproves the saved business frontier from original FULL/SEM/SAVE/Queue and canonical ancestry; prior GREEN is not authority. */
public final class OriginalRollbackSavedFrontier {
    private OriginalRollbackSavedFrontier() { }
    public static final class Saved {
        private final ObjectNode basis,rawCheckpoint;
        private final SavedFrame frame;
        private final long cycles,next,previousHistoryRows;
        private final ExactRef driver,save,validator;
        private final FileStatIdentity driverIdentity,saveIdentity;
        private Saved(ObjectNode basis,ObjectNode checkpoint,SavedFrame frame,long cycles,long next,long previousHistoryRows,
                ExactRef driver,ExactRef save,ExactRef validator,FileStatIdentity driverIdentity,FileStatIdentity saveIdentity) {
            this.basis=basis.deepCopy();rawCheckpoint=checkpoint.deepCopy();this.frame=frame;this.cycles=cycles;this.next=next;this.previousHistoryRows=previousHistoryRows;
            this.driver=driver;this.save=save;this.validator=validator;this.driverIdentity=driverIdentity;this.saveIdentity=saveIdentity;
        }
        public ObjectNode basis(){return basis.deepCopy();}
        public ObjectNode rawCheckpoint(){return rawCheckpoint.deepCopy();}
        public SavedFrame frame(){return frame;}
        public long cycles(){return cycles;}
        public long next(){return next;}
        public long previousHistoryRows(){return previousHistoryRows;}
        public ExactRef driver(){return driver;}
        public ExactRef save(){return save;}
        public ExactRef validator(){return validator;}
        public FileStatIdentity driverIdentity(){return driverIdentity;}
        public FileStatIdentity saveIdentity(){return saveIdentity;}
    }
    public static Saved verify(OriginalRollbackFiles.Scope files,OriginalRollbackProof proof) throws IOException {
        ObjectNode basis=load(files,proof.sources().priorBasis(),65536);
        exact(basis,Set.of("schema","machine_id","observed_at_utc","origin","frame","completed_cycles","checkpoint","campaign_goal_anchor","refs","identity_schema",
                "driver_identity","save_identity","next_sequence","progress","unknown_requests","sidecars","ordinary_cycle_credit","game_day_credit","original_actions_replayed","power_loss_durability"));
        eq(basis,"schema","xar.current-saved-basis/v1");eq(basis,"machine_id",proof.machineId());utc(basis,"observed_at_utc");
        zero(basis,"ordinary_cycle_credit");zero(basis,"game_day_credit");no(basis.get("original_actions_replayed"));eq(basis,"power_loss_durability","not_asserted");
        eq(basis,"identity_schema",FileStatIdentity.SCHEMA);
        ObjectNode refs=obj(basis.get("refs"));exact(refs,Set.of("settled_state","seed","governance","semantic_response","save_response","settled_full_response","driver","save",
                "driver_close","closure","ledger","next","origin_ledger","wall_origin","checkpoint_validator"));
        ObjectNode prior=load(files,proof.sources().priorValidation(),65536);
        eq(prior,"machine_id",proof.machineId());
        if(prior.has("basis_ref"))require(ref(prior,"basis_ref").equals(proof.sources().priorBasis()),"prior qualification source tuple changed");
        // The prior row is retained as historical source only. Every needed saved frontier fact is rederived below.
        ObjectNode origin=obj(basis.get("origin"));String campaign=text(origin,"campaign_id");utc(origin,"original_wall_origin_utc");
        long start=n(origin,"start_date_raw",0),target=n(origin,"target_date_raw",0),days=n(origin,"target_days",1);
        require(target>start&&target-start==Math.multiplyExact(days,24),"actual original campaign day target differs");
        SavedFrame frame=SavedFrame.fromJson(basis.get("frame"));long cycles=n(basis,"completed_cycles",0),next=n(basis,"next_sequence",1);
        require(frame.dateRaw()>=start,"saved frame predates original campaign");
        ObjectNode goal=obj(basis.get("campaign_goal_anchor"));eq(goal,"campaign_id",campaign);
        require(n(goal,"current_character_id",1)==frame.actorCharacterId(),"saved campaign actor differs");
        ObjectNode seed=load(files,ref(refs,"seed"),262144),state=load(files,ref(refs,"settled_state"),262144);
        clean(seed);clean(state);
        for(ObjectNode row:List.of(seed,state))require(n(row,"completed_cycles",0)==cycles&&SavedFrame.fromJson(row.get("before")).equals(frame)
                &&n(row,"start_date_raw",0)==start&&same(row.get("campaign_goal_anchor"),goal),"original saved Queue/seed/frame/goal differs");
        Set<String> changed=Set.of("actual_saved_checkpoint","actual_saved_checkpoint_source","counts","checkpoint_calendar_v1","checkpoint_dirty_since_save","checkpoint_due_after_readonly_chain");
        var fields=new HashSet<String>();seed.fieldNames().forEachRemaining(fields::add);state.fieldNames().forEachRemaining(fields::add);
        for(String key:fields)if(!changed.contains(key))require(seed.has(key)&&state.has(key)&&same(seed.get(key),state.get(key)),"maintenance SAVE changed original field: "+key);
        ObjectNode full=load(files,ref(refs,"settled_full_response"),2*1024*1024),fullRequest=obj(full.get("request")),fullBody=successful(full,null);
        eq(fullRequest,"command","full_loop");eq(fullBody,"status","bounded_loop_finished");no(fullBody.get("replay_allowed"));
        require(n(fullBody,"cumulative_cycles",0)==cycles&&n(fullBody,"actual_end_date_raw",0)==frame.dateRaw()
                &&SavedFrame.fromJson(fullBody.get("actual_end_frame")).equals(frame),"actual saved FULL/Queue frontier differs");
        long fullSequence=n(fullRequest,"sequence",1);
        ObjectNode semRow=load(files,ref(refs,"semantic_response"),2*1024*1024),sem=successful(semRow,"ck3_take_semantic_snapshot_private_v1");
        long semSequence=n(obj(semRow.get("request")),"sequence",1);
        require(n(sem,"date_raw",0)==frame.dateRaw()&&n(sem,"episode_character_id",1)==frame.actorCharacterId()
                &&text(sem,"episode_run_id").equals(frame.episodeRunId())&&same(sem.get("campaign_goal"),goal),"actual saved SEM identity/goal differs");
        yes(sem.get("map_ready"));
        ObjectNode saveRow=load(files,ref(refs,"save_response"),2*1024*1024),saveRequest=obj(saveRow.get("request"));
        long saveSequence=n(saveRequest,"sequence",1);ObjectNode saveBody=successful(saveRow,"ck3_save_checkpoint"),checkpoint=obj(saveBody.get("checkpoint"));
        require(n(obj(saveRequest.get("arguments")),"expected_revision",1)==n(sem,"revision",1),"actual SAVE did not bind original SEM revision");
        eq(checkpoint,"status","saved");
        require(same(checkpoint,seed.get("actual_saved_checkpoint"))&&n(checkpoint,"date_raw",0)==frame.dateRaw()
                &&n(checkpoint,"episode_character_id",1)==frame.actorCharacterId()&&text(checkpoint,"episode_run_id").equals(frame.episodeRunId())
                &&same(checkpoint.get("succession_lifecycle"),sem.get("succession_lifecycle")),"actual saved checkpoint/lifecycle differs");
        ObjectNode governance=load(files,ref(refs,"governance"),262144);nil(governance,"pending_cycle");require(n(governance,"completed_cycles",0)==cycles,"saved governance frontier differs");
        ObjectNode ledger=load(files,ref(refs,"ledger"),65536),originLedger=load(files,ref(refs,"origin_ledger"),65536);
        for(ObjectNode old:List.of(ledger,originLedger)) {
            eq(old,"machine_id",proof.machineId());require(n(old,"start_date_raw",0)==start&&n(old,"target_date_raw",0)==target&&n(old,"target_days",1)==days,"actual saved ledger/window origin differs");
            ContinuityState retained=files.session().requireHistoricalState(n(old,"sequence",0),ContinuityJson.digest(old));
            require(same(retained.toJson(),old),"saved ledger source is outside actual canonical ancestry");
        }
        ObjectNode wall=load(files,ref(refs,"wall_origin"),65536);eq(wall,"schema","xar.c23.canonical-cold-prelaunch/v1");eq(wall,"machine_id",proof.machineId());
        require(text(wall,"original_wall_start_utc").equals(text(origin,"original_wall_origin_utc")),"original wall time changed");
        ObjectNode oldCounts=obj(state.get("counts")),newCounts=obj(seed.get("counts"));require(keys(oldCounts).equals(keys(newCounts)),"saved counter keys changed");
        for(String key:keys(oldCounts)) {long before=n(oldCounts,key,0),after=n(newCounts,key,0);require(key.equals("checkpoint_saved")||before==after,"unrelated saved counter changed");}
        long oldCount=n(oldCounts,"checkpoint_saved",0),newCount=n(newCounts,"checkpoint_saved",0);
        boolean accounted=same(state.get("actual_saved_checkpoint"),checkpoint)&&isFalse(state.get("checkpoint_dirty_since_save"))
                &&state.has("checkpoint_calendar_v1")&&n(obj(state.get("checkpoint_calendar_v1")),"last_saved_date_raw",0)==frame.dateRaw();
        ObjectNode progress=obj(basis.get("progress"));exact(progress,Set.of("ledger_cycles","ledger_date_raw","settled_cycles","settled_date_raw","full_sequence","checkpoint_count_before","checkpoint_count_after","maintenance_save_already_accounted"));
        require(n(progress,"ledger_cycles",0)==n(ledger,"last_settled_cycles",0)&&n(progress,"ledger_date_raw",0)==n(ledger,"last_settled_date_raw",0)
                &&n(progress,"settled_cycles",0)==cycles&&n(progress,"settled_date_raw",0)==frame.dateRaw()&&n(progress,"full_sequence",1)==fullSequence
                &&n(progress,"checkpoint_count_before",0)==oldCount&&n(progress,"checkpoint_count_after",0)==newCount
                &&newCount==oldCount+(accounted?0:1)&&bool(progress.get("maintenance_save_already_accounted"))==accounted
                &&n(progress,"ledger_cycles",0)<=cycles&&n(progress,"ledger_date_raw",0)<=frame.dateRaw(),"original SAVE accounting differs");
        ObjectNode historicalNext=load(files,ref(refs,"next"),16384);
        require(n(historicalNext,"next_sequence",1)==next&&fullSequence<semSequence&&semSequence<saveSequence&&saveSequence<next,"original FULL/SEM/SAVE/NEXT ordering differs");
        ObjectNode close=load(files,ref(refs,"driver_close"),262144),closure=load(files,ref(refs,"closure"),1024*1024);
        eq(close,"machine_id",proof.machineId());eq(closure,"machine_id",proof.machineId());
        long previousHistory=n(obj(close.get("Driver")),"command_history_count",1);
        var unknown=arr(basis.get("unknown_requests"),64);var sequences=new HashSet<Long>();
        for(JsonNode node:unknown) {
            ObjectNode row=obj(node);exact(row,Set.of("sequence","evidence_ref","status","replayed","cycle_credit","day_credit"));
            long sequence=n(row,"sequence",1);require(sequence<next&&sequences.add(sequence),"historical UNKNOWN identity changed");eq(row,"status","unknown");no(row.get("replayed"));zero(row,"cycle_credit");zero(row,"day_credit");
            ObjectNode actual=load(files,ref(row,"evidence_ref"),262144),pending=obj(actual.get("pending_cycle"));
            require(n(pending,"auto_sequence",1)==sequence,"original UNKNOWN source differs");eq(pending,"stage","auto_unsettled");
        }
        var sidecars=arr(basis.get("sidecars"),64);var names=new HashSet<String>();
        for(JsonNode node:sidecars) {
            ExactRef source=ExactRef.fromJson(node);require(names.add(source.path()),"duplicate saved sidecar source");
            ObjectNode sidecar=load(files,source,65536);if(sidecar.has("pending"))nil(sidecar,"pending");
        }
        ExactRef driver=ref(refs,"driver"),save=ref(refs,"save"),validator=ref(refs,"checkpoint_validator");
        files.read(validator,65536);
        FileStatIdentity driverIdentity=FileStatIdentity.fromJson(basis.get("driver_identity"),FileStatIdentity.SCHEMA),saveIdentity=FileStatIdentity.fromJson(basis.get("save_identity"),FileStatIdentity.SCHEMA);
        require(driverIdentity.bytes().equals(java.math.BigInteger.valueOf(driver.bytes()))&&saveIdentity.bytes().equals(java.math.BigInteger.valueOf(save.bytes())),"saved Driver/SAVE byte identities differ");
        ObjectNode anchor=obj(basis.get("checkpoint"));exact(anchor,Set.of("name","load_save_name","path","size","sha256","saved_date_raw","history_index","succession_lifecycle"));
        eq(anchor,"name","xar_checkpoint.ck3");eq(anchor,"load_save_name","xar_checkpoint");
        require(text(anchor,"path").equals(save.path())&&n(anchor,"size",1)==save.bytes()&&text(anchor,"sha256").equals(save.sha256())
                &&n(anchor,"saved_date_raw",0)==frame.dateRaw()&&n(anchor,"history_index",1)==n(checkpoint,"history_index",1),"normalized saved anchor differs");
        require(same(anchor.get("succession_lifecycle"),checkpoint.get("succession_lifecycle")),"saved lifecycle differs from normalized anchor");
        return new Saved(basis,checkpoint,frame,cycles,next,previousHistory,driver,save,validator,driverIdentity,saveIdentity);
    }
    static ObjectNode load(OriginalRollbackFiles.Scope files,ExactRef ref,int maximum)throws IOException {
        return obj(StrictJson.parse(files.read(ref,maximum).bytes(),maximum));
    }
    static ObjectNode successful(ObjectNode row,String tool) {
        require(!row.hasNonNull("client_error"),"original response has client failure");
        ObjectNode request=obj(row.get("request")),result=obj(row.get("result"));if(tool!=null)eq(request,"tool",tool);
        no(result.get("is_error"));eq(result,"result_type","complete");return obj(result.get("structured_content"));
    }
    static void clean(ObjectNode row){eq(row,"schema","g2.queue.cumulative-loop/v1");for(String key:List.of("pending_cycle","pending_checkpoint","terminal"))nil(row,key);for(String key:List.of("pending_natural_succession","pending_unsafe_route_halt"))if(row.has(key))nil(row,key);}
    static ObjectNode obj(JsonNode value){require(value instanceof ObjectNode,"required original object; absent/null are distinct");return (ObjectNode)value;}
    static List<JsonNode> arr(JsonNode value,int maximum){require(value!=null&&value.isArray()&&value.size()<=maximum,"finite original array required");var result=new java.util.ArrayList<JsonNode>();value.forEach(result::add);return List.copyOf(result);}
    static Set<String> keys(ObjectNode row){var result=new HashSet<String>();row.fieldNames().forEachRemaining(result::add);return Set.copyOf(result);}
    static void exact(ObjectNode row,Set<String> fields){require(keys(row).equals(fields),"exact original field contract required");}
    static String text(ObjectNode row,String key){return StrictJson.text(row.get(key));}
    static long n(ObjectNode row,String key,long minimum){return StrictJson.integer(row.get(key),minimum,StrictJson.MAX_SAFE_INTEGER);}
    static ExactRef ref(ObjectNode row,String key){return ExactRef.fromJson(row.get(key));}
    static void eq(ObjectNode row,String key,String expected){require(expected.equals(text(row,key)),"actual original "+key+" differs");}
    static void zero(ObjectNode row,String key){StrictJson.integer(row.get(key),0,0);}
    static void yes(JsonNode value){StrictJson.trueValue(value);}
    static void no(JsonNode value){require(isFalse(value),"actual original false value required");}
    static boolean isFalse(JsonNode value){return value!=null&&value.isBoolean()&&!value.booleanValue();}
    static boolean bool(JsonNode value){require(value!=null&&value.isBoolean(),"actual original boolean required");return value.booleanValue();}
    static void nil(ObjectNode row,String key){require(row.has(key)&&row.get(key).isNull(),"actual required original null: "+key);}
    static void utc(ObjectNode row,String key){StrictJson.utc(text(row,key));}
    static boolean same(JsonNode first,JsonNode second){return first==null||second==null?first==second:ContinuityJson.same(first,second);}
    static void require(boolean condition,String reason){StrictJson.require(condition,reason);}
}
