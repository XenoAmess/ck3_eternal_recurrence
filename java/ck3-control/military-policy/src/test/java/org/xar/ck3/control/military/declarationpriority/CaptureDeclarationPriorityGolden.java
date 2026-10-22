package org.xar.ck3.control.military.declarationpriority;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit, once-only producer capture. Default JUnit never launches Python. */
public final class CaptureDeclarationPriorityGolden {
    private CaptureDeclarationPriorityGolden() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) {
            throw new IllegalArgumentException("arguments: repository-root existing-python output-json");
        }
        Path root = Path.of(arguments[0]).toRealPath();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture never overwrites existing evidence"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-B", "-c", SCRIPT, root.toString()))
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = readers.submit(() -> child.getInputStream().readNBytes(65_537));
            if (!child.waitFor(Duration.ofSeconds(45).toMillis(), TimeUnit.MILLISECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly);
                child.destroyForcibly();
                throw new IllegalStateException("producer capture timed out");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally {
            if (child.isAlive()) { child.destroyForcibly(); }
        }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > 65_536) {
            throw new IllegalStateException("capture failed, exit=" + child.exitValue() + ", bytes=" + raw.length);
        }
        Files.createDirectories(output.getParent());
        Files.write(output, raw, java.nio.file.StandardOpenOption.CREATE_NEW);
        System.out.println("Captured " + raw.length + " bytes at " + output);
    }

    private static final String SCRIPT = """
            import sys,json,hashlib,subprocess,unittest,importlib.util,copy,datetime
            from pathlib import Path
            root=Path(sys.argv[1])
            sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.declaration_objective_priority_v1 import native_declaration_objective_priority_v1 as leaf
            from xar_autoplayer.strategy import _preferred_native_declaration as choose
            fixture_rel='ck3_autonomous_player/tests/unit/fixtures/robert_v20261019_declaration_order_178_192.json'
            fixture=json.loads((root/fixture_rel).read_text(encoding='utf-8'))
            test_path=root/'ck3_autonomous_player/tests/unit/test_declaration_objective_priority_v1.py'
            spec=importlib.util.spec_from_file_location('original_declaration_priority_tests',test_path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            suite=unittest.defaultTestLoader.loadTestsFromModule(module)
            result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
            if not result.wasSuccessful() or result.testsRun!=7 or result.skipped:sys.exit(2)
            keys=('declaration_id','target_character_id','casus_belli_index','casus_belli_key','configuration_index','claimant_character_id','target_title_ids','source')
            powerkeys=('target_character_id','actor_power_base_raw','actor_network_contribution_raw','target_network_contribution_raw','target_power_total_raw','actual_power_ratio_raw','distance_raw')
            actor=fixture['actor_character_id']; rows=[v['declaration'] for v in fixture['cases']]
            powers={v['result_assessment']['target_character_id']:v['result_assessment'] for v in fixture['cases']}
            own=copy.deepcopy(next(v for v in rows if v['target_character_id']==33388))
            def project(row):return {k:copy.deepcopy(row[k]) for k in keys if k in row}
            leaves=[];selections=[];rejects=[]
            def add_leaf(name,who,row):
                request={'schema':'xar.ck3.declaration-objective-priority.input/v1','actor_character_id':who,'declaration':project(row) if isinstance(row,dict) else row}
                leaves.append({'name':name,'request':request,'expected_priority':leaf(row,actor_character_id=who)})
            for i,row in enumerate(rows):add_leaf('observed-'+str(fixture['cases'][i]['sequence']),actor,row)
            for field in ('source','casus_belli_key','claimant_character_id','target_title_ids'):
                row=copy.deepcopy(own);row.pop(field);add_leaf('missing-'+field,actor,row)
                row=copy.deepcopy(own);row[field]=None;add_leaf('null-'+field,actor,row)
            for name,mutation in [('nonplayer',{'claimant_character_id':actor+1}),('synthetic',{'source':'synthetic'}),('source-case',{'source':'Native'}),('cb-case',{'casus_belli_key':'CLAIM_CB'}),('empty-titles',{'target_title_ids':[]}),('zero-title',{'target_title_ids':[0]}),('negative-title',{'target_title_ids':[-1]}),('duplicate-positive-titles',{'target_title_ids':[7219,7219]}),('relic-name-not-title-claim',{'casus_belli_key':'reclaim_relic_artifact_war'}),('unreviewed-claim',{'casus_belli_key':'unreviewed_claim_cb'}),('empty-source',{'source':''})]:
                add_leaf(name,actor,{**own,**mutation})
            for who in (None,0,-1):add_leaf('actor-'+str(who),who,own)
            add_leaf('null-declaration',actor,None)
            huge=(1<<128)+51
            add_leaf('python-exact-integer-beyond-uint64',huge,{**own,'claimant_character_id':huge,'target_title_ids':[(1<<100)+7]})
            for name,who,row in [('bool-actor',True,own),('float-actor',float(actor),own),('string-actor',str(actor),own),('bool-claimant',actor,{**own,'claimant_character_id':True}),('float-claimant',actor,{**own,'claimant_character_id':float(actor)}),('bool-title',actor,{**own,'target_title_ids':[True]}),('float-title',actor,{**own,'target_title_ids':[7219.0]}),('string-title',actor,{**own,'target_title_ids':['7219']}),('tuple-titles',actor,{**own,'target_title_ids':'7219'}),('boolean-source',actor,{**own,'source':True})]:
                request={'schema':'xar.ck3.declaration-objective-priority.input/v1','actor_character_id':who,'declaration':project(row)}
                rejects.append({'name':name,'request':request,'raw_request_json':json.dumps(request,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False),'legacy_priority':leaf(row,actor_character_id=who),'expected_wire_rejection':True})
            def add_select(name,rs,assess=None,who=actor):
                selected=choose(rs,war_entry_assessments=assess,actor_character_id=who)
                idx=None if selected is None else next(i for i,r in enumerate(rs) if r is selected)
                request={'schema':'xar.ck3.declaration-objective-order.input/v1','actor_character_id':who,'declarations':[project(r) for r in rs],'war_entry_assessments':None if assess is None else [{k:v[k] for k in powerkeys} for v in assess.values()]}
                selections.append({'name':name,'request':request,'expected_index':idx,'expected_declaration_id':None if selected is None else selected.get('declaration_id')})
            add_select('observed-unassessed-missing-actor',rows,who=None)
            add_select('observed-unassessed-own-claim',rows)
            add_select('observed-assessed-missing-actor',rows,powers,who=None)
            add_select('observed-assessed-power-precedes-own-claim',rows,powers)
            other=next(v for v in rows if v['target_character_id']==26904)
            add_select('bad-assessed-claim-cannot-starve-fallback',[own,other],powers)
            add_select('nonclaims-retain-order',[v for v in rows if v['casus_belli_key']!='claim_cb'])
            add_select('assessed-claims-retain-power-order',[v for v in rows if v['casus_belli_key']=='claim_cb'],powers)
            add_select('empty',[])
            tied={**own,'declaration_id':'first-tied'};second={**own,'declaration_id':'second-tied'}
            add_select('first-exact-tie',[tied,second]);add_select('first-exact-tie-reversed',[second,tied])
            simple={**own,'claimant_character_id':-1,'target_title_ids':[],'casus_belli_key':'ordinary_cb'}
            left={**simple,'target_character_id':1,'declaration_id':'left'};right={**simple,'target_character_id':2,'declaration_id':'right'}
            baseline={'actor_power_base_raw':100,'actor_network_contribution_raw':10,'target_network_contribution_raw':20,'target_power_total_raw':100,'actual_power_ratio_raw':100,'distance_raw':30}
            mutations=[{'actor_power_base_raw':101,'target_power_total_raw':101},{'actual_power_ratio_raw':99},{'actor_network_contribution_raw':9},{'target_network_contribution_raw':19},{'target_power_total_raw':99},{'distance_raw':29}]
            for lane,mutation in enumerate(mutations):
                a={**baseline,'target_character_id':1};b={**baseline,**mutation,'target_character_id':2}
                if lane==0:a['actor_power_base_raw']=99
                add_select('power-lane-'+str(lane),[left,right],{1:a,2:b})
            hugea={**baseline,'target_character_id':1,'actor_power_base_raw':(1<<127),'target_power_total_raw':(1<<127)+1}
            hugeb={**hugea,'target_character_id':2,'target_power_total_raw':(1<<127)}
            add_select('beyond-signed64-subtraction',[left,right],{1:hugea,2:hugeb})
            negativea={**baseline,'target_character_id':1,'actor_network_contribution_raw':-999,'target_network_contribution_raw':-1}
            negativeb={**negativea,'target_character_id':2,'actor_network_contribution_raw':0,'target_network_contribution_raw':0}
            add_select('negative-network-clamps-only-comparison',[right,left],{1:negativea,2:negativeb})
            add_select('cb-key-order',[{**left,'casus_belli_key':'claim_cb'},{**right,'casus_belli_key':'HOLY_WAR_COUNTY'}],who=None)
            add_select('empty-assessment-is-not-an-assessment',[own,other],{})
            add_select('unknown-cb-does-not-prove-no-consequences',[{**own,'casus_belli_key':'unknown_claim_cb','target_title_ids':[]}])
            refs=[]
            for rel in ('ck3_autonomous_player/src/xar_autoplayer/declaration_objective_priority_v1.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/tests/unit/test_declaration_objective_priority_v1.py',fixture_rel):
                raw=(root/rel).read_bytes();refs.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            value={'schema':'xar.ck3.declaration-priority.original-producer-golden/v1','capture_machine_id':machine,'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'historical_observation_machine_id':fixture['machine_id'],'historical_observed_at_utc':fixture['observed_at_utc'],'scope':'Exact original pure leaf and original pure ordering consumer; historical eight-row subset, not live game admission or complete candidate set.','original_unittest':{'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)},'source_refs':refs,'leaf_cases':leaves,'selection_cases':selections,'wire_rejections':rejects}
            print(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')))
            """;
}
