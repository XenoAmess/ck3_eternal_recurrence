package org.xar.ck3.control.wave2.military.disembark;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit old-production capture, run only by the shared bounded Java Job owner. Ordinary JUnit launches no Python. */
public final class CaptureDisembarkGolden {
    private CaptureDisembarkGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 4) { throw new IllegalArgumentException("repository python-exe fresh-output machine-id required"); }
        Path root = Path.of(args[0]).toRealPath(); Path output = Path.of(args[2]).toAbsolutePath().normalize();
        Path owned = Path.of(System.getProperty("java.io.tmpdir")).toRealPath()
                .resolve("movement-captures/disembark").normalize();
        if (!output.startsWith(owned) || Files.exists(output)) { throw new IllegalArgumentException("fresh owned capture output required"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM, root.toString(), args[3]));
        builder.directory(root.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("OMP_NUM_THREADS", "1"); builder.environment().put("OPENBLAS_NUM_THREADS", "1");
        builder.redirectError(ProcessBuilder.Redirect.INHERIT); Process process = builder.start(); byte[] bytes;
        try (var reader = Executors.newSingleThreadExecutor()) {
            var response = reader.submit(() -> { try (var stream = process.getInputStream()) { return stream.readNBytes(110_001); } });
            if (!process.waitFor(90, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
                throw new IOException("original producer capture timeout");
            }
            try { bytes = response.get(); }
            catch (ExecutionException error) { throw new IOException("original producer capture read failed", error.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 110_000) {
            throw new IOException("capture failed/over budget: exit=" + process.exitValue() + " bytes=" + bytes.length);
        }
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured disembark original producer bytes=" + bytes.length + " machine_id=" + args[3]);
    }

    private static final String PROGRAM = """
import copy,datetime,hashlib,json,pathlib,runpy,sys
root=pathlib.Path(sys.argv[1]);machine=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'tools'))
from xar_autoplayer.bridge import army_current_disembark_penalty_contract as p
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12003,CK3_12004
from xar_autoplayer.bridge.war_contract import normalize_army_strengths
paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_disembark_penalty_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_unit_arrival_prestore_disembark_write_projection.py','ck3_autonomous_player/tests/test_current_disembark_penalty_mcp_compound.py']
before={path:hashlib.sha256((root/path).read_bytes()).hexdigest() for path in paths}
def source(build):return dict(snapshot_id='disembark-capture:42',revision=42,native_revision=7,date_raw=10000,game_version=build.game_version,executable_sha256=build.executable_sha256)
def leaf(days):return dict(schema_version=1,source=p.SOURCE,status='available',remaining_days=days,unavailable_reason=None)
samples=[]
for build in (CK3_12003,CK3_12004):
    for days in (-(1<<31),-34,-1,0,1,34,(1<<31)-1):
        samples.append(dict(id=build.game_version+'_'+str(days),input=dict(raw=leaf(days),source_provenance=source(build))))
    samples.append(dict(id=build.game_version+'_unavailable',input=dict(raw=dict(schema_version=1,source=p.SOURCE,status='unavailable',remaining_days=None,unavailable_reason='disembark_getter_not_bound'),source_provenance=source(build))))
samples.append(dict(id='omitted_without_build',input=dict(raw=None,source_provenance={})))
samples.append(dict(id='opaque_source_null_empty_and_decimal',input=dict(raw=None,source_provenance=dict(snapshot_id=None,extra_float=1.0,extra_int=18446744073709551615,empty=[],explicit_null=None))))
lower=source(CK3_12004);lower['executable_sha256']=lower['executable_sha256'].lower()
samples.append(dict(id='lowercase_exact_sha',input=dict(raw=leaf(-7),source_provenance=lower)))
for item in samples:
    data=copy.deepcopy(item['input']);untouched=copy.deepcopy(data)
    item['expected_projection']=p.project_current_disembark_penalty_v1(data['raw'],source_provenance=data['source_provenance'])
    if data['raw'] is not None:item['expected_normalized']=p.normalize_current_disembark_penalty_v1(data['raw'])
    if data!=untouched:raise RuntimeError('original pure producer mutated evidence')
bad=[]
for field,values in [('schema_version',[True,1.0,'1',2,18446744073709551615]),('remaining_days',[True,False,1.0,-1.0,'1',None,-(1<<31)-1,1<<31]),('source',['other',None]),('status',['other',True]),('unavailable_reason',['',False])]:
    for value in values:
        raw=leaf(1);raw[field]=value;bad.append(dict(id=field+'_'+repr(value),raw=raw))
for key in leaf(0):
    raw=leaf(0);del raw[key];bad.append(dict(id='missing_'+key,raw=raw))
raw=leaf(0);raw['active']=True;bad.append(dict(id='extra_active',raw=raw))
for item in bad:
    item['raw_json']=json.dumps(item.pop('raw'),separators=(',',':'))
    try:p.normalize_current_disembark_penalty_v1(json.loads(item['raw_json']))
    except ValueError:pass
    else:raise RuntimeError('original unexpectedly accepted '+item['id'])
factory=runpy.run_path(str(root/'ck3_autonomous_player/tests/test_current_disembark_penalty_mcp_compound.py'))['_MemoryDriver']
rows=[]
for name,raw in [('negative',leaf(-1)),('zero',leaf(0)),('nonstock',leaf(34)),('getter_unavailable',dict(schema_version=1,source=p.SOURCE,status='unavailable',remaining_days=None,unavailable_reason='disembark_getter_not_bound')),('old_wire_omission',None)]:
    row=dict(status='available',army_id=16777217,native_carmy_id=33554433,scope_role='player',war_ids=[],regiment_count=0,current_soldiers=0,maximum_soldiers=0,ai_base_power_raw=0,ai_base_power_scale=100000,unavailable_reason=None)
    if raw is not None:row[p.LEAF]=raw
    driver=factory(row);snapshot=driver.take_snapshot();service=GameplayBridgeService(driver)
    untouched=copy.deepcopy(row);normal=normalize_army_strengths([row],expected_scope=[dict(army_id=row['army_id'],scope_role='player',war_ids=[])])
    actual=service.query_army_strengths([row['army_id']],expected_revision=42)
    if driver.calls!=[('query-army-strengths-v1',42)] or row!=untouched:raise RuntimeError('real consumer chain did not remain read-only')
    rows.append(dict(id=name,row=row,snapshot=snapshot,hello=snapshot['diagnostics']['hello'],expected_normalized_leaf=normal[0].get(p.LEAF),expected_service_row=actual[p.LEAF][0],actual_original_service_calls=len(driver.calls)))
refs=[]
for path in paths:
    data=(root/path).read_bytes();digest=hashlib.sha256(data).hexdigest()
    if digest!=before[path]:raise RuntimeError('source changed during capture '+path)
    refs.append(dict(path=path,bytes=len(data),sha256=digest))
print(json.dumps(dict(schema='xar.disembark.original-producer-golden/v1',machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),qualification='original pure producer + whole-row normalizer + real GameplayBridgeService; synthetic read-only Driver envelopes; no native ABI/live/future/write qualification',source_refs=refs,samples=samples,rejections=bad,service_rows=rows),ensure_ascii=False,separators=(',',':')))
""";
}
