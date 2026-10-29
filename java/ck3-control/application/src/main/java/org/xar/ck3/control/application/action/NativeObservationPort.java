package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Native observations retain original opaque integer/token domains, independent of action state. */
public interface NativeObservationPort {
    ObservedFrame observe(Instant deadline) throws InterruptedException;
    record TransportSession(String machineId, GameGeneration game, BigInteger connectionGeneration, String sessionId) {
        public TransportSession {
            StrictJson.text(machineId); Objects.requireNonNull(game); Objects.requireNonNull(connectionGeneration);
            StrictJson.require(connectionGeneration.signum() > 0 && connectionGeneration.compareTo(StrictJson.UINT64_MAX) <= 0, "uint64 connection generation required");
            StrictJson.text(sessionId);
        }
    }
    record ObservedFrame(TransportSession session, String snapshotId, BigInteger nativeRevision, RawJson state,
            byte[] originalPacket, Instant observedAt) {
        public ObservedFrame {
            Objects.requireNonNull(session); StrictJson.text(snapshotId); Objects.requireNonNull(nativeRevision);
            StrictJson.require(nativeRevision.signum() >= 0, "original nonnegative opaque native revision required");
            Objects.requireNonNull(state); Objects.requireNonNull(originalPacket); originalPacket = originalPacket.clone(); Objects.requireNonNull(observedAt);
        }
        @Override public byte[] originalPacket() { return originalPacket.clone(); }
    }
}
