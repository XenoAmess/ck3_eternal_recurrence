package org.xar.ck3.control.wave2.planning.scoreinputs;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.capture.PythonStdinCapture;

/** Calls the retained original eight-test/twelve-vector oracle, never the Java implementation. */
public final class CashMetricsGoldenCapture {
    private CashMetricsGoldenCapture() { }

    /** repository, interpreter, selected cash-producer-spec.json, fresh output, actual machine ID. */
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 5) { throw new IllegalArgumentException("repository python input-spec fresh-output machine-id required"); }
        Path repository = existing(arguments[0], true), python = existing(arguments[1], false);
        Path input = existing(arguments[2], false), output = Path.of(arguments[3]);
        String machine = arguments[4];
        StrictJson.require(machine.matches("[a-z0-9][a-z0-9-]{0,95}"), "explicit machine ID required");
        StrictJson.require(output.isAbsolute() && !Files.exists(output), "absolute fresh output required");
        existing(output.getParent().toString(), true);
        PythonStdinCapture.requireCompiledLauncher(CashMetricsGoldenCapture.class,
                Path.of(property(PythonStdinCapture.CLASS_ROOT_PROPERTY)), Path.of(property("xar.capture.helperRoot")));
        JsonNode spec = StrictJson.parse(read(input));
        StrictJson.object(spec, Set.of("schema", "cases"));
        StrictJson.require(spec.path("schema").asText().equals("xar.ck3.java-cashmetrics-producer-spec/v1")
                && spec.path("cases").isArray() && spec.path("cases").size() == 12, "original twelve-vector input required");
        byte[] raw = PythonStdinCapture.run(new PythonStdinCapture.Invocation(python, repository, PROGRAM,
                List.of(repository.toString(), input.toString(), machine), Duration.ofSeconds(90), 65_536)).stdout();
        validateOutput(raw, machine);
        Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        System.out.println("cashmetrics: original_tests=8 cases=12 output_created");
    }

    static void validateOutput(byte[] raw, String machine) {
        JsonNode document = StrictJson.parse(raw);
        StrictJson.object(document, Set.of("schema", "machine_id", "observed_at_utc", "producer", "source_refs",
                "original_test_count", "original_test_skipped", "cases"));
        StrictJson.require(document.path("schema").asText().equals("xar.ck3.java-cashmetrics-producer-golden/v1")
                && document.path("machine_id").asText().equals(machine)
                && StrictJson.integer(document.get("original_test_count"), 8, 8) == 8
                && StrictJson.integer(document.get("original_test_skipped"), 0, 0) == 0
                && document.path("cases").isArray() && document.path("cases").size() == 12
                && document.path("source_refs").isArray() && document.path("source_refs").size() == 11,
                "actual original producer document required");
        for (JsonNode row : document.path("source_refs")) { org.xar.ck3.control.contracts.ExactRef.fromJson(row); }
        var producer = org.xar.ck3.control.contracts.ExactRef.fromJson(document.get("producer"));
        StrictJson.require(producer.equals(org.xar.ck3.control.contracts.ExactRef.fromJson(document.path("source_refs").get(0)))
                && producer.bytes() == 10_112 && producer.sha256().equals("3d7fabb8181da6b8ae3a5e554e5a291c3b11d4e69a85100da219a8ccead72fb2"),
                "retained original cash producer source required");
    }

    private static String property(String name) {
        String value = System.getProperty(name);
        if (value == null || value.isBlank()) { throw new IllegalArgumentException("explicit " + name + " required"); }
        return value;
    }
    private static Path existing(String value, boolean directory) throws IOException {
        Path path = Path.of(value);
        StrictJson.require(path.isAbsolute(), "absolute capture path required");
        Path actual = path.toRealPath();
        if (directory ? !Files.isDirectory(actual) : !Files.isRegularFile(actual)) { throw new IOException("capture path role differs"); }
        return actual;
    }
    private static byte[] read(Path path) throws IOException {
        if (Files.size(path) != 6697) { throw new IOException("exact original twelve-vector input required"); }
        byte[] raw = Files.readAllBytes(path);
        try {
            String sha = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));
            StrictJson.require(sha.equals("9cd2ebbf66f1c1e69af8baaa5e67ab2cea5f962d6c69933f30e6ede2ec15da56"), "original input SHA differs");
        } catch (java.security.NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
        return raw;
    }

    // Retained CASHMETRICS-CAPTURE-RECIPE04 script, with explicit argv/input and stdout transport only.
    private static final String PROGRAM = """
import sys,json,hashlib,os,unittest
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
root=Path(sys.argv[1])
sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit'),str(root)]
from tools.ck3_live_run_id import current_machine_id
import xar_autoplayer.campaign_score_existing_inputs_v1 as producer
from xar_autoplayer.bridge.driver import BridgeUnavailableError
import test_campaign_score_existing_inputs_v1 as fixture
paths=[str(root/'ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py'),str(root/'ck3_autonomous_player/src/xar_autoplayer/bridge/war_cash_private_transport_v1.py'),str(root/'ck3_autonomous_player/src/xar_autoplayer/bridge/war_cash_current_raw_context_v1.py'),str(root/'ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py'),str(root/'ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py'),str(root/'ck3_autonomous_player/tests/unit/test_campaign_score_existing_inputs_v1.py'),str(root/'ck3_autonomous_player/tests/unit/test_turn_bundle_v1.py'),str(root/'ck3_autonomous_player/tests/fixtures/construction_cash_current_12004.json'),str(root/'tools/ck3_live_run_id.py'),str(Path(sys.argv[2])),str(root/'ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py')]
def refs():
    return [{'path':p,'bytes':len(Path(p).read_bytes()),'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in paths]
before=refs()
if current_machine_id()!=sys.argv[3]: raise RuntimeError('capture machine drift')
if Path(producer.__file__).resolve()!=Path(paths[0]).resolve():
    raise RuntimeError('cash metrics producer import route mismatch')
suite=unittest.defaultTestLoader.loadTestsFromName('test_campaign_score_existing_inputs_v1')
result=unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful() or result.testsRun!=8 or result.skipped:
    raise SystemExit('original eight existing-input tests did not pass without skips')
spec=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
if spec.get('schema')!='xar.ck3.java-cashmetrics-producer-spec/v1' or len(spec.get('cases',[]))!=12:
    raise ValueError('unexpected cash metrics capture spec')
cases=[]
for case in spec['cases']:
    snapshot,unused_source,packet=fixture.cash_inputs()
    for mutation in case['mutations']:
        container=snapshot if mutation['target']=='snapshot' else packet
        for key in mutation['path'][:-1]:
            container=container[key]
        key=mutation['path'][-1]
        if mutation['action']=='set':
            container[key]=deepcopy(mutation['value'])
        elif mutation['action']=='remove':
            container.pop(key,None)
        else:
            raise ValueError('unrecognized cash metrics mutation')
    request={'packet':packet,'snapshot':snapshot}
    try:
        value=producer._cash_metrics(snapshot,packet)
        expected={'status':'returned','value':value}
    except (ValueError,TypeError,KeyError,BridgeUnavailableError) as error:
        expected={'status':'rejected','error_type':type(error).__name__}
    cases.append({'id':case['id'],'request':request,'expected':expected})
if before!=refs():
    raise RuntimeError('source changed during real cash-metrics producer capture')
document={'schema':'xar.ck3.java-cashmetrics-producer-golden/v1','machine_id':current_machine_id(),'observed_at_utc':datetime.now(timezone.utc).isoformat(),'producer':before[0],'source_refs':before,'original_test_count':8,'original_test_skipped':0,'cases':cases}
raw=(json.dumps(document,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
if len(raw)>65536:
    raise ValueError('cash metrics golden exceeds 65536-byte fixture budget')
sys.stdout.buffer.write(raw)

""";
}
