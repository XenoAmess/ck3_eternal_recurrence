package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionFixtures.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Original native pending producer, sole contract, receipt publication, and actual foreground collector. */
final class PendingEventCollectorTest {
    @Test void sameInstalledPendingContractPublishesOriginalSignedInstanceIntoCollectorHistory() {
        var held=context();var contract=PendingInteractionContracts.pending(SOURCE);
        var arguments=PendingInteractionReadArguments.current(held);
        var request=new PlanningReadRequest(held.before(),held.source(),held.sessionId(),contract.operation(),arguments,held.deadline());
        assertEquals(PENDING,parse(contract.prepare(request,"pending-event-wire").additionalFields()).get("pending_interaction_id").intValue());
        var guard=new PlanningReadGuard(new GuardEvidence(held.before(),held.source(),held.sessionId(),BigInteger.ONE,contract.operation(),SOURCE,SOURCE,"declared-only",NOW,held.deadline()),true,true,true,"b".repeat(64));
        var token=wire(held,"spar_with_knight_interaction");token.remove(java.util.List.of("queried_snapshot_id","queried_revision","queried_native_revision"));token.put("backend_id","native-headless");String id="original-pending-event-read";
        var packet=F.objectNode().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);packet.set("result",token);
        byte[] bytes=packet.toString().getBytes(StandardCharsets.UTF_8);
        var original=new NativeActionPort.AckReceived(id,true,Optional.of(encode(token)),new RawJson(bytes),packet(bytes));
        var receipt=new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,original);
        AtomicInteger reads=new AtomicInteger(),publications=new AtomicInteger();
        var same=new PlanningReadPort(){
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> actual,PlanningReadRequest received) {
                assertSame(contract,actual);assertEquals(request,received);reads.incrementAndGet();
                return new PlanningReadResult.Known<>(actual.decode(receipt),receipt,SOURCE);
            }
        };
        var binding=EventReadBinding.actualReceipt(contract,actual->PendingInteractionReadArguments.current(held),known->{
            assertSame(receipt,known.receipt());assertEquals(SOURCE,known.originalReceipt());publications.incrementAndGet();
            return new EventPolicies.ReadPublication(InteractionReadPublications.pending(known),Optional.empty());
        });
        var planning=new PlanningRequest(held.before(),held.source(),held.sessionId(),held.deadline(),
                new PlanningObservation(InteractionArguments.app(snapshot(held)),List.of(),Set.of(contract.operation()),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var captured=assertInstanceOf(org.xar.ck3.control.application.planning.events.EventReadBinding.Captured.class,binding.read(same,planning));
        assertEquals(1,reads.get());assertEquals(1,publications.get());assertEquals(SOURCE,captured.originalReceipt());assertTrue(captured.replayContext().isEmpty());
        var history=captured.history();assertEquals(new OpportunityJson.Text(contract.operation().value()),history.get("command"));
        assertEquals(new OpportunityJson.Text(contract.contractId()),history.get("read_contract_id"));
        assertEquals(new OpportunityJson.Text(id),history.get("native_read_request_id"));
        assertEquals(new OpportunityJson.IntegerValue(BigInteger.valueOf(PENDING)),OpportunityJson.object(captured.publication().result().get("pending_character_interaction_context"),"pending context").get("pending_interaction_id"));
        assertThrows(IllegalStateException.class,binding::query);
    }
    @Test void actualEventPolicyCollectsItsOriginalPendingReadBeforeUnavailableSourceDiagnostic() {
        var held=context();var contract=PendingInteractionContracts.pending(SOURCE);AtomicInteger readCount=new AtomicInteger(),captureCount=new AtomicInteger();
        var binding=EventReadBinding.actualReceipt(contract,actual->PendingInteractionReadArguments.current(held),known->
                new EventPolicies.ReadPublication(InteractionReadPublications.pending(known),Optional.empty()));
        PlanningReadPort originalReads=new PlanningReadPort(){
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> actual,PlanningReadRequest request) {
                assertSame(contract,actual);readCount.incrementAndGet();String id="event-policy-original";
                var guard=new PlanningReadGuard(new GuardEvidence(held.before(),held.source(),held.sessionId(),BigInteger.ONE,actual.operation(),SOURCE,SOURCE,"declared-only",NOW,held.deadline()),true,true,true,"b".repeat(64));
                var token=wire(held,"spar_with_knight_interaction");token.remove(java.util.List.of("queried_snapshot_id","queried_revision","queried_native_revision"));token.put("backend_id","native-headless");var frame=F.objectNode().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);frame.set("result",token);
                byte[] bytes=frame.toString().getBytes(StandardCharsets.UTF_8);var ack=new NativeActionPort.AckReceived(id,true,Optional.of(encode(token)),new RawJson(bytes),packet(bytes));
                var receipt=new PlanningReadReceipt(request,actual.contractId(),id,guard,guard,ack);
                return new PlanningReadResult.Known<>(actual.decode(receipt),receipt,SOURCE);
            }
        };
        var planning=new PlanningRequest(held.before(),held.source(),held.sessionId(),held.deadline(),new PlanningObservation(InteractionArguments.app(snapshot(held)),List.of(),Set.of(contract.operation()),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        EventIncidentCapturePort captures=(actual,diagnosis)->{
            captureCount.incrementAndGet();assertEquals(held.before(),actual.before());assertEquals(1,actual.observations().history().size());
            assertEquals(new OpportunityJson.Text("event-policy-original"),actual.observations().history().getFirst().get("native_read_request_id"));
            assertNotNull(diagnosis.get("unhandled_native_window_diagnostic"));
        };
        var continuation=EventPolicies.policies(SOURCE,Optional.empty(),(actual,operation,plan,trait)->Optional.empty(),originalReads,
                List.of(binding),(actual,raw)->Optional.empty(),captures,
                (actual,operation,args,plan,purpose,domain)->{throw new AssertionError("pending collector test must not invoke the shared command producer");}).stream().filter(policy->policy.stage()==PlanningStage.EVENT_AND_INTERACTION_CONTINUATION).findFirst().orElseThrow();
        var previous=new OrdinaryPolicy.Draft("fixture","pending","actual pending collector",OrdinaryPolicy.Kind.FOREGROUND,Optional.empty(),OrdinaryPolicy.Purpose.READ_ONLY,Optional.empty(),new OpportunityJson.Obj(java.util.Map.of()));
        assertInstanceOf(OrdinaryPolicy.Wait.class,continuation.evaluate(planning,previous));assertEquals(1,readCount.get());assertEquals(1,captureCount.get());
    }
    private static byte[] packet(byte[] raw) {
        try { return NativeWire.packet(raw); }catch(java.io.IOException invalid){throw new AssertionError("synthetic original native packet malformed",invalid);}
    }
}
