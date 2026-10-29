package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import org.junit.jupiter.api.Test;

/** The actual test consumes the native producer receipt; synthetic rejection checks grant no native credit. */
final class Person10NativeCorpusBuildTest {
    @Test void mixedBuildLeafOrLeafOnlyJsonCannotPretendToBeAnActualWholeProducerPacket() throws Exception {
        var producer = Person10NativeCorpusBuild.PRODUCERS.getFirst();
        ObjectNode leafOnly = ControlBuild.strictMapper().createObjectNode();
        leafOnly.putObject(producer.field()).put("build_version", "1.20.0.4");
        assertThrows(java.io.IOException.class, () -> Person10NativeCorpusBuild.validatePacket(producer, leafOnly));
        ObjectNode root = packet(producer, "1.20.0.4");
        Person10NativeCorpusBuild.validatePacket(producer, root); // explicitly synthetic parser-boundary fixture
        ObjectNode mixed = packet(producer, "1.20.0.3");
        assertThrows(java.io.IOException.class, () -> Person10NativeCorpusBuild.validatePacket(producer, mixed));
        ObjectNode oldSha = packet(producer, "1.20.0.4");
        ((ObjectNode)oldSha.path("result").path("battle_terminal_transition").path("character_observations").get(0).path(producer.field()))
                .put("executable_sha256", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
        assertThrows(java.io.IOException.class, () -> Person10NativeCorpusBuild.validatePacket(producer, oldSha));
        ObjectNode floatVersion = packet(producer, "1.20.0.4"); floatVersion.put("protocol_version", 1.0);
        assertThrows(java.io.IOException.class, () -> Person10NativeCorpusBuild.validatePacket(producer, floatVersion));
        ObjectNode wrongStep = packet(producer, "1.20.0.4"); ((ObjectNode)wrongStep.get("result")).put("step", "other-read");
        assertThrows(java.io.IOException.class, () -> Person10NativeCorpusBuild.validatePacket(producer, wrongStep));
        assertEquals(10, Person10NativeCorpusBuild.PRODUCERS.stream().map(Person10NativeCorpusBuild.Producer::target).distinct().count());
        assertEquals(83, Person10NativeCorpusBuild.PRODUCERS.stream().mapToInt(Person10NativeCorpusBuild.Producer::packetCount).sum());
    }
    private static ObjectNode packet(Person10NativeCorpusBuild.Producer producer, String build) {
        ObjectNode packet = ControlBuild.strictMapper().createObjectNode().put("type", "command_result").put("protocol_version", 1).put("ok", true).put("request_id", "SYNTHETIC-BOUNDARY");
        ObjectNode result = packet.putObject("result").put("accepted", true).put("step", "query-battle-terminal-transition-v1-none:characters:67108867");
        ObjectNode transition = result.putObject("battle_terminal_transition").put("contract_stage", "production_exact_battle_terminal_transition");
        transition.putArray("character_observations").addObject().putObject(producer.field()).put("build_version", build)
                .put("executable_sha256", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        return packet;
    }
}

