package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class CanonicalPythonInvocationTest {
    @TempDir Path root;
    @Test void fullOriginalThirtyParsesAndPreservesTheIndependentContinuationBody() throws Exception {
        String repository = CanonicalOracleEnvironment.require(System.getenv()).repositoryRoot();
        var step = CanonicalColdWarmStage.parseStep(Files.readString(Path.of(repository).resolve(".github/workflows/static-ci.yml")));
        int count = 0, continuation = 0;
        for (int index = 0; index < step.commandLines().size(); index += 2) {
            String original = step.commandLines().get(index); var parsed = CanonicalPythonInvocation.parse(original, root);
            assertEquals(original, parsed.originalCommand()); assertEquals("-B", parsed.interpreterArguments().getFirst()); count++;
            if (original.contains("CurrentSavedSdkPersistenceTests.test_sdk_persist_closed_rejection_warm_binding_and_wrong_generations")) {
                continuation++; assertEquals(CanonicalPythonInvocation.Mode.INLINE_SOURCE, parsed.mode());
                assertTrue(parsed.inlineSource().contains("b.HARD=524288; b.SOFT=458752"));
                assertTrue(parsed.inlineSource().indexOf("b.HARD=524288") < parsed.inlineSource().indexOf("test_current_saved_campaign_cold_v1 as c"));
            }
        }
        assertEquals(30, count); assertEquals(1, continuation);
    }
    @Test void moduleInlineAndScriptKeepDifferentTypedPayloadsAndDeclaredTemporaryExpansion() throws Exception {
        var module = CanonicalPythonInvocation.parse("python -B -m mypy --cache-dir \"%RUNNER_TEMP%\\cold-cache\"", root);
        assertEquals(CanonicalPythonInvocation.Mode.MODULE, module.mode()); assertEquals("mypy", module.moduleName());
        assertEquals(List.of("--cache-dir", root + "\\cold-cache"), module.arguments()); assertNull(module.inlineSource());
        String source = "import sys; print('body keeps = and >'); sys.exit(7)";
        var inline = CanonicalPythonInvocation.parse("python -B -X utf8 -c \"" + source + "\"", root);
        assertEquals(source, inline.inlineSource()); assertEquals(List.of("-B", "-X", "utf8"), inline.interpreterArguments()); assertNull(inline.moduleName());
        var script = CanonicalPythonInvocation.parse("python -B -X utf8 tools/g2_saved_campaign/test_owner_prepare_contract_v1.py", root);
        assertEquals(CanonicalPythonInvocation.Mode.SCRIPT_FILE, script.mode()); assertEquals("tools/g2_saved_campaign/test_owner_prepare_contract_v1.py", script.relativeScript());
    }
    @Test void unknownShellExpansionOptionsAndUnfinishedQuotesNeverBecomeDifferentCommands() throws Exception {
        for (String invalid : List.of("python -m unittest test_module", "python -B -X dev -m unittest test_module",
                "python -B -m mypy & echo unsafe", "python -B -m mypy %UNDECLARED_ROOT%", "python -B -c \"unfinished",
                "python -B ../foreign.py", "python -B -m", "python -B -c \"body\"\npython -B -c \"another\""))
            assertThrows(IOException.class, () -> CanonicalPythonInvocation.parse(invalid, root), invalid);
    }
    @Test void typedInvocationRoundTripRejectsMixedModesAndBooleanFields() throws Exception {
        var value = CanonicalPythonInvocation.parse("python -B -X utf8 -c \"print('exact')\"", root);
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(value);
        assertEquals(value, mapper.readValue(raw, CanonicalPythonInvocation.Invocation.class));
        for (String wrong : List.of(raw.replace("\"mode\":\"INLINE_SOURCE\"", "\"mode\":\"MODULE\""),
                raw.replace("\"module_name\":null", "\"module_name\":\"mypy\""),
                raw.replace("\"relative_script\":null", "\"relative_script\":true"))) {
            assertNotEquals(raw, wrong); assertThrows(IOException.class, () -> mapper.readValue(wrong, CanonicalPythonInvocation.Invocation.class));
        }
    }
}
