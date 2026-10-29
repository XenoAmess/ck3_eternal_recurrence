package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;

/** Bounded original producer fixture capture; never a game launch or gameplay receipt. */
public final class ObservedUiRecoveryGoldenCapture {
    private ObservedUiRecoveryGoldenCapture() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("repository Python output required");
        Path repository = Path.of(args[0]).toAbsolutePath(); Path output = Path.of(args[2]).toAbsolutePath();
        Process machine = new ProcessBuilder(args[1], repository.resolve("tools/ck3_live_run_id.py").toString(), "machine")
                .directory(repository.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] identity = machine.getInputStream().readNBytes(4097);
        if (!machine.waitFor(30, java.util.concurrent.TimeUnit.SECONDS) || machine.exitValue() != 0 || identity.length > 4096)
            throw new IOException("actual machine identity unavailable");
        String machineId = new String(identity, StandardCharsets.UTF_8).strip();
        if (!machineId.matches("[a-z0-9][a-z0-9-]{0,63}") || machineId.equals("unknown")) throw new IOException("machine identity malformed");
        List<String> command = new ArrayList<>(List.of(args[1], "-", repository.toString(), machineId));
        Process process = new ProcessBuilder(command).directory(repository.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        try {
            try (var input = process.getOutputStream()) { input.write(CAPTURE.getBytes(StandardCharsets.UTF_8)); }
            byte[] packed = process.getInputStream().readNBytes(65_537);
            if (!process.waitFor(60, java.util.concurrent.TimeUnit.SECONDS) || process.exitValue() != 0 || packed.length > 65_536)
                throw new IOException("original UI knowledge capture failed or exceeded bound");
            Files.write(output, packed, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            if (!java.util.Arrays.equals(packed, Files.readAllBytes(output))) throw new IOException("capture output readback differs");
        } finally { if (process.isAlive()) process.destroyForcibly(); }
    }

    private static final String CAPTURE = """
from pathlib import Path
from datetime import datetime, timezone
import base64, copy, gzip, hashlib, importlib.util, json, sys, tempfile
root,machine=Path(sys.argv[1]),sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
import test_mandatory_choice_offline_analysis_v1 as evidence_fixture
import test_mandatory_choice_planning_v1 as planning_fixture
from xar_autoplayer import mandatory_choice_offline_analysis_v1 as original
from xar_autoplayer.mandatory_choice_planning_v1 import plan_native_mandatory_choice_v1
spec=importlib.util.spec_from_file_location('original_mandatory_worker',root/'ck3_autonomous_player/offline_mandatory_choice_worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
blobs={};cases=[]
def retain(path,base,role):
    raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if len(raw)>1048576:raise RuntimeError('original UI evidence file exceeds bound')
    blobs[sha]=base64.b64encode(raw).decode('ascii')
    return {'path':str(path),'relative':path.relative_to(base).as_posix(),'bytes':len(raw),'sha256':sha,'role':role,'origin_machine_id':machine}
with tempfile.TemporaryDirectory(prefix='java-observed-ui-') as temporary:
    base=Path(temporary)
    historical=base/'historical-attempt';incidents=historical/'state/evidence/unknown-mandatory-choices';incidents.mkdir(parents=True)
    before,after=evidence_fixture.pair()
    before.update(schema='xar.unknown-mandatory-choice-incident/v1',captured_at_utc='2026-10-15T08:00:00+00:00')
    after.update(schema='xar.unknown-mandatory-choice-incident/v1',captured_at_utc='2026-10-15T08:00:01+00:00')
    first=incidents/'incident-1.before.json';first.write_text(json.dumps(before),encoding='utf-8')
    after['before']={'sha256':hashlib.sha256(first.read_bytes()).hexdigest()}
    last=incidents/'incident-1.after.json';last.write_text(json.dumps(after),encoding='utf-8')
    launch=historical/'ROOT-ACTUAL-GAME-LAUNCH.json';launch.write_text(json.dumps({'machine_id':machine,'pid':555,'dll_sha256':evidence_fixture.BACKEND_SHA}),encoding='utf-8')
    responses=historical/'p01-responses';responses.mkdir()
    later={**before['frame_binding'],'date_raw':53112346,'native_revision':101};later.pop('game_pid')
    later_path=responses/'0002-1-result.json';later_path.write_text(json.dumps({'ended_at_utc':'2026-10-15T08:00:02+00:00','result':{'is_error':False,'structured_content':later}}),encoding='utf-8')
    originals=[retain(launch,base,'UI_RECOVERY_LAUNCH'),retain(first,base,'UI_RECOVERY_BEFORE'),retain(last,base,'UI_RECOVERY_AFTER'),retain(later_path,base,'UI_RECOVERY_LATER')]
    for pid in (555,556):
        attempt=base/('current-'+str(pid));state=attempt/'state';state.mkdir(parents=True)
        current_launch=attempt/'ROOT-ACTUAL-GAME-LAUNCH.json';current_launch.write_text(json.dumps({'machine_id':machine,'pid':pid,'dll_sha256':evidence_fixture.BACKEND_SHA}),encoding='utf-8')
        review_root=state/'evidence/unknown-mandatory-choice-reviews'
        records=worker.review_once(historical,review_root)
        if len(records)!=1 or records[0]['status']!='known_ui_recovery_observed':raise RuntimeError('actual original worker did not publish source-bound knowledge')
        worker_review_path=Path(records[0]['review'])
        dto=planning_fixture.dto();dto['choices']=[{**copy.deepcopy(before['native_window']['choices'][0]),'action_token':'fresh-instance-token','visible':True,'enabled':True,'is_choice':True}]
        dto['stable_source_identity']=copy.deepcopy(before['native_window']['stable_source_identity'])
        dto['window_instance_id']='fresh-instance-'+str(pid);dto['frame_binding']['game_pid']=pid
        snapshot=planning_fixture.snapshot();snapshot['diagnostics']['bridge_pid']=pid
        row=planning_fixture.query_row(dto)
        expected=plan_native_mandatory_choice_v1([row],snapshot=snapshot,action_steps=[planning_fixture.QUERY_STEP],bridge_capabilities=[planning_fixture.QUERY_CAPABILITY],known_review_root=review_root,backend_sha256=evidence_fixture.BACKEND_SHA)
        if expected['phase']!='known_observed_ui_recovery_first_enabled':raise RuntimeError('actual old planner failed historical source lookup')
        review_path=Path(expected['known_ui_recovery_source']['review_path'])
        files=originals+[retain(current_launch,base,'UI_RECOVERY_LAUNCH'),retain(worker_review_path,base,'worker-review'),retain(review_path,base,'review')]
        cases.append({'name':'same-pid' if pid==555 else 'historical-different-pid','state_relative':state.relative_to(base).as_posix(),'review_path':str(review_path),'worker_review_path':str(worker_review_path),'files':files,
            'request':{'schema':'xar.java-mandatory-choice-planning-request/v1','snapshot':snapshot,'commands':[row],'action_steps':[planning_fixture.QUERY_STEP],'bridge_capabilities':[planning_fixture.QUERY_CAPABILITY]},'expected':expected})
paths=['ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_offline_analysis_v1.py','ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_planning_v1.py','ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_policy_v1.py','ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_evidence_v1.py','ck3_autonomous_player/offline_mandatory_choice_worker.py','ck3_autonomous_player/tests/unit/test_mandatory_choice_offline_analysis_v1.py','ck3_autonomous_player/tests/unit/test_mandatory_choice_planning_v1.py']
record={'schema':'xar.observed-ui-recovery-producer-golden/v1','machine_id':machine,'captured_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'actual original worker, lookup, planner; synthetic immutable game evidence; no Game/native authority','producer_refs':[{'path':p,'bytes':(root/p).stat().st_size,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths],'cases':cases,'blobs':blobs}
raw=json.dumps(record,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
if len(raw)>1048576:raise RuntimeError('UI producer decompressed bound')
sys.stdout.buffer.write(gzip.compress(raw,compresslevel=9,mtime=0))
""";
}
