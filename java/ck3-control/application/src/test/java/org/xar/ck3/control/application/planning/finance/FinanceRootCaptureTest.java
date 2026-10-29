package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Real public producer, fixed native preparation and strict persisted request arguments. No canonical authority is fabricated here. */
final class FinanceRootCaptureTest {
    private static final ExactRef REF=new ExactRef("D:/fixture/finance-root.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-24T00:00:00Z","1.20.0.4",REF);
    private static PlanningRequest request() {
        var before=new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.valueOf(100)),
                        "native:root-fixture",BigInteger.ONE,"episode-root-fixture"),1);
        Obj snapshot=object(parse(("{\"paused\":true,\"map_ready\":true,\"snapshot_id\":\"native:root-fixture\",\"revision\":1,\"native_revision\":1,"
                +"\"date_raw\":100,\"episode_run_id\":\"episode-root-fixture\",\"played_character\":{\"character_id\":1,\"alive\":true},"
                +"\"active_wars\":[],\"player_armies\":[],\"active_event\":null,\"pending_character_interaction\":null}").getBytes(StandardCharsets.UTF_8)),"fixture");
        return new PlanningRequest(before,SOURCE,"root-session-fixture",Instant.parse("2099-01-01T00:00:00Z"),
                new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static FinanceReadContracts definitions() {
        return new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,new FinanceReadContracts.Permission(
                Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
    }
    private static PlanningReadRequest readRequest(PlanningRequest original,FinanceReadContracts.Query query,Obj args) {
        return new PlanningReadRequest(original.before(),original.source(),original.sessionId(),query.operation(),args,original.deadline());
    }
    private static final class CapturingPort implements PlanningReadPort {
        private ReadContract<?> contract;
        private PlanningReadRequest request;
        private Session session;
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> actual,PlanningReadRequest original) {
            contract=actual;request=original;session=null;return new PlanningReadResult.Unavailable<>("fixture has no native transport",Optional.empty());
        }
        @Override public <T> PlanningReadResult<T> read(Session same,ReadContract<T> actual,PlanningReadRequest original) {
            contract=actual;request=original;session=same;return new PlanningReadResult.Unavailable<>("fixture has no native transport",Optional.empty());
        }
    }
    @Test void actualPublicProducerAndBorrowedProducerUseTheIdenticalVersionedContractAndWrapper() {
        var defs=definitions();var input=request();var port=new CapturingPort();var query=FinanceReadContracts.Query.ROOT;
        assertInstanceOf(PlanningReadResult.Unavailable.class,defs.read(query,port,input));
        assertSame(defs.contract(query),port.contract);assertEquals(FinanceReadContracts.ROOT_CONTRACT_ID,port.contract.contractId());
        assertEquals(FinanceReadContracts.RootCapture.PUBLIC_QUERY,FinanceReadContracts.rootCapture(port.request.arguments()));
        assertEquals(input.before(),port.request.before());assertEquals(input.source(),port.request.source());assertEquals(input.deadline(),port.request.deadline());
        assertTrue(port.contract.hasPureReplay());assertTrue(object(parse(port.contract.prepare(port.request,"public-root").additionalFields().bytes()),"native args").members().isEmpty());
        Session held=(Session)java.lang.reflect.Proxy.newProxyInstance(Session.class.getClassLoader(),new Class<?>[]{Session.class},
                (proxy,method,args)->{throw new AssertionError("capture producer must retain the supplied writer without dereferencing or replacing it");});
        defs.read(held,query,port,input);assertSame(held,port.session);assertSame(defs.contract(query),port.contract);
        assertEquals(FinanceReadContracts.RootCapture.PUBLIC_QUERY,FinanceReadContracts.rootCapture(port.request.arguments()));
    }
    @Test void bothCaptureKindsRoundTripAsExactArgumentsButPrepareTheSameNativeEmptyArguments() {
        var defs=definitions();var input=request();var query=FinanceReadContracts.Query.ROOT;
        for(var capture:FinanceReadContracts.RootCapture.values()) {
            Obj original=FinanceReadContracts.rootArguments(capture);
            Obj restored=DriverJson.object(encode(original),RawJson.MAXIMUM_BYTES);
            assertEquals(original,restored);assertEquals(capture,FinanceReadContracts.rootCapture(restored));
            var prepared=defs.contract(query).prepare(readRequest(input,query,restored),"typed-root-"+capture.name());
            assertEquals(query.operation().value(),prepared.step());
            assertEquals(new Obj(Map.of()),DriverJson.object(prepared.additionalFields().bytes(),RawJson.MAXIMUM_BYTES));
        }
        assertNotEquals(FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),
                FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS));
    }
    @Test void oldAliasMissingNullWrongTypesAndExtraFieldsCannotBePreparedOrReinterpreted() {
        var defs=definitions();var input=request();var query=FinanceReadContracts.Query.ROOT;
        for(String json:List.of("{}","{\"capture_context\":\"PUBLIC_QUERY\"}",
                "{\"capture_context\":null,\"public_arguments\":{}}","{\"capture_context\":true,\"public_arguments\":{}}",
                "{\"capture_context\":\"public_query\",\"public_arguments\":{}}","{\"capture_context\":\"PUBLIC_QUERY\",\"public_arguments\":null}",
                "{\"capture_context\":\"PUBLIC_QUERY\",\"public_arguments\":[]}","{\"capture_context\":\"PUBLIC_QUERY\",\"public_arguments\":{\"extra\":1}}",
                "{\"capture_context\":\"PUBLIC_QUERY\",\"public_arguments\":{},\"extra\":1}")) {
            Obj invalid=DriverJson.object(json.getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES);
            assertThrows(IllegalArgumentException.class,()->FinanceReadContracts.rootCapture(invalid));
            assertThrows(IllegalArgumentException.class,()->defs.contract(query).prepare(readRequest(input,query,invalid),"invalid-root"));
        }
        Obj publicArgs=FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY);
        assertThrows(IllegalArgumentException.class,()->defs.contract(FinanceReadContracts.Query.CASH).prepare(readRequest(input,FinanceReadContracts.Query.CASH,publicArgs),"wrong-query"));
        var port=new CapturingPort();defs.read(FinanceReadContracts.Query.CASH,port,input);
        assertEquals(new Obj(Map.of()),port.request.arguments());
        assertEquals(Set.of("expected_snapshot_revision"),DriverJson.object(port.contract.prepare(port.request,"cash").additionalFields().bytes(),RawJson.MAXIMUM_BYTES).members().keySet());
    }
}
