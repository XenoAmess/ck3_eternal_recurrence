package org.xar.ck3.control.wave2.runtime.clockreader;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Attempt;
import org.xar.ck3.control.reconciliation.LateOutcome.Budget;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockCustodyGuard.Source;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockCustodyGuard.Role;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockPinnedFiles.Pin;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderApplication.OriginalWriterRecheck;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderApplication.RunResult;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ReadLedger;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.SystemTimeSource;
import org.xar.ck3.control.wave2.runtime.stdioidentity.Win32ProcessIdentityReader;
import org.xar.ck3.control.wave2.runtime.closedadoption.OriginalWriterTransaction;

/** Production wiring: shared measured Win32 birth reader and the existing same-session Queue channel. */
public final class ClockReaderSession implements AutoCloseable {
    private final OriginalQueueFileReader reader;
    private final ClockReaderApplication application;
    private final Attempt attempt;
    private final Pin expectedWriterHead;
    private final Thread owner = Thread.currentThread();
    ClockReaderSession(OriginalQueueFileReader reader, ClockReaderApplication application, Attempt attempt, Pin expectedWriterHead) {
        this.reader = Objects.requireNonNull(reader); this.application = Objects.requireNonNull(application);
        this.attempt = Objects.requireNonNull(attempt); this.expectedWriterHead = Objects.requireNonNull(expectedWriterHead);
        StrictJson.require(expectedWriterHead.sha256().equals(attempt.expectedHead().sha256())
                && expectedWriterHead.bytes() == attempt.expectedHead().bytes(), "same admitted original writer head pin");
    }
    public static ClockReaderSession open(Path admittedChannelRoot, Pin channelManifest, Attempt attempt, List<Source> sources)
            throws IOException {
        var time = new SystemTimeSource();
        List<Source> admittedSources = List.copyOf(sources);
        var guard = new ClockCustodyGuard(attempt, admittedSources, new Win32ClockProcessProbe(new Win32ProcessIdentityReader()));
        var reader = new OriginalQueueFileReader(admittedChannelRoot, channelManifest, attempt, guard, time);
        Pin expectedHead = admittedSources.stream().filter(source -> source.role() == Role.EXPECTED_HEAD)
                .findFirst().orElseThrow().pin();
        return new ClockReaderSession(reader, new ClockReaderApplication(reader, time), attempt, expectedHead);
    }
    public RunResult reconcile(Budget budget, ReadLedger completePriorLedger) throws IOException, InterruptedException {
        requireOwner();
        return application.run(attempt, budget, completePriorLedger);
    }
    /** The original writer invokes this callback under its own existing lock; this session cannot commit. */
    public OriginalWriterRecheck originalWriterRecheck(RunResult proposal) {
        requireOwner();
        OriginalWriterRecheck callback = application.originalWriterRecheck(proposal);
        return () -> { requireOwner(); return callback.recheck(); };
    }
    /**
     * Mechanical adapter for the actual original writer's lock-held callback point.
     * The fixed closed-failure entry must not install this live-reader callback or grant it live scope.
     */
    public OriginalWriterTransaction.LockedRecheck originalWriterLockedRecheck(RunResult proposal) {
        OriginalWriterRecheck callback = originalWriterRecheck(proposal);
        return target -> {
            requireOwner(); Objects.requireNonNull(target);
            ClockPinnedFiles.require(target.canonicalPath().toRealPath().equals(expectedWriterHead.contentStamp().realPath()),
                    "original locked writer target differs from the admitted clock head");
            ClockPinnedFiles.read(expectedWriterHead, 65_536);
            callback.recheck();
        };
    }
    private void requireOwner() {
        StrictJson.require(Thread.currentThread() == owner, "clock reader belongs to its retained Root owner thread");
    }
    @Override public void close() throws IOException { requireOwner(); reader.close(); }
}
