package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;

/** Packet boundary used by the Win32 provider and original-producer replay tests. Not an action authority. */
public interface NativePacketPort extends AutoCloseable {
    /** Produced by an actual deadline check, never by interpreting an IO message. */
    final class DeadlineExpired extends IOException {
        private static final long serialVersionUID=1L;
        private final transient org.xar.ck3.control.application.action.NativeActionPort.DeadlineObservation observation;
        public DeadlineExpired(org.xar.ck3.control.application.action.NativeActionPort.DeadlineObservation observation) {
            super("Native transport deadline expired");this.observation=Objects.requireNonNull(observation);
        }
        public org.xar.ck3.control.application.action.NativeActionPort.DeadlineObservation observation(){return observation;}
    }
    sealed interface WaitResult permits Packet, Elapsed { }
    record Packet(byte[] originalPacket) implements WaitResult {
        public Packet {
            Objects.requireNonNull(originalPacket);
            if (originalPacket.length < 5 || originalPacket.length > NativeWire.MAXIMUM_FRAME_BYTES + 4)
                throw new IllegalArgumentException("bounded complete original Native packet required");
            originalPacket = originalPacket.clone();
        }
        @Override public byte[] originalPacket() { return originalPacket.clone(); }
    }
    record Elapsed(Instant waitUntil, Instant observedAt) implements WaitResult {
        public Elapsed {
            Objects.requireNonNull(waitUntil); Objects.requireNonNull(observedAt);
            if (observedAt.isBefore(waitUntil)) throw new IllegalArgumentException("zero-prefix deadline must actually have elapsed");
        }
    }
    /** Actual interrupted read custody; partial bytes can never be mistaken for a completed packet or elapsed wait. */
    final class ReadInterrupted extends InterruptedException {
        private static final long serialVersionUID = 1L;
        private final byte[] originalPartialPacket;
        public ReadInterrupted(byte[] originalPartialPacket, InterruptedException original) {
            super(Objects.requireNonNull(original).getMessage());
            this.originalPartialPacket = Objects.requireNonNull(originalPartialPacket).clone(); initCause(original);
        }
        public byte[] originalPartialPacket() { return originalPartialPacket.clone(); }
    }
    /** Actual native connection boundary DATA; only the Win32 endpoint constructs an observation. */
    final class Disconnection {
        private final String operation;
        private final int win32Code;
        private final boolean nativeDisconnectSucceeded;
        Disconnection(String operation,int win32Code,boolean nativeDisconnectSucceeded) {
            this.operation=Objects.requireNonNull(operation);this.win32Code=win32Code;
            this.nativeDisconnectSucceeded=nativeDisconnectSucceeded;
            if(nativeDisconnectSucceeded ? !operation.equals("DisconnectNamedPipe")||win32Code!=0
                    : win32Code!=109&&win32Code!=232&&win32Code!=233)
                throw new IllegalArgumentException("actual successful native disconnect or original Win32 pipe-loss code required");
        }
        public String operation(){return operation;}
        public int win32Code(){return win32Code;}
        public boolean nativeDisconnectSucceeded(){return nativeDisconnectSucceeded;}
    }
    final class ConnectionLost extends IOException {
        private static final long serialVersionUID=1L;
        private final transient Disconnection original;
        ConnectionLost(Disconnection original) {
            super(Objects.requireNonNull(original).operation()+" Win32="+original.win32Code());this.original=original;
        }
        public Disconnection original(){return original;}
    }
    /** Pure actual source readback, never inferred from close(), IOException text, timeout or an ACK. */
    default java.util.Optional<Disconnection> originalDisconnection(){return java.util.Optional.empty();}
    void verify() throws IOException;
    void awaitConnection(Instant deadline) throws IOException, InterruptedException;
    byte[] readPacket(Instant deadline) throws IOException, InterruptedException;
    /** Legacy providers cannot infer a timeout from an IOException or silently call another observation route. */
    default WaitResult readPacketUntil(Instant waitUntil, Instant captureUntil) throws IOException, InterruptedException {
        throw new IOException("actual Native packet provider does not implement typed zero-prefix waiting");
    }
    void writePacket(byte[] packet, Instant deadline) throws IOException, InterruptedException;
    @Override void close() throws IOException;
}
