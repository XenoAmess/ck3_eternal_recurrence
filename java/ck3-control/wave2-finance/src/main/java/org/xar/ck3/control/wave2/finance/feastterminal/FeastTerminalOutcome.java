package org.xar.ck3.control.wave2.finance.feastterminal;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.CompletionStamp;

/** Pure terminal observation model; no utility, material debit, SAVE or action credit. */
public final class FeastTerminalOutcome {
    public static final String SCHEMA = "xar.ck3.activity-feast-terminal-outcome.v1";
    public static final String POST_SCHEMA = "activity-feast-hosted-post-private-read-v1";
    private FeastTerminalOutcome() { }

    public enum BooleanObservation { UNKNOWN, FALSE, TRUE }
    public enum Status { UNKNOWN, ONGOING, COMPLETED, INVALIDATED, COMPLETED_AND_INVALIDATED }
    public enum UnknownReason { ACTIVITY_NOT_OBSERVED, HOST_FRAME_MISMATCH, ACTIVITY_IDENTITY_MISMATCH, TERMINAL_FLAGS_UNOBSERVED }

    public sealed interface TextField permits AbsentText, NullText, PresentText { }
    public record AbsentText() implements TextField { }
    public record NullText() implements TextField { }
    public record PresentText(String value) implements TextField {
        public PresentText { Objects.requireNonNull(value, "value"); }
    }
    public record Provenance(TextField exactBuild, TextField exeSha256, TextField queriedSnapshotId) {
        public Provenance {
            Objects.requireNonNull(exactBuild); Objects.requireNonNull(exeSha256); Objects.requireNonNull(queriedSnapshotId);
        }
    }

    public sealed interface JournalField permits AbsentJournal, UnusableJournal, ParsedJournal { }
    public record AbsentJournal() implements JournalField { }
    /** Present null or malformed optional journals normalize to unavailable, as in the source. */
    public record UnusableJournal() implements JournalField { }
    public record ParsedJournal(NativeTerminalJournal value) implements JournalField {
        public ParsedJournal { Objects.requireNonNull(value, "value"); }
    }

    public record Post(BigInteger revision, BigInteger dateRaw, Optional<Long> frameActor,
                       HostedFeastActivities hosted, JournalField journal, Provenance provenance) {
        public Post {
            if (Objects.requireNonNull(revision).signum() <= 0 || Objects.requireNonNull(dateRaw).signum() < 0) {
                throw new IllegalArgumentException("private feast terminal post read malformed");
            }
            Objects.requireNonNull(frameActor).ifPresent(value -> positiveU32(value, "actor_character_id"));
            Objects.requireNonNull(hosted); Objects.requireNonNull(journal); Objects.requireNonNull(provenance);
        }
    }

    public record Request(long activityId, long actorId, Post post) {
        public Request {
            positiveU32(activityId, "activity_id"); positiveU32(actorId, "actor_character_id");
            Objects.requireNonNull(post, "post");
            if (post.journal() instanceof ParsedJournal parsed && parsed.value().available()
                    && parsed.value().queryActorId() != actorId) {
                throw new IllegalArgumentException("journal actor differs from target actor");
            }
        }
    }

    public record Outcome(long activityId, long actorId, BigInteger revision, BigInteger dateRaw,
                          Status status, boolean terminalFlagsObserved,
                          BooleanObservation completed, BooleanObservation invalidated,
                          Optional<UnknownReason> unknownReason, CompletionStamp completionStamp,
                          Optional<NativeTerminalJournal.Cut> historicalObservation,
                          JournalField journalCoverage, Provenance provenance) {
        public Outcome {
            positiveU32(activityId, "activity_id"); positiveU32(actorId, "actor_character_id");
            Objects.requireNonNull(revision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(status);
            Objects.requireNonNull(completed); Objects.requireNonNull(invalidated); Objects.requireNonNull(unknownReason);
            Objects.requireNonNull(completionStamp); Objects.requireNonNull(historicalObservation);
            Objects.requireNonNull(journalCoverage); Objects.requireNonNull(provenance);
            if (revision.signum() <= 0 || dateRaw.signum() < 0) throw new IllegalArgumentException("outcome frame is malformed");
            if ((status == Status.UNKNOWN) != unknownReason.isPresent()) throw new IllegalArgumentException("unknown reason/status mismatch");
            if (terminalFlagsObserved != (completed != BooleanObservation.UNKNOWN && invalidated != BooleanObservation.UNKNOWN))
                throw new IllegalArgumentException("terminal flags observation mismatch");
            boolean consistent = switch (status) {
                case UNKNOWN -> completed == BooleanObservation.UNKNOWN && invalidated == BooleanObservation.UNKNOWN && historicalObservation.isEmpty();
                case ONGOING -> completed == BooleanObservation.FALSE && invalidated == BooleanObservation.FALSE && historicalObservation.isEmpty();
                case COMPLETED -> completed == BooleanObservation.TRUE && invalidated != BooleanObservation.TRUE;
                case INVALIDATED -> invalidated == BooleanObservation.TRUE && completed != BooleanObservation.TRUE;
                case COMPLETED_AND_INVALIDATED -> completed == BooleanObservation.TRUE && invalidated == BooleanObservation.TRUE;
            };
            if (!consistent) throw new IllegalArgumentException("terminal status contradicts observed flags");
            if (historicalObservation.isPresent()) {
                NativeTerminalJournal.Cut cut = historicalObservation.orElseThrow();
                if (!(journalCoverage instanceof ParsedJournal parsed) || !parsed.value().records().contains(cut)
                        || cut.activityFullId() != activityId || Integer.toUnsignedLong(cut.hostCharacterId()) != actorId)
                    throw new IllegalArgumentException("historical cut is not bound to the outcome identity and coverage");
            }
        }
    }

    private static void positiveU32(long value, String name) {
        if (value <= 0 || value > HostedFeastActivities.MAX_U32) throw new IllegalArgumentException(name + " must be a positive uint32 integer");
    }
}
