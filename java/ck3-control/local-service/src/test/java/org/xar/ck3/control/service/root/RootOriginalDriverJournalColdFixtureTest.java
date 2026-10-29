package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.time.Clock;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;

/** The sole v2 bundle supplies fixed readonly writer and exact prelaunch/profile/storage originals. No fake Managed Game or skipped fixture. */
public final class RootOriginalDriverJournalColdFixtureTest {
    @Test void actualQualifiedPlanPolicyGuardedFilesAndOriginalWriterProduceTheRetainedColdInputs()throws Exception {
        var fixture=RootOriginalDriverColdFixture.readRequiredSystemProperties();
        assertEquals(WindowsJobProcess.currentMachineId(),fixture.machineId());
        for(RootOriginalDriverColdFixture.Case test:fixture.cases()) {
            // readExact uses the real fixed Native launch evidence reader. This does not create a process or a Native pipe.
            var plan=NativeLaunchPlan.readExact(test.launchPlan(),new NativeBridgeLaunchEvidence());
            Clock clock=Clock.systemUTC();RootOriginalDriverColdFixture.requirePrelaunch(plan,clock);
            var profile=RootFrozenRunProfile.readExact(test.runRequest(),plan,test.episodePolicy(),clock);
            var policy=profile.initialPolicy();
            try(var scope=RootOriginalDriverColdFixture.openReadOnlyScope(test.control(),test.storageLease(),fixture.machineId(),clock)) {
            var writer=scope.writer();var storage=scope.storage();var files=scope.files();
            RootOriginalDriverColdFixture.requireStorage(plan,test.control(),storage);
            var producer=new RootOriginalDriverJournal.Prepared(files,storage,plan,profile,clock);
            writer.locked(same->{
                String before=same.head().digest();var loaded=producer.load(writer,same,plan);assertEquals(test.expectedStatus(),loaded.status(),test.name());
                loaded.requireRetained(same);assertSame(profile,loaded.frozenProfile());assertSame(policy,loaded.frozenProfile().initialPolicy());
                if(test.expectedFullPayloadSha256()!=null) {
                    assertEquals(test.expectedFullPayloadSha256(),OriginalDriverJournal.sha256(loaded.fullBytes()));
                    var rows=(org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ArrayValue)loaded.fullPayload().get("command_history");
                    assertEquals(test.expectedHistoryRows().intValue(),rows.values().size());
                }else assertThrows(IOException.class,loaded::fullPayload);
                assertEquals(before,same.head().digest(),"read-only import cannot create a transition, history row or empty episode");return null;
            });
            }
        }
    }
}
