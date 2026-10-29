package org.xar.ck3.control.governance.heirpreference;

import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

/** Explicit offline recapture only; default JUnit never starts Python. */
public final class HeirPreferenceGoldenCapture {
    private HeirPreferenceGoldenCapture() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) {
            throw new IllegalArgumentException("expected Python executable, repository root, machine ID");
        }
        Path repository = Path.of(arguments[1]).toRealPath();
        String script = """
                import sys,json,hashlib,datetime
                from pathlib import Path
                sys.path.insert(0,'ck3_autonomous_player/src')
                from xar_autoplayer.first_heir_native_reproductive_preference import prioritize_observed_native_reproductive_choices as produce
                root=Path('java/ck3-control/governance-policy/src/test/resources/heirpreference')
                source=Path('ck3_autonomous_player/src/xar_autoplayer/first_heir_native_reproductive_preference.py')
                seed=root/'producer-inputs.json'
                cases=json.loads(seed.read_text(encoding='utf-8'))['cases']
                result={
                    'schema':'xar.ck3.heir-reproductive-preference.producer-golden.v1',
                    'capture':{
                        'machine_id':sys.argv[1],
                        'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'source_kind':'source-shaped-inputs-through-actual-old-python-producer',
                        'game_action':False,
                        'native_requalification':False,
                        'production_consumer_cutover':False},
                    'producer':{'path':source.as_posix(),'bytes':source.stat().st_size,
                        'sha256':hashlib.sha256(source.read_bytes()).hexdigest()},
                    'input_sha256':hashlib.sha256(seed.read_bytes()).hexdigest(),
                    'cases':[{**case,'expected':produce(case['input']['choices'],case['input']['rows'])} for case in cases]}
                output=root/'producer-golden.json'
                output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\\n',encoding='utf-8')
                print(json.dumps({'case_count':len(cases),'path':output.as_posix(),
                    'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
                    'producer':result['producer'],'observed_at_utc':result['capture']['observed_at_utc']}))
                """;
        Process child = new ProcessBuilder(Path.of(arguments[0]).toRealPath().toString(), "-B", "-X", "utf8",
                "-c", script, arguments[2]).directory(repository.toFile()).inheritIO().start();
        if (!child.waitFor(Duration.ofSeconds(15).toMillis(), TimeUnit.MILLISECONDS)) {
            child.destroyForcibly().waitFor();
            throw new IllegalStateException("offline producer capture timed out");
        }
        if (child.exitValue() != 0) {
            throw new IllegalStateException("offline producer capture failed: " + child.exitValue());
        }
    }
}
