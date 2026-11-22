package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Small physical DATA and actual NoGame transport custody; no Game/save/health business qualification. */
class NativeSupermanHealthBaselineRecoveryTest {
    record Data(Path root,ExactRef owner,FileWitness[] pair,ObjectNode progress) {
        ExactRef seal()throws IOException{return write(root.resolve("progress.json"),StrictJson.canonical(progress));}
        SupermanHealthBaselineReceipt load()throws IOException{return SupermanHealthBaselineReceipt.load(seal(),owner,pair[0],pair[1]);}
    }
    static ExactRef write(Path path,byte[] raw)throws IOException {Files.write(path,raw);return new ExactRef(path.toString(),raw.length,ActionCodec.sha256(raw));}
    static ObjectNode material(Path root,String name,byte[] raw)throws IOException {return StrictJson.object().set("reference",write(root.resolve(name),raw).toJson());}
    static ObjectNode archived(Path root,String name,NativeActionPort.AckReceived ack)throws IOException {
        var row=StrictJson.object().put("class","AckReceived").put("native_ok",ack.nativeOk()).put("request_id",ack.requestId());
        row.set("ack_packet",material(root,name+"-ack.bin",ack.originalPacket()));row.set("outbound",material(root,name+"-request.bin",ack.outbound().orElseThrow().originalPacket()));
        row.set("result_token",material(root,name+"-token.json",ack.originalResultToken().orElseThrow().bytes()));row.set("ack_payload",material(root,name+"-payload.json",ack.originalFrame().bytes()));
        var c=ack.custody().orElseThrow();var custody=StrictJson.object().put("request_id",ack.requestId()).put("custody_epoch",c.custodyEpoch().toString());
        var session=custody.putObject("session").put("machine_id",c.session().machineId()).put("session_id",c.session().sessionId()).put("connection_generation",c.session().connectionGeneration().toString());session.set("game",c.session().game().toJson());
        custody.putObject("original_request").put("bytes",c.originalRequest().bytes()).put("sha256",c.originalRequest().sha256());
        custody.putObject("original_response").put("bytes",c.originalResponse().bytes()).put("sha256",c.originalResponse().sha256());
        for(var entry:java.util.Map.of("write_entered",c.writeEntered(),"write_completed",c.writeCompleted(),"response_received",c.responseReceived()).entrySet())custody.putObject(entry.getKey()).put("order",entry.getValue().order().toString()).put("observed_at_utc",entry.getValue().observedAt().toString());
        row.set("actual_custody",custody);row.set("custody_material",material(root,name+"-custody.json",StrictJson.canonical(custody)));return row;
    }
    static Data data()throws Exception {
        Path root=Files.createTempDirectory("health-recovery-data-");var pair=NativeCurrentSupermanHealthTransportTest.actualSmallPair();var owner=write(root.resolve("owner.json"),new byte[]{1,2,3});
        var r=new NativeCurrentSupermanHealthTransportTest.Replay("known",CurrentSupermanHealth.Phase.BASELINE);
        try(var t=NativeCurrentSupermanHealthTransportTest.transport(r)) {
            var before=NativeCurrentSupermanHealthTransportTest.core(t);var saved=t.prepareCurrentCoreCheckpoint(before,before.validUntil());
            var save=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCoreCheckpoint(saved));
            var row=StrictJson.object().put("schema","xar.native-owner-current-superman-health/v1").put("mode","current_superman_health_baseline_save_and_begin")
                    .put("save_calls",1).put("choose_calls",0).put("read_calls",2).put("baseline_physical_material_observed",true).put("query_available",false).put("known_choice_dispatched",false);
            row.set("owner_descriptor",owner.toJson());var cp=row.putObject("baseline_checkpoint").put("save_calls",1).put("save_dispatch_class","AckReceived").put("native_checkpoint_status","submitted")
                    .put("changed_physical_material_observed",true).put("archive_is_copy_not_another_SAVE",true).put("save_request_id",save.requestId())
                    .put("source_date_raw",((CoreFrame.Partial)before.frame()).prefix().dateRaw()).put("save_deadline_utc",saved.deadline().toString());
            for(int i=0;i<2;i++){var w=StrictJson.object();w.set("reference",pair[i].reference().toJson());w.set("identity",pair[i].identity().toJson());cp.set(i==0?"checkpoint_source":"checkpoint_immutable_archive",w);}
            var originals=row.putObject("originals");var originalSave=originals.putObject("baseline_checkpoint");originalSave.set("core_dispatch",archived(root,"core",before.original()));originalSave.set("save_dispatch",archived(root,"save",save));
            var failure=originals.putObject("core_dispatch").put("class","Unknown").put("failure_kind","FRAME_BUDGET_EXHAUSTED").put("failure_stage","RESPONSE_WAIT");
            failure.set("outbound",material(root,"failed-core.bin",before.original().outbound().orElseThrow().originalPacket()));return new Data(root,owner,pair,row);
        }
    }
    @Test void exactAcceptedArchiveCanRestoreDataWithoutAnotherSaveOrOldCorePermit()throws Exception {
        var d=data();var receipt=d.load();var old=receipt.oldSession;
        var session=new NativeObservationPort.TransportSession(StrictJson.text(old.get("machine_id")),org.xar.ck3.control.contracts.GameGeneration.fromJson(old.get("game")),new BigInteger(StrictJson.text(old.get("connection_generation"))).add(BigInteger.ONE),StrictJson.text(old.get("session_id")));
        receipt.verifyCurrent(session,receipt.saved,Instant.now().plusMillis(1));assertEquals(d.pair()[0],receipt.source);
        var p=receipt.saved;var other=new CoreFrame.Prefix(p.dateRaw()+24,p.speed(),p.paused(),p.localPlayerId(),p.mapReady(),p.hasPlayedCharacter(),p.playedCharacterId(),p.playedCharacterAlive());assertThrows(IOException.class,()->receipt.verifyCurrent(session,other,Instant.now()));
    }
    @Test void priorChoiceAttemptOrUnknownEffectCannotBecomeAnotherBegin()throws Exception {var d=data();d.progress().put("choose_calls",1);assertThrows(IOException.class,d::load);}
    @Test void onlyThePreciseReadonlyFrameBudgetFailureIsRecoverable()throws Exception {var d=data();((ObjectNode)d.progress().get("originals").get("core_dispatch")).put("failure_kind","IO_FAILURE");assertThrows(IOException.class,d::load);}
    @Test void changedArchiveAndDifferentPhysicalPairAreRejected()throws Exception {var d=data();Files.write(Path.of(d.pair()[1].reference().path()),new byte[]{9});assertThrows(IOException.class,d::load);}
    @Test void rawOriginalPacketMismatchIsRejectedBeforeNewQuery()throws Exception {var d=data();Files.write(d.root().resolve("save-ack.bin"),new byte[]{9});assertThrows(IOException.class,d::load);}
    @Test void changedProgressOwnerOrOldSaveDeadlineIsRejected()throws Exception {var d=data();((ObjectNode)d.progress().get("baseline_checkpoint")).put("save_deadline_utc","2000-01-01T00:00:00Z");assertThrows(IOException.class,d::load);}
    @Test void missingAcceptedPhysicalEvidenceIsNeverFilledWithCallerBoolean()throws Exception {var d=data();((ObjectNode)d.progress().get("baseline_checkpoint")).remove("checkpoint_immutable_archive");assertThrows(Exception.class,d::load);}
}
