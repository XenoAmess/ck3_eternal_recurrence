package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionObservationWindow;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
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
    private final Clock clock;

    public RootOrdinaryWorkerLoop(Configuration configuration, Control control) {
        this(configuration, control, Clock.systemUTC());
    }

    RootOrdinaryWorkerLoop(Configuration configuration, Control control, Clock clock) {
        this.configuration = Objects.requireNonNull(configuration);
        this.control = Objects.requireNonNull(control);
        this.clock = Objects.requireNonNull(clock);
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

            if (isUnissuedLifeBudgetDeferral(report)) {
                if (currentSession.controller().isQuarantined() || currentSession.controller().isRetired()) {
                    stopReason = StopReason.TERMINAL_FAILURE;
                    failureDetail = Optional.of("budget deferral lost its actual clean Controller"); break;
                }
                if (previousReport.filter(previous -> sameUnissuedLifeBudgetScope(previous, report)).isPresent()) {
                    stopReason = StopReason.NO_PROGRESS;
                    failureDetail = Optional.of("a second consecutive fresh batch still lacks the estimated Life budget; no action was issued"); break;
                }
                // One new normal batch, never a renewed command or a reused selected plan.
                previousReport = Optional.of(report); continue;
            }

            if (report.terminal() == BatchReport.Terminal.CHECKPOINT_UNKNOWN && currentSession.controller().isQuarantined()) {
                try {
                    if (control.stopRequested()) { stopReason = StopReason.OPERATOR_STOP; break; }
                    boolean recovered = currentSession.execution().recoverCheckpointStability(report, sequence,
                            clock.instant().plus(ActionObservationWindow.MAXIMUM_WINDOW));
                    if (control.stopRequested()) { stopReason = StopReason.OPERATOR_STOP; break; }
                    if (recovered && !currentSession.controller().isQuarantined()) continue;
                } catch (InterruptedException failure) {
                    Thread.currentThread().interrupt(); stopReason = StopReason.INTERRUPTED;
                    failureDetail = Optional.of(failure.toString()); break;
                } catch (IOException | RuntimeException failure) {
                    stopReason = StopReason.TERMINAL_FAILURE;
                    failureDetail = Optional.of(failure.toString()); break;
                }
                // Unqualified or still-unconfirmed originals retain the original failure path below.
            }
            if (report.terminal() == BatchReport.Terminal.WALL_TIMEOUT
                    && currentSession.controller().isQuarantined() && appliedLifeAtWall(report).isPresent()) {
                try {
                    if (control.stopRequested()) { stopReason = StopReason.OPERATOR_STOP; break; }
                    // A new read/reconciliation budget never changes the original command deadline.
                    boolean recovered = currentSession.execution().recoverWallBoundary(report, sequence,
                            clock.instant().plus(configuration.wallTime()));
                    if (control.stopRequested()) { stopReason = StopReason.OPERATOR_STOP; break; }
                    if (!recovered || currentSession.controller().isQuarantined()) {
                        stopReason = StopReason.TERMINAL_FAILURE;
                        failureDetail = Optional.of(report.terminal().name() + ": " + report.detail());
                        break;
                    }
                } catch (InterruptedException failure) {
                    Thread.currentThread().interrupt(); stopReason = StopReason.INTERRUPTED;
                    failureDetail = Optional.of(failure.toString()); break;
                } catch (IOException | RuntimeException failure) {
                    stopReason = StopReason.TERMINAL_FAILURE;
                    failureDetail = Optional.of(failure.toString()); break;
                }
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
        default boolean recoverCheckpointStability(BatchReport report, long nextBatchSequence, Instant deadline)
                throws IOException, InterruptedException { return false; }
        default boolean recoverWallBoundary(BatchReport report, long nextBatchSequence, Instant deadline)
                throws IOException, InterruptedException { return false; }
    }

    private final class BatchAccessAdapter implements BatchAccess {
        private final RootSessionAccess access;
        BatchAccessAdapter(RootSessionAccess access) { this.access = Objects.requireNonNull(access); }
        public BatchCurrent current() throws IOException {
            var root = access.current();
            return new BatchCurrent(root.controllerForPublication(), new BatchCall() {
                @Override public BatchReport batch(BatchLimits limits) throws IOException, InterruptedException {
                    return root.batch(limits);
                }
                @Override public boolean recoverCheckpointStability(BatchReport report, long nextBatchSequence, Instant deadline)
                        throws IOException, InterruptedException {
                    return recoverRetainedSaveStability(root, report, nextBatchSequence, deadline);
                }
                @Override public boolean recoverWallBoundary(BatchReport report, long nextBatchSequence, Instant deadline)
                        throws IOException, InterruptedException {
                    return recoverRetainedWallCycle(root, report, nextBatchSequence, deadline);
                }
            });
        }
    }

    /** One bounded collection of this live Root's original ACK SAVE; no batch or command deadline is extended. */
    private boolean recoverRetainedSaveStability(RootApplicationSession root, BatchReport report,
            long nextBatchSequence, Instant deadline) throws IOException, InterruptedException {
        var controller = root.controllerForPublication();
        if (report.terminal() != BatchReport.Terminal.CHECKPOINT_UNKNOWN || !report.session().equals(root.identity())
                || controller.lastReport().filter(report::equals).isEmpty() || !controller.isQuarantined()
                || controller.isRunning() || controller.isRetired() || control.stopRequested()
                || !clock.instant().isBefore(deadline)) return false;
        var retained = root.withPublicStandaloneRead(deadline, same -> {
            var data = root.batchJournal().readUnresolvedSameGame(same, root.identity());
            var head = same.head();
            StrictJson.require(data.canonicalSequence() == head.state().sequence()
                    && data.canonicalHeadDigest().equals(head.digest()), "warm SAVE DATA changed its actual head");
            StrictJson.require(data.capturedController().owner().equals(report.session())
                    && data.nextBatchSequence() == nextBatchSequence && nextBatchSequence > 0
                    && data.usedBatches().contains(report.batchId())
                    && report.batchId().equals(data.capturedController().batchPrefix() + "-" + (nextBatchSequence - 1)),
                    "warm SAVE DATA changed its actual owner or interrupted batch");
            if (data.retainedHistory().isEmpty() || data.retainedHistory().orElseThrow().cycleSemantic().isEmpty()
                    || data.capturedController().savedPair().isEmpty() || data.unresolvedActions().size() != 1
                    || !awaitsSecondStableSave(data.unresolvedActions().getFirst()))
                return Optional.<ContinuityBatchJournal.UnresolvedSameGameData>empty();
            return Optional.of(data);
        });
        if (retained.isEmpty() || control.stopRequested() || !clock.instant().isBefore(deadline)) return false;
        var data = retained.orElseThrow();var original = data.unresolvedActions().getFirst();
        // Release the DATA reader's borrowed writer before using this same live Controller's original reconciliation.
        ActionReceipt actual = root.reconcileUnresolvedOriginal(data, deadline);
        if (!actual.settled() && awaitsSecondStableSave(actual) && !control.stopRequested()
                && clock.instant().isBefore(deadline)) actual = root.reconcileUnresolvedOriginal(data, deadline);
        return actual.settled() && actual.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                && actual.bodySha256().equals(original.bodySha256())
                && java.util.Arrays.equals(ActionCodec.encodeCommand(actual.command()), ActionCodec.encodeCommand(original.command()))
                && root.controllerForPublication() == controller && !controller.isQuarantined() && !controller.isRetired()
                && controller.savedPair().filter(pair -> pair.saveActionId().equals(original.command().actionId())).isPresent();
    }

    /** Eligibility DATA only; the existing original observer, physical pair and canonical SAVE commit remain mandatory. */
    static boolean awaitsSecondStableSave(ActionReceipt actual) {
        if (!(actual.state() instanceof ActionState.Unknown unknown)
                || !unknown.reason().equals("SAVE awaits second stable physical observation")
                || !ContinuityBatchJournal.isReadOnlySaveRecovery(actual)) return false;
        var dispatch = ActionTransitions.dispatch(actual.state());
        return dispatch.isPresent() && dispatch.orElseThrow() instanceof NativeActionPort.AckReceived ack
                && ack.outbound().isPresent();
    }

    private boolean recoverRetainedWallCycle(RootApplicationSession root, BatchReport report,
            long nextBatchSequence, Instant deadline) throws IOException, InterruptedException {
        var original = appliedLifeAtWall(report);
        var controller = root.controllerForPublication();
        if (original.isEmpty() || !report.session().equals(root.identity()) || !controller.isQuarantined()
                || controller.isRunning() || controller.isRetired() || control.stopRequested()) return false;
        ActionReceipt expected = original.orElseThrow();
        var data = root.withPublicStandaloneRead(deadline, same -> {
            var actual = root.batchJournal().readUnresolvedSameGame(same, root.identity());
            var head = same.head();
            StrictJson.require(actual.canonicalSequence() == head.state().sequence()
                    && actual.canonicalHeadDigest().equals(head.digest()), "wall recovery DATA changed its actual head");
            StrictJson.require(actual.capturedController().owner().equals(report.session())
                    && actual.nextBatchSequence() == nextBatchSequence && nextBatchSequence > 0
                    && actual.usedBatches().contains(report.batchId())
                    && report.batchId().equals(actual.capturedController().batchPrefix() + "-" + (nextBatchSequence - 1)),
                    "wall recovery DATA changed its actual owner or interrupted batch");
            StrictJson.require(actual.unresolvedActions().size() == 1
                    && actual.unresolvedActions().getFirst().equals(expected),
                    "wall recovery DATA changed the exact reported applied Life receipt");
            return actual;
        });
        if (control.stopRequested()) return false;
        // The DATA read releases its borrowed writer before the original Controller reconciles.
        // Its retain/settle path revalidates the current canonical receipt and pending frontier.
        ActionReceipt actual = root.reconcileUnresolvedOriginal(data, deadline);
        return actual.equals(expected) && isAppliedLife(actual) && root.controllerForPublication() == controller
                && !controller.isQuarantined() && !controller.isRetired();
    }

    static Optional<ActionReceipt> appliedLifeAtWall(BatchReport report) {
        if (report.terminal() != BatchReport.Terminal.WALL_TIMEOUT) return Optional.empty();
        var receipts = new java.util.ArrayList<ActionReceipt>();
        report.turns().forEach(turn -> receipts.add(turn.receipt()));
        report.reconciliations().forEach(turn -> receipts.add(turn.originalReceipt()));
        report.lifecycleTurns().forEach(turn -> receipts.add(turn.receipt()));
        report.readPublicationReconciliations().forEach(turn -> receipts.add(turn.originalReceipt()));
        if (receipts.isEmpty() || receipts.stream().anyMatch(receipt -> !receipt.settled())) return Optional.empty();
        var latest = receipts.stream().max(java.util.Comparator.comparingLong(ActionReceipt::sequence)).orElseThrow();
        var command = latest.command();
        return isAppliedLife(latest) && command.sessionId().equals(report.session().sessionId())
                && command.origin().machineId().equals(report.session().machineId())
                && command.origin().game().equals(report.session().game()) ? Optional.of(latest) : Optional.empty();
    }

    private static boolean isAppliedLife(ActionReceipt receipt) {
        return receipt.settled() && receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                && receipt.visibleGameplay() && receipt.eligibleAdvance()
                && receipt.command().origin() instanceof CommandOrigin.Gameplay
                && LifeAdvanceComposite.accepts(receipt.command().operation().value())
                && receipt.state() instanceof ActionState.CompositeSettled settled
                && settled.settlement() instanceof ActionState.Applied
                && settled.execution().handlerId().equals(LifeAdvanceComposite.HANDLER);
    }

    /** A private producer detail on the actual zero-dispatch report; no new action capability. */
    static boolean isUnissuedLifeBudgetDeferral(BatchReport report) {
        if (report.terminal() != BatchReport.Terminal.WALL_TIMEOUT
                || !report.detail().startsWith("PRE_INTENT_LIFE_BUDGET_DEFERRED: ")
                || report.dirtySinceSave() || report.eligibleAdvancesSinceSave() != 0 || report.committedSavedDays() != 0
                || report.lastSavedPair().isEmpty() || report.lastPlan().isEmpty()
                || !report.turns().isEmpty() || !report.reconciliations().isEmpty() || !report.lifecycleTurns().isEmpty()
                || !report.readPublicationReconciliations().isEmpty() || !report.revisionReplans().isEmpty()
                || report.phases().stream().anyMatch(span -> span.phase() == BatchReport.Phase.ACTION
                    || span.phase() == BatchReport.Phase.ACTION_RECONCILIATION || span.phase() == BatchReport.Phase.CHECKPOINT)) return false;
        var selected = report.lastPlan().orElseThrow().finalPlan().flatMap(plan -> plan.command());
        return selected.filter(command -> command.origin() instanceof CommandOrigin.Gameplay
                && LifeAdvanceComposite.accepts(command.operation().value())
                && command.sessionId().equals(report.session().sessionId())
                && command.origin().machineId().equals(report.session().machineId())
                && command.origin().game().equals(report.session().game())).isPresent();
    }

    static boolean sameUnissuedLifeBudgetScope(BatchReport previous, BatchReport current) {
        if (!isUnissuedLifeBudgetDeferral(previous) || !isUnissuedLifeBudgetDeferral(current)
                || !previous.session().equals(current.session())) return false;
        var before = previous.lastPlan().orElseThrow().before();
        var after = current.lastPlan().orElseThrow().before();
        // Fresh READ revisions, snapshot IDs and domain imports do not manufacture game-day progress.
        return before.machineId().equals(after.machineId()) && before.game().equals(after.game())
                && before.frame().episodeRunId().equals(after.frame().episodeRunId())
                && before.frame().identity().player().equals(after.frame().identity().player())
                && before.frame().identity().dateRaw().equals(after.frame().identity().dateRaw());
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
        } else if (current.committedSavedDays() > 0) {
            return true;
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
