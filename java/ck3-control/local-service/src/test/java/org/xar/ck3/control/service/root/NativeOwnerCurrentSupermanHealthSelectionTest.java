package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentSupermanHealth;
import org.xar.ck3.control.nativebridge.CurrentSupermanHealthSource;
import org.xar.ck3.control.nativebridge.CurrentSupermanHealthResult;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA only; no fixture/Native/live claim and no private baseline permission is minted here. */
final class NativeOwnerCurrentSupermanHealthSelectionTest {
    private static ObjectNode common(String mode) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v35").put("mode",mode)
                .put("overall_timeout_seconds",180).put("read_timeout_seconds",60).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/superman-health-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static ObjectNode query(String phase){return common("current_superman_health_query").put("phase",phase);}
    private static ObjectNode close(){return common("current_superman_health_completed_close");}
    private static ObjectNode begin(){return common("current_superman_health_baseline_save_and_begin").put("checkpoint_archive_path","D:/superman-health-DATA/baseline.ck3").put("maximum_checkpoint_bytes",1L<<30).put("checkpoint_observation_attempts",64).put("checkpoint_poll_interval_ms",500);}
    private static FileWitness witness(String path,long bytes,String sha,String id){return new FileWitness(new ExactRef(path,bytes,sha),new FileStatIdentity(BigInteger.valueOf(bytes),id,"1700000000000000000"));}
    private static CoreFrame.Prefix core(int date){return new CoreFrame.Prefix(date,1,true,0,true,true,42,true);}
    private static List<CurrentSupermanHealthSource.HealthCharacter> characters(long health) {
        var rows=new ArrayList<CurrentSupermanHealthSource.HealthCharacter>();
        for(int i=0;i<40;i++) {
            var values=new LinkedHashMap<String,Long>();for(String key:CurrentSupermanHealthSource.VALUE_NAMES)values.put(key,0L);
            values.put("sxad_health_value",health);values.put("sxad_health_balance_value",Long.MAX_VALUE);
            int id=i==0?42:i==1?0:i==2?Integer.MIN_VALUE:100+i;
            rows.add(new CurrentSupermanHealthSource.HealthCharacter(CurrentSupermanHealthSource.CASE_KEYS.get(i/2),i%2==0?CurrentSupermanHealthSource.Role.RECEIVER:CurrentSupermanHealthSource.Role.DONOR,id,values));
        }
        return rows;
    }
    private static CurrentSupermanHealthSource source(CurrentSupermanHealth.Phase phase,boolean event,boolean admitted,long health) {
        return new CurrentSupermanHealthSource(phase,true,phase==CurrentSupermanHealth.Phase.BASELINE?Optional.of(100000L):Optional.empty(),
                phase==CurrentSupermanHealth.Phase.COMPLETED?Optional.of(100000L):Optional.empty(),40,characters(health),true,event?1:2,event,event,event,event,
                event?Optional.of(7):Optional.empty(),event?Optional.of(42):Optional.empty(),event?Optional.of(phase.eventKey()):Optional.empty(),
                event?Optional.of(""):Optional.empty(),event?Optional.of("#bold actual DATA #!"):Optional.empty(),event?Optional.of(1):Optional.empty(),
                event?List.of(new CurrentSupermanHealthSource.HealthOption(0,"","",true,Optional.of(phase.optionKey()))):List.of(),admitted);
    }
    private static CurrentSupermanHealthResult frame(CurrentSupermanHealth.Action action,CurrentSupermanHealthSource source,int provider,int query,int date,int connection) {
        boolean effect=action==CurrentSupermanHealth.Action.CHOOSE_KNOWN;
        return new CurrentSupermanHealthResult(action,effect?CurrentSupermanHealthResult.Status.KNOWN_CHOICE_DISPATCHED:CurrentSupermanHealthResult.Status.AVAILABLE,
                effect,effect,true,BigInteger.valueOf(provider),BigInteger.valueOf(query),effect?BigInteger.ONE:BigInteger.ZERO,Optional.of(core(date)),
                Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.TWO,BigInteger.valueOf(3),4)),Optional.of(source),Optional.empty(),source.phase());
    }
    private static CurrentSupermanHealthResult query(CurrentSupermanHealthSource source){return frame(CurrentSupermanHealth.Action.QUERY_HEALTH,source,1,2,1000,1);}
    @Test void queryPhaseAndTwoFixedWorkflowRolesStaySeparate()throws IOException {
        assertEquals(CurrentSupermanHealth.Phase.BASELINE,NativeOwnerSnapshotMain268.currentSupermanHealthConfig(query("baseline")).phase());
        assertEquals(CurrentSupermanHealth.Phase.COMPLETED,NativeOwnerSnapshotMain268.currentSupermanHealthConfig(query("completed")).phase());
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_SUPERMAN_HEALTH_QUERY,NativeOwnerSnapshotMain268.observationMode(query("baseline")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_SUPERMAN_HEALTH_BASELINE_SAVE_AND_BEGIN,NativeOwnerSnapshotMain268.observationMode(begin()));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_SUPERMAN_HEALTH_COMPLETED_CLOSE,NativeOwnerSnapshotMain268.observationMode(close()));
        assertEquals(CurrentSupermanHealth.Phase.BASELINE,NativeOwnerSnapshotMain268.currentSupermanHealthConfig(begin()).phase());
        assertEquals(CurrentSupermanHealth.Phase.COMPLETED,NativeOwnerSnapshotMain268.currentSupermanHealthConfig(close()).phase());
        assertThrows(IllegalArgumentException.class,()->new NativeOwnerSnapshotMain268.SupermanHealthConfig(NativeOwnerSnapshotMain268.SupermanHealthMode.BASELINE_SAVE_AND_BEGIN,CurrentSupermanHealth.Phase.COMPLETED));
    }
    @Test void missingMistypedPhaseOrConfiguredPhaseOnEffectModesIsRejected()throws IOException {
        for(var n:List.of(common("current_superman_health_query"),query("BASELINE"),query("baseline "),query("other"),query("baseline").putNull("phase"),query("baseline").put("phase",true),query("baseline").put("phase",1),begin().put("phase","baseline"),close().put("phase","completed")))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(common("current_superman_health_choose_known")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(common("current_superman_health_query_and_begin")));
    }
    @Test void baselineRequiresRealArchiveBoundsAndPairedPreviousWitnessObjects()throws IOException {
        for(String key:List.of("checkpoint_archive_path","maximum_checkpoint_bytes","checkpoint_observation_attempts","checkpoint_poll_interval_ms")){var n=begin();n.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));}
        for(var n:List.of(begin().put("checkpoint_archive_path","relative.ck3"),begin().put("maximum_checkpoint_bytes",true),begin().put("maximum_checkpoint_bytes",0),begin().put("maximum_checkpoint_bytes",(1L<<30)+1),begin().put("checkpoint_observation_attempts",65),begin().put("checkpoint_poll_interval_ms",99)))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        var unpaired=begin();unpaired.putObject("previous_checkpoint_source");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(unpaired));
        for(var n:List.of(begin().putNull("previous_checkpoint_source").putNull("previous_checkpoint_archive"),begin().put("previous_checkpoint_source",true).put("previous_checkpoint_archive",true)))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(query("baseline").put("checkpoint_archive_path","D:/unexpected.ck3")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(close().put("maximum_checkpoint_bytes",1)));
    }
    @Test void commonFilePinRejectsBoolBytesAndCallerCannotGrantBaselineOrChoose()throws IOException {
        var boolBytes=begin();((ObjectNode)boolBytes.get("owner_descriptor")).put("bytes",true);
        for(var n:List.of(boolBytes,close().put("owner_descriptor","D:/owner.json"),query("baseline").put("read_timeout_seconds",61),close().put("maximum_frames_per_operation",0),begin().put("overall_timeout_seconds",601)))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        for(String field:List.of("baseline_saved","physical_save_confirmed","baseline_ready_raw","matrix_done_raw","native_choice_admissible","event_id","event_key","option_key","option_index","instance_id","target_character_id","expected_core","provider_generation","query_sequence","claim_sequence","namespace","scope","action","deadline","save_calls","maximum_status_polls","status_poll_interval_ms"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(begin().put(field,1)),field);
    }
    @Test void oldV14RetainsItsOwnSaveModeAndCannotBorrowNewPhaseOrWorkflow()throws IOException {
        var old=begin().put("schema","xar.native-owner-snapshot-config/v14").put("mode","current_core_checkpoint_save");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CORE_CHECKPOINT_SAVE,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.deepCopy().put("phase","baseline")));
        for(int version:List.of(24,25,26,27,28,29,30,31,32,33,34))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(query("baseline").put("schema","xar.native-owner-snapshot-config/v"+version)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(begin().put("schema","xar.native-owner-snapshot-config/v14")));
    }
    @Test void matchingBytesCannotReplaceDistinctPhysicalArchiveIdentityOrExpectedPaths()throws IOException {
        Path checkpoint=Path.of("D:/superman-health-DATA/xar_checkpoint.ck3"),archive=Path.of("D:/superman-health-DATA/baseline.ck3");
        var source=witness(checkpoint.toString(),42,"1".repeat(64),"11");var copy=witness(archive.toString(),42,"1".repeat(64),"12");
        NativeOwnerSnapshotMain268.requireSupermanBaselineMaterial(source,copy,checkpoint,archive,42);
        var alias=witness(archive.toString(),42,"1".repeat(64),"11");assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireSupermanBaselineMaterial(source,alias,checkpoint,archive,42));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireSupermanBaselineMaterial(source,copy,checkpoint,checkpoint,42));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireSupermanBaselineMaterial(source,copy,checkpoint,Path.of("D:/other/baseline.ck3"),42));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireSupermanBaselineMaterial(source,copy,Path.of("relative.ck3"),archive,42));
    }
    @Test void emptyOversizeOrDifferentArchiveBytesNeverBecomeABaseline()throws IOException {
        Path checkpoint=Path.of("D:/superman-health-DATA/xar_checkpoint.ck3"),archive=Path.of("D:/superman-health-DATA/baseline.ck3");
        var source=witness(checkpoint.toString(),42,"1".repeat(64),"11");
        for(var copy:List.of(witness(archive.toString(),41,"1".repeat(64),"12"),witness(archive.toString(),42,"2".repeat(64),"12")))assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireSupermanBaselineMaterial(source,copy,checkpoint,archive,42));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireSupermanBaselineMaterial(source,witness(archive.toString(),42,"1".repeat(64),"12"),checkpoint,archive,41));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireSupermanBaselineMaterial(witness(checkpoint.toString(),0,"0".repeat(64),"11"),witness(archive.toString(),0,"0".repeat(64),"12"),checkpoint,archive,42));
    }
    @Test void completeFixtureDataOrEventAbsenceCannotInferChoicePermission()throws IOException {
        var phase=CurrentSupermanHealth.Phase.BASELINE;var absent=source(phase,false,false,75);
        NativeOwnerSnapshotMain268.requireCurrentSupermanHealthQueryFrame(query(absent),core(1000),phase);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentSupermanHealthChoiceSource(query(absent),phase));
        var denied=source(phase,true,false,75);assertTrue(denied.options().getFirst().nativeCanSelect());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentSupermanHealthChoiceSource(query(denied),phase));
        var partial=new LinkedHashMap<>(characters(75).getFirst().values());partial.remove("sxad_health_value");
        assertThrows(IllegalArgumentException.class,()->new CurrentSupermanHealthSource.HealthCharacter(CurrentSupermanHealthSource.CASE_KEYS.getFirst(),CurrentSupermanHealthSource.Role.RECEIVER,42,partial));
        var raw=StrictJson.parse(query(absent).encode().bytes(),1<<20);assertTrue(raw.get("source").get("matrix_done_raw").isNull());assertEquals(40,raw.get("source").get("reference_count").intValue());
    }
    @Test void fullSourceCorePhaseAndPrivateLeaseDriftCannotQualifyAKnownReply()throws IOException {
        var phase=CurrentSupermanHealth.Phase.BASELINE;var s=source(phase,true,true,75);var q=query(s);
        NativeOwnerSnapshotMain268.requireCurrentSupermanHealthDispatchFrame(q,frame(CurrentSupermanHealth.Action.CHOOSE_KNOWN,s,1,2,1000,1),phase);
        for(var d:List.of(frame(CurrentSupermanHealth.Action.CHOOSE_KNOWN,s,2,2,1000,1),frame(CurrentSupermanHealth.Action.CHOOSE_KNOWN,s,1,3,1000,1),frame(CurrentSupermanHealth.Action.CHOOSE_KNOWN,s,1,2,1001,1),frame(CurrentSupermanHealth.Action.CHOOSE_KNOWN,s,1,2,1000,2),frame(CurrentSupermanHealth.Action.CHOOSE_KNOWN,source(phase,true,true,76),1,2,1000,1),frame(CurrentSupermanHealth.Action.CHOOSE_KNOWN,source(CurrentSupermanHealth.Phase.COMPLETED,true,true,75),1,2,1000,1),q))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentSupermanHealthDispatchFrame(q,d,phase));
        var refused=new CurrentSupermanHealthResult(CurrentSupermanHealth.Action.CHOOSE_KNOWN,CurrentSupermanHealthResult.Status.STALE_SOURCE,false,false,true,BigInteger.ONE,BigInteger.TWO,BigInteger.ONE,q.factsBefore(),q.owner(),q.source(),Optional.of("actual_stale_DATA"),phase);
        assertFalse(refused.successful());assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentSupermanHealthDispatchFrame(q,refused,phase));
    }
    @Test void signedIdsRawValuesAndVoidFlagsAreRetainedInBothFixedPhases()throws IOException {
        for(var phase:CurrentSupermanHealth.Phase.values()) {
            var s=source(phase,true,true,Long.MIN_VALUE);var q=query(s);var d=frame(CurrentSupermanHealth.Action.CHOOSE_KNOWN,s,1,2,1000,1);
            NativeOwnerSnapshotMain268.requireCurrentSupermanHealthDispatchFrame(q,d,phase);
            assertEquals(0,s.characters().get(1).characterId());assertEquals(Integer.MIN_VALUE,s.characters().get(2).characterId());
            var raw=StrictJson.parse(d.encode().bytes(),1<<20);var values=raw.get("source").get("characters").get(0).get("values");
            assertEquals(Long.toString(Long.MIN_VALUE),values.get("sxad_health_value").textValue());assertEquals(Long.toString(Long.MAX_VALUE),values.get("sxad_health_balance_value").textValue());
            for(String key:List.of("native_handled","event_closed","health_changed","trait_UI_rendered","new_date_observed","physical_save_confirmed"))assertFalse(raw.get(key).booleanValue(),key);
        }
    }
}
