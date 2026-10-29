package org.xar.ck3.control.wave3.governance.marriagepending;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffModel.FamilyRecord;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffModel.Ledger;

/** Exact pending-result read schedule. No state mutation or submission authority. */
public final class MarriagePendingModel {
    private static final BigInteger UINT64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private MarriagePendingModel() { }
    public record ProcessIdentity(long pid, String creationDate) {
        public ProcessIdentity {
            if (pid <= 0 || pid > 0xffff_ffffL) { throw new IllegalArgumentException("positive native PID required"); }
            StrictJson.text(creationDate);
        }
    }
    public record RetainedProcess(Long pid, String creationDate) {
        public RetainedProcess {
            if (pid != null && (pid <= 0 || pid > 0xffff_ffffL)) { throw new IllegalArgumentException("retained PID outside native domain"); }
            if (creationDate != null) { StrictJson.text(creationDate); }
        }
        public boolean matches(ProcessIdentity current) { return pid != null && pid == current.pid() && Objects.equals(creationDate, current.creationDate()); }
    }
    public record Frame(String episodeRunId, BigInteger nativeRevision) {
        public Frame { StrictJson.text(episodeRunId); if (nativeRevision != null) { revision(nativeRevision); } }
    }
    public record Pending(FamilyRecord original, RetainedProcess sourceProcess, RetainedProcess lastCheckedProcess,
                          BigInteger lastCheckedNativeRevision, boolean coldAbsentRelationUnresolved,
                          String lastOutboundPendingState) {
        public Pending {
            Objects.requireNonNull(original); Objects.requireNonNull(sourceProcess); Objects.requireNonNull(lastCheckedProcess);
            revision(lastCheckedNativeRevision); if (lastOutboundPendingState != null) { StrictJson.text(lastOutboundPendingState); }
        }
    }
    public record Inputs(Ledger ledger, Pending pending, Frame frame, ProcessIdentity currentProcess) {
        public Inputs {
            Objects.requireNonNull(ledger); Objects.requireNonNull(frame);
            if ((ledger.pending() == null) != (pending == null) || (pending != null && !ledger.pending().equals(pending.original()))) {
                throw new IllegalArgumentException("pending schedule crossed its ledger source");
            }
            if (MarriagePendingReadPolicy.requiresCurrentProcess(ledger, frame)) { Objects.requireNonNull(currentProcess, "same episode pending needs actual current bridge identity"); }
        }
    }
    public sealed interface Decision permits NoPending, OtherEpisode, ReadResult, WaitLater { }
    /** Caller falls through to its existing non-pending planner. */
    public record NoPending() implements Decision { }
    public record OtherEpisode() implements Decision { }
    public record ReadResult(Pending pending, boolean coldRecovery) implements Decision { public ReadResult { Objects.requireNonNull(pending); } }
    public record WaitLater(Pending pending) implements Decision { public WaitLater { Objects.requireNonNull(pending); } }
    static void revision(BigInteger value) {
        if (value == null || value.signum() < 0 || value.compareTo(UINT64_MAX) > 0) { throw new IllegalArgumentException("exact uint64 revision required"); }
    }
}

