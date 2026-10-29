package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import org.xar.ck3.control.contracts.SavedFrame;
import static org.xar.ck3.control.service.root.OriginalRollbackSavedFrontier.*;

/** Reconstructs every completed unsaved cycle from the original contiguous FULL chain. No shape-only eligibility. */
public final class OriginalRollbackTail {
    private OriginalRollbackTail(){ }
    public record Tail(SavedFrame frame,long cycles,long nextSequence,ObjectNode state) {
        public Tail { state=state.deepCopy(); }
        @Override public ObjectNode state(){return state.deepCopy();}
    }
    public static Tail verify(OriginalRollbackFiles.Scope files,OriginalRollbackProof proof,Saved saved)throws IOException {
        ObjectNode raw=load(files,proof.sources().rawState(),262144),governance=load(files,proof.sources().rawGovernance(),262144);
        clean(raw);nil(governance,"pending_cycle");long cycles=n(raw,"completed_cycles",0);SavedFrame current=SavedFrame.fromJson(raw.get("before"));
        require(cycles>saved.cycles()&&current.dateRaw()>=saved.frame().dateRaw()
                &&current.actorCharacterId()==saved.frame().actorCharacterId()&&current.episodeRunId().equals(saved.frame().episodeRunId()),
                "actual completed unsaved tail must advance cycles in the unchanged saved episode");
        require(same(raw.get("actual_saved_checkpoint"),saved.rawCheckpoint())&&same(raw.get("campaign_goal_anchor"),saved.basis().get("campaign_goal_anchor"))
                &&n(raw,"start_date_raw",0)==n(obj(saved.basis().get("origin")),"start_date_raw",0)&&n(governance,"completed_cycles",0)==cycles,
                "completed tail changed the saved checkpoint, original goal or governance frontier");
        yes(raw.get("checkpoint_dirty_since_save"));
        long beforeCycles=saved.cycles(),beforeDate=saved.frame().dateRaw(),sequence=saved.next()-1;
        for(var source:proof.sources().successfulFullResponses()) {
            ObjectNode full=load(files,source,2*1024*1024),request=obj(full.get("request")),body=successful(full,null);
            eq(request,"command","full_loop");eq(body,"status","bounded_loop_finished");no(body.get("replay_allowed"));
            long afterCycles=n(body,"cumulative_cycles",0),turns=n(body,"actual_turns",1),afterSequence=n(request,"sequence",1);
            SavedFrame after=SavedFrame.fromJson(body.get("actual_end_frame"));
            require(afterSequence>sequence&&afterCycles>beforeCycles&&afterCycles-beforeCycles==turns
                    &&turns<=n(obj(request.get("arguments")),"max_turns",1)&&after.dateRaw()>=beforeDate
                    &&n(body,"actual_end_date_raw",0)==after.dateRaw()&&after.actorCharacterId()==saved.frame().actorCharacterId()
                    &&after.episodeRunId().equals(saved.frame().episodeRunId()),"retained FULL chain is noncontiguous, reordered or from another episode");
            ObjectNode tools=obj(obj(body.get("full_rpc_rows_v1")).get("tools"));
            for(String label:java.util.List.of("AUTO","MET")) {
                ObjectNode tool=obj(tools.get(label));require(n(tool,"count",0)==turns,"FULL AUTO/MET count differs from actual turns");
                zero(tool,"error_count");zero(tool,"client_error_count");
            }
            zero(obj(tools.get("SAVE")),"count");beforeCycles=afterCycles;beforeDate=after.dateRaw();sequence=afterSequence;
        }
        require(beforeCycles==cycles&&beforeDate==current.dateRaw(),"successful FULL chain omits part of the actual discarded progress");
        ObjectNode next=load(files,proof.sources().actualNext(),16384);long actualNext=n(next,"next_sequence",1);
        require(actualNext>sequence,"actual NEXT cannot be rolled back or reused");
        return new Tail(current,cycles,actualNext,raw);
    }
}
