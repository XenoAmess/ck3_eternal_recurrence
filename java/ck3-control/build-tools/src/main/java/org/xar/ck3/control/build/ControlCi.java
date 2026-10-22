package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;
import java.util.TreeMap;

/** The durable CI route: qualify tools under a native Job, then run the same build and consumers. */
public final class ControlCi {
    private ControlCi() {}
    public static final String ACTUAL_SCHEMA = "xar.java-control-CI-actual/v2";

    public record Receipt(String schema, String machineId, String startedAtUtc, String observedAtUtc,
            String status, String error, ControlBuild.FileRef planRef, ControlBuild.FileRef capacityReleaseRef,
            ControlBuild.FileRef toolsBuildReceiptRef, WindowsJobProcess.CommandResult qualifiedPipeline,
            ControlBuild.FileRef reactorBuildReceiptRef, ControlBuild.FileRef consumerReceiptRef,
            List<ControlBuild.FileRef> pythonStaticReceiptRefs) {
        public Receipt {
            if (!ACTUAL_SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact CI actual v2 contract required");
            pythonStaticReceiptRefs = List.copyOf(pythonStaticReceiptRefs);
        }
    }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length == 2 && arguments[0].equals("--verify-static-receipts")) {
            requireCompletedPythonStaticPipeline(Path.of(arguments[1]).toRealPath()); return;
        }
        if (arguments.length == 2 && arguments[0].equals("--verify-shared-fixture-junit")) {
            PythonBoundaryStaticStage.requireSuccessfulPytest(Path.of(arguments[1]).toRealPath()); return;
        }
        if (arguments.length != 2 && arguments.length != 4) throw new IllegalArgumentException("Exact bootstrap plan and optional qualified tools receipt required");
        if (!arguments[0].equals("--bootstrap-plan") || (arguments.length == 4 && !arguments[2].equals("--qualified-tools-receipt"))) {
            throw new IllegalArgumentException("Unknown CI arguments");
        }
        Path planPath = Path.of(arguments[1]).toRealPath();
        if (Files.size(planPath) > 1024 * 1024) throw new IOException("Bounded CI plan required");
        CiBootstrap.Plan plan = ControlBuild.strictMapper().readValue(Files.readAllBytes(planPath), CiBootstrap.Plan.class);
        verifyPlan(plan, arguments.length == 4);
        if (arguments.length == 2) qualify(planPath, plan);
        else runQualified(planPath, plan, Path.of(arguments[3]).toRealPath());
    }

    private static void verifyPlan(CiBootstrap.Plan plan, boolean qualifiedInvocation) throws IOException {
        if (!CiBootstrap.PLAN_SCHEMA.equals(plan.schema()) || !plan.machineId().equals(WindowsJobProcess.currentMachineId())
                || !Instant.now().isBefore(Instant.parse(plan.reviewAtUtc())) || plan.bootstrapRuntimeClosure().isEmpty()
                || plan.sourcePins().isEmpty()) throw new IOException("Current complete bootstrap plan required");
        for (CiBootstrap.FilePin pin : plan.sourcePins()) ref(pin).verify();
        for (CiBootstrap.FilePin pin : plan.bootstrapRuntimeClosure()) ref(pin).verify();
        List<ControlBuild.FileRef> expected = plan.sourcePins().stream().map(ControlCi::ref).sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList();
        if (!expected.equals(ControlBuild.sourceManifest(Path.of(plan.repoRoot()).resolve("java/ck3-control/build-tools")))) {
            throw new IOException("Bootstrap source closure changed or grew");
        }
        if (!qualifiedInvocation && !ControlBuild.producerClosure().equals(plan.bootstrapRuntimeClosure().stream().map(ControlCi::ref).sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList())) {
            throw new IOException("Current bootstrap runtime differs from plan");
        }
    }

    private static void qualify(Path planPath, CiBootstrap.Plan plan) throws IOException, InterruptedException {
        Path root = Path.of(plan.workRoot());
        Path releasePath = root.resolve("logs/ci-capacity-release.json");
        ControlBuild.CapacityRelease release = ControlBuild.ciCapacityRelease(plan);
        publish(releasePath, release);
        Path toolsSource = Path.of(plan.repoRoot()).resolve("java/ck3-control/build-tools");
        ControlBuild.BuildReceipt tools = ControlBuild.build(config(plan, toolsSource, releasePath, "qualified-tools", ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME));
        if (!tools.status().equals("PASS")) throw new IOException("Native Job tools qualification failed");
        Path toolsReceipt = root.resolve("logs/build-qualified-tools.json");
        requireJUnit(Path.of(tools.deploymentRoot()).resolve("surefire-reports"), 120);
        List<String> arguments = new ArrayList<>(List.of("-Xms32m", "-Xmx128m", "-XX:MaxMetaspaceSize=96m",
                "-XX:ReservedCodeCacheSize=48m", "-XX:MaxDirectMemorySize=32m", "-Djava.io.tmpdir=" + root.resolve("scratch"),
                "-Djna.tmpdir=" + root.resolve("scratch"), "-cp",
                Path.of(tools.deploymentRoot()).resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar").toString(),
                ControlCi.class.getName(), "--bootstrap-plan", planPath.toString(), "--qualified-tools-receipt", toolsReceipt.toString()));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        environment.remove("JAVA_TOOL_OPTIONS"); environment.remove("JDK_JAVA_OPTIONS");
        environment.put("TEMP", root.resolve("scratch").toString()); environment.put("TMP", root.resolve("scratch").toString());
        WindowsJobProcess.CommandResult result;
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(Path.of(plan.javaHome()).resolve("bin/java.exe"), arguments,
                Path.of(plan.repoRoot()), environment, root.resolve("logs/qualified-control.stdout.log"),
                root.resolve("logs/qualified-control.stderr.log"), 2L << 30))) {
            result = child.await(Duration.ofMinutes(20), Instant.parse(plan.reviewAtUtc()), () -> {});
        }
        publish(root.resolve("logs/control-ci-bootstrap-terminal.json"), result);
        if (!result.passed()) throw new IOException("Qualified Java pipeline did not exit cleanly: " + result);
    }

    private static void runQualified(Path planPath, CiBootstrap.Plan plan, Path toolsReceiptPath) throws IOException, InterruptedException {
        String started = Instant.now().toString(); Path root = Path.of(plan.workRoot());
        Path releasePath = root.resolve("logs/ci-capacity-release.json");
        ControlBuild.BuildReceipt tools = ControlBuild.acceptedReceipt(toolsReceiptPath);
        if (tools.targetKind() != ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME || !tools.completeDeployment().equals(ControlBuild.producerClosure())) {
            throw new IOException("Actual running qualified jar/lib must exactly equal the qualified build closure");
        }
        String failure = null; ControlBuild.FileRef reactorRef = null, consumerRef = null;
        List<ControlBuild.FileRef> staticRefs = new ArrayList<>();
        boolean complete = false;
        try {
            requireExpectedMavenFailure(plan, releasePath);
            ControlBuild.BuildReceipt reactor = ControlBuild.build(config(plan, Path.of(plan.repoRoot()).resolve("java/ck3-control"),
                    releasePath, "ci-reactor", ControlBuild.TargetKind.SERVICE_FAST_JAR));
            Path reactorPath = root.resolve("logs/build-ci-reactor.json"); reactorRef = ControlBuild.FileRef.measure(reactorPath);
            if (!reactor.status().equals("PASS")) throw new IOException("Complete reactor failed");
            MapAdmissionCi.run(new MapAdmissionCi.Config(Path.of(plan.repoRoot()), reactorPath, root.resolve("artifacts/map-ci"),
                    Path.of(plan.javaHome()).resolve("bin/java.exe"), Path.of(plan.pythonExecutable()), Instant.parse(plan.reviewAtUtc()), 8089));
            consumerRef = ControlBuild.FileRef.measure(root.resolve("artifacts/map-ci/logs/actual.json"));
            for (var kind : PythonBoundaryStaticStage.Kind.values()) {
                staticRefs.add(PythonBoundaryStaticStage.run(new PythonBoundaryStaticStage.Config(kind,
                        Path.of(plan.repoRoot()), pythonStaticRoot(root, kind), Path.of(plan.pythonExecutable()),
                        root.resolve("scratch"), Instant.parse(plan.reviewAtUtc()), plan.machineId())));
            }
            requirePythonStaticReceipts(root); complete = true;
        } catch (IOException | RuntimeException error) { failure = error.getClass().getSimpleName() + ": " + error.getMessage(); }
        finally {
            if (!complete && failure == null) failure = "Pipeline did not complete all validation and cleanup";
            publish(root.resolve("logs/control-ci-actual.json"), new Receipt(ACTUAL_SCHEMA, plan.machineId(), started, Instant.now().toString(),
                    complete && failure == null ? "PASS" : "RED", failure, ControlBuild.FileRef.measure(planPath), ControlBuild.FileRef.measure(releasePath),
                    ControlBuild.FileRef.measure(toolsReceiptPath), null, reactorRef, consumerRef, List.copyOf(staticRefs)));
        }
        if (!complete || failure != null) throw new IOException(failure);
    }

    /** Execute the original failing producer path, not just the source-postcheck helper. */
    private static void requireExpectedMavenFailure(CiBootstrap.Plan plan, Path release) throws IOException, InterruptedException {
        Path fixture = Path.of(plan.repoRoot()).resolve("java/ck3-control/build-tools/src/test/resources/maven-failure");
        ControlBuild.BuildReceipt actual = ControlBuild.build(config(plan, fixture, release, "ci-expected-maven-red", ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME));
        if (!actual.status().equals("RED") || actual.mavenResult() == null || actual.mavenResult().exitCode() == 0
                || actual.mavenResult().accounting().activeProcesses() != 0 || actual.mavenResult().stopReason() != null
                || actual.sourcePostcheck().state() != ControlBuild.SourceState.MATCH
                || actual.compiledSourcePostcheck().state() != ControlBuild.SourceState.MATCH) {
            throw new IOException("Expected real Maven model failure lost its terminal result or actual source postchecks");
        }
    }

    private static ControlBuild.Config config(CiBootstrap.Plan plan, Path source, Path release, String attempt, ControlBuild.TargetKind target) {
        return new ControlBuild.Config(source, Path.of(plan.workRoot()), release, attempt, plan.ownerTask(), null,
                Path.of(plan.javaHome()), CiBootstrap.MINIMUM_MAVEN_VERSION, 900, target,
                source.equals(Path.of(plan.repoRoot()).resolve("java/ck3-control"))
                        ? ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022
                        : ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
    }

    private static ControlBuild.FileRef ref(CiBootstrap.FilePin pin) { return new ControlBuild.FileRef(pin.path(), pin.bytes(), pin.sha256()); }

    private static Path pythonStaticRoot(Path root, PythonBoundaryStaticStage.Kind kind) {
        return root.resolve("artifacts/python-static").resolve(kind == PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED
                ? "sdk-sentinel" : "monthly-fixture");
    }

    private static List<ControlBuild.FileRef> requirePythonStaticReceipts(Path root) throws IOException {
        String machine = WindowsJobProcess.currentMachineId();
        List<ControlBuild.FileRef> refs = new ArrayList<>();
        for (var kind : PythonBoundaryStaticStage.Kind.values()) {
            ControlBuild.FileRef receipt = PythonBoundaryStaticStage.requireAccepted(pythonStaticRoot(root, kind).resolve("actual.json"), kind, machine);
            refs.add(receipt);
            System.out.println("ACCEPTED_PYTHON_STATIC " + kind + " " + receipt);
        }
        return List.copyOf(refs);
    }

    private static void requireCompletedPythonStaticPipeline(Path root) throws IOException {
        List<ControlBuild.FileRef> refs = requirePythonStaticReceipts(root);
        Path path = root.resolve("logs/control-ci-actual.json");
        if (Files.size(path) > 65536) throw new IOException("Bounded completed CI actual required");
        Receipt actual = ControlBuild.strictMapper().readValue(Files.readAllBytes(path), Receipt.class);
        if (!actual.machineId().equals(WindowsJobProcess.currentMachineId()) || !actual.status().equals("PASS")
                || actual.error() != null || !actual.pythonStaticReceiptRefs().equals(refs)
                || actual.planRef() == null || actual.capacityReleaseRef() == null || actual.toolsBuildReceiptRef() == null
                || actual.reactorBuildReceiptRef() == null || actual.consumerReceiptRef() == null) {
            throw new IOException("Complete CI v2 actual must bind both accepted Python static receipts");
        }
        actual.planRef().verify(); actual.capacityReleaseRef().verify(); actual.toolsBuildReceiptRef().verify();
        actual.reactorBuildReceiptRef().verify(); actual.consumerReceiptRef().verify();
        System.out.println("ACCEPTED_CONTROL_CI_V2 " + ControlBuild.FileRef.measure(path));
    }

    private static void publish(Path path, Record value) throws IOException {
        Files.write(path, ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(value), StandardOpenOption.CREATE_NEW);
    }

    /** Read actual Surefire XML; a green Maven command alone cannot prove any non-skipped test ran. */
    static void requireJUnit(Path reports, int minimumTests) throws IOException {
        int tests = 0; int files = 0; Set<String> suites = new HashSet<>();
        try (var paths = Files.list(reports)) {
            for (Path path : paths.filter(item -> item.getFileName().toString().matches("TEST-.*\\.xml")).toList()) {
                try {
                    var factory = javax.xml.parsers.DocumentBuilderFactory.newInstance();
                    factory.setFeature(javax.xml.XMLConstants.FEATURE_SECURE_PROCESSING, true);
                    factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
                    factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
                    var suite = factory.newDocumentBuilder().parse(path.toFile()).getDocumentElement();
                    if (!suites.add(suite.getAttribute("name"))) throw new IOException("Duplicate JUnit suite");
                    if (!suite.getTagName().equals("testsuite") || !suite.getAttribute("failures").equals("0")
                            || !suite.getAttribute("errors").equals("0") || !suite.getAttribute("skipped").equals("0")) throw new IOException("JUnit failure/skip or wrong suite");
                    String count = suite.getAttribute("tests"); if (!count.matches("[1-9][0-9]{0,5}")) throw new IOException("Positive bounded actual test count required");
                    tests = Math.addExact(tests, Integer.parseInt(count)); files++;
                } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException | NumberFormatException error) { throw new IOException("Actual JUnit report invalid", error); }
            }
        }
        if (files == 0 || tests < minimumTests || !suites.containsAll(Set.of("org.xar.ck3.control.build.ControlBuildTest",
                "org.xar.ck3.control.build.WindowsJobProcessTest", "org.xar.ck3.control.build.NativeTcpListenerTest",
                "org.xar.ck3.control.build.CiBootstrapTest", "org.xar.ck3.control.build.MapAdmissionServiceOwnerTest",
                "org.xar.ck3.control.build.SourceLimitProfileTest", "org.xar.ck3.control.build.PythonBoundaryStaticStageTest", "org.xar.ck3.control.build.SdkSourceAssemblyTest",
                "org.xar.ck3.control.build.ProjectionDeploymentProofTest",
                "org.xar.ck3.control.build.ProjectionRuntimeSourcesTest",
                "org.xar.ck3.control.build.ProjectionCaptureScopeTest",
                "org.xar.ck3.control.build.CompiledClassProvenanceTest",
                "org.xar.ck3.control.build.ControlBuildCaptureTest"))) throw new IOException("Complete actual non-skipped JUnit reports missing");
    }
}
