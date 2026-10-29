package org.xar.ck3.control.nativebridge.capabilities.religion;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionModels.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Executes pinned original Python producer bodies offline; no game, JVM test result or qualification is claimed by the source. */
final class ReligionOriginalProducerTest {
    @TempDir Path temporary;
    private int sequence;
    private JsonNode sourceMap;
    private final Capture capture=new Capture();
    private static final String ORIGINAL="""
        import ast,base64,copy,hashlib,json,sys,types,uuid
        from pathlib import Path
        p=Path(sys.argv[1]); original=p.read_bytes()
        if hashlib.sha256(original).hexdigest()!=sys.argv[2]: raise RuntimeError('pinned original producer drift')
        mode=sys.argv[3]; arg=json.loads(base64.b64decode(sys.argv[4])); tree=ast.parse(original.decode('utf-8-sig'))
        def find(name):
            return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
        def load(name,scope):
            node=copy.deepcopy(find(name))
            class Imports(ast.NodeTransformer):
                def visit_ImportFrom(self,node): return None
            node=Imports().visit(node)
            future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[future,node],type_ignores=[])),str(p),'exec'),scope)
            return scope[name]
        b3=types.SimpleNamespace(game_version='1.20.0.3',executable_sha256='94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6')
        b4=types.SimpleNamespace(game_version='1.20.0.4',executable_sha256='98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518')
        before={'revision':5,'native_revision':7,'date_raw':1,'paused':True,'map_ready':True,'snapshot_id':'original-fixture',
          'played_character':{'character_id':29829,'alive':True},'diagnostics':{'connection_generation':11,'bridge_pid':42}}
        sent=[]
        def primitive(step,**kw):
            packet={'type':'execute_step','protocol_version':1,'request_id':kw.get('protocol_request_id','fixture'),
                'step':step,'expected_revision':7,**kw['request_fields']}
            sent.append(packet); return {}
        def wait(request_id,timeout):
            step=sent[-1]['step']; result={'step':step,'accepted':True,'private_build':True,'read_only':True,
              'advertised':False,'backend_id':'native-headless','game_version':b3.game_version,'executable_sha256':b3.executable_sha256,
              'snapshot_revision':7,'public_revision':5,'date_raw':1,'capture_epoch':9}
            if mode=='conversion': result['read_only']=step==arg['result_step']
            if mode=='epidemic':
                result={k:result[k] for k in ('step','accepted','private_build','read_only','advertised','backend_id','snapshot_revision')}
                title=arg.get('title',0)
                result.update(status='available',query_sequence=1,observation_revision=1,player_epidemic_recovery={
                  'schema':'player-epidemic-recovery-v1','schema_version':1,'snapshot_revision':7,'date_raw':1,'played_character_id':29829,
                  'list_key':'formerly_infected_counties','requested_title_id':title,'status':'available',
                  'counties':[] if title==0 else [{'landed_title_id':title,'minor_present':False,'tiny_present':True}],
                  'remaining_days':{'status':'unavailable','value':None,'unavailable_reason':'duration_abi_not_verified'},'unavailable_reason':None})
            if mode=='ghw': result.update(game_version=b4.game_version,executable_sha256=b4.executable_sha256,domain_key='player_ghw_permissions',status='observed',player_ghw_permissions={'available':True})
            return {'type':'command_result','protocol_version':1,'request_id':request_id,'ok':True,'result':result}
        driver=types.SimpleNamespace(endpoint=types.SimpleNamespace(send=lambda packet:sent.append(packet)),state=types.SimpleNamespace(wait_for_command_result=wait),
          take_snapshot=lambda:copy.deepcopy(before),take_snapshot_without_native_command_history=lambda:copy.deepcopy(before),
          _execute_primitive_step=primitive,_record_command=lambda *a,**kw:None)
        scope={'__name__':'original_request_fixture','copy':copy,'Mapping':__import__('collections.abc',fromlist=['Mapping']).Mapping,
          'uuid':types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='fixture')),
          'BridgeUnavailableError':RuntimeError,'PreSubmissionRevisionMismatchError':RuntimeError,'UnsupportedStepError':RuntimeError,
          'private_native_provenance':lambda x:{},'private_g2_query_metadata_v1':lambda x:{},
          'private_native_build_identity':lambda x:b3,'_binding':lambda x:(x['revision'],x['native_revision'],x['date_raw']),
          'NAVIGATE_STEP':'navigate-ingame-ui-v1','NAVIGATE_CAPABILITY':'game.command.navigate-ingame-ui-v1',
          'QUERY_STEP':'query-ingame-ui-window-v1','QUERY_CAPABILITY':'game.command.query-ingame-ui-window-v1'}
        if mode=='g2':
            driver.permission=True; scope['private_g2_query_snapshot_v1']=lambda d,**kw:d.take_snapshot()
            load('read_private_g2_native_query_v1',scope)(driver,permission='permission',step=arg['step'],expected_revision=5,request_fields=arg['fields'])
        elif mode=='confucian':
            scope['OPERATIONS']={arg['operation']:(arg['step'],)};scope['integer']=lambda value,lo,hi,name:value
            scope['validate_faith_ids']=lambda value:value
            sent.append(load('encode_query_request',scope)(arg['operation'],{'native_revision':7},'fixture',arg.get('faith_full_ids')))
        elif mode=='conversion':
            scope['RESULT_STEP']=arg['result_step'];load('_integer',scope)
            load('_send',scope)(driver,before,step=arg['step'],fields=arg['fields'],timeout_seconds=1)
        elif mode=='ui':
            scope.update(validate_ui_request=lambda *a,**kw:None,validate_ui_build_scope=lambda *a,**kw:None,
              ingame_ui_build_binding=lambda snapshot:(b4,True),_title_camera_navigation_binding_from_snapshot=lambda snapshot:{'connection_generation':11},
              _same_paused_native_frame=lambda a,b:True,presentation_fields=lambda *a,**kw:{},is_presentation=lambda *a,**kw:False,
              normalize_ui_result=lambda raw,**kw:raw)
            driver.allow_private_player_holy_site_creation_ui=True
            load('_ingame_ui_v1',scope)(driver,arg['operation'],arg['kind'],arg['subject_id'],expected_revision=5,
              holy_site_action=arg.get('action'),holy_site_creation_type_key=arg.get('type_key'))
        elif mode=='create':
            node=find('create_holy_site_once_private_v1')
            call=next(n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_execute_primitive_step')
            scope.update(driver=driver,expected_revision=5,request_id='fixture',OPERATION='create_holy_site_once',KIND='holy_site_creation',preview=arg['preview'],before=before)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.Expr(value=copy.deepcopy(call))],type_ignores=[])),str(p),'exec'),scope)
        elif mode=='stress':
            scope.update(validate_base_amount=lambda n:n,stress_query_binding=lambda a,b:{'played_character_id':29829,'game_pid':42,'connection_generation':11},
              same_stress_query_frame=lambda *a:True,project_stress_query=lambda raw,*a:raw,
              CURRENT_ACTOR_STRESS_ADJUSTMENT_V1_STEP='query-current-actor-stress-adjustment-v1',CURRENT_ACTOR_STRESS_ADJUSTMENT_V1_CAPABILITY='game.query.current-actor-stress-adjustment.v1')
            load('query_current_actor_stress_adjustment_v1',scope)(driver,arg['base_amount'],expected_revision=5)
        elif mode=='epidemic':
            before['active_event']={'instance_id':99};driver.allow_private_epidemic_recovery_query=True
            scope.update(STEP='query-player-epidemic-recovery-v1',TITLE_STEP_PREFIX='query-player-epidemic-recovery-v1-title-',LIST_KEY='formerly_infected_counties',DURATION={'status':'unavailable','value':None,'unavailable_reason':'duration_abi_not_verified'})
            load('query_player_epidemic_recovery_private_v1',scope)(driver,expected_revision=5,requested_title_id=arg.get('title',0),expected_event_instance_id=None if arg.get('title',0)>0 else 99)
        elif mode=='ghw':
            import math
            scope.update(math=math,private_g2_query_snapshot_v1=lambda d,**kw:d.take_snapshot(),owner=lambda s:(7,42,11,b4),
              require_exact_native_backend=lambda *a,**kw:b4,CK3_12004=b4,normalize_player_ghw_permissions_v1=lambda value,**kw:value)
            load('need',scope);load('integer',scope);load('reference',scope)
            driver.allow_private_player_ghw_permissions_query=True
            load('_query',scope)(driver,permission='allow_private_player_ghw_permissions_query',step='query-player-ghw-permissions-v1-private',domain='player_ghw_permissions',result_key='player_ghw_permissions',suffix='player-ghw-permissions-v1-private',expected_revision=5)
        else: raise RuntimeError('unknown fixture mode')
        if len(sent)!=1: raise RuntimeError('original producer did not make exactly one request')
        sys.stdout.write(json.dumps(sent[0],separators=(',',':')))
        """;
    @Test void allTwentyThreePublicMethodsUsePinnedOriginalRequestProducers() throws Exception {
        var registry=registration();var facade=new ReligionCapabilities(capture,capture,registry);Context four=context(Build.CROZIER4),three=context(Build.CROZIER3);FullId site=new FullId(4294967294L);
        checkRead(()->facade.query_player_holy_site_creation_context_v1(four),"g2",readSource(ReligionCapabilities.ReadKind.CREATION),ReligionCapabilities.empty().put("step",ReligionCapabilities.ReadKind.CREATION.step()).set("fields",ReligionCapabilities.empty()));
        checkRead(()->facade.query_player_ghw_permissions_v1(four),"ghw",readSource(ReligionCapabilities.ReadKind.GHW),ReligionCapabilities.empty());
        checkRead(()->facade.query_player_holy_site_decision_detail_v1(four,Decision.PROMOTE,site),"g2",readSource(ReligionCapabilities.ReadKind.DETAIL),g2(ReligionCapabilities.ReadKind.DETAIL,ReligionCapabilities.empty().put("action","promote").put("holy_site_id",site.value())));
        checkRead(()->facade.query_player_holy_site_decision_cooldown_v1(four,Decision.DEMOTE),"g2",readSource(ReligionCapabilities.ReadKind.COOLDOWN),g2(ReligionCapabilities.ReadKind.COOLDOWN,ReligionCapabilities.empty().put("action","demote")));
        checkRead(()->facade.query_player_seek_indulgences_terms_v1(three,site),"g2",readSource(ReligionCapabilities.ReadKind.INDULGENCES),g2(ReligionCapabilities.ReadKind.INDULGENCES,ReligionCapabilities.empty().put("recipient_character_id",site.value())));
        OwnerId owner=new OwnerId("owner-fixture"),request=new OwnerId("retained-fixture");
        checkAction(()->facade.submit_player_religion_conversion_private_v1(action(three),site,new BigInteger("9223372036854775807"),owner),registry,"conversion",actionSource(ReligionCapabilities.MutationSource.RELIGION_CONVERSION),conversion("submit-player-religion-conversion-private-v1","query-player-religion-conversion-result-private-v1",ReligionCapabilities.empty().put("target_rite_id",site.value()).put("max_piety_cost_raw",new BigInteger("9223372036854775807")).put("action_id",owner.value())));
        checkRead(()->facade.query_player_religion_conversion_result_private_v1(three,request,owner),"conversion",readSource(ReligionCapabilities.ReadKind.RELIGION_RESULT),conversion(ReligionCapabilities.ReadKind.RELIGION_RESULT.step(),ReligionCapabilities.ReadKind.RELIGION_RESULT.step(),ReligionCapabilities.empty().put("submitted_request_id",request.value()).put("action_id",owner.value())));
        checkAction(()->facade.submit_county_conversion_task_private_v1(action(four),new PositiveId(41),new PositiveId(42),new PositiveId(43),true,owner),registry,"conversion",actionSource(ReligionCapabilities.MutationSource.COUNTY_TASK),conversion("county-conversion-task-submit-private-v1","county-conversion-task-result-private-v1",ReligionCapabilities.empty().put("expected_active_task_id",41).put("expected_incumbent_character_id",42).put("province_id",43).put("replace_existing_task",true).put("action_id",owner.value())));
        checkRead(()->facade.query_county_conversion_task_result_private_v1(four,request,owner),"conversion",readSource(ReligionCapabilities.ReadKind.COUNTY_RESULT),conversion(ReligionCapabilities.ReadKind.COUNTY_RESULT.step(),ReligionCapabilities.ReadKind.COUNTY_RESULT.step(),ReligionCapabilities.empty().put("submitted_request_id",request.value()).put("action_id",owner.value())));
        checkAction(()->facade.create_holy_site_once_v1(action(four),new PreviewIdentity("a".repeat(64))),registry,"create",actionSource(ReligionCapabilities.MutationSource.CREATION),ReligionCapabilities.empty().put("preview","a".repeat(64)));
        checkAction(()->facade.open_holy_site_creation_window_v1(action(four)),registry,"ui",actionSource(ReligionCapabilities.MutationSource.UI),ui("open_holy_site_creation","holy_site_creation",0));
        checkAction(()->facade.select_holy_site_creation_type_v1(action(four),"sacred_land"),registry,"ui",actionSource(ReligionCapabilities.MutationSource.UI),ui("select_holy_site_creation_type","holy_site_creation",0).put("type_key","sacred_land"));
        checkAction(()->facade.select_holy_site_creation_barony_v1(action(four),site),registry,"ui",actionSource(ReligionCapabilities.MutationSource.UI),ui("select_holy_site_creation_barony","holy_site_creation",4294967294L));
        checkAction(()->facade.open_holy_site_window_v1(action(four),site),registry,"ui",actionSource(ReligionCapabilities.MutationSource.UI),ui("open_holy_site","holy_site",4294967294L));
        checkAction(()->facade.open_holy_site_adoption_decision_v1(action(four),site),registry,"ui",actionSource(ReligionCapabilities.MutationSource.UI),ui("open_holy_site_adoption","holy_site",4294967294L));
        checkAction(()->facade.confirm_holy_site_adoption_decision_v1(action(four),site),registry,"ui",actionSource(ReligionCapabilities.MutationSource.UI),ui("confirm_site_adoption","holy_site_adoption",4294967294L));
        checkAction(()->facade.open_holy_site_decision_v1(action(four),Decision.ABANDON,site),registry,"ui",actionSource(ReligionCapabilities.MutationSource.UI),ui("open_holy_site_adoption","holy_site",4294967294L).put("action","abandon"));
        checkAction(()->facade.confirm_holy_site_decision_v1(action(four),Decision.PROMOTE,site),registry,"ui",actionSource(ReligionCapabilities.MutationSource.UI),ui("confirm_site_adoption","holy_site_adoption",4294967294L).put("action","promote"));
        checkRead(()->facade.query_confucian_assembly_predicates_v1(four),"confucian",readSource(ReligionCapabilities.ReadKind.ASSEMBLY),confucian("assembly_predicates",ReligionCapabilities.ReadKind.ASSEMBLY));
        ObjectNode graph=confucian("challenger_graph",ReligionCapabilities.ReadKind.CHALLENGERS);graph.putArray("faith_full_ids").add(site.value());checkRead(()->facade.query_confucian_challenger_graph_v1(four,List.of(site)),"confucian",readSource(ReligionCapabilities.ReadKind.CHALLENGERS),graph);
        checkRead(()->facade.query_confucian_religious_title_v1(four),"confucian",readSource(ReligionCapabilities.ReadKind.TITLE),confucian("religious_title",ReligionCapabilities.ReadKind.TITLE));
        checkRead(()->facade.query_current_actor_stress_adjustment_v1(three,-300),"stress",ref("nativeDriverFrozen"),ReligionCapabilities.empty().put("base_amount",-300));
        checkRead(()->facade.query_player_epidemic_recovery_private_v1(four,new EventCounties(BigInteger.valueOf(99))),"epidemic",readSource(ReligionCapabilities.ReadKind.EPIDEMIC),ReligionCapabilities.empty());
        checkRead(()->facade.query_player_epidemic_recovery_private_v1(four,new ExplicitTitle(new PositiveId(43))),"epidemic",readSource(ReligionCapabilities.ReadKind.EPIDEMIC),ReligionCapabilities.empty().put("title",43));
        assertEquals(24,capture.calls); // Both original epidemic selectors exercise one public method.
    }
    @Test void strictBoundaryRejectsWrongFieldTypesUnknownActionsAndUnregisteredTitle() throws Exception {
        var registry=registration();var facade=new ReligionCapabilities(capture,capture,registry);Context c=context(Build.CROZIER4);
        assertThrows(IllegalArgumentException.class,()->new FullId(-1));assertThrows(IllegalArgumentException.class,()->new PositiveId(0));assertThrows(IllegalArgumentException.class,()->Decision.parse("elevate"));assertThrows(IllegalArgumentException.class,()->new PreviewIdentity("A".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->facade.query_player_epidemic_recovery_private_v1(c,new ExplicitTitle(new PositiveId(44))));assertEquals(0,capture.calls);
        assertThrows(IllegalArgumentException.class,()->facade.select_holy_site_creation_type_v1(action(c),"bad\0type"));
        ReadContract<?> detail=registry.readContracts().stream().filter(v->v.operation().value().equals(ReligionCapabilities.ReadKind.DETAIL.step())).findFirst().orElseThrow();
        for(String json:List.of("{\"action\":\"adopt\",\"holy_site_id\":true}","{\"action\":\"adopt\",\"holy_site_id\":1.0}","{\"action\":\"adopt\"}","{\"action\":\"adopt\",\"holy_site_id\":1,\"alias\":1}")){
            var args=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(json.getBytes(StandardCharsets.UTF_8)),"fixture");assertThrows(IllegalArgumentException.class,()->detail.prepare(new PlanningReadRequest(c.before(),c.source(),c.sessionId(),detail.operation(),args,c.deadline()),"fixture"));
        }
        assertThrows(IllegalArgumentException.class,()->new RawJson("{\"action\":1,\"action\":1}".getBytes(StandardCharsets.UTF_8)));
        assertEquals(2,registry.privateActions((a,b,d,q)->{throw new IOException("software test has no actual private qualification");},(a,b,d,q)->{throw new IOException("software test has no actual private qualification");}).size());
    }
    private void checkRead(Runnable call,String mode,ExactRef source,ObjectNode inputs)throws Exception{capture.reset();assertThrows(Captured.class,call::run);NativeRequest prepared=capture.contract.prepare(capture.read,"fixture");compare(prepared,capture.contract.wireProfile(),mode,source,inputs);}
    private void checkAction(Runnable call,ReligionCapabilities.Registration registry,String mode,ExactRef source,ObjectNode inputs)throws Exception{capture.reset();assertThrows(Captured.class,call::run);NativeRequest prepared=registry.prepare(capture.action);compare(prepared,ReadContract.WireProfile.EXECUTE_STEP,mode,source,inputs);}
    private void compare(NativeRequest request,ReadContract.WireProfile profile,String mode,ExactRef source,ObjectNode inputs)throws Exception{JsonNode original=producer(mode,source,inputs);String id=original.get("request_id").textValue();byte[] packet=switch(profile){case EXECUTE_STEP->NativeWire.execute(id,request.step(),BigInteger.valueOf(7),request.additionalFields().bytes());case G2_PRIVATE_QUERY->NativeWire.executePrivateQuery(id,request.step(),BigInteger.valueOf(7),request.additionalFields().bytes());case SNAPSHOT_REVISION_ONLY->NativeWire.executeSnapshotRevisionOnly(id,request.step(),BigInteger.valueOf(7),request.additionalFields().bytes());case COUNCIL_MAILBOX_STATUS->throw new AssertionError("council mailbox status is outside religion producer fixture");};assertEquals(original,NativeWire.parse(java.util.Arrays.copyOfRange(packet,4,packet.length)),"actual original "+mode+" request differs");assertEquals(request.additionalFields(),new RawJson(request.additionalFields().bytes()));}
    private JsonNode producer(String mode,ExactRef source,ObjectNode input)throws Exception{if(mode.equals("g2"))source=ref("g2PrivateFrozen");if(mode.equals("confucian"))source=ref("confucianProducerFrozen");Path out=temporary.resolve("original-"+(++sequence)+".json"),err=temporary.resolve("original-"+sequence+".stderr");Process p=new ProcessBuilder(required("xar.python"),"-X","utf8","-c",ORIGINAL,source.path(),source.sha256(),mode,Base64.getEncoder().encodeToString(ReligionCapabilities.raw(input).bytes())).redirectOutput(out.toFile()).redirectError(err.toFile()).start();if(!p.waitFor(20,TimeUnit.SECONDS)){p.destroyForcibly();throw new IOException("original producer timeout");}if(p.exitValue()!=0)throw new IOException("original producer RED: "+Files.readString(err));return NativeWire.parse(Files.readAllBytes(out));}
    private ObjectNode g2(ReligionCapabilities.ReadKind kind,ObjectNode fields){return ReligionCapabilities.empty().put("step",kind.step()).set("fields",fields);}
    private ObjectNode conversion(String step,String result,ObjectNode fields){return ReligionCapabilities.empty().put("step",step).put("result_step",result).set("fields",fields);}
    private ObjectNode ui(String operation,String kind,long subject){return ReligionCapabilities.empty().put("operation",operation).put("kind",kind).put("subject_id",subject);}
    private ObjectNode confucian(String operation,ReligionCapabilities.ReadKind kind){return ReligionCapabilities.empty().put("operation",operation).put("step",kind.step());}
    private ReligionCapabilities.Registration registration()throws Exception{List<ReligionCapabilities.ReadSource> reads=new ArrayList<>();for(var k:ReligionCapabilities.ReadKind.values())reads.add(new ReligionCapabilities.ReadSource(k,readSource(k)));List<ReligionCapabilities.ActionSource> actions=new ArrayList<>();for(var k:ReligionCapabilities.MutationSource.values())actions.add(new ReligionCapabilities.ActionSource(k,actionSource(k)));return new ReligionCapabilities.Registration(reads,actions,List.of(new PositiveId(43)),(k,r)->{},(k,c)->{});}
    private ExactRef readSource(ReligionCapabilities.ReadKind kind)throws Exception{return ref("readSources",kind.name());}
    private ExactRef actionSource(ReligionCapabilities.MutationSource kind)throws Exception{return ref("actionSources",kind.name());}
    private ExactRef ref(String... keys) throws Exception {
        if (sourceMap == null) {
            byte[] bound = Files.readAllBytes(Path.of(required("xar.religionContext.sourceMap")));
            sourceMap = readBaseMap(bound, required("xar.religionContext.sourceMapSha256"));
        }
        JsonNode n = sourceMap;
        for (String key : keys) n = n.get(key);
        return new ExactRef(n.get("path").textValue(), n.get("bytes").longValue(), n.get("sha256").textValue());
    }
    /** The existing Context typed role binds the unchanged base map; no parallel role or property fallback. */
    private static JsonNode readBaseMap(byte[] bound, String boundSha256) throws Exception {
        if (!sha256(bound).equals(boundSha256)) throw new IOException("bound religion Context source map SHA drift");
        JsonNode context = NativeWire.parse(bound);
        if (!context.isObject() ||
                !"xar.java-phase1.religion-context-source-map/v1".equals(context.path("schema").textValue())) {
            throw new IllegalArgumentException("religion Context map schema required");
        }
        JsonNode nested = context.get("religion_base_source_map_ref");
        if (nested == null || !nested.isObject() || nested.size() != 3 ||
                !nested.has("path") || !nested.has("bytes") || !nested.has("sha256") ||
                !nested.get("path").isTextual() || nested.get("path").textValue().isBlank() ||
                !nested.get("bytes").isIntegralNumber() || !nested.get("bytes").canConvertToLong() ||
                nested.get("bytes").longValue() < 0 || !nested.get("sha256").isTextual() ||
                !nested.get("sha256").textValue().matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("exact religion base source map ref required");
        }
        ExactRef ref = new ExactRef(nested.get("path").textValue(),
                nested.get("bytes").longValue(), nested.get("sha256").textValue());
        byte[] bytes = Files.readAllBytes(Path.of(ref.path()));
        if (bytes.length != ref.bytes() || !sha256(bytes).equals(ref.sha256())) {
            throw new IOException("actual religion base source map bytes or SHA drift");
        }
        JsonNode base = NativeWire.parse(bytes);
        if (!base.isObject() || !"xar.ck3.religion-java-source-map.v1".equals(base.path("schema").textValue())) {
            throw new IllegalArgumentException("original religion base map schema required");
        }
        if (!context.path("machine_id").isTextual() ||
                !context.path("machine_id").equals(base.path("machine_id"))) {
            throw new IllegalArgumentException("religion base map machine identity mismatch");
        }
        return base;
    }
    private static String sha256(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    @Test void baseProducerMapUsesTheBoundContextRoleAndExactNestedOriginal() throws Exception {
        byte[] bound = Files.readAllBytes(Path.of(required("xar.religionContext.sourceMap")));
        String boundSha = required("xar.religionContext.sourceMapSha256");
        JsonNode base = readBaseMap(bound, boundSha);
        assertEquals("xar.ck3.religion-java-source-map.v1", base.path("schema").textValue());
        assertEquals(8, base.path("javaFiles").size());
        assertThrows(IOException.class, () -> readBaseMap(bound, "0".repeat(64)));
        ObjectNode original = (ObjectNode) NativeWire.parse(bound);
        List<Consumer<ObjectNode>> malformed = List.of(
                value -> value.remove("religion_base_source_map_ref"),
                value -> value.putNull("religion_base_source_map_ref"),
                value -> value.put("schema", "wrong"),
                value -> value.put("machine_id", "wrong"),
                value -> ((ObjectNode) value.get("religion_base_source_map_ref")).put("alias", 1),
                value -> ((ObjectNode) value.get("religion_base_source_map_ref")).put("path", ""),
                value -> ((ObjectNode) value.get("religion_base_source_map_ref")).put("bytes", true),
                value -> ((ObjectNode) value.get("religion_base_source_map_ref")).put("bytes", 1.0),
                value -> ((ObjectNode) value.get("religion_base_source_map_ref")).put("bytes", "14486"),
                value -> ((ObjectNode) value.get("religion_base_source_map_ref")).put("sha256", "bad"));
        for (Consumer<ObjectNode> change : malformed) {
            ObjectNode invalid = original.deepCopy();
            change.accept(invalid);
            byte[] bytes = invalid.toString().getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> readBaseMap(bytes, sha256(bytes)));
        }
        ObjectNode drifted = original.deepCopy();
        ((ObjectNode) drifted.get("religion_base_source_map_ref")).put("sha256", "0".repeat(64));
        byte[] bytes = drifted.toString().getBytes(StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> readBaseMap(bytes, sha256(bytes)));
    }
    private Context context(Build build)throws Exception{Instant now=Instant.now();ExactRef source=ref("nativeDriverFrozen");G2Source g2=new G2Source("software-fixture-machine",now.toString(),"original-request-producer-fixture",source);var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(7),BigInteger.ONE),"original-fixture",BigInteger.valueOf(5),"fixture-episode");return new Context(new ProposalLifecycle.ObservationIdentity(g2.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1),g2,"fixture-session",BigInteger.valueOf(11),build,now.plusSeconds(60));}
    private ActionContext action(Context context){return new ActionContext(context,"durable-fixture",new ProposalLifecycle.ExpectedPostcondition(1,context.before(),context.source(),"software-fixture/v1",List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"),true))),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()));}
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT EXECUTED: original producer property missing: "+key);return value;}
    private static final class Captured extends RuntimeException { private static final long serialVersionUID=1; }
    private static final class Capture implements PlanningReadPort,ActionCoordinatorPort {
        int calls;ActionCommand action;PlanningReadRequest read;ReadContract<?> contract;
        void reset(){action=null;read=null;contract=null;}
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){this.contract=contract;this.read=request;calls++;throw new Captured();}
        @Override public ActionReceipt execute(ActionCommand command){action=command;calls++;throw new Captured();}
        @Override public ActionReceipt reconcile(String actionId){throw new UnsupportedOperationException("request producer fixture has no journal or Game");}
    }
}
