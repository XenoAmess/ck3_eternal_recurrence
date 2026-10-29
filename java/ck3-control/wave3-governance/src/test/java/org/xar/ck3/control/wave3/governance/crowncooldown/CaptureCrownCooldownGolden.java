package org.xar.ck3.control.wave3.governance.crowncooldown;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Once-only capture of the original pure native-clock value producers. */
public final class CaptureCrownCooldownGolden {
    private CaptureCrownCooldownGolden() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repository-root existing-python output-json"); }
        Path root = Path.of(arguments[0]).toRealPath();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("never overwrite a captured original"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-B", "-c", SCRIPT, root.toString()))
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var reader = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = reader.submit(() -> child.getInputStream().readNBytes(65_537));
            if (!child.waitFor(60, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IllegalStateException("original Crown cooldown capture timed out");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) { child.destroyForcibly(); } }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > 65_536) {
            throw new IllegalStateException("original cooldown capture failed: exit=" + child.exitValue() + ", bytes=" + raw.length);
        }
        Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        System.out.println("Captured original Crown cooldown values: " + raw.length + " bytes at " + output);
    }

    private static final String SCRIPT = """
            import sys,json,copy,hashlib,dataclasses,importlib.util,subprocess,datetime
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/crown_authority_cooldown_clock_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/realm_law_paused_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/crown_authority_formal_consumer_v1.py','ck3_autonomous_player/tests/unit/test_crown_authority_cooldown_clock_12004.py']
            def refs():return [{'path':p,'bytes':len((root/p).read_bytes()),'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths]
            before=refs()
            spec=importlib.util.spec_from_file_location('original_crown_clock_test',root/paths[3]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            module.test_actual_duration_factors_and_same_query_clock_meaning_12004()
            from xar_autoplayer.bridge.crown_authority_cooldown_clock_12004 import scale_native_duration_literal_12004 as scale,interpret_crown_cooldown_native_clock_12004 as interpret
            from xar_autoplayer.bridge.realm_law_paused_private_transport import normalize_crown_authority_cooldown_turn_tick_v1 as ticknorm,COOLDOWN_EXPIRY_TYPE,COOLDOWN_REMAINING_UNIT,COOLDOWN_PROJECTED_REMAINING_UNIT,COOLDOWN_TURN_TICK_SOURCE
            literals=[];clocks=[];rejections=[]
            def wire(value):return json.loads(json.dumps(dataclasses.asdict(value)))
            for token in (1300,1301,1302,1327):
                for literal in (-2147483648,-3,0,1,2147483647):
                    request={'schema':'xar.java-crown-duration-literal/v1','token_id':token,'literal_i32':literal}
                    literals.append({'name':'token-'+str(token)+'-literal-'+str(literal),'request':request,'expected':wire(scale(token,literal))})
            for token in (0,0x1300,1<<100):
                literals.append({'name':'unknown-token-'+str(token),'request':{'schema':'xar.java-crown-duration-literal/v1','token_id':token,'literal_i32':20},'expected':wire(scale(token,20))})
            date=53288232
            base={'read_available':True,'present':True,'timed':True,'expiry_raw':7304,'current_clock_raw':4,'remaining_raw':7300,'retry_date_raw':None,'expiry_type':COOLDOWN_EXPIRY_TYPE,'remaining_unit':COOLDOWN_REMAINING_UNIT}
            def add_clock(name,raw=None,day=date,tick=None):
                raw=copy.deepcopy(base if raw is None else raw)
                if tick is not None:ticknorm(tick)
                request={'schema':'xar.java-crown-cooldown-clock/v1','date_raw':day,'raw_observation':raw,'turn_tick_observation':tick}
                clocks.append({'name':name,'request':request,'expected':wire(interpret(raw,date_raw=day))})
            add_clock('timed_unqualified_native_counter')
            for expiry,current,remaining in ((7,8,-1),(8,8,0),(0,-2147483648,-2147483648)):
                add_clock('signed-remaining-'+str(remaining),{**base,'expiry_raw':expiry,'current_clock_raw':current,'remaining_raw':remaining})
            add_clock('absent_is_not_timed_minus_one',{**base,'present':False,'timed':False,'expiry_raw':None,'remaining_raw':-1,'retry_date_raw':date})
            add_clock('present_untimed_native_sentinel',{**base,'timed':False,'expiry_raw':-1,'remaining_raw':-1})
            add_clock('unavailable_retains_nulls',{**base,'read_available':False,'present':None,'timed':None,'expiry_raw':None,'current_clock_raw':None,'remaining_raw':None})
            for name,count,remaining,day in [('single_same_query_match',1,20,53169072),('double_match_odd_remaining',2,21,53169072),('uint64_count_beyond_js_safe',(1<<53)+1,20,53169072),('uint64_max_context_count',(1<<64)-1,2147483647,53169072),('signed32_calendar_wrap',1,20,2147483600)]:
                steps=(remaining+count-1)//count;bits=(day+steps*24)&0xffffffff;retry=bits if bits<0x80000000 else bits-0x100000000
                raw={**base,'expiry_raw':remaining+4 if remaining<2147483647 else 2147483647,'current_clock_raw':4 if remaining<2147483647 else 0,'remaining_raw':remaining,'retry_date_raw':retry,'remaining_unit':COOLDOWN_PROJECTED_REMAINING_UNIT}
                tick={'source':COOLDOWN_TURN_TICK_SOURCE,'read_available':True,'manager_match_count':count,'manager_contains_context':True,'scalar_tail_allows_tick':True,'context_tick_eligible':True,'unavailable_reason':None}
                add_clock(name,raw,day,tick)
            def rejected(name,operation,request):
                try:
                    if operation=='literal':scale(request['token_id'],request['literal_i32'])
                    else:interpret(request['raw_observation'],date_raw=request['date_raw'])
                except ValueError as error:
                    rejections.append({'name':name,'operation':operation,'raw_request_json':json.dumps(request,ensure_ascii=False,separators=(',',':'),allow_nan=False),'legacy_error':str(error)})
                else:raise RuntimeError('original producer unexpectedly accepted negative fixture '+name)
            for name,token,literal in [('bool_token',True,20),('float_token',1302.0,20),('bool_literal',1302,True),('float_literal',1302,20.0),('literal_above_i32',1302,2147483648)]:
                rejected(name,'literal',{'schema':'xar.java-crown-duration-literal/v1','token_id':token,'literal_i32':literal})
            for name,mutation in [('bool_current',{'current_clock_raw':True}),('float_remaining',{'remaining_raw':7300.0}),('wrong_native_remaining',{'remaining_raw':7299}),('unexpected_calendar_retry',{'retry_date_raw':date+24}),('unknown_clock_unit',{'remaining_unit':'invented_days'})]:
                rejected(name,'clock',{'schema':'xar.java-crown-cooldown-clock/v1','date_raw':date,'raw_observation':{**base,**mutation},'turn_tick_observation':None})
            after=refs()
            if before!=after:raise RuntimeError('original Crown cooldown source changed during capture')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            value={'schema':'xar.java-crown-cooldown-original-producer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'historical_native_observation_machine_id':'unknown','scope':'Actual original literal producer, raw9 normalizer, turn-tick normalizer and clock interpreter over source-shaped unit fixtures. Projected cases explicitly carry same-query count math; complete native law capture and processed timed-suffix qualification remain external. No native whole packet, Game or live RPC.','source_refs':before,'source_refs_unchanged':True,'original_unit_methods_executed':1,'original_unit_skips':0,'literal_cases':literals,'clock_cases':clocks,'wire_rejections':rejections}
            print(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
