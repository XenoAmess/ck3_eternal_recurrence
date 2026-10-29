package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.service.root.RootSavedCheckpointMaterials;

/** Actual controlled SAVE producer -> sole saved source store -> full physical Java material consumer. No live Game credit. */
final class RootSavedCheckpointMaterialsJavaCycleTest {
    @TempDir Path temporary;
    private static final String PIPE="\\\\.\\pipe\\action-writer-software-fixture";
    @Test void actualSaveMaterialBranchRetainsItsExactWitnessAndRerunsPhysicalReadUnderTheSameWriter()throws Exception {
        try(var fixture=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("cycle-material-consumer"),false)) {
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,fixture.service.checkpoint(fixture.request));
            fixture.saveBoundary(confirmed.pair());
            var consumer=new RootSavedCheckpointMaterials(fixture.actual.writer);
            fixture.actual.writer.locked(same->{
                var material=fixture.sources.load(confirmed.pair());
                var source=new RootSavedCheckpointMaterials.JavaSavedMaterial(fixture.sources,confirmed.pair(),material.witness(),PIPE,fixture.actual.root.resolve("profile"));
                var verified=consumer.verify(same,source);
                assertEquals(RootSavedCheckpointMaterials.Branch.JAVA_SAVED_MATERIAL,verified.branch());
                assertEquals(material.witness(),verified.requireJavaSavedMaterial().witness());
                assertThrows(Exception.class,verified::requireFirstJavaSavedMaterial);
                long sequence=same.head().state().sequence();consumer.requireCurrent(same,verified);assertEquals(sequence,same.head().state().sequence());
                Files.writeString(Path.of(confirmed.pair().save().reference().path()),"later actual SAVE changed these original physical bytes");
                assertThrows(Exception.class,()->consumer.requireCurrent(same,verified));return null;
            });
            assertEquals(1,fixture.actual.nativeActionWrites(),"physical validation cannot resubmit SAVE");
        }
    }
    @Test void sameManifestBytesWithReplacedFileIdentityCannotAcquireJavaMaterialQualification()throws Exception {
        try(var fixture=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("manifest-replaced"),false)) {
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,fixture.service.checkpoint(fixture.request));fixture.saveBoundary(confirmed.pair());
            var consumer=new RootSavedCheckpointMaterials(fixture.actual.writer);
            fixture.actual.writer.locked(same->{
                var material=fixture.sources.load(confirmed.pair());var source=new RootSavedCheckpointMaterials.JavaSavedMaterial(fixture.sources,confirmed.pair(),material.witness(),PIPE,fixture.actual.root.resolve("profile"));
                Path path=Path.of(material.reference().path());byte[] bytes=Files.readAllBytes(path);var modified=Files.getLastModifiedTime(path);
                Files.move(path,path.resolveSibling("retained-original-material.json"));Files.write(path,bytes);Files.setLastModifiedTime(path,modified);
                assertEquals(material.reference(),fixture.files.observe(path).orElseThrow().reference());
                assertNotEquals(material.witness().identity(),fixture.files.observe(path).orElseThrow().identity());
                long sequence=same.head().state().sequence();assertThrows(Exception.class,()->consumer.verify(same,source));assertEquals(sequence,same.head().state().sequence());return null;
            });assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
    @Test void sourceQualifiedSavedPairStillRejectsTheWrongCanonicalProfile()throws Exception {
        try(var fixture=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("wrong-profile"),false)) {
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,fixture.service.checkpoint(fixture.request));fixture.saveBoundary(confirmed.pair());
            var consumer=new RootSavedCheckpointMaterials(fixture.actual.writer);
            fixture.actual.writer.locked(same->{
                var material=fixture.sources.load(confirmed.pair());Path wrong=fixture.actual.root.resolve("other-profile");Files.createDirectories(wrong.resolve("save games"));
                var source=new RootSavedCheckpointMaterials.JavaSavedMaterial(fixture.sources,confirmed.pair(),material.witness(),PIPE,wrong);
                assertThrows(Exception.class,()->consumer.verify(same,source));return null;
            });assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
}
