package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;

/** Actual original evidence fixture checks the exact old-frame identity guard used by cold continuation. The fixture retains its genuine DEATH origin.
 * This tests DATA identity checks; no private PendingToken, cold Root or continuation permission is minted.
 */
final class LifecycleRetainedFrameBoundaryTest {
    @TempDir Path temporary;
    @Test void actualOriginalTerminalFrameRetainsItsExactCanonicalParentScope()throws Exception {
        var actual=new LifecycleBusinessFixture(temporary.resolve("original"));
        var parent=actual.parent;
        assertDoesNotThrow(()->LifecycleComposites.validateScope(parent,actual.snapshot));
        assertEquals(parent.lifecycleBefore().evidence().originalDriver().sha256(),actual.snapshot.facts().stamp().driverSha256());
        assertEquals(parent.lifecycleBefore().nativeEvidence(),actual.snapshot.originalEvidence());
    }
    @Test void alreadyPublishedDriverVersionAndUnboundPacketCannotReplaceTheOldTerminalFrame()throws Exception {
        var actual=new LifecycleBusinessFixture(temporary.resolve("changed"));var parent=actual.parent;
        var old=actual.snapshot;var known=old.facts();var stamp=known.stamp();
        var later=new DriverSnapshotFacts.Known(known.driver(),new DriverSnapshotFacts.Stamp(stamp.driverVersion()+1,
                stamp.episodeEpoch(),stamp.game(),stamp.episodeRunId(),stamp.driverSha256()),
                known.originalHistoryBasis(),known.actionRows(),known.auxiliary(),known.loop(),Optional.empty());
        var changed=new LifecycleObservationPort.Snapshot(old.actual(),old.source(),old.semantic(),later,old.originalEvidence());
        assertThrows(IllegalArgumentException.class,()->LifecycleComposites.validateScope(parent,changed));
        var other=actual.files.createNew(temporary.resolve("different-original-packet.bin"),old.actual().originalPacket()).reference();
        var foreign=new LifecycleObservationPort.Snapshot(old.actual(),old.source(),old.semantic(),known,other);
        assertThrows(IllegalArgumentException.class,()->LifecycleComposites.validateScope(parent,foreign));
    }
}
