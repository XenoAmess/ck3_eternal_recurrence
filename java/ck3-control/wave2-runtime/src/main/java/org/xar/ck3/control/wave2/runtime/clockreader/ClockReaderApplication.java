package org.xar.ck3.control.wave2.runtime.clockreader;

import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Assessment;
import org.xar.ck3.control.reconciliation.LateOutcome.Attempt;
import org.xar.ck3.control.reconciliation.LateOutcome.Budget;
import org.xar.ck3.control.reconciliation.LateOutcome.Context;
import org.xar.ck3.control.reconciliation.LateOutcome.GameLife;
import org.xar.ck3.control.reconciliation.LateOutcome.Outcome;
import org.xar.ck3.control.reconciliation.LateOutcome.Read;
import org.xar.ck3.control.reconciliation.LateOutcomePlanner;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.OriginalQueueReadPort;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ReadCommand;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ReadLedger;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.Tick;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.TimeSource;

/** Actual application coordination; all reads remain on the original Queue transport. */
public final class ClockReaderApplication {
    public record RunResult(Assessment assessment, ReadLedger ledger) {
        public RunResult { Objects.requireNonNull(assessment); Objects.requireNonNull(ledger); }
        public int originalCredit() { return 0; }
        public boolean neverReplay() { return true; }
    }
    /**
     * Read-only callback for the original writer to invoke while it actually holds its existing lock.
     * This interface does not acquire or prove that lock, run a reducer, approve CAS, or commit.
     */
    @FunctionalInterface public interface OriginalWriterRecheck {
        RunResult recheck() throws IOException;
    }
    private record LocalRun(Attempt attempt, Budget budget, RunResult result) { }
    private final OriginalQueueReadPort reader;
    private final TimeSource time;
    private LocalRun latest;
    public ClockReaderApplication(OriginalQueueReadPort reader, TimeSource time) {
        this.reader = Objects.requireNonNull(reader); this.time = Objects.requireNonNull(time);
    }
    /** Input history is the actual complete prior read ledger, never a de-duplicated cache. */
    public synchronized RunResult run(Attempt attempt, Budget budget, ReadLedger prior)
            throws IOException, InterruptedException {
        Objects.requireNonNull(attempt); Objects.requireNonNull(budget); Objects.requireNonNull(prior);
        // Any later run invalidates a callback from the preceding run, even if the later run fails.
        latest = null;
        List<Read> history = new ArrayList<>(prior.reads());
        while (true) {
            RunResult current = assessCurrent(attempt, budget, new ReadLedger(history));
            Assessment assessment = current.assessment();
            if (assessment.outcome() != Outcome.WAIT) {
                latest = new LocalRun(attempt, budget, current); return current;
            }
            if (assessment.waitMillis() != 0) { time.waitMillis(assessment.waitMillis()); }
            Tick beforeRead = time.now();
            long local = budget.maximumDurationMillis() - beforeRead.elapsedMillis();
            Duration utc = Duration.between(beforeRead.utc(), budget.hardDeadline());
            if (local <= 0 || utc.isNegative() || utc.isZero()) { continue; }
            Duration clipped = Duration.ofMillis(local);
            if (utc.compareTo(clipped) < 0) { clipped = utc; }
            long remaining = clipped.toMillis();
            if (remaining <= 0) { time.waitMillis(1); continue; }
            ReadCommand command = new ReadCommand(attempt, assessment.nextRead(), UUID.randomUUID().toString().replace("-", ""),
                    8 * 1024 * 1024, remaining, budget.hardDeadline());
            // IOException preserves the unique request/INFLIGHT and raw transport error in the adapter.
            // It is never converted to an empty successful read or an automatic replay.
            history.add(reader.read(command));
        }
    }
    /**
     * Binds only the exact terminal result issued by this application instance and its original budget.
     * A reconstructed RunResult or serialized assessment cannot supply this local execution context.
     * The callback makes no new Queue request and always rebinds the preserved raw evidence again.
     */
    public synchronized OriginalWriterRecheck originalWriterRecheck(RunResult proposal) {
        Objects.requireNonNull(proposal);
        StrictJson.require(latest != null && latest.result() == proposal && proposal.assessment().outcome() == Outcome.PROPOSED,
                "only this application's actual current proposal can be rechecked");
        LocalRun issued = latest;
        return () -> recheck(issued);
    }
    private synchronized RunResult recheck(LocalRun issued) throws IOException {
        ClockPinnedFiles.require(latest == issued, "proposal superseded by another application run");
        RunResult current = assessCurrent(issued.attempt(), issued.budget(), issued.result().ledger());
        ClockPinnedFiles.require(current.assessment().outcome() == Outcome.PROPOSED
                && current.assessment().equals(issued.result().assessment()),
                "current original evidence no longer supports the same proposal");
        return current;
    }
    private RunResult assessCurrent(Attempt attempt, Budget budget, ReadLedger ledger) throws IOException {
        // Both sides are actual kernel/source measurements, including the preserved failure and expected writer head.
        reader.verifyCustody(attempt);
        reader.verifyCompleteLedger(attempt, ledger);
        int count = reader.completedReadCount(attempt);
        reader.verifyCustody(attempt);
        Tick tick = time.now();
        Assessment assessment = LateOutcomePlanner.assess(attempt, budget,
                new Context(GameLife.SAME_PROCESS_ALIVE, tick.elapsedMillis(), tick.utc(), count), ledger.reads());
        return new RunResult(assessment, ledger);
    }
}
