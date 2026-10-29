package org.xar.ck3.control.wave2.military.warexitterms;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit compatibility capture. Synthetic returned data never enables the disabled native collector. */
public final class WarExitTermsGoldenCapture {
    private WarExitTermsGoldenCapture() { }

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 4) { throw new IllegalArgumentException("repository python-exe fresh-output machine-id required"); }
        Path repository = Path.of(args[0]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("fresh capture output required"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM,
                repository.toString(), args[3]));
        builder.directory(repository.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", repository + File.pathSeparator
                + repository.resolve("ck3_autonomous_player/src") + File.pathSeparator
                + repository.resolve("ck3_autonomous_player/tests/unit"));
        builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process = builder.start();
        byte[] bytes;
        try (var reader = Executors.newSingleThreadExecutor()) {
            var response = reader.submit(() -> {
                try (var stream = process.getInputStream()) { return stream.readNBytes(65_537); }
            });
            if (!process.waitFor(90, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly);
                process.destroyForcibly();
                throw new IOException("producer capture timeout");
            }
            try { bytes = response.get(); }
            catch (ExecutionException error) { throw new IOException("capture read failed", error.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 65_536) {
            throw new IOException("capture failed/over budget: exit=" + process.exitValue() + " bytes=" + bytes.length);
        }
        Files.createDirectories(output.getParent());
        Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + bytes.length + " bytes to " + output);
    }

    private static final String PROGRAM = """
            import contextlib,copy,datetime,hashlib,json,sys,threading,types,unittest
            from pathlib import Path
            import test_war_termination_exit_terms_v2_contract as tests
            from xar_autoplayer.bridge import native_driver as driver
            from xar_autoplayer.bridge import war_exit_terms_contract as producer
            root=Path(sys.argv[1]); machine=sys.argv[2]
            result=unittest.TestResult()
            with contextlib.redirect_stdout(sys.stderr):
                unittest.defaultTestLoader.loadTestsFromModule(tests).run(result)
            if result.testsRun!=5 or result.failures or result.errors or result.skipped:
                raise RuntimeError('original five exit-terms tests failed/skipped: '+repr(result.failures+result.errors+result.skipped))
            if producer.WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED is not False:
                raise RuntimeError('disabled native-preview admission changed')
            war_id=16777300
            normalized=producer.normalize_war_termination_exit_terms(tests._fixture(),expected_war_id=war_id)
            snapshot=dict(paused=True,snapshot_id='native:40',revision=41,native_revision=40,
                episode_run_id='synthetic-exit-terms-replay',diagnostics=dict(connection_generation=1),
                played_character=dict(character_id=16777218),active_wars=[dict(war_id=war_id,
                player_side='attacker',player_is_primary_war_leader=True,
                primary_opponent_character_id=16777219,targeted_title_ids=[16777221])])
            receipt=dict(step=producer.query_war_termination_exit_terms_step(war_id),accepted=True,
                status='available',query_sequence=2**64-1,backend_id='native-headless',
                war_termination_exit_terms=copy.deepcopy(normalized))
            # Only the original returned-data consumer runs. No driver constructor, endpoint or native dispatch runs.
            fake=types.SimpleNamespace(_driver_state_lock=threading.RLock(),_war_termination_exit_terms={})
            fake._execute_primitive_step=lambda step,**kwargs: copy.deepcopy(receipt)
            fake.take_snapshot=lambda: copy.deepcopy(snapshot)
            actual=driver.NativeHeadlessGameplayDriver._execute_war_termination_exit_terms_query(
                fake,receipt['step'],starting=copy.deepcopy(snapshot),selected_revision=41,war_id=war_id)
            cache=driver.NativeHeadlessGameplayDriver._war_termination_exit_terms_cache_for_snapshot(
                fake,copy.deepcopy(snapshot),episode_run_id=snapshot['episode_run_id'])
            if len(cache)!=1 or actual['query_sequence']!=2**64-1:
                raise RuntimeError('actual original driver/cache consumer returned incomplete capture')
            def artifact(name,value):
                raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
                return dict(name=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),utf8=raw.decode('utf-8'))
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/war_exit_terms_contract.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/__init__.py',
                'ck3_autonomous_player/tests/unit/test_war_termination_exit_terms_v2_contract.py',
                'ck3_autonomous_player/tests/fixtures/war_termination_exit_terms_v2_synthetic.json',
                'ck3_autonomous_player/tests/fixtures/war_termination_exit_terms_v2_contract.txt']
            pins=[dict(path=p,bytes=len((root/p).read_bytes()),sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths]
            output=dict(schema='xar.ck3.war-exit-terms-producer-bundle/v1',machine_id=machine,
                captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_machine_id='unknown',
                synthetic_inputs=True,native_dispatch_count=0,production_enabled=False,
                original_tests=result.testsRun,original_skipped=0,source_pins=pins,
                artifacts=[artifact('normalized.json',normalized),artifact('driver-result.json',actual),
                    artifact('snapshot-cache.json',cache)])
            raw=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            if len(raw)>65536: raise RuntimeError('golden bundle exceeds 64KiB budget')
            sys.stdout.buffer.write(raw)
            """;
}
