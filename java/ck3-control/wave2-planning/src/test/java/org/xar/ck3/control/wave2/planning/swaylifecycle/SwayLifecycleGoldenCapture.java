package org.xar.ck3.control.wave2.planning.swaylifecycle;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit bounded original producer capture. Default JUnit never invokes this tool. */
public final class SwayLifecycleGoldenCapture {
    private SwayLifecycleGoldenCapture() { }
    private static final String SCRIPT = """
            import copy, datetime, hashlib, json, pathlib, sys
            from xar_autoplayer.ordinary_sway_lifecycle_observation_v1 import READERS, _binding, observe_resolved_sway_lifecycle_v1
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
            from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, read_sway_ledger
            from xar_autoplayer.sway_lifecycle_consumer import record_sway_terminal_observation
            from test_ordinary_sway_lifecycle_observation_v1 import seed, SourceDriver, ACTOR, TARGET
            root, work, machine = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
            work.mkdir(parents=True,exist_ok=False)
            definitions = [
                ('ordinary-registered-service',{}),
                ('completion-read-fails',{'fail':True}),
                ('post-frame-changed',{'after_revision':18}),
                ('opinion-only',{'completion':False}),
                ('all-disabled',{'completion':False,'opinion':False}),
                ('unpaused',{'before':{'paused':False}}),
                ('map-unready',{'before':{'map_ready':False}}),
                ('played-character-dead',{'before':{'played_character':{'character_id':ACTOR,'alive':False}}}),
                ('other-actor',{'before':{'played_character':{'character_id':999,'alive':True}}}),
                ('other-explicit-target',{'target':TARGET+1}),
                ('one-life-terminal',{'before':{'one_life_terminal_reason':'played_character_changed'}}),
                ('flattened-explicit-runner-frame',{'flattened':True}),
                ('bad-instance-generation',{'receipt':{'scheme_instance_generation':7}}),
                ('bool-instance-generation',{'receipt':{'scheme_instance_generation':True}}),
                ('original-already-applied-terminal-stays-observable',{'terminal':True}),
                ('termination-read-unsupported',{'termination':True}),
                ('opinion-read-value-error',{'opinion_error':True}),
                ('resolved-not-applied',{'resolved':{'status':'pending'}}),
                ('unverified-resolved',{'resolved':{'postcondition_verified':False}}),
            ]
            cases = []
            def project_frame(frame):
                keys=('snapshot_id','revision','native_revision','date_raw','paused','map_ready','episode_run_id','episode_character_id','one_life_terminal_reason','played_character','played_character_id','played_character_alive')
                projected={key:copy.deepcopy(frame[key]) for key in keys if key in frame}
                if _binding(frame) != _binding(projected):
                    raise RuntimeError('frame projection changed actual original binding')
                return projected
            for name, settings in definitions:
                directory = work/name
                directory.mkdir()
                resolved = seed(directory)
                resolved.update(settings.get('resolved',{}))
                resolved['native_receipt'].update(settings.get('receipt',{}))
                (directory/LEDGER_FILE).write_text(json.dumps({'schema':'xar.ck3.active-scheme-sway-formal-private.v1','pending':None,'resolved':resolved}),encoding='utf-8')
                driver = SourceDriver(directory)
                retained_terminal_seed = None
                if settings.get('terminal'):
                    # Build the retained record through the original writer and original
                    # SourceDriver packet; native revision is not public revision17.
                    driver.terminal = True
                    terminal_read = driver.query_active_scheme_sway_completion_private_v1(
                        expected_revision=driver.frame['revision'],
                        target_character_id=TARGET,
                        scheme_instance_id=resolved['native_receipt']['scheme_instance_id'])
                    if terminal_read['snapshot_revision'] != driver.frame['native_revision']:
                        raise RuntimeError('terminal seed query differs from actual fixture native frame')
                    record_sway_terminal_observation(directory,completion_read=terminal_read)
                    resolved = read_sway_ledger(directory)['resolved']
                    retained = resolved['terminal_intervention']
                    if retained['source_native_revision'] != terminal_read['snapshot_revision']:
                        raise RuntimeError('original terminal writer lost actual native revision')
                    retained_terminal_seed = {
                        'producer':'sway_lifecycle_consumer.record_sway_terminal_observation',
                        'query_count':1,
                        'frame_public_revision':driver.frame['revision'],
                        'frame_native_revision':driver.frame['native_revision'],
                        'completion_snapshot_revision':terminal_read['snapshot_revision']}
                    driver.terminal = False
                driver.fail = settings.get('fail',False)
                driver.allow_private_active_scheme_sway_completion_query = settings.get('completion',True)
                driver.allow_private_active_scheme_sway_outcome_opinion_query = settings.get('opinion',True)
                driver.allow_private_active_scheme_sway_completion_termination_query = settings.get('termination',False)
                if settings.get('termination'):
                    def unsupported(**arguments):
                        raise UnsupportedStepError('synthetic existing-reader unsupported boundary')
                    driver.query_active_scheme_sway_completion_termination_private_v1 = unsupported
                if settings.get('opinion_error'):
                    def bad_opinion(**arguments):
                        raise ValueError('synthetic normalized opinion invalid')
                    driver.query_active_scheme_sway_outcome_opinion_private_v1 = bad_opinion
                before = copy.deepcopy(driver.frame)
                before.update(settings.get('before',{}))
                if settings.get('flattened'):
                    played = before.pop('played_character')
                    before.update(played_character_id=played['character_id'],played_character_alive=played['alive'])
                service = GameplayBridgeService(driver)
                trace, after = [], []
                for reader, _, method in READERS:
                    original = getattr(service,method)
                    def wrap(original=original,reader=reader,**arguments):
                        try:
                            observation = original(**arguments)
                        except (BridgeUnavailableError,UnsupportedStepError,ValueError) as error:
                            trace.append({'reader':reader,'arguments':arguments,'kind':'failed','error_kind':type(error).__name__,'message':str(error)})
                            raise
                        projected={key:copy.deepcopy(observation[key]) for key in ('status','queried_snapshot_id','queried_revision','queried_native_revision','date_raw') if key in observation}
                        trace.append({'reader':reader,'arguments':arguments,'kind':'returned','observation':projected})
                        return observation
                    setattr(service,method,wrap)
                original_snapshot = service.snapshot
                def snapshot(**arguments):
                    value = original_snapshot(**arguments)
                    if 'after_revision' in settings:
                        value = {**value,'revision':settings['after_revision']}
                    after.append(copy.deepcopy(value))
                    return value
                service.snapshot = snapshot
                target = settings.get('target')
                result = observe_resolved_sway_lifecycle_v1(service,snapshot=before,target_character_id=target)
                inputs = {'resolved':resolved,'before':project_frame(before),'after':project_frame(after[-1]) if after else None,'target_character_id':target,'permissions':{'completion':driver.allow_private_active_scheme_sway_completion_query,'opinion':driver.allow_private_active_scheme_sway_outcome_opinion_query,'termination':driver.allow_private_active_scheme_sway_completion_termination_query},'reads':trace}
                cases.append({'id':name,'input':inputs,'expected':result,'native_inputs':'synthetic-existing-SourceDriver-fixture','producer_and_registered_service_executed':True,'fixture_seed':retained_terminal_seed})
            paths = ['ck3_autonomous_player/src/xar_autoplayer/ordinary_sway_lifecycle_observation_v1.py','ck3_autonomous_player/src/xar_autoplayer/sway_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_lifecycle_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_material_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_end_causal_consumer_12004.py','ck3_autonomous_player/src/xar_autoplayer/environment.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/bridge/sway_terminal_source_producer_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_sway_service_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_sway_quiet_observation_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_sway_hold_observation_v1.py','ck3_autonomous_player/tests/unit/test_ordinary_sway_lifecycle_observation_v1.py']
            sources=[{'path':path,'sha256':hashlib.sha256((root/path).read_bytes()).hexdigest()} for path in paths]
            result={'schema':'xar.java.sway-lifecycle-producer-golden.v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'sources':sources,'cases':cases,'game_rpc_count':0,'canonical_ledger_write_count':0,'fixture_ledger_writes':'existing-original-consumers-only-under-explicit-D-scratch','production_cutover':False}
            output=json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            if len(output.encode('utf-8')) > 65536:
                raise RuntimeError('capture exceeds 64 KiB golden budget')
            print(output)
            """;

    public static void main(String[] args) throws Exception {
        if (args.length != 5) { throw new IllegalArgumentException("python-exe repo-root new-output new-fixture-dir machine-id required"); }
        Path python = Path.of(args[0]).toAbsolutePath().normalize(), root = Path.of(args[1]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize(), fixture = Path.of(args[3]).toAbsolutePath().normalize();
        Path allowed = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch").toAbsolutePath().normalize();
        if (!Files.isRegularFile(python) || Files.exists(output) || Files.exists(fixture)
                || !output.startsWith(allowed) || !fixture.startsWith(allowed) || args[4].isBlank()) {
            throw new IllegalArgumentException("new bounded D scratch outputs and actual machine identity required");
        }
        Files.createDirectories(output.getParent());
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-c", SCRIPT, root.toString(), fixture.toString(), args[4]);
        builder.directory(root.toFile());
        builder.environment().put("PYTHONPATH", root.resolve("ck3_autonomous_player/src") + ";" + root.resolve("ck3_autonomous_player/tests/unit"));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.redirectOutput(output.toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process = builder.start();
        if (!process.waitFor(15, TimeUnit.SECONDS)) {
            process.destroyForcibly(); process.waitFor();
            throw new IllegalStateException("original capture timed out; incomplete output retained");
        }
        if (process.exitValue() != 0 || Files.size(output) == 0 || Files.size(output) > 65_536) {
            throw new IllegalStateException("original capture failed; output retained");
        }
        System.out.println("Sway lifecycle original producer captured " + Files.size(output) + " bytes");
    }
}

