package org.xar.ck3.control.wave2.events.mandatorybefore;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit bounded original before-writer capture; never invoked by default JUnit. */
public final class MandatoryBeforeGoldenCapture {
    private MandatoryBeforeGoldenCapture() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repository new_output existing_python required"); }
        Path root = Path.of(arguments[0]).toAbsolutePath().normalize(); Path output = Path.of(arguments[1]).toAbsolutePath().normalize();
        Path scratch = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        if (!output.startsWith(scratch.getParent().resolve("logs")) || Files.exists(output)) { throw new IllegalArgumentException("new task-local output required"); }
        Files.createDirectories(output.getParent());
        String script = """
import sys,json,copy,runpy,hashlib,datetime,tempfile,gzip
from pathlib import Path
r=Path(sys.argv[1]); output=Path(sys.argv[2]); scratch=Path(sys.argv[3]); sys.path.insert(0,str(r/'ck3_autonomous_player/src'))
t=runpy.run_path(str(r/'ck3_autonomous_player/tests/unit/test_mandatory_choice_planning_v1.py'))
from xar_autoplayer.mandatory_choice_planning_v1 import plan_native_mandatory_choice_v1,QUERY_STEP,QUERY_CAPABILITY
from xar_autoplayer.mandatory_choice_evidence_v1 import capture_before
snap=t['snapshot'](); plan=plan_native_mandatory_choice_v1([t['query_row']()],snapshot=snap,action_steps=[QUERY_STEP],bridge_capabilities=[QUERY_CAPABILITY])
base={'snapshot_id':snap['snapshot_id'],'revision':snap['revision'],'plan':plan}; cases=[]
with tempfile.TemporaryDirectory(prefix='mandatory-before-capture-',dir=scratch) as temporary:
    def emit(name,planned):
        body=None; rejected=False
        try:
            ticket=capture_before(Path(temporary)/name,planned); body=json.loads(Path(ticket['before']['path']).read_bytes())
        except ValueError:
            rejected=True
        request={'schema':'xar.java-mandatory-choice-before-body-request/v1','planned':copy.deepcopy(planned),'incident_id':body['incident_id'] if body else 'fixture-rejected-no-incident','captured_at_utc':body['captured_at_utc'] if body else '2026-10-22T00:00:00Z'}
        cases.append({'name':name,'request':request,'rejected':rejected,'output':body})
    emit('actual_planner_to_before_writer',copy.deepcopy(base))
    d=copy.deepcopy(base); d['plan']['unknown_mandatory_choice_v1']['fixture_extension']={'bounded':[]}; emit('capture_extension_retained',d)
    d=copy.deepcopy(base); d['snapshot_id']='stale'; emit('stale_public_snapshot',d)
    d=copy.deepcopy(base); d['revision']+=1; emit('stale_public_revision',d)
    d=copy.deepcopy(base); d['plan']['selected_step']='different-step'; emit('wrong_selected_step',d)
    for name,field in [('missing_blocking_proof','blocking_proof_verified'),('incomplete_catalogue','catalogue_complete')]:
        d=copy.deepcopy(base); d['plan']['unknown_mandatory_choice_v1'][field]=False; emit(name,d)
    d=copy.deepcopy(base); d['plan']['unknown_mandatory_choice_v1']['native_window']['blocking_proof']['verified']=False; emit('native_proof_unverified',d)
    d=copy.deepcopy(base); d['plan']['unknown_mandatory_choice_v1']['native_window']['choices_complete']=False; emit('native_catalogue_incomplete',d)
    for name,field in [('selected_disabled','enabled'),('selected_not_choice','is_choice')]:
        d=copy.deepcopy(base); d['plan']['unknown_mandatory_choice_v1']['native_window']['choices'][3][field]=False; emit(name,d)
    d=copy.deepcopy(base); d['plan']['unknown_mandatory_choice_v1']['selection']['action_token']='different-original-token'; emit('token_changed',d)
    d=copy.deepcopy(base); choices=d['plan']['unknown_mandatory_choice_v1']['native_window']['choices']; choices.append(copy.deepcopy(choices[3])); emit('duplicate_selected_original_row',d)
    d=copy.deepcopy(base); d['plan']['unknown_mandatory_choice_v1']['native_window']['frame_binding']['revision']+=1; emit('native_frame_changed',d)
paths=['ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_planning_v1.py','ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_policy_v1.py','ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_evidence_v1.py','ck3_autonomous_player/tests/unit/test_mandatory_choice_planning_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py']
body={'schema':'xar.java-mandatory-before-golden/v1','provenance':{'machine_id':'xenoamess-full-tower-eb9d2c1186','captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'actual unchanged planner to capture_before write/read; temporary D fixture originals removed after scope; no Game/ledger','sources':[{'path':p,'sha256':hashlib.sha256((r/p).read_bytes()).hexdigest()} for p in paths]},'cases':cases}
raw=(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
if len(raw)>524288: raise RuntimeError('full before golden exceeds 512 KiB decompression cap')
packed=gzip.compress(raw,compresslevel=9,mtime=0)
if len(packed)>98304: raise RuntimeError('compressed before golden exceeds 96 KiB output cap')
with output.open('xb') as handle: handle.write(packed)
print(json.dumps({'cases':len(cases),'raw_bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(packed),'sha256':hashlib.sha256(packed).hexdigest(),'output':str(output)}))
""";
        ProcessBuilder builder = new ProcessBuilder(arguments[2], "-", root.toString(), output.toString(), scratch.toString());
        builder.directory(root.toFile()); builder.redirectErrorStream(true); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("TEMP", scratch.toString()); builder.environment().put("TMP", scratch.toString());
        Process process = builder.start();
        try (var input = process.getOutputStream()) { input.write(script.getBytes(StandardCharsets.UTF_8)); }
        if (!process.waitFor(75, TimeUnit.SECONDS)) {
            process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("before-body capture timeout");
        }
        System.out.print(new String(process.getInputStream().readNBytes(16_384), StandardCharsets.UTF_8));
        if (process.exitValue() != 0 || !Files.isRegularFile(output) || Files.size(output) > 98_304) {
            throw new IllegalStateException("actual before-body capture failed with exit " + process.exitValue());
        }
    }
}
