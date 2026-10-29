package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit shared-Job capture of unmodified Python stable_source_key, never part of default JUnit. */
public final class UiRecoveryIdentityGoldenCapture {
    private UiRecoveryIdentityGoldenCapture() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repository new_output existing_python required"); }
        Path root = Path.of(arguments[0]).toAbsolutePath().normalize(); Path output = Path.of(arguments[1]).toAbsolutePath().normalize();
        Path logs = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize().getParent().resolve("logs");
        if (!output.startsWith(logs) || Files.exists(output)) { throw new IllegalArgumentException("new task-local capture output required"); }
        Files.createDirectories(output.getParent());
        String script = """
import sys,json,copy,runpy,hashlib,datetime
from pathlib import Path
r=Path(sys.argv[1]); p=Path(sys.argv[2]); sys.path.insert(0,str(r/'ck3_autonomous_player/src'))
t=runpy.run_path(str(r/'ck3_autonomous_player/tests/unit/test_mandatory_choice_offline_analysis_v1.py'))
from xar_autoplayer.mandatory_choice_offline_analysis_v1 import stable_source_key
b=t['pair']()[0]['native_window']; backend=t['BACKEND_SHA']; cases=[]
def emit(name,window,sha=backend):
    request={'schema':'xar.java-ui-recovery-source-key-request/v1','window':copy.deepcopy(window),'backend_sha256':sha}
    cases.append({'name':name,'request':request,'output':stable_source_key(window,backend_sha256=sha)})
emit('existing_symbolic_rva_producer',copy.deepcopy(b))
d=copy.deepcopy(b); d['window_instance_id']='changed-pointer'; d['choices'][0]['action_token']='changed-token'; d['choices'][0]['bounds']['left']=900; d['choices'][0]['choice_id']='new-id'; d['stable_source_identity']['choice_catalogue'][0]['choice_id']='new-id'; emit('nonce_pointer_rect_and_live_id_excluded',d)
d=copy.deepcopy(b); d['stable_source_identity']['choice_catalogue'][0]['callback_identities'][0]['function_module_rva']='ck3.exe+0xac'; emit('callback_changes_source_key',d)
emit('missing_backend_sha',copy.deepcopy(b),None)
native=json.loads((r/'ck3_autonomous_player/tests/fixtures/mandatory_choice_v1/native-query.json').read_bytes())['result']['mandatory_choice']; emit('native_numeric_rva_parallel_catalogue',copy.deepcopy(native))
for name,value in [('zero_rva',0),('negative_rva',-1),('float_rva',1.0),('bool_rva',True),('maximum_uint64_rva',2**64-1),('overflow_uint64_rva',2**64)]:
    d=copy.deepcopy(b); d['stable_source_identity']['root_vtable_module_rva']=value; emit(name,d)
d=copy.deepcopy(b); d['stable_source_identity']['backend_sha256']=backend.upper(); emit('matching_backend_case_normalized',d,backend.upper())
d=copy.deepcopy(b); d['stable_source_identity']['backend_sha256']='c'*64; emit('backend_mismatch',d)
d=copy.deepcopy(b); d['choices'].append(copy.deepcopy(d['choices'][0])); d['stable_source_identity']['choice_catalogue'].append(copy.deepcopy(d['stable_source_identity']['choice_catalogue'][0])); emit('duplicate_display_identity',d)
d=copy.deepcopy(b); d['stable_source_identity']['choice_catalogue']=[]; emit('catalogue_length_mismatch',d)
d=copy.deepcopy(native); d['stable_source_identity']={}; emit('empty_stable_identity_uses_source_identity',d)
d=copy.deepcopy(native); d['stable_source_identity']='unusable-nonempty'; emit('truthy_bad_stable_identity_not_fallback',d)
d=copy.deepcopy(b); d['choices'][0].pop('label'); d['stable_source_identity']['choice_catalogue'][0]['role']=None; emit('missing_label_and_null_catalogue_role',d)
d=copy.deepcopy(b); d['choices'][0]['label']='陌生标签 😀\\n'; d['stable_source_identity']['root_runtime_name']='名\\"称\\\\'; emit('unicode_and_control_canonical_bytes',d)
d=copy.deepcopy(native); d['source_identity']['choice_catalogue'][0]['callback_identities'].append({'vtable_module_rva':9,'function_module_rva':1}); d['source_identity']['choice_catalogue'][0]['callback_identities'].reverse(); emit('callbacks_canonical_order',d)
sources=['ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_offline_analysis_v1.py','ck3_autonomous_player/tests/unit/test_mandatory_choice_offline_analysis_v1.py','ck3_autonomous_player/tests/fixtures/mandatory_choice_v1/native-query.json']
body={'schema':'xar.java-ui-recovery-identity-golden/v1','provenance':{'machine_id':'xenoamess-full-tower-eb9d2c1186','captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'actual unmodified Python stable_source_key calls; offline fixture only, no observed-effect qualification','sources':[{'path':x,'sha256':hashlib.sha256((r/x).read_bytes()).hexdigest()} for x in sources]},'cases':cases}
raw=(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
if len(raw)>65536: raise RuntimeError('identity golden exceeds 64 KiB')
with p.open('xb') as handle: handle.write(raw)
print(json.dumps({'cases':len(cases),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'output':str(p)}))
""";
        ProcessBuilder builder = new ProcessBuilder(arguments[2], "-c", script, root.toString(), output.toString());
        builder.directory(root.toFile()); builder.redirectErrorStream(true); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        if (!process.waitFor(75, TimeUnit.SECONDS)) {
            process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("source key capture timeout");
        }
        System.out.print(new String(process.getInputStream().readNBytes(16_384), StandardCharsets.UTF_8));
        if (process.exitValue() != 0 || !Files.isRegularFile(output) || Files.size(output) > 65_536) {
            throw new IllegalStateException("actual source key capture failed with exit " + process.exitValue());
        }
    }
}
