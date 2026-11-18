package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.FileTime;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Tiny real Windows files. A writable profile clone never changes the original pair role. */
final class NativeCheckpointCloneCustodyTest {
    @TempDir Path temporary;

    @Test void retainedOriginalPairProtectsItsOwnFilesWhileCloneSaveObservationStaysFresh()throws Exception {
        var files=new NativeCheckpointFiles();
        Path source=temporary.resolve("original/xar_checkpoint.ck3");Files.createDirectories(source.getParent());
        Path driver=temporary.resolve("original/driver.json"),ack=temporary.resolve("original/ack.json");
        Files.writeString(source,"selected original save");Files.writeString(driver,"original driver");Files.writeString(ack,"original ack");
        var pair=new CheckpointPair(files.observe(source).orElseThrow(),files.observe(driver).orElseThrow(),frame(),
                "clone-custody-lineage",1,"old-save-action",files.observe(ack).orElseThrow().reference(),Instant.parse("2026-01-01T00:00:00Z"));
        var originalNative=SharedSourceFiles.observe(source).nativeFile();
        Path target=temporary.resolve("new-profile/save games/xar_checkpoint.ck3");Files.createDirectories(target.getParent());
        var initialClone=files.copyNew(pair.save(),target);
        var cloneNative=SharedSourceFiles.observe(target).nativeFile();
        assertEquals(pair.save().reference().bytes(),initialClone.reference().bytes());
        assertEquals(pair.save().reference().sha256(),initialClone.reference().sha256());
        assertEquals(originalNative.volumeSerialDecimal(),cloneNative.volumeSerialDecimal());
        assertNotEquals(originalNative.identityKey(),cloneNative.identityKey());
        assertNotEquals(pair.save().identity().fileId(),initialClone.identity().fileId());

        try(var scope=files.beginVerification(pair)) {
            scope.verify(pair);
            assertWriteDenied(source);assertWriteDenied(driver);
            assertThrows(IOException.class,()->Files.delete(source));
            assertThrows(IOException.class,()->Files.delete(driver));
            byte[] saved="new independently observed profile SAVE output".getBytes(StandardCharsets.UTF_8);
            try(var output=FileChannel.open(target,StandardOpenOption.READ,StandardOpenOption.WRITE)) {
                output.truncate(0);ByteBuffer pending=ByteBuffer.wrap(saved);
                while(pending.hasRemaining())output.write(pending);output.force(true);
            }
            Files.setLastModifiedTime(target,FileTime.fromMillis(946684800000L));
            var actual=scope.observe(target).orElseThrow();
            assertEquals(initialClone.reference().path(),actual.reference().path());
            assertEquals(saved.length,actual.reference().bytes());
            assertEquals(DriverCheckpointStore.sha256(saved),actual.reference().sha256());
            assertNotEquals(initialClone.reference().sha256(),actual.reference().sha256());
            assertEquals(initialClone.identity().fileId(),actual.identity().fileId());
            assertNotEquals(initialClone.identity().mtimeNs(),actual.identity().mtimeNs());
            assertEquals("946684800000000000",actual.identity().mtimeNs());
            assertThrows(IOException.class,()->files.verify(initialClone));
            scope.verify(pair);
            assertEquals(pair.save(),files.observe(source).orElseThrow());
            assertEquals(pair.driver(),files.observe(driver).orElseThrow());
            assertArrayEquals(Files.readAllBytes(driver),scope.read(pair.driver(),4096));
            assertEquals(originalNative,SharedSourceFiles.observe(source).nativeFile());
            assertWriteDenied(source);
        }
        // Only the original pair was leased; closing releases both original file handles.
        try(var sourceWriter=FileChannel.open(source,StandardOpenOption.WRITE);
            var driverWriter=FileChannel.open(driver,StandardOpenOption.WRITE)) {
            assertTrue(sourceWriter.isOpen());assertTrue(driverWriter.isOpen());
        }
        assertEquals(pair.save(),files.observe(source).orElseThrow());
    }
    private static void assertWriteDenied(Path path) {
        assertThrows(IOException.class,()->{
            try(var unexpected=FileChannel.open(path,StandardOpenOption.READ,StandardOpenOption.WRITE)) {
                fail("original pair deny-write lease was absent: "+unexpected);
            }
        });
    }
    private static ProposalLifecycle.ObservationIdentity frame() {
        return new ProposalLifecycle.ObservationIdentity("software-clone-custody",
                new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.valueOf(240)),
                        "software:1",BigInteger.ONE,"clone-custody-episode"),1);
    }
}
