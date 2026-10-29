package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Calls unchanged original Python optional-root producer as a compatibility oracle, without creating a Python module. */
final class NativePlayerHeirOptional12004Test {
    @Test void originalNativeSevenFieldsUseActualReceiptFrameWithoutInventingServiceBinding() {
        ObjectNode root=root(); root.put("player_character_alive",true); root.putObject("readiness").put("same_frame_ready",true);
        root.set(COMPONENT,component());
        ObjectNode token=StrictJson.object().put("step","query-campaign-root-context-v1").put("accepted",true).put("status","available")
                .put("query_sequence",7).put("snapshot_revision",31).put("backend_id","native-headless"); token.set("campaign_root_context",root);
        Frame actual=new Frame("native-31",BigInteger.valueOf(900),BigInteger.valueOf(31),53144328,31254,0);
        assertEquals(State.LIVING_CANDIDATE,parseNativeResult(StrictJson.canonical(token),actual).state());
        assertThrows(IllegalArgumentException.class,()->parse(StrictJson.canonical(token),actual));
        token.putObject("binding").put("snapshot_id","manufactured");
        assertThrows(IllegalArgumentException.class,()->parseNativeResult(StrictJson.canonical(token),actual));
    }
    @Test void optionalSyntaxDoesNotAcquireStrictFrameOrSourceAuthority() {
        ObjectNode root = root(), component = component();
        ((ObjectNode) component.get("observation").get("before")).put("paused", false);
        assertEquals(OptionalStatus.PARSED, parseOptionalComponent(component, root).status());
        assertEquals(component, normalizeOptionalComponent(component, root));
        component.put("parent_frame_bound", false);
        assertEquals(OptionalStatus.UNKNOWN, parseOptionalComponent(component, root).status());
        assertNotNull(parseOptionalComponent(component, root).observation());
        assertEquals(component, normalizeOptionalComponent(component, root));
    }
    @Test void malformedOptionalValueIsLocalUnknownAndNeverAChangedRoot() {
        ObjectNode root = root(), original = root.deepCopy(), component = component();
        ((ObjectNode) component.get("observation")).put("candidate_character_id", true);
        JsonNode normalized = normalizeOptionalComponent(component, root);
        assertEquals("unknown", normalized.get("SDK_parse_status").textValue());
        assertEquals("malformed_native_candidate_observation", normalized.get("unavailable_reason").textValue());
        assertEquals(original, root);
        assertTrue(normalizeOptionalComponent(com.fasterxml.jackson.databind.node.NullNode.instance, root).isNull());
    }
    @Test void wholeOptionalProducerMatchesOriginalPythonForActualNullUnboundAndWrongTypeDomains() throws Exception {
        ArrayNode cases = StrictJson.object().putArray("cases");
        add(cases, root(), com.fasterxml.jackson.databind.node.NullNode.instance);
        add(cases, root(), component());
        ObjectNode c = component(); c.put("parent_frame_bound", false); add(cases, root(), c);
        ObjectNode r = root(); r.put("status", "unavailable"); add(cases, r, component());
        for (String token : List.of("true", "31.0", "\"31\"")) {
            c = component(); c.set("snapshot_revision", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8))); add(cases, root(), c);
        }
        c = component(); c.put("getter_rva", "0x28C17E0"); add(cases, root(), c);
        c = component(); ((ObjectNode)c.get("observation")).put("candidate_character_id", true); add(cases, root(), c);
        c = component(); ((ObjectNode)c.get("observation")).remove("getter_observed"); add(cases, root(), c);
        c = component(); ((ObjectNode)c.get("observation").get("candidate_lineage")).put("dynasty_id", 174.0); add(cases, root(), c);
        c = component(); ((ObjectNode)c.get("observation").get("before")).put("date_raw", 53144328.0); add(cases, root(), c);
        c = component(); ((ObjectNode)c.get("observation").get("before")).put("paused", false); add(cases, root(), c);
        c = component(); ((ObjectNode)c.get("observation").get("after")).put("local_player_id", -1); add(cases, root(), c);
        c = component(); ((ObjectNode)c.get("observation")).put("unavailable_reason", "\uD83D\uDD25".repeat(1000)); add(cases, root(), c);
        c = component(); c.put("unexpected", true); add(cases, root(), c);
        JsonNode expected = original(cases); assertEquals(cases.size(), expected.size());
        for (int index = 0; index < cases.size(); index++)
            assertArrayEquals(StrictJson.canonical(expected.get(index), MAX_BYTES),
                    StrictJson.canonical(normalizeOptionalComponent(cases.get(index).get("component"), cases.get(index).get("root")), MAX_BYTES), "original case " + index);
    }
    private static ObjectNode root() {
        ObjectNode root = StrictJson.object().put("status", "available").put("snapshot_revision", 31).put("date_raw", 53144328)
                .put("local_player_id", 0).put("player_character_id", 31254);
        root.putObject("provenance").put("executable_sha256", EXE_SHA256); return root;
    }
    private static ObjectNode component() {
        Core core = new Core(53144328, true, 3, 0, true, true, 31254, true);
        Component component = new Component(BigInteger.valueOf(31), true, new Observation(true, null, false, true,
                core, core, true, true, 31254, -2147483647, true, true, true, new Lineage(-2147483646, 174), null));
        return (ObjectNode) StrictJson.parse(encodeComponent(component), MAX_BYTES);
    }
    private static void add(ArrayNode cases, JsonNode root, JsonNode component) {
        ObjectNode row = cases.addObject(); row.set("root", root); row.set("component", component);
    }
    static JsonNode originalProjection(ArrayNode input) throws Exception { return original(input, "projection"); }
    private static JsonNode original(ArrayNode input) throws Exception { return original(input, "optional"); }
    private static JsonNode original(ArrayNode input, String operation) throws Exception {
        Path repository = Path.of(required("xar.repository.root")).toRealPath();
        Path python = Path.of(required("xar.native.producer.python")).toRealPath();
        verify(repository);
        String script = """
                import sys,json,pathlib
                sys.dont_write_bytecode=True
                root=pathlib.Path(sys.argv[1])
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
                from dataclasses import asdict
                from xar_autoplayer.bridge.player_heir_candidate_component_v1 import parse_optional_player_heir_component_v1
                import xar_autoplayer.player_heir_fixed_dynasty_projection_v1 as p
                rows=json.load(sys.stdin)
                result=[]
                for row in rows:
                  if sys.argv[2]=='optional':
                    component=row['component']
                    parsed=parse_optional_player_heir_component_v1(component,root=row['root'])
                    result.append(component if parsed.observation is not None or component is None else
                      {'SDK_parse_status':'unknown','unavailable_reason':parsed.reason})
                  else:
                    anchor=p.FixedDynastyAnchorV1(**row['anchor'])
                    binding=p.CandidateQueryBindingV1(**row['binding']) if row['binding'] is not None else None
                    core=p.CandidateCoreFrameV1(**row['core']) if row['core'] is not None else None
                    captured=row['captured']
                    if captured is not None:
                      raw=captured['observation']
                      if raw is not None:
                        raw={**raw,'before':p.CandidateCoreFrameV1(**raw['before']),'after':p.CandidateCoreFrameV1(**raw['after']),
                          'candidate_lineage':p.CandidateLineageV1(**raw['candidate_lineage'])}
                        raw=p.NativePlayerHeirCandidateV1(**raw)
                      captured=p.BoundPlayerHeirCandidateV1(p.CandidateQueryBindingV1(**captured['binding']),raw,
                        captured['source_kind'],captured['getter_source_closure_sha256'])
                    result.append(asdict(p.project_fixed_dynasty_candidate_v1(anchor=anchor,captured=captured,current=binding,current_core=core)))
                print(json.dumps(result,ensure_ascii=False,allow_nan=False))
                """;
        Process child = new ProcessBuilder(python.toString(), "-X", "utf8", "-I", "-B", "-c", script, repository.toString(), operation).start();
        FutureTask<byte[]> stdout = new FutureTask<>(() -> child.getInputStream().readNBytes(MAX_BYTES + 1));
        FutureTask<byte[]> stderr = new FutureTask<>(() -> child.getErrorStream().readNBytes(16385));
        Thread.ofVirtual().start(stdout); Thread.ofVirtual().start(stderr);
        try {
            try (var request = child.getOutputStream()) { request.write(originalInput(input)); }
            assertTrue(child.waitFor(30, TimeUnit.SECONDS), "original optional producer timed out");
            byte[] output = stdout.get(5, TimeUnit.SECONDS), errors = stderr.get(5, TimeUnit.SECONDS);
            assertTrue(output.length <= MAX_BYTES && errors.length <= 16384, "bounded original output required");
            assertEquals(0, child.exitValue(), () -> new String(errors, StandardCharsets.UTF_8));
            verify(repository); return StrictJson.parse(output, MAX_BYTES);
        } finally { if (child.isAlive()) { child.destroyForcibly(); child.waitFor(5, TimeUnit.SECONDS); } }
    }
    private static void verify(Path root) throws Exception {
        for (var pin : List.of(
                new Source("ck3_autonomous_player/src/xar_autoplayer/bridge/player_heir_candidate_component_v1.py", "69977b160964c526187e3ae4612d2da670e6af5e6f76acc5fb2ccdfd4570342a"),
                new Source("ck3_autonomous_player/src/xar_autoplayer/player_heir_fixed_dynasty_projection_v1.py", "1ca02c48f94503ef05a4d3f0d2d3045d8eb83670c55fd6ac7952a321ac3f735e"))) {
            Path source = root.resolve(pin.path()).toRealPath(); assertTrue(source.startsWith(root) && Files.size(source) <= MAX_BYTES);
            assertEquals(pin.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source))));
        }
    }
    private record Source(String path, String sha256) { }
    /** Test transport preserves float tokens even after the production parser strips decimal zeroes. */
    private static byte[] originalInput(ArrayNode input) throws java.io.IOException {
        var bytes = new java.io.ByteArrayOutputStream();
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        try (var generator = new com.fasterxml.jackson.core.util.JsonGeneratorDelegate(mapper.getFactory().createGenerator(bytes)) {
            @Override public void writeNumber(java.math.BigDecimal value) throws java.io.IOException {
                String token = value.toString();
                super.writeNumber(token.indexOf('.') < 0 && token.indexOf('E') < 0 ? token + ".0" : token);
            }
        }) { mapper.writeTree(generator, input); }
        byte[] encoded = bytes.toByteArray();
        assertTrue(encoded.length > 0 && encoded.length <= StrictJson.EXPLICIT_MAX_BYTES, "bounded original producer input required");
        return encoded;
    }
    private static String required(String name) {
        String value = System.getProperty(name); assertTrue(value != null && !value.isBlank(), "NOT EXECUTED: required property missing " + name); return value;
    }
}
