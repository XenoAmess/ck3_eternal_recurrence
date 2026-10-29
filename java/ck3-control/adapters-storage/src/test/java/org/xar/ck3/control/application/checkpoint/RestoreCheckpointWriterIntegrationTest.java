package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** A manual pair and shaped basis never mint the original store's private saved material. */
public final class RestoreCheckpointWriterIntegrationTest {
    @TempDir Path temporary;
    private record Fixture(NativeCheckpointFiles files,DriverCheckpointStore drivers,CheckpointPair pair,
            CheckpointRequest.Readiness current,RestoreCheckpointService.NativeCandidate loaded,
            ContinuityWriter writer,WriterContracts.Request request) { }
    private Fixture fixture() throws Exception {
        var files=new NativeCheckpointFiles();var oldGame=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133000000000000001")));
        var newGame=new GameGeneration(124,new PythonOnlyUInt64(new BigInteger("133000000000000002")));
        var frame=new ObservationIdentity("test-machine-1",oldGame,new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(
                BigInteger.valueOf(29829),BigInteger.ONE,BigInteger.valueOf(240)),"native:1",BigInteger.ONE,"episode-1"),1);
        Path save=temporary.resolve("xar_checkpoint.ck3");Files.writeString(save,"real temporary SAVE input");
        var state=new AtomicReference<>(DriverStateSnapshot.decodeComplete(("{\"format_version\":2,\"pipe_name\":\"test-pipe\",\"bridge_pid\":123,\"episode_character_id\":29829,\"episode_run_id\":\"episode-1\","
                +"\"command_history\":[],\"last_checkpoint\":null,\"rollback_war_failure\":null,\"managed_restore_transaction\":null,\"succession_expectation\":null,\"succession_lifecycle\":null,\"campaign_goal\":null,\"rollback_war_failures\":[]}").getBytes(StandardCharsets.UTF_8)));
        var drivers=new DriverCheckpointStore(files,temporary.resolve("driver.json"),"test-pipe",new DriverCheckpointStore.SnapshotSupplier(){
            public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work)throws IOException {
                synchronized(state){return work.run(state.get(),(before,after)->{assertTrue(state.compareAndSet(before,after));});}
            }
        });
        var saveRef=files.observe(save).orElseThrow();var anchor=drivers.persist("save-test-1",saveRef,frame,"lineage-1");
        var ack=files.createNew(temporary.resolve("ack.json"),"{\"ok\":true}".getBytes(StandardCharsets.UTF_8)).reference();
        var pair=new CheckpointPair(saveRef,anchor.driver(),frame,"lineage-1",anchor.historyIndex(),"save-test-1",ack,Instant.now());
        var source=new G2Source("test-machine-1","2026-10-23T15:00:00Z","test-build",ack);
        var ready=new CheckpointRequest.Readiness(frame,source,"old-session","lineage-1",true,true,true,"test_native_ready",ack,Instant.now());
        var rawState=StrictJson.object();rawState.put("paused",true);rawState.put("map_ready",true);rawState.put("date_raw",240);
        var player=rawState.putObject("played_character");player.put("character_id",29829);player.put("alive",true);
        var packet=StrictJson.object();packet.put("type","state_snapshot");packet.put("protocol_version",1);packet.put("snapshot_id","native:1");packet.put("revision",1);packet.set("state",rawState);
        byte[] json=StrictJson.canonical(packet),framed=ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
        var rawRef=files.createNew(temporary.resolve("restored-raw.bin"),framed).reference();
        var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine-1",newGame,BigInteger.ONE,"new-session"),
                "native:1",BigInteger.ONE,new RawJson(StrictJson.canonical(rawState)),framed,Instant.now());
        var candidate=new RestoreCheckpointService.NativeCandidate(actual,source,"lineage-1",rawRef);
        var predecessor=StrictJson.object();predecessor.put("schema","root.ck3.continuity-window/v1");predecessor.put("machine_id","test-machine-1");
        predecessor.put("sequence",0);predecessor.put("window_id",1);predecessor.put("start_date_raw",0);predecessor.put("target_date_raw",240);
        predecessor.put("target_days",10);predecessor.put("status","running");predecessor.put("last_settled_cycles",0);predecessor.put("last_settled_date_raw",0);
        var pending=predecessor.putObject("pending_cycle");pending.put("stage","auto_unsettled");pending.put("auto_sequence",11558);predecessor.put("NEXT",11559);
        var old=ContinuityState.fromJson(predecessor,"test-machine-1");
        var details=StrictJson.object();details.put("evidence_id","restore-fixture-1");details.put("source","actual-temporary-pair");
        details.put("new_ordinary_cycle_credit",0);details.put("game_day_credit",0);details.put("original_actions_replayed",false);details.put("window_origin_reset",false);
        details.set(SavedAttachmentAuthority.PAIR_DETAIL,StrictJson.parse(CheckpointPairCodec.encode(pair)));
        var basis=StrictJson.object();basis.put("machine_id","test-machine-1");basis.put("completed_cycles",0);
        var origin=basis.putObject("origin");origin.put("start_date_raw",0);origin.put("target_date_raw",240);
        var originalFrame=basis.putObject("frame");originalFrame.put("snapshot_id","native:1");originalFrame.put("revision",1);originalFrame.put("native_revision",1);
        originalFrame.put("date_raw",240);originalFrame.put("actor_character_id",29829);originalFrame.put("episode_run_id","episode-1");
        var refs=basis.putObject("refs");refs.set("driver",pair.driver().reference().toJson());refs.set("save",pair.save().reference().toJson());refs.set("settled_full_response",ack.toJson());
        basis.put("identity_schema",FileStatIdentity.SCHEMA);basis.set("driver_identity",pair.driver().identity().toJson());basis.set("save_identity",pair.save().identity().toJson());
        var checkpoint=basis.putObject("checkpoint");checkpoint.put("path",pair.save().reference().path());checkpoint.put("size",pair.save().reference().bytes());
        checkpoint.put("sha256",pair.save().reference().sha256());checkpoint.put("history_index",pair.historyIndex());checkpoint.put("saved_date_raw",240);
        var goal=basis.putObject("campaign_goal_anchor");goal.put("campaign_id","lineage-1");goal.put("current_character_id",29829);
        var progress=StrictJson.object();progress.put("ledger_cycles",0);progress.put("ledger_date_raw",0);
        var input=new SavedContinuityAttachment.Input(old,StrictJson.canonical(details),StrictJson.canonical(basis),StrictJson.canonical(newGame.toJson()),
                StrictJson.canonical(originalFrame),StrictJson.canonical(progress));
        var request=new WriterContracts.Request(SavedAttachmentAuthority.KIND,StrictJson.canonical(details),List.of(rawRef,ack));
        var authority=new SavedAttachmentAuthority(drivers,(head,actualRequest)->{
            throw new IOException("actual private saved material and original source loader are unavailable");
        });
        Path ledger=temporary.resolve("ROOT-CONTINUITY-WINDOW.json"),anchorPath=temporary.resolve("anchor.json");
        Files.write(ledger,StrictJson.canonical(predecessor));var originRef=files.createNew(anchorPath,StrictJson.canonical(predecessor)).reference();
        Files.createFile(temporary.resolve("ROOT-CONTINUITY-WINDOW.lock"));Files.createDirectory(temporary.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        var sourceRef=files.createNew(temporary.resolve("source.txt"),"reviewed temporary source".getBytes(StandardCharsets.UTF_8)).reference();
        var layout=new WriterContracts.Layout(ledger,originRef,"test-machine-1");
        var storage=org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport.create(layout);
        var writer=new ContinuityWriter(layout,List.of(sourceRef),authority,storage);
        return new Fixture(files,drivers,pair,ready,candidate,writer,request);
    }
    @Test void manualPhysicalPairAndConstructedBasisCannotReplaceActualPrivateSourceMaterial()throws Exception {
        var f=fixture();
        f.writer().locked(same->{
            String before=same.head().digest();
            IOException refused=assertThrows(IOException.class,()->same.preview(f.request()));
            assertTrue(refused.getMessage().contains("private saved material"));
            assertEquals(before,same.head().digest());assertEquals(0,same.head().state().sequence());return null;
        });
        assertThrows(NullPointerException.class,()->new RestoreCheckpointService.Request("manual-restore",f.pair(),f.current(),
                "0".repeat(64),Instant.now().plusSeconds(20),null));
    }
}
