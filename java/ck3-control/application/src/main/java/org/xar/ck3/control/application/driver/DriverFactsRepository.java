package org.xar.ck3.control.application.driver;

import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** In-memory Driver owner only. Physical Driver/SAVE and canonical ledger writes remain in their existing stores. */
public final class DriverFactsRepository {
    private DriverSnapshotFacts.State current;
    public DriverFactsRepository(DriverSnapshotFacts.State actualInitialFacts) { current=Objects.requireNonNull(actualInitialFacts); }

    /** Explicit original-wire import; callers must obtain a real approved artifact. This method never opens a path. */
    public static DriverSnapshotFacts.Known imported(ExactRef original, byte[] originalWire, long actualVersion,
            long actualEpisodeEpoch, GameGeneration actualGame, OpportunityJson.Obj actualAuxiliary) {
        Objects.requireNonNull(original); Objects.requireNonNull(originalWire);
        StrictJson.require(original.bytes()==originalWire.length && original.sha256().equals(DriverJson.sha256(originalWire)),
                "actual imported full Driver bytes differ from their original reference");
        DriverStateSnapshot.Complete driver=DriverStateSnapshot.decodeComplete(originalWire);
        var stamp=new DriverSnapshotFacts.Stamp(actualVersion,actualEpisodeEpoch,actualGame,driver.session().episodeRunId(),DriverJson.sha256(driver.encode()));
        // No Java action is claimed covered merely because a legacy history file exists.
        return new DriverSnapshotFacts.Known(driver,stamp,original,java.util.List.of(),actualAuxiliary,
                java.util.Optional.empty(),java.util.Optional.empty());
    }
    synchronized <T>T locked(Function<DriverSnapshotFacts.State,T> operation) { return operation.apply(current); }
    void compareAndSet(DriverSnapshotFacts.Stamp expected, DriverSnapshotFacts.Known replacement) {
        StrictJson.require(Thread.holdsLock(this),"Driver facts mutation requires its frozen owner lease");
        StrictJson.require(current instanceof DriverSnapshotFacts.Known,"full predecessor facts unavailable");
        DriverSnapshotFacts.Known before=(DriverSnapshotFacts.Known)current;
        StrictJson.require(before.stamp().equals(expected),"stale Driver version CAS");
        StrictJson.require(replacement.stamp().driverVersion()==Math.addExact(expected.driverVersion(),1),"Driver publication advances exactly one owner version");
        current=Objects.requireNonNull(replacement);
    }
    void replaceObservation(DriverSnapshotFacts.Stamp expected, DriverObservationFacts observed) {
        StrictJson.require(Thread.holdsLock(this) && current instanceof DriverSnapshotFacts.Known,"actual frozen Driver facts required");
        DriverSnapshotFacts.Known before=(DriverSnapshotFacts.Known)current;
        StrictJson.require(before.stamp().equals(expected),"semantic observation crossed Driver CAS");
        current=new DriverSnapshotFacts.Known(before.driver(),before.stamp(),before.originalHistoryBasis(),before.actionRows(),
                before.auxiliary(),before.loop(),java.util.Optional.of(observed));
    }
    /** Ephemeral runtime observations have their own source/version; the original thirteen-field Driver is unchanged. */
    void publishCapabilityInputs(DriverSnapshotFacts.Stamp expected,String expectedAuxiliarySha256,
            DriverCapabilityStateProducer.InitialAuxiliary actual) {
        StrictJson.require(Thread.holdsLock(this) && current instanceof DriverSnapshotFacts.Known,"capability publication requires the sole frozen Driver owner");
        var before=(DriverSnapshotFacts.Known)current;
        StrictJson.require(before.stamp().equals(expected) && actual.expectedStamp().equals(expected)
                && expectedAuxiliarySha256.equals(DriverJson.sha256(DriverJson.encode(before.auxiliary())))
                && expectedAuxiliarySha256.equals(actual.expectedAuxiliarySha256()),"stale capability auxiliary publication CAS");
        current=new DriverSnapshotFacts.Known(before.driver(),before.stamp(),before.originalHistoryBasis(),before.actionRows(),
                actual.auxiliary(),before.loop(),before.observation());
    }
}
