package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.driver.DriverCapabilityStateProducer;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverPersistentPlanningState;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Relocated event1..35/38 DATA exercises the original capability capsule consumer.
 * All artifacts live under @TempDir. No Native transport, writer, Game or model is used.
 */
final class SettledCapabilityRecoveryRegressionTest {
    @TempDir Path temporary;

    @Test void settled35RecoversThePublishedConfigurationAndPersistentSources() throws Exception {
        Path root=PortableSettledFixture.materialize(temporary);
        var fixture=new SettledSameGameRecoveryRegressionTest.Fixture(root);
        var data=fixture.read();var auxiliary=data.retainedFacts().auxiliary();

        assertEquals(35,data.canonicalSequence());
        assertEquals(3,data.retainedFacts().stamp().driverVersion());
        var configuration=DynamicCapabilities.decodeConfiguration(
                assertInstanceOf(OpportunityJson.Obj.class,auxiliary.get("capability_configuration")));
        assertTrue(configuration.stateDir().orElseThrow().startsWith(root));
        assertTrue(configuration.saveDir().orElseThrow().startsWith(root));
        assertEquals(3,configuration.routeContactTimelineSpeed());
        assertEquals(3,configuration.routeContactEffectiveTimelineSpeed());
        assertFalse(configuration.allowRouteContactHighSpeedAb());
        assertFalse(configuration.stationaryObjectiveHoldCanaryRequested());
        var source=DriverObservationEvidenceReader.reference(auxiliary.get(DriverCapabilityStateProducer.STATE_SOURCE));
        assertTrue(Path.of(source.path()).startsWith(root));
        var capsule=DriverJson.object(fixture.outcomes.loadFullMaterial(source).bytes(),DriverJson.MAX_NATIVE_BYTES);
        assertEquals(new OpportunityJson.Text("xar.driver-capability-state/v2"),capsule.get("schema"));
        assertNotNull(auxiliary.get(DriverPersistentPlanningState.COOLDOWN_STATE));
        assertNotNull(auxiliary.get(DriverPersistentPlanningState.COOLDOWN_SOURCE));
        assertNotNull(auxiliary.get(DriverPersistentPlanningState.STRATEGY_SOURCE));
        assertNotNull(auxiliary.get("driver_read_publication"));
        assertDoesNotThrow(()->DriverPersistentPlanningState.replay(auxiliary,fixture.outcomes));
        assertTrue(data.retainedFacts().observation().isEmpty(),"historical replay grants no fresh Native custody");
        assertEquals(4,data.retainedFacts().driver().commandHistory().size());
        assertEquals(0,fixture.commits);fixture.assertNoCredit();
    }

    @Test void changedConfigurationContentCannotPassTheOriginalRuntimeCapsuleConsumer() throws Exception {
        Path root=PortableSettledFixture.materialize(temporary);
        var fixture=new SettledSameGameRecoveryRegressionTest.Fixture(root);
        var retained=fixture.read().retainedFacts();var originals=fixture.outcomes;
        var source=DriverObservationEvidenceReader.reference(retained.auxiliary().get(DriverCapabilityStateProducer.STATE_SOURCE));
        var state=DriverJson.object(originals.loadFullMaterial(source).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var manifestReference=DriverObservationEvidenceReader.reference(state.get("semantic_source"));
        var manifest=originals.loadFullMaterial(manifestReference);
        var nativeReference=DriverObservationEvidenceReader.reference(retained.auxiliary().get("capability_observed_native_source"));
        var raw=DriverObservationEvidenceReader.nativeFrame(manifestReference,manifest,originals.loadNativeFrame(nativeReference));
        var driverReference=DriverObservationEvidenceReader.currentDriverReference(manifestReference,manifest);
        var facts=DriverObservationEvidenceReader.decode(manifestReference,manifest,originals.loadFullMaterial(driverReference),raw);
        var stamp=new DriverSnapshotFacts.Stamp(facts.driverVersion(),facts.episodeEpoch(),facts.transport().game(),
                facts.driver().session().episodeRunId(),DriverJson.sha256(facts.driver().encode()));
        var known=new DriverSnapshotFacts.Known(facts.driver(),stamp,retained.originalHistoryBasis(),retained.actionRows(),
                retained.auxiliary(),retained.loop(),Optional.of(facts));
        var frame=assertInstanceOf(DriverObservationAssembler.Complete.class,
                new DriverObservationAssembler().assemble(raw,facts,nativeReference));

        var changed=new LinkedHashMap<>(state.members());
        for(String key:new String[]{"cache_values","owner_auxiliary"}) {
            var owner=new LinkedHashMap<>(OpportunityJson.object(state.get(key),key).members());
            var configuration=new LinkedHashMap<>(OpportunityJson.object(owner.get("capability_configuration"),"configuration").members());
            configuration.put("state_dir",new OpportunityJson.Text(root.resolve("different-state").toString()));
            owner.put("capability_configuration",new OpportunityJson.Obj(configuration));
            changed.put(key,new OpportunityJson.Obj(owner));
        }
        byte[] bytes=DriverJson.encode(new OpportunityJson.Obj(changed));
        Path alteredPath=root.resolve("altered-capability-state.json");Files.write(alteredPath,bytes);
        var altered=new ExactRef(alteredPath.toString(),bytes.length,ActionCodec.sha256(bytes));
        var rejected=assertThrows(IllegalArgumentException.class,
                ()->DriverCapabilityStateProducer.replay(frame,known,altered,originals));
        assertTrue(rejected.getMessage().contains("cached values differ from original complete runtime capsule"),rejected.getMessage());
        assertEquals(0,fixture.commits);fixture.assertNoCredit();
    }

    @Test void deferredBatch38RetainsCapabilitiesAndTheNextBatchWithoutSaveCredit() throws Exception {
        Path root=PortableSettledFixture.materialize38(temporary);
        var fixture=new SettledSameGameRecoveryRegressionTest.Fixture(root);
        var data=fixture.read();

        assertEquals(38,data.canonicalSequence());
        assertEquals(2,data.controller().nextBatchSequence());
        assertEquals(2,data.controller().usedBatches().size());
        assertTrue(data.controller().dirty());
        assertEquals(1,data.controller().unsavedGameplayActions().size());
        assertTrue(data.controller().savedPair().isEmpty());
        assertEquals(3,data.retainedFacts().stamp().driverVersion());
        assertEquals(4,data.retainedFacts().driver().commandHistory().size());
        assertInstanceOf(OpportunityJson.Obj.class,data.retainedFacts().auxiliary().get("capability_configuration"));
        assertDoesNotThrow(()->DriverPersistentPlanningState.replay(data.retainedFacts().auxiliary(),fixture.outcomes));
        assertTrue(data.latestObservedFrame().frame().revision().compareTo(BigInteger.valueOf(7))>=0);
        assertEquals(0,fixture.commits);fixture.assertNoCredit();
    }
}
