package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.FileTime;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.SharedSourceFiles;

/** Actual temporary Windows file facts into the production DATA gate; no ManagedGameSession or Game birth is minted. */
final class NormalExitSettingsOriginTest {
    @TempDir Path temporary;
    private Path file(String name)throws Exception {
        Path path=temporary.resolve(name);
        Files.writeString(path,"actual unchanged launch settings bytes",StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        return path;
    }
    private static BigInteger latest(SharedSourceFiles.NativeFile file) {
        return new BigInteger(file.creationFiletimeDecimal()).max(new BigInteger(file.lastWriteFiletimeDecimal()));
    }
    @Test void actualNativeCreationRejectsALateCopyDespiteEqualLaunchBytes()throws Exception {
        Path original=file("immutable-settings.txt"),live=file("live-settings.txt");
        var snapshot=SharedSourceFiles.observe(original);var output=SharedSourceFiles.observe(live);
        assertEquals(snapshot.source().sha256(),output.source().sha256());
        assertNotEquals(snapshot.nativeFile().identityKey(),output.nativeFile().identityKey());
        // Synthetic boundary exercises the real comparison only; it is not a process or qualification fixture.
        var dataBirth=latest(snapshot.nativeFile()).add(BigInteger.ONE);
        assertDoesNotThrow(()->NormalExitSourceInventory.requireSnapshotBeforeGame(snapshot.nativeFile(),output.nativeFile(),dataBirth));
        var beforeCreation=new BigInteger(snapshot.nativeFile().creationFiletimeDecimal()).subtract(BigInteger.ONE);
        assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.requireSnapshotBeforeGame(snapshot.nativeFile(),output.nativeFile(),beforeCreation));
    }
    @Test void actualPostBirthLastWriteRejectsEvenWhenTheFileBytesAndNativeIdentityAreUnchanged()throws Exception {
        Path original=file("snapshot-write-time.txt"),live=file("live-write-time.txt");
        var before=SharedSourceFiles.observe(original);var output=SharedSourceFiles.observe(live);
        var dataBirth=latest(before.nativeFile()).add(BigInteger.ONE);
        Files.setLastModifiedTime(original,FileTime.from(Instant.now().plusSeconds(120)));
        var after=SharedSourceFiles.observe(original);
        assertEquals(before.source(),after.source());assertEquals(before.nativeFile().identityKey(),after.nativeFile().identityKey());
        assertTrue(new BigInteger(after.nativeFile().lastWriteFiletimeDecimal()).compareTo(dataBirth)>0);
        assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.requireSnapshotBeforeGame(after.nativeFile(),output.nativeFile(),dataBirth));
    }
    @Test void theLiveFileCannotQualifyAsAnIndependentSnapshotThroughAnotherReference()throws Exception {
        var actual=SharedSourceFiles.observe(file("one-actual-file.txt")).nativeFile();
        var dataBirth=latest(actual).add(BigInteger.ONE);
        assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.requireSnapshotBeforeGame(actual,actual,dataBirth));
    }
}
