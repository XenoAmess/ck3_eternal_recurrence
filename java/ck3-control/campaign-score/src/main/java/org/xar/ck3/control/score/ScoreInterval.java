package org.xar.ck3.control.score;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared immutable interval; unknown [0,100] is distinct from absent input. */
public record ScoreInterval(ScoreDecimal lower, ScoreDecimal upper) {
    public static final ScoreInterval UNKNOWN = new ScoreInterval(ScoreDecimal.ZERO, ScoreDecimal.HUNDRED);

    public ScoreInterval {
        Objects.requireNonNull(lower, "lower required");
        Objects.requireNonNull(upper, "upper required");
        StrictJson.require(lower.compareTo(upper) <= 0, "invalid score interval");
    }
    public static ScoreInterval exact(ScoreDecimal value) { return new ScoreInterval(value, value); }
    public static ScoreInterval exact(String value) { return exact(ScoreDecimal.parse(value)); }
    public boolean known() { return lower.compareTo(upper) == 0; }

    public ScoreInterval scale(ScoreDecimal weight) {
        StrictJson.require(weight.compareTo(ScoreDecimal.ZERO) >= 0, "negative interval weight");
        return new ScoreInterval(lower.multiply(weight, ScoreDecimal.CONTEXT_80),
                upper.multiply(weight, ScoreDecimal.CONTEXT_80));
    }
    public ScoreInterval add(ScoreInterval other) {
        Objects.requireNonNull(other, "interval required");
        return new ScoreInterval(lower.add(other.lower, ScoreDecimal.CONTEXT_80),
                upper.add(other.upper, ScoreDecimal.CONTEXT_80));
    }
}
