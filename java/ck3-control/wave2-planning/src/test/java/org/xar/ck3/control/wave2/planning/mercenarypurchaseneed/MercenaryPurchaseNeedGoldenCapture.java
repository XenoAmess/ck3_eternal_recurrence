package org.xar.ck3.control.wave2.planning.mercenarypurchaseneed;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Explicit source-mode sampler of the existing pure producer; no default Python test dependency. */
public final class MercenaryPurchaseNeedGoldenCapture {
    private static final String SOURCE = "ck3_autonomous_player/src/xar_autoplayer/war_reinforcement_tradeoff_v1.py";
    private MercenaryPurchaseNeedGoldenCapture() { }

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
        Path work = Files.createTempDirectory(scratch, "mercenary-need-capture-");
        Path stdout = work.resolve("producer-golden.json");
        Path stderr = work.resolve("producer-stderr.txt");
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-I", "-B", "-c", ORACLE,
                repository.toString(), args[4]);
        builder.directory(work.toFile()).redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
        Process process = builder.start();
        if (!process.waitFor(60, TimeUnit.SECONDS)) {
            process.descendants().forEach(ProcessHandle::destroyForcibly);
            process.destroyForcibly();
            process.waitFor(10, TimeUnit.SECONDS);
            throw new IOException("producer capture timeout; no golden published");
        }
        if (process.exitValue() != 0) { throw new IOException("producer exit " + process.exitValue() + "; see " + stderr); }
        if (!before.equals(hash(repository.resolve(SOURCE))) || Files.size(stderr) != 0
                || Files.size(stdout) <= 0 || Files.size(stdout) > 98_304) {
            throw new IOException("producer drift, unexpected stderr or golden size");
        }
        Files.createDirectories(output.getParent());
        Files.write(output, Files.readAllBytes(stdout));
        System.out.println("MERCENARY_PURCHASE_NEED_REAL_PRODUCER_CAPTURE_OK bytes=" + Files.size(output) + " sha256=" + hash(output));
    }
    private static String hash(Path path) throws IOException {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    private static final String ORACLE = """
            import copy, datetime, hashlib, json, pathlib, sys
            repository=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(repository/'ck3_autonomous_player'/'src'))
            from xar_autoplayer.war_reinforcement_tradeoff_v1 import observe_mercenary_purchase_model_need_v1
            base={'wars':[{'war_id':99,'protect_cash_reasons':['observed-pressure'],
              'player_relative_war_score':-20,'observed_player_raised_soldiers':1000,
              'observed_enemy_raised_soldiers':1500,'raised_force_deficit':True}],
              'primary_war_hostile_union_v1':{'war_ids':[99],'shared_force_deficit':True}}
            cases=[]
            def sample(name,priority):
                request={'schema':'xar.mercenary-purchase-model-need.request.v1','priority':priority}
                wire=json.dumps(request,ensure_ascii=False,separators=(',',':'))
                supplied=json.loads(wire)
                result=observe_mercenary_purchase_model_need_v1(supplied['priority'])
                cases.append({'name':name,'request_json':wire,'expected_result':result})
            sample('known-current-deficit',copy.deepcopy(base))
            for count in (None,0,1000):
                row=copy.deepcopy(base);row['wars'][0]['raised_force_deficit']=False
                row['wars'][0]['observed_enemy_raised_soldiers']=count;sample('observed-enemy-'+repr(count),row)
            row=copy.deepcopy(base);row['wars'][0]['raised_force_deficit']=False;del row['wars'][0]['observed_player_raised_soldiers'];sample('missing-own-count-stays-unknown',row)
            for score in (-101,-100,-99,0,False,1.0,None):
                row=copy.deepcopy(base);row['wars'][0]['player_relative_war_score']=score;sample('score-'+repr(score),row)
            for reasons in ([],None):
                row=copy.deepcopy(base);row['wars'][0]['protect_cash_reasons']=reasons;sample('no-protection-'+repr(reasons),row)
            for shared in (False,True,None):
                row=copy.deepcopy(base);row['wars'][0]['raised_force_deficit']=False
                row['primary_war_hostile_union_v1']={'war_ids':[99,100],'shared_force_deficit':shared}
                sample('shared-two-war-force-'+repr(shared),row)
            row=copy.deepcopy(base);row['wars'][0]['raised_force_deficit']=False;row['primary_war_hostile_union_v1']={'war_ids':[99,100]};sample('shared-force-missing-is-not-false',row)
            for wars in ([],None,[None,False,0]):
                row=copy.deepcopy(base);row['wars']=wars;sample('no-recoverable-wars-'+str(len(cases)),row)
            row=copy.deepcopy(base);row['wars'][0]['observed_player_raised_soldiers']=2**90;row['wars'][0]['observed_enemy_raised_soldiers']=2**91;sample('exact-counts-above-double-and-long',row)
            source=pathlib.Path('ck3_autonomous_player/src/xar_autoplayer/war_reinforcement_tradeoff_v1.py')
            result={'schema':'xar.mercenary-purchase-model-need.golden.v1','machine_id':sys.argv[2],
              'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'producer_ref':{'path':source.as_posix(),'sha256':hashlib.sha256((repository/source).read_bytes()).hexdigest()},
              'producer_exit_code':0,'cases':cases}
            print(json.dumps(result,ensure_ascii=False,separators=(',',':')))
            """;
}
