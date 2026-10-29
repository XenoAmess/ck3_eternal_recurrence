package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.application.effects.RootFirstCheckpointTestSupport;
import org.xar.ck3.control.application.effects.RootFirstCheckpointTestSupport.NativeSaveFileEdge;
import org.xar.ck3.control.application.effects.RootFirstCheckpointTestSupport.SavedPairOriginals;

/** Read-only FIRST assertions for action_coordinator's sole actual Core chain fixture; constructs no Root/proof/authority. */
public final class RootFirstCheckpointChainAssertions {
    private RootFirstCheckpointChainAssertions() { }

    /** Real Game path: read-only original custody, with no software filesystem edge or unmeasured wire-count claim. */
    public static SavedPairOriginals beforeDomainImports(RootEpisodeChainFixture.BeforeImports actual) throws IOException {
        return originalBeforeDomainImports(actual);
    }
    /** Optional finite software file-edge assertions; this overload must not replace a real Game's native SAVE. */
    public static SavedPairOriginals beforeDomainImports(RootEpisodeChainFixture.BeforeImports actual,
            NativeSaveFileEdge actualNativeSave) throws IOException {
        var originals = originalBeforeDomainImports(actual);
        assertEquals(1, actualNativeSave.enteredWrites(), "the software first SAVE has exactly one observed packet write");
        assertEquals(originals.pair().save(), actualNativeSave.emittedFile().orElseThrow());
        assertEquals(originals.canonicalSave().ack().orElseThrow().requestId(), actualNativeSave.originalPacket().orElseThrow().requestId());
        return originals;
    }
    private static SavedPairOriginals originalBeforeDomainImports(RootEpisodeChainFixture.BeforeImports actual) throws IOException {
        var core = actual.core(); var same = actual.sameWriter(); var context = actual.context();
        core.writer().requireSession(same); String head = same.head().digest();
        assertEquals(actual.head().digest(), head); assertSame(core.writer(), context.writer()); assertSame(core.archive(), context.archive());
        assertSame(actual.catalog().context(), context); assertSame(context.adopted(), actual.checkpointStage().driver());
        var driverSession=context.adopted().session();
        var expectedOwner=new SessionIdentity(driverSession.machineId(),driverSession.game(),driverSession.sessionId());
        assertEquals(expectedOwner, actual.firstCheckpoint().session());
        assertEquals(context.game().generation(), actual.firstCheckpoint().pair().frame().game());
        assertSame(actual.stage(), actual.begun().stage()); assertSame(actual.begun(), actual.baseline().begun());
        assertSame(actual.firstCheckpoint(), actual.baseline().firstCheckpoint());
        assertSame(actual.firstCheckpoint(), actual.baselineBinding().firstCheckpoint());
        assertTrue(actual.stage().previous().isRetired()); assertTrue(actual.stage().previous().ownedBy(core));
        assertSame(core.writer(), actual.stage().previous().writer());
        // The retired predecessor intentionally has no public current() admission. The actual private stage/proof
        // below verifies retained ownership and absence of premature publication without reopening the public port.
        core.nextEpisodeWindows().requireBegun(same, actual.begun());
        core.nextEpisodeWindows().requireBaseline(same, actual.baseline());
        actual.baseline().firstVerifier().requireIssued(same, actual.firstCheckpoint());
        actual.baselineBinding().requireCurrent(same); actual.nextProof().requireCurrent(same, context);
        var originals = RootFirstCheckpointTestSupport.requireCanonicalSavedPair(same, core.writer(), core.archive(), core.actions(),
                actual.checkpointStage().driverCheckpoints(), actual.checkpointStage().saveReceiptVerifier(), core.frameLoader(),
                actual.firstCheckpoint().canonicalSave(), expectedOwner, context.source(), core.authorityId());
        assertEquals(actual.firstCheckpoint().pair(), originals.pair());
        assertArrayEquals(actual.firstCheckpoint().savedDriver().encode(), originals.savedDriver().encode());
        long canonicalIdentities = core.actions().withFrozen(same, held -> {
            long count = held.snapshot().actions().stream().filter(receipt -> receipt.command().actionId().equals(originals.pair().saveActionId())).count();
            held.assertCurrent(); return count;
        });
        assertEquals(1L, canonicalIdentities, "one canonical first-SAVE identity; this does not measure native wire writes");
        assertEquals(actual.begun().opening().frame().frame().identity().dateRaw(), originals.pair().frame().frame().identity().dateRaw(),
                "first physical SAVE preserves date and adds no saved-day credit");
        assertEquals(head, same.head().digest()); return originals;
    }

    /** Publication is asserted from its actual returned product; old private initialization proofs are not reopened. */
    public static void afterPublication(RootEpisodeChainFixture.Published actual) throws IOException {
        var before = actual.imported().before(); var core = before.core(); var same = actual.sameWriter();
        core.writer().requireSession(same); String head = same.head().digest();
        assertEquals(actual.head().digest(), head); assertTrue(actual.session().hasInstalledHost());
        assertSame(actual.session(), core.sessionAccess().current()); assertSame(before.context().adopted(), actual.session().driver());
        assertSame(core.writer(), actual.session().writer()); assertSame(core.archive(), actual.session().archive());
        assertNotEquals(before.stage().previous().identity(), actual.session().identity());
        assertEquals(before.firstCheckpoint().session(), actual.session().identity());
        assertEquals(0, actual.rebound().newSavedDayCredit()); assertEquals(0, actual.rebound().newCompletedCycleCredit());
        assertEquals(head, same.head().digest());
    }
    /** Software fixture-only additional write count; a real Game uses the read-only overload above. */
    public static void afterPublication(RootEpisodeChainFixture.Published actual, NativeSaveFileEdge actualNativeSave) throws IOException {
        afterPublication(actual);
        assertEquals(1, actualNativeSave.enteredWrites(), "software publication or reconciliation cannot replay the original SAVE");
    }
}
