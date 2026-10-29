package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;

/** One held receiver. Waiting and sampling retained originals never submit a world action. */
public interface NativeSnapshotWaitPort extends NativeObservationPort {
    sealed interface WaitResult permits Received, Elapsed { ObservedFrame frame(); }
    record Received(ObservedFrame frame) implements WaitResult {
        public Received { Objects.requireNonNull(frame); }
    }
    record Elapsed(ObservedFrame frame) implements WaitResult {
        public Elapsed { Objects.requireNonNull(frame); }
    }
    /** Read the actual retained accepted original under the same source; no native read or fresh observation. */
    ObservedFrame currentSnapshot(Instant captureUntil) throws IOException;
    /** captureUntil is the original later deadline for an already-started packet and final source checks. */
    WaitResult waitForSnapshot(Instant waitUntil, Instant captureUntil) throws IOException, InterruptedException;

    /** Serialized evidence DATA. Decoding this does not mint a live ReadSample or verify a physical source. */
    record SampleData(ObservedFrame frame,Instant startedAt,Instant completedAt) {
        public SampleData {
            Objects.requireNonNull(frame);Objects.requireNonNull(startedAt);Objects.requireNonNull(completedAt);
            if(completedAt.isBefore(startedAt))throw new IllegalArgumentException("snapshot sample clock moved backwards");
        }
    }
    /** Issued only by the actual call interval below. Root still qualifies the identical physical held receiver. */
    final class ReadSample {
        private final NativeSnapshotWaitPort issuer;
        private final SampleData original;
        private ReadSample(NativeSnapshotWaitPort issuer,SampleData original){this.issuer=issuer;this.original=original;}
        public ObservedFrame frame(){return original.frame();}
        public Instant startedAt(){return original.startedAt();}
        public Instant completedAt(){return original.completedAt();}
        public SampleData data(){return original;}
        public void requirePort(NativeSnapshotWaitPort actualHeld)throws IOException {
            if(actualHeld==null||issuer!=actualHeld)throw new IOException("snapshot sample belongs to another held receiver");
        }
    }
    /**
     * Samples the retained original through the actual receiver's source checks. The original frame time is unchanged;
     * these timestamps prove this local read interval, not a new native packet, world state or gameplay qualification.
     */
    default ReadSample sampleCurrentSnapshot(Instant captureUntil)throws IOException {
        Objects.requireNonNull(captureUntil);Instant started=Instant.now();
        if(!started.isBefore(captureUntil))throw new IOException("snapshot sample deadline already elapsed");
        ObservedFrame actual=Objects.requireNonNull(currentSnapshot(captureUntil));
        Instant completed=Instant.now();
        if(completed.isBefore(started)||!completed.isBefore(captureUntil))
            throw new IOException("snapshot sample clock/deadline failed after actual source checks");
        return new ReadSample(this,new SampleData(actual,started,completed));
    }
}
