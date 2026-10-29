package org.xar.ck3.control.wave2.runtime.clockreader;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Attempt;
import org.xar.ck3.control.reconciliation.LateOutcome.ProcessIdentity;
import org.xar.ck3.control.reconciliation.LateOutcome.Read;
import org.xar.ck3.control.reconciliation.LateOutcome.ReadKind;

/** Application ports. Implementations borrow original custody; none creates a native client. */
public final class ClockReaderPorts {
    private ClockReaderPorts() { }
    public record Tick(long elapsedMillis, Instant utc) {
        public Tick { StrictJson.safe(elapsedMillis, 0); Objects.requireNonNull(utc); }
    }
    public interface TimeSource {
        Tick now();
        void waitMillis(long millis) throws InterruptedException;
    }
    public record ProcessObservation(ProcessIdentity identity, Path executable, CrossJsDecimalUInt64 win32UptimeMillis) {
        public ProcessObservation {
            Objects.requireNonNull(identity); Objects.requireNonNull(executable); Objects.requireNonNull(win32UptimeMillis);
            StrictJson.require(executable.isAbsolute(), "absolute measured executable path required");
        }
    }
    @FunctionalInterface public interface KernelProcessProbe {
        /** Must measure actual live kernel creation FILETIME, not decode a claimed alive flag. */
        ProcessObservation observe(long pid) throws IOException;
    }
    public record ReadCommand(Attempt attempt, ReadKind kind, String ticket, int maximumRawReplyBytes,
                              long remainingMillis, Instant hardDeadline) {
        public ReadCommand {
            Objects.requireNonNull(attempt); Objects.requireNonNull(kind);
            StrictJson.require(ticket != null && ticket.matches("[0-9a-f]{32}"), "canonical unique ticket");
            StrictJson.require(maximumRawReplyBytes >= 1 && maximumRawReplyBytes <= 8 * 1024 * 1024, "bounded raw native reply");
            StrictJson.require(remainingMillis >= 1 && remainingMillis <= 3_600_000, "bounded remaining read time");
            Objects.requireNonNull(hardDeadline);
        }
    }
    public interface OriginalQueueReadPort {
        /** Actually remeasure original kernel/source custody; a claimed scope or GREEN flag is insufficient. */
        void verifyCustody(Attempt attempt) throws IOException;
        /** Actual persistent transport ledger count, including known-error replies; cannot reset on host restart. */
        int completedReadCount(Attempt attempt) throws IOException;
        /** Rebind every supplied typed fact to the preserved original request/reply/row/guard artifacts. */
        void verifyCompleteLedger(Attempt attempt, ReadLedger ledger) throws IOException;
        /** One unique transport read. It must retain the original raw result before returning. */
        Read read(ReadCommand command) throws IOException, InterruptedException;
    }
    public record ReadLedger(List<Read> reads) {
        public ReadLedger {
            reads = List.copyOf(reads); StrictJson.require(reads.size() <= 64, "bounded original read ledger");
            long previous = 0;
            for (Read read : reads) {
                StrictJson.require(read.evidence().sequence() > previous, "unique ordered transport sequences");
                previous = read.evidence().sequence();
            }
        }
    }
    /** Concrete application clock. Native Win32 uptime is supplied separately by the process probe. */
    public static final class SystemTimeSource implements TimeSource {
        private final long startNanos = System.nanoTime();
        @Override public Tick now() { return new Tick((System.nanoTime() - startNanos) / 1_000_000L, Instant.now()); }
        @Override public void waitMillis(long millis) throws InterruptedException {
            StrictJson.require(millis >= 0 && millis <= 3_600_000, "bounded application wait"); Thread.sleep(millis);
        }
    }
}
