package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Configuration/summary Java DATA only; no Save, transport, baseline authority or Native claim. */
final class NativeOwnerCurrentSupermanHealthResumeSelectionTest {
    private static ObjectNode resume() {
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v36")
                .put("mode","current_superman_health_resume_saved_baseline_and_begin")
                .put("overall_timeout_seconds",180).put("read_timeout_seconds",60).put("maximum_frames_per_operation",64);
        c.putObject("owner_descriptor").put("path","D:/health-resume-DATA/owner.json").put("bytes",12).put("sha256","1".repeat(64));
        c.set("baseline_progress",new ExactRef("D:/health-resume-DATA/current-superman-health-progress.json",19786,"2".repeat(64)).toJson());return c;
    }
    @Test void explicitResumeRequiresOnlyCommonAndFullProgressFilePin()throws IOException {
        var c=resume();var r=NativeOwnerSnapshotMain268.currentSupermanSavedBaselineConfig(c);
        assertEquals("D:/health-resume-DATA/current-superman-health-progress.json",r.path());assertEquals(19786,r.bytes());assertEquals("2".repeat(64),r.sha256());
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_SUPERMAN_HEALTH_RESUME_SAVED_BASELINE_AND_BEGIN,NativeOwnerSnapshotMain268.observationMode(c));
    }
    @Test void eachRequiredFieldMustBePresent()throws IOException {
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","baseline_progress")) {
            var c=resume();c.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(c),field);
        }
    }
    @Test void referenceIsExactObjectAndDoesNotAcceptBooleanBytesOrLooseIdentity()throws IOException {
        for(var c:List.of(resume().putNull("baseline_progress"),resume().put("baseline_progress",true),resume().put("baseline_progress","D:/progress.json")))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(c));
        for(String field:List.of("path","bytes","sha256")){var c=resume();((ObjectNode)c.get("baseline_progress")).remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(c));}
        for(var ref:List.of(StrictJson.object().put("path","D:/a.json").put("bytes",true).put("sha256","2".repeat(64)),
                new ExactRef("relative.json",12,"2".repeat(64)).toJson(),new ExactRef("D:/empty.json",0,"2".repeat(64)).toJson(),
                new ExactRef("D:/huge.json",1L<<30,"2".repeat(64)).toJson(),new ExactRef("D:/a.json",12,"2".repeat(64)).toJson().put("permission",true))) {
            var c=resume();c.set("baseline_progress",ref);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(c));
        }
    }
    @Test void cannotAddSaveFieldsOrConfiguredWitnessPermissionToResume()throws IOException {
        for(String field:List.of("checkpoint_archive_path","maximum_checkpoint_bytes","checkpoint_observation_attempts","checkpoint_poll_interval_ms", "previous_checkpoint_source","previous_checkpoint_archive",
                "baseline_saved","physical_save_confirmed","source","archive","phase","event_id","option_key","instance_id","expected_core","provider_generation","query_sequence","deadline","save_calls"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(resume().put(field,1)),field);
    }
    @Test void oldSchemasCannotBorrowProgressAndNewSchemaCannotDispatchOldSaveMode()throws IOException {
        for(int v:List.of(1,14,24,25,26,27,28,29,30,31,32,33,34,35))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(resume().put("schema","xar.native-owner-snapshot-config/v"+v)));
        for(String mode:List.of("current_core_checkpoint_save","current_superman_health_baseline_save_and_begin","current_superman_health_query","current_superman_health_completed_close","current_superman_health_resume_saved_baseline_and_begin "))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(resume().put("mode",mode)));
    }
    @Test void newWorkflowStartsWithZeroSavesAndNoInventedCompletionOrPhysicalCredit()throws IOException {
        var n=StrictJson.object();NativeOwnerSnapshotMain268.initializeSupermanSavedBaselineResult(n,resume(),"java-data");
        assertEquals("current_superman_health_resume_saved_baseline_and_begin",n.path("mode").asText());assertEquals("baseline",n.path("phase").asText());
        for(String field:List.of("read_calls","choose_calls","save_calls"))assertEquals(0,n.path(field).asInt(-1),field);
        for(String field:List.of("query_available","known_choice_dispatched","baseline_physical_material_observed","baseline_source_restored_from_progress","native_returned","native_handled","event_closed","health_changed","trait_UI_rendered","new_date_observed","physical_save_confirmed"))assertFalse(n.path(field).asBoolean(true),field);
    }
    @Test void commonOwnerAndTimeoutContractsRemainStrict()throws IOException {
        var badOwner=resume();((ObjectNode)badOwner.get("owner_descriptor")).put("bytes",true);
        for(var c:List.of(badOwner,resume().put("overall_timeout_seconds",0),resume().put("overall_timeout_seconds",601),resume().put("read_timeout_seconds",61),resume().put("maximum_frames_per_operation",0)))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(c));
        var old=resume();old.remove("baseline_progress");old.put("schema","xar.native-owner-snapshot-config/v35").put("mode","current_superman_health_query").put("phase","baseline");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_SUPERMAN_HEALTH_QUERY,NativeOwnerSnapshotMain268.observationMode(old));
    }
}
