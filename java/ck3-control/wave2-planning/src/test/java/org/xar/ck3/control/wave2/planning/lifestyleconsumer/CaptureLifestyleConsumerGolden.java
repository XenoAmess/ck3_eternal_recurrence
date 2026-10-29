package org.xar.ck3.control.wave2.planning.lifestyleconsumer;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/** Explicit original-producer capture only; not a runtime Python implementation or default JUnit dependency. */
public final class CaptureLifestyleConsumerGolden {
    private CaptureLifestyleConsumerGolden() { }
    private static final int MAXIMUM_BYTES = 98304;
    private static final String SCRIPT = """
import sys,json,hashlib,datetime,copy,importlib.util
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
from xar_autoplayer.lifestyle_formal_consumer import consume_lifestyle_private_query
from xar_autoplayer.lifestyle_education_focus_scope_v1 import qualify_current_education_focus
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,root/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
minimum=module('legacy_life_min_fixture','ck3_autonomous_player/tests/unit/test_lifestyle_min_policy.py')
all_life=module('legacy_all_life_fixture','ck3_autonomous_player/tests/unit/test_all_lifestyle_policy_v3.py')
def args(): return dict(baseline_plan=dict(selected_step='life-advance',phase='ordinary',opaque_prior_note=dict(value=1.5)),scope=dict(status='admitted',at_peace=True),query=None,preferred_focus_target_key='stewardship_wealth_focus',allow_wartime_initial_focus=False)
def adult():
 a=args();a['query']=dict(status='available',snapshot=minimum._complete_snapshot(),formal_precondition_status='ready');return a
cases=[]
def capture(name,a):
 result=consume_lifestyle_private_query(**a)
 cases.append(dict(name=name,input=dict(schema='xar.java.lifestyle-consumer.v1',**a),expected=result))
a=args();a['baseline_plan']['selected_step']='query-army-strengths-v1';a['scope']=None;capture('unrelated-baseline-retained',a)
a=args();a['scope']['status']='outside_scene';capture('outside-scene-keeps-baseline',a)
a=args();a['scope']['status']='root_query_needed';capture('root-query-needed',a)
a=args();a['scope']['status']='scope_unavailable';capture('scope-unavailable',a)
capture('missing-query',args())
a=args();a['query']=dict(status='current_state_unavailable',state=dict(native_error='exact-inner-error',request_id='synthetic-original-id'));capture('exact-inner-error-retained',a)
capture('life2-ready-perk',adult())
a=adult();a['query']['formal_precondition_status']='not_ready';capture('life2-action-not-fireable',a)
a=adult();a['query']['snapshot']['legal_perk_candidates']['items']=[];capture('life2-no-legal-minimum',a)
a=adult();s=a['query']['snapshot'];s['current_focus']={'presence':'absent'};s['current_lifestyle_progress']={'presence':'absent'};s['target_lifestyle_progress']={'presence':'present','lifestyle_key':'stewardship_lifestyle','unspent_perk_points':0};s['legal_focus_candidates']['items']=[dict(key='stewardship_wealth_focus',lifestyle_key='stewardship_lifestyle')];a['query'].update(status='stock_focus_available',formal_precondition_status='stock_focus_ready');capture('native-legal-first-focus',a)
a=args();a['scope']['government_key']='landless_adventurer_government';a['query']=dict(status='available',snapshot=all_life.snapshot('thoughtful_perk',positive='diplomacy_lifestyle'),formal_precondition_status='ready');capture('v3-cross-focus-nonfeudal-perk',a)
a=copy.deepcopy(a);a['query']['snapshot']['all_lifestyle_progress_v3']['native_revision']+=1;capture('v3-stale-progress-retained-unavailable',a)
a=copy.deepcopy(a);a['query']['snapshot']['all_lifestyle_progress_v3']=None;capture('v3-null-progress-does-not-fall-back-to-life2',a)
closed=json.loads((root/'ck3_autonomous_player/tests/unit/fixtures/lifestyle_after_succession_4106_4107_v1.json').read_text(encoding='utf-8'))
frame=closed['frame'];fact=qualify_current_education_focus(closed['education_query'],frame,expected_revision=frame['revision'])
if fact is None: raise RuntimeError('original closed education fact did not qualify')
a=args();a['scope']=dict(status='admitted',snapshot_revision=frame['native_revision'],player_character_id=frame['player_character_id'],at_peace=False);a['query']=dict(status='education_focus_not_applicable',state=closed['state_query'],education_focus_source_frame=frame,education_focus_scope=fact,education_focus_query=closed['education_query']);capture('closed-education-fact-requalified',a)
a=copy.deepcopy(a);a['query']['education_focus_query']['current_focus']['key']='stewardship_wealth_focus';capture('education-source-drift-remains-unavailable',a)
refs=[]
for relative in ['ck3_autonomous_player/src/xar_autoplayer/lifestyle_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/lifestyle_min_policy.py','ck3_autonomous_player/src/xar_autoplayer/all_lifestyle_perk_policy_v3.py','ck3_autonomous_player/src/xar_autoplayer/lifestyle_education_focus_scope_v1.py','ck3_autonomous_player/tests/unit/test_lifestyle_min_policy.py','ck3_autonomous_player/tests/unit/test_all_lifestyle_policy_v3.py','ck3_autonomous_player/src/xar_autoplayer/data/vanilla_lifestyle_catalog_12004.json','ck3_autonomous_player/tests/unit/fixtures/lifestyle_after_succession_4106_4107_v1.json']:
 raw=(root/relative).read_bytes();refs.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
out=dict(schema='xar.ck3.java-lifestyleconsumer.original-producer-golden.v1',machine_id='xenoamess-full-tower-eb9d2c1186',observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),evidence_scope='Actual unchanged consumer and original policies on synthetic unit snapshots plus retained historical education fixture. No Game, native calls, action submission, or current-build qualification.',sources=refs,cases=cases)
sys.stdout.buffer.write(json.dumps(out,ensure_ascii=False,separators=(',',':')).encode())
""";
    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository, existing Python, new output path required"); }
        Path output = Path.of(args[2]); if (Files.exists(output)) { throw new IOException("new capture output required"); }
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-c", SCRIPT, args[0]);
        builder.directory(Path.of(args[0]).toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); Process process = builder.start();
        CompletableFuture<byte[]> read = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readNBytes(MAXIMUM_BYTES + 1); }
            catch (IOException error) { throw new java.io.UncheckedIOException(error); }
        });
        if (!process.waitFor(60, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("original consumer capture timeout"); }
        byte[] raw = read.get(10, TimeUnit.SECONDS);
        if (process.exitValue() != 0 || raw.length == 0 || raw.length > MAXIMUM_BYTES) { throw new IOException("original consumer capture failed or exceeded allowance"); }
        Files.write(output, raw, StandardOpenOption.CREATE_NEW); System.out.println("Captured original LIFE consumer: " + raw.length + " bytes");
    }
}
