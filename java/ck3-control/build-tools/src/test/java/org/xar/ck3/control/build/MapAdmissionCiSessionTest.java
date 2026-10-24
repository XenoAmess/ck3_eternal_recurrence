package org.xar.ck3.control.build;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertEquals;

/** The actual new public producer entrypoint must refuse missing scope before opening a repository or creating metadata. */
final class MapAdmissionCiSessionTest {
    @TempDir Path directory;
    @Test void missingRootArtifactConfigurationCannotCreateASessionOrReadMissingInputs() {
        Path work = directory.resolve("must-not-create");
        var config = new MapAdmissionCi.Config(directory.resolve("missing-repository"), directory.resolve("missing-build.json"), work,
                directory.resolve("missing-java.exe"), directory.resolve("missing-python.exe"), Instant.now().plusSeconds(30), 28089);
        assertThrows(IllegalArgumentException.class, () -> MapAdmissionCi.startWithProjection(config, null));
        assertFalse(Files.exists(work));
    }
    @Test void missingSoftwareFixtureCannotOpenInputsOrCreateAHost() {
        Path work = directory.resolve("software-must-not-create");
        var config = new MapAdmissionCi.Config(directory.resolve("missing-repository"), directory.resolve("missing-build.json"), work,
                directory.resolve("missing-java.exe"), directory.resolve("missing-python.exe"), Instant.now().plusSeconds(30), 28089);
        assertThrows(IllegalArgumentException.class, () -> MapAdmissionCi.retainForSoftwareFixtures(config, null));
        assertFalse(Files.exists(work));
    }
    @Test void projectionConsumersReceiveTheActualProjectionReceiptAlongsideTheOriginalMapReceipt() throws Exception {
        Path map = directory.resolve("map-running.json"), projection = directory.resolve("projection-running.json");
        Files.writeString(map, "original map service receipt"); Files.writeString(projection, "original projection service receipt");
        var mapRef = ControlBuild.FileRef.measure(map); var projectionRef = ControlBuild.FileRef.measure(projection);
        var base = java.util.Map.of("XAR_JAVA_PROJECTION_SERVICE_EVIDENCE", "inherited stale receipt");
        var actual = MapAdmissionCi.serviceEnvironment(base, mapRef, projectionRef);
        assertEquals(mapRef.path(), actual.get("XAR_JAVA_MAP_SERVICE_EVIDENCE"));
        assertEquals(projectionRef.path(), actual.get("XAR_JAVA_PROJECTION_SERVICE_EVIDENCE"));
        assertFalse(MapAdmissionCi.serviceEnvironment(base, mapRef, null).containsKey("XAR_JAVA_PROJECTION_SERVICE_EVIDENCE"));
    }
    @Test void borrowedMapSoftwareRequiresItsTypedHostBeforeOpeningFilesOrCreatingMetadata() {
        Path work = directory.resolve("borrow-must-not-create");
        var config = new MapAdmissionCi.Config(directory.resolve("missing-repository"), directory.resolve("missing-capture.json"), work,
                directory.resolve("missing-java.exe"), directory.resolve("missing-python.exe"), Instant.now().plusSeconds(30), 28089);
        assertThrows(IllegalArgumentException.class, () -> MapAdmissionCi.borrowForMapVerticalSoftware(config, null));
        assertFalse(Files.exists(work));
    }
    @Test void originalWholeGroupKeepsBothModulesAndAllSixConsumersWithoutMethodSelectors() {
        var config = new MapAdmissionCi.Config(directory, directory.resolve("capture.json"), directory.resolve("work"),
                directory.resolve("java.exe"), directory.resolve("python.exe"), Instant.now().plusSeconds(30), 28089);
        var strict = MapAdmissionCi.originalStaticArguments(config);
        assertEquals(directory.resolve("tools/g2_saved_campaign/java_map_admission_client_v1.py").toString(), strict.get(strict.size() - 2));
        assertEquals(directory.resolve("tools/g2_saved_campaign/test_java_map_admission_v1.py").toString(), strict.getLast());
        assertEquals(java.util.List.of("-B", "-X", "utf8", "-m", "unittest", "-v", "tools.g2_saved_campaign.test_java_map_admission_v1"), MapAdmissionCi.originalConsumerArguments());
        MapAdmissionCi.requireOriginalConsumerSummary("actual cases\nRan 6 tests in 1.234s\n\nOK\n");
        for (String wrong : java.util.List.of("Ran 5 tests in 1s\n\nOK", "Ran 6 tests in 1s\n\nOK (skipped=1)",
                "Ran 6 tests in 1s\n\nOK (expected failures=1)", "Ran 6 tests in 1s\n\nFAILED (errors=1)")) {
            assertThrows(IllegalStateException.class, () -> MapAdmissionCi.requireOriginalConsumerSummary("actual cases\n" + wrong));
        }
        assertThrows(NullPointerException.class, () -> new MapAdmissionCi.OriginalMapConsumerGroup(null, null));
    }
}
