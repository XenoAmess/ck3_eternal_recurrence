package org.xar.ck3.control.wave3.planning.peacetimescope;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/** Explicit shared-owner sizing capture, never invoked by default tests or production. */
public final class CaptureJointInventoryProfile {
    private CaptureJointInventoryProfile() { }
    private static final int MAXIMUM_BYTES = 16384;
    private static final String SCRIPT = """
import sys,json,hashlib,datetime,copy
from pathlib import Path
root=Path(sys.argv[1]);original=Path(sys.argv[2])
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
from xar_autoplayer.m5_joint_intake import build_m5_same_frame_intake
from xar_autoplayer.m5_joint_shortlist import compare_m5_joint_shortlist
from xar_autoplayer.m5_joint_budget_selector import select_m5_assessed_candidate
from test_m5_joint_intake import _frame,_war_query
raw=original.read_bytes()
if len(raw)>1048576:raise ValueError('retained input exceeds finite size allowance')
family=json.loads(raw)
if hashlib.sha256(raw).hexdigest()!='d7c3fe9bc820983be6e747a2415dcddc69f4fd5a10e88d65dc4543759a8b698a':raise ValueError('retained input pin drift')
before=_frame();after=copy.deepcopy(before);wars=_war_query()
intake_args=dict(before=before,after=after,first_heir_legality=family,declarable_war_query=wars)
intake=build_m5_same_frame_intake(**intake_args)
selector_args=dict(intake=intake,snapshot=before,assessments=[],commitments={},gold_reserve_raw=0,max_active_wars=0)
selector=select_m5_assessed_candidate(**selector_args)
shortlist_args=dict(snapshot=before,intake=intake,observed_proposals=[],assessments=[],marriage_projection=None,war_current=None,existing_commitments={},gold_reserve_raw=0,max_active_wars=0)
shortlist=compare_m5_joint_shortlist(**shortlist_args)
def encoded(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
def measure(name,value):
 data=encoded(value);return dict(name=name,compact_json_bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
refs=[]
for relative in ['ck3_autonomous_player/src/xar_autoplayer/m5_joint_intake.py','ck3_autonomous_player/src/xar_autoplayer/m5_joint_shortlist.py','ck3_autonomous_player/src/xar_autoplayer/m5_joint_budget_selector.py','ck3_autonomous_player/src/xar_autoplayer/m5_joint_dispatch.py','ck3_autonomous_player/tests/unit/test_m5_joint_intake.py']:
 data=(root/relative).read_bytes();refs.append(dict(path=relative,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
shapes=[]
for name,rows in [('retained_candidates',family['candidates']),('retained_final_legal_candidates',family['native_legal_candidates']),('intake_candidates',intake['candidates']),('shortlist_unpriced_candidates',shortlist['unpriced_candidates'])]:
 shapes.append(dict(name=name,count=len(rows),row_fields=list(rows[0]) if rows else [],first_row_bytes=len(encoded(rows[0])) if rows else 0,all_rows_bytes=len(encoded(rows))))
out=dict(schema='xar.ck3.java-m5-inventory-size-profile.v1',machine_id='xenoamess-full-tower-eb9d2c1186',observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),evidence_scope='Actual unchanged Python producers executed for byte sizing only. Retained 657 family rows are composed with existing synthetic test frame and synthetic one-war query. This is not original same-episode intake, native qualification, production switching, performance or saved-day evidence.',source_machine_id='unknown',retained_input=dict(path=str(original),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),exact_ck3_build=family['exact_ck3_build']),synthetic_inputs=dict(frame_source='test_m5_joint_intake._frame',war_source='test_m5_joint_intake._war_query',priced_assessments=0),sources=refs,measurements=[measure('retained_json_compact',family),measure('intake_wrapper',intake_args),measure('intake_output',intake),measure('selector_wrapper',selector_args),measure('selector_output',selector),measure('shortlist_wrapper',shortlist_args),measure('shortlist_output',shortlist)],shapes=shapes,existing_profiles=dict(jointbudget_wrapper_bytes=65536,jointshortlist_wrapper_bytes=65536,jointshortlist_output_bytes=65536,jointintake_wrapper_bytes=131072),conclusion='Compare measured wrappers and output against their individual profiles. Do not globally raise a shared parser guard or make unused shortlist an active production precondition.')
sys.stdout.buffer.write(encoded(out))
""";

    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("repository, existing Python, retained original, new output required"); }
        Path output = Path.of(args[3]); if (Files.exists(output)) { throw new IOException("new output required"); }
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-c", SCRIPT, args[0], args[2]);
        builder.directory(Path.of(args[0]).toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); Process process = builder.start();
        CompletableFuture<byte[]> read = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readNBytes(MAXIMUM_BYTES + 1); }
            catch (IOException error) { throw new java.io.UncheckedIOException(error); }
        });
        if (!process.waitFor(60, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("size capture timeout"); }
        byte[] raw = read.get(10, TimeUnit.SECONDS);
        if (process.exitValue() != 0 || raw.length == 0 || raw.length > MAXIMUM_BYTES) { throw new IOException("original sizing failed or exceeded allowance"); }
        Files.write(output, raw, StandardOpenOption.CREATE_NEW); System.out.println("Captured size profile: " + raw.length + " bytes");
    }
}
