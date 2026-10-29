package org.xar.ck3.control.wave2.development.constructionincome;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/**
 * Test-only fixed-original capture using qualified build-tools + Jackson.
 * No wave2 classes, mandatory golden, contracts module or Java projection is required.
 * Source launch with the complete qualified tools22-04 classpath.
 */
public final class ConstructionStandardGoldenCapture02 {
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final String REQUEST_SCHEMA = "xar.shared-golden-capture-batch/v1";
    private static final int REQUEST_BYTES = 65_536;
    private static final int STDERR_BYTES = 8_192;
    private static final long INPUT_BYTES = 8_388_608;

    private enum Producer {
        READBACK("readback", "constructionreadback/golden-inputs.json",
                "xar.ck3.constructionreadback-golden/v1", 65_536, 22),
        INCOME("income", "constructionincome/golden-inputs.json",
                "xar.ck3.constructionincome-golden/v1", 32_768, 22),
        PROVINCE("province", "constructionincome/province-golden-inputs.json",
                "xar.ck3.constructionprovinceincome-golden/v1", 32_768, 20);
        private final String wire;
        private final String resource;
        private final String schema;
        private final int maximumBytes;
        private final int cases;
        Producer(String wire, String resource, String schema, int maximumBytes, int cases) {
            this.wire = wire; this.resource = resource; this.schema = schema;
            this.maximumBytes = maximumBytes; this.cases = cases;
        }
        private static Producer parse(String value) {
            for (Producer producer : values()) { if (producer.wire.equals(value)) { return producer; } }
            throw new IllegalArgumentException("producer must be readback, income or province");
        }
    }

    /** Shared strict mapper rejects extra, missing, null and coerced record fields. */
    private record AcceptedBatch(String schema, String machineId, List<AcceptedCapture> captures) {
        private AcceptedBatch {
            require(REQUEST_SCHEMA.equals(schema), "shared capture batch schema required");
            text(machineId);
            require(captures != null && !captures.isEmpty() && captures.size() <= 32, "bounded capture list required");
            captures = List.copyOf(captures);
            Set<String> unique = new HashSet<>();
            for (AcceptedCapture capture : captures) { require(unique.add(capture.id()), "duplicate accepted capture id"); }
        }
    }

    /** Exactly the seven accepted V7 capture fields, with shared exact FileRef. */
    private record AcceptedCapture(String id, List<String> command, String cwd,
            List<FileRef> sourceRefs, List<FileRef> inputRefs, String outputPath, int maxOutputBytes) {
        private AcceptedCapture {
            text(id); text(cwd); text(outputPath);
            require(command != null && !command.isEmpty() && command.size() <= 256, "bounded accepted command required");
            command = List.copyOf(command);
            for (String argument : command) { text(argument); }
            sourceRefs = refs(sourceRefs); inputRefs = refs(inputRefs);
            require(maxOutputBytes > 0, "positive output cap required");
        }
    }

    private record PinManifest(String machineId, List<FileRef> sources, List<FileRef> inputs,
                               List<String> command) {
        private PinManifest {
            sources = List.copyOf(sources); inputs = List.copyOf(inputs); command = List.copyOf(command);
            Set<Path> unique = new HashSet<>();
            for (FileRef pin : all(sources, inputs)) {
                require(pin.bytes() <= INPUT_BYTES && unique.add(normalized(pin)), "bounded unique capture pin required");
            }
        }
        private static PinManifest read(Path path, String captureId, Path repository,
                                        Producer producer, Path output) throws IOException {
            byte[] raw;
            try (InputStream input = Files.newInputStream(path)) { raw = bounded(input, REQUEST_BYTES); }
            AcceptedBatch batch = JSON.readValue(raw, AcceptedBatch.class);
            AcceptedCapture selected = null;
            for (AcceptedCapture capture : batch.captures()) {
                if (captureId.equals(capture.id())) { selected = capture; }
            }
            require(selected != null, "accepted capture id absent");
            require(Path.of(selected.cwd()).toRealPath().equals(repository), "accepted capture cwd differs");
            require(Path.of(selected.outputPath()).toAbsolutePath().normalize().equals(output), "accepted capture output differs");
            require(selected.maxOutputBytes() == producer.maximumBytes, "accepted capture output bound differs");
            return new PinManifest(batch.machineId(), selected.sourceRefs(), selected.inputRefs(), selected.command());
        }
        private void verify() throws IOException { for (FileRef pin : all(sources, inputs)) { pin.verify(); } }
        private void requireSource(Path path) {
            require(sources.stream().anyMatch(pin -> normalized(pin).equals(path.toAbsolutePath().normalize())),
                    "mandatory source absent from exact request: " + path);
        }
        private void requireInput(Path path) {
            require(inputs.stream().anyMatch(pin -> normalized(pin).equals(path.toAbsolutePath().normalize())),
                    "mandatory fixture absent from exact request: " + path);
        }
    }

    private ConstructionStandardGoldenCapture02() { }

    /** PRODUCER MACHINE_ID REPO PYTHON ORACLE_UNIT_DIRECTORY ACCEPTED_BATCH_REQUEST CAPTURE_ID NEW_OUTPUT */
    public static void main(String[] args) throws Exception {
        require(args.length == 8,
                "usage: ConstructionStandardGoldenCapture02 PRODUCER MACHINE_ID REPO PYTHON ORACLE_UNIT_DIRECTORY ACCEPTED_BATCH_REQUEST CAPTURE_ID NEW_OUTPUT");
        Producer producer = Producer.parse(args[0]);
        String machine = text(args[1]);
        Path repository = Path.of(args[2]).toRealPath();
        Path python = Path.of(args[3]).toRealPath();
        Path oracleUnit = Path.of(args[4]).toRealPath();
        require(oracleUnit.equals(repository.resolve("ck3_autonomous_player/tests/unit").toRealPath()),
                "reference Python and frozen source must be canonically adopted under the repository");
        Path requestPath = Path.of(args[5]).toRealPath();
        String captureId = text(args[6]);
        Path output = Path.of(args[7]).toAbsolutePath().normalize();
        require(Files.isRegularFile(python), "existing Python executable required");
        require(output.getParent() != null && Files.isDirectory(output.getParent())
                && !output.startsWith(repository) && !Files.exists(output), "fresh external output required");
        require(Files.size(requestPath) <= REQUEST_BYTES, "accepted request exceeds bound");
        FileRef requestIdentity = FileRef.measure(requestPath);
        PinManifest pins = PinManifest.read(requestPath, captureId, repository, producer, output);
        require(pins.command().size() >= args.length
                && pins.command().subList(pins.command().size() - args.length, pins.command().size())
                    .equals(List.of(args)), "accepted command arguments differ from this invocation");
        require(machine.equals(pins.machineId()), "accepted request machine differs");
        Path frozen = oracleUnit.getParent().resolve("fixtures/construction_python_oracle_v1");
        for (String name : List.of("construction_python_oracle_v1.py", "construction_java_fixture_v1.py")) {
            pins.requireSource(oracleUnit.resolve(name));
        }
        for (String name : List.of("construction_formal_consumer.py.txt",
                "domain_construction_private_transport_v1.py.txt", "m5-construction-cash-enrichment.py.txt",
                "source-pins.json")) { pins.requireSource(frozen.resolve(name)); }
        for (String relative : List.of(
                "construction_selected_intent_continuity_v1.py", "construction_economic_outcome_v1.py",
                "bridge/construction_monthly_budget_v1.py", "construction_scene_scope_v1.py",
                "bridge/construction_economic_value_v1.py", "bridge/construction_owner_mode3_inputs_12004.py",
                "environment.py", "lifestyle_formal_consumer.py", "bridge/version_identity.py",
                "bridge/war_cash_private_transport_v1.py", "construction_formal_consumer.py")) {
            pins.requireSource(repository.resolve("ck3_autonomous_player/src/xar_autoplayer").resolve(relative));
        }
        pins.requireSource(repository.resolve("tools/ck3_live_run_id.py"));
        require(pins.sources().stream().filter(pin -> normalized(pin).getFileName().toString()
                .equals("ConstructionStandardGoldenCapture02.java")).count() == 1,
                "one actual test capture Java source pin required");
        pins.requireInput(repository.resolve("java/ck3-control/wave2-development/src/test/resources")
                .resolve(producer.resource));
        if (producer == Producer.READBACK) {
            pins.requireInput(repository.resolve("tools/g2_saved_campaign/fixtures/construction_cold_readback_p02_0011_minimal.json"));
        }
        requestIdentity.verify(); pins.verify();
        List<String> command = List.of(python.toString(), "-I", "-B", "-", producer.wire,
                machine, repository.toString(), oracleUnit.toString(), requestPath.toString(), captureId);
        ProcessBuilder builder = new ProcessBuilder(command).directory(repository.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONUTF8", "1");
        builder.environment().put("PYTHONIOENCODING", "utf-8");
        Process child = builder.start();
        ExecutorService readers = Executors.newFixedThreadPool(2);
        try {
            Future<byte[]> stdout = readers.submit(() -> bounded(child.getInputStream(), producer.maximumBytes));
            Future<byte[]> stderr = readers.submit(() -> bounded(child.getErrorStream(), STDERR_BYTES));
            try (var input = child.getOutputStream()) { input.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
            if (!child.waitFor(45, TimeUnit.SECONDS)) { throw new IOException("original reference producer timed out"); }
            byte[] errors = result(stderr);
            require(child.exitValue() == 0, "original reference producer exit=" + child.exitValue() + ": "
                    + new String(errors, StandardCharsets.UTF_8));
            byte[] raw = result(stdout);
            JsonNode golden = JSON.readTree(raw);
            require(producer.schema.equals(jsonText(golden, "schema"))
                    && machine.equals(jsonText(golden, "machine_id"))
                    && "REFERENCE_ORACLE".equals(jsonText(golden, "producer"))
                    && golden.path("reference_only").isBoolean() && golden.path("reference_only").booleanValue()
                    && golden.path("cases").isArray() && golden.path("cases").size() == producer.cases,
                    "original producer schema/machine/count/reference evidence differs");
            if (producer == Producer.READBACK) {
                require(golden.path("time_cases").isArray() && golden.path("time_cases").size() == 9,
                        "all original readback time cases required");
            }
            pins.verify(); requestIdentity.verify();
            Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            System.out.println("{\"status\":\"CAPTURED_REFERENCE_ORACLE\",\"bytes\":" + raw.length
                    + ",\"sha256\":\"" + FileRef.measure(output).sha256() + "\"}");
        } finally {
            if (child.isAlive()) { child.destroyForcibly(); child.waitFor(5, TimeUnit.SECONDS); }
            readers.shutdownNow();
        }
    }

    private static List<FileRef> refs(List<FileRef> rows) {
        require(rows != null && rows.size() <= 128, "bounded pin list required");
        return List.copyOf(rows);
    }
    private static Path normalized(FileRef pin) { return Path.of(pin.path()).toAbsolutePath().normalize(); }
    private static String text(String value) {
        require(value != null && !value.isEmpty() && value.equals(value.strip()), "nonempty exact text required");
        return value;
    }
    private static String jsonText(JsonNode object, String field) {
        require(object != null && object.isObject() && object.path(field).isTextual(), "required JSON text field: " + field);
        return text(object.get(field).textValue());
    }
    private static void require(boolean condition, String message) {
        if (!condition) { throw new IllegalArgumentException(message); }
    }
    private static byte[] result(Future<byte[]> future) throws Exception {
        try { return future.get(5, TimeUnit.SECONDS); }
        catch (ExecutionException error) {
            if (error.getCause() instanceof IOException io) { throw io; }
            throw error;
        }
    }
    private static List<FileRef> all(List<FileRef> first, List<FileRef> second) {
        List<FileRef> result = new ArrayList<>(first); result.addAll(second); return List.copyOf(result);
    }
    private static byte[] bounded(InputStream stream, int maximum) throws IOException {
        try (stream; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4_096]; int count;
            while ((count = stream.read(buffer)) != -1) {
                if (output.size() + count > maximum) { throw new IOException("reference child stream exceeds cap"); }
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }

    private static final String SCRIPT = """
import sys,json,hashlib,datetime,copy,ast
from pathlib import Path
kind,machine,root,unit,pin_path,capture_id=sys.argv[1:]
root,unit,pin_path=Path(root),Path(unit),Path(pin_path)
batch=json.loads(pin_path.read_text(encoding='utf-8'))
matches=[capture for capture in batch['captures'] if capture['id']==capture_id]
if len(matches)!=1: raise RuntimeError('accepted capture id is absent or ambiguous')
pins=matches[0]
all_pins=pins['source_refs']+pins['input_refs']
def check_pins():
 for pin in all_pins:
  path=Path(pin['path'])
  if path.stat().st_size!=pin['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=pin['sha256']:
   raise RuntimeError('reference capture pin drift: '+str(path))
check_pins()
sys.path[:0]=[str(root),str(root/'tools'),str(root/'ck3_autonomous_player/src'),str(unit)]
import ck3_live_run_id
if ck3_live_run_id.current_machine_id()!=machine or batch['machine_id']!=machine:
 raise RuntimeError('reference capture machine drift')
from construction_python_oracle_v1 import ConstructionPythonOracleV1
oracle=ConstructionPythonOracleV1(root)
if Path(sys.modules['construction_python_oracle_v1'].__file__).resolve()!=unit/'construction_python_oracle_v1.py':
 raise RuntimeError('reference oracle import routing drift')
frozen=oracle.fixtures
def pin_for(path):
 matches=[pin for pin in all_pins if Path(pin['path']).resolve()==path.resolve()]
 if len(matches)!=1: raise RuntimeError('mandatory unique original source pin absent: '+str(path))
 return matches[0]
formal_pin=pin_for(frozen/'construction_formal_consumer.py.txt')
transport_pin=pin_for(frozen/'domain_construction_private_transport_v1.py.txt')
resource={'readback':'constructionreadback/golden-inputs.json','income':'constructionincome/golden-inputs.json','province':'constructionincome/province-golden-inputs.json'}[kind]
data=json.loads((root/'java/ck3-control/wave2-development/src/test/resources'/resource).read_text(encoding='utf-8'))
if kind=='readback':
 fixture=json.loads((root/'tools/g2_saved_campaign/fixtures/construction_cold_readback_p02_0011_minimal.json').read_text(encoding='utf-8'))
 body=fixture['body']
 process={'pid':fixture['game_pid'],'creation_time':body['result']['post_bridge_creation_date']}
 snapshot={key:body['planning_source_frame'][key] for key in ['episode_run_id','native_revision','date_raw']}
 data['cases'].extend([{'name':'real-N40-original-scope','operation':'scope','receipt':body['plan']['construction_pending_action']},{'name':'real-N40-old-process-needs-requery','operation':'priority','ledger':{'applied_prior':[],'applied':body['plan']['construction_pending_action']},'snapshot':snapshot,'process_identity':process},{'name':'real-N40-fresh-readback-not-yet-due','operation':'priority','ledger':{'applied_prior':[],'applied':body['result']},'snapshot':snapshot,'process_identity':process}])
 for case in data['cases']:
  before=copy.deepcopy(case)
  if case['operation']=='scope':
   expected=oracle.original('construction_receipt_readback_scope_v1',(case['receipt'],))
  else:
   identity=case['process_identity']
   expected=oracle.original('priority_construction_receipt',(None,case['ledger'],case['snapshot']),{'process_identity':(identity['pid'],identity['creation_time'])})
  if case!=before: raise RuntimeError('original readback mutated supplied input')
  case['expected']=expected
 for case in data['time_cases']:
  case['expected']=oracle.original('same_construction_process_identity',((7,case['first']),(7,case['second'])))
 prefix=[formal_pin,pin_for(root/'ck3_autonomous_player/src/xar_autoplayer/environment.py')]
 data.update(schema='xar.ck3.constructionreadback-golden/v1',fixture_original_machine_id='unknown',extraction_scope=['applied_construction_receipts','construction_receipt_readback_scope_v1','priority_construction_receipt','process_creation_utc','same_construction_process_identity','same_process_creation_time'])
else:
 for case in data['cases']:
  before=copy.deepcopy(case)
  if kind=='income':
   observation=oracle.original('same_frame_construction_income',(case['snapshot'],case['history']))
   if case['operation']=='observe': expected=observation
   else: expected=oracle.original('receipt_income_original_v1',(observation[1],case['snapshot'],case['prior_receipt'],case['cold_recheck'],case['completed']))
  elif case['operation']=='observe':
   expected=oracle.original('_province_income_observation',(case['world'],case['candidate'],case['source_frame']))
  else:
   expected=oracle.original('province_income_original_v1',(case['world'],case['candidate'],case['source_frame'],case['prior_receipt'],case['cold_recheck'],case['completed']))
  if case!=before: raise RuntimeError('original income producer mutated supplied input')
  case['expected']=expected
 # Metadata comes from the same frozen original AST; no function is rewritten here.
 tree=ast.parse((frozen/'domain_construction_private_transport_v1.py.txt').read_text(encoding='utf-8'))
 query=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='query_construction_receipt')
 if kind=='income':
  start=next(index for index,node in enumerate(query.body) if isinstance(node,ast.Assign) and isinstance(node.value,ast.Name) and node.value.id=='starting_income' and any(isinstance(target,ast.Name) and target.id=='observed_income' for target in node.targets))
  segment=query.body[start:start+4]
  if len(segment)!=4 or not isinstance(segment[-1],ast.If): raise RuntimeError('fixed original scalar metadata segment drift')
  prefix=[formal_pin,transport_pin]
  schema='xar.ck3.constructionincome-golden/v1'
  scope=['same_frame_construction_income','ROOT_QUERY_STEP','query_construction_receipt scalar carry segment']
 else:
  start=next(index for index,node in enumerate(query.body) if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='_province_income_observation')
  segment=query.body[start:start+2]
  if len(segment)!=2 or not isinstance(segment[-1],ast.If): raise RuntimeError('fixed original province metadata segment drift')
  prefix=[transport_pin]
  schema='xar.ck3.constructionprovinceincome-golden/v1'
  scope=['_province_income_observation','query_construction_receipt prior province observation retention']
 data.update(schema=schema,extraction_scope=scope,receipt_segment_first_line=segment[0].lineno,receipt_segment_last_line=segment[-1].end_lineno)
data.update(machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_refs=prefix,execution_source_refs=pins['source_refs'],execution_input_refs=pins['input_refs'],producer='REFERENCE_ORACLE',reference_only=True,java_projection_executed=False,scope='Fixed original AST and pinned original dependencies only; no live migrated wrapper is used as the oracle.')
# All project Python modules actually loaded by this reference execution must
# appear as source refs, including package initializers and deferred imports.
source_paths={Path(pin['path']).resolve() for pin in pins['source_refs']}
for module in list(sys.modules.values()):
 loaded=getattr(module,'__file__',None)
 if loaded is None: continue
 path=Path(loaded).resolve()
 if path.is_relative_to(root) and path.suffix=='.py' and path not in source_paths:
  raise RuntimeError('reference import closure lacks source pin: '+str(path))
check_pins()
raw=(json.dumps(data,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
cap=65536 if kind=='readback' else 32768
if len(raw)>cap: raise RuntimeError('original reference evidence exceeds domain output cap')
sys.stdout.buffer.write(raw)
""";
}
