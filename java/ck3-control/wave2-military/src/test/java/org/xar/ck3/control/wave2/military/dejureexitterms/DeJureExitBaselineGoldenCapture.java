package org.xar.ck3.control.wave2.military.dejureexitterms;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit baseline-only capture from existing synthetic fixtures and the unchanged original producer. */
public final class DeJureExitBaselineGoldenCapture {
    private DeJureExitBaselineGoldenCapture() { }

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
            import contextlib,copy,datetime,hashlib,json,sys,unittest
            from pathlib import Path
            import test_defender_dejure_exit_terms_v1 as tests
            from xar_autoplayer.bridge import defender_dejure_exit_terms_v1 as producer
            root=Path(sys.argv[1]); machine=sys.argv[2]
            result=unittest.TestResult()
            with contextlib.redirect_stdout(sys.stderr):
                unittest.defaultTestLoader.loadTestsFromModule(tests).run(result)
            if result.testsRun!=11 or result.failures or result.errors or result.skipped:
                raise RuntimeError('original eleven baseline tests failed/skipped: '+repr(result.failures+result.errors+result.skipped))
            baseline=tests._candidate()
            truce=tests._candidate(); truce['truce_inputs_v1']=tests._truce_inputs()
            storage=copy.deepcopy(truce)
            storage['border_raid_storage_candidate_v1']=dict(
                schema='xar.ck3.h2743-border-raid-storage-candidate.v1',status='structural_candidate_only',
                candidate=False,storage_capacity=17,active_war_count=2,matching_war_count=0,
                unavailable_reason=None,native_condition_observed=False)
            def artifact(name,value):
                raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
                return dict(name=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),utf8=raw.decode('utf-8'))
            artifacts=[]
            for name,candidate in [('baseline',baseline),('truce',truce),('storage',storage)]:
                if 'h2743_stock_predicate_evidence_v1' in candidate:
                    raise RuntimeError('H2743 stock evidence cannot enter baseline capture')
                projected=producer.normalize_defender_dejure_exit_terms_v1(candidate,
                    expected_war_id=16777231,expected_native_revision=3,expected_date_raw=53217264,
                    expected_defender_id=29829,expected_attacker_id=30097,expected_target_title_ids=[2128])
                if projected['material_complete'] is not False or projected['action_literal'] is not None:
                    raise RuntimeError('baseline producer unexpectedly granted material/action authority')
                artifacts.extend([artifact(name+'-input.json',candidate),artifact(name+'-expected.json',projected)])
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/defender_dejure_exit_terms_v1.py',
                'ck3_autonomous_player/src/xar_autoplayer/h2743_stock_predicate_admission.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/__init__.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py',
                'ck3_autonomous_player/tests/unit/test_defender_dejure_exit_terms_v1.py']
            pins=[dict(path=p,bytes=len((root/p).read_bytes()),sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths]
            output=dict(schema='xar.ck3.dejure-exit-baseline-producer-bundle/v1',machine_id=machine,
                captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_machine_id='unknown',
                synthetic_inputs=True,native_dispatch_count=0,h2743_stock_admitted=False,
                original_tests=result.testsRun,original_skipped=0,source_pins=pins,artifacts=artifacts)
            raw=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            if len(raw)>65536: raise RuntimeError('golden bundle exceeds 64KiB budget')
            sys.stdout.buffer.write(raw)
            """;
}
