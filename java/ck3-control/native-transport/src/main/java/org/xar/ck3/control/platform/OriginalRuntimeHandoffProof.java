package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;

/** Live, scoped retirement custody. Serialized observations are DATA, never a lease. */
public final class OriginalRuntimeHandoffProof {
    private OriginalRuntimeHandoffProof() { }
    public enum Reason {
        ORIGINAL_OWNED_LAUNCH_UNAVAILABLE, ORIGINAL_LAUNCH_UNSUPPORTED,
        ORIGINAL_RETIREMENT_UNAVAILABLE, ORIGINAL_STORE_OR_MACHINE_DIFFERS
    }
    public sealed interface Result<T> permits Available, Unavailable { }
    public record Available<T>(T value) implements Result<T> { }
    public record Unavailable<T>(Reason reason, String detail, List<ExactRef> originalEvidence) implements Result<T> {
        public Unavailable {
            Objects.requireNonNull(reason); Objects.requireNonNull(detail);
            originalEvidence = List.copyOf(originalEvidence);
            if (detail.isBlank() || detail.length() > 1024) throw new IllegalArgumentException("Bounded reason required");
        }
    }
    @FunctionalInterface public interface Work<T> { T run(Lease lease) throws IOException; }

    /** Cannot be implemented by a caller or minted from a PID, flag or JSON receipt. */
    public static final class Provider {
        private final WindowsOriginalRuntimeHandoff binding;
        private Provider(WindowsOriginalRuntimeHandoff binding) { this.binding = binding; }
        public <T> Result<T> withOriginalStore(Path exactActualStore, String actualMachine, Work<T> work)
                throws IOException {
            Objects.requireNonNull(exactActualStore); Objects.requireNonNull(actualMachine); Objects.requireNonNull(work);
            if (!exactActualStore.isAbsolute() || !exactActualStore.normalize().equals(exactActualStore)
                    || !actualMachine.matches("[a-z0-9][a-z0-9-]{0,63}") || actualMachine.equals("unknown"))
                throw new IllegalArgumentException("Exact absolute store and known machine required");
            if (binding == null) return new Unavailable<>(Reason.ORIGINAL_OWNED_LAUNCH_UNAVAILABLE,
                    "No original in-memory owned Python launch/source/store object is available", List.of());
            WindowsOriginalRuntimeHandoff.Acquisition acquired = binding.acquire(exactActualStore, actualMachine);
            if (acquired instanceof WindowsOriginalRuntimeHandoff.Missing missing)
                return new Unavailable<>(missing.reason(), missing.detail(), missing.evidence());
            if (!(acquired instanceof WindowsOriginalRuntimeHandoff.Held held))
                throw new IOException("Unknown original custody acquisition branch");
            try (Lease lease = new Lease(held)) {
                lease.requireCurrent();
                T value = work.run(lease);
                lease.requireCurrent();
                return new Available<>(value);
            }
        }
    }
    public static Provider unavailable() { return new Provider(null); }
    static Provider bound(WindowsOriginalRuntimeHandoff original) { return new Provider(Objects.requireNonNull(original)); }

    /** Public type, private issuer; the importer must retain this same object through commit. */
    public static final class Lease implements AutoCloseable {
        private final WindowsOriginalRuntimeHandoff.Held held;
        private final Thread thread = Thread.currentThread();
        private boolean closed;
        private Lease(WindowsOriginalRuntimeHandoff.Held held) { this.held = held; }
        public Path originalStore() { return held.store(); }
        public String machineId() { return held.machine(); }
        public List<ExactRef> originalEvidence() { return held.evidence(); }
        /** Exact original read-only OS observation; archive these bytes without granting restored authority. */
        public byte[] originalObservation() { return held.originalObservation(); }
        public void requireCurrent() throws IOException {
            if (closed || Thread.currentThread() != thread) throw new IOException("Original handoff lease is closed or escaped its thread");
            held.requireCurrent();
        }
        @Override public void close() {
            if (closed) return;
            closed = true;
            held.close();
        }
    }
}
