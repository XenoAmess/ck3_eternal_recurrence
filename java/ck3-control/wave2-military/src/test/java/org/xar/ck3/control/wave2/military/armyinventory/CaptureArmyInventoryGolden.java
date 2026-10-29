package org.xar.ck3.control.wave2.military.armyinventory;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit coordinator-run capture of unchanged legacy production functions. */
public final class CaptureArmyInventoryGolden {
    private CaptureArmyInventoryGolden() { }
    private static final String SCRIPT = """
            import copy, dataclasses, datetime, hashlib, importlib, json, pathlib, subprocess, sys
            root=pathlib.Path(sys.argv[1])
            sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
            sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            fixture=importlib.import_module('test_physical_army_inventory_v1')
            producer=importlib.import_module('xar_autoplayer.physical_army_inventory_v1')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            expected={'date_raw':fixture.DATE,'war_id':fixture.WAR,'subject_army_id':fixture.SUBJECT,
                'snapshot_id':'native:7','revision':8,'native_revision':7,
                'episode_run_id':'native-29829-2bc2d599f7f9','connection_generation':3,
                'published_player_ids':[fixture.SUBJECT],'published_allied_ids':[fixture.SUBJECT],
                'published_enemy_ids':[fixture.ENEMY],'contact_request_ids':[fixture.ENEMY],'contact_result_ids':[fixture.ENEMY]}
            native,snapshot,horizon=fixture.mailbox_fixture()
            bases={'shape':{'mode':'shape','receipt':fixture.receipt(),'expected':expected},
                'mailbox':{'mode':'mailbox','native_receipt':native,'starting':snapshot,'current':copy.deepcopy(snapshot),
                    'horizon':horizon,'query_sequence':9,'subject_army_id':fixture.SUBJECT,'requested_hostiles':[fixture.ENEMY]}}
            cases=[]
            def setv(path,value): return {'op':'set','path':path,'value':value}
            def remove(path): return {'op':'remove','path':path}
            def add(name,base,patches):
                value=copy.deepcopy(bases[base])
                for patch in patches:
                    target=value
                    for segment in patch['path'][:-1]: target=target[segment]
                    key=patch['path'][-1]
                    if patch['op']=='remove': del target[key]
                    else: target[key]=copy.deepcopy(patch['value'])
                if base=='shape':
                    e=value['expected']
                    args={('expected_'+key if key in ('date_raw','war_id','subject_army_id','snapshot_id','revision','native_revision','episode_run_id','connection_generation') else key):v for key,v in e.items()}
                    checked=producer.validate_physical_army_inventory_shape_v1(value['receipt'],**args)
                else:
                    checked=producer.validate_native_physical_inventory_mailbox_v1(value['native_receipt'],starting=value['starting'],
                        current=value['current'],horizon=value['horizon'],query_sequence=value['query_sequence'],
                        subject_army_id=value['subject_army_id'],requested_hostiles=tuple(value['requested_hostiles']))
                cases.append({'name':name,'base':base,'patches':patches,'expected':dataclasses.asdict(checked)})
            add('shape_valid_read_only','shape',[])
            for key,value in [('status','partial'),('source_build','CK3 1.20.0.4'),('date_raw',fixture.DATE+24),
                ('date_raw',float(fixture.DATE)),('war_id',True),('subject_army_id',fixture.SUBJECT+1),
                ('snapshot_id','old'),('revision',7),('native_revision',6),('episode_run_id','old'),('connection_generation',2),
                ('storage_capacity',0),('storage_capacity',1000001),('storage_capacity',True),('slots_scanned',3),
                ('empty_slots',1),('canonical_units',1),('invalid_id_slots',1),('noncanonical_slots',1),('unresolved_slots',1),
                ('units',None),('player_army_ids',[]),('allied_army_ids',[]),('hostile_army_ids',[]),
                ('contact_hostile_army_ids',[]),('retreating_hostile_army_ids',[fixture.ENEMY])]:
                add('shape_'+key+'_'+str(value),'shape',[setv(['receipt',key],value)])
            for key,value in [('army_id',0),('army_id',True),('army_id',float(fixture.ENEMY)),('army_id',fixture.SUBJECT),
                ('war_side','unknown'),('war_side',['hostile']),('owner_character_id',None),('current_province_id',0),
                ('retreating',1),('controllable',1),('army_state_code',6),('army_state_code',10),('in_combat',True),
                ('in_combat',None),('route_read_status','target_only'),('route_source_count',2),('route_province_ids',[0])]:
                add('unit_'+key+'_'+str(value),'shape',[setv(['receipt','units',1,key],value)])
            add('subject_route_incomplete','shape',[setv(['receipt','units',0,'route_read_status'],'target_only')])
            add('subject_not_controllable','shape',[setv(['receipt','units',0,'controllable'],False)])
            add('retreating_hostile_never_silently_excluded','shape',[setv(['receipt','units',1,'retreating'],True),
                setv(['receipt','contact_hostile_army_ids'],[]),setv(['receipt','retreating_hostile_army_ids'],[fixture.ENEMY]),
                setv(['expected','contact_request_ids'],[]),setv(['expected','contact_result_ids'],[])])
            add('capacity_maximum_complete','shape',[setv(['receipt','storage_capacity'],1000000),
                setv(['receipt','slots_scanned'],1000000),setv(['receipt','empty_slots'],999998)])
            add('shape_projection_retains_native_extension','shape',[setv(['receipt','future_field'],True)])
            for key in ('published_player_ids','published_allied_ids','published_enemy_ids','contact_request_ids','contact_result_ids'):
                add('expected_'+key+'_mismatch','shape',[setv(['expected',key],[])])
            add('exact_large_integer_army_identity','shape',[setv(['receipt','units',1,'army_id'],2**100),
                setv(['receipt','hostile_army_ids'],[2**100]),setv(['receipt','contact_hostile_army_ids'],[2**100]),
                setv(['expected','published_enemy_ids'],[2**100]),setv(['expected','contact_request_ids'],[2**100]),
                setv(['expected','contact_result_ids'],[2**100])])
            add('mailbox_valid_read_only','mailbox',[])
            for key,value in [('mailbox_pump_epoch',0),('mailbox_thread_id',False),('mailbox_date_raw',fixture.DATE+24),
                ('mailbox_paused',False),('same_source_across_route',False),('query_sequence',10),('native_revision',6),
                ('unresolved_slots',1),('slots_scanned',3)]:
                add('mailbox_'+key,'mailbox',[setv(['native_receipt',key],value)])
            add('mailbox_unknown_field','mailbox',[setv(['native_receipt','extra'],True)])
            add('mailbox_required_field_missing','mailbox',[remove(['native_receipt','mailbox_paused'])])
            add('mailbox_unit_unknown_field','mailbox',[setv(['native_receipt','units',0,'extra'],True)])
            for key,value in [('revision',9),('map_ready',False),('active_event',{'instance_id':7}),
                ('pending_character_interaction',{'interaction_id':9}),('route_contact_horizon_supported',False)]:
                add('public_frame_changed_'+key,'mailbox',[setv(['current',key],value)])
            add('connection_changed','mailbox',[setv(['current','diagnostics','connection_generation'],4)])
            add('additional_capability_changed','mailbox',[setv(['current','another_supported'],True)])
            add('missing_capability_not_empty','mailbox',[setv(['starting','capabilities'],[])])
            add('h3937_actor_guard','mailbox',[setv([frame,'played_character','character_id'],29830) for frame in ('starting','current')])
            add('episode_actor_guard','mailbox',[setv([frame,'episode_character_id'],29830) for frame in ('starting','current')])
            add('h3937_episode_guard','mailbox',[setv([frame,'episode_run_id'],'another') for frame in ('starting','current')])
            add('h3937_war_guard','mailbox',[setv([frame,'active_wars',0,'war_id'],fixture.WAR+1) for frame in ('starting','current')])
            add('route_contact_result_missing','mailbox',[remove(['horizon','hostile_army_ids'])])
            paths=['ck3_autonomous_player/src/xar_autoplayer/physical_army_inventory_v1.py',
                'ck3_autonomous_player/tests/unit/test_physical_army_inventory_v1.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','tools/ck3_live_run_id.py']
            result={'schema':'xar.army-inventory-producer-golden/v1','machine_id':machine,
                'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'qualification':'actual_unchanged_python_producer_on_committed_source_fixtures_not_native_or_live',
                'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},
                'bases':bases,'cases':cases}
            print(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':')))
            """;

    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository python new-output required"); }
        Path output = Path.of(args[2]);
        if (Files.exists(output)) { throw new IllegalArgumentException("capture output must be new"); }
        Process process = new ProcessBuilder(args[1], "-c", SCRIPT, args[0]).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] captured = process.getInputStream().readNBytes(35 * 1024 + 1);
        if (!process.waitFor(90, TimeUnit.SECONDS)) {
            process.destroyForcibly(); throw new IllegalStateException("producer capture timeout");
        }
        if (process.exitValue() != 0 || captured.length > 35 * 1024) {
            throw new IllegalStateException("producer capture failed or exceeded 35 KiB: " + process.exitValue());
        }
        Files.createDirectories(output.toAbsolutePath().getParent()); Files.write(output, captured);
        System.out.println("army inventory actual producer golden bytes=" + captured.length);
    }
}
