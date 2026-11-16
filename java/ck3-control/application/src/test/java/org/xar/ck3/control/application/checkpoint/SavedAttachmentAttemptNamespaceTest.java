package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;

/** Namespace DATA only; no fabricated NativeCandidate, Loaded role or physical-write permission. */
final class SavedAttachmentAttemptNamespaceTest {
    @TempDir Path directory;
    private ExactRef packet(String name,String body) throws Exception {
        var path=directory.resolve(name);byte[] bytes=body.getBytes(StandardCharsets.UTF_8);
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW);
        return new ExactRef(path.toString(),bytes.length,ActionCodec.sha256(bytes));
    }

    @Test void loadedKeyBindsParentAndEveryOriginalPacketCoordinate() throws Exception {
        var packet=packet("raw.bin","original raw capture");
        String key=SavedAttachmentSourceStore.restoreDirectoryKey("parent",packet,true);
        assertEquals(key,SavedAttachmentSourceStore.restoreDirectoryKey("parent",packet,true));
        assertNotEquals(key,SavedAttachmentSourceStore.restoreDirectoryKey("another-parent",packet,true));
        assertNotEquals(key,SavedAttachmentSourceStore.restoreDirectoryKey("parent",
                new ExactRef(directory.resolve("other.bin").toString(),packet.bytes(),packet.sha256()),true));
        assertNotEquals(key,SavedAttachmentSourceStore.restoreDirectoryKey("parent",
                new ExactRef(packet.path(),packet.bytes()+1,packet.sha256()),true));
        assertNotEquals(key,SavedAttachmentSourceStore.restoreDirectoryKey("parent",
                new ExactRef(packet.path(),packet.bytes(),"0".repeat(64)),true));
    }

    @Test void distinctCapturePreservesEarlierFourOriginalDocuments() throws Exception {
        var first=packet("first.bin","first capture");var second=packet("second.bin","new capture");
        Path old=directory.resolve(SavedAttachmentSourceStore.restoreDirectoryKey("parent",first,true));
        Path next=directory.resolve(SavedAttachmentSourceStore.restoreDirectoryKey("parent",second,true));
        assertNotEquals(old,next);Files.createDirectory(old);Files.createDirectory(next);
        for(String name:new String[]{"basis.json","game.json","opening.json","progress.json"}) {
            byte[] prior=("original "+name).getBytes(StandardCharsets.UTF_8);
            Files.write(old.resolve(name),prior,StandardOpenOption.CREATE_NEW);
            Files.write(next.resolve(name),("new "+name).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
            assertArrayEquals(prior,Files.readAllBytes(old.resolve(name)));
        }
        assertEquals(old.getFileName().toString(),SavedAttachmentSourceStore.restoreDirectoryKey("parent",first,true));
    }

    @Test void genericRequestDirectoryKeepsItsOriginalHash() throws Exception {
        var first=packet("generic-a.bin","first");var next=packet("generic-b.bin","next");
        String original=ActionCodec.sha256("parent".getBytes(StandardCharsets.UTF_8));
        assertEquals(original,SavedAttachmentSourceStore.restoreDirectoryKey("parent",first,false));
        assertEquals(original,SavedAttachmentSourceStore.restoreDirectoryKey("parent",next,false));
    }
}
