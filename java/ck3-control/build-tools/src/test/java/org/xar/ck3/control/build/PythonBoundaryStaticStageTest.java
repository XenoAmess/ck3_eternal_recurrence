package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;

class PythonBoundaryStaticStageTest {
    @TempDir Path root;

    private ControlBuild.FileRef file(String name) throws IOException {
        Path path = root.resolve(name); Files.writeString(path, "actual source " + name);
        return ControlBuild.FileRef.measure(path.toRealPath());
    }

    private PythonBoundaryStaticStage.ScopeManifest whole(String version, boolean completed, int errors) throws IOException {
        var source = file("test_conditional_monthly_loss_budgets.py");
        return new PythonBoundaryStaticStage.ScopeManifest("xar.python-boundary-static-scope/v2",
                PythonBoundaryStaticStage.Kind.MONTHLY_FIXTURE_WHOLE_MODULE, true, completed, errors,
                version, "1.15.0", "", List.of(new PythonBoundaryStaticStage.SourceRange("whole_module", source.path(), 1, 30)),
                List.of(), List.of(source, file("driver.py"), file("service.py")), List.of());
    }

    private PythonBoundaryStaticStage.ScopeManifest sdk(boolean wholeCredit, String mcpVersion, boolean actualDependencies) throws IOException {
        var nativeSource = file("native_driver.py"); var mcpSource = file("mcp_server.py");
        var driver = file("driver.py"); var test = file("test_mcp_war_daily_watch_config_v1.py");
        List<PythonBoundaryStaticStage.SourceRange> ranges = new ArrayList<>();
        for (String name : List.of("_TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY", "_TACTICAL_DAILY_SENTINEL_STATUS_STEP",
                "allow_private_semantic_snapshot_readonly", "read_tactical_daily_sentinel_status_private_v1")) ranges.add(new PythonBoundaryStaticStage.SourceRange(name, nativeSource.path(), 1, 10));
        for (String name : List.of("read_only_tool", "sentinel_status", "sentinel_guard_and_handler")) {
            ranges.add(new PythonBoundaryStaticStage.SourceRange(name, mcpSource.path(), 1, 10));
        }
        for (String name : List.of("test_fixed_status_driver_uses_only_existing_capability_without_transcript",
                "test_fixed_status_actual_registered_mcp_is_zero_argument_and_opt_in",
                "test_fixed_status_registered_mcp_rejects_transcript_and_arbitrary_arguments", "NoGameEndpoint")) {
            ranges.add(new PythonBoundaryStaticStage.SourceRange(name, test.path(), 1, 10));
        }
        return new PythonBoundaryStaticStage.ScopeManifest("xar.python-boundary-static-scope/v2",
                PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED, wholeCredit, true, 0,
                "3.13", "1.15.0", mcpVersion, ranges,
                List.of(new PythonBoundaryStaticStage.SourceRange("_execute_primitive_step", nativeSource.path(), 1, 4)),
                List.of(nativeSource, mcpSource, driver, test),
                actualDependencies ? List.of(file("mcp_actual_server.py"), file("mcp_actual_types.py")) : List.of());
    }

    @Test void acceptsExplicitWholeFixtureScopeAtTheSupportedPythonVersion() throws IOException {
        var manifest = whole("3.13", true, 0);
        assertDoesNotThrow(() -> PythonBoundaryStaticStage.requireScope(PythonBoundaryStaticStage.Kind.MONTHLY_FIXTURE_WHOLE_MODULE, manifest));
    }
    @Test void unqualifiedPython311CannotClaimTheObservedPython313FixtureScope() throws IOException {
        var manifest = whole("3.11", true, 0);
        assertThrows(IOException.class, () -> PythonBoundaryStaticStage.requireScope(PythonBoundaryStaticStage.Kind.MONTHLY_FIXTURE_WHOLE_MODULE, manifest));
    }
    @Test void incompleteStaticProcessCannotClaimACompletedScope() throws IOException {
        var manifest = whole("3.13", false, 0);
        assertThrows(IOException.class, () -> PythonBoundaryStaticStage.requireScope(PythonBoundaryStaticStage.Kind.MONTHLY_FIXTURE_WHOLE_MODULE, manifest));
    }
    @Test void actualTypeErrorsRemainRed() throws IOException {
        var manifest = whole("3.13", true, 1);
        assertThrows(IOException.class, () -> PythonBoundaryStaticStage.requireScope(PythonBoundaryStaticStage.Kind.MONTHLY_FIXTURE_WHOLE_MODULE, manifest));
    }
    @Test void acceptsActualExtractedScopeWithoutWholeSdkModuleCredit() throws IOException {
        var manifest = sdk(false, "2.0.0", true);
        assertDoesNotThrow(() -> PythonBoundaryStaticStage.requireScope(PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED, manifest));
    }
    @Test void missingActualReadonlyFieldCannotClaimCompleteSdkScope() throws IOException {
        var manifest = sdk(false, "2.0.0", true);
        var incomplete = new PythonBoundaryStaticStage.ScopeManifest(manifest.schema(), manifest.kind(),
                manifest.wholeModuleCredit(), manifest.completed(), manifest.errorCount(), manifest.pythonVersion(),
                manifest.mypyVersion(), manifest.mcpVersion(), manifest.checkedDefinitions().stream()
                        .filter(range -> !range.symbol().equals("allow_private_semantic_snapshot_readonly")).toList(),
                manifest.signatureOnlyDefinitions(), manifest.sourceRefs(), manifest.dependencySourceRefs());
        assertThrows(IOException.class, () -> PythonBoundaryStaticStage.requireScope(PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED, incomplete));
    }
    @Test void extractedSdkCannotClaimWholeModuleCredit() throws IOException {
        var manifest = sdk(true, "2.0.0", true);
        assertThrows(IOException.class, () -> PythonBoundaryStaticStage.requireScope(PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED, manifest));
    }
    @Test void sdkSignatureDependencyPinsCannotBeOmitted() throws IOException {
        var manifest = sdk(false, "2.0.0", false);
        assertThrows(IOException.class, () -> PythonBoundaryStaticStage.requireScope(PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED, manifest));
    }
    @Test void differentSdkSignaturesCannotUseTheOldScopeQualification() throws IOException {
        var manifest = sdk(false, "1.0.0", true);
        assertThrows(IOException.class, () -> PythonBoundaryStaticStage.requireScope(PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED, manifest));
    }
    @Test void actualSignatureFileDriftIsRejected() throws IOException {
        var manifest = sdk(false, "2.0.0", true);
        Files.writeString(Path.of(manifest.dependencySourceRefs().getFirst().path()), "changed installed signature");
        assertThrows(IOException.class, () -> PythonBoundaryStaticStage.requireScope(PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED, manifest));
    }
    @Test void integerTokensAndRequiredManifestFieldsStayStrict() throws IOException {
        var manifest = whole("3.13", true, 0);
        String raw = ControlBuild.strictMapper().writeValueAsString(manifest);
        for (String invalid : List.of(raw.replace("\"error_count\":0", "\"error_count\":0.0"),
                raw.replace("\"error_count\":0", "\"error_count\":false"),
                raw.replace("\"completed\":true,", ""), raw.replace("\"completed\":true", "\"completed\":true,\"extra\":1"))) {
            assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(invalid, PythonBoundaryStaticStage.ScopeManifest.class));
        }
        var actual = new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "2026-10-22T00:00:00Z",
                "2026-10-22T00:00:01Z", ControlCi.PipelineState.RED, "expected incomplete fixture", null, null, null, null, null, null, List.of(), null,
                null, null, null, ControlCi.ExecutionPurpose.HOSTED_CI, null, ControlCi.initialStages());
        String actualRaw = ControlBuild.strictMapper().writeValueAsString(actual);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(
                actualRaw.replace(ControlCi.ACTUAL_SCHEMA, "xar.java-control-CI-actual/v1"), ControlCi.Receipt.class));
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(
                actualRaw.replace(",\"python_static_receipt_refs\":[]", ""), ControlCi.Receipt.class));
    }
    @Test void consumesActualPytestCasesAndZeroTerminalCounters() throws IOException {
        Path report = root.resolve("actual.xml");
        Files.writeString(report, "<testsuites><testsuite tests=\"2\" failures=\"0\" errors=\"0\" skipped=\"0\"><testcase name=\"first\"/><testcase name=\"second\"/></testsuite></testsuites>");
        assertDoesNotThrow(() -> PythonBoundaryStaticStage.requireSuccessfulPytest(report));
    }
    @Test void zeroExitCannotMakeSkippedPytestCasesPass() throws IOException {
        Path report = root.resolve("actual.xml");
        Files.writeString(report, "<testsuites><testsuite tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"1\"><testcase name=\"missing\"><skipped/></testcase></testsuite></testsuites>");
        assertThrows(IOException.class, () -> PythonBoundaryStaticStage.requireSuccessfulPytest(report));
    }
    @Test void fabricatedPytestCountersDoNotReplaceExecutedCases() throws IOException {
        Path report = root.resolve("actual.xml");
        Files.writeString(report, "<testsuites><testsuite tests=\"2\" failures=\"0\" errors=\"0\" skipped=\"0\"><testcase name=\"only-one\"/></testsuite></testsuites>");
        assertThrows(IOException.class, () -> PythonBoundaryStaticStage.requireSuccessfulPytest(report));
    }
}
