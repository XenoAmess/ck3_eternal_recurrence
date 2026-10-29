package org.xar.ck3.control.wave2.finance.feastordinary;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Immutable result of the existing Feast transport's pure hosted-identity normalizer. */
public record HostedFeastActivities(List<Activity> activities) {
    public static final int MAX_ACTIVITIES = 64;
    public static final long MAX_U32 = 0xFFFF_FFFFL;
    public static final BigInteger MAX_U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);

    public HostedFeastActivities {
        activities = List.copyOf(Objects.requireNonNull(activities, "activities"));
        if (activities.size() > MAX_ACTIVITIES) throw new IllegalArgumentException("private feast hosted identities malformed");
        Set<Long> ids = new HashSet<>();
        for (Activity activity : activities) {
            if (!ids.add(activity.activityId())) throw new IllegalArgumentException("private feast hosted identity malformed");
        }
    }

    /** Missing terminal fields differ from a current native observation of false flags. */
    public sealed interface Terminal permits TerminalAbsent, TerminalObserved { }
    public record TerminalAbsent() implements Terminal { }
    public record TerminalObserved(boolean completed, boolean invalidated) implements Terminal { }

    /** Stamp absence, explicitly unobserved/null and observed zero retain distinct meanings. */
    public sealed interface CompletionStamp permits StampAbsent, StampUnobserved, StampObserved { }
    public record StampAbsent() implements CompletionStamp { }
    public record StampUnobserved() implements CompletionStamp { }
    public record StampObserved(BigInteger raw) implements CompletionStamp {
        public StampObserved {
            Objects.requireNonNull(raw, "raw");
            if (raw.signum() < 0 || raw.compareTo(MAX_U64) > 0) {
                throw new IllegalArgumentException("private feast native completion stamp malformed");
            }
        }
    }

    public record Activity(long activityId, long hostCharacterId, String activityTypeKey,
                           Terminal terminal, CompletionStamp completionStamp) {
        public Activity {
            positiveU32(activityId, "activity_id"); positiveU32(hostCharacterId, "host_character_id");
            Objects.requireNonNull(activityTypeKey, "activity_type_key");
            if (activityTypeKey.isEmpty() || activityTypeKey.codePointCount(0, activityTypeKey.length()) > 63) {
                throw new IllegalArgumentException("private feast hosted identity malformed");
            }
            Objects.requireNonNull(terminal, "terminal"); Objects.requireNonNull(completionStamp, "completionStamp");
        }
    }

    private static void positiveU32(long value, String name) {
        if (value <= 0 || value > MAX_U32) throw new IllegalArgumentException(name + " must be a positive uint32 integer");
    }
}
