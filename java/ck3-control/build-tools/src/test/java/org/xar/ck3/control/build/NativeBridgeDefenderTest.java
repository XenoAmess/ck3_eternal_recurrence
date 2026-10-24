package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class NativeBridgeDefenderTest {
    @TempDir Path temporary;
    private ControlBuild.FileRef pin(String name, String body) throws IOException {
        Path path = temporary.resolve(name); Files.writeString(path, body); return ControlBuild.FileRef.measure(path);
    }
    @Test void missingAdminTokenDisabledAndAckDoNotQualifyExclusionReadback() throws Exception {
        var injector = pin("xar_ck3_bridge_injector.exe", "not executable; data fixture only");
        var manifest = pin("manifest.json", "{\"schema\":\"xar.project-exe-exclusions.v1\",\"files\":[]}");
        for (String status : List.of("disabled", "settings_failed", "running", "verified")) {
            var receipt = pin("receipt-" + status + ".json", "{\"schema\":\"xar.project-exe-exclusions.v1\",\"status\":\"" + status + "\",\"admin_token\":false}");
            assertThrows(IOException.class, () -> NativeBridgeDefender.readVerified(receipt, manifest, injector));
        }
    }
    @Test void arbitraryInterpreterAndIncompleteHelperClosureAreRejected() throws Exception {
        var python = pin("other.exe", "fixture"); var helper = pin("other.py", "fixture");
        var runtime = new NativeBridgeDefender.HelperRuntime(temporary.resolve("base"), temporary.resolve("venv"), python, helper, List.of(python), List.of(helper));
        assertThrows(IOException.class, () -> NativeBridgeDefender.verifyHelperRuntime(temporary, runtime));
    }
    @Test void arbitraryNamedBinaryCannotMasqueradeAsProductionPe() throws Exception {
        var file = pin("xar_ck3_bridge.dll", "x".repeat(128));
        assertThrows(IOException.class, () -> NativeBridgeDefender.requirePe(file, true));
        assertThrows(IOException.class, () -> NativeBridgeDefender.requirePe(file, false));
    }
    @Test void nativeReceiptDecimalSizeRejectsBooleanBeforeReadback() throws Exception {
        var mapper = ControlBuild.strictMapper();
        for (String token : List.of("true", "1.0", "\"1\"")) {
            String raw = "{\"path\":\"fixture\",\"size\":" + token + ",\"sha256\":\"fixture\",\"target\":\"fixture\",\"target_id\":\"fixture\"}";
            assertThrows(IOException.class, () -> mapper.readValue(raw, NativeBridgeDefender.ManifestFile.class));
        }
    }
}
