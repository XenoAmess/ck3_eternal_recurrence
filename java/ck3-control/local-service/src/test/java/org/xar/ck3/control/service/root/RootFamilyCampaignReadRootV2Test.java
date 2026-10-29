package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Actual Family request producer -> sole Finance preparation/serde -> Family original guards. No live witness is forged. */
final class RootFamilyCampaignReadRootV2Test {
    private static final ExactRef REF=new ExactRef("D:/synthetic-family-root/source",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static PlanningReadRequest leaf() {
        var source=new G2Source("fixture-family-root-machine",NOW.toString(),"fixture-build",REF);
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(7),BigInteger.valueOf(100)),"synthetic-root",BigInteger.valueOf(9),"synthetic-episode"),1);
        return new PlanningReadRequest(identity,source,"synthetic-root-session",new OperationKey("synthetic-family-leaf"),new Obj(Map.of()),NOW.plusSeconds(30));
    }
    @Test void actualFamilyProducerUsesTypedPublicCaptureAndTheFinanceNativePreparerKeepsNativeArgumentsEmpty() {
        var leaf=leaf();var request=RootFamilyCampaignRead.publicRootRequest(leaf);
        assertEquals(leaf.before(),request.before());assertEquals(leaf.source(),request.source());assertEquals(leaf.sessionId(),request.sessionId());assertEquals(leaf.deadline(),request.deadline());
        assertEquals(FinanceReadContracts.Query.ROOT.operation(),request.operation());assertEquals(FinanceReadContracts.RootCapture.PUBLIC_QUERY,FinanceReadContracts.rootCapture(request.arguments()));
        var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,new FinanceReadContracts.Permission(Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
        var contract=definitions.contract(FinanceReadContracts.Query.ROOT);assertEquals(FinanceReadContracts.ROOT_CONTRACT_ID,contract.contractId());
        var nativeRequest=contract.prepare(request,"synthetic-public-root");assertEquals(FinanceReadContracts.Query.ROOT.operation().value(),nativeRequest.step());
        assertEquals(new Obj(Map.of()),DriverJson.object(nativeRequest.additionalFields().bytes(),RawJson.MAXIMUM_BYTES));
        Obj restored=DriverJson.object(DriverJson.encode(request.arguments()),RawJson.MAXIMUM_BYTES);assertEquals(request.arguments(),restored);
        assertEquals(FinanceReadContracts.RootCapture.PUBLIC_QUERY,FinanceReadContracts.rootCapture(restored));
    }
    @Test void familyOriginalConsumerAcceptsOnlyExactPublicV2AndRejectsInternalLegacyMissingAndWrongCapture() {
        var request=RootFamilyCampaignRead.publicRootRequest(leaf());assertDoesNotThrow(()->RootFamilyCampaignRead.requireOriginal(receipt(request,FinanceReadContracts.ROOT_CONTRACT_ID)));
        assertThrows(IllegalArgumentException.class,()->RootFamilyCampaignRead.requireOriginal(receipt(request,"ordinary-finance-read:ROOT")));
        for(Obj args:List.of(new Obj(Map.of()),FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS),
                DriverJson.object("{\"capture_context\":null,\"public_arguments\":{}}".getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES),
                DriverJson.object("{\"capture_context\":\"PUBLIC_QUERY\",\"public_arguments\":null}".getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES))) {
            var changed=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),request.operation(),args,request.deadline());
            assertThrows(IllegalArgumentException.class,()->RootFamilyCampaignRead.requireOriginal(receipt(changed,FinanceReadContracts.ROOT_CONTRACT_ID)));
        }
        var wrong=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),new OperationKey("another-query"),request.arguments(),request.deadline());
        assertThrows(IllegalArgumentException.class,()->RootFamilyCampaignRead.requireOriginal(receipt(wrong,FinanceReadContracts.ROOT_CONTRACT_ID)));
    }
    private static PlanningReadReceipt receipt(PlanningReadRequest request,String contractId) {
        var binding=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,request.operation(),REF,
                new ExactRef("D:/synthetic-family-root/capabilities",1,"b".repeat(64)),"synthetic-root-authority",NOW,request.deadline());
        var guard=new PlanningReadGuard(binding,true,true,true,"c".repeat(64));
        var body=new RawJson("{}".getBytes(StandardCharsets.UTF_8));var frame=new RawJson("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"synthetic-root\",\"ok\":true,\"result\":{}}".getBytes(StandardCharsets.UTF_8));
        return new PlanningReadReceipt(request,contractId,"synthetic-root",guard,guard,new NativeActionPort.AckReceived("synthetic-root",true,Optional.of(body),frame,frame.bytes()));
    }
}
