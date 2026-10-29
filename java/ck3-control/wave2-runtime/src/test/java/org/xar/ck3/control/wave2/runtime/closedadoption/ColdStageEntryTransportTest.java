package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.WindowsJobProcess;
import static org.junit.jupiter.api.Assertions.*;

/** Actual existing emitter -> emitted transport -> exact original pure SDK functions, using owned small files only. */
final class ColdStageEntryTransportTest {
    @TempDir Path temporary;
    @Test void actualEmitterAndOriginalSdkFunctionsRejectWrongDynamicSources() throws Exception {
        String repoValue=System.getProperty("xar.repo",System.getenv("XAR_REPO_ROOT"));
        assertNotNull(repoValue,"explicit current source repo required");Path repo=Path.of(repoValue).toRealPath();
        Path producer=Path.of(System.getProperty("xar.recovery.prepare",repo.resolve("tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py").toString()));
        Path python=Path.of(System.getProperty("xar.python",repo.resolve("tools/.venv/Scripts/python.exe").toString()));
        var environment=new HashMap<>(System.getenv());environment.put("PYTHONDONTWRITEBYTECODE","1");environment.put("PYTHONUTF8","1");
        environment.put("TMP",temporary.toString());environment.put("TEMP",temporary.toString());
        var command=new WindowsJobProcess.CommandSpec(python,List.of("-I","-B","-X","utf8","-c",PROGRAM,
                producer.toString(),repo.resolve("tools/g2_saved_campaign/prepare_source28_a14_rich_native31_union_v1.py").toString(),
                repo.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/succession_transition_contract.py").toString(),temporary.toString()),
                temporary,environment,temporary.resolve("stdout.json"),temporary.resolve("stderr.log"),96L*1024*1024);
        try(var process=WindowsJobProcess.start(command)) {
            var result=process.await(Duration.ofSeconds(20),Instant.now().plusSeconds(20),()->{});
            assertTrue(result.passed(),()->read(temporary.resolve("stderr.log")));assertEquals(0,result.accounting().activeProcesses());
        }
        assertEquals("{\"cases\":6,\"original_sdk_calls\":1}",Files.readString(temporary.resolve("stdout.json")).trim());
    }
    private static String read(Path path) {try{return Files.readString(path);}catch(java.io.IOException error){return error.toString();}}
    private static final String PROGRAM="""
import ast,hashlib,json,os,sys
from pathlib import Path
from typing import Final
producer,legacy,sdk,root=map(Path,sys.argv[1:])
def need(ok,message):
    if not ok: raise ValueError(message)
def load_selected(path,names,namespace):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    nodes=[]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in names: nodes.append(node)
        elif isinstance(node,(ast.Assign,ast.AnnAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            if any(isinstance(target,ast.Name) and target.id in names for target in targets): nodes.append(node)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
space={'ast':ast,'hashlib':hashlib,'MAX_FILE':1048576,'need':need,'sha256_v1':lambda raw:hashlib.sha256(raw).hexdigest()}
load_selected(producer,{'ROOT_COLD_STAGE_BINDINGS_TRANSPORT_V1','emit_root_cold_stage_bindings_transport_v1'},space)
old={};load_selected(legacy,{'MOD_CLEAN_RUNTIME14'},old)
original=old['MOD_CLEAN_RUNTIME14'].encode();emitted=space['emit_root_cold_stage_bindings_transport_v1'](original)
pure={'Final':Final};exec('import re',pure)
load_selected(sdk,{'SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA','ROGUE_ONE_LIFE','ORDINARY_CAMPAIGN_SUCCESSION','UNKNOWN_SUCCESSION_LIFECYCLE',
    '_SUCCESSION_LIFECYCLES','_LIFECYCLE_BINDING_FIELDS','normalize_succession_lifecycle_binding_v1',
    'verify_xar_mod_absence_evidence_v1','bind_succession_lifecycle_from_environment_v1'},pure)
calls=0
def original_binder(*args,**kwargs):
    global calls
    calls+=1
    return pure['bind_succession_lifecycle_from_environment_v1'](*args,**kwargs)
entry={'Path':Path,'json':json,'original_bind_lifecycle':original_binder}
exec(compile(emitted,'<actual emitted Root cold metadata transport>','exec'),entry)
def write(name,value):
    path=root/name;raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode();path.write_bytes(raw)
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
profile=root/'profile';profile.mkdir();(profile/'logs').mkdir();mods=write('profile/dlc_load.json',{'enabled_mods':[]})
snapshot=root/'snapshot.log';snapshot.write_bytes(b'[setup] Synthetic known-empty startup source fixture\\n')
snap={'path':str(snapshot),'bytes':snapshot.stat().st_size,'sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest()}
manifest={'machine_id':'source-fixture-machine','profile_dir':str(profile),'environment_sha256':'a'*64,'rules':{'profile':[]},'fixture_integer':1,
    'load_profile':{'enabled_mods':[],'dlc_load_sha256':mods['sha256']}}
manifest_ref=write('environment.json',manifest);review_ref=write('root-stage-review.json',{'scope':'SYNTHETIC_DATA_NOT_AUTHORITY'})
birth='18446744073709551615';nonce='b'*32
launch={'schema':'xar.root-held-saved-game-launch/v1','machine_id':'source-fixture-machine','session_nonce':nonce,'pid':2222,'creation_filetime_decimal':birth}
launch_ref=write('launch.json',launch)
proof={'schema':'xar.verified-xar-mod-absence/v2','machine_id':'source-fixture-machine','game_pid':2222,'game_creation_filetime_decimal':birth,
    'status':'ACTUAL_PROFILE_AND_STARTUP_LOG_VERIFIED','reviewer':'/root','enabled_mods_known':True,'loaded_mods_known':True,'startup_log_reviewed':True,
    'enabled_mods':[],'loaded_mods':[],'environment_sha256':'a'*64,'profile_dir':str(profile),'profile_enabled_mods':mods,'startup_log_snapshot':snap,
    'startup_log_original_path':str(profile/'logs/game.log'),'actual_game':launch_ref,'environment_manifest':manifest_ref,'root_stage_review':review_ref}
proof_ref=write('proof.json',proof)
expected={'schema':'xar.ck3.succession-lifecycle-binding/v1','lifecycle':'ordinary_campaign_succession','xar_enabled':None,
    'pact_contract':'absent_by_verified_xar_mod_not_loaded','source':'absent_by_verified_xar_mod_not_loaded','environment_sha256':'a'*64}
sidecar={'schema':'xar.root-saved-cold-actual-bindings/v1','machine_id':'source-fixture-machine','session_nonce':nonce,'basis_ref':review_ref,
    'qualification_ref':review_ref,'plan_ref':review_ref,'quote_ref':review_ref,'preflight_ref':review_ref,'pipe_name':'synthetic-pipe',
    'actual_game':launch_ref,'mod_absence':proof_ref,'environment_manifest':manifest_ref,'root_review_ref':review_ref,'expected_lifecycle':expected}
def install(value):
    ref=write('bindings.json',value)
    for key,value in [('PATH',ref['path']),('BYTES',str(ref['bytes'])),('SHA256',ref['sha256'])]: os.environ['XAR_ROOT_COLD_BINDINGS_'+key]=value
def rejected(action):
    try: action()
    except (ValueError,KeyError): return
    raise AssertionError('actual emitted transport accepted a negative vector')
def invoke(): return entry['bind_clean_lifecycle'](manifest,lifecycle='ordinary_campaign_succession',ordinary_campaign_no_pact=True)
install(sidecar);before={p:p.read_bytes() for p in [root/'bindings.json',root/'proof.json',root/'launch.json']}
assert invoke()==expected and calls==1 and all(p.read_bytes()==raw for p,raw in before.items())
rejected(lambda:entry['bind_clean_lifecycle']({**manifest,'fixture_integer':True},lifecycle='ordinary_campaign_succession',ordinary_campaign_no_pact=True))
wrong={**sidecar,'mod_absence':{**proof_ref,'sha256':'f'*64}};install(wrong);rejected(invoke)
wrong_proof={**proof,'game_creation_filetime_decimal':'18446744073709551614'}
install({**sidecar,'mod_absence':write('wrong-proof.json',wrong_proof)});rejected(invoke)
wrong_proof={**proof,'game_creation_filetime_decimal':True}
install({**sidecar,'mod_absence':write('bool-proof.json',wrong_proof)});rejected(invoke)
del os.environ['XAR_ROOT_COLD_BINDINGS_PATH'];rejected(invoke)
assert calls==1
print(json.dumps({'cases':6,'original_sdk_calls':calls},separators=(',',':')))
""";
}
