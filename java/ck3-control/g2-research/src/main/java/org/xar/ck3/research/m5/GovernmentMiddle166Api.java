package org.xar.ck3.research.m5;
import java.util.Objects;
/** New owned-memory composition [30A376E,30A41CE); no full-primary/Native/Game claim. */
public final class GovernmentMiddle166Api {
    private GovernmentMiddle166Api() { }
    /** All three values are actual execution outputs, never projections of original input. */
    public record Result(GovernmentCompaction160Api.Join compactionJoin,
            GovernmentPreprefix159Api.Entry preludeEntry, GovernmentJoined159Api.Result joinedResult) {
        public Result { Objects.requireNonNull(compactionJoin);Objects.requireNonNull(preludeEntry);Objects.requireNonNull(joinedResult); }
    }
}
