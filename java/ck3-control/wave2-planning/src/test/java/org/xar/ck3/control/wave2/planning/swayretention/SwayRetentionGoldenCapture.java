package org.xar.ck3.control.wave2.planning.swayretention;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit one-shot producer capture with the original causal writer and following consumer. */
public final class SwayRetentionGoldenCapture {
    private SwayRetentionGoldenCapture() { }
    private static final String SCRIPT = """
            import copy, datetime, hashlib, json, pathlib, sys
            from test_sway_causal_terminal_retention_12004 import SwayCausalTerminalRetention12004Test, unknown_observation, set_current_identity, IDENTITY
            from xar_autoplayer.sway_end_causal_consumer_12004 import retain_sway_end_causal_terminal_12004
            from xar_autoplayer.bridge.version_identity import CK3_12003
            root, machine = pathlib.Path(sys.argv[1]), sys.argv[2]
            original=SwayCausalTerminalRetention12004Test
            original.setUpClass()
            try:
                base={'previous':copy.deepcopy(original.retained),'observation':unknown_observation()}
                if base['previous']['next_turn_consumed'] is not True or base['previous']['following_native_revision'] != 802:
                    raise RuntimeError('original causal writer/following consumer did not produce a consumed admitted terminal')
                cases=[]
                def change(path,value):
                    return {'path':path.split('.'),'value':value}
                def remove(path):
                    return {'path':path.split('.'),'remove':True}
                def capture(name,mutations):
                    data=copy.deepcopy(base)
                    for mutation in mutations:
                        row=data
                        for key in mutation['path'][:-1]:
                            row=row[key]
                        if mutation.get('remove') is True:
                            row.pop(mutation['path'][-1],None)
                        else:
                            row[mutation['path'][-1]]=mutation['value']
                    before=copy.deepcopy(data)
                    result=retain_sway_end_causal_terminal_12004(data['previous'],data['observation'])
                    if data != before:
                        raise RuntimeError('original pure producer mutated inputs')
                    if result == data['previous']:
                        selected='previous'
                    elif result == data['observation']:
                        selected='observation'
                    else:
                        raise RuntimeError('original result is not an exact source snapshot')
                    digest=hashlib.sha256(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                    cases.append({'id':name,'mutations':mutations,'expected_result_ref':selected,'original_result_canonical_sha256':digest})
                capture('same-instance-retains-consumed-history',[])
                capture('purged-owner-sentinel',[change('observation.native_observation.native_owner_raw',4294967295),change('observation.native_observation.owner_matches_actor',False)])
                capture('new-action',[change('observation.action_id','new-action')])
                capture('same-slot-new-generation',[change('observation.scheme_instance_id',IDENTITY['scheme_instance_id']+0x01000000),change('observation.native_observation.scheme_instance_id',IDENTITY['scheme_instance_id']+0x01000000)])
                capture('other-generation',[change('observation.scheme_instance_generation',8),change('observation.native_observation.scheme_instance_generation',8)])
                capture('other-actor',[change('observation.actor_character_id',0x08000031),change('observation.native_observation.actor_character_id',0x08000031)])
                capture('other-target',[change('observation.target_character_id',0x09000041),change('observation.native_observation.target_character_id',0x09000041)])
                capture('different-build',[change('observation.exact_ck3_build',CK3_12003.game_version),change('observation.native_observation.exact_ck3_build',CK3_12003.game_version),change('observation.exe_sha256',CK3_12003.executable_sha256),change('observation.native_observation.exe_sha256',CK3_12003.executable_sha256)])
                capture('wrong-sha',[change('observation.exe_sha256','0'*64),change('observation.native_observation.exe_sha256','0'*64)])
                capture('reused-slot',[change('observation.native_observation.storage_slot_reused',True)])
                capture('absent-instance',[change('observation.native_observation.instance_present',False)])
                capture('join-not-ready',[change('observation.native_observation.exact_instance_join_ready',False)])
                capture('other-owner',[change('observation.native_observation.native_owner_raw',0x0A000031)])
                capture('bool-status',[change('observation.native_observation.native_status_raw',True)])
                capture('float-status',[change('observation.native_observation.native_status_raw',1.0)])
                capture('absent-causal-proof',[remove('previous.causal_observation')])
                capture('different-actor-in-proof',[change('previous.causal_observation.actor_character_id',IDENTITY['actor_character_id']+0x01000000)])
                capture('unobserved-causal-transition',[change('previous.causal_observation.native_terminal_transition_observed',False)])
                capture('previous-not-terminal',[change('previous.instance_terminal_outcome_observed',False)])
                capture('previous-cause-unobserved',[change('previous.terminal_cause_observed',False)])
                capture('current-not-terminal',[change('observation.instance_terminal_outcome_observed',False)])
                capture('current-new-cause-observed',[change('observation.terminal_cause_observed',True)])
                capture('identity-sha-spelling-differs',[change('observation.exe_sha256',IDENTITY['exe_sha256'].lower()),change('observation.native_observation.exe_sha256',IDENTITY['exe_sha256'].lower())])
                capture('causal-status-float',[change('previous.causal_observation.native_status_raw',1.0)])
                paths=['ck3_autonomous_player/src/xar_autoplayer/sway_end_causal_consumer_12004.py','ck3_autonomous_player/src/xar_autoplayer/sway_lifecycle_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/bridge/sway_completion_causal_private_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/environment.py','ck3_autonomous_player/tests/unit/test_sway_causal_terminal_retention_12004.py']
                result={'schema':'xar.java.sway-retention-producer-golden.v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'sources':[{'path':path,'sha256':hashlib.sha256((root/path).read_bytes()).hexdigest()} for path in paths],'base':base,'cases':cases,'producer_chain':'actual-original-causal-writer-then-following-consumer-then-retention-function','native_inputs':'fresh-synthetic-existing-source-frames-no-native-game-observation','game_rpc_count':0,'canonical_ledger_write_count':0,'production_cutover':False}
                output=json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))
                if len(output.encode('utf-8')) > 65536:
                    raise RuntimeError('capture exceeds 64 KiB')
                print(output)
            finally:
                original.doClassCleanups()
            """;

    public static void main(String[] args) throws Exception {
        if (args.length != 5) { throw new IllegalArgumentException("python-exe repo-root new-output fixture-parent machine-id required"); }
        Path python = Path.of(args[0]).toAbsolutePath().normalize(), root = Path.of(args[1]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize(), fixture = Path.of(args[3]).toAbsolutePath().normalize();
        Path allowed = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch").toAbsolutePath().normalize();
        if (!Files.isRegularFile(python) || Files.exists(output) || !output.startsWith(allowed)
                || !fixture.startsWith(allowed) || args[4].isBlank()) {
            throw new IllegalArgumentException("bounded new D scratch output and current machine identity required");
        }
        Files.createDirectories(output.getParent()); Files.createDirectories(fixture);
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-c", SCRIPT, root.toString(), args[4]);
        builder.directory(root.toFile());
        builder.environment().put("PYTHONPATH", root.resolve("ck3_autonomous_player/src") + ";" + root.resolve("ck3_autonomous_player/tests/unit"));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("XAR_M6E_TEMP_ROOT", fixture.toString());
        builder.environment().put("TEMP", fixture.toString()); builder.environment().put("TMP", fixture.toString());
        builder.redirectOutput(output.toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process = builder.start();
        if (!process.waitFor(15, TimeUnit.SECONDS)) {
            process.destroyForcibly(); process.waitFor();
            throw new IllegalStateException("original capture timed out; incomplete output retained");
        }
        if (process.exitValue() != 0 || Files.size(output) == 0 || Files.size(output) > 65_536) {
            throw new IllegalStateException("original capture failed; output retained");
        }
        System.out.println("Sway retention original producer captured " + Files.size(output) + " bytes");
    }
}
