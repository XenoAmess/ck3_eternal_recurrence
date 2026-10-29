package org.xar.ck3.control.planning.swayreuse;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

/** Explicit one-shot legacy producer capture; not invoked by default JUnit. */
public final class SwayReuseGoldenCapture {
    private SwayReuseGoldenCapture() { }

    private static final String SCRIPT = """
            import copy, datetime, hashlib, json, pathlib, sys
            from xar_autoplayer.reused_sway_opportunity_v1 import reused_sway_observation_gap_v1, fresh_empty_sway_slot_after_reuse_v1
            root = pathlib.Path(sys.argv[1])
            machine = sys.argv[2]
            evidence = root / 'docs/ck3-native-ai/evidence/m6-sway-closed-ledger-2026-10-20.json'
            raw = evidence.read_bytes()
            original = json.loads(raw)['resolved']
            keys = ['status','postcondition_verified','actor_character_id','target_character_id','action_id','pre_capture_epoch','post_capture_epoch','post_date_raw','native_receipt']
            resolved = {key:copy.deepcopy(original[key]) for key in keys}
            resolved['terminal_intervention'] = {'instance_terminal_outcome_observed': original['terminal_intervention']['instance_terminal_outcome_observed']}
            observation = original['latest_instance_observation']
            obskeys = ['action_id','actor_character_id','target_character_id','scheme_instance_id','scheme_instance_generation','exact_ck3_build','exe_sha256','source_native_revision','source_date_raw','tracked_instance_active','instance_terminal_outcome_observed']
            projected = {key:copy.deepcopy(observation[key]) for key in obskeys}
            nativekeys = ['schema','available','snapshot_revision','date_raw','actor_character_id','target_character_id','scheme_instance_id','scheme_instance_generation','instance_source_observed','instance_present','storage_slot_reused','exact_instance_join_ready','native_status_observed','native_terminal_state_observed','native_status_raw','exact_ck3_build','exe_sha256']
            projected['native_observation'] = {key:copy.deepcopy(observation['native_observation'][key]) for key in nativekeys}
            resolved['latest_instance_observation'] = projected
            date = 53274960
            actor = 40526
            quote = {'schema':'active-scheme-sway-private-read-v1','date_raw':date,'actor_character_id':actor,'target_character_id':34973,'active_scheme_count':0,'active_sway_instances':[],'matching_sway_active':False,'native_complete_can_send':True,'native_legal_now':True,'exact_ck3_build':'1.20.0.4','exe_sha256':observation['exe_sha256']}
            base = {'resolved':resolved,'actor_character_id':actor,'date_raw':date,'readback':quote}
            def invoke(value, operation):
                if operation == 'gap':
                    return reused_sway_observation_gap_v1(value['resolved'], actor_character_id=value['actor_character_id'], date_raw=value['date_raw'])
                return fresh_empty_sway_slot_after_reuse_v1(value['resolved'],value['readback'])
            full = reused_sway_observation_gap_v1(original,actor_character_id=actor,date_raw=date)
            if full != invoke(base,'gap') or full is None:
                raise RuntimeError('projected retained source differs from real full-ledger producer')
            cases = []
            def capture(name, operation, mutations):
                value = copy.deepcopy(base)
                for change in mutations:
                    parent = value
                    for key in change['path'][:-1]:
                        parent = parent[key]
                    if change.get('remove') is True:
                        parent.pop(change['path'][-1],None)
                    else:
                        parent[change['path'][-1]] = change['value']
                cases.append({'id':name,'operation':operation,'mutations':mutations,'expected':invoke(value,operation)})
            def change(path,value):
                return {'path':path.split('.'),'value':value}
            def remove(path):
                return {'path':path.split('.'),'remove':True}
            capture('retained-full-ledger-projected','gap',[])
            capture('legal-empty-slot','fresh',[])
            capture('unknown-status','gap',[change('resolved.status','pending')])
            capture('unverified-applied','gap',[change('resolved.postcondition_verified',False)])
            capture('actor-bool','gap',[change('actor_character_id',True)])
            capture('date-float','gap',[change('date_raw',float(date))])
            capture('terminal-actually-observed','gap',[change('resolved.terminal_intervention.instance_terminal_outcome_observed',True)])
            capture('receipt-action-drift','gap',[change('resolved.native_receipt.action_id','different-action')])
            capture('receipt-epoch-equal-to-before','gap',[change('resolved.native_receipt.post_capture_epoch',resolved['pre_capture_epoch'])])
            capture('receipt-post-date-drift','gap',[change('resolved.native_receipt.post_date_raw',1)])
            capture('future-observation','gap',[change('date_raw',observation['source_date_raw']-1)])
            capture('latest-instance-missing','gap',[remove('resolved.latest_instance_observation.scheme_instance_id')])
            capture('latest-generation-float','gap',[change('resolved.latest_instance_observation.scheme_instance_generation',5.0)])
            capture('native-generation-bool','gap',[change('resolved.latest_instance_observation.native_observation.scheme_instance_generation',True)])
            capture('native-build-drift','gap',[change('resolved.latest_instance_observation.native_observation.exact_ck3_build','1.20.0.3')])
            capture('native-sha-drift','gap',[change('resolved.latest_instance_observation.native_observation.exe_sha256','a'*64)])
            capture('native-presence-true','gap',[change('resolved.latest_instance_observation.native_observation.instance_present',True)])
            capture('native-reuse-false','gap',[change('resolved.latest_instance_observation.native_observation.storage_slot_reused',False)])
            capture('native-status-missing','gap',[remove('resolved.latest_instance_observation.native_observation.native_status_raw')])
            capture('native-status-zero','gap',[change('resolved.latest_instance_observation.native_observation.native_status_raw',0)])
            capture('zero-native-revision','gap',[change('resolved.latest_instance_observation.source_native_revision',0)])
            capture('fresh-count-bool','fresh',[change('readback.active_scheme_count',True)])
            capture('fresh-count-null','fresh',[change('readback.active_scheme_count',None)])
            capture('fresh-instances-null','fresh',[change('readback.active_sway_instances',None)])
            capture('fresh-instances-occupied','fresh',[change('readback.active_sway_instances',[{}])])
            capture('fresh-native-illegal','fresh',[change('readback.native_legal_now',False)])
            capture('fresh-matching-active','fresh',[change('readback.matching_sway_active',True)])
            capture('fresh-wrong-actor','fresh',[change('readback.actor_character_id',40527)])
            recovered = {'schema':'xar.ck3.sway-recovered-instance-observation.v1','source_kind':'matching_active_readback_recovery','submission_receipt_available':False,'action_id':resolved['action_id'],'actor_character_id':actor,'target_character_id':34973,'scheme_instance_id':observation['scheme_instance_id'],'scheme_instance_generation':observation['scheme_instance_generation'],'active_instance':copy.deepcopy(original['applied_instance_observation']['active_instance']),'source_read':copy.deepcopy(original['applied_instance_observation']['source_read'])}
            capture('recovered-independent-read-identity','gap',[remove('resolved.native_receipt'),change('resolved.recovered_instance_observation',recovered)])
            capture('explicit-receipt-identities','gap',[change('resolved.native_receipt.actor_character_id',actor),change('resolved.native_receipt.target_character_id',34973)])
            capture('receipt-zero-instance','gap',[change('resolved.native_receipt.scheme_instance_id',0)])
            capture('receipt-reserved-instance','gap',[change('resolved.native_receipt.scheme_instance_id',4294967295)])
            sourcepaths = ['ck3_autonomous_player/src/xar_autoplayer/reused_sway_opportunity_v1.py','ck3_autonomous_player/src/xar_autoplayer/sway_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/ordinary_sway_schedule_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/tests/unit/test_source27_master_integration_v1.py']
            sources = [{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in sourcepaths]
            result = {'schema':'xar.java.sway-reuse-producer-golden.v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'producer':'xar_autoplayer.reused_sway_opportunity_v1','sources':sources,'retained_evidence':{'path':str(evidence.relative_to(root)).replace(chr(92),'/'),'sha256':hashlib.sha256(raw).hexdigest()},'base_kind':'exact-consumed-field-projection-of-retained-ledger-plus-existing-integration-test-readback','full_ledger_gap_equal_to_projection':True,'base':base,'cases':cases,'game_rpc_count':0,'ledger_write_count':0,'production_consumer_cutover':False}
            output = json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)
            if len(output.encode('utf-8')) > 65536:
                raise RuntimeError('golden output exceeds 64 KiB')
            print(output)
            """;

    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("python-exe repo-root new-output machine-id required"); }
        Path python = Path.of(args[0]).toAbsolutePath().normalize();
        Path root = Path.of(args[1]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (!Files.isRegularFile(python) || Files.exists(output) || args[3].isBlank()) {
            throw new IllegalArgumentException("existing interpreter, new output and observed machine required");
        }
        Files.createDirectories(output.getParent());
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-c", SCRIPT, root.toString(), args[3]);
        builder.directory(root.toFile());
        builder.environment().put("PYTHONPATH", root.resolve("ck3_autonomous_player/src").toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.redirectOutput(output.toFile());
        builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process = builder.start();
        if (!process.waitFor(Duration.ofSeconds(10).toMillis(), TimeUnit.MILLISECONDS)) {
            process.destroyForcibly();
            process.waitFor();
            throw new IllegalStateException("legacy producer capture timed out; incomplete output retained");
        }
        if (process.exitValue() != 0 || Files.size(output) == 0 || Files.size(output) > 65_536) {
            throw new IllegalStateException("legacy producer capture failed; output retained");
        }
        System.out.println("Sway reuse producer capture completed: " + output + " bytes=" + Files.size(output));
    }
}
