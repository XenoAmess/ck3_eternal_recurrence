package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Actual publisher rejects metadata-only inputs; positive native output qualification belongs to Root. */
final class NativeFixtureCorporaTest {
    @TempDir Path temporary;
    @Test void closedPublicationRequestsRoundtripAndRejectUnknownMissingOrRepeatedNativeTargets() throws Exception {
        var request = request(); var mapper = ControlBuild.strictMapper();
        assertEquals(request, mapper.readValue(mapper.writeValueAsBytes(request), NativeFixtureCorpora.Request.class));
        var json = mapper.valueToTree(request); ((com.fasterxml.jackson.databind.node.ObjectNode)json).put("kind", 1);
        assertThrows(IOException.class, () -> mapper.treeToValue(json, NativeFixtureCorpora.Request.class));
        assertThrows(IllegalArgumentException.class, () -> new NativeFixtureCorpora.Request(request.schema(), request.machineId(), request.kind(), request.sourceMapRef(), request.nativeEnvironmentRef(), request.nativeSourceSnapshotRef(), List.of()));
        var duplicate = new ArrayList<>(request.runs()); duplicate.set(4, duplicate.getFirst());
        assertThrows(IllegalArgumentException.class, () -> new NativeFixtureCorpora.Request(request.schema(), request.machineId(), request.kind(), request.sourceMapRef(), request.nativeEnvironmentRef(), request.nativeSourceSnapshotRef(), duplicate));
        var bad = mapper.valueToTree(request); ((com.fasterxml.jackson.databind.node.ObjectNode)bad.get("runs").get(0).get("source_ref")).put("bytes", true);
        assertThrows(IOException.class, () -> mapper.treeToValue(bad, NativeFixtureCorpora.Request.class));
    }
    @Test void sourceBoundMetadataWithoutRealOwnedTerminalCannotPublishAnyCorpusOrSuccessProof() throws Exception {
        var request = request(); Path input = temporary.resolve("request.json"); Files.write(input, ControlBuild.strictMapper().writeValueAsBytes(request)); Path output = temporary.resolve("must-not-exist.json");
        assertThrows(IOException.class, () -> NativeFixtureCorpora.produce(ControlBuild.FileRef.measure(input), output));
        assertFalse(Files.exists(output)); assertFalse(Files.exists(NativeFixtureCorpora.proofPath(output)));
    }
    @Test void actualC16TerminalReservationAcceptsOnlyItsSettledChildJob() throws Exception {
        var terminal = originalTerminal(); var command = originalRequest();
        assertFalse(terminal.outer().hardJobEnforced());
        assertEquals(268435456L, terminal.outer().reservedMemoryBytes());
        assertEquals(0, terminal.child().accounting().activeProcesses());
        assertDoesNotThrow(() -> NativeFixtureCorpora.requireSettledOwnedProcess(terminal.machineId(), terminal, command));
        // This exact original v2 shape was rejected by the old outer.hardJobEnforced predicate.
    }
    @Test void reservationCannotReplaceRealChildJobOrCrossOriginalRequest() throws Exception {
        var mapper = ControlBuild.strictMapper(); var original = originalTerminal(); var command = originalRequest();
        var outer = mapper.valueToTree(original);
        ((com.fasterxml.jackson.databind.node.ObjectNode)outer.get("outer")).put("hard_job_enforced", true);
        var fakeOuter = mapper.treeToValue(outer, SharedOwnedCommand.Terminal.class);
        assertThrows(IllegalArgumentException.class, () -> NativeFixtureCorpora.requireSettledOwnedProcess(original.machineId(), fakeOuter, command));
        for (String field : List.of("active_processes", "limit_flags", "memory_limit_bytes")) {
            var node = mapper.valueToTree(original); var accounting = (com.fasterxml.jackson.databind.node.ObjectNode)node.get("child").get("accounting");
            if (field.equals("active_processes")) accounting.put(field, 1);
            else if (field.equals("limit_flags")) accounting.put(field, 0);
            else accounting.put(field, command.memoryLimitBytes() + 4096L);
            var changed = mapper.treeToValue(node, SharedOwnedCommand.Terminal.class);
            assertThrows(IllegalArgumentException.class, () -> NativeFixtureCorpora.requireSettledOwnedProcess(original.machineId(), changed, command), field);
        }
        var crossed = mapper.valueToTree(original); ((com.fasterxml.jackson.databind.node.ObjectNode)crossed).put("slot_id", "another-slot");
        var changed = mapper.treeToValue(crossed, SharedOwnedCommand.Terminal.class);
        assertThrows(IllegalArgumentException.class, () -> NativeFixtureCorpora.requireSettledOwnedProcess(original.machineId(), changed, command));
        var wrongInteger = mapper.valueToTree(original); ((com.fasterxml.jackson.databind.node.ObjectNode)wrongInteger.get("child").get("accounting")).put("active_processes", false);
        assertThrows(IOException.class, () -> mapper.treeToValue(wrongInteger, SharedOwnedCommand.Terminal.class));
    }
    private SharedOwnedCommand.Terminal originalTerminal() throws Exception {
        byte[] raw = resource("actual-owned-command-terminal-v2.json");
        assertEquals("6b585e703816a12005a146ecf00ecaf07fc388922b938cd297a39dd51acad7f7", java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw)));
        return ControlBuild.strictMapper().readValue(raw, SharedOwnedCommand.Terminal.class);
    }
    private SharedOwnedCommand.Request originalRequest() throws Exception {
        byte[] raw = resource("actual-owned-command-request-v2.json");
        assertEquals("2b095825ed044c50704a4677e2c7c00e8815023621b1fa2aeb981cb666b5bef3", java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw)));
        return SharedOwnedCommand.parseRequest(ControlBuild.strictMapper().readTree(raw));
    }
    private byte[] resource(String name) throws IOException {
        try (var stream = NativeFixtureCorporaTest.class.getResourceAsStream("/nativefixture/" + name)) {
            if (stream == null) throw new IOException("Original v2 owned-command regression resource absent: " + name);
            return stream.readAllBytes();
        }
    }
    private NativeFixtureCorpora.Request request() throws Exception {
        var source = pin("original.cpp", "controlled source fixture"); var executable = pin("producer.exe", "never executed"); var terminal = pin("terminal.json", "{}");
        var output = pin("wire.json", "{\"samples\":{}}"); var environment = pin("environment.json", "{}"); var snapshot = pin("snapshot.json", "{}");
        var map = pin("map.json", ControlBuild.strictMapper().writeValueAsString(List.of(source)));
        List<String> targets = List.of("xar_bridge_ck3_12003_army_condition30_inputs_test", "xar_bridge_ck3_12003_army_flag20_inputs_test", "xar_bridge_ck3_12003_army_flag21_inputs_test", "xar_bridge_ck3_12003_selected_title_holder_owner_relation_test", "xar_bridge_ck3_12003_army_flag31_inputs_test");
        return new NativeFixtureCorpora.Request(NativeFixtureCorpora.REQUEST_SCHEMA, WindowsJobProcess.currentMachineId(), NativeFixtureCorpora.Kind.MANAGERS, map, environment, snapshot,
                targets.stream().map(target -> new NativeFixtureCorpora.Run(target, source, executable, terminal, output)).toList());
    }
    private ControlBuild.FileRef pin(String filename, String text) throws Exception { Path path = temporary.resolve(filename); Files.writeString(path, text); return ControlBuild.FileRef.measure(path); }
}
