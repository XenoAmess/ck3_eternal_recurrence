package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.core.JsonProcessingException;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Exercises real emitted XML, compiled-source pins and the exact JSON contract. */
final class ReactorTestClosureTest {
    @TempDir Path temporary;
    private static final String HTTP = "org.xar.ck3.control.service.G2ResearchHttpTest";
    private static final ReactorTestClosure.RequiredSuite REQUIRED = new ReactorTestClosure.RequiredSuite(
            "local-service", "ck3-control-local-service", HTTP, 2);

    @Test void actualReportsFromAllModulesAndThePinnedRequiredSourceRoundTrip() throws Exception {
        Fixture fixture = fixture();
        report(fixture.build(), "ck3-control-local-service", HTTP, 2, "");
        report(fixture.build(), "g2-research", "org.xar.ck3.control.g2.m5.M5IntegrationTest", 3, "");
        var actual = ReactorTestClosure.evaluate(fixture.source(), fixture.pins(), fixture.build(), List.of(REQUIRED));
        assertEquals(5, actual.actualTestCases()); assertEquals(2, actual.allEmittedSuites().size());
        assertEquals(2, actual.requiredSuites().getFirst().actual().testCases());
        var receipt = new ReactorTestClosure.Receipt(ReactorTestClosure.SCHEMA, "software-fixture",
                "2026-10-22T23:00:00Z", "2026-10-22T23:00:01Z", ReactorTestClosure.Status.PASS, null,
                fixture.pins().getFirst(), List.of(REQUIRED), actual, 0);
        var mapper = ControlBuild.strictMapper();
        assertEquals(receipt, mapper.readValue(mapper.writeValueAsBytes(receipt), ReactorTestClosure.Receipt.class));
        String encoded = mapper.writeValueAsString(receipt);
        for (String token : List.of("null", "true", "1", "\"GREEN\"")) {
            assertThrows(JsonProcessingException.class, () -> mapper.readValue(
                    encoded.replace("\"status\":\"PASS\"", "\"status\":" + token), ReactorTestClosure.Receipt.class));
        }
        assertThrows(JsonProcessingException.class, () -> mapper.readValue(encoded.replace(
                "xar.java-reactor-test-closure/v1", "xar.java-reactor-test-closure/v0"), ReactorTestClosure.Receipt.class));
    }

    @Test void oldMapOrGenericHttpSuccessCannotReplaceMissingActualDomainSuites() throws Exception {
        Fixture fixture = fixture(); report(fixture.build(), "ck3-control-local-service", HTTP, 12, "");
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), fixture.pins(),
                fixture.build(), ReactorTestClosure.g2HttpRequirements()));
    }

    @Test void newlyAdoptedConsumerTestCannotDisappearFromReportsAfterGenericHttpPasses() throws Exception {
        Fixture fixture = fixture(); report(fixture.build(), "ck3-control-local-service", HTTP, 2, "");
        String consumer = "org.xar.ck3.control.service.M3ResidentUiHttpTest";
        Path source = fixture.source().resolve("local-service/src/test/java/" + consumer.replace('.', '/') + ".java");
        Files.writeString(source, "package org.xar.ck3.control.service; class M3ResidentUiHttpTest {}\n");
        List<ControlBuild.FileRef> pins = new ArrayList<>(fixture.pins()); pins.add(ControlBuild.FileRef.measure(source));
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), pins, fixture.build(), List.of(REQUIRED)));
        report(fixture.build(), "ck3-control-local-service", consumer, 3, "");
        var actual = ReactorTestClosure.evaluate(fixture.source(), pins, fixture.build(), List.of(REQUIRED));
        assertEquals(2, actual.requiredSuites().size()); assertEquals(5, actual.actualTestCases());
        assertTrue(actual.requiredSuites().stream().anyMatch(item -> item.requirement().testClass().equals(consumer)));
    }

    @Test void failingAndSkippedUnrequiredModulesStillRejectTheWholeReactor() throws Exception {
        Fixture fixture = fixture(); report(fixture.build(), "ck3-control-local-service", HTTP, 2, "");
        Path other = report(fixture.build(), "g2-research", "org.xar.ck3.control.g2.m2.M2PayloadTest", 1, "");
        String pass = Files.readString(other);
        for (String attribute : List.of("failures", "errors", "skipped")) {
            Files.writeString(other, pass.replace(attribute + "=\"0\"", attribute + "=\"1\""));
            assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), fixture.pins(),
                    fixture.build(), List.of(REQUIRED)));
        }
    }

    @Test void testcaseFailureCannotHideBehindAGreenSummary() throws Exception {
        Fixture fixture = fixture();
        for (String outcome : List.of("failure", "error", "skipped")) {
            Path file = report(fixture.build(), "ck3-control-local-service", HTTP, 2, "<" + outcome + "/>");
            assertThrows(IOException.class, () -> ReactorTestClosure.readReports(fixture.build()));
            Files.delete(file);
        }
    }

    @Test void summaryCountsMustMatchActualTestcasesAndCannotCoerceWrongTokens() throws Exception {
        Fixture fixture = fixture(); Path file = report(fixture.build(), "ck3-control-local-service", HTTP, 2, "");
        String original = Files.readString(file);
        for (String token : List.of("0", "1", "3", "true", "2.0", "02", "-1", "")) {
            Files.writeString(file, original.replace("tests=\"2\"", "tests=\"" + token + "\""));
            assertThrows(IOException.class, () -> ReactorTestClosure.readReports(fixture.build()));
        }
        Files.writeString(file, original.replace(" failures=\"0\"", ""));
        assertThrows(IOException.class, () -> ReactorTestClosure.readReports(fixture.build()));
    }

    @Test void missingReportsAndTooFewActualHttpInvocationsReject() throws Exception {
        Fixture fixture = fixture();
        assertThrows(IOException.class, () -> ReactorTestClosure.readReports(fixture.build()));
        report(fixture.build(), "ck3-control-local-service", HTTP, 1, "");
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), fixture.pins(),
                fixture.build(), List.of(REQUIRED)));
    }

    @Test void duplicatesAndReportSetGrowthRemainObservable() throws Exception {
        Fixture fixture = fixture(); Path original = report(fixture.build(), "ck3-control-local-service", HTTP, 2, "");
        var first = ReactorTestClosure.evaluate(fixture.source(), fixture.pins(), fixture.build(), List.of(REQUIRED));
        Path duplicate = original.resolveSibling("TEST-duplicate.xml"); Files.copy(original, duplicate);
        assertThrows(IOException.class, () -> ReactorTestClosure.readReports(fixture.build()));
        Files.delete(duplicate);
        report(fixture.build(), "g2-research", "org.xar.ck3.control.g2.m3.M3OriginalProducerTest", 1, "");
        assertNotEquals(first, ReactorTestClosure.evaluate(fixture.source(), fixture.pins(), fixture.build(), List.of(REQUIRED)));
    }

    @Test void aPassingReportCannotUseUnpinnedOrChangedTestSourceOrWrongMavenModule() throws Exception {
        Fixture fixture = fixture(); report(fixture.build(), "ck3-control-local-service", HTTP, 2, "");
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), List.of(),
                fixture.build(), List.of(REQUIRED)));
        Path javaSource = fixture.source().resolve("local-service/src/test/java/" + HTTP.replace('.', '/') + ".java");
        Files.writeString(javaSource, "changed after actual compile");
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), fixture.pins(),
                fixture.build(), List.of(REQUIRED)));
        Path pom = fixture.source().resolve("local-service/pom.xml");
        Files.writeString(pom, "<project><artifactId>another-module</artifactId></project>");
        List<ControlBuild.FileRef> changedPins = List.of(ControlBuild.FileRef.measure(pom), ControlBuild.FileRef.measure(javaSource));
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), changedPins,
                fixture.build(), List.of(REQUIRED)));
    }

    @Test void duplicateRequirementsAndXmlExternalEntitiesReject() throws Exception {
        Fixture fixture = fixture(); Path file = report(fixture.build(), "ck3-control-local-service", HTTP, 2, "");
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), fixture.pins(),
                fixture.build(), List.of(REQUIRED, REQUIRED)));
        Files.writeString(file, "<!DOCTYPE testsuite [<!ENTITY x SYSTEM 'file:///unread'>]><testsuite>&x;</testsuite>");
        assertThrows(IOException.class, () -> ReactorTestClosure.readReports(fixture.build()));
    }

    @Test void jsonRequirementsRejectMissingExtraNullBoolFloatAndUnknownStatus() throws Exception {
        var mapper = ControlBuild.strictMapper(); String body = mapper.writeValueAsString(REQUIRED);
        for (String token : List.of("null", "true", "2.0", "\"2\"")) {
            String malformed = body.replace("\"minimum_test_cases\":2", "\"minimum_test_cases\":" + token);
            assertThrows(JsonProcessingException.class, () -> mapper.readValue(malformed, ReactorTestClosure.RequiredSuite.class));
        }
        for (String malformed : List.of(body.replace("\"minimum_test_cases\":2", "\"other\":2"),
                body.replace("\"minimum_test_cases\":2", "\"minimum_test_cases\":2,\"extra\":true"),
                body.replace("\"module_directory\":\"local-service\"", "\"module_directory\":null"))) {
            assertThrows(JsonProcessingException.class, () -> mapper.readValue(malformed, ReactorTestClosure.RequiredSuite.class));
        }
        assertThrows(IllegalArgumentException.class, () -> new ReactorTestClosure.Receipt(ReactorTestClosure.SCHEMA,
                "fixture", "2026-10-22T23:00:00Z", "2026-10-22T23:00:01Z", ReactorTestClosure.Status.PASS,
                null, null, List.of(REQUIRED), null, 0));
        assertTrue(ReactorTestClosure.g2HttpRequirements().stream().anyMatch(item -> item.testClass().endsWith("M7ConsumerHttpTest")));
    }

    @Test void stabilizationRequiresBothM4ParameterLeavesWithoutChangingHistoricalResearch() throws Exception {
        var selected = ReactorTestClosure.g2StabilizationHttpRequirements();
        assertEquals(ReactorTestClosure.g2HttpRequirements(), selected.subList(0, ReactorTestClosure.g2HttpRequirements().size()));
        var requirement = selected.stream().filter(item -> item.testClass().endsWith("M4OrdinaryConstructionHttpTest")).findFirst().orElseThrow();
        Fixture fixture = fixture();
        Path source = fixture.source().resolve("local-service/src/test/java/" + requirement.testClass().replace('.', '/') + ".java");
        Files.writeString(source, "package org.xar.ck3.control.service; class M4OrdinaryConstructionHttpTest {}\n");
        var pins = new ArrayList<>(fixture.pins()); pins.add(ControlBuild.FileRef.measure(source));
        report(fixture.build(), "ck3-control-local-service", HTTP, 2, "");
        report(fixture.build(), requirement.moduleArtifactId(), requirement.testClass(), 1, "");
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), pins, fixture.build(), List.of(requirement)));
        report(fixture.build(), requirement.moduleArtifactId(), requirement.testClass(), 2, "");
        assertEquals(4, ReactorTestClosure.evaluate(fixture.source(), pins, fixture.build(), List.of(requirement)).actualTestCases());
        assertTrue(selected.stream().anyMatch(item -> item.testClass().endsWith("M7ScheduleHttpTest") && item.minimumTestCases() == 1));
        assertTrue(selected.stream().anyMatch(item -> item.testClass().endsWith("SavedContinuityHttpTest") && item.minimumTestCases() == 2));
    }

    @Test void currentRestartRequirementRejectsTheHistoricalIncompleteSuite() throws Exception {
        var historical = ReactorTestClosure.g2FullParityResumeRequirements();
        var selected = ReactorTestClosure.g2FullParityCurrentRequirements();
        assertEquals(historical, selected.subList(0, historical.size()));
        var restart = selected.stream().filter(item -> item.testClass().equals(
                "org.xar.ck3.control.nativebridge.CleanRestartCanonicalWriterTest")).findFirst().orElseThrow();
        assertEquals(8, restart.minimumTestCases());
        Fixture fixture = fixture();
        Path source = fixture.source().resolve("local-service/src/test/java/" + restart.testClass().replace('.', '/') + ".java");
        Files.createDirectories(source.getParent());
        Files.writeString(source, "package org.xar.ck3.control.nativebridge; class CleanRestartCanonicalWriterTest {}\n");
        var pins = new ArrayList<>(fixture.pins()); pins.add(ControlBuild.FileRef.measure(source));
        report(fixture.build(), "ck3-control-local-service", HTTP, 2, "");
        report(fixture.build(), restart.moduleArtifactId(), restart.testClass(), 7, "");
        assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), pins,
                fixture.build(), List.of(restart)));
        report(fixture.build(), restart.moduleArtifactId(), restart.testClass(), 8, "");
        var actual = ReactorTestClosure.evaluate(fixture.source(), pins, fixture.build(), List.of(restart));
        assertEquals(10, actual.actualTestCases());
        assertEquals(8, actual.requiredSuites().stream().filter(item -> item.requirement().equals(restart))
                .findFirst().orElseThrow().actual().testCases());
    }

    @Test void currentCanonicalRecoveryRequirementsRejectIncompleteReports() throws Exception {
        var expected = List.of(
                new ReactorTestClosure.RequiredSuite("adapters-storage", "adapters-storage",
                        "org.xar.ck3.control.continuity.writer.HistoricalTransitionBatchTest", 2),
                new ReactorTestClosure.RequiredSuite("adapters-storage", "adapters-storage",
                        "org.xar.ck3.control.continuity.writer.DomainReadSessionReuseTest", 2),
                new ReactorTestClosure.RequiredSuite("local-service", "ck3-control-local-service",
                        "org.xar.ck3.control.nativebridge.SessionControllerDeferredCanonicalRecoveryTest", 1));
        var selected = ReactorTestClosure.g2FullParityCurrentRequirements().stream()
                .filter(item -> expected.stream().anyMatch(required -> required.testClass().equals(item.testClass())))
                .toList();
        assertEquals(expected, selected);
        Fixture fixture = fixture();
        var pins = new ArrayList<>(fixture.pins());
        Path storagePom = fixture.source().resolve("adapters-storage/pom.xml");
        Files.createDirectories(storagePom.getParent());
        Files.writeString(storagePom, "<project><artifactId>adapters-storage</artifactId></project>");
        pins.add(ControlBuild.FileRef.measure(storagePom));
        report(fixture.build(), "ck3-control-local-service", HTTP, 2, "");
        for (var requirement : selected) {
            Path source = fixture.source().resolve(requirement.moduleDirectory()).resolve("src/test/java/")
                    .resolve(requirement.testClass().replace('.', '/') + ".java");
            Files.createDirectories(source.getParent());
            int split = requirement.testClass().lastIndexOf('.');
            Files.writeString(source, "package " + requirement.testClass().substring(0, split) + "; class "
                    + requirement.testClass().substring(split + 1) + " {}\n");
            pins.add(ControlBuild.FileRef.measure(source));
            report(fixture.build(), requirement.moduleArtifactId(), requirement.testClass(),
                    requirement.minimumTestCases(), "");
        }
        for (var requirement : selected) {
            Path emitted = report(fixture.build(), requirement.moduleArtifactId(), requirement.testClass(),
                    requirement.minimumTestCases() - 1, "");
            assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), pins,
                    fixture.build(), selected));
            Files.delete(emitted);
            assertThrows(IOException.class, () -> ReactorTestClosure.evaluate(fixture.source(), pins,
                    fixture.build(), selected));
            report(fixture.build(), requirement.moduleArtifactId(), requirement.testClass(),
                    requirement.minimumTestCases(), "");
        }
        var actual = ReactorTestClosure.evaluate(fixture.source(), pins, fixture.build(), selected);
        assertEquals(7, actual.actualTestCases());
        for (var requirement : selected) {
            assertEquals(requirement.minimumTestCases(), actual.requiredSuites().stream()
                    .filter(item -> item.requirement().equals(requirement)).findFirst().orElseThrow().actual().testCases());
        }
    }

    private record Fixture(Path source, Path build, List<ControlBuild.FileRef> pins) {}

    private Fixture fixture() throws IOException {
        Path source = Files.createDirectory(temporary.resolve("source"));
        Path build = Files.createDirectory(temporary.resolve("build"));
        Path module = source.resolve("local-service");
        Path java = module.resolve("src/test/java/" + HTTP.replace('.', '/') + ".java");
        Files.createDirectories(java.getParent());
        Files.writeString(java, "package org.xar.ck3.control.service; class G2ResearchHttpTest {}\n");
        Path pom = module.resolve("pom.xml");
        Files.writeString(pom, "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><artifactId>ck3-control-local-service</artifactId></project>");
        return new Fixture(source, build, List.of(ControlBuild.FileRef.measure(pom), ControlBuild.FileRef.measure(java)));
    }

    private static Path report(Path build, String module, String suite, int count, String outcome) throws IOException {
        Path reports = build.resolve(module).resolve("surefire-reports"); Files.createDirectories(reports);
        List<String> testcases = new ArrayList<>();
        for (int index = 0; index < count; index++) testcases.add("<testcase name=\"case[" + index + "]\" classname=\"" + suite + "\">" + outcome + "</testcase>");
        Path file = reports.resolve("TEST-" + suite + ".xml");
        Files.writeString(file, "<testsuite name=\"" + suite + "\" tests=\"" + count + "\" failures=\"0\" errors=\"0\" skipped=\"0\">"
                + String.join("", testcases) + "</testsuite>");
        return file;
    }
}
