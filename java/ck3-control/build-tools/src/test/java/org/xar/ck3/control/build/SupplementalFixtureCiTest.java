package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SupplementalFixtureCiTest {
    @TempDir Path root;
    private static final String FIRST = "ck3_autonomous_player/tests/unit/test_first.py";
    private static final String SECOND = "ck3_autonomous_player/tests/unit/test_second.py";

    private SupplementalFixtureCi.PytestCounts parse(String xml, String stdout, List<String> modules) throws IOException {
        Path report = root.resolve("pytest-" + java.util.UUID.randomUUID() + ".xml");
        Path log = report.resolveSibling(report.getFileName() + ".log");
        Files.writeString(report, xml); Files.writeString(log, stdout);
        return SupplementalFixtureCi.readPytest(report, log, modules);
    }
    private static String cleanXml(int tests) {
        return "<testsuites><testsuite tests=\"" + tests + "\" failures=\"0\" errors=\"0\" skipped=\"0\">"
                + "<testcase classname=\"tests.unit.test_first.First\" name=\"test_one\"/>"
                + "<testcase classname=\"tests.unit.test_second.Second\" name=\"test_two\"/></testsuite></testsuites>";
    }
    @Test void realPytestNineMultiFailureParentStaysOneParentAndFiveSubtests() throws IOException {
        Path xml = original("/ci-pytest-parent-subtest/failed34.pytest.xml.gz", "historical.xml");
        Path stdout = original("/ci-pytest-parent-subtest/failed34.pytest.stdout.log.gz", "historical.log");
        assertEquals("a691913115bbff12a23532658023a12713893cf36c08e9445aefbb837a5f285c", ControlBuild.FileRef.measure(xml).sha256());
        assertEquals("54db35b4101b5758d59c3365805c6abe95beeb3a3f5376419b53081c71885475", ControlBuild.FileRef.measure(stdout).sha256());
        var counts = SupplementalFixtureCi.readPytest(xml, stdout, SupplementalFixtureCi.coreModules());
        assertEquals(52, counts.junitTests()); assertEquals(41, counts.testcaseElements());
        assertEquals(40, counts.parentPassed()); assertEquals(1, counts.parentFailed());
        assertEquals(6, counts.subtestsPassed()); assertEquals(5, counts.subtestsFailed()); assertEquals(6, counts.aggregateFailed());
        assertEquals(0, counts.parentSkipped()); assertEquals(34, counts.modules().size());
        assertThrows(IOException.class, () -> SupplementalFixtureCi.requirePassed(counts));
    }
    @Test void successfulSubtestsAreNotMisreportedAsFabricatedParentCases() throws IOException {
        var counts = parse(cleanXml(5), "2 passed, 3 subtests passed in 0.10s\n", List.of(FIRST, SECOND));
        assertEquals(2, counts.testcaseElements()); assertEquals(3, counts.subtestsPassed());
        SupplementalFixtureCi.requirePassed(counts);
    }
    @Test void simpleSuccessfulXmlStillHasExactExecutedCounts() throws IOException {
        var counts = parse(cleanXml(2), "2 passed in 0.10s\n", List.of(FIRST, SECOND));
        assertEquals(0, counts.subtestsPassed()); SupplementalFixtureCi.requirePassed(counts);
        SupplementalFixtureCi.requirePassed(parse(cleanXml(2), "2 passed in 84.19s (0:01:24)\n", List.of(FIRST, SECOND)));
        assertThrows(IOException.class, () -> parse(cleanXml(2), "2 passed in 84.19s (0:02:24)\n", List.of(FIRST, SECOND)));
    }
    @Test void inflatedXmlOrSummaryCountsCannotClaimSubtests() {
        assertThrows(IOException.class, () -> parse(cleanXml(5), "2 passed in 0.10s\n", List.of(FIRST, SECOND)));
        assertThrows(IOException.class, () -> parse(cleanXml(2), "2 passed, 3 subtests passed in 0.10s\n", List.of(FIRST, SECOND)));
    }
    @Test void incompleteModuleInventoryAndSelectorsAreRejected() {
        assertThrows(IOException.class, () -> parse(cleanXml(2), "2 passed in 0.10s\n", List.of(FIRST)));
        assertThrows(IOException.class, () -> parse(cleanXml(2), "2 passed in 0.10s\n", List.of(FIRST, SECOND, "ck3_autonomous_player/tests/unit/test_third.py")));
        assertThrows(IllegalArgumentException.class, () -> parse(cleanXml(2), "2 passed in 0.10s\n", List.of(FIRST + "::test_one")));
    }
    @Test void skippedAndExpectedFailureOutcomesCannotQualify() throws IOException {
        String skipped = cleanXml(2).replace("skipped=\"0\"", "skipped=\"1\"")
                .replace("name=\"test_two\"/>", "name=\"test_two\"><skipped/></testcase>");
        var counts = parse(skipped, "1 passed, 1 skipped in 0.10s\n", List.of(FIRST, SECOND));
        assertThrows(IOException.class, () -> SupplementalFixtureCi.requirePassed(counts));
        assertThrows(IOException.class, () -> parse(cleanXml(2), "2 passed, 1 xfailed in 0.10s\n", List.of(FIRST, SECOND)));
        assertThrows(IOException.class, () -> parse(cleanXml(2), "2 passed, 1 subtests skipped in 0.10s\n", List.of(FIRST, SECOND)));
        String sub = "<testsuite tests=\"2\" failures=\"0\" errors=\"0\" skipped=\"1\"><testcase classname=\"tests.unit.test_first.First\" name=\"test_one\"><skipped/></testcase></testsuite>";
        var subCounts = parse(sub, "1 passed, 1 skipped in 0.10s\n", List.of(FIRST));
        assertEquals(1, subCounts.parentPassed()); assertEquals(0, subCounts.parentSkipped()); assertEquals(1, subCounts.subtestsSkipped());
        assertThrows(IOException.class, () -> SupplementalFixtureCi.requirePassed(subCounts));
        String mixed = cleanXml(4).replace("failures=\"0\"", "failures=\"2\"").replace("skipped=\"0\"", "skipped=\"1\"")
                .replace("name=\"test_one\"/>", "name=\"test_one\"><failure/><failure/><skipped/></testcase>");
        String summary = "SUBFAILED(scene='one') " + FIRST + "::First::test_one\nFAILED " + FIRST + "::First::test_one\n2 failed, 1 passed, 1 skipped in 0.10s\n";
        var mixedCounts = parse(mixed, summary, List.of(FIRST, SECOND));
        assertEquals(1, mixedCounts.parentFailed()); assertEquals(1, mixedCounts.subtestsFailed()); assertEquals(1, mixedCounts.subtestsSkipped());
        assertThrows(IOException.class, () -> SupplementalFixtureCi.requirePassed(mixedCounts));
        assertThrows(IOException.class, () -> parse(mixed, summary.replace("FAILED " + FIRST, "FAILED ck3_autonomous_player/tests/unit/test_unknown.py"), List.of(FIRST, SECOND)));
        assertThrows(IOException.class, () -> parse(mixed, "SUBFAILED(scene='one') " + FIRST + "::First::test_one\n" + summary, List.of(FIRST, SECOND)));
    }
    @Test void missingAmbiguousSummaryAndExternalEntitiesAreRejected() {
        assertThrows(IOException.class, () -> parse(cleanXml(2), "", List.of(FIRST, SECOND)));
        assertThrows(IOException.class, () -> parse(cleanXml(2), "2 passed in 0.10s\n2 passed in 0.11s\n", List.of(FIRST, SECOND)));
        assertThrows(IOException.class, () -> parse("<!DOCTYPE testsuite [<!ENTITY x SYSTEM 'file:///unavailable'>]>" + cleanXml(2), "2 passed in 0.10s\n", List.of(FIRST, SECOND)));
    }
    @Test void multiFailureXmlNeedsMatchingExplicitSubfailureAndParentSummary() {
        String xml = "<testsuite tests=\"3\" failures=\"2\" errors=\"0\" skipped=\"0\">"
                + "<testcase classname=\"tests.unit.test_first.First\" name=\"test_one\"><failure/><failure/></testcase>"
                + "<testcase classname=\"tests.unit.test_second.Second\" name=\"test_two\"/></testsuite>";
        assertThrows(IOException.class, () -> parse(xml, "FAILED test_first.py::test_one\n2 failed, 1 passed in 0.10s\n", List.of(FIRST, SECOND)));
    }
    @Test void exactCoreSupplementaryAndWholeModuleScopesTravelWithTheOriginalCommands() throws IOException {
        assertEquals(34, SupplementalFixtureCi.coreModules().size()); assertEquals(2, SupplementalFixtureCi.supplementaryModules().size());
        assertEquals(7, SupplementalFixtureCi.wholeStaticModules().size());
        List<String> all = new ArrayList<>(SupplementalFixtureCi.coreModules()); all.addAll(SupplementalFixtureCi.supplementaryModules());
        assertEquals(36, all.stream().distinct().count()); assertTrue(all.containsAll(SupplementalFixtureCi.wholeStaticModules()));
        assertTrue(SupplementalFixtureCi.staticArguments().containsAll(SupplementalFixtureCi.wholeStaticModules()));
        var pytest = SupplementalFixtureCi.pytestArguments(root.resolve("pytest.xml"), root.resolve("tmp"));
        assertTrue(pytest.containsAll(all)); assertTrue(pytest.contains("-ra")); assertFalse(pytest.stream().anyMatch(value -> value.contains("::")));
        Path site = root.resolve("checker"); Files.createDirectories(site.resolve("mypy"));
        for (String file : List.of("__main__.py", "main.py", "build.py")) Files.writeString(site.resolve("mypy").resolve(file), "# exact synthetic checker source");
        String metadata = "Name: mypy\nVersion: 1.15.0\nLocation: " + site + "\nFiles:\n  mypy/__main__.py\n  mypy/main.py\n  mypy/build.py\n";
        assertEquals(3, SupplementalFixtureCi.checkerSources(metadata, site).size());
        assertThrows(IOException.class, () -> SupplementalFixtureCi.checkerSources(metadata.replace("1.15.0", "1.16.0"), site));
        assertThrows(IOException.class, () -> SupplementalFixtureCi.checkerSources(metadata, root));
        Path isolated = root.resolve("pycache-fixture"); Files.createDirectories(isolated.resolve("scratch"));
        SupplementalFixtureCi.requireUnusedPycache(isolated);
        Path cache = Files.createDirectory(isolated.resolve("scratch/pycache-no-read"));
        SupplementalFixtureCi.requireUnusedPycache(isolated);
        Files.writeString(cache.resolve("stale.pyc"), "unrecorded ambient bytecode");
        assertThrows(IOException.class, () -> SupplementalFixtureCi.requireUnusedPycache(isolated));
    }
    @Test void actualJsonRejectsWrongIntegerTokensAndMissingOrExtraContractFields() throws IOException {
        var counts = parse(cleanXml(2), "2 passed in 0.10s\n", List.of(FIRST, SECOND));
        String raw = ControlBuild.strictMapper().writeValueAsString(counts);
        for (String bad : List.of(raw.replace("\"junit_tests\":2", "\"junit_tests\":2.0"),
                raw.replace("\"junit_tests\":2", "\"junit_tests\":true"),
                raw.replace("\"junit_tests\":2,", ""), raw.replace("\"junit_tests\":2", "\"junit_tests\":2,\"unknown\":0"))) {
            assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(bad, SupplementalFixtureCi.PytestCounts.class));
        }
        var restored = ControlBuild.strictMapper().readValue(raw, SupplementalFixtureCi.PytestCounts.class);
        for (String bad : List.of(raw.replace("\"parent_passed\":2", "\"parent_passed\":1"),
                raw.replace("\"junit_tests\":2", "\"junit_tests\":3"), raw.replace("\"aggregate_failed\":0", "\"aggregate_failed\":1"),
                raw.replace(SECOND, FIRST))) assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(bad, SupplementalFixtureCi.PytestCounts.class));
        assertEquals(counts, restored);
    }
    @Test void reviewedProductionWalRequiresTheExactResourceBytes() throws IOException {
        assertThrows(IOException.class, () -> SupplementalFixtureCi.requireReviewedWal(root));
        Path target = root.resolve(SupplementalFixtureCi.WAL_RELATIVE); Files.createDirectories(target.getParent());
        try (var input = getClass().getResourceAsStream("/ci-reviewed-small-wal/ROOT-FIRST-NATURAL-H-WAL01.json")) {
            if (input == null) throw new IOException("Reviewed original WAL test resource missing");
            Files.copy(input, target);
        }
        var actual = SupplementalFixtureCi.requireReviewedWal(root);
        assertEquals(SupplementalFixtureCi.WAL_BYTES, actual.bytes()); assertEquals(SupplementalFixtureCi.WAL_SHA256, actual.sha256());
        assertThrows(IOException.class, () -> SupplementalFixtureCi.requireReviewedWalEnvironment(root, java.util.Map.of()));
        assertThrows(IOException.class, () -> SupplementalFixtureCi.requireReviewedWalEnvironment(root, java.util.Map.of(
                "XAR_WAL_DIAGNOSTIC_ACTUAL_WAL", target.toString(), "XAR_WAL_DIAGNOSTIC_ACTUAL_SHA256", "wrong")));
        assertEquals(actual, SupplementalFixtureCi.requireReviewedWalEnvironment(root, java.util.Map.of(
                "XAR_WAL_DIAGNOSTIC_ACTUAL_WAL", target.toString(), "XAR_WAL_DIAGNOSTIC_ACTUAL_SHA256", SupplementalFixtureCi.WAL_SHA256)));
        Files.writeString(target, "changed fixture");
        assertThrows(IOException.class, () -> SupplementalFixtureCi.requireReviewedWal(root));
    }
    @Test void finiteSharedProducerCliRejectsMissingUnknownAndDuplicateArguments() {
        assertThrows(IOException.class, () -> ControlCi.main(new String[] {"--verify-shared-fixture-junit", root.resolve("missing.xml").toString()}));
        assertThrows(IllegalArgumentException.class, () -> new SupplementalFixtureCi.Config(root, root.resolve("work"), root.resolve("python.exe"), root.resolve("scratch"), java.time.Instant.now().plusSeconds(60), "fixture", null));
        assertThrows(IllegalArgumentException.class, () -> new SupplementalFixtureCi.Config(root.resolve("repo"), root.resolve("work"), root.resolve("python.exe"), root.resolve("work/child"), java.time.Instant.now().plusSeconds(60), "fixture", null));
        assertThrows(IOException.class, () -> SupplementalFixtureCi.parseArguments(new String[0]));
        assertThrows(IOException.class, () -> SupplementalFixtureCi.parseArguments(new String[] {
                "--repo-root", root.toString(), "--work-root", root.toString(), "--python-executable", root.toString(),
                "--temporary-root", root.toString(), "--review-at-utc", "2026-10-22T00:00:00Z", "--unknown", "fixture-machine"}));
        assertThrows(IOException.class, () -> SupplementalFixtureCi.parseArguments(new String[] {
                "--repo-root", root.toString(), "--work-root", root.toString(), "--python-executable", root.toString(),
                "--temporary-root", root.toString(), "--review-at-utc", "2026-10-22T00:00:00Z", "--repo-root", root.toString()}));
    }
    private Path original(String resource, String name) throws IOException {
        Path result = root.resolve(name);
        try (var input = getClass().getResourceAsStream(resource)) {
            if (input == null) throw new IOException("Original pytest evidence resource unavailable: " + resource);
            try (var gzip = new GZIPInputStream(input)) { Files.write(result, gzip.readAllBytes()); }
        }
        return result;
    }
}
