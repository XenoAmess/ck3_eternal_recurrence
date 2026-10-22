package org.xar.ck3.control.reconciliation;

import java.math.BigInteger;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Arm;
import org.xar.ck3.control.reconciliation.LateOutcome.Assessment;
import org.xar.ck3.control.reconciliation.LateOutcome.Attempt;
import org.xar.ck3.control.reconciliation.LateOutcome.Budget;
import org.xar.ck3.control.reconciliation.LateOutcome.Context;
import org.xar.ck3.control.reconciliation.LateOutcome.Evidence;
import org.xar.ck3.control.reconciliation.LateOutcome.GameLife;
import org.xar.ck3.control.reconciliation.LateOutcome.Outcome;
import org.xar.ck3.control.reconciliation.LateOutcome.Read;
import org.xar.ck3.control.reconciliation.LateOutcome.ReadKind;
import org.xar.ck3.control.reconciliation.LateOutcome.Reason;
import org.xar.ck3.control.reconciliation.LateOutcome.Scope;
import org.xar.ck3.control.reconciliation.LateOutcome.Semantic;
import org.xar.ck3.control.reconciliation.LateOutcome.SemanticRead;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.reconciliation.LateOutcome.StatusRead;
import org.xar.ck3.control.reconciliation.LateOutcome.UnavailableRead;
import static org.xar.ck3.control.reconciliation.LateOutcome.number;

/** Deterministic bounded assessment only. No clock, files, Game, Queue, writer, reducer or network I/O. */
public final class LateOutcomePlanner {
    private LateOutcomePlanner() { }

    /** The complete append-only read history is required; callers must not reset it to replenish budget. */
    public static Assessment assess(Attempt attempt, Budget budget, Context context, List<Read> history) {
        Objects.requireNonNull(attempt); Objects.requireNonNull(budget); Objects.requireNonNull(context);
        List<Read> reads = List.copyOf(history);
        StrictJson.require(reads.size() <= 64, "bounded complete reconciliation history");
        if (context.totalReadsConsumed() != reads.size()) {
            return new Assessment(Outcome.REJECTED, Reason.HISTORY_INCOMPLETE, null, 0,
                    context.totalReadsConsumed(), sequences(reads));
        }
        if (context.gameLife() == GameLife.CLOSED) { return end(Outcome.REJECTED, Reason.GAME_CLOSED, reads); }
        if (context.gameLife() != GameLife.SAME_PROCESS_ALIVE) { return end(Outcome.UNRESOLVED, Reason.GAME_LIVENESS_UNKNOWN, reads); }
        if (!context.now().isBefore(budget.hardDeadline())) { return end(Outcome.UNRESOLVED, Reason.DEADLINE_EXPIRED, reads); }
        if (context.elapsedMillis() >= budget.maximumDurationMillis() || reads.size() > budget.maximumReads()) {
            return end(Outcome.UNRESOLVED, Reason.BUDGET_EXHAUSTED, reads);
        }
        long previousSequence = attempt.original().autoSequence(), previousElapsed = -1;
        java.time.Instant previousTime = null;
        Status terminal = null;
        Semantic acceptedFrame = null, previousFrame = null;
        Evidence acceptedFrameEvidence = null;
        ReadKind expected = ReadKind.CURRENT_SENTINEL_STATUS;
        Reason waiting = Reason.NEED_STATUS;
        boolean complete = false;
        for (Read read : reads) {
            Evidence evidence = read.evidence();
            if (!attempt.scope().equals(evidence.before()) || !attempt.scope().equals(evidence.after())) {
                return end(Outcome.REJECTED, Reason.SOURCE_OR_IDENTITY_CHANGED, reads);
            }
            if (evidence.sequence() <= previousSequence) { return end(Outcome.REJECTED, Reason.READ_SEQUENCE_INVALID, reads); }
            if (evidence.receivedElapsedMillis() < previousElapsed || evidence.receivedElapsedMillis() > context.elapsedMillis()
                    || evidence.observedAt().isAfter(context.now()) || (previousTime != null && evidence.observedAt().isBefore(previousTime))) {
                return end(Outcome.REJECTED, Reason.READ_TIME_INVALID, reads);
            }
            previousSequence = evidence.sequence(); previousElapsed = evidence.receivedElapsedMillis(); previousTime = evidence.observedAt();
            if (read.kind() != expected || complete) { return end(Outcome.REJECTED, Reason.WRONG_READ_ORDER, reads); }
            if (read instanceof UnavailableRead) { return end(Outcome.UNRESOLVED, Reason.READ_UNAVAILABLE, reads); }
            if (read instanceof StatusRead statusRead) {
                Status status = statusRead.status();
                if (status.state() == State.UNAVAILABLE) { return end(Outcome.UNRESOLVED, Reason.READ_UNAVAILABLE, reads); }
                if (!sameArm(attempt.arm(), status)) { return end(Outcome.REJECTED, Reason.SLOT_CHANGED, reads); }
                if (status.state() == State.ARMED) {
                    if (terminal != null) { return end(Outcome.REJECTED, Reason.SLOT_CHANGED, reads); }
                    waiting = Reason.ARMED_GUARD_RETAINED;
                } else if (status.state() == State.TRIGGERED) {
                    if (!validStop(attempt.arm(), status)) { return end(Outcome.REJECTED, Reason.STOP_NOT_VALID, reads); }
                    if (terminal == null) {
                        terminal = status; expected = ReadKind.CURRENT_SEMANTIC_FRAME; waiting = Reason.NEED_PAUSED_SEMANTIC;
                    } else {
                        if (!terminal.equals(status)) { return end(Outcome.REJECTED, Reason.SLOT_CHANGED, reads); }
                        if (!fresh(acceptedFrame, acceptedFrameEvidence, budget, context)) {
                            return end(Outcome.UNRESOLVED, Reason.SEMANTIC_NOT_FRESH, reads);
                        }
                        complete = true;
                    }
                } else { return end(Outcome.UNRESOLVED, Reason.SLOT_NOT_TRIGGERED, reads); }
            } else if (read instanceof SemanticRead semanticRead) {
                Semantic frame = semanticRead.semantic();
                if (!sameFrameIdentity(attempt.scope(), frame)) { return end(Outcome.REJECTED, Reason.FRAME_IDENTITY_CHANGED, reads); }
                if (regressed(attempt, previousFrame, frame)) { return end(Outcome.REJECTED, Reason.FRAME_REGRESSED, reads); }
                previousFrame = frame;
                if (!frame.paused() || !frame.ownerPaused()) { waiting = Reason.SEMANTIC_NOT_PAUSED; }
                else if (!sampleFresh(frame, evidence, budget)) { waiting = Reason.SEMANTIC_NOT_FRESH; }
                else {
                    if (terminal == null || frame.dateRaw() != terminal.triggerDateRaw() || frame.ownerDateRaw() != frame.dateRaw()
                            || frame.speed() != terminal.speed()) { return end(Outcome.REJECTED, Reason.FRAME_DATE_CHANGED, reads); }
                    acceptedFrame = frame; acceptedFrameEvidence = evidence;
                    expected = ReadKind.CURRENT_SENTINEL_STATUS; waiting = Reason.NEED_CONFIRMING_STATUS;
                }
            }
        }
        if (complete) { return end(Outcome.PROPOSED, Reason.LATE_STOP_REQUIRES_WRITER_REDUCER, reads); }
        if (reads.size() >= budget.maximumReads()) { return end(Outcome.UNRESOLVED, Reason.BUDGET_EXHAUSTED, reads); }
        Duration localRemaining = Duration.ofMillis(budget.maximumDurationMillis() - context.elapsedMillis());
        Duration utcRemaining = Duration.between(context.now(), budget.hardDeadline());
        // Compare before conversion: an otherwise valid Instant.MAX deadline must not overflow millis.
        long remaining = (utcRemaining.compareTo(localRemaining) < 0 ? utcRemaining : localRemaining).toMillis();
        if (remaining <= 0) { return end(Outcome.UNRESOLVED, Reason.DEADLINE_EXPIRED, reads); }
        return new Assessment(Outcome.WAIT, waiting, expected, Math.min(budget.pollWaitMillis(), remaining), reads.size(), sequences(reads));
    }
    private static boolean sameArm(Arm arm, Status status) {
        return arm.generation().equals(status.generation()) && arm.startingDateRaw() == status.startingDateRaw()
                && arm.targetDateRaw() == status.targetDateRaw() && arm.speed() == status.speed()
                && arm.mode() == status.mode() && arm.watchArmyIds().size() == status.armyCount()
                && arm.combatCount() == status.combatCount();
    }
    /** Mirrors frozen SDK stop predicates, retaining pause ownership and day/tick checks. */
    private static boolean validStop(Arm arm, Status status) {
        long end = status.triggerDateRaw(), delta = end - arm.startingDateRaw();
        boolean nativePause = status.triggerReasons().contains("native_pause");
        return status.state() == State.TRIGGERED && !status.abnormal() && sameArm(arm, status)
                && status.lastObservedDateRaw() == end && status.pauseObserved() && status.triggerFlags() != 0
                && !status.triggerReasons().isEmpty() && status.signedDateDeltaFromTargetRaw() == end - arm.targetDateRaw()
                && status.overshootDays() == 0 && end <= arm.targetDateRaw() && delta > 0 && delta % 24 == 0
                && status.completedDailyTicks() == delta / 24
                && status.triggerReasons().contains("date_deadline") == (end == arm.targetDateRaw())
                && status.intermediatePauseCount() == (nativePause ? 1 : 0) && status.pauseWrapperCalled() != nativePause;
    }
    private static boolean sameFrameIdentity(Scope scope, Semantic frame) {
        return frame.connected() && frame.bridgePid() == scope.game().pid() && frame.heartbeatPid() == scope.game().pid()
                && frame.connectionGeneration() == scope.connectionGeneration() && frame.actorId() == scope.actorId()
                && frame.playedActorId() == scope.actorId() && frame.playedActorAlive()
                && !frame.oneLifeTerminal() && !frame.episodeIdentityPending()
                && frame.snapshotId().equals("native:" + frame.nativeRevision())
                && frame.episodeId().equals(scope.episodeId()) && frame.world().equals(scope.world());
    }
    private static boolean regressed(Attempt attempt, Semantic previous, Semantic frame) {
        if (frame.nativeRevision() < attempt.minNativeRevision()
                || number(frame.verifiedPumpEpoch()).compareTo(number(attempt.minVerifiedPumpEpoch())) < 0
                || number(frame.heartbeatSequence()).compareTo(number(attempt.minHeartbeatSequence())) < 0) { return true; }
        return previous != null && (frame.nativeRevision() < previous.nativeRevision() || frame.publicRevision() < previous.publicRevision()
                || number(frame.verifiedPumpEpoch()).compareTo(number(previous.verifiedPumpEpoch())) < 0
                || number(frame.pumpEpoch()).compareTo(number(previous.pumpEpoch())) < 0
                || number(frame.heartbeatSequence()).compareTo(number(previous.heartbeatSequence())) < 0
                || number(frame.heartbeatMillis()).compareTo(number(previous.heartbeatMillis())) < 0);
    }
    private static boolean fresh(Semantic frame, Evidence evidence, Budget budget, Context context) {
        return sampleFresh(frame, evidence, budget)
                && context.elapsedMillis() - evidence.receivedElapsedMillis() <= budget.maximumSampleAgeMillis();
    }
    private static boolean sampleFresh(Semantic frame, Evidence evidence, Budget budget) {
        if (frame == null || evidence == null) { return false; }
        BigInteger age = number(evidence.readerWin32UptimeMillis()).subtract(number(frame.heartbeatMillis()));
        return age.signum() >= 0 && age.compareTo(BigInteger.valueOf(budget.maximumSampleAgeMillis())) <= 0
                && frame.mapReady() && frame.stampReadSuccess() && !frame.mailboxStop() && frame.mailboxFailure() == 0
                && frame.ownerTid() > 0 && frame.ownerTid() == frame.currentTid()
                && number(frame.verifiedPumpEpoch()).signum() > 0
                && number(frame.pumpEpoch()).compareTo(number(frame.verifiedPumpEpoch())) >= 0;
    }
    private static List<Long> sequences(List<Read> reads) { return reads.stream().map(read -> read.evidence().sequence()).toList(); }
    private static Assessment end(Outcome outcome, Reason reason, List<Read> reads) {
        return new Assessment(outcome, reason, null, 0, reads.size(), sequences(reads));
    }
}
