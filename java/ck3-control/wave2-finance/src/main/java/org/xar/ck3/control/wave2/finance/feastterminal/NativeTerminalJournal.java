package org.xar.ck3.control.wave2.finance.feastterminal;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Validated historical native-cut facts. A journal is never a current live object. */
public record NativeTerminalJournal(boolean available, Optional<String> unavailableReason,
                                    boolean observerAttached, long queryThreadId, long queryActorId,
                                    BigInteger earliestSequence, BigInteger latestSequence,
                                    BigInteger overflowDroppedCount, List<Cut> records) {
    public static final String SCHEMA = "activity_terminal_observations_12004_v1";
    public static final BigInteger MAX_U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    public static final long MAX_U32 = 0xFFFF_FFFFL;
    public static final long SOURCE_CUT_RVA = 0x29BF68CL;

    public NativeTerminalJournal {
        Objects.requireNonNull(unavailableReason, "unavailableReason");
        unsigned32(queryThreadId, false, "query_thread_id_u32");
        unsigned32(queryActorId, false, "query_actor_full_id_u32");
        unsigned64(earliestSequence, false, "earliest_retained_sequence_u64");
        unsigned64(latestSequence, false, "latest_capture_sequence_u64");
        unsigned64(overflowDroppedCount, false, "overflow_dropped_count_u64");
        records = List.copyOf(Objects.requireNonNull(records, "records"));
        if (records.size() > 64 || earliestSequence.signum() == 0 != (latestSequence.signum() == 0)
                || earliestSequence.compareTo(latestSequence) > 0) invalid();
        if (available) {
            if (unavailableReason.isPresent() || !observerAttached || queryThreadId == 0) invalid();
        } else if (unavailableReason.isEmpty() || unavailableReason.orElseThrow().isEmpty() || !records.isEmpty()) invalid();
        BigInteger previous = BigInteger.ZERO;
        for (Cut cut : records) {
            if (cut.sequence().compareTo(earliestSequence) < 0 || cut.sequence().compareTo(latestSequence) > 0
                    || cut.sequence().compareTo(previous) <= 0
                    || Integer.toUnsignedLong(cut.hostCharacterId()) != queryActorId) invalid();
            previous = cut.sequence();
        }
    }

    public record Frame(long dateRaw, int actorCharacterId, long ownerThreadId,
                        boolean paused, boolean mapReady, boolean hasPlayedCharacter, boolean playedCharacterAlive) {
        public Frame {
            unsigned32(ownerThreadId, true, "owner_thread_id_u32");
            if (!mapReady || !hasPlayedCharacter || !playedCharacterAlive) invalid();
        }
    }

    public record Cut(BigInteger sequence, long threadId, long sourceCutRva,
                      BigInteger managerIdentity, BigInteger activityIdentity, BigInteger typeIdentity,
                      long activityFullId, int instanceGeneration, int hostCharacterId,
                      Optional<Integer> completedRaw, Optional<Integer> invalidatedRaw,
                      Optional<BigInteger> completionStampRaw, Frame frame) {
        public Cut {
            unsigned64(sequence, true, "capture_sequence_u64");
            unsigned32(threadId, true, "capture_thread_id_u32");
            if (sourceCutRva != SOURCE_CUT_RVA) invalid();
            unsigned64(managerIdentity, false, "manager_identity_u64");
            unsigned64(activityIdentity, false, "activity_identity_u64");
            unsigned64(typeIdentity, false, "type_identity_u64");
            if (activityFullId < 0 || activityFullId > 0xFFFF_FFFEL
                    || instanceGeneration < 0 || instanceGeneration > 255
                    || instanceGeneration != (activityFullId >>> 24)) invalid();
            rawByte(completedRaw); rawByte(invalidatedRaw);
            Objects.requireNonNull(completionStampRaw, "completionStampRaw")
                    .ifPresent(value -> unsigned64(value, false, "native_completion_stamp_raw_u64"));
            Objects.requireNonNull(frame, "frame");
            if (frame.actorCharacterId() != hostCharacterId || frame.ownerThreadId() != threadId) invalid();
        }
    }

    private static void rawByte(Optional<Integer> raw) {
        Objects.requireNonNull(raw, "raw").ifPresent(value -> { if (value < 0 || value > 255) invalid(); });
    }
    private static void unsigned32(long value, boolean positive, String name) {
        if (value < (positive ? 1 : 0) || value > MAX_U32) throw new IllegalArgumentException(name + " outside uint32");
    }
    private static void unsigned64(BigInteger value, boolean positive, String name) {
        Objects.requireNonNull(value, name);
        if (value.compareTo(positive ? BigInteger.ONE : BigInteger.ZERO) < 0 || value.compareTo(MAX_U64) > 0) {
            throw new IllegalArgumentException(name + " outside uint64");
        }
    }
    private static void invalid() { throw new IllegalArgumentException("private feast native terminal journal malformed"); }
}
