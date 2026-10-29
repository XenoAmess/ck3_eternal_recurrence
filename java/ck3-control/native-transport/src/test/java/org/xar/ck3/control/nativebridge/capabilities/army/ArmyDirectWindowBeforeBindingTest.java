package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Original before-bind parser parity only. No construction here issues a Core, dispatch permit or fixed-window Completion. */
final class ArmyDirectWindowBeforeBindingTest {
    @TempDir Path temporary;
    private static final Instant NOW = Instant.parse("2026-10-24T11:00:00Z");
    private static final String SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String SCRIPT = """
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/"ck3_autonomous_player/src"))
from xar_autoplayer.bridge.prewar_force_coalition_transport import _frame_binding
from xar_autoplayer.bridge.war_declared_overview_transport import _generation as overview_generation
from xar_autoplayer.bridge.war_results_window_transport import _generation as results_generation
result=[]
for frame in json.load(sys.stdin):
    errors=[]
    for generation in (overview_generation,results_generation):
        try:
            _frame_binding(frame);generation(frame);error=None
        except (ValueError,TypeError) as rejected: error=str(rejected)
        errors.append(error)
    result.append(errors)
print(json.dumps(result))
""";
    @Test void originalTwoNativeWindowBeforeBindParsersMatchTheSharedPreparationBoundary() throws Exception {
        Path repository = required("xar.repository.root"), python = required("xar.python");
        List<ObjectNode> cases = cases(); var request = StrictJson.object().arrayNode(); cases.forEach(request::add);
        Path out = temporary.resolve("window-bindings.stdout.json"), err = temporary.resolve("window-bindings.stderr.txt");
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-I", "-c", SCRIPT, repository.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.redirectOutput(out.toFile()); builder.redirectError(err.toFile());
        pin(repository); Process process = builder.start();
        try {
            try (var input = process.getOutputStream()) { input.write(DriverJson.encodeNode(request)); }
            assertTrue(process.waitFor(30, TimeUnit.SECONDS), "required original before-binding oracle timed out");
            assertEquals(0, process.exitValue(), Files.readString(err)); assertTrue(Files.size(out) < 65536 && Files.size(err) < 32768);
            JsonNode original = StrictJson.parse(Files.readAllBytes(out)); assertEquals(cases.size(), original.size());
            List<PublicMethod> methods = List.of(PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1, PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1);
            for (int i = 0; i < cases.size(); i++) for (int m = 0; m < methods.size(); m++) {
                ObjectNode frame = cases.get(i); String error = null;
                try { ArmyOrdinaryActionPreparation.requireDirectWindowBefore(methods.get(m), frame); }
                catch (IllegalArgumentException refused) { error = refused.getMessage(); }
                JsonNode expected = original.get(i).get(m);
                assertEquals(expected.isNull() ? null : expected.textValue(), error, "exact original before error case " + i + " " + methods.get(m) + " " + frame);
            }
        } finally { if (process.isAlive()) process.destroyForcibly(); pin(repository); }
    }
    @Test void directProducerRejectsMissingNullOrStaleExpectedRevisionBeforeAnyQueryOrSubmission() {
        ObjectNode frame = base(); var context = context(frame);
        for (ArmyTypes.Field<BigInteger> value : List.<ArmyTypes.Field<BigInteger>>of(new ArmyTypes.Missing<>(), new ArmyTypes.NullValue<>(), new ArmyTypes.Present<>(BigInteger.valueOf(9)))) {
            var call = new ArmyCalls.Frame(PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1, new ArmyCalls.Revision(value));
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionPreparation.requireDirectWindowSource(call, context, frame));
        }
    }
    @Test void originalExpectedTypePrecedesBeforeValidityAndBeforeValidityPrecedesStaleComparison() {
        ObjectNode invalidBefore = base(); invalidBefore.put("paused", false); var actualScope = context(base());
        for (PublicMethod method : List.of(PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1, PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1)) {
            String name = method == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1 ? "war overview" : "war results";
            var missing = new ArmyCalls.Frame(method, new ArmyCalls.Revision(new ArmyTypes.Missing<>()));
            assertEquals(name + " expected_revision is outside its native integer range", assertThrows(IllegalArgumentException.class,
                    () -> ArmyOrdinaryActionPreparation.requireDirectWindowSource(missing, actualScope, invalidBefore)).getMessage());
            var stale = new ArmyCalls.Frame(method, new ArmyCalls.Revision(new ArmyTypes.Present<>(BigInteger.valueOf(9))));
            assertEquals("prewar query requires a living paused native map", assertThrows(IllegalArgumentException.class,
                    () -> ArmyOrdinaryActionPreparation.requireDirectWindowSource(stale, actualScope, invalidBefore)).getMessage());
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionPreparation.requireDirectWindowSource(stale, actualScope, base()));
        }
    }
    private static ObjectNode base() {
        var frame = StrictJson.object().put("paused", true).put("map_ready", true).put("snapshot_id", "native:3")
                .put("revision", 10).put("native_revision", 3).put("date_raw", 100).put("episode_run_id", "original-episode");
        frame.putObject("played_character").put("character_id", 7).put("alive", true);
        frame.putObject("diagnostics").put("connection_generation", 0).putObject("hello")
                .put("expected_ck3_version", "1.20.0.4").put("expected_ck3_sha256", SHA).put("connection_generation", 1);
        return frame;
    }
    private static List<ObjectNode> cases() {
        List<ObjectNode> cases = new ArrayList<>(); cases.add(base());
        for (String path : List.of("revision", "native_revision", "date_raw", "played_character.character_id", "diagnostics.connection_generation", "diagnostics.hello.connection_generation")) {
            for (String token : List.of("true", "1.25", "\"1\"", "null", "-2147483649", "18446744073709551616")) {
                var frame = base(); put(frame, path, StrictJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8))); cases.add(frame);
            }
        }
        for (String path : List.of("revision", "native_revision", "played_character.character_id", "diagnostics.hello.connection_generation")) {
            var frame = base(); put(frame, path, StrictJson.object().numberNode(0)); cases.add(frame);
        }
        for (String path : List.of("revision", "native_revision", "diagnostics.connection_generation", "diagnostics.hello.connection_generation")) {
            var frame = base(); put(frame, path, StrictJson.object().numberNode(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE))); cases.add(frame);
        }
        for (int date : List.of(Integer.MIN_VALUE, -1, 0, Integer.MAX_VALUE)) { var frame = base(); frame.put("date_raw", date); cases.add(frame); }
        var maxActor = base(); ((ObjectNode) maxActor.get("played_character")).put("character_id", Integer.MAX_VALUE); cases.add(maxActor);
        var tooWideActor = base(); ((ObjectNode) tooWideActor.get("played_character")).put("character_id", 2147483648L); cases.add(tooWideActor);
        for (String flag : List.of("paused", "map_ready", "played_character.alive")) { var frame = base(); put(frame, flag, StrictJson.object().booleanNode(false)); cases.add(frame); }
        var wrongBuild = base(); put(wrongBuild, "diagnostics.hello.expected_ck3_version", StrictJson.object().textNode("1.20.0.3")); cases.add(wrongBuild);
        var wrongSha = base(); put(wrongSha, "diagnostics.hello.expected_ck3_sha256", StrictJson.object().textNode("0".repeat(64))); cases.add(wrongSha);
        var emptySnapshot = base(); emptySnapshot.put("snapshot_id", ""); cases.add(emptySnapshot);
        var nullEpisode = base(); nullEpisode.putNull("episode_run_id"); cases.add(nullEpisode);
        var noEpisode = base(); noEpisode.remove("episode_run_id"); cases.add(noEpisode);
        for (String path : List.of("revision", "native_revision", "date_raw", "played_character.character_id", "played_character.alive", "snapshot_id", "paused", "map_ready", "diagnostics.connection_generation", "diagnostics.hello.connection_generation", "diagnostics.hello.expected_ck3_version", "diagnostics.hello.expected_ck3_sha256")) {
            var frame = base(); String[] keys = path.split("\\."); ObjectNode parent = frame;
            for (int i = 0; i < keys.length - 1; i++) parent = (ObjectNode) parent.get(keys[i]); parent.remove(keys[keys.length - 1]); cases.add(frame);
        }
        var emptyEpisode = base(); emptyEpisode.put("episode_run_id", ""); cases.add(emptyEpisode);
        var wrongEpisode = base(); wrongEpisode.put("episode_run_id", true); cases.add(wrongEpisode);
        var noActor = base(); noActor.putNull("played_character"); cases.add(noActor);
        var noDiagnostics = base(); noDiagnostics.remove("diagnostics"); cases.add(noDiagnostics);
        var lowercaseSha = base(); put(lowercaseSha, "diagnostics.hello.expected_ck3_sha256", StrictJson.object().textNode(SHA.toLowerCase(java.util.Locale.ROOT))); cases.add(lowercaseSha);
        var originalOtherBuild = base(); put(originalOtherBuild, "diagnostics.hello.expected_ck3_version", StrictJson.object().textNode("1.19.0.6"));
        put(originalOtherBuild, "diagnostics.hello.expected_ck3_sha256", StrictJson.object().textNode("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86")); cases.add(originalOtherBuild);
        return List.copyOf(cases);
    }
    private static void put(ObjectNode frame, String path, JsonNode value) {
        String[] keys = path.split("\\."); ObjectNode current = frame;
        for (int i = 0; i < keys.length - 1; i++) current = (ObjectNode) current.get(keys[i]);
        current.set(keys[keys.length - 1], value);
    }
    private static BigInteger integer(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "actual before frame requires integer tokens"); return value.bigIntegerValue();
    }
    private static ArmyTypes.Context context(ObjectNode raw) {
        var ref = new ExactRef("D:/synthetic-no-authority/before.json", 1, "a".repeat(64));
        var source = new G2Source("synthetic-no-game", NOW.toString(), "1.20.0.4", ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(integer(raw.path("played_character").get("character_id")),
                integer(raw.get("native_revision")), integer(raw.get("date_raw"))), raw.path("snapshot_id").asText(), integer(raw.get("revision")),
                raw.hasNonNull("episode_run_id") ? raw.get("episode_run_id").textValue() : null);
        var identity = new ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        return new ArmyTypes.Context(identity, source, "original-session", NOW.plusSeconds(30));
    }
    private static Path required(String name) { String value = System.getProperty(name); assertNotNull(value, "required original parser input missing: " + name); Path path = Path.of(value); assertTrue(path.isAbsolute()); return path; }
    private static void pin(Path repository) throws Exception {
        var pins = java.util.Map.of("prewar_force_coalition_transport.py", "28ffe1bc6cd9f8042417e16c97bb7c76fe812d5d1386f9015909010eb7203299",
                "war_declared_overview_transport.py", "52183d4339e407bdbc29f9b222d28a7b80c5691a5b67e6ef158e9313a6f77b4c",
                "war_results_window_transport.py", "e1a3d7d5ae36ccf2a17055d166742f3fd49b11529bdbd383c7b2b9d5640fd86e",
                "version_identity.py", "9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086",
                "war_declared_overview_contract.py", "86ebfb0fc5ba6a0150f28c8ac4aeceb3c65116b03d0f5175a99fc9659377ece0",
                "war_results_window_contract.py", "3373fd42fc1cf8da88caf515061b4d8909816bf4ace66a6e01b25ac091a6cd66");
        for (var entry : pins.entrySet()) assertEquals(entry.getValue(), java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256")
                .digest(Files.readAllBytes(repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge").resolve(entry.getKey())))));
    }
}
