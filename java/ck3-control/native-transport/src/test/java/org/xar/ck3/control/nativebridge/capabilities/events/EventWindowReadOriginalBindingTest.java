package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual original Python producer fixture -> full native wire -> installed Java decoder -> public facade.
 * Synthetic transport records are boundary inputs and acquire no private Root/Game permission. */
final class EventWindowReadOriginalBindingTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final int EVENT=0x01000029;
    private static final BigInteger NATIVE=BigInteger.valueOf(17),PUBLIC=BigInteger.valueOf(41);
    private static final String REQUEST="event-original-bound-query";
    @TempDir Path temporary;
    private record Fixture(ReadContract<EventPolicies.ReadPublication> contract,PlanningReadRequest request,
            PlanningReadGuard guard,Binding binding,ObjectNode result) { }
    private static RawJson raw(ObjectNode node) {return EventWindowRead.raw(node);}
    private ExactRef preserve(String filename,byte[] bytes)throws Exception {
        Path file=temporary.resolve(filename);Files.write(file,bytes);var exact=SharedSourceFiles.observe(file).source();
        return new ExactRef(exact.path(),exact.bytes(),exact.sha256());
    }
    private static byte[] hello(Build build,boolean capability)throws Exception {
        ObjectNode row=EventWindowCodec.parse(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        row.put("type","hello").put("protocol_version",1).put("pid",123).put("connection_generation",1)
                .put("bridge_version","original-wire-fixture").put("expected_ck3_sha256",build.sha256())
                .put("game_adapter_id","ck3-"+build.version()+"-msvc-x64").put("game_adapter_status","ready").put("ck3_build_match",true);
        var names=row.putArray("capabilities");if(capability)names.add(EventWindowRead.CAPABILITY);
        return NativeWire.packet(raw(row).bytes());
    }
    private Fixture fixture()throws Exception {
        var source=preserve("collector-source.txt",new byte[]{'e','v','e','n','t'});
        var cap=preserve("native-hello.bin",hello(Build.CROZIER4,true));
        var identity=new ObservationIdentity("synthetic-event-machine",new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(707),NATIVE,BigInteger.valueOf(741221)),"event-original-frame",PUBLIC,"event-original-episode"),1);
        var g2=new G2Source(identity.machineId(),NOW.toString(),"1.20.0.4",source);
        var snapshot=EventWindowCodec.parse(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        snapshot.put("snapshot_id","event-original-frame").put("revision",PUBLIC).put("native_revision",NATIVE).put("date_raw",741221).put("paused",true).put("backend_id","native-headless");
        snapshot.putObject("active_event").put("instance_id",EVENT);
        var contract=EventWindowRead.contract(source,request->{});
        var request=new PlanningReadRequest(identity,g2,"event-original-session",contract.operation(),
                OpportunityJson.object(OpportunityJson.parse(raw(snapshot).bytes()),"original semantic event frame"),NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(new GuardEvidence(identity,g2,request.sessionId(),BigInteger.ONE,contract.operation(),source,cap,"synthetic-boundary-only",NOW,request.deadline()),true,true,true,"b".repeat(64));
        var result=EventWindowCodec.parse(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        result.put("step",EventWindowRead.STEP).put("accepted",true).put("status","available").put("query_sequence",1).put("snapshot_revision",NATIVE).put("backend_id","native-headless");
        result.set("current_event_window_context",EventWindowOriginalProducerTest.fixture("available",Build.CROZIER4));
        return new Fixture(contract,request,guard,new Binding(Build.CROZIER4,NATIVE,741221,EVENT),result);
    }
    private static byte[] outbound(String id,BigInteger revision,int event)throws Exception {
        var row=EventWindowCodec.parse(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        row.put("type","execute_step").put("protocol_version",1).put("request_id",id).put("step",EventWindowRead.STEP)
                .put("expected_revision",revision).put("event_instance_id",event);
        return NativeWire.packet(raw(row).bytes());
    }
    private static NativeActionPort.AckReceived ack(ObjectNode result,String wireId,BigInteger revision,int event)throws Exception {
        var returned=EventWindowCodec.parse(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        returned.put("type","command_result").put("protocol_version",1).put("request_id",wireId).put("ok",true);returned.set("result",result);
        return new NativeActionPort.AckReceived(REQUEST,true,Optional.of(raw(result)),raw(returned),NativeWire.packet(raw(returned).bytes()),
                Optional.of(new NativeActionPort.OutboundPacket(REQUEST,outbound(REQUEST,revision,event))));
    }
    private static PlanningReadReceipt receipt(Fixture f,NativeActionPort.AckReceived ack) {
        return new PlanningReadReceipt(f.request(),f.contract().contractId(),REQUEST,f.guard(),f.guard(),ack);
    }
    @Test void originalProducerAndPacketBindTheSameInstalledReadThroughPublicQuery()throws Exception {
        var f=fixture();var sent=f.contract().prepare(f.request(),REQUEST);
        assertEquals(EVENT,EventWindowCodec.parse(sent.additionalFields()).get("event_instance_id").intValue());
        var receipt=receipt(f,ack(f.result(),REQUEST,NATIVE,EVENT));
        var publication=f.contract().decode(receipt);assertEquals(publication,f.contract().replay(receipt));
        AtomicInteger calls=new AtomicInteger();
        PlanningReadPort reads=new PlanningReadPort(){
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> actual,PlanningReadRequest request) {
                assertSame(f.contract(),actual);assertEquals(f.request(),request);calls.incrementAndGet();
                return new PlanningReadResult.Known<>(actual.decode(receipt),receipt,f.guard().binding().nativeEvidence());
            }
        };
        var service=new EventWindowService(reads,f.contract(),query->f.request());
        var output=EventWindowCodec.parse(EventWindowService.encode(service.query_current_event_window_context_v1(new EventWindowService.Query(EVENT,PUBLIC))));
        assertEquals(1,calls.get());assertEquals(EVENT,output.get("current_event_instance_id").intValue());
        assertEquals("event-original-frame",output.get("queried_snapshot_id").textValue());
        assertEquals(PUBLIC,output.get("queried_revision").bigIntegerValue());assertEquals(NATIVE,output.get("queried_native_revision").bigIntegerValue());
        assertEquals(741221,output.get("binding").get("date_raw").intValue());
        assertFalse(output.get("options").get(0).get("enabled").booleanValue());
        assertFalse(output.get("readiness").get("effect_preview_ready").booleanValue());
        assertThrows(IllegalArgumentException.class,()->service.query_current_event_window_context_v1(new EventWindowService.Query(EVENT,PUBLIC.add(BigInteger.ONE))));
    }
    @Test void originalPacketCannotBeReboundByASeparateAckTokenOrOutboundFrame()throws Exception {
        var f=fixture();
        for(var changed:List.of(ack(f.result(),"other-return",NATIVE,EVENT),ack(f.result(),REQUEST,NATIVE.add(BigInteger.ONE),EVENT),ack(f.result(),REQUEST,NATIVE,EVENT+1)))
            assertThrows(IllegalArgumentException.class,()->f.contract().decode(receipt(f,changed)));
        var real=ack(f.result(),REQUEST,NATIVE,EVENT);var altered=f.result().deepCopy();altered.put("status","unavailable");
        var tokenOnly=new NativeActionPort.AckReceived(REQUEST,true,Optional.of(raw(altered)),real.originalFrame(),real.originalPacket(),real.outbound());
        assertThrows(IllegalArgumentException.class,()->f.contract().decode(receipt(f,tokenOnly)));
        var noOutbound=new NativeActionPort.AckReceived(REQUEST,true,real.originalResultToken(),real.originalFrame(),real.originalPacket());
        assertThrows(IllegalArgumentException.class,()->f.contract().replay(receipt(f,noOutbound)));
    }
    @Test void outerProducerFieldsAndConnectedBuildRemainStrict()throws Exception {
        var f=fixture();var omitted=f.result().deepCopy();omitted.remove("query_sequence");
        var floating=f.result().deepCopy();floating.put("query_sequence",1.0);
        var wrong=f.result().deepCopy();wrong.put("accepted",false);
        var status=f.result().deepCopy();status.put("status","unavailable");
        for(var malformed:List.of(omitted,floating,wrong,status)) {
            var ack=ack(malformed,REQUEST,NATIVE,EVENT);
            assertThrows(IllegalArgumentException.class,()->f.contract().decode(receipt(f,ack)));
        }
        assertEquals(Build.CROZIER4,EventWindowRead.connectedBuild(hello(Build.CROZIER4,true),123,BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->EventWindowRead.connectedBuild(hello(Build.CROZIER4,false),123,BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->EventWindowRead.connectedBuild(hello(Build.CROZIER4,true),124,BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->EventWindowRead.connectedBuild(hello(Build.CROZIER4,true),123,BigInteger.TWO));
    }
    @Test void displayedOptionOrderCannotAcquireADifferentNativeIdentity()throws Exception {
        var f=fixture();var nativeContext=(ObjectNode)f.result().get("current_event_window_context");
        var duplicate=nativeContext.deepCopy();var options=(com.fasterxml.jackson.databind.node.ArrayNode)duplicate.get("options");
        var second=options.get(0).deepCopy();((ObjectNode)second).put("rendered_index",1);options.add(second);
        assertThrows(IllegalArgumentException.class,()->EventWindowCodec.decode(raw(duplicate),f.binding()));
        var hidden=nativeContext.deepCopy();((ObjectNode)hidden.get("options").get(0)).put("shown",false);
        assertThrows(IllegalArgumentException.class,()->EventWindowCodec.decode(raw(hidden),f.binding()));
    }
}
