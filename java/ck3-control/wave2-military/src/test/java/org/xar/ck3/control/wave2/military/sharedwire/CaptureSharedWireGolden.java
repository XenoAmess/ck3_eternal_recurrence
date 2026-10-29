package org.xar.ck3.control.wave2.military.sharedwire;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Offline capture of the unchanged original pure transport producer/consumers; shared Job owner only. */
public final class CaptureSharedWireGolden {
    private CaptureSharedWireGolden() { }
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) throw new IllegalArgumentException("repo python new-output.json.gz required");
        Path output = Path.of(arguments[2]).toAbsolutePath();
        if (Files.exists(output)) throw new IllegalArgumentException("new output required");
        Process child = new ProcessBuilder(List.of(arguments[1], "-B", "-X", "utf8", "-c", SCRIPT,
                arguments[0], output.toString())).directory(Path.of(arguments[0]).toFile()).inheritIO().start();
        if (!child.waitFor(60, TimeUnit.SECONDS)) { child.destroyForcibly();
            throw new IllegalStateException("capture timeout; shared Job owns remaining descendants"); }
        if (child.exitValue() != 0) throw new IllegalStateException("original capture exit " + child.exitValue());
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 16384)
            throw new IllegalStateException("finite shared wire golden absent or oversized");
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime,subprocess,gzip
            from pathlib import Path
            repo=Path(sys.argv[1]); output=Path(sys.argv[2])
            sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge.army_strengths_manager_shared_wire import FIELD_NAMES,pack_army_strengths_manager_inputs as pack,expand_army_strengths_manager_inputs as expand
            key='army_manager_inputs_shared_v1'; own='current_army_combat_roles_phase_inputs_v1'
            extra=['current_army_condition30_inputs_v1','current_army_flag20_inputs_v1','current_army_flag21_inputs_v1','current_pre_date_character_prefix_inputs_v1']
            def body(n):return {'opaque_transport_marker':n}
            def base(names=FIELD_NAMES):return {'unrelated_root':{'preserved':True},'army_strengths':[dict(army_id=i,unrelated_row={'zero':0},**{n:body(j) for j,n in enumerate(names)}) for i in [0,17]]}
            cases=[]
            def add(name,value,valid=True):
                before=copy.deepcopy(value); packed=pack(value)
                if before!=value:raise ValueError('original pack mutated input')
                expanded=expand(packed); attached=expand(packed,detached=False)
                if expanded!=attached:raise ValueError('original detached values differ')
                cases.append({'name':name,'input':value,'expected_packed':packed,'expected_expanded':expanded,'pack_returned_original_object':packed is value,'valid_token_domain':valid})
            add('all_six_base_families',base())
            add('all_ten_families',base(FIELD_NAMES+tuple(extra)))
            add('single_owned_family',base((own,)))
            add('only_additional_no_base',base(tuple(extra)))
            add('empty_rows',{'army_strengths':[]})
            add('missing_rows',{'another_extension':True})
            one=base();one['army_strengths'].pop();add('single_row',one)
            badrows=base();badrows['army_strengths'][1]=None;add('nonobject_row',badrows)
            for family in FIELD_NAMES:
                v=base();v['army_strengths'][1].pop(family);add('missing_base_'+family,v)
            v=base();v['army_strengths'][1][own]['native_zero']=1;add('divergent_base',v)
            v=base();v['army_strengths'][0][own]=[];add('first_family_wrong_container',v)
            v=base();v['army_strengths'][0][own]=None;v['army_strengths'][1][own]=None;add('known_null_family',v)
            v=base(FIELD_NAMES+tuple(extra));v['army_strengths'][1][extra[1]]={'divergent':True};add('divergent_additional_retains_inline',v)
            for name,identity in [('negative',-1),('bool',True),('float',17.0),('overflow',2**31),('duplicate',0)]:
                v=base();v['army_strengths'][1]['army_id']=identity;add('invalid_public_id_'+name,v)
            v=base();v[key]={'deliberately_opaque':'existing_capsule_pack_returns_original'}
            cases.append({'name':'existing_bundle','input':v,'expected_packed':pack(v),'pack_returned_original_object':pack(v) is v,'valid_token_domain':True})
            for name,token in [('bool',True),('float',1.0)]:
                v=base((own,));v['army_strengths'][0][own]={'same_python_value':1};v['army_strengths'][1][own]={'same_python_value':token}
                add('historical_python_equal_'+name,v,False)
            good=pack(base()); failures=[]
            def reject(name,change):
                value=copy.deepcopy(good);change(value)
                try:expand(value)
                except ValueError:failures.append({'name':name,'input':value,'expected_error':'ValueError'})
                else:raise ValueError('original malformed expansion unexpectedly accepted '+name)
            reject('bundle_extra',lambda v:v[key].update(extra=True))
            reject('bundle_missing_fields',lambda v:v[key].pop('fields'))
            reject('bool_version',lambda v:v[key].update(schema_version=True))
            reject('float_version',lambda v:v[key].update(schema_version=1.0))
            reject('empty_ids',lambda v:v[key].update(army_ids=[]))
            reject('duplicate_ids',lambda v:v[key].update(army_ids=[0,0]))
            reject('wrong_order',lambda v:v[key].update(army_ids=[17,0]))
            reject('row_duplicate_id',lambda v:v['army_strengths'][1].update(army_id=0))
            reject('bool_row_id',lambda v:v['army_strengths'][1].update(army_id=True))
            reject('overflow_row_id',lambda v:v['army_strengths'][1].update(army_id=2**31))
            reject('unsupported_family',lambda v:v[key]['fields'].update(unsupported_family={}))
            reject('empty_fields',lambda v:v[key].update(fields={}))
            reject('wrong_family_container',lambda v:v[key]['fields'].update({own:[]}))
            reject('inline_collision',lambda v:v['army_strengths'][0].update({own:None}))
            sources=['ck3_autonomous_player/src/xar_autoplayer/bridge/army_strengths_manager_shared_wire.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/episode04_ready_t0_12004.py',
                'ck3_autonomous_player/tests/unit/test_army_manager_shared_normalization_reuse_12004.py']
            bindings=[{'path':p,'bytes':(repo/p).stat().st_size,'sha256':hashlib.sha256((repo/p).read_bytes()).hexdigest()} for p in sources]
            machine=subprocess.check_output([sys.executable,'-B',str(repo/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()
            data={'schema':'xar.shared-wire-original-producer-golden.v1','machine_id':machine,
                'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_bindings':bindings,
                'origin':'Explicit synthetic pure-transport carriers. Family bodies intentionally opaque to transport; no family readiness or Game qualification.',
                'actual_live_qualification':False,'base_family_names':list(FIELD_NAMES),'additional_family_names':extra,
                'cases':cases,'rejections':failures}
            raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
            packed=gzip.compress(raw,mtime=0)
            if len(raw)>262144 or len(packed)>16384:raise ValueError('finite shared-wire fixture budget exceeded')
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as handle:handle.write(packed)
            print(json.dumps({'machine_id':machine,'observed_at_utc':data['observed_at_utc'],'cases':len(cases),'rejections':len(failures),
                'bytes':len(packed),'uncompressed_bytes':len(raw),'sha256':hashlib.sha256(packed).hexdigest()}))
            """;
}
