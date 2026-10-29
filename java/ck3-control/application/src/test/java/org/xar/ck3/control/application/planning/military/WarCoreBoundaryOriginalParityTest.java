package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.history.RollbackWarFailures;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Required original-producer differential. Missing capture is RED, never a skipped green test. */
final class WarCoreBoundaryOriginalParityTest {
    @TempDir Path temporary;
    @Test void completeOriginalBoundaryCaptureMatchesActualJavaProducers()throws Exception {
        String repo=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repo,"full CI must provide its actual original producer repository");
        assertNotNull(python,"full CI must provide its actual original producer interpreter");
        Path capture=temporary.resolve("boundary-original.json");
        WarCoreBoundaryOriginalCapture.main(new String[]{repo,python,capture.toString()});
        Obj golden=OpportunityJson.object(OpportunityJson.parse(Files.readAllBytes(capture)),"actual original boundary capture");
        assertEquals(new Text("xar.warcore-boundary-original-golden.v1"),golden.get("schema"));
        assertTrue(golden.get("machine_id") instanceof Text);
        assertEquals(new Bool(false),golden.get("new_live_evidence"));
        for(Obj row:objects(golden.get("rollback"))) {
            Optional<RollbackWarFailures.Failure> actual=RollbackWarFailures.deriveEpoch(objects(row.get("history")),(Obj)row.get("checkpoint"),
                    (Obj)row.get("restored_snapshot"),OpportunityJson.text(row.get("episode_run_id"),"episode"),Optional.empty());
            assertEquals(row.get("expected"),actual.<Value>map(RollbackWarFailures::encode).orElse(Nil.INSTANCE),row.get("name").toString());
        }
        for(Obj row:objects(golden.get("assault"))) {
            Obj snapshot=(Obj)row.get("snapshot");
            List<Obj> actual=AssaultLifecycle.pending(snapshot,objects(snapshot.get("active_wars")),objects(row.get("history"))).stream().map(AssaultLifecycle.Pending::toJson).toList();
            assertEquals(row.get("expected"),new Arr(actual.stream().<Value>map(value->value).toList()),row.get("name").toString());
        }
        for(Obj row:objects(golden.get("end_conditions")))
            assertEquals(row.get("expected"),NativeWarEndConditions.assess((Obj)row.get("war"),row.get("options") instanceof Obj options?options:null),row.get("name").toString());
    }
    private static List<Obj> objects(Value value){return OpportunityJson.array(value,"capture array").stream().map(item->OpportunityJson.object(item,"capture row")).toList();}
}
