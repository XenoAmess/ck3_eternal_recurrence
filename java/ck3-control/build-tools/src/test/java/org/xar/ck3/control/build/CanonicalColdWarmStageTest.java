package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class CanonicalColdWarmStageTest {
    @TempDir Path root;
    private static Path requiredPath(String name) throws IOException {
        String value = System.getenv(name); if (value == null || value.isBlank()) throw new IOException("Required fixture environment missing: " + name); return Path.of(value).toRealPath();
    }
    private CanonicalColdWarmStage.CommandActual execute(String line, int index) throws Exception {
        Map<String, String> env = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); env.putAll(System.getenv());
        for (String key : List.of("PYTHONHOME", "PYTHONPATH", "PYTHONSAFEPATH", "PYTHONINSPECT", "PYTEST_ADDOPTS", "PYTEST_PLUGINS")) env.remove(key);
        env.put("PYTHONDONTWRITEBYTECODE", "1"); env.put("PYTHONIOENCODING", "utf-8");
        return CanonicalColdWarmStage.execute(index, CanonicalPythonInvocation.parse(line, root), CanonicalColdWarmStage.BootstrapMode.NONE,
                null, ControlBuild.FileRef.measure(requiredPath("XAR_ORACLE_PYTHON")), root, root.resolve("command-" + index), Map.copyOf(env),
                256L << 20, Duration.ofSeconds(20), Instant.now().plusSeconds(25), pending -> {});
    }
    @Test void parsesActualCompleteThirtyAndRequiresIndependentContinuation() throws Exception {
        var inputs = CanonicalOracleEnvironment.require(System.getenv());
        String raw = Files.readString(Path.of(inputs.repositoryRoot()).resolve(".github/workflows/static-ci.yml")); var step = CanonicalColdWarmStage.parseStep(raw);
        assertEquals(30, step.pythonCommands()); assertEquals(60, step.commandLines().size());
        assertThrows(IOException.class, () -> CanonicalColdWarmStage.parseStep(raw.replace("CurrentSavedSdkPersistenceTests.test_sdk_persist_closed_rejection_warm_binding_and_wrong_generations", "removed_continuation")));
        assertThrows(IOException.class, () -> CanonicalColdWarmStage.parseStep(raw.replaceFirst("python -B -m mypy", "echo removed")));
    }
    @Test void combinedUnittestSkipAndExpectedFailureCannotBecomePass() throws Exception {
        var combined = CanonicalColdWarmStage.summary("Ran 8 tests in 0.12s\nOK (skipped=1, expected failures=2)\n");
        assertEquals(1, combined.skipped()); assertEquals(2, combined.expectedFailures()); assertFalse(combined.accepted());
        assertFalse(CanonicalColdWarmStage.summary("Ran 1 test in 0.1s\nOK (expected failures=1)\n").accepted());
        assertFalse(CanonicalColdWarmStage.summary("Ran 1 test in 0.1s\nFAILED (unexpected successes=1)\n").accepted());
        assertFalse(CanonicalColdWarmStage.summary("Ran 0 tests in 0.0s\nOK\n").accepted());
        assertThrows(IOException.class, () -> CanonicalColdWarmStage.summary("OK (unknown=1)\n"));
        assertFalse(CanonicalColdWarmStage.summary("=== 2 passed, 1 xfailed, 1 skipped in 0.4s ===\n").accepted());
    }
    @Test void realOriginalNonzeroBodyRetainsNativeTerminalObservationAndIndependentOutputs() throws Exception {
        var command = execute("python -B -X utf8 -c \"print('first actual'); raise SystemExit(7)\"", 1);
        assertEquals(CanonicalColdWarmStage.CommandState.RED, command.state()); assertEquals(7, command.result().exitCode());
        assertEquals(0, command.result().accounting().activeProcesses()); assertNull(command.result().stopReason());
        assertEquals(7, command.observation().exitCode()); assertNull(command.observation().bootstrapEvidence());
        assertTrue(Files.readString(Path.of(command.stdoutRef().path())).contains("first actual"));
        var notRun = new CanonicalColdWarmStage.CommandActual(2, CanonicalPythonInvocation.parse("python -B -c \"raise RuntimeError('must not start')\"", root),
                CanonicalColdWarmStage.CommandState.NOT_RUN, List.of(), null, null, null, null, null, null, null, null);
        assertEquals(CanonicalColdWarmStage.CommandState.NOT_RUN, notRun.state()); assertNull(notRun.result());
    }
    @Test void actualExpectedFailureExitZeroIsRejectedByTheSharedDirectProducer() throws Exception {
        var command = execute("python -B -X utf8 -c \"import unittest; T=type('ActualExpectedFailure',(unittest.TestCase,),{'test_expected':unittest.expectedFailure(lambda self:self.fail('actual expected failure'))}); result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T)); raise SystemExit(0 if result.wasSuccessful() else 1)\"", 1);
        assertTrue(command.result().passed()); assertEquals(0, command.observation().exitCode());
        assertEquals(1, command.summary().expectedFailures()); assertEquals(CanonicalColdWarmStage.CommandState.RED, command.state()); assertNotNull(command.error());
    }
    @Test void actualChildRejectsInvalidBootstrapBeforeTheOriginalBodyAndRetainsNativeFailure() throws Exception {
        Path malformed = root.resolve("malformed-bootstrap.json"); Files.writeString(malformed, "{}");
        var invocation = CanonicalPythonInvocation.parse("python -B -X utf8 -c \"from pathlib import Path; Path('body-must-not-run').write_text('invalid bootstrap accepted')\"", root);
        var command = CanonicalColdWarmStage.execute(1, invocation, CanonicalColdWarmStage.BootstrapMode.ROOT_SOFTWARE_FIXTURE,
                ControlBuild.FileRef.measure(malformed), ControlBuild.FileRef.measure(requiredPath("XAR_ORACLE_PYTHON")), root, root.resolve("rejected-bootstrap"),
                Map.copyOf(System.getenv()), 256L << 20, Duration.ofSeconds(20), Instant.now().plusSeconds(25), pending -> {});
        assertEquals(CanonicalColdWarmStage.CommandState.RED, command.state()); assertNotNull(command.result());
        assertNotEquals(0, command.result().exitCode()); assertEquals(0, command.result().accounting().activeProcesses());
        assertFalse(Files.exists(root.resolve("body-must-not-run"))); assertNotNull(command.stderrRef());
        assertTrue(Files.size(Path.of(command.stderrRef().path())) > 0); assertNull(command.observation()); assertNotNull(command.error());
    }
    @Test void originalScriptAndModuleBodiesKeepArgvFileAndModuleExecutionSemantics() throws Exception {
        Files.createDirectories(root.resolve("tools"));
        Files.writeString(root.resolve("tools/original_script.py"), "import json,sys,pathlib\nprint(json.dumps([__name__,__file__,sys.argv,sys.path[0]]))\n");
        var script = execute("python -B -X utf8 tools/original_script.py original-argument", 1);
        assertEquals(CanonicalColdWarmStage.CommandState.PASS, script.state(), script.error());
        String raw = Files.readString(Path.of(script.stdoutRef().path()));
        assertTrue(raw.contains("__main__")); assertTrue(raw.contains("tools/original_script.py")); assertTrue(raw.contains("original-argument"));
        Files.writeString(root.resolve("original_module.py"), "import sys\nassert __name__ == '__main__'\nassert sys.argv[1:] == ['module-argument']\nprint('ORIGINAL_MODULE_ACTUAL')\n");
        var module = execute("python -B -m original_module module-argument", 2);
        assertEquals(CanonicalColdWarmStage.CommandState.PASS, module.state(), module.error());
        assertTrue(Files.readString(Path.of(module.stdoutRef().path())).contains("ORIGINAL_MODULE_ACTUAL"));
    }
    @Test void explicitNoneScopeConfigRoundTripAndWrongMissingOrBooleanFieldsReject() throws Exception {
        Path source = root.resolve("fixture.pin"), git = root.resolve("git.exe"); Files.writeString(source, "configuration fixture pin"); Files.writeString(git, "synthetic metadata fixture; never executed");
        var pin = ControlBuild.FileRef.measure(source);
        var value = new CanonicalColdWarmStage.Config(CanonicalColdWarmStage.SCHEMA, "fixture-machine", Instant.now().plusSeconds(120).toString(), root.resolve("repo").toString(),
                root.resolve("work").toString(), pin, ControlBuild.FileRef.measure(git), pin, pin, List.of(pin), List.of(root.resolve("dependencies").toString()), List.of(pin), pin,
                CanonicalColdWarmStage.BootstrapMode.NONE, null, 256L << 20, 20);
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(value); assertEquals(value, mapper.readValue(raw, CanonicalColdWarmStage.Config.class));
        for (String wrong : List.of(raw.replace("\"bootstrap_mode\":\"NONE\"", "\"bootstrap_mode\":\"ROOT_SOFTWARE_FIXTURE\""),
                raw.replace("\"canonical_sources\"", "\"missing_source_contract\""), raw.replace("\"timeout_seconds\":20", "\"timeout_seconds\":true"),
                raw.replace("\"timeout_seconds\":20", "\"timeout_seconds\":20.0"), raw.replace(CanonicalColdWarmStage.SCHEMA, "xar.canonical-cold-warm-stage/v2"))) {
            assertNotEquals(raw, wrong); assertThrows(IOException.class, () -> mapper.readValue(wrong, CanonicalColdWarmStage.Config.class));
        }
    }
    @Test void realNativeFailureSurvivesFinalMetadataGuardFailureInTypedStderrEvidence() throws Exception {
        var command = execute("python -B -X utf8 -c \"raise SystemExit(9)\"", 1); assertEquals(9, command.result().exitCode());
        Path source = root.resolve("fixture.pin"), git = root.resolve("git.exe"); Files.writeString(source, "synthetic configuration pin"); Files.writeString(git, "metadata fixture; never executed");
        var pin = ControlBuild.FileRef.measure(source); String machine = WindowsJobProcess.currentMachineId();
        var config = new CanonicalColdWarmStage.Config(CanonicalColdWarmStage.SCHEMA, machine, Instant.now().plusSeconds(120).toString(), root.resolve("repository").toString(), root.resolve("work").toString(),
                pin, ControlBuild.FileRef.measure(git), pin, pin, List.of(pin), List.of(root.resolve("dependencies").toString()), List.of(pin), pin,
                CanonicalColdWarmStage.BootstrapMode.NONE, null, 256L << 20, 20);
        var actual = new CanonicalColdWarmStage.Actual(CanonicalColdWarmStage.SCHEMA, machine, Instant.now().toString(), Instant.now().toString(), SupplementalFixtureCi.Status.RED,
                "Actual command failed", pin, pin, pin, List.of(pin), WindowsJobProcess.ConsoleMode.DETACHED, List.of(command), pin, null, ControlBuild.SourceState.UNKNOWN,
                CanonicalColdWarmStage.BootstrapMode.NONE, false);
        PrintStream previous = System.err; ByteArrayOutputStream captured = new ByteArrayOutputStream();
        try (PrintStream output = new PrintStream(captured, true, StandardCharsets.UTF_8)) {
            System.setErr(output); assertThrows(IOException.class, () -> CanonicalColdWarmStage.writeActual(root.resolve("actual.json"), actual, config,
                    pending -> { throw new IOException("actual final publication guard rejection"); }));
        } finally { System.setErr(previous); }
        var retained = ControlBuild.strictMapper().readValue(captured.toByteArray(), CanonicalColdWarmStage.Actual.class);
        assertEquals(command.result(), retained.commands().getFirst().result()); assertEquals(actual.commands(), retained.commands());
        assertEquals(SupplementalFixtureCi.Status.RED, retained.status()); assertTrue(retained.error().contains("actual final publication guard rejection"));
    }
}
