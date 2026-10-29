package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.HexFormat;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.time.Instant;
import java.time.Duration;
import java.math.BigDecimal;
import javax.tools.ToolProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real javac class origins plus deliberately synthetic compiler-list fixtures; no Maven success is invented. */
class ControlBuildCaptureTest {
    @TempDir Path temporary;
    private record Fixture(Path snapshot, Path module, Path build, Path output, Path inputList,
            Path createdList, Path source, List<ControlBuild.FileRef> sources) { }

    @Test void captureArgumentsCompileTestsPackageAndNeverRunVerify() {
        Path root = temporary.toAbsolutePath();
        var config = new ControlBuild.Config(root.resolve("source"), root.resolve("work"), root.resolve("lease.json"),
                "capture-fixture", "/root/build", null, Path.of(System.getProperty("java.home")), "3.10.0", 30,
                ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        var environment = Map.of("XAR_ORACLE_PYTHON", root.resolve("recorded/Scripts/python.exe").toString());
        List<String> arguments = ControlBuild.reactorCaptureArguments(config, root.resolve("settings.xml"), root.resolve("snapshot"), root.resolve("build"), environment);
        assertEquals("package", arguments.getLast()); assertTrue(arguments.contains("-DskipTests=true"));
        assertTrue(arguments.contains("-Dmaven.test.skip=false")); assertFalse(arguments.contains("verify"));
        assertFalse(arguments.stream().anyMatch(arg -> arg.equals("-Dmaven.test.skip=true")));
        assertEquals("verify", ControlBuild.reactorVerifyArguments(config, root.resolve("settings.xml"), root.resolve("snapshot"), root.resolve("build"), environment).getLast());
    }

    @Test void serviceBuildSelectsFrameworkMainAndToolsKeepTheirOriginalArgumentSequence() {
        Path root = temporary.toAbsolutePath(), settings = root.resolve("settings.xml"),
                snapshot = root.resolve("snapshot"), build = root.resolve("build");
        var environment = Map.of("XAR_ORACLE_PYTHON", root.resolve("recorded/Scripts/python.exe").toString());
        var service = mainSelectionConfig(root, ControlBuild.TargetKind.SERVICE_FAST_JAR);
        var tools = mainSelectionConfig(root, ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME);
        String selector = "-Dquarkus.package.main-class=io.quarkus.runner.GeneratedMain";
        var serviceVerify = ControlBuild.reactorVerifyArguments(service, settings, snapshot, build, environment);
        var serviceCapture = ControlBuild.reactorCaptureArguments(service, settings, snapshot, build, environment);
        var toolsVerify = ControlBuild.reactorVerifyArguments(tools, settings, snapshot, build, environment);
        var toolsCapture = ControlBuild.reactorCaptureArguments(tools, settings, snapshot, build, environment);
        for (var command : List.of(serviceVerify, serviceCapture))
            assertEquals(1, command.stream().filter(selector::equals).count());
        assertEquals(toolsVerify, serviceVerify.stream().filter(argument -> !argument.equals(selector)).toList());
        assertEquals(toolsCapture, serviceCapture.stream().filter(argument -> !argument.equals(selector)).toList());
        assertFalse(toolsVerify.stream().anyMatch(argument -> argument.startsWith("-Dquarkus.package.main-class")));
        assertFalse(toolsCapture.stream().anyMatch(argument -> argument.startsWith("-Dquarkus.package.main-class")));
    }

    @Test void completedServiceMainReplaysNewAndHistoricalShapesOnlyAsExactData() throws IOException {
        Path root = temporary.toAbsolutePath(), settings = root.resolve("settings.xml"),
                snapshot = root.resolve("snapshot"), build = root.resolve("build");
        var service = mainSelectionConfig(root, ControlBuild.TargetKind.SERVICE_FAST_JAR);
        var environment = Map.of("XAR_ORACLE_PYTHON", root.resolve("recorded/Scripts/python.exe").toString());
        String selector = "-Dquarkus.package.main-class=io.quarkus.runner.GeneratedMain";
        var verify = ControlBuild.reactorVerifyArguments(service, settings, snapshot, build, environment);
        var capture = ControlBuild.reactorCaptureArguments(service, settings, snapshot, build, environment);
        // Synthetic historical-shape DATA: removing only the new property preserves the pre-selector producer.
        for (var current : List.of(verify, capture)) {
            var historical = current.stream().filter(argument -> !argument.equals(selector)).toList();
            assertEquals(current, ControlBuild.completedServiceMainArguments(service.targetKind(), current, current));
            assertEquals(historical, ControlBuild.completedServiceMainArguments(service.targetKind(), current, historical));
            for (String invalid : List.of("-Dquarkus.package.main-class=", "-Dquarkus.package.main-class=finite-first-live",
                    selector + "-unknown", "-Dquarkus.package.main-class", "-Dquarkus.main=io.quarkus.runner.GeneratedMain")) {
                var changed = new ArrayList<>(current); changed.set(changed.indexOf(selector), invalid);
                assertThrows(IOException.class, () -> ControlBuild.completedServiceMainArguments(service.targetKind(), current, changed));
            }
            var duplicate = new ArrayList<>(current); duplicate.add(selector);
            var misplaced = new ArrayList<>(current); misplaced.remove(selector); misplaced.add(selector);
            var unrelated = new ArrayList<>(historical); unrelated.set(unrelated.indexOf("-Dck3.build.root=" + build), "-Dck3.build.root=drift");
            for (var changed : List.of(duplicate, misplaced, unrelated))
                assertThrows(IOException.class, () -> ControlBuild.completedServiceMainArguments(service.targetKind(), current, changed));
            assertThrows(IOException.class, () -> ControlBuild.completedServiceMainArguments(ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, current, current));
        }
        assertEquals(capture, ControlBuild.completedCaptureArguments(service, settings, snapshot, build, capture));
        var historicalCapture = capture.stream().filter(argument -> !argument.equals(selector)).toList();
        assertEquals(historicalCapture, ControlBuild.completedCaptureArguments(service, settings, snapshot, build, historicalCapture));
        var wrongCapture = new ArrayList<>(capture); wrongCapture.add(selector);
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(service, settings, snapshot, build, wrongCapture));
    }

    private ControlBuild.Config mainSelectionConfig(Path root, ControlBuild.TargetKind target) {
        return new ControlBuild.Config(root.resolve("source"), root.resolve("work"), root.resolve("lease.json"),
                "main-selection", "/root/build", null, Path.of(System.getProperty("java.home")), "3.10.0", 30,
                target, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
    }

    @Test void completedCaptureUsesItsExactRecordedPythonWithoutCurrentEnvironment() throws IOException {
        Path root = temporary.toAbsolutePath();
        var config = new ControlBuild.Config(root.resolve("source"), root.resolve("work"), root.resolve("lease.json"),
                "recorded-capture", "/root/build", null, Path.of(System.getProperty("java.home")), "3.10.0", 30,
                ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023);
        Path settings = root.resolve("settings.xml"), snapshot = root.resolve("snapshot"), build = root.resolve("build");
        String historicalPython = root.resolve("recorded environment/Scripts/python.exe").toString();
        List<String> original = ControlBuild.reactorCaptureArguments(config, settings, snapshot, build,
                Map.of("XAR_ORACLE_PYTHON", historicalPython));
        byte[] wire = ControlBuild.strictMapper().writeValueAsBytes(original);
        List<String> decoded = ControlBuild.strictMapper().readValue(wire,
                new com.fasterxml.jackson.core.type.TypeReference<List<String>>() { });
        assertEquals(original, ControlBuild.completedCaptureArguments(config, settings, snapshot, build, decoded));
        assertTrue(original.contains("-Dxar.rootContext.pythonExecutable=" + historicalPython));
        assertThrows(IllegalArgumentException.class,
                () -> ControlBuild.reactorCaptureArguments(config, settings, snapshot, build, Map.of()));
        List<String> duplicate = new ArrayList<>(original);
        duplicate.add("-Dxar.rootContext.pythonExecutable=" + historicalPython);
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, duplicate));
        List<String> missing = original.stream().filter(arg -> !arg.startsWith("-Dxar.rootContext.pythonExecutable=")).toList();
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, missing));
        for (String invalid : List.of("", "relative/python.exe", historicalPython + "\n")) {
            List<String> changed = original.stream().map(arg -> arg.startsWith("-Dxar.rootContext.pythonExecutable=")
                    ? "-Dxar.rootContext.pythonExecutable=" + invalid : arg).toList();
            assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, changed));
        }
        for (String originalArgument : List.of("package", "-DskipTests=true", "-Dmaven.test.skip=false",
                "-Dck3.build.root=" + build, "-f")) {
            List<String> changed = new ArrayList<>(original); changed.set(changed.indexOf(originalArgument), "drift");
            assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, changed));
        }
    }

    @Test void fullR7CaptureOmitsExecutionFixturesAndReplaysOnlyItsExplicitNoRunPolicy() throws IOException {
        Path root=temporary.toAbsolutePath(),settings=root.resolve("settings.xml"),snapshot=root.resolve("snapshot"),build=root.resolve("build");
        var config=new ControlBuild.Config(root.resolve("source"),root.resolve("work"),root.resolve("lease.json"),
                "capture-r7","/root/build",null,Path.of(System.getProperty("java.home")),"3.10.0",30,
                ControlBuild.TargetKind.SERVICE_FAST_JAR,ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261025_R7);
        String python=root.resolve("recorded/Scripts/python.exe").toString();
        // Invalid execution inputs cannot become a capture prerequisite; no test or Native fixture is executed.
        var environment=Map.of("XAR_ORACLE_PYTHON",python,"XAR_FULL_PARITY_CURRENT_INPUTS","not-an-actual-input",
                "XAR_FULL_PARITY_CURRENT_INPUTS_SHA256","invalid");
        var arguments=ControlBuild.reactorCaptureArguments(config,settings,snapshot,build,environment);
        String marker="-Dxar.control.capture.commandPolicy=COMPILE_ONLY_WITHOUT_TEST_INPUTS";
        assertEquals(1,arguments.stream().filter(marker::equals).count());
        assertEquals("package",arguments.getLast());assertTrue(arguments.contains("-Dmaven.test.skip=false"));
        assertTrue(arguments.contains("-DskipTests=true"));assertFalse(arguments.contains("verify"));
        assertFalse(arguments.stream().anyMatch(value->value.startsWith("-Dxar.fullParity.")||value.startsWith("-Dxar.holyOrder.")));
        assertEquals(arguments,ControlBuild.completedCaptureArguments(config,settings,snapshot,build,arguments));
        assertThrows(IllegalArgumentException.class,()->ControlBuild.reactorVerifyArguments(config,settings,snapshot,build,environment));
        var duplicate=new ArrayList<>(arguments);duplicate.add(marker);
        var contaminated=new ArrayList<>(arguments);contaminated.add("-Dxar.fullParity.current.inputs=unbound");
        var unknown=new ArrayList<>(arguments);unknown.set(unknown.indexOf(marker),marker+"-unknown");
        var missing=arguments.stream().filter(value->!value.equals(marker)).toList();
        for(var changed:List.of(duplicate,contaminated,unknown,missing))
            assertThrows(IOException.class,()->ControlBuild.completedCaptureArguments(config,settings,snapshot,build,changed));
    }

    @Test void legacyFullParityCaptureReplaysOnlyItsOriginalRecordedFixtureCommand() throws IOException {
        Path root=temporary.toAbsolutePath(),settings=root.resolve("settings.xml"),snapshot=root.resolve("snapshot"),build=root.resolve("build");
        var config=new ControlBuild.Config(root.resolve("source"),root.resolve("work"),root.resolve("lease.json"),
                "legacy-capture","/root/build",null,Path.of(System.getProperty("java.home")),"3.10.0",30,
                ControlBuild.TargetKind.SERVICE_FAST_JAR,ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024);
        String python=root.resolve("recorded/Scripts/python.exe").toString(),repository=root.resolve("recorded-repository").toString();
        // Synthetic immutable recorded values exercise historical command reconstruction, never fixture or Maven qualification.
        var fixtures=java.util.Arrays.stream(FullParityOracleBindings.FixtureRole.values()).map(role->
                new FullParityOracleBindings.BoundFixture(role,new ControlBuild.FileRef(root.resolve(role.name()+".json").toString(),1,"0".repeat(64)))).toList();
        var bindings=new FullParityOracleBindings.Bindings(python,repository,Path.of(repository).resolve(FullParityOracleBindings.NATIVE_RELATIVE).toString(),"0".repeat(64),fixtures);
        var original=new ArrayList<>(ControlBuild.reactorVerifyArguments(config,settings,snapshot,build,python,bindings));
        assertEquals("verify",original.removeLast());original.add("-Dmaven.test.skip=false");original.add("-DskipTests=true");original.add("package");
        assertEquals(original,ControlBuild.completedCaptureArguments(config,settings,snapshot,build,original));
        var changed=new ArrayList<>(original);changed.removeIf(value->value.startsWith("-Dxar.m3.timeline.nativeWholeSha256="));
        assertThrows(IOException.class,()->ControlBuild.completedCaptureArguments(config,settings,snapshot,build,changed));
    }

    @Test void explicitMavenOverrideIsRefusedBeforeCaptureStartsAnyProcess() {
        Path root = temporary.toAbsolutePath();
        var config = new ControlBuild.Config(root.resolve("source"), root.resolve("work"), root.resolve("lease.json"),
                "capture-fixture", "/root/build", root.resolve("mvn.cmd"), Path.of(System.getProperty("java.home")), "3.10.0", 30,
                ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        assertThrows(IOException.class, () -> ControlBuild.buildCapture(config));
        assertFalse(Files.exists(root.resolve("work")));
    }

    @Test void actualOuterAndInnerClassSourceFilesBindToOneExactModuleTestSource() throws Exception {
        Fixture f = fixture(); var manifest = collect(f, f.sources());
        assertEquals(ControlBuild.CaptureTestState.NOT_RUN, manifest.tests()); assertEquals(1, manifest.modules().size());
        assertEquals(1, manifest.notRunTests().size()); assertEquals(2, manifest.notRunTests().getFirst().compiledClassRefs().size());
        assertEquals(ControlBuild.FileRef.measure(f.source()), manifest.notRunTests().getFirst().sourceRef());
        assertEquals(ControlBuild.CaptureTestState.NOT_RUN, manifest.notRunTests().getFirst().state());
        assertEquals(f.output().toRealPath().toString(), manifest.modules().getFirst().classOutputRoot());
        manifest.modules().getFirst().compilerInputsRef().verify(); manifest.modules().getFirst().compilerCreatedFilesRef().verify();
    }

    @Test void missingCompilerInputAndPinnedSourceWithNoBinaryAreRejected() throws Exception {
        Fixture f = fixture(); Files.writeString(f.inputList(), f.module().resolve("src/test/java/sample/Other.java") + "\n");
        assertThrows(IOException.class, () -> collect(f, f.sources()));
        Path empty = f.source().resolveSibling("Empty.java"); Files.writeString(empty, "package sample;\n");
        Files.writeString(f.inputList(), f.source() + "\n" + empty + "\n");
        List<ControlBuild.FileRef> sources = new ArrayList<>(f.sources()); sources.add(ControlBuild.FileRef.measure(empty));
        assertThrows(IOException.class, () -> collect(f, sources));
    }

    @Test void compilerCreatedPathOutsideModuleClassRootIsRejected() throws Exception {
        Fixture f = fixture(); Files.writeString(f.createdList(), "../foreign/FixtureTest.class\n");
        assertThrows(IOException.class, () -> collect(f, f.sources()));
    }

    @Test void unlistedActualBinaryCannotBeBorrowedFromAnOutputDirectory() throws Exception {
        Fixture f = fixture(); Files.copy(f.output().resolve("sample/FixtureTest.class"), f.output().resolve("sample/Unlisted.class"));
        assertThrows(IOException.class, () -> collect(f, f.sources()));
    }

    @Test void duplicatedCompilerInputCannotMaskMissingSourceOrInflateOrigins() throws Exception {
        Fixture f = fixture(); Files.writeString(f.inputList(), f.source() + "\n" + f.source() + "\n");
        assertThrows(IOException.class, () -> collect(f, f.sources()));
    }

    @Test void normalAndCaptureReadersRejectEachOthersSchemasAndMissingEvidence() throws Exception {
        Path capture = temporary.resolve("capture.json");
        Files.writeString(capture, "{\"schema\":\"" + ControlBuild.CAPTURE_SCHEMA + "\"}");
        assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(capture));
        Path normal = temporary.resolve("normal.json");
        Files.writeString(normal, "{\"schema\":\"" + ControlBuild.SCHEMA + "\"}");
        assertThrows(IOException.class, () -> ControlBuild.acceptedCaptureReceipt(normal));
    }

    @Test void genuineFullG2RedReceiptUsesTheProductionSerializerWithinTheSharedBound() throws Exception {
        ControlBuild.BuildReceipt original = genuineFullG2RedReceipt();
        byte[] encoded = ControlBuild.buildReceiptBytes(original);
        assertTrue(encoded.length > (1 << 20));
        assertTrue(encoded.length <= ControlBuild.BUILD_RECEIPT_MAX_BYTES);
        Path output = temporary.resolve("actual-red-envelope.json"); Files.write(output, encoded);
        assertEquals(original, ControlBuild.readBuildReceiptEnvelope(output));
        // Original RED/native failure remains RED; accepting the larger envelope grants no qualification.
        IOException completed = assertThrows(IOException.class,
                () -> ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(output)));
        assertEquals("Build receipt did not establish current-machine complete qualification", completed.getMessage());
        assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(output));
        assertThrows(IOException.class, () -> ControlBuild.acceptedCaptureReceipt(output));
        assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedCaptureReceipt(ControlBuild.FileRef.measure(output)));
    }

    @Test void allBuildAndCaptureBoundariesRejectTheFirstByteBeyondTwoMiB() throws Exception {
        assertEquals(2 << 20, ControlBuild.BUILD_RECEIPT_MAX_BYTES);
        ControlBuild.BuildReceipt original = genuineFullG2RedReceipt();
        ObjectNode oversized = (ObjectNode) ControlBuild.strictMapper().valueToTree(original);
        // Synthetic error-text padding preserves the genuine source/native fields and cannot claim PASS.
        oversized.put("error", "x".repeat(ControlBuild.BUILD_RECEIPT_MAX_BYTES));
        ControlBuild.BuildReceipt large = ControlBuild.strictMapper().treeToValue(oversized, ControlBuild.BuildReceipt.class);
        assertEquals("RED", large.status());
        assertEquals("Build receipt exceeds finite 2 MiB byte limit",
                assertThrows(IOException.class, () -> ControlBuild.buildReceiptBytes(large)).getMessage());
        Path output = temporary.resolve("oversized-envelope.json");
        Files.write(output, new byte[ControlBuild.BUILD_RECEIPT_MAX_BYTES + 1]);
        assertEquals("JSON input exceeds limit",
                assertThrows(IOException.class, () -> ControlBuild.readBuildReceiptEnvelope(output)).getMessage());
        assertEquals("JSON input exceeds limit",
                assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(output))).getMessage());
        assertEquals("JSON input exceeds limit",
                assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(output)).getMessage());
        assertEquals("JSON input exceeds limit",
                assertThrows(IOException.class, () -> ControlBuild.acceptedCaptureReceipt(output)).getMessage());
        assertEquals("JSON input exceeds limit",
                assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedCaptureReceipt(ControlBuild.FileRef.measure(output))).getMessage());
    }


    @Test void completedCaptureAuthorityUsesTheOriginalWindowWhileLiveAuthorityExpires() throws Exception {
        CaptureLeaseFixture f = captureLeaseFixture(false);
        // A real native terminal and synthetic bounded lease test this shared production boundary only.
        // No complete Maven PASS/capture receipt is created or claimed by this unit fixture.
        var window = ControlBuild.completedLeaseWindow(f.releaseRef(), WindowsJobProcess.currentMachineId(), f.completed());
        ControlBuild.requireCompletedNativeWindow(f.terminal(), window.opened(), f.completed());
        ControlBuild.readLeaseAt(f.config(), WindowsJobProcess.currentMachineId(), f.completed());
        assertThrows(IOException.class, () -> ControlBuild.readLeaseAt(f.config(), WindowsJobProcess.currentMachineId(), Instant.now()));
        assertThrows(IOException.class, () -> ControlBuild.completedLeaseWindow(f.releaseRef(),
                WindowsJobProcess.currentMachineId(), window.opened().minusNanos(1)));
        assertThrows(IOException.class, () -> ControlBuild.completedLeaseWindow(f.releaseRef(),
                WindowsJobProcess.currentMachineId(), window.review()));
        assertThrows(IOException.class, () -> ControlBuild.completedLeaseWindow(f.releaseRef(),
                WindowsJobProcess.currentMachineId(), Instant.now().plusSeconds(60)));
    }

    @Test void typedCaptureLeaseChecksItsOriginalOverrideAndKeepsEveryPolicyGuard() throws Exception {
        CaptureLeaseFixture f = captureLeaseFixture(true);
        ControlBuild.readLeaseAt(f.config(), WindowsJobProcess.currentMachineId(), f.completed());
        assertThrows(IOException.class, () -> ControlBuild.readLeaseAt(f.config(), WindowsJobProcess.currentMachineId(), Instant.now()));
        var mapper = ControlBuild.strictMapper();
        ObjectNode original = (ObjectNode) mapper.readTree(Files.readAllBytes(Path.of(f.releaseRef().path())));
        List<ObjectNode> changed = new ArrayList<>();
        ObjectNode writer = original.deepCopy(); writer.put("owner_task", "/root/another-writer"); changed.add(writer);
        ObjectNode machine = original.deepCopy(); machine.put("machine_id", "another-machine"); changed.add(machine);
        ObjectNode scratch = original.deepCopy(); scratch.put("temporary_root", temporary.resolve("wrong-scratch").toString()); changed.add(scratch);
        ObjectNode missingCap = original.deepCopy(); ((ObjectNode) missingCap.get("parts")).remove("build"); changed.add(missingCap);
        ObjectNode override = original.deepCopy();
        var firstOverride = override.get("quota_overrides").properties().iterator().next().getValue();
        ((ObjectNode) firstOverride).put("review_at_utc", f.completed().toString()); changed.add(override);
        ObjectNode source = original.deepCopy();
        var sourceOverride = source.get("quota_overrides").properties().iterator().next().getValue();
        ((ObjectNode) sourceOverride.get("source_ref")).put("sha256", "0".repeat(64)); changed.add(source);
        for (ObjectNode mutation : changed) {
            Files.write(Path.of(f.releaseRef().path()), mapper.writeValueAsBytes(mutation));
            assertThrows(IOException.class, () -> ControlBuild.readLeaseAt(f.config(), WindowsJobProcess.currentMachineId(), f.completed()));
        }
        Files.write(Path.of(f.releaseRef().path()), mapper.writeValueAsBytes(original));
        ControlBuild.readLeaseAt(f.config(), WindowsJobProcess.currentMachineId(), f.completed());
    }

    @Test void completedCaptureChronologyRejectsForgedNativeBirthAndElapsed() throws Exception {
        CaptureLeaseFixture f = captureLeaseFixture(false);
        var window = ControlBuild.completedLeaseWindow(f.releaseRef(), WindowsJobProcess.currentMachineId(), f.completed());
        var mapper = ControlBuild.strictMapper();
        ObjectNode wrongBirth = mapper.valueToTree(f.terminal());
        ((ObjectNode) wrongBirth.get("identity")).put("creation_filetime_decimal", "1");
        var beforeLease = mapper.treeToValue(wrongBirth, WindowsJobProcess.CommandResult.class);
        assertThrows(IOException.class, () -> ControlBuild.requireCompletedNativeWindow(beforeLease, window.opened(), f.completed()));
        ObjectNode wrongElapsed = mapper.valueToTree(f.terminal());
        wrongElapsed.put("elapsed_seconds", 86400.0);
        var longerThanLease = mapper.treeToValue(wrongElapsed, WindowsJobProcess.CommandResult.class);
        assertThrows(IOException.class, () -> ControlBuild.requireCompletedNativeWindow(longerThanLease, window.opened(), f.completed()));
        assertTrue(f.terminal().passed()); assertEquals(0, f.terminal().accounting().activeProcesses());
    }

    private record CaptureLeaseFixture(ControlBuild.Config config, ControlBuild.FileRef releaseRef,
            Instant completed, WindowsJobProcess.CommandResult terminal) { }

    private CaptureLeaseFixture captureLeaseFixture(boolean typed) throws Exception {
        var mapper = ControlBuild.strictMapper();
        Path nativeRoot = Files.createDirectories(temporary.resolve(typed ? "typed-native" : "manual-native"));
        Path command = Path.of(System.getenv("SystemRoot"), "System32/cmd.exe");
        Path batch = nativeRoot.resolve("exit-zero.cmd"); Files.writeString(batch, "@echo off\r\nexit /b 0\r\n");
        Instant opened = Instant.now().minusSeconds(1);
        WindowsJobProcess.CommandResult terminal;
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(command,
                List.of("/d", "/c", batch.toString()), nativeRoot, Map.copyOf(System.getenv()),
                nativeRoot.resolve("stdout.log"), nativeRoot.resolve("stderr.log"), 64L << 20))) {
            terminal = child.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
        }
        assertTrue(terminal.passed()); assertEquals(0, terminal.accounting().activeProcesses());
        Instant completed = Instant.now(); Instant review = completed.plusNanos(1);
        Path sourceRoot = Files.createDirectories(temporary.resolve(typed ? "typed-source" : "manual-source"));
        Path work = Files.createDirectories(temporary.resolve(typed ? "typed-work" : "manual-work"));
        Path scratch = Files.createDirectories(work.resolve("scratch"));
        Path policyPath = temporary.resolve(typed ? "typed-policy.json" : "manual-policy.json");
        String policyJson = "{\"schema\":\"xar-storage-retention-policy-v1\",\"policy_version\":\"1.0.0\",\"capacity\":{"
                + "\"safety_floor_bytes\":1,\"safety_ceiling_bytes\":1,\"safety_volume_fraction\":0.001,"
                + "\"default_project_quota_ceiling_bytes\":1048576,\"default_project_quota_volume_fraction\":0.01,\"quota_override_max_hours\":24}}";
        Files.writeString(policyPath, policyJson);
        Path releasePath = temporary.resolve(typed ? "typed-capture-release.json" : "manual-capture-release.json");
        String owner = "/root/capture-test", machine = WindowsJobProcess.currentMachineId();
        Map<String, Long> parts = Map.of("m2", 1L << 20, "build", 1L << 20, "tools", 1L << 20,
                "scratch", 1L << 20, "artifacts", 1L << 20, "metadata_logs", 1L << 20);
        if (typed) {
            var policy = new CiBootstrap.Policy(1, 1, new BigDecimal("0.001"), 1L << 20, new BigDecimal("0.01"), 24);
            Path overridePath = temporary.resolve("typed-override-source.json");
            Files.writeString(overridePath, "synthetic finite lease regression; no production authority");
            ControlBuild.FileRef overrideRef = ControlBuild.FileRef.measure(overridePath);
            var override = new CiBootstrap.QuotaOverride("test-owner", owner, "exercise original override clock", 8L << 30,
                    review.toString(), new CiBootstrap.FilePin(overrideRef.path(), overrideRef.bytes(), overrideRef.sha256()));
            var volume = CiBootstrap.calculate(policy, 16L << 30, 4L << 30, 1L << 30, 0, 1, 1L << 30,
                    override, opened, review);
            var release = new ControlBuild.CapacityRelease("xar.java-control.capacity-release/v1", machine,
                    opened.toString(), review.toString(), "RELEASED", owner, ControlBuild.FileRef.measure(policyPath),
                    List.of(temporary.toAbsolutePath().toString()), scratch.toString(), parts,
                    Map.of(work.getRoot().toString(), volume), Map.of(work.getRoot().toString(), override), 64L << 20, 32L << 20);
            Files.write(releasePath, mapper.writeValueAsBytes(release));
        } else {
            ObjectNode release = mapper.createObjectNode();
            release.put("schema", "xar.java-phase1.manual-capacity-release/v1"); release.put("machine_id", machine);
            release.put("status", "RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE"); release.put("single_Maven_writer", owner);
            release.put("observed_at_utc", opened.toString()); release.put("review_at_utc", review.toString());
            release.putArray("approved_output_roots").add(temporary.toAbsolutePath().toString());
            release.put("Maven_repository", work.resolve("m2").toString()); release.put("build_root", work.resolve("build").toString());
            release.put("temporary_root", scratch.toString()); release.set("parts", mapper.valueToTree(parts));
            release.set("policy_ref", mapper.valueToTree(ControlBuild.FileRef.measure(policyPath)));
            ObjectNode volume = release.putObject("volumes").putObject(work.getRoot().toString());
            volume.put("required_free", 3); volume.put("this_write_peak", 1); volume.put("other_unspent_reservations", 0);
            volume.put("system_growth_reserve", 1); volume.put("safety_reserve", 1);
            volume.put("current_project_usage_conservative_upper", 1); volume.put("effective_project_quota", 100);
            release.put("test_RAM_joint_hard_bytes", 64L << 20); release.put("Maven_heap_bytes", 32L << 20);
            Files.write(releasePath, mapper.writeValueAsBytes(release));
        }
        var config = new ControlBuild.Config(sourceRoot, work, releasePath, "capture-lease-test", owner,
                null, Path.of(System.getProperty("java.home")), "3.10.0", 30,
                ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        return new CaptureLeaseFixture(config, ControlBuild.FileRef.measure(releasePath), completed, terminal);
    }

    private ControlBuild.BuildReceipt genuineFullG2RedReceipt() throws Exception {
        byte[] raw;
        try (InputStream input = ControlBuildCaptureTest.class.getResourceAsStream("/build-receipts/full-g2-capture01-red.json")) {
            if (input == null) throw new IOException("Exact portable original capture failure fixture required");
            raw = input.readNBytes(ControlBuild.BUILD_RECEIPT_MAX_BYTES + 1);
        }
        assertEquals(1201708, raw.length);
        assertEquals("c2423f9f849244232fe4a592113c01a3fbb45af77436952c5a7157da5fa93c42",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        var failure = ControlBuild.strictMapper().readTree(raw);
        assertEquals("xar.java-control-test-compiled-capture-failure/v1", failure.path("schema").textValue());
        // This is the source machine's recorded negative evidence, never a claim about the current machine.
        assertEquals("xenoamess-full-tower-eb9d2c1186", failure.path("machine_id").textValue());
        ControlBuild.BuildReceipt receipt = ControlBuild.strictMapper().treeToValue(failure.path("terminal"), ControlBuild.BuildReceipt.class);
        assertEquals("RED", receipt.status()); assertFalse(receipt.mavenResult().passed());
        assertEquals(1931, receipt.sourcePins().size()); assertEquals(1931, receipt.compiledSourcePins().size());
        return receipt;
    }

    private ControlBuild.TestCompilationManifest collect(Fixture f, List<ControlBuild.FileRef> refs) throws IOException {
        return ControlBuild.collectTestCompilation("synthetic-compiler-fixture", f.snapshot(), f.build(), refs);
    }

    @Test void realCollectorAndCodecKeepThirtyFourModulesAnd2209NotRunSources() throws Exception {
        // Real javac outputs with explicit synthetic compiler lists; no Maven success is claimed.
        Path root = Files.createTempDirectory(temporary, "capture-cohort-").toAbsolutePath();
        Path template = Files.createDirectories(root.resolve("template"));
        Path binaries = Files.createDirectories(root.resolve("template-classes"));
        List<String> arguments = new ArrayList<>(List.of("--release", "21", "-g:source",
                "-encoding", "UTF-8", "-proc:none", "-d", binaries.toString()));
        for (int index = 0; index < 65; index++) {
            Path source = template.resolve("CaptureCase" + index + ".java");
            Files.writeString(source, "package sample; class CaptureCase" + index + " { }\n");
            arguments.add(source.toString());
        }
        var compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) throw new IllegalStateException("Actual JDK compiler required");
        assertEquals(0, compiler.run(null, null, null, arguments.toArray(String[]::new)));
        Path snapshot = Files.createDirectories(root.resolve("source"));
        Path build = Files.createDirectories(root.resolve("build"));
        List<ControlBuild.FileRef> pins = new ArrayList<>();
        StringBuilder modules = new StringBuilder();
        for (int module = 0; module < 34; module++) {
            String artifact = "capture-module-" + module;
            Path home = snapshot.resolve(artifact), sourceBase = home.resolve("src/test/java/sample");
            Files.createDirectories(sourceBase); modules.append("<module>").append(artifact).append("</module>");
            Path pom = home.resolve("pom.xml");
            Files.writeString(pom, "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion><artifactId>"
                    + artifact + "</artifactId></project>");
            pins.add(ControlBuild.FileRef.measure(pom));
            Path output = Files.createDirectories(build.resolve(artifact + "/test-classes/sample"));
            Path status = Files.createDirectories(build.resolve(artifact + "/maven-status/maven-compiler-plugin/testCompile/default-testCompile"));
            List<String> inputs = new ArrayList<>(), created = new ArrayList<>();
            for (int index = 0; index < (module == 33 ? 64 : 65); index++) {
                String name = "CaptureCase" + index;
                Path source = sourceBase.resolve(name + ".java");
                Files.copy(template.resolve(name + ".java"), source);
                Files.copy(binaries.resolve("sample/" + name + ".class"), output.resolve(name + ".class"));
                pins.add(ControlBuild.FileRef.measure(source)); inputs.add(source.toString());
                created.add("sample/" + name + ".class");
            }
            Files.writeString(status.resolve("inputFiles.lst"), String.join("\n", inputs) + "\n");
            Files.writeString(status.resolve("createdFiles.lst"), String.join("\n", created) + "\n");
        }
        Path parent = snapshot.resolve("pom.xml");
        Files.writeString(parent, "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion><artifactId>capture-parent</artifactId><packaging>pom</packaging><modules>"
                + modules + "</modules></project>");
        pins.add(ControlBuild.FileRef.measure(parent));
        var actual = ControlBuild.collectTestCompilation(WindowsJobProcess.currentMachineId(), snapshot, build, pins);
        assertEquals(34, actual.modules().size()); assertEquals(2209, actual.notRunTests().size());
        assertEquals(ControlBuild.CaptureTestState.NOT_RUN, actual.tests());
        assertTrue(actual.notRunTests().stream().allMatch(row -> row.state() == ControlBuild.CaptureTestState.NOT_RUN));
        assertEquals(2209L, actual.notRunTests().stream().mapToLong(row -> row.compiledClassRefs().size()).sum());
        byte[] wire = ControlBuild.strictMapper().writeValueAsBytes(actual);
        assertTrue(wire.length <= (4 << 20));
        assertEquals(actual, ControlBuild.strictMapper().readValue(wire, ControlBuild.TestCompilationManifest.class));
    }

    private Fixture fixture() throws Exception {
        Path root = Files.createTempDirectory(temporary, "compiler-fixture-").toAbsolutePath();
        Path snapshot = Files.createDirectories(root.resolve("source")), module = Files.createDirectory(snapshot.resolve("module"));
        Path pom = module.resolve("pom.xml"); Files.writeString(pom, "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion><artifactId>fixture</artifactId></project>");
        Path source = module.resolve("src/test/java/sample/FixtureTest.java"); Files.createDirectories(source.getParent());
        Files.writeString(source, "package sample; class FixtureTest { static class Inner {} }\n");
        Path build = root.resolve("build"), output = Files.createDirectories(build.resolve("fixture/test-classes"));
        var compiler = ToolProvider.getSystemJavaCompiler(); if (compiler == null) throw new IllegalStateException("Actual JDK compiler required");
        assertEquals(0, compiler.run(null, null, null, "-g:source", "-d", output.toString(), source.toString()));
        Path status = Files.createDirectories(build.resolve("fixture/maven-status/maven-compiler-plugin/testCompile/default-testCompile"));
        Path inputs = status.resolve("inputFiles.lst"), created = status.resolve("createdFiles.lst");
        Files.writeString(inputs, source + "\n");
        List<String> binaries;
        try (var walk = Files.walk(output)) { binaries = walk.filter(Files::isRegularFile).map(file -> output.relativize(file).toString()).sorted(Comparator.naturalOrder()).toList(); }
        assertEquals(2, binaries.size()); Files.writeString(created, String.join("\n", binaries) + "\n");
        return new Fixture(snapshot, module, build, output, inputs, created, source,
                List.of(ControlBuild.FileRef.measure(pom), ControlBuild.FileRef.measure(source)));
    }
}
