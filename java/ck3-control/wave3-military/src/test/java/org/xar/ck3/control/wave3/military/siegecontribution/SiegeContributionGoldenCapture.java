package org.xar.ck3.control.wave3.military.siegecontribution;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Calls real legacy normalizers and producer in the shared bounded offline capture Job only. */
public final class SiegeContributionGoldenCapture {
    private SiegeContributionGoldenCapture() { }
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python new-output required"); }
        Path output = Path.of(arguments[2]).toAbsolutePath();
        if (Files.exists(output)) { throw new IllegalArgumentException("fresh capture output required"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-c", SCRIPT, arguments[0], output.toString()))
                .directory(Path.of(arguments[0]).toFile()).inheritIO().start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.destroyForcibly(); throw new IllegalStateException("capture timeout; parent Job owns cleanup");
        }
        if (child.exitValue() != 0) { throw new IllegalStateException("legacy capture exited " + child.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 71_680) {
            throw new IllegalStateException("finite capture output required");
        }
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime
            from pathlib import Path
            repo=Path(sys.argv[1]);output=Path(sys.argv[2]);sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
            from xar_autoplayer.siege_subject_contribution_v1 import observe_siege_subject_contribution as observe
            from xar_autoplayer.bridge.siege_membership_contract import normalize_siege_province_unit_occurrences as occurrences
            from xar_autoplayer.bridge.province_besieging_army_selection_contract import normalize_province_besieging_army_selection as selection
            fixture=repo/'ck3_autonomous_player/tests/unit/fixtures/war6356_current_army_dto_v1.json'
            original=json.loads(fixture.read_bytes());snapshot=original['snapshot'];raw_province=snapshot['active_wars'][0]['objective_province_states'][0];raw_subject=snapshot['player_armies'][0]
            def take(value,names):return {key:copy.deepcopy(value[key]) for key in names if key in value}
            province=take(raw_province,['province_id','current_besieging_army_selection'])
            province['active_siege']={'province_unit_occurrences':copy.deepcopy(raw_province['active_siege']['province_unit_occurrences'])}
            subject=take(raw_subject,['army_id','controllable','current_province_id','move_target_province_id','route_province_ids'])
            base={'schema':'xar.siege-subject-contribution-input.v1','province':province,'subject':subject}
            def real_pipeline(request):
                province=copy.deepcopy(request['province']);subject=request['subject']
                if 'current_besieging_army_selection' in province:province['current_besieging_army_selection']=selection(province['current_besieging_army_selection'],name='capture.current_selection')
                siege=province.get('active_siege')
                if isinstance(siege,dict) and 'province_unit_occurrences' in siege:siege['province_unit_occurrences']=occurrences(siege['province_unit_occurrences'],name='capture.occurrences')
                return observe(province,subject)
            baseline=real_pipeline(base)
            if baseline!=observe(raw_province,raw_subject):raise ValueError('consumed projection changed actual6356 producer result')
            if baseline['status']!='excluded' or baseline['native_carmy_id']!=33554783:raise ValueError('retained actual6356 exclusion changed')
            rows=base['province']['active_siege']['province_unit_occurrences'];subject_id=base['subject']['army_id'];matching=[index for index,row in enumerate(rows) if row.get('public_unit_id')==subject_id]
            if not matching:raise ValueError('actual selected occurrence absent')
            selected=matching[0];cases=[]
            def add(name,change=None,origin='explicit_synthetic_variant',reject=False):
                request=copy.deepcopy(base)
                if change is not None:change(request)
                try:expected=real_pipeline(request)
                except ValueError as error:
                    if not reject:raise
                    cases.append({'name':name,'origin':origin,'request_raw':json.dumps(request,ensure_ascii=False,sort_keys=True,separators=(',',':')),'expected_rejection':True,'legacy_error_type':type(error).__name__});return
                if reject:raise ValueError('negative legacy guard did not reject '+name)
                cases.append({'name':name,'origin':origin,'request_raw':json.dumps(request,ensure_ascii=False,sort_keys=True,separators=(',',':')),'expected_rejection':False,'expected_decision':expected})
            def selected_row(request):return request['province']['active_siege']['province_unit_occurrences'][selected]
            def eligible(request):
                for row in request['province']['active_siege']['province_unit_occurrences']:
                    if row.get('public_unit_id')==subject_id:row.update(eligible=True,qualified_regiment_ids=[])
            def duplicate(request,mixed=False,different_native=False):
                eligible(request);rows=request['province']['active_siege']['province_unit_occurrences'];copy_row=copy.deepcopy(selected_row(request));copy_row['occurrence_index']=len(rows)
                if mixed:copy_row.update(eligible=False,qualified_regiment_ids=[])
                if different_native:copy_row['native_carmy_id']+=1
                rows.append(copy_row)
            add('actual6356_excluded',origin='historical_actual_consumed_projection')
            add('synthetic_eligible',eligible)
            add('repeated_subject_occurrences',duplicate)
            add('one_excluded_occurrence_excludes_subject',lambda r:duplicate(r,mixed=True))
            add('first_native_identity_retained',lambda r:duplicate(r,different_native=True))
            add('unknown_eligibility',lambda r:selected_row(r).update(eligible=None,qualified_regiment_ids=None))
            add('unknown_native_mapping',lambda r:selected_row(r).update(native_carmy_id=None))
            add('native_slot_zero_observation',lambda r:selected_row(r).update(native_carmy_id=0))
            add('wrong_public_unit',lambda r:selected_row(r).update(public_unit_id=99))
            add('no_selected_subject',lambda r:r.update(subject=None))
            add('uncontrollable_subject',lambda r:r['subject'].update(controllable=False))
            add('unknown_controllability',lambda r:r['subject'].update(controllable=None))
            add('subject_not_arrived',lambda r:r['subject'].update(current_province_id=r['province']['province_id']+1))
            add('committed_target',lambda r:r['subject'].update(move_target_province_id=r['province']['province_id']+1))
            add('nonempty_route',lambda r:r['subject'].update(route_province_ids=[r['province']['province_id']+1]))
            add('missing_route',lambda r:r['subject'].pop('route_province_ids'))
            add('unknown_occurrence_collection',lambda r:r['province']['active_siege'].update(province_unit_occurrences=None))
            add('known_empty_occurrence_collection',lambda r:r['province']['active_siege'].update(province_unit_occurrences=[]))
            add('unknown_selection',lambda r:r['province'].update(current_besieging_army_selection=None))
            add('unknown_selection_native_identity',lambda r:r['province']['current_besieging_army_selection'].update(native_carmy_id=None))
            add('selection_matches_first_subject',lambda r:r['province']['current_besieging_army_selection'].update(native_carmy_id=selected_row(r)['native_carmy_id']))
            add('public_slot_zero',lambda r:(r['subject'].update(army_id=0),selected_row(r).update(public_unit_id=0)))
            add('eligible_with_unread_regiments',lambda r:(eligible(r),selected_row(r).update(qualified_regiment_ids=None)))
            add('repeated_regiment_id_preserved',lambda r:(eligible(r),selected_row(r).update(qualified_regiment_ids=[7,7,3])))
            add('optional_normalizer_fields_missing',lambda r:(selected_row(r).pop('native_carmy_id'),r['province']['current_besieging_army_selection'].pop('public_unit_id')))
            add('unknown_sdk_extension',lambda r:(r['province'].update(future_sdk_value={'ratio':1.0}),selected_row(r).update(future_native_field='retained only by upstream DTO')))
            for name,field,value in [('float_occurrence_index','occurrence_index',0.0),('bool_occurrence_index','occurrence_index',True),('string_public_id','public_unit_id',str(subject_id)),('float_native_id','native_carmy_id',33554783.0),('bool_eligibility','eligible',1)]:
                add(name,lambda r,field=field,value=value:selected_row(r).update({field:value}),reject=True)
            add('excluded_regiments_null',lambda r:selected_row(r).update(eligible=False,qualified_regiment_ids=None),reject=True)
            add('array_position_mismatch',lambda r:selected_row(r).update(occurrence_index=123),reject=True)
            add('eligible_requires_native_identity',lambda r:(eligible(r),selected_row(r).update(native_carmy_id=None)),reject=True)
            add('unknown_eligibility_cannot_publish_regiments',lambda r:selected_row(r).update(eligible=None,qualified_regiment_ids=[]),reject=True)
            add('float_selection_identity',lambda r:r['province']['current_besieging_army_selection'].update(native_carmy_id=1.0),reject=True)
            add('bool_selection_controllability',lambda r:r['province']['current_besieging_army_selection'].update(controllable=1),reject=True)
            sources=['ck3_autonomous_player/src/xar_autoplayer/siege_subject_contribution_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/siege_membership_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/province_besieging_army_selection_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/tests/unit/test_stationary_excluded_siege_watch_6343.py','ck3_autonomous_player/tests/unit/test_foreign_leader_siege_material_service_12004.py','ck3_autonomous_player/tests/unit/fixtures/war6356_current_army_dto_v1.json']
            bindings=[{'path':path,'bytes':(repo/path).stat().st_size,'sha256':hashlib.sha256((repo/path).read_bytes()).hexdigest()} for path in sources]
            data={'schema':'xar.siege-subject-contribution-original-producer-golden.v1','machine_id':'xenoamess-full-tower-eb9d2c1186','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_origin_machine_id':original.get('machine_id','unknown'),'actual_live_qualification':False,'source_bindings':bindings,'capture_method':'Actual6356 retained excluded input plus explicitly synthetic eligible/unknown/guard variants. Real unchanged occurrence and selection normalizers -> observe_siege_subject_contribution. Raw JSON strings preserve wrong float/bool tokens into the Java decoder. Historical source is not a current native admission, no Game/RPC/ledger/service execution.','cases':cases}
            raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
            if len(raw)>71680:raise ValueError('finite70KiB golden exceeded: '+str(len(raw)))
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as handle:handle.write(raw)
            print(json.dumps({'machine_id':data['machine_id'],'observed_at_utc':data['observed_at_utc'],'cases':len(cases),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}))
            """;
}
