package org.xar.ck3.control.score;

import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/** Side-effect-free port of Interval, aggregate_state, score_360 and interval_text. */
public final class CampaignScoreCore {
    public static final String VERSION = "campaign-development-v1-design-2026-10-19";
    private static final List<ScoreDecimal> WEIGHTS = List.of(d(".25"), d(".25"), d(".15"), d(".10"), d(".15"), d(".10"));
    private CampaignScoreCore() { }

    public static ScoreInterval aggregateState(DomainScores scores) {
        ScoreInterval total = ScoreInterval.exact("0");
        List<ScoreInterval> ordered = scores.ordered();
        for (int index = 0; index < WEIGHTS.size(); index++) {
            total = total.add(ordered.get(index).scale(WEIGHTS.get(index)));
        }
        return total;
    }

    public static ScoreInterval score360(MonthlyHistory history) {
        return new ScoreInterval(bound(history, false), bound(history, true));
    }

    private static ScoreDecimal bound(MonthlyHistory history, boolean upper) {
        List<ScoreDecimal> values = new ArrayList<>(360);
        for (ScoreInterval sample : history.samples()) {
            ScoreDecimal value = upper ? sample.upper() : sample.lower();
            inRange(value, "monthly state outside 0..100");
            values.add(value);
        }
        ScoreDecimal end = upper ? history.endpoint().upper() : history.endpoint().lower();
        inRange(end, "endpoint outside 0..100");
        ScoreDecimal last = divide(sum(values.subList(348, 360)), 12);
        ScoreDecimal mean = divide(sum(values), 360);
        List<ScoreDecimal> sorted = new ArrayList<>(values);
        sorted.sort(ScoreDecimal::compareTo);
        ScoreDecimal low = divide(sum(sorted.subList(0, 36)), 36);
        // Keep every Python Decimal operation and rounding boundary, including each addition.
        ScoreDecimal finalWindow = add(multiply(d(".6"), end), multiply(d(".4"), last));
        ScoreDecimal weighted = add(add(multiply(d(".7"), finalWindow), multiply(d(".2"), mean)), multiply(d(".1"), low));
        return multiply(d("10"), weighted);
    }

    public static String intervalText(ScoreDecimal lower, ScoreDecimal upper, int places) {
        if (lower.compareTo(upper) == 0) { return lower.fixed(places, RoundingMode.HALF_EVEN); }
        return lower.fixed(places, RoundingMode.FLOOR) + "–" + upper.fixed(places, RoundingMode.CEILING);
    }

    private static ScoreDecimal d(String value) { return ScoreDecimal.parse(value); }
    private static ScoreDecimal add(ScoreDecimal left, ScoreDecimal right) { return left.add(right, ScoreDecimal.CONTEXT_40); }
    private static ScoreDecimal multiply(ScoreDecimal left, ScoreDecimal right) { return left.multiply(right, ScoreDecimal.CONTEXT_40); }
    private static ScoreDecimal divide(ScoreDecimal left, long right) { return left.divide(ScoreDecimal.integer(right), ScoreDecimal.CONTEXT_40); }
    private static ScoreDecimal sum(List<ScoreDecimal> values) {
        ScoreDecimal total = ScoreDecimal.ZERO;
        for (ScoreDecimal value : values) { total = add(total, value); }
        return total;
    }
    private static void inRange(ScoreDecimal value, String message) {
        StrictJson.require(value.compareTo(ScoreDecimal.ZERO) >= 0 && value.compareTo(ScoreDecimal.HUNDRED) <= 0, message);
    }
}
