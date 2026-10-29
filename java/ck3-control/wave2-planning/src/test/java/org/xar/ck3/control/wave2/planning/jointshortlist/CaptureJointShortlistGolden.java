package org.xar.ck3.control.wave2.planning.jointshortlist;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/** Explicit one-shot capture. Default JUnit uses the committed capture and never starts Python. */
public final class CaptureJointShortlistGolden {
    private CaptureJointShortlistGolden() { }
    private static final int MAXIMUM_BYTES = 114_688;
    private static final String SCRIPT = """
import sys,json,hashlib,datetime,importlib.util,copy
from pathlib import Path
root=Path(sys.argv[1])
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
spec=importlib.util.spec_from_file_location('legacy_shortlist_test',root/'ck3_autonomous_player/tests/unit/test_m5_joint_shortlist.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from xar_autoplayer.m5_joint_shortlist import compare_m5_joint_shortlist
cases=[]
def capture(name,args):
 item={'name':name,'input':args}
 try:
  result=compare_m5_joint_shortlist(**args)
  projection={key:result[key] for key in ('frame','legal_candidate_count','priced_candidate_count','unpriced_candidates','current_war_resources')}
  projection.update(phase='fewer_than_five_priced_legal_candidates' if len(args['assessments'])<5 else 'assessed_comparison_prepared',analysis=result.get('analysis'),reservation_created=False,selected_step=None,formal_action_ready=False)
  item.update(expected_preparation=projection,projection_not_original=True,original_result_sha256=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest())
 except ValueError as error: item.update(rejected=True,legacy_error=str(error))
 cases.append(item)
def family():
 a=m._args();a['assessments']=[m._quote(row,benefit=index+2) for index,row in enumerate(a['intake']['candidates'][:5])];return a
def gift():
 a=family();p=a['observed_proposals'][0];q=m._quote(p,benefit=10);q.update(gold_raw=p['gold_cost_raw'],character_ids=p['character_ids'],commitment_keys=p['commitment_keys']);a['assessments'].append(q);return a
capture('unpriced-specific-observation-gaps',m._args())
capture('five-valued-family-rows',family())
capture('six-valued-rows-gift-wins',gift())
a=gift();a['existing_commitments']['character_ids']=[41003];capture('gift-already-occupied-family-wins',a)
a=family();war=m._quote(a['intake']['candidates'][5],benefit=20);war.update(gold_raw=7000000,projected_supply_margin_units=100000,army_ids=[71]);a['assessments'].append(war);a['max_active_wars']=2;capture('priced-war-current-readback',a)
a=m._args();a['assessments']=[m._quote(a['intake']['candidates'][0],benefit=3)];a['marriage_projection']=None;capture('under-five-still-requires-priced-family-readback',a)
a=family();a['assessments'].append(m._quote(a['intake']['candidates'][5],benefit=20));a['war_current']['m5_war_primary_current']['current_treasury']['raw']+=1;capture('priced-war-treasury-drift-rejected',a)
a=family();a['assessments'][0]['common_value_policy']='different-value-scale';capture('mixed-common-value-scales-rejected',a)
a=gift();a['assessments'][-1]['gold_raw']=0;capture('observed-shared-claim-drift-rejected',a)
refs=[]
for relative in ['ck3_autonomous_player/src/xar_autoplayer/m5_joint_shortlist.py','ck3_autonomous_player/src/xar_autoplayer/m5_joint_dispatch.py','ck3_autonomous_player/src/xar_autoplayer/m5_joint_budget_selector.py','ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py','ck3_autonomous_player/tests/unit/test_m5_joint_shortlist.py']:
 raw=(root/relative).read_bytes();refs.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
out=dict(schema='xar.ck3.java-jointshortlist.original-producer-golden.v1',machine_id='xenoamess-full-tower-eb9d2c1186',observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),evidence_scope='Actual unchanged compare_m5_joint_shortlist on synthetic assessment fixtures; expected projection excludes original ephemeral analytic reservation, never a production or live acceptance.',sources=refs,cases=cases)
sys.stdout.buffer.write(json.dumps(out,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
""";
    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository, existing Python, new output path required"); }
        Path output = Path.of(args[2]);
        if (Files.exists(output)) { throw new IOException("capture output must be new"); }
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-c", SCRIPT, args[0]);
        builder.directory(Path.of(args[0]).toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        CompletableFuture<byte[]> read = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readNBytes(MAXIMUM_BYTES + 1); }
            catch (IOException error) { throw new java.io.UncheckedIOException(error); }
        });
        if (!process.waitFor(60, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("original producer capture timed out"); }
        byte[] raw = read.get(10, TimeUnit.SECONDS);
        if (process.exitValue() != 0 || raw.length == 0 || raw.length > MAXIMUM_BYTES) { throw new IOException("capture failed or exceeded finite output allowance"); }
        Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        System.out.println("Captured unchanged original producer: " + raw.length + " bytes; no reservation imported");
    }
}
