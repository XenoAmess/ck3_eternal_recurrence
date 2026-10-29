package org.xar.ck3.control.wave2.events.mandatoryreceipt;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Shared-Job explicit producer capture. Original writes execute only inside bounded task scratch. */
public final class MandatoryReceiptGoldenCapture {
    private MandatoryReceiptGoldenCapture() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repository new_output existing_python required"); }
        Path root = Path.of(arguments[0]).toAbsolutePath().normalize(); Path output = Path.of(arguments[1]).toAbsolutePath().normalize();
        Path scratch = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        if (!output.startsWith(scratch.getParent().resolve("logs")) || Files.exists(output)) { throw new IllegalArgumentException("new task-local output required"); }
        Files.createDirectories(output.getParent());
        String script = """
import sys,json,copy,runpy,hashlib,datetime,tempfile
from pathlib import Path
r=Path(sys.argv[1]); output=Path(sys.argv[2]); scratch=Path(sys.argv[3]); sys.path.insert(0,str(r/'ck3_autonomous_player/src'))
t=runpy.run_path(str(r/'ck3_autonomous_player/tests/unit/test_mandatory_choice_evidence_v1.py'))
from xar_autoplayer.mandatory_choice_evidence_v1 import capture_before,capture_after
base={'accepted':True,'mandatory_choice_postcondition':{'verified':True,'old_window_id':'w1','old_instance':'i1','selected_choice_id':'c1','old_window_no_longer_blocking':True}}
cases=[]
with tempfile.TemporaryDirectory(prefix='mandatory-after-capture-',dir=scratch) as temporary:
    def emit(name,outcome=None,error=None):
        ticket=capture_before(Path(temporary)/name,t['planned']())
        receipt=capture_after(ticket,outcome=outcome,error=error)
        after=json.loads(Path(receipt['after']['path']).read_bytes())
        request={'schema':'xar.java-mandatory-choice-after-response-request/v1','ticket':copy.deepcopy(ticket),'outcome':copy.deepcopy(outcome),'error':copy.deepcopy(after['error']),'captured_at_utc':after['captured_at_utc']}
        cases.append({'name':name,'request':request,'output':after})
    emit('actual_complete_original_window_proof',{'result':copy.deepcopy(base)})
    emit('ack_only',{'result':{'accepted':True}})
    emit('missing_result',{})
    emit('missing_outcome')
    for name,field,value in [('post_unverified','verified',False),('wrong_window','old_window_id','w2'),('wrong_instance','old_instance','i2'),('wrong_choice','selected_choice_id','c2'),('same_window_still_blocking','old_window_no_longer_blocking',False)]:
        result=copy.deepcopy(base); result['mandatory_choice_postcondition'][field]=value; emit(name,{'result':result})
    result=copy.deepcopy(base); result['accepted']=False; emit('native_not_accepted',{'result':result})
    result=copy.deepcopy(base); result['mandatory_choice_postcondition'].pop('selected_choice_id'); emit('missing_original_choice_identity',{'result':result})
    emit('malformed_result_array_retained_diagnostic',{'result':[]})
    emit('explicit_null_result',{'result':None})
    error=ValueError('unsettled native result'); error.mandatory_choice_raw_receipt={'request_id':'original-request','claim_path':'original.claim.json','native_result_path':None}; emit('unknown_error_keeps_original_claim',error=error)
    emit('error_and_original_response_remain_separate',{'result':copy.deepcopy(base)},ValueError('consumer failed after response'))
paths=['ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_evidence_v1.py','ck3_autonomous_player/tests/unit/test_mandatory_choice_evidence_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py']
body={'schema':'xar.java-mandatory-receipt-golden/v1','provenance':{'machine_id':'xenoamess-full-tower-eb9d2c1186','captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'actual unmodified capture_before/capture_after write/read in temporary D fixture paths; no Game/ledger; fixture originals removed on scope exit','sources':[{'path':p,'sha256':hashlib.sha256((r/p).read_bytes()).hexdigest()} for p in paths]},'cases':cases}
raw=(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
if len(raw)>65536: raise RuntimeError('receipt golden exceeds 64 KiB')
with output.open('xb') as handle: handle.write(raw)
print(json.dumps({'cases':len(cases),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'output':str(output)}))
""";
        ProcessBuilder builder = new ProcessBuilder(arguments[2], "-c", script, root.toString(), output.toString(), scratch.toString());
        builder.directory(root.toFile()); builder.redirectErrorStream(true);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("TEMP", scratch.toString()); builder.environment().put("TMP", scratch.toString());
        Process process = builder.start();
        if (!process.waitFor(75, TimeUnit.SECONDS)) {
            process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("mandatory receipt capture timeout");
        }
        System.out.print(new String(process.getInputStream().readNBytes(16_384), StandardCharsets.UTF_8));
        if (process.exitValue() != 0 || !Files.isRegularFile(output) || Files.size(output) > 65_536) {
            throw new IllegalStateException("actual receipt producer capture failed with exit " + process.exitValue());
        }
    }
}
