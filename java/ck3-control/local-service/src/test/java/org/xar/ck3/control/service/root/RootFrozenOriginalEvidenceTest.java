package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;

/** Physical originals use the production evidence reader; these files grant no Prepared/Game authority. */
public final class RootFrozenOriginalEvidenceTest {
    @TempDir Path root;
    private static ExactRef ref(Path path)throws IOException {
        var actual=FileRef.measure(path);return new ExactRef(actual.path(),actual.bytes(),actual.sha256());
    }
    @Test void retainsEmptyAndLargerThanJsonEvidenceThroughTheActualReader()throws Exception {
        Path empty=Files.createFile(root.resolve("empty-profile-input"));
        var emptyRef=ref(empty);var zero=RootFrozenRunProfile.retainOriginalEvidence(emptyRef);
        assertEquals(0,zero.nativeFile().logicalBytes());assertEquals(emptyRef.sha256(),zero.source().sha256());
        Path large=root.resolve("saved-game.ck3");
        try(var out=Files.newOutputStream(large,StandardOpenOption.CREATE_NEW)) {
            byte[] block=new byte[8192];for(int n=0;n<128;n++)out.write(block);out.write(1);
        }
        var largeRef=ref(large);assertEquals(1048577,largeRef.bytes());
        var held=RootFrozenRunProfile.retainOriginalEvidence(largeRef);
        assertEquals(largeRef.bytes(),held.nativeFile().logicalBytes());SharedSourceFiles.assertUnchanged(held);
        Instant now=Instant.parse("2026-10-25T00:00:00Z");
        assertThrows(IllegalArgumentException.class,()->new RootFrozenRunProfile.Request("physical-test",now,now.plusSeconds(60),
                "request","session",largeRef,RootFrozenRunProfile.LifecycleMode.ORDINARY_CAMPAIGN_SUCCESSION,true,
                new RootFrozenRunProfile.DisabledFreshRobert()));
        assertThrows(IllegalArgumentException.class,()->new RootFrozenRunProfile.Request("physical-test",now,now.plusSeconds(60),
                "request","session",emptyRef,RootFrozenRunProfile.LifecycleMode.ORDINARY_CAMPAIGN_SUCCESSION,true,
                new RootFrozenRunProfile.DisabledFreshRobert()));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(new byte[0]));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(new byte[RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES+1]));
    }
    @Test void retainedWitnessRejectsSameBytesWithDifferentNativeIdentity()throws Exception {
        Path original=Files.createFile(root.resolve("original"));var exact=ref(original);
        var held=RootFrozenRunProfile.retainOriginalEvidence(exact);
        Path replacement=Files.createFile(root.resolve("replacement"));
        var other=SharedSourceFiles.observe(replacement);
        assertNotEquals(held.nativeFile().identityKey(),other.nativeFile().identityKey());
        Files.move(replacement,original,StandardCopyOption.REPLACE_EXISTING);
        assertEquals(exact,ref(original));
        assertThrows(IOException.class,()->SharedSourceFiles.assertUnchanged(held));
    }
    @Test void changedMissingAndIncorrectExactOriginalsAreRejected()throws Exception {
        Path file=root.resolve("input");Files.writeString(file,"first",StandardOpenOption.CREATE_NEW);var original=ref(file);
        var held=RootFrozenRunProfile.retainOriginalEvidence(original);
        Files.writeString(file,"other",StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IOException.class,()->RootFrozenRunProfile.retainOriginalEvidence(original));
        assertThrows(IOException.class,()->SharedSourceFiles.assertUnchanged(held));
        var actual=ref(file);String wrong=actual.sha256().equals("0".repeat(64))?"1".repeat(64):"0".repeat(64);
        assertThrows(IOException.class,()->RootFrozenRunProfile.retainOriginalEvidence(new ExactRef(actual.path(),actual.bytes(),wrong)));
        Files.delete(file);assertThrows(IOException.class,()->RootFrozenRunProfile.retainOriginalEvidence(actual));
    }
}
