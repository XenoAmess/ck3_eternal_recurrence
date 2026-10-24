package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xml.sax.SAXException;

/** Binds the complete emitted Surefire reports and required G2 HTTP suites to the actual reactor build. */
public final class ReactorTestClosure {
    public static final String SCHEMA = "xar.java-reactor-test-closure/v1";
    private ReactorTestClosure() {}

    public enum Status { PASS, RED }

    public record RequiredSuite(String moduleDirectory, String moduleArtifactId, String testClass,
                                int minimumTestCases) {
        public RequiredSuite {
            if (!simpleName(moduleDirectory) || !simpleName(moduleArtifactId)
                    || testClass == null || !testClass.matches("[A-Za-z_$][\\w$]*(\\.[A-Za-z_$][\\w$]*)+" )
                    || minimumTestCases < 1) throw new IllegalArgumentException("Explicit module and positive test suite requirement required");
        }
        String key() { return moduleArtifactId + "/" + testClass; }
    }

    public record SuiteEvidence(String moduleArtifactId, String testClass, int testCases,
                                ControlBuild.FileRef reportRef) {
        public SuiteEvidence {
            if (!simpleName(moduleArtifactId) || testClass == null || testClass.isBlank() || testCases < 1)
                throw new IllegalArgumentException("Positive actual Surefire suite required");
            Objects.requireNonNull(reportRef);
        }
        String key() { return moduleArtifactId + "/" + testClass; }
    }

    public record SatisfiedSuite(RequiredSuite requirement, ControlBuild.FileRef modulePomRef,
                                 ControlBuild.FileRef testSourceRef, SuiteEvidence actual) {
        public SatisfiedSuite {
            Objects.requireNonNull(requirement); Objects.requireNonNull(modulePomRef);
            Objects.requireNonNull(testSourceRef); Objects.requireNonNull(actual);
            if (!requirement.key().equals(actual.key()) || actual.testCases() < requirement.minimumTestCases())
                throw new IllegalArgumentException("Required suite is not satisfied");
        }
    }

    public record Evaluation(List<SuiteEvidence> allEmittedSuites, List<SatisfiedSuite> requiredSuites,
                             int actualTestCases) {
        public Evaluation {
            allEmittedSuites = List.copyOf(allEmittedSuites); requiredSuites = List.copyOf(requiredSuites);
            if (allEmittedSuites.isEmpty() || requiredSuites.isEmpty() || actualTestCases < 1)
                throw new IllegalArgumentException("Complete positive report evaluation required");
        }
    }

    public record Receipt(String schema, String machineId, String startedAtUtc, String observedAtUtc,
                          Status status, String error, ControlBuild.FileRef reactorBuildReceiptRef,
                          List<RequiredSuite> requirements, Evaluation evaluation,
                          int gameNativeRpcOrCampaignLedgerWrites) {
        public Receipt {
            if (!SCHEMA.equals(schema) || machineId == null || machineId.isBlank() || status == null
                    || reactorBuildReceiptRef == null || gameNativeRpcOrCampaignLedgerWrites != 0)
                throw new IllegalArgumentException("Exact reactor software test closure contract required");
            Instant.parse(startedAtUtc); Instant.parse(observedAtUtc); requirements = List.copyOf(requirements);
            if (requirements.isEmpty() || (status == Status.PASS && (error != null || evaluation == null))
                    || (status == Status.RED && (error == null || error.isBlank() || evaluation != null)))
                throw new IllegalArgumentException("Consistent PASS/RED test closure required");
        }
    }

    /** The eight real domain HTTP suites, shared client route and resource contract must all execute. */
    public static List<RequiredSuite> g2HttpRequirements() {
        String module = "local-service", artifact = "ck3-control-local-service", service = "org.xar.ck3.control.service.";
        return List.of(new RequiredSuite(module, artifact, service + "G2ResearchHttpTest", 14),
                new RequiredSuite(module, artifact, service + "G2ResearchResourceTest", 6),
                new RequiredSuite(module, artifact, "org.xar.ck3.control.g2.m0.integration.M0ConsumerHttpTest", 1),
                new RequiredSuite(module, artifact, service + "M1EightRouteHttpTest", 9),
                new RequiredSuite(module, artifact, service + "M2ConsumerHttpTest", 3),
                new RequiredSuite(module, artifact, service + "M3ConsumerHttpTest", 4),
                new RequiredSuite(module, artifact, service + "M4ConsumerHttpTest", 3),
                new RequiredSuite(module, artifact, service + "M5ConsumerHttpTest", 3),
                new RequiredSuite(module, artifact, service + "M6ConsumerHttpTest", 2),
                new RequiredSuite(module, artifact, service + "M6ServiceCompositionHttpTest", 2),
                new RequiredSuite(module, artifact, service + "M7ConsumerHttpTest", 2),
                new RequiredSuite(module, artifact, service + "CampaignMapAdmissionHttpContractTest", 2),
                new RequiredSuite(module, artifact, service + "CampaignMapAdmissionResourceContractTest", 3));
    }

    /** New selected stabilization suites; the historical research requirements remain unchanged. */
    public static List<RequiredSuite> g2StabilizationHttpRequirements() {
        var suites = new ArrayList<>(g2HttpRequirements());
        String module = "local-service", artifact = "ck3-control-local-service", service = "org.xar.ck3.control.service.";
        suites.add(new RequiredSuite(module, artifact, service + "M4OrdinaryConstructionHttpTest", 2));
        suites.add(new RequiredSuite(module, artifact, service + "M7ScheduleHttpTest", 1));
        suites.add(new RequiredSuite(module, artifact, service + "SavedContinuityHttpTest", 2));
        return List.copyOf(suites);
    }

    /** Complete migration still requires every default source suite in addition to these real chain anchors. */
    public static List<RequiredSuite> g2FullParityResumeRequirements() {
        List<RequiredSuite> result = new ArrayList<>(g2FullParityRequirements());
        result.add(new RequiredSuite("build-tools", "ck3-control-build-tools", "org.xar.ck3.control.build.FullParityResumeCiTest", 8));
        return List.copyOf(result);
    }
    /** Every default suite is still enumerated from actual compiler source pins; these are additional anchors. */
    public static List<RequiredSuite> g2FullParityCurrentRequirements() {
        var result = new ArrayList<>(g2FullParityResumeRequirements());
        result.add(new RequiredSuite("build-tools", "ck3-control-build-tools", "org.xar.ck3.control.build.FullParityCurrentBindingsTest", 4));
        result.add(new RequiredSuite("build-tools", "ck3-control-build-tools", "org.xar.ck3.control.build.CompleteSourceGraphResumedCardTest", 2));
        result.add(new RequiredSuite("build-tools", "ck3-control-build-tools", "org.xar.ck3.control.build.ReinforcementArrivalFirstCorpusTest", 2));
        result.add(new RequiredSuite("build-tools", "ck3-control-build-tools", "org.xar.ck3.control.build.NativeFixtureCorporaTest", 2));
        return List.copyOf(result);
    }

    public static List<RequiredSuite> g2FullParityRequirements() {
        var suites = new ArrayList<>(g2StabilizationHttpRequirements());
        suites.add(new RequiredSuite("application", "application",
                "org.xar.ck3.control.application.action.ActionCoordinatorTest", 1));
        suites.add(new RequiredSuite("native-transport", "native-transport",
                "org.xar.ck3.control.nativebridge.NativeOriginalProducerTest", 1));
        String writer = "org.xar.ck3.control.continuity.writer.";
        suites.add(new RequiredSuite("adapters-storage", "adapters-storage", writer + "ContinuityWriterTransactionTest", 1));
        suites.add(new RequiredSuite("adapters-storage", "adapters-storage", writer + "OriginalWindowReducerDifferentialTest", 2));
        suites.add(new RequiredSuite("adapters-storage", "adapters-storage", writer + "WindowsWriterInteropTest", 2));
        suites.add(new RequiredSuite("adapters-storage", "adapters-storage", writer + "CanonicalContinuityTransactionsTest", 5));
        suites.add(new RequiredSuite("local-service", "ck3-control-local-service",
                "org.xar.ck3.control.application.action.ActionCoordinatorWriterIntegrationTest", 1));
        return List.copyOf(suites);
    }

    /** Called only after the existing shared producer accepted the complete reactor build. */
    public static ControlBuild.FileRef run(Path buildReceiptPath, Path outputActualPath,
                                           List<RequiredSuite> requiredSuites) throws IOException {
        String started = Instant.now().toString();
        ControlBuild.FileRef buildRef = ControlBuild.FileRef.measure(buildReceiptPath);
        String machine = WindowsJobProcess.currentMachineId();
        String failure = null; Evaluation evaluation = null;
        try {
            ControlBuild.BuildReceipt build = ControlBuild.acceptedReceipt(buildReceiptPath);
            if (build.targetKind() != ControlBuild.TargetKind.SERVICE_FAST_JAR)
                throw new IOException("Complete service reactor build required");
            Path deployment = Path.of(build.deploymentRoot());
            if (!deployment.getFileName().toString().equals("quarkus-app")
                    || !deployment.getParent().getFileName().toString().equals("ck3-control-local-service"))
                throw new IOException("Shared reactor deployment route required");
            evaluation = evaluate(Path.of(build.compiledSourceRoot()), build.compiledSourcePins(),
                    deployment.getParent().getParent(), requiredSuites);
            buildRef.verify();
        } catch (IOException | RuntimeException error) {
            failure = error.getClass().getSimpleName() + ": " + error.getMessage();
            evaluation = null;
        }
        Receipt actual = new Receipt(SCHEMA, machine, started, Instant.now().toString(),
                failure == null ? Status.PASS : Status.RED, failure, buildRef, requiredSuites, evaluation, 0);
        Files.write(outputActualPath, ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(actual),
                StandardOpenOption.CREATE_NEW);
        if (failure != null) throw new IOException(failure);
        return ControlBuild.FileRef.measure(outputActualPath);
    }

    /** Reader rechecks the real build and every emitted report, including report-set growth or removal. */
    public static ControlBuild.FileRef requireAccepted(Path actualPath, Path expectedBuildReceiptPath,
                                                       List<RequiredSuite> expectedRequirements) throws IOException {
        Receipt actual = ControlBuild.strictMapper().readValue(Files.readAllBytes(actualPath), Receipt.class);
        ControlBuild.FileRef expectedBuild = ControlBuild.FileRef.measure(expectedBuildReceiptPath);
        if (actual.status() != Status.PASS || !actual.machineId().equals(WindowsJobProcess.currentMachineId())
                || !actual.reactorBuildReceiptRef().equals(expectedBuild) || !actual.requirements().equals(expectedRequirements))
            throw new IOException("Current reactor test closure and exact requirements required");
        ControlBuild.BuildReceipt build = ControlBuild.acceptedReceipt(expectedBuildReceiptPath);
        Path buildRoot = Path.of(build.deploymentRoot()).getParent().getParent();
        if (!actual.evaluation().equals(evaluate(Path.of(build.compiledSourceRoot()), build.compiledSourcePins(),
                buildRoot, expectedRequirements))) throw new IOException("Actual emitted reactor test closure changed");
        return ControlBuild.FileRef.measure(actualPath);
    }

    static Evaluation evaluate(Path sourceRoot, List<ControlBuild.FileRef> compiledSourcePins,
                               Path buildRoot, List<RequiredSuite> requirements) throws IOException {
        if (requirements.isEmpty()) throw new IOException("Explicit mandatory suites required");
        List<SuiteEvidence> reports = readReports(buildRoot);
        TreeMap<String, RequiredSuite> effective = defaultSourceRequirements(sourceRoot, compiledSourcePins);
        Set<String> requiredKeys = new HashSet<>();
        for (RequiredSuite required : requirements) {
            if (!requiredKeys.add(required.key())) throw new IOException("Duplicate required suite: " + required.key());
            RequiredSuite fromSource = effective.get(required.key());
            if (fromSource != null && !fromSource.moduleDirectory().equals(required.moduleDirectory()))
                throw new IOException("Required suite module differs from actual default source");
            effective.put(required.key(), required);
        }
        List<SatisfiedSuite> satisfied = new ArrayList<>();
        for (RequiredSuite required : effective.values()) {
            Path module = sourceRoot.resolve(required.moduleDirectory());
            ControlBuild.FileRef pom = pinned(module.resolve("pom.xml"), compiledSourcePins);
            Element project = parseXml(Path.of(pom.path()));
            if (!project.getTagName().equals("project")
                    || !required.moduleArtifactId().equals(directText(project, "artifactId")))
                throw new IOException("Required test module artifact differs from pinned Maven module");
            ControlBuild.FileRef source = pinned(module.resolve("src/test/java")
                    .resolve(required.testClass().replace('.', '/') + ".java"), compiledSourcePins);
            SuiteEvidence report = reports.stream().filter(item -> item.key().equals(required.key())).findFirst()
                    .orElseThrow(() -> new IOException("Required actual suite missing: " + required.key()));
            if (report.testCases() < required.minimumTestCases())
                throw new IOException("Required actual suite incomplete: " + required.key());
            satisfied.add(new SatisfiedSuite(required, pom, source, report));
        }
        int total = 0; for (SuiteEvidence report : reports) total = Math.addExact(total, report.testCases());
        return new Evaluation(reports, satisfied, total);
    }

    /** Every selected default test class must emit a report, including newly adopted consumer tests. */
    private static TreeMap<String, RequiredSuite> defaultSourceRequirements(Path sourceRoot,
            List<ControlBuild.FileRef> compiledSourcePins) throws IOException {
        TreeMap<String, RequiredSuite> expected = new TreeMap<>();
        Path root = sourceRoot.toAbsolutePath().normalize();
        for (ControlBuild.FileRef pin : compiledSourcePins) {
            Path source = Path.of(pin.path()).toAbsolutePath().normalize();
            if (!source.startsWith(root)) throw new IOException("Compiled test source escaped the accepted source root");
            String relative = root.relativize(source).toString().replace('\\', '/');
            String marker = "/src/test/java/"; int boundary = relative.indexOf(marker);
            if (boundary < 1 || !relative.endsWith(".java")) continue;
            String file = source.getFileName().toString();
            if (!(file.startsWith("Test") || file.endsWith("Test.java") || file.endsWith("Tests.java")
                    || file.endsWith("TestCase.java") || file.endsWith("NativeIT.java"))) continue;
            pin.verify(); String module = relative.substring(0, boundary);
            ControlBuild.FileRef pom = pinned(root.resolve(module).resolve("pom.xml"), compiledSourcePins);
            Element project = parseXml(Path.of(pom.path()));
            if (!project.getTagName().equals("project")) throw new IOException("Pinned module POM project required");
            String artifact = directText(project, "artifactId");
            String testClass = relative.substring(boundary + marker.length(), relative.length() - 5).replace('/', '.');
            RequiredSuite required = new RequiredSuite(module, artifact, testClass, 1);
            if (expected.putIfAbsent(required.key(), required) != null)
                throw new IOException("Duplicate actual default test source: " + required.key());
        }
        if (expected.isEmpty()) throw new IOException("Default reactor test source inventory missing");
        return expected;
    }

    static List<SuiteEvidence> readReports(Path buildRoot) throws IOException {
        List<SuiteEvidence> reports = new ArrayList<>(); Set<String> keys = new HashSet<>();
        List<Path> modules;
        try (var paths = Files.list(buildRoot)) { modules = paths.filter(Files::isDirectory).sorted().toList(); }
        for (Path module : modules) {
            Path directory = module.resolve("surefire-reports");
            if (!Files.isDirectory(directory)) continue;
            List<Path> files;
            try (var paths = Files.list(directory)) {
                files = paths.filter(path -> path.getFileName().toString().matches("TEST-.*\\.xml")).sorted().toList();
            }
            for (Path report : files) {
                ControlBuild.FileRef ref = ControlBuild.FileRef.measure(report);
                Element suite = parseXml(report);
                if (!suite.getTagName().equals("testsuite")) throw new IOException("Surefire testsuite required: " + report);
                int tests = count(suite, "tests");
                if (tests == 0 || count(suite, "failures") != 0 || count(suite, "errors") != 0 || count(suite, "skipped") != 0)
                    throw new IOException("Actual reactor suite failed, skipped, or empty: " + report);
                int actual = 0;
                for (Node child = suite.getFirstChild(); child != null; child = child.getNextSibling()) {
                    if (!(child instanceof Element element) || !element.getTagName().equals("testcase")) continue;
                    actual++;
                    if (element.getAttribute("name").isBlank() || element.getAttribute("classname").isBlank())
                        throw new IOException("Actual testcase identity missing: " + report);
                    for (Node result = element.getFirstChild(); result != null; result = result.getNextSibling()) {
                        if (result instanceof Element outcome && Set.of("failure", "error", "skipped").contains(outcome.getTagName()))
                            throw new IOException("Actual testcase failure or skip contradicts summary: " + report);
                    }
                }
                if (actual != tests) throw new IOException("Actual testcase count differs from suite summary: " + report);
                SuiteEvidence evidence = new SuiteEvidence(module.getFileName().toString(), suite.getAttribute("name"), tests, ref);
                if (!keys.add(evidence.key())) throw new IOException("Duplicate emitted suite: " + evidence.key());
                ref.verify(); reports.add(evidence);
            }
        }
        if (reports.isEmpty()) throw new IOException("Complete actual reactor Surefire reports missing");
        reports.sort(Comparator.comparing(SuiteEvidence::key)); return List.copyOf(reports);
    }

    private static ControlBuild.FileRef pinned(Path path, List<ControlBuild.FileRef> pins) throws IOException {
        ControlBuild.FileRef actual = ControlBuild.FileRef.measure(path);
        if (!pins.contains(actual)) throw new IOException("Required suite source is outside the compiled source closure: " + path);
        return actual;
    }

    private static Element parseXml(Path path) throws IOException {
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            try (var input = Files.newInputStream(path)) { return factory.newDocumentBuilder().parse(input).getDocumentElement(); }
        } catch (ParserConfigurationException | SAXException error) { throw new IOException("Actual pinned Maven/Surefire XML invalid: " + path, error); }
    }

    private static int count(Element element, String attribute) throws IOException {
        String value = element.getAttribute(attribute);
        if (!value.matches("0|[1-9][0-9]{0,8}")) throw new IOException("Canonical nonnegative JUnit count required: " + attribute);
        try { return Integer.parseInt(value); }
        catch (NumberFormatException error) { throw new IOException("Bounded JUnit count required", error); }
    }

    private static String directText(Element parent, String name) throws IOException {
        String value = null;
        for (Node child = parent.getFirstChild(); child != null; child = child.getNextSibling()) {
            if (child instanceof Element element && element.getTagName().equals(name)) {
                if (value != null) throw new IOException("Duplicate Maven " + name);
                value = element.getTextContent();
            }
        }
        return value;
    }

    private static boolean simpleName(String value) { return value != null && value.matches("[a-z0-9][a-z0-9-]*"); }
}
