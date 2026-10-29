package org.xar.ck3.control.wave2.military.actualcontact;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Actual legacy producer capture; version-token fixes retain contrary legacy outputs. */
public final class CaptureActualContactGolden {
    private CaptureActualContactGolden() { }
    private static final String SCRIPT = """
            import copy,datetime,hashlib,importlib,json,pathlib,subprocess,sys
            root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'));sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            fixture=importlib.import_module('test_actual_contact_scope_contract')
            producer=importlib.import_module('xar_autoplayer.bridge.actual_contact_contract')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            expected={'subject_army_id':11,'target_province_id':2585,'date_raw':53176104,'snapshot_revision':17}
            scope=fixture._scope()
            variants={'new_attacker':scope,'new_defender':fixture._scope(initiator_is_defender=True,attacker_army_ids=[31,41],defender_army_ids=[11]),
                'join':fixture._scope(transition_kind='join_existing',selected_combat_id=71,selected_combat_array_index=1,join_side='defender',
                    defender_seed_character_id=None,initiator_is_defender=False,adjacency_kind_raw=0,opponent_army_ids=[],attacker_army_ids=[31],defender_army_ids=[41,11]),
                'none':fixture._scope(transition_kind='none',defender_seed_character_id=None,adjacency_kind_raw=0,opponent_army_ids=[],attacker_army_ids=[],defender_army_ids=[],combat_v3_participant_scope_ready=False),
                'observed':fixture._scope(scope_kind='post_contact_observation',transition_kind='in_combat',selected_combat_id=71,selected_combat_array_index=1,
                    join_side=None,defender_seed_character_id=None,initiator_is_defender=False,adjacency_kind_raw=0,loser_excluded_native_carmy_ids=[],
                    opponent_army_ids=[],attacker_army_ids=[31,11],defender_army_ids=[41])}
            bases={name:{'scope':value,'expected':copy.deepcopy(expected)} for name,value in variants.items()};cases=[];queries=[]
            def p(path,value):return {'op':'set','path':path,'value':value}
            def rm(path):return {'op':'remove','path':path}
            def add(name,base,patches,fix=None):
                value=copy.deepcopy(bases[base])
                for patch in patches:
                    target=value
                    for key in patch['path'][:-1]:target=target[key]
                    key=patch['path'][-1]
                    if patch['op']=='remove':del target[key]
                    else:target[key]=copy.deepcopy(patch['value'])
                try:output=producer.normalize_actual_contact_scope(value['scope'],**{'expected_'+key:v for key,v in value['expected'].items()})
                except ValueError:output={'error':'invalid_arguments'}
                row={'name':name,'base':base,'patches':patches,'legacy_expected':output}
                if fix is not None:row['intentional_type_fix']=fix
                cases.append(row)
            for name in variants:add('transition_'+name,name,[])
            add('raw_opponents_repeat_but_final_sides_dedup','new_attacker',[p(['scope','opponent_army_ids'],[31,31,41])])
            add('first_seen_opponent_order_retained','new_attacker',[p(['scope','opponent_army_ids'],[41,31,41]),p(['scope','defender_army_ids'],[41,31])])
            add('none_retains_loser_exclusion_evidence','none',[p(['scope','loser_excluded_native_carmy_ids'],[303,303])])
            for field,value in [('schema_version',0),('contract_stage','unknown'),('status','unavailable'),('stored_order_policy','other'),
                ('scope_kind','unknown'),('subject_army_id',True),('subject_army_id',11.0),('subject_army_id',0),
                ('subject_native_carmy_id',0),('subject_owner_character_id',0),('target_province_id',0),('date_raw',True),
                ('date_raw',53176104.0),('snapshot_revision',0),('snapshot_revision',17.0),('snapshot_revision',2**64),
                ('province_unit_army_ids',[31,11,41]),('province_unit_army_ids',[11,31,31,41]),('province_combat_ids',[71,51]),
                ('attacker_army_ids',[11,11]),('defender_army_ids',[31,11]),('opponent_army_ids',[11]),
                ('actual_contact_scope_ready',False),('actual_contact_scope_ready',None),('combat_v3_participant_scope_ready',False),
                ('selected_combat_id',71),('selected_combat_array_index',0),('join_side','defender'),('defender_seed_character_id',None),
                ('initiator_is_defender',True),('adjacency_kind_raw',2**31)]:
                add('bad_'+field+'_'+str(value),'new_attacker',[p(['scope',field],value)])
            add('required_nullable_missing','new_attacker',[rm(['scope','selected_combat_id'])])
            add('unknown_scope_field','new_attacker',[p(['scope','extra'],True)])
            for base,field,value in [('join','selected_combat_array_index',0),('join','defender_army_ids',[11,41]),
                ('none','defender_seed_character_id',19),('none','initiator_is_defender',True),
                ('observed','scope_kind','pre_contact_prediction'),('observed','attacker_army_ids',[31]),
                ('observed','loser_excluded_native_carmy_ids',[303]),('observed','adjacency_kind_raw',1)]:
                add(base+'_bad_'+field,base,[p(['scope',field],value)])
            add('uint64_max_exact','new_attacker',[p(['scope','snapshot_revision'],2**64-1),p(['expected','snapshot_revision'],2**64-1)])
            add('public_zero_subject','new_attacker',[p(['scope','subject_army_id'],0),p(['scope','province_unit_army_ids'],[0,31,41]),
                p(['scope','attacker_army_ids'],[0]),p(['expected','subject_army_id'],0)])
            add('public_zero_opponent','new_attacker',[p(['scope','province_unit_army_ids'],[0,11,41]),
                p(['scope','opponent_army_ids'],[0,41]),p(['scope','defender_army_ids'],[0,41])])
            for token in (True,1.0):add('version_type_fix_'+str(token),'new_attacker',[p(['scope','schema_version'],token)],'schema_version_must_be_integer_token')
            for subject in (0,11,2**31-1,True,11.0,-1,2**31):
                value={'operation':'build_query','subject_army_id':subject,'target_province_id':2585}
                try:output={'step':producer.query_actual_contact_scope_step(subject,2585)}
                except ValueError:output={'error':'invalid_arguments'}
                queries.append({'name':'query_subject_'+str(subject),'input':value,'expected':output})
            for text in ('query-actual-contact-scope-v1-0-at-2585','query-actual-contact-scope-v1-11-at-2585',
                'query-actual-contact-scope-v1-011-at-2585','query-actual-contact-scope-v1-11-at-0',
                'query-actual-contact-scope-v1-11-at-2585-at-7','query-actual-contact-scope-v1-2147483648-at-2585',None,True):
                queries.append({'name':'parse_'+str(text),'input':{'operation':'parse_query','step':text},
                    'expected':{'parsed':producer.parse_query_actual_contact_scope_step(text)}})
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/actual_contact_contract.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py',
                'ck3_autonomous_player/tests/unit/test_actual_contact_scope_contract.py','tools/ck3_live_run_id.py']
            output={'schema':'xar.actual-contact-producer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'qualification':'unchanged_python_producer_actual_outputs_type_fixes_explicit_no_native_qualification',
                'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},'bases':bases,'cases':cases,'query_cases':queries}
            print(json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':')))
            """;

    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository python new-output required"); }
        Path output = Path.of(args[2]); if (Files.exists(output)) { throw new IllegalArgumentException("new capture output required"); }
        Process process = new ProcessBuilder(args[1], "-c", SCRIPT, args[0]).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] captured = process.getInputStream().readNBytes(64 * 1024 + 1);
        if (!process.waitFor(90, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IllegalStateException("producer capture timeout"); }
        if (process.exitValue() != 0 || captured.length > 64 * 1024) { throw new IllegalStateException("producer failed or exceeded budget"); }
        Files.createDirectories(output.toAbsolutePath().getParent()); Files.write(output, captured);
        System.out.println("actual contact producer golden bytes=" + captured.length);
    }
}
