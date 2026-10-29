package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeColdAdoptionProjection;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.ColdRestoreDriverLineage;
import static org.junit.jupiter.api.Assertions.*;

/** Preserved small source bytes plus synthetic measured metadata; never constructs an authority or reads persistence. */
final class RawRestoreAdmissionReducerTest {
    private record Fixture(RecoveryEvidence basis,ObjectNode receipt,ColdRestoreDriverLineage lineage,
            FileStatIdentity identity,RootColdResumeSession.RawColdFrame raw) { }
    @Test void unchangedClosedDriverPermitsOnlyBootstrapAndPreservesT0Unknowns() throws IOException {
        var f=fixture();byte[] before=f.basis().bytes();var preview=reduce(f);
        assertEquals(RawRestoreAdmissionReducer.DriverBranch.ACTUAL_PENDING_COLD_WITH_UNCHANGED_CLOSED_DRIVER,preview.branch());
        assertEquals("native-40526-1bec95182886",preview.episodeRunId());assertEquals(5628,preview.elapsedGameDays());
        assertEquals(0,preview.newGameDayCredit());assertEquals(0,preview.newOrdinaryCycleCredit());
        assertFalse(preview.grantsWarmAttachment());assertFalse(preview.originalActionsReplayed());
        assertTrue(Arrays.equals(before,f.basis().bytes()));assertEquals(3,StrictJson.parse(before).get("unknown_requests").size());
    }
    @Test void actualNewGameHeaderCanHaveNewDriverHashWithoutChangingEpisode() throws IOException {
        var f=fixture();f.receipt().set("driver_ref",new ExactRef(ExactRef.fromJson(f.receipt().get("driver_ref")).path(),f.identity().bytes().longValueExact(),"1".repeat(64)).toJson());
        var current=new ColdRestoreDriverLineage(f.raw().game().pid(),f.lineage().episodeCharacterId(),f.lineage().episodeRunId(),f.lineage().successionLifecycle());
        var preview=RawRestoreAdmissionReducer.preview(f.basis(),evidence(f.receipt(),"synthetic-current-header.json"),current,f.identity(),f.raw());
        assertEquals(RawRestoreAdmissionReducer.DriverBranch.ACTUAL_CURRENT_GAME_HEADER,preview.branch());
    }
    @Test void changedOldHeaderIsUnavailable() throws IOException {
        var f=fixture();f.receipt().set("driver_ref",new ExactRef(ExactRef.fromJson(f.receipt().get("driver_ref")).path(),f.identity().bytes().longValueExact(),"2".repeat(64)).toJson());
        assertThrows(IllegalArgumentException.class,()->reduce(f));
    }
    @Test void newEpisodeNeverBecomesOldEpisodeByExpectedFrame() throws IOException {
        var f=fixture();var changed=new ColdRestoreDriverLineage(f.raw().game().pid(),40526,"native-new-unqualified",f.lineage().successionLifecycle());
        assertThrows(IllegalArgumentException.class,()->RawRestoreAdmissionReducer.preview(f.basis(),evidence(f.receipt(),"synthetic-episode.json"),changed,f.identity(),f.raw()));
    }
    @Test void checkpointBooleanDateIsRejected() throws IOException {
        var f=fixture();((ObjectNode)f.receipt().get("checkpoint")).put("date_raw",true);assertThrows(IllegalArgumentException.class,()->reduce(f));
    }
    @Test void checkpointFloatDateIsRejected() throws IOException {
        var f=fixture();((ObjectNode)f.receipt().get("checkpoint")).put("date_raw",53279400.0);assertThrows(IllegalArgumentException.class,()->reduce(f));
    }
    @Test void checkpointHistoryCannotDrift() throws IOException {
        var f=fixture();((ObjectNode)f.receipt().get("checkpoint")).put("history_index",5945);assertThrows(IllegalArgumentException.class,()->reduce(f));
    }
    @Test void allSixLifecycleFieldsBindCurrentHeaderAndCheckpoint() throws IOException {
        var f=fixture();((ObjectNode)f.receipt().get("checkpoint").get("succession_lifecycle")).put("xar_enabled",false);
        assertThrows(IllegalArgumentException.class,()->reduce(f));
    }
    @Test void unknownReplayIsNeverAllowedByRawFrame() throws IOException {
        var f=fixture();var old=(ObjectNode)StrictJson.parse(f.basis().bytes());((ObjectNode)old.get("unknown_requests").get(0)).put("replayed",true);
        assertThrows(IllegalArgumentException.class,()->RawRestoreAdmissionReducer.preview(evidence(old,"synthetic-replayed-basis.json"),
                evidence(f.receipt(),"synthetic-replayed-measurement.json"),f.lineage(),f.identity(),f.raw()));
    }
    @Test void rawUInt64IsAStringAndFrameCannotAdvanceDate() throws IOException {
        var f=fixture();assertTrue(f.raw().toJson().get("connection_generation").isTextual());
        var raw=new RootColdResumeSession.RawColdFrame("native:2",3,2,53279424,40526,true,true,f.raw().game(),f.raw().pipeName(),"18446744073709551615","a".repeat(64),2,f.raw().ownerColdAdoption());
        assertThrows(IllegalArgumentException.class,()->RawRestoreAdmissionReducer.preview(f.basis(),evidence(f.receipt(),"synthetic-future-frame.json"),f.lineage(),f.identity(),raw));
    }
    @Test void expectedEpisodeAndRawMetadataCannotReplaceTheActualPendingOwnerProducer() throws IOException {
        var f=fixture();var owner=StrictJson.object();owner.put("schema",NativeColdAdoptionProjection.SCHEMA);owner.put("binding_state","unbound");
        owner.put("session_bridge_pid",f.raw().game().pid());owner.putNull("restore_kind");owner.putNull("rejection");owner.putNull("pending");
        assertThrows(IllegalArgumentException.class,()->reduceWithOwner(f,owner));
        var current=new ColdRestoreDriverLineage(f.raw().game().pid(),f.lineage().episodeCharacterId(),f.lineage().episodeRunId(),f.lineage().successionLifecycle());
        var raw=withOwner(f,NativeColdAdoptionProjection.fromJson(owner));
        assertThrows(IllegalArgumentException.class,()->RawRestoreAdmissionReducer.preview(f.basis(),evidence(f.receipt(),"synthetic-unbound-current-header.json"),current,f.identity(),raw));
    }
    @Test void actualPendingMustBindHeldGameOriginalProducerAndCompleteOldCheckpoint() throws IOException {
        var f=fixture();var wrong=f.raw().ownerColdAdoption().toJson();wrong.put("session_bridge_pid",3333);
        assertThrows(IllegalArgumentException.class,()->reduceWithOwner(f,wrong));
        var rejected=f.raw().ownerColdAdoption().toJson();rejected.put("rejection","no_complete_checkpoint_anchor");
        assertThrows(IllegalArgumentException.class,()->reduceWithOwner(f,rejected));
        var notReady=f.raw().ownerColdAdoption().toJson();((ObjectNode)notReady.get("pending")).put("original_cold_ready",false);
        assertThrows(IllegalArgumentException.class,()->reduceWithOwner(f,notReady));
        var episode=f.raw().ownerColdAdoption().toJson();((ObjectNode)episode.get("pending")).put("episode_run_id","fabricated-new-episode");
        assertThrows(IllegalArgumentException.class,()->reduceWithOwner(f,episode));
        var checkpoint=f.raw().ownerColdAdoption().toJson();((ObjectNode)checkpoint.get("pending").get("last_checkpoint")).put("sha256","f".repeat(64));
        assertThrows(IllegalArgumentException.class,()->reduceWithOwner(f,checkpoint));
    }
    @Test void actualPendingSelectedAnchorCannotBeForgedByReadyTrueOrJacksonIntegerNodeKinds() throws IOException {
        var f=fixture();assertDoesNotThrow(()->reduceWithOwner(f,(ObjectNode)StrictJson.parse(StrictJson.canonical(f.raw().ownerColdAdoption().toJson()))));
        for(String field:java.util.List.of("index","command","ok","result_checkpoint")) {
            var owner=f.raw().ownerColdAdoption().toJson();var selected=(ObjectNode)owner.get("pending").get("checkpoint_anchor");
            switch(field) {
                case "index" -> selected.put("index",1);
                case "command" -> selected.put("command","unqualified-save-command");
                case "ok" -> selected.put("ok",false);
                case "result_checkpoint" -> ((ObjectNode)selected.get(field)).put("sha256","f".repeat(64));
                default -> throw new AssertionError(field);
            }
            assertThrows(IllegalArgumentException.class,()->reduceWithOwner(f,owner));
        }
    }
    private static RawRestoreAdmissionReducer.Preview reduceWithOwner(Fixture f,ObjectNode owner) {
        return RawRestoreAdmissionReducer.preview(f.basis(),evidence(f.receipt(),"synthetic-owner-measurement.json"),f.lineage(),f.identity(),
                withOwner(f,NativeColdAdoptionProjection.fromJson(owner)));
    }
    private static RootColdResumeSession.RawColdFrame withOwner(Fixture f,NativeColdAdoptionProjection owner) {
        var raw=f.raw();return new RootColdResumeSession.RawColdFrame(raw.snapshotId(),raw.publicRevision(),raw.nativeRevision(),raw.dateRaw(),raw.actorCharacterId(),
                raw.mapReady(),raw.paused(),raw.game(),raw.pipeName(),raw.connectionGeneration(),raw.responseSha256(),raw.arrivalSequence(),owner);
    }
    private static RawRestoreAdmissionReducer.Preview reduce(Fixture f) {
        return RawRestoreAdmissionReducer.preview(f.basis(),evidence(f.receipt(),"synthetic-current-measurement.json"),f.lineage(),f.identity(),f.raw());
    }
    private static Fixture fixture() throws IOException {
        byte[] bytes;try(var input=RawRestoreAdmissionReducerTest.class.getResourceAsStream("/n46-prior-basis.actual.json")) {
            if(input==null){throw new IOException("preserved finite source fixture required");}bytes=input.readAllBytes();
        }
        assertEquals("4b53ffa1a422df36cd18d29f47737fed8417a257ff42d2dc4b7093de56d27afa",RecoveryEvidence.sha256(bytes));
        var basis=new RecoveryEvidence(new ExactRef(Path.of("synthetic-prior-basis-source.json").toAbsolutePath().toString(),bytes.length,RecoveryEvidence.sha256(bytes)),bytes);
        ObjectNode old=(ObjectNode)StrictJson.parse(bytes);ObjectNode anchor=(ObjectNode)old.get("checkpoint");
        ObjectNode checkpoint=anchor.deepCopy();checkpoint.remove("load_save_name");checkpoint.put("date_raw",checkpoint.remove("saved_date_raw").longValue());
        checkpoint.put("episode_character_id",40526);checkpoint.put("episode_run_id","native-40526-1bec95182886");
        var receipt=StrictJson.object();receipt.put("schema","xar.current-saved-recovery-checkpoint-qualification/v1");receipt.put("status","ORIGINAL_SDK_SAVED_CHECKPOINT_QUALIFIED");
        receipt.put("machine_id",StrictJson.text(old.get("machine_id")));receipt.set("driver_ref",old.get("refs").get("driver"));
        receipt.set("save_ref",old.get("refs").get("save"));receipt.set("driver_identity_before",old.get("driver_identity"));receipt.set("driver_identity_after",old.get("driver_identity"));
        receipt.set("checkpoint",checkpoint);receipt.put("pipe_name","synthetic-original-pipe");
        for(String field:java.util.List.of("driver_physical_body_reads","driver_payload_reader_calls","original_validator_calls","save_sha256_calls")){receipt.put(field,1);}
        receipt.put("driver_body_rewritten",false);receipt.put("ledger_write_already_performed",false);receipt.put("game_or_RPC_calls",0);
        var lineage=new ColdRestoreDriverLineage(1111,40526,"native-40526-1bec95182886",(ObjectNode)anchor.get("succession_lifecycle"));
        var game=new WindowsJobProcess.ProcessIdentity(2222,"133700000000000000",Path.of("synthetic-game.exe").toAbsolutePath().toString());
        var pending=StrictJson.object();pending.put("format_version",2);pending.put("bridge_pid",1111);pending.put("episode_character_id",40526);
        pending.put("episode_run_id","native-40526-1bec95182886");pending.set("succession_lifecycle",anchor.get("succession_lifecycle"));pending.set("last_checkpoint",checkpoint.deepCopy());
        pending.put("command_history_length",5944);pending.put("original_cold_ready",true);var selected=StrictJson.object();selected.put("index",5944);
        selected.put("command","save-checkpoint");selected.put("ok",true);selected.set("result_checkpoint",checkpoint.deepCopy());pending.set("checkpoint_anchor",selected);
        var owner=StrictJson.object();owner.put("schema",NativeColdAdoptionProjection.SCHEMA);owner.put("binding_state","pending_cold_candidate");owner.put("session_bridge_pid",2222);
        owner.putNull("restore_kind");owner.putNull("rejection");owner.set("pending",pending);
        var raw=new RootColdResumeSession.RawColdFrame("native:1",2,1,53279400,40526,true,true,game,"synthetic-original-pipe","18446744073709551615","a".repeat(64),1,NativeColdAdoptionProjection.fromJson(owner));
        return new Fixture(basis,receipt,lineage,FileStatIdentity.fromJson(old.get("driver_identity"),FileStatIdentity.SCHEMA),raw);
    }
    private static RecoveryEvidence evidence(ObjectNode object,String name) {
        byte[] bytes=StrictJson.canonical(object);return new RecoveryEvidence(new ExactRef(Path.of(name).toAbsolutePath().toString(),bytes.length,RecoveryEvidence.sha256(bytes)),bytes);
    }
}
