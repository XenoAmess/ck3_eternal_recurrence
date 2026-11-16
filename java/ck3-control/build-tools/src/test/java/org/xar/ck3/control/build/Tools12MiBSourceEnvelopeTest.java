package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonProcessingException;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.parallel.Execution;
import org.junit.jupiter.api.parallel.ExecutionMode;

/** Source-only fixtures. No Maven, Own production, completed build, Native Job or CI qualification. */
@Execution(ExecutionMode.SAME_THREAD)
final class Tools12MiBSourceEnvelopeTest {
    private static final ControlBuild.SourceLimitProfile TOOLS = ControlBuild.SourceLimitProfile.TOOLS_20261116_12_MIB;
    private static final ControlBuild.SourceLimitProfile R8 = ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261116_R8;
    private static final ControlBuild.SourceLimitProfile R7 = ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261025_R7;
    private static final ControlBuild.SourceLimitProfile R6 = ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R6;
    @TempDir Path root;

    @Test void newProfilesKeepHistoricalWireAndEveryUnchangedEnvelope() throws Exception {
        var standard = ControlBuild.SourceLimitProfile.STANDARD_8_MIB;
        assertEquals(1000, standard.maxFiles()); assertEquals(8L << 20, standard.maxBytes());
        assertEquals(1000, TOOLS.maxFiles()); assertEquals(12L << 20, TOOLS.maxBytes()); assertEquals(1, TOOLS.maxReactorProjects());
        assertEquals(12L << 20, TOOLS.moduleSourceBytes("", "src")); assertEquals(8L << 20, TOOLS.moduleSourceBytes("", ".mvn"));
        assertFalse(TOOLS.completeG2()); assertFalse(TOOLS.fullParity()); assertFalse(TOOLS.currentParity());
        assertTrue(TOOLS.toolsRuntimeSources()); assertTrue(standard.toolsRuntimeSources()); assertFalse(R8.toolsRuntimeSources());
        assertEquals(6144, R8.maxFiles()); assertEquals(96L << 20, R8.maxBytes()); assertEquals(35, R8.maxReactorProjects());
        assertEquals(8L << 20, R6.moduleSourceBytes("build-tools", "src")); assertEquals(8L << 20, R7.moduleSourceBytes("build-tools", "src"));
        assertEquals(16L << 20, R6.moduleSourceBytes("local-service", "src")); assertEquals(13L << 20, R6.moduleSourceBytes("application", "src"));
        assertEquals(19L << 20, R7.moduleSourceBytes("local-service", "src")); assertEquals(14L << 20, R7.moduleSourceBytes("application", "src"));
        for (String module : CompleteSourceGraph.modules(CompleteSourceGraph.Profile.G2_FULL_PARITY_20261116_R8))
            for (String directory : List.of("src", ".mvn"))
                assertEquals(module.equals("build-tools") && directory.equals("src") ? 12L << 20 : R7.moduleSourceBytes(module, directory),
                        R8.moduleSourceBytes(module, directory), module + "/" + directory);
        var graph = CompleteSourceGraph.Profile.G2_FULL_PARITY_20261116_R8;
        assertEquals(CompleteSourceGraph.modules(CompleteSourceGraph.Profile.G2_FULL_PARITY_20261025_R7), CompleteSourceGraph.modules(graph));
        assertEquals(34, graph.childModules()); assertEquals(35, graph.reactorProjects());
        assertEquals(6144, graph.maxFiles()); assertEquals(96L << 20, graph.maxLogicalBytes()); assertEquals(112L << 20, graph.maxNativeBytes());
        assertEquals(16 << 20, graph.copyProofMaxBytes()); assertEquals(R8, graph.sourceLimitProfile());
        var mapper = ControlBuild.strictMapper();
        for (var profile : List.of(standard, R6, R7, TOOLS, R8))
            assertEquals(profile, mapper.readValue(mapper.writeValueAsBytes(profile), ControlBuild.SourceLimitProfile.class));
        assertEquals(graph, mapper.readValue(mapper.writeValueAsBytes(graph), CompleteSourceGraph.Profile.class));
        assertThrows(JsonProcessingException.class, () -> mapper.readValue("\"TOOLS_20261116_UNBOUNDED\"", ControlBuild.SourceLimitProfile.class));
    }

    @Test void bootstrapAndBuildProducerPinTheSameWholeTreeIncludingLargeFixedResourcesAndDotMvn() throws Exception {
        Path tools = tools();
        file(tools.resolve("src/main/java/Software.java"), "final class Software {}\n");
        file(tools.resolve("src/test/java/SoftwareTest.java"), "final class SoftwareTest {}\n");
        Path fixed = tools.resolve("src/test/resources/fixed-original.bin"); payload(fixed, (8L << 20) + 1);
        file(tools.resolve(".mvn/maven.config"), "-ntp\n"); file(tools.resolve("src/.source-marker"), "retained\n");
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(tools));
        var actual = ControlBuild.sourceManifest(tools, TOOLS);
        assertTrue(actual.contains(ControlBuild.FileRef.measure(fixed))); assertEquals(6, actual.size());
        assertEquals(actual, bootstrapPins(tools));
        assertEquals(TOOLS.name(), CiBootstrap.TOOLS_SOURCE_PROFILE);
        assertEquals(TOOLS.maxFiles(), CiBootstrap.TOOLS_SOURCE_MAX_FILES); assertEquals(TOOLS.maxBytes(), CiBootstrap.TOOLS_SOURCE_MAX_BYTES);
        assertEquals(ControlBuild.SourceState.MATCH, ControlBuild.postcheckSource(tools, actual, TOOLS).state());
        file(fixed, "changed actual fixed resource\n");
        assertEquals(ControlBuild.SourceState.MISMATCH, ControlBuild.postcheckSource(tools, actual, TOOLS).state());
    }

    @Test void exactAggregateTwelveMiBCeilingAndFirstExcessByteUseOnePhysicalPayload() throws Exception {
        Path tools = tools(), payload = tools.resolve("src/fixed.bin");
        payload(payload, TOOLS.maxBytes() - Files.size(tools.resolve("pom.xml")));
        var actual = ControlBuild.sourceManifest(tools, TOOLS);
        assertEquals(TOOLS.maxBytes(), actual.stream().mapToLong(ControlBuild.FileRef::bytes).sum());
        assertEquals(actual, bootstrapPins(tools));
        Files.write(payload, new byte[]{1}, StandardOpenOption.APPEND);
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(tools, TOOLS));
        assertThrows(IOException.class, () -> CiBootstrap.sourcePins(tools));
    }

    @Test void dotMvnRetainsItsHistoricalEightMiBSubtreeLimit() throws Exception {
        Path tools = tools(); payload(tools.resolve(".mvn/fixed.bin"), (8L << 20) + 1);
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(tools, TOOLS));
        assertThrows(IOException.class, () -> CiBootstrap.sourcePins(tools));
    }

    @Test void thousandFileEnvelopeCountsThePomAndDoesNotDropTheFirstExcessFile() throws Exception {
        Path tools = tools();
        for (int index = 0; index < 999; index++) file(tools.resolve("src/fixed-" + index), "x");
        var actual = ControlBuild.sourceManifest(tools, TOOLS); assertEquals(1000, actual.size()); assertEquals(actual, bootstrapPins(tools));
        file(tools.resolve("src/first-excess"), "x");
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(tools, TOOLS));
        assertThrows(IOException.class, () -> CiBootstrap.sourcePins(tools));
    }

    @Test void toolsEnvelopeRequiresItsOneCanonicalProjectAndCanonicalSourceRoots() throws Exception {
        Path tools = tools();
        for (String extra : List.of("<modules><module>other</module></modules>",
                "<build><sourceDirectory>../outside</sourceDirectory></build>",
                "<build><testSourceDirectory>../outside</testSourceDirectory></build>",
                "<build><plugins><plugin><artifactId>build-helper-maven-plugin</artifactId></plugin></plugins></build>")) {
            file(tools.resolve("pom.xml"), project("ck3-control-build-tools", extra));
            assertThrows(IOException.class, () -> ControlBuild.sourceManifest(tools, TOOLS));
        }
        file(tools.resolve("pom.xml"), project("different-project", ""));
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(tools, TOOLS));
    }

    @Test void currentR8ActualSourceManifestKeepsAllThirtyFiveProjectsAndOnlyExpandsTools() throws Exception {
        StringBuilder modules = new StringBuilder();
        for (String module : CompleteSourceGraph.modules(CompleteSourceGraph.Profile.G2_FULL_PARITY_20261116_R8)) {
            modules.append("<module>").append(module).append("</module>");
            file(root.resolve(module + "/pom.xml"), project(module.equals("build-tools") ? "ck3-control-build-tools" : module, ""));
        }
        file(root.resolve("pom.xml"), project("ck3-control-parent", "<modules>" + modules + "</modules>"));
        Path fixed = root.resolve("build-tools/src/test/resources/fixed.bin"); payload(fixed, (8L << 20) + 1);
        var actual = ControlBuild.sourceManifest(root, R8); assertEquals(36, actual.size()); assertTrue(actual.contains(ControlBuild.FileRef.measure(fixed)));
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, R7));
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, R6));
        assertEquals(ControlBuild.SourceState.MATCH, ControlBuild.postcheckSource(root, actual, R8).state());
        file(fixed, "changed\n"); assertEquals(ControlBuild.SourceState.MISMATCH, ControlBuild.postcheckSource(root, actual, R8).state());
    }

    @Test void bothCurrentPipelineTiersSelectR8ButMavenRedFixtureKeepsStandard() throws Exception {
        for (String schema : List.of(CiBootstrap.PLAN_SCHEMA, CiBootstrap.COMPLETE_PLAN_SCHEMA)) {
            var plan = plan(schema); Path reactor = root.resolve("java/ck3-control");
            assertEquals(R8, ControlCi.buildSourceProfile(plan, reactor));
            assertEquals(TOOLS, ControlCi.buildSourceProfile(plan, reactor.resolve("build-tools")));
            assertEquals(ControlBuild.SourceLimitProfile.STANDARD_8_MIB,
                    ControlCi.buildSourceProfile(plan, reactor.resolve("build-tools/src/test/resources/maven-failure")));
            if (schema.equals(CiBootstrap.PLAN_SCHEMA)) {
                assertEquals(CiBootstrap.PipelineProfile.LEGACY, CiBootstrap.pipelineProfile(plan));
                assertThrows(IllegalArgumentException.class, () -> CiBootstrap.requireCompletePipeline(plan));
            } else assertEquals(CiBootstrap.PipelineProfile.COMPLETE_CURRENT, CiBootstrap.pipelineProfile(plan));
        }
        assertEquals(ControlCi.httpRequirements(R7), ControlCi.httpRequirements(R8));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.httpRequirements(TOOLS));
    }

    @Test void toolsSourceProfileCannotBecomeAServiceTargetOrAG2RootCard() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> config(TOOLS, ControlBuild.TargetKind.SERVICE_FAST_JAR));
        assertThrows(IllegalArgumentException.class, () -> config(R8, ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME));
        var ref = reference();
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.RootSoftwareExecutionCard(ControlCi.ROOT_CARD_SCHEMA,
                ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, "software-profile-test", "2026-11-16T00:00:00Z", "2026-11-16T00:01:00Z",
                "/root/software-test", "software-slot", ref, ref, ref, ref, ref, TOOLS, null));
    }

    @Test void explicitToolsStillConsumesTheOriginalSelectedLobbyInputs() throws Exception {
        Path fixture = root.resolve("src/test/java/org/xar/ck3/control/build/FrontendLobbyCallbackObservationTest.java");
        file(fixture, "// selected source-only fixture marker\n");
        var environment = Map.of(ControlBuild.LobbyVerifyTestInputs.ENV, root.resolve("missing-lobby.json").toString(),
                "XAR_ORACLE_PYTHON", root.resolve("python.exe").toString());
        for (var profile : List.of(ControlBuild.SourceLimitProfile.STANDARD_8_MIB, TOOLS)) {
            var rejected = assertThrows(IllegalArgumentException.class, () -> ControlBuild.reactorVerifyArguments(
                    config(profile, ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME), root.resolve("settings.xml"), root, root.resolve("build"), environment));
            assertEquals("Selected pinned lobby fixture inputs required", rejected.getMessage());
        }
    }

    @Test void newProfilesRoundTripStrictBuildReceiptsWithoutLargerReceiptOrDeploymentBudgets() throws Exception {
        var ref = reference(); var post = new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null);
        for (var profile : List.of(TOOLS, R8)) {
            var kind = profile == TOOLS ? ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME : ControlBuild.TargetKind.SERVICE_FAST_JAR;
            var receipt = new ControlBuild.BuildReceipt(ControlBuild.SCHEMA, "software-profile-test", "2026-11-16T00:00:00Z", "RED",
                    root.toString(), root.toString(), root.toString(), post, post, kind, profile,
                    List.of(ref), List.of(ref), List.of(), List.of(ref), ref, null, ref, null, null, Map.of(), "not executed");
            byte[] bytes = ControlBuild.buildReceiptBytes(receipt);
            assertEquals(receipt, ControlBuild.decodeBuildReceipt(bytes));
            assertEquals(profile == TOOLS ? 2 << 20 : 4 << 20, ControlBuild.receiptMaxBytes(profile));
        }
    }

    private Path tools() throws IOException {
        file(root.resolve("pom.xml"), project("ck3-control-build-tools", "")); Files.createDirectories(root.resolve("src")); return root;
    }
    private static String project(String artifact, String extra) {
        return "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion><artifactId>" + artifact + "</artifactId>" + extra + "</project>";
    }
    private static void file(Path path, String content) throws IOException { Files.createDirectories(path.getParent()); Files.writeString(path, content); }
    private static void payload(Path path, long size) throws IOException {
        Files.createDirectories(path.getParent()); byte[] block = new byte[8192]; java.util.Arrays.fill(block, (byte)7);
        try (OutputStream output = Files.newOutputStream(path)) {
            for (long remaining = size; remaining > 0;) { int count = (int)Math.min(block.length, remaining); output.write(block, 0, count); remaining -= count; }
        }
    }
    private static List<ControlBuild.FileRef> bootstrapPins(Path source) throws IOException {
        return CiBootstrap.sourcePins(source).stream().map(pin -> new ControlBuild.FileRef(pin.path(), pin.bytes(), pin.sha256()))
                .sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList();
    }
    private ControlBuild.FileRef reference() throws IOException { Path pin = root.resolve("software-reference"); file(pin, "source-only\n"); return ControlBuild.FileRef.measure(pin); }
    private CiBootstrap.Plan plan(String schema) {
        String observed = Instant.parse("2026-11-16T00:00:00Z").toString(), review = Instant.parse(observed).plusSeconds(120).toString();
        var pin = new CiBootstrap.FilePin(root.resolve("plan-pin").toString(), 1, "0".repeat(64));
        return new CiBootstrap.Plan(schema, "software-profile-test", observed, review, root.toString(), root.resolve("work").toString(),
                root.resolve("jdk").toString(), null, root.resolve("python.exe").toString(), "/root/software-test", pin,
                Map.of(), Map.of(), Map.of(), List.of(pin), List.of(pin), false, false);
    }
    private ControlBuild.Config config(ControlBuild.SourceLimitProfile profile, ControlBuild.TargetKind kind) {
        return new ControlBuild.Config(root, root.resolve("work"), root.resolve("release.json"), "software-source-envelope", "/root/software-test",
                null, root.resolve("jdk"), "3.10.0", 900, kind, profile);
    }
}
