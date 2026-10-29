package org.xar.ck3.control.wave2.military.commander;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** M7-only capture of actual legacy producer/consumer over retained whole native fixture packets. */
public final class CommanderGoldenCapture {
    private CommanderGoldenCapture() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 5) { throw new IllegalArgumentException("repository python-exe retained-native-dir fresh-output machine-id required"); }
        Path repository = Path.of(args[0]).toAbsolutePath().normalize(); Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("fresh capture output required"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM, repository.toString(), args[2], args[4]));
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("PYTHONPATH", repository.resolve("ck3_autonomous_player/src") + File.pathSeparator + repository);
        builder.redirectError(ProcessBuilder.Redirect.INHERIT); Process process = builder.start(); byte[] bytes;
        try (var reader = Executors.newSingleThreadExecutor()) {
            var response = reader.submit(() -> { try (var stream = process.getInputStream()) { return stream.readNBytes(98_305); } });
            if (!process.waitFor(60, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IOException("legacy commander capture timeout"); }
            try { bytes = response.get(); } catch (ExecutionException error) { throw new IOException("capture read failed", error.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 98_304) { throw new IOException("capture failed/over budget: exit=" + process.exitValue() + " bytes=" + bytes.length); }
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW); System.out.println("captured " + bytes.length + " bytes to " + output);
    }
    private static final String PROGRAM = """
            import sys,json,copy,hashlib,datetime,types,importlib
            from pathlib import Path
            root=Path(sys.argv[1]); native=Path(sys.argv[2]); machine=sys.argv[3]
            # Skip only the eager bridge package re-export initializer; actual leaf/driver source is imported unchanged.
            import xar_autoplayer
            package=types.ModuleType('xar_autoplayer.bridge'); package.__path__=[str(root/'ck3_autonomous_player/src/xar_autoplayer/bridge')]; sys.modules[package.__name__]=package
            normal=importlib.import_module('xar_autoplayer.bridge.army_commander_candidates')
            producer=importlib.import_module('xar_autoplayer.commander_quality_formal_proposal_v1')
            consumer=importlib.import_module('xar_autoplayer.commander_quality_formal_consumer_v1')
            driver=importlib.import_module('xar_autoplayer.bridge.driver')
            snapshot=dict(snapshot_id='retained-native:11',revision=4,native_revision=11,date_raw=53288448,paused=True,player_armies=[dict(army_id=83886367,controllable=True)])
            cases=[]; plans=[]; pins=[]
            def pin(path,label=None):
                raw=path.read_bytes(); pins.append(dict(path=label or str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
            names=['quality-current-outside-pool.json','quality-current-zero.json','quality-current-unavailable.json','quality-candidate-comparison.json']
            inputs={}
            def put(name,value,original=False):
                if not original: value['current_movement_speed']=None
                normalized=normal.normalize_army_commander_candidates_v1(value,expected_army_id=value['army_id'],expected_snapshot_revision=11,expected_date_raw=53288448)
                packet=dict(schema='xar.java.commander-quality-input.v1',snapshot=copy.deepcopy(snapshot),query_sequence=7,candidates=normalized)
                result=producer.propose_commander_quality_v1(normalized,snapshot=snapshot,query_sequence=7)
                cases.append(dict(name=name,input=packet,expected=result,original_whole_packet=original)); inputs[name]=packet
                return packet
            for name in names:
                path=native/name; pin(path); packet=json.loads(path.read_text(encoding='utf-8-sig')); assert packet['ok'] is True
                put(name,packet['result']['army_commander_candidates'],True)
            base=copy.deepcopy(inputs[names[0]]['candidates'])
            for name,quality in [('equal-score',25),('negative-score',-30),('int32-min-score',-(1<<31))]:
                value=copy.deepcopy(base); value['current_commander']['current_native_ai_base_quality']['value']=quality; put(name,value)
            value=copy.deepcopy(base); value['current_commander'].pop('current_native_ai_base_quality'); put('legacy-quality-missing',value)
            value=copy.deepcopy(base); value['current_commander']['current_native_ai_base_quality']=None; put('legacy-quality-null',value)
            value=copy.deepcopy(base); value['candidates'][1]['native_ai_base_quality']=25; put('candidate-tie-keeps-first',value)
            value=copy.deepcopy(base); value['candidates'][0]['can_assign']=False; put('higher-ineligible-candidate',value)
            value=copy.deepcopy(base); value['current_commander']=dict(status='absent',character_id=None,unavailable_reason=None); value['current_movement_speed']=None; put('absent-role',value)
            value=copy.deepcopy(value); value['candidates']=[]; put('absent-no-candidate',value)
            value=copy.deepcopy(base); value['current_commander']['status']='unavailable'; value['current_commander']['current_native_ai_base_quality']=None; value['current_commander'].pop('current_total_martial'); put('unknown-role-not-absent',value)
            value=copy.deepcopy(base); value['current_commander']['current_native_ai_base_quality']['value']=-(1<<31); value['candidates'][0]['native_ai_base_quality']=(1<<31)-1; put('gain-exceeds-signed32',value)
            caps=[normal.QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY,consumer.ASSIGN_ARMY_COMMANDER_V1_CAPABILITY]
            def plan_case(name,queries,phase='native_war_counterpolicy_hold',step=None,pursuit=None,capabilities=None):
                s=copy.deepcopy(snapshot); s['player_armies']=[dict(army_id=army,controllable=True) for army,_ in queries] or copy.deepcopy(snapshot['player_armies'])
                p=dict(revision=4,snapshot_id=s['snapshot_id'],plan=dict(phase=phase,selected_step=step,required_step='baseline-required',opaque_extension=dict(decimal_weight=1.25)))
                if pursuit is not None: p['plan']['pursuit']=dict(army_id=pursuit)
                q=[]
                for army,value in queries:
                    if isinstance(value,str): q.append(dict(army_id=army,proposal_input=None,unavailable_reason=value)); continue
                    value=copy.deepcopy(value); value['snapshot']=copy.deepcopy(s); value['candidates']['army_id']=army; value['candidates'].pop('current_movement_speed',None)
                    q.append(dict(army_id=army,proposal_input=value,unavailable_reason=None))
                class Port:
                    def __init__(self): self.calls=[]
                    def query_army_commander_candidates_v1(self,army_id,*,expected_revision=None):
                        row=q[len(self.calls)]; self.calls.append(army_id); assert row['army_id']==army_id and expected_revision==4
                        if row['unavailable_reason'] is not None: raise driver.BridgeUnavailableError(row['unavailable_reason'])
                        value=row['proposal_input']; result=producer.propose_commander_quality_v1(value['candidates'],snapshot=s,query_sequence=7)
                        return dict(commander_quality_proposal=result)
                port=Port(); result=consumer.plan_commander_quality_formal_v1(port,planned=p,snapshot=s,bridge_capabilities=caps if capabilities is None else capabilities)
                plans.append(dict(name=name,input=dict(schema='xar.java.commander-quality-plan-input.v1',planned=p,snapshot=s,bridge_capabilities=caps if capabilities is None else capabilities,queries=q[:len(port.calls)]),expected=result,query_order=port.calls))
            for name in names: plan_case('formal-'+name,[(83886367,inputs[name])])
            plan_case('later-army-after-keep',[(83886367,inputs[names[0]]),(83886368,inputs[names[1]])])
            plan_case('later-army-after-unavailable',[(83886367,'original query unavailable'),(83886368,inputs[names[1]])])
            plan_case('all-inputs-unavailable',[(83886367,'first unavailable'),(83886368,'second unavailable')])
            plan_case('pursuit-no-fallback',[(83886367,'pursuit unavailable')],phase='native_war_pursuit',step='move-army-baseline',pursuit=83886367)
            plan_case('mandatory-phase-retained',[],phase='native_war_battle',step='battle-response')
            plan_case('capability-missing',[],capabilities=[])
            plan_case('hold-existing-action-retained',[],step='existing-action')
            plan_case('recon-life-advance',[(83886367,inputs[names[1]])],phase='native_war_reconnaissance',step='life-advance')
            plan_case('progress-life-advance',[(83886367,inputs[names[1]])],phase='native_war_pursuit_progress',step='life-advance')
            for path in ['commander_quality_formal_proposal_v1.py','commander_quality_formal_consumer_v1.py','bridge/army_commander_candidates.py','bridge/army_commander_assignment.py','bridge/army_commander_current_base_quality.py','bridge/army_commander_current_martial.py','bridge/army_commander_target_rolls.py','bridge/army_commander_conditional_capacity.py','bridge/public_unit_contract.py','bridge/army_family_12004_identity.py','bridge/service.py']:
                p=root/'ck3_autonomous_player/src/xar_autoplayer'/path; pin(p,str(p.relative_to(root)))
            pin(native/'FIXTURE-PROVENANCE.json')
            out=dict(schema='xar.java.commander-quality-golden.v1',machine_id=machine,captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_machine_id='unknown',fixture_scope='retained native serializer fixtures; synthetic callbacks/raw storage; no game execution',source_pins=pins,original_packet_count=4,game_touched=False,assignment_executed=False,cases=cases,plans=plans)
            raw=json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            if len(raw)>98304: raise RuntimeError('commander golden exceeds 96KiB')
            sys.stdout.buffer.write(raw)
            """;
}
