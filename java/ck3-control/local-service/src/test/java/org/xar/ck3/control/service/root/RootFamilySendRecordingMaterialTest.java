package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Unchanged actual Python producer/recorder differential. Protocol fixture DATA grants no managed-Root authority. */
final class RootFamilySendRecordingMaterialTest {
    @Test void actualOriginalWrapperAndRecorderMatchTypedProjection() throws Exception {
        Path python=Path.of(required("xar.python")).toRealPath(),repo=Path.of(required("xar.repository.root")).toRealPath();
        var child=new ProcessBuilder(python.toString(),"-I","-B","-X","utf8","-c",ORACLE,repo.toString()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        child.getOutputStream().close();byte[] output;
        try {
            assertTrue(child.waitFor(30,TimeUnit.SECONDS),"actual original producer timeout");
            output=child.getInputStream().readNBytes(65537);assertTrue(output.length<=65536);assertEquals(0,child.exitValue());
        } finally {if(child.isAlive()){child.destroyForcibly();assertTrue(child.waitFor(10,TimeUnit.SECONDS));}}
        JsonNode rows=StrictJson.parse(output);assertEquals(2,rows.size());
        for(JsonNode row:rows){
            RawJson raw=new RawJson(StrictJson.canonical(row.get("primitive")));
            ObjectNode choice=(ObjectNode)row.get("choice");
            RawJson actual=RootFamilySendRecordingMaterial.project("arrange-marriage-101-202",choice,raw,12345);
            assertEquals(row.get("result"),StrictJson.parse(actual.bytes()));
            assertEquals(row.get("history").get("result"),StrictJson.parse(actual.bytes()));
            assertTrue(row.get("history").get("ok").booleanValue());
            assertEquals("arrange-marriage-101-202",row.get("history").get("command").textValue());
            assertEquals(1,row.get("history").get("index").intValue());
            assertFalse(StrictJson.parse(actual.bytes()).has("marriage_result"),"send records cannot invent relationship outcomes");
            assertThrows(IllegalArgumentException.class,()->RootFamilySendRecordingMaterial.project("arrange-marriage-101-303",choice,raw,12345));
            ObjectNode wrong=choice.deepCopy().put("played_character_id",true);
            assertThrows(IllegalArgumentException.class,()->RootFamilySendRecordingMaterial.project("arrange-marriage-101-202",wrong,raw,12345));
        }
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException(key+" required; actual original producer NOT_RUN without fallback/skip");return value;}
    private static final String ORACLE="""
import ast,copy,hashlib,importlib,json,sys,threading,types
from pathlib import Path
repo=Path(sys.argv[1]).resolve();base=repo/'ck3_autonomous_player/src/xar_autoplayer/bridge'
p=base/'native_driver.py';b=p.read_bytes()
if len(b)!=1658471 or hashlib.sha256(b).hexdigest()!='eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603':raise RuntimeError('actual original driver pin changed')
c=base/'marriage_contract.py';cb=c.read_bytes()
if len(cb)!=3370 or hashlib.sha256(cb).hexdigest()!='f85b94e237f7ec4baa7cb872b29514cec4210afca583fc51075114e6e7e4db71':raise RuntimeError('actual original contract pin changed')
sys.path.insert(0,str(base.parent.parent));contract=importlib.import_module('xar_autoplayer.bridge.marriage_contract')
names={'_date_raw','_execute_arrange_marriage_step','_record_command'};nodes=[]
for node in ast.walk(ast.parse(b.decode('utf-8-sig'))):
 if isinstance(node,ast.FunctionDef) and node.name in names:node.decorator_list=[];nodes.append(node)
if {n.name for n in nodes}!=names:raise RuntimeError('actual producer body missing')
env=dict(vars(contract),copy=copy,BridgeUnavailableError=RuntimeError,UnsupportedStepError=RuntimeError,
 _RESTORE_CHECKPOINT_STEP='restore-checkpoint',QUERY_ARMY_STRENGTHS_STEP='query-army-strengths',CONTINUE_AS_RECONCILED_SUCCESSOR_STEP='continue-as-successor',
 _is_deferred_read_only_history_step=lambda step:False,is_life_advance_step=lambda step:False)
exec(compile(ast.fix_missing_locations(ast.Module(body=ast.parse('from __future__ import annotations').body+nodes,type_ignores=[])),str(p),'exec'),env)
for name in names:
 if Path(env[name].__code__.co_filename).resolve()!=p.resolve():raise RuntimeError('substituted original body')
rows=[]
choice={'choice_id':'101-202','played_character_id':101,'candidate_character_id':202,'ignored_original_extra':'drop exactly as original normalizer'}
for primitive in ({'step':'arrange-marriage-101-202','accepted':True,'native_exact':9223372036854775807},None):
 projected={**primitive,'backend_id':'native-headless'} if isinstance(primitive,dict) else {'result':primitive,'backend_id':'native-headless'}
 driver=types.SimpleNamespace(_driver_state_lock=threading.RLock(),_history_lock=threading.RLock(),_command_history=[],_driver_state_dirty=False,
  _arrange_marriage_choices=contract.normalize_arrange_marriage_choices([choice]),_arrange_marriage_query_sequence=9,
  take_snapshot=lambda:{'date_raw':12345},_execute_primitive_step=lambda *args,**kwargs:copy.deepcopy(projected),
  _persist_driver_state=lambda **kwargs:None,_route_horizon_wal_eligible_v1=lambda *args:False)
 result=env['_execute_arrange_marriage_step'](driver,'arrange-marriage-101-202',expected_revision=7)
 env['_record_command'](driver,'arrange-marriage-101-202',ok=True,result=result)
 rows.append(dict(primitive=primitive,choice=choice,result=result,history=driver._command_history[0]))
if hashlib.sha256(p.read_bytes()).hexdigest()!=hashlib.sha256(b).hexdigest() or c.read_bytes()!=cb:raise RuntimeError('original changed during differential')
json.dump(rows,sys.stdout,separators=(',',':'))
""";
}
