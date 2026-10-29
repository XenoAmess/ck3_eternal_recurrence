package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Pure typed descriptor/reducer/cold-DATA tests. No Root, actual ACK, private proof or Game permission is minted. */
class EpisodeOperatorRebindTest {
    static ExactRef ref(String name){return new ExactRef("fixture/"+name,1,ContinuityJson.digest(StrictJson.object().put("fixture",name)));}
    static EpisodeWindow.Identity identity(long pid,String run,long epoch,long actor,long date){return new EpisodeWindow.Identity("fixture-machine",new GameGeneration(pid,new PythonOnlyUInt64(BigInteger.valueOf(pid+1000))),"session-"+pid,run,epoch,actor,date);}
    static ContinuityState active(){
        var old=identity(1,"old-run",0,7,100);var current=identity(2,"same-run",1,43,100);
        var begin=new EpisodeWindow.Begin("first",old,current,1,2,"next-parent",1,"a".repeat(64),ref("lifecycle"),ref("adopted"),List.of());
        var pin=new Pin(ref("begin"),new FileIdentity("1","2","3","2026-10-24T00:00:00Z",1));
        var committed=new EpisodeWindow.CommittedBegin(begin,2,begin.request().identity(),"b".repeat(64),pin);
        var baseline=new EpisodeWindow.Baseline(committed,"first-save",ref("pair"),ref("pair").sha256(),ref("save-receipt"),"c".repeat(64),current);
        var row=StrictJson.object().put("schema",EpisodeWindow.STATE_SCHEMA).put("machine_id","fixture-machine").put("sequence",3).put("window_id",2).put("status","running")
                .put("target_days",OriginalWindowReducer.TARGET_DAYS).put("start_date_raw",100).put("target_date_raw",100+24*OriginalWindowReducer.TARGET_DAYS)
                .put("last_settled_date_raw",100).put("last_settled_cycles",0).put("binding_lineage_count",0);
        row.set("game_binding",current.game().toJson());row.putObject("latest_binding").put("actor_character_id",43).put("episode_run_id","same-run").put("date_raw",100);
        row.set(EpisodeWindow.FIELD,new EpisodeWindow.State(EpisodeWindow.Phase.ACTIVE,begin,Optional.of(baseline)).toJson());row.putObject("UNKNOWN").put("existing","never-replay");
        return ContinuityState.fromJson(row,"fixture-machine");
    }
    static EpisodeWindow.OperatorRebind rebind(){var before=identity(2,"same-run",1,43,100);var after=identity(2,"same-run",1,-2,100);
        var originals=new EpisodeWindow.OperatorOriginals(ref("hello"),ref("native-before"),ref("ack"),ref("native-after"),ref("driver-before"),ref("driver-after"),ref("aux-before"),ref("aux-after"));
        return new EpisodeWindow.OperatorRebind("switch",before,after,5,6,"actual-switch-action","d".repeat(64),"original-request",ref("source"),originals,Optional.empty());}
    @Test void typedOperatorRoundTripAndPureReductionRetainFirstSaveAncestryAndUnknown(){
        var before=active();var change=rebind();assertEquals(change,EpisodeWindow.OperatorRebind.fromJson(change.toJson()));
        var after=EpisodeWindow.reduce(before,change.request());var decoded=EpisodeWindow.State.fromJson(after.toJson().get(EpisodeWindow.FIELD));
        assertEquals(1,decoded.operatorLineage().size());assertEquals(-2,decoded.operatorLineage().getFirst().after().actorId());
        assertEquals(EpisodeWindow.state(before).orElseThrow().baseline(),decoded.baseline());assertEquals(EpisodeWindow.state(before).orElseThrow().begin(),decoded.begin());
        assertEquals(before.origin(),after.origin());assertEquals(before.settledCycles(),after.settledCycles());assertEquals(before.settledDateRaw(),after.settledDateRaw());
        assertEquals(before.toJson().get("UNKNOWN"),after.toJson().get("UNKNOWN"));assertFalse(after.toJson().get("latest_binding").has("snapshot_id"),"old native snapshot identity is never relabeled as the switched actor");
        EpisodeWindow.requireReduction(before,after,change.request(),false);
        assertEquals(after.toJson(),OriginalWindowReducer.reduce(before,change.request()).toJson());
        assertThrows(IllegalArgumentException.class,()->EpisodeWindow.reduce(after,change.request()),"same original action cannot be committed twice");
    }
    @Test void actorTypesSameEpochAndDistinctRealOriginalRequirementsRejectInvalidDescriptors(){
        var original=rebind().toJson();for(var bad:List.of(StrictJson.object().put("x",true).get("x"),StrictJson.object().put("x",1.0).get("x"),StrictJson.object().put("x","-2").get("x"),StrictJson.object().put("x",-1).get("x"))){
            var changed=original.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("after")).set("actor_id",bad);assertThrows(IllegalArgumentException.class,()->EpisodeWindow.OperatorRebind.fromJson(changed));}
        for(String field:List.of("epoch","actor_id")){var changed=original.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("after")).put(field,field.equals("epoch")?2:43);assertThrows(IllegalArgumentException.class,()->EpisodeWindow.OperatorRebind.fromJson(changed));}
        var sameVersion=original.deepCopy().put("after_driver_version",5);assertThrows(IllegalArgumentException.class,()->EpisodeWindow.OperatorRebind.fromJson(sameVersion));
        var backwards=original.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)backwards.get("after")).put("date_raw",99);assertThrows(IllegalArgumentException.class,()->EpisodeWindow.OperatorRebind.fromJson(backwards));
    }
    @Test void oldSchemaCannotHideOperatorLineageAndWholeReducerRejectsUnrelatedMutation(){
        var before=active();var changed=EpisodeWindow.reduce(before,rebind().request());var state=(com.fasterxml.jackson.databind.node.ObjectNode)changed.toJson().get(EpisodeWindow.FIELD);
        assertEquals(EpisodeWindow.OPERATOR_SCHEMA,state.get("schema").textValue());assertEquals(state,EpisodeWindow.State.fromJson(state).toJson());
        var hidden=state.deepCopy().put("schema",EpisodeWindow.SCHEMA);assertThrows(IllegalArgumentException.class,()->EpisodeWindow.State.fromJson(hidden));
        var corrupt=changed.toJson();corrupt.put("last_settled_cycles",1);assertThrows(IllegalArgumentException.class,()->EpisodeWindow.requireReduction(before,ContinuityState.fromJson(corrupt,before.machineId()),rebind().request(),false));
    }
}
