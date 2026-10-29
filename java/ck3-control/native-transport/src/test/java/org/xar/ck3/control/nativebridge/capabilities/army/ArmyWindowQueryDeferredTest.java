package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual retained Python Driver+software endpoint -> original packets -> Java readonly producer and public codec.
 * Controlled chronology is DATA; it grants no Root physical permission, native action credit or Game qualification. */
final class ArmyWindowQueryDeferredTest {
    private static final Instant END=Instant.parse("2030-01-01T00:00:00Z");
    private record Case(ArmyCalls.Frame input,Complete before,PlanningReadRequest request,
                        PlanningReadResult.Unavailable<ArmyWindowCodec.Observation> unavailable,ObjectNode expected) { }
    @Test void originalDriverSingleNegativeQueryPreservesWholeDeferredResponseAndPublicSerde() throws Exception {
        Case c=fixture(); var original=ArmyWindowQueryDeferred.from(c.input(),c.before(),c.request(),c.unavailable()).orElseThrow();
        assertEquals(c.expected(),ArmyJson.parse(original.normalized().bytes()));
        assertSame(c.unavailable().original().orElseThrow(),original.original());
        var reply=new ArmyWindowService.ReadDeferred(original); RawJson encoded=ArmyWindowService.encode(reply);
        assertEquals(OpportunityJson.object(OpportunityJson.parse(original.normalized().bytes()),"deferred"),
                ArmyPublicWire.decodeExactSourceBound(encoded,original.context()));
        ObjectNode wire=ArmyJson.parse(encoded.bytes());
        assertTrue(wire.get("queried_connection_generation").isTextual());
        assertTrue(wire.path("native_error_evidence").path("native_request").path("expected_revision").isTextual());
        assertTrue(wire.path("source_frame").path("bridge_pid").isIntegralNumber());
        for(String key:List.of("accepted","available","business_submission","native_ack_verified","request_retried","ui_action_credit","date_advance_observed","close_dispatched"))
            assertFalse(c.expected().get(key).booleanValue(),key);
    }
    @Test void mismatchedActualPacketsPidRequestAndCloseNeverBecomeDeferred() throws Exception {
        Case c=fixture();
        var close=new ArmyCalls.Frame(PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1,c.input().revision());
        // The producer is QUERY-only even when a caller presents a close-shaped public selection.
        assertThrows(IllegalArgumentException.class,()->ArmyWindowQueryDeferred.from(close,c.before(),c.request(),c.unavailable()));
        ObjectNode state=ArmyJson.object(OpportunityJson.toNode(c.before().semantic())).deepCopy();state.withObject("diagnostics").put("bridge_pid",0);
        Complete wrongPid=new Complete(c.before().identity(),c.before().source(),c.before().sessionId(),c.before().connectionGeneration(),
                OpportunityJson.object(OpportunityJson.parse(ArmyJson.bytes(state)),"mutated pid"),c.before().originalEvidence(),c.before().observedAt(),c.before().fullBindingSha256());
        assertTrue(ArmyWindowQueryDeferred.from(c.input(),wrongPid,c.request(),c.unavailable()).isEmpty());
        var old=(NativeActionPort.AckReceived)c.unavailable().original().orElseThrow();byte[] changed=old.originalPacket();changed[changed.length-1]^=1;
        var corrupt=new NativeActionPort.AckReceived(old.requestId(),false,old.originalResultToken(),old.originalFrame(),changed,old.outbound(),old.custody());
        assertThrows(IllegalArgumentException.class,()->ArmyWindowQueryDeferred.from(c.input(),c.before(),c.request(),unavailable(corrupt)));
        ObjectNode other=ArmyJson.parse(old.originalFrame().bytes()).put("error","arbitrary_error");
        assertTrue(ArmyWindowQueryDeferred.from(c.input(),c.before(),c.request(),unavailable(ack(other,
                old.outbound().orElseThrow().originalPacket(),c.before()))).isEmpty());
        assertEquals("Native war results refused: arbitrary_error",ArmyWindowQueryFailure.from(ArmyWindowCodec.Kind.RESULTS,
                unavailable(ack(other,old.outbound().orElseThrow().originalPacket(),c.before()))).getMessage());
    }
    @Test void strictOriginalRefusalMessagesKeepBothWindowRolesAndRejectMalformedFalseTop() {
        for(var kind:ArmyWindowCodec.Kind.values()) {
            String label=kind==ArmyWindowCodec.Kind.OVERVIEW?"war overview":"war results";
            ObjectNode top=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","q").put("ok",false).put("error","state_changed");
            assertEquals("Native "+label+" refused: state_changed",ArmyWindowQueryFailure.refusalMessage(kind,new RawJson(ArmyJson.bytes(top)),"q"));
            assertEquals(label+" original command_result timed out",ArmyWindowQueryFailure.timeoutMessage(kind));
            for(String corruption:List.of("extra","bool_protocol","wrong_request","null_error")) {
                ObjectNode bad=top.deepCopy();switch(corruption){case "extra"->bad.put("alias",true);case "bool_protocol"->bad.put("protocol_version",true);
                    case "wrong_request"->bad.put("request_id","other");case "null_error"->bad.putNull("error");default->throw new AssertionError();}
                assertThrows(IllegalArgumentException.class,()->ArmyWindowQueryFailure.refusalMessage(kind,new RawJson(ArmyJson.bytes(bad)),"q"));
            }
        }
    }
    private static Case fixture() throws Exception {
        ObjectNode actual=oracle();ObjectNode before=ArmyJson.object(actual.get("before")),top=ArmyJson.object(actual.get("top"));
        String id=top.get("request_id").textValue();var sourceRef=new ExactRef("controlled/original-python-source",1,"a".repeat(64));
        var source=new G2Source("source-shaped-software-machine","2026-10-24T00:00:00Z","1.20.0.4",sourceRef);
        BigInteger revision=before.get("revision").bigIntegerValue(),nativeRevision=before.get("native_revision").bigIntegerValue();
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(before.path("played_character").path("character_id").bigIntegerValue(),
                nativeRevision,before.get("date_raw").bigIntegerValue()),before.get("snapshot_id").textValue(),revision,
                before.path("episode_run_id").isTextual()?before.get("episode_run_id").textValue():null);
        var game=new GameGeneration(before.path("diagnostics").path("bridge_pid").longValue(),new PythonOnlyUInt64(BigInteger.ONE));
        var identity=new ObservationIdentity(source.machineId(),game,frame,1);
        var semantic=OpportunityJson.object(OpportunityJson.parse(ArmyJson.bytes(before)),"original Driver frame");
        Complete complete=new Complete(identity,source,"controlled-original-session",before.path("diagnostics").path("hello").path("connection_generation").bigIntegerValue(),
                semantic,sourceRef,Instant.parse("2026-10-24T00:00:00Z"),"b".repeat(64));
        var input=new ArmyCalls.Frame(PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1,new ArmyCalls.Revision(new ArmyTypes.Present<>(revision)));
        var request=new PlanningReadRequest(identity,source,complete.sessionId(),new OperationKey(ArmyWindowCodec.Kind.RESULTS.step(ArmyWindowCodec.Operation.QUERY)),ArmyWindowReads.arguments(input),END);
        byte[] outbound=NativeWire.execute(id,request.operation().value(),nativeRevision,new byte[]{'{','}'});
        assertEquals(actual.get("request"),ArmyJson.parse(java.util.Arrays.copyOfRange(outbound,4,outbound.length)),
                "the sole actual Native wire producer must retain the original Python five-field request");
        return new Case(input,complete,request,unavailable(ack(top,outbound,complete)),ArmyJson.object(actual.get("result")));
    }
    private static PlanningReadResult.Unavailable<ArmyWindowCodec.Observation> unavailable(NativeActionPort.AckReceived ack) {
        return new PlanningReadResult.Unavailable<>("actual native negative",Optional.of(ack));
    }
    private static NativeActionPort.AckReceived ack(ObjectNode top,byte[] outbound,Complete before) {
        String id=top.get("request_id").textValue();byte[] body=ArmyJson.bytes(top),incoming=packet(body);Instant start=before.observedAt();
        var session=new NativeObservationPort.TransportSession(before.source().machineId(),before.identity().game(),before.connectionGeneration(),before.sessionId());
        var custody=new NativeRequestChronology(session,UUID.fromString("0aa4976c-4ec9-4aab-9350-6d304a649357"),id,
                NativeRequestChronology.PacketIdentity.of(outbound),NativeRequestChronology.PacketIdentity.of(incoming),
                new NativeRequestChronology.Event(BigInteger.ONE,start.plusMillis(1)),new NativeRequestChronology.Event(BigInteger.TWO,start.plusMillis(2)),
                new NativeRequestChronology.Event(BigInteger.valueOf(3),start.plusMillis(3)));
        return new NativeActionPort.AckReceived(id,false,Optional.empty(),new RawJson(body),incoming,
                Optional.of(new NativeActionPort.OutboundPacket(id,outbound)),Optional.of(custody));
    }
    private static byte[] packet(byte[] body){return ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();}
    private static ObjectNode oracle() throws Exception {
        Path root=required("xar.repository.root"),python=required("xar.python");verify(root);
        String code="""
import sys,json
from pathlib import Path
root=Path(sys.argv[1]);sys.dont_write_bytecode=True
sys.path[:0]=[str(root/'ck3_autonomous_player'/'tests'/'unit'),str(root/'ck3_autonomous_player'/'src')]
from test_native_bridge_driver import FakeEndpoint,_hello,_snapshot
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_results_window_contract import QUERY_CAPABILITY,CLOSE_CAPABILITY
endpoint=FakeEndpoint();driver=NativeHeadlessGameplayDriver(endpoint.pipe_name,endpoint=endpoint)
hello=_hello('game.state.snapshot',QUERY_CAPABILITY,CLOSE_CAPABILITY)
hello.update(bridge_version='0.1.0.4',expected_ck3_version=CK3_12004.game_version,expected_ck3_sha256=CK3_12004.executable_sha256,connection_generation=23)
endpoint.publish(hello);endpoint.publish(_snapshot(40,played_character={'character_id':707,'alive':True}))
before=driver.take_internal_semantic_snapshot();endpoint.frames.clear();received=[]
def send(request):
 top={'type':'command_result','protocol_version':1,'request_id':request['request_id'],'ok':False,'error':'state_changed'}
 received.append(top);endpoint.publish(top)
endpoint.send_hook=send
try:
 result=driver.query_war_results_window_v1(expected_revision=before['revision'])
 assert len(endpoint.frames)==len(received)==1
 print(json.dumps({'before':before,'request':endpoint.frames[0],'top':received[0],'result':result},allow_nan=False,separators=(',',':')))
finally:driver.close()
""";
        ProcessBuilder builder=new ProcessBuilder(python.toString(),"-I","-B","-c",code,root.toString()).directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");Process process=builder.start();
        FutureTask<byte[]> out=new FutureTask<>(()->process.getInputStream().readNBytes(1024*1024+1));
        FutureTask<byte[]> err=new FutureTask<>(()->process.getErrorStream().readNBytes(16385));Thread.ofVirtual().start(out);Thread.ofVirtual().start(err);
        process.getOutputStream().close();try{
            if(!process.waitFor(60,TimeUnit.SECONDS))throw new IllegalStateException("original Driver query fixture timed out");
            byte[] bytes=out.get(5,TimeUnit.SECONDS),errors=err.get(5,TimeUnit.SECONDS);
            if(process.exitValue()!=0||bytes.length>1024*1024||errors.length>16384)throw new IllegalStateException("original Driver fixture failed: "+new String(errors,StandardCharsets.UTF_8));
            verify(root);return ArmyJson.parse(bytes);
        }finally{if(process.isAlive()){process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);}}
    }
    private static Path required(String property)throws Exception {
        String value=System.getProperty(property);if(value==null||value.isBlank())throw new IllegalStateException("required original fixture property missing: "+property);
        Path path=Path.of(value);if(!path.isAbsolute())throw new IllegalArgumentException("absolute original fixture path required");return path.toRealPath();
    }
    private static void verify(Path root)throws Exception {
        String[][] pins={
            {"src/xar_autoplayer/bridge/war_results_window_transport.py","e1a3d7d5ae36ccf2a17055d166742f3fd49b11529bdbd383c7b2b9d5640fd86e"},
            {"src/xar_autoplayer/bridge/war_results_window_contract.py","3373fd42fc1cf8da88caf515061b4d8909816bf4ace66a6e01b25ac091a6cd66"},
            {"src/xar_autoplayer/bridge/prewar_force_coalition_transport.py","28ffe1bc6cd9f8042417e16c97bb7c76fe812d5d1386f9015909010eb7203299"},
            {"src/xar_autoplayer/bridge/native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},
            {"tests/unit/test_native_bridge_driver.py","4cf26ef6804ba46b7e8d1f3ef5aeaffafab136e7ee4f0b3a45462906dcdc1f99"},
            {"tests/unit/test_war_results_first_read_defer.py","cfabec0804361f063a6e55b6298d63542369ccf746bfbd0eb15ea381f4efb70b"}};
        for(var pin:pins){Path path=root.resolve("ck3_autonomous_player").resolve(pin[0]).toRealPath();assertTrue(path.startsWith(root));
            assertEquals(pin[1],ActionCodec.sha256(Files.readAllBytes(path)),"original query fixture source drift");}
    }
}
