package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.*;

/** Identity/frontier DATA preflight only. No private material, replacement Game or readiness is constructed. */
class OrdinarySavedPredecessorTest {
    private static ObjectNode retained(String name)throws IOException{
        try(InputStream stream=OrdinarySavedPredecessorTest.class.getResourceAsStream("/"+name)){
            assertNotNull(stream,"existing retained continuity resource: "+name);
            return ContinuityJson.parseObject(stream.readAllBytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
        }
    }
    private static ContinuityState current(){var row=EpisodeOperatorRebindTest.active().toJson();row.put("last_settled_cycles",3);row.put("last_settled_date_raw",124);return ContinuityState.fromJson(row,"fixture-machine");}
    private static ObjectNode basis(ContinuityState actual){var row=StrictJson.object();row.put("machine_id",actual.machineId());row.put("completed_cycles",4);
        var origin=row.putObject("origin");origin.put("window_id",actual.origin().windowId());origin.put("start_date_raw",actual.origin().startDateRaw());origin.put("target_date_raw",actual.origin().targetDateRaw());origin.put("target_days",actual.origin().targetDays());
        var frame=row.putObject("frame");frame.put("snapshot_id","saved");frame.put("revision",4);frame.put("native_revision",4);frame.put("date_raw",148);frame.put("actor_character_id",-2);frame.put("episode_run_id","same-run");
        row.putObject("refs").set("settled_full_response",new ExactRef("data/already-settled-response",1,"a".repeat(64)).toJson());return row;
    }
    private static SavedContinuityAttachment.Input input(ContinuityState actual,ObjectNode basis){
        var details=StrictJson.object();details.put("new_ordinary_cycle_credit",0);details.put("game_day_credit",0);details.put("original_actions_replayed",false);details.put("window_origin_reset",false);
        var progress=StrictJson.object();progress.put("ledger_cycles",actual.settledCycles());progress.put("ledger_date_raw",actual.settledDateRaw());
        var opening=StrictJson.object();opening.put("actor_character_id",-2);opening.put("date_raw",148);opening.put("episode_run_id","same-run");
        return new SavedContinuityAttachment.Input(actual,ContinuityJson.canonical(details),ContinuityJson.canonical(basis),ContinuityJson.canonical(actual.toJson().get("game_binding")),ContinuityJson.canonical(opening),ContinuityJson.canonical(progress));
    }
    @Test void sharedPreflightAndRealPureReducerUseSameOriginAndAlreadySettledFrontier(){
        var actual=current();var basis=basis(actual);SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(basis));
        var after=SavedContinuityAttachment.reduce(input(actual,basis));assertEquals(actual.origin(),after.origin());assertEquals(4,after.settledCycles());assertEquals(148,after.settledDateRaw());
        assertEquals(actual.toJson().get(EpisodeWindow.FIELD),after.toJson().get(EpisodeWindow.FIELD));assertEquals(actual.toJson().get("UNKNOWN"),after.toJson().get("UNKNOWN"));
        assertEquals(0,after.toJson().get("current_saved_reconciliation").get("ordinary_cycle_credit").longValue());
        var equal=basis(actual);equal.put("completed_cycles",actual.settledCycles());((ObjectNode)equal.get("frame")).put("date_raw",actual.settledDateRaw());
        SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(equal));
    }
    @Test void rollbackWrongWindowAndTargetFailBeforeReplacementAndAlsoAtReducer(){
        var actual=current();
        for(String field:List.of("window_id","start_date_raw","target_date_raw","target_days")){
            var invalid=basis(actual);ObjectNode origin=(ObjectNode)invalid.get("origin");origin.put(field,origin.get(field).longValue()+1);
            assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(invalid)));
            assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.reduce(input(actual,invalid)));
        }
        var oldCycles=basis(actual);oldCycles.put("completed_cycles",2);assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(oldCycles)));
        var oldDate=basis(actual);((ObjectNode)oldDate.get("frame")).put("date_raw",123);assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.reduce(input(actual,oldDate)));
        var foreign=basis(actual);foreign.put("machine_id","other-machine");assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(foreign)));
    }
    @Test void strictTypesMissingNullAndFirstBranchCannotMasqueradeAsOrdinaryPreflight(){
        var actual=current();
        for(String field:List.of("completed_cycles","date_raw","actor_character_id"))for(var bad:List.of(StrictJson.object().put("x",true).get("x"),StrictJson.object().put("x",4.0).get("x"),StrictJson.object().put("x","4").get("x"),com.fasterxml.jackson.databind.node.NullNode.instance)){
            var invalid=basis(actual);ObjectNode container=field.equals("completed_cycles")?invalid:(ObjectNode)invalid.get("frame");container.set(field,bad);
            assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(invalid)));
        }
        for(String field:List.of("origin","frame","completed_cycles")){var missing=basis(actual);missing.remove(field);assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(missing)));}
        var sentinel=basis(actual);((ObjectNode)sentinel.get("frame")).put("actor_character_id",-1);assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(sentinel)));
        var first=basis(actual);first.put("schema",SavedContinuityAttachment.FIRST_BASIS_SCHEMA);assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(first)));
    }
    @Test void originalP37RecordedAlignmentReplaysButCannotAuthorizeAnotherRollbackReplacement()throws IOException{
        var head=retained("n46-head240.actual.json");var basis=retained("n46-prior-basis.actual.json");
        assertEquals(SavedContinuityAttachment.LEGACY_BASIS_SCHEMA,basis.get("schema").textValue());
        assertFalse(basis.get("origin").has("window_id"));
        var actual=ContinuityState.fromJson(head,head.get("machine_id").textValue());
        var progress=((ObjectNode)basis.get("progress")).deepCopy();progress.put("ledger_cycles",actual.settledCycles());progress.put("ledger_date_raw",actual.settledDateRaw());
        var request=new SavedContinuityAttachment.Input(actual,ContinuityJson.canonical(head.get("last_current_saved_cold")),ContinuityJson.canonical(basis),
                ContinuityJson.canonical(head.get("game_binding")),ContinuityJson.canonical(basis.get("frame")),ContinuityJson.canonical(progress));
        var replayed=SavedContinuityAttachment.reduce(request);
        assertEquals(-7,replayed.toJson().get("current_saved_reconciliation").get("already_settled_alignment_cycles").longValue());
        assertEquals(actual.origin(),replayed.origin());assertEquals(actual.sequence(),replayed.sequence());
        assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(basis)));
        var aligned=head.deepCopy();aligned.put("last_settled_cycles",basis.get("completed_cycles").longValue());
        var alignedActual=ContinuityState.fromJson(aligned,actual.machineId());
        SavedContinuityAttachment.requireOrdinaryPredecessor(alignedActual,ContinuityJson.canonical(basis));
    }
    @Test void explicitP37ShapeIsSeparateFromJavaWindowAndFirstContracts()throws IOException{
        var head=retained("n46-head240.actual.json");var legacy=retained("n46-prior-basis.actual.json");
        head.put("last_settled_cycles",legacy.get("completed_cycles").longValue());
        var actual=ContinuityState.fromJson(head,head.get("machine_id").textValue());
        var modern=legacy.deepCopy();modern.remove("schema");
        assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(modern)));
        var invented=legacy.deepCopy();((ObjectNode)invented.get("origin")).put("window_id",actual.origin().windowId());
        assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(invented)));
        for(String field:List.of("start_date_raw","target_date_raw","target_days")){
            var invalid=legacy.deepCopy();((ObjectNode)invalid.get("origin")).put(field,true);
            assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(invalid)));
        }
        var wrongDays=legacy.deepCopy();((ObjectNode)wrongDays.get("origin")).put("target_days",actual.origin().targetDays()+1);
        assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(wrongDays)));
        var unknown=legacy.deepCopy();unknown.put("schema","xar.current-saved-basis/v999");
        assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(actual,ContinuityJson.canonical(unknown)));
    }
}
