package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** NoGame original C++ health tokens; checkpoint ACK and small physical files below are explicit Java software DATA. */
class NativeCurrentSupermanHealthTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\superman-health-data","superman-health-data",GAME,"superman-health-session","superman-health-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(20)));}
    static NativeGameTransport.SupermanHealthReceived query(NativeGameTransport t,CurrentSupermanHealth.Phase phase)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.SupermanHealthReceived.class,t.readCurrentSupermanHealth(c,phase,c.validUntil()));}
    static NativeGameTransport.SupermanHealthPrepared prepare(NativeGameTransport t,NativeGameTransport.SupermanHealthReceived q)throws IOException{return t.prepareCurrentSupermanHealthChoose(q);}
    static FileWitness[] actualSmallPair()throws Exception{Path dir=Files.createTempDirectory("superman-health-baseline-");assertEquals(Path.of("D:/").getRoot(),dir.getRoot());var files=new NativeCheckpointFiles();Path source=dir.resolve(CurrentCoreCheckpointSave.FILENAME),archive=dir.resolve("immutable.ck3");Files.write(source,new byte[]{83,65,86,1,2,3});var before=files.observe(source).orElseThrow();return new FileWitness[]{before,files.copyNew(before,archive)};}
    static void submittedSave(NativeGameTransport t)throws Exception{var c=core(t);var p=t.prepareCurrentCoreCheckpoint(c,c.validUntil());assertTrue(CurrentCoreCheckpointSaveResult.decodeOutcome(assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCoreCheckpoint(p))).accepted());}
    @Test void completedUsesPrivatePhaseOriginalDeadlineAndOneSubmission()throws Exception{
        var r=new Replay("known",CurrentSupermanHealth.Phase.COMPLETED);try(var t=transport(r)){var q=query(t,r.phase);var p=prepare(t,q);assertEquals(q.phase(),p.phase());assertEquals(q.frame().source().orElseThrow(),p.selected());assertEquals(q.validUntil(),p.deadline());var request=NativeWire.decodeExecuteRequest(p.originalPacket().value());var fields=NativeWire.parse(request.normalizedAdditionalFields().value());assertEquals("completed",fields.get("superman_health").get("phase").textValue());assertEquals(p.deadline().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentSupermanHealthChoose(p));assertSame(out,t.submitCurrentSupermanHealthChoose(p));assertEquals(CurrentSupermanHealthResult.decodeOutcome(out),p.latestFrame().orElseThrow());assertEquals(1,r.choiceWrites);}
    }
    @Test void baselineCannotUseCompletedFactoryOrAnyCallerWitnessWithoutOwnSave()throws Exception{
        var r=new Replay("known",CurrentSupermanHealth.Phase.BASELINE);try(var t=transport(r)){var q=query(t,r.phase);assertThrows(IOException.class,()->prepare(t,q));var pair=actualSmallPair();assertThrows(IOException.class,()->t.prepareCurrentSupermanHealthBegin(q,pair[0],pair[1]));assertEquals(0,r.saveWrites);assertEquals(0,r.choiceWrites);}
    }
    @Test void actualSameReceiverSaveThenFreshCoreAndTwoPhysicalWitnessesAdmitOneBegin()throws Exception{
        var r=new Replay("capture-pair",CurrentSupermanHealth.Phase.BASELINE);try(var t=transport(r)){submittedSave(t);var pair=actualSmallPair();var q=query(t,r.phase);var p=t.prepareCurrentSupermanHealthBegin(q,pair[0],pair[1]);assertEquals(CurrentSupermanHealth.Phase.BASELINE,p.phase());var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentSupermanHealthChoose(p));assertSame(out,t.submitCurrentSupermanHealthChoose(p));assertEquals(1,r.saveWrites);assertEquals(1,r.choiceWrites);}
    }
    @Test void changedPhysicalArchiveAfterPreparationRejectsBeforeChoiceWrite()throws Exception{
        var r=new Replay("known",CurrentSupermanHealth.Phase.BASELINE);try(var t=transport(r)){submittedSave(t);var pair=actualSmallPair();var q=query(t,r.phase);var p=t.prepareCurrentSupermanHealthBegin(q,pair[0],pair[1]);Files.write(Path.of(pair[1].reference().path()),new byte[]{7});assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitCurrentSupermanHealthChoose(p));assertEquals(0,r.choiceWrites);}
    }
    @Test void freshCoreWithDifferentDateCannotBorrowTheOlderAcceptedSave()throws Exception{
        var r=new Replay("date-change",CurrentSupermanHealth.Phase.BASELINE);try(var t=transport(r)){submittedSave(t);var pair=actualSmallPair();var q=query(t,r.phase);assertThrows(IOException.class,()->t.prepareCurrentSupermanHealthBegin(q,pair[0],pair[1]));assertEquals(0,r.choiceWrites);}
    }
    @Test void absentEventOrNativeCanFalseNeverMintsKnownChoice()throws Exception{
        for(String mode:new String[]{"empty","can-false"}){var r=new Replay(mode,CurrentSupermanHealth.Phase.COMPLETED);try(var t=transport(r)){var q=query(t,r.phase);assertThrows(IOException.class,()->prepare(t,q));assertEquals(0,r.choiceWrites);}}
    }
    @Test void privateQueryCannotCrossReceiverAndCapabilityCannotBeInvented()throws Exception{
        var a=new Replay("known",CurrentSupermanHealth.Phase.COMPLETED);var b=new Replay("known",CurrentSupermanHealth.Phase.COMPLETED);try(var t=transport(a);var other=transport(b)){var q=query(t,a.phase);assertThrows(IOException.class,()->prepare(other,q));var p=prepare(t,q);assertSame(p,prepare(t,q));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentSupermanHealthChoose(p));assertEquals(0,b.choiceWrites);}
        var r=new Replay("missing-effects",CurrentSupermanHealth.Phase.COMPLETED);try(var t=transport(r)){var q=query(t,r.phase);assertThrows(IOException.class,()->prepare(t,q));assertEquals(0,r.choiceWrites);}
    }
    @Test void extendedCoreDeadlineRejectsBeforeReadonlyWrite()throws Exception{
        var r=new Replay("known",CurrentSupermanHealth.Phase.COMPLETED);try(var t=transport(r)){var c=core(t);var read=t.readCurrentSupermanHealth(c,r.phase,c.validUntil().plusMillis(1));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,read.original());assertEquals(0,r.queries);}
    }
    @Test void lostChoiceAckIsStickyUnknownAndBlocksOtherCoreEffects()throws Exception{
        var r=new Replay("lost",CurrentSupermanHealth.Phase.COMPLETED);try(var t=transport(r)){var c=core(t);var q=assertInstanceOf(NativeGameTransport.SupermanHealthReceived.class,t.readCurrentSupermanHealth(c,r.phase,c.validUntil()));var p=prepare(t,q);var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentSupermanHealthChoose(p));assertSame(out,t.submitCurrentSupermanHealthChoose(p));assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(1,r.choiceWrites);}
    }
    @Test void changedPhaseLeaseOrBeforeSnapshotKeepsOriginalAckAsUnknown()throws Exception{
        for(String mode:new String[]{"wrong-phase","wrong-lease","changed-source"}){var r=new Replay(mode,CurrentSupermanHealth.Phase.COMPLETED);try(var t=transport(r)){var p=prepare(t,query(t,r.phase));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentSupermanHealthChoose(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentSupermanHealthChoose(p));assertEquals(1,r.choiceWrites);}}
    }
    @Test void originalSpentClaimRefusalIsKnownZeroEffectAndNeverRetried()throws Exception{
        var r=new Replay("early",CurrentSupermanHealth.Phase.BASELINE);try(var t=transport(r)){submittedSave(t);var pair=actualSmallPair();var q=query(t,r.phase);var p=t.prepareCurrentSupermanHealthBegin(q,pair[0],pair[1]);var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentSupermanHealthChoose(p));var f=CurrentSupermanHealthResult.decodeOutcome(out);assertFalse(f.successful());assertFalse(f.effectAttempted());assertEquals(BigInteger.ONE,f.claimSequence());assertEquals(q.frame().providerGeneration(),f.providerGeneration());assertEquals(q.frame().querySequence(),f.querySequence());assertSame(out,t.submitCurrentSupermanHealthChoose(p));assertEquals(1,r.choiceWrites);}
    }
    @Test void indeterminateCleanupOrForgedRefusalEffectLocksSharedUnknown()throws Exception{
        for(String mode:new String[]{"indeterminate","bad-refusal"}){var r=new Replay(mode,CurrentSupermanHealth.Phase.BASELINE);try(var t=transport(r)){submittedSave(t);var pair=actualSmallPair();var q=query(t,r.phase);var p=t.prepareCurrentSupermanHealthBegin(q,pair[0],pair[1]);var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentSupermanHealthChoose(p));assertSame(out,t.submitCurrentSupermanHealthChoose(p));assertEquals(1,r.choiceWrites);}}
    }
    static final class Replay implements NativePacketPort {
        final String mode;final CurrentSupermanHealth.Phase phase;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int saveWrites,choiceWrites,queries;
        Replay(String mode,CurrentSupermanHealth.Phase phase)throws IOException{this.mode=mode;this.phase=phase;var f=NativeCurrentSupermanHealth26785313ProducerTest.frame(NativeCurrentSupermanHealth26785313ProducerTest.queryRole(phase));var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",f.owner().orElseThrow().connectionGeneration()).put("bridge_version","superman-health-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(CurrentCoreCheckpointSave.CAPABILITY).add(CurrentSupermanHealth.Action.QUERY_HEALTH.capability());if(!mode.equals("missing-effects"))caps.add(CurrentSupermanHealth.Action.CHOOSE_KNOWN.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));}
        public void verify()throws IOException{if(closed)throw new IOException("Health DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Health DATA response missing");return packets.removeFirst();}public void close(){closed=true;}
        public void writePacket(byte[] packet,Instant until)throws IOException{
            verify();var request=NativeWire.decodeExecuteRequest(packet);ObjectNode token;boolean ok;
            if(request.step().equals(CoreFrame.STEP)) {var actual=NativeCurrentSupermanHealth26785313ProducerTest.actualCore(phase);if(mode.equals("date-change")&&saveWrites>0){var p=actual.prefix();actual=new CoreFrame.Partial(BUILD,new CoreFrame.Prefix(p.dateRaw()+24,p.speed(),p.paused(),p.localPlayerId(),p.mapReady(),p.hasPlayedCharacter(),p.playedCharacterId(),p.playedCharacterAlive()));}token=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(actual).bytes()));ok=true;}
            else if(request.step().equals(CurrentCoreCheckpointSave.STEP)){
                saveWrites++;token=StrictJson.object().put("schema",CurrentCoreCheckpointSave.RESULT_SCHEMA).put("game_version",BUILD.version()).put("executable_sha256",BUILD.executableSha256().toUpperCase(java.util.Locale.ROOT)).put("adapter_id",BUILD.coreFrameAdapterId()).put("backend",CurrentCoreCheckpointSave.BACKEND).put("step",CurrentCoreCheckpointSave.STEP).put("accepted",true).put("queue_status","submitted").put("effect_attempted",true).put("complete_snapshot",false).put("physical_save_confirmed",false).put("save_name",CurrentCoreCheckpointSave.SAVE_NAME).put("physical_filename",CurrentCoreCheckpointSave.FILENAME);token.putObject("submission").put("sequence",1).put("requested_save_name",CurrentCoreCheckpointSave.SAVE_NAME).put("date_raw",NativeCurrentSupermanHealth26785313ProducerTest.actualCore(phase).prefix().dateRaw());ok=true;
            } else {
                var fields=NativeWire.parse(request.normalizedAdditionalFields().value());var claim=fields.get("superman_health");assertEquals(phase.wire(),claim.get("phase").textValue());boolean query=claim.get("action").textValue().equals("query_health");String role;
                if(query){queries++;assertEquals("0",claim.get("provider_generation").textValue());role=NativeCurrentSupermanHealth26785313ProducerTest.queryRole(phase);}else{choiceWrites++;assertEquals(CurrentSupermanHealth.Action.CHOOSE_KNOWN.step(),request.step());assertFalse(claim.has("instance_id"));if(mode.equals("lost"))return;role=mode.equals("early")||mode.equals("bad-refusal")?"stale":mode.equals("indeterminate")?"indeterminate":NativeCurrentSupermanHealth26785313ProducerTest.choiceRole(phase);}
                if(mode.equals("capture-pair"))retain(claim.get("action").textValue()+"-"+phase.wire(),packet);
                var envelope=NativeCurrentSupermanHealth26785313ProducerTest.envelope(role);token=NativeWire.object(envelope.get("result"));ok=envelope.get("ok").booleanValue();
                if(query){
                    if(mode.equals("date-change")&&saveWrites>0)((ObjectNode)token.get("facts_before")).put("date_raw",NativeCurrentSupermanHealth26785313ProducerTest.actualCore(phase).prefix().dateRaw()+24);
                    if(mode.equals("can-false")){var s=NativeCurrentSupermanHealth26785313ProducerTest.source(token);s.put("native_choice_admissible",false);((ObjectNode)s.get("options").get(0)).put("native_can_select",false);}
                    if(mode.equals("empty")){var s=NativeCurrentSupermanHealth26785313ProducerTest.source(token);s.put("event_found",false).put("named_root_bound",false).put("window_visible",false).put("window_enabled",false).put("native_choice_admissible",false);for(String k:new String[]{"instance_id","recipient_character_id","definition_key","opening","description","authored_option_count"})s.putNull(k);s.putArray("options");}
                }else{if(mode.equals("wrong-phase"))token.put("phase","baseline");if(mode.equals("wrong-lease"))token.put("query_sequence","0");if(mode.equals("changed-source"))((ObjectNode)NativeCurrentSupermanHealth26785313ProducerTest.source(token).get("characters").get(39).get("values")).put("sxad_health_value","777");if(mode.equals("early"))token.put("claim_sequence","1");if(mode.equals("bad-refusal"))token.put("effect_attempted",true);}
            }
            var e=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",ok);e.set("result",token);packets.add(NativeWire.packet(StrictJson.canonical(e)));
        }
        static void retain(String role,byte[] packet)throws IOException{String folder=System.getProperty("xar.current267.superman.health.java.requests");if(folder==null)return;Path dir=Path.of(folder).toAbsolutePath().normalize();if(!dir.getRoot().equals(Path.of("D:/").getRoot()))throw new IOException("D request artifact root required");Files.createDirectories(dir);Path p=dir.resolve(role+".request.json");if(!Files.exists(p))Files.write(p,java.util.Arrays.copyOfRange(packet,4,packet.length),java.nio.file.StandardOpenOption.CREATE_NEW);}
    }
}
