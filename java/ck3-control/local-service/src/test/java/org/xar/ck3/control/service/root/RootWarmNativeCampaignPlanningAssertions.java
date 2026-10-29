package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.application.driver.DriverCapabilityRuntime;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;

/** Called only with a genuine published warm restoration and its actual joined read. No authority is constructed. */
public final class RootWarmNativeCampaignPlanningAssertions {
    private RootWarmNativeCampaignPlanningAssertions(){ }
    public static DriverCapabilityRuntime.NativeCampaignConstructorFacts assertActualRestored(
            RootInstalledCatalog catalog,RootFrozenRunProfile.FrozenRunProfile original,
            DriverCapabilityRuntime capabilities,Session same,FullSnapshot full,Known known)throws Exception {
        var context=catalog.context();String head=same.head().digest();byte[] driver=known.driver().encode();
        var actual=context.requireRestoredOrigin(same);actual.requireOriginal(same);original.requireExplicitNativeCampaign();
        context.adopted().producer().requireNativeCampaignProjectionOrigin(original);
        context.adopted().producer().requireNativeCampaignRestoredProjection(same,actual);
        RootPostAdoptionCollector.bindRestoredPlanning(same,catalog,original);
        var source=capabilities.actualPublicPlanningLifecycleSource(same);
        source.requireOwner(same,context.adopted().authority(),context.archive(),catalog.bindings());
        var captured=source.capture(same,full,known);source.requireCurrent(same,full,known,captured);
        assertSame(captured,source.capture(same,full,known));assertEquals(source.sources(),captured.sourceClosure());
        assertEquals(context.game().generation(),captured.game());assertEquals(context.game().sessionId(),captured.sessionId());
        assertEquals(original.initialPolicy().source(),captured.policySource());
        var environment=context.game().launchPlan().preparedProfile().environmentManifest();
        assertEquals(environment.path(),captured.environmentSource().path());assertEquals(environment.bytes(),captured.environmentSource().bytes());
        assertEquals(environment.sha256(),captured.environmentSource().sha256());
        assertTrue(captured.sourceClosure().contains(actual.evidence().originalHistoryBasis()));
        assertTrue(captured.sourceClosure().containsAll(original.originalReferences()));
        var copy=new DriverCapabilityRuntime.NativeCampaignConstructorFacts(captured.constructor(),captured.game(),captured.sessionId(),
                captured.source(),captured.policySource(),captured.environmentSource(),captured.sourceClosure(),captured.headDigest());
        assertEquals(captured,copy);assertNotSame(captured,copy);
        assertThrows(IllegalArgumentException.class,()->source.requireCurrent(same,full,known,copy));
        source.requireCurrent(same,full,known,captured);assertSame(actual,context.requireRestoredOrigin(same));
        var current=context.adopted().authority().withFrozenFacts(same,frozen->frozen.state());
        assertSame(known,current);assertArrayEquals(driver,assertInstanceOf(Known.class,current).driver().encode());
        assertEquals(head,same.head().digest());return captured;
    }
}
