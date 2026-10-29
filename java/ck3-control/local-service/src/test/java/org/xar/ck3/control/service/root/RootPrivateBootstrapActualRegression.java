package org.xar.ck3.control.service.root;

import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.platform.ColdBootstrapJson;
import static org.junit.jupiter.api.Assertions.*;

/** Separate real-boundary target. Missing actual private Root inputs is RED, never a skipped success.
 * Its provider is supplied by the qualified full Root fixture, not by production code or JSON. */
public final class RootPrivateBootstrapActualRegression {
    public interface ActualInput extends AutoCloseable {
        /** Produced by the real finished Root startup route; this test never prepares, adopts or completes it again. */
        RootPrivateBootstrap.Original original()throws Exception;
        /** Same actual Root and genuine public Confirmed SAVE. The outer fixture owns its single lifetime. */
        RootWarmNativeCampaignRestoreCheck.ActualInput qualifiedWarmInput()throws Exception;
        @Override void close()throws java.io.IOException;
    }
    @Test void actualNewCreatorCanonicalColdAdoptionAndRealRestoreConsumer()throws Exception {
        var providers=ServiceLoader.load(ActualInput.class).stream().toList();
        if(providers.size()!=1)throw new IllegalStateException("Exactly one qualified actual Root cold fixture is required; ordinary mocks/JSON do not qualify");
        try(ActualInput input=providers.get(0).get()) {
            var original=input.original();var context=original.context();
            assertEquals(original.data(),ColdBootstrapJson.decodeAdoption(ColdBootstrapJson.encodeAdoption(original.data())));
            context.withSession(same->{
                original.requireCurrent(same,context);var prefix=same.head();
                original.requireOriginal(same);assertEquals(prefix,same.head(),"historical qualification cannot write or credit gameplay");
                var rebound=context.requireColdReboundOrigin(same);rebound.requireOriginal(same);
                RootColdReboundAssertions.requireActual(same,original,rebound);
                RootColdReboundContextAssertions.assertActualBound(context,rebound,same);
                assertEquals(0,rebound.newSavedDayCredit());assertEquals(0,rebound.newCycleCredit());
                original.requireOriginal(same);return null;
            });
            // Complete all cold checks before warm restore retires this original Root/context.
            var warm=input.qualifiedWarmInput();
            assertNotNull(warm,"MISSING_ACTUAL_WARM_INPUT: qualified original Root and genuine public SAVE required");
            var before=warm.originalRoot();var access=warm.actualAccess();
            assertSame(context.actions(),before,"warm input must retain this exact cold Root");
            assertTrue(before.ownedBy(context.core()),"warm input crossed its real Core");
            assertSame(before,access.current(),"warm access is not on this exact current Root");
            assertSame(context.writer(),before.writer());assertSame(context.archive(),before.archive());
            assertTrue(before.hasInstalledHost(),"actual Root has no currently installed Host");
            var host=before.hostForPublication();assertNotNull(host);
            before.driver().producer().requireNativeCampaignProjectionOrigin(warm.originalFrozen());
            // This helper calls the actual public SAVE/LOAD chain; it neither creates nor closes a separate fixture.
            var published=RootWarmNativeCampaignRestoreCheck.requireActual(warm);
            assertSame(published.second(),access.current());assertTrue(published.first().isRetired());
            assertFalse(published.second().isRetired());assertTrue(published.second().ownedBy(context.core()));
            assertSame(context.writer(),published.second().writer());assertSame(context.archive(),published.second().archive());
            assertSame(host,published.first().hostForPublication());assertSame(host,published.second().hostForPublication());
            assertEquals(0,published.firstBinding().newSavedDayCredit());assertEquals(0,published.secondBinding().newSavedDayCredit());
            // The original Root is retired now. Its old current-Game/readiness guards must not be reused.
        }
    }
}
