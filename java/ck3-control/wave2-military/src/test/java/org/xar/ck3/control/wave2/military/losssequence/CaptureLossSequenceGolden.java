package org.xar.ck3.control.wave2.military.losssequence;

import java.io.IOException;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

/** Bounded original-producer capture, executed only by the central storage/M7 process owner. */
public final class CaptureLossSequenceGolden {
    private static final String SCRIPT = """
import contextlib, copy, datetime, hashlib, json, pathlib, random, runpy, sys, unittest
root=pathlib.Path(sys.argv[1]);machine_id=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
paths=('ck3_autonomous_player/src/xar_autoplayer/bridge/army_loss_sequence_replay.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_chunk_loss_writeback_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_regiment_refresh_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_loss_allocation_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_selected_refill_monthly_assembly.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_callback_soldier_effects_projection.py','ck3_autonomous_player/tests/unit/test_conditional_loss_sequence_replay.py','ck3_autonomous_player/tests/unit/test_army_chunk_loss_writeback_projection.py','ck3_autonomous_player/tests/unit/test_conditional_monthly_loss_budgets.py')
paths=paths+('ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_replenishment_records_contract.py')
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from xar_autoplayer.bridge.army_loss_sequence_replay import project_conditional_army_loss_sequence
from xar_autoplayer.bridge.army_chunk_loss_writeback_projection import project_observed_writer_chunk_changes, _q_div, _div
from xar_autoplayer.bridge.army_monthly_loss_budget_projection import construct_conditional_monthly_loss_budgets
sequence_fixture=runpy.run_path(str(root/paths[7]));writer_fixture=runpy.run_path(str(root/paths[8]));monthly_fixture=runpy.run_path(str(root/paths[9]))
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(fixture[name]) for fixture,name in ((sequence_fixture,'ConditionalLossSequenceReplayTests'),(writer_fixture,'ChunkLossWritebackTest'),(monthly_fixture,'ConditionalMonthlyLossBudgetsTests')))
with contextlib.redirect_stdout(sys.stderr):tests=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
if not tests.wasSuccessful() or tests.skipped or tests.testsRun==0:raise RuntimeError('complete original loss sequence suite failed/skipped/empty')
factory=sequence_fixture['full_stage_packet'];record=writer_fixture['record'];monthly_factory=monthly_fixture['monthly_budget_packet']
base=factory();legacy=copy.deepcopy(base);legacy['regiment_replenishment_records_v1'][0].pop('native_loss_writer_skipped')
unknown=copy.deepcopy(base);unknown['regiment_strengths'][0]['native_supply_loss_eligible']=None
zero=copy.deepcopy(base);zero['loss_application_inputs_v1'].update(current_supply_loss_budget=0,siege_loss_budget=0,raid_loss_budget=0)
no_data=copy.deepcopy(zero);no_data.pop('regiment_replenishment_records_v1')
missing_budget=copy.deepcopy(base);missing_budget['loss_application_inputs_v1'].pop('current_supply_loss_budget')
cases=[('all_four_passes',base),('legacy_missing_writer_admission',legacy),('unknown_supply_eligibility',unknown),('not_called_zero_budgets',zero),('physical_coverage_unknown',no_data),('missing_original_supply_budget',missing_budget),('unavailable',dict(status='unavailable'))]
sequences=[]
for label,row in cases:
    before_row=copy.deepcopy(row);expected=project_conditional_army_loss_sequence(row)
    if row!=before_row:raise RuntimeError('sequence mutated input')
    sequences.append(dict(id=label,input=row,expected=expected))
overrides=[]
for label,row in (('recover_missing_supply',missing_budget),('still_missing_raid',copy.deepcopy(missing_budget))):
    if label=='still_missing_raid':row['loss_application_inputs_v1'].pop('raid_loss_budget')
    changed=dict(row);changed['loss_application_inputs_v1']=dict(row['loss_application_inputs_v1'],current_supply_loss_budget=0)
    overrides.append(dict(id=label,input=row,supply_budget=0,expected=project_conditional_army_loss_sequence(changed)))
monthly=[]
for label,row in (('complete_monthly',monthly_factory()),):
    untouched=copy.deepcopy(row);expected=construct_conditional_monthly_loss_budgets(row)
    if row!=untouched:raise RuntimeError('monthly producer mutated input')
    monthly.append(dict(id=label,input=row,expected=expected))
data=dict(army_regiment_id=117440517,status='available',native_loss_writer_skipped=False,records=[record(0,301989889,0,4,3),record(1,570425346,20,25),record(2,570425346,20,25)])
army=dict(regiment_strengths=[dict(army_regiment_id=117440517,current_soldiers=20)],regiment_replenishment_records_v1=[data])
writers=[]
for label,raw in (('state3_aliases',300000),('fractional_quantity',50000),('exhausted_quantity',2300000),('negative_quantity',-50000)):
    request=dict(army_regiment_id=117440517,writer_quantity_raw=raw,writer_quantity_scale=100000)
    untouched=copy.deepcopy(army);expected=project_observed_writer_chunk_changes(army,request)
    if army!=untouched:raise RuntimeError('writer projection mutated input')
    writers.append(dict(id=label,input=army,request=request,expected=expected))
skipped=copy.deepcopy(army);skipped['regiment_replenishment_records_v1'][0]['native_loss_writer_skipped']=True
request=dict(army_regiment_id=117440517,writer_quantity_raw=300000,writer_quantity_scale=100000)
writers.append(dict(id='writer_skipped',input=skipped,request=request,expected=project_observed_writer_chunk_changes(skipped,request)))
rng=random.Random(0x2634286);vectors=[(-(1<<63),-(1<<63)),((1<<63)-1,1),(-(1<<63),-1),(1,0),(0,0),(-92233720368547,3),(-92233720368548,-10000000000)]
vectors.extend((rng.randint(-(1<<63),(1<<63)-1),rng.choice((0,1,-1,100000,-100000,10000000000,-(1<<63)))) for _ in range(32))
divisions=[]
for index,(a,b) in enumerate(vectors):
    item=dict(id='writer_qdivide_'+str(index),numerator=a,denominator=b)
    try:item['expected']=_q_div(a,b)
    except ArithmeticError as error:item['error']=str(error)
    divisions.append(item)
idiv=[]
for a,b in ((-(1<<63),-1),(0,0),(-7,3),(7,-3),(-(1<<63),1)):
    item=dict(numerator=a,denominator=b)
    try:item['expected']=_div(a,b)
    except ArithmeticError as error:item['error']=str(error)
    idiv.append(item)
refs=[]
for p in paths:
    raw=(root/p).read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if sha!=before[p]:raise RuntimeError('source changed during capture '+p)
    refs.append(dict(path=p,bytes=len(raw),sha256=sha))
print(json.dumps(dict(schema='xar.losssequence.original-producer-golden/v1',machine_id=machine_id,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='actual original derived four-pass and associated writer producers; shared refresh; no Game writer or observation',original_tests_executed=True,original_tests=tests.testsRun,original_skipped=len(tests.skipped),source_refs=refs,sequences=sequences,supply_overrides=overrides,monthly=monthly,writers=writers,qdivisions=divisions,idivisions=idiv),separators=(',',':')))
""";
    private CaptureLossSequenceGolden() {}
    public static void main(String[] args) throws Exception {
        if (args.length != 5) throw new IllegalArgumentException("repo-root python-exe D-scratch owned-output machine-id required");
        Path root = Path.of(args[0]).toRealPath(); Path scratch = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (!output.startsWith(scratch) || output.equals(scratch)) throw new IllegalArgumentException("capture outside qualified scratch root");
        if (Files.exists(output)) throw new IOException("existing evidence is immutable");
        Path stdout = Files.createTempFile(scratch, "losssequence-golden-", ".json");
        Path stderr = Files.createTempFile(scratch, "losssequence-capture-", ".log");
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", SCRIPT, root.toString(), args[4]);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("OPENBLAS_NUM_THREADS", "1");
        builder.environment().put("OMP_NUM_THREADS", "1"); builder.redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
        Process child = builder.start();
        if (!child.waitFor(120, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
            throw new IOException("original producer capture timed out");
        }
        System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
        if (child.exitValue() != 0) throw new IOException("original producer capture exit " + child.exitValue());
        byte[] raw = Files.readAllBytes(stdout);
        if (raw.length == 0 || raw.length > 160 * 1024) throw new IOException("raw golden exceeds bounded JSON budget");
        ByteArrayOutputStream packed = new ByteArrayOutputStream();
        try (GZIPOutputStream gzip = new GZIPOutputStream(packed)) { gzip.write(raw); }
        byte[] compressed = packed.toByteArray();
        if (compressed.length > 24 * 1024) throw new IOException("compressed golden exceeds leaf budget");
        try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            if (!Arrays.equals(raw, gzip.readNBytes(160 * 1024 + 1))) throw new IOException("gzip roundtrip changed producer bytes");
        }
        Files.createDirectories(output.getParent()); Files.write(output, compressed, java.nio.file.StandardOpenOption.CREATE_NEW);
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        System.out.println("machine_id=" + args[4] + " observed_at_utc=" + Instant.now() + " raw_bytes=" + raw.length
                + " raw_sha256=" + HexFormat.of().formatHex(digest.digest(raw)) + " gzip_bytes=" + compressed.length
                + " gzip_sha256=" + HexFormat.of().formatHex(digest.digest(compressed)));
    }
}
