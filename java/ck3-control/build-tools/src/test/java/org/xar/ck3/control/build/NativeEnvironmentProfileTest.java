package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/** Synthetic authority data verifies the actual producer/reader contract; it never starts a stage. */
final class NativeEnvironmentProfileTest {
    @TempDir Path temporary;

    @Test void boundedEnvCardRoundTripsThroughTheProductionReader() throws Exception {
        var mapper = ControlBuild.strictMapper();
        var card = card(268435456L, 16777216L);
        byte[] wire = mapper.writeValueAsBytes(card);
        var read = mapper.readValue(wire, NativeFixtureBuild.ResourceCard.class);
        assertEquals(card, read);
        assertEquals(268435456L, NativeFixtureBuild.stageMemoryLimit(read.allowedStage()));
        assertEquals(16777216L, NativeFixtureBuild.stageScratchLimit(read.allowedStage()));
        assertEquals(120, read.timeoutSeconds());
        ObjectNode wrongType = (ObjectNode) mapper.readTree(wire);
        wrongType.put("scratch_limit_bytes", true);
        assertThrows(java.io.IOException.class, () -> mapper.treeToValue(wrongType, NativeFixtureBuild.ResourceCard.class));
    }

    @Test void oldWideEnvCardCannotAuthorizeTheSmallRealProbe() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> card(2147483648L, 134217728L));
        var mapper = ControlBuild.strictMapper();
        ObjectNode legacy = mapper.valueToTree(card(268435456L, 16777216L));
        legacy.put("schema", "xar.shared-native-stage-resource-card/v1");
        assertThrows(java.io.IOException.class, () -> mapper.treeToValue(legacy, NativeFixtureBuild.ResourceCard.class));
        ObjectNode missing = mapper.valueToTree(card(268435456L, 16777216L));
        missing.remove("scratch_limit_bytes");
        assertThrows(java.io.IOException.class, () -> mapper.treeToValue(missing, NativeFixtureBuild.ResourceCard.class));
    }

    private NativeFixtureBuild.ResourceCard card(long memory, long scratch) throws Exception {
        Path fixture = temporary.resolve("synthetic-card-ref");
        if (!Files.exists(fixture)) Files.writeString(fixture, "metadata-only fixture; not a Root authority");
        ControlBuild.FileRef ref = ControlBuild.FileRef.measure(fixture);
        return new NativeFixtureBuild.ResourceCard("xar.shared-native-stage-resource-card/v2",
                "xenoamess-full-tower-eb9d2c1186", "2026-10-23T07:00:00Z", "2026-10-23T08:30:00Z",
                "/root/native_fixture09", NativeFixtureBuild.ResourceStatus.ADMITTED_SINGLE_STAGE,
                NativeFixtureBuild.Stage.ENV, memory, scratch, 120, ref, ref, ref, ref, ref, ref,
                List.of(), List.of(temporary.toString()));
    }
}
