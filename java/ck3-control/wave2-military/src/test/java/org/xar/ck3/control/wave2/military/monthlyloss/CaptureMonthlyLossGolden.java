package org.xar.ck3.control.wave2.military.monthlyloss;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.concurrent.TimeUnit;

/** Explicit original-producer capture. Scheduling and Win32 Job containment belong to storage/M7. */
public final class CaptureMonthlyLossGolden {
    private static final String SCRIPT = """
import contextlib, copy, datetime, hashlib, json, pathlib, runpy, sys, unittest
root=pathlib.Path(sys.argv[1]); machine_id=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
paths=('ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_inputs_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_loss_sequence_replay.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_chunk_loss_writeback_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_callback_supply_risk_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_full_land_supply_rate_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_loss_allocation_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_selected_refill_monthly_assembly.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_fleet_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_land_stock_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_stock_supply_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_zero_stock_clock_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/tests/unit/test_conditional_monthly_loss_budgets.py')
monthly_fixture_path=paths[-1]
paths=paths+('ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py')
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from xar_autoplayer.bridge.army_monthly_loss_budget_projection import construct_conditional_monthly_loss_budgets, _derive_supply_component
from xar_autoplayer.bridge.army_monthly_loss_budget_inputs_contract import normalize_monthly_loss_budget_inputs_v1
from xar_autoplayer.bridge.army_current_callback_supply_risk_projection import _stock_state
fixture=runpy.run_path(str(root/monthly_fixture_path));factory=fixture['monthly_budget_packet']
with contextlib.redirect_stdout(sys.stderr):tests=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(fixture['ConditionalMonthlyLossBudgetsTests']))
if not tests.wasSuccessful() or tests.skipped or tests.testsRun==0:raise RuntimeError('complete original monthly suite failed/skipped/empty')
def base():
    full=factory(); fields=('status','monthly_loss_budget_inputs_v1','loss_application_inputs_v1','army_update_clock_v1','current_supply_raw','current_supply_change_monthly_raw','current_supply_capacity_raw')
    row={k:copy.deepcopy(full[k]) for k in fields};row['regiment_strengths']=[];return row
def mutate(label, group=None, **changes):
    row=base();target=row if group is None else row[group];target.update(changes)
    family=row['monthly_loss_budget_inputs_v1']
    if any(v is None for k,v in family.items() if k not in ('unavailable_reason','commander_supply_modifier_id','commander_supply_modifier_raw')) or family['commander_valid'] and family['commander_supply_modifier_raw'] is None:
        family.update(status='unavailable',ready=False,unavailable_reason='captured_missing_reached_operand')
    return label,row
cases=[('base',base()),mutate('rejected_native_unit','monthly_loss_budget_inputs_v1',unit_native_170_raw=3,loaded_supply_state_levels=None,loaded_supply_state_fractions_raw=None,commander_supply_modifier_raw=None),mutate('fleet_suppressed','monthly_loss_budget_inputs_v1',native_fleet_supply_loss_suppressed=True,loaded_supply_state_levels=None,loaded_supply_state_fractions_raw=None,commander_supply_modifier_raw=None),mutate('invalid_commander_unclamped','monthly_loss_budget_inputs_v1',commander_valid=False,commander_supply_modifier_id=None,commander_supply_modifier_raw=None,loaded_supply_state_fractions_raw=[0,0,150000]),mutate('unknown_unit','monthly_loss_budget_inputs_v1',unit_native_170_raw=None),mutate('empty_levels','monthly_loss_budget_inputs_v1',loaded_supply_state_levels=[],loaded_supply_state_fractions_raw=None,commander_supply_modifier_raw=None),mutate('half_component','monthly_loss_budget_inputs_v1',commander_supply_modifier_raw=-50000),mutate('high_operand_decomposition','monthly_loss_budget_inputs_v1',loaded_supply_state_fractions_raw=[0,0,(1<<63)-1],commander_supply_modifier_raw=-99998),mutate('overflow_modifier','monthly_loss_budget_inputs_v1',commander_supply_modifier_raw=(1<<63)-1),mutate('unknown_suppression','monthly_loss_budget_inputs_v1',native_fleet_supply_loss_suppressed=None),mutate('missing_stock',current_supply_raw=None),mutate('missing_rate',current_supply_change_monthly_raw=None),mutate('missing_capacity',current_supply_capacity_raw=None),mutate('negative_wrapped_add',current_supply_raw=(1<<63)-1,current_supply_change_monthly_raw=1,current_supply_capacity_raw=None),mutate('negative_capacity',current_supply_capacity_raw=-1),mutate('independent_rounding','loss_application_inputs_v1',whole_soldiers=12,siege_rate_raw=5000,raid_rate_raw=5000),mutate('both_inactive','loss_application_inputs_v1',siege_active=False,raid_active=False,whole_soldiers=None,siege_rate_raw=None,raid_rate_raw=None),mutate('missing_loss_count','loss_application_inputs_v1',whole_soldiers=None,supply_eligible_soldiers=None),mutate('negative_count','loss_application_inputs_v1',whole_soldiers=-2147483648,supply_eligible_soldiers=-2147483648),mutate('unknown_siege','loss_application_inputs_v1',siege_active=None),mutate('negative_fraction','monthly_loss_budget_inputs_v1',commander_valid=False,commander_supply_modifier_id=None,commander_supply_modifier_raw=None,loaded_supply_state_fractions_raw=[0,0,-50000]),mutate('short_fraction_vector','monthly_loss_budget_inputs_v1',loaded_supply_state_fractions_raw=[])]
for date in (239,240,241,-2147483648,2147483647):cases.append(mutate('grace_'+str(date),'army_update_clock_v1',current_date_raw=date))
for gate,value in (('native_unit_in_combat',True),('native_unit_gathering',True),('army_gathering_count_raw',-1)):
    cases.append(mutate('reject_'+gate,'monthly_loss_budget_inputs_v1',**{gate:value}))
cases.append(('unavailable_row',dict(status='unavailable')))
samples=[]
for label,row in cases:
    original=copy.deepcopy(row);out=construct_conditional_monthly_loss_budgets(row)
    if original!=row:raise RuntimeError('monthly producer mutated input')
    out.pop('same_input_conditional_loss_sequence_v1')
    samples.append(dict(id=label,input=row,expected_kernel=out))
supply=[]
for i,(stock,levels,fractions,commander,modifier,count) in enumerate(((950000,[60,10,0],[0,0,10000],True,0,12),(0,[],None,None,None,None),(-1,[0],[100000],False,None,100),((1<<63)-1,[60,10,0],[0,0,(1<<63)-1],True,-99998,2147483647),(0,[0],[150000],False,None,12),(0,[0],[0],None,None,None),(0,[0],[10000],None,None,12),(0,None,None,None,None,None),(0,[0],None,False,None,12),(0,[0],[10000],True,None,12),(0,[0],[10000],False,None,None),(0,[0],[],None,None,None))):
    inputs=dict(loaded_supply_state_levels=levels,loaded_supply_state_fractions_raw=fractions,commander_valid=commander,commander_supply_modifier_raw=modifier);losses=dict(supply_eligible_soldiers=count)
    result=dict(conditional_post_supply_raw=stock,missing_inputs=[],supply_state_index=None,supply_base_fraction_raw=None,supply_effective_fraction_raw=None,supply_budget_soldiers=None,supply_budget_ready=False)
    _derive_supply_component(result,inputs,losses);result.pop('conditional_post_supply_raw')
    supply.append(dict(id='supply_'+str(i),stock=stock,inputs=inputs,losses=losses,expected=result,expected_state=_stock_state(stock,inputs)))
contract=[]
valid=base()['monthly_loss_budget_inputs_v1']
def probe(label,value):
    raw=json.dumps(value,separators=(',',':'));entry=dict(id=label,raw=raw)
    try:entry['expected']=normalize_monthly_loss_budget_inputs_v1(json.loads(raw));entry['accepted']=True
    except ValueError:entry['accepted']=False
    contract.append(entry)
probe('null',None);probe('valid',valid)
for key,bad in (('scale',True),('scale',100000.0),('unit_native_170_raw',1.0),('unit_native_170_raw',True),('unit_native_170_raw',2147483648),('commander_supply_modifier_id',65536),('commander_supply_modifier_raw',9223372036854775808),('loaded_supply_state_levels',[None]),('loaded_supply_state_fractions_raw',[1.0]),('native_unit_in_combat',0),('ready',1),('unavailable_reason','unexpected')):
    value=copy.deepcopy(valid);value[key]=bad;probe('invalid_'+key+'_'+str(len(contract)),value)
value=copy.deepcopy(valid);del value['unit_native_170_raw'];probe('missing_key',value)
value=copy.deepcopy(valid);value['extra']=1;probe('extra_key',value)
value=copy.deepcopy(valid);value.update(commander_valid=False);probe('invalid_commander_publishes_modifier',value)
value=copy.deepcopy(valid);value.update(status='unavailable',ready=False,unavailable_reason='missing',unit_native_170_raw=None);probe('partial_valid',value)
refs=[]
for p in paths:
    data=(root/p).read_bytes();digest=hashlib.sha256(data).hexdigest()
    if digest!=before[p]:raise RuntimeError('source changed during capture '+p)
    refs.append(dict(path=p,bytes=len(data),sha256=digest))
print(json.dumps(dict(schema='xar.monthlyloss.original-producer-golden/v1',machine_id=machine_id,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='complete pure caller budget kernel and supply component; physical loss sequence omitted and not qualified',original_tests_executed=True,original_tests=tests.testsRun,original_skipped=len(tests.skipped),source_refs=refs,monthly=samples,supply=supply,contract=contract),separators=(',',':')))
""";
    private CaptureMonthlyLossGolden() {}

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("--gzip-existing")) throw new IllegalArgumentException("historical monthly raw cannot be adopted; final fixture requires fresh complete original suite");
        if (args.length != 5) throw new IllegalArgumentException("repo-root python-exe D-scratch owned-output machine-id required");
        Path root = Path.of(args[0]).toRealPath();
        Path scratch = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (!output.startsWith(scratch) || output.equals(scratch)) {
            throw new IllegalArgumentException("capture outside owned roots");
        }
        if (Files.exists(output)) throw new IOException("existing evidence is immutable");
        Path stdout = Files.createTempFile(scratch, "monthlyloss-golden-", ".json");
        Path stderr = Files.createTempFile(scratch, "monthlyloss-capture-", ".log");
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", SCRIPT, root.toString(), args[4]);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("OPENBLAS_NUM_THREADS", "1");
        builder.environment().put("OMP_NUM_THREADS", "1"); builder.redirectOutput(stdout.toFile()).redirectError(ProcessBuilder.Redirect.PIPE);
        Process child = builder.start(); Diagnostics diagnostics = beginDiagnostics(child, stderr);
        if (!child.waitFor(120, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
            throw new IOException("original producer capture timed out");
        }
        finishDiagnostics(diagnostics);
        System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
        if (child.exitValue() != 0) throw new IOException("original producer capture exit " + child.exitValue());
        byte[] raw = Files.readAllBytes(stdout);
        writeGolden(raw, output, args[4]);
    }

    private static final int RAW_MAX = 131_072;
    private static final int GZIP_MAX = 16_384;
    private static void writeGolden(byte[] raw, Path output, String machine) throws Exception {
        if (raw.length == 0 || raw.length > RAW_MAX) throw new IOException("raw golden exceeds 128KiB profile");
        StandardCharsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(raw));
        java.io.ByteArrayOutputStream packed = new java.io.ByteArrayOutputStream();
        try (java.util.zip.GZIPOutputStream gzip = new java.util.zip.GZIPOutputStream(packed)) { gzip.write(raw); }
        byte[] compressed = packed.toByteArray();
        if (compressed.length > GZIP_MAX) throw new IOException("gzip golden exceeds 16KiB profile; all cases retained");
        try (java.util.zip.GZIPInputStream gzip = new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(compressed))) {
            if (!java.util.Arrays.equals(raw, gzip.readNBytes(RAW_MAX + 1))) throw new IOException("gzip changed original token bytes");
        }
        Files.createDirectories(output.getParent()); Files.write(output, compressed, java.nio.file.StandardOpenOption.CREATE_NEW);
        java.security.MessageDigest digest = java.security.MessageDigest.getInstance("SHA-256");
        System.out.println("machine_id=" + machine + " observed_at_utc=" + Instant.now() + " raw_bytes=" + raw.length
                + " raw_sha256=" + java.util.HexFormat.of().formatHex(digest.digest(raw)) + " gzip_bytes=" + compressed.length
                + " gzip_sha256=" + java.util.HexFormat.of().formatHex(digest.digest(compressed)));
    }

    private record Diagnostics(Thread reader, java.util.concurrent.atomic.AtomicBoolean overflow,
            java.util.concurrent.atomic.AtomicReference<IOException> failure) { }
    private static Diagnostics beginDiagnostics(Process child, Path file) {
        var overflow = new java.util.concurrent.atomic.AtomicBoolean();
        var failure = new java.util.concurrent.atomic.AtomicReference<IOException>();
        Thread reader = Thread.startVirtualThread(() -> {
            try (var input = child.getErrorStream(); var output = Files.newOutputStream(file)) {
                byte[] buffer = new byte[1024]; int total = 0, count;
                while ((count = input.read(buffer)) != -1) {
                    int retained = Math.min(count, 8192 - total); output.write(buffer, 0, retained); total += retained;
                    if (retained != count) { overflow.set(true); child.destroyForcibly(); }
                }
            } catch (IOException error) { failure.set(error); child.destroyForcibly(); }
        });
        return new Diagnostics(reader, overflow, failure);
    }
    private static void finishDiagnostics(Diagnostics value) throws IOException, InterruptedException {
        value.reader().join(5000);
        if (value.reader().isAlive()) throw new IOException("diagnostic reader did not terminate");
        if (value.failure().get() != null) throw new IOException("diagnostic transfer failed", value.failure().get());
        if (value.overflow().get()) throw new IOException("diagnostics exceeded 8KiB; bounded prefix retained");
    }
}
