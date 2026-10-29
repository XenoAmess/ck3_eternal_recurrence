package org.xar.ck3.control.wave3.planning.warpriorityfocus;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Capture a declared projection from the original complete priority producer, never a replacement. */
public final class WarCashFocusGoldenCapture {
    private static final List<String> SOURCES = List.of(
            "ck3_autonomous_player/src/xar_autoplayer/war_reinforcement_tradeoff_v1.py",
            "ck3_autonomous_player/src/xar_autoplayer/war_political_survival_stakes_v1.py",
            "ck3_autonomous_player/src/xar_autoplayer/nonleading_player_realm_siege_v1.py",
            "ck3_autonomous_player/src/xar_autoplayer/strategy.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py");
    private static final String ACTUAL_INPUT = "docs/ck3-native-ai/evidence/p50-actual-operational-strength-2026-10-18.json";
    private WarCashFocusGoldenCapture() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 5) { throw new IllegalArgumentException("python repository scratch output machine-id required"); }
        Path python = Path.of(args[0]).toAbsolutePath().normalize();
        Path repository = Path.of(args[1]).toRealPath(), scratch = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (!Files.isRegularFile(python) || args[4].isBlank()
                || !scratch.toString().replace('\\', '/').startsWith("D:/codex-ck3-demos/2026-10-22-java-phase1/")
                || !output.startsWith(scratch)) {
            throw new IllegalArgumentException("capture path or machine identity outside assigned boundary");
        }
        List<String> before = hashes(repository);
        Path work = Files.createTempDirectory(scratch, "war-cash-focus-capture-");
        Path stdout = work.resolve("producer-projection-golden.json"), stderr = work.resolve("producer-stderr.txt");
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-I", "-B", "-c", ORACLE, repository.toString(), args[4]);
        builder.directory(work.toFile()).redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
        Process process = builder.start();
        if (!process.waitFor(60, TimeUnit.SECONDS)) {
            process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
            process.waitFor(10, TimeUnit.SECONDS); throw new IOException("priority capture timeout; no golden published");
        }
        if (process.exitValue() != 0) { throw new IOException("priority capture exit " + process.exitValue() + "; see " + stderr); }
        if (!before.equals(hashes(repository)) || Files.size(stderr) != 0 || Files.size(stdout) <= 0 || Files.size(stdout) > 98_304) {
            throw new IOException("priority source/input drift, unexpected stderr or output size");
        }
        Files.createDirectories(output.getParent()); Files.write(output, Files.readAllBytes(stdout));
        System.out.println("WAR_CASH_FOCUS_ORIGINAL_PRODUCER_PROJECTION_OK bytes=" + Files.size(output) + " sha256=" + hash(output));
    }
    private static List<String> hashes(Path repository) throws IOException {
        List<String> values = new ArrayList<>();
        for (String source : SOURCES) { values.add(hash(repository.resolve(source))); }
        values.add(hash(repository.resolve(ACTUAL_INPUT)));
        return List.copyOf(values);
    }
    private static String hash(Path file) throws IOException {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    private static final String ORACLE = """
            import copy, datetime, hashlib, json, pathlib, sys
            repository=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(repository/'ck3_autonomous_player'/'src'))
            from xar_autoplayer.war_reinforcement_tradeoff_v1 import observe_war_spending_priority_v1
            from xar_autoplayer.bridge.version_identity import CK3_12004
            def army(identity,soldiers,province=2623,**updates):
                value={'source':'native','army_id':identity,'soldiers':soldiers,'current_province_id':province,
                  'owner_character_id':41 if identity==1 else 999,'controllable':identity==1,
                  'in_combat':False,'retreating':False,'army_state':'regular','army_state_code':0,
                  'move_target_observable':True,'move_target_province_id':None,'route_province_ids':[],
                  'route_source_count':0,'route_read_status':'complete_empty'}
                value.update(updates);return value
            base={'schema':'xar.war-cash-focus.request.v1',
              'snapshot':{'source':'injected-dll-named-pipe','snapshot_id':'native:12','revision':7,
                'native_revision':12,'date_raw':53300000,'episode_run_id':'synthetic-war-cash-focus',
                'paused':True,'map_ready':True,'active_event':None,'pending_character_interaction':None,
                'played_character':{'source':'native','character_id':41,'alive':True},
                'diagnostics':{'connected':True,'bridge_pid':77,'connection_generation':17},
                'player_armies':[army(1,800)],'active_wars':[{'source':'native','war_id':99,
                  'player_is_primary_war_leader':True,'player_side':'defender','player_relative_war_score':-40,
                  'targeted_title_ids':[2230],'primary_opponent_character_id':999,'enemy_armies':[army(2,1500,2629)]}]},
              'campaign_root':{'status':'available','player_character_id':41,'snapshot_revision':12,'date_raw':53300000,
                'primary_title':{'title_id':2230},'held_title_partition':[{'title':{'title_id':2230,'tier_raw':3}}]}}
            cases=[]
            def sample(name,request,input_kind='synthetic'):
                wire=json.dumps(request,ensure_ascii=False,separators=(',',':'));supplied=json.loads(wire)
                priority=observe_war_spending_priority_v1(supplied['snapshot'],campaign_root=supplied['campaign_root'])
                order=priority['cash_protection_priority_war_ids']
                focus=next((war for identity in order for war in priority['wars'] if war['war_id']==identity),None)
                projected=({key:focus[key] for key in ['war_id','observed_player_raised_soldiers','observed_enemy_raised_soldiers']} if focus is not None else None)
                cases.append({'name':name,'input_kind':input_kind,'request_json':wire,'expected_result':projected,
                  'original_priority_war_ids':order})
            sample('primary-title-loss-and-deficit',copy.deepcopy(base))
            row=copy.deepcopy(base);row['snapshot']['player_armies'][0]['soldiers']=2000;sample('known-advantage-still-losing-defence',row)
            row=copy.deepcopy(base);row['snapshot']['active_wars'][0]['player_relative_war_score']=40;sample('preventive-known-deficit',row)
            row=copy.deepcopy(row);row['snapshot']['player_armies'][0]['soldiers']=2000;sample('winning-current-advantage-no-protected-focus',row)
            row=copy.deepcopy(base);row['snapshot']['player_armies'][0]['soldiers']=None;sample('unknown-own-count-is-not-zero',row)
            row=copy.deepcopy(base);row['snapshot']['active_wars']=[];sample('no-active-war',row)
            multi=copy.deepcopy(base);second=copy.deepcopy(multi['snapshot']['active_wars'][0]);second.update(war_id=100,player_relative_war_score=-80,targeted_title_ids=[2231]);second['enemy_armies'][0]['army_id']=3;multi['snapshot']['active_wars'].append(second)
            sample('primary-title-first-beats-worse-score',copy.deepcopy(multi))
            row=copy.deepcopy(multi);row['campaign_root']['primary_title']['title_id']=2231;sample('second-primary-title-gets-first-focus',row)
            row=copy.deepcopy(multi);row['campaign_root']['snapshot_revision']=11;sample('stale-root-cannot-win-title-sort',row)
            row=copy.deepcopy(base);war=row['snapshot']['active_wars'][0];war.update(player_is_primary_war_leader=False,player_relative_war_score=20)
            war['enemy_armies'][0].update(army_state='sieging',army_state_code=3,siege_province_in_player_subrealm=True)
            sample('qualified-nonleading-realm-siege',copy.deepcopy(row))
            row['snapshot']['source']='unknown';sample('nonleading-unqualified-frame-keeps-no-focus',row)
            row=copy.deepcopy(base);row['snapshot']['player_armies'][0]['soldiers']=2000;war=row['snapshot']['active_wars'][0];war['player_relative_war_score']=40
            war['objective_province_states']=[{'province_id':2623,'occupation_observable':True,'is_occupied':True,'occupying_character_id':999}];sample('observed-opponent-objective-occupation',row)
            row=copy.deepcopy(base);row['snapshot']['player_armies'][0].update(soldiers=2000,retreating=True);row['snapshot']['active_wars'][0]['player_relative_war_score']=40;sample('all-current-own-armies-retreating',row)
            row=copy.deepcopy(base);row['snapshot']['player_armies'][0]['soldiers']=2000;row['snapshot']['active_wars'][0].update(player_side='attacker',player_relative_war_score=-100,targeted_title_ids=[]);sample('active-score-defeat-threshold',row)
            political=copy.deepcopy(base);political['snapshot']['player_armies'][0]['soldiers']=2000;war=political['snapshot']['active_wars'][0];war.update(player_side='attacker',targeted_title_ids=[])
            political['campaign_root'].update(player_character_alive=True,independent=False,immediate_liege_character_id=999,top_liege_character_id=999,
              provenance={'game_version':CK3_12004.game_version,'executable_sha256':CK3_12004.executable_sha256,'backend_id':CK3_12004.backend_id('campaign-root-context-v1')},readiness={'lieges_ready':True})
            political['snapshot']['war_termination_options']=[{'war_id':99,'source':'native','query_sequence':22,
              'queried_snapshot_id':'native:12','queried_revision':7,'queried_native_revision':12,'queried_connection_generation':17,
              'episode_run_id':'synthetic-war-cash-focus','player_side':'attacker','player_is_primary_war_leader':True,'player_relative_war_score':-40,
              'active_casus_belli_present':True,'active_casus_belli_identity':{'canonical_key':'refused_liege_demand_war','database_index':34},
              'options':{'surrender':{'outcome':'attacker_defeat'}}}]
            sample('source-bound-political-survival',copy.deepcopy(political));political['snapshot']['war_termination_options'][0]['queried_connection_generation']=18;sample('political-query-wrong-generation',political)
            row=copy.deepcopy(base);row['snapshot']['active_wars'][0]['war_id']=2**80;row['snapshot']['player_armies'][0]['soldiers']=2**90;row['snapshot']['active_wars'][0]['enemy_armies'][0]['soldiers']=2**91;sample('exact-identities-and-counts-above-long',row)
            actual_path=pathlib.Path('docs/ck3-native-ai/evidence/p50-actual-operational-strength-2026-10-18.json')
            historical=json.loads((repository/actual_path).read_bytes())
            sample('historical-p50-operational-strength-projection',{'schema':'xar.war-cash-focus.request.v1','snapshot':historical['snapshot'],'campaign_root':None},'historical_original_readonly_input_not_current_native_qualification')
            names=['war_reinforcement_tradeoff_v1.py','war_political_survival_stakes_v1.py','nonleading_player_realm_siege_v1.py','strategy.py','bridge/version_identity.py']
            refs=[]
            for name in names:
                path=pathlib.Path('ck3_autonomous_player/src/xar_autoplayer')/name;refs.append({'path':path.as_posix(),'sha256':hashlib.sha256((repository/path).read_bytes()).hexdigest()})
            result={'schema':'xar.war-cash-focus.golden.v1','scope':'projection_not_original_priority_receipt',
              'machine_id':sys.argv[2],'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'producer_refs':refs,'input_ref':{'path':actual_path.as_posix(),'sha256':hashlib.sha256((repository/actual_path).read_bytes()).hexdigest(),
                'historical_machine_id':historical.get('machine_id') if isinstance(historical.get('machine_id'),str) and historical['machine_id'] else 'unknown',
                'historical_machine_id_source':'explicit_top_level_original_field_else_unknown'},
              'producer_exit_code':0,'cases':cases}
            print(json.dumps(result,ensure_ascii=False,separators=(',',':')))
            """;
}
