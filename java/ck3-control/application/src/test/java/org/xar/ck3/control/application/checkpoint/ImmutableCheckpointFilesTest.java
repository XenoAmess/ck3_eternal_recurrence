package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

public final class ImmutableCheckpointFilesTest {
    @TempDir Path temporary;
    @Test void completePublicationNeverOverwritesAnExistingFileOrChangesItsIdentity() throws Exception {
        var files=new NativeCheckpointFiles();Path target=temporary.resolve("immutable.json");byte[] first="original".getBytes(StandardCharsets.UTF_8);
        var published=files.createNew(target,first);assertArrayEquals(first,files.read(published,1024));
        assertThrows(IOException.class,()->files.createNew(target,"replacement".getBytes(StandardCharsets.UTF_8)));
        files.verify(published);assertArrayEquals(first,Files.readAllBytes(target));
        try(var entries=Files.list(temporary)){assertEquals(1,entries.count());}
    }
    @Test void concurrentPublishersHaveOneCompleteWinnerAndNoPartialVisibleTarget() throws Exception {
        var files=new NativeCheckpointFiles();Path target=temporary.resolve("race.json");CountDownLatch start=new CountDownLatch(1);
        byte[] first="a".repeat(65536).getBytes(StandardCharsets.UTF_8);byte[] second="b".repeat(65536).getBytes(StandardCharsets.UTF_8);
        try(var executor=Executors.newFixedThreadPool(2)) {
            var one=executor.submit(()->publish(files,target,first,start));var two=executor.submit(()->publish(files,target,second,start));start.countDown();
            assertNotEquals(one.get(),two.get());byte[] actual=Files.readAllBytes(target);
            assertTrue(java.util.Arrays.equals(first,actual)||java.util.Arrays.equals(second,actual));
        }
        try(var entries=Files.list(temporary)){assertEquals(1,entries.count());}
    }
    @Test void missingParentAndInvalidBytesCannotLeaveAnEmptyImmutableTarget() throws Exception {
        var files=new NativeCheckpointFiles();Path target=temporary.resolve("missing").resolve("seed.json");
        assertThrows(IOException.class,()->files.createNew(target,"x".getBytes(StandardCharsets.UTF_8)));assertFalse(Files.exists(target));
        assertThrows(IOException.class,()->files.createNew(temporary.resolve("empty"),new byte[0]));
        try(var entries=Files.list(temporary)){assertEquals(0,entries.count());}
    }
    private static boolean publish(NativeCheckpointFiles files,Path target,byte[] raw,CountDownLatch start) throws InterruptedException {
        start.await();try{files.createNew(target,raw);return true;}catch(IOException conflict){return false;}
    }
}
