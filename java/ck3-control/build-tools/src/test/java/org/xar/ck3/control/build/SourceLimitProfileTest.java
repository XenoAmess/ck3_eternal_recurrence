package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Exercises the actual pinned source producer, strict receipt reader and postcheck. */
final class SourceLimitProfileTest {
    @TempDir Path temporary;

    @Test void explicitExistingCohortAdmitsRealNineMiBAndRetainsDefaultEightMiBRefusal() throws Exception {
        Path root = parent("contracts", "finance-policy", "war-policy");
        for (String module : List.of("contracts", "finance-policy", "war-policy")) {
            Files.write(root.resolve(module).resolve("src/data.bin"), new byte[3 << 20]);
        }
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root));
        var actual = ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022);
        assertEquals(7, actual.size());
        assertTrue(actual.stream().mapToLong(ControlBuild.FileRef::bytes).sum() > (8L << 20));
        assertEquals(ControlBuild.SourceState.MATCH, ControlBuild.postcheckSource(root, actual,
                ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022).state());
        assertEquals(ControlBuild.SourceState.UNKNOWN, ControlBuild.postcheckSource(root, actual).state());
        Files.write(root.resolve("contracts/src/data.bin"), new byte[] {1});
        assertEquals(ControlBuild.SourceState.MISMATCH, ControlBuild.postcheckSource(root, actual,
                ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022).state());
    }

    @Test void actualSourceGraphPreservesExactSourceAndDotMvnClosureAcrossCanonicalRoots() throws Exception {
        Path root = parent("contracts");
        Files.createDirectories(root.resolve(".mvn"));
        Files.writeString(root.resolve(".mvn/maven.config"), "-ntp\n");
        Files.createDirectories(root.resolve("contracts/src/test/resources"));
        Path golden = root.resolve("contracts/src/test/resources/producer-golden.json");
        Files.writeString(golden, "{\"value\":1.0}\n");
        Path hidden = root.resolve("contracts/src/.source-marker"); Files.writeString(hidden, "pinned");
        Files.createDirectories(root.resolve("contracts/src/main/resources/META-INF/services"));
        Path services = root.resolve("contracts/src/main/resources/META-INF/services/org.example.ProjectionPortCatalog");
        Files.writeString(services, "org.example.ExistingCatalog\n");
        var actual = ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022);
        assertEquals(6, actual.size());
        for (Path path : List.of(root.resolve("pom.xml"), root.resolve(".mvn/maven.config"),
                root.resolve("contracts/pom.xml"), golden, hidden, services)) {
            assertTrue(actual.contains(ControlBuild.FileRef.measure(path)));
        }
        Files.writeString(golden, "{\"value\":2.0}\n");
        assertEquals(ControlBuild.SourceState.MISMATCH, ControlBuild.postcheckSource(root, actual,
                ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022).state());
    }

    @Test void finiteProfileRejectsUnknownModulesExternalSourceRootsAndRepeatedModules() throws Exception {
        Path root = parent("contracts");
        Path pom = root.resolve("pom.xml"); String original = Files.readString(pom);
        Files.writeString(pom, original.replace("<module>contracts</module>", "<module>new-domain</module>"));
        Files.createDirectories(root.resolve("new-domain/src"));
        Files.writeString(root.resolve("new-domain/pom.xml"), project("new-domain", ""));
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022));
        Files.writeString(pom, original);
        Path child = root.resolve("contracts/pom.xml");
        for (String build : List.of(
                "<build><sourceDirectory>../../staging/src</sourceDirectory></build>",
                "<build><testSourceDirectory>../../staging/test</testSourceDirectory></build>",
                "<build><plugins><plugin><artifactId>build-helper-maven-plugin</artifactId></plugin></plugins></build>")) {
            Files.writeString(child, project("contracts", build));
            assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022));
        }
        Files.writeString(child, project("contracts", ""));
        Files.writeString(pom, original.replace("<module>contracts</module>", "<module>contracts</module><module>contracts</module>"));
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022));
    }

    @Test void expandedSourceProfilePreservesPerModuleEightMiBLimit() throws Exception {
        Path root = parent("contracts");
        Files.write(root.resolve("contracts/src/too-large.bin"), new byte[(8 << 20) + 1]);
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022));
    }

    @Test void expandedSourceProfileRejectsActualAggregateByteOverflow() throws Exception {
        Path root = parent("contracts", "finance-policy", "war-policy", "campaign-score");
        for (String module : List.of("contracts", "finance-policy", "war-policy", "campaign-score")) {
            Files.write(root.resolve(module).resolve("src/data.bin"), new byte[7 << 20]);
        }
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022));
    }

    @Test void expandedSourceProfileAdmitsOverThousandFilesAndRejectsFiniteCountOverflow() throws Exception {
        Path root = parent("contracts"); Path src = root.resolve("contracts/src");
        for (int index = 0; index < 1001; index++) Files.writeString(src.resolve("file-" + index), "x");
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root));
        assertEquals(1003, ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022).size());
        for (int index = 1001; index < 1536; index++) Files.writeString(src.resolve("file-" + index), "x");
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022));
    }

    @Test void strictReceiptRoundTripRequiresTypedProfileAndCurrentVersionWithoutCoercion() throws Exception {
        Path file = temporary.resolve("ref"); Files.writeString(file, "x");
        var ref = ControlBuild.FileRef.measure(file);
        var postcheck = new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null);
        var receipt = new ControlBuild.BuildReceipt(ControlBuild.SCHEMA, "software-fixture", "2026-10-22T16:00:00Z", "RED",
                temporary.toString(), temporary.toString(), temporary.toString(), postcheck, postcheck,
                ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022,
                List.of(ref), List.of(ref), List.of(), List.of(ref), ref, null, ref, null, null, Map.of(), "not executed");
        var mapper = ControlBuild.strictMapper(); String body = mapper.writeValueAsString(receipt);
        assertEquals(receipt, mapper.readValue(body, ControlBuild.BuildReceipt.class));
        for (String token : List.of("null", "true", "1", "1.0", "\"UNKNOWN\"")) {
            String bad = body.replace("\"source_limit_profile\":\"EXISTING_MIGRATION_20261022\"", "\"source_limit_profile\":" + token);
            assertThrows(JsonProcessingException.class, () -> mapper.readValue(bad, ControlBuild.BuildReceipt.class));
        }
        assertThrows(JsonProcessingException.class, () -> mapper.readValue(
                body.replace("\"source_limit_profile\":\"EXISTING_MIGRATION_20261022\",", ""), ControlBuild.BuildReceipt.class));
        assertThrows(JsonProcessingException.class, () -> mapper.readValue(
                body.replace("actual-build/v5", "actual-build/v4"), ControlBuild.BuildReceipt.class));
    }

    private Path parent(String... modules) throws IOException {
        Path root = Files.createTempDirectory(temporary, "reactor-"); List<String> declarations = new ArrayList<>();
        for (String module : modules) {
            declarations.add("<module>" + module + "</module>");
            Files.createDirectories(root.resolve(module).resolve("src"));
            Files.writeString(root.resolve(module).resolve("pom.xml"), project(module, ""));
        }
        Files.writeString(root.resolve("pom.xml"), project("ck3-control-parent", "<modules>" + String.join("", declarations) + "</modules>"));
        return root;
    }

    private static String project(String artifact, String contents) {
        return "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion><artifactId>"
                + artifact + "</artifactId>" + contents + "</project>";
    }
}
