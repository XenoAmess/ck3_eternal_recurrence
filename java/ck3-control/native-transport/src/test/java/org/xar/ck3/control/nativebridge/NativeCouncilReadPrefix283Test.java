package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.NativeTransportCouncilFixture;
import org.xar.ck3.control.application.action.council.CouncilContinuationModel.Stage;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.capabilities.governance.PrivateCouncilReads;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Software-only packet custody. This does not qualify any live Game/source or replay action 198. */
final class NativeCouncilReadPrefix283Test {
    @TempDir Path temporary;
    private static final String ASSIGN="private-assign-councillor-v1";
    private static final String RECEIPT="private-query-assign-councillor-receipt-v1";
    private static final String STATUS=CouncilPrivateCodec.STATUS, GATES=CouncilPrivateCodec.GATES;

    @Test void consumedActualReadPrefixAllowsOneAssignmentButStillRequiresItsIndependentReceipt() throws Exception {
        Fixture f=new Fixture("positive"); AtomicInteger statuses=new AtomicInteger();
        f.port.reaction=wire->{
            var request=NativeWire.decodeExecuteRequest(wire);String step=request.step();String value;
            if(step.equals(GATES)) value=pending(GATES);
            else if(step.equals(ASSIGN)||step.equals(RECEIPT)) value=pending(step);
            else {
                assertEquals(STATUS,step);int number=statuses.incrementAndGet();
                value=number==1?terminal(GATES,7):terminal(number==2?"assign-councillor-v1":"query-assign-councillor-receipt-v1",8);
            }
            f.port.reply(request.requestId(),value);
            if(step.equals(STATUS)&&statuses.get()==2)f.port.packets.add(packet(snapshot(8)));
        };
        try(var transport=f.transport()) {
            transport.observe(deadline());
            transport.withMailbox(deadline(),scope->{
                Instant until=deadline();var initial=f.read(transport,false,"gates",until);
                var terminal=f.read(transport,true,"gates-status",until);var prefix=List.of(initial,terminal);
                var before=f.guard(transport,ASSIGN,7);
                var request=new NativeRequest(ASSIGN,Optional.empty(),raw("{\"candidate_character_id\":73}"));
                assertEquals(2,f.port.writes);
                scope.consumeReadOnlyPrefix(prefix);
                assertThrows(IOException.class,()->scope.consumeReadOnlyPrefix(prefix));
                var permit=NativeTransportSubmissionFixture.issue(command(before),before,request,"actual-assign");
                var submitted=assertInstanceOf(NativeActionPort.AckReceived.class,transport.submit(permit,request,until));
                assertTrue(permit.consumed());assertEquals(3,f.port.writes);
                assertThrows(IOException.class,()->scope.complete(submitted));
                assertThrows(IOException.class,()->scope.consumeReadOnlyPrefix(prefix));
                NativeRequest status=new NativeRequest(STATUS,Optional.empty(),raw("{}"));
                var helper=NativeTransportCouncilFixture.issue(command(before).actionId(),"actual-assign","helper-status",Stage.HELPER_STATUS,before,status,()->{});
                var helperAck=transport.continueCouncil(helper,status,until);
                assertInstanceOf(NativeActionPort.AckReceived.class,helperAck);
                assertThrows(IOException.class,()->scope.complete(helperAck));
                transport.observe(until);var after=f.guard(transport,ASSIGN,8);
                NativeRequest receipt=new NativeRequest(RECEIPT,Optional.empty(),raw("{}"));
                var query=NativeTransportCouncilFixture.issue(command(before).actionId(),"actual-assign","receipt-query",Stage.RECEIPT_QUERY,after,receipt,()->{});
                assertInstanceOf(NativeActionPort.AckReceived.class,transport.continueCouncil(query,receipt,until));
                var finalPermit=NativeTransportCouncilFixture.issue(command(before).actionId(),"actual-assign","receipt-status",Stage.RECEIPT_STATUS,after,status,()->{});
                var actual=assertInstanceOf(NativeActionPort.AckReceived.class,transport.continueCouncil(finalPermit,status,until));
                scope.complete(actual);assertEquals(6,f.port.writes);return actual;
            });
            assertTrue(transport.mailboxDiagnostics().poison().isEmpty());
        }
    }

    @Test void incompleteReorderedCopiedOrWrongFrameReadPrefixesCannotUnlockAssignment() throws Exception {
        for(String variant:List.of("pending-only","reordered","copied-ack","wrong-frame","action-material")) {
            Fixture f=new Fixture(variant);
            f.port.reaction=wire->{var r=NativeWire.decodeExecuteRequest(wire);
                String result=r.step().equals(GATES)?pending(GATES):terminal(GATES,variant.equals("wrong-frame")?8:7);
                if(r.step().equals(STATUS)&&variant.equals("action-material"))result=result.substring(0,result.length()-1)+",\"native_action_submitted\":true}";
                f.port.reply(r.requestId(),result);
            };
            try(var transport=f.transport()) {
                transport.observe(deadline());
                assertThrows(IOException.class,()->transport.withMailbox(deadline(),scope->{
                    Instant until=deadline();var first=f.read(transport,false,"initial",until);
                    List<PlanningReadReceipt> prefix;
                    if(variant.equals("pending-only"))prefix=List.of(first);
                    else {
                        var last=f.read(transport,true,"status",until);prefix=List.of(first,last);
                        if(variant.equals("reordered"))prefix=List.of(last,first);
                        if(variant.equals("copied-ack")) {
                            var a=last.original();var copy=new NativeActionPort.AckReceived(a.requestId(),a.nativeOk(),a.originalResultToken(),a.originalFrame(),a.originalPacket(),a.outbound(),a.custody());
                            prefix=List.of(first,new PlanningReadReceipt(last.request(),last.contractId(),last.requestId(),last.before(),last.after(),copy));
                        }
                    }
                    List<PlanningReadReceipt> rejected=prefix;
                    assertThrows(IOException.class,()->scope.consumeReadOnlyPrefix(rejected),variant);
                    int prior=f.port.writes;var before=f.guard(transport,ASSIGN,7);
                    var request=new NativeRequest(ASSIGN,Optional.empty(),raw("{\"candidate_character_id\":73}"));
                    var permit=NativeTransportSubmissionFixture.issue(command(before),before,request,"never-dispatch");
                    assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,transport.submit(permit,request,until));
                    assertFalse(permit.consumed());assertEquals(prior,f.port.writes);return null;
                }),variant);
                assertTrue(transport.mailboxDiagnostics().poison().isPresent(),variant);
            }
        }
    }

    @Test void unknownAfterPendingCannotBeClearedOrRetriedByReadPrefixConsumption() throws Exception {
        Fixture f=new Fixture("unknown");AtomicInteger reachedRejection=new AtomicInteger();
        f.port.reaction=wire->{var r=NativeWire.decodeExecuteRequest(wire);
            if(r.step().equals(GATES))f.port.reply(r.requestId(),pending(GATES));
            else f.port.readFailure=new IOException("controlled response lost after actual software write");
        };
        try(var transport=f.transport()) {
            transport.observe(deadline());
            assertThrows(IOException.class,()->transport.withMailbox(deadline(),scope->{
                Instant until=deadline();var first=f.read(transport,false,"initial",until);
                var guard=f.guard(transport,STATUS,7);var next=f.guard(transport,ASSIGN,7);var contract=f.reads.status();
                var request=new PlanningReadRequest(guard.observed(),guard.source(),guard.sessionId(),contract.operation(),new OpportunityJson.Obj(Map.of()),until);
                var readGuard=new PlanningReadGuard(guard,true,true,true,"b".repeat(64));
                var prepared=contract.prepare(request,"lost-status");var permit=NativeSelectorReadFixture.issue(contract,request,prepared,readGuard,"lost-status");
                var unknown=transport.read(permit,prepared,until);
                assertInstanceOf(NativeActionPort.Unknown.class,unknown);assertTrue(permit.consumed());assertEquals(2,f.port.writes);
                assertThrows(IOException.class,()->scope.consumeReadOnlyPrefix(List.of(first)));
                assertThrows(IOException.class,()->scope.complete(unknown));
                var assign=new NativeRequest(ASSIGN,Optional.empty(),raw("{\"candidate_character_id\":73}"));
                var submission=NativeTransportSubmissionFixture.issue(command(next),next,assign,"never-after-unknown");
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,transport.submit(submission,assign,until));
                assertFalse(submission.consumed());assertEquals(2,f.port.writes);reachedRejection.incrementAndGet();return null;
            }));
            assertEquals(1,reachedRejection.get());assertTrue(transport.mailboxDiagnostics().poison().isPresent());
        }
    }

    private final class Fixture {
        final G2Source source;final PrivateCouncilReads reads;final Replay port;
        Fixture(String name) throws Exception {
            Path original=temporary.resolve(name+".txt");Files.writeString(original,"controlled offline Council source, no live build qualification");
            ExactRef ref=reference(original.toString(),Files.readAllBytes(original));
            source=new G2Source(config().machineId(),Instant.now().toString(),"controlled-software-only",ref);reads=new PrivateCouncilReads(ref);
            port=new Replay(packet(hello()),packet(snapshot(7)));
        }
        NativeGameTransport transport() {
            var permission=new NativePrivateActionPermission(new OperationKey(ASSIGN),"controlled",source.sourceRef(),
                r->{if(!r.additionalFields().objectFieldNames().equals(Set.of("candidate_character_id")))throw new IOException("wrong fields");},
                (c,h,g,r)->source.sourceRef());
            return new NativeGameTransport(port,config(),16,64,List.of(permission));
        }
        GuardEvidence guard(NativeGameTransport transport,String operation,int revision) throws IOException {
            var frame=transport.latestObservedSnapshot().orElseThrow();
            var observation=new ProposalLifecycle.ObservationIdentity(config().machineId(),config().game(),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(revision),BigInteger.ONE),frame.snapshotId(),BigInteger.valueOf(revision),"controlled-episode"),1);
            Instant now=Instant.now();return new GuardEvidence(observation,source,config().sessionId(),frame.session().connectionGeneration(),new OperationKey(operation),
                reference("controlled-snapshot",frame.originalPacket()),reference("controlled-hello",transport.originalHello().packet().value()),"controlled-root",now,now.plusSeconds(30));
        }
        PlanningReadReceipt read(NativeGameTransport transport,boolean status,String id,Instant until) throws IOException,InterruptedException {
            var contract=status?reads.status():reads.gates();var guard=guard(transport,contract.operation().value(),7);
            var arguments=status?new OpportunityJson.Obj(Map.of()):OpportunityJson.parse("{\"position_key\":\"councillor_steward\"}".getBytes(StandardCharsets.UTF_8));
            var request=new PlanningReadRequest(guard.observed(),source,config().sessionId(),contract.operation(),(OpportunityJson.Obj)arguments,until);
            var readGuard=new PlanningReadGuard(guard,true,true,true,"b".repeat(64));var prepared=contract.prepare(request,id);
            var permit=NativeSelectorReadFixture.issue(contract,request,prepared,readGuard,id);
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,transport.read(permit,prepared,until));assertTrue(permit.consumed());
            return new PlanningReadReceipt(request,contract.contractId(),id,readGuard,readGuard,ack);
        }
    }
    private static ActionCommand command(GuardEvidence guard) {
        var expected=new ProposalLifecycle.ExpectedPostcondition(1,guard.observed(),guard.source(),"controlled-council/v1",List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"),true)));
        return new ActionCommand("controlled-council",guard.observed(),guard.source(),guard.sessionId(),guard.operation(),new OpportunityJson.Obj(Map.of()),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),guard.validUntil());
    }
    private static Instant deadline(){return Instant.now().plusSeconds(20);}
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static ExactRef reference(String path,byte[] bytes) {
        try{return new ExactRef(path,bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));}
        catch(java.security.NoSuchAlgorithmException impossible){throw new AssertionError(impossible);}
    }
    private static String pending(String step){return "{\"private_council_transport\":true,\"advertised\":false,\"step\":\""+step+"\",\"status\":\"pending\"}";}
    private static String terminal(String step,int revision){return "{\"schema\":\"xar.ck3.council-application-main/v1\",\"accepted\":true,\"step\":\""+step+"\",\"status\":\"available\",\"query_sequence\":1,\"snapshot_revision\":"+revision+",\"backend_id\":\"native-headless\"}";}
    private static String hello(){return "{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":18446744073709551615,\"bridge_version\":\"fixture\",\"expected_ck3_sha256\":\""+"0".repeat(64)+"\",\"game_adapter_id\":\"fixture-adapter\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\",\"game.command.pause-map\"]}";}
    private static String snapshot(int revision){return "{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"fixture-snapshot\",\"revision\":"+revision+",\"state\":{\"date_raw\":1,\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":29829,\"alive\":true},\"nullable\":null}}";}
    private static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\offline-council283","fixture-machine",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"fixture-session","fixture","0".repeat(64),"fixture-adapter");}
    private static byte[] packet(String text)throws IOException{return NativeWire.packet(text.getBytes(StandardCharsets.UTF_8));}
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets;int writes;Reaction reaction=p->{};IOException readFailure;
        Replay(byte[]... initial){packets=new ArrayDeque<>(Arrays.asList(initial));}
        void reply(String id,String result)throws IOException{packets.add(packet("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+id+"\",\"ok\":true,\"result\":"+result+"}"));}
        @Override public void verify(){}
        @Override public void awaitConnection(Instant until){}
        @Override public byte[] readPacket(Instant until)throws IOException {if(readFailure!=null){var failure=readFailure;readFailure=null;throw failure;}if(packets.isEmpty())throw new IOException("software packet exhausted");return packets.removeFirst().clone();}
        @Override public void writePacket(byte[] bytes,Instant until)throws IOException{writes++;try{reaction.accept(bytes.clone());}catch(Exception failure){throw new IOException("software reaction failed",failure);}}
        @Override public void close(){}
    }
    @FunctionalInterface private interface Reaction{void accept(byte[] packet)throws Exception;}
}
