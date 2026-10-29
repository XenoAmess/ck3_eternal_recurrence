package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class SdkFixtureProductionInputsTest {
    private static FileRef ref(String name) { return new FileRef("D:/contract-only/" + name, 1, "a".repeat(64)); }
    private static SdkFixtureProductionInputs.Inputs current() {
        var law = new SdkFixtureProductionInputs.LawWireSet("D:/contract-only/law", List.of(
                ref("law/query.json"), ref("law/pending.json"), ref("law/unchanged.json"), ref("law/enacted.json")));
        var lobby = new SdkFixtureProductionInputs.LobbyWireSet("D:/contract-only/lobby",
                SdkFixtureProductionInputs.LOBBY_NAMES.stream().map(name -> ref("lobby/" + name)).toList());
        return new SdkFixtureProductionInputs.Inputs(SdkFixtureProductionInputs.SCHEMA, "contract-machine", "2030-01-01T00:00:00Z",
                ref("gui.json"), law, "D:/contract-only/owned-scratch", ref("nested.json"), lobby);
    }
    @Test void currentFourPackageCodecAndRecordedArgumentsShareOneProjectionAndLegacyReplayRemainsExact() throws Exception {
        var input = current();
        assertEquals(input, SdkFixtureProductionInputs.decode(SdkFixtureProductionInputs.encode(input)));
        var command = SdkFixtureProductionInputs.commandArguments(input);
        assertEquals(11, command.mavenArguments().size());
        assertEquals(command, SdkFixtureProductionInputs.fromRecordedArguments(command.mavenArguments()));
        for (String field : List.of(SdkFixtureProductionInputs.BUNDLE_SCHEMA_PROPERTY, SdkFixtureProductionInputs.LOBBY_DIRECTORY)) {
            String prefix = "-D" + field + "=";
            assertThrows(IllegalArgumentException.class, () -> SdkFixtureProductionInputs.fromRecordedArguments(command.mavenArguments().stream().filter(arg -> !arg.startsWith(prefix)).toList()));
            var duplicate = new ArrayList<>(command.mavenArguments()); duplicate.add(command.mavenArguments().stream().filter(arg -> arg.startsWith(prefix)).findFirst().orElseThrow());
            assertThrows(IllegalArgumentException.class, () -> SdkFixtureProductionInputs.fromRecordedArguments(duplicate));
        }
        var old = new SdkFixtureProductionInputs.Inputs(SdkFixtureProductionInputs.LEGACY_SCHEMA, input.machineId(), input.reviewAtUtc(),
                input.guiConfigurationRef(), input.lawWires(), input.lawScratchDirectory(), input.nestedQuantityWireRef(), null);
        var oldCommand = SdkFixtureProductionInputs.commandArguments(old);
        assertEquals(SdkFixtureProductionInputs.Generation.V1_THREE, oldCommand.generation());
        assertEquals(9, oldCommand.mavenArguments().size());
        assertEquals(oldCommand, SdkFixtureProductionInputs.fromRecordedArguments(oldCommand.mavenArguments()));
        assertEquals(old, SdkFixtureProductionInputs.decode(SdkFixtureProductionInputs.encode(old)));
        assertThrows(IllegalArgumentException.class, () -> SdkFixtureProductionInputs.requireCurrent(old));
        assertThrows(IllegalArgumentException.class, () -> new SdkFixtureProductionInputs.Inputs(input.schema(), input.machineId(), input.reviewAtUtc(),
                input.guiConfigurationRef(), input.lawWires(), input.lawScratchDirectory(), input.nestedQuantityWireRef(), null));
        assertFalse(command.equals(oldCommand));
    }
    @Test void lobbyBoundaryRequiresTheFiveOriginalNamesSameParentPositiveBytesAndStrictIntegerTypes() throws Exception {
        var input = current(); var wires = input.lobbyWires().originals();
        assertThrows(IllegalArgumentException.class, () -> new SdkFixtureProductionInputs.LobbyWireSet(input.lobbyWires().directory(), wires.subList(0, 4)));
        var duplicate = new ArrayList<>(wires); duplicate.set(4, wires.getFirst());
        assertThrows(IllegalArgumentException.class, () -> new SdkFixtureProductionInputs.LobbyWireSet(input.lobbyWires().directory(), duplicate));
        var crossed = new ArrayList<>(wires); crossed.set(0, ref("different/lobby-callback-request.json"));
        assertThrows(IllegalArgumentException.class, () -> new SdkFixtureProductionInputs.LobbyWireSet(input.lobbyWires().directory(), crossed));
        var empty = new ArrayList<>(wires); empty.set(0, new FileRef(wires.getFirst().path(), 0, wires.getFirst().sha256()));
        assertThrows(IllegalArgumentException.class, () -> new SdkFixtureProductionInputs.LobbyWireSet(input.lobbyWires().directory(), empty));
        var mapper = ControlBuild.strictMapper();
        var tree = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(SdkFixtureProductionInputs.encode(input));
        var missing = tree.deepCopy(); missing.remove("lobby_wires");
        assertThrows(java.io.IOException.class, () -> SdkFixtureProductionInputs.decode(mapper.writeValueAsBytes(missing)));
        var wrong = tree.deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode) wrong.path("lobby_wires").path("originals").get(0)).put("bytes", true);
        assertThrows(java.io.IOException.class, () -> SdkFixtureProductionInputs.decode(mapper.writeValueAsBytes(wrong)));
        var legacyWithLobby = tree.deepCopy(); legacyWithLobby.put("schema", SdkFixtureProductionInputs.LEGACY_SCHEMA);
        assertThrows(java.io.IOException.class, () -> SdkFixtureProductionInputs.decode(mapper.writeValueAsBytes(legacyWithLobby)));
        assertTrue(Path.of(input.lawScratchDirectory()).isAbsolute());
    }
}

