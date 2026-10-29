package org.xar.ck3.control.admission.closedpartial;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Original immutable receipts. No process, SDK, filesystem or ledger operation is performed. */
public record ClosedPartialSources(RecoveryEvidence sdkClosed, RecoveryEvidence gameExit,
        RecoveryEvidence supervisorClosed, RecoveryEvidence recordingClosed, RecoveryEvidence captureClosed,
        RecoveryEvidence screenReleased, List<Task> tasks, List<Cycle> settledCycles) {
    public ClosedPartialSources {
        Objects.requireNonNull(sdkClosed); Objects.requireNonNull(gameExit);
        Objects.requireNonNull(supervisorClosed); Objects.requireNonNull(recordingClosed);
        Objects.requireNonNull(screenReleased); Objects.requireNonNull(captureClosed);
        tasks = List.copyOf(tasks); settledCycles = List.copyOf(settledCycles);
        StrictJson.require(tasks.size() == 3, "supervisor, feeder and display task closures required");
        StrictJson.require(!settledCycles.isEmpty() && settledCycles.size() <= 30, "bounded actual settled partial cycles");
    }
    public enum TaskRole { SUPERVISOR, FEEDER, DISPLAY }
    public record Task(TaskRole role, RecoveryEvidence spec, RecoveryEvidence closed, RecoveryEvidence unregistered) {
        public Task { Objects.requireNonNull(role); Objects.requireNonNull(spec);
            Objects.requireNonNull(closed); Objects.requireNonNull(unregistered); }
    }
    public record Cycle(ClosedPartialRpcEvidence auto, ClosedPartialRpcEvidence metrics) {
        public Cycle { Objects.requireNonNull(auto); Objects.requireNonNull(metrics); }
    }
}
