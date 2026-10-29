package org.xar.ck3.control.wave2.military.stockconsumers;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrameCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteProjection;
import org.xar.ck3.control.wave2.military.stocksupply.StockSupplyCodec;
import org.xar.ck3.control.wave2.military.stocksupply.StockSupplyProjection;
import org.xar.ck3.control.wave2.military.stocksupply.NextFleetRate;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSupplyRisk;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSupplyRiskCodec;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSoldierEffects;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSoldierEffectsCodec;

/** Explicit bounded post-build probe. Domain code executes in this one JVM; Python owns original consumers. */
public final class ProbeCompiledStockConsumers {
    static final int FRAME_LIMIT = 262_144;
    private static final int OUTPUT_LIMIT = 196_608;
    enum Operation { UPDATER, STOCK, RATE, RISK, EFFECTS, UPDATER_REJECT }
    record Message(int sequence, Operation operation, JsonNode row, JsonNode risk, String rawJson) { }
    record Ref(Path path, long bytes, String sha256) {
        static Ref decode(JsonNode node) {
            if (node == null || !node.isObject() || node.size() != 3 || !node.has("path") || !node.has("bytes") || !node.has("sha256")
                    || !node.get("path").isTextual() || !node.get("bytes").isIntegralNumber()
                    || !node.get("bytes").canConvertToLong() || node.get("bytes").longValue() < 1
                    || !node.get("sha256").isTextual() || !node.get("sha256").textValue().matches("[a-f0-9]{64}")) {
                throw new IllegalArgumentException("exact bounded file reference required");
            }
            return new Ref(Path.of(node.get("path").textValue()).toAbsolutePath().normalize(),
                    node.get("bytes").longValue(), node.get("sha256").textValue());
        }
        void verify() throws Exception {
            if (!Files.isRegularFile(path) || Files.isSymbolicLink(path) || bytes > 16_777_216
                    || Files.size(path) != bytes || !hash(Files.readAllBytes(path)).equals(sha256)) {
                throw new IllegalStateException("qualified input drift: " + path);
            }
        }
        ObjectNode encode() {
            ObjectNode node = StrictJson.object();
            node.put("path", path.toString()); node.put("bytes", bytes); node.put("sha256", sha256); return node;
        }
    }
    private ProbeCompiledStockConsumers() { }

    static Message decodeMessage(byte[] raw) {
        JsonNode node = StrictJson.parse(raw, FRAME_LIMIT);
        Set<String> fields = Set.of("kind", "sequence", "operation", "row", "risk", "raw_json");
        if (!node.isObject() || node.size() != fields.size() || fields.stream().anyMatch(key -> !node.has(key))
                || !node.get("kind").isTextual() || !"request".equals(node.get("kind").textValue())
                || !node.get("sequence").isIntegralNumber() || !node.get("sequence").canConvertToInt()
                || node.get("sequence").intValue() < 1 || !node.get("operation").isTextual()) {
            throw new IllegalArgumentException("closed request and integer sequence required");
        }
        Operation operation = Operation.valueOf(node.get("operation").textValue());
        if (operation == Operation.UPDATER_REJECT) {
            if (!node.get("row").isNull() || !node.get("risk").isNull() || !node.get("raw_json").isTextual()) {
                throw new IllegalArgumentException("raw rejection token bytes required");
            }
        } else if (!node.get("row").isObject() || !node.get("raw_json").isNull()
                || (operation == Operation.EFFECTS ? !node.get("risk").isObject() : !node.get("risk").isNull())) {
            throw new IllegalArgumentException("declared row/risk shape required");
        }
        return new Message(node.get("sequence").intValue(), operation, node.get("row"), node.get("risk"),
                node.get("raw_json").isTextual() ? node.get("raw_json").textValue() : null);
    }

    static JsonNode dispatch(Message message) {
        // decodeMessage already bounds and validates this transport frame. Preserve
        // floating opaque SDK extensions and let each declared field decoder
        // reject its own non-integral operands without re-encoding the whole row.
        return switch (message.operation()) {
            case UPDATER -> UpdaterWriteCodec.encode(UpdaterWriteProjection.project(UpdaterWriteCodec.decode(message.row())));
            case STOCK -> StockSupplyCodec.encode(StockSupplyProjection.project(StockSupplyCodec.decodeRow(message.row())));
            case RATE -> StockSupplyCodec.encodeRate(NextFleetRate.project(StockSupplyCodec.decodeRateRow(message.row())));
            case RISK -> CallbackSupplyRiskCodec.encode(CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decodeRow(message.row())));
            case EFFECTS -> {
                var risk = CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decodeRow(message.row()));
                if (!java.util.Arrays.equals(StrictJson.canonical(CallbackSupplyRiskCodec.encode(risk), FRAME_LIMIT),
                        StrictJson.canonical(message.risk(), FRAME_LIMIT))) {
                    throw new IllegalArgumentException("original consumer did not pass the actual same-row Java risk");
                }
                yield CallbackSoldierEffectsCodec.encode(CallbackSoldierEffects.project(
                        CallbackSoldierEffectsCodec.decodeRow(message.row(), risk)));
            }
            case UPDATER_REJECT -> {
                boolean rejected = false;
                try { SourceNextFrameCodec.decode(message.rawJson().getBytes(StandardCharsets.UTF_8), 11, 12); }
                catch (IllegalArgumentException expected) { rejected = true; }
                yield com.fasterxml.jackson.databind.node.BooleanNode.valueOf(rejected);
            }
        };
    }

    static byte[] readFrame(InputStream input, int maximum) throws IOException {
        ByteArrayOutputStream body = new ByteArrayOutputStream();
        for (;;) {
            int value = input.read();
            if (value == -1) {
                if (body.size() == 0) return null;
                throw new IOException("unterminated child frame");
            }
            if (value == 10) return body.toByteArray();
            if (body.size() == maximum) throw new IOException("child frame exceeds declared limit");
            body.write(value);
        }
    }

    private static final String PYTHON = """
import asyncio,contextlib,copy,gzip,hashlib,io,json,pathlib,sys,tempfile,threading,unittest
root=pathlib.Path(sys.argv[1]).resolve(); fixtures=pathlib.Path(sys.argv[2]).resolve()
sys.path[:0]=[str(root/'tools'),str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
tempfile.tempdir=str(fixtures)
def unique(pairs):
    value={}
    for key,item in pairs:
        if key in value: raise ValueError('duplicate JSON key')
        value[key]=item
    return value
def loads(raw):
    def reject(value): raise ValueError('non-JSON constant '+value)
    return json.loads(raw,object_pairs_hook=unique,parse_constant=reject)
initial=loads(sys.stdin.readline())
if initial['schema']!='xar.stock3.compiled-consumer-input/v1': raise RuntimeError('Java input schema')
sequence=0; calls={}; lock=threading.Lock()
def java(operation: str,row: dict[str,object] | None=None,risk: dict[str,object] | None=None,raw_json: str | None=None) -> object:
    global sequence
    with lock:
        sequence+=1
        request=dict(kind='request',sequence=sequence,operation=operation,row=row,risk=risk,raw_json=raw_json)
        sys.stdout.write(json.dumps(request,separators=(',',':'))+chr(10));sys.stdout.flush()
        response=loads(sys.stdin.readline())
        if type(response) is not dict or set(response)!={'sequence','ok','value'} or type(response['sequence']) is not int or response['sequence']!=sequence or response['ok'] is not True: raise RuntimeError('actual Java rejected request: '+str(response))
        if operation=='UPDATER_REJECT':
            if type(response['value']) is not bool: raise RuntimeError('actual Java rejection discriminator is not bool')
        elif type(response['value']) is not dict: raise RuntimeError('actual Java projection is not an object')
        calls[operation]=calls.get(operation,0)+1
        return response['value']
import xar_autoplayer.bridge.service as service_mod
import xar_autoplayer.bridge.army_next_updater_write_projection as updater_mod
import xar_autoplayer.bridge.army_next_stock_supply_budget_projection as stock_mod
import xar_autoplayer.bridge.army_next_land_stock_supply_budget_projection as land_mod
import xar_autoplayer.bridge.army_zero_stock_clock_12004 as zero_mod
import xar_autoplayer.bridge.army_current_callback_supply_risk_projection as risk_mod
import xar_autoplayer.bridge.army_current_callback_soldier_effects_projection as effects_mod
from unittest.mock import patch
original_updater=updater_mod.project_source_derived_next_updater_writes_v1
original_stock=stock_mod.project_source_derived_next_stock_supply_budget_v1
original_rate=stock_mod.project_next_admitted_day_fleet_rate_v1
original_risk=risk_mod.project_current_callback_supply_risk_v1
original_effects=effects_mod.project_current_callback_soldier_effects_v1
for module in (service_mod,updater_mod,stock_mod,land_mod,zero_mod,risk_mod,effects_mod):
    if not pathlib.Path(module.__file__).resolve().is_relative_to(root/'ck3_autonomous_player/src'):
        raise RuntimeError('consumer import escaped pinned source root')
def same(left: object,right: object) -> bool:
    if type(left) is not type(right): return False
    if type(left) is dict: return left.keys()==right.keys() and all(same(left[key],right[key]) for key in left)
    if type(left) in (list,tuple): return len(left)==len(right) and all(same(a,b) for a,b in zip(left,right))
    return left==right
def compare(operation,original,row,risk=None):
    before=copy.deepcopy(row)
    expected=loads(json.dumps(original(row) if risk is None else original(row,risk),separators=(',',':')))
    actual=java(operation,row,risk)
    if not same(actual,expected) or not same(row,before): raise AssertionError(operation+' actual Java bytes differ at original consumer boundary')
    return actual
def updater(row): return compare('UPDATER',original_updater,row)
def stock(row): return compare('STOCK',original_stock,row)
def rate(row): return compare('RATE',original_rate,row)
def risk(row): return compare('RISK',original_risk,row)
def effects(row,observed_risk): return compare('EFFECTS',original_effects,row,observed_risk)
with contextlib.ExitStack() as stack:
    for module in (service_mod,stock_mod,land_mod,zero_mod):
        stack.enter_context(patch.object(module,'project_source_derived_next_updater_writes_v1',updater))
    stack.enter_context(patch.object(service_mod,'project_source_derived_next_stock_supply_budget_v1',stock))
    for module in (service_mod,stock_mod):
        stack.enter_context(patch.object(module,'project_next_admitted_day_fleet_rate_v1',rate))
    stack.enter_context(patch.object(service_mod,'project_current_callback_supply_risk_v1',risk))
    stack.enter_context(patch.object(service_mod,'project_current_callback_soldier_effects_v1',effects))
    direct=0
    def downstream(consumer,row):
        try: return ('returned',consumer(row))
        except ValueError as error: return ('rejected',type(error).__name__,str(error))
    for vector in initial['updater']['projections']:
        row=vector['input']
        for consumer in (original_stock,land_mod.project_source_derived_next_land_stock_supply_budget_v1,zero_mod.project_zero_stock_next_callback_candidate_12004):
            before=copy.deepcopy(row)
            with contextlib.ExitStack() as baseline:
                for module in (stock_mod,land_mod,zero_mod):
                    baseline.enter_context(patch.object(module,'project_source_derived_next_updater_writes_v1',original_updater))
                baseline.enter_context(patch.object(stock_mod,'project_next_admitted_day_fleet_rate_v1',original_rate))
                expected=downstream(consumer,row)
            actual=downstream(consumer,row)
            if not same(actual,expected) or not same(row,before): raise AssertionError('original ordered consumer changed after consuming actual Java updater bytes')
            direct+=1
    for vector in initial['updater']['rejections']:
        if java('UPDATER_REJECT',raw_json=vector['raw_json']) is not True: raise AssertionError('raw original rejection token accepted by Java')
    for vector in initial['stock']['rate_vectors']:
        if not same(rate(vector['input']),vector['expected']): raise AssertionError('standalone Java Fleet rate branch differs')
    for vector in initial['callback']['vectors']:
        row=vector['input']; actual_risk=risk(row); actual_effects=effects(row,actual_risk)
        if not same(actual_risk,vector['expected_risk']) or not same(actual_effects,vector['expected_effects']): raise AssertionError('Java callback chain differs from retained original vector')
    import test_current_callback_supply_risk_service_12004 as risk_test
    import test_current_callback_soldier_effects_service_12004 as ordered_test
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(risk_test),unittest.defaultTestLoader.loadTestsFromModule(ordered_test)])
    result=unittest.TextTestRunner(stream=sys.stderr,verbosity=2).run(suite)
    if result.testsRun!=2 or result.skipped or not result.wasSuccessful(): raise RuntimeError('complete original current-risk/ordered registered consumer modules failed')
    from test_native_bridge_driver import _army,_hello,_snapshot
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.version_identity import CK3_12004
    from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_CAPABILITY
    async def registered_stock():
        row=copy.deepcopy(initial['stock']['service_consumer']['input']); before_row=copy.deepcopy(row)
        endpoint=ordered_test._CurrentCallbackEndpoint()
        driver=NativeHeadlessGameplayDriver(endpoint=endpoint,state_dir=fixtures/'stock-driver-state',save_dir=fixtures/'unused-save',command_timeout_seconds=0.5,episode_projection='native_campaign')
        try:
            hello=_hello('bridge.heartbeat','game.state.snapshot',QUERY_ARMY_STRENGTHS_CAPABILITY)
            hello.update(game_version=CK3_12004.game_version,executable_sha256=CK3_12004.executable_sha256)
            endpoint.publish(hello)
            endpoint.whole=dict(type='command_result',protocol_version=1,request_id='source-shaped-stock-java-consumer',ok=True,result=dict(step='query-army-strengths',accepted=True,status='available',query_sequence=1,army_strengths=[copy.deepcopy(row)]))
            # Keep the actual symbolic step from the unchanged module.
            from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP
            endpoint.whole['result']['step']=QUERY_ARMY_STRENGTHS_STEP
            endpoint.publish(_snapshot(revision=41,date_raw=row['army_update_clock_v1']['current_date_raw'],played_character=dict(character_id=29829,alive=True,name='Robert'),player_armies=[_army(0,soldiers=row['current_soldiers'],owner_character_id=29829)],active_wars=[]))
            before=driver.take_snapshot(); server=create_server(driver)
            observed=await server.call_tool('ck3_query_army_strengths',dict(army_ids=[0],expected_revision=before['revision']))
            if observed.is_error is not False: raise AssertionError('registered stock route rejected Java output')
            value=observed.structured_content
            for key,original in before_row.items():
                if value['army_strengths'][0][key]!=original or driver._army_strength_query['army_strengths'][0][key]!=original: raise AssertionError('real Driver/Service changed source operand '+key)
            if value['source_derived_next_updater_writes_v1'][0]['projection']!=java('UPDATER',row): raise AssertionError('Java updater did not reach registered Service')
            if value['source_derived_next_stock_supply_budget_v1'][0]['projection']!=java('STOCK',row): raise AssertionError('Java stock did not reach registered Service')
            if value['same_input_conditional_next_admitted_day_fleet_rate_v1'][0]['projection']!=java('RATE',row): raise AssertionError('Java standalone Fleet rate did not reach registered Service')
            if len(endpoint.requests)!=1 or row!=before_row: raise AssertionError('registered stock transport count/input preservation')
            return dict(native_driver_queries=1,registered_service_queries=1,updater_and_stock_java_wire_consumed=True,source_shaped_envelope=True,compiled_native_reader=False)
        finally: driver.close()
    registered=asyncio.run(registered_stock())
    if direct!=72 or any(calls.get(key,0)<1 for key in ('UPDATER','STOCK','RATE','RISK','EFFECTS','UPDATER_REJECT')): raise AssertionError('closed finite consumer coverage incomplete')
    summary=dict(kind='complete',tests_run=result.testsRun,skipped=0,failures=0,errors=0,direct_ordered_updater_consumers=direct,callback_java_risk_to_original_effects_cases=8,standalone_java_rate_cases=12,registered_stock=registered,original_registered_callback_scenes=5,actual_java_calls=calls,compiled_native_reader=False,live=False,original_external_whole_stock_and_updater_tests='NOTRUN: required native wire/context inputs not supplied')
sys.stdout.write(json.dumps(summary,separators=(',',':'))+chr(10));sys.stdout.flush()
""";

    public static void main(String[] args) throws Exception {
        if (args.length != 6) throw new IllegalArgumentException("repo python compiled-packet output fresh-fixture-root machine required");
        Path root = Path.of(args[0]).toRealPath(), configPath = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize(), fixtures = Path.of(args[4]).toAbsolutePath().normalize();
        if (Files.size(configPath) < 1 || Files.size(configPath) > FRAME_LIMIT) throw new IllegalArgumentException("bounded compiled packet required");
        byte[] configBytes = Files.readAllBytes(configPath);
        JsonNode config = StrictJson.parse(configBytes, FRAME_LIMIT);
        Ref configRef = new Ref(configPath, configBytes.length, hash(configBytes));
        JsonNode roots = StrictJson.object(config.path("roots"), Set.of("scratch", "logs", "artifacts", "source_staging"));
        Path scratch = Path.of(StrictJson.text(roots.get("scratch"))).toRealPath();
        Path logs = Path.of(StrictJson.text(roots.get("logs"))).toRealPath();
        Path artifacts = Path.of(StrictJson.text(roots.get("artifacts"))).toRealPath();
        Path staging = Path.of(StrictJson.text(roots.get("source_staging"))).toRealPath();
        if ((!output.startsWith(logs) && !output.startsWith(staging)) || !fixtures.startsWith(scratch) || fixtures.equals(scratch)
                || Files.exists(output) || Files.exists(fixtures)) throw new IllegalArgumentException("fresh bounded fixture/output roots required");
        if (!"xar.stock3.compiled-consumer-packet/v1".equals(config.path("schema").asText())
                || !"QUALIFIED_COMPILED_INPUTS".equals(config.path("status").asText())) {
            throw new IllegalStateException("SOURCE_READY_UNCOMPILED: real qualified main jar/test classes and refs required");
        }
        if (!args[5].equals(config.path("machine_id").asText())) throw new IllegalArgumentException("packet machine mismatch");
        List<Ref> refs = new ArrayList<>(); refs.add(configRef);
        Ref mainJar = Ref.decode(config.get("main_jar")); refs.add(mainJar);
        Path testClasses = Path.of(config.path("test_classes").textValue()).toRealPath();
        if (!mainJar.path().startsWith(artifacts) || !mainJar.path().toString().endsWith(".jar")
                || !testClasses.startsWith(artifacts) || !Files.isDirectory(testClasses)) {
            throw new IllegalArgumentException("separate post-package jar and compiled test-class directory required");
        }
        Ref probeClass = Ref.decode(config.get("probe_class"));
        if (!probeClass.path().equals(testClasses.resolve("org/xar/ck3/control/wave2/military/stockconsumers/ProbeCompiledStockConsumers.class"))) {
            throw new IllegalArgumentException("exact compiled probe class pin required");
        }
        refs.add(probeClass);
        for (JsonNode ref : config.path("runtime_refs")) refs.add(Ref.decode(ref));
        if (!config.path("source_refs").isArray() || config.path("source_refs").size() < 16 || config.path("source_refs").size() > 64) {
            throw new IllegalArgumentException("complete original consumer source closure required");
        }
        for (JsonNode ref : config.path("source_refs")) refs.add(Ref.decode(ref));
        List<Ref> goldens = new ArrayList<>();
        for (String key : List.of("updater", "stock", "callback")) {
            Ref ref = Ref.decode(config.get("goldens").get(key)); refs.add(ref); goldens.add(ref);
        }
        if (refs.size() > 128) throw new IllegalArgumentException("finite qualified closure required");
        for (Ref ref : refs) {
            if (!ref.path().startsWith(artifacts) && !ref.path().startsWith(root) && !ref.path().startsWith(staging)
                    && !ref.path().startsWith(scratch) && !ref.path().startsWith(logs)) {
                throw new IllegalArgumentException("input escapes explicit machine profile roots");
            }
            ref.verify();
        }
        for (Class<?> producer : List.of(UpdaterWriteCodec.class, StockSupplyCodec.class, CallbackSupplyRiskCodec.class,
                CallbackSoldierEffectsCodec.class)) {
            Path origin = Path.of(producer.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
            if (!origin.equals(mainJar.path().toRealPath())) throw new IllegalStateException("actual producer did not load qualified main jar");
        }
        Path ownOrigin = Path.of(ProbeCompiledStockConsumers.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        if (!ownOrigin.equals(testClasses)) throw new IllegalStateException("probe did not load qualified test classes");
        ObjectNode initial = StrictJson.object(); initial.put("schema", "xar.stock3.compiled-consumer-input/v1");
        int index = 0;
        for (String key : List.of("updater", "stock", "callback")) {
            Ref ref = goldens.get(index++); byte[] raw;
            if (ref.path().toString().endsWith(".gz")) {
                try (InputStream gzip = new GZIPInputStream(Files.newInputStream(ref.path()))) { raw = gzip.readNBytes(131_073); }
            } else raw = Files.readAllBytes(ref.path());
            if (raw.length == 0 || raw.length > 131_072) throw new IOException("golden raw cap");
            JsonNode rawClaim = config.get("golden_raw").get(key);
            if (!rawClaim.isObject() || rawClaim.size() != 2 || !rawClaim.path("bytes").isIntegralNumber()
                    || !rawClaim.path("bytes").canConvertToInt() || rawClaim.path("bytes").intValue() != raw.length
                    || !rawClaim.path("sha256").isTextual() || !hash(raw).equals(rawClaim.path("sha256").textValue())) {
                throw new IOException("original raw golden length/SHA differs: " + key);
            }
            initial.set(key, StrictJson.parse(raw, 131_072));
        }
        Files.createDirectory(fixtures);
        Path errors = fixtures.resolve("python-consumer.stderr.log");
        ProcessBuilder builder = new ProcessBuilder(args[1], "-X", "utf8", "-B", "-c", PYTHON, root.toString(), fixtures.toString());
        builder.directory(root.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("TEMP", fixtures.toString()); builder.environment().put("TMP", fixtures.toString());
        builder.environment().remove("XAR_CURRENT_CALLBACK_SUPPLY_RISK_FIRST_OUTPUT");
        builder.environment().remove("XAR_CURRENT_CALLBACK_SOLDIER_EFFECTS_FIRST_OUTPUT");
        builder.redirectError(errors.toFile());
        Process child = builder.start();
        ObjectNode report = StrictJson.object(); report.put("schema", "xar.stock3.actual-java-original-consumer/v1");
        report.put("machine_id", args[5]); report.put("observed_at_utc", Instant.now().toString());
        report.set("compiled_input_packet", configRef.encode());
        report.set("qualified_main_jar", mainJar.encode()); report.put("qualified_test_classes", testClasses.toString());
        report.set("goldens", config.get("goldens")); var events = report.putArray("java_wire_events");
        JsonNode completion = null; int expected = 1;
        Set<Operation> retainedWireKinds = java.util.EnumSet.noneOf(Operation.class);
        try (OutputStream commands = child.getOutputStream(); InputStream responses = child.getInputStream()) {
            commands.write(StrictJson.canonical(initial, 524_288)); commands.write(10); commands.flush();
            for (;;) {
                byte[] line = readFrame(responses, FRAME_LIMIT);
                if (line == null) break;
                JsonNode candidate = StrictJson.parse(line, FRAME_LIMIT);
                if ("complete".equals(candidate.path("kind").asText())) { completion = candidate; break; }
                if (expected > 256) throw new IOException("finite Java consumer call cap");
                Message message = decodeMessage(line);
                if (message.sequence() != expected++) throw new IOException("consumer sequence drift");
                JsonNode value = dispatch(message); byte[] wire = StrictJson.canonical(value, FRAME_LIMIT);
                var event = events.addObject(); event.put("sequence", message.sequence()); event.put("operation", message.operation().name());
                event.put("request_sha256", hash(line)); event.put("actual_java_wire_bytes", wire.length); event.put("actual_java_wire_sha256", hash(wire));
                if (retainedWireKinds.add(message.operation())) event.put("actual_java_wire_json", new String(wire, StandardCharsets.UTF_8));
                if (message.operation() == Operation.UPDATER_REJECT) event.put("raw_input_json", message.rawJson());
                ObjectNode response = StrictJson.object(); response.put("sequence", message.sequence()); response.put("ok", true); response.set("value", value);
                commands.write(StrictJson.canonical(response, FRAME_LIMIT)); commands.write(10); commands.flush();
            }
        } finally {
            if (completion == null && child.isAlive()) child.destroyForcibly();
            if (!child.waitFor(15, TimeUnit.SECONDS)) {
                child.destroyForcibly(); child.waitFor();
                throw new IOException("consumer did not terminate");
            }
            for (Ref ref : refs) ref.verify();
        }
        if (Files.size(errors) > 65_536) throw new IOException("retained consumer stderr exceeds bounded budget");
        if (child.exitValue() != 0 || completion == null) {
            throw new IOException("actual original consumer closure RED; see retained stderr");
        }
        StrictJson.integer(completion.path("tests_run"), 2, 2);
        for (String field : List.of("skipped", "failures", "errors")) StrictJson.integer(completion.path(field), 0, 0);
        StrictJson.integer(completion.path("direct_ordered_updater_consumers"), 72, 72);
        StrictJson.integer(completion.path("callback_java_risk_to_original_effects_cases"), 8, 8);
        StrictJson.integer(completion.path("standalone_java_rate_cases"), 12, 12);
        StrictJson.integer(completion.path("original_registered_callback_scenes"), 5, 5);
        StrictJson.integer(completion.path("registered_stock").path("native_driver_queries"), 1, 1);
        StrictJson.integer(completion.path("registered_stock").path("registered_service_queries"), 1, 1);
        long counted = 0;
        for (Operation operation : Operation.values()) counted += StrictJson.integer(
                completion.path("actual_java_calls").path(operation.name()), 1, 256);
        if (counted != events.size()) throw new IOException("actual Java call counts differ from retained wire transcript");
        report.set("original_consumer_result", completion); report.put("status", "PASS"); report.put("python_exit_code", child.exitValue());
        report.put("all_qualified_inputs_pre_post_match", true);
        byte[] payload = StrictJson.canonical(report, OUTPUT_LIMIT);
        Files.write(output, payload, StandardOpenOption.CREATE_NEW);
    }

    private static String hash(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
}
