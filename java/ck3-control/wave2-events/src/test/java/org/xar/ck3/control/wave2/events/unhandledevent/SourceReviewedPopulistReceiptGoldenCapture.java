package org.xar.ck3.control.wave2.events.unhandledevent;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;

/** Captures the original response comparator against the existing counterfactual fixture; no Game or native call. */
public final class SourceReviewedPopulistReceiptGoldenCapture {
    private SourceReviewedPopulistReceiptGoldenCapture() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("repository Python output required");
        Path repository = Path.of(args[0]).toAbsolutePath(), output = Path.of(args[2]).toAbsolutePath();
        Process machine = new ProcessBuilder(args[1], repository.resolve("tools/ck3_live_run_id.py").toString(), "machine")
                .directory(repository.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] identity = machine.getInputStream().readNBytes(4097);
        if (!machine.waitFor(30, java.util.concurrent.TimeUnit.SECONDS) || machine.exitValue() != 0 || identity.length > 4096)
            throw new IOException("actual machine identity unavailable");
        String machineId = new String(identity, StandardCharsets.UTF_8).strip();
        if (!machineId.matches("[a-z0-9][a-z0-9-]{0,63}") || machineId.equals("unknown")) throw new IOException("malformed machine identity");
        Process process = new ProcessBuilder(List.of(args[1], "-", repository.toString(), machineId))
                .directory(repository.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        try {
            try (var input = process.getOutputStream()) { input.write(CAPTURE.getBytes(StandardCharsets.UTF_8)); }
            byte[] packed = process.getInputStream().readNBytes(65_537);
            if (!process.waitFor(60, java.util.concurrent.TimeUnit.SECONDS) || process.exitValue() != 0 || packed.length > 65_536)
                throw new IOException("original populist receipt capture failed or exceeded bound");
            Files.write(output, packed, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            if (!java.util.Arrays.equals(packed, Files.readAllBytes(output))) throw new IOException("capture readback differs");
        } finally { if (process.isAlive()) process.destroyForcibly(); }
    }
    private static final String CAPTURE = """
from pathlib import Path
from datetime import datetime,timezone
import copy,gzip,hashlib,json,sys,tempfile
root,machine=Path(sys.argv[1]),sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
from xar_autoplayer.vanilla_events.populist1001_known_refusal_v1 import choose_source_reviewed_populist_refusal_v1,verify_source_reviewed_populist_refusal_result_v1
from xar_autoplayer.vanilla_events.unhandled_fallback import capture_unhandled_event_before_v1,capture_unhandled_event_after_v1
fixture_path=root/'ck3_autonomous_player/tests/unit/fixtures/event72_populist_actual518_source_reviewed.json'
fixture=json.loads(fixture_path.read_bytes())
plan=choose_source_reviewed_populist_refusal_v1(copy.deepcopy(fixture['plan']),snapshot=fixture['snapshot'],action_steps=('select-event-option-3','select-event-option-4'))
if plan.get('phase')!='active_event_source_reviewed_populist_refusal':raise RuntimeError('original reviewed policy did not select refusal')
body={**copy.deepcopy(fixture['counterfactual_refusal_receipt']),'plan':plan}
with tempfile.TemporaryDirectory(prefix='java-populist-receipt-') as temporary:
    ticket=capture_unhandled_event_before_v1(Path(temporary),{'plan':plan,'snapshot_id':fixture['snapshot']['snapshot_id'],'revision':fixture['snapshot']['revision']})
    body['unhandled_event_fallback_evidence']=capture_unhandled_event_after_v1(ticket,outcome=body)
    rows=[]
    def retain(name,value):
        try:expected=verify_source_reviewed_populist_refusal_result_v1(value);rows.append({'name':name,'body':value,'expected':expected,'rejected':False})
        except ValueError as error:rows.append({'name':name,'body':value,'rejected':True,'error':str(error)})
    retain('original-counterfactual-receipt',copy.deepcopy(body))
    for name in ('accepted','postcondition','old-instance','native-index','capture-index','ending-revision','source-fingerprint','missing-after'):
        changed=copy.deepcopy(body);inner=changed['result'];post=inner['event_selection'];capture=changed['plan']['unhandled_event_fallback']
        if name=='accepted':inner['accepted']=False
        elif name=='postcondition':post['postcondition_verified']=False
        elif name=='old-instance':post['old_event_instance_id']+=1
        elif name=='native-index':post['selected_native_option_index']=2
        elif name=='capture-index':capture['selection']['native_option_index']=2
        elif name=='ending-revision':post['ending_revision']=post['starting_revision']
        elif name=='source-fingerprint':capture['source_knowledge']['fingerprint']='0'*64
        else:changed['unhandled_event_fallback_evidence'].pop('after')
        retain(name,changed)
    retain('other-plan',{'plan':{'phase':'other'}});retain('null',None)
paths=['ck3_autonomous_player/src/xar_autoplayer/vanilla_events/populist1001_known_refusal_v1.py','ck3_autonomous_player/src/xar_autoplayer/vanilla_events/unhandled_fallback.py','ck3_autonomous_player/tests/unit/fixtures/event72_populist_actual518_source_reviewed.json']
result={'schema':'xar.source-reviewed-populist-receipt-golden/v1','machine_id':machine,'captured_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'actual original Python response comparator and before/after producer, existing counterfactual receipt fixture; no Game/native/business-success claim','producer_refs':[{'path':p,'bytes':(root/p).stat().st_size,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths],'cases':rows}
raw=json.dumps(result,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
if len(raw)>1048576:raise RuntimeError('receipt decompressed bound')
sys.stdout.buffer.write(gzip.compress(raw,compresslevel=9,mtime=0))
""";
}
