package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;

/** Pure versioned DTO contract. It grants no Native capability or complete gameplay observation. */
final class CoreFrameBuildIdentityTest {
    private static final CoreFrame.Prefix PREFIX = new CoreFrame.Prefix(53144328, 3, true, 7, true, true, 7, true);

    @Test void florinPartialAndUnavailableKeepTheirExactIdentityThroughPublicNormalization() {
        for (CoreFrame original : List.of(new CoreFrame.Partial(ExactCk3Build.CK3_1210, PREFIX),
                new CoreFrame.Unavailable(ExactCk3Build.CK3_1210, true, "core_prefix_unavailable"))) {
            var encoded = CoreFramePublicCodec.encode(original);
            var row = RegistryJson.object(encoded);
            assertEquals("ck3_1210_core_frame_v1", row.get("schema").textValue());
            assertEquals("1.21.0", row.get("game_version").textValue());
            assertEquals("ck3-1.21.0-native-headless-main-thread", row.get("backend").textValue());
            assertFalse(row.get("complete_snapshot").booleanValue());
            assertEquals(original, CoreFrame.decode(encoded));
            assertEquals(ExactCk3Build.CK3_1210, CoreFrame.decode(encoded).build());
        }
    }

    @Test void existingConstructorsStillEncodeTheFrozenPreviousProfile() {
        for (CoreFrame original : List.of(new CoreFrame.Partial(PREFIX), new CoreFrame.Unavailable(false, "not_ready"))) {
            var encoded = CoreFramePublicCodec.encode(original);
            var row = RegistryJson.object(encoded);
            assertEquals("ck3_12004_core_frame_v1", row.get("schema").textValue());
            assertEquals("1.20.0.4", row.get("game_version").textValue());
            assertEquals(RegistryJson.EXE, row.get("executable_sha256").textValue());
            assertEquals(original, CoreFrame.decode(encoded));
        }
    }

    @Test void aNewVersionCannotRelabelOldLayoutOrTurnAPartialPrefixIntoACompleteSnapshot() {
        var source = RegistryJson.object(CoreFramePublicCodec.encode(new CoreFrame.Partial(ExactCk3Build.CK3_1210, PREFIX)));
        for (String field : List.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "complete_snapshot")) {
            var tampered = source.deepCopy();
            switch (field) {
                case "schema" -> tampered.put(field, "ck3_12004_core_frame_v1");
                case "game_version" -> tampered.put(field, "1.21.0.0");
                case "executable_sha256" -> tampered.put(field, ExactCk3Build.CK3_12004.executableSha256());
                case "adapter_id" -> tampered.put(field, "ck3-1.20.0.4-msvc-x64");
                case "backend" -> tampered.put(field, "ck3-1.20.0.4-native-headless-main-thread");
                case "complete_snapshot" -> tampered.put(field, true);
                default -> throw new AssertionError(field);
            }
            var raw = new RawJson(tampered.toString().getBytes(StandardCharsets.UTF_8));
            assertThrows(IllegalArgumentException.class, () -> CoreFrame.decode(raw), field);
        }
    }
}
