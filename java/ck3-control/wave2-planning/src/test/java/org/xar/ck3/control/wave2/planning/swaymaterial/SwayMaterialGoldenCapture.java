package org.xar.ck3.control.wave2.planning.swaymaterial;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** One-shot original two-route stage and following consumer capture, outside default JUnit. */
public final class SwayMaterialGoldenCapture {
    private SwayMaterialGoldenCapture() { }
    private static final String SCRIPT = """
            import copy, datetime, hashlib, json, pathlib, sys, unittest
            import xar_autoplayer.sway_material_consumer as material
            import xar_autoplayer.sway_formal_consumer as formal
            import test_sway_material_consumer as census_test
            from test_sway_final_material_registered_12004 import FinalMaterialSoleCompound
            root, work, machine=pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3]
            work.mkdir(parents=True,exist_ok=False)
            captures=[]
            seen=set()
            context=[]
            writes=[0]
            original_core, original_census, original_following, original_write=material._record_sway_material,material.record_sway_material_intervention,material.consume_sway_material_following_turn,formal._write
            def projected(row,keys):
                return {key:copy.deepcopy(row[key]) for key in keys if key in row}
            def resolved_projection(row):
                value=projected(row,('status','postcondition_verified','action_id','actor_character_id','target_character_id','pre_capture_epoch','post_capture_epoch','post_date_raw','native_receipt','recovered_instance_observation','material_intervention','first_named_gain_intervention'))
                if isinstance(row.get('latest_instance_observation'),dict):
                    latest=projected(row['latest_instance_observation'],('action_id','actor_character_id','target_character_id','scheme_instance_id','scheme_instance_generation','exact_ck3_build','exe_sha256','source_native_revision','source_date_raw','tracked_instance_active','instance_terminal_outcome_observed'))
                    if isinstance(row['latest_instance_observation'].get('native_observation'),dict):
                        latest['native_observation']=projected(row['latest_instance_observation']['native_observation'],('schema','available','actor_character_id','target_character_id','scheme_instance_id','scheme_instance_generation','exact_ck3_build','exe_sha256','date_raw','exact_instance_join_ready','owner_matches_actor','native_status_observed','native_status_raw','native_terminal_state_observed'))
                    value['latest_instance_observation']=latest
                if row.get('terminal_intervention') is not None:
                    value['terminal_intervention']=projected(row['terminal_intervention'],('instance_terminal_outcome_observed','source_native_revision','native_status_key','terminal_cause_observed','terminal_cause'))
                return value
            def retain(case):
                key=hashlib.sha256(json.dumps(case,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                if key not in seen:
                    seen.add(key); case['id']='original-call-'+str(len(captures)+1); captures.append(case)
            def write(*args,**kwargs):
                writes[0]+=1
                return original_write(*args,**kwargs)
            formal._write=write
            def census(state_dir,**kwargs):
                context.append(copy.deepcopy(kwargs['sway_read']))
                try:
                    return original_census(state_dir,**kwargs)
                finally:
                    context.pop()
            material.record_sway_material_intervention=census
            census_test.record_sway_material_intervention=census
            def core(state_dir,**kwargs):
                before=copy.deepcopy(kwargs['resolved'])
                source={'kind':'completion'} if 'current_terminal_observed' in kwargs else {'kind':'census','sway_read':copy.deepcopy(context[-1])}
                inputs={'resolved':resolved_projection(before),'opinion_read':copy.deepcopy(kwargs['opinion_read']),'source':source}
                count=writes[0]
                result=original_core(state_dir,**kwargs)
                after=formal.read_sway_ledger(state_dir)['resolved']
                first_created='first_named_gain_intervention' not in before and 'first_named_gain_intervention' in after
                if 'first_named_gain_intervention' in before and before['first_named_gain_intervention'] != after.get('first_named_gain_intervention'):
                    raise RuntimeError('original stage replaced the first named gain')
                case={'operation':'stage','input':inputs,'expected_material':copy.deepcopy(result),'expected_write_count':writes[0]-count,'first_named_gain_created':first_created}
                if first_created:
                    case['expected_first_named_gain']=copy.deepcopy(after['first_named_gain_intervention'])
                retain(case)
                return result
            material._record_sway_material=core
            def following(value,**kwargs):
                before=copy.deepcopy(value)
                result=original_following(value,**kwargs)
                if value != before:
                    raise RuntimeError('original following consumer mutated input')
                if isinstance(value,dict):
                    retain({'operation':'following','input':{'material':before,**kwargs},'expected':copy.deepcopy(result)})
                return result
            material.consume_sway_material_following_turn=following
            census_dir=work/'census'
            census_dir.mkdir()
            census_test.test_original_sway_material_consumption_compound(census_dir)
            suite=unittest.TestSuite([FinalMaterialSoleCompound('test_final_named_gain_normal_turn_and_independent_controls')])
            result=unittest.TestResult()
            suite.run(result)
            if not result.wasSuccessful() or result.testsRun != 1 or result.skipped:
                raise RuntimeError('original full registered-MCP material compound failed: '+repr(result.errors)+repr(result.failures)+repr(result.skipped))
            if not any(row['operation']=='stage' and row['input']['source']['kind']=='completion' for row in captures):
                raise RuntimeError('actual completion consumer route was not executed')
            if not any(row['operation']=='stage' and row['input']['source']['kind']=='census' for row in captures):
                raise RuntimeError('actual census consumer route was not executed')
            paths=['ck3_autonomous_player/src/xar_autoplayer/sway_material_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_lifecycle_consumer.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/environment.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/tests/unit/test_sway_material_consumer.py','ck3_autonomous_player/tests/unit/test_sway_final_material_registered_12004.py']
            output={'schema':'xar.java.sway-material-producer-golden.v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'sources':[{'path':path,'sha256':hashlib.sha256((root/path).read_bytes()).hexdigest()} for path in paths],'cases':captures,'original_census_compound_executed':True,'original_registered_mcp_compound_tests':result.testsRun,'original_registered_mcp_skipped':len(result.skipped),'game_rpc_count':0,'canonical_ledger_write_count':0,'native_inputs':'existing-explicit-synthetic-native-protocol-and-source-fixtures','production_cutover':False}
            text=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            if len(text.encode()) > 98304:
                raise RuntimeError('capture exceeds 96 KiB; real failure output preserved by outer caller')
            print(text)
            """;

    public static void main(String[] args) throws Exception {
        if (args.length != 5) { throw new IllegalArgumentException("python-exe repo-root new-output new-fixture-dir machine-id required"); }
        Path python=Path.of(args[0]).toAbsolutePath().normalize(), root=Path.of(args[1]).toAbsolutePath().normalize();
        Path output=Path.of(args[2]).toAbsolutePath().normalize(), fixture=Path.of(args[3]).toAbsolutePath().normalize();
        Path allowed=Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch").toAbsolutePath().normalize();
        if (!Files.isRegularFile(python) || Files.exists(output) || Files.exists(fixture)
                || !output.startsWith(allowed) || !fixture.startsWith(allowed) || args[4].isBlank()) {
            throw new IllegalArgumentException("new finite D scratch outputs and current machine required");
        }
        Files.createDirectories(output.getParent());
        ProcessBuilder builder=new ProcessBuilder(python.toString(),"-c",SCRIPT,root.toString(),fixture.toString(),args[4]);
        builder.directory(root.toFile());
        builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src")+";"+root.resolve("ck3_autonomous_player/tests/unit")+";"+root.resolve("tools")+";"+root.resolve("ck3_workshop_mcp/src"));
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        builder.environment().put("TEMP",output.getParent().toString()); builder.environment().put("TMP",output.getParent().toString());
        builder.redirectOutput(output.toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process=builder.start();
        if (!process.waitFor(30,TimeUnit.SECONDS)) {
            process.destroyForcibly(); process.waitFor(); throw new IllegalStateException("original compound timed out; failure evidence retained");
        }
        if (process.exitValue()!=0 || Files.size(output)==0 || Files.size(output)>98304) { throw new IllegalStateException("original compound capture failed; output retained"); }
        System.out.println("Sway material original two-route producer captured "+Files.size(output)+" bytes");
    }
}
