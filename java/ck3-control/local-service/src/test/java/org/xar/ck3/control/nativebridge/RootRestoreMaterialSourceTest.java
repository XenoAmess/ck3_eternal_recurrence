package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.service.root.RootRestoreMaterials;
import org.xar.ck3.control.service.root.RootSavedCheckpointMaterials;

/** Actual canonical SAVE material enters Root's shared source gate; no synthetic FIRST proof or managed Game is minted. */
final class RootRestoreMaterialSourceTest {
    @TempDir Path temporary;
    private static final String PIPE="\\\\.\\pipe\\action-writer-software-fixture";
    @Test void rootConsumesTheExactPrivateMaterialAndItsOriginalSemanticWithoutAnOrdinaryProofAssumption()throws Exception {
        try(var fixture=materialFixture(temporary.resolve("root-material-source"))) {
            var pair=save(fixture);var ready=fixture.actual.collector.checkpoint("software-save-lineage").observe(Instant.now().plusSeconds(30));
            fixture.actual.writer.locked(same->{
                SavedCheckpointMaterial material=fixture.materials.currentPhysical(same,pair);
                var request=new RestoreCheckpointService.Request("root-material-source",pair,ready,same.head().digest(),Instant.now().plusSeconds(30),material);
                long sequence=same.head().state().sequence();
                assertSame(material,RootRestoreMaterials.requireRetainedSource(same,fixture.materials,request,material.savedDriver()));
                assertEquals(material.sourceSemantic(),OrdinaryCycleTransitions.semanticFromJson(OrdinaryCycleTransitions.semanticToJson(material.sourceSemantic())));
                assertEquals(pair,CheckpointPairCodec.decode(CheckpointPairCodec.encode(pair)));assertEquals(sequence,same.head().state().sequence());return null;
            });assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
    @Test void rootSourceGateRetainsManifestFileIdentityEvenWhenCompleteBytesAreRestored()throws Exception {
        try(var fixture=materialFixture(temporary.resolve("root-replaced-material"))) {
            var pair=save(fixture);var ready=fixture.actual.collector.checkpoint("software-save-lineage").observe(Instant.now().plusSeconds(30));
            fixture.actual.writer.locked(same->{
                var material=fixture.materials.currentPhysical(same,pair);var request=new RestoreCheckpointService.Request("root-replaced-material",pair,ready,same.head().digest(),Instant.now().plusSeconds(30),material);
                Path original=Path.of(material.reference().path());byte[] bytes=Files.readAllBytes(original);var modified=Files.getLastModifiedTime(original);
                Files.move(original,original.resolveSibling("retained-original-root-material.json"));Files.write(original,bytes);Files.setLastModifiedTime(original,modified);
                assertEquals(material.reference(),fixture.files.observe(original).orElseThrow().reference());
                assertNotEquals(material.witness().identity(),fixture.files.observe(original).orElseThrow().identity());
                long sequence=same.head().state().sequence();assertThrows(Exception.class,()->RootRestoreMaterials.requireRetainedSource(same,fixture.materials,request,material.savedDriver()));
                assertEquals(sequence,same.head().state().sequence());return null;
            });assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
    @Test void rootRejectsAnotherConfiguredAggregateAndAnAlteredCompleteSavedDriver()throws Exception {
        try(var fixture=materialFixture(temporary.resolve("root-source-owner"))) {
            var pair=save(fixture);
            try(var other=materialFixture(temporary.resolve("root-source-foreign"))) {
                var ready=fixture.actual.collector.checkpoint("software-save-lineage").observe(Instant.now().plusSeconds(30));
                fixture.actual.writer.locked(same->{
                    var material=fixture.materials.currentPhysical(same,pair);var request=new RestoreCheckpointService.Request("root-source-owner",pair,ready,same.head().digest(),Instant.now().plusSeconds(30),material);
                    assertThrows(Exception.class,()->RootRestoreMaterials.requireRetainedSource(same,other.materials,request,material.savedDriver()));
                    var original=material.savedDriver();var session=original.session();
                    var wrong=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session(session.pipeName(),session.bridgePid(),session.actorId().add(java.math.BigInteger.ONE),session.episodeRunId()),
                            original.commandHistory(),original.lastCheckpoint(),original.rollbackWarFailure(),original.managedRestoreTransaction(),original.successionExpectation(),original.successionLifecycle(),original.campaignGoal(),original.rollbackWarFailures());
                    assertThrows(Exception.class,()->RootRestoreMaterials.requireRetainedSource(same,fixture.materials,request,wrong));return null;
                });
                assertEquals(0,other.actual.nativeActionWrites());
            }
            assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
    @Test void physicalFirstBranchCannotImportAnOrdinaryManifestAsABaselinedFirstSave()throws Exception {
        try(var fixture=materialFixture(temporary.resolve("root-not-first-baseline"))) {
            var pair=save(fixture);var physical=new RootSavedCheckpointMaterials(fixture.actual.writer);
            fixture.actual.writer.locked(same->{
                var material=fixture.materials.currentPhysical(same,pair);
                var source=new RootSavedCheckpointMaterials.JavaFirstSavedMaterial(fixture.firstSources,pair,material.witness(),PIPE,fixture.actual.root.resolve("profile"));
                assertThrows(Exception.class,()->physical.verify(same,source));return null;
            });assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
    @Test void rootRejectsRetainedSourceWhenOriginalMaterialFileDisappears()throws Exception {
        try(var fixture=materialFixture(temporary.resolve("root-missing-material"))) {
            var pair=save(fixture);var ready=fixture.actual.collector.checkpoint("software-save-lineage").observe(Instant.now().plusSeconds(30));
            fixture.actual.writer.locked(same->{
                var material=fixture.materials.currentPhysical(same,pair);
                var request=new RestoreCheckpointService.Request("root-missing-material",pair,ready,same.head().digest(),Instant.now().plusSeconds(30),material);
                Path original=Path.of(material.reference().path());
                Files.delete(original);
                long sequence=same.head().state().sequence();
                assertThrows(Exception.class,()->RootRestoreMaterials.requireRetainedSource(same,fixture.materials,request,material.savedDriver()));
                assertEquals(sequence,same.head().state().sequence());return null;
            });assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
    @Test void retainedHistoricalMaterialDoesNotGrantPhysicalRestoreAfterSaveDisappears()throws Exception {
        try(var fixture=materialFixture(temporary.resolve("root-missing-physical"))) {
            var pair=save(fixture);var ready=fixture.actual.collector.checkpoint("software-save-lineage").observe(Instant.now().plusSeconds(30));
            fixture.actual.writer.locked(same->{
                var material=fixture.materials.currentPhysical(same,pair);
                var request=new RestoreCheckpointService.Request("root-missing-physical",pair,ready,same.head().digest(),Instant.now().plusSeconds(30),material);
                Path physical=Path.of(pair.save().reference().path());
                Files.delete(physical);
                long sequence=same.head().state().sequence();
                assertSame(material,RootRestoreMaterials.requireRetainedSource(same,fixture.materials,request,material.savedDriver()));
                assertThrows(java.io.IOException.class,()->material.requirePhysical(same));
                assertEquals(sequence,same.head().state().sequence());return null;
            });assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
    private static CheckpointSourceCompositionTest.Fixture materialFixture(Path root)throws Exception {
        return new CheckpointSourceCompositionTest.Fixture(root,false,Clock.systemUTC(),Optional.empty(),Optional.empty(),List.of(),java.time.Duration.ofMinutes(1));
    }
    private static CheckpointPair save(CheckpointSourceCompositionTest.Fixture fixture)throws Exception {
        var before=Instant.now();
        var result=fixture.service.checkpoint(fixture.request);
        var after=Instant.now();
        var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,result,()->{
            var actionId = fixture.request.saveCommand().actionId();
            var observations = fixture.actual.getGuardObservations(actionId);
            var obsStr = observations.stream().map(o -> "[" + o.before() + "->" + o.after() + " head=" + o.headSequence()+":"+o.headDigest() + " deadline=" + o.callerDeadline() + " thrown=" + o.thrownClass() + ":" + o.thrownMessage() + "]").collect(java.util.stream.Collectors.joining(", "));
            return "result="+result+" before="+before+" after="+after+" deadline="+fixture.request.saveCommand().deadline()+" lastCheckpointObservationDeadline="+fixture.lastCheckpointObservationDeadline.get()+" nativeActionWrites="+fixture.actual.nativeActionWrites()+" guardObservations="+obsStr;
        });
        fixture.saveBoundary(confirmed.pair());fixture.actual.ready();return confirmed.pair();
    }
}
