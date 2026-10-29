package org.xar.ck3.control.wave2.military.commander;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.HashSet;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.combatroles.CombatWholeWire;
import org.xar.ck3.control.wave2.military.holyhirecontract.HolyHireCodec;
import org.xar.ck3.control.wave2.military.holyreinf.HolyReinforcementCodec;

/** Post-package actual Java bytes to the existing original commander/holy consumers. No Game or submits. */
public final class ProbeCompiledObservedMilitaryConsumers {
    private static final int PACKET_MAX = 1_048_576;
    private ProbeCompiledObservedMilitaryConsumers() { }
    public enum Family { COMMANDER, HOLY_HIRE, HOLY_REINFORCEMENT }
    public record Golden(Family family, CombatWholeWire.FileReference reference) { }
    public record Qualification(Path taskRoot, Path logsRoot, Path scratchRoot, Path repository, Path python,
            CombatWholeWire.FileReference mainJar, Path testClasses,
            List<CombatWholeWire.FileReference> classFiles, List<Golden> goldens, Path output) {
        public Qualification { classFiles = List.copyOf(classFiles); goldens = List.copyOf(goldens); }
    }

    public static void main(String[] args) throws IOException, URISyntaxException, InterruptedException {
        if (args.length != 1) throw new IllegalArgumentException("one actual compiled artifact/source qualification required");
        Qualification q = decode(StrictJson.parse(readBounded(Path.of(args[0]), 65536)));
        verify(q);
        byte[] mainBefore = CombatWholeWire.readPinned(q.mainJar(), q.taskRoot());
        ObjectNode packet = StrictJson.object().put("schema", "xar.compiled-observed-military-consumers/v1")
                .put("main_jar_sha256", q.mainJar().sha256()).put("game_operations", 0);
        ArrayNode rows = packet.putArray("cases");
        for (Golden source : q.goldens()) {
            byte[] original = CombatWholeWire.readPinned(source.reference(), q.taskRoot());
            JsonNode golden;
            if (source.family() == Family.COMMANDER) golden = StrictJson.parse(original, 131072);
            else try (var gzip = new GZIPInputStream(new java.io.ByteArrayInputStream(original))) {
                golden = StrictJson.parse(gzip.readNBytes(262145), 262144);
            }
            String expectedSchema = switch (source.family()) {
                case COMMANDER -> "xar.java.commander-quality-golden.v1";
                case HOLY_HIRE -> "xar.ck3.holy-hire-contract-golden.v1";
                case HOLY_REINFORCEMENT -> "xar.ck3.holy-reinforcement-golden.v1";
            };
            if (!expectedSchema.equals(golden.path("schema").textValue()) || !golden.path("cases").isArray()) {
                throw new IllegalArgumentException("exact original family golden schema required");
            }
            if (source.family() == Family.COMMANDER) {
                for (JsonNode sample : golden.path("cases")) append(rows, "commander_proposal", sample, true);
                for (JsonNode sample : golden.path("plans")) append(rows, "commander_plan", sample, true);
            } else {
                for (JsonNode sample : golden.path("cases")) {
                    if (source.family() == Family.HOLY_HIRE && !sample.path("accepted").isBoolean()) {
                        throw new IllegalArgumentException("actual original acceptance boolean required");
                    }
                    String operation = source.family() == Family.HOLY_HIRE ? "hire_" + sample.path("operation").textValue()
                            : "reinforcement_" + sample.path("operation").textValue();
                    append(rows, operation, sample, source.family() == Family.HOLY_REINFORCEMENT || sample.path("accepted").booleanValue());
                }
            }
        }
        byte[] wire = packet.toString().getBytes(StandardCharsets.UTF_8);
        if (wire.length > PACKET_MAX || rows.size() < 80) throw new IllegalArgumentException("complete finite original consumer matrix required");
        Path packetPath = q.output().resolveSibling(q.output().getFileName() + ".java-wire-packet.json");
        if (Files.exists(packetPath) || Files.exists(q.output())) throw new IllegalArgumentException("fresh probe outputs required");
        Files.write(packetPath, wire, StandardOpenOption.CREATE_NEW);
        ProcessBuilder process = new ProcessBuilder(List.of(q.python().toString(), "-B", "-X", "utf8", "-c", SCRIPT,
                packetPath.toString(), q.output().toString(), q.repository().toString()));
        process.directory(q.repository().toFile()).inheritIO();
        process.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        process.environment().put("PYTHONPATH", q.repository().resolve("ck3_autonomous_player/src")
                + java.io.File.pathSeparator + q.repository().resolve("ck3_autonomous_player/tests/unit"));
        Process child = process.start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
            throw new IllegalStateException("original consumer probe timeout; shared Job owns remaining descendants");
        }
        if (child.exitValue() != 0 || !Files.isRegularFile(q.output()) || Files.size(q.output()) > 32768) {
            throw new IllegalStateException("original consumer probe failed or exceeded its report budget");
        }
        if (!java.util.Arrays.equals(mainBefore, CombatWholeWire.readPinned(q.mainJar(), q.taskRoot()))
                || !CombatWholeWire.sha256(wire).equals(CombatWholeWire.sha256(readBounded(packetPath, PACKET_MAX)))) {
            throw new IllegalStateException("actual compiled producer or wire packet changed during original consumption");
        }
        verify(q);
    }

    private static void append(ArrayNode rows, String operation, JsonNode sample, boolean accepted) {
        if (!Set.of("commander_proposal","commander_plan","hire_request","hire_ack","hire_query",
                "reinforcement_choose","reinforcement_plan","reinforcement_post").contains(operation)
                || !sample.path("name").isTextual() || sample.path("name").textValue().isBlank()
                || !sample.path("input").isObject()) {
            throw new IllegalArgumentException("known complete original consumer case required");
        }
        JsonNode input = sample.get("input");
        byte[] request = input.toString().getBytes(StandardCharsets.UTF_8);
        ObjectNode row = rows.addObject().put("name", sample.path("name").textValue()).put("operation", operation)
                .put("input_json", new String(request, StandardCharsets.UTF_8)).put("accepted", accepted);
        if (!accepted) {
            try { execute(operation, request); throw new IllegalStateException("compiled codec accepted original rejection " + sample.path("name").textValue()); }
            catch (IllegalArgumentException expected) { row.put("compiled_rejection", expected.getClass().getName()); }
            return;
        }
        byte[] actual = execute(operation, request);
        JsonNode expected = sample.get("expected");
        if (!StrictJson.parse(actual, PACKET_MAX).equals(expected)) {
            throw new IllegalStateException("compiled result differs from original captured JSON domain: " + operation + "/" + sample.path("name").textValue());
        }
        row.put("actual_json", new String(actual, StandardCharsets.UTF_8));
        if (operation.equals("commander_plan")) {
            ArrayNode queries = row.putArray("java_query_replies");
            for (JsonNode query : input.get("queries")) {
                ObjectNode reply = queries.addObject().put("army_id", query.get("army_id").intValue());
                if (query.get("proposal_input").isNull()) reply.putNull("proposal_json");
                else reply.put("proposal_json", new String(CommanderQualityCodec.propose(
                        query.get("proposal_input").toString().getBytes(StandardCharsets.UTF_8)), StandardCharsets.UTF_8));
            }
        }
        if (operation.equals("reinforcement_post")) {
            ObjectNode choose = StrictJson.object().put("schema", "xar.ck3.holy-reinforcement-choose-input.v1");
            choose.set("snapshot", input.get("before_snapshot")); choose.set("plan", input.get("plan")); choose.set("holy_context", input.get("before_context"));
            row.put("java_proposal_json", new String(HolyReinforcementCodec.choose(StrictJson.canonical(choose, 131072)), StandardCharsets.UTF_8));
        }
    }
    static byte[] execute(String operation, byte[] raw) {
        return switch (operation) {
            case "commander_proposal" -> CommanderQualityCodec.propose(raw);
            case "commander_plan" -> CommanderQualityCodec.plan(raw);
            case "hire_ack" -> HolyHireCodec.acknowledge(raw);
            case "hire_query" -> HolyHireCodec.query(raw);
            case "hire_request" -> {
                var request = HolyHireCodec.request(raw);
                yield StrictJson.canonical(StrictJson.object().put("holy_order_id", request.holyOrderId())
                        .put("expected_revision", request.expectedRevision()), 131072);
            }
            case "reinforcement_choose" -> HolyReinforcementCodec.choose(raw);
            case "reinforcement_plan" -> HolyReinforcementCodec.plan(raw);
            case "reinforcement_post" -> HolyReinforcementCodec.postcondition(raw);
            default -> throw new IllegalArgumentException("unsupported existing observed-consumer operation");
        };
    }
    private static void verify(Qualification q) throws IOException, URISyntaxException {
        if (!origin(CommanderQualityCodec.class).equals(q.mainJar().path())
                || !origin(HolyHireCodec.class).equals(q.mainJar().path())
                || !origin(HolyReinforcementCodec.class).equals(q.mainJar().path())
                || !origin(ProbeCompiledObservedMilitaryConsumers.class).equals(q.testClasses())
                || !origin(CombatWholeWire.class).equals(q.testClasses())) {
            throw new IllegalStateException("compiled classes loaded from an unqualified jar/test directory");
        }
        if (!q.logsRoot().startsWith(q.taskRoot()) || !q.scratchRoot().startsWith(q.taskRoot())
                || !q.output().startsWith(q.logsRoot()) || !q.mainJar().path().toString().endsWith(".jar")
                || q.classFiles().isEmpty() || q.goldens().size() != 3) {
            throw new IllegalArgumentException("explicit finite task paths and all original golden families required");
        }
        Set<Family> families = new HashSet<>(); Set<String> classes = new HashSet<>();
        for (Golden golden : q.goldens()) {
            if (!families.add(golden.family())) throw new IllegalArgumentException("duplicate original family");
            CombatWholeWire.readPinned(golden.reference(), q.taskRoot());
        }
        for (var ref : q.classFiles()) {
            if (!ref.path().startsWith(q.testClasses()) || !ref.path().toString().endsWith(".class")) throw new IllegalArgumentException("qualified compiled test path required");
            CombatWholeWire.readPinned(ref, q.taskRoot()); classes.add(q.testClasses().relativize(ref.path()).toString().replace('\\', '/'));
        }
        if (!classes.contains("org/xar/ck3/control/wave2/military/commander/ProbeCompiledObservedMilitaryConsumers.class")
                || !classes.contains("org/xar/ck3/control/wave2/military/combatroles/CombatWholeWire.class")) {
            throw new IllegalArgumentException("actual compiled probe dependencies omitted");
        }
        for (String packageName : List.of("commander", "combatroles")) {
            Path packageRoot = q.testClasses().resolve("org/xar/ck3/control/wave2/military/" + packageName);
            try (var files = Files.list(packageRoot)) {
                for (Path file : files.filter(p -> Files.isRegularFile(p, java.nio.file.LinkOption.NOFOLLOW_LINKS)).toList()) {
                    String name = file.getFileName().toString();
                    if (name.endsWith(".class") && (name.startsWith("ProbeCompiledObservedMilitaryConsumers$")
                            || name.startsWith("CombatWholeWire$"))
                            && !classes.contains(q.testClasses().relativize(file).toString().replace('\\','/'))) {
                        throw new IllegalArgumentException("nested actual compiled probe dependency omitted");
                    }
                }
            }
        }
    }
    private static Qualification decode(JsonNode value) throws IOException {
        if (!value.isObject()) throw new IllegalArgumentException("actual qualification object required");
        Set<String> fields = new HashSet<>(); value.fieldNames().forEachRemaining(fields::add);
        if (!fields.equals(Set.of("schema","task_root","logs_root","scratch_root","repository","python","main_jar",
                "test_classes","class_files","goldens","output"))
                || !"xar.compiled-observed-military-input/v1".equals(value.path("schema").textValue())) throw new IllegalArgumentException("exact qualification fields required");
        List<CombatWholeWire.FileReference> classes = new ArrayList<>();
        if (!value.path("class_files").isArray() || !value.path("goldens").isArray()) throw new IllegalArgumentException("actual class/golden manifests required");
        for (JsonNode ref : value.get("class_files")) classes.add(ref(ref));
        List<Golden> goldens = new ArrayList<>();
        for (JsonNode golden : value.get("goldens")) {
            Set<String> keys = new HashSet<>(); golden.fieldNames().forEachRemaining(keys::add);
            if (!keys.equals(Set.of("family","reference"))) throw new IllegalArgumentException("exact original family reference required");
            goldens.add(new Golden(Family.valueOf(golden.path("family").textValue()), ref(golden.get("reference"))));
        }
        return new Qualification(path(value,"task_root"),path(value,"logs_root"),path(value,"scratch_root"),path(value,"repository"),path(value,"python"),
                ref(value.get("main_jar")),path(value,"test_classes"),classes,goldens,path(value,"output"));
    }
    private static Path path(JsonNode value, String field) {
        if (!value.path(field).isTextual()) throw new IllegalArgumentException("actual path required");
        Path result = Path.of(value.get(field).textValue());
        if (!result.isAbsolute() || !result.normalize().equals(result)) throw new IllegalArgumentException("normalized absolute path required"); return result;
    }
    private static CombatWholeWire.FileReference ref(JsonNode value) throws IOException { return CombatWholeWire.reference(value.toString().getBytes(StandardCharsets.UTF_8)); }
    private static Path origin(Class<?> type) throws URISyntaxException { return Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize(); }
    private static byte[] readBounded(Path path, int maximum) throws IOException { try (var stream = Files.newInputStream(path)) { byte[] raw = stream.readNBytes(maximum+1); if(raw.length>maximum)throw new IllegalArgumentException("finite actual input required");return raw; } }

    private static final String SCRIPT = """
            import sys,json,hashlib,copy
            from pathlib import Path
            packet_path=Path(sys.argv[1]); output=Path(sys.argv[2]); root=Path(sys.argv[3])
            packet=json.loads(packet_path.read_bytes())
            if packet['schema']!='xar.compiled-observed-military-consumers/v1' or output.exists():raise ValueError('actual packet/fresh output required')
            from xar_autoplayer import commander_quality_formal_proposal_v1 as commander
            from xar_autoplayer import commander_quality_formal_consumer_v1 as formal
            from xar_autoplayer import holy_order_siege_reinforcement_v1 as holy
            from xar_autoplayer.bridge.driver import BridgeUnavailableError
            from xar_autoplayer.bridge.hire_holy_order import validate_hire_holy_order_request_v1,normalize_hire_holy_order_v1
            from xar_autoplayer.bridge.player_holy_order_context_private_transport import query_player_holy_order_context_private_v1
            from xar_autoplayer.bridge.army_commander_candidates import normalize_army_commander_candidates_v1
            receipts=[]
            for row in packet['cases']:
                x=json.loads(row['input_json']); op=row['operation']; actual=json.loads(row['actual_json']) if row['accepted'] else None
                def consume():
                    if op=='commander_proposal':
                        c=normalize_army_commander_candidates_v1(x['candidates'],expected_army_id=x['candidates']['army_id'],
                            expected_snapshot_revision=x['snapshot']['native_revision'],expected_date_raw=x['snapshot']['date_raw'])
                        return commander.propose_commander_quality_v1(c,snapshot=x['snapshot'],query_sequence=x['query_sequence'])
                    if op=='commander_plan':
                        replies=row['java_query_replies']
                        class Port:
                            def __init__(self):self.calls=[]
                            def query_army_commander_candidates_v1(self,army_id,*,expected_revision=None):
                                index=len(self.calls); self.calls.append(army_id); q=x['queries'][index]
                                if q['army_id']!=army_id or expected_revision!=x['snapshot']['revision']:raise ValueError('actual formal query order/binding')
                                if q['proposal_input'] is None:raise BridgeUnavailableError(q['unavailable_reason'])
                                return {'commander_quality_proposal':json.loads(replies[index]['proposal_json'])}
                        port=Port(); return formal.plan_commander_quality_formal_v1(port,planned=x['planned'],snapshot=x['snapshot'],bridge_capabilities=x['bridge_capabilities'])
                    if op=='hire_request':
                        value=actual if actual is not None else x
                        validate_hire_holy_order_request_v1(value['holy_order_id'],value['expected_revision'])
                        return {'holy_order_id':value['holy_order_id'],'expected_revision':value['expected_revision']}
                    if op=='hire_ack':
                        value=actual if actual is not None else x['ack']
                        return normalize_hire_holy_order_v1(value,snapshot=x['snapshot'],expected_holy_order_id=x['expected_holy_order_id'])
                    if op=='hire_query':
                        class Reader:
                            allow_private_player_religion_context_query=True
                            def __init__(self):self.endpoint=self;self.state=self;self.count=0;self.request=None
                            def take_snapshot(self):
                                value=x['before_snapshot'] if self.count==0 else x['after_snapshot'];self.count+=1;return copy.deepcopy(value)
                            def send(self,request):self.request=request
                            def wait_for_command_result(self,request_id,timeout):
                                p=copy.deepcopy(x['packet']);p['request_id']=request_id
                                if actual is not None:p['result']['player_holy_order_context']=copy.deepcopy(actual)
                                return p
                        return query_player_holy_order_context_private_v1(Reader(),expected_revision=x['expected_revision'])
                    if op=='reinforcement_choose':return holy.choose_holy_order_siege_reinforcement_v1(snapshot=x['snapshot'],plan=x['plan'],holy_context=x['holy_context'])
                    if op=='reinforcement_plan':
                        class Reader:
                            def query_player_holy_order_context_private_v1(self,**kw):
                                if x['query_error'] is not None:raise BridgeUnavailableError(x['query_error'])
                                return copy.deepcopy(x['holy_context'])
                        driver=Reader() if x['query_available'] else object()
                        return holy.plan_holy_order_siege_reinforcement_v1(driver,planned=x['planned'],snapshot=x['snapshot'],bridge_capabilities=x['bridge_capabilities'])
                    if op=='reinforcement_post':
                        class Reader:
                            def hire_holy_order_v1(self,**kw):return copy.deepcopy(x['ack'])
                            def take_snapshot(self):
                                if x['post_query_error'] is not None:raise BridgeUnavailableError(x['post_query_error'])
                                return copy.deepcopy(x['after_snapshot'])
                            def query_player_holy_order_context_private_v1(self,**kw):return copy.deepcopy(x['after_context'])
                            def query_army_strengths(self,**kw):return copy.deepcopy(x['army_strengths'])
                            def query_war_cash_current_resources_private_v1(self,**kw):
                                if x['expense_query_error'] is not None:raise BridgeUnavailableError(x['expense_query_error'])
                                return copy.deepcopy(x['actor_expenses'])
                        return holy.submit_holy_order_siege_reinforcement_v1(Reader(),plan={'holy_order_hire_proposal':json.loads(row['java_proposal_json'])},expected_revision=x['before_snapshot']['revision'])
                    raise ValueError('unknown captured operation')
                try: expected=consume()
                except (ValueError,BridgeUnavailableError):
                    if row['accepted']:raise
                    receipts.append({'name':row['name'],'operation':op,'actual_original_rejection':True});continue
                if not row['accepted'] or expected!=actual:raise ValueError('actual compiled Java bytes differ in original consumer '+op+'/'+row['name'])
                receipts.append({'name':row['name'],'operation':op,'actual_original_consumer':True,
                    'java_wire_sha256':hashlib.sha256(row['actual_json'].encode()).hexdigest()})
            result={'schema':'xar.compiled-observed-military-consumers-actual/v1','status':'PASS','cases':receipts,
                'actual_java_wire_packet_sha256':hashlib.sha256(packet_path.read_bytes()).hexdigest(),
                'game_operations':0,'synthetic_transport_only':True,'assignment_or_hire_execution_credit':False}
            raw=(json.dumps(result,sort_keys=True,separators=(',',':'))+'\\n').encode()
            if len(raw)>32768:raise ValueError('finite consumer report cap')
            with output.open('xb') as f:f.write(raw)
            print(json.dumps({'cases':len(receipts),'bytes':len(raw),'status':'PASS'}))
            """;
}
