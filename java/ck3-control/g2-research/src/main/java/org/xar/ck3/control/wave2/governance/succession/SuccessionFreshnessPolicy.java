package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.SuccessionFreshnessModel.*;
import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.check;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.util.Objects;
import java.util.Optional;

/** Exact original source-age comparison. A newer scalar cannot become a complete prediction. */
public final class SuccessionFreshnessPolicy {
    private SuccessionFreshnessPolicy() { }

    public static Observation observe(Input input) {
        Objects.requireNonNull(input);
        EpisodeBinding source = input.predecessorBinding();
        check(source.episodeCharacterId().equals(input.predecessorCharacterId()),
                "succession freshness predecessor differs");
        BigInteger age = input.boundaryBinding().dateRaw().subtract(source.frame().dateRaw());
        check(age.signum() >= 0, "succession freshness source is after the boundary");
        input.expectation().ifPresent(full -> check(
                EpisodeBinding.fromExpectation(full.binding()).equals(source),
                "complete title expectation belongs to another source frame"));

        Optional<BigInteger> livingAge = Optional.empty();
        Optional<Boolean> same = Optional.empty();
        if (input.lastLivingFrame().isPresent()) {
            EpisodeBinding living = input.lastLivingFrame().orElseThrow();
            check(living.episodeRunId().equals(source.episodeRunId())
                            && living.episodeCharacterId().equals(source.episodeCharacterId()),
                    "last observed living frame belongs to another episode");
            check(source.frame().dateRaw().compareTo(living.frame().dateRaw()) <= 0
                            && living.frame().dateRaw().compareTo(input.boundaryBinding().dateRaw()) <= 0,
                    "last observed living frame is outside the transition dates");
            same = Optional.of(source.equals(living));
            livingAge = Optional.of(input.boundaryBinding().dateRaw().subtract(living.frame().dateRaw()));
        }
        AllTitleFreshness state = input.expectation().isEmpty() ? AllTitleFreshness.FULL_EXPECTATION_NOT_OBSERVED
                : input.lastLivingFrame().isEmpty() ? AllTitleFreshness.LAST_LIVING_FRAME_NOT_OBSERVED
                : same.orElseThrow() ? AllTitleFreshness.SAME_AS_LAST_OBSERVED_LIVING_FRAME
                : AllTitleFreshness.DIFFERENT_FROM_LAST_OBSERVED_LIVING_FRAME;
        return new Observation(input, age, livingAge, same, state);
    }

    /** Original Python /24 presentation is binary64; identities and raw ages stay BigInteger. */
    static double days(BigInteger raw) {
        // A finite binary64 quotient has at most 310 decimal integer digits. Keeping 400
        // significant digits avoids rounding the arbitrary-precision integer before division.
        double result = new BigDecimal(raw).divide(BigDecimal.valueOf(24),
                new MathContext(400, RoundingMode.HALF_EVEN)).doubleValue();
        check(Double.isFinite(result), "diagnostic day age exceeds the original finite float domain");
        return result;
    }
}
