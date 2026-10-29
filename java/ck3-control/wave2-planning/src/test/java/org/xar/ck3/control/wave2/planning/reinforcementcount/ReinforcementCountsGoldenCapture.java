package org.xar.ck3.control.wave2.planning.reinforcementcount;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;

/** Explicit real-helper oracle; the shared capture owner supplies the bounded process tree. */
public final class ReinforcementCountsGoldenCapture {
    private static final String SOURCE = "ck3_autonomous_player/src/xar_autoplayer/war_reinforcement_tradeoff_v1.py";
    private ReinforcementCountsGoldenCapture() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 5) { throw new IllegalArgumentException("python repository scratch output machine-id required"); }
        Path python = Path.of(args[0]).toAbsolutePath().normalize();
        Path repository = Path.of(args[1]).toRealPath();
        Path scratch = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (!Files.isRegularFile(python) || args[4].isBlank()
                || !scratch.toString().replace('\\', '/').startsWith("D:/codex-ck3-demos/2026-10-22-java-phase1/")
                || !output.startsWith(scratch)) {
            throw new IllegalArgumentException("capture path or machine identity outside assigned boundary");
        }
        String before = hash(repository.resolve(SOURCE));
        Path work = Files.createTempDirectory(scratch, "reinforcement-count-capture-");
        Path stdout = work.resolve("producer-golden.json"), stderr = work.resolve("producer-stderr.txt");
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-I", "-B", "-c", ORACLE, repository.toString(), args[4]);
        builder.directory(work.toFile()).redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
        Process process = builder.start();
        if (!process.waitFor(60, TimeUnit.SECONDS)) {
            process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
            process.waitFor(10, TimeUnit.SECONDS); throw new IOException("helper oracle timeout; no golden published");
        }
        if (process.exitValue() != 0) { throw new IOException("helper oracle exit " + process.exitValue() + "; see " + stderr); }
        if (!before.equals(hash(repository.resolve(SOURCE))) || Files.size(stderr) != 0
                || Files.size(stdout) <= 0 || Files.size(stdout) > 98_304) {
            throw new IOException("source drift, unexpected stderr or output size");
        }
        Files.createDirectories(output.getParent()); Files.write(output, Files.readAllBytes(stdout));
        System.out.println("REINFORCEMENT_REAL_HELPERS_CAPTURE_OK bytes=" + Files.size(output) + " sha256=" + hash(output));
    }
    private static String hash(Path file) throws IOException {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    private static final String ORACLE = """
            import copy, datetime, hashlib, json, pathlib, sys
            repository=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(repository/'ck3_autonomous_player'/'src'))
            from xar_autoplayer.war_reinforcement_tradeoff_v1 import _count,_stationary_staging
            base={'schema':'xar.reinforcement-count.request.v1','rows':[{'army_id':1,'soldiers':800}],
              'snapshot':{'snapshot_id':'native-frame','revision':7,'army_strengths_status':'available',
                'army_strengths_queried_snapshot_id':'native-frame','army_strengths_queried_revision':7,
                'army_strengths':[{'army_id':1,'scope_role':'player','war_ids':[99],'status':'available','current_soldiers':900}]},
              'role':'player','war_id':None}
            cases=[]
            def sample(name,request,operation='count'):
                wire=json.dumps(request,ensure_ascii=False,separators=(',',':'));value=json.loads(wire)
                result=(_count(value['rows'],snapshot=value['snapshot'],role=value['role'],war_id=value['war_id'])
                    if operation=='count' else _stationary_staging(value['row'],value['province']))
                cases.append({'name':name,'operation':operation,'request_json':wire,'expected_result':result})
            sample('current-strength-overrides-semantic',copy.deepcopy(base))
            for key,value in [('army_strengths_status','unavailable'),('army_strengths_queried_snapshot_id','stale'),('army_strengths_queried_revision',6),('army_strengths_status','partial')]:
                row=copy.deepcopy(base);row['snapshot'][key]=value;sample('binding-'+key+'-'+str(value),row)
            row=copy.deepcopy(base);row['role']='active_war_enemy';sample('different-scope-role',row)
            for war in (99,100):
                row=copy.deepcopy(base);row['war_id']=war;sample('war-filter-'+str(war),row)
            row=copy.deepcopy(base);row['snapshot']['army_strengths']*=2;sample('duplicate-current-cache-falls-back',row)
            row=copy.deepcopy(base);row['rows']*=2;sample('same-army-counted-once',row)
            row=copy.deepcopy(base);row['rows'].append({'army_id':1,'soldiers':801});sample('current-cache-resolves-different-semantic-counts',row)
            row['snapshot']['army_strengths_status']='unavailable';sample('conflicting-duplicate-is-unknown',row)
            row=copy.deepcopy(base);row['rows']=[];sample('explicit-empty-count-is-zero',row)
            row=copy.deepcopy(base);row['rows'][0]['soldiers']=None;sample('null-semantic-count-with-native-current-count',row)
            row['snapshot']['army_strengths_status']='unavailable';sample('null-semantic-and-no-current-count-is-unknown',row)
            row=copy.deepcopy(base);row['snapshot']['army_strengths_status']='unavailable';row['rows'][0]['soldiers']=-1;sample('negative-count-is-unknown',row)
            row=copy.deepcopy(base);row['rows'][0]['army_id']=0;row['snapshot']['army_strengths'][0]['army_id']=0;sample('army-id-zero-keeps-original-predicate',row)
            row=copy.deepcopy(base);row['rows'][0]['army_id']=2**90;row['snapshot']['army_strengths'][0].update(army_id=2**90,current_soldiers=2**100);sample('exact-integers-beyond-double-and-long',row)
            staging={'schema':'xar.reinforcement-staging.request.v1','province':2623,
              'row':{'army_id':1,'current_province_id':2623,'controllable':True,'in_combat':False,'retreating':False,
                'move_target_observable':False,'move_target_province_id':None,'route_province_ids':[],
                'route_source_count':0,'route_read_status':'complete_empty','army_state':'regular'}}
            sample('ordinary-stationary-staging',copy.deepcopy(staging),'staging')
            for field,value in [('controllable',False),('in_combat',True),('retreating',True),('current_province_id',2624),('route_province_ids',None),('route_province_ids',[2624])]:
                row=copy.deepcopy(staging);row['row'][field]=value;sample('staging-guard-'+field+'-'+str(value),row,'staging')
            row=copy.deepcopy(staging);del row['row']['route_province_ids'];sample('missing-route-is-not-empty',row,'staging')
            row=copy.deepcopy(staging);row['row'].update(army_state='gathering',move_target_observable=True);sample('observable-absent-target-original-branch',row,'staging')
            row=copy.deepcopy(staging);row['row']['move_target_province_id']=55;sample('complete-empty-route-original-branch',row,'staging')
            source=pathlib.Path('ck3_autonomous_player/src/xar_autoplayer/war_reinforcement_tradeoff_v1.py')
            result={'schema':'xar.reinforcement-count.golden.v1','machine_id':sys.argv[2],
              'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'producer_ref':{'path':source.as_posix(),'sha256':hashlib.sha256((repository/source).read_bytes()).hexdigest()},
              'producer_exit_code':0,'cases':cases}
            print(json.dumps(result,ensure_ascii=False,separators=(',',':')))
            """;
}
