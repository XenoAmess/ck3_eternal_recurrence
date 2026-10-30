package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.PlanningReadFailure;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJsonTest;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Software READ DTO consumer only: no RootContext, lease, writer permit, Native call or canonical credit. */
final class MilitaryRootReadRouteTest {
    private static final ExactRef REF=new ExactRef("D:/fixture/root-route-source",1,"a".repeat(64));
    private static final ExactRef RECEIPT_REF=new ExactRef("D:/fixture/root-route-read-dto",1,"b".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-24T00:00:00Z","1.20.0.4",REF);
    private static final Instant DEADLINE=Instant.parse("2099-01-01T00:00:00Z");
    private static Obj originalRoot;
    private static synchronized Obj originalRoot() throws Exception {
        if(originalRoot==null)originalRoot=CampaignRootContextJsonTest.originalActual4RootFixture();
        return originalRoot;
    }
    private static PlanningRequest request() throws Exception {
        Obj root=originalRoot();
        BigInteger revision=OpportunityJson.integer(root.get("snapshot_revision"),"original revision");
        BigInteger date=OpportunityJson.integer(root.get("date_raw"),"original date");
        BigInteger actor=OpportunityJson.integer(root.get("player_character_id"),"original actor");
        var before=new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor,revision,date),"native:root-route-software",revision,"root-route-software"),1);
        Obj snapshot=new Obj(Map.of("paused",new Bool(true),"map_ready",new Bool(true),"snapshot_id",new Text(before.frame().snapshotId()),
                "revision",new IntegerValue(revision),"native_revision",new IntegerValue(revision),"date_raw",new IntegerValue(date),
                "episode_run_id",new Text(before.frame().episodeRunId()),"played_character",new Obj(Map.of("character_id",new IntegerValue(actor),"alive",new Bool(true)))));
        snapshot=snapshot.with("active_wars",new Arr(List.of())).with("player_armies",new Arr(List.of()))
                .with("active_event",Nil.INSTANCE).with("pending_character_interaction",Nil.INSTANCE);
        return new PlanningRequest(before,SOURCE,"root-route-software",DEADLINE,
                new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static FinanceReadContracts definitions() {
        return new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,new FinanceReadContracts.Permission(
                Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
    }
    private static Session readOnlySession() {
        return (Session)java.lang.reflect.Proxy.newProxyInstance(Session.class.getClassLoader(),new Class<?>[]{Session.class},
                (proxy,method,args)->{throw new AssertionError("the route must retain its caller's writer DATA without inventing scope or opening another transaction");});
    }
    private static PlanningReadGuard guard(PlanningReadRequest request) {
        var binding=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,request.operation(),
                REF,REF,"root-route-software-read-dto",Instant.parse("2026-10-24T00:00:00Z"),DEADLINE);
        return new PlanningReadGuard(binding,true,true,true,"c".repeat(64));
    }
    private static Obj result(long sequence) throws Exception {
        Obj root=originalRoot();
        return new Obj(Map.of("step",new Text(FinanceReadContracts.Query.ROOT.operation().value()),"accepted",new Bool(true),
                "status",root.get("status"),"query_sequence",new IntegerValue(BigInteger.valueOf(sequence)),
                "snapshot_revision",root.get("snapshot_revision"),"campaign_root_context",root,"backend_id",new Text("native-headless")));
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract,PlanningReadRequest request,long sequence) throws Exception {
        String id="root-route-software-"+sequence;Obj result=result(sequence);
        Obj envelope=new Obj(Map.of("type",new Text("command_result"),"protocol_version",new IntegerValue(BigInteger.ONE),
                "request_id",new Text(id),"ok",new Bool(true),"result",result));
        byte[] frame=DriverJson.encode(envelope);
        byte[] packet=ByteBuffer.allocate(frame.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(frame.length).put(frame).array();
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(DriverJson.encode(result))),new RawJson(frame),packet);
        var guard=guard(request);
        return new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
    }
    private static final class Port implements PlanningReadPort {
        private final Session expected;
        private final FinanceReadContracts definitions;
        private final boolean drift;
        private final boolean unknown;
        private ReadContract<?> capturedContract;
        private PlanningReadRequest capturedRequest;
        private PlanningReadReceipt actualReceipt;
        private PlanningReadResult.Unavailable<?> missing;
        private int calls;
        Port(Session expected,FinanceReadContracts definitions,boolean drift,boolean unknown) {
            this.expected=expected;this.definitions=definitions;this.drift=drift;this.unknown=unknown;
        }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            throw new AssertionError("ordinary ROOT route must borrow its supplied Session");
        }
        @Override public <T> PlanningReadResult<T> read(Session same,ReadContract<T> contract,PlanningReadRequest request) {
            calls++;assertSame(expected,same);assertSame(definitions.contract(FinanceReadContracts.Query.ROOT),contract);
            capturedContract=contract;capturedRequest=request;
            assertEquals(FinanceReadContracts.RootCapture.PUBLIC_QUERY,FinanceReadContracts.rootCapture(request.arguments()));
            assertTrue(DriverJson.object(contract.prepare(request,"root-route-software").additionalFields().bytes(),RawJson.MAXIMUM_BYTES).members().isEmpty());
            if(unknown) {
                String id="root-route-returned-unknown";
                var outcome=new NativeActionPort.Unknown(id,"software returned query has no final response",new byte[]{1},Optional.empty(),
                        Optional.of(new NativeActionPort.FailureCause(NativeActionPort.FailureKind.FRAME_BUDGET_EXHAUSTED,
                                NativeActionPort.FailureStage.RESPONSE_WAIT,Optional.empty(),Optional.empty(),Optional.empty())));
                var observed=new PlanningReadFailure(request,contract.contractId(),id,guard(request),guard(request),contract.prepare(request,id),
                        outcome,RECEIPT_REF,REF,0,"d".repeat(64));
                var unavailable=new PlanningReadResult.Unavailable<T>(outcome.reason(),Optional.of(outcome),Optional.empty(),Optional.of(observed));
                missing=unavailable;return unavailable;
            }
            try {
                var first=receipt(contract,request,1);T decoded=contract.decode(first);
                actualReceipt=drift?receipt(contract,request,2):first;
                return new PlanningReadResult.Known<>(decoded,actualReceipt,RECEIPT_REF);
            } catch(Exception failure) {throw new IllegalStateException("software ROOT original producer failed",failure);}
        }
    }
    @Test void knownUsesExactBorrowedPublicRootContractAndPureReceiptDecoder() throws Exception {
        var input=request();var same=readOnlySession();var definitions=definitions();var port=new Port(same,definitions,false,false);
        var result=MilitaryNativeReadDispatcher.root(definitions,port,same,input);
        var known=assertInstanceOf(PlanningReadResult.Known.class,result);
        assertEquals(1,port.calls);assertSame(definitions.contract(FinanceReadContracts.Query.ROOT),port.capturedContract);
        assertEquals(FinanceReadContracts.ROOT_CONTRACT_ID,port.capturedContract.contractId());assertTrue(port.capturedContract.hasPureReplay());
        assertEquals(input.before(),port.capturedRequest.before());assertEquals(input.source(),port.capturedRequest.source());
        assertEquals(input.sessionId(),port.capturedRequest.sessionId());assertEquals(input.deadline(),port.capturedRequest.deadline());
        assertSame(port.actualReceipt,known.receipt());assertSame(RECEIPT_REF,known.originalReceipt());
        assertEquals(definitions.contract(FinanceReadContracts.Query.ROOT).replay(port.actualReceipt).result(),known.value());
        assertEquals(new Text("available"),OpportunityJson.object(((Obj)known.value()).get("campaign_root_context"),"decoded root").get("status"));
    }
    @Test void unknownKeepsExactOriginalAndObservedFailureWithoutInventingDecodedValue() throws Exception {
        var input=request();var same=readOnlySession();var definitions=definitions();var port=new Port(same,definitions,false,true);
        var missing=assertInstanceOf(PlanningReadResult.Unavailable.class,MilitaryNativeReadDispatcher.root(definitions,port,same,input));
        assertEquals(1,port.calls);assertEquals(port.missing.reason(),missing.reason());
        assertSame(port.missing.original().orElseThrow(),missing.original().orElseThrow());
        assertSame(port.missing.observedFailure().orElseThrow(),missing.observedFailure().orElseThrow());
        assertTrue(missing.decodeFailure().isEmpty(),"UNKNOWN cannot carry a live successful-ACK decode failure");
    }
    @Test void valueFromOneNativeReceiptCannotBeAttachedToChangedOriginalReceipt() throws Exception {
        var input=request();var same=readOnlySession();var definitions=definitions();var port=new Port(same,definitions,true,false);
        assertThrows(IllegalArgumentException.class,()->MilitaryNativeReadDispatcher.root(definitions,port,same,input));
        assertEquals(1,port.calls);
    }
}
