package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.Family;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.Method;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesService;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Actual source-owned decoder -> shared result -> sole EXECUTE mapper.
 * These explicit software packets are DATA, not a Root, held Native read or failure-row qualification. */
final class RootChinaCasesOriginalFailureTest {
    private static final ExactRef DATA=new ExactRef("synthetic/china-case-original-failure",1,"a".repeat(64));
    private static final PlanningReadPort NEVER_READ=new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            throw new AssertionError("pure decoder/mapper DATA cannot issue a READ");
        }
    };
    private static final ActionCoordinatorPort NEVER_ACTION=new ActionCoordinatorPort() {
        @Override public ActionReceipt execute(ActionCommand command) {throw new AssertionError("failed READ cannot submit");}
        @Override public ActionReceipt reconcile(String id) {throw new AssertionError("failed READ cannot reconcile");}
    };

    @Test void originalEnvelopeFailureMapsOnlyAfterIdenticalProducerContractAndRequest() {
        Fixture data=fixture();ObjectNode malformed=envelope();malformed.remove("query_sequence");
        PlanningReadReceipt receipt=data.receipt(malformed,true);
        var original=assertThrows(ChinaCasesFacade.OriginalDriverFailure.class,()->data.contract().decode(receipt));
        original.requireOriginal(data.contract(),data.request(),receipt);
        var unavailable=unavailable(receipt,original);
        var mapped=RootChinaCasesPublicStepProducts.originalDriverFailure(unavailable,data.facade(),data.contract(),data.request()).orElseThrow();
        assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,mapped.kind());
        assertEquals("BridgeUnavailableError",mapped.kind().pythonClassName());
        assertEquals("native ZhongGuo case query returned a malformed envelope",mapped.getMessage());
        assertSame(original,mapped.getCause());assertTrue(mapped.originalCandidate().isEmpty());
        assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicStepProducts.originalDriverFailure(
                unavailable,new ChinaCasesFacade(NEVER_READ,NEVER_ACTION),data.contract(),data.request()));
        ReadContract<?> other=new ChinaCasesFacade(NEVER_READ,NEVER_ACTION).readContracts().stream()
                .filter(c->c.operation().equals(data.contract().operation())).findFirst().orElseThrow();
        assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicStepProducts.originalDriverFailure(
                unavailable,data.facade(),other,data.request()));
        var request=data.request();var changed=new PlanningReadRequest(request.before(),request.source(),"another-session",
                request.operation(),request.arguments(),request.deadline());
        assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicStepProducts.originalDriverFailure(
                unavailable,data.facade(),data.contract(),changed));
    }

    @Test void presentInvalidQuerySequenceHasTheOtherOriginalLiteralAndDoesNotBecomeMissingKey() {
        Fixture data=fixture();
        for(String json:List.of("null","true","1.0","0","18446744073709551616")) {
            ObjectNode malformed=envelope();if(json.equals("1.0"))malformed.put("query_sequence",1.0);
            else malformed.set("query_sequence",StrictJson.parse(json.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            var receipt=data.receipt(malformed,true);
            var original=assertThrows(ChinaCasesFacade.OriginalDriverFailure.class,()->data.contract().decode(receipt),json);
            assertEquals(ChinaCasesFacade.OriginalDriverFailure.Kind.CASE_QUERY_SEQUENCE_MISSING,original.kind(),json);
            var mapped=RootChinaCasesPublicStepProducts.originalDriverFailure(unavailable(receipt,original),
                    data.facade(),data.contract(),data.request()).orElseThrow();
            assertEquals("native ZhongGuo case query lacks query_sequence",mapped.getMessage(),json);
            assertSame(original,mapped.getCause());assertTrue(mapped.originalCandidate().isEmpty());
        }
    }

    @Test void reasonTextAndOtherDecodeMarkersCannotMintAnOriginalCasesFailure() {
        Fixture data=fixture();
        for(String reason:List.of("OriginalDriverFailure:native ZhongGuo case query lacks query_sequence",
                "BridgeUnavailableError:native ZhongGuo case query returned a malformed envelope")) {
            var absent=new PlanningReadResult.Unavailable<Object>(reason,Optional.empty());
            assertTrue(RootChinaCasesPublicStepProducts.originalDriverFailure(absent,data.facade(),data.contract(),data.request()).isEmpty());
        }
        OriginalReadDecodeFailure unrelated=(contract,request,receipt)->{throw new AssertionError("foreign marker must not be consulted");};
        var foreign=new PlanningReadResult.Unavailable<Object>("another domain failure",
                Optional.of(data.receipt(envelope(),true).original()),Optional.of(unrelated));
        assertTrue(RootChinaCasesPublicStepProducts.originalDriverFailure(foreign,data.facade(),data.contract(),data.request()).isEmpty());
    }

    @Test void pureReplayAndNativeOuterFailureDoNotIssueLiveOriginalFailureQualification() {
        Fixture data=fixture();ObjectNode malformed=envelope();malformed.remove("accepted");
        var receipt=data.receipt(malformed,true);
        var replay=assertThrows(IllegalArgumentException.class,()->data.contract().replay(receipt));
        assertFalse(replay instanceof ChinaCasesFacade.OriginalDriverFailure);
        var outer=assertThrows(IllegalArgumentException.class,()->data.contract().decode(data.receipt(malformed,false)));
        assertFalse(outer instanceof ChinaCasesFacade.OriginalDriverFailure);
    }

    @Test void directAndGenericConsumersUseOneFiniteMappingAfterTheirActualSourceGuards() {
        Fixture data=fixture();ObjectNode malformed=envelope();malformed.putNull("query_sequence");
        var receipt=data.receipt(malformed,true);
        var original=assertThrows(ChinaCasesFacade.OriginalDriverFailure.class,()->data.contract().decode(receipt));
        var direct=new ChinaCasesService.Unavailable("actual original decoder failure",
                Optional.of(receipt.original()),Optional.of(original));
        var context=new ChinaCasesFacade.Context(data.request().before(),data.request().source(),
                data.request().sessionId(),BigInteger.valueOf(3),data.request().deadline());
        var generic=RootChinaCasesPublicStepProducts.originalDriverFailure(unavailable(receipt,original),
                data.facade(),data.contract(),data.request()).orElseThrow();
        var mapped=RootChinaCasesPublicStepProducts.originalDirectDriverFailure(direct,data.facade(),Family.CASE,context).orElseThrow();
        assertEquals(generic.kind(),mapped.kind());assertEquals(generic.getMessage(),mapped.getMessage());
        assertSame(original,mapped.getCause());assertTrue(mapped.originalCandidate().isEmpty());
        assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicStepProducts.originalDirectDriverFailure(
                direct,new ChinaCasesFacade(NEVER_READ,NEVER_ACTION),Family.CASE,context));
        assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicStepProducts.originalDirectDriverFailure(
                direct,data.facade(),Family.B1,context));
        var changed=new ChinaCasesFacade.Context(context.before(),context.source(),context.sessionId(),
                BigInteger.valueOf(4),context.deadline());
        assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicStepProducts.originalDirectDriverFailure(
                direct,data.facade(),Family.CASE,changed));
        var otherDeadline=new ChinaCasesFacade.Context(context.before(),context.source(),context.sessionId(),
                context.connectionGeneration(),context.deadline().plusSeconds(1));
        assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicStepProducts.originalDirectDriverFailure(
                direct,data.facade(),Family.CASE,otherDeadline));
        var reasonOnly=new ChinaCasesService.Unavailable("OriginalDriverFailure:"+mapped.getMessage(),Optional.of(receipt.original()));
        assertTrue(RootChinaCasesPublicStepProducts.originalDirectDriverFailure(reasonOnly,data.facade(),Family.CASE,context).isEmpty());
    }

    private static PlanningReadResult.Unavailable<Object> unavailable(PlanningReadReceipt receipt,
            ChinaCasesFacade.OriginalDriverFailure failure) {
        return new PlanningReadResult.Unavailable<>("original decoder rejected the actual packet",
                Optional.of(receipt.original()),Optional.of(failure));
    }
    private static ObjectNode envelope() {
        ObjectNode result=StrictJson.object().put("step",Method.CASE.family().step()).put("accepted",true)
                .put("status","unavailable").put("query_sequence",9).put("snapshot_revision",31).put("backend_id","native-headless");
        result.putNull(Method.CASE.payload());return result;
    }
    private static Fixture fixture() {
        var facade=new ChinaCasesFacade(NEVER_READ,NEVER_ACTION);
        ReadContract<?> contract=facade.readContracts().stream()
                .filter(c->c.operation().value().equals(Method.CASE.family().step())).findFirst().orElseThrow();
        Instant now=Instant.now();var source=new G2Source("software-fixture",now.toString(),"original-case-fault-data",DATA);
        var identity=new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(31),BigInteger.valueOf(42));
        var frame=new JointBudgetSelector.ProposalFrame(identity,"original-fault-snapshot",BigInteger.valueOf(19),"software-episode");
        var before=new ProposalLifecycle.ObservationIdentity("software-fixture",
                new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        var encoded=new OperationKey(Method.CASE.family().step()+"-b1-102-0-4e31");
        var request=new PlanningReadRequest(before,source,"software-session",contract.operation(),
                ChinaCasesCodec.executionArguments(encoded,BigInteger.valueOf(3)),now.plusSeconds(60));
        contract.prepare(request,"software-case-fault");return new Fixture(facade,contract,request);
    }
    private record Fixture(ChinaCasesFacade facade,ReadContract<?> contract,PlanningReadRequest request) {
        PlanningReadReceipt receipt(ObjectNode result,boolean nativeOk) {
            Instant now=Instant.now();
            var guard=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.valueOf(3),
                    request.operation(),DATA,DATA,"software-data",now,now.plusSeconds(60));
            var binding=new PlanningReadGuard(guard,true,true,true,"b".repeat(64));
            ObjectNode ack=StrictJson.object().put("type","command_result").put("protocol_version",1)
                    .put("request_id","software-case-fault").put("ok",nativeOk);ack.set("result",result);
            RawJson frame=raw(ack);byte[] bytes=frame.bytes();
            byte[] packet=ByteBuffer.allocate(bytes.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
            var original=new NativeActionPort.AckReceived("software-case-fault",nativeOk,Optional.of(raw(result)),frame,packet);
            return new PlanningReadReceipt(request,contract.contractId(),"software-case-fault",binding,binding,original);
        }
    }
    private static RawJson raw(ObjectNode value) {return new RawJson(StrictJson.canonical(value));}
}
