package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;

/** Real owned file copies only, never presented as Native SAVE or game-format success. */
final class CurrentCoreCheckpointArchiveTest {
    @TempDir Path dir;
    @Test void independentFirstArchiveSurvivesChangedSecondMaterial()throws Exception {
        var files=new NativeCheckpointFiles();Path source=dir.resolve("xar_checkpoint.ck3"),a=dir.resolve("e1.ck3"),b=dir.resolve("e2.ck3");
        var empty=CurrentCoreCheckpointArchive.preflight(files,source,a,4096,Optional.empty(),Optional.empty());assertTrue(empty.isEmpty());
        Files.writeString(source,"SYNTHETIC E1 FILE MATERIAL");
        var one=CurrentCoreCheckpointArchive.observeAndCopyChanged(files,source,empty,a,Instant.now().plusSeconds(5),4096,1,100);
        assertEquals(one.source().reference().sha256(),one.archive().reference().sha256());assertNotEquals(one.source().identity().fileId(),one.archive().identity().fileId());
        var before=CurrentCoreCheckpointArchive.preflight(files,source,b,4096,Optional.of(one.source()),Optional.of(one.archive()));
        Files.writeString(source,"SYNTHETIC E2 NEW FILE MATERIAL");
        var two=CurrentCoreCheckpointArchive.observeAndCopyChanged(files,source,before,b,Instant.now().plusSeconds(5),4096,1,100);
        assertNotEquals(one.source().reference().sha256(),two.source().reference().sha256());files.verify(one.archive());
        assertEquals("SYNTHETIC E1 FILE MATERIAL",Files.readString(a));assertEquals("SYNTHETIC E2 NEW FILE MATERIAL",Files.readString(b));
    }
    @Test void unknownExistingFixedFileAndExistingArchiveAreRejectedBeforeCopy()throws Exception {
        var files=new NativeCheckpointFiles();Path source=dir.resolve("xar_checkpoint.ck3"),archive=dir.resolve("e1.ck3");Files.writeString(source,"original");
        assertThrows(IOException.class,()->CurrentCoreCheckpointArchive.preflight(files,source,archive,4096,Optional.empty(),Optional.empty()));
        Files.writeString(archive,"keep original archive");
        assertThrows(IOException.class,()->CurrentCoreCheckpointArchive.preflight(files,source,archive,4096,Optional.empty(),Optional.empty()));
        assertEquals("original",Files.readString(source));assertEquals("keep original archive",Files.readString(archive));
    }
    @Test void unchangedOldSourceNeverPassesNewMaterialAndTamperedArchiveBlocksNextPreflight()throws Exception {
        var files=new NativeCheckpointFiles();Path source=dir.resolve("xar_checkpoint.ck3"),a=dir.resolve("e1.ck3"),b=dir.resolve("e2.ck3");
        Files.writeString(source,"synthetic old material");var old=files.observe(source).orElseThrow();var retained=files.copyNew(old,a);
        assertThrows(IOException.class,()->CurrentCoreCheckpointArchive.observeAndCopyChanged(files,source,Optional.of(old),b,Instant.now().plusSeconds(2),4096,1,100));assertFalse(Files.exists(b));
        Files.writeString(a,"tampered archive");
        assertThrows(IOException.class,()->CurrentCoreCheckpointArchive.preflight(files,source,b,4096,Optional.of(old),Optional.of(retained)));
    }
    @Test void sourceByteBoundIsCheckedBeforePhysicalPublication()throws Exception {
        var files=new NativeCheckpointFiles();Path source=dir.resolve("xar_checkpoint.ck3"),a=dir.resolve("e1.ck3");Files.writeString(source,"more-than-four-bytes");
        assertThrows(IOException.class,()->CurrentCoreCheckpointArchive.preflight(files,source,a,4,Optional.empty(),Optional.empty()));assertFalse(Files.exists(a));
    }
}
