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
import java.util.Set;
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
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.*;

/** Software source differential only. No private Root Stage/proof/qualification is constructed here. */
final class ChinaCasesPublicBoundaryTest {
    @TempDir Path temp;
    private static final String EXE="2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final String ORIGINAL="""
import copy,dataclasses,hashlib,json,runpy,sys
from pathlib import Path
root=Path(sys.argv[1]); method=sys.argv[2]
sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
manifest=json.loads(sys.argv[3])
for item in manifest:
 data=(root/item['path']).read_bytes()
 if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
  raise RuntimeError('original source drift: '+item['path'])
from xar_autoplayer.bridge.service import GameplayBridgeService
spec={
 'B1':('test_zhongguo_b1_cycle_snapshot_v1_contract.py','frame'),
 'CASE':('test_zhongguo_case_snapshot_contract.py','_frame'),
 'AI_OWNED':('test_zhongguo_ai_owned_case_snapshot_contract.py','_frame'),
 'RESULT':('test_zhongguo_result_case_snapshot_contract.py','_frame'),
 'PIP':('test_zhongguo_b2_pip_snapshot_v1_bridge.py','_pending_frame'),
 'PROMOTION':('test_zhongguo_promotion_compensation_v1_bridge.py','_native_frame'),
 'PROJECTS':('test_zhongguo_projects_metrics_v1_bridge.py','_native_frame'),
 'INCIDENT':('test_zhongguo_incident_snapshot_contract.py','na_frame'),
 'SCOREBOARD':('test_zhongguo_scoreboard_state_contract.py','native_frame')}
if method=='ACTIVATE_SCOREBOARD':
 m=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_zhongguo_scoreboard_action_contract.py'))
 f=m['_frame'](open_tab=None);r=m['_request'](f,action='open',target_identity=m['ENTRY']['received'])
 from xar_autoplayer.bridge.zhongguo_scoreboard_action_contract import plan_zhongguo_scoreboard_action_v1,acknowledged_zhongguo_scoreboard_action_v1
 ack=acknowledged_zhongguo_scoreboard_action_v1(plan_zhongguo_scoreboard_action_v1(r,source_state=f,observed_revision=r.expected_revision,observed_connection_generation=r.expected_connection_generation))
 result={'step':'activate-zhongguo-scoreboard-v1','accepted':True,'status':'acknowledged_verification_pending','request_nonce':r.request_nonce,'action':r.action,'action_sequence':9,'snapshot_revision':r.expected_native_revision,'rejection_reason':None,'action_ack':ack,'production_capability_advertised':False,'backend_id':'native-headless'}
 print(json.dumps({'frame':f,'request':dataclasses.asdict(r),'result':result},separators=(',',':')));sys.exit(0)
if method=='AF5':f=json.loads((root/'ck3_autonomous_player/tests/fixtures/zhongguo_compensation_af5_snapshot_v1.json').read_text())['frames']['pre_action']
else:
 filename,factory=spec[method];m=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit'/filename));f=m[factory]()
variant=int(sys.argv[7])
if method=='B1':
 if variant==1:
  f['cycle']['active']={'status':'unavailable','value':None,'unavailable_reason':'variable_absent'};f['status']='unavailable';f['unavailable_reason']='cycle_not_found';f['readiness']['ready']=False
 elif variant==2:f['pending']['open_count']['value']=-1
 elif variant==3:f['cycle']['state']['value']=8;f['cycle']['active']['value']=False
 elif variant==4:f['roster']['subject_count']['value']=0
 elif variant==5:f['quota']['target_top']['value']=3;f['quota']['built_case_serial']['value']=20
step=sys.argv[4];payload=sys.argv[5];public_name=sys.argv[6]
snapshot={'format_version':1,'snapshot_id':'china-original-fixture','revision':19,'native_revision':f['snapshot_revision'],'source':'named-pipe','backend_id':'native-headless','date_raw':f['date_raw'],'paused':True,'played_character':{'character_id':f['player_character_id'],'alive':True},'diagnostics':{'connection_generation':3,'bridge_version':'0.1.0','hello':{'bridge_version':'0.1.0','game_adapter_id':'ck3-1.19.0.6-msvc-x64','expected_ck3_version':'1.19.0.6','expected_ck3_sha256':'2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'}}}
native={'step':step,'accepted':True,'status':f['status'],'query_sequence':9,'snapshot_revision':f['snapshot_revision'],payload:copy.deepcopy(f),'backend_id':'native-headless'}
result={**native,'queried_snapshot_id':snapshot['snapshot_id'],'queried_revision':19,'queried_native_revision':f['snapshot_revision'],'queried_connection_generation':3}
class Driver:
 def capabilities(self):return {'format_version':1,'backend_id':'native-headless','source':'named-pipe','snapshot':True,'wait_for_change':False,'action_steps':[],'bridge_capabilities':['game.command.'+step]}
 def take_snapshot(self):return copy.deepcopy(snapshot)
 def execute_step(self,actual,*,expected_revision=None):
  if expected_revision!=19:raise RuntimeError('original public revision changed')
  return copy.deepcopy(result)
service=object.__new__(GameplayBridgeService);service.driver=Driver()
arguments={'request_nonce':f['request_nonce'],'expected_revision':19}
if method=='CASE':
 arguments.update(case_kind='zhongguo.b1.performance',subject_character_id=f['subject_character_id'],owner_character_id=f['requested_owner_character_id'])
elif method=='AI_OWNED':arguments.update(owner_character_id=f['requested_owner_character_id'],subject_character_id=f['subject_character_id'])
elif method in ('RESULT','PIP','INCIDENT','PROJECTS'):arguments['owner_character_id']=f['requested_owner_character_id']
if method=='PROJECTS':arguments['subject_character_id']=f['requested_subject_character_id']
if method=='INCIDENT':arguments['profile']=f['profile']
answer=getattr(service,public_name.removeprefix('ck3_'))(**arguments)
def public_u64(obj):
 for key in ('snapshot_revision','query_sequence','observation_sequence','observed_state_revision'):
  if key in obj:obj[key]=str(obj[key])
 for group in ('source','bridge_source','binding'):
  if group in obj:
   for key in ('revision','native_revision','connection_generation','expected_revision','query_sequence'):
    if key in obj[group]:obj[group][key]=str(obj[group][key])
public_u64(answer)
print(json.dumps({'frame':f,'request':arguments,'native':native,'public':answer},separators=(',',':')))
""";
    @Test void allTenOriginalServiceProducersFeedTheRealFamilyDecoderAndExactPublicRenderer() throws Exception {
        assertFalse(RootOriginalPublicTestInputs.tools().isEmpty(),"original SDK inventory is mandatory");
        for(Method method:Method.values())if(method.readOnly()) {
            ObjectNode oracle=oracle(method);ObjectNode frame=object(oracle.get("frame"));
            var request=ChinaCasesCodec.decodeRead(method,object(oracle.get("request")));
            assertEquals(request,ChinaCasesCodec.decodeRead(method,ChinaCasesCodec.encodeReadRequest(request)));
            var context=context(frame,BigInteger.valueOf(19),BigInteger.valueOf(3),"china-original-fixture");
            var read=new SoftwareRead(object(oracle.get("native")),context.query());
            var service=new ChinaCasesService(new ChinaCasesFacade(read,noActions()));
            var known=assertInstanceOf(ChinaCasesService.Known.class,service.query(request,context));
            assertEquals(1,read.calls);assertEquals(method.family().step(),read.lastPrepared.step());
            assertEquals(object(oracle.get("public")),ChinaCasesCodec.encodeReadResult(known.response()),method.publicName()+" entire original public response, including derived fields");
            assertEquals(known.response().publicJson(),ChinaCasesCodec.decodeReadResult(request,context,known.receipt(),known.response().publicJson()).publicJson());
            var changed=ChinaCasesCodec.encodeReadResult(known.response());changed.put("unregistered_extra",true);
            assertThrows(RuntimeException.class,()->ChinaCasesCodec.decodeReadResult(request,context,known.receipt(),raw(changed)));
            var wrongBuild=new ChinaCasesService.Context(context.query(),context.bridgeVersion(),context.gameAdapterId(),"1.20.0.4","9".repeat(64));
            assertThrows(RuntimeException.class,()->service.query(request,wrongBuild),"a software response cannot qualify another executable");
        }
    }
    @Test void publicMissingNullU64AndMalformedArgumentsRemainDistinctAndNeverDispatch() {
        ObjectNode ai=StrictJson.object();ai.put("request_nonce","valid:nonce");ai.put("owner_character_id",20);ai.put("subject_character_id",30);
        var missing=ChinaCasesCodec.decodeRead(Method.AI_OWNED,ai);assertInstanceOf(PublicUnsigned64.Missing.class,missing.expectedRevision());
        ai.putNull("expected_revision");var nil=ChinaCasesCodec.decodeRead(Method.AI_OWNED,ai);assertInstanceOf(PublicUnsigned64.NullValue.class,nil.expectedRevision());
        assertFalse(ChinaCasesCodec.encodeReadRequest(missing).has("expected_revision"));assertTrue(ChinaCasesCodec.encodeReadRequest(nil).get("expected_revision").isNull());
        ai.put("expected_revision","18446744073709551615");assertEquals(PublicUnsigned64.MAXIMUM,assertInstanceOf(PublicUnsigned64.Value.class,ChinaCasesCodec.decodeRead(Method.AI_OWNED,ai).expectedRevision()).value());
        for(String token:List.of("true","1.0","9007199254740992","\"01\"","\"18446744073709551616\"")) {
            ai.set("expected_revision",StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));assertThrows(RuntimeException.class,()->ChinaCasesCodec.decodeRead(Method.AI_OWNED,ai));
        }
        ObjectNode b1=StrictJson.object();b1.put("request_nonce","with space");b1.put("expected_revision","19");assertThrows(RuntimeException.class,()->ChinaCasesCodec.decodeRead(Method.B1,b1));
        b1.put("request_nonce","valid");b1.put("unexpected",true);assertThrows(RuntimeException.class,()->ChinaCasesCodec.decodeRead(Method.B1,b1));
        assertThrows(RuntimeException.class,()->new org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.Nonce("with space"));
        assertThrows(RuntimeException.class,()->new org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.CharacterId(0));
        assertEquals(BigInteger.valueOf(Integer.MAX_VALUE),new org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.CharacterId(Integer.MAX_VALUE).integer());
    }
    @Test void b1OriginalDerivationPreservesUnknownFalseAndOrderedAnomaliesThroughTheWholeDecoder() throws Exception {
        for(int variant=1;variant<=5;variant++) {
            ObjectNode oracle=oracle(Method.B1,variant);var request=ChinaCasesCodec.decodeRead(Method.B1,object(oracle.get("request")));
            var context=context(object(oracle.get("frame")),BigInteger.valueOf(19),BigInteger.valueOf(3),"china-original-fixture");
            var service=new ChinaCasesService(new ChinaCasesFacade(new SoftwareRead(object(oracle.get("native")),context.query()),noActions()));
            var known=assertInstanceOf(ChinaCasesService.Known.class,service.query(request,context));
            ObjectNode actual=ChinaCasesCodec.encodeReadResult(known.response());assertEquals(oracle.get("public"),actual,"B1 actual Python derivation variant "+variant);
            if(variant==1){assertTrue(actual.get("invariants").get("active_matches_state").isNull());assertEquals("active_state_mismatch",actual.get("anomalies").get(0).textValue());}
            if(variant==2)assertFalse(actual.get("invariants").get("counts_nonnegative").booleanValue());
            if(variant==3)assertFalse(actual.get("invariants").get("closed_state_coherent").booleanValue());
        }
    }
    @Test void originalAckRemainsPendingAndAllNestedBindingsAreCheckedWithoutForgingAWorldEffect() throws Exception {
        ObjectNode oracle=oracle(Method.ACTIVATE_SCOREBOARD);var request=ChinaCasesCodec.decodeAction(object(oracle.get("request")));
        assertEquals(request,ChinaCasesCodec.decodeAction(ChinaCasesCodec.encodeActionRequest(request)));
        var context=context(object(oracle.get("frame")),request.expectedRevision(),request.expectedConnectionGeneration(),"original-scoreboard");
        RawJson original=raw(object(oracle.get("result")));assertSame(original,ChinaCasesCodec.validateActionResult(request,context.query(),original,false));
        ObjectNode wire=ChinaCasesCodec.encodeActionResult(request,context.query(),original);
        assertEquals("acknowledged_verification_pending",wire.get("status").textValue());assertFalse(wire.get("action_ack").get("postcondition_verified").booleanValue());
        assertTrue(wire.get("action_sequence").isTextual());assertTrue(wire.get("action_ack").get("source").get("observation_sequence").isTextual());
        ObjectNode changed=object(oracle.get("result")).deepCopy();object(changed.get("action_ack")).put("postcondition_verified",true);
        RawJson wrongVerified=raw(changed);assertThrows(RuntimeException.class,()->ChinaCasesCodec.validateActionResult(request,context.query(),wrongVerified,false));
        changed=object(oracle.get("result")).deepCopy();object(object(changed.get("action_ack")).get("expected_postcondition")).put("minimum_observation_sequence",1);
        RawJson wrongPost=raw(changed);assertThrows(RuntimeException.class,()->ChinaCasesCodec.validateActionResult(request,context.query(),wrongPost,false));
        ObjectNode unavailable=object(oracle.get("result")).deepCopy();unavailable.put("accepted",false);unavailable.put("status","unavailable");unavailable.put("rejection_reason","unsupported_build");unavailable.putNull("action_ack");
        RawJson rejected=raw(unavailable);assertSame(rejected,ChinaCasesCodec.validateActionResult(request,context.query(),rejected,false));
        unavailable.put("accepted",0);RawJson wrongBool=raw(unavailable);assertThrows(RuntimeException.class,()->ChinaCasesCodec.validateActionResult(request,context.query(),wrongBool,false));
    }
    private final class SoftwareRead implements PlanningReadPort {
        private final ObjectNode nativeResult;private final ChinaCasesFacade.Context context;private int calls;private NativeRequest lastPrepared;
        SoftwareRead(ObjectNode nativeResult,ChinaCasesFacade.Context context) {this.nativeResult=nativeResult;this.context=context;}
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            calls++;lastPrepared=contract.prepare(request,"software-china-query");var ref=reference("query-reference");
            var binding=new GuardEvidence(request.before(),request.source(),request.sessionId(),context.connectionGeneration(),request.operation(),ref,ref,"software-data-only",Instant.now(),Instant.now().plusSeconds(60));
            var guard=new PlanningReadGuard(binding,true,true,true,"a".repeat(64));
            RawJson result=raw(nativeResult);ObjectNode ack=StrictJson.object();ack.put("type","ack");ack.put("request_id","software-china-query");ack.put("ok",true);ack.set("result",nativeResult);
            RawJson rawAck=raw(ack);byte[] body=rawAck.bytes();byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
            var original=new NativeActionPort.AckReceived("software-china-query",true,Optional.of(result),rawAck,packet);
            var receipt=new PlanningReadReceipt(request,contract.contractId(),"software-china-query",guard,guard,original);
            return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,ref);
        }
    }
    private ChinaCasesService.Context context(ObjectNode raw,BigInteger revision,BigInteger generation,String snapshot) {
        var game=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE));var ref=reference("source-original");
        var source=new G2Source("software-fixture",Instant.now().toString(),"china-original-source-differential",ref);
        var identity=new JointBudgetSelector.Frame(raw.get("player_character_id").bigIntegerValue(),raw.get("snapshot_revision").bigIntegerValue(),raw.get("date_raw").bigIntegerValue());
        var frame=new JointBudgetSelector.ProposalFrame(identity,snapshot,revision,"software-china-episode");
        var before=new ProposalLifecycle.ObservationIdentity("software-fixture",game,frame,1);
        return new ChinaCasesService.Context(new ChinaCasesFacade.Context(before,source,"software-session",generation,Instant.now().plusSeconds(60)),"0.1.0","ck3-1.19.0.6-msvc-x64","1.19.0.6",EXE);
    }
    private ObjectNode oracle(Method method) throws Exception { return oracle(method,0); }
    private ObjectNode oracle(Method method,int variant) throws Exception {
        String python=required("xar.native.producer.python"),root=required("xar.public.original.repo.root"),manifest=required("xar.public.china.original.manifest");
        if(!Path.of(python).isAbsolute()||!Path.of(root).isAbsolute()||!Path.of(manifest).isAbsolute())throw new IllegalStateException("absolute pinned original inputs required");
        String manifestBytes=required("xar.public.china.original.manifest.bytes"),manifestSha=required("xar.public.china.original.manifest.sha256");
        new org.xar.ck3.control.build.ControlBuild.FileRef(manifest,Long.parseLong(manifestBytes),manifestSha).verify();
        Path out=temp.resolve(method.name()+".json"),err=temp.resolve(method.name()+".stderr");
        Process process=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL,root,method.name(),Files.readString(Path.of(manifest)),method.readOnly()?method.family().step():"",method.readOnly()?method.payload():"",method.publicName(),Integer.toString(variant)).redirectOutput(out.toFile()).redirectError(err.toFile()).start();
        if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();throw new IllegalStateException("original source differential timed out");}
        if(process.exitValue()!=0)throw new IllegalStateException("original source differential failed: "+Files.readString(err));
        return object(StrictJson.parse(Files.readAllBytes(out),StrictJson.EXPLICIT_MAX_BYTES));
    }
    private static ActionCoordinatorPort noActions(){return new ActionCoordinatorPort(){public ActionReceipt execute(ActionCommand c){throw new AssertionError("query submitted a mutation");}public ActionReceipt reconcile(String id){throw new AssertionError("query reconciled a mutation");}};}
    private ExactRef reference(String name){return new ExactRef(temp.resolve(name).toString(),1,"0".repeat(64));}
    private static RawJson raw(ObjectNode node){return new RawJson(StrictJson.canonical(node));}
    private static ObjectNode object(JsonNode node){return assertInstanceOf(ObjectNode.class,node);}
    private static String required(String name){String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ORIGINAL_INPUT: -D"+name);return value;}
}
