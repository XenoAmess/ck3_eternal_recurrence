package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class G2SourceLimitProfileTest {
    private static final List<String> MODULES=List.of("contracts","local-service","native-diagnostics","war-policy","campaign-score",
            "finance-policy","event-policy","military-policy","late-outcome-reconciliation","governance-policy","planning-runtime",
            "closed-failure-recovery","admission-contracts","replenishment-policy","wave2-military","build-tools","wave2-runtime",
            "war-budget","wave2-finance","wave2-development","wave2-governance","wave2-planning","wave3-governance","wave3-planning",
            "wave2-events","wave2-prisoners","wave3-development","wave3-runtime","wave3-military","g2-research");
    @TempDir Path root;
    private void complete() throws IOException { complete(MODULES); }
    private void complete(List<String> selected) throws IOException {
        StringBuilder modules=new StringBuilder();
        for(String module:selected) {
            modules.append("<module>").append(module).append("</module>");
            Path dir=Files.createDirectory(root.resolve(module));
            Files.writeString(dir.resolve("pom.xml"),"<project xmlns='http://maven.apache.org/POM/4.0.0'><modelVersion>4.0.0</modelVersion><artifactId>"+module+"</artifactId></project>");
        }
        Files.writeString(root.resolve("pom.xml"),"<project xmlns='http://maven.apache.org/POM/4.0.0'><modelVersion>4.0.0</modelVersion><artifactId>ck3-control-parent</artifactId><modules>"+modules+"</modules></project>");
    }
    @Test void acceptsTheCompleteThirtyChildGraphWithoutChangingTheOldCohort() throws IOException {
        complete();
        assertEquals(31,ControlBuild.sourceManifest(root,ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023).size());
        assertThrows(IOException.class,()->ControlBuild.sourceManifest(root,ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022));
    }
    @Test void stabilizationAddsOnlyContinuityAndKeepsResearchHistoricalRoster() throws IOException {
        var modules = new java.util.ArrayList<>(MODULES);
        modules.add(modules.indexOf("contracts") + 1, "continuity-core"); complete(modules);
        var profile = ControlBuild.SourceLimitProfile.G2_STABILIZATION_20261023;
        assertEquals(32, ControlBuild.sourceManifest(root, profile).size());
        assertEquals(2304, profile.maxFiles()); assertEquals(32L << 20, profile.maxBytes());
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023));
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022));
        Path pom = root.resolve("pom.xml");
        Files.writeString(pom, Files.readString(pom).replace("<module>continuity-core</module>", ""));
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, profile));
    }
    @Test void stabilizationRejectsTheFirstFileBeyondTheSameFiniteExtent() throws IOException {
        var modules = new java.util.ArrayList<>(MODULES);
        modules.add(modules.indexOf("contracts") + 1, "continuity-core"); complete(modules);
        Path resources = Files.createDirectories(root.resolve("continuity-core/src/main/resources"));
        for (int index = 0; index < 2272; index++) Files.createFile(resources.resolve("input-" + index));
        var profile = ControlBuild.SourceLimitProfile.G2_STABILIZATION_20261023;
        assertEquals(2304, ControlBuild.sourceManifest(root, profile).size());
        Files.createFile(resources.resolve("first-excess"));
        IOException rejected = assertThrows(IOException.class, () -> ControlBuild.sourceManifest(root, profile));
        assertTrue(rejected.getMessage().contains("G2_STABILIZATION_20261023"));
    }
    @Test void rejectsMissingDeclaredChild() throws IOException {
        complete(); Path pom=root.resolve("pom.xml");
        Files.writeString(pom,Files.readString(pom).replace("<module>g2-research</module>",""));
        assertThrows(IOException.class,()->ControlBuild.sourceManifest(root,ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023));
    }
    @Test void rejectsUnregisteredOrdinaryFile() throws IOException {
        complete(); Files.writeString(root.resolve("unregistered.txt"),"must not escape source pins");
        assertThrows(IOException.class,()->ControlBuild.sourceManifest(root,ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023));
    }
    @Test void acceptsDirectoryRichSourcesWithinTheIndependentFileExtent() throws IOException {
        complete(); Path resources=Files.createDirectories(root.resolve("g2-research/src/main/resources"));
        for(int index=0;index<1200;index++) {
            Path directory=Files.createDirectory(resources.resolve("package-"+index));
            Files.createFile(directory.resolve("source.java"));
        }
        long entries;
        try(var paths=Files.walk(resources)) { entries=paths.count(); }
        assertTrue(entries>ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023.maxFiles());
        assertEquals(1231,ControlBuild.sourceManifest(root,ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023).size());
        assertEquals(2304,ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023.maxFiles());
        assertEquals(32L<<20,ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023.maxBytes());
        assertEquals(1536,ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022.maxFiles());
        assertEquals(24L<<20,ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022.maxBytes());
    }
    @Test void rejectsTheFirstFileBeyondTheFiniteExtent() throws IOException {
        complete(); Path resources=Files.createDirectories(root.resolve("g2-research/src/main/resources"));
        for(int index=0;index<2273;index++) Files.createFile(resources.resolve("input-"+index));
        assertEquals(2304,ControlBuild.sourceManifest(root,ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023).size());
        Files.createFile(resources.resolve("input-2273"));
        IOException rejected=assertThrows(IOException.class,()->ControlBuild.sourceManifest(root,ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023));
        assertTrue(rejected.getMessage().contains("G2_RESEARCH_20261023"));
    }
}
