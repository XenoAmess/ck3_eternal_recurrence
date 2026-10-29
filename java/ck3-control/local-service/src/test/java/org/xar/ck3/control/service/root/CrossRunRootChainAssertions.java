package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.util.Optional;

/** Concrete consumer of action_coordinator's sole actual Root fixture callbacks. No fixture or authority is created. */
public final class CrossRunRootChainAssertions implements RootEpisodeChainFixture.Assertions {
    private CrossRunFirstCheckpointAssertions.Observed pending;
    private CrossRunFirstCheckpointAssertions.Observed previous;

    @Override public void beforeDomainImports(RootEpisodeChainFixture.BeforeImports actual)throws IOException {
        assertNull(pending,"a partial actual callback sequence cannot be retried as a new FIRST");
        assertSame(actual.firstCheckpoint(),actual.baselineBinding().firstCheckpoint());
        assertSame(actual.firstCheckpoint(),actual.baseline().firstCheckpoint());
        assertSame(actual.baselineBinding(),actual.nextProof().baseline());
        pending=CrossRunFirstCheckpointAssertions.assertNextBeforeRebind(actual.sameWriter(),actual.preparedCrossRun(),
                actual.context(),actual.nextProof());
        if(previous!=null){
            CrossRunFirstCheckpointAssertions.assertDistinctNextSameCore(previous,pending);
            CrossRunFirstCheckpointAssertions.assertRetainedOriginal(actual.sameWriter(),previous);
        }
    }

    @Override public void afterDomainImports(RootEpisodeChainFixture.Imported actual)throws IOException {
        assertNotNull(pending,"actual FIRST capture must precede actual domain imports");
        var before=actual.before();
        var read=CrossRunFirstCheckpointAssertions.assertNextBeforeRebind(actual.sameWriter(),before.preparedCrossRun(),
                actual.context(),actual.nextProof());
        assertEquals(pending.saved().material().witness(),read.saved().material().witness());
        assertEquals(pending.saved().material().baseline(),read.saved().material().baseline());
        assertEquals(pending.saved().body(),read.saved().body());assertEquals(pending.saved().state(),read.saved().state());
        assertEquals(pending.saved().plan(),read.saved().plan());assertEquals(pending.saved().strategySource(),read.saved().strategySource());
        assertFalse(actual.bodies().stream().anyMatch(body->
                body.slot()==org.xar.ck3.control.continuity.writer.DomainBodies.Slot.CROSS_RUN_PLANNING),
                "new-episode initializers must retain the original CrossRun body");
    }

    @Override public void afterPublication(RootEpisodeChainFixture.Published actual)throws IOException {
        assertNotNull(pending,"actual publication must retain its prior FIRST observation");
        assertEquals(pending.saved().material().session(),actual.session().identity());
        // The private NEXT proof has ended at rebind. Only immutable original material is read here.
        CrossRunFirstCheckpointAssertions.assertRetainedOriginal(actual.sameWriter(),pending);
        if(previous!=null)CrossRunFirstCheckpointAssertions.assertRetainedOriginal(actual.sameWriter(),previous);
        previous=pending;pending=null;
    }

    /** Historical DATA for a later genuine FIRST restore callback; no live private NEXT proof is exposed. */
    public Optional<CrossRunFirstCheckpointAssertions.Observed> lastPublished(){return Optional.ofNullable(previous);}

    /** Called after a genuinely admitted FIRST restore; the actual context independently replays its private original. */
    public void verifyActualRestoredFirst(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            RootCrossRunPlanning.Prepared actual,RootRuntimeContext restored)throws IOException {
        assertNull(pending);assertNotNull(previous,"a real published FIRST must precede its restore comparison");
        CrossRunFirstCheckpointAssertions.assertRestoredFirst(same,actual,restored,previous);
    }

    public void verifyActualRestoredInitialization(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            RootCrossRunPlanning.Prepared actual,RootRuntimeContext restored,
            RootApplicationAssembly.RestoredFirstEpisodeDomainProof proof)throws IOException {
        assertNull(pending);assertNotNull(previous,"a real published FIRST must precede its private restored initialization");
        CrossRunFirstCheckpointAssertions.assertRestoredInitialization(same,actual,restored,proof,previous);
    }
}
