package org.xar.ck3.control.nativebridge.capabilities.china_cases;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade.OriginalDriverFailure;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade.OriginalDriverFailure.Kind;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.Family;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesService;

/** Software ordinary READ fixtures only. No private Root, admission, readiness or SAVE proof is created. */
final class ChinaCasesOriginalFailureTest {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private record Rejected(ChinaCasesFacade facade,ReadContract<?> contract,PlanningReadRequest request,
            PlanningReadReceipt receipt,OriginalDriverFailure failure) { }
    private static PlanningReadPort unusedReads(){return new PlanningReadPort(){
        @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("no Native read");}
    };}
    private static ChinaCasesFacade facade(PlanningReadPort reads){return new ChinaCasesFacade(reads,
            new ActionCoordinatorPort(){
                @Override public ActionReceipt execute(ActionCommand command){throw new AssertionError("no mutation");}
                @Override public ActionReceipt reconcile(String actionId){throw new AssertionError("no mutation");}
            },new ChinaCasesFacade.HistoryProjectionFactory(){
                @Override public DriverReadHistoryRichMaterial.Kind kind(){return DriverReadHistoryRichMaterial.Kind.PUBLIC_EXECUTE_QUERY;}
                @Override public <T>Optional<ReadContract.OriginalHistoryProjection<T>> forFamily(Family family){
                    return family==Family.PROGRESS?Optional.empty():Optional.of((receipt,value)->{
                        throw new AssertionError("no successful history projection in this failure fixture");
                    });
                }
            });}
    @Test void formalDecorationRetainsExplicitPureReplayForEveryInstalledCasesContract(){
        var actual=facade(unusedReads());
        assertEquals(11,actual.readContracts().size());
        for(var contract:actual.readContracts())assertTrue(contract.hasPureReplay(),contract.contractId());
        for(int index=0;index<10;index++)assertEquals(Optional.of(DriverReadHistoryRichMaterial.Kind.PUBLIC_EXECUTE_QUERY),
                actual.readContracts().get(index).originalHistoryKind());
    }
    @Test void liveFailureBelongsToFinalDecoratedInstanceAndPureReplayNeverIssuesTheMarker(){
        ObjectNode missing=base();missing.remove("query_sequence");
        var actual=rejected(missing);
        assertSame(actual.facade().readContracts().get(1),actual.contract());
        actual.failure().requireOriginal(actual.contract(),actual.request(),actual.receipt());
        actual.failure().requireProducer(actual.facade(),actual.contract(),actual.request());
        assertEquals(Kind.CASE_MALFORMED_ENVELOPE,actual.failure().kind());
        assertEquals("BridgeUnavailableError",actual.failure().originalErrorClass());
        assertEquals("native ZhongGuo case query returned a malformed envelope",actual.failure().originalMessage());
        assertThrows(IllegalArgumentException.class,()->actual.failure().requireProducer(facade(unusedReads()),actual.contract(),actual.request()));
        var replayFailure=assertThrows(IllegalArgumentException.class,()->actual.contract().replay(actual.receipt()));
        assertFalse(replayFailure instanceof OriginalReadDecodeFailure,"pure archive interpretation cannot issue a live decoder cause");
    }
    @Test void envelopeHasOriginalPriorityOverMissingOrWrongTypedSequence(){
        ObjectNode missing=base();missing.remove("query_sequence");
        assertEquals(Kind.CASE_MALFORMED_ENVELOPE,rejected(missing).failure().kind());
        var variants=new ArrayList<ObjectNode>();
        ObjectNode wrongStep=base();wrongStep.put("step","another-step");variants.add(wrongStep);
        ObjectNode wrongAccepted=base();wrongAccepted.put("accepted",1);variants.add(wrongAccepted);
        ObjectNode wrongRevision=base();wrongRevision.put("snapshot_revision",2);variants.add(wrongRevision);
        ObjectNode extra=base();extra.put("extra",true);variants.add(extra);
        for(ObjectNode original:variants){original.putNull("query_sequence");
            assertEquals(Kind.CASE_MALFORMED_ENVELOPE,rejected(original).failure().kind());}
        for(JsonNode sequence:List.of(StrictJson.parse("null".getBytes()),StrictJson.parse("true".getBytes()),
                com.fasterxml.jackson.databind.node.DoubleNode.valueOf(1.0),StrictJson.parse("0".getBytes()),
                StrictJson.parse("18446744073709551616".getBytes()))){
            ObjectNode original=base();original.set("query_sequence",sequence);
            assertEquals(Kind.CASE_QUERY_SEQUENCE_MISSING,rejected(original).failure().kind());
        }
    }
    @Test void additionalStrictJavaGuardsAreNotMislabelledAsOriginalPythonBranches(){
        for(JsonNode revision:List.of(StrictJson.parse("true".getBytes()),com.fasterxml.jackson.databind.node.DoubleNode.valueOf(1.0))){
            ObjectNode original=base();original.set("snapshot_revision",revision);
            assertTrue(ChinaCasesCodec.originalCaseEnvelopeFailure(receipt(original,request())).isEmpty(),
                    "original Python equality accepts the numerically equal revision; Java strict type rejection is separate");
        }
        ObjectNode wrongSequence=base();wrongSequence.put("query_sequence",1.0);
        assertEquals(Optional.of(Kind.CASE_QUERY_SEQUENCE_MISSING),ChinaCasesCodec.originalCaseEnvelopeFailure(receipt(wrongSequence,request())));
    }
    @Test void finiteBranchesMatchTheActualOriginalPythonDriver()throws Exception {
        String python=required("xar.native.producer.python"),root=required("xar.public.original.repo.root");
        assertTrue(Path.of(python).isAbsolute());assertTrue(Path.of(root).isAbsolute());
        var rows=StrictJson.object().arrayNode();
        ObjectNode missing=base();missing.remove("query_sequence");rows.add(missing);
        ObjectNode extra=base();extra.put("extra",true);rows.add(extra);
        ObjectNode wrongAccepted=base();wrongAccepted.put("accepted",1);rows.add(wrongAccepted);
        ObjectNode wrongRevision=base();wrongRevision.put("snapshot_revision",2);rows.add(wrongRevision);
        for(JsonNode sequence:List.of(StrictJson.parse("null".getBytes()),StrictJson.parse("true".getBytes()),
                com.fasterxml.jackson.databind.node.DoubleNode.valueOf(1.0),StrictJson.parse("0".getBytes()),
                StrictJson.parse("18446744073709551616".getBytes()))){
            ObjectNode row=base();row.set("query_sequence",sequence);rows.add(row);
        }
        Path input=temporary.resolve("original-driver-input.json"),output=temporary.resolve("original-driver-output.json"),errors=temporary.resolve("original-driver-stderr.txt");
        Files.writeString(input,rows.toString(),StandardCharsets.UTF_8);
        Process original=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL_DRIVER,root,input.toString())
                .redirectOutput(output.toFile()).redirectError(errors.toFile()).start();
        if(!original.waitFor(30,TimeUnit.SECONDS)){original.destroyForcibly();throw new IllegalStateException("original CASE driver timed out");}
        assertEquals(0,original.exitValue(),()->"original CASE driver failed: "+readDiagnostic(errors));
        JsonNode results=StrictJson.parse(Files.readAllBytes(output),StrictJson.EXPLICIT_MAX_BYTES);
        assertTrue(results.isArray());assertEquals(rows.size(),results.size());
        for(int index=0;index<rows.size();index++){
            var actual=rejected((ObjectNode)rows.get(index)).failure();var expected=results.get(index);
            assertEquals(expected.get("class").textValue(),actual.originalErrorClass());
            assertEquals(expected.get("message").textValue(),actual.originalMessage());
        }
    }
    @Test void directServiceRetainsTheSameLiveCauseAndValidatesItsActualContextWithoutRetry(){
        ObjectNode malformed=base();malformed.remove("query_sequence");
        var cause=new AtomicReference<OriginalDriverFailure>();var calls=new java.util.concurrent.atomic.AtomicInteger();
        var actual=facade(new PlanningReadPort(){
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
                calls.incrementAndGet();var received=receipt(malformed,request);
                try{contract.decode(received);throw new AssertionError("malformed CASE unexpectedly decoded");}
                catch(OriginalDriverFailure failure){failure.requireOriginal(contract,request,received);cause.set(failure);
                    return new PlanningReadResult.Unavailable<>("actual software decoder failure",Optional.of(received.original()),Optional.of(failure));}
            }
        });
        var service=new ChinaCasesService(actual);var context=context();
        var request=new org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.ReadRequest(
                org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.Method.CASE,
                "n",new PublicUnsigned64.Value(BigInteger.ONE),java.util.OptionalInt.empty(),java.util.OptionalInt.of(12),Optional.empty());
        var direct=assertInstanceOf(ChinaCasesService.Unavailable.class,service.query(request,new ChinaCasesService.Context(
                context,"software-bridge","software-adapter","1.19.0.6","d".repeat(64))));
        assertEquals(1,calls.get());assertSame(cause.get(),direct.decodeFailure().orElseThrow());
        actual.requireDirectOriginalFailure(cause.get(),Family.CASE,context);
        assertThrows(IllegalArgumentException.class,()->facade(unusedReads()).requireDirectOriginalFailure(cause.get(),Family.CASE,context));
        assertThrows(IllegalArgumentException.class,()->actual.requireDirectOriginalFailure(cause.get(),Family.B1,context));
        var foreignGeneration=new ChinaCasesFacade.Context(context.before(),context.source(),context.sessionId(),BigInteger.TWO,context.deadline());
        assertThrows(IllegalArgumentException.class,()->actual.requireDirectOriginalFailure(cause.get(),Family.CASE,foreignGeneration));
        assertTrue(new ChinaCasesService.Unavailable("transport unavailable",Optional.empty()).decodeFailure().isEmpty());
    }
    private static String readDiagnostic(Path path){try{return Files.readString(path);}catch(java.io.IOException failure){return failure.toString();}}
    private static String required(String name){String value=System.getProperty(name);if(value==null||value.isBlank())
        throw new IllegalStateException("NOT_RUN_REQUIRED_ORIGINAL_INPUT: -D"+name);return value;}
    private static Rejected rejected(ObjectNode raw){
        var installed=new AtomicReference<ReadContract<?>>();var requested=new AtomicReference<PlanningReadRequest>();
        var received=new AtomicReference<PlanningReadReceipt>();
        var actual=facade(new PlanningReadPort(){
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
                installed.set(contract);requested.set(request);var receipt=receipt(raw,request);received.set(receipt);
                contract.decode(receipt);throw new AssertionError("malformed original unexpectedly decoded");
            }
        });
        var failure=assertThrows(OriginalDriverFailure.class,()->actual.query_zhongguo_case_snapshot_v1(
                context(),ChinaCasesFacade.CaseKind.B1_PERFORMANCE,new Nonce("n"),Optional.of(new CharacterId(12)),Optional.empty()));
        return new Rejected(actual,installed.get(),requested.get(),received.get(),failure);
    }
    private static ObjectNode base(){var n=StrictJson.object();n.put("step",Family.CASE.step());n.put("accepted",true);
        n.put("status","unavailable");n.put("query_sequence",1);n.put("snapshot_revision",1);n.putNull("zhongguo_case_snapshot");n.put("backend_id","software-only");return n;}
    private static ChinaCasesFacade.Context context(){
        var game=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE));
        var before=new ObservationIdentity("software-cases-fault",game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(12),BigInteger.ONE,BigInteger.valueOf(53217264)),"software-snapshot",BigInteger.ONE,"software-episode"),1);
        var ref=new ExactRef("software-source",1,"a".repeat(64));
        return new ChinaCasesFacade.Context(before,new G2Source(before.machineId(),NOW.toString(),"software-only",ref),
                "software-session",BigInteger.ONE,NOW.plusSeconds(60));
    }
    private static PlanningReadRequest request(){
        var context=context();var args=StrictJson.object();args.put("request_nonce","n");args.put("case_kind","zhongguo.b1.performance");
        args.put("subject_character_id",12);args.put("owner_character_id",0);
        return new PlanningReadRequest(context.before(),context.source(),context.sessionId(),new OperationKey(Family.CASE.step()),
                (OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(args)),context.deadline());
    }
    private static PlanningReadReceipt receipt(ObjectNode raw,PlanningReadRequest request){
        var ref=new ExactRef("software-reference",1,"b".repeat(64));
        var binding=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,request.operation(),
                ref,ref,"software-only",NOW,NOW.plusSeconds(60));
        var guard=new PlanningReadGuard(binding,true,true,true,"c".repeat(64));
        var ack=StrictJson.object();ack.put("type","ack");ack.put("request_id","software-case-query");ack.put("ok",true);ack.set("result",raw);
        RawJson token=new RawJson(ack.toString().getBytes(StandardCharsets.UTF_8));byte[] body=token.bytes();
        byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        var original=new NativeActionPort.AckReceived("software-case-query",true,Optional.of(new RawJson(raw.toString().getBytes(StandardCharsets.UTF_8))),token,packet);
        return new PlanningReadReceipt(request,"china-cases/"+Family.CASE.step()+"/v1","software-case-query",guard,guard,original);
    }
    private static final String ORIGINAL_DRIVER="""
import copy,hashlib,json,sys
from pathlib import Path
from types import SimpleNamespace
root=Path(sys.argv[1]);source=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'
data=source.read_bytes()
if len(data)!=1658471 or hashlib.sha256(data).hexdigest()!='eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603':
 raise RuntimeError('original native driver source drift')
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
snapshot={'paused':True,'date_raw':53217264,'native_revision':1,'snapshot_id':'software-snapshot','revision':1,'played_character':{'character_id':12},'diagnostics':{'connection_generation':1}}
query=SimpleNamespace(case_kind='zhongguo.b1.performance',subject_character_id=12,owner_character_id=None,request_nonce='n')
answers=[]
for row in json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')):
 class IO:
  def take_snapshot(self):return copy.deepcopy(snapshot)
  def _execute_primitive_step(self,*args,**kwargs):return copy.deepcopy(row)
 try:
  NativeHeadlessGameplayDriver._execute_zhongguo_case_snapshot_v1_query(IO(),query,expected_revision=1)
 except Exception as error:answers.append({'class':type(error).__name__,'message':str(error)})
 else:raise RuntimeError('expected original driver branch was not reached')
print(json.dumps(answers,separators=(',',':')))
""";
}
