package org.xar.ck3.control.reconciliation;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Immutable facts supplied by the original Queue owner. Constructors confer no source authority. */
public final class LateOutcome {
    private LateOutcome() { }
    public enum State { IDLE, ARMED, TRIGGERED, FAILED, UNAVAILABLE }
    public enum Mode { DECISION_EPOCH, TERMINAL_OR_SENTINEL }
    public enum ReadKind { CURRENT_SENTINEL_STATUS, CURRENT_SEMANTIC_FRAME }
    public enum Outcome { PROPOSED, WAIT, UNRESOLVED, REJECTED }
    public enum GameLife { SAME_PROCESS_ALIVE, CLOSED, UNKNOWN }
    public enum Reason {
        NEED_STATUS, ARMED_GUARD_RETAINED, NEED_PAUSED_SEMANTIC, NEED_CONFIRMING_STATUS,
        LATE_STOP_REQUIRES_WRITER_REDUCER, ORIGINAL_PROJECTION_INCOMPLETE,
        GAME_CLOSED, GAME_LIVENESS_UNKNOWN, BUDGET_EXHAUSTED, DEADLINE_EXPIRED,
        SOURCE_OR_IDENTITY_CHANGED, READ_SEQUENCE_INVALID, READ_TIME_INVALID, HISTORY_INCOMPLETE,
        WRONG_READ_ORDER, SLOT_CHANGED, STOP_NOT_VALID, READ_UNAVAILABLE,
        SLOT_NOT_TRIGGERED, SEMANTIC_NOT_PAUSED, SEMANTIC_NOT_FRESH,
        FRAME_IDENTITY_CHANGED, FRAME_REGRESSED, FRAME_DATE_CHANGED
    }

    public record ProcessIdentity(long pid, CrossJsDecimalUInt64 creationFiletime) {
        public ProcessIdentity {
            StrictJson.require(pid >= 1 && pid <= 0xffff_ffffL, "uint32 process ID required");
            positive(creationFiletime, "process creation FILETIME");
        }
    }
    /** Native world pointers are equality identities, never ordered epoch counters. */
    public record WorldIdentity(CrossJsDecimalUInt64 gameState, CrossJsDecimalUInt64 jominiState) {
        public WorldIdentity { positive(gameState, "game state"); positive(jominiState, "Jomini state"); }
    }
    public record SourceBinding(String closureSha256, String javaBuildSha256, String providerSha256,
                                String executableSha256, String qualificationReceiptSha256) {
        public SourceBinding {
            digest(closureSha256); digest(javaBuildSha256); digest(providerSha256);
            digest(executableSha256); digest(qualificationReceiptSha256);
        }
    }
    public record Scope(String machineId, ProcessIdentity game, ProcessIdentity queue,
                        ProcessIdentity application, String sessionId, SourceBinding source,
                        long connectionGeneration, int actorId, String episodeId, WorldIdentity world) {
        public Scope {
            StrictJson.text(machineId); Objects.requireNonNull(game); Objects.requireNonNull(queue);
            Objects.requireNonNull(application); StrictJson.text(sessionId); Objects.requireNonNull(source);
            StrictJson.safe(connectionGeneration, 1); StrictJson.require(actorId >= 1, "positive actor ID");
            StrictJson.text(episodeId); Objects.requireNonNull(world);
        }
    }
    public record ContentEvidenceRef(String sha256, long bytes, String evidenceKey) {
        public ContentEvidenceRef { digest(sha256); StrictJson.safe(bytes, 1); StrictJson.text(evidenceKey); }
    }
    public record Arm(CrossJsDecimalUInt64 generation, int startingDateRaw, int targetDateRaw,
                      int speed, Mode mode, List<Integer> watchArmyIds, long combatCount) {
        public Arm {
            positive(generation, "arm generation"); Objects.requireNonNull(mode);
            StrictJson.require(startingDateRaw >= 0 && targetDateRaw > startingDateRaw
                    && ((long) targetDateRaw - startingDateRaw) % 24 == 0, "positive whole-day arm interval");
            StrictJson.require(speed >= 1 && speed <= 5, "speed 1..5");
            watchArmyIds = List.copyOf(watchArmyIds);
            StrictJson.require(watchArmyIds.size() <= 64, "at most 64 public CUnit watch IDs");
            int previous = -1;
            for (Integer id : watchArmyIds) {
                StrictJson.require(id != null && id >= 0 && id > previous, "sorted unique nonnegative int32 public CUnit IDs");
                previous = id;
            }
            uint32(combatCount);
        }
    }
    /** Original error facts remain separate even after a new late-stop observation. */
    public record OriginalFailure(ContentEvidenceRef receipt, long fullSequence, long autoSequence,
                                  boolean normalStatusQueryAttempted, boolean stopValidationAttempted) {
        public OriginalFailure {
            Objects.requireNonNull(receipt); StrictJson.safe(fullSequence, 1); StrictJson.safe(autoSequence, 1);
            StrictJson.require(autoSequence > fullSequence, "AUTO sequence follows FULL");
        }
        public int originalCredit() { return 0; }
        public boolean neverReplay() { return true; }
    }
    /** expectedHead identifies the real writer CAS/reducer inputs; this module never opens them. */
    public record Attempt(Scope scope, OriginalFailure original, Arm arm, ContentEvidenceRef expectedHead,
                          long minNativeRevision, CrossJsDecimalUInt64 minVerifiedPumpEpoch,
                          CrossJsDecimalUInt64 minHeartbeatSequence) {
        public Attempt {
            Objects.requireNonNull(scope); Objects.requireNonNull(original); Objects.requireNonNull(arm);
            Objects.requireNonNull(expectedHead); StrictJson.safe(minNativeRevision, 0);
            Objects.requireNonNull(minVerifiedPumpEpoch); Objects.requireNonNull(minHeartbeatSequence);
        }
    }
    public record Budget(long maximumDurationMillis, int maximumReads, long maximumSampleAgeMillis,
                         long pollWaitMillis, Instant hardDeadline) {
        public Budget {
            StrictJson.require(maximumDurationMillis >= 1 && maximumDurationMillis <= 3_600_000, "bounded duration");
            StrictJson.require(maximumReads >= 1 && maximumReads <= 64, "bounded read count");
            StrictJson.require(maximumSampleAgeMillis >= 1 && maximumSampleAgeMillis <= 60_000, "bounded sample age");
            StrictJson.require(pollWaitMillis >= 0 && pollWaitMillis <= maximumDurationMillis, "bounded poll delay");
            Objects.requireNonNull(hardDeadline);
        }
    }
    /** elapsed is Java orchestration time; Win32 uptime is a separate native freshness domain. */
    public record Context(GameLife gameLife, long elapsedMillis, Instant now, int totalReadsConsumed) {
        public Context {
            Objects.requireNonNull(gameLife); StrictJson.safe(elapsedMillis, 0); Objects.requireNonNull(now);
            StrictJson.require(totalReadsConsumed >= 0 && totalReadsConsumed <= 64, "actual bounded transport read ledger count");
        }
    }
    public record Evidence(Scope before, Scope after, long sequence, ContentEvidenceRef reply,
                           long receivedElapsedMillis, Instant observedAt, CrossJsDecimalUInt64 readerWin32UptimeMillis) {
        public Evidence {
            Objects.requireNonNull(before); Objects.requireNonNull(after); StrictJson.safe(sequence, 1);
            Objects.requireNonNull(reply); StrictJson.safe(receivedElapsedMillis, 0);
            Objects.requireNonNull(observedAt); Objects.requireNonNull(readerWin32UptimeMillis);
        }
    }
    public record Status(State state, CrossJsDecimalUInt64 generation, int startingDateRaw,
                         int targetDateRaw, int lastObservedDateRaw, int triggerDateRaw, int speed, Mode mode,
                         long armyCount, long combatCount, long completedDailyTicks, long intermediatePauseCount,
                         long triggerFlags, List<String> triggerReasons, int signedDateDeltaFromTargetRaw,
                         int overshootDays, boolean pauseWrapperCalled, boolean pauseObserved,
                         boolean terminalObserved, boolean abnormal) {
        public Status {
            Objects.requireNonNull(state); Objects.requireNonNull(generation); Objects.requireNonNull(mode);
            StrictJson.require(startingDateRaw >= 0 && targetDateRaw >= 0 && lastObservedDateRaw >= 0
                    && triggerDateRaw >= 0, "nonnegative native date fields");
            StrictJson.require(overshootDays >= -1, "overshoot days at least -1");
            StrictJson.require(speed >= 1 && speed <= 5, "status speed 1..5");
            uint32(armyCount); uint32(combatCount); uint32(completedDailyTicks); uint32(intermediatePauseCount);
            StrictJson.require(triggerFlags >= 0 && triggerFlags < (1L << 17), "known sentinel flags only");
            triggerReasons = List.copyOf(triggerReasons);
            StrictJson.require(triggerReasons.equals(SentinelCodec.reasons(triggerFlags)), "ordered reasons match flags");
            StrictJson.require(terminalObserved == ((triggerFlags & (1L << 8)) != 0), "terminal flag relationship");
            StrictJson.require(abnormal == (state == State.FAILED), "abnormal iff failed");
        }
    }
    /** Selected real SEM fields, not a claim to validate all unrelated business fields. */
    public record Semantic(int dateRaw, boolean paused, boolean mapReady, int speed, long nativeRevision,
                           long publicRevision, String snapshotId, int actorId, String episodeId,
                           int playedActorId, boolean playedActorAlive, boolean oneLifeTerminal, boolean episodeIdentityPending,
                           boolean connected, long connectionGeneration, long bridgePid,
                           CrossJsDecimalUInt64 heartbeatSequence, CrossJsDecimalUInt64 heartbeatMillis,
                           long heartbeatPid, CrossJsDecimalUInt64 pumpEpoch, CrossJsDecimalUInt64 verifiedPumpEpoch,
                           long ownerTid, long currentTid, WorldIdentity world, int ownerDateRaw,
                           boolean ownerPaused, boolean stampReadSuccess, boolean mailboxStop, long mailboxFailure) {
        public Semantic {
            StrictJson.require(speed >= 1 && speed <= 5, "semantic speed 1..5");
            StrictJson.safe(nativeRevision, 0); StrictJson.safe(publicRevision, 0); StrictJson.text(snapshotId);
            StrictJson.require(dateRaw >= 0 && ownerDateRaw >= 0, "nonnegative semantic date");
            NativeCharacterId.of(actorId); NativeCharacterId.of(playedActorId); StrictJson.text(episodeId);
            StrictJson.safe(connectionGeneration, 1); uint32(bridgePid); uint32(heartbeatPid);
            Objects.requireNonNull(heartbeatSequence); Objects.requireNonNull(heartbeatMillis);
            Objects.requireNonNull(pumpEpoch); Objects.requireNonNull(verifiedPumpEpoch);
            uint32(ownerTid); uint32(currentTid); Objects.requireNonNull(world); uint32(mailboxFailure);
        }
    }
    public sealed interface Read permits StatusRead, SemanticRead, UnavailableRead {
        Evidence evidence(); ReadKind kind();
    }
    public record StatusRead(Evidence evidence, Status status) implements Read {
        public StatusRead { Objects.requireNonNull(evidence); Objects.requireNonNull(status); }
        @Override public ReadKind kind() { return ReadKind.CURRENT_SENTINEL_STATUS; }
    }
    public record SemanticRead(Evidence evidence, Semantic semantic) implements Read {
        public SemanticRead { Objects.requireNonNull(evidence); Objects.requireNonNull(semantic); }
        @Override public ReadKind kind() { return ReadKind.CURRENT_SEMANTIC_FRAME; }
    }
    public record UnavailableRead(Evidence evidence, ReadKind kind, String diagnostic) implements Read {
        public UnavailableRead { Objects.requireNonNull(evidence); Objects.requireNonNull(kind); StrictJson.text(diagnostic); }
    }
    /** No action capability, resume ticket, replay instruction, cancel instruction or commit method exists. */
    public record Assessment(Outcome outcome, Reason reason, ReadKind nextRead, long waitMillis,
                             int consumedReads, List<Long> observedSequences) {
        public Assessment {
            Objects.requireNonNull(outcome); Objects.requireNonNull(reason); observedSequences = List.copyOf(observedSequences);
            StrictJson.require(waitMillis >= 0 && consumedReads >= 0 && consumedReads <= 64
                    && observedSequences.size() <= 64, "bounded observed read sequence list");
            StrictJson.require(reason == Reason.HISTORY_INCOMPLETE || consumedReads == observedSequences.size(), "complete history unless explicitly rejected");
            for (Long sequence : observedSequences) { StrictJson.require(sequence != null, "read sequence required"); StrictJson.safe(sequence, 1); }
            StrictJson.require(outcome != Outcome.PROPOSED || (consumedReads >= 3 && consumedReads == observedSequences.size()), "proposal needs complete three-read evidence");
            StrictJson.require((outcome == Outcome.WAIT) == (nextRead != null), "only WAIT proposes a read");
            StrictJson.require(outcome == Outcome.WAIT || waitMillis == 0, "no wait outside WAIT");
            StrictJson.require(waitMillis <= 3_600_000, "bounded proposed delay");
            boolean reasonAllowed = switch (outcome) {
                case PROPOSED -> reason == Reason.LATE_STOP_REQUIRES_WRITER_REDUCER;
                case WAIT -> java.util.EnumSet.of(Reason.NEED_STATUS, Reason.ARMED_GUARD_RETAINED,
                        Reason.NEED_PAUSED_SEMANTIC, Reason.NEED_CONFIRMING_STATUS, Reason.SEMANTIC_NOT_PAUSED,
                        Reason.SEMANTIC_NOT_FRESH).contains(reason);
                case UNRESOLVED -> java.util.EnumSet.of(Reason.ORIGINAL_PROJECTION_INCOMPLETE,
                        Reason.GAME_LIVENESS_UNKNOWN, Reason.BUDGET_EXHAUSTED, Reason.DEADLINE_EXPIRED,
                        Reason.READ_UNAVAILABLE, Reason.SLOT_NOT_TRIGGERED, Reason.SEMANTIC_NOT_FRESH).contains(reason);
                case REJECTED -> java.util.EnumSet.of(Reason.GAME_CLOSED, Reason.SOURCE_OR_IDENTITY_CHANGED,
                        Reason.READ_SEQUENCE_INVALID, Reason.READ_TIME_INVALID, Reason.HISTORY_INCOMPLETE,
                        Reason.WRONG_READ_ORDER, Reason.SLOT_CHANGED, Reason.STOP_NOT_VALID,
                        Reason.FRAME_IDENTITY_CHANGED, Reason.FRAME_REGRESSED, Reason.FRAME_DATE_CHANGED).contains(reason);
            };
            StrictJson.require(reasonAllowed, "reason must belong to outcome branch");
        }
        public int originalCredit() { return 0; }
        public boolean neverReplay() { return true; }
    }
    static void digest(String value) {
        StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "lowercase SHA-256 required");
    }
    static void uint32(long value) { StrictJson.require(value >= 0 && value <= 0xffff_ffffL, "uint32 required"); }
    static BigInteger number(CrossJsDecimalUInt64 value) { return new BigInteger(value.decimal()); }
    private static void positive(CrossJsDecimalUInt64 value, String name) {
        Objects.requireNonNull(value); StrictJson.require(number(value).signum() > 0, name + " must be positive");
    }
}
