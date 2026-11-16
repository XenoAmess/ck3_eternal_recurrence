package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.service.root.RootRestoreMaterials;

/** Real software SAVE/SEM/Driver provenance. No Game, restoration or adoption is claimed. */
final class SavedMaterialSemanticDriverPhaseTest {
    @TempDir Path temporary;

    @Test void actualSaveSelectsItsBeforeSemanticDriverAndRejectsForeignDriverAndChangedOriginals()throws Exception {
        Path root=temporary.resolve("phase");
        try(var f=new CheckpointSourceCompositionTest.Fixture(root,false,Clock.systemUTC(),Optional.empty(),Optional.empty(),List.of(),
                Duration.ofSeconds(90),root.resolve("profile"),Optional.empty(),
                Optional.of(CheckpointSourceCompositionTest.freshReconciliationReads()),false,true)) {
            byte[] command=org.xar.ck3.control.application.action.ActionCodec.encodeCommand(f.request.saveCommand());
            Instant deadline=f.request.saveCommand().deadline();
            var result=f.service.checkpoint(f.request);
            if(result instanceof CheckpointResult.Unknown unknown) {
                var action=unknown.action().orElseThrow();assertTrue(action.ack().orElseThrow().nativeOk(),result::toString);
                result=f.service.queryOriginal(unknown.actionId(),Instant.now().plusSeconds(30));
            }
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,result,result.toString());
            assertArrayEquals(command,org.xar.ck3.control.application.action.ActionCodec.encodeCommand(confirmed.action().command()));
            assertEquals(deadline,confirmed.action().command().deadline());f.saveBoundary(confirmed.pair());
            f.actual.writer.locked(same->{
                var material=f.sources.load(confirmed.pair());String head=same.head().digest();
                var saved=material.savedDriver();var before=material.requireSemanticDriver(same,saved);
                byte[] original=f.actual.archive.readArtifact(same,material.sourceSemantic().originalDriver(),WriterContracts.MAX_PIN_BYTES);
                assertArrayEquals(original,before.encode());
                assertEquals(before.commandHistory().size()+1,saved.commandHistory().size());
                for(int i=0;i<before.commandHistory().size();i++)
                    assertArrayEquals(before.commandHistory().get(i).originalRow().json(),saved.commandHistory().get(i).originalRow().json());
                assertEquals(confirmed.pair().historyIndex(),saved.commandHistory().getLast().index());
                assertNotEquals(before.lastCheckpoint(),saved.lastCheckpoint());
                assertArrayEquals(saved.encode(),f.files.read(confirmed.pair().driver(),DriverCheckpointStore.MAX_DRIVER_BYTES));
                assertArrayEquals(before.encode(),select(same,material,saved).encode(),"both Root callers use this same ordinary selector");
                var session=saved.session();var foreign=new DriverStateSnapshot.Complete(
                        new DriverStateSnapshot.Session(session.pipeName(),session.bridgePid(),session.actorId(),session.episodeRunId()+"-foreign"),
                        saved.commandHistory(),saved.lastCheckpoint(),saved.rollbackWarFailure(),saved.managedRestoreTransaction(),
                        saved.successionExpectation(),saved.successionLifecycle(),saved.campaignGoal(),saved.rollbackWarFailures());
                assertThrows(Exception.class,()->select(same,material,foreign));
                changedCopy(Path.of(material.sourceSemantic().originalDriver().path()),true,
                        ()->assertThrows(Exception.class,()->material.requireSemanticDriver(same,saved)));
                changedCopy(Path.of(material.pair().driver().reference().path()),false,
                        ()->assertThrows(Exception.class,()->material.requireSemanticDriver(same,saved)));
                changedCopy(Path.of(material.reference().path()),false,
                        ()->assertThrows(Exception.class,()->material.requireSemanticDriver(same,saved)));
                assertArrayEquals(before.encode(),material.requireSemanticDriver(same,saved).encode());
                assertEquals(head,same.head().digest());return null;
            });
            assertEquals(1,f.actual.nativeActionWrites(),"all checks are DATA-only; the original SAVE is not replayed");
        }
    }
    private static DriverStateSnapshot.Complete select(ContinuityStorePort.Session same,SavedCheckpointMaterial material,
            DriverStateSnapshot.Complete saved)throws IOException {
        try {
            var method=RootRestoreMaterials.class.getDeclaredMethod("semanticDriver",ContinuityStorePort.Session.class,
                    SavedCheckpointMaterial.class,DriverStateSnapshot.Complete.class);
            method.setAccessible(true);return (DriverStateSnapshot.Complete)method.invoke(null,same,material,saved);
        }catch(InvocationTargetException failure) {
            if(failure.getCause() instanceof IOException io)throw io;
            if(failure.getCause() instanceof RuntimeException runtime)throw runtime;
            throw new IOException(failure.getCause());
        }catch(ReflectiveOperationException failure){throw new IOException(failure);}
    }
    @FunctionalInterface private interface Check {void run()throws IOException;}
    private static void changedCopy(Path path,boolean changeBytes,Check check)throws IOException {
        byte[] exact=Files.readAllBytes(path);Path original=path.resolveSibling(path.getFileName()+".held-original");
        Files.move(path,original);
        try {
            byte[] replacement=exact.clone();if(changeBytes)replacement[replacement.length-1]^=1;
            Files.write(path,replacement);check.run();
        }finally {Files.deleteIfExists(path);Files.move(original,path);}
    }
}
