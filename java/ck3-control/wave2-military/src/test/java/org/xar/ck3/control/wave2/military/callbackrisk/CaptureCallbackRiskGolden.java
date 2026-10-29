package org.xar.ck3.control.wave2.military.callbackrisk;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

/** Original pure producers plus the actual existing in-memory Service consumer; central owner only. */
public final class CaptureCallbackRiskGolden {
    static final int MAX_RAW_BYTES = 131_072;
    static final int MAX_GZIP_BYTES = 16_384;
    private static final String SCRIPT = """
import copy,datetime,hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);machine=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
paths=('ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_callback_supply_risk_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_callback_soldier_effects_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_daily_supply_dispatch_inputs_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_loss_sequence_replay.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_chunk_loss_writeback_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_regiment_refresh_projection.py','ck3_autonomous_player/src/xar_autoplayer/simulation/battle_trait_numeric_inputs_12003.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/tests/unit/test_current_callback_supply_risk_service_12004.py','ck3_autonomous_player/tests/unit/test_conditional_monthly_loss_budgets.py','ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py')
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from test_current_callback_supply_risk_service_12004 import current_packet
from test_conditional_monthly_loss_budgets import MemoryStrengthService
from xar_autoplayer.bridge.army_current_callback_supply_risk_projection import project_current_callback_supply_risk_v1 as risk
from xar_autoplayer.bridge.army_current_callback_soldier_effects_projection import project_current_callback_soldier_effects_v1 as effects
rows=[]
def add(name,change):
    row=current_packet();change(row);rows.append((name,row))
add('crosses_positive_base_state',lambda x:None)
add('exact_threshold_zero_without_loss_family',lambda x:(x.update(current_supply_raw=800000),x.pop('loss_application_inputs_v1')))
add('known_rejection_unused_tables',lambda x:(x.update(current_supply_change_monthly_raw=None),x.pop('loss_application_inputs_v1'),x['monthly_loss_budget_inputs_v1'].update(status='unavailable',ready=False,unavailable_reason='unused state-table read unavailable',native_unit_in_combat=True,loaded_supply_state_levels=None,loaded_supply_state_fractions_raw=None)))
add('unknown_rate',lambda x:x.update(current_supply_change_monthly_raw=None))
add('suppressed_zero_with_unknown_stock',lambda x:(x.update(current_supply_raw=None),x['monthly_loss_budget_inputs_v1'].update(native_fleet_supply_loss_suppressed=True)))
add('missing_eligible_count',lambda x:x.pop('loss_application_inputs_v1'))
add('empty_selected_bucket',lambda x:x['current_daily_supply_dispatch_inputs_v1'].update(selected_bucket_count_raw=0,selected_bucket_data_present=False,subject_dispatch_occurrence_count=0,subject_occurrence_indices=[]))
add('missing_siege_budget',lambda x:x['loss_application_inputs_v1'].pop('siege_loss_budget'))
vectors=[]
for name,row in rows:
    prior=copy.deepcopy(row);r=risk(row);e=effects(row,r)
    if row!=prior:raise RuntimeError('original callback producer/consumer mutated input')
    vectors.append(dict(id=name,input=row,expected_risk=r,expected_effects=e))
# Existing MemoryStrengthService inherits the actual production query_army_strengths;
# only execute_step and readonly current snapshot are the existing memory fixture.
row=current_packet();prior=copy.deepcopy(row);service=MemoryStrengthService(row)
observed=service.query_army_strengths([0],expected_revision=2)
if service.calls!=1 or row!=prior:raise RuntimeError('actual Service call count or input preservation failed')
service_expected={k:observed[k] for k in ('current_callback_supply_risk_v1','current_callback_soldier_effects_v1')}
if service_expected['current_callback_supply_risk_v1'][0]['projection']!=vectors[0]['expected_risk']:raise RuntimeError('actual Service risk differs from original producer')
if service_expected['current_callback_soldier_effects_v1'][0]['projection']!=vectors[0]['expected_effects']:raise RuntimeError('actual Service effects differs from original consumer')
refs=[]
for p in paths:
    body=(root/p).read_bytes();digest=hashlib.sha256(body).hexdigest()
    if digest!=before[p]:raise RuntimeError('source changed during capture: '+p)
    refs.append(dict(path=p,bytes=len(body),sha256=digest))
out=dict(schema='xar.callbackrisk.original-producer-consumer-golden/v1',machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='projection_not_original; unchanged original callback risk -> soldier effects -> original four-pass core, plus one real GameplayBridgeService.query_army_strengths over existing memory transport fixture; no native callback or game effect',source_refs=refs,vectors=vectors,service_consumer=dict(actual_service_method='GameplayBridgeService.query_army_strengths',fixture='MemoryStrengthService',execute_step_calls=service.calls,input_vector_index=0,expected_fields=service_expected,registered_mcp_or_native_pipeline_executed=False))
print(json.dumps(out,separators=(',',':')))
""";
    private CaptureCallbackRiskGolden() {}
    public static void main(String[] args) throws Exception {
        if (args.length != 6 && args.length != 9) throw new IllegalArgumentException(
                "repo-root python-exe scratch-root owned-output-root gzip-output machine-id [--gzip-existing raw sha256] required");
        Path root = Path.of(args[0]).toRealPath(), scratch = Path.of(args[2]).toRealPath();
        Path ownedOutput = Path.of(args[3]).toRealPath(), output = Path.of(args[4]).toAbsolutePath().normalize();
        if (!ownedOutput.startsWith(scratch) || ownedOutput.equals(scratch)
                || !output.startsWith(ownedOutput) || output.equals(ownedOutput)
                || !output.toString().endsWith(".json.gz")) throw new IllegalArgumentException("explicit owned scratch/gzip output required");
        if (Files.exists(output)) throw new IOException("capture refuses to overwrite existing evidence");
        boolean existing = args.length == 9;
        Path rawPath;
        if (existing) {
            if (!"--gzip-existing".equals(args[6]) || !args[8].matches("[a-f0-9]{64}")) {
                throw new IllegalArgumentException("explicit existing raw path and SHA required");
            }
            rawPath = Path.of(args[7]).toRealPath();
            if (!rawPath.startsWith(scratch) || Files.isSymbolicLink(rawPath)) throw new IllegalArgumentException("existing raw outside explicit scratch");
        } else {
            rawPath = Files.createTempFile(ownedOutput, "callbackrisk-golden-", ".json");
            Path stderr = Files.createTempFile(ownedOutput, "callbackrisk-capture-", ".log");
            ProcessBuilder builder = new ProcessBuilder(args[1], "-X", "utf8", "-B", "-c", SCRIPT, root.toString(), args[5]);
            builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
            builder.redirectOutput(rawPath.toFile()).redirectError(stderr.toFile());
            Process child = builder.start();
            if (!child.waitFor(120, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IOException("original callback risk capture timeout");
            }
            System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
            if (child.exitValue() != 0) throw new IOException("original callback risk capture exit " + child.exitValue());
        }
        if (Files.size(rawPath) < 1 || Files.size(rawPath) > MAX_RAW_BYTES) throw new IOException("callback raw exceeds 128 KiB budget");
        byte[] raw = Files.readAllBytes(rawPath);
        String rawSha = digest(raw);
        if (existing && !args[8].equals(rawSha)) throw new IOException("existing callback raw SHA mismatch");
        byte[] compressed = compressGolden(raw);
        if (!java.util.Arrays.equals(raw, decompressGolden(compressed))) throw new IOException("callback gzip changed original bytes");
        if (Files.size(rawPath) != raw.length || !digest(Files.readAllBytes(rawPath)).equals(rawSha)) throw new IOException("raw changed during gzip derivation");
        Files.createDirectories(output.getParent()); Files.write(output, compressed, StandardOpenOption.CREATE_NEW);
        System.out.println("machine_id=" + args[5] + " observed_at_utc=" + Instant.now()
                + " producer_execution=" + !existing + " eligibility="
                + (existing ? "HISTORICAL_RAW_SIZING_ONLY" : "FRESH_PRODUCER_REQUIRES_CURRENT_SOURCE_PINS")
                + " raw_bytes=" + raw.length + " raw_sha256=" + rawSha
                + " gzip_bytes=" + compressed.length + " gzip_sha256=" + digest(compressed));
    }
    static byte[] compressGolden(byte[] raw) throws IOException {
        validateRaw(raw);
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        try (GZIPOutputStream gzip = new GZIPOutputStream(buffer)) { gzip.write(raw); }
        byte[] compressed = buffer.toByteArray();
        if (compressed.length > MAX_GZIP_BYTES) throw new IOException("callback gzip exceeds 16 KiB budget");
        return compressed;
    }
    static byte[] decompressGolden(byte[] compressed) throws IOException {
        if (compressed.length == 0 || compressed.length > MAX_GZIP_BYTES) throw new IOException("callback gzip exceeds 16 KiB budget");
        try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            byte[] raw = gzip.readNBytes(MAX_RAW_BYTES + 1);
            validateRaw(raw); return raw;
        }
    }
    private static void validateRaw(byte[] raw) throws IOException {
        if (raw.length == 0 || raw.length > MAX_RAW_BYTES) throw new IOException("callback raw exceeds 128 KiB budget");
        StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(raw));
    }
    private static String digest(byte[] raw) throws NoSuchAlgorithmException {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }
}
