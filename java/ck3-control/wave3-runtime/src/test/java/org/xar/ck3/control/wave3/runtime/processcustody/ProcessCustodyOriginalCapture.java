package org.xar.ck3.control.wave3.runtime.processcustody;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.capture.PythonStdinCapture;

/** Captures the unchanged original producer and SDK-pair consumer using injected handles. */
public final class ProcessCustodyOriginalCapture {
    private ProcessCustodyOriginalCapture() { }

    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 5) {
            throw new IllegalArgumentException("repository python scratch output machine required");
        }
        Path repository = Path.of(arguments[0]).toRealPath();
        Path python = Path.of(arguments[1]).toRealPath();
        Path scratch = Path.of(arguments[2]).toRealPath();
        Path output = Path.of(arguments[3]).toAbsolutePath().normalize();
        String machine = StrictJson.text(arguments[4]);
        if (!Files.isDirectory(repository) || !Files.isDirectory(scratch)
                || !python.equals(repository.resolve("tools/.venv/Scripts/python.exe").toRealPath())
                || output.startsWith(repository) || scratch.startsWith(repository)
                || !Files.isDirectory(output.getParent()) || Files.exists(output)) {
            throw new IllegalArgumentException("actual repository interpreter and fresh external output required");
        }
        PythonStdinCapture.requireCompiledLauncher(ProcessCustodyOriginalCapture.class,
                requiredOrigin("xar.capture.classRoot"), requiredOrigin("xar.capture.helperRoot"));
        byte[] raw = PythonStdinCapture.run(new PythonStdinCapture.Invocation(python, repository,
                SCRIPT, List.of(repository.toString(), scratch.toString(), machine),
                Duration.ofSeconds(60), 98_304)).stdout();
        var golden = StrictJson.parse(raw, 98_304);
        StrictJson.require(StrictJson.text(golden.get("schema")).equals(
                "xar.processcustody-original-producer-golden/v1"), "original custody schema required");
        StrictJson.require(StrictJson.text(golden.get("machine_id")).equals(machine), "observing machine required");
        StrictJson.require(golden.path("cases").isArray() && golden.path("cases").size() == 26
                && golden.path("sdk_pair_consumers").isArray()
                && golden.path("sdk_pair_consumers").size() == 6, "complete original custody cases required");
        StrictJson.integer(golden.path("original_complete_fake_suite").get("tests_run"), 22, 22);
        Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }

    private static Path requiredOrigin(String property) {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) { throw new IllegalArgumentException("explicit " + property + " required"); }
        return Path.of(value);
    }

    private static final String SCRIPT = """
import copy, datetime, hashlib, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
repository=Path(sys.argv[1]).resolve();scratch=Path(sys.argv[2]).resolve();machine=sys.argv[3]
sys.path.insert(0,str(repository));sys.path.insert(0,str(repository/'tools'))
from ck3_live_run_id import current_machine_id
if current_machine_id()!=machine:raise RuntimeError('actual machine mismatch')
from tools.g2_saved_campaign import sdk_process_custody as sdk
from tools.g2_saved_campaign import runtime_repair_status_v2 as status
pins = [('tools/g2_saved_campaign/sdk_process_custody.py',14743,'55e4409b2b0920085d432cd4a7ef9eef316a49762856db33e07d802128c274cc'),('tools/g2_saved_campaign/runtime_repair_status_v2.py',18989,'cd0983bfa17877cf5781017e388435d4e980a57c03940edc32236ba4fd9d36ba'),('tools/g2_saved_campaign/runtime_repair_status.py',20920,'5fd2fd03ed8febb949d70d77f4da24d80dc9f19b6f82f6e25a067a734a351705')]
original = {}
for name, size, digest in pins:
    path = repository / name
    raw = path.read_bytes()
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest: raise RuntimeError('source pin drift: ' + name)
    original[path] = raw
test_path = repository/'tools/test_g2_sdk_process_custody.py'
original[test_path] = test_path.read_bytes()
machine_source=repository/'tools/ck3_live_run_id.py';original[machine_source]=machine_source.read_bytes()
suite_result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(unittest.defaultTestLoader.loadTestsFromName('tools.test_g2_sdk_process_custody'))
if not suite_result.wasSuccessful() or suite_result.testsRun != 22 or suite_result.skipped: raise RuntimeError('original complete fake-handle suite did not pass')
BASE_BIRTH = 134371502550367280
class Api:
    def __init__(self, pid=17):
        self.pid, self.birth, self.image = pid, BASE_BIRTH + pid - 17, 'C:/Python/python.exe'
        self.wait, self.exit, self.fail_wait, self.fail_exit, self.fail_close = 258,259,False,False,False
        self.handle, self.calls = object(), dict(open=0, birth=0, image=0, wait=0, exit=0, close=0)
    def open_process(self, pid): self.calls['open'] += 1; return self.handle
    def query_creation_filetime(self, h): self.calls['birth'] += 1; return self.birth
    def query_executable(self, h): self.calls['image'] += 1; return self.image
    def wait_zero(self, h):
        self.calls['wait'] += 1
        if h is not self.handle: raise AssertionError('foreign handle')
        if self.fail_wait: raise OSError('injected wait failure')
        return self.wait
    def get_exit_code(self, h):
        self.calls['exit'] += 1
        if h is not self.handle: raise AssertionError('foreign handle')
        if self.fail_exit: raise OSError('injected exit failure')
        return self.exit
    def close_handle(self, h):
        self.calls['close'] += 1
        if h is not self.handle: raise AssertionError('foreign handle')
        if self.fail_close: raise OSError('injected close failure')
cases = []
def one(name, changes):
    api = Api()
    generation = sdk.RetainedProcessGeneration.capture(17, expected_creation_filetime=BASE_BIRTH, expected_executable=api.image, api=api)
    closed = changes.get('closed', False)
    for key,value in changes.items():
        if key not in ('closed','mutate_identity'): setattr(api,key,value)
    if changes.get('mutate_identity'): api.birth += 100; api.image = 'C:/replacement/python.exe'
    close_error = None
    if closed:
        try: generation.close()
        except OSError as error: close_error = str(error)
    observed = generation.observe()
    try: generation.require_live(); live = True
    except sdk.ProcessCustodyError: live = False
    try: generation.close(); generation.close()
    except OSError as error: close_error = str(error)
    cases.append(dict(id=name, configuration=changes, observation=observed, require_live=live, calls=api.calls, close_error=close_error))
for code in (0,259,4294967295): one('unsignaled-exit-' + str(code), dict(exit=code))
for code in (0,1,259,4294967295): one('signaled-exit-' + str(code), dict(wait=0,exit=code))
for code in (1,4294967295,-1): one('unknown-wait-' + str(code), dict(wait=code))
one('wait-api-error', dict(fail_wait=True))
for name,value in [('bool',True),('float',258.0),('string','258'),('null',None)]: one('wrong-wait-' + name,dict(wait=value))
for wait in (0,258): one('exit-api-error-wait-' + str(wait),dict(wait=wait,fail_exit=True))
for name,value in [('negative',-1),('overflow',4294967296),('bool',True),('float',259.0),('string','259'),('null',None)]: one('wrong-exit-' + name,dict(exit=value))
one('closed-observation',dict(closed=True))
one('failed-close-stays-closed',dict(closed=True,fail_close=True))
one('identity-not-requeried',dict(mutate_identity=True))
consumer = []
actual_capture, actual_observe = sdk.RetainedProcessGeneration.capture, sdk.RetainedProcessGeneration.observe
for name in ('live','queue-exit-259','application-exit-1','wait-unavailable','second-capture-failure','late-application-exit'):
    with tempfile.TemporaryDirectory(prefix='processcustody-',dir=scratch) as folder:
        root = Path(folder); apis = {17:Api(17),21:Api(21)}; captures = []; emitted = []; observed = []
        if name == 'queue-exit-259': apis[17].wait,apis[17].exit = 0,259
        if name == 'application-exit-1': apis[21].wait,apis[21].exit = 0,1
        if name == 'wait-unavailable': apis[21].fail_wait = True
        pair = dict(status='SDK_PAIR_HANDLES_RETAINED',future_extension=dict(opaque=True),processes=[dict(role=role,pid=pid,creation_filetime=BASE_BIRTH+pid-17,executable='C:/Python/python.exe',future_row_extension='preserved original') for role,pid in [('sdk_queue',17),('sdk_application',21)]])
        pair_raw = json.dumps(pair,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        pair_path = root/'ROOT-ACTUAL-SDK-PROCESSES-PINNED-P35.json'; pair_path.write_text(pair_raw,encoding='utf-8')
        publisher = status.IncrementalPublisher.__new__(status.IncrementalPublisher)
        publisher.session,publisher.store,publisher.prefix,publisher.binding = root,root/'status','p35',dict(synthetic=True)
        publisher._sdk_handles,publisher._sdk_capture_error,publisher._sdk_failure_reported = None,None,False
        publisher.open_source_incident = lambda *args: emitted.append(args)
        def capture(pid, **kwargs):
            captures.append(pid)
            if name == 'second-capture-failure' and pid == 21: raise OSError('injected second capture failure')
            return actual_capture(pid,api=apis[pid],**kwargs)
        def observe(generation):
            value = actual_observe(generation); observed.append(dict(value)); return value
        snapshots = []
        with patch.object(sdk.RetainedProcessGeneration,'capture',side_effect=capture), patch.object(sdk.RetainedProcessGeneration,'observe',new=observe):
            for index in range(3):
                if name == 'late-application-exit' and index == 1: apis[21].wait,apis[21].exit = 0,1
                start = len(observed); publisher.observe_sdk_pair()
                snapshots.append(dict(observations=observed[start:],capture_error=publisher._sdk_capture_error is not None,incident_count=len(emitted),capture_attempts=list(captures)))
            publisher.close(); publisher.close()
        consumer.append(dict(id=name,published_pair_json=pair_raw,snapshots=snapshots,calls={str(pid):api.calls for pid,api in apis.items()}))
for path,raw in original.items():
    if path.read_bytes() != raw: raise RuntimeError('source changed during capture: ' + str(path))
body = dict(schema='xar.processcustody-original-producer-golden/v1',machine_id=machine,observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=[dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for path,raw in original.items()],scope='original producer and actual SDK-pair consumer with injected handles; no native/process/Game/canonical access',original_complete_fake_suite=dict(tests_run=suite_result.testsRun,failures=0,errors=0,skipped=0),cases=cases,sdk_pair_consumers=consumer)
payload = (json.dumps(body,ensure_ascii=False,separators=(',',':'))+'\\n').encode('utf-8')
if len(payload) > 98304: raise RuntimeError('bounded golden too large')
sys.stdout.buffer.write(payload)

""";
}
