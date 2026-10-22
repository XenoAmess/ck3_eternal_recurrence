package org.xar.ck3.control.score;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Arithmetic slots only: caller still proves original T0, fixed dates and endpoint identity. */
public record MonthlyHistory(List<ScoreInterval> samples, ScoreInterval endpoint) {
    public MonthlyHistory {
        samples = List.copyOf(samples);
        Objects.requireNonNull(endpoint, "endpoint required");
        StrictJson.require(samples.size() == 360, "exactly 360 fixed month slots required; do not shorten denominator");
    }
}
