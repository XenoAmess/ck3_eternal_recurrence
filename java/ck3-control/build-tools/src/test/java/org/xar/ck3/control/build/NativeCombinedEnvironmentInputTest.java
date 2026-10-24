package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** The real addon input codec and producer guard; no source/ENV qualification is fabricated. */
final class NativeCombinedEnvironmentInputTest {
    @TempDir Path temporary;

    @Test void v2InputRoundTripsAnExplicitNullRegistrationHelper() throws IOException {
        var input = input("xar.native-combined-environment-input/v2", null);
        var mapper = RootNativePlanJson.mapper();
        var tree = mapper.readTree(mapper.writeValueAsBytes(input));
        assertTrue(tree.has("defender"));
        assertTrue(tree.get("defender").isNull());
        assertEquals(input, mapper.treeToValue(tree, NativeCombinedSourceCut.EnvironmentInput.class));
        assertThrows(IOException.class, () -> NativeCombinedSourceCut.writeEnvironmentRequest(input));
    }

    @Test void historicalInputCannotProduceANewEnvRequest() throws IOException {
        var legacy = input("xar.native-combined-environment-input/v1", null);
        IOException rejected = assertThrows(IOException.class,
                () -> NativeCombinedSourceCut.writeEnvironmentRequest(legacy));
        assertTrue(rejected.getMessage().contains("v2"));
    }

    @Test void registrationPayloadIsRejectedBeforeReadingSourceActual() throws IOException {
        var python = pin("python.exe", "unqualified codec input");
        var helper = pin("helper.py", "unqualified codec input");
        var registration = new NativeBridgeDefender.HelperRuntime(temporary.resolve("python-base"),
                temporary.resolve("venv"), python, helper, List.of(python), List.of(helper));
        var invalid = input("xar.native-combined-environment-input/v2", registration);
        IOException rejected = assertThrows(IOException.class,
                () -> NativeCombinedSourceCut.writeEnvironmentRequest(invalid));
        assertTrue(rejected.getMessage().contains("REGISTER"));
    }

    @Test void omissionOfTheNullableCreatorRemainsAnError() throws IOException {
        var mapper = RootNativePlanJson.mapper();
        ObjectNode tree = mapper.valueToTree(input("xar.native-combined-environment-input/v2", null));
        tree.remove("defender");
        assertThrows(IOException.class,
                () -> mapper.readValue(mapper.writeValueAsBytes(tree), NativeCombinedSourceCut.EnvironmentInput.class));
    }

    private NativeCombinedSourceCut.EnvironmentInput input(String schema,
            NativeBridgeDefender.HelperRuntime registration) throws IOException {
        var tools = new ArrayList<ControlBuild.FileRef>();
        for (String name : List.of("cmd.exe", "vcvars64.bat", "java.exe", "cmake.exe", "ninja.exe", "cl.exe", "link.exe")) {
            tools.add(pin(name, "codec input only"));
        }
        return new NativeCombinedSourceCut.EnvironmentInput(schema, pin("source-actual.json", "{}"), temporary,
                pin("qualified-tools.json", "{}"), new NativeBridgeBuild.Toolchain(tools.get(0), tools.get(1),
                        tools.get(2), tools.get(3), tools.get(4), tools.get(5), tools.get(6)),
                List.of(new NativeBridgeBuild.Definition("XAR_CK3_ENABLE_HOLY_LOAN_SOURCE12004", NativeBridgeBuild.SwitchValue.OFF)),
                4, temporary.resolve("build"), temporary.resolve("scratch"), registration,
                temporary.resolve("owned"), temporary.resolve("owned/env-request.json"));
    }

    private ControlBuild.FileRef pin(String name, String body) throws IOException {
        Path file = temporary.resolve(name);
        if (!Files.exists(file)) Files.writeString(file, body);
        return ControlBuild.FileRef.measure(file);
    }
}
