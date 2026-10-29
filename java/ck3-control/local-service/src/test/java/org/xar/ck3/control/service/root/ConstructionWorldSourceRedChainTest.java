package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryModel;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryPolicy;

/** Original packet DATA -> actual Finance contract -> owning reducer -> real public binder/formatter.
 * The original Python module executes its own _send and world query over the same software transport.
 * No Root, Managed, source qualification or native success is fabricated. Missing exact input fails. */
final class ConstructionWorldSourceRedChainTest {
    private static final Instant T=Instant.parse("2026-10-24T20:15:00Z");
    private static final ExactRef SOURCE=new ExactRef("software/construction-source-red",1,"a".repeat(64));
    private static final G2Source G2=new G2Source("software-construction-source-red",T.toString(),"1.20.0.4",SOURCE);
    private static FinanceReadContracts definitions(){
        return new FinanceReadContracts(query->new FinanceReadContracts.Registration(SOURCE,
                new FinanceReadContracts.Permission(Optional.empty(),query.operation().value(),
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
    }
    private static ObjectNode jsonObject(JsonNode value){if(value instanceof ObjectNode object)return object;throw new IllegalArgumentException("JSON object required");}
    private static ObjectNode input()throws Exception {
        byte[] bytes=Files.readAllBytes(Path.of(required("xar.construction.world.original.input")));
        assertEquals(required("xar.construction.world.original.sha256"),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        var input=jsonObject(StrictJson.parse(bytes,ConstructionQueryCodec.MAX_BYTES));
        assertTrue(input.get("material_receipt").booleanValue());assertFalse(input.get("wartime_observation").booleanValue());
        return input;
    }
    private static PlanningReadReceipt receipt(FinanceReadContracts defs,FinanceReadContracts.Query query,ObjectNode input){
        var before=input.get("starting_snapshot");
        var identity=new ProposalLifecycle.ObservationIdentity(G2.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(before.get("played_character").get("character_id").bigIntegerValue(),
                        before.get("native_revision").bigIntegerValue(),before.get("date_raw").bigIntegerValue()),
                        before.get("snapshot_id").textValue(),before.get("revision").bigIntegerValue(),before.get("episode_run_id").textValue()),1);
        var request=new PlanningReadRequest(identity,G2,"software-source-red-session",query.operation(),new OpportunityJson.Obj(Map.of()),T.plusSeconds(60));
        String id=input.get("native_query_request_id").textValue();
        var envelope=(ObjectNode)input.get("native_envelope").deepCopy();envelope.put("request_id",id);
        RawJson frame=PublicDataJson.encode(envelope),result=PublicDataJson.encode(envelope.get("result"));
        byte[] packet=ByteBuffer.allocate(frame.bytes().length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(frame.bytes().length).put(frame.bytes()).array();
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(result),frame,packet);
        var basis=new GuardEvidence(identity,G2,request.sessionId(),BigInteger.ONE,query.operation(),SOURCE,SOURCE,"software-DATA-only",T,T.plusSeconds(60));
        var guard=new PlanningReadGuard(basis,true,true,true,"b".repeat(64));
        return new PlanningReadReceipt(request,defs.contract(query).contractId(),id,guard,guard,ack);
    }
    private static RootConstructionWorldPublicProducts.Response javaChain(ObjectNode input){
        var defs=definitions();var contract=defs.contract(FinanceReadContracts.Query.CONSTRUCTION);
        var original=receipt(defs,FinanceReadContracts.Query.CONSTRUCTION,input);
        var live=contract.decode(original);
        var before=DriverJson.object(PublicDataJson.encode(input.get("starting_snapshot")).bytes(),ConstructionQueryCodec.MAX_BYTES);
        var replay=defs.decodeOriginal(FinanceReadContracts.Query.CONSTRUCTION,original,before);
        assertEquals(live.result(),replay.result());assertEquals(live.originalResult(),replay.originalResult());
        assertEquals(DriverJson.object(PublicDataJson.encode(input.get("native_envelope").get("result")).bytes(),ConstructionQueryCodec.MAX_BYTES),live.originalResult());
        assertArrayEquals(original.original().originalFrame().bytes(),live.originalFrame());
        var result=RootConstructionWorldPublicProducts.finalizeOriginal(new RootConstructionWorldPublicProducts.Request(input.get("expected_revision").bigIntegerValue()),
                before,DriverJson.object(PublicDataJson.encode(input.get("ending_snapshot")).bytes(),ConstructionQueryCodec.MAX_BYTES),
                new RawJson(live.originalFrame()),original.requestId());
        return result;
    }
    private static List<ObjectNode> mismatches(ObjectNode original){
        var values=new ArrayList<ObjectNode>();
        var step=original.deepCopy();((ObjectNode)step.get("native_envelope").get("result")).put("step","different-original-step");values.add(step);
        var accepted=original.deepCopy();((ObjectNode)accepted.get("native_envelope").get("result")).put("accepted",false);values.add(accepted);
        for(String field:List.of("step","accepted")) {
            var missing=original.deepCopy();((ObjectNode)missing.get("native_envelope").get("result")).remove(field);values.add(missing);
            var nil=original.deepCopy();((ObjectNode)nil.get("native_envelope").get("result")).putNull(field);values.add(nil);
            var integer=original.deepCopy();((ObjectNode)integer.get("native_envelope").get("result")).put(field,1);values.add(integer);
        }
        var wrongProbe=accepted.deepCopy();((ObjectNode)wrongProbe.get("native_envelope").get("result")).put("private_probe","uninterpreted original rejected mapping");values.add(wrongProbe);
        return values;
    }
    @Test void actualFinanceLiveAndColdDecodersLetTheOwningReducerEmitEveryReturnedAdmissionMismatch()throws Exception {
        for(var input:mismatches(input())) {
            var result=javaChain(input);var row=PublicDataJson.object(result.originalMemory());
            assertEquals("source_red",row.get("status").textValue());
            assertEquals(input.get("native_envelope").get("result"),row.get("native_result"));
            var decoded=ConstructionQueryCodec.decode(PublicDataJson.encode(input).bytes());
            assertInstanceOf(ConstructionQueryModel.NativeAdmissionMismatch.class,decoded.envelope().result().value());
            assertInstanceOf(ConstructionQueryModel.SourceRed.class,ConstructionQueryPolicy.finalizeObservation(decoded));
            var wire=RootConstructionWorldPublicProducts.encode(result);
            assertEquals(row,PublicDataJson.object(RootConstructionWorldPublicProducts.restore(wire).originalMemory()));
        }
    }
    @Test void originalPythonSendAndQueryMatchTheCompleteJavaResultAndPublicBinding()throws Exception {
        for(var input:mismatches(input())) {
            var actual=javaChain(input);
            var child=new ProcessBuilder(required("xar.original.python"),"-c",ORIGINAL,required("xar.original.python.source.root"))
                    .redirectError(ProcessBuilder.Redirect.INHERIT).start();
            try(var stdin=child.getOutputStream()){stdin.write(PublicDataJson.encode(input).bytes());}
            byte[] output=child.getInputStream().readAllBytes();assertEquals(0,child.waitFor(),"original Python transport/query failed");
            assertEquals(PublicDataJson.object(new RawJson(output)),PublicDataJson.object(actual.originalMemory()));
            var binding=RootConstructionWorldPublicProducts.binding(SOURCE,request->actual);
            var request=new RootConstructionWorldPublicProducts.Request(input.get("expected_revision").bigIntegerValue());
            var response=binding.actual().invoke(request);assertSame(actual,response);
            assertEquals(RootConstructionWorldPublicProducts.NAME,binding.name());assertNotNull(binding.encoder().encode(response));
        }
    }
    @Test void otherFinanceQueriesAndCorruptTransportOrResultTokensRetainStrictRejection()throws Exception {
        var input=input();var defs=definitions();var cash=defs.contract(FinanceReadContracts.Query.CASH);
        assertThrows(IllegalArgumentException.class,()->cash.decode(receipt(defs,FinanceReadContracts.Query.CASH,input)));
        var wrongOk=input.deepCopy();((ObjectNode)wrongOk.get("native_envelope")).put("ok",false);
        assertThrows(IllegalArgumentException.class,()->javaChain(wrongOk));
        var contract=defs.contract(FinanceReadContracts.Query.CONSTRUCTION);var original=receipt(defs,FinanceReadContracts.Query.CONSTRUCTION,input);
        var ack=original.original();var changed=new NativeActionPort.AckReceived(original.requestId(),true,
                Optional.of(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))),ack.originalFrame(),ack.originalPacket());
        var corrupt=new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),original.before(),original.after(),changed);
        assertThrows(IllegalArgumentException.class,()->contract.replay(corrupt));
    }
    @Test void unchangedAcceptedOriginalStillReachesItsMaterialSourceAndLosslessFormatter()throws Exception {
        var actual=javaChain(input());assertEquals("material_source",PublicDataJson.object(actual.originalMemory()).get("status").textValue());
        assertEquals(PublicDataJson.object(actual.originalMemory()),PublicDataJson.object(
                RootConstructionWorldPublicProducts.restore(RootConstructionWorldPublicProducts.encode(actual)).originalMemory()));
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("actual CI prerequisite missing: "+key);return value;}
    private static final String ORIGINAL="""
import copy,json,sys,types
sys.path.insert(0,sys.argv[1])
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as m
x=json.load(sys.stdin);rid=x['native_query_request_id'];assert rid.startswith('construction-read-')
frames=iter([x['starting_snapshot'],x['ending_snapshot']])
class Driver:
 command_timeout_seconds=1
 def __init__(self):
  self.endpoint=types.SimpleNamespace(send=self.send)
  self.state=types.SimpleNamespace(wait_for_command_result=self.wait)
 def take_snapshot_without_native_command_history(self):return copy.deepcopy(next(frames))
 def send(self,packet):
  assert packet=={'type':'execute_step','protocol_version':1,'request_id':rid,'step':m.QUERY_NATIVE,'expected_revision':x['starting_snapshot']['native_revision']}
 def wait(self,request_id,timeout):
  assert request_id==rid and timeout==1
  return copy.deepcopy(x['native_envelope'])
m.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=rid[len('construction-read-'):]))
print(json.dumps(m.query_domain_construction_world_private_v1(Driver(),expected_revision=x['expected_revision']),ensure_ascii=False,separators=(',',':')))
""";
}
