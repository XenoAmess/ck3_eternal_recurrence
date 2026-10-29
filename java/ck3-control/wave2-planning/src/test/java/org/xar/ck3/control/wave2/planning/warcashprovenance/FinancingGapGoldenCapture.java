package org.xar.ck3.control.wave2.planning.warcashprovenance;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Explicit old-producer sampling; the shared capture owner supplies the outer Win32 Job. */
public final class FinancingGapGoldenCapture {
    private static final List<String> SOURCES = List.of(
            "ck3_autonomous_player/src/xar_autoplayer/wartime_construction_cash_v1.py",
            "ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py",
            "ck3_autonomous_player/src/xar_autoplayer/war_reinforcement_tradeoff_v1.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_decision_outcome_contract.py");
    private FinancingGapGoldenCapture() { }

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
        List<String> before = sourceHashes(repository);
        Path work = Files.createTempDirectory(scratch, "financing-gap-capture-");
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
            throw new IOException("producer oracle timeout; no golden published");
        }
        if (process.exitValue() != 0) { throw new IOException("producer oracle exit " + process.exitValue() + "; see " + stderr); }
        if (!before.equals(sourceHashes(repository)) || Files.size(stderr) != 0
                || Files.size(stdout) <= 0 || Files.size(stdout) > 131_072) {
            throw new IOException("producer drift, unexpected stderr or golden size");
        }
        Files.createDirectories(output.getParent());
        Files.write(output, Files.readAllBytes(stdout));
        System.out.println("WAR_FINANCING_REAL_PRODUCER_CAPTURE_OK bytes=" + Files.size(output) + " sha256=" + hash(output));
    }
    private static List<String> sourceHashes(Path repository) throws IOException {
        List<String> result = new ArrayList<>();
        for (String source : SOURCES) { result.add(hash(repository.resolve(source))); }
        return List.copyOf(result);
    }
    private static String hash(Path file) throws IOException {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    // Data cases call the unchanged old producer; no financing algorithm is reproduced here.
    private static final String ORACLE = """
            import copy, datetime, hashlib, json, pathlib, sys
            repository=pathlib.Path(sys.argv[1])
            sys.path.insert(0,str(repository/'ck3_autonomous_player'/'src'))
            from xar_autoplayer.wartime_construction_cash_v1 import observe_war_financing_capability_gap_v1
            from xar_autoplayer.bridge.ingame_decision_outcome_contract import CAPABILITY
            base={'schema':'xar.war-financing-capability-gap.request.v1',
              'snapshot':{'played_character':{'character_id':41},'native_revision':12,'revision':7,
                'date_raw':53300000,'snapshot_id':'synthetic-financing-frame','episode_run_id':'synthetic-financing-episode',
                'paused':True,'map_ready':True,'played_character_gold':{'raw':25000000,'scale':100000},
                'active_wars':[{'war_id':99}]},
              'priority':{'wars':[{'war_id':99,'primary_player_war':True,'player_relative_war_score':-80,'raised_force_deficit':True}]},
              'root':{'status':'available','player_character_id':41,'snapshot_revision':12,'date_raw':53300000,
                'player_max_monthly_gold_maintenance_v1':{'status':'available','value':{'raw':2000000,'scale':100000}}},
              'construction_ledger':{'pending':None},'bridge_capabilities':None}
            examples=[]
            def sample(name,request):
                wire=json.dumps(request,ensure_ascii=False,separators=(',',':'))
                supplied=json.loads(wire)
                caps=supplied['bridge_capabilities']
                args=dict(snapshot=supplied['snapshot'],priority=supplied['priority'],root=supplied['root'],
                    construction_ledger=supplied['construction_ledger'],bridge_capabilities=set(caps) if caps is not None else None)
                case={'name':name,'request_json':wire}
                try: case['expected_result']=observe_war_financing_capability_gap_v1(**args)
                except ValueError as error: case['expected_exception']=type(error).__name__
                examples.append(case)
            sample('crisis-unknown-capability',copy.deepcopy(base))
            for advertised in (False,True):
                row=copy.deepcopy(base);row['bridge_capabilities']=[CAPABILITY] if advertised else []
                sample('advertised-'+str(advertised),row)
            for field,value in [('player_character_id',42),('snapshot_revision',11),('date_raw',53300024),('status','unavailable')]:
                row=copy.deepcopy(base);row['root'][field]=value;sample('foreign-root-'+field,row)
            for active in ([],None,[{'war_id':100}]):
                row=copy.deepcopy(base);row['snapshot']['active_wars']=active;sample('priority-is-not-active-'+str(len(examples)),row)
            for cash in (False,1.0,None,-1):
                row=copy.deepcopy(base);row['snapshot']['played_character_gold']['raw']=cash;sample('cash-token-'+repr(cash),row)
            for current in (True,False):
                row=copy.deepcopy(base);row['priority']['wars'][0]['player_relative_war_score']=40
                if not current:row['root']['snapshot_revision']=11
                sample('ordinary-shortfall-current-root-'+str(current),row)
            for cash in (19999999,20000000):
                row=copy.deepcopy(base);row['root']=None;row['priority']['wars'][0]['player_relative_war_score']=40
                row['snapshot']['played_character_gold']['raw']=cash;sample('fallback-buffer-boundary-'+str(cash),row)
            for cash in (35999999,36000000):
                row=copy.deepcopy(base);row['priority']['wars'][0]['player_relative_war_score']=40
                row['snapshot']['played_character_gold']['raw']=cash;sample('observed-buffer-boundary-'+str(cash),row)
            for score in (-25,-24):
                row=copy.deepcopy(base);row['priority']['wars'][0]['player_relative_war_score']=score
                row['snapshot']['played_character_gold']['raw']=100000000;sample('crisis-score-boundary-'+str(score),row)
            for evidence in ('observed_primary_opponent_objective_occupation_province_ids','observed_hostile_siege_in_player_subrealm_army_ids','all_observed_own_raised_armies_currently_retreating'):
                row=copy.deepcopy(base);row['priority']['wars'][0]['raised_force_deficit']=False
                row['priority']['wars'][0][evidence]=True if evidence.startswith('all_') else [77]
                sample('crisis-evidence-'+evidence,row)
            row=copy.deepcopy(base);row['construction_ledger']['pending']={'status':'submission_unresolved'};sample('construction-pending-is-only-intent',row)
            row=copy.deepcopy(base);row['snapshot']['played_character_id']=41;del row['snapshot']['played_character'];sample('observed-frame-fallback-is-not-root-actor',row)
            row=copy.deepcopy(base);huge=2**80;row['snapshot']['active_wars']=[{'war_id':huge}]
            row['priority']['wars'][0]['war_id']=huge;row['snapshot']['played_character_gold']['raw']=-(2**90)
            sample('integer-precision-beyond-double-and-long',row)
            for field,value in [('native_revision',True),('date_raw',1.0),('revision',None)]:
                row=copy.deepcopy(base);row['snapshot'][field]=value;sample('invalid-frame-'+field,row)
            refs=[]
            for name in ['wartime_construction_cash_v1.py','m5_observed_opportunity_selector.py','war_reinforcement_tradeoff_v1.py','bridge/ingame_decision_outcome_contract.py']:
                path=pathlib.Path('ck3_autonomous_player/src/xar_autoplayer')/name
                refs.append({'path':path.as_posix(),'sha256':hashlib.sha256((repository/path).read_bytes()).hexdigest()})
            result={'schema':'xar.war-financing-capability-gap.golden.v1','machine_id':sys.argv[2],
              'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'producer_refs':refs,
              'producer_exit_code':0,'cases':examples}
            print(json.dumps(result,ensure_ascii=False,separators=(',',':')))
            """;
}
