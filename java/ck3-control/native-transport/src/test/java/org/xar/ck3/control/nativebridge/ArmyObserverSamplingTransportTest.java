package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling;

/** Actual software packet port -> unchanged production transport -> exact typed sampling wire consumer. No OS pipe or Game. */
final class ArmyObserverSamplingTransportTest {
    @Test void realReadAndBothSubmitBranchesUseOnlyTheirOriginalPacketAndConsumedPermit()throws Exception {
        for(String step:List.of(ArmyObserverSampling.QUERY,ArmyObserverSampling.ENABLE,ArmyObserverSampling.DISABLE)){
            Replay port=new Replay();try(var transport=new NativeGameTransport(port,config(),16,16)){
                var original=transport.observe(Instant.now().plusSeconds(5));var operation=new OperationKey(step);var selected=new ArmyObserverSampling.Selection(ArmyObserverSampling.Family.REGULAR_CORE,Optional.empty());var request=ArmyObserverSampling.request(step,selected);var guard=guard(transport,operation);
                NativeActionPort.DispatchOutcome actual;
                if(step.equals(ArmyObserverSampling.QUERY)){
                    ExactRef source=ref("controlled-native-definition",new byte[]{1});
                    var contract=new ReadContract<>("controlled-sampling-query",operation,Optional.of(ArmyObserverSampling.CAPABILITY),"controlled-sampling",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,source,ignored->request,receipt->ArmyObserverSampling.decode(receipt.original().originalResultToken().orElseThrow(),step,selected));
                    var read=new PlanningReadRequest(guard.observed(),guard.source(),guard.sessionId(),operation,new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),guard.validUntil());var permit=NativeSelectorReadFixture.issue(contract,read,request,new PlanningReadGuard(guard,true,true,true,"b".repeat(64)),"sampling-read");
                    actual=transport.read(permit,request,guard.validUntil());assertTrue(permit.consumed());
                }else{
                    var post=new ProposalLifecycle.ExpectedPostcondition(1,guard.observed(),guard.source(),ArmyObserverSampling.OBSERVER,ArmyObserverSampling.expected(step.equals(ArmyObserverSampling.ENABLE),selected.family()));
                    var command=new ActionCommand("sampling-original-"+step,guard.observed(),guard.source(),guard.sessionId(),operation,new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),post,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),guard.validUntil());
                    var permit=NativeTransportSubmissionFixture.issue(command,guard,request,"sampling-set");actual=transport.submit(permit,request,guard.validUntil());assertTrue(permit.consumed());
                    assertInstanceOf(NativeActionPort.Unknown.class,transport.submit(permit,request,guard.validUntil()));
                }
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,actual);ArmyObserverSampling.verifyAck(ack,step,selected,guard.observed());
                assertEquals(1,port.writes);assertArrayEquals(port.outbound,ack.outbound().orElseThrow().originalPacket());assertTrue(transport.originalRequestChronology(ack.requestId()).isPresent());
                var decoded=ArmyObserverSampling.decode(ack.originalResultToken().orElseThrow(),step,selected);assertTrue(decoded.accepted());
                if(step.equals(ArmyObserverSampling.QUERY)) {
                    var full=ArmyObserverSampling.driverResult(decoded,guard.observed(),guard.connectionGeneration());var exposed=ArmyObserverSampling.publicResult(decoded,guard.observed(),guard.connectionGeneration());
                    var roles=org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers.fromResults(full,exposed);
                    var projection=new org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Projection(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Kind.ARMY_OBSERVER_SAMPLING,full,roles,List.of(ref("actual-producer-data",new byte[]{1})));
                    assertEquals(full,projection.fullResult());assertEquals(roles,projection.publicNumbers());
                }
                assertSame(original,transport.latestObservedSnapshot().orElseThrow());
            }
        }
    }
    @Test void actualIncompleteOriginalIsReturnedAsDataWithoutSettlingOrResubmittingCanonicalUnknown()throws Exception {
        Replay port=new Replay(true);try(var transport=new NativeGameTransport(port,config(),16,16)){
            transport.observe(Instant.now().plusSeconds(5));var operation=new OperationKey(ArmyObserverSampling.DISABLE);var selected=new ArmyObserverSampling.Selection(ArmyObserverSampling.Family.REGULAR_CORE,Optional.empty());var request=ArmyObserverSampling.request(operation.value(),selected);var guard=guard(transport,operation);
            var args=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(request.additionalFields().bytes()),"actual sampling fields");
            var post=new ProposalLifecycle.ExpectedPostcondition(1,guard.observed(),guard.source(),ArmyObserverSampling.OBSERVER,ArmyObserverSampling.expected(false,selected.family()));
            var command=new ActionCommand("incomplete-original",guard.observed(),guard.source(),guard.sessionId(),operation,args,post,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),guard.validUntil());
            var permit=NativeTransportSubmissionFixture.issue(command,guard,request,"incomplete-request");Instant submittedAt=Instant.now();var ack=assertInstanceOf(NativeActionPort.AckReceived.class,transport.submit(permit,request,guard.validUntil()));
            var attempt=new ActionState.Attempt(ack.requestId(),submittedAt,guard,request);var unknown=new ActionState.Unknown(Optional.of(attempt),Optional.of(ack),"actual control clear is incomplete",List.of(guard.nativeEvidence()));
            var actual=ArmyObserverSampling.incompleteOriginal(command,attempt,ack);assertFalse(actual.accepted());assertEquals(ArmyObserverSampling.CaptureStatus.BUSY,actual.rows().getFirst().status());
            assertSame(ack,unknown.dispatch().orElseThrow());assertEquals("incomplete",NativeWire.object(NativeWire.parse(ArmyObserverSampling.publicResult(actual,command.before(),guard.connectionGeneration()).bytes())).get("status").textValue());
            assertInstanceOf(NativeActionPort.Unknown.class,transport.submit(permit,request,guard.validUntil()));assertEquals(1,port.writes);
        }
    }
    private static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\sampling-software", "fixture-machine",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"fixture-session","fixture","0".repeat(64),"fixture");}
    private static GuardEvidence guard(NativeGameTransport transport,OperationKey operation)throws IOException {
        var frame=transport.latestObservedSnapshot().orElseThrow();var config=config();var identity=new ProposalLifecycle.ObservationIdentity(config.machineId(),config.game(),new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.valueOf(7),BigInteger.valueOf(1234)),frame.snapshotId(),BigInteger.valueOf(7),"fixture-episode"),1);var now=Instant.now();var source=new G2Source(config.machineId(),now.toString(),"controlled-sampling",ref("controlled",new byte[]{1}));
        return new GuardEvidence(identity,source,config.sessionId(),frame.session().connectionGeneration(),operation,ref("actual-snapshot",frame.originalPacket()),ref("actual-hello",transport.originalHello().packet().value()),"controlled",now,now.plusSeconds(15));
    }
    private static ExactRef ref(String path,byte[] bytes){return new ExactRef(path,bytes.length,ActionCodec.sha256(bytes));}
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> input=new ArrayDeque<>();int writes;byte[] outbound;final boolean incomplete;
        Replay()throws IOException {this(false);}
        Replay(boolean incomplete)throws IOException {this.incomplete=incomplete;String hello=NativeSnapshotWaitReceiverFixture.HELLO.replace("\"game.state.snapshot\"","\"game.state.snapshot\",\""+ArmyObserverSampling.CAPABILITY+"\"");input.add(NativeSnapshotWaitReceiverFixture.packet(hello));input.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.snapshot("sampling:7",7,NativeSnapshotWaitReceiverFixture.STATE.substring(0,NativeSnapshotWaitReceiverFixture.STATE.length()-1)+",\"diagnostics\":{},\"one_life_terminal_reason\":null}")));}
        public void verify(){}public void awaitConnection(Instant deadline){}public byte[] readPacket(Instant deadline)throws IOException {if(input.isEmpty())throw new IOException("software queue elapsed");return input.removeFirst();}public void close(){}
        public void writePacket(byte[] packet,Instant deadline)throws IOException {writes++;outbound=packet.clone();var request=NativeWire.decodeExecuteRequest(packet);boolean enable=!request.step().equals(ArmyObserverSampling.DISABLE);String row="{\"installed\":true,\"available\":true,\"capture_enabled\":"+enable+",\"busy\":false,\"clear_completed\":"+!enable+",\"epoch\":18446744073709551615,\"active_captures\":0,\"retained_records\":0,\"qualified_records\":0,\"status\":\""+(enable?"enabled":"disabled")+"\",\"readiness\":\""+(enable?"awaiting_sample":"off")+"\"}";
            String body="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":true,\"result\":{\"step\":\""+request.step()+"\",\"accepted\":true,\"status\":\"completed\",\"army_observer_research_sampling_v1\":{\"regular_core\":"+row+"}}}";if(incomplete)body=body.replace("\"accepted\":true","\"accepted\":false").replace("\"status\":\"completed\"","\"status\":\"incomplete\"").replace("\"busy\":false","\"busy\":true").replace("\"clear_completed\":true","\"clear_completed\":false").replace("\"active_captures\":0","\"active_captures\":1").replace("\"retained_records\":0","\"retained_records\":1").replace("\"status\":\"disabled\"","\"status\":\"busy\"");input.add(NativeWire.packet(body.getBytes(StandardCharsets.UTF_8)));}
    }
}
