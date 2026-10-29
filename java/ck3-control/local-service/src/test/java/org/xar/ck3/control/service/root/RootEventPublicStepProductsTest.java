package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.application.planning.events.EventSelectionPublicResult;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Actual software READ/preparation/effect/archive/formatter producers and EXECUTE callback helpers.
 * No current Root, ManagedGame, Catalog owner guard or private/native submit authority is fabricated.
 * Full install -> RootPublicStepExecution.execute -> once coordinator remains NOT_RUN_REQUIRED. */
final class RootEventPublicStepProductsTest {
    @TempDir Path temporary;
    @BeforeAll static void originalInputs()throws Exception{PendingUiEventPreparationTest.originalProducers();}

    @Test void exactEventSelectorsNeverClaimCharacterInteractionOrUnsupportedOptionShapes(){
        assertTrue(RootEventPublicStepProducts.selectsRead(new OperationKey(EventWindowRead.STEP)));
        for(String step:List.of("select-event-option-1","select-event-option-4","select-event-option-999999999")){
            assertTrue(RootEventPublicStepProducts.selectsOption(new OperationKey(step)));assertFalse(RootEventPublicStepProducts.selectsRead(new OperationKey(step)));
        }
        for(String step:List.of("query-pending-character-interaction-context-v1","accept-pending-character-interaction","reject-pending-character-interaction",
                "acknowledge-pending-character-interaction","block-pending-character-interaction","select-event-option-0","select-event-option-01",
                "select-event-option-1000000000","select-event-option-1-extra","query-current-event-window-context-v2")){
            assertFalse(RootEventPublicStepProducts.selectsOption(new OperationKey(step)));assertFalse(RootEventPublicStepProducts.selectsRead(new OperationKey(step)));
        }
    }

    @Test void originalExecuteRequestSerdeKeepsMissingNullAndExplicitRevisionForEventProducts(){
        for(var revision:List.<PublicPlanningCodec.Revision>of(new PublicPlanningCodec.RevisionMissing(),new PublicPlanningCodec.RevisionNull(),new PublicPlanningCodec.RevisionValue(BigInteger.valueOf(9)))){
            var request=caller("select-event-option-4",revision);RawJson encoded=PublicPlanningCodec.encodeExecute(request);
            assertEquals(request,PublicPlanningCodec.decodeExecute(new PublicBindings.Value(encoded)));
            assertTrue(RootEventPublicStepProducts.selectsOption(request.step()));
        }
        for(String invalid:List.of("{\"step\":true}","{\"step\":\"select-event-option-4\",\"expected_revision\":false}",
                "{\"step\":\"select-event-option-4\",\"expected_revision\":9.0}","{\"step\":\"select-event-option-4\",\"option_number\":4}"))
            assertThrows(IllegalArgumentException.class,()->PublicPlanningCodec.decodeExecute(new PublicBindings.Value(raw(invalid))));
    }

    @Test void executeReadUsesActualOriginalContractAndSamePublicEncoderAsIndependentQuery()throws Exception{
        var helper=new RootEventWindowPublicProductsTest();helper.temporary=temporary;
        var f=helper.fixture("execute-event-read",4242,9007199254740993L,"available");
        var original=planning(f);var caller=caller(EventWindowRead.STEP,new PublicPlanningCodec.RevisionValue(original.before().frame().revision()));
        var reads=new AtomicInteger();PlanningReadPort port=port(f,reads);
        byte[] archived=f.archive().archive.loadRead(f.retained()).original().originalFrame().bytes();
        RawJson result=RootEventPublicStepProducts.readOriginal(port,f.contract(),original,caller,f.archive().archive);
        assertEquals(1,reads.get());var node=node(result);
        assertEquals("9007199254740993",node.path("queried_revision").textValue());assertEquals("17",node.path("queried_native_revision").textValue());
        assertEquals("1",node.path("query_sequence").textValue());assertEquals("17",node.path("current_event_window_context").path("snapshot_revision").textValue());
        assertEquals(EventWindowService.PUBLIC64_WIRE_ENCODING,node.path("event_window_wire_encoding").textValue());
        assertEquals("9007199254740993",node.path("source").path("revision").textValue());assertEquals("9007199254740993",node.path("binding").path("expected_revision").textValue());
        assertEquals(f.window().get("options"),node.get("options"));assertEquals(f.event(),node.path("current_event_instance_id").intValue());
        RawJson independent=EventWindowService.encode(f.service().query_current_event_window_context_v1(new EventWindowService.Query(f.event(),original.before().frame().revision())));
        assertEquals(result,independent);
        assertEquals(result,roundtrip(result));assertArrayEquals(archived,f.archive().archive.loadRead(f.retained()).original().originalFrame().bytes());
        assertTrue(f.contract().decode(f.receipt()).result().get("queried_revision") instanceof OpportunityJson.IntegerValue,"native/archive publication stays numeric");
        var stale=caller(EventWindowRead.STEP,new PublicPlanningCodec.RevisionValue(BigInteger.ONE));
        assertEquals(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,assertThrows(PublicServiceFailure.class,
                ()->RootEventPublicStepProducts.readOriginal(port,f.contract(),original,stale,f.archive().archive)).kind());
        var absent=original.observations();var noCapability=new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),
                new PlanningObservation(absent.snapshot(),absent.history(),absent.actionSteps(),Set.of(),absent.battleSpeedReadiness(),absent.actionFacts(),absent.campaignGoal(),absent.crossRunPlan(),absent.initialLifestyleFocusRequired()));
        assertEquals(PublicServiceFailure.Kind.UNSUPPORTED_STEP,assertThrows(PublicServiceFailure.class,()->RootEventPublicStepProducts.readOriginal(port,f.contract(),noCapability,stale,f.archive().archive)).kind());
        var invalidEvent=withSnapshot(original,original.observations().snapshot().with("active_event",OpportunityJson.Nil.INSTANCE));
        assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,assertThrows(PublicServiceFailure.class,
                ()->RootEventPublicStepProducts.readOriginal(port,f.contract(),invalidEvent,stale,f.archive().archive)).kind());assertEquals(1,reads.get());
    }

    @Test void eventActionCheapChecksPrecedeRevisionWithoutReadingOrSubmitting()throws Exception{
        var helper=new RootEventWindowPublicProductsTest();helper.temporary=temporary;var f=helper.fixture("original-check-order",4242,9,"available");
        var original=planning(f);var event=OpportunityJson.object(original.observations().snapshot().get("active_event"),"actual fixture event")
                .with("option_count",new OpportunityJson.IntegerValue(BigInteger.valueOf(4)));
        var valid=withSnapshot(original,original.observations().snapshot().with("active_event",event));
        var current=caller("select-event-option-4",new PublicPlanningCodec.RevisionValue(BigInteger.valueOf(9)));
        var stale=caller("select-event-option-4",new PublicPlanningCodec.RevisionValue(BigInteger.ONE));
        var option=EventActionPreparation.option(current.step());
        assertEquals(f.event(),RootEventPublicStepProducts.optionFrame(valid,f.contract(),current,option));
        assertEquals(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,assertThrows(PublicServiceFailure.class,
                ()->RootEventPublicStepProducts.optionFrame(valid,f.contract(),stale,option)).kind());
        for(var bad:List.of(valid.observations().snapshot().with("map_ready",new OpportunityJson.Bool(false)),
                valid.observations().snapshot().with("paused",new OpportunityJson.Bool(false)),
                valid.observations().snapshot().with("active_event",OpportunityJson.Nil.INSTANCE),
                valid.observations().snapshot().with("active_event",event.with("instance_id",new OpportunityJson.Bool(true))),
                valid.observations().snapshot().with("active_event",event.with("option_count",new OpportunityJson.Bool(true))),
                valid.observations().snapshot().with("active_event",event.with("option_count",new OpportunityJson.IntegerValue(BigInteger.valueOf(3)))))){
            var changed=withSnapshot(valid,bad);
            assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,assertThrows(PublicServiceFailure.class,
                    ()->RootEventPublicStepProducts.optionFrame(changed,f.contract(),stale,option)).kind());
        }
    }

    @Test void publicWindowCodecKeepsDeclaredWideRolesAndRejectsMalformedOrUndeclaredNumbers()throws Exception{
        var helper=new RootEventWindowPublicProductsTest();helper.temporary=temporary;var f=helper.fixture("wire-boundaries",4242,9,"available");
        var original=f.contract().decode(f.receipt());var maximum=StrictJson.UINT64_MAX;
        var wide=new EventPolicies.ReadPublication(original.result().with("query_sequence",new OpportunityJson.IntegerValue(maximum)),original.snapshot());
        RawJson encoded=encode(f,wide);assertEquals(maximum.toString(),node(encoded).path("query_sequence").textValue());assertEquals(encoded,roundtrip(encoded));
        for(var wrong:List.<OpportunityJson.Value>of(OpportunityJson.Nil.INSTANCE,new OpportunityJson.Bool(true),new OpportunityJson.DecimalValue("1.0"),new OpportunityJson.Text("1"),new OpportunityJson.IntegerValue(maximum.add(BigInteger.ONE)))){
            var bad=new EventPolicies.ReadPublication(original.result().with("query_sequence",wrong),original.snapshot());assertThrows(IllegalArgumentException.class,()->encode(f,bad));
        }
        var undeclared=new EventPolicies.ReadPublication(original.result().with("unrecognized_identity",new OpportunityJson.IntegerValue(maximum)),original.snapshot());
        assertThrows(IllegalArgumentException.class,()->encode(f,undeclared));
        var decoded=EventWindowService.decode(new PublicBindings.Value(raw("{\"event_instance_id\":1,\"expected_revision\":\"18446744073709551615\"}")));
        assertEquals(maximum,decoded.expectedRevision());
        for(String bad:List.of("null","true","1.0","9007199254740992","\"01\"","\"-1\"","\"18446744073709551616\""))
            assertThrows(IllegalArgumentException.class,()->EventWindowService.decode(new PublicBindings.Value(raw("{\"event_instance_id\":1,\"expected_revision\":"+bad+"}"))));
        var unavailable=new PlanningReadResult.Unavailable<EventPolicies.ReadPublication>("actual original read unavailable",Optional.empty());
        assertSame(unavailable,assertThrows(EventWindowService.ReadUnavailable.class,()->EventWindowService.encode(new EventWindowService.Response(unavailable))).original());
    }

    @Test void preparedEventCommandAndActualAfterFormatterRetainUnknownAckAndIndependentWindowProof()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("execute-choice"),16*1024*1024)){
            disk.writer.locked(same->{var archive=disk.archive.withSession(same);var fixture=new PendingUiEventPreparationTest.Inputs(disk,archive,same);
                var current=fixture.event(true);var prepared=fixture.eventPreparation(current,fixture.eventContext(true),1,"execute-format-applied");
                var command=ActionCodec.decodeCommand(ActionCodec.encodeCommand(prepared.command()));assertEquals(prepared.command(),command);
                assertEquals("select-event-option-4",EventActionPreparation.prepare(command).step());
                var applied=fixture.effect(prepared,current,fixture.next(current),false);assertTrue(applied.applied().isPresent());assertTrue(applied.ack().isEmpty());
                var verified=EventSelectionPublicResult.encode(applied,NativeEffectEvidence.load(applied,archive,new DriverFrameEvidenceLoader(new DriverObservationAssembler())));
                var result=RootEventPublicStepProducts.presentOriginal(applied,archive,Optional.of(verified));var node=node(result);
                assertEquals("9007199254740994",node.path("revision").textValue());assertTrue(node.path("event_selection").path("postcondition_verified").booleanValue());
                assertTrue(node.path("active_event").isNull());assertTrue(node.path("action_receipt").path("old_instance_advanced").booleanValue());assertFalse(node.path("action_receipt").path("ack_received").booleanValue());
                assertEquals(result,EventOptionPublicResponse.parse(roundtrip(result)).original());
                for(boolean ack:List.of(false,true)){
                    var held=fixture.eventPreparation(current,fixture.eventContext(true),2,ack?"execute-format-ack":"execute-format-unknown");
                    var unresolved=fixture.effect(held,current,fixture.later(current,false),ack);
                    RawJson unknown=RootEventPublicStepProducts.presentOriginal(unresolved,archive,Optional.empty());var pending=node(unknown);
                    assertEquals("action_state_unknown",pending.path("status").textValue());assertFalse(pending.path("event_material_result_available").booleanValue());
                    assertTrue(pending.path("action_receipt").path("old_instance_advanced").isNull());assertEquals(ack,pending.path("action_receipt").path("ack_received").booleanValue());
                    assertEquals(unresolved,archive.loadReceipt(org.xar.ck3.control.contracts.ExactRef.fromJson(pending.path("action_receipt").get("original_receipt"))));
                    assertEquals(unknown,EventOptionPublicResponse.parse(roundtrip(unknown)).original());
                }
                return null;});
        }
    }

    private static PlanningRequest planning(RootEventWindowPublicProductsTest.Fixture fixture){
        var original=fixture.receipt().request();return new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),
                new PlanningObservation(original.arguments(),List.of(),Set.of(original.operation()),Set.of(EventWindowRead.CAPABILITY),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static PlanningRequest withSnapshot(PlanningRequest original,OpportunityJson.Obj snapshot){
        var observed=original.observations();return new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),
                new PlanningObservation(snapshot,observed.history(),observed.actionSteps(),observed.bridgeCapabilities(),observed.battleSpeedReadiness(),
                        observed.actionFacts(),observed.campaignGoal(),observed.crossRunPlan(),observed.initialLifestyleFocusRequired()));
    }
    private static PlanningReadPort port(RootEventWindowPublicProductsTest.Fixture f,AtomicInteger calls){return new PlanningReadPort(){
        @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
            assertSame(f.contract(),contract);assertEquals(f.receipt().request(),request);calls.incrementAndGet();contract.prepare(request,f.receipt().requestId());
            var original=f.archive().archive.loadRead(f.retained());return new PlanningReadResult.Known<>(contract.decode(original),original,f.retained());
        }};
    }
    private static RawJson encode(RootEventWindowPublicProductsTest.Fixture f,EventPolicies.ReadPublication value){return EventWindowService.encode(new EventWindowService.Response(new PlanningReadResult.Known<>(value,f.receipt(),f.retained())));}
    private static PublicPlanningCodec.ExecuteRequest caller(String step,PublicPlanningCodec.Revision revision){return new PublicPlanningCodec.ExecuteRequest(new OperationKey(step),revision,new PublicPlanningCodec.FrameMissing());}
    private static ObjectNode node(RawJson value){return (ObjectNode)DriverJson.toNode(DriverJson.object(value.bytes(),8*1024*1024));}
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static RawJson roundtrip(RawJson original){return new RawJson(DriverJson.encode(DriverJson.object(original.bytes(),8*1024*1024)));}
}
