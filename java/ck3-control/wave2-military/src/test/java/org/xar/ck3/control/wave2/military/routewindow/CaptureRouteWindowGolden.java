package org.xar.ck3.control.wave2.military.routewindow;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit coordinator-only capture; normal JUnit never launches Python. */
public final class CaptureRouteWindowGolden {
    private CaptureRouteWindowGolden() { }
    private static final String SCRIPT = """
            import copy,datetime,hashlib,importlib,json,pathlib,subprocess,sys
            root=pathlib.Path(sys.argv[1])
            sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
            sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            fixture=importlib.import_module('test_normal_three_day_route_window')
            from xar_autoplayer.bridge.route_contact_window_projection_v1 import project_route_contact_window_v1
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            bases={'free':{'horizon':fixture._horizon(),'horizon_days':3},
                'day_two':{'horizon':fixture._horizon(second_day_contact=True),'horizon_days':3}}
            cases=[]
            def p(path,value):return {'op':'set','path':path,'value':value}
            def rm(path):return {'op':'remove','path':path}
            def add(name,base,patches):
                value=copy.deepcopy(bases[base])
                for patch in patches:
                    target=value
                    for key in patch['path'][:-1]:target=target[key]
                    key=patch['path'][-1]
                    if patch['op']=='remove':del target[key]
                    else:target[key]=copy.deepcopy(patch['value'])
                output=project_route_contact_window_v1(value['horizon'],horizon_days=value['horizon_days'])
                cases.append({'name':name,'base':base,'patches':patches,'expected':output})
            add('three_day_frozen_routes_free','free',[])
            add('second_day_contact_retains_one_whole_day','day_two',[])
            for days in (1,2,3):
                add('free_'+str(days)+'_day_prefix','free',[p(['horizon_days'],days)])
                for offset in (0,1,23,24,25,47,48,49,71,72,73):
                    add('closed_boundary_d'+str(days)+'_offset'+str(offset),'free',[
                        p(['horizon_days'],days),p(['horizon','subject_route','route_province_ids'],[]),
                        p(['horizon','subject_route','arrival_date_raws'],[]),
                        p(['horizon','hostile_routes',0,'route_province_ids'],[20]),
                        p(['horizon','hostile_routes',0,'arrival_date_raws'],[fixture._START+offset])])
            for key,value in [('status','unavailable'),('date_raw',True),('date_raw',24000.0),('date_raw',2147483640),
                ('subject_route',None),('hostile_routes',None),('hostile_army_ids',None),('hostile_army_ids',[]),
                ('hostile_army_ids',[22])]:
                add('missing_'+key+'_'+str(value),'free',[p(['horizon',key],value)])
            for key,value in [('timeline_observable',False),('current_province_id',0),('current_province_id',20.0),
                ('route_province_ids',None),('route_province_ids',[31]),('arrival_date_raws',None),
                ('arrival_date_raws',[23999,24240]),('arrival_date_raws',[24240,24120]),
                ('arrival_date_raws',[24120.0,24240])]:
                add('subject_bad_'+key+'_'+str(value),'free',[p(['horizon','subject_route',key],value)])
            add('hostile_row_missing','free',[p(['horizon','hostile_routes'],[None])])
            add('missing_subject_container','free',[rm(['horizon','subject_route'])])
            add('missing_current_timeline','free',[rm(['horizon','subject_route','timeline_observable'])])
            add('opaque_normalized_horizon_extension','free',[p(['horizon','unrelated_source_extension'],True)])
            add('reverse_edge_conflict_before_either_arrival','free',[
                p(['horizon','subject_route','route_province_ids'],[31]),p(['horizon','subject_route','arrival_date_raws'],[24120]),
                p(['horizon','hostile_routes',0,'current_province_id'],31),
                p(['horizon','hostile_routes',0,'route_province_ids'],[20]),p(['horizon','hostile_routes',0,'arrival_date_raws'],[24121])])
            add('closed_province_endpoint_and_edge_order','free',[
                p(['horizon','subject_route','route_province_ids'],[31]),p(['horizon','subject_route','arrival_date_raws'],[24048]),
                p(['horizon','hostile_routes',0,'current_province_id'],31),
                p(['horizon','hostile_routes',0,'route_province_ids'],[20]),p(['horizon','hostile_routes',0,'arrival_date_raws'],[24048])])
            add('native_current_not_effective_origin','free',[p(['horizon','subject_route','effective_origin_province_id'],99)])
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/route_contact_window_projection_v1.py',
                'ck3_autonomous_player/tests/unit/test_normal_three_day_route_window.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','tools/ck3_live_run_id.py']
            result={'schema':'xar.route-window-producer-golden/v1','machine_id':machine,
                'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'qualification':'actual_unchanged_python_projection_on_committed_source_fixtures_not_native_or_live',
                'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},'bases':bases,'cases':cases}
            print(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':')))
            """;

    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository python new-output required"); }
        Path output = Path.of(args[2]);
        if (Files.exists(output)) { throw new IllegalArgumentException("capture output must be new"); }
        Process process = new ProcessBuilder(args[1], "-c", SCRIPT, args[0]).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] captured = process.getInputStream().readNBytes(64 * 1024 + 1);
        if (!process.waitFor(90, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IllegalStateException("producer capture timeout"); }
        if (process.exitValue() != 0 || captured.length > 64 * 1024) {
            throw new IllegalStateException("projection capture failed or exceeded budget: " + process.exitValue());
        }
        Files.createDirectories(output.toAbsolutePath().getParent()); Files.write(output, captured);
        System.out.println("route window actual producer golden bytes=" + captured.length);
    }
}
