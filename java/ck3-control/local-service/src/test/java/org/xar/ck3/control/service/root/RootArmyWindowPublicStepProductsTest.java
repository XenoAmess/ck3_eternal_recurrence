package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Original Python full responses -> the actual Java formatter -> public wire -> serde.
 * Synthetic original fixtures are software evidence; no Root authority or Game success is manufactured. */
final class RootArmyWindowPublicStepProductsTest {
    private static final BigInteger WIDE=new BigInteger("18446744073709551615");
    private static final String[][] PINS={
        {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_declared_overview_contract.py","86ebfb0fc5ba6a0150f28c8ac4aeceb3c65116b03d0f5175a99fc9659377ece0"},
        {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_results_window_contract.py","3373fd42fc1cf8da88caf515061b4d8909816bf4ace66a6e01b25ac091a6cd66"},
        {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_declared_overview_transport.py","52183d4339e407bdbc29f9b222d28a7b80c5691a5b67e6ef158e9313a6f77b4c"},
        {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_results_window_transport.py","e1a3d7d5ae36ccf2a17055d166742f3fd49b11529bdbd383c7b2b9d5640fd86e"},
        {"ck3_autonomous_player/tests/unit/test_war_declared_overview_transport.py","9396dbd32df16530dceaa9b928b5d4c29eaf693e711f7ae27017c62fc6933365"},
        {"ck3_autonomous_player/tests/test_war_results_window_contract_b15.py","37264573cfca1d344146a17f5756df60f4e730f26b42e21d1457543f7e065237"},
        {"ck3_autonomous_player/tests/unit/test_war_results_scope_transition_transport.py","2d77c0809312a14a230927e783210db6be3ec9402300c6c0021c69db5a8b5b9d"},
        {"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"}
    };
    private static volatile ObjectNode retained;
    private static ArmyTypes.Context source(){
        var ref=new ExactRef("software-original-window-source",1,"a".repeat(64));
        var source=new G2Source("software-fixture-machine","2026-10-24T00:00:00Z","1.20.0.4",ref);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(31254),
                BigInteger.valueOf(617),BigInteger.valueOf(53169792)),"fixture:617",BigInteger.valueOf(9),"fixture-episode");
        return new ArmyTypes.Context(new ObservationIdentity(source.machineId(),new GameGeneration(42,
                new PythonOnlyUInt64(BigInteger.ONE)),frame,1),source,"fixture-session",Instant.parse("2026-10-24T00:01:00Z"));
    }
    private static ObjectNode object(JsonNode n){assertInstanceOf(ObjectNode.class,n);return (ObjectNode)n;}
    private static RawJson raw(JsonNode n){return new RawJson(StrictJson.canonical(n));}
    private static ObjectNode parsed(RawJson n){return object(StrictJson.parse(n.bytes()));}
    private static ArmyTypes.Context sourceFor(ObjectNode sample){
        ObjectNode expected=object(sample.get("expected"));var base=source();
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(expected.get("queried_actor_character_id").bigIntegerValue(),
                expected.get("queried_native_revision").bigIntegerValue(),expected.get("queried_date_raw").bigIntegerValue()),
                expected.get("queried_snapshot_id").textValue(),expected.get("queried_revision").bigIntegerValue(),
                expected.get("queried_episode_run_id").isNull()?null:expected.get("queried_episode_run_id").textValue());
        return new ArmyTypes.Context(new ObservationIdentity(base.before().machineId(),base.before().game(),frame,1),
                base.source(),base.sessionId(),base.deadline());
    }
    private static RawJson format(ObjectNode sample){
        ObjectNode top=object(sample.get("top"));
        return RootArmyPublicStepProducts.windowNumeric(new OperationKey(sample.get("step").textValue()),raw(top),
                top.get("request_id").textValue(),sourceFor(sample),sample.get("generation").bigIntegerValue(),sample.get("driver_generation").bigIntegerValue());
    }

    @Test void bothOriginalCloseTransportsPreserveWholeResponsesForEveryCompletionBranch()throws Exception {
        ObjectNode corpus=corpus();int count=0;
        for(JsonNode item:corpus.withArray("cases")){
            ObjectNode sample=object(item),expected=object(sample.get("expected"));RawJson numeric=format(sample);
            assertEquals(expected,parsed(numeric),sample.get("name").textValue());
            RawJson encoded=RootArmyPublicStepProducts.encodeOriginal(numeric,sourceFor(sample));
            assertEquals(DriverJson.object(numeric.bytes(),DriverJson.MAX_NATIVE_BYTES),ArmyPublicWire.decodeExactSourceBound(encoded,sourceFor(sample)));
            assertEquals(parsed(encoded),parsed(raw(parsed(encoded))));
            assertEquals(expected.get("accepted"),parsed(encoded).get("accepted"));
            assertEquals(expected.get("closure_verified"),parsed(encoded).get("closure_verified"));
            assertFalse(parsed(encoded).has("action_id"));assertFalse(parsed(encoded).has("world_effect_verified"));count++;
        }
        assertEquals(17,count,"both seven-branch transports, scope transition and two distinct native/Driver generation cases are required");
    }
    @Test void completeWideOwnerSequenceRolesSurvivePublicSerdeWithoutRounding()throws Exception {
        for(JsonNode item:corpus().withArray("wide")){
            ObjectNode sample=object(item);RawJson numeric=format(sample);
            assertEquals(sample.get("expected"),parsed(numeric));ObjectNode encoded=parsed(RootArmyPublicStepProducts.encodeOriginal(numeric,source()));
            String key=sample.get("owner_key").textValue();ObjectNode owner=object(encoded.get("native_command_result").get(key));
            for(String role:List.of("ticket_sequence","executor_started_sequence","completed_sequence","pump_epoch"))
                assertEquals(WIDE.toString(),owner.get(role).textValue(),role);
            assertEquals(DriverJson.object(numeric.bytes(),DriverJson.MAX_NATIVE_BYTES),
                    ArmyPublicWire.decodeExactSourceBound(raw(encoded),source()));
        }
    }
    @Test void actualTopOwnerRequestTypeAndCompleteLeafCannotBeSubstituted()throws Exception {
        ObjectNode sample=object(corpus().withArray("cases").get(0));
        for(String fault:List.of("missing_owner","owner_request","owner_started","bool_sequence","float_revision","null_leaf","extra_leaf","wrong_request","partial_stage")){
            ObjectNode changed=sample.deepCopy(),top=object(changed.get("top")),leaf=object(top.get("result"));
            String key=changed.get("owner_key").textValue();ObjectNode owner=object(top.get(key));
            switch(fault){
                case "missing_owner" -> top.remove(key);
                case "owner_request" -> owner.put("request_id","different-original");
                case "owner_started" -> owner.put("executor_started_sequence",14);
                case "bool_sequence" -> owner.put("ticket_sequence",true);
                case "float_revision" -> leaf.put("native_revision",617.0);
                case "null_leaf" -> top.putNull("result");
                case "extra_leaf" -> leaf.put("invented_success",true);
                case "wrong_request" -> leaf.put("request_id","different-original");
                case "partial_stage" -> {leaf.remove("close_exception_code");leaf.put("close_stage","not_attempted");}
                default -> throw new AssertionError(fault);
            }
            assertThrows(IllegalArgumentException.class,()->format(changed),fault);
        }
    }
    @Test void formatterRequiresOriginalCloseIdentityAndActualNativeLease()throws Exception {
        ObjectNode sample=object(corpus().withArray("cases").get(0)),top=object(sample.get("top"));
        assertTrue(RootArmyPublicStepProducts.windowKind(new OperationKey("query-war-results-window-v1")).isEmpty());
        assertTrue(RootArmyPublicStepProducts.windowKind(new OperationKey("close-war-results-window-v1-extra")).isEmpty());
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.windowNumeric(new OperationKey("query-war-declared-overview-v1"),raw(top),top.get("request_id").textValue(),source(),BigInteger.valueOf(17),BigInteger.valueOf(17)));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.windowNumeric(new OperationKey(sample.get("step").textValue()),raw(top),top.get("request_id").textValue(),source(),BigInteger.valueOf(18),BigInteger.valueOf(17)));
        ObjectNode pending=object(corpus().withArray("cases").get(3));assertFalse(parsed(format(pending)).get("closure_verified").booleanValue());
    }
    @Test void nativeHelloAndDriverGenerationRemainIndependentIncludingDriverZero()throws Exception {
        int seen=0;
        for(JsonNode item:corpus().withArray("cases")){
            ObjectNode sample=object(item);if(!sample.get("name").textValue().startsWith("overview-native23-driver"))continue;
            ObjectNode result=parsed(format(sample));assertEquals(23,result.get("connection_generation").intValue());
            assertEquals(sample.get("driver_generation"),result.get("queried_connection_generation"));
            ObjectNode publicResult=parsed(RootArmyPublicStepProducts.encodeOriginal(raw(result),sourceFor(sample)));
            assertEquals("23",publicResult.get("connection_generation").textValue());
            assertEquals(sample.get("driver_generation").bigIntegerValue().toString(),publicResult.get("queried_connection_generation").textValue());seen++;
        }
        assertEquals(2,seen);
    }
    @Test void actualOriginalScopeTransitionTransportKeepsItsBeforeLeaseAndPendingResponse()throws Exception {
        ObjectNode sample=null;
        for(JsonNode item:corpus().withArray("cases"))if(item.get("name").textValue().equals("results-scope-transition"))sample=object(item);
        assertNotNull(sample);ObjectNode normalized=parsed(format(sample));assertEquals(sample.get("expected"),normalized);
        assertEquals("verification_pending",normalized.get("status").textValue());assertFalse(normalized.get("available").booleanValue());
        assertFalse(normalized.get("accepted").booleanValue());assertFalse(normalized.get("closure_verified").booleanValue());
        assertFalse(normalized.get("scope_unchanged").booleanValue());assertFalse(sample.get("after_snapshot").get("paused").booleanValue());
        assertTrue(sample.get("after_snapshot").get("date_raw").bigIntegerValue().compareTo(normalized.get("queried_date_raw").bigIntegerValue())>0);
        assertEquals(1,sample.get("sent_commands").intValue());
        assertEquals(normalized,parsed(raw(normalized)));assertFalse(normalized.has("close_action_credit"));
    }
    @Test void originalRequiredRevisionAndStaleFaultsAreOwnerOrderedForBothCloseRoutes(){
        for(var kind:ArmyWindowCodec.Kind.values()){
            OperationKey step=new OperationKey(kind.step(ArmyWindowCodec.Operation.CLOSE));
            String label=kind==ArmyWindowCodec.Kind.OVERVIEW?"war overview":"war results";
            for(var missing:List.of(new PublicPlanningCodec.RevisionMissing(),new PublicPlanningCodec.RevisionNull(),new PublicPlanningCodec.RevisionValue(BigInteger.ZERO))){
                var caller=new PublicPlanningCodec.ExecuteRequest(step,missing,new PublicPlanningCodec.FrameMissing());
                var error=assertThrows(PublicServiceFailure.class,()->RootArmyPublicStepProducts.windowCall(caller,BigInteger.valueOf(9)));
                assertEquals(PublicServiceFailure.Kind.VALUE_ERROR,error.kind());
                assertEquals(label+" expected_revision is outside its native integer range",error.getMessage());
            }
            var stale=new PublicPlanningCodec.ExecuteRequest(step,new PublicPlanningCodec.RevisionValue(BigInteger.ONE),new PublicPlanningCodec.FrameMissing());
            var error=assertThrows(PublicServiceFailure.class,()->RootArmyPublicStepProducts.windowCall(stale,BigInteger.valueOf(9)));
            assertEquals(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,error.kind());assertEquals(label+" public revision is stale",error.getMessage());
            var valid=new PublicPlanningCodec.ExecuteRequest(step,new PublicPlanningCodec.RevisionValue(WIDE),new PublicPlanningCodec.FrameMissing());
            assertEquals(new ArmyCalls.Revision(new ArmyTypes.Present<>(WIDE)),RootArmyPublicStepProducts.windowCall(valid,WIDE).revision());
        }
    }
    @Test void originalArmyRevisionRulesKeepCommanderRequiredAndOtherStepsOptional(){
        for(var kind:RootArmyPublicStepProducts.Kind.values()){
            String step=kind==RootArmyPublicStepProducts.Kind.COMMANDER?"assign-army-commander-v1-army-0-to-character-0"
                    :kind==RootArmyPublicStepProducts.Kind.RAISE?"raise-troops-default":"disband-army-0";
            for(var absent:List.of(new PublicPlanningCodec.RevisionMissing(),new PublicPlanningCodec.RevisionNull())){
                var caller=new PublicPlanningCodec.ExecuteRequest(new OperationKey(step),absent,new PublicPlanningCodec.FrameMissing());
                if(kind==RootArmyPublicStepProducts.Kind.COMMANDER){
                    var error=assertThrows(PublicServiceFailure.class,()->RootArmyPublicStepProducts.requireArmyRevision(kind,caller,BigInteger.ZERO));
                    assertEquals(PublicServiceFailure.Kind.VALUE_ERROR,error.kind());assertEquals("expected_revision must be a non-negative integer",error.getMessage());
                }else assertDoesNotThrow(()->RootArmyPublicStepProducts.requireArmyRevision(kind,caller,BigInteger.ZERO));
            }
            var zero=new PublicPlanningCodec.ExecuteRequest(new OperationKey(step),new PublicPlanningCodec.RevisionValue(BigInteger.ZERO),new PublicPlanningCodec.FrameMissing());
            assertDoesNotThrow(()->RootArmyPublicStepProducts.requireArmyRevision(kind,zero,BigInteger.ZERO));
            var error=assertThrows(PublicServiceFailure.class,()->RootArmyPublicStepProducts.requireArmyRevision(kind,zero,BigInteger.ONE));
            assertEquals(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,error.kind());
            assertEquals(kind==RootArmyPublicStepProducts.Kind.COMMANDER?"native commander assignment source revision is stale"
                    :"native gameplay revision mismatch: expected 0, current 1",error.getMessage());
        }
    }
    @Test void actualRefusalAndUnknownKeepTheirSpecializedOriginalMessagesAndCustody(){
        ExactRef original=new ExactRef("software-original-window-refusal",8,"b".repeat(64));
        ObjectNode refusal=StrictJson.object().put("type","command_result").put("protocol_version",1)
                .put("request_id","original-close").put("ok",false).put("error","actual native refusal");
        for(var kind:ArmyWindowCodec.Kind.values()){
            String label=kind==ArmyWindowCodec.Kind.OVERVIEW?"war overview":"war results";
            var error=RootArmyPublicStepProducts.windowNativeFailure(kind,raw(refusal),"original-close",java.util.Optional.of(original));
            assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,error.kind());assertEquals("Native "+label+" refused: actual native refusal",error.getMessage());
            assertEquals(java.util.Optional.of(original),error.originalCandidate());
            var unknown=new NativeActionPort.Unknown("original-close","no response observed",new byte[]{1},java.util.Optional.empty());
            var pending=RootArmyPublicStepProducts.windowDispatchFailure(kind,unknown,java.util.Optional.of(original));
            assertEquals(label+" original command_result timed out",pending.getMessage());assertEquals(java.util.Optional.of(original),pending.originalCandidate());
            for(ObjectNode invalid:List.of(refusal.deepCopy().put("protocol_version",true),refusal.deepCopy().put("request_id","different"),
                    refusal.deepCopy().put("ok",true),refusal.deepCopy().put("extra",1),refusal.deepCopy().putNull("error")))
                assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.windowNativeFailure(kind,raw(invalid),"original-close",java.util.Optional.of(original)));
        }
    }
    @Test void originalCommanderDriverCatchProducesTheSameCompleteFailureReportAndPublicRoles()throws Exception {
        ObjectNode sample=object(corpus().get("commander_failure"));
        var operation=new OperationKey(sample.get("step").textValue());
        var request=DriverJson.object(raw(sample.get("request")).bytes(),65536);
        var response=DriverJson.object(raw(sample.get("response")).bytes(),65536);
        RawJson numeric=RootArmyPublicStepProducts.commanderRejectedResult(operation,sample.get("request_id").textValue(),request,response);
        assertEquals(sample.get("expected"),parsed(numeric));
        ObjectNode exposed=parsed(RootArmyPublicStepProducts.encodeOriginal(numeric,source()));
        assertEquals(WIDE.toString(),exposed.get("native_request_frame").get("expected_revision").textValue());
        assertTrue(exposed.get("never_replay").booleanValue());assertFalse(exposed.has("accepted"));
        assertEquals(request,ArmyPublicWire.decodeExactSourceBound(raw(exposed),source()).get("native_request_frame"));
        assertEquals(exposed,parsed(raw(exposed)));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.commanderRejectedResult(operation,"different",request,response));
        var wrongRevision=new java.util.LinkedHashMap<>(request.members());wrongRevision.put("expected_revision",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.commanderRejectedResult(operation,sample.get("request_id").textValue(),
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(wrongRevision),response));
        var wrongResponse=new java.util.LinkedHashMap<>(response.members());wrongResponse.put("request_id",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("another-request"));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.commanderRejectedResult(operation,sample.get("request_id").textValue(),request,
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(wrongResponse)));

    }

    private static synchronized ObjectNode corpus()throws Exception {
        if(retained!=null)return retained.deepCopy();Path repository=required("xar.repository.root",true),python=required("xar.python",false);
        pins(repository);
        String script="""
                import sys,os,json,importlib.util
                from pathlib import Path
                sys.dont_write_bytecode=True
                root=Path(sys.argv[1])
                os.environ['XAR_SOURCE_REPOSITORY']=str(root)
                os.environ['PYTHONDONTWRITEBYTECODE']='1'
                for p in (root,root/'ck3_autonomous_player',root/'ck3_autonomous_player'/'src',root/'ck3_autonomous_player'/'tests'/'unit'):
                    sys.path.insert(0,str(p))
                def load(name,path):
                    spec=importlib.util.spec_from_file_location(name,root/path)
                    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
                ov=load('original_overview_window_fixture','ck3_autonomous_player/tests/unit/test_war_declared_overview_transport.py')
                rs=load('original_results_window_fixture','ck3_autonomous_player/tests/test_war_results_window_contract_b15.py')
                from xar_autoplayer.bridge import war_declared_overview_transport as overview
                from xar_autoplayer.bridge import war_results_window_transport as results
                before={'played_character':{'character_id':31254},'date_raw':53169792,'native_revision':617}
                binding={'snapshot_id':'fixture:617','revision':9,'native_revision':617,'date_raw':53169792,'actor_character_id':31254,'episode_run_id':'fixture-episode'}
                cases=[];wide=[]
                for family,transport,generation in (('overview',overview,17),('results',results,13)):
                    for branch in ('closed','hidden','absent','pending','unavailable','preflight','exception'):
                        if family=='overview':
                            presence='hidden' if branch=='hidden' else 'absent' if branch=='absent' else 'visible'
                            top=ov._reply({'request_id':'original-'+family+'-'+branch},before,presence=presence,operation='close',pending=branch in ('pending','preflight','exception'),unavailable=branch=='unavailable')
                            owner_key='war_declared_overview_owner_receipt';stage='close'
                        else:
                            leaf=rs.old_leaf();owner_key='war_results_window_owner_receipt';stage='dismiss'
                            leaf['request_id']='original-'+family+'-'+branch
                            owner={'request_id':leaf['request_id'],'ticket_sequence':303,'executor_started_sequence':303,'completed_sequence':303,'pump_epoch':101,'thread_id':202,'date_raw':53169792,'connection_generation':generation}
                            top={'type':'command_result','protocol_version':1,'request_id':leaf['request_id'],'ok':True,'result':leaf,owner_key:owner}
                            if branch=='closed':leaf.update(available=True,accepted=True,status='closed_verified',unavailable_reason='',dispatch_invoked=True,native_handled=True,closure_verified=True,post_effective_visible=False)
                            elif branch in ('hidden','absent'):
                                present=branch=='hidden'
                                leaf.update(available=True,accepted=False,status='already_'+branch,unavailable_reason='',window_present=present,effective_visible=False,button_name='',dispatch_attempted=False,post_window_present=present,post_effective_visible=False)
                            elif branch=='unavailable':leaf.update(status='unavailable',dispatch_attempted=False,root_observed=False,window_present=False,effective_visible=False,post_observed=False,post_window_present=False,post_effective_visible=False,scope_unchanged=False,button_name='')
                            elif branch=='pending':leaf.update(dispatch_invoked=True,native_handled=True)
                        leaf=top['result']
                        if branch=='preflight':leaf.update(**{stage+'_stage':'preflight_rejected',stage+'_exception_code':0,'dispatch_invoked':False,'native_handled':False})
                        elif branch=='exception':leaf.update(**{stage+'_stage':'callback_exception',stage+'_exception_code':0xC0000005,'dispatch_invoked':False,'native_handled':False})
                        source={**binding,'connection_generation':generation}
                        expected=transport._result(top,top['request_id'],'close',source,generation)
                        sample={'name':family+'-'+branch,'step':transport.CLOSE_STEP,'generation':generation,'driver_generation':generation,'owner_key':owner_key,'top':top,'expected':expected}
                        cases.append(sample)
                    top=json.loads(json.dumps(cases[-7]['top']));owner=top[owner_key]
                    for key in ('ticket_sequence','executor_started_sequence','completed_sequence','pump_epoch'):owner[key]=(1<<64)-1
                    for key in ('ticket_sequence','pump_epoch'):top['result'][key]=(1<<64)-1
                    expected=transport._result(top,top['request_id'],'close',{**binding,'connection_generation':generation},generation)
                    wide.append({'name':family+'-wide','step':transport.CLOSE_STEP,'generation':generation,'driver_generation':generation,'owner_key':owner_key,'top':top,'expected':expected})
                transition=load('original_results_transition_fixture','ck3_autonomous_player/tests/unit/test_war_results_scope_transition_transport.py')
                driver,sent=transition.fixture('close');original_wait=driver.state.wait_for_command_result;captured=[]
                def wait_original(rid,timeout):
                    packet=original_wait(rid,timeout);captured.append(packet);return packet
                driver.state.wait_for_command_result=wait_original
                original_snapshot=driver.take_internal_semantic_snapshot;snapshots=[]
                def retained_snapshot():
                    value=original_snapshot();snapshots.append(value);return value
                driver.take_internal_semantic_snapshot=retained_snapshot
                expected=results.execute_war_results_window_v1(driver,operation='close',expected_revision=3)
                cases.append({'name':'results-scope-transition','step':results.CLOSE_STEP,'generation':13,'driver_generation':13,
                    'owner_key':'war_results_window_owner_receipt','top':captured[0],'expected':expected,
                    'after_snapshot':snapshots[-1],'sent_commands':len(sent)})
                for driver_generation in (0,17):
                    top=json.loads(json.dumps(cases[0]['top']))
                    top['result']['connection_generation']=23;top['war_declared_overview_owner_receipt']['connection_generation']=23
                    expected=overview._result(top,top['request_id'],'close',{**binding,'connection_generation':driver_generation},23)
                    cases.append({'name':'overview-native23-driver'+str(driver_generation),'step':overview.CLOSE_STEP,'generation':23,
                        'driver_generation':driver_generation,'owner_key':'war_declared_overview_owner_receipt','top':top,'expected':expected})
                from types import SimpleNamespace
                from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver,_NativeCommandRejectedError
                step='assign-army-commander-v1-army-0-to-character-0';rid='original-commander-failure'
                request={'type':'execute_step','protocol_version':1,'request_id':rid,'step':step,'expected_revision':(1<<64)-1}
                response={'type':'command_result','protocol_version':1,'request_id':rid,'ok':False,'error':'actual native refusal'}
                error=_NativeCommandRejectedError('actual native refusal',native_request_id=rid,native_request_frame=request,native_command_result_frame=response)
                recorded=[]
                def fail_original(*args,**kwargs):raise error
                driver=SimpleNamespace(_execute_step_unrecorded=fail_original,_record_command=lambda step,**kwargs:recorded.append(kwargs))
                try:NativeHeadlessGameplayDriver.execute_step(driver,step,expected_revision=9)
                except _NativeCommandRejectedError as actual:
                    assert actual is error
                assert len(recorded)==1 and recorded[0]['ok'] is False
                commander={'step':step,'request_id':rid,'request':request,'response':response,'expected':recorded[0]['result']}
                print(json.dumps({'cases':cases,'wide':wide,'commander_failure':commander},allow_nan=False))
                """;
        ProcessBuilder builder=new ProcessBuilder(python.toString(),"-B","-X","utf8","-",repository.toString()).directory(repository.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("XAR_SOURCE_REPOSITORY",repository.toString());
        builder.environment().put("PYTHONPATH",repository.resolve("ck3_autonomous_player/src").toString()+java.io.File.pathSeparator+repository.resolve("ck3_autonomous_player/tests/unit"));
        Process child=builder.start();FutureTask<byte[]> stdout=new FutureTask<>(()->child.getInputStream().readNBytes(1024*1024+1));
        FutureTask<byte[]> stderr=new FutureTask<>(()->child.getErrorStream().readNBytes(16385));Thread.ofVirtual().start(stdout);Thread.ofVirtual().start(stderr);
        try{
            try(var input=child.getOutputStream()){input.write(script.getBytes(StandardCharsets.UTF_8));}
            if(!child.waitFor(60,TimeUnit.SECONDS))throw new IOException("original close-window transport oracle timed out");
            byte[] output=stdout.get(5,TimeUnit.SECONDS),errors=stderr.get(5,TimeUnit.SECONDS);
            if(output.length>1024*1024||errors.length>16384)throw new IOException("original close-window oracle output exceeded bound");
            if(child.exitValue()!=0)throw new IOException("original close-window oracle exit="+child.exitValue()+": "+new String(errors,StandardCharsets.UTF_8));
            pins(repository);retained=object(StrictJson.parse(output, 1_048_576));return retained.deepCopy();
        }finally{if(child.isAlive()){child.destroyForcibly();child.waitFor(5,TimeUnit.SECONDS);}}
    }
    private static Path required(String property,boolean directory)throws IOException {
        String supplied=System.getProperty(property);if(supplied==null||supplied.isBlank())throw new IOException("required original oracle property missing: "+property);
        Path path=Path.of(supplied);if(!path.isAbsolute())throw new IOException("absolute original oracle property required: "+property);
        Path actual=path.toRealPath();if(directory?!Files.isDirectory(actual):!Files.isRegularFile(actual))throw new IOException("unavailable original oracle property: "+property);return actual;
    }
    private static void pins(Path root)throws Exception {
        for(String[] pin:PINS){Path path=root.resolve(pin[0]).toRealPath();if(!path.startsWith(root)||Files.size(path)>2*1024*1024)throw new IOException("original window source path/size differs");
            assertEquals(pin[1],HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))),pin[0]);}
    }
}
