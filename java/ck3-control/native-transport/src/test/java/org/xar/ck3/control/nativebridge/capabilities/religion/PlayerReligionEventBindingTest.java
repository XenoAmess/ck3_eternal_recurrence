package org.xar.ck3.control.nativebridge.capabilities.religion;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEventEffects;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.application.planning.events.EventReadBinding;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventmaterial.RiteGrowthMaterial;
import org.xar.ck3.control.wave2.events.eventoutcome.RegisteredEventMaterial;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** Real pinned C++ fixture -> original decoder -> same installed contract -> planner publication -> material.
 * Controlled build/request-id remaps remain synthetic. The escaped original request id must be
 * rejected by the real wire decoder before a legal software envelope is built; no .4 Native credit.
 */
final class PlayerReligionEventBindingTest {
    @TempDir Path temporary;
    private static final ExactRef SOURCE=new ExactRef("synthetic-binding-installation-source",1,"a".repeat(64));
    private static final PlanningReadPort UNUSED=new PlanningReadPort(){
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("binding must receive the actual root read port");}
    };
    @Test void originalDecoderUsesIdenticalContractWithEmptyArgumentsAndPublishesTheActualZeroMaterial() throws Exception {
        var fixture=PlayerReligionContextReadTest.fixtureAt(temporary);ObjectNode nativeFrame=bindingPacket(fixture);PlayerReligionContextReadTest.remapFour((ObjectNode)nativeFrame.get("result"));
        ObjectNode component=(ObjectNode)nativeFrame.get("result").get("player_religion_context");component.put("schema",PlayerReligionContext.Build.CROZIER4.schema());PlayerReligionContextReadTest.remapFour(component);
        PlanningReadReceipt original=fixture.receipt(nativeFrame);PlanningRequest current=planning(original);
        var read=new PlayerReligionContextRead(UNUSED,new PlayerReligionContextRead.Sources(SOURCE,SOURCE,SOURCE),(sources,request)->{});
        var binding=PlayerReligionEventBinding.bind(read);AtomicInteger calls=new AtomicInteger();
        PlanningReadPort root=known(read.contract(),original,calls);
        var result=assertInstanceOf(org.xar.ck3.control.application.planning.events.EventReadBinding.Captured.class,binding.read(root,current));assertEquals(1,calls.get());var resolved=binding.query().resolve(materialFrame(current));assertSame(read.contract(),resolved.contract());
        var effects=new NativeEventEffects.MaterialQueries(Optional.empty(),Optional.of(binding.query()));assertSame(binding.query(),effects.religionContext().orElseThrow());
        assertTrue(resolved.request().arguments().members().isEmpty());assertTrue(result.replayContext().isEmpty());assertFalse(result.history().members().containsKey("native_read_replay_context"));
        JsonNode next=OpportunityJson.toNode(result.publication().snapshot().orElseThrow());
        var observed=RiteGrowthMaterial.decodeObservation(next.get(RiteGrowthMaterial.SNAPSHOT_FIELD));assertEquals(RiteGrowthMaterial.Status.AVAILABLE,observed.status());assertEquals(BigInteger.ZERO,observed.fulfillmentRaw());
        ObjectNode decision=StrictJson.object().put("status","recommended").put("event_definition_key",RiteGrowthMaterial.EVENT).put("ck3_build","1.20.0.4").put("selected_option_number",1).put("selected_native_option_index",0);
        var material=RegisteredEventMaterial.plan(retained(decision),retained(next)).orElseThrow();
        assertEquals("ready",StrictJson.parse(RetainedJson.encode(material)).get("status").textValue());
        assertEquals(BigInteger.ZERO,StrictJson.parse(RetainedJson.encode(material)).get("starting_value").bigIntegerValue());
        assertEquals(original.requestId(),result.requestId());assertEquals(read.contract().contractId(),result.contractId());assertNotNull(result.originalReceipt());
    }
    @Test void actualUnavailableReadNeverInvokesPublisherOrRetriesAndPublicationCannotChangeTheFrozenFrame() throws Exception {
        var fixture=PlayerReligionContextReadTest.fixtureAt(temporary);ObjectNode nativeFrame=bindingPacket(fixture);PlayerReligionContextReadTest.remapFour((ObjectNode)nativeFrame.get("result"));
        ObjectNode component=(ObjectNode)nativeFrame.get("result").get("player_religion_context");component.put("schema",PlayerReligionContext.Build.CROZIER4.schema());PlayerReligionContextReadTest.remapFour(component);
        PlanningReadReceipt original=fixture.receipt(nativeFrame);PlanningRequest current=planning(original);
        var read=new PlayerReligionContextRead(UNUSED,new PlayerReligionContextRead.Sources(SOURCE,SOURCE,SOURCE),(sources,request)->{});var binding=PlayerReligionEventBinding.bind(read);
        AtomicInteger calls=new AtomicInteger();PlanningReadPort unavailable=new PlanningReadPort(){
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> actual,PlanningReadRequest request){calls.incrementAndGet();assertSame(read.contract(),actual);assertTrue(request.arguments().members().isEmpty());return new PlanningReadResult.Unavailable<>("actual unavailable fixture",Optional.empty());}
        };
        var rejectedPublisher=new EventReadBinding<>(binding.query(),(request,value)->{throw new AssertionError("unavailable typed read cannot publish a material observation");});
        assertInstanceOf(org.xar.ck3.control.application.planning.events.EventReadBinding.Unavailable.class,rejectedPublisher.read(unavailable,current));assertEquals(1,calls.get());
        var drifted=new EventReadBinding<>(binding.query(),(request,value,actualEncoded)->{
            EventPolicies.ReadPublication actual=binding.publication().publish(request,value,actualEncoded);
            return new EventPolicies.ReadPublication(actual.result(),Optional.of(actual.snapshot().orElseThrow().with("native_revision",new OpportunityJson.IntegerValue(BigInteger.valueOf(999)))));
        });
        assertThrows(IllegalArgumentException.class,()->drifted.read(known(read.contract(),original,new AtomicInteger()),current));
    }
    private static ObjectNode bindingPacket(PlayerReligionContextReadTest fixture) throws Exception {
        ObjectNode original = fixture.fixture("current-zero");
        assertEquals("religion\"mailbox-fixture", original.get("request_id").textValue());
        assertThrows(java.io.IOException.class, () -> NativeWire.decode(NativeWire.packet(StrictJson.canonical(original))));
        ObjectNode software = original.deepCopy();
        software.put("request_id", "software-event-binding-read");
        assertEquals(original.get("result"), software.get("result"));
        return software;
    }
    private static org.xar.ck3.control.application.effects.EventMaterialQuerySource.Frame materialFrame(PlanningRequest current) {
        return new org.xar.ck3.control.application.effects.EventMaterialQuerySource.Frame(current.before(),current.source(),current.sessionId(),current.observations().snapshot(),current.deadline());
    }
    @Test void currentSourceResolutionRetainsExactOriginalContextAndRejectsAnotherIssuedFrameBeforeReading() throws Exception {
        var fixture=PlayerReligionContextReadTest.fixtureAt(temporary); ObjectNode packet=bindingPacket(fixture);
        PlayerReligionContextReadTest.remapFour((ObjectNode)packet.get("result"));
        ObjectNode component=(ObjectNode)packet.get("result").get("player_religion_context");
        component.put("schema",PlayerReligionContext.Build.CROZIER4.schema());PlayerReligionContextReadTest.remapFour(component);
        PlanningReadReceipt original=fixture.receipt(packet);PlanningRequest current=planning(original);
        var read=new PlayerReligionContextRead(UNUSED,new PlayerReligionContextRead.Sources(SOURCE,SOURCE,SOURCE),(sources,request)->{});
        var fixed=PlayerReligionEventBinding.bind(read); var resolves=new AtomicInteger();
        Path contextFile=temporary.resolve("synthetic-issued-selection-context.json");
        byte[] contextBytes=StrictJson.canonical(StrictJson.object().put("scope","synthetic-query-source-context"));
        java.nio.file.Files.write(contextFile,contextBytes);
        ExactRef sidecar=new ExactRef(contextFile.toString(),contextBytes.length,org.xar.ck3.control.application.driver.DriverJson.sha256(contextBytes));
        var source=new org.xar.ck3.control.application.effects.EventMaterialQuerySource<PlayerReligionContextRead.Observation>() {
            @Override public OperationKey operation(){return fixed.operation();}
            @Override public Resolved<PlayerReligionContextRead.Observation> resolve(Frame frame){
                resolves.incrementAndGet();assertEquals(materialFrame(current),frame);
                var selected=fixed.query().resolve(frame);
                return new Resolved<>(selected.contract(),selected.request(),value->{
                    ObjectNode complete=(ObjectNode)StrictJson.parse(selected.encode().apply(value).bytes());
                    complete.set("synthetic_original_selection_context",sidecar.toJson());
                    return new RawJson(StrictJson.canonical(complete));
                },Optional.of(sidecar));
            }
            @Override public Resolved<PlayerReligionContextRead.Observation> restore(Frame frame,PlanningReadReceipt receipt,Optional<ExactRef> retained,ActionPorts.OutcomeArchive archive){
                throw new AssertionError("a live planning read cannot restore from an archive or current fallback");
            }
        };
        var publications=new AtomicInteger();
        var binding=new EventReadBinding<>(source,(request,value,actualEncoded)->{
            publications.incrementAndGet();
            assertEquals(sidecar,ExactRef.fromJson(StrictJson.parse(actualEncoded.bytes()).get("synthetic_original_selection_context")));
            return fixed.publication().publish(request,value,actualEncoded);
        });var calls=new AtomicInteger();
        var captured=assertInstanceOf(org.xar.ck3.control.application.planning.events.EventReadBinding.Captured.class,binding.read(known(read.contract(),original,calls),current));
        assertSame(source,binding.query());assertEquals(1,resolves.get());assertEquals(1,calls.get());assertEquals(1,publications.get());assertEquals(Optional.of(sidecar),captured.replayContext());
        JsonNode history=OpportunityJson.toNode(captured.history());assertEquals(sidecar,ExactRef.fromJson(history.get("native_read_replay_context")));
        assertEquals(captured.originalReceipt(),ExactRef.fromJson(history.get("native_read_original_receipt")));
        var wrong=new org.xar.ck3.control.application.effects.EventMaterialQuerySource<PlayerReligionContextRead.Observation>() {
            @Override public OperationKey operation(){return source.operation();}
            @Override public Resolved<PlayerReligionContextRead.Observation> resolve(Frame frame){
                var selected=source.resolve(frame);var request=selected.request();
                var drifted=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),request.operation(),request.arguments(),request.deadline().plusMillis(1));
                return new Resolved<>(selected.contract(),drifted,selected.encode(),selected.replayContext());
            }
            @Override public Resolved<PlayerReligionContextRead.Observation> restore(Frame frame,PlanningReadReceipt receipt,Optional<ExactRef> retained,ActionPorts.OutcomeArchive archive){throw new AssertionError("not an archive test");}
        };
        calls.set(0);var drifted=new EventReadBinding<>(wrong,fixed.publication());
        assertThrows(IllegalArgumentException.class,()->drifted.read(known(read.contract(),original,calls),current));assertEquals(0,calls.get());
    }
    private static PlanningReadPort known(ReadContract<PlayerReligionContextRead.Observation> expected,PlanningReadReceipt original,AtomicInteger calls) {
        return new PlanningReadPort(){
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> actual,PlanningReadRequest request){
                calls.incrementAndGet();assertSame(expected,actual);assertTrue(request.arguments().members().isEmpty());assertEquals(original.request().before(),request.before());assertEquals(original.request().source(),request.source());
                PlanningReadReceipt receipt=new PlanningReadReceipt(request,actual.contractId(),original.requestId(),original.before(),original.after(),original.original());
                return new PlanningReadResult.Known<>(actual.decode(receipt),receipt,original.before().binding().nativeEvidence());
            }
        };
    }
    private static PlanningRequest planning(PlanningReadReceipt receipt) {
        var request=receipt.request();ObjectNode snapshot=PlayerReligionContextReadTest.snapshot();snapshot.put("episode_run_id",request.before().frame().episodeRunId());
        snapshot.putArray("active_wars");snapshot.putArray("player_armies");
        snapshot.putObject("active_event").put("instance_id",29).put("option_count",3);
        var observation=new PlanningObservation(object(snapshot),List.of(),Set.of(PlayerReligionContextRead.OPERATION),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(request.before(),request.source(),request.sessionId(),request.deadline(),observation);
    }
    private static OpportunityJson.Obj object(JsonNode value){return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"synthetic binding fixture");}
    private static RetainedJson.ObjectValue retained(JsonNode value){return RetainedJson.object(RetainedJson.parse(StrictJson.canonical(value)));}
}
