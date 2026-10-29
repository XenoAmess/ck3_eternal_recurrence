package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.zip.GZIPOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Whole graph, actual source consumer, immutable capture argv and all default report closure regressions. */
final class FullParityCiTest {
    @TempDir Path temporary;
    private static final CompleteSourceGraph.Profile FULL = CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024;
    private static final String PRODUCER = "application/src/main/resources/producer.json";
    private static final String CONSUMER = "native-transport/src/test/resources/consumer.json";

    @Test void full35UsesActualSourceProducerWithoutWideningTheOlderProfiles() throws Exception {
        assertEquals(29, CompleteSourceGraph.Profile.JAVA29_REPAIR_20261023.childModules());
        assertEquals(30, CompleteSourceGraph.Profile.G2_RESEARCH_20261023.childModules());
        assertEquals(31, CompleteSourceGraph.Profile.G2_STABILIZATION_20261023.childModules());
        assertEquals(34, FULL.childModules()); assertEquals(35, FULL.reactorProjects());
        assertEquals(35, FULL.sourceLimitProfile().maxReactorProjects());
        List<String> selected = CompleteSourceGraph.modules(FULL);
        assertEquals(CompleteSourceGraph.modules(CompleteSourceGraph.Profile.G2_STABILIZATION_20261023), selected.subList(0, 31));
        assertEquals(List.of("adapters-storage", "application", "native-transport"), selected.subList(31, 34));
        Fixture fixture = graph("full35");
        var actual = CompleteSourceGraph.verifyMaterialized(fixture.plan(), fixture.root());
        assertEquals(ControlBuild.sourceManifest(fixture.root(), FULL.sourceLimitProfile()), actual.sourcePins());
        assertEquals(FULL, actual.profile());
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(fixture.root(),
                ControlBuild.SourceLimitProfile.G2_STABILIZATION_20261023));
    }

    @Test void strictGraphRoundtripAndSourceConsumerContentRemainBound() throws Exception {
        Fixture original = graph("original"), materialized = graph("materialized");
        byte[] wire = CompleteSourceGraph.encodePlan(original.plan());
        var json = ControlBuild.strictMapper();
        assertEquals(original.plan(), json.readValue(wire, CompleteSourceGraph.Plan.class));
        CompleteSourceGraph.verifyMaterialized(original.plan(), materialized.root());
        Files.writeString(materialized.root().resolve(CONSUMER), "{\"value\":2}");
        assertEquals(ControlBuild.sourceManifest(original.root(), FULL.sourceLimitProfile()).size(),
                ControlBuild.sourceManifest(materialized.root(), FULL.sourceLimitProfile()).size());
        assertThrows(IOException.class, () -> CompleteSourceGraph.verifyMaterialized(original.plan(), materialized.root()));
        String encoded = new String(wire, java.nio.charset.StandardCharsets.UTF_8);
        for (String invalid : List.of(encoded.replace("G2_FULL_PARITY_20261024", "G2_STABILIZATION_20261023"),
                encoded.replaceFirst("\"bytes\":[0-9]+", "\"bytes\":true"),
                encoded.replaceFirst("\"bytes\":[0-9]+", "\"bytes\":1.0"),
                encoded.replace("\"modules\":", "\"unknown\":"))) {
            assertThrows(IOException.class, () -> json.readValue(invalid, CompleteSourceGraph.Plan.class));
        }
    }

    @Test void full35CannotDropOrAliasAnApplicationModule() throws Exception {
        Fixture fixture = graph("missing-module");
        Path parent = fixture.root().resolve("pom.xml");
        String original = Files.readString(parent);
        Files.writeString(parent, original.replace("<module>native-transport</module>", ""));
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(fixture.root(), FULL.sourceLimitProfile()));
        Files.writeString(parent, original.replace("<module>native-transport</module>", "<module>application</module>"));
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(fixture.root(), FULL.sourceLimitProfile()));
    }

    @Test void newNativeExtentRequiresTheExactMatchingProfileCard() throws Exception {
        CompleteSourceGraphMaterializer.requireProfileBudget(FULL, 56L << 20);
        CompleteSourceGraphMaterializer.requireProfileBudget(CompleteSourceGraph.Profile.G2_STABILIZATION_20261023, 44L << 20);
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.requireProfileBudget(FULL, 44L << 20));
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.requireProfileBudget(
                CompleteSourceGraph.Profile.G2_STABILIZATION_20261023, 56L << 20));
        ControlBuild.FileRef pin = ref("admission", "source-only fixture pin");
        var card = new CompleteSourceGraphMaterializer.Card("xar.complete-source-graph-operation-card/v1",
                "fixture-machine", "/root/source03_audit", "2026-10-23T16:00:00Z", "2026-10-23T17:00:00Z",
                CompleteSourceGraphMaterializer.Operation.MATERIALIZE, pin, pin, pin, pin, pin, pin, null,
                temporary.resolve("future-source").toString(), temporary.resolve("future-metadata").toString(),
                56L << 20, 1L << 20, "FULL_GRAPH_SOURCE_OPERATION_ADMITTED");
        assertEquals(card, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(card),
                CompleteSourceGraphMaterializer.Card.class));
    }

    @Test void liveOracleProducerPinsTheActualSourceAndMissingInputsAreRed() throws Exception {
        Oracle oracle = oracle("live-oracle");
        var bindings = FullParityOracleBindings.fromEnvironment(oracle.environment());
        assertEquals(ControlBuild.FileRef.measure(oracle.nativeSource()).sha256(), bindings.nativeProducerSha256());
        assertEquals(oracle.python().toRealPath().toString(), bindings.python());
        assertEquals(11, bindings.mavenArguments().size());
        assertEquals(List.of(FullParityOracleBindings.FixtureRole.values()), bindings.nativeFixtures().stream().map(FullParityOracleBindings.BoundFixture::role).toList());
        Files.delete(oracle.armyFixture());
        assertThrows(IllegalArgumentException.class, () -> FullParityOracleBindings.fromEnvironment(oracle.environment()));
        assertThrows(IllegalArgumentException.class, () -> FullParityOracleBindings.fromEnvironment(Map.of()));
        assertThrows(IllegalArgumentException.class, () -> FullParityOracleBindings.fromEnvironment(
                Map.of("XAR_ORACLE_PYTHON", oracle.python().toString())));
        Files.delete(oracle.nativeSource());
        assertThrows(IllegalArgumentException.class, () -> FullParityOracleBindings.fromEnvironment(oracle.environment()));
    }

    @Test void completeCaptureReaderUsesOnlyTheImmutableRecordedBindings() throws Exception {
        Oracle oracle = oracle("capture-oracle");
        ControlBuild.Config config = config();
        Path settings = temporary.resolve("settings.xml"), snapshot = temporary.resolve("snapshot"), build = temporary.resolve("build");
        List<String> verify = ControlBuild.reactorVerifyArguments(config, settings, snapshot, build, oracle.environment());
        assertEquals("verify", verify.getLast());
        assertTrue(verify.contains("--fail-at-end"));
        assertFalse(verify.stream().anyMatch(argument -> argument.startsWith("-Dtest=") || argument.equals("-pl")));
        List<String> capture = historicalCaptureCommand(ControlBuild.reactorVerifyArguments(config, settings, snapshot, build, oracle.environment()));
        assertEquals("package", capture.getLast()); assertTrue(capture.contains("-DskipTests=true"));
        assertTrue(capture.contains("-Dmaven.test.skip=false"));
        var bindings = FullParityOracleBindings.fromRecordedArguments(capture);
        assertEquals(bindings, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(bindings),
                FullParityOracleBindings.Bindings.class));
        // Original files may be retained elsewhere or superseded. They must not be silently rebound during historical review.
        Files.delete(oracle.python()); Files.delete(oracle.nativeSource());
        Files.delete(oracle.m3Fixture()); Files.delete(oracle.armyFixture());
        assertEquals(capture, ControlBuild.completedCaptureArguments(config, settings, snapshot, build, capture));
        assertThrows(IllegalArgumentException.class, () -> ControlBuild.reactorVerifyArguments(config, settings, snapshot, build, oracle.environment()));
    }

    @Test void recordedCaptureRejectsDuplicateMissingMixedInterpreterAndSelectedTestArguments() throws Exception {
        Oracle oracle = oracle("bad-capture"); ControlBuild.Config config = config();
        Path settings = temporary.resolve("settings.xml"), snapshot = temporary.resolve("snapshot"), build = temporary.resolve("build");
        List<String> capture = historicalCaptureCommand(ControlBuild.reactorVerifyArguments(config, settings, snapshot, build, oracle.environment()));
        List<String> missing = capture.stream().filter(argument -> !argument.startsWith("-Dxar.native.producer.sha256=")).toList();
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, missing));
        var duplicate = new ArrayList<>(capture); duplicate.add("-Dxar.python=" + oracle.python());
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, duplicate));
        var wrongInterpreter = new ArrayList<>(capture);
        wrongInterpreter.replaceAll(argument -> argument.startsWith("-Dxar.native.producer.python=")
                ? "-Dxar.native.producer.python=" + temporary.resolve("other-python.exe") : argument);
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, wrongInterpreter));
        var selected = new ArrayList<>(capture); selected.add("-Dtest=OneSelectedTest");
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, selected));
    }

    @Test void everyFullParityAndNewDefaultConsumerMustEmitAnUnskippedActualReport() throws Exception {
        List<ReactorTestClosure.RequiredSuite> required = ReactorTestClosure.g2FullParityRequirements();
        assertEquals(required, ControlCi.httpRequirements(FULL.sourceLimitProfile()));
        assertEquals(ReactorTestClosure.g2StabilizationHttpRequirements(), required.subList(0,
                ReactorTestClosure.g2StabilizationHttpRequirements().size()));
        Path source = Files.createDirectory(temporary.resolve("suite-source"));
        Path build = Files.createDirectory(temporary.resolve("suite-build"));
        for (var suite : required) {
            testSource(source, suite);
            report(build, suite.moduleArtifactId(), suite.testClass(), suite.minimumTestCases(), false);
        }
        List<ControlBuild.FileRef> pins = pins(source);
        var complete = ReactorTestClosure.evaluate(source, pins, build, required);
        assertEquals(required.size(), complete.requiredSuites().size());
        var extra = new ReactorTestClosure.RequiredSuite("application", "application", "fixture.NewConsumerNativeIT", 1);
        testSource(source, extra); pins = pins(source);
        List<ControlBuild.FileRef> withExtra = pins;
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(source, withExtra, build, required));
        report(build, extra.moduleArtifactId(), extra.testClass(), 1, false);
        assertEquals(required.size() + 1, ReactorTestClosure.evaluate(source, pins, build, required).requiredSuites().size());
        report(build, extra.moduleArtifactId(), extra.testClass(), 1, true);
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(source, withExtra, build, required));
    }

    @Test void completeCiCannotTreatMissingSdkOrOnlyAnOldCompletedConfigAsQualification() throws Exception {
        assertThrows(IOException.class, () -> ControlCi.requireFullParityFixtureProduction(FULL.sourceLimitProfile(), null));
        ControlCi.requireFullParityFixtureProduction(FULL.sourceLimitProfile(), ref("production-request", "input binding only"));
        ControlCi.requireFullParityFixtureProduction(ControlBuild.SourceLimitProfile.G2_STABILIZATION_20261023, null);
    }

    private record Fixture(Path root, CompleteSourceGraph.Plan plan) { }
    private Fixture graph(String name) throws IOException {
        Path root = Files.createDirectory(temporary.resolve(name));
        StringBuilder declarations = new StringBuilder();
        for (String module : CompleteSourceGraph.modules(FULL)) {
            declarations.append("<module>").append(module).append("</module>");
            Path directory = Files.createDirectory(root.resolve(module));
            String artifact = module.equals("build-tools") ? "ck3-control-build-tools"
                    : module.equals("local-service") ? "ck3-control-local-service" : module;
            Files.writeString(directory.resolve("pom.xml"), "<project><artifactId>" + artifact + "</artifactId></project>");
        }
        Files.writeString(root.resolve("pom.xml"), "<project><artifactId>ck3-control-parent</artifactId><modules>"
                + declarations + "</modules></project>");
        for (String relative : List.of(PRODUCER, CONSUMER)) {
            Path file = root.resolve(relative); Files.createDirectories(file.getParent()); Files.writeString(file, "{\"value\":1}");
        }
        Path inventory = temporary.resolve(name + "-inventory.json.gz");
        try (var output = new GZIPOutputStream(Files.newOutputStream(inventory))) {
            output.write(ControlBuild.strictMapper().writeValueAsBytes(ControlBuild.sourceManifest(root, FULL.sourceLimitProfile())));
        }
        ControlBuild.FileRef owner = ref(name + "-owner", "complete explicit owner selection");
        var selections = new ArrayList<CompleteSourceGraph.ComponentSelection>();
        for (var component : CompleteSourceGraph.Component.values()) {
            List<CompleteSourceGraph.SelectedFile> files = component == CompleteSourceGraph.Component.BUILD_TOOLS
                    ? List.of(new CompleteSourceGraph.SelectedFile("build-tools/pom.xml", ControlBuild.FileRef.measure(root.resolve("build-tools/pom.xml"))))
                    : List.of(new CompleteSourceGraph.SelectedFile(PRODUCER, ControlBuild.FileRef.measure(root.resolve(PRODUCER))),
                            new CompleteSourceGraph.SelectedFile(CONSUMER, ControlBuild.FileRef.measure(root.resolve(CONSUMER))));
            selections.add(new CompleteSourceGraph.ComponentSelection(component, owner, files));
        }
        return new Fixture(root, new CompleteSourceGraph.Plan(CompleteSourceGraph.PLAN_SCHEMA, "fixture-machine",
                "2026-10-23T16:00:00Z", CompleteSourceGraph.SelectionStatus.SOURCE_SELECTION_ONLY, FULL,
                new CompleteSourceGraph.Baseline(root.toString(), ControlBuild.FileRef.measure(inventory)),
                CompleteSourceGraph.modules(FULL), selections, List.of()));
    }

    /** Original pre-policy command data keeps full-fixture historical replay and rejection coverage. */
    private static List<String> historicalCaptureCommand(List<String> verify) {
        var capture = new ArrayList<>(verify);
        assertEquals("verify", capture.removeLast());
        capture.addAll(List.of("-Dmaven.test.skip=false", "-DskipTests=true", "package"));
        assertFalse(capture.stream().anyMatch(argument -> argument.startsWith("-Dxar.control.capture.commandPolicy=")));
        return List.copyOf(capture);
    }

    private record Oracle(Path python, Path repository, Path nativeSource, Path m3Fixture, Path armyFixture) {
        Map<String, String> environment() { return Map.of("XAR_ORACLE_PYTHON", python.toString(), "XAR_ORACLE_REPO", repository.toString(),
                "XAR_M3_TIMELINE_NATIVE_WHOLE", m3Fixture.toString(), "XAR_ARMY_DEFAULT_RAISE_FIXTURE", armyFixture.toString()); }
    }
    private Oracle oracle(String name) throws IOException {
        Path repo = Files.createDirectory(temporary.resolve(name));
        Path python = repo.resolve("selected-python.exe"); Files.writeString(python, "binding unit fixture; never executed");
        Path nativeSource = repo.resolve(FullParityOracleBindings.NATIVE_RELATIVE);
        Files.createDirectories(nativeSource.getParent()); Files.writeString(nativeSource, "# original fixture producer\n");
        Path m3 = repo.resolve("m3-original-whole.json"), army = repo.resolve("army-original-default-raise.json");
        Files.writeString(m3, "{\"fixture\":\"original M3 input binding only\"}");
        Files.writeString(army, "{\"fixture\":\"original Army input binding only\"}");
        return new Oracle(python, repo, nativeSource, m3, army);
    }
    private ControlBuild.Config config() {
        return new ControlBuild.Config(temporary.resolve("source"), temporary.resolve("work"), temporary.resolve("release.json"),
                "full35", "fixture-owner", null, temporary.resolve("java21"), "3.10.0", 900,
                ControlBuild.TargetKind.SERVICE_FAST_JAR, FULL.sourceLimitProfile());
    }
    private ControlBuild.FileRef ref(String name, String content) throws IOException {
        Path file = temporary.resolve(name + ".json"); Files.writeString(file, content); return ControlBuild.FileRef.measure(file);
    }
    private static void testSource(Path root, ReactorTestClosure.RequiredSuite suite) throws IOException {
        Path module = root.resolve(suite.moduleDirectory()); Files.createDirectories(module);
        Path pom = module.resolve("pom.xml");
        if (!Files.exists(pom)) Files.writeString(pom, "<project><artifactId>" + suite.moduleArtifactId() + "</artifactId></project>");
        Path source = module.resolve("src/test/java/" + suite.testClass().replace('.', '/') + ".java");
        Files.createDirectories(source.getParent()); Files.writeString(source, "// actual selected source fixture\n");
    }
    private static List<ControlBuild.FileRef> pins(Path root) throws IOException {
        List<ControlBuild.FileRef> refs = new ArrayList<>();
        try (var paths = Files.walk(root)) { for (Path file : paths.filter(Files::isRegularFile).sorted().toList()) refs.add(ControlBuild.FileRef.measure(file)); }
        return List.copyOf(refs);
    }
    private static void report(Path root, String module, String suite, int count, boolean skipped) throws IOException {
        Path directory = root.resolve(module).resolve("surefire-reports"); Files.createDirectories(directory);
        StringBuilder cases = new StringBuilder();
        for (int index = 0; index < count; index++) cases.append("<testcase name='case").append(index).append("' classname='")
                .append(suite).append("'>").append(skipped && index == 0 ? "<skipped/>" : "").append("</testcase>");
        Files.writeString(directory.resolve("TEST-" + suite + ".xml"), "<testsuite name='" + suite + "' tests='" + count
                + "' failures='0' errors='0' skipped='" + (skipped ? 1 : 0) + "'>" + cases + "</testsuite>");
    }
}
