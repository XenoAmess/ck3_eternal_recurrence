package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Genuine whole-chain acceptance helper. Call after an actual legal READ/BATCH changed the current owner.
 * This helper constructs no Root, Managed session, M3 token, admission ticket, Base or current qualification.
 */
public final class LifecycleHistoricalPublicationAssertions {
    private LifecycleHistoricalPublicationAssertions(){ }
    public static LifecycleHistoricalPublication.Recorded requireHistoricalAfterProgress(ContinuityStorePort.Session same,
            LifecycleHistoricalPublication actualReader,LifecycleHistoricalPublication.Recorded original,
            DriverStateAssembler actualCurrentDriver)throws Exception {
        String head=same.head().digest();
        var before=actualCurrentDriver.withFrozenFacts(same,frozen->{
            assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());return (DriverSnapshotFacts.Known)frozen.state();
        });
        long originalVersion=Math.addExact(LifecycleJson.integer(original.publication().detailsObject().get("driver_snapshot").get("expected_version"),
                java.math.BigInteger.ZERO).longValueExact(),1);
        assertTrue(before.stamp().driverVersion()>originalVersion,"caller must supply an actual later Driver publication");
        original.requireCurrent(same);
        var retained=actualReader.read(same,original.parent().command().actionId());
        assertArrayEquals(original.proof().encode(),retained.proof().encode());
        assertEquals(original.publication().eventIdentity(),retained.publication().eventIdentity());
        assertEquals(original.predecessorDriverReference(),retained.predecessorDriverReference());
        assertTrue(retained.publication().warmCommit().isEmpty());
        actualCurrentDriver.withFrozenFacts(same,frozen->{assertSame(before,frozen.state());return null;});
        assertEquals(head,same.head().digest());return retained;
    }

    /** Consume the actual installed M7 binding: its Recorded retains the real historical reader issuer.
     * Root's actual-input exercise already holds this binding and Known. No alternative reader is supplied.
     */
    public static LifecycleHistoricalPublication.Recorded requireHistoricalAfterProgress(ContinuityStorePort.Session same,
            LifecycleEpisodeInputs actualProducer,LifecycleEpisodeInputs.CurrentAdoptionBinding actualCurrent,
            DriverSnapshotFacts.Known actualKnown)throws IOException {
        String head=same.head().digest();long sequence=same.head().state().sequence();
        actualProducer.requireCurrentAdoption(same,actualCurrent);
        var recorded=actualCurrent.recorded();
        assertSame(recorded,actualCurrent.historical().recorded());
        assertEquals(recorded.parent(),actualCurrent.parent());
        assertEquals(actualKnown.stamp(),actualCurrent.driverStamp());
        assertArrayEquals(actualKnown.driver().encode(),actualCurrent.driver().encode());
        long originalVersion=Math.addExact(LifecycleJson.integer(recorded.publication().detailsObject().get("driver_snapshot").get("expected_version"),
                java.math.BigInteger.ZERO).longValueExact(),1);
        assertTrue(actualKnown.stamp().driverVersion()>originalVersion,"caller must supply an actual later Driver publication");
        byte[] originalProof=recorded.proof().encode();
        var originalEvent=recorded.publication().eventIdentity();
        var originalPins=recorded.publication().proofDocuments();
        assertArrayEquals(originalProof,LifecycleProofCodec.decodeRecorded(originalProof).encode());
        for(var pin:originalPins)assertEquals(pin,LifecycleProofCodec.decodePin(LifecycleProofCodec.encodePin(pin)));
        // This invokes the real reader retained by Recorded and checks original proof, complete command and FileID pins.
        recorded.requireCurrent(same);
        assertArrayEquals(originalProof,recorded.proof().encode());
        assertEquals(originalEvent,recorded.publication().eventIdentity());
        assertEquals(originalPins,recorded.publication().proofDocuments());
        assertTrue(recorded.publication().warmCommit().isEmpty());
        assertEquals(0,actualCurrent.savedDayCredit());assertEquals(0,actualCurrent.completedCycleCredit());
        // Re-enter the production current guard separately: historical DATA never supplies current qualification.
        actualProducer.requireCurrentAdoption(same,actualCurrent);
        assertEquals(head,same.head().digest());assertEquals(sequence,same.head().state().sequence());
        return recorded;
    }

    public static void requireAppliedParentBoundary(ContinuityStorePort.Session same,LifecycleHistoricalPublication actualReader,
            String actualUnsettledParentId)throws Exception {
        String head=same.head().digest();
        assertThrows(Exception.class,()->actualReader.read(same,actualUnsettledParentId));assertEquals(head,same.head().digest());
    }
}
