package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;
import org.xar.ck3.control.platform.WindowsOriginalRuntimeHandoff;

/** Actual platform factory negative. No fabricated Lease, owned Python object, writer or positive import. */
public final class RootRiteLegacyCustodyTest {
    @TempDir Path directory;
    @Test void missingOriginalOwnedPythonNeverEntersCaptureReplayOrCommit()throws Exception{
        var provider=WindowsOriginalRuntimeHandoff.originalOwnedLaunch(Optional.empty());
        Path store=directory.resolve("native-session").resolve("rite-creation-actions").toAbsolutePath().normalize();
        var captures=new AtomicInteger();
        var result=provider.withOriginalStore(store,"synthetic-test-machine",lease->{captures.incrementAndGet();throw new AssertionError("capture, preview and commit cannot begin without original runtime custody");});
        assertInstanceOf(OriginalRuntimeHandoffProof.Unavailable.class,result);
        assertEquals(OriginalRuntimeHandoffProof.Reason.ORIGINAL_OWNED_LAUNCH_UNAVAILABLE,((OriginalRuntimeHandoffProof.Unavailable<?>)result).reason());
        assertEquals(0,captures.get());assertFalse(Files.exists(store));
    }
    @Test void callerPathOrMachineCannotStandInForAnOwnedLaunch()throws Exception{
        var provider=WindowsOriginalRuntimeHandoff.originalOwnedLaunch(Optional.empty());
        assertThrows(IllegalArgumentException.class,()->provider.withOriginalStore(Path.of("relative-store"),"synthetic-test-machine",lease->null));
        assertThrows(IllegalArgumentException.class,()->provider.withOriginalStore(directory.toAbsolutePath().normalize(),"unknown",lease->null));
    }
}
