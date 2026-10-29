package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.build.ControlBuild;

/** Test-only independent original-source oracle. No driver instance, current Root or IO authority is issued. */
public final class OriginalPublicPlanningOracle {
    private OriginalPublicPlanningOracle() { }
    private static final int LIMIT=1<<20;
    private static final Map<String,String> PINS=Map.of(
        "bridge/service.py","a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e",
        "bridge/native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603",
        "bridge/h2743_preaction_existing_truce_v1.py","3a63d58445c29bc43cde4827b7626576f53a64d01bf15db15b508a40b3b587f5",
        "lifestyle_formal_consumer.py","d971e1737acd5654a6fdd9c7219a3982a6bce3de44b0c95bc0fac735922b7df2",
        "bridge/ordinary_sway_service_v1.py","3f45b4c07dd79a8279605c438a57fa7cdc819a7900a642953f9c3e0fd93d8321",
        "ordinary_player_risk_context_v1.py","32fbced5f6f6c874e556f1953ffbe228cafeb9a4dc6384166502af19e8a2bfe3");
    private static final String ORIGINAL="""
        import ast,copy,hashlib,json,pathlib,sys,types,base64,importlib
        sys.dont_write_bytecode=True
        repo=pathlib.Path(sys.argv[1]).resolve(strict=True)
        source=repo/'ck3_autonomous_player/src/xar_autoplayer'
        pins=json.loads(base64.b64decode(sys.argv[2])); mode=sys.argv[3]
        case_raw=pathlib.Path(sys.argv[4]).read_bytes()
        assert len(case_raw)==int(sys.argv[5])<=1048576
        assert hashlib.sha256(case_raw).hexdigest()==sys.argv[6]
        cases=json.loads(case_raw)
        def exact(name):
            path=source/name; raw=path.read_bytes()
            assert hashlib.sha256(raw).hexdigest()==pins[name],name
            return path,raw
        service_path,service_raw=exact('bridge/service.py')
        native_path,native_raw=exact('bridge/native_driver.py')
        for name in pins:exact(name)
        # Execute these exact checked source bytes, preserving real relative imports and code filename.
        name='xar_autoplayer.bridge.service'
        module=types.ModuleType(name);module.__file__=str(service_path);module.__package__='xar_autoplayer.bridge'
        sys.modules[name]=module
        exec(compile(service_raw,str(service_path),'exec'),module.__dict__)
        Service=module.GameplayBridgeService
        assert pathlib.Path(Service.plan_turn.__code__.co_filename).resolve()==service_path.resolve()
        tree=ast.parse(service_raw.decode('utf-8-sig'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='GameplayBridgeService')
        parent=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_plan_turn_internal_without_readonly_retry_v1')
        inner=next(n for n in parent.body if isinstance(n,ast.FunctionDef) and n.name=='plan_from_view')
        assigned=next(n for n in inner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='planned' for t in n.targets) and isinstance(n.value,ast.Dict))
        prune=next(n for n in inner.body if isinstance(n,ast.If) and ast.unparse(n.test)=='window_priority is not None')
        marker=next(n for n in parent.body if isinstance(n,ast.If) and isinstance(n.test,ast.Call) and ast.unparse(n.test).startswith("planned.pop('_private_window_priority_v1'"))
        native_tree=ast.parse(native_raw.decode('utf-8-sig'))
        validate=next(n for n in native_tree.body if isinstance(n,ast.FunctionDef) and n.name=='_validate_revision')
        native_env={};exec(compile(ast.Module(body=[validate],type_ignores=[]),str(native_path),'exec'),native_env)
        from xar_autoplayer.bridge.ordinary_sway_service_v1 import project_ordinary_sway_input_v1
        from xar_autoplayer.ordinary_player_risk_context_v1 import build_ordinary_player_risk_context_v1
        rows=[]
        for case in cases:
            if mode=='plan':
                snapshot=case['snapshot'];history=case['history'];flags=case['flags'];branch=case['branch']
                driver=types.SimpleNamespace(**flags);driver.capabilities=lambda:{'bridge_capabilities':[]}
                owner=Service.__new__(Service);owner.driver=driver
                env=dict(module.__dict__);env.update(self=owner,planning_snapshot=snapshot,history=history,
                    played_character=snapshot.get('played_character'),plan=case['detail'],
                    opening_focus_first=flags['require_initial_lifestyle_focus_before_date_advance'],
                    window_priority=case['detail'] if branch=='WINDOW_PRIORITY' else None,
                    planning_source_frame=Service._observed_planning_source_frame(snapshot),
                    routable_steps=set(case['steps']),use_internal_view=False,private_history_views={})
                exec(compile(ast.Module(body=[assigned],type_ignores=[]),str(service_path),'exec'),env)
                before={k:copy.deepcopy(v) for k,v in env['planned'].items() if k.startswith('_private_')}
                exec(compile(ast.Module(body=[prune],type_ignores=[]),str(service_path),'exec'),env)
                eval(compile(ast.Expression(marker.test),str(service_path),'eval'),env)
                # Detach public JSON slots independently; original AST snapshots may alias.
                planned={k:copy.deepcopy(v) for k,v in env['planned'].items()}
                # Both are original pure observed-data producers; no substitute/native read or algorithm is supplied.
                planned['plan']={**planned['plan'],'player_risk_context':build_ordinary_player_risk_context_v1(snapshot,None)}
                planned['_ordinary_sway_input_v1']=project_ordinary_sway_input_v1(snapshot,None)
                # Only documented public uint64 roles change representation; domain/body numbers remain untouched.
                planned['revision']=str(planned['revision'])
                for frame in [planned['planning_source_frame'],planned['_auto_camera_hotspot_input']['source_frame']]:
                    for key in ['revision','native_revision','connection_generation']:
                        if frame[key] is not None:frame[key]=str(frame[key])
                # Explicit public identity representation contract, never recursive key guessing.
                def decimal_role(obj,key):
                    if isinstance(obj,dict) and key in obj and obj[key] is not None:
                        assert type(obj[key]) is int and obj[key]>=0
                        obj[key]=str(obj[key])
                for key in ['_private_faction_snapshot_v1','_private_construction_snapshot_v1',
                    '_private_family_marriage_snapshot_v1','_private_council_snapshot_v1','_private_m5_snapshot_v1']:
                    observed=planned.get(key)
                    if isinstance(observed,dict):
                        decimal_role(observed,'revision');decimal_role(observed,'native_revision')
                        decimal_role(observed.get('diagnostics'),'connection_generation')
                decimal_role(planned.get('_private_lifestyle_scope_v1'),'snapshot_revision')
                pending=planned.get('_private_lifestyle_pending_v1')
                if isinstance(pending,dict):
                    decimal_role(pending,'pre_public_revision')
                    decimal_role(pending.get('source_frame'),'revision');decimal_role(pending.get('source_frame'),'native_revision')
                war=planned.get('_private_lifestyle_war_frame_v1')
                if isinstance(war,(list,tuple)):
                    war=list(war)
                    if war[3] is not None:war[3]=str(war[3])
                    planned['_private_lifestyle_war_frame_v1']=war
                sway=planned['_ordinary_sway_input_v1']
                decimal_role(sway['snapshot'],'revision');decimal_role(sway['snapshot'],'native_revision')
                decimal_role(sway.get('root'),'snapshot_revision')
                rows.append({'before_private':before,'public':planned})
            elif mode=='revision':
                try:native_env['_validate_revision'](case['value'],'expected_revision');rows.append({'accepted':True})
                except Exception as error:rows.append({'accepted':False,'kind':type(error).__name__,'message':str(error)})
            elif mode=='routing':rows.append(module._route_plan_to_available_step(case['detail'],set(case['steps'])))
            elif mode=='h2743_entry':
                owner=Service.__new__(Service);owner.driver=types.SimpleNamespace()
                kwargs={k:case[k] for k in ('expected_revision','expected_h2743_frame') if k in case}
                try:Service.execute_step(owner,case['step'],**kwargs)
                except (module.BridgeUnavailableError,module.UnsupportedStepError) as error:rows.append({'kind':type(error).__name__,'message':str(error)})
                else:raise AssertionError('H2743 reader absence or required claim was not rejected')
            elif mode=='h2743_native_failure':
                function=next(n for n in ast.walk(native_tree) if isinstance(n,ast.FunctionDef) and n.name=='query_h2743_preaction_existing_truce_v1')
                error=module.BridgeUnavailableError('actual H2743 entry failure')
                step=importlib.import_module('xar_autoplayer.bridge.h2743_preaction_existing_truce_v1').QUERY_STEP
                env={'H2743_PREACTION_EXISTING_TRUCE_STEP':step}
                exec(compile(ast.Module(body=[function],type_ignores=[]),str(native_path),'exec'),env)
                class Boundary:
                    def __init__(self):self.attempts=0;self.rows=[]
                    def _execute_native_war_step(self,*a,**k):self.attempts+=1;raise error
                    def _record_command(self,command,**fields):self.rows.append({'command':command,**fields})
                boundary=Boundary()
                try:env[function.name](boundary,case['frame'],expected_revision=case['revision'])
                except module.BridgeUnavailableError as actual:
                    assert actual is error
                    rows.append({'attempts':boundary.attempts,'rows':boundary.rows,'same_error':True})
                else:raise AssertionError('the dedicated original H2743 failure was lost')
            elif mode=='unsupported':
                owner=Service.__new__(Service)
                owner.driver=types.SimpleNamespace(execute_step=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('unsupported route called driver')))
                try:owner.execute_step(case['step']);raise AssertionError('unsupported route returned')
                except module.UnsupportedStepError as error:rows.append({'kind':type(error).__name__,'message':str(error)})
            else:raise AssertionError(mode)
        for name in pins:exact(name)
        print(json.dumps({'rows':rows},sort_keys=True,separators=(',',':'),allow_nan=False))
        """;

    public static JsonNode run(String mode, JsonNode cases, Path scratch) throws Exception {
        Path repo=requiredPath("xar.repository.root"),python=requiredPath("xar.python");
        Path source=repo.resolve("ck3_autonomous_player/src/xar_autoplayer");
        var refs=new java.util.ArrayList<ControlBuild.FileRef>();
        for(var pin:PINS.entrySet()) {
            Path original=source.resolve(pin.getKey()).toRealPath();
            var ref=ControlBuild.FileRef.measure(original);
            if(ref.bytes()<=0||ref.bytes()>(2L<<20)||!ref.sha256().equals(pin.getValue()))
                throw new IOException("NOT_RUN_REQUIRED_ORIGINAL_SOURCE: "+pin.getKey());
            ref.verify();refs.add(ref);
        }
        byte[] body=PublicDataJson.encode(cases).bytes();
        if(body.length>LIMIT)throw new IOException("finite original oracle cases required");
        Files.createDirectories(scratch);Path input=Files.createTempFile(scratch,"original-plan-cases-",".json");
        Files.write(input,body);var inputRef=ControlBuild.FileRef.measure(input);
        String pins=Base64.getEncoder().encodeToString(ControlBuild.strictMapper().writeValueAsBytes(PINS));
        // Preserve the exact original program across Windows argument quote parsing.
        String program="exec(__import__('base64').b64decode('"
                +Base64.getEncoder().encodeToString(ORIGINAL.getBytes(StandardCharsets.UTF_8))+"'))";
        ProcessBuilder builder=new ProcessBuilder(python.toString(),"-B","-X","utf8","-c",program,
                repo.toString(),pins,mode,input.toString(),Long.toString(inputRef.bytes()),inputRef.sha256());
        builder.directory(repo.toFile()).redirectErrorStream(true);
        var env=builder.environment();env.put("PYTHONPATH",repo.resolve("ck3_autonomous_player/src").toString());
        env.put("XAR_SOURCE_REPOSITORY",repo.toString());env.put("PYTHONDONTWRITEBYTECODE","1");env.put("PYTHONUTF8","1");
        env.put("PYTHONPYCACHEPREFIX",scratch.resolve("absent-original-bytecode-cache").toString());
        Process child=builder.start();child.getOutputStream().close();
        var output=new java.util.concurrent.CompletableFuture<byte[]>();
        Thread reader=Thread.ofVirtual().start(()->{
            try(var stream=child.getInputStream()) {
                byte[] bytes=stream.readNBytes(LIMIT+1);
                if(bytes.length>LIMIT){child.destroyForcibly();throw new IOException("original oracle exceeded finite output bound");}
                output.complete(bytes);
            }catch(Throwable failure){output.completeExceptionally(failure);}
        });
        try {
            if(!child.waitFor(45,TimeUnit.SECONDS)){child.destroyForcibly();throw new IOException("original PLAN/EXECUTE oracle timed out");}
            byte[] bytes=output.get(5,TimeUnit.SECONDS);
            if(child.exitValue()!=0)throw new IOException("original producer failed: "+new String(bytes,StandardCharsets.UTF_8));
            inputRef.verify();for(var ref:refs)ref.verify();
            return PublicDataJson.object(new RawJson(bytes)).get("rows");
        }finally {if(child.isAlive())child.destroyForcibly();reader.interrupt();}
    }
    public static org.xar.ck3.control.contracts.ExactRef bindingSource() throws IOException {
        Path root=requiredPath("xar.army.managers.java.root");
        var ref=ControlBuild.FileRef.measure(root.resolve("local-service/src/main/java/org/xar/ck3/control/service/mcp/RootMcpPlanning.java"));ref.verify();
        return new org.xar.ck3.control.contracts.ExactRef(ref.path(),ref.bytes(),ref.sha256());
    }
    public static <Q,R> PublicMcpDirectory directory(String name,org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings.TypedBinding<Q,R> actual)throws Exception {
        var descriptor=org.xar.ck3.control.service.root.RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(name)).findFirst()
            .orElseThrow(()->new IOException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));
        var bindings=PublicMcpBindingTest.oneAdmitted(name);
        PublicMcpNativeAdapter.register(bindings,org.xar.ck3.control.service.root.RootPublicCatalogCodec.executableTool(descriptor),actual);
        return bindings.freezeSoftwareScope();
    }
    public static PublicMcpDirectory.ToolCall call(String name,String json){
        return new PublicMcpDirectory.ToolCall(name,new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,
            java.util.Optional.of(new RawJson(json.getBytes(StandardCharsets.UTF_8)))),java.util.Optional.empty(),new McpCancellation());
    }
    public static JsonNode rpc(PublicMcpDirectory directory,String name,String arguments)throws Exception {
        return rpc(directory,name,arguments,PublicMcpSession.MODERN);
    }
    public static JsonNode rpc(PublicMcpDirectory directory,String name,String arguments,String protocol)throws Exception {
        if(!PublicMcpSession.MODERN.equals(protocol)&&!PublicMcpSession.LEGACY.contains(protocol))
            throw new IOException("declared actual MCP protocol required");
        try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
            peer.initialize(protocol);
            peer.send(PublicMcpProtocolTest.request(protocol,"1","tools/call",
                "\"name\":\""+name+"\",\"arguments\":"+arguments));
            return peer.receive();
        }
    }
    private static Path requiredPath(String property)throws IOException {
        String value=System.getProperty(property);
        if(value==null||value.isBlank())throw new IOException("NOT_RUN_REQUIRED: "+property);
        Path path=Path.of(value);if(!path.isAbsolute()||!path.normalize().equals(path))
            throw new IOException("exact absolute original path required: "+property);
        return path.toRealPath();
    }
}
