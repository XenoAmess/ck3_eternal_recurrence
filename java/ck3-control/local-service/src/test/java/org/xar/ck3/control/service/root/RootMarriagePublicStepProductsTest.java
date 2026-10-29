package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.MarriageArrangePublicCodec;
import org.xar.ck3.control.service.mcp.MarriageChoicesPublicCodec;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;

/** Actual typed native read/preparation plus original Python Service/driver differential.
 * Software packets and retained DATA do not provide a ManagedRoot, mutation permission, or successful Game effect.
 */
final class RootMarriagePublicStepProductsTest {
    private static final Instant NOW=Instant.parse("2026-10-24T09:20:00Z");
    private static final ExactRef REF=new ExactRef("synthetic/generic-marriage-software-original",1,"a".repeat(64));
    private static final String STEP="arrange-marriage-29829-8";
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static PublicBindings.Arguments args(String value){return PublicBindings.present(raw(value));}
    private static ObjectNode object(RawJson value){return (ObjectNode)StrictJson.parse(value.bytes());}

    @Test void soleSelectorsKeepMarriageSeparateFromKnownNotificationsAndOtherSteps() {
        assertTrue(RootMarriagePublicStepProducts.query(new OperationKey("query-arrange-marriage-choices")));
        assertTrue(RootMarriagePublicStepProducts.marriage(new OperationKey(STEP)));
        assertEquals("29829-8",RootMarriagePublicStepProducts.choiceId(new OperationKey(STEP)).orElseThrow());
        for(String other:List.of("arrange-marriage-x-8","arrange-marriage-29829-8-extra","arrange-marriage-29829-",
                "query-pending-character-interaction-context-v1","accept-pending-character-interaction",
                "reject-pending-character-interaction","acknowledge-pending-character-interaction",
                "initiate-character-interaction-ordinary-v1","submit-player-child-default-marriage-v1-private"))
            assertFalse(RootMarriagePublicStepProducts.marriage(new OperationKey(other)),other);
        assertFalse(RootMarriagePublicStepProducts.query(new OperationKey(STEP)));
    }

    @Test void actualInstalledNativeReadThenOwnerPreparePreservesWholeQueryAndCommandSerde() {
        var rig=new Rig();var known=rig.query();
        ObjectNode expected=rig.packet.deepCopy();expected.put("query_sequence","18446744073709551615");
        ((ObjectNode)expected.path("arrange_marriage_choices").get(0)).put("source","native");expected.put("backend_id","native-headless");
        ObjectNode query=object(RootMarriagePublicStepProducts.queryResult(known));assertEquals(StrictJson.parse(StrictJson.canonical(expected)),query);
        assertTrue(query.path("arrange_marriage_choices").get(0).get("played_character_id").isIntegralNumber());
        assertFalse(query.has("queried_revision"),"generic original result must not borrow typed-facade metadata");
        var request=RootMarriagePublicStepProducts.request(PublicPlanningCodec.decodeExecute(args("{\"step\":\""+STEP+"\"}")));
        var decision=RootMarriagePublicStepProducts.decide(request,List.of(),rig.context,rig.facade,ignored->{throw new AssertionError("no original pending receipt");});
        var command=((RootApplicationSession.SubmitPublicAction<RawJson>)decision).command();
        assertEquals(STEP,command.operation().value());assertEquals(0,rig.submissions);
        var intent=RulerMarriageIntent.fromJson(command.arguments());assertEquals("29829-8",intent.choiceId());
        var proof=object(new RawJson(OpportunityJson.encode(intent.planningProof().orElseThrow())));
        assertEquals(REF,ExactRef.fromJson(proof.get("original_query")));
        assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        assertThrows(InteractionOriginalFailure.class,()->rig.facade.prepareArrangeMarriage(rig.context,"no-replay",new Claims(Set.of(),Set.of(),Set.of(),Set.of()),"29829-8"));
    }

    @Test void originalUnknownSelectsOnlyReconciliationAndCannotAcquireASuccessWrapper() {
        var rig=new Rig();rig.query();
        var request=new MarriageArrangePublicCodec.Request("29829-8",new MarriageChoicesPublicCodec.Request(new MarriageChoicesPublicCodec.MissingRevision()));
        var first=RootMarriagePublicStepProducts.decide(request,List.of(),rig.context,rig.facade,ignored->REF);
        ActionCommand command=((RootApplicationSession.SubmitPublicAction<RawJson>)first).command();
        var unknown=new ActionReceipt(1,4,command,ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual result not resolved; no replay",List.of()));
        rig.query();
        for(int repetition=0;repetition<2;repetition++) {
            var selected=RootMarriagePublicStepProducts.decide(request,List.of(unknown),rig.context,rig.facade,original->{assertSame(unknown,original);return REF;});
            var retained=(RootApplicationSession.ReconcilePublicAction<RawJson>)selected;
            assertEquals(command.actionId(),retained.originalActionId());assertEquals(REF,retained.originalReceipt());
        }
        assertEquals(0,rig.submissions);
        // Reconciliation did not even consume the latest native choice or manufacture a new command.
        assertDoesNotThrow(()->rig.facade.prepareArrangeMarriage(rig.context,"retained-choice-still-present",new Claims(Set.of(),Set.of(),Set.of(),Set.of()),"29829-8"));
        var missing=assertThrows(RootMarriagePublicStepProducts.ResultUnavailable.class,()->RootMarriagePublicStepProducts.requireCompletedResult(unknown,REF));
        assertSame(unknown,missing.receipt());assertEquals(REF,missing.originalReceipt());assertFalse(RootFamilySendRecordingMaterial.supports(unknown));
        var other=new MarriageArrangePublicCodec.Request("29829-9",request.revision());
        assertThrows(IllegalArgumentException.class,()->RootMarriagePublicStepProducts.decide(other,List.of(unknown),rig.context,rig.facade,ignored->REF));
    }

    @Test void genericRequestSerdeKeepsRevisionPresenceAndStrictTypesBeforeAnyProducer() {
        for(String suffix:List.of("",",\"expected_revision\":null",",\"expected_revision\":0",",\"expected_revision\":\"18446744073709551615\"")) {
            var request=PublicPlanningCodec.decodeExecute(args("{\"step\":\""+STEP+"\""+suffix+"}"));
            assertEquals(request,PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicPlanningCodec.encodeExecute(request))));
            var typed=RootMarriagePublicStepProducts.request(request);assertEquals(STEP,typed.step());
            if(request.expectedRevision() instanceof PublicPlanningCodec.RevisionMissing)assertInstanceOf(MarriageChoicesPublicCodec.MissingRevision.class,typed.revision().expectedRevision());
            if(request.expectedRevision() instanceof PublicPlanningCodec.RevisionNull)assertInstanceOf(MarriageChoicesPublicCodec.NullRevision.class,typed.revision().expectedRevision());
        }
        for(String invalid:List.of("true","1.0","9007199254740992","\"01\"","\"18446744073709551616\""))
            assertThrows(IllegalArgumentException.class,()->PublicPlanningCodec.decodeExecute(args("{\"step\":\""+STEP+"\",\"expected_revision\":"+invalid+"}")));
        assertThrows(IllegalArgumentException.class,()->RootMarriagePublicStepProducts.request(PublicPlanningCodec.decodeExecute(args("{\"step\":\"accept-pending-character-interaction\"}"))));
    }

    @Test void wholeOriginalServiceDriverResponsesMatchQueryAndSoleWrapperFormatter()throws Exception {
        var rig=new Rig();var known=rig.query();
        var primitive=StrictJson.object().put("step",STEP).put("accepted",true).put("status","acknowledged_verification_pending")
                .put("revision",new BigInteger("18446744073709551615"));
        primitive.putObject("native_detail").putNull("optional").putArray("values");
        ObjectNode choice=rig.packet.path("arrange_marriage_choices").get(0).deepCopy();
        RawJson numeric=RootFamilySendRecordingMaterial.project(STEP,choice,new RawJson(StrictJson.canonical(primitive)),53146848);
        ObjectNode output=original(rig.packet,primitive);
        assertEquals(output.get("query"),object(RootMarriagePublicStepProducts.queryResult(known)));
        ObjectNode projected=object(RootMarriagePublicStepProducts.publicResult(numeric));assertEquals(output.get("action"),projected);
        assertEquals("proposal_submitted",projected.path("marriage_action").path("status").textValue());
        assertEquals(53146848,projected.path("marriage_action").path("submitted_date_raw").intValue());
        assertTrue(projected.path("marriage_choice").path("candidate_character_id").isIntegralNumber());
        assertFalse(projected.has("relationship_confirmed"));assertFalse(projected.has("eligible_advance"));
        assertEquals(numeric, new RawJson(numeric.bytes()),"public conversion must not rewrite the numeric archive original");
        assertEquals(projected,object(new RawJson(RootMarriagePublicStepProducts.publicResult(numeric).bytes())));
        assertEquals(2,output.path("primitive_steps").size());
        assertEquals(RootMarriagePublicStepProducts.QUERY,output.path("primitive_steps").get(0).textValue());
        assertEquals(STEP,output.path("primitive_steps").get(1).textValue());
        rig.facade.forgetMarriageChoices();
        var fault=assertThrows(org.xar.ck3.control.service.mcp.PublicServiceFailure.class,()->RootMarriageArrangePublicProducts.prepareOriginal(
                rig.facade,rig.context,"original-fault-differential",new Claims(Set.of(),Set.of(),Set.of(),Set.of()),"29829-8"));
        var error=output.path("missing_choice_error");
        assertEquals(error.path("class").textValue(),fault.kind().pythonClassName());assertEquals(error.path("message").textValue(),fault.getMessage());
        assertTrue(fault.originalCandidate().isEmpty());assertEquals(0,rig.submissions);
    }

    @Test void missingNullWrongTypeDiagnosticsAndUnknownWideIntegersFailWithoutSubmission() {
        for(int mode=0;mode<3;mode++) {
            var rig=new Rig();var diagnostic=(ObjectNode)rig.packet.get("arrange_marriage_diagnostics");
            if(mode==0)diagnostic.remove("slots_scanned");else if(mode==1)diagnostic.putNull("slots_scanned");else diagnostic.put("slots_scanned",true);
            assertThrows(IllegalArgumentException.class,()->RootMarriagePublicStepProducts.queryResult(rig.query()));assertEquals(0,rig.submissions);
        }
        assertThrows(IllegalArgumentException.class,()->RootMarriagePublicStepProducts.publicResult(raw("{\"unknown_native_id\":9007199254740992}")));
        assertThrows(IllegalArgumentException.class,()->RootMarriagePublicStepProducts.publicResult(raw("{\"revision\":null}")));
        assertThrows(IllegalArgumentException.class,()->RootMarriagePublicStepProducts.publicResult(raw("{\"query_sequence\":true}")));
        assertThrows(IllegalArgumentException.class,()->RootMarriagePublicStepProducts.publicResult(raw("{\"revision\":1.0}")));
    }

    @Test void actualStrongPreparationCannotInventAnOriginalDriverInvocationOrMapUnknownToAnExceptionClass() {
        var rig=new Rig();rig.query();
        var request=new MarriageArrangePublicCodec.Request("29829-8",new MarriageChoicesPublicCodec.Request(new MarriageChoicesPublicCodec.MissingRevision()));
        var decision=RootMarriagePublicStepProducts.decide(request,List.of(),rig.context,rig.facade,ignored->REF);
        var command=((RootApplicationSession.SubmitPublicAction<RawJson>)decision).command();
        assertThrows(java.io.IOException.class,()->RootPublicStepFailureOriginals.trackPreparedAction(command),
                "a typed prepared command does not create Root's private original Driver entry");
        assertEquals(0,rig.submissions);assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        var unknown=new ActionReceipt(1,4,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),Optional.empty(),"unresolved original",List.of()));
        Throwable retained=assertThrows(RootMarriagePublicStepProducts.ResultUnavailable.class,()->RootMarriagePublicStepProducts.requireCompletedResult(unknown,REF));
        assertFalse(retained instanceof org.xar.ck3.control.service.mcp.PublicServiceFailure,
                "UNKNOWN and an unavailable complete wrapper cannot supply a guessed Python exception class");
        assertEquals(0,rig.submissions);
    }

    static final class Rig {
        final ObjectNode packet=packet();final Context context;final InteractionCapabilities facade;int submissions;
        Rig() {
            var template=MarriageArrangePublicCodecTest.commandData();
            var source=new G2Source(template.before().machineId(),NOW.toString(),Build.CROZIER4.version(),REF);
            context=new Context(template.before(),source,template.sessionId(),BigInteger.TWO,Build.CROZIER4,NOW.plusSeconds(30),
                    new ControlFrame(true,true,true,1,19L,29829,template.before().frame().episodeRunId(),false,null,null,List.of()));
            var sources=new InteractionCapabilities.Sources(REF,REF,REF,REF,REF,REF,REF,REF,REF,REF);
            var root=new InteractionCapabilities.RootHeirSource() {
                public PlanningReadResult<HeirSubject> read(Context ignored){throw new AssertionError("marriage query has no heir policy");}
                public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Context ignored){throw new AssertionError("marriage query has no heir policy");}
            };
            var installed=new InteractionCapabilities.Installation(sources,new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),root);
            var reads=new PlanningReadPort(){public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
                assertSame(installed.marriageChoices(),contract);var receipt=receipt(contract,request,packet);
                return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,REF);
            }};
            var actions=new ActionCoordinatorPort() {
                public ActionReceipt execute(ActionCommand command){submissions++;throw new AssertionError("pure preparation must not execute");}
                public ActionReceipt reconcile(String id){throw new AssertionError("pure branch selection does not execute reconciliation");}
            };
            facade=new InteractionCapabilities(installed,reads,actions);
        }
        PlanningReadResult.Known<MarriageChoices> query(){return (PlanningReadResult.Known<MarriageChoices>)facade.queryArrangeMarriageChoices(context);}
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract,PlanningReadRequest request,ObjectNode result) {
        String id="generic-choices-query";ObjectNode packet=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);
        packet.set("result",result);byte[] bytes=StrictJson.canonical(packet);
        byte[] nativePacket;
        try { nativePacket=NativeWire.packet(bytes); }
        catch (java.io.IOException failure) { throw new java.io.UncheckedIOException("controlled marriage packet encoding failed",failure); }
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(bytes),nativePacket);
        var evidence=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.TWO,request.operation(),REF,REF,"software-generic-marriage",NOW,NOW.plusSeconds(60));
        var guard=new PlanningReadGuard(evidence,true,true,true,"b".repeat(64));
        return new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
    }
    private static ObjectNode packet() {
        var n=StrictJson.object().put("step",RootMarriagePublicStepProducts.QUERY).put("accepted",true).put("status","available")
                .put("query_sequence",new BigInteger("18446744073709551615"));
        n.putArray("arrange_marriage_choices").addObject().put("choice_id","29829-8").put("played_character_id",29829).put("candidate_character_id",8);
        n.putObject("arrange_marriage_diagnostics").put("storage_capacity",1).put("slots_scanned",1).put("empty_slots",0).put("live_candidates",1)
                .put("dead_candidates",0).put("self_candidates",0).put("generation_mismatch_candidates",0).put("contexts_constructed",1)
                .put("context_construct_failures",0).put("native_validate_true",1).put("native_validate_false",0).putArray("validation_false_samples");
        return n;
    }

    private static ObjectNode original(ObjectNode query,ObjectNode primitive)throws Exception {
        Path repo=Path.of(required("xar.repository.root")),python=Path.of(required("xar.python"));
        assertTrue(repo.isAbsolute()&&Files.isDirectory(repo));assertTrue(python.isAbsolute()&&Files.isRegularFile(python));
        repo=repo.toRealPath();python=python.toRealPath();
        ObjectNode input=StrictJson.object();input.set("query",query);input.set("primitive",primitive);
        var builder=new ProcessBuilder(python.toString(),"-B","-X","utf8","-c",ORACLE,repo.toString()).directory(repo.toFile()).redirectErrorStream(true);
        builder.environment().put("PYTHONPATH",repo.resolve("ck3_autonomous_player/src").toString());builder.environment().put("XAR_SOURCE_REPOSITORY",repo.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONUTF8","1");
        Process child=builder.start();
        try {
            var output=CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readNBytes(1048577);}catch(java.io.IOException error){throw new java.io.UncheckedIOException(error);}});
            try(var stdin=child.getOutputStream()){stdin.write(StrictJson.canonical(input));}
            assertTrue(child.waitFor(30,TimeUnit.SECONDS));byte[] bytes=output.get(5,TimeUnit.SECONDS);
            assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));assertTrue(bytes.length<=1048576);return object(new RawJson(bytes));
        }finally{if(child.isAlive())child.destroyForcibly();}
    }
    private static String required(String key){String value=System.getProperty(key);assertTrue(value!=null&&!value.isBlank(),"required actual CI input: "+key);return value;}
    private static final String ORACLE="""
import copy,hashlib,json,pathlib,sys,threading,types
sys.dont_write_bytecode=True
repo=pathlib.Path(sys.argv[1]).resolve();base=repo/'ck3_autonomous_player/src/xar_autoplayer/bridge'
pins={'native_driver.py':(1658471,'eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603'),'service.py':(897392,'a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e'),'marriage_contract.py':(3370,'f85b94e237f7ec4baa7cb872b29514cec4210afca583fc51075114e6e7e4db71')}
for name,(size,sha) in pins.items():
 raw=(base/name).read_bytes()
 if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:raise RuntimeError('actual original source changed: '+name)
sys.path.insert(0,str(base.parent.parent))
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
value=json.load(sys.stdin);steps=[];query='query-arrange-marriage-choices';send='arrange-marriage-29829-8'
driver=types.SimpleNamespace(_driver_state_lock=threading.RLock(),_arrange_marriage_choices=[],_arrange_marriage_query_sequence=None,
 capabilities=lambda:{'action_steps':[query,send],'bridge_capabilities':[]},take_snapshot=lambda:{'date_raw':53146848},
 take_snapshot_without_native_command_history=lambda:{'played_character':{'character_id':29829}})
def primitive(step,**kwargs):
 steps.append(step);body=copy.deepcopy(value['query'] if step==query else value['primitive']);body['backend_id']='native-headless';return body
driver._execute_primitive_step=primitive
driver._execute_arrange_marriage_step=types.MethodType(NativeHeadlessGameplayDriver._execute_arrange_marriage_step,driver)
driver.execute_step=lambda step,**kwargs:NativeHeadlessGameplayDriver._execute_step_unrecorded(driver,step,**kwargs)
service=types.SimpleNamespace(driver=driver)
out={'query':GameplayBridgeService.execute_step(service,query,expected_revision=7),'action':GameplayBridgeService.execute_step(service,send,expected_revision=7),'primitive_steps':steps}
if driver._arrange_marriage_choices or driver._arrange_marriage_query_sequence is not None:raise RuntimeError('original finally did not clear choice cache')
try:GameplayBridgeService.execute_step(service,send,expected_revision=7)
except Exception as error:out['missing_choice_error']={'class':type(error).__name__,'message':str(error)}
else:raise RuntimeError('original empty-choice branch unexpectedly returned a result')
for result in (out['query'],out['action']):
 for key in ('query_sequence','revision','native_revision','queried_revision','queried_native_revision'):
  if key in result:result[key]=str(result[key])
for name,(size,sha) in pins.items():
 if hashlib.sha256((base/name).read_bytes()).hexdigest()!=sha:raise RuntimeError('source drifted during original differential')
json.dump(out,sys.stdout,separators=(',',':'))
""";
}
