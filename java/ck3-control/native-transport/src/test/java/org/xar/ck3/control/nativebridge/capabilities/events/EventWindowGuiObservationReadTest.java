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

/** New explicit GUI request -> original wire decoder -> installed Java publication, with owned software packets. */
final class EventWindowGuiObservationReadTest {
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
    private Fixture fixture(boolean guiObservation)throws Exception {
        var source=preserve("collector-source.txt",new byte[]{'e','v','e','n','t'});
        var cap=preserve("native-hello.bin",hello(Build.CROZIER4,true));
        var identity=new ObservationIdentity("synthetic-event-machine",new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(707),NATIVE,BigInteger.valueOf(741221)),"event-original-frame",PUBLIC,"event-original-episode"),1);
        var g2=new G2Source(identity.machineId(),NOW.toString(),"1.20.0.4",source);
        var snapshot=EventWindowCodec.parse(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        snapshot.put("snapshot_id","event-original-frame").put("revision",PUBLIC).put("native_revision",NATIVE).put("date_raw",741221).put("paused",true).put("backend_id","native-headless");
        snapshot.putObject("active_event").put("instance_id",EVENT);
        var contract=guiObservation?EventWindowRead.contractWithGuiObservation(source,request->{}):EventWindowRead.contract(source,request->{});
        var request=new PlanningReadRequest(identity,g2,"event-original-session",contract.operation(),
                OpportunityJson.object(OpportunityJson.parse(raw(snapshot).bytes()),"original semantic event frame"),NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(new GuardEvidence(identity,g2,request.sessionId(),BigInteger.ONE,contract.operation(),source,cap,"synthetic-boundary-only",NOW,request.deadline()),true,true,true,"b".repeat(64));
        var result=EventWindowCodec.parse(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        result.put("step",EventWindowRead.STEP).put("accepted",true).put("status","available").put("query_sequence",1).put("snapshot_revision",NATIVE).put("backend_id","native-headless");
        ObjectNode context=EventWindowGuiAvailabilityCodecTest.packet(guiObservation?2:1,true,false);
        if(guiObservation) ((ObjectNode)context.path("options").get(0)).putObject("gui_availability").put("status","observed").put("is_valid",false);
        result.set("current_event_window_context",context);
        return new Fixture(contract,request,guard,new Binding(Build.CROZIER4,NATIVE,741221,EVENT),result);
    }
    private static byte[] outbound(String id,BigInteger revision,int event,ObjectNode extra)throws Exception {
        var row=EventWindowCodec.parse(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        row.put("type","execute_step").put("protocol_version",1).put("request_id",id).put("step",EventWindowRead.STEP)
                .put("expected_revision",revision).put("event_instance_id",event);
        extra.fieldNames().forEachRemaining(key->row.set(key,extra.get(key)));
        return NativeWire.packet(raw(row).bytes());
    }
    private static NativeActionPort.AckReceived ack(ObjectNode result,String wireId,BigInteger revision,int event,ObjectNode extra)throws Exception {
        var returned=EventWindowCodec.parse(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        returned.put("type","command_result").put("protocol_version",1).put("request_id",wireId).put("ok",true);returned.set("result",result);
        return new NativeActionPort.AckReceived(REQUEST,true,Optional.of(raw(result)),raw(returned),NativeWire.packet(raw(returned).bytes()),
                Optional.of(new NativeActionPort.OutboundPacket(REQUEST,outbound(REQUEST,revision,event,extra))));
    }
    private static PlanningReadReceipt receipt(Fixture f,NativeActionPort.AckReceived ack) {
        return new PlanningReadReceipt(f.request(),f.contract().contractId(),REQUEST,f.guard(),f.guard(),ack);
    }
    private static ObjectNode extra() { return EventWindowCodec.parse(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))); }
    private static ObjectNode flag() { return extra().put("gui_observation_version",2); }
    @Test void defaultContractKeepsV1PacketAndDoesNotRequestObservation()throws Exception {
        Fixture f=fixture(false);
        ObjectNode sent=EventWindowCodec.parse(f.contract().prepare(f.request(),REQUEST).additionalFields());
        assertEquals(1,sent.size()); assertEquals(EVENT,sent.get("event_instance_id").intValue());
        assertEquals("native/event-window-v1",f.contract().contractId());
        var original=receipt(f,ack(f.result(),REQUEST,NATIVE,EVENT,extra()));
        var publication=f.contract().decode(original);
        assertEquals(publication,f.contract().replay(original));
        assertEquals(1,EventWindowCodec.parse(new RawJson(OpportunityJson.encode(publication.result()))).get("schema_version").intValue());
    }
    @Test void explicitV2RequestBindsFullWireAndPublishesObservedFalseWithoutChangingRawFlag()throws Exception {
        Fixture f=fixture(true);
        ObjectNode sent=EventWindowCodec.parse(f.contract().prepare(f.request(),REQUEST).additionalFields());
        assertTrue(sent.get("gui_observation_version").isIntegralNumber());
        assertEquals(2,sent.get("gui_observation_version").intValue());
        assertEquals("native/event-window-v2",f.contract().contractId());
        var original=receipt(f,ack(f.result(),REQUEST,NATIVE,EVENT,flag()));
        var publication=f.contract().decode(original);
        assertEquals(publication,f.contract().replay(original));
        var history=EventWindowCodec.parse(new RawJson(OpportunityJson.encode(publication.result())));
        assertEquals(2,history.get("schema_version").intValue());
        assertTrue(history.path("options").get(0).get("enabled").booleanValue());
        assertFalse(history.path("options").get(0).path("gui_availability").get("is_valid").booleanValue());
    }
    @Test void outboundVersionTypeAndRequestedResponseVersionRemainExact()throws Exception {
        Fixture f=fixture(true);
        List<ObjectNode> invalid=new java.util.ArrayList<>();
        invalid.add(extra()); invalid.add(extra().put("gui_observation_version",true));
        invalid.add(extra().put("gui_observation_version",2.0));invalid.add(extra().put("gui_observation_version","2"));
        invalid.add(extra().putNull("gui_observation_version"));invalid.add(extra().put("gui_observation_version",3));
        invalid.add(flag().put("extra",1));
        for(ObjectNode changed:invalid) {
            var original=receipt(f,ack(f.result(),REQUEST,NATIVE,EVENT,changed));
            assertThrows(IllegalArgumentException.class,()->f.contract().decode(original),changed::toString);
        }
        ObjectNode wrongVersion=f.result().deepCopy();
        wrongVersion.set("current_event_window_context",EventWindowGuiAvailabilityCodecTest.packet(1,true,false));
        var wrong=receipt(f,ack(wrongVersion,REQUEST,NATIVE,EVENT,flag()));
        assertThrows(IllegalArgumentException.class,()->f.contract().decode(wrong));
        Fixture legacy=fixture(false);
        var extraFlag=receipt(legacy,ack(legacy.result(),REQUEST,NATIVE,EVENT,flag()));
        assertThrows(IllegalArgumentException.class,()->legacy.contract().decode(extraFlag));
    }
    @Test void capabilitySelectionKeepsOldAndUnrelatedNativeOnV1()throws Exception {
        Fixture f=fixture(false);AtomicInteger admissions=new AtomicInteger();
        for(java.util.Set<String> names:List.of(java.util.Set.<String>of(),java.util.Set.of(EventWindowRead.CAPABILITY),
                java.util.Set.of(EventWindowRead.CAPABILITY,EventWindowRead.GUI_OBSERVATION_CAPABILITY+"-unrelated"))) {
            var contract=EventWindowRead.contractForCapabilities(f.contract().sourceRef(),request->admissions.incrementAndGet(),names);
            assertEquals("native/event-window-v1",contract.contractId());
            ObjectNode sent=EventWindowCodec.parse(contract.prepare(f.request(),REQUEST).additionalFields());
            assertEquals(1,sent.size());assertFalse(sent.has("gui_observation_version"));
            assertEquals(EVENT,sent.get("event_instance_id").intValue());
        }
        assertEquals(3,admissions.get());
    }
    @Test void exactGuiCapabilitySelectsV2AndRetainsTheBoundRequest()throws Exception {
        Fixture f=fixture(false);AtomicInteger admissions=new AtomicInteger();
        java.util.Set<String> capabilities=java.util.Set.of(EventWindowRead.CAPABILITY,EventWindowRead.GUI_OBSERVATION_CAPABILITY);
        var contract=EventWindowRead.contractForCapabilities(f.contract().sourceRef(),request->{assertEquals(f.request(),request);admissions.incrementAndGet();},capabilities);
        assertEquals("native/event-window-v2",contract.contractId());
        ObjectNode sent=EventWindowCodec.parse(contract.prepare(f.request(),REQUEST).additionalFields());
        assertEquals(2,sent.size());assertEquals(EVENT,sent.get("event_instance_id").intValue());
        assertTrue(sent.get("gui_observation_version").isIntegralNumber());assertEquals(2,sent.get("gui_observation_version").intValue());
        assertEquals(1,admissions.get());assertEquals(f.contract().sourceRef(),contract.sourceRef());
    }
}
