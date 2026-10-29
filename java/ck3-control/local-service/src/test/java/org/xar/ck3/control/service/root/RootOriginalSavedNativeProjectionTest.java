package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.time.Clock;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.history.LegacyResumeMigration;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;

/** Actual source/profile and original readonly journal producer; absent SavedNative inputs fail. */
final class RootOriginalSavedNativeProjectionTest {
    @Test void originalSavedNativePrivatePolicyAuthorizesNullProjectionWithoutAFreshFixture() throws Exception {
        var fixture=RootOriginalDriverColdFixture.readRequiredSystemProperties();
        assertEquals(WindowsJobProcess.currentMachineId(),fixture.machineId());
        int savedNativeCases=0;
        for(var test:fixture.cases()) {
            var request=RootFrozenRunProfile.decode(RootRuntimeDefinitions.read(RootApplicationConfiguration.file(test.runRequest()),RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES));
            if(!(request.legacyImport() instanceof RootFrozenRunProfile.EnabledNativeCampaign)
                    ||test.expectedFullPayloadSha256()==null)continue;
            savedNativeCases++;
            var plan=NativeLaunchPlan.readExact(test.launchPlan(),new NativeBridgeLaunchEvidence());
            assertInstanceOf(NativeLaunchPlan.SavedGame.class,plan.load());
            Clock clock=Clock.systemUTC();RootOriginalDriverColdFixture.requirePrelaunch(plan,clock);
            var profile=RootFrozenRunProfile.readExact(test.runRequest(),plan,test.episodePolicy(),clock);
            assertTrue(profile.lifecycleBinding().isEmpty());assertTrue(profile.fixture().isEmpty());
            profile.requireExplicitNativeCampaign();profile.initialPolicy().requireSavedProjection(plan);
            try(var scope=RootOriginalDriverColdFixture.openReadOnlyScope(test.control(),test.storageLease(),fixture.machineId(),clock)) {
                RootOriginalDriverColdFixture.requireStorage(plan,test.control(),scope.storage());
                var producer=new RootOriginalDriverJournal.Prepared(scope.files(),scope.storage(),plan,profile,clock);
                scope.writer().locked(same->{
                    String before=same.head().digest();var original=producer.load(scope.writer(),same,plan);
                    assertEquals(test.expectedStatus(),original.status());assertSame(profile,original.frozenProfile());
                    original.requireRetained(same);
                    assertInstanceOf(RootOriginalDriverJournal.ExplicitNullLifecycle.class,original.persistedLifecycleData());
                    assertInstanceOf(LegacyResumeMigration.ExplicitNativeCampaign.class,original.frozenLifecycleProjection());
                    assertThrows(IOException.class,original::persistedLifecycle);
                    var normalized=assertInstanceOf(LegacyResumeNormalizer.Loaded.class,original.normalizeForFrozen(same));
                    assertSame(Nil.INSTANCE,normalized.normalizedLifecycle());assertFalse(normalized.lifecycleMigrationRequired());
                    assertEquals(test.expectedFullPayloadSha256(),OriginalDriverJournal.sha256(original.fullBytes()));
                    assertEquals(before,same.head().digest(),"readonly Saved import must not commit or manufacture an episode");
                    original.requireRetained(same);return null;
                });
            }
        }
        assertTrue(savedNativeCases>0,"required original cold fixture must contain a genuine SavedNative source case; never skip");
    }
}
