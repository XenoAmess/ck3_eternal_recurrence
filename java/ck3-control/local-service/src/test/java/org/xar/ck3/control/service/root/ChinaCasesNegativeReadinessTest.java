package org.xar.ck3.control.service.root;

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
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.*;

/** Original Python rejection oracle -> actual shared decoder -> public service. Software DATA, never Root authority. */
final class ChinaCasesNegativeReadinessTest {
    @TempDir Path temp;
    private static final String EXE="2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final String ORIGINAL="""
import copy,hashlib,json,runpy,sys
from pathlib import Path
root=Path(sys.argv[1]);family=sys.argv[2];reason=sys.argv[3]
sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
for item in json.loads(sys.argv[4]):
 raw=(root/item['path']).read_bytes()
 if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise RuntimeError('original source changed: '+item['path'])
name='test_zhongguo_ai_owned_case_snapshot_contract.py' if family=='AI_OWNED' else 'test_zhongguo_b2_pip_snapshot_v1_bridge.py'
m=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit'/name));frame=m['_unavailable_frame'](reason)
if family=='PIP':frame['readiness']['same_frame_ready']=reason in {'case_not_found','case_inconsistent','owner_filter_mismatch','not_received_self'}
normalized=m['_normalize'](frame)
rejected=[]
for key in frame['readiness']:
 bad=copy.deepcopy(frame);bad['readiness'][key]=not bad['readiness'][key]
 try:m['_normalize'](bad)
 except ValueError:rejected.append(key)
 else:raise RuntimeError('original accepted changed unavailable readiness '+key)
print(json.dumps({'frame':frame,'normalized':normalized,'rejected_components':rejected},separators=(',',':')))
""";
    @Test void exactOriginalUnavailableTupleIsSharedByAllActualFamilyConsumers() throws Exception {
        assertFalse(RootOriginalPublicTestInputs.tools().isEmpty());
        for(Method method:List.of(Method.AI_OWNED,Method.PIP))for(String reason:List.of("case_not_found","unsupported_build")) {
            ObjectNode oracle=original(method,reason),frame=object(oracle.get("frame"));var context=context(frame);
            ReadRequest request=new ReadRequest(method,frame.get("request_nonce").textValue(),new PublicUnsigned64.Value(BigInteger.valueOf(19)),
                    OptionalInt.of(frame.get("requested_owner_character_id").intValue()),
                    method==Method.AI_OWNED?OptionalInt.of(frame.get("subject_character_id").intValue()):OptionalInt.empty(),Optional.empty());
            ChinaCasesService service=service(method,frame,context);
            var result=assertInstanceOf(ChinaCasesService.Known.class,service.query(request,context));
            ObjectNode response=ChinaCasesCodec.encodeReadResult(result.response());
            assertEquals("unavailable",response.get("status").textValue());assertEquals(reason,response.get("unavailable_reason").textValue());
            assertEquals(oracle.get("normalized").get("readiness"),response.get("readiness"));
            for(JsonNode field:oracle.get("rejected_components")) {
                ObjectNode changed=frame.deepCopy();ObjectNode readiness=object(changed.get("readiness"));String key=field.textValue();readiness.put(key,!readiness.get(key).booleanValue());
                ChinaCasesService invalid=service(method,changed,context);
                assertThrows(RuntimeException.class,()->invalid.query(request,context),method+" "+reason+" cannot fabricate "+key);
            }
        }
    }
    private ChinaCasesService service(Method method,ObjectNode frame,ChinaCasesService.Context context) {
        PlanningReadPort actualOriginalDecoder=new PlanningReadPort(){
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
                contract.prepare(request,"software-negative-query");ObjectNode envelope=StrictJson.object();
                envelope.put("step",method.family().step());envelope.put("accepted",true);envelope.put("status","unavailable");envelope.put("query_sequence",9);
                envelope.put("snapshot_revision",frame.get("snapshot_revision").bigIntegerValue());envelope.put("backend_id","native-headless");envelope.set(method.payload(),frame);
                ExactRef ref=reference();var guard=new GuardEvidence(request.before(),request.source(),request.sessionId(),context.query().connectionGeneration(),request.operation(),ref,ref,"software-data",Instant.now(),Instant.now().plusSeconds(60));
                var binding=new PlanningReadGuard(guard,true,true,true,"b".repeat(64));ObjectNode ack=StrictJson.object();ack.put("type","ack");ack.put("request_id","software-negative-query");ack.put("ok",true);ack.set("result",envelope);
                RawJson originalAck=raw(ack);byte[] bytes=originalAck.bytes();byte[] packet=ByteBuffer.allocate(bytes.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
                var original=new NativeActionPort.AckReceived("software-negative-query",true,Optional.of(raw(envelope)),originalAck,packet);
                var receipt=new PlanningReadReceipt(request,contract.contractId(),"software-negative-query",binding,binding,original);
                return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,ref);
            }
        };
        ActionCoordinatorPort noActions=new ActionCoordinatorPort(){public ActionReceipt execute(ActionCommand c){throw new AssertionError("read submitted mutation");}public ActionReceipt reconcile(String id){throw new AssertionError("read reconciled mutation");}};
        return new ChinaCasesService(new ChinaCasesFacade(actualOriginalDecoder,noActions));
    }
    private ChinaCasesService.Context context(ObjectNode frame) {
        var source=new G2Source("software-fixture",Instant.now().toString(),"original-negative-differential",reference());
        var identity=new JointBudgetSelector.Frame(frame.get("player_character_id").bigIntegerValue(),frame.get("snapshot_revision").bigIntegerValue(),frame.get("date_raw").bigIntegerValue());
        var proposal=new JointBudgetSelector.ProposalFrame(identity,"negative-original",BigInteger.valueOf(19),"software-episode");
        var before=new ProposalLifecycle.ObservationIdentity("software-fixture",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),proposal,1);
        var query=new ChinaCasesFacade.Context(before,source,"software-session",BigInteger.valueOf(3),Instant.now().plusSeconds(60));
        return new ChinaCasesService.Context(query,"0.1.0","ck3-1.19.0.6-msvc-x64","1.19.0.6",EXE);
    }
    private ObjectNode original(Method method,String reason)throws Exception {
        String python=required("xar.native.producer.python"),root=required("xar.public.original.repo.root"),manifest=required("xar.public.china.original.manifest");
        if(!Path.of(python).isAbsolute()||!Path.of(root).isAbsolute()||!Path.of(manifest).isAbsolute())throw new IllegalStateException("absolute original input required");
        new org.xar.ck3.control.build.ControlBuild.FileRef(manifest,Long.parseLong(required("xar.public.china.original.manifest.bytes")),required("xar.public.china.original.manifest.sha256")).verify();
        Path out=temp.resolve(method.name()+reason+".json"),err=temp.resolve(method.name()+reason+".stderr");
        Process process=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL,root,method.name(),reason,Files.readString(Path.of(manifest))).redirectOutput(out.toFile()).redirectError(err.toFile()).start();
        if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();throw new IllegalStateException("original negative oracle timed out");}
        if(process.exitValue()!=0)throw new IllegalStateException("original negative oracle failed: "+Files.readString(err));
        return object(StrictJson.parse(Files.readAllBytes(out),StrictJson.EXPLICIT_MAX_BYTES));
    }
    private ExactRef reference(){return new ExactRef(temp.resolve("software-source-data").toString(),1,"0".repeat(64));}
    private static RawJson raw(ObjectNode n){return new RawJson(StrictJson.canonical(n));}
    private static ObjectNode object(JsonNode n){return assertInstanceOf(ObjectNode.class,n);}
    private static String required(String name){String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ORIGINAL_INPUT: -D"+name);return value;}
}
