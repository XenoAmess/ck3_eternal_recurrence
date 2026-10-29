package org.xar.ck3.control.planning.optionalcadence;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;

/** Explicit, non-default migration oracle capture. An external qualified Job owns all children. */
public final class OptionalCadenceGoldenCapture {
    private OptionalCadenceGoldenCapture() { }

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 5) {
            throw new IllegalArgumentException("python-executable repository-root scratch-root output-json machine-id required");
        }
        Path python = Path.of(args[0]).toAbsolutePath().normalize();
        Path repository = Path.of(args[1]).toRealPath();
        Path scratch = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        String machineId = args[4];
        if (machineId == null || machineId.isBlank()) { throw new IllegalArgumentException("machine_id required"); }
        Path producer = repository.resolve("ck3_autonomous_player/src/xar_autoplayer/optional_check_cadence_v1.py");
        Path outputRoot = repository.resolve("java/ck3-control/planning-runtime/src/test/resources/optionalcadence");
        if (!Files.isRegularFile(python) || !Files.isRegularFile(producer) || !output.startsWith(outputRoot)
                || !scratch.toString().replace('\\', '/').startsWith("D:/codex-ck3-demos/2026-10-22-java-phase1/")) {
            throw new IllegalArgumentException("capture paths are outside the assigned boundary");
        }
        String before = sha256(producer);
        Path work = Files.createTempDirectory(scratch, "optionalcadence-capture-");
        Path stdout = work.resolve("producer-golden.json");
        Path stderr = work.resolve("producer-stderr.txt");
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-I", "-B", "-X", "utf8", "-c", ORACLE,
                producer.toString(), work.toString(), machineId);
        builder.directory(work.toFile());
        builder.redirectOutput(stdout.toFile());
        builder.redirectError(stderr.toFile());
        Process process = builder.start();
        if (!process.waitFor(Duration.ofSeconds(60).toMillis(), TimeUnit.MILLISECONDS)) {
            process.descendants().forEach(ProcessHandle::destroyForcibly);
            process.destroyForcibly();
            process.waitFor(10, TimeUnit.SECONDS);
            throw new IOException("producer capture timeout; no golden published");
        }
        if (process.exitValue() != 0) { throw new IOException("producer capture exit " + process.exitValue() + "; see " + stderr); }
        if (!before.equals(sha256(producer))) { throw new IOException("producer changed during capture"); }
        long size = Files.size(stdout);
        if (size <= 0 || size > 131_072 || Files.size(stderr) != 0) {
            throw new IOException("unexpected capture output size or stderr");
        }
        byte[] captured = Files.readAllBytes(stdout);
        StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(captured));
        Files.createDirectories(output.getParent());
        Files.write(output, captured);
        System.out.println("OPTIONAL_CADENCE_REAL_PRODUCER_CAPTURE_OK sha256=" + sha256(output) + " bytes=" + size);
    }

    private static String sha256(Path path) throws IOException {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 unavailable", error); }
    }

    // This is a bounded test oracle invoking only the unchanged existing producer, not a second implementation.
    private static final String ORACLE = """
            import copy, datetime, hashlib, importlib.util, json, pathlib, sys, tempfile
            source=pathlib.Path(sys.argv[1])
            spec=importlib.util.spec_from_file_location('optional_cadence_existing_producer',source)
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cases=[]
            def scenario(name,episode,operations):
                with tempfile.TemporaryDirectory(dir=sys.argv[2],prefix='state-') as directory:
                    directory=pathlib.Path(directory)
                    steps=[]
                    for operation in operations:
                        op=copy.deepcopy(operation)
                        current=(op.get('episode',episode),op['date_raw'],op['native_revision'])
                        kind=op['operation']
                        if kind=='record':
                            module.record(directory,op['domain'],current,actual_action=op['actual_action'])
                        elif kind=='defer_council':
                            module.defer_council_technical_read(directory,current,evidence_path=op['evidence_path'])
                        elif kind=='requalify':
                            op['expected_changed']=module.requalify_lifestyle_frontier_once(directory,current,native_catalogue=op['native_catalogue'])
                        elif kind=='deferred':
                            op['expected_deferred']=module.deferred(directory,op['domain'],current)
                        elif kind=='action_recorded':
                            op['expected_action_recorded']=module.action_recorded(directory,op['domain'],current)
                        else:
                            raise ValueError(kind)
                        op['expected_state']=copy.deepcopy(module._load(directory,current[0]))
                        steps.append(op)
                    cases.append({'name':name,'episode':episode,'steps':steps})
            def record(domain,date,revision,action=False,**extra):
                return dict(operation='record',domain=domain,date_raw=date,native_revision=revision,actual_action=action,**extra)
            def deferred(domain,date,revision):
                return dict(operation='deferred',domain=domain,date_raw=date,native_revision=revision)
            def technical(date,revision,evidence):
                return dict(operation='defer_council',date_raw=date,native_revision=revision,evidence_path=evidence)
            def requalify(date,revision,catalogue):
                return dict(operation='requalify',date_raw=date,native_revision=revision,native_catalogue=catalogue)
            scenario('three-noops-deduplicate-boundaries-and-action','cadence-oracle-one',[
                record('council',0,1),record('council',0,1),record('council',24,2),
                record('council',48,3),deferred('council',72,4),deferred('council',767,4),
                deferred('council',768,4),record('ransom',72,4),record('council',72,4,True),
                record('council',72,4,True),dict(operation='action_recorded',domain='council',date_raw=72,native_revision=4),
                dict(operation='action_recorded',domain='council',date_raw=72,native_revision=5),
                record('council',72,4)])
            scenario('technical-unavailable-is-neither-noop-nor-action','cadence-oracle-two',[
                record('council',0,1),technical(24,2,'evidence/中文-query.json'),
                technical(24,2,'evidence/must-not-replace-same-frame.json'),record('council',24,2),
                deferred('council',48,3),technical(48,3,'evidence/later-query.json'),
                deferred('council',767,4),deferred('council',768,4),record('council',768,4),
                technical(792,5,'evidence/third-query.json'),record('council',792,5,True)])
            scenario('catalogue-upgrade-resets-only-lifestyle-once','cadence-oracle-three',[
                record('lifestyle',0,1),record('lifestyle',24,2),record('lifestyle',48,3),
                record('council',0,1),record('council',24,2),record('council',48,3),
                requalify(72,4,'game.state.private-lifestyle-stewardship-frontier-v2'),
                requalify(72,4,'game.state.private-lifestyle-stewardship-frontier-v2'),
                deferred('council',72,4),record('lifestyle',72,4),
                requalify(96,5,'game.state.private-lifestyle-all-frontier-v3'),
                record('lifestyle',96,5,True),requalify(96,5,'game.state.private-lifestyle-all-frontier-v3')])
            huge=2**80
            scenario('arbitrary-precision-and-episode-reset','cadence-oracle-four',[
                record('feast',huge,huge),record('feast',huge+1,huge+1),record('feast',huge+2,huge+2),
                deferred('feast',huge+3,huge+3),record('feast',0,0,episode='fresh-episode')])
            snapshot_results=[]
            for snapshot in [dict(paused=True,episode_run_id='frame',date_raw=0,native_revision=0),
                    dict(paused=False,episode_run_id='frame',date_raw=0,native_revision=0),
                    dict(paused=True,episode_run_id='frame',date_raw=True,native_revision=0),
                    dict(paused=True,episode_run_id='frame',date_raw=0,native_revision=1.0),
                    dict(paused=True,episode_run_id='',date_raw=0,native_revision=0),
                    dict(paused=True,episode_run_id='frame',date_raw=huge,native_revision=huge)]:
                result=module.frame(snapshot)
                snapshot_results.append({'snapshot':snapshot,'expected_frame':list(result) if result is not None else None})
            result={'schema':'xar.optional-check-cadence.golden.v1','machine_id':sys.argv[3],
                'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'producer':{'path':'ck3_autonomous_player/src/xar_autoplayer/optional_check_cadence_v1.py',
                    'sha256':hashlib.sha256(source.read_bytes()).hexdigest()},
                'producer_exit_code':0,'cases':cases,'snapshot_cases':snapshot_results}
            print(json.dumps(result,ensure_ascii=False,separators=(',',':')))
            """;
}
