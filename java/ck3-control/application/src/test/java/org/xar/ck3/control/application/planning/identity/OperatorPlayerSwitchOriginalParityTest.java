package org.xar.ck3.control.application.planning.identity;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;

/** Original MCP helper -> Service -> native Driver method bodies, with explicit DATA endpoint/snapshot fixtures. */
final class OperatorPlayerSwitchOriginalParityTest {
    private static final String ORACLE="""
        import ast,copy,json,pathlib,runpy,sys,threading,types
        bridge=pathlib.Path(sys.argv[1]).resolve()/'ck3_autonomous_player/src/xar_autoplayer/bridge'
        x=json.load(sys.stdin)
        ns=runpy.run_path(str(bridge/'set_played_character_contract.py'))
        # Execute the exact selected function bodies. Giant-module imports and their environment are not qualified here.
        ns.update(copy=copy,BridgeUnavailableError=RuntimeError,UnsupportedStepError=RuntimeError,PreSubmissionRevisionMismatchError=RuntimeError)
        def selected(file,owner,name):
          tree=ast.parse((bridge/file).read_text(encoding='utf-8-sig'))
          scope=tree.body if owner is None else next(v for v in tree.body if isinstance(v,ast.ClassDef) and v.name==owner).body
          matches=[v for v in scope if isinstance(v,ast.FunctionDef) and v.name==name]
          assert len(matches)==1,(file,owner,name)
          future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
          module=ast.fix_missing_locations(ast.Module(body=[future,matches[0]],type_ignores=[]))
          exec(compile(module,str(bridge/file),'exec'),ns)
          return ns[name]
        selected('native_driver.py',None,'_validate_revision')
        selected('native_driver.py',None,'_string_list')
        # The rejection type is never used to claim an effect; the positive fixture supplies one native ACK.
        ns['_NativeCommandRejectedError']=type('FixtureNativeRejection',(RuntimeError,),{})
        native=selected('native_driver.py','NativeHeadlessGameplayDriver','set_player_character_v1')
        service=selected('service.py','GameplayBridgeService','set_player_character_v1')
        mcp=selected('mcp_server.py',None,'_ck3_set_played_character_v1')
        class Driver:
          def __init__(self):
            self._episode_character_id=x['prior_actor'];self._episode_run_id='same-run';self._episode_identity_lock=threading.Lock()
            self._episode_binding_state='active_new';self._driver_state_restore_kind='new_episode'
            self._command_history=[{'index':1,'command':'controlled-existing-history','ok':True}]
            self._succession_lifecycle={'retain':'original lifecycle'};self._campaign_goal={'retain':'original goal'}
            self.written=False;self.calls=[];self.persisted=False
            for key in ('declarable_wars','declaration_query_sequence','declaration_query_binding','army_strength_query','combat_simulation_inputs_query',
              'combat_simulation_inputs_v3_query','battle_control_snapshot_v1_query','active_combat_retreat_v1_token','war_entry_assessments_query',
              'war_termination_options','war_termination_terms','war_termination_exit_terms','arrange_marriage_choices','arrange_marriage_query_sequence',
              'succession_expectation','succession_reconciliation'):
              setattr(self,'_'+key,{'old_character_cache':True})
          def capabilities(self):return {'bridge_capabilities':[ns['SET_PLAYED_CHARACTER_V1_CAPABILITY']]}
          def take_snapshot(self):
            self.calls.append('snapshot')
            return {'revision':x['after_revision'] if self.written else 10,'native_revision':12,'date_raw':x['date_raw'],
              'paused':True,'map_ready':True,'played_character':{'character_id':7 if self.written else x['from_actor'],'alive':True if self.written else x['before_alive']},
              'diagnostics':{'hello':{'expected_ck3_version':ns['SET_PLAYED_CHARACTER_V1_GAME_VERSION'],'expected_ck3_sha256':ns['SET_PLAYED_CHARACTER_V1_EXECUTABLE_SHA256']}},
              'episode_character_id':self._episode_character_id,'episode_run_id':self._episode_run_id,
              'one_life_terminal':self._episode_character_id!=7,'one_life_terminal_reason':'dead' if self._episode_character_id!=7 else None}
          def _execute_primitive_step(self,step,*,expected_revision,required_capability):
            assert step=='set-played-character-v1-7' and expected_revision==10 and required_capability==ns['SET_PLAYED_CHARACTER_V1_CAPABILITY']
            self.calls.append('native_once');assert not self.written;self.written=True;return {'status':x['status']}
          def wait_for_change(self,expected_revision,timeout_seconds):
            assert expected_revision==10 and timeout_seconds==5.0;self.calls.append('wait_for_change');return self.take_snapshot()
          def _persist_driver_state(self,*,persistence_reason):
            assert persistence_reason=='player_identity' and self._episode_character_id==7
            self.calls.append('persist_player_identity');self.persisted=True
          def _record_command(self,*args,**kwargs):raise AssertionError('the actual original setter does not append compatibility history')
        driver=Driver();driver.set_player_character_v1=types.MethodType(native,driver)
        wrapper=types.SimpleNamespace(driver=driver,capabilities=driver.capabilities,snapshot=driver.take_snapshot)
        wrapper.set_player_character_v1=types.MethodType(service,wrapper)
        result=mcp(wrapper,7,10)
        for key in ('before_revision','after_revision','native_revision'):result[key]=str(result[key])
        assert isinstance(result['date_raw'],int) and not isinstance(result['date_raw'],bool)
        out={'result':result,'calls':driver.calls,'persisted':driver.persisted,'history':driver._command_history,
          'lifecycle':driver._succession_lifecycle,'goal':driver._campaign_goal,'restore_kind':driver._driver_state_restore_kind,
          'binding_state':driver._episode_binding_state,'retreat':driver._active_combat_retreat_v1_token}
        print(json.dumps(out,separators=(',',':')))
        """;
    private static final ExactRef DATA=new ExactRef("D:/operator-original-parity/data.json",1,"a".repeat(64));
    private static ExactRef ref(String role){return new ExactRef("D:/operator-original-parity/"+role,1,"b".repeat(64));}
    private static void requireOriginal(Path path,String sha)throws Exception {
        assertTrue(Files.isRegularFile(path),"the exact original producer is mandatory");byte[] bytes=Files.readAllBytes(path);
        assertTrue(bytes.length<=(4<<20));assertEquals(sha,ActionCodec.sha256(bytes),"original fixture source changed; collect a new explicit oracle input");
    }
    private static ObjectNode original(ObjectNode fixture)throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repository,"original workspace is mandatory; no skip");assertNotNull(python,"explicit Python interpreter is mandatory; no skip");assertFalse(python.isBlank());
        Path root=Path.of(repository).toRealPath(),bridge=root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge");
        requireOriginal(bridge.resolve("set_played_character_contract.py"),"cfda4f0cc4deb230369c500b6ac75dfe9fececf52530623272e46f8bd6524a30");
        requireOriginal(bridge.resolve("native_driver.py"),"eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603");
        requireOriginal(bridge.resolve("service.py"),"a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e");
        requireOriginal(bridge.resolve("mcp_server.py"),"b7569231226484b0bdd98c40ace14a82672b2138a0aab77711e559a4d9b8ccbc");
        Process child=new ProcessBuilder(python,"-B","-X","utf8","-c",ORACLE,root.toString()).redirectErrorStream(true).start();
        var output=CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readNBytes(16385);}catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}});
        try {
            try(var input=child.getOutputStream()){input.write(StrictJson.canonical(fixture));}
            boolean ended=child.waitFor(30,TimeUnit.SECONDS);if(!ended)child.destroyForcibly();assertTrue(ended,"bounded original producer oracle timeout");
            byte[] bytes=output.get(5,TimeUnit.SECONDS);assertTrue(bytes.length<=16384,"bounded original producer oracle output required");assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));
            JsonNode parsed=StrictJson.parse(bytes);assertInstanceOf(ObjectNode.class,parsed);return (ObjectNode)parsed;
        }finally{if(child.isAlive())child.destroyForcibly();}
    }
    @Test void actualOriginalPublicChainPreservesAllFieldsForSwitchAlreadyPlayedAndSameActorNoop()throws Exception {
        for(int branch=0;branch<3;branch++) {
            String status=branch==0?"switched":"already_played";long prior=branch==2?7:3,from=branch==0?3:7;
            var fixture=StrictJson.object();fixture.put("status",status);fixture.put("prior_actor",prior);fixture.put("from_actor",from);fixture.put("before_alive",branch!=0);
            fixture.put("after_revision",branch==0?11:10);fixture.put("date_raw",Integer.MIN_VALUE);
            var expected=original(fixture);var game=new GameGeneration(123,new PythonOnlyUInt64(BigInteger.valueOf(1001)));
            var source=new G2Source("controlled-original","2026-10-24T08:45:00Z","1.19.0.6",DATA);
            var refs=new OperatorPlayerSwitch.Artifacts(ref("hello"),ref("before"),ref("ack"),ref("after"),ref("before-driver"),ref("after-driver"),ref("before-aux"),ref("after-aux"),ref("commit"),ref("proof"),ref("rebound"));
            var completion=new OperatorPlayerSwitch.Completion(new OperatorPlayerSwitch.Request(7,BigInteger.TEN),"controlled-action","c".repeat(64),"controlled-request",source,
                    new NativeObservationPort.TransportSession("controlled-original",game,BigInteger.ONE,"session"),"same-run",2,prior,5,prior==7?5:6,
                    OperatorPlayerSwitch.NativeStatus.parse(status),BigInteger.valueOf(branch==0?11:10),BigInteger.valueOf(12),Integer.MIN_VALUE,refs);
            var actual=StrictJson.parse(OperatorPlayerSwitch.publicResult(completion,from).bytes());assertEquals(expected.get("result"),actual);
            assertEquals(prior!=7,expected.get("persisted").booleanValue());assertEquals(1,expected.get("history").size());
            assertEquals("original lifecycle",expected.get("lifecycle").get("retain").textValue());assertEquals("original goal",expected.get("goal").get("retain").textValue());
            assertEquals(branch==0,expected.get("calls").toString().contains("wait_for_change"));
            assertEquals(prior==7?"new_episode":"operator_played_character_rebind",expected.get("restore_kind").textValue());
            assertEquals(prior==7?"active_new":"active_operator_rebind",expected.get("binding_state").textValue());
            if(prior!=7)assertTrue(expected.get("retreat").isNull());
        }
    }
}
