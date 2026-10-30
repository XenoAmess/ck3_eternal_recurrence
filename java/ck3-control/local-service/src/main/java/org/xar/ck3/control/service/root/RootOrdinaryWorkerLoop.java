package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.SessionController;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;

/**
 * Ordinary batch execution loop for a RootSessionAccess.
 * Runs real RootApplicationSession.batch via RootSessionAccess.current().
 * Does not manage Game lifecycle, transport, or session retirement.
 */
public final class RootOrdinaryWorkerLoop {

    public record Configuration(String batchIdPrefix, int maximumTurns, Duration wallTime, Duration readinessTimeout, Duration pollInterval, int checkpointEveryEligibleAdvances) {
        public Configuration {
            StrictJson.require(batchIdPrefix != null && batchIdPrefix.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,63}"), "bounded batch ID prefix required");
            new BatchLimits(batchIdPrefix + "-0", maximumTurns, wallTime, readinessTimeout, pollInterval, checkpointEveryEligibleAdvances);
        }
    }

    public interface Control {
        boolean stopRequested();
        void onBatchCompleted(BatchReport report, long nextBatchSequence) throws IOException, InterruptedException;
    }

    public enum StopReason {
        OPERATOR_STOP, NO_PROGRESS, EPISODE_HANDOFF_STALE, TERMINAL_FAILURE, INTERRUPTED, CALLBACK_FAILURE, BATCH_SEQUENCE_EXHAUSTED
    }

    public record Result(Optional<BatchReport> lastReport, long nextBatchSequence, StopReason stopReason, Optional<String> failureDetail) {
        public Result {
            Objects.requireNonNull(lastReport);
            Objects.requireNonNull(stopReason);
            Objects.requireNonNull(failureDetail);
            StrictJson.require(nextBatchSequence >= 0, "nonnegative next batch sequence required");
        }
    }

    private final Configuration configuration;
    private final Control control;

    public RootOrdinaryWorkerLoop(Configuration configuration, Control control) {
        this.configuration = Objects.requireNonNull(configuration);
        this.control = Objects.requireNonNull(control);
    }

    public Result run(RootSessionAccess access, long firstDurableBatchSequence) throws IOException, InterruptedException {
        Objects.requireNonNull(access);
        StrictJson.require(firstDurableBatchSequence >= 0, "nonnegative first durable batch sequence required");
        return run(new BatchAccessAdapter(access), firstDurableBatchSequence);
    }

    Result run(BatchAccess access, long firstDurableBatchSequence) throws IOException, InterruptedException {
        Objects.requireNonNull(access);
        StrictJson.require(firstDurableBatchSequence >= 0, "nonnegative first durable batch sequence required");
        long sequence = firstDurableBatchSequence;
        Optional<BatchReport> lastReport = Optional.empty();
        Optional<BatchReport> previousReport = Optional.empty();
        StopReason stopReason = StopReason.OPERATOR_STOP;
        Optional<String> failureDetail = Optional.empty();

        while (true) {
            if (sequence == Long.MAX_VALUE) {
                stopReason = StopReason.BATCH_SEQUENCE_EXHAUSTED;
                break;
            }

            try {
                if (control.stopRequested()) {
                    stopReason = StopReason.OPERATOR_STOP;
                    break;
                }
            } catch (RuntimeException e) {
                stopReason = StopReason.TERMINAL_FAILURE;
                failureDetail = Optional.of(e.toString());
                break;
            }

            String batchId = configuration.batchIdPrefix + "-" + sequence;
            BatchLimits limits = new BatchLimits(
                batchId,
                configuration.maximumTurns,
                configuration.wallTime,
                configuration.readinessTimeout,
                configuration.pollInterval,
                configuration.checkpointEveryEligibleAdvances
            );

            BatchReport report;
            BatchCurrent currentSession;
            try {
                currentSession = access.current();
                currentSession.controller().bindExternalStopSignal(control::stopRequested);
                report = currentSession.execution().batch(limits);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                stopReason = StopReason.INTERRUPTED;
                failureDetail = Optional.of(e.toString());
                break;
            } catch (IOException e) {
                stopReason = StopReason.TERMINAL_FAILURE;
                failureDetail = Optional.of(e.toString());
                break;
            } catch (RuntimeException e) {
                stopReason = StopReason.TERMINAL_FAILURE;
                failureDetail = Optional.of(e.toString());
                break;
            }

            lastReport = Optional.of(report);
            sequence = Math.addExact(sequence, 1L);

            try {
                control.onBatchCompleted(report, sequence);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                stopReason = StopReason.CALLBACK_FAILURE;
                failureDetail = Optional.of(e.toString());
                break;
            } catch (IOException e) {
                stopReason = StopReason.CALLBACK_FAILURE;
                failureDetail = Optional.of(e.toString());
                break;
            } catch (RuntimeException e) {
                stopReason = StopReason.CALLBACK_FAILURE;
                failureDetail = Optional.of(e.toString());
                break;
            }

            boolean cleanWallBoundary = isCleanWallBoundary(report.terminal(),
                    currentSession.controller().isQuarantined());
            if (report.terminal() == BatchReport.Terminal.CHECKPOINT_DEFERRED && !currentSession.controller().isQuarantined()) {
                try {
                    if (control.stopRequested()) {
                        stopReason = StopReason.OPERATOR_STOP;
                        break;
                    }
                } catch (RuntimeException e) {
                    stopReason = StopReason.TERMINAL_FAILURE;
                    failureDetail = Optional.of(e.toString());
                    break;
                }
            }
            if (report.terminal() != BatchReport.Terminal.TURN_BOUND
                    && report.terminal() != BatchReport.Terminal.EPISODE_HANDOFF
                    && report.terminal() != BatchReport.Terminal.OPERATOR_STOP
                    && !cleanWallBoundary) {
                stopReason = StopReason.TERMINAL_FAILURE;
                failureDetail = Optional.of(report.terminal().name() + ": " + report.detail());
                break;
            }

            try {
                if (control.stopRequested()) {
                    stopReason = StopReason.OPERATOR_STOP;
                    break;
                }
            } catch (RuntimeException e) {
                stopReason = StopReason.TERMINAL_FAILURE;
                failureDetail = Optional.of(e.toString());
                break;
            }

            if (report.terminal() == BatchReport.Terminal.TURN_BOUND) {
                if (!progressed(report, previousReport)) {
                    stopReason = StopReason.NO_PROGRESS;
                    break;
                }
                previousReport = Optional.of(report);
                continue;
            } else if (cleanWallBoundary) {
                if (noProgressAfterWall(report, currentSession.controller().lastBatchBoundary(), configuration.wallTime())) {
                    stopReason = StopReason.NO_PROGRESS;
                    break;
                }
                previousReport = Optional.of(report);
                continue;
            } else if (report.terminal() == BatchReport.Terminal.EPISODE_HANDOFF) {
                try {
                    var newCurrent = access.current();
                    if (newCurrent.controller() == currentSession.controller()) {
                        stopReason = StopReason.EPISODE_HANDOFF_STALE;
                        break;
                    }
                    continue;
                } catch (IOException e) {
                    stopReason = StopReason.TERMINAL_FAILURE;
                    failureDetail = Optional.of(e.toString());
                    break;
                } catch (RuntimeException e) {
                    stopReason = StopReason.TERMINAL_FAILURE;
                    failureDetail = Optional.of(e.toString());
                    break;
                }
            } else {
                if (report.terminal() == BatchReport.Terminal.OPERATOR_STOP) {
                    stopReason = StopReason.OPERATOR_STOP;
                } else {
                    stopReason = StopReason.TERMINAL_FAILURE;
                    failureDetail = Optional.of(report.terminal().name() + ": " + report.detail());
                }
                break;
            }
        }

        return new Result(lastReport, sequence, stopReason, failureDetail);
    }

    interface BatchAccess {
        BatchCurrent current() throws IOException;
    }

    record BatchCurrent(SessionController controller, BatchCall execution) {
        public BatchCurrent {
            Objects.requireNonNull(controller);
            Objects.requireNonNull(execution);
        }
    }

    interface BatchCall {
        BatchReport batch(BatchLimits limits) throws IOException, InterruptedException;
    }

    private final class BatchAccessAdapter implements BatchAccess {
        private final RootSessionAccess access;
        BatchAccessAdapter(RootSessionAccess access) { this.access = Objects.requireNonNull(access); }
        public BatchCurrent current() throws IOException {
            var root = access.current();
            return new BatchCurrent(root.controllerForPublication(), root::batch);
        }
    }

    static boolean isCleanWallBoundary(BatchReport.Terminal terminal, boolean quarantined) {
        return terminal == BatchReport.Terminal.WALL_TIMEOUT && !quarantined;
    }

    static boolean noProgressAfterWall(BatchReport report, Optional<SessionController.BatchBoundary> boundary, Duration wallTime) {
        if (report.terminal() != BatchReport.Terminal.WALL_TIMEOUT || report.fullWallNanos() < wallTime.toNanos()
                || !report.turns().isEmpty() || !report.reconciliations().isEmpty() || !report.lifecycleTurns().isEmpty()
                || !report.readPublicationReconciliations().isEmpty() || report.committedSavedDays() > 0
                || report.phases().stream().anyMatch(span -> span.phase() == BatchReport.Phase.ACTION
                        || span.phase() == BatchReport.Phase.ACTION_RECONCILIATION
                        || span.phase() == BatchReport.Phase.CHECKPOINT)) return false;
        if (boundary.isEmpty()) return false;
        var actual = boundary.orElseThrow();
        if (!actual.batchId().equals(report.batchId()) || !actual.session().equals(report.session())
                || actual.pendingAction() || actual.observedDateChanged()) return false;
        // Missing end observations are not manufactured. The complete zero-dispatch wall bound
        // can end this business worker; the existing restart capture still validates actual pending state.
        if (actual.firstObservation().isEmpty() || actual.lastObservation().isEmpty()) return true;
        var first = actual.firstObservation().orElseThrow();
        var last = actual.lastObservation().orElseThrow();
        return first.machineId().equals(report.session().machineId()) && first.game().equals(report.session().game())
                && first.machineId().equals(last.machineId()) && first.game().equals(last.game())
                && first.frame().episodeRunId().equals(last.frame().episodeRunId())
                && first.frame().identity().player().equals(last.frame().identity().player())
                && first.frame().identity().dateRaw().equals(last.frame().identity().dateRaw());
    }

    static boolean progressed(BatchReport current, Optional<BatchReport> previous) {
        if (!current.turns().isEmpty() || !current.reconciliations().isEmpty() || !current.lifecycleTurns().isEmpty() ||
            !current.readPublicationReconciliations().isEmpty() || !current.revisionReplans().isEmpty()) {
            return true;
        }
        if (previous.isPresent()) {
            var prev = previous.get();
            if (prev.session().equals(current.session())) {
                if (current.lastSavedPair().isPresent() && !current.lastSavedPair().equals(prev.lastSavedPair())) return true;
                if (current.committedLedgerHead().isPresent() && !current.committedLedgerHead().equals(prev.committedLedgerHead())) return true;
                if (current.committedSavedDays() > prev.committedSavedDays()) return true;
            }
        }
        return false;
    }

    /**
     * Caller-opt-in pause attempt after settled state. Response is not confirmation Game is paused.
     */
    public static PauseAttempt pauseSettledCurrent(RootSessionAccess access, Clock clock, Duration pauseDuration) throws IOException, InterruptedException {
        Objects.requireNonNull(access); Objects.requireNonNull(clock); Objects.requireNonNull(pauseDuration);
        StrictJson.require(!pauseDuration.isNegative() && !pauseDuration.isZero(), "positive pause duration required");
        try {
            var current = access.current();
            var catalog = current.installedCatalog();
            var request = new PublicPlanningCodec.ExecuteRequest(
                new OperationKey("pause-map"),
                new PublicPlanningCodec.RevisionMissing(),
                new PublicPlanningCodec.FrameMissing()
            );
            var deadline = clock.instant().plus(pauseDuration);
            var response = RootPublicStepExecution.execute(current, catalog, request, deadline);
            return new PauseAttempt(Optional.of(response), Optional.empty());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return new PauseAttempt(Optional.empty(), Optional.of(e.toString()));
        } catch (IOException e) {
            return new PauseAttempt(Optional.empty(), Optional.of(e.toString()));
        } catch (RuntimeException e) {
            return new PauseAttempt(Optional.empty(), Optional.of(e.toString()));
        }
    }

    public record PauseAttempt(Optional<RawJson> response, Optional<String> diagnostic) {
        public PauseAttempt {
            Objects.requireNonNull(response);
            Objects.requireNonNull(diagnostic);
            StrictJson.require(response.isPresent() ^ diagnostic.isPresent(), "exactly one of response or diagnostic required");
        }
    }
}
