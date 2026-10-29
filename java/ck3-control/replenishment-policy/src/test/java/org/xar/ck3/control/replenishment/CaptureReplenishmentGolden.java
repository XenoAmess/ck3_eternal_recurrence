package org.xar.ck3.control.replenishment;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;

/** One-time explicit capture tool. Default JUnit never executes Python. */
public final class CaptureReplenishmentGolden {
    private static final String SCRIPT = """
import copy, hashlib, json, pathlib, random, runpy, sys, unittest
root=pathlib.Path(sys.argv[1]); machine_id=sys.argv[2]
test_path=root/'ck3_autonomous_player/tests/unit/test_replenishment_numeric.py'
source_paths=('ck3_autonomous_player/src/xar_autoplayer/replenishment_numeric.py','ck3_autonomous_player/tests/unit/test_replenishment_numeric.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_replenishment_records_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_associated_refill_current_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_scoped_ordered_refill_projection.py')
source_before={relative:hashlib.sha256((root/relative).read_bytes()).hexdigest() for relative in source_paths}
namespace=runpy.run_path(str(test_path))
namespace['ReplenishmentNumericTests'].maxDiff=None
suite=unittest.defaultTestLoader.loadTestsFromTestCase(namespace['ReplenishmentNumericTests'])
result=unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful(): raise SystemExit(21)
record=namespace['record']; army=namespace['army']
q=namespace['same_input_chunk_q']; project=namespace['project_observed_replenishment_v1']
def project_input(rows):
    out=[]
    for row in rows:
        item={'army_id':row['army_id']}
        if 'regiment_replenishment_records_v1' in row:
            source=row['regiment_replenishment_records_v1']
            if source is None: item['regiment_replenishment_records_v1']=None
            else:
                item['regiment_replenishment_records_v1']=[]
                for snapshot in source:
                    fields=('army_regiment_id','status','native_data_record_count','unavailable_reason')
                    snap={field:snapshot[field] for field in fields}
                    fields=('status','unavailable_reason','record_index','persistent_regiment_id','chunk_index','maximum_soldiers','effective_current_soldiers','persistent_prepared_replenishment_fraction_raw','persistent_prepared_replenishment_fraction_scale','native_chunk_can_replenish')
                    snap['records']=[{field:entry[field] for field in fields} for entry in snapshot['records']]
                    item['regiment_replenishment_records_v1'].append(snap)
        out.append(item)
    return {'schema':'xar.replenishment.observed-input/v1','army_rows':out}
projections=[]
def add(name, rows):
    before=copy.deepcopy(rows); expected=project(rows)
    if before != rows: raise RuntimeError('original producer mutated its input')
    projections.append({'id':name,'input':project_input(rows),'expected':expected})
add('basic',[army()]); add('no_armies',[])
add('native_empty_records',[army(records=[])])
add('missing_snapshots',[{'army_id':1}])
add('null_snapshots',[{'army_id':1,'regiment_replenishment_records_v1':None}])
add('published_empty_snapshots',[{'army_id':1,'regiment_replenishment_records_v1':[]}])
add('partial_source',[army(data_status='partial')])
add('unavailable_source',[army(data_status='unavailable')])
add('unavailable_record',[army(records=[record(status='unavailable')],data_status='partial')])
add('qualified_integer_zero',[army(records=[record(current=0,maximum=10,prepared=1)])])
add('seven_observed',[army(records=[record(ordinal=i) for i in range(7)])])
add('same_alias_two_armies',[army(),army(1)])
add('conflicting_alias_two_armies',[army(),army(1,records=[record(prepared=5000)])])
add('available_and_unavailable_alias',[army(),army(1,records=[record(status='unavailable')],data_status='partial')])
add('negative_wrapped_request',[army(records=[record(current=0,maximum=3,prepared=6148914691236483871)])])
add('low32_store',[army(records=[record(current=-2147483648,maximum=2147483647,prepared=400000)])])
for field in ('maximum_soldiers','effective_current_soldiers','persistent_prepared_replenishment_fraction_raw','native_chunk_can_replenish'):
    row=army(); row['regiment_replenishment_records_v1'][0]['records'][0][field]=None
    add('nullable_'+field,[row])
for field,value in (('persistent_regiment_id',-1),('chunk_index',-1),('chunk_index',7),('persistent_prepared_replenishment_fraction_scale',99999)):
    row=army(); row['regiment_replenishment_records_v1'][0]['records'][0][field]=value
    add('special_'+field+'_'+str(value),[row])
add('different_ids_insertion_order',[army(3),army(1,records=[dict(record(),persistent_regiment_id=9)])])
add('incomplete_slots_still_available',[army(records=[record(ordinal=6)])])
add('partial_and_missing_sources',[army(),{'army_id':2}])
add('two_sources_one_snapshot_unavailable',[army(),army(2,data_status='unavailable')])
values=[(100,90,20000,True),(10,0,1,True),(3,0,6148914691236483871,True),(2147483647,-2147483648,400000,True),(-2147483648,2147483647,9223372036854775807,True),(100,0,0,True),(100,0,-1,True),(100,0,20000,False),(0,-1,9223372036854775807,True)]
rng=random.Random(262_9_0)
for _ in range(320):
    values.append((rng.randint(-2147483648,2147483647),rng.randint(-2147483648,2147483647),rng.randint(-9223372036854775808,9223372036854775807),bool(rng.getrandbits(1))))
chunks=[]
for index,(maximum,current,prepared,predicate) in enumerate(values):
    chunks.append({'id':'native_int_width_'+str(index),'input':{'schema':'xar.replenishment.chunk-input/v1','maximum_soldiers':maximum,'effective_current_soldiers':current,'prepared_fraction_raw':prepared,'native_chunk_can_replenish':predicate},'expected':q(maximum,current,prepared,predicate)})
sources=[]
for relative in source_paths:
    data=(root/relative).read_bytes(); digest=hashlib.sha256(data).hexdigest()
    if digest != source_before[relative]: raise RuntimeError('source changed during capture: '+relative)
    sources.append({'path':relative,'bytes':len(data),'sha256':digest})
out={'schema':'xar.replenishment.python-producer-golden/v1','machine_id':machine_id,'observed_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'original_tests_run':result.testsRun,'original_test_failures':len(result.failures),'original_test_errors':len(result.errors),'source_refs':sources,'scope':'projection_not_original; normalized DATA leaf operands only; no game, dispatch, future preparation, physical writeback, or saved progress','chunks':chunks,'projections':projections}
print(json.dumps(out,ensure_ascii=False,separators=(',',':')))
""";

    private CaptureReplenishmentGolden() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 5) throw new IllegalArgumentException("repo-root python-exe D-scratch output-golden machine-id required");
        Path root = Path.of(args[0]).toRealPath();
        Path scratch = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        Path module = root.resolve("java/ck3-control/replenishment-policy").toAbsolutePath().normalize();
        if (!output.startsWith(module) || !scratch.toString().toLowerCase(java.util.Locale.ROOT).startsWith("d:")) {
            throw new IllegalArgumentException("capture output must be in owned module and scratch must be on D");
        }
        Path production = root.resolve("ck3_autonomous_player/src/xar_autoplayer/replenishment_numeric.py");
        String before = sha(Files.readAllBytes(production));
        Path stdout = Files.createTempFile(scratch, "replenishment-golden-", ".json");
        Path stderr = Files.createTempFile(scratch, "replenishment-tests-", ".log");
        Instant started = Instant.now();
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-c", SCRIPT, root.toString(), args[4]);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        // Importing the existing service can load OpenBLAS. Its default worker pool exceeded
        // the original 512 MiB Job before any original tests ran; this integer-only capture
        // does not use BLAS, so bound the imported library rather than changing the producer.
        builder.environment().put("OPENBLAS_NUM_THREADS", "1");
        builder.environment().put("OMP_NUM_THREADS", "1");
        builder.redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
        Process child = builder.start();
        if (!child.waitFor(120, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly);
            child.destroyForcibly();
            throw new IOException("original producer capture timed out; no golden published");
        }
        System.out.print(Files.readString(stderr, StandardCharsets.UTF_8));
        if (child.exitValue() != 0) throw new IOException("original producer/tests exit " + child.exitValue());
        byte[] data = Files.readAllBytes(stdout);
        if (data.length == 0 || data.length > 400_000 || !before.equals(sha(Files.readAllBytes(production)))) {
            throw new IOException("golden size or source stability validation failed");
        }
        Files.createDirectories(output.getParent());
        if (Files.exists(output)) throw new IOException("golden already exists; use a fresh version instead of overwriting evidence");
        Files.write(output, data, java.nio.file.StandardOpenOption.CREATE_NEW);
        System.out.println("capture_started_at_utc=" + started + " completed_at_utc=" + Instant.now()
                + " bytes=" + data.length + " sha256=" + sha(data)
                + " original_producer_sha256=" + before + " machine_id=" + args[4]);
    }
    private static String sha(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
}
