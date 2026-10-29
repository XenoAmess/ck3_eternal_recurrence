package org.xar.ck3.control.wave2.military.routewindowstep;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Runs only under the common coordinator's bounded Java Job. */
public final class CaptureRouteWindowStepGolden {
    private CaptureRouteWindowStepGolden() { }
    private static final String SCRIPT = """
            import datetime,hashlib,importlib,json,pathlib,subprocess,sys
            root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            producer=importlib.import_module('xar_autoplayer.bridge.route_contact_window_contract')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            cases=[]
            def build(name,subject=11,target=31,hostiles=None,days=3):
                rows=[21] if hostiles is None else hostiles
                value={'operation':'build','subject_army_id':subject,'target_province_id':target,'hostile_army_ids':rows,'horizon_days':days}
                try:expected={'step':producer.advance_route_contact_window_step(subject,target,rows,horizon_days=days)}
                except ValueError:expected={'error':'invalid_arguments'}
                cases.append({'name':name,'input':value,'expected':expected})
            def parse(name,step):
                cases.append({'name':name,'input':{'operation':'parse','step':step},
                    'expected':{'parsed':producer.parse_advance_route_contact_window_step(step)}})
            for days in (2,3):
                for subject,rows in [(11,[21]),(0,[2,1]),(11,[22,21,22]),(2147483647,[0,1]),(100,list(range(64)))]:
                    build('canonical_'+str(days)+'_'+str(subject),subject=subject,hostiles=rows,days=days)
                    parse('roundtrip_'+str(days)+'_'+str(subject),producer.advance_route_contact_window_step(subject,31,rows,horizon_days=days))
            for subject in (True,11.0,'11',-1,2147483648):build('bad_subject_'+str(subject),subject=subject)
            for target in (True,31.0,'31',0,-1,2147483648):build('bad_target_'+str(target),target=target)
            for days in (True,3.0,'3',0,1,4):build('bad_days_'+str(days),days=days)
            for rows in ([],[11],[True],[21.0],['21'],[-1],[2147483648],list(range(65)),None,{}):
                # None is intentionally passed as a literal invalid container here.
                if rows is None:
                    value={'operation':'build','subject_army_id':11,'target_province_id':31,'hostile_army_ids':None,'horizon_days':3}
                    try:producer.advance_route_contact_window_step(11,31,None)
                    except ValueError:cases.append({'name':'null_hostile_container','input':value,'expected':{'error':'invalid_arguments'}})
                else:build('bad_hostiles_'+str(rows),hostiles=rows)
            step=producer.advance_route_contact_window_step(11,31,[21,22],horizon_days=3)
            for name,value in [('null',None),('boolean',True),('integer',42),('float',42.0),('array',[]),('object',{}),
                ('empty',''),('prefix','advance-route-contact-window-v1-'),('wrong_prefix','advance-other-11'),
                ('subject_leading_zero',step.replace('v1-11','v1-011')),('target_leading_zero',step.replace('-to-31','-to-031')),
                ('day_leading_zero',step.replace('-days-3','-days-03')),('count_leading_zero',step.replace('-h-2','-h-02')),
                ('hostile_leading_zero',step.replace('-21-22','-021-22')),('reverse_order',step.replace('-21-22','-22-21')),
                ('duplicate_ids',step.replace('-21-22','-21-21')),('wrong_count',step.replace('-h-2','-h-3')),
                ('invalid_day',step.replace('-days-3','-days-1')),('subject_is_hostile',step.replace('v1-11','v1-21')),
                ('negative_subject',step.replace('v1-11','v1--11')),('unicode_subject',step.replace('v1-11','v1-١١')),
                ('plus_subject',step.replace('v1-11','v1-+11')),('trailing_delimiter',step+'-'),('trailing_text',step+'x'),
                ('subject_overflow',step.replace('v1-11','v1-2147483648')),('target_overflow',step.replace('-to-31','-to-2147483648'))]:
                parse('parse_'+name,value)
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/route_contact_window_contract.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py','tools/ck3_live_run_id.py']
            result={'schema':'xar.route-window-step-producer-golden/v1','machine_id':machine,
                'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'qualification':'actual_unchanged_python_constructor_parser_not_native_or_action_admission',
                'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},'cases':cases}
            print(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':')))
            """;

    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository python new-output required"); }
        Path output = Path.of(args[2]); if (Files.exists(output)) { throw new IllegalArgumentException("new capture path required"); }
        Process process = new ProcessBuilder(args[1], "-c", SCRIPT, args[0]).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] captured = process.getInputStream().readNBytes(64 * 1024 + 1);
        if (!process.waitFor(90, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IllegalStateException("producer capture timeout"); }
        if (process.exitValue() != 0 || captured.length > 64 * 1024) { throw new IllegalStateException("producer failed or exceeded budget"); }
        Files.createDirectories(output.toAbsolutePath().getParent()); Files.write(output, captured);
        System.out.println("route window step actual producer golden bytes=" + captured.length);
    }
}
