package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.activity.*;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts.Query;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.Build;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

/** Original eight query producers -> same native family -> public representation and typed error.
 * Software packets/guards below grant no qualified Root, source permission, read lease or Game. */
public final class RootMcpActivityReadsTest {
    @TempDir Path temporary;
    private static JsonNode originals;
    private static final String ORACLE="""
        import copy,importlib,json,os,runpy
        from pathlib import Path
        root=Path(os.environ['XAR_SOURCE_REPOSITORY'])
        source_pins={"ck3_autonomous_player/src/xar_autoplayer/bridge/activity_feast_guest_candidate_private_transport.py":"6ded1ff311c3103ce300b18c4dc98dfe42a9f21e14715bcac671a63397424b7a","ck3_autonomous_player/tests/unit/test_activity_feast_guest_candidate_private_transport.py":"543e799de9a071d5be601103ac8aabe0cc5bdf35b023acc1993452a8a63a225f","ck3_autonomous_player/src/xar_autoplayer/bridge/activity_feast_guest_opinion_private_transport.py":"2dc8219a916de5c5d3332ab945302f97ae2b4238238dabfc52382d08122806b7","ck3_autonomous_player/tests/unit/test_activity_feast_guest_opinion_private_transport.py":"d29cc993bd79f3724b900b9e2fae47817c0590083fbe430329fcebad3136c75e","ck3_autonomous_player/src/xar_autoplayer/bridge/activity_feast_guest_target_private_transport.py":"7cd49556a9b43ae8c80e5e62875f7d162ca2dee61bd8d32139057ca37454e19b","ck3_autonomous_player/tests/unit/test_activity_feast_guest_target_private_transport.py":"f6bb268a113306422007ec9b0741479cb3b98f606816f729b153a1551650e3b5","ck3_autonomous_player/src/xar_autoplayer/bridge/activity_feast_guest_route_proof_private_transport.py":"54f6014d7bcd51c57626fe03b61ea470f5eae98cbe17de8e30c97bde1f42ced4","ck3_autonomous_player/tests/unit/test_activity_feast_guest_route_proof_private_transport.py":"c0aa67f40c82eac38a6f47b417dab77c15ccc0c865cb5d37aebebed6b3bdc999","ck3_autonomous_player/src/xar_autoplayer/bridge/activity_feast_guest_rule_provenance_private_transport.py":"bce5656019b0bfec90ec38c88c83b9cb48885f63508274be95a8b24444c9b2df","ck3_autonomous_player/tests/unit/test_activity_feast_guest_rule_provenance_private_transport.py":"5a9076637c2f0e0bcc9b592c865d5454e73702642b95f205b85f24edb0b33c0d","ck3_autonomous_player/src/xar_autoplayer/bridge/activity_feast_stage5_start_private_transport.py":"656b02666880395c1bc1e0e3de4d9ff9d1a0d30e1393fc69e1d930aef43b8f3f","ck3_autonomous_player/tests/unit/test_activity_feast_stage5_start_private_transport.py":"c8b7816eb20d8503d9b53f5b3ffcf2fc2f1502c32af255e58f4fbdbb69d7ad39","ck3_autonomous_player/src/xar_autoplayer/bridge/activity_stage5_feast_full_cost_private_transport.py":"e8630a63c7ae5cc08f0413bf21e707a92b5eced42fd41a75fb0f686e99e8efe9","ck3_autonomous_player/tests/unit/test_activity_stage5_feast_full_cost_private_transport.py":"10232552d4fe37bec59047af269d1c5cc7dda180b6c3e71aef99f73f9df304e0"}
        import hashlib
        for relative,pin in source_pins.items():
            if hashlib.sha256((root/relative).read_bytes()).hexdigest()!=pin:raise RuntimeError('original Activity source/fixture drift: '+relative)
        specs=[('GUEST_CANDIDATE','activity_feast_guest_candidate',{}),('GUEST_OPINION','activity_feast_guest_opinion',{'guest_character_id':32000}),('GUEST_TARGET','activity_feast_guest_target',{'target_character_id':43699}),('GUEST_ROUTE_PROOF','activity_feast_guest_route_proof',{}),('GUEST_RULE_PROVENANCE','activity_feast_guest_rule_provenance',{'authored_rule_key':'activity_invite_rule_vassals','candidate_character_id':32000}),('START_INPUTS','activity_feast_stage5_start',{}),('HOSTED','activity_feast_stage5_start',{}),('FULL_COST','activity_stage5_feast_full_cost',{})]
        rows=[];maxu=2**64-1
        def terminal(actor,date):
            frame=dict(date_raw_i64=-(2**63),actor_character_id_i32=actor,owner_thread_id_u32=7,paused=True,map_ready=True,has_played_character=True,played_character_alive=True)
            record=dict(capture_sequence_u64=maxu,capture_thread_id_u32=7,source_cut_rva_u64=0x29BF68C,manager_identity_u64=maxu,activity_identity_u64=maxu,type_identity_u64=maxu,activity_full_id_u32=17,activity_instance_generation_u8=0,host_character_id_i32=actor,type_key='activity_feast',completed_observed=True,completed_raw_u8=1,invalidated_observed=True,invalidated_raw_u8=0,native_completion_stamp_observed=True,native_completion_stamp_raw_u64=maxu,capture_frame=frame)
            return dict(schema='activity_terminal_observations_12004_v1',available=True,unavailable_reason=None,observer_attached=True,process_lifetime=True,read_only=True,query_thread_id_u32=7,query_actor_full_id_u32=actor,record_capacity=64,earliest_retained_sequence_u64=maxu,latest_capture_sequence_u64=maxu,overflow_dropped_count_u64=0,record_count=1,records=[record])
        for query,name,args in specs:
            m=importlib.import_module('xar_autoplayer.bridge.'+name+'_private_transport')
            f=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit'/('test_'+name+'_private_transport.py')))
            if query=='GUEST_ROUTE_PROOF':
                case=f['GuestRouteProofTransportTests']();case.setUp();payload=copy.deepcopy(case.payload)
            elif query=='START_INPUTS':payload=f['inputs_payload']()
            elif query=='HOSTED':payload=f['common_payload'](m.POST_SCHEMA)
            else:payload=f['payload']()
            if query=='GUEST_CANDIDATE':payload['candidate']['planner_join_raw']=9007199254740993
            if query=='GUEST_TARGET':payload['planner_join_raw']=2**63-1
            if query=='GUEST_ROUTE_PROOF':payload['pre_invitation_candidate']['planner_join_raw']=2**63-1
            if query=='FULL_COST':payload['actor_gold_raw']=-(2**63);payload['resources']['gold']['configured_cost_raw']=2**63-1
            if query in ('START_INPUTS','HOSTED'):
                payload['balances']['gold']['raw']=2**63-1
                payload['hosted_activities'][0].update(native_completion_stamp_observed=True,native_completion_stamp_raw=maxu)
            if query=='HOSTED':payload['native_terminal_observations']=terminal(payload['actor_character_id'],payload['date_raw'])
            public_revision=2**32-1 if query=='GUEST_RULE_PROVENANCE' else maxu
            before=dict(snapshot_id='native:'+str(payload['snapshot_revision']),revision=public_revision,native_revision=payload['snapshot_revision'],date_raw=payload['date_raw'],paused=True,map_ready=True,played_character={'character_id':payload['actor_character_id'],'alive':True},episode_run_id='actual-original-activity-fixture',episode_character_id=payload['actor_character_id'],diagnostics={'hello':{'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':'98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518'}})
            step=m.INPUT_STEP if query=='START_INPUTS' else m.POST_STEP if query=='HOSTED' else m.STEP
            key={'START_INPUTS':'activity_feast_stage5_start_inputs','HOSTED':'activity_feast_hosted_post','FULL_COST':'activity_stage5_feast_full_cost'}.get(query,name)
            fn=getattr(m,'query_'+{'START_INPUTS':'activity_feast_stage5_start_inputs','HOSTED':'activity_feast_hosted_post','FULL_COST':'activity_stage5_feast_full_cost'}.get(query,name)+'_private_v1')
            class Driver:
                def __init__(self,red=False,payload_override=None):
                    self.sent=[];self.endpoint=self;self.state=self;self.red=red;self.payload=copy.deepcopy(payload if payload_override is None else payload_override)
                def __getattr__(self,name):
                    if name.startswith('allow_private_'):return True
                    raise AttributeError(name)
                def take_snapshot(self):return copy.deepcopy(before)
                def send(self,request):self.sent.append(copy.deepcopy(request))
                def wait_for_command_result(self,request_id,timeout):
                    self.returned=dict(type='command_result',protocol_version=1,request_id=request_id,ok=not self.red,error='actual_native_activity_red' if self.red else None,result=None if self.red else dict(step=step,accepted=True,status='available',private_build=True,read_only=True,advertised=False,backend_id='native-headless',**{key:copy.deepcopy(self.payload)}))
                    return copy.deepcopy(self.returned)
            driver=Driver();result=fn(driver,expected_revision=public_revision,**args)
            rows.append(dict(query=query,before=before,arguments=args,payload=payload,request=driver.sent[0],returned=driver.returned,result=result))
            red=Driver(True)
            try:fn(red,expected_revision=public_revision,**args);raise AssertionError('native RED accepted')
            except Exception as error:
                if type(error).__name__!='BridgeUnavailableError':raise
                rows[-1]['red']=dict(kind=type(error).__name__,message=str(error),returned=red.returned)
            stale=Driver()
            try:fn(stale,expected_revision=1,**args);raise AssertionError('stale Activity request accepted')
            except Exception as error:
                if type(error).__name__!='BridgeUnavailableError':raise
                rows[-1]['stale']=dict(kind=type(error).__name__,message=str(error),dispatch_count=len(stale.sent))
            malformed=[]
            for mode in ('missing_schema','null_schema','bool_native_revision','wrong_schema'):
                broken=copy.deepcopy(payload)
                if mode=='missing_schema':broken.pop('schema')
                elif mode=='null_schema':broken['schema']=None
                elif mode=='bool_native_revision':broken['snapshot_revision']=True
                else:broken['schema']='foreign-schema'
                bad=Driver(payload_override=broken)
                try:fn(bad,expected_revision=public_revision,**args);raise AssertionError('malformed Activity payload accepted')
                except Exception as error:
                    if type(error).__name__!='BridgeUnavailableError':raise
                    malformed.append(dict(case=mode,kind=type(error).__name__,message=str(error),returned=bad.returned))
            if query=='GUEST_CANDIDATE':
                for field in ('normal_refresh_sequence','candidate'):
                    broken=copy.deepcopy(payload);broken[field]=None;bad=Driver(payload_override=broken)
                    try:fn(bad,expected_revision=public_revision,**args);raise AssertionError('malformed candidate accepted')
                    except Exception as error:
                        if type(error).__name__!='BridgeUnavailableError':raise
                        malformed.append(dict(case=field,kind=type(error).__name__,message=str(error),returned=bad.returned))
            nested={
                'GUEST_CANDIDATE':[('candidate','planner_join_raw')],
                'GUEST_OPINION':[('guest_opinion_of_actor',)],
                'GUEST_TARGET':[('planner_join_raw',)],
                'GUEST_ROUTE_PROOF':[('pre_invitation_candidate','planner_join_raw')],
                'GUEST_RULE_PROVENANCE':[('candidate_membership',)],
                'START_INPUTS':[('resources','gold','configured_cost_raw'),('balances','gold','raw')],
                'HOSTED':[('balances','gold','raw'),('hosted_activities',0,'native_completion_stamp_raw')],
                'FULL_COST':[('resources','gold','configured_cost_raw'),('final_can_start_failure_display','state')],
            }
            for path in nested[query]:
                broken=copy.deepcopy(payload);target=broken
                for part in path[:-1]:target=target[part]
                target[path[-1]]=None;bad=Driver(payload_override=broken)
                try:fn(bad,expected_revision=public_revision,**args);raise AssertionError('malformed nested Activity payload accepted')
                except Exception as error:
                    if type(error).__name__!='BridgeUnavailableError':raise
                    malformed.append(dict(case='.'.join(map(str,path)),kind=type(error).__name__,message=str(error),returned=bad.returned))
            rows[-1]['malformed']=malformed
        print(json.dumps(rows,ensure_ascii=True,separators=(',',':')))
        """;
    public static synchronized JsonNode originalCases()throws Exception {
        if(originals!=null)return originals.deepCopy();String interpreter=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");
        assertNotNull(interpreter,"required xar.python missing; do not skip original Activity producers");assertNotNull(repository,"required xar.repository.root missing");assertTrue(Path.of(interpreter).isAbsolute());Path root=Path.of(repository).toRealPath();
        var builder=new ProcessBuilder(interpreter,"-B","-c",ORACLE).directory(root.toFile()).redirectErrorStream(true);
        builder.environment().put("XAR_SOURCE_REPOSITORY",root.toString());builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src").toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        var child=builder.start();var captured=new FutureTask<byte[]>(()->child.getInputStream().readNBytes(1_048_577));Thread reader=Thread.ofVirtual().start(captured);
        try {assertTrue(child.waitFor(45,TimeUnit.SECONDS),"original eight Activity producers timed out");byte[] bytes=captured.get(5,TimeUnit.SECONDS);assertTrue(bytes.length<=1_048_576);assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));originals=StrictJson.parse(bytes);assertEquals(8,originals.size());return originals.deepCopy();}
        finally {if(child.isAlive())child.destroyForcibly();reader.interrupt();}
    }
    public static ActivityNativeContracts.Packet actualPacket(JsonNode original,Path directory)throws Exception {
        Files.createDirectories(directory);Query query=Query.valueOf(original.path("query").textValue());JsonNode before=original.get("before");
        ExactRef source=preserve(directory.resolve("original-producer.txt"),new byte[]{'s','o','f','t','w','a','r','e'});
        var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",123).put("connection_generation",1).put("bridge_version","actual-original-activity-fixture")
                .put("expected_ck3_sha256",Build.CROZIER4.sha256()).put("game_adapter_id","ck3-"+Build.CROZIER4.version()+"-msvc-x64").put("game_adapter_status","ready").put("ck3_build_match",true);hello.putArray("capabilities");
        ExactRef helloRef=preserve(directory.resolve("original-hello.bin"),NativeWire.packet(StrictJson.canonical(hello)));
        var identity=new ObservationIdentity("synthetic-activity-machine",new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(before.path("played_character").path("character_id").bigIntegerValue(),before.path("native_revision").bigIntegerValue(),before.path("date_raw").bigIntegerValue()),before.path("snapshot_id").textValue(),before.path("revision").bigIntegerValue(),before.path("episode_run_id").textValue()),1);
        Instant now=Instant.parse("2026-10-24T00:00:00Z");var provenance=new G2Source(identity.machineId(),now.toString(),Build.CROZIER4.version(),source);
        var installed=new ActivityNativeContracts.Installation(Arrays.stream(Query.values()).map(value->new ActivityNativeContracts.Source(value,source)).toList(),(value,request)->assertEquals(query,value));
        var contract=installed.contract(query);var request=new PlanningReadRequest(identity,provenance,"actual-original-activity-session",contract.operation(),object(original.get("arguments")),now.plusSeconds(30));
        String id=original.path("request").path("request_id").textValue();NativeRequest nativeRequest=contract.prepare(request,id);
        ObjectNode sent=(ObjectNode)original.get("request").deepCopy();for(String key:List.of("type","protocol_version","request_id","step","expected_revision"))sent.remove(key);
        assertEquals(object(sent),OpportunityJson.parse(nativeRequest.additionalFields().bytes()),"actual original query fields -> same Java preparer");
        var guard=new PlanningReadGuard(new GuardEvidence(identity,provenance,request.sessionId(),BigInteger.ONE,contract.operation(),source,helloRef,"software-activity-original-boundary",now,request.deadline()),true,true,true,"b".repeat(64));
        var returned=(ObjectNode)original.get("returned");var result=raw(returned.get("result"));
        byte[] outbound=NativeWire.execute(id,nativeRequest.step(),identity.frame().identity().nativeRevision(),nativeRequest.additionalFields().bytes());
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(result),raw(returned),NativeWire.packet(StrictJson.canonical(returned)),Optional.of(new NativeActionPort.OutboundPacket(id,outbound)));
        return contract.decode(new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack));
    }
    private static ExactRef preserve(Path path,byte[] bytes)throws Exception {Files.write(path,bytes);var actual=SharedSourceFiles.observe(path).source();return new ExactRef(actual.path(),actual.bytes(),actual.sha256());}
    private static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value));}
    private static OpportunityJson.Obj object(JsonNode value){return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"actual original Activity data");}
    private static PublicMcpDirectory.Arguments arguments(RawJson raw){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(raw));}

    @Test void actualEightOriginalProducersFullResultsRoundTripPublicWideValuesWithoutChangingNativeOriginals()throws Exception {
        for(JsonNode row:originalCases()) {
            Query query=Query.valueOf(row.path("query").textValue());var packet=actualPacket(row,temporary.resolve(query.name()));
            byte[] payload=ActivityReadCodec.encode(packet.payload());RawJson normalized=ActivityNativeContracts.normalizedNumeric(packet),published=ActivityNativeContracts.normalizedForPublic(packet);
            assertEquals(object(row.get("result")),OpportunityJson.parse(normalized.bytes()));
            assertEquals(OpportunityJson.parse(normalized.bytes()),OpportunityJson.parse(ActivityPublic64.decode(query,published).bytes()));
            assertArrayEquals(payload,ActivityReadCodec.encode(packet.payload()),"public projection must not mutate original native/archive data");
            RawJson publicPayload=ActivityPublic64.encode(query,new RawJson(payload));var frame=packet.receipt().request().before().frame().identity();
            assertEquals(packet.payload(),ActivityReadCodec.decodePublicPayload(query,publicPayload.bytes(),new org.xar.ck3.control.governance.activity.ActivityConfigurationModels.Frame(frame.nativeRevision(),frame.dateRaw(),frame.player()),packet.receipt().request().arguments(),"available",null));
            var decoded=StrictJson.parse(published.bytes());assertEquals(row.path("before").path("revision").bigIntegerValue().toString(),decoded.path("queried_revision").textValue());assertTrue(decoded.path("actor_character_id").isIntegralNumber());
            if(query==Query.GUEST_CANDIDATE)assertEquals("9007199254740993",decoded.path("candidate").path("planner_join_raw").textValue());
            if(query==Query.HOSTED){assertEquals("18446744073709551615",decoded.path("native_terminal_observations").path("records").get(0).path("activity_identity_u64").textValue());assertEquals("-9223372036854775808",decoded.path("native_terminal_observations").path("records").get(0).path("capture_frame").path("date_raw_i64").textValue());}
        }
    }
    @Test void originalExactNativeRedBecomesTypedBridgeDiagnosticAndUnavailableDoesNotProduceSuccessOrResend()throws Exception {
        for(JsonNode row:originalCases()) {
            Query query=Query.valueOf(row.path("query").textValue());var packet=actualPacket(row,temporary.resolve(query.name()));
            var returned=(ObjectNode)row.path("red").path("returned");String id=returned.path("request_id").textValue();
            var ack=new NativeActionPort.AckReceived(id,false,Optional.empty(),raw(returned),NativeWire.packet(StrictJson.canonical(returned)));
            var unavailable=new PlanningReadResult.Unavailable<ActivityNativeContracts.Packet>("actual retained native RED",Optional.of(ack));
            var failure=assertThrows(PublicServiceFailure.class,()->RootMcpActivityReads.present(query,unavailable));
            assertEquals(row.path("red").path("kind").textValue(),failure.kind().pythonClassName());assertEquals(row.path("red").path("message").textValue(),failure.getMessage());
            var retained=assertInstanceOf(RootMcpActivityReads.ActualReadFailure.class,failure.getCause());assertSame(ack,retained.evidence().original().orElseThrow());assertEquals(query,retained.evidence().query());assertEquals(RootMcpActivityReads.FailureStage.NATIVE_RED,retained.evidence().stage());
            var missing=assertThrows(PublicServiceFailure.class,()->RootMcpActivityReads.present(query,new PlanningReadResult.Unavailable<>("actual native result unavailable",Optional.empty())));
            assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,missing.kind());assertTrue(missing.getMessage().contains("actual native result unavailable"));
            assertNotNull(RootMcpActivityReads.present(query,new PlanningReadResult.Known<>(packet,packet.receipt(),packet.receipt().before().binding().nativeEvidence())));
        }
    }
    @Test void callerPublicRevisionAndDeclaredWidePathsRejectTypeRangePresenceAndForeignFields()throws Exception {
        for(JsonNode row:originalCases()) {
            Query query=Query.valueOf(row.path("query").textValue());var packet=actualPacket(row,temporary.resolve(query.name()));
            var request=new RootMcpActivityReads.Request(query,packet.receipt().request().before().frame().revision(),packet.receipt().request().arguments());
            var wire=RootMcpActivityReads.encodeRequest(request);assertEquals(request,RootMcpActivityReads.decode(query,arguments(wire)));
            RootMcpActivityReads.validateCurrent(request,request.expectedRevision(),packet.receipt().request().before().frame().identity().player());
            var staleRequest=new RootMcpActivityReads.Request(query,BigInteger.ONE,request.arguments());
            var stale=assertThrows(PublicServiceFailure.class,()->RootMcpActivityReads.validateCurrent(staleRequest,request.expectedRevision(),packet.receipt().request().before().frame().identity().player()));
            assertEquals(row.path("stale").path("kind").textValue(),stale.kind().pythonClassName());assertEquals(row.path("stale").path("message").textValue(),stale.getMessage());assertEquals(0,row.path("stale").path("dispatch_count").intValue());
            for(String bad:List.of("0","01","+1","-1","18446744073709551616")) {ObjectNode invalid=(ObjectNode)StrictJson.parse(wire.bytes());invalid.put("expected_revision",bad);assertThrows(PublicServiceFailure.class,()->RootMcpActivityReads.decode(query,arguments(raw(invalid))));}
            ObjectNode missing=(ObjectNode)StrictJson.parse(wire.bytes());missing.remove("expected_revision");assertThrows(IllegalArgumentException.class,()->RootMcpActivityReads.decode(query,arguments(raw(missing))));
            ObjectNode unsafe=(ObjectNode)StrictJson.parse(ActivityNativeContracts.normalizedForPublic(packet).bytes());unsafe.put("undeclared_raw",new BigInteger("9007199254740993"));assertThrows(IllegalArgumentException.class,()->ActivityPublic64.decode(query,raw(unsafe)));
            ObjectNode changed=(ObjectNode)StrictJson.parse(ActivityNativeContracts.normalizedForPublic(packet).bytes());changed.put("snapshot_revision",true);assertThrows(IllegalArgumentException.class,()->ActivityPublic64.decode(query,raw(changed)));
        }
    }
}
