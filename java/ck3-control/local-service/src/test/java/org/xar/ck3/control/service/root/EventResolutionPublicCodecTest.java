package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeActiveEvent;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual original Service/normalizer/chooser are the compatibility oracle. Callbacks are declared software fixtures. */
final class EventResolutionPublicCodecTest {
    private static final String CONTRACT="876d69c1efa7948ebaa157782a688caeeab7954dc550e06dfc8afff1cc5e8970";
    private static final String SERVICE="a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e";
    private static final String EXAMPLE="e3a8b75462f485f01b19363ac8473855b482989be5c613b4f67f1d8b1ded04f3";
    private static final String DRIVER="eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6";
    private static final String PROGRAM="""
            import ast,copy,hashlib,json,pathlib,runpy,sys
            root=pathlib.Path(sys.argv[1])
            files=[('ck3_autonomous_player/src/xar_autoplayer/bridge/event_contract.py',sys.argv[2]),('ck3_autonomous_player/src/xar_autoplayer/bridge/service.py',sys.argv[3]),('ck3_autonomous_player/tests/unit/test_event_contract.py',sys.argv[4]),('ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py',sys.argv[5])]
            def pin():
                for name,sha in files:
                    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=sha:raise RuntimeError('actual event original drift: '+name)
            pin();scope=runpy.run_path(str(root/files[0][0]))
            source=ast.parse((root/files[1][0]).read_text(encoding='utf-8'))
            classes=[n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='GameplayBridgeService']
            if len(classes)!=1:raise RuntimeError('actual original Service class changed')
            methods=[n for n in classes[0].body if isinstance(n,ast.FunctionDef) and n.name in ('select_event_option','resolve_active_event')]
            driver=ast.parse((root/files[3][0]).read_text(encoding='utf-8'))
            errors=[n for n in driver.body if isinstance(n,ast.ClassDef) and n.name in ('BridgeUnavailableError','UnsupportedStepError')]
            if len(methods)!=2 or len(errors)!=2:raise RuntimeError('actual original resolver/exception definitions changed')
            # Only the unchanged original methods and exceptions are compiled. No module with frozen runtime roots is imported.
            cls=classes[0];cls.body=methods
            module=ast.Module(body=ast.parse('from __future__ import annotations').body+errors+[cls],type_ignores=[])
            exec(compile(ast.fix_missing_locations(module),str(root/files[1][0]),'exec'),scope)
            GameplayBridgeService=scope['GameplayBridgeService'];normalize_active_event=scope['normalize_active_event']
            tree=ast.parse((root/files[2][0]).read_text(encoding='utf-8'));base=None
            for cls in [n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='EventContractTests']:
                for fn in [n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_service_selects_typed_event_option_with_revision']:
                    for row in fn.body:
                        if isinstance(row,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='snapshot' for t in row.targets):base=ast.literal_eval(row.value)
            if not isinstance(base,dict) or base['active_event']['instance_id']!=812:raise RuntimeError('actual original example changed')
            choices=[[(True,0),(True,0)],[(True,-1),(True,7)],[(True,9),(True,9)],[(True,-0.0),(True,0.0)],[(True,2**53),(True,2**53+1)],[(False,1000),(True,-20)],[(True,2**80),(True,1e23)]]
            good=[]
            for scores in choices:
                for presence in ['missing','null','value']:
                    for revision in [17,(1<<64)-1]:
                        snapshot=copy.deepcopy(base);snapshot['revision']=revision
                        snapshot['active_event']['options']=[dict(index=i,option_number=i+1,label='original option '+str(i+1),enabled=enabled,strategy_score=score) for i,(enabled,score) in enumerate(scores)]
                        snapshot['active_event']['source']='retained-native-fixture';snapshot['active_event']['title']='Original callback example'
                        service=object.__new__(GameplayBridgeService);calls=[]
                        def take_snapshot(*,include_native_command_history=True):calls.append(['snapshot',include_native_command_history]);return copy.deepcopy(snapshot)
                        def execute(step,*,expected_revision):calls.append(['execute',step,expected_revision]);return dict(accepted=True,status='fixture_ack_only',step=step,revision=expected_revision,opaque_original='retained')
                        service.snapshot=take_snapshot;service.execute_step=execute;service.capabilities=lambda:{'action_steps':['select-event-option-1','select-event-option-2']}
                        args={}
                        if presence=='null':args.update(event_instance_id=None,expected_revision=None)
                        if presence=='value':args.update(event_instance_id=812,expected_revision=revision)
                        result=service.resolve_active_event(**args)
                        if calls[:2]!=[['snapshot',True],['snapshot',False]] or len(calls)!=3:raise RuntimeError('original callback sequence changed')
                        public=copy.deepcopy(args)
                        if public.get('expected_revision') is not None:public['expected_revision']=str(public['expected_revision'])
                        normalized=normalize_active_event(snapshot['active_event'],default_source='bridge')
                        good.append(dict(arguments=public,snapshot=snapshot,normalized=normalized,result=result,calls=calls))
            unavailable=[]
            for event in [None,dict(instance_id=812,option_count=2,options=[dict(index=0,enabled=False),dict(index=1,enabled=False)])]:
                service=object.__new__(GameplayBridgeService);snapshot=copy.deepcopy(base);snapshot['active_event']=event;service.snapshot=lambda **kwargs:copy.deepcopy(snapshot)
                service.execute_step=lambda *a,**k:(_ for _ in ()).throw(AssertionError('no native dispatch for unavailable event'))
                try:service.resolve_active_event()
                except Exception as failure:unavailable.append(dict(event=event,error=type(failure).__name__))
                else:raise RuntimeError('unavailable original unexpectedly submitted')
            pin();print(json.dumps(dict(good=good,unavailable=unavailable),separators=(',',':')))
            """;
    @Test void optionalPresenceAndCanonicalWideRevisionRoundTripWithoutCoercion() {
        for(var instance:EventOptionPublicCodec.Presence.values())for(var revision:EventOptionPublicCodec.Presence.values()) {
            var request=new EventResolutionPublicCodec.Request(field(instance,812),field(revision,new BigInteger("18446744073709551615")));
            var raw=EventResolutionPublicCodec.encodeRequest(request);
            assertEquals(request,EventResolutionPublicCodec.decode(PublicBindings.present(raw)));
            var n=StrictJson.parse(raw.bytes(),16384);assertEquals(instance!=EventOptionPublicCodec.Presence.MISSING,n.has("event_instance_id"));
            assertEquals(revision!=EventOptionPublicCodec.Presence.MISSING,n.has("expected_revision"));
            if(revision==EventOptionPublicCodec.Presence.VALUE)assertEquals("18446744073709551615",n.get("expected_revision").textValue());
        }
        var omitted=EventResolutionPublicCodec.decode(new PublicBindings.Missing());
        assertTrue(omitted.expectedInstance().isEmpty());assertTrue(omitted.expectedPublicRevision().isEmpty());
    }
    @Test void malformedRequestsAndUnknownFieldsFailBeforeTheCurrentRootIsAcquired() {
        assertThrows(IllegalArgumentException.class,()->EventResolutionPublicCodec.decode(new PublicBindings.Null()));
        for(String bad:List.of("[]","null","{\"event_instance_id\":0}","{\"event_instance_id\":true}","{\"event_instance_id\":1.0}",
                "{\"event_instance_id\":2147483648}","{\"expected_revision\":17}","{\"expected_revision\":\"01\"}","{\"expected_revision\":\"+1\"}",
                "{\"expected_revision\":\"-0\"}","{\"expected_revision\":\"18446744073709551616\"}","{\"option_number\":1}",
                "{\"expected_revision\":null,\"expected_revision\":null}","{} null"))
            assertThrows(IllegalArgumentException.class,()->EventResolutionPublicCodec.decode(PublicBindings.present(raw(bad))),bad);
        assertThrows(IllegalArgumentException.class,()->EventResolutionPublicCodec.decode(PublicBindings.present(new RawJson(new byte[]{(byte)0xc0,(byte)0x80}))));
    }
    @Test void actualOriginalResolverBestEnabledChoiceAndFullSelectionMetadataRemainCompatible()throws Exception {
        JsonNode corpus=oracle();int count=0;
        for(JsonNode sample:corpus.get("good")) {
            var request=EventResolutionPublicCodec.decode(PublicBindings.present(raw(sample.get("arguments").toString())));
            var event=NativeActiveEvent.normalize(sample.get("snapshot").get("active_event"),"bridge");
            assertEquals(sample.get("normalized"),event);
            var number=NativeActiveEvent.chooseOptionNumber(event).orElseThrow();
            assertEquals(sample.get("result").get("option_number").bigIntegerValue(),number);
            assertEquals("select-event-option-"+number,sample.get("calls").get(2).get(1).textValue());
            var row=sample.get("result").get("ordinary_events").get(0);
            assertEquals(event.get("options"),row.get("visible_options"));assertEquals("backend-neutral-event-v1",row.get("strategy").textValue());
            assertEquals(number.subtract(BigInteger.ONE),row.get("selected_option_index").bigIntegerValue());
            var selectedRevision=request.expectedPublicRevision().orElse(sample.get("snapshot").get("revision").bigIntegerValue());
            assertEquals(selectedRevision,sample.get("calls").get(2).get(2).bigIntegerValue());
            assertEquals(request,EventResolutionPublicCodec.decode(PublicBindings.present(EventResolutionPublicCodec.encodeRequest(request))));count++;
        }
        assertEquals(42,count);assertEquals(2,corpus.get("unavailable").size());
    }
    private static JsonNode oracle()throws Exception {
        Path root=Path.of(required("xar.repository.root"));Path python=Path.of(required("xar.python"));assertTrue(python.isAbsolute());
        pin(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/event_contract.py"),CONTRACT);
        pin(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/service.py"),SERVICE);
        pin(root.resolve("ck3_autonomous_player/tests/unit/test_event_contract.py"),EXAMPLE);
        pin(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py"),DRIVER);
        Process process=new ProcessBuilder(python.toString(),"-I","-B","-X","utf8","-c",PROGRAM,root.toString(),CONTRACT,SERVICE,EXAMPLE,DRIVER).redirectErrorStream(true).start();
        try(var executor=Executors.newSingleThreadExecutor()) {
            var output=executor.submit(()->process.getInputStream().readNBytes(1048577));
            if(!process.waitFor(60,TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly);process.destroyForcibly();
                process.waitFor(10,TimeUnit.SECONDS);throw new IllegalStateException("actual original resolve producer timeout");
            }
            byte[] bytes=output.get(10,TimeUnit.SECONDS);
            assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));assertTrue(bytes.length<=1048576);
            return OpportunityJson.toNode(DriverJson.object(bytes,1048576));
        } finally { if(process.isAlive()) { process.descendants().forEach(ProcessHandle::destroyForcibly);process.destroyForcibly(); } }
    }
    private static void pin(Path path,String expected)throws Exception { assertEquals(expected,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)))); }
    private static <T> EventOptionPublicCodec.Field<T> field(EventOptionPublicCodec.Presence presence,T value) { return switch(presence) {case MISSING->EventOptionPublicCodec.Field.missing();case NULL->EventOptionPublicCodec.Field.nullValue();case VALUE->EventOptionPublicCodec.Field.of(value);}; }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static String required(String name) { String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("Mandatory original resolve regression setting missing: "+name);return value; }
}
